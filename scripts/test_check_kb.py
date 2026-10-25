"""Tests for the read-only AD&C KB probe; run: python -m unittest discover -s scripts -p 'test_check_kb.py'."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from check_kb import META_FIELDS, run


class KBProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "00_system").mkdir()
        (self.root / "START_HERE.md").write_text("ADNC_INSTALLER_VERSION: 1.5.2\n")
        (self.root / "BUILD_PLAN.md").write_text("<!-- ADNC_CURRENT_RESUME: resume step B -->\n")
        meta = dict.fromkeys(META_FIELDS)
        meta["revision"] = 1
        self.doc = self.root / "record.md"
        self.doc.write_text("\x60\x60\x60json\n" + json.dumps(meta) + "\n\x60\x60\x60\n")
        self.entry = {"id": "REC1", "path": "record.md", "revision": 1,
                      "sha256": hashlib.sha256(self.doc.read_bytes()).hexdigest()}
        self.save_registry()

    def save_registry(self, entries=None):
        (self.root / "00_system" / "registry.json").write_text(
            json.dumps({"records": [self.entry] if entries is None else entries})
        )

    def states(self):
        return {x["check"]: x["status"] for x in run(self.root)}

    def test_fully_matched_is_pass(self):
        self.assertTrue(all(x == "PASS" for x in self.states().values()))

    def test_missing_entry_not_pass(self):
        (self.root / "START_HERE.md").unlink()
        self.assertEqual(self.states()["required:START_HERE.md"], "FAIL")

    def test_id_duplicate(self):
        self.save_registry([self.entry, self.entry])
        self.assertEqual(self.states()["registry:records"], "FAIL")

    def test_sha_mismatch(self):
        self.doc.write_text("changed without registry sync")
        self.assertEqual(self.states()["registry:records"], "FAIL")

    def test_revision_mismatch(self):
        self.entry["revision"] = 5
        self.save_registry()
        self.assertEqual(self.states()["registry:records"], "FAIL")

    def test_nested_meta_revision_match(self):
        self.entry.pop("revision")
        self.entry["meta"] = {"revision": 1}
        self.save_registry()
        self.assertEqual(self.states()["registry:records"], "PASS")
        self.assertEqual(self.states().get("revision_compare:records"), None)

    def test_nested_meta_revision_mismatch(self):
        self.entry.pop("revision")
        self.entry["meta"] = {"revision": 9}
        self.save_registry()
        self.assertEqual(self.states()["registry:records"], "FAIL")

    def test_flat_nested_revision_conflict(self):
        self.entry["meta"] = {"revision": 7}
        self.save_registry()
        self.assertEqual(self.states()["registry:records"], "FAIL")

    def test_unavailable_partial_export(self):
        self.doc.unlink()
        self.assertEqual(self.states()["files_unavailable:records"], "NOT_RUN")

    def test_history_is_not_false_failure(self):
        (self.root / "BUILD_PLAN.md").write_text(
            "## 次回の再開位置\nhistorical A\n## 次回の再開位置\nhistorical B\n"
        )
        self.assertEqual(self.states()["resume_marker"], "NOT_RUN")

    def test_two_canonical_resume_markers_fail(self):
        (self.root / "BUILD_PLAN.md").write_text(
            "<!-- ADNC_CURRENT_RESUME: A -->\n<!-- ADNC_CURRENT_RESUME: B -->\n"
        )
        self.assertEqual(self.states()["resume_marker"], "FAIL")

    def test_path_traversal_is_rejected(self):
        self.entry["path"] = "../../outside.md"
        self.save_registry()
        self.assertEqual(self.states()["registry:records"], "FAIL")


if __name__ == "__main__":
    unittest.main()
