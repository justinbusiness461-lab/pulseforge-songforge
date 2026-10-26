#!/usr/bin/env python3
"""Deterministic SongForge unit tests: compiler, ticks, phonemes, WAV, PF-SOUND-002."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import song_compiler as sc  # noqa: E402
import studio_server as server  # noqa: E402
from certify_mix import amplitude_dbfs, inspect as inspect_wav  # noqa: E402


class TickMath(unittest.TestCase):
    def test_tpq_bar(self):
        self.assertEqual(4 * sc.TPQ, 3840)

    def test_ticks_to_samples_102bpm(self):
        # 1 quarter at 102 BPM = 60/102 sec * 44100
        samples = sc.ticks_to_samples(sc.TPQ, 102, 44100)
        expected = int(round((60.0 / 102.0) * 44100))
        self.assertEqual(samples, expected)

    def test_section_span_integer(self):
        spec = sc.parse_prompt("dark 102 BPM F# minor", {"nonce": "0"})
        for sec in spec["structure"]["sections"]:
            self.assertIsInstance(sec["start_tick"], int)
            self.assertIsInstance(sec["end_tick"], int)
            self.assertEqual(sec["start_tick"] % (sc.TPQ // 2), 0)


class PhonemeTimeline(unittest.TestCase):
    def test_known_words(self):
        phones = sc.lyrics_to_phonemes("late night same streetlight")
        self.assertGreaterEqual(len(phones), 4)
        self.assertTrue(all(p["phoneme"] in {"ah", "eh", "ee", "oh", "oo"} for p in phones))

    def test_empty_fallback(self):
        self.assertEqual(sc.lyrics_to_phonemes("")[0]["phoneme"], "ah")

    def test_vocal_events_have_phonemes(self):
        spec = sc.parse_prompt("102 BPM F# minor male verse", {"nonce": "0"})
        vocal = next(t for t in spec["tracks"] if t["type"] == "VOCAL")
        self.assertTrue(vocal["events"])
        for ev in vocal["events"]:
            self.assertIn(ev["phoneme"], {"ah", "eh", "ee", "oh", "oo"})
            self.assertIsInstance(ev["tick"], int)


class PromptCompiler(unittest.TestCase):
    def test_seed_repro(self):
        a = sc.parse_prompt("dark 102 BPM alt hip-hop, F# minor, guitar plucks", {"nonce": "0"})
        b = sc.parse_prompt("dark 102 BPM alt hip-hop, F# minor, guitar plucks", {"nonce": "0"})
        self.assertEqual(a["generation_seed"], b["generation_seed"])
        self.assertEqual(a["song_id"], b["song_id"])
        self.assertEqual(sc.identity_fingerprint(a), sc.identity_fingerprint(b))

    def test_seed_differs_by_nonce(self):
        a = sc.parse_prompt("trap 140 BPM", {"nonce": "0"})
        b = sc.parse_prompt("trap 140 BPM", {"nonce": "1"})
        self.assertNotEqual(a["generation_seed"], b["generation_seed"])

    def test_explicit_seed(self):
        a = sc.parse_prompt("house 120 BPM", {"seed": 42})
        b = sc.parse_prompt("completely different text", {"seed": 42})
        self.assertEqual(a["generation_seed"], 42)
        self.assertEqual(b["generation_seed"], 42)
        self.assertEqual(a["song_id"], "sf-2a")

    def test_schema_versioned(self):
        spec = sc.parse_prompt("lofi 80 BPM A minor", {"nonce": "0"})
        self.assertEqual(spec["$schema"], sc.SONG_SCHEMA)
        self.assertEqual(spec["schema_version"], sc.SONG_SCHEMA_VERSION)
        self.assertEqual(spec["timebase"]["ticks_per_quarter_note"], 960)
        self.assertEqual(spec["change_ledger"], [])

    def test_bridge_injection(self):
        with_b = sc.parse_prompt("dark 102 BPM with bridge", {"nonce": "0"})
        without = sc.parse_prompt("dark 102 BPM", {"nonce": "0"})
        self.assertGreater(len(with_b["structure"]["sections"]), len(without["structure"]["sections"]))


class WavIdentity(unittest.TestCase):
    def test_header_pcm16_stereo(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "t.wav"
            nbytes = server.write_stereo_wav(path, duration_sec=0.25, bpm=102)
            self.assertGreater(nbytes, 0)
            raw = path.read_bytes()
            self.assertEqual(raw[:4], b"RIFF")
            self.assertEqual(raw[8:12], b"WAVE")
            # fmt chunk: PCM=1, channels=2, rate=44100, bits=16
            audio_format, channels, rate, _, _, bits = struct.unpack_from("<HHIIHH", raw, 20)
            self.assertEqual((audio_format, channels, rate, bits), (1, 2, 44100, 16))
            metrics = inspect_wav(path)
            self.assertTrue(metrics["decoded_sample_frames"] > 0)
            self.assertIsNotNone(metrics["sample_peak_dbfs"])

    def test_same_params_same_pcm(self):
        with tempfile.TemporaryDirectory() as td:
            a = Path(td) / "a.wav"
            b = Path(td) / "b.wav"
            server.write_stereo_wav(a, duration_sec=0.5, bpm=102)
            server.write_stereo_wav(b, duration_sec=0.5, bpm=102)
            self.assertEqual(hashlib.sha256(a.read_bytes()).hexdigest(), hashlib.sha256(b.read_bytes()).hexdigest())

    def test_amplitude_dbfs_helpers(self):
        self.assertAlmostEqual(amplitude_dbfs(0.5), -6.020599913279624)
        self.assertEqual(amplitude_dbfs(1), 0)
        self.assertIsNone(amplitude_dbfs(0))


class ContentAddressedIntegrity(unittest.TestCase):
    """PF-SOUND-002: alias overwrite must not break historical ledger rows."""

    def test_alias_overwrite_history_survives(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = server.persist_export(root, "master.wav", "mixes", b"CONTENT-A")
            b = server.persist_export(root, "master.wav", "mixes", b"CONTENT-B")
            self.assertNotEqual(a["sha256"], b["sha256"])
            self.assertNotEqual(a["saved_at"], b["saved_at"])
            ledger = json.loads((root / "manifest_registry.json").read_text())
            self.assertEqual(len(ledger), 2)
            for row in ledger:
                path = Path(row["absolute_path"])
                self.assertTrue(path.is_file())
                digest = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(digest, row["sha256_checksum"].replace("sha256:", ""))


if __name__ == "__main__":
    unittest.main()
