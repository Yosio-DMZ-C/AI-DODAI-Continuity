#!/usr/bin/env python3
"""T017 independent reviewer: compare three local approved PNGs to registry.json.

Read-only. No Drive API, no writes, no image regeneration.
Usage: python scripts/verify_t017_character_assets.py registry.json 01.png 02.png 03.png
Exit 0 only if all three sha256 values match the registry. The reviewer must
download the PNGs independently, and record the download source and timestamp.
This script alone is NOT Q2 independent acceptance.
"""
import hashlib
import json
import pathlib
import sys

IDS = ("VID-CHAR-01", "VID-CHAR-02", "VID-CHAR-03")
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def main(argv):
    if len(argv) != 5:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    registry = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    records = registry.get("records", [])
    passed = True
    for asset_id, filename in zip(IDS, argv[2:]):
        matches = [r for r in records if r.get("id") == asset_id]
        if len(matches) != 1:
            print(f"{asset_id}: FAIL registry record count={len(matches)}")
            passed = False
            continue
        record = matches[0]
        expected = record.get("sha256", "").lower()
        if len(expected) != 64 or any(c not in "0123456789abcdef" for c in expected):
            print(f"{asset_id}: NOT_RUN registry SHA-256 missing or malformed")
            passed = False
            continue
        data = pathlib.Path(filename).read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        png_ok = data.startswith(PNG_MAGIC)
        ok = png_ok and actual == expected
        print(f"{asset_id}: {'PASS' if ok else 'FAIL'} bytes={len(data)} "
              f"png={png_ok} sha256={actual} expected={expected} "
              f"registry_fileId={record.get('fileId', 'MISSING')}")
        passed &= ok
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
