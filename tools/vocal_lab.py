#!/usr/bin/env python3
"""
S.A.R.A. Sound Forge — Production Vocal Lab (local, sovereign)

Tiers
  formant   : classic source-filter (fast)
  production: torch LF-glottal + 5 formants + vibrato + breath (CPU)
  onnx      : optional drop-in ONNX acoustic/vocoder if weights present under models/

This is NOT ElevenLabs/Suno cloud parity until real SVS weights are installed.
It is the strongest offline path available without multi-GB checkpoints.
"""
from __future__ import annotations

import hashlib
import math
import os
import random
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    import torch.nn.functional as F
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

try:
    import onnxruntime as ort
    HAS_ORT = True
except ImportError:
    HAS_ORT = False

SAMPLE_RATE = 44100
MODELS_DIR = Path(__file__).resolve().parent.parent / "models" / "vocal"
ACOUSTIC_ONNX = MODELS_DIR / "diffsinger_acoustic.onnx"
VOCODER_ONNX = MODELS_DIR / "nsf_hifigan.onnx"
PHONE_TO_ID = {"sp": 0, "ah": 1, "ee": 2, "oo": 3, "oh": 4, "eh": 5, "ih": 6, "uh": 7, "cl": 8, "rest": 0}


# ── Phoneme formant tables (Hz): F1..F5 approx adult values ─────────────
FORMANTS = {
    "ah": [(700, 90), (1220, 110), (2600, 170), (3200, 200), (4500, 300)],
    "ee": [(270, 60), (2290, 120), (3010, 150), (3500, 200), (4500, 300)],
    "oo": [(300, 70), (870, 100), (2240, 150), (3200, 200), (4500, 300)],
    "oh": [(450, 80), (800, 100), (2830, 160), (3200, 200), (4500, 300)],
    "eh": [(530, 80), (1840, 120), (2480, 150), (3500, 200), (4500, 300)],
    "ih": [(390, 70), (1990, 120), (2550, 150), (3500, 200), (4500, 300)],
    "uh": [(440, 80), (1020, 100), (2240, 150), (3200, 200), (4500, 300)],
    "rest": [(500, 100), (1500, 150), (2500, 200), (3500, 250), (4500, 300)],
}


def _role_scale(role: str) -> float:
    r = (role or "male").lower()
    if r in ("female", "alto", "soprano"):
        return 1.18
    if r in ("both", "duet"):
        return 1.08
    return 1.0


def _phoneme_from_token(token: str) -> str:
    t = (token or "la").lower()
    if any(c in t for c in "iy"):
        return "ee"
    if any(c in t for c in "ou"):
        return "oo"
    if "a" in t:
        return "ah"
    if "e" in t:
        return "eh"
    return "ah"


# ── Numpy formant path (always available) ───────────────────────────────
def _biquad_bandpass(sr: int, freq: float, bw: float):
    q = max(0.5, freq / max(1.0, bw))
    w0 = 2.0 * math.pi * freq / sr
    alpha = math.sin(w0) / (2.0 * q)
    a0 = 1.0 + alpha
    return alpha / a0, 0.0, -alpha / a0, (-2.0 * math.cos(w0)) / a0, (1.0 - alpha) / a0


