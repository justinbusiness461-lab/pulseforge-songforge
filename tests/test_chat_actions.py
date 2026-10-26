#!/usr/bin/env python3
"""Chat-studio actions: generate/vary/extend/remix determinism (Python mirror)."""
from __future__ import annotations
import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import song_compiler as sc

PROMPT = "dark 102 BPM alt hip-hop, F# minor, guitar plucks, male verse, female chorus"

class ChatActions(unittest.TestCase):
    def test_generate_stable(self):
        a = sc.parse_prompt(PROMPT, {"nonce": "0"})
        b = sc.parse_prompt(PROMPT, {"nonce": "0"})
        self.assertEqual(sc.identity_fingerprint(a), sc.identity_fingerprint(b))
        self.assertEqual(a["schema_version"], "2.20.0")

    def test_vary_changes_seed(self):
        a = sc.parse_prompt(PROMPT, {"nonce": "0"})
        b = sc.parse_prompt(PROMPT, {"nonce": "vary-1"})
        self.assertNotEqual(a["generation_seed"], b["generation_seed"])
        self.assertNotEqual(a["song_id"], b["song_id"])

    def test_extend_appends_section_and_events(self):
        base = sc.parse_prompt(PROMPT, {"nonce": "0"})
        n_sec = len(base["structure"]["sections"])
        n_events = sum(len(t["events"]) for t in base["tracks"])
        ext = sc.extend_arrangement(base, lyrics="keep going keep going")
        self.assertEqual(len(ext["structure"]["sections"]), n_sec + 1)
        self.assertGreater(sum(len(t["events"]) for t in ext["tracks"]), n_events)
        self.assertTrue(any(e.get("op") == "extend_arrangement" for e in ext["change_ledger"]))
        last = ext["structure"]["sections"][-1]
        self.assertGreater(last["end_tick"], last["start_tick"])
        self.assertEqual(last["start_tick"] % 1, 0)

    def test_remix_preserves_lyrics_changes_seed(self):
        base = sc.parse_prompt(PROMPT, {"nonce": "0"})
        # stamp custom lyrics
        for sec in base["structure"]["sections"]:
            if sec.get("role") != "none":
                sec["lyrics"] = "custom line one"
        rem = sc.remix_arrangement(base, nonce="remix-1")
        self.assertNotEqual(rem["generation_seed"], base["generation_seed"])
        matched = False
        for a, b in zip(base["structure"]["sections"], rem["structure"]["sections"]):
            if a.get("role") != "none":
                self.assertEqual(b.get("lyrics"), "custom line one")
                matched = True
        self.assertTrue(matched)

if __name__ == "__main__":
    unittest.main()
