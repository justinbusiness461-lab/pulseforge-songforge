import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from project_authority import ProjectStore


class ProjectAuthority(unittest.TestCase):
    def test_r1_r2_reopen_without_cache(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStore(Path(td) / "projects")
            created = store.create_project("prj-demo")
            r1 = created["revision"]["revisionId"]
            self.assertEqual(created["manifest"]["currentRevisionId"], r1)

            song_r2 = {"sections": [{"name": "verse", "transpose": 0}]}
            timeline_r2 = {"clips": [{"section": "verse"}]}
            committed = store.commit_revision(
                "prj-demo",
                expected_current_revision_id=r1,
                parent_revision_id=r1,
                song_spec=song_r2,
                production_timeline=timeline_r2,
                output_artifact_ids=["art-wav-r2"],
            )
            r2 = committed["revision"]["revisionId"]
            self.assertEqual(committed["manifest"]["currentRevisionId"], r2)
            self.assertEqual(committed["revision"]["parentRevisionId"], r1)

            store2 = ProjectStore(Path(td) / "projects")
            opened = store2.reopen("prj-demo")
            self.assertEqual(opened["manifest"]["currentRevisionId"], r2)
            self.assertEqual(opened["revision"]["revisionId"], r2)
            self.assertEqual(opened["revision"]["outputArtifactIds"], ["art-wav-r2"])
            self.assertEqual(opened["browserCacheRole"], "ignored")

            old = store2.get_revision("prj-demo", r1)
            self.assertEqual(old["revisionId"], r1)

    def test_stale_r1_cannot_overwrite_r2(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStore(Path(td) / "projects")
            created = store.create_project("prj-cas")
            r1 = created["revision"]["revisionId"]
            committed = store.commit_revision(
                "prj-cas",
                expected_current_revision_id=r1,
                parent_revision_id=r1,
                song_spec={"v": 2},
            )
            r2 = committed["revision"]["revisionId"]
            with self.assertRaises(ValueError) as ctx:
                store.commit_revision(
                    "prj-cas",
                    expected_current_revision_id=r1,
                    parent_revision_id=r1,
                    song_spec={"v": "evil"},
                )
            self.assertIn("stale_revision", str(ctx.exception))
            self.assertEqual(store.get_manifest("prj-cas")["currentRevisionId"], r2)

    def test_bind_output_tip_only(self):
        with tempfile.TemporaryDirectory() as td:
            store = ProjectStore(Path(td) / "projects")
            created = store.create_project("prj-bind")
            r1 = created["revision"]["revisionId"]
            committed = store.commit_revision(
                "prj-bind",
                expected_current_revision_id=r1,
                parent_revision_id=r1,
                song_spec={"a": 1},
            )
            r2 = committed["revision"]["revisionId"]
            with self.assertRaises(ValueError):
                store.bind_output("prj-bind", r1, "art-old")
            rev = store.bind_output(
                "prj-bind", r2, "art-new", expected_current_revision_id=r2
            )
            self.assertIn("art-new", rev["outputArtifactIds"])


if __name__ == "__main__":
    unittest.main()