def synthesize_formant_phrase(
    phoneme_map: List[Dict[str, Any]],
    bpm: float = 102.0,
    tpq: int = 960,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    def tick_sec(t: float) -> float:
        return (float(t) / tpq) * (60.0 / max(40.0, bpm))

    total = 0
    for item in phoneme_map:
        end = int(tick_sec(float(item.get("tick_position", 0)) + float(item.get("duration_ticks", tpq))) * sample_rate)
        total = max(total, end)
    master = np.zeros(total + sample_rate, dtype=np.float64)

    for item in phoneme_map:
        start = int(tick_sec(float(item.get("tick_position", 0))) * sample_rate)
        n = max(1, int(tick_sec(float(item.get("duration_ticks", tpq))) * sample_rate))
        f0 = float(item.get("target_f0_hz") or 220.0)
        ph = str(item.get("phoneme") or "ah")
        role = str(item.get("role_profile") or "male")
        scale = _role_scale(role)
        formants = FORMANTS.get(ph, FORMANTS["ah"])
        formants = [(f * scale, b) for f, b in formants]

        phase = 0.0
        states = [(0.0, 0.0) for _ in formants]
        coeffs = [_biquad_bandpass(sample_rate, f, b) for f, b in formants]
        omega = 2.0 * math.pi * max(50.0, f0) / sample_rate
        vib_phase = random.random() * math.pi

        for i in range(n):
            env = 1.0
            att, rel = min(n // 12, 900), min(n // 10, 1400)
            if i < att:
                env = i / max(1, att)
            elif i > n - rel:
                env = max(0.0, (n - i) / max(1, rel))

            vib = 1.0 + 0.012 * math.sin(2 * math.pi * 5.5 * i / sample_rate + vib_phase)
            # LF-ish glottal: negative saw with closing skew
            phase += omega * vib * (1.0 + random.uniform(-0.003, 0.003))
            if phase > math.pi:
                phase -= 2 * math.pi
            # Rosenberg-like pulse
            tnorm = (phase + math.pi) / (2 * math.pi)
            if tnorm < 0.6:
                source = math.sin(math.pi * tnorm / 0.6)
            else:
                source = 0.5 * math.sin(math.pi * (tnorm - 0.6) / 0.4) * math.exp(-4 * (tnorm - 0.6))
            source += random.uniform(-1, 1) * 0.02  # aspiration

            y = 0.0
            for k, (b0, b1, b2, a1, a2) in enumerate(coeffs):
                y1, y2 = states[k]
                out = b0 * source + b1 * 0.0 + b2 * 0.0 - a1 * y1 - a2 * y2
                states[k] = (out, y1)
                y += out * (0.55 if k == 0 else 0.35 if k == 1 else 0.18 if k == 2 else 0.1)

            master[start + i] += max(-1.0, min(1.0, y * 0.35 * env))

    peak = np.max(np.abs(master)) + 1e-9
    master = (master / peak * 0.92).astype(np.float32)
    return master


# ── Torch production path ───────────────────────────────────────────────
def synthesize_production_phrase(
    phoneme_map: List[Dict[str, Any]],
    bpm: float = 102.0,
    tpq: int = 960,
    sample_rate: int = SAMPLE_RATE,
) -> np.ndarray:
    """Vectorized glottal + multi-formant on CPU torch when available."""
    if not HAS_TORCH:
        return synthesize_formant_phrase(phoneme_map, bpm, tpq, sample_rate)

    def tick_sec(t: float) -> float:
        return (float(t) / tpq) * (60.0 / max(40.0, bpm))

    total = 0
    segments = []
    for item in phoneme_map:
        start = int(tick_sec(float(item.get("tick_position", 0))) * sample_rate)
        n = max(1, int(tick_sec(float(item.get("duration_ticks", tpq))) * sample_rate))
        total = max(total, start + n)
        segments.append((start, n, item))

    master = torch.zeros(total + sample_rate, dtype=torch.float32)

    for start, n, item in segments:
        f0 = float(item.get("target_f0_hz") or 220.0)
        ph = str(item.get("phoneme") or "ah")
        role = str(item.get("role_profile") or "male")
        scale = _role_scale(role)
        formants = [(f * scale, b) for f, b in FORMANTS.get(ph, FORMANTS["ah"])]

        t = torch.arange(n, dtype=torch.float32) / sample_rate
        # Vibrato + slight drift
        vib = 1.0 + 0.015 * torch.sin(2 * math.pi * 5.4 * t + random.random())
        # Instantaneous phase for glottal
        inst_f0 = f0 * vib
        phase = torch.cumsum(2 * math.pi * inst_f0 / sample_rate, dim=0)
        phase = torch.remainder(phase, 2 * math.pi)
        tnorm = phase / (2 * math.pi)
        # Glottal flow derivative approx (Liljencrants-Fant simplified)
        open_quot = 0.6
        source = torch.where(
            tnorm < open_quot,
            torch.sin(math.pi * tnorm / open_quot),
            0.45 * torch.sin(math.pi * (tnorm - open_quot) / (1 - open_quot))
            * torch.exp(-5.0 * (tnorm - open_quot)),
        )
        source = source + 0.025 * torch.randn(n)

        # ADSR-ish envelope
        att = max(1, min(n // 12, 900))
        rel = max(1, min(n // 10, 1400))
        env = torch.ones(n)
        env[:att] = torch.linspace(0, 1, att)
        if rel < n:
            env[-rel:] = torch.linspace(1, 0, rel)

        y = torch.zeros(n)
        # Cascade resonance via sequential IIR in numpy for stability (formant parallel)
        src_np = source.numpy()
        y_np = np.zeros(n, dtype=np.float64)
        for fi, (freq, bw) in enumerate(formants):
            b0, b1, b2, a1, a2 = _biquad_bandpass(sample_rate, freq, bw)
            y1 = y2 = 0.0
            gain = [0.5, 0.35, 0.2, 0.12, 0.08][min(fi, 4)]
            acc = np.zeros(n)
            for i in range(n):
                out = b0 * src_np[i] - a1 * y1 - a2 * y2
                y2, y1 = y1, out
                acc[i] = out * gain
            y_np += acc
        y = torch.from_numpy(y_np.astype(np.float32)) * env * 0.4
        end = start + n
        if end > len(master):
            y = y[: max(0, len(master) - start)]
            end = start + len(y)
        master[start:end] += y

    peak = master.abs().max().clamp(min=1e-6)
    master = (master / peak * 0.92).numpy()
    return master.astype(np.float32)


# ── ONNX optional ───────────────────────────────────────────────────────
def has_onnx_weights() -> bool:
    return ACOUSTIC_ONNX.is_file() and VOCODER_ONNX.is_file()


def build_control_tensors(phoneme_map, bpm: float = 102.0, tpq: int = 960, frame_hz: float = 80.0):
    """Build DiffSinger-style control frames: tokens, f0, voicing [1, T]."""
    def tick_sec(t):
        return (float(t) / tpq) * (60.0 / max(40.0, bpm))

    phone_ids = []
    f0_list = []
    for item in phoneme_map:
        ph = str(item.get("phoneme") or "ah")
        ph_id = PHONE_TO_ID.get(ph, 1)
        dur = tick_sec(float(item.get("duration_ticks") or tpq))
        n_frames = max(1, int(round(dur * frame_hz)))
        f0 = float(item.get("target_f0_hz") or 220.0)
        phone_ids.extend([ph_id] * n_frames)
        f0_list.extend([f0] * n_frames)

    if not phone_ids:
        phone_ids, f0_list = [1], [220.0]

    tokens = np.array([phone_ids], dtype=np.int64)
    f0 = np.array([f0_list], dtype=np.float32)
    uv = (f0 > 0).astype(np.float32)
    return tokens, f0, uv


def try_onnx_svs(phoneme_map, bpm: float = 102.0, tpq: int = 960) -> Optional[np.ndarray]:
    """
    Run DiffSinger acoustic + NSF-HiFiGAN if both ONNX files exist.
    Input names tried in order; real exports vary — mismatch returns None + logs.
    """
    if not HAS_ORT or not has_onnx_weights():
        return None
    try:
        tokens, f0, uv = build_control_tensors(phoneme_map, bpm, tpq)
        opts = ort.SessionOptions()
        opts.intra_op_num_threads = 2
        providers = ["CPUExecutionProvider"]

        acoustic = ort.InferenceSession(str(ACOUSTIC_ONNX), sess_options=opts, providers=providers)
        a_inputs = {i.name: i for i in acoustic.get_inputs()}
        feed = {}
        # Flexible name matching for community exports
        for name, arr in (
            ("tokens", tokens), ("tokens_raw", tokens), ("phone", tokens), ("ph_seq", tokens),
            ("f0", f0), ("f0_seq", f0), ("pitch", f0),
            ("voicing", uv), ("uv", uv), ("v_uv", uv),
        ):
            if name in a_inputs:
                # reshape if model expects different rank
                expected = a_inputs[name].shape
                feed[name] = arr

        if not feed:
            print("[ONNX] acoustic input names:", list(a_inputs.keys()), "— no match; skip")
            return None

        mel_out = acoustic.run(None, feed)[0]
        print(f"[ONNX] acoustic mel shape {getattr(mel_out, 'shape', None)}")

        vocoder = ort.InferenceSession(str(VOCODER_ONNX), sess_options=opts, providers=providers)
        v_inputs = {i.name: i for i in vocoder.get_inputs()}
        vfeed = {}
        for name, arr in (("mel", mel_out), ("spec", mel_out), ("x", mel_out), ("f0", f0), ("f0_seq", f0)):
            if name in v_inputs:
                vfeed[name] = arr
        if not vfeed:
            print("[ONNX] vocoder input names:", list(v_inputs.keys()), "— no match; skip")
            return None

        wave = vocoder.run(None, vfeed)[0]
        wave = np.asarray(wave, dtype=np.float32).flatten()
        peak = np.max(np.abs(wave)) + 1e-9
        return (wave / peak * 0.92).astype(np.float32)
    except Exception as e:
        print(f"[ONNX] inference fault (fallback to production): {e}")
        return None


def try_onnx_vocoder(mel_or_features: Optional[np.ndarray] = None) -> Optional[np.ndarray]:
    return None  # use try_onnx_svs with phoneme_map


class InAppNeuralVocalsLab:
    def __init__(self, sample_rate: int = SAMPLE_RATE, quality: str = "production"):
        self.sample_rate = sample_rate
        self.quality = quality if quality in ("formant", "production", "onnx") else "production"
        self.phoneme_profiles = {k: (v[0][0], v[1][0]) for k, v in FORMANTS.items()}

    def synthesize_speech_phoneme(self, duration_samples, f0_hz, phoneme_str, role_profile):
        item = {
            "tick_position": 0,
            "duration_ticks": max(1, int(duration_samples / self.sample_rate * 960 * 102 / 60)),
            "target_f0_hz": f0_hz,
            "phoneme": phoneme_str,
            "role_profile": role_profile,
        }
        # Single-event map with synthetic ticks
        bpm, tpq = 102.0, 960
        dur_ticks = max(1, int((duration_samples / self.sample_rate) * (tpq * bpm / 60.0)))
        item["duration_ticks"] = dur_ticks
        pcm = self.compile_singing_timeline([item], bpm=bpm, tpq=tpq)
        return pcm[:duration_samples].tolist()

    def compile_singing_timeline(
        self, phoneme_map: List[Dict[str, Any]], bpm: float = 102.0, tpq: int = 960
    ) -> List[float]:
        for item in phoneme_map:
            if "phoneme" not in item or not item["phoneme"]:
                item["phoneme"] = _phoneme_from_token(str(item.get("text_token") or "la"))
            if "target_f0_hz" not in item or item["target_f0_hz"] in (None, ""):
                midi = float(item.get("midi_note") or 60)
                item["target_f0_hz"] = 440.0 * (2 ** ((midi - 69) / 12))

        if self.quality == "formant":
            pcm = synthesize_formant_phrase(phoneme_map, bpm, tpq, self.sample_rate)
            engine = "formant_source_filter"
        elif self.quality == "onnx":
            onnx_out = try_onnx_svs(phoneme_map, bpm, tpq)
            if onnx_out is not None:
                pcm = onnx_out
                engine = "onnx_runtime_svs"
            else:
                pcm = synthesize_production_phrase(phoneme_map, bpm, tpq, self.sample_rate)
                engine = "production_torch_fallback_no_onnx_weights"
        else:
            pcm = synthesize_production_phrase(phoneme_map, bpm, tpq, self.sample_rate)
            engine = "production_torch_glottal_formant" if HAS_TORCH else "production_numpy_formant"

        self.last_engine = engine
        return pcm.tolist() if isinstance(pcm, np.ndarray) else list(pcm)


def write_stereo_wav(path: Path, mono: np.ndarray, sample_rate: int = SAMPLE_RATE) -> str:
    mono = np.asarray(mono, dtype=np.float32)
    peak = np.max(np.abs(mono)) + 1e-9
    mono = mono / peak * 0.95
    pcm = bytearray()
    for s in mono:
        i = int(max(-1.0, min(1.0, float(s))) * 32767)
        pcm += struct.pack("<hh", i, i)
    data = bytes(pcm)
    header = b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
    header += struct.pack("<IHHIIHH", 16, 1, 2, sample_rate, sample_rate * 4, 4, 16)
    header += b"data" + struct.pack("<I", len(data))
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.with_suffix(path.suffix + ".tmp")
    with open(staging, "wb") as f:
        f.write(header + data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(staging, path)
    return hashlib.sha256(data).hexdigest()


def render_vocal_job(request: Dict[str, Any], export_dir: Path) -> Dict[str, Any]:
    quality = str(request.get("quality") or "production")
    role = str(request.get("role_profile") or "male")
    bpm = float(request.get("bpm") or 102)
    tpq = int(request.get("tpq") or 960)
    phoneme_map = list(request.get("phoneme_map") or [])
    for it in phoneme_map:
        it["role_profile"] = role

    lab = InAppNeuralVocalsLab(sample_rate=SAMPLE_RATE, quality=quality)
    pcm_list = lab.compile_singing_timeline(phoneme_map, bpm=bpm, tpq=tpq)
    pcm = np.asarray(pcm_list, dtype=np.float32)
    vault = export_dir / "vocal_stems"
    vault.mkdir(parents=True, exist_ok=True)
    asset_hash = hashlib.sha256(pcm.tobytes()).hexdigest()
    wav_path = vault / f"vocal_{quality}_{asset_hash[:16]}.wav"
    write_stereo_wav(wav_path, pcm)

    return {
        "status": "SUCCESS",
        "asset_hash": asset_hash,
        "saved_master_path": str(wav_path.resolve()),
        "samples_rendered": int(pcm.shape[0]),
        "engine": getattr(lab, "last_engine", quality),
        "quality": quality,
        "torch": HAS_TORCH,
        "onnx_runtime": HAS_ORT,
        "onnx_weights_present": has_onnx_weights(),
        "ceiling_note": (
            "production torch glottal+formant (local). "
            "Commercial neural SVS requires DiffSinger/SO-VITS weights in models/vocal/."
        ),
    }


if __name__ == "__main__":
    # quick self-test
    demo = [
        {"tick_position": 0, "duration_ticks": 960, "target_f0_hz": 220, "phoneme": "ah", "role_profile": "male"},
        {"tick_position": 960, "duration_ticks": 960, "target_f0_hz": 247, "phoneme": "ee", "role_profile": "male"},
    ]
    out = render_vocal_job({"phoneme_map": demo, "quality": "production"}, Path("/tmp"))
    print(out)
