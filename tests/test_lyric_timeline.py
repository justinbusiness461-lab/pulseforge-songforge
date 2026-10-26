import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from lyric_timeline import LyricStore, validate_range


class LyricTimeline(unittest.TestCase):
    def setUp(self):
        meta = json.loads((ROOT / "fixtures/lyrics/hello_higher_world.json").read_text())
        self.meta = meta
        self.digest = meta["sourceAudioDigest"]
        self.sr = meta["sourceSampleRate"]
        self.frames = meta["decodedFrameCount"]

    def test_r1_r2_correction_and_reopen(self):
        with tempfile.TemporaryDirectory() as td:
            store = LyricStore(Path(td))
            words = []
            for i, w in enumerate(self.meta["words_ground_truth"]):
                text = "fire" if i == 1 else w["text"]
                words.append(
                    {
                        "text": text,
                        "decodedSampleStart": w["start"],
                        "decodedSampleEnd": w["end"],
                        "confidence": 0.72,
                    }
                )
            r1 = store.create_machine_r1(
                "prj-lyric",
                source_audio_digest=self.digest,
                source_sample_rate=self.sr,
                frame_count=self.frames,
                words=words,
                alignment_model_or_method="fixture_aligner_v0",
            )
            self.assertIsNone(r1["parentRevisionId"])
            self.assertEqual(r1["words"][1]["text"], "fire")
            r2 = store.correct_word(
                "prj-lyric",
                parent_revision_id=r1["revisionId"],
                word_index=1,
                new_text="higher",
            )
            self.assertEqual(r2["parentRevisionId"], r1["revisionId"])
            self.assertEqual(r2["words"][1]["text"], "higher")
            self.assertEqual(r2["sourceAudioDigest"], self.digest)
            still = store.get("prj-lyric", r1["revisionId"])
            self.assertEqual(still["words"][1]["text"], "fire")
            store2 = LyricStore(Path(td))
            cur = store2.get("prj-lyric", r2["revisionId"])
            self.assertEqual(cur["words"][1]["text"], "higher")
            hist = store2.get("prj-lyric", r1["revisionId"])
            self.assertEqual(hist["words"][1]["text"], "fire")

    def test_instrumental_no_hallucination(self):
        with tempfile.TemporaryDirectory() as td:
            store = LyricStore(Path(td))
            r1 = store.instrumental_r1(
                "prj-inst",
                source_audio_digest="a" * 64,
                source_sample_rate=44100,
                frame_count=44100,
            )
            self.assertEqual(r1["words"], [])
            self.assertEqual(r1["status"], "no_vocal_detected")
            self.assertLessEqual(float(r1["confidence"]), 0.0)

    def test_invalid_range_rejected(self):
        with self.assertRaises(ValueError):
            validate_range(10, 10, 100)
        with self.assertRaises(ValueError):
            validate_range(-1, 5, 100)
        with self.assertRaises(ValueError):
            validate_range(0, 101, 100)

    def test_wrong_digest_rejected(self):
        from lyric_timeline import validate_timeline

        words = [
            {
                "text": "x",
                "decodedSampleStart": 0,
                "decodedSampleEnd": 10,
                "confidence": 0.9,
            }
        ]
        doc = {
            "sourceAudioDigest": "c" * 64,
            "sourceSampleRate": 44100,
            "alignmentModelOrMethod": "m",
            "words": words,
            "phrases": [],
        }
        with self.assertRaises(ValueError):
            validate_timeline(doc, frame_count=100, source_digest="d" * 64)


if __name__ == "__main__":
    unittest.main()
