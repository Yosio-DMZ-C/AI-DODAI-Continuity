#!/usr/bin/env python3
"""AD&C local KB consistency probe. Read-only; stdlib; never prints record content.

This probe does not certify that an AI can resume a task. It checks only observable
local artifacts. Missing/unavailable evidence is NOT_RUN, not a fabricated PASS.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

META_FIELDS = (
    "schema_version", "id", "node_id", "global_id", "title", "kind",
    "status", "revision", "updated_at", "owner", "sensitivity",
    "sharing_scope", "sources", "evidence_basis", "verification",
    "execution_status", "review_due", "scope",
)
RESUME_TAG = re.compile(r"<!--\s*ADNC_CURRENT_RESUME\s*:\s*(.*?)\s*-->", re.I)
JSON_BLOCK = re.compile(r"\x60{3}json\s*(\{.*?\})\s*\x60{3}", re.I | re.S)


def run(root):
    root = Path(root).resolve()
    checks = []

    def record(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    if not root.is_dir():
        record("input", "FAIL", "指定したKBディレクトリを開けない")
        return checks

    required = ["START_HERE.md", "BUILD_PLAN.md", "00_system/registry.json"]
    for path in required:
        record("required:" + path, "PASS" if (root / path).is_file() else "FAIL",
               "実ファイルを確認" if (root / path).is_file() else "必須入口がない")
    rp = root / "00_system/registry.json"
    if not rp.is_file():
        return checks
    try:
        registry = json.loads(rp.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        record("registry_json", "FAIL", "registry.jsonの取得・JSON構文に失敗")
        return checks
    if not isinstance(registry, dict):
        record("registry_json", "FAIL", "registryルートはJSON objectが必要")
        return checks
    record("registry_json", "PASS", "JSON構文を確認")

    groups = [(key, registry[key]) for key in ("records", "nodes", "sources", "control_records")
              if isinstance(registry.get(key), list)]
    if not groups:
        record("entries", "NOT_RUN", "対応する台帳配列を認識できない")
    for group_name, entries in groups:
        seen_ids, seen_paths = set(), set()
        duplicates = 0
        checked_hash, bad_hash, missing_files, revision_checked, rev_bad = 0, 0, 0, 0, 0
        malformed_path, malformed_meta, fields_missing = 0, 0, 0
        for entry in entries:
            if not isinstance(entry, dict):
                malformed_path += 1
                continue
            # Older KBs place record revision under meta.revision.
            # A disagreement between flat and nested forms is itself a defect.
            nested = entry.get("meta")
            nested_revision = nested.get("revision") if isinstance(nested, dict) else None
            flat_revision = entry.get("revision")
            if (flat_revision is not None and nested_revision is not None
                    and str(flat_revision) != str(nested_revision)):
                rev_bad += 1
            expected_revision = (flat_revision if flat_revision is not None
                                 else nested_revision)
            identifier = entry.get("id")
            if identifier:
                if identifier in seen_ids:
                    duplicates += 1
                seen_ids.add(identifier)
            path = entry.get("path")
            if not isinstance(path, str) or not path:
                # Some source-ledger entries refer only to external URLs.
                continue
            relative = PurePosixPath(path.replace("\\", "/"))
            if relative.is_absolute() or ".." in relative.parts or "\x00" in path:
                malformed_path += 1
                continue
            if str(relative) in seen_paths:
                duplicates += 1
            seen_paths.add(str(relative))
            real_path = (root / str(relative)).resolve()
            if not real_path.is_relative_to(root):
                malformed_path += 1
                continue
            if not real_path.is_file():
                missing_files += 1
                continue
            try:
                data = real_path.read_bytes()
            except OSError:
                missing_files += 1
                continue
            digest = entry.get("sha256")
            if isinstance(digest, str) and digest:
                checked_hash += 1
                if hashlib.sha256(data).hexdigest() != digest.lower().removeprefix("sha256:"):
                    bad_hash += 1
            if real_path.suffix.lower() != ".md":
                continue
            try:
                txt = data.decode("utf-8-sig")
            except UnicodeDecodeError:
                malformed_meta += 1
                continue
            block = JSON_BLOCK.search(txt)
            if block:
                try:
                    meta = json.loads(block.group(1))
                except json.JSONDecodeError:
                    malformed_meta += 1
                    continue
                if not isinstance(meta, dict):
                    malformed_meta += 1
                    continue
                if any(k not in meta for k in META_FIELDS):
                    fields_missing += 1
                if expected_revision is not None and meta.get("revision") is not None:
                    revision_checked += 1
                    if str(expected_revision) != str(meta["revision"]):
                        rev_bad += 1
        violations = duplicates + malformed_path + malformed_meta + bad_hash + rev_bad
        record("registry:" + group_name, "FAIL" if violations else "PASS",
               "entries=%d duplicates=%d invalid_paths=%d invalid_meta=%d hash_checked=%d hash_mismatch=%d revision_checked=%d revision_mismatch=%d" %
               (len(entries), duplicates, malformed_path, malformed_meta, checked_hash, bad_hash, revision_checked, rev_bad))
        if missing_files:
            record("files_unavailable:" + group_name, "NOT_RUN",
                   "台帳参照の一部がローカル一式にない: 件数=%d" % missing_files)
        if not revision_checked:
            record("revision_compare:" + group_name, "NOT_RUN",
                   "revisionを台帳と本文の両方に持つ参照がなく比較できない")
        if fields_missing:
            record("required_metadata:" + group_name, "NOT_RUN",
                   "形式・世代を特定できず、正式フィールド不足の判定保留: 件数=%d" % fields_missing)

    plan = root / "BUILD_PLAN.md"
    if plan.is_file():
        try:
            body = plan.read_text(encoding="utf-8-sig")
            markers = RESUME_TAG.findall(body)
            if len(markers) > 1:
                record("resume_marker", "FAIL", "現行再開位置の明示マーカーが複数存在")
            elif len(markers) == 1:
                record("resume_marker", "PASS" if markers[0].strip() else "FAIL",
                       "現行再開位置のマーカーが1件" if markers[0].strip() else "再開位置が空")
            else:
                record("resume_marker", "NOT_RUN",
                       "旧形式には現行再開位置マーカーがない。歴史的な複数見出しを自動矛盾と断定しない")
        except (OSError, UnicodeError):
            record("resume_marker", "NOT_RUN", "BUILD_PLAN本文を読み取れない")
    return checks


def _target_bytes(root, name):
    """Never follow references outside a caller-supplied local KB."""
    relative = PurePosixPath(name.replace("\\", "/"))
    if (not name or relative.is_absolute() or ".." in relative.parts
            or "\x00" in name or relative.as_posix() == "."):
        return "FAIL", None
    target = (root / str(relative)).resolve()
    if not target.is_relative_to(root):
        return "FAIL", None
    try:
        return ("PASS", target.read_bytes()) if target.is_file() else ("NOT_RUN", None)
    except OSError:
        return "NOT_RUN", None


def capture_baseline(root, names):
    """Emit a local pre-edit snapshot; no write or cloud operation."""
    root = Path(root).resolve()
    files, issues = [], []
    for name in names:
        status, data = _target_bytes(root, name)
        if status != "PASS":
            issues.append({"path": name, "status": status})
        else:
            files.append({"path": name, "sha256": hashlib.sha256(data).hexdigest(),
                          "size": len(data)})
    return {"format": "ADNC-BASELINE-1", "files": files, "issues": issues,
            "status": ("FAIL" if any(x["status"] == "FAIL" for x in issues)
                       else "NOT_RUN" if issues else "PASS")}


def verify_baseline(root, baseline):
    """Check previously observed bytes against current local bytes.

    Detects drift only when rechecked. It is NOT a server-side CAS/atomic lock.
    """
    root = Path(root).resolve()
    checks = []
    if (not isinstance(baseline, dict) or baseline.get("format") != "ADNC-BASELINE-1"
            or baseline.get("status") != "PASS" or not isinstance(baseline.get("files"), list)
            or not baseline["files"] or baseline.get("issues")):
        return [{"check": "prewrite", "status": "FAIL", "detail": "無効または部分的な取得基準"}]
    seen = set()
    for item in baseline["files"]:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            return [{"check": "prewrite", "status": "FAIL", "detail": "不正な基準レコード"}]
        name = item["path"]
        if name in seen:
            return [{"check": "prewrite", "status": "FAIL", "detail": "基準内に重複パス"}]
        seen.add(name)
        expected = item.get("sha256")
        size = item.get("size")
        if (not isinstance(expected, str) or not re.fullmatch("[0-9a-f]{64}", expected)
                or type(size) is not int or size < 0):
            return [{"check": "prewrite", "status": "FAIL", "detail": "SHAまたはサイズが不正"}]
        status, data = _target_bytes(root, name)
        if status == "PASS":
            status = ("PASS" if len(data) == size and
                      hashlib.sha256(data).hexdigest() == expected else "FAIL")
        checks.append({"check": "prewrite:" + name, "status": status,
                       "detail": {"PASS": "基準と同一", "FAIL": "基準から変更・パス不正",
                                  "NOT_RUN": "対象の実バイトを取得できない"}[status]})
    return checks


def main():
    ap = argparse.ArgumentParser(description="Read-only AD&C KB consistency probe")
    ap.add_argument("root", help="ローカルに取得済みのKBルート（クラウドへ直接接続しません）")
    ap.add_argument("--snapshot", nargs="+", metavar="REL_PATH",
                    help="変更前の対象ファイルSHA・サイズを標準出力へ表示（非書込）")
    ap.add_argument("--expect", metavar="BASELINE_JSON",
                    help="書込直前の取得バイトを基準JSONと比較（サーバー排他ではない）")
    args = ap.parse_args()
    if args.snapshot and args.expect:
        ap.error("--snapshot と --expect は同時に使用できません")
    if args.snapshot:
        snapshot = capture_baseline(args.root, args.snapshot)
        print(json.dumps(snapshot, ensure_ascii=False, indent=2))
        raise SystemExit({"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[snapshot["status"]])
    if args.expect:
        try:
            baseline = json.loads(Path(args.expect).read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            baseline = None
        checks = verify_baseline(args.root, baseline)
    else:
        checks = run(args.root)
    outcome = "FAIL" if any(x["status"] == "FAIL" for x in checks) else (
        "NOT_RUN" if any(x["status"] == "NOT_RUN" for x in checks) else "PASS")
    print(json.dumps({"overall": outcome, "checks": checks}, ensure_ascii=False, indent=2))
    raise SystemExit({"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[outcome])


if __name__ == "__main__":
    main()
