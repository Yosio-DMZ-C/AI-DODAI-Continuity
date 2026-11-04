#!/usr/bin/env python3
"""T007 conservative next-action navigator for Issue #13.

Read-only; requires explicit approval evidence before suggesting execution.
Prints candidates for leader review, never marks a task DONE or writes to GitHub.
Usage: python scripts/t007_next_action_guard.py issue13.md
       python scripts/t007_next_action_guard.py --self-test
"""
import pathlib
import re
import sys

ROW = re.compile(r"^\|\s*(ADNC-T\d{3})\s*\|(.+)$", re.M)
UNSAFE = ("BLOCKED", "REVIEW_PENDING", "PROPOSED", "DONE", "DROPPED")
DECISION = ("本人", "承認待ち", "正式企画", "判断待ち", "別AI", "実受領未確認")


def candidates(body):
    """Fail closed on duplicate IDs or malformed/ambiguous statuses."""
    found = {}
    for match in ROW.finditer(body):
        task_id = match.group(1)
        cells = [x.strip().replace("**", "") for x in match.group(2).split("|")]
        # Issue #13 contains a compact live table and a historical detail table.
        # Only the live table has priority (P0/P1/P2) in column 2.
        if len(cells) < 4 or not re.match(r"^P[0-2](?:\b|（)", cells[0]):
            continue
        if not re.match(r"^(?:IN_PROGRESS|BLOCKED|REVIEW_PENDING|PROPOSED|DONE|DROPPED)(?:$|[（( ])", cells[1]):
            continue  # historical detail row, not a live status
        if task_id in found:
            raise ValueError(f"duplicate live task: {task_id}")
        status, owner, summary = cells[1:4]
        found[task_id] = (status, owner, summary)
    if not found:
        raise ValueError("no live task rows: refuse to recommend")
    out = []
    for task_id, (status, owner, summary) in found.items():
        if not status.startswith("IN_PROGRESS") or any(x in status for x in UNSAFE):
            continue
        if any(x in owner + summary for x in DECISION):
            continue
        out.append((task_id, summary))
    return sorted(out)


def self_test():
    def row(i, status, owner="開発リーダー", summary="検査"):
        return f"| {i} | P1 | **{status}** | {owner} | {summary} |"
    sample = "\n".join([
        row("ADNC-T001", "DONE"),
        row("ADNC-T002", "BLOCKED"),
        row("ADNC-T003", "REVIEW_PENDING"),
        row("ADNC-T004", "PROPOSED"),
        row("ADNC-T005", "IN_PROGRESS"),
        row("ADNC-T006", "IN_PROGRESS", summary="本人判断待ち"),
        row("ADNC-T007", "IN_PROGRESS", owner="別AI"),
        "| ADNC-T005 | P1 | historical detail | not a live row |",
    ])
    assert candidates(sample) == [("ADNC-T005", "検査")]
    for bad in ("", row("ADNC-T001", "IN_PROGRESS") + "\n" + row("ADNC-T001", "IN_PROGRESS")):
        try:
            candidates(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("must fail closed")
    print("SELF_TEST_PASS: safe status, decision gate, historical rows, duplicates, missing table")


def main(args):
    if len(args) == 2 and args[1] == "--self-test":
        self_test()
        return 0
    if len(args) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    try:
        result = candidates(pathlib.Path(args[1]).read_text(encoding="utf-8-sig"))
    except (ValueError, OSError) as exc:
        print(f"NOT_RUN: {exc}", file=sys.stderr)
        return 1
    if not result:
        print("NO_SAFE_CANDIDATE: human leader review required")
        return 0
    for task_id, summary in result:
        print(f"REVIEW_ONLY {task_id}: {summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
