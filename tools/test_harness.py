#!/usr/bin/env python3
"""Integration harness: load MusicEventGraph.json → armature transforms."""
from __future__ import annotations

import json
import os
import sys

from armature_solver import ArmatureVisemeSolver


def execute_integration_harness(meg_path: str) -> bool:
    print(f"[Harness] Loading Cinema Graph: {meg_path}")
    if not os.path.exists(meg_path):
        print(f"Error: file not found: {meg_path}")
        return False

    with open(meg_path, "r", encoding="utf-8") as f:
        graph = json.load(f)

    title = graph.get("title") or graph.get("song_id") or "UNKNOWN"
    tb = graph.get("timebase") or {}
    bpm = graph.get("bpm") or tb.get("initial_bpm") or 102
    print(f"[Harness] Title: {title} | BPM: {bpm}")

    solver = ArmatureVisemeSolver()
    events = graph.get("events") or graph.get("timeline") or []

    print("\n" + "=" * 70)
    print(" PROCESSING MUSIC EVENT GRAPH VIA ANIMATION SOLVER")
    print("=" * 70)

    sections = 0
    phonemes = 0

    for event in events:
        et = event.get("type") or event.get("event_type") or ""
        result = solver.solve_meg_event(event)

        if result["kind"] == "section":
            sections += 1
            role = (result.get("role") or "none").upper()
            print(f"\nSection: {str(result.get('name')):<12} | Role: {role}")
            print(
                f"  Samples [{result.get('start_sample')} -> {result.get('end_sample')}]"
            )
            layout = result.get("layout") or []
            if layout:
                print(f"  Viseme chain: {layout}")
                for t in result.get("transforms") or []:
                    print(
                        f"    [{t['viseme']}] jaw_y={t['jaw_translation_y_mm']}mm "
                        f"scale_x={t['mouth_scale_x']} pucker={t['lip_pucker_z_factor']}"
                    )
            elif role == "NONE":
                print("  Instrumental — viseme bypass")
            else:
                print("  No layout on section (use PHONEME events for detail)")

        elif result["kind"] == "phoneme":
            phonemes += 1
            t = result["transforms"]
            print(
                f"  PHONEME tick={result.get('tick')} word={result.get('word')!r} "
                f"role={result.get('role')} → [{t['viseme']}] "
                f"jaw_y={t['jaw_translation_y_mm']}mm scale_x={t['mouth_scale_x']}"
            )

    # Safety check baseline pupils
    spacing = solver.evaluate_pupil_safety_clearance([0, 0, 0], [0, 0, 0])
    print("=" * 70)
    print(
        f"[Harness] Done. sections={sections} phonemes={phonemes} "
        f"pupil_spacing={spacing}mm (safe)"
    )
    return True


def seed_mock_meg(path: str) -> None:
    mock = {
        "$schema": "pulseforge.music_event_graph.v2",
        "song_id": "sf-mock-badhabit",
        "title": "BAD HABIT",
        "bpm": 102,
        "timebase": {"initial_bpm": 102, "ticks_per_quarter_note": 960},
        "events": [
            {
                "type": "SECTION_START",
                "name": "Intro",
                "vocal_role": "none",
                "tick": 0,
                "start_sample": 0,
                "end_sample": 176400,
                "lyrics": "",
            },
            {
                "type": "SECTION_START",
                "name": "Verse",
                "vocal_role": "male",
                "tick": 3840,
                "start_sample": 176400,
                "end_sample": 529200,
                "lyrics": "late night same streetlight",
                "viseme_map": {"layout": ["A", "E", "O", "U"]},
            },
            {
                "type": "PHONEME",
                "tick": 3840,
                "sample": 176400,
                "phoneme": "ah",
                "viseme": "A",
                "word": "late",
                "role": "male",
                "note": 54,
            },
            {
                "type": "PHONEME",
                "tick": 4320,
                "sample": 198450,
                "phoneme": "ee",
                "viseme": "E",
                "word": "night",
                "role": "male",
                "note": 57,
            },
            {
                "type": "PHONEME",
                "tick": 4800,
                "sample": 220500,
                "phoneme": "oh",
                "viseme": "O",
                "word": "same",
                "role": "male",
                "note": 59,
            },
            {
                "type": "PHONEME",
                "tick": 5280,
                "sample": 242550,
                "phoneme": "oo",
                "viseme": "U",
                "word": "streetlight",
                "role": "male",
                "note": 61,
            },
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(mock, f, indent=2)
    print(f"[Harness] Seeded mock MEG at {path}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "MusicEventGraph.json"
    if not os.path.exists(target):
        seed_mock_meg(target)
    ok = execute_integration_harness(target)
    sys.exit(0 if ok else 1)
