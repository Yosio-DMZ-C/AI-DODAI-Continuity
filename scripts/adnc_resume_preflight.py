#!/usr/bin/env python3
"""AD&C beta: read-only work-state preflight (no cloud/API calls).

Prepare a temporary JSON from existing START_HERE / Project Context / BUILD_PLAN:
{
  "artifact_id": "episode-1", "adopted_version": "v1.5",
  "inputs": ["01", "02", "03", "04"], "requested": ["02", "04"],
  "preview_limit": 3, "paid_action": true,
  "same_failed_approach_count": 0,
  "required_assets": [
    {"role": "logo", "path": "staged-logo.png", "sha256": "<64 hex chars>"}
  ]
}

Run: python scripts/adnc_resume_preflight.py work-state.json --root fetched-files
Test: python scripts/adnc_resume_preflight.py --self-test

The script checks only bytes actually fetched into the local staging folder.
Cloud links without downloaded bytes remain NOT_RUN, never assumed absent.
This does not perform edits, API calls, payment, or external delivery.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest


def preflight(state, root):
    """Check explicit work state and derive only the needed work stages."""
    report = {"status": "PASS", "flow": "RESEARCH", "issues": [],
              "preview": [], "remainder": [], "execution_ready": False,
              "approval_required": False, "checkpoint": False}
    failures, unknowns = [], []
    if not isinstance(state, dict):
        return {**report, "status": "FAIL", "issues": ["state must be an object"]}
    items = state.get("inputs", [])
    chosen = state.get("requested", [])
    assets = state.get("required_assets", [])
    preview_limit = state.get("preview_limit", 0)
    attempts = state.get("same_failed_approach_count", 0)
    max_items = state.get("max_items")
    if (not isinstance(items, list) or not isinstance(chosen, list)
            or not isinstance(assets, list)
            or any(not isinstance(x, str) or not x for x in items + chosen)
            or len(set(items)) != len(items) or len(set(chosen)) != len(chosen)
            or not isinstance(preview_limit, int) or isinstance(preview_limit, bool)
            or preview_limit < 0 or not isinstance(attempts, int)
            or isinstance(attempts, bool) or attempts < 0
            or (max_items is not None and (
                not isinstance(max_items, int) or isinstance(max_items, bool)
                or max_items < 1))):
        failures.append("invalid or duplicate input/target/limit/counter")
    elif max_items is not None and len(items) > max_items:
        failures.append("input exceeds the explicit operational limit")
    elif not set(chosen).issubset(set(items)):
        failures.append("requested ID not found in current inputs")
    else:
        report["preview"] = chosen[:preview_limit]
        report["remainder"] = chosen[preview_limit:]
    report["checkpoint"] = attempts >= 2 if isinstance(attempts, int) else False
    report["approval_required"] = bool(chosen) and state.get("paid_action", False) is True
    if state.get("reconsider_adopted") is True:
        report["flow"] = "RESEARCH"
    elif state.get("artifact_id") and state.get("adopted_version"):
        report["flow"] = "RESTORE"
    else:
        report["flow"] = "RESEARCH"
    if chosen and report["flow"] == "RESTORE" and not assets:
        unknowns.append("required asset set not supplied")
    seen_roles = set()
    root = Path(root).resolve()
    if not failures and chosen and report["flow"] == "RESTORE":
        for asset in assets:
            if not isinstance(asset, dict):
                failures.append("invalid asset record")
                continue
            role = asset.get("role")
            if not isinstance(role, str) or not role or role in seen_roles:
                failures.append("asset role missing or duplicated")
                continue
            seen_roles.add(role)
            rel, digest = asset.get("path"), asset.get("sha256")
            if not isinstance(rel, str) or not rel:
                unknowns.append(role + ": no locally fetched artifact; remote reference is not proof")
                continue
            p = (root / rel).resolve()
            if p == root or root not in p.parents:
                failures.append(role + ": path escapes staging root")
            elif not p.is_file():
                unknowns.append(role + ": artifact not fetched; absence is not deletion evidence")
            elif not isinstance(digest, str) or len(digest) != 64 or any(
                    c not in "0123456789abcdefABCDEF" for c in digest):
                unknowns.append(role + ": no usable expected SHA-256")
            elif hashlib.sha256(p.read_bytes()).hexdigest() != digest.lower():
                failures.append(role + ": SHA-256 mismatch")
    if failures:
        report["status"] = "FAIL"
    elif unknowns:
        report["status"] = "NOT_RUN"
        if report["flow"] == "RESTORE":
            report["flow"] = "REPAIR_REFS"
    report["issues"] = failures + unknowns
    report["execution_ready"] = (report["status"] == "PASS"
                                  and report["flow"] == "RESTORE"
                                  and bool(chosen) and not report["checkpoint"])
    # Readiness never authorizes paid calls, publishing, deletion or external sending.
    return report


class SelfTest(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "logo.bin").write_bytes(b"fixed asset")
        self.base = {
            "artifact_id": "episode-1", "adopted_version": "v1.5",
            "inputs": [str(i) for i in range(1, 16)],
            "requested": ["2", "4", "6", "8"],
            "preview_limit": 3, "paid_action": True,
            "required_assets": [{
                "role": "logo", "path": "logo.bin",
                "sha256": hashlib.sha256(b"fixed asset").hexdigest()}]}

    def check_count(self, n):
        s = {**self.base, "requested": self.base["inputs"][:n]}
        r = preflight(s, self.root)
        self.assertEqual(r["status"], "PASS")
        self.assertEqual((len(r["preview"]), len(r["remainder"])),
                         (min(n, 3), max(n-3, 0)))
        self.assertEqual(r["execution_ready"], n > 0)
        self.assertEqual(r["approval_required"], n > 0)

    def test_zero(self): self.check_count(0)
    def test_one(self): self.check_count(1)
    def test_two(self): self.check_count(2)
    def test_three(self): self.check_count(3)
    def test_four(self): self.check_count(4)
    def test_fifteen(self): self.check_count(15)

    def test_missing_asset_is_unknown(self):
        s = {**self.base, "required_assets": [{"role": "kit", "uri": "drive:opaque"}]}
        r = preflight(s, self.root)
        self.assertEqual((r["status"], r["flow"]), ("NOT_RUN", "REPAIR_REFS"))
        self.assertFalse(r["execution_ready"])

    def test_bad_hash_fails(self):
        s = {**self.base, "required_assets": [
            {**self.base["required_assets"][0], "sha256": "0"*64}]}
        self.assertEqual(preflight(s, self.root)["status"], "FAIL")

    def test_bad_target_fails(self):
        self.assertEqual(preflight({**self.base, "requested": ["999"]}, self.root)["status"], "FAIL")

    def test_duplicate_input_fails(self):
        self.assertEqual(preflight({**self.base, "inputs": ["1", "1"]}, self.root)["status"], "FAIL")

    def test_path_escape_fails(self):
        s = {**self.base, "required_assets": [
            {**self.base["required_assets"][0], "path": "../outside"}]}
        self.assertEqual(preflight(s, self.root)["status"], "FAIL")

    def test_two_failures_trigger_checkpoint(self):
        r = preflight({**self.base, "same_failed_approach_count": 2}, self.root)
        self.assertTrue(r["checkpoint"])
        self.assertFalse(r["execution_ready"])

    def test_reconsider_is_not_autorestore(self):
        r = preflight({**self.base, "reconsider_adopted": True}, self.root)
        self.assertEqual(r["flow"], "RESEARCH")
        self.assertFalse(r["execution_ready"])

    def test_explicit_limit(self):
        s = {**self.base, "max_items": 4}
        self.assertEqual(preflight(s, self.root)["status"], "FAIL")

    def test_no_implicit_remote_verification(self):
        s = {**self.base, "required_assets": [{"role": "audio", "path": "missing.zip",
                                               "sha256": "0"*64}]}
        self.assertEqual(preflight(s, self.root)["status"], "NOT_RUN")


def main():
    if "--self-test" in sys.argv:
        argv = [sys.argv[0]]
        unittest.main(argv=argv)
        return
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("state", type=Path, help="local JSON assembled from existing project records")
    p.add_argument("--root", type=Path, help="local staging area for actually fetched assets")
    args = p.parse_args()
    try:
        state = json.loads(args.state.read_text(encoding="utf-8-sig"))
        result = preflight(state, args.root or args.state.parent)
    except (ValueError, OSError) as exc:
        result = {"status": "FAIL", "issues": [type(exc).__name__], "execution_ready": False}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit({"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[result["status"]])


if __name__ == "__main__":
    main()
