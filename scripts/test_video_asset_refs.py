"""Synthetic tests for read-only video Context registry ID validation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from check_video_asset_refs import validate


def doc(asset_id="X-LOGO", reference="X-PPT"):
    return f"""# Example
```yaml
reference_ppt:
  asset_id: "{reference}"
assets:
  - id: "{asset_id}"
    label: "Friendly display name"
    role: "logo"
```
"""


class AssetReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "assets").mkdir()
        (self.root / "assets" / "ppt.txt").write_text("PPT bytes")
        (self.root / "assets" / "logo.txt").write_text("LOGO bytes")
        self.reg = {"records": [
            {"id": "X-PPT", "fileId": "opaque-file-id-1",
             "path": "assets/ppt.txt",
             "sha256": hashlib.sha256(b"PPT bytes").hexdigest()},
            {"id": "X-LOGO", "fileId": "opaque-file-id-2",
             "path": "assets/logo.txt",
             "sha256": hashlib.sha256(b"LOGO bytes").hexdigest()}
        ]}

    def states(self, src=None, root=None):
        return {x["check"]: x["status"]
                for x in validate(self.reg, src if src is not None else doc(), root)}

    def test_ids_and_all_bytes_pass(self):
        self.assertEqual(set(self.states(root=self.root).values()), {"PASS"})

    def test_display_label_in_id_fails(self):
        self.assertEqual(self.states(doc("official logo (pretty name)"))[
                         "context_registry_resolution"], "FAIL")

    def test_unsupported_id_fails(self):
        self.assertEqual(self.states(doc("NOT-REGISTERED"))[
                         "context_registry_resolution"], "FAIL")

    def test_duplicate_reference_fails(self):
        self.assertEqual(self.states(doc("X-PPT"))[
                         "context_registry_resolution"], "FAIL")

    def test_no_local_bytes_not_run(self):
        self.assertEqual(self.states()["asset_bytes"], "NOT_RUN")

    def test_missing_local_asset_not_run(self):
        (self.root / "assets" / "logo.txt").unlink()
        self.assertEqual(self.states(root=self.root)["asset_bytes"], "NOT_RUN")

    def test_changed_asset_bytes_fail(self):
        (self.root / "assets" / "logo.txt").write_text("changed")
        self.assertEqual(self.states(root=self.root)["asset_bytes"], "FAIL")

    def test_unparsed_list_fails_closed(self):
        broken = doc().replace('  - id: "X-LOGO"', '  - label: "Friendly"')
        self.assertEqual(self.states(broken)["context_shape"], "FAIL")

    def test_registry_duplicate_id_fails(self):
        self.reg["records"].append(dict(self.reg["records"][0]))
        self.assertEqual(self.states()["registry_unique_ids"], "FAIL")

    def test_missing_file_id_fails(self):
        self.reg["records"][1].pop("fileId")
        self.assertEqual(self.states()["context_registry_resolution"], "FAIL")

    def test_path_escape_fails(self):
        self.reg["records"][1]["path"] = "../sensitive.txt"
        self.assertEqual(self.states()["context_registry_resolution"], "FAIL")


if __name__ == "__main__":
    unittest.main()
