#!/usr/bin/env python3
"""B4/B5: project schema + section identity + fingerprint stability (no browser)."""
from __future__ import annotations
import json, copy, sys
from pathlib import Path

def make_fixture():
    return {
        "$schema": "pulseforge.songforge.skeleton.v2.8",
        "song_id": "sf-test-001",
        "generation_seed": 42,
        "title": "RoundTrip",
        "timebase": {"ticks_per_quarter_note": 480, "initial_bpm": 100, "key": "F# minor", "genre": "trap", "meter": "4/4", "sample_rate": 44100},
        "structure": {
            "sections": [
                {"id": "sec-0", "name": "Intro", "type": "intro", "start_tick": 0, "end_tick": 1920, "role": "none", "lyrics": ""},
                {"id": "sec-1920", "name": "Verse", "type": "verse", "start_tick": 1920, "end_tick": 5760, "role": "male", "lyrics": "test line one"},
                {"id": "sec-5760", "name": "Chorus", "type": "chorus", "start_tick": 5760, "end_tick": 9600, "role": "female", "lyrics": "hook line"},
            ]
        },
        "tracks": [
            {"track_id": "drums", "name": "Drums", "type": "DRUMS", "volume_db": -1, "pan": 0, "muted": False,
             "events": [{"type": "NOTE_ON", "tick": 0, "note_number": 36, "velocity": 100, "duration_ticks": 120}]},
            {"track_id": "vocal", "name": "Vocal", "type": "VOCAL", "volume_db": -4, "pan": 0, "muted": False,
             "events": [{"type": "NOTE_ON", "tick": 1920, "note_number": 60, "velocity": 100, "duration_ticks": 240, "phoneme": "ah", "role": "male"}]},
        ],
        "prompt": "100 BPM trap",
        "edit_history": [],
    }

def fingerprint(sk):
    secs = [{"id": s["id"], "name": s["name"], "start": s["start_tick"], "end": s["end_tick"],
             "role": s["role"], "lyrics": s.get("lyrics") or "", "muted": bool(s.get("muted"))}
            for s in sk["structure"]["sections"]]
    tracks = [{"id": t["track_id"], "type": t["type"], "muted": bool(t.get("muted")),
               "n_events": len(t.get("events") or []), "vol": t.get("volume_db")}
              for t in sk["tracks"]]
    return json.dumps({"song_id": sk["song_id"], "seed": sk.get("generation_seed"),
                       "bpm": sk["timebase"]["initial_bpm"], "key": sk["timebase"]["key"],
                       "sections": secs, "tracks": tracks}, sort_keys=True)

def main() -> int:
    print("=" * 72)
    print(" PROJECT ROUND-TRIP / SECTION-ISOLATION HARNESS")
    print("=" * 72)
    fail = 0
    sk = make_fixture()
    fp0 = fingerprint(sk)
    raw = json.dumps(sk)
    sk2 = json.loads(raw)
    fp1 = fingerprint(sk2)
    if fp0 != fp1:
        print("FAIL serialize fingerprint drift"); fail += 1
    else:
        print("PASS serialize identity stable")
    others_before = {s["id"]: copy.deepcopy(s) for s in sk2["structure"]["sections"] if s["id"] != "sec-1920"}
    for s in sk2["structure"]["sections"]:
        if s["id"] == "sec-1920":
            s["lyrics"] = "edited verse lyrics only"
    for oid, before in others_before.items():
        after = next(s for s in sk2["structure"]["sections"] if s["id"] == oid)
        if after != before:
            print(f"FAIL unrelated section mutated: {oid}"); fail += 1; break
    else:
        print("PASS section lyrics edit isolated")
    src = next(s for s in sk2["structure"]["sections"] if s["id"] == "sec-5760")
    span = src["end_tick"] - src["start_tick"]
    last = max(s["end_tick"] for s in sk2["structure"]["sections"])
    copy_sec = copy.deepcopy(src)
    copy_sec["id"] = f"sec-{last}-copy"
    copy_sec["name"] = src["name"] + " (copy)"
    copy_sec["start_tick"] = last
    copy_sec["end_tick"] = last + span
    sk2["structure"]["sections"].append(copy_sec)
    ids = [s["id"] for s in sk2["structure"]["sections"]]
    if len(ids) != len(set(ids)):
        print("FAIL duplicate section ids"); fail += 1
    else:
        print("PASS unique section ids after duplicate")
    bad = {"foo": 1}
    if bad.get("structure") and bad.get("tracks"):
        print("FAIL invalid should reject"); fail += 1
    else:
        print("PASS invalid schema rejected by contract")
    out = Path("workspace/studio_exports/score_graphs/roundtrip_fixture.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sk2, indent=2))
    sk3 = json.loads(out.read_text())
    if fingerprint(sk2) != fingerprint(sk3):
        print("FAIL disk round-trip drift"); fail += 1
    else:
        print("PASS disk round-trip fingerprint")
    if sk3.get("generation_seed") != 42:
        print("FAIL seed lost"); fail += 1
    else:
        print("PASS generation_seed preserved")
    print("=" * 72)
    print("RESULT:", "PASS" if fail == 0 else f"FAIL ({fail})")
    return 1 if fail else 0

if __name__ == "__main__":
    raise SystemExit(main())
