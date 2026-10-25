#!/usr/bin/env python3
"""Read-only AD&C video Context -> registry asset reference validator.

Usage:
    python scripts/check_video_asset_refs.py registry.json A-VIDEO.md
    python scripts/check_video_asset_refs.py registry.json A-VIDEO.md --root /path/to/KB

No cloud calls, writes, or private data in output. A correct registry ID is not
proof that remote bytes are fetchable or that a person approved the artwork.
Exit codes: PASS=0, FAIL=1, NOT_RUN=2.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath

FENCE = re.compile(r"(?m)^```ya?ml\s*\n(.*?)^```\s*$", re.S)
FIELD = re.compile(r'^\s*([A-Za-z_][A-Za-z_0-9]*):\s*(.*?)\s*$')
ID = re.compile(r'^([A-Za-z0-9][A-Za-z0-9_.-]*)$')


def scalar(value):
    """Read a YAML scalar ID (not a general YAML parser)."""
    value = value.strip()
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        value = value[1:-1]
    return value


def context_ids(body):
    """Extract reference_ppt.asset_id and all assets[].id entries.

    Reject unsupported inline/multiline assets to avoid silently passing an
    unrecognized schema. This intentionally supports the existing Context shape.
    """
    match = FENCE.search(body)
    if not match:
        return [], ["YAML block not found"]
    section, refs, errors = None, [], []
    asset_rows = 0
    for line in match.group(1).splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.endswith(":"):
            section = line[:-1].strip()
            continue
        if not line.startswith(" ") and ":" in line:
            section = None
        if section == "reference_ppt":
            found = FIELD.match(line)
            if found and found.group(1) == "asset_id":
                refs.append(("reference_ppt.asset_id", scalar(found.group(2))))
        elif section == "assets":
            if re.match(r"^\s+-\s+", line):
                asset_rows += 1
                m = re.match(r"^\s+-\s+id:\s*(.*?)\s*$", line)
                if m:
                    refs.append((f"assets[{asset_rows - 1}].id", scalar(m.group(1))))
                else:
                    errors.append("asset list row has no direct id")
    if not any(k == "reference_ppt.asset_id" for k, _ in refs):
        errors.append("reference_ppt.asset_id missing")
    if asset_rows == 0:
        errors.append("assets list is empty or unsupported")
    if sum(k.startswith("assets[") for k, _ in refs) != asset_rows:
        errors.append("assets list contains unresolved rows")
    return refs, errors


def validate(registry, context, root=None):
    checks = []
    def add(key, status, description):
        checks.append({"check": key, "status": status, "detail": description})
    if not isinstance(registry, dict) or not isinstance(registry.get("records"), list):
        return [{"check": "registry", "status": "FAIL", "detail": "records array missing"}]
    index = {}
    duplicate = set()
    for entry in registry["records"]:
        if isinstance(entry, dict) and isinstance(entry.get("id"), str):
            rid = entry["id"]
            if rid in index:
                duplicate.add(rid)
            index[rid] = entry
    if duplicate:
        add("registry_unique_ids", "FAIL", "duplicate registry IDs")
        return checks
    add("registry_unique_ids", "PASS", "registry IDs unique")
    refs, errors = context_ids(context)
    if errors:
        add("context_shape", "FAIL", "; ".join(sorted(set(errors))))
    else:
        add("context_shape", "PASS", "supported reference shape")
    seen = set()
    valid = []
    invalid = 0
    for where, rid in refs:
        if not ID.fullmatch(rid) or rid not in index or rid in seen:
            invalid += 1
            continue
        seen.add(rid)
        entry = index[rid]
        path = entry.get("path")
        file_id = entry.get("fileId")
        if not isinstance(path, str) or not path or not isinstance(file_id, str) or not file_id:
            invalid += 1
            continue
        rel = PurePosixPath(path.replace("\\", "/"))
        if rel.is_absolute() or ".." in rel.parts or "\x00" in path:
            invalid += 1
            continue
        valid.append((entry, str(rel)))
    add("context_registry_resolution", "FAIL" if invalid else "PASS",
        f"references={len(refs)} resolved={len(valid)} invalid_or_duplicate={invalid}")
    if not refs:
        add("asset_bytes", "NOT_RUN", "no asset references resolved")
    elif root is None:
        add("asset_bytes", "NOT_RUN", "local original bytes not provided; remote access not tested")
    else:
        base = Path(root).resolve()
        matched, unavailable, mismatch, unchecked = 0, 0, 0, 0
        for entry, rel in valid:
            target = (base / rel).resolve()
            if not target.is_relative_to(base):
                mismatch += 1
                continue
            try:
                data = target.read_bytes() if target.is_file() else None
            except OSError:
                data = None
            if data is None:
                unavailable += 1
            else:
                expected = entry.get("sha256")
                if not isinstance(expected, str) or not re.fullmatch(
                        r"(?:sha256:)?[0-9a-fA-F]{64}", expected):
                    unchecked += 1
                elif hashlib.sha256(data).hexdigest() != expected.lower().removeprefix("sha256:"):
                    mismatch += 1
                else:
                    matched += 1
        add("asset_bytes", ("FAIL" if mismatch else
                            "NOT_RUN" if unavailable or unchecked or len(valid) != len(refs)
                            else "PASS"),
            f"sha_matched={matched} mismatch={mismatch} unavailable={unavailable} no_sha={unchecked}")
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("registry", type=Path)
    parser.add_argument("context", type=Path)
    parser.add_argument("--root", type=Path, help="downloaded local KB tree (optional)")
    args = parser.parse_args()
    try:
        registry = json.loads(args.registry.read_text(encoding="utf-8-sig"))
        context = args.context.read_text(encoding="utf-8-sig")
        checks = validate(registry, context, args.root)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        checks = [{"check": "input", "status": "NOT_RUN",
                   "detail": "input missing, unreadable, or invalid"}]
    overall = ("FAIL" if any(c["status"] == "FAIL" for c in checks) else
               "NOT_RUN" if any(c["status"] == "NOT_RUN" for c in checks) else "PASS")
    print(json.dumps({"overall": overall, "checks": checks}, ensure_ascii=False, indent=2))
    raise SystemExit({"PASS": 0, "FAIL": 1, "NOT_RUN": 2}[overall])


if __name__ == "__main__":
    main()
