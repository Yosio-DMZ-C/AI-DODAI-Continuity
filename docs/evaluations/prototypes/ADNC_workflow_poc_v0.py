#!/usr/bin/env python3
"""AD&C research-only: one declarative plan -> Japanese guide + sandbox execution.
No network or production writes. Python stdlib only.
"""
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Op:
    title: str
    guide: str
    handler: object


def inside(root, rel):
    p = Path(rel)
    if p.is_absolute() or not p.parts or ".." in p.parts:
        raise ValueError("Unsafe path")
    target = (root / p).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError("Path escaped sandbox")
    return target


def snapshot(root, args):
    data = inside(root, args["source"]).read_bytes()
    json.loads(data)
    inside(root, args["baseline"]).write_bytes(data)
    return "入力JSONを別ファイルに保全"


def patch(root, args):
    doc = json.loads(inside(root, args["baseline"]).read_text(encoding="utf-8"))
    doc["status"] = "reviewed"
    inside(root, args["output"]).write_text(
        json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return "原本には触れず別名JSONを生成"


def verify(root, args):
    original = json.loads(inside(root, args["source"]).read_text(encoding="utf-8"))
    baseline = json.loads(inside(root, args["baseline"]).read_text(encoding="utf-8"))
    output = json.loads(inside(root, args["output"]).read_text(encoding="utf-8"))
    if original != baseline or output != {**original, "status": "reviewed"}:
        raise ValueError("Original/output mismatch")
    return "原本不変・生成差分を検証"


OPS = {
    "snapshot": Op("入力の保全", "入力JSONを検査し、保全用コピーを作る", snapshot),
    "patch": Op("別名で変換", "保全データをもとに別名JSONを作る", patch),
    "verify": Op("差分と原本の検証", "原本の不変と出力の期待値を確認する", verify),
}
PLAN = [
    {"id": "S1", "op": "snapshot", "args": {"source": "input.json", "baseline": "baseline.json"}},
    {"id": "S2", "op": "patch", "args": {"baseline": "baseline.json", "output": "result.json"}},
    {"id": "S3", "op": "verify", "args": {"source": "input.json", "baseline": "baseline.json", "output": "result.json"}},
]


def validate(plan):
    ids = [s["id"] for s in plan]
    if len(ids) != len(set(ids)) or not ids:
        raise ValueError("Duplicate or empty step IDs")
    for step in plan:
        if step["op"] not in OPS:
            raise ValueError("Unknown operation: " + str(step["op"]))
        if not isinstance(step["args"], dict):
            raise ValueError("Invalid args")
        for val in step["args"].values():
            if not isinstance(val, str) or not val or Path(val).is_absolute() or ".." in Path(val).parts:
                raise ValueError("Unsafe argument")


def guide(plan):
    validate(plan)
    lines = ["# 作業手順（工程定義から自動生成）", "", f"全{len(plan)}工程｜開始前：0/{len(plan)}完了", ""]
    for i, step in enumerate(plan, 1):
        op = OPS[step["op"]]
        lines.append(f"{i}. [{step['id']}] {op.title}：{op.guide}（AI実行）")
    lines += ["", "原本を上書きしない。結果の検査に通らなければ完了扱いにしない。"]
    return "\n".join(lines) + "\n"


def run(root, plan):
    validate(plan)  # All operations are allowlisted before any action
    results = []
    for step in plan:
        try:
            message = OPS[step["op"]].handler(root, step["args"])
            results.append({"id": step["id"], "status": "PASS", "detail": message})
        except Exception as exc:
            results.append({"id": step["id"], "status": "FAIL", "detail": type(exc).__name__})
            break
    return {"completed": sum(r["status"] == "PASS" for r in results),
            "total": len(plan), "status": "PASS" if len(results) == len(plan) and all(r["status"] == "PASS" for r in results) else "FAIL",
            "steps": results}


def selftest():
    checked = []
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        original = '{"id":"TEST-1","name":"sample"}\n'
        (root / "input.json").write_text(original, encoding="utf-8")
        generated_guide = guide(PLAN)
        report = run(root, PLAN)
        assert report["status"] == "PASS" and report["completed"] == 3
        assert (root / "input.json").read_text(encoding="utf-8") == original
        assert all(f"[{step['id']}]" in generated_guide for step in PLAN)
        checked.append("normal_run_and_document_consistency")

        (root / "input.json").write_text("not-json", encoding="utf-8")
        report_fail = run(root, PLAN)
        assert report_fail["status"] == "FAIL" and report_fail["completed"] == 0
        checked.append("invalid_input_fail_closed")

        try:
            run(root, [{"id": "X", "op": "delete", "args": {}}])
            raise AssertionError("Unknown operation accepted")
        except ValueError:
            checked.append("unknown_action_rejected")

        try:
            run(root, [{"id": "X", "op": "snapshot", "args": {"source": "../secret", "baseline": "save.json"}}])
            raise AssertionError("Traversal accepted")
        except ValueError:
            checked.append("path_traversal_rejected")
    return {"tests_passed": len(checked), "tests_total": 4, "checks": checked}


if __name__ == "__main__":
    print(json.dumps(selftest(), ensure_ascii=False, indent=2))
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "input.json").write_text('{"id":"SAMPLE","name":"test"}\n', encoding="utf-8")
        print(guide(PLAN))
        print(json.dumps(run(root, PLAN), ensure_ascii=False, indent=2))
