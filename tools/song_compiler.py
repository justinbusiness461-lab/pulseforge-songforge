#!/usr/bin/env python3
"""Deterministic prompt → SongSpec compiler (Python mirror of app-core.js parsePrompt).

Ceiling: rule-based genre/key/form + integer ticks. Not neural arrangement.
Identity contract: same (prompt, seed/nonce) → same seed, ticks, event counts.
Wall-clock created_at is intentionally omitted from the identity fingerprint.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

TPQ = 960
SONG_SCHEMA = "pulseforge.songforge.skeleton.v2.20"
SONG_SCHEMA_VERSION = "2.20.0"

SCALES = {
    "F# minor": {"root": 42, "scale": [0, 2, 3, 5, 7, 8, 10], "lead": [66, 69, 71, 73], "pluck": [54, 57, 61, 64], "vocal": [54, 57, 59, 61]},
    "A minor": {"root": 45, "scale": [0, 2, 3, 5, 7, 8, 10], "lead": [69, 72, 74, 76], "pluck": [57, 60, 64, 67], "vocal": [57, 60, 62, 64]},
    "C minor": {"root": 36, "scale": [0, 2, 3, 5, 7, 8, 10], "lead": [60, 63, 65, 67], "pluck": [48, 51, 55, 58], "vocal": [48, 51, 53, 55]},
    "D minor": {"root": 38, "scale": [0, 2, 3, 5, 7, 8, 10], "lead": [62, 65, 67, 69], "pluck": [50, 53, 57, 60], "vocal": [50, 53, 55, 57]},
    "E minor": {"root": 40, "scale": [0, 2, 3, 5, 7, 8, 10], "lead": [64, 67, 69, 71], "pluck": [52, 55, 59, 62], "vocal": [52, 55, 57, 59]},
    "G major": {"root": 43, "scale": [0, 2, 4, 5, 7, 9, 11], "lead": [67, 71, 74, 76], "pluck": [55, 59, 62, 67], "vocal": [55, 59, 62, 64]},
}


def mulberry32(a: int):
    """Match JS mulberry32 used in app-core.js (Math.imul semantics)."""
    state = a & 0xFFFFFFFF

    def rnd_js():
        nonlocal state
        state = (state + 0x6D2B79F5) & 0xFFFFFFFF
        t = state
        t = _imul(t ^ (t >> 15), t | 1) & 0xFFFFFFFF
        t = (t ^ ((_imul(t ^ (t >> 7), t | 61) + t) & 0xFFFFFFFF)) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296

    return rnd_js


def _imul(a: int, b: int) -> int:
    a = a & 0xFFFFFFFF
    b = b & 0xFFFFFFFF
    # signed 32-bit imul then reinterpret as unsigned for mulberry steps
    prod = (a * b) & 0xFFFFFFFF
    return prod


def hash_seed(s: str) -> int:
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = _imul(h, 16777619) & 0xFFFFFFFF
    return h & 0xFFFFFFFF


def lyrics_to_phonemes(text: str) -> list[dict[str, str]]:
    words = re.sub(r"[^a-z\s']", " ", (text or "").lower()).split()
    out: list[dict[str, str]] = []
    for w in words:
        parts = re.findall(r"[^aeiouy]*[aeiouy]+[^aeiouy]*", w, flags=re.I) or [w]
        for part in parts:
            pl = part.lower()
            if re.search(r"ee|ea|i|y|ay|ey", pl):
                ph = "ee"
            elif re.search(r"oo|u|ou", pl):
                ph = "oo"
            elif re.search(r"o|oa|ow", pl):
                ph = "oh"
            elif re.search(r"e|eh", pl):
                ph = "eh"
            elif re.search(r"a|ah", pl):
                ph = "ah"
            else:
                ph = "ah"
            out.append({"word": w, "phoneme": ph, "syllable": part})
    return out or [{"word": "ah", "phoneme": "ah", "syllable": "ah"}]


def ticks_to_samples(ticks: int, bpm: float, sample_rate: int = 44100, tpq: int = TPQ) -> int:
    sec = (ticks / tpq) * (60.0 / bpm)
    return int(round(sec * sample_rate))


def parse_prompt(text: str, opts: dict | None = None) -> dict[str, Any]:
    opts = opts or {}
    p = (text or "").lower()
    if opts.get("seed") is not None:
        seed_val = int(opts["seed"]) & 0xFFFFFFFF
    else:
        seed_val = hash_seed(p + "|" + str(opts.get("nonce") or "0"))
    # rnd reserved for future density variation — keep call for seed advance parity
    _rnd = mulberry32(seed_val)

    bpm = 102
    m = re.search(r"(\d{2,3})\s*bpm", p)
    if m:
        bpm = max(60, min(180, int(m.group(1))))

    key = "F# minor"
    for k in SCALES:
        if k.lower() in p:
            key = k
            break
    if "c minor" in p:
        key = "C minor"
    if "a minor" in p:
        key = "A minor"
    if "d minor" in p:
        key = "D minor"

    genre = "alt-hip-hop"
    if "house" in p or "club" in p:
        genre = "house"
    elif "blues" in p:
        genre = "electro-blues"
    elif "trap" in p:
        genre = "trap"
    elif "lo-fi" in p or "lofi" in p:
        genre = "lo-fi"

    dark = bool(re.search(r"dark|smoky|noir|sparse|minimal", p))
    want_pluck = bool(re.search(r"guitar|pluck|string|acoustic|blues", p))

    form = [
        {"name": "Intro", "type": "intro", "bars": 2, "role": "none", "lyrics": ""},
        {"name": "Verse", "type": "verse", "bars": 4, "role": "male", "lyrics": "late night same streetlight i keep telling myself im fine"},
        {"name": "Chorus", "type": "chorus", "bars": 4, "role": "both", "lyrics": "its a bad habit but i cant break it"},
        {"name": "Verse", "type": "verse", "bars": 4, "role": "male", "lyrics": "same song different room same old tune"},
        {"name": "Chorus", "type": "chorus", "bars": 4, "role": "female", "lyrics": "its a bad habit but i cant break it"},
        {"name": "Outro", "type": "outro", "bars": 2, "role": "none", "lyrics": ""},
    ]
    if "bridge" in p:
        form.insert(4, {"name": "Bridge", "type": "bridge", "bars": 2, "role": "female", "lyrics": "if i said stay would you mean it"})

    tick = 0
    sections = []
    for s in form:
        start = tick
        tick += s["bars"] * 4 * TPQ
        sections.append({
            "id": f"sec-{start}",
            "name": s["name"],
            "type": s["type"],
            "start_tick": start,
            "end_tick": tick,
            "role": s["role"],
            "lyrics": s["lyrics"],
        })

    sc = SCALES.get(key) or SCALES["F# minor"]
    drums = {"track_id": "drums", "name": "Drums", "type": "DRUMS", "volume_db": -3 if dark else -1, "pan": 0, "muted": False, "events": []}
    bass = {"track_id": "bass", "name": "Bass", "type": "BASS", "volume_db": -2, "pan": 0, "muted": False, "events": []}
    pad = {"track_id": "pad", "name": "Pad", "type": "PAD", "volume_db": -10, "pan": -0.2, "muted": False, "events": []}
    lead = {"track_id": "lead", "name": "Lead", "type": "LEAD", "volume_db": -6, "pan": 0.15, "muted": False, "events": []}
    pluck = {"track_id": "pluck", "name": "Pluck", "type": "STRINGS", "volume_db": -4, "pan": 0.25, "muted": False, "events": []}
    vocal = {"track_id": "vocal", "name": "Vocal", "type": "VOCAL", "volume_db": -3, "pan": -0.05, "muted": False, "events": []}

    total_ticks = tick
    bar_ticks = 4 * TPQ
    eighth = TPQ // 2

    bar = 0
    while bar * bar_ticks < total_ticks:
        base = bar * bar_ticks
        drums["events"].append({"type": "NOTE_ON", "tick": base, "note_number": 36, "velocity": 115, "duration_ticks": 200})
        if (not dark) or (bar % 2 == 0):
            drums["events"].append({"type": "NOTE_ON", "tick": base + 2 * TPQ, "note_number": 38, "velocity": 100, "duration_ticks": 180})
        for e in range(8):
            if dark and e % 2 == 1:
                continue
            drums["events"].append({
                "type": "NOTE_ON",
                "tick": base + e * eighth,
                "note_number": 42,
                "velocity": 70 if e % 2 == 0 else 45,
                "duration_ticks": 80,
            })
        bar += 1

    progression = [0, 0, 5, 3, 0, 7, 5, 0]
    bar = 0
    while bar * bar_ticks < total_ticks:
        deg = progression[bar % len(progression)]
        note = sc["root"] + sc["scale"][deg % len(sc["scale"])]
        base = bar * bar_ticks
        dens = 2 if dark else 4
        for i in range(dens):
            bass["events"].append({
                "type": "NOTE_ON",
                "tick": int(base + i * (bar_ticks / dens)),
                "note_number": note,
                "velocity": 105,
                "duration_ticks": int(bar_ticks / dens) - 40,
            })
        bar += 1

    for sec in sections:
        if sec["type"] in ("intro", "outro"):
            continue
        deg = 0 if sec["type"] == "chorus" else 5
        pad["events"].append({
            "type": "NOTE_ON",
            "tick": sec["start_tick"],
            "note_number": sc["root"] + 12 + sc["scale"][deg % len(sc["scale"])],
            "velocity": 70,
            "duration_ticks": sec["end_tick"] - sec["start_tick"] - 100,
        })

    for sec in [s for s in sections if s["type"] in ("chorus", "bridge")]:
        for i in range(4):
            lead["events"].append({
                "type": "NOTE_ON",
                "tick": sec["start_tick"] + i * TPQ,
                "note_number": sc["lead"][i % len(sc["lead"])],
                "velocity": 95,
                "duration_ticks": TPQ - 80,
            })

    for sec in [s for s in sections if s["type"] in ("verse", "chorus") or want_pluck]:
        for i in range(4):
            pluck["events"].append({
                "type": "NOTE_ON",
                "tick": sec["start_tick"] + i * TPQ + (0 if want_pluck else TPQ // 2),
                "note_number": sc["pluck"][i % len(sc["pluck"])],
                "velocity": 100 if want_pluck else 75,
                "duration_ticks": 480,
            })

    for sec in sections:
        if sec["role"] == "none" or not sec["lyrics"]:
            continue
        phones = lyrics_to_phonemes(sec["lyrics"])
        span = sec["end_tick"] - sec["start_tick"]
        step = max(TPQ // 2, span // max(1, len(phones)))
        for i, ph in enumerate(phones):
            t = sec["start_tick"] + i * step
            if t >= sec["end_tick"]:
                break
            note = sc["vocal"][i % len(sc["vocal"])] + (5 if sec["role"] == "female" else 0)
            role = ("male" if i % 2 == 0 else "female") if sec["role"] == "both" else sec["role"]
            vocal["events"].append({
                "type": "NOTE_ON",
                "tick": t,
                "note_number": note,
                "velocity": 100,
                "duration_ticks": min(step - 40, TPQ),
                "phoneme": ph["phoneme"],
                "word": ph["word"],
                "role": role,
            })

    return {
        "$schema": SONG_SCHEMA,
        "schema_version": SONG_SCHEMA_VERSION,
        "song_id": f"sf-{seed_val:x}",
        "generation_seed": seed_val,
        "title": "Generated",
        "engine": "phase4-spatial-bbd",
        "timebase": {
            "ticks_per_quarter_note": TPQ,
            "initial_bpm": bpm,
            "sample_rate": 44100,
            "key": key,
            "genre": genre,
            "meter": "4/4",
        },
        "structure": {"sections": sections},
        "tracks": [drums, bass, pad, lead, pluck, vocal],
        "prompt": text,
        "change_ledger": [],
    }



def extend_arrangement(spec: dict, *, lyrics: str | None = None) -> dict:
    """Append a copy of the last vocal (or last) section after arrangement end."""
    import copy
    spec = copy.deepcopy(spec)
    secs = spec["structure"]["sections"]
    template = next((s for s in reversed(secs) if s.get("role") and s.get("role") != "none"), secs[-1])
    span = (template["end_tick"] - template["start_tick"]) or (4 * 4 * TPQ)
    last_end = max(s["end_tick"] for s in secs)
    new = copy.deepcopy(template)
    new["id"] = f"sec-{last_end}-x"
    new["name"] = (template.get("name") or "Section") + " +"
    new["start_tick"] = last_end
    new["end_tick"] = last_end + span
    if lyrics is not None:
        new["lyrics"] = lyrics
    delta = new["start_tick"] - template["start_tick"]
    for tr in spec["tracks"]:
        adds = []
        for ev in tr.get("events") or []:
            if template["start_tick"] <= ev["tick"] < template["end_tick"]:
                nev = copy.deepcopy(ev)
                nev["tick"] = ev["tick"] + delta
                adds.append(nev)
        tr["events"] = (tr.get("events") or []) + adds
    secs.append(new)
    ledger = spec.setdefault("change_ledger", [])
    ledger.append({"op": "extend_arrangement", "new_id": new["id"], "from": template["id"]})
    return spec


def remix_arrangement(spec: dict, *, nonce: str = "remix-1") -> dict:
    """Recompile with new seed; preserve lyrics/roles by section index when lengths match."""
    import copy
    prior = copy.deepcopy(spec)
    text = prior.get("prompt") or "dark 102 BPM F# minor"
    seed = hash_seed(text + "|remix|" + nonce)
    nxt = parse_prompt(text, {"seed": seed})
    n = min(len(prior["structure"]["sections"]), len(nxt["structure"]["sections"]))
    for i in range(n):
        src = prior["structure"]["sections"][i]
        dst = nxt["structure"]["sections"][i]
        if src.get("lyrics"):
            dst["lyrics"] = src["lyrics"]
        if src.get("role"):
            dst["role"] = src["role"]
        if src.get("name"):
            dst["name"] = src["name"]
    nxt["title"] = prior.get("title") or nxt.get("title")
    nxt["change_ledger"] = list(prior.get("change_ledger") or [])
    nxt["change_ledger"].append({"op": "remix_arrangement", "seed": nxt["generation_seed"], "nonce": nonce})
    return nxt


def identity_fingerprint(spec: dict) -> str:
    """Stable identity excluding wall-clock fields."""
    payload = {
        "schema": spec.get("$schema"),
        "schema_version": spec.get("schema_version"),
        "song_id": spec.get("song_id"),
        "generation_seed": spec.get("generation_seed"),
        "timebase": spec.get("timebase"),
        "structure": spec.get("structure"),
        "tracks": [
            {
                "track_id": t.get("track_id"),
                "type": t.get("type"),
                "volume_db": t.get("volume_db"),
                "events": t.get("events"),
            }
            for t in (spec.get("tracks") or [])
        ],
        "prompt": spec.get("prompt"),
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


if __name__ == "__main__":
    import sys

    prompt = " ".join(sys.argv[1:]) or "dark 102 BPM alt hip-hop, F# minor, guitar plucks"
    spec = parse_prompt(prompt, {"nonce": "0"})
    print(json.dumps({"song_id": spec["song_id"], "seed": spec["generation_seed"], "fingerprint": identity_fingerprint(spec), "sections": len(spec["structure"]["sections"])}, indent=2))
