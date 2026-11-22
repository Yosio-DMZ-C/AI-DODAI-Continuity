#!/usr/bin/env python3
"""Build a private, one-run secretary dashboard from one authorized 10-section JSON.

This program only transforms supplied data. It does not fetch accounts, save source
records, send mail, click UI, schedule work, publish, or grant approvals.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date, datetime
from pathlib import Path
from typing import Any

from secretary_runtime import JST, compute
from render_report import render

SECTION_LABELS = {
    "1": "予定・天気・移動",
    "2": "個人タスク",
    "3": "メール",
    "4": "案件",
    "5": "半月次",
    "6": "動画・専門案件",
    "7": "本人判断",
    "8": "月次",
    "9": "記録・PDF・UI",
    "10": "課題・次の一手",
}
PASS_VALUES = {"PASS", "DONE", "COMPLETE", "COMPLETED"}
ATTENTION_VALUES = {
    "MISSING", "NOT_RUN", "UNKNOWN", "ERROR", "FAIL", "EVIDENCE_INSUFFICIENT",
    "PARTIAL", "OPEN", "DONE_WITH_ISSUES",
}
DATE_FORMAT = "%Y-%m-%d"


def _as_string(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""


def _parse_date(value: Any) -> date | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return date.fromisoformat(value.strip())
    except ValueError:
        return None


def _item_due(item: dict[str, Any], snapshot: date) -> dict[str, Any]:
    due_raw = _as_string(item.get("due"))
    if not due_raw:
        return {"due": "", "due_state": "UNKNOWN", "days_to_due": None}
    due = _parse_date(due_raw)
    if due is None:
        return {"due": due_raw, "due_state": "INVALID_DATE", "days_to_due": None}
    delta = (due - snapshot).days
    return {
        "due": due.isoformat(),
        "due_state": "OVERDUE" if delta < 0 else ("DUE_TODAY" if delta == 0 else "UPCOMING"),
        "days_to_due": delta,
    }


def _normalize_status(raw: Any, evidence: str) -> tuple[str, str, str]:
    status = _as_string(raw).upper() or "MISSING"
    verification = "EVIDENCE_FIELD_PROVIDED" if evidence else "EVIDENCE_FIELD_EMPTY"
    effective = status
    if status in PASS_VALUES and not evidence:
        effective = "EVIDENCE_INSUFFICIENT"
    return status, effective, verification


def build_bundle(data: dict[str, Any], today: date | str | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("input JSON root must be an object")
    snapshot_raw = _as_string(data.get("snapshot_date"))
    if today is None:
        snapshot = _parse_date(snapshot_raw) or datetime.now(JST).date()
    elif isinstance(today, str):
        snapshot = date.fromisoformat(today)
    else:
        snapshot = today
    snapshot_date = snapshot.isoformat()
    checked = _as_string(data.get("source_checked_at")) or "未確認"
    source_label = _as_string(data.get("source_label")) or "既存日次ワークシート"
    source_url = _as_string(data.get("source_url"))
    sections_in = data.get("sections", {})
    if sections_in is None:
        sections_in = {}
    if not isinstance(sections_in, dict):
        raise ValueError("sections must be an object keyed by 1..10")

    section_rows: list[dict[str, Any]] = []
    normalized_sections: dict[str, Any] = {}
    status_counts: dict[str, int] = {}
    case_items: list[dict[str, Any]] = []
    missing_sections: list[str] = []
    evidence_gaps: list[str] = []
    errors: list[str] = []
    changed_sections: list[dict[str, Any]] = []
    previous_sections = data.get("previous_sections")
    previous_available = isinstance(previous_sections, dict)

    for key, label in SECTION_LABELS.items():
        section = sections_in.get(key)
        if not isinstance(section, dict):
            section = {}
            missing_sections.append(key)
        raw_status, evidence = section.get("status"), _as_string(section.get("evidence"))
        input_status, effective_status, verification = _normalize_status(raw_status, evidence)
        if input_status == "MISSING":
            missing_sections.append(key) if key not in missing_sections else None
        if verification == "EVIDENCE_FIELD_EMPTY":
            evidence_gaps.append(key)
        error_text = _as_string(section.get("error"))
        if input_status == "ERROR" or error_text:
            errors.append(key)

        raw_items = section.get("items", [])
        if raw_items is None:
            raw_items = []
        if not isinstance(raw_items, list):
            raise ValueError(f"sections[{key}].items must be a list")
        normalized_items: list[dict[str, Any]] = []
        for n, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, dict):
                raise ValueError(f"sections[{key}].items[{n}] must be an object")
            item = dict(raw_item)
            item["title"] = _as_string(item.get("title")) or f"{label}（項目名未確認）"
            item["status"] = _as_string(item.get("status")) or "UNKNOWN"
            due_info = _item_due(item, snapshot)
            item.update(due_info)
            if due_info["due_state"] == "OVERDUE":
                item["next_action"] = _as_string(item.get("next_action")) or "期限超過を既存正本で確認し、必要な対応を判断"
            normalized_items.append(item)
            case_items.append(item)

        row = {
            "id": key,
            "title": label,
            "status": effective_status,
            "input_status": input_status,
            "verification": verification,
            "owner": _as_string(section.get("owner")) or "未確認",
            "next_action": _as_string(section.get("next_action")) or "既存正本で確認",
            "evidence": evidence or ("根拠未提供。未実施・未確認と区別。" if input_status in {"MISSING", "NOT_RUN", "UNKNOWN"} else "根拠なし"),
            "due": _as_string(section.get("due")),
            "source_url": _as_string(section.get("source_url")),
            "error": error_text,
            "items": normalized_items,
        }
        prior = previous_sections.get(key) if previous_available else None
        if isinstance(prior, dict):
            changes = [
                field for field in ("status", "due", "next_action")
                if _as_string(prior.get(field)) != _as_string(section.get(field))
            ]
            if changes:
                changed_sections.append({"id": key, "title": label, "changed_fields": changes})
        section_rows.append(row)
        normalized_sections[key] = row
        status_counts[effective_status] = status_counts.get(effective_status, 0) + 1

    # Runtime calculations reuse the existing helper's rules and terminology.
    state = dict(data)
    state["items"] = case_items
    state["monthly_completed_on"] = (
        data.get("monthly_completed_on") or data.get("monthly_review_last_completed_on")
    )
    state["monthly_prompted_on"] = (
        data.get("monthly_prompted_on") or data.get("monthly_review_last_prompted_on")
    )
    runtime = compute(state, snapshot)

    unresolved = data.get("unresolved_for_human")
    if not (isinstance(unresolved, int) and not isinstance(unresolved, bool) and unresolved >= 0):
        unresolved = None
    ui_branch = {
        "unresolved_for_human": unresolved,
        "one_question_entry": runtime["one_question_entry"],
        "monthly_prompt": runtime["monthly_prompt"],
        "existing_choice_ui": "専用Playbook/UIが実際に利用できる場合のみ。Pythonは選択肢を確定・表示・押下しない。",
    }

    summary_lines = [
        f"対象日：{snapshot_date}",
        f"必須欄：{len(section_rows) - len(missing_sections)}/10（欠落 {len(set(missing_sections))}）",
        f"根拠欄が空：{len(set(evidence_gaps))}欄",
        f"実エラー記録：{len(set(errors))}欄",
        f"月次分岐：{runtime['monthly_prompt']}／本人判断：{runtime['one_question_entry']}",
        "空欄・UNKNOWN・未試行は0件/PASSへ変換していない。",
    ]
    attention_rows = [row for row in section_rows if row["status"] in ATTENTION_VALUES]
    if attention_rows:
        details = [f"{row['title']}={row['status']}" for row in attention_rows[:3]]
        remainder = len(attention_rows) - len(details)
        summary_lines.append("確認候補：" + "、".join(details) + (f"、ほか{remainder}欄" if remainder else ""))
    if previous_available:
        summary_lines.append(f"前回からの状態・期限・次の一手の差分：{len(changed_sections)}欄")
    else:
        summary_lines.append("前回差分：未比較（previous_sections未提供）")
    due_overdue = sum(1 for item in case_items if item.get("due_state") == "OVERDUE")
    if due_overdue:
        summary_lines.append(f"期限超過項目：{due_overdue}件（期限値を取得できた項目のみ）")
    summary = "\n".join(summary_lines)

    dashboard_items = []
    for row in section_rows:
        dashboard_items.append({
            "id": f"SECTION-{row['id']}",
            "title": row["title"],
            "priority": "OTHER",
            "status": row["status"],
            "owner": row["owner"],
            "next_action": row["next_action"],
            "evidence": row["evidence"],
            "source_url": row["source_url"],
            "due": row["due"],
        })
    dashboard_items.extend(case_items)
    report_data = {
        "kind": "secretary",
        "title": _as_string(data.get("title")) or "秘書の日次ダッシュボード",
        "snapshot_date": snapshot_date,
        "source_checked_at": checked,
        "source_label": source_label,
        "source_url": source_url,
        "visibility": "private",
        "summary": summary,
        "handoff": _as_string(data.get("handoff")),
        "items": dashboard_items,
    }
    morning_report = "\n".join([report_data["title"], *summary_lines])
    return {
        "schema": "ADNC_SECRETARY_DASHBOARD_V1",
        "snapshot_date": snapshot_date,
        "source_checked_at": checked,
        "source_label": source_label,
        "source_url": source_url,
        "runtime": runtime,
        "ui_branch_data": ui_branch,
        "sections": normalized_sections,
        "section_status_counts": status_counts,
        "case_status_counts": runtime["status_counts"],
        "missing_sections": sorted(set(missing_sections), key=lambda x: int(x)),
        "evidence_gaps": sorted(set(evidence_gaps), key=lambda x: int(x)),
        "error_sections": sorted(set(errors), key=lambda x: int(x)),
        "difference": {
            "state": "COMPARED" if previous_available else "NOT_AVAILABLE",
            "changed_sections": changed_sections,
        },
        "due_counts": {
            "overdue": due_overdue,
            "due_today": sum(1 for item in case_items if item.get("due_state") == "DUE_TODAY"),
            "upcoming": sum(1 for item in case_items if item.get("due_state") == "UPCOMING"),
            "unknown_or_invalid": sum(1 for item in case_items if item.get("due_state") in {"UNKNOWN", "INVALID_DATE"}),
        },
        "morning_report": morning_report,
        "renderer_input": report_data,
        "generation_boundary": {
            "account_reads": "NOT_RUN_BY_PYTHON",
            "source_writes": "NOT_RUN_BY_PYTHON",
            "mail_delivery": "NOT_RUN_BY_PYTHON",
            "ui_clicks": "NOT_RUN_BY_PYTHON",
            "human_semantic_decisions": "REMAIN_WITH_SECRETARY_AND_USER",
        },
    }


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def generate(data: dict[str, Any], out_dir: Path, script_dir: Path | None = None,
             today: date | str | None = None, pdf_enabled: bool = True) -> dict[str, Any]:
    script_dir = script_dir or Path(__file__).resolve().parent
    result = build_bundle(data, today)
    paths = {
        "json": out_dir / "secretary_dashboard.json",
        "html": out_dir / "secretary_dashboard.html",
        "text": out_dir / "morning_report.txt",
        "pdf": out_dir / "secretary_dashboard.pdf",
        "log": out_dir / "run.log",
    }
    events: list[str] = []
    renderer_input_text = json.dumps(result["renderer_input"], ensure_ascii=False, indent=2) + "\n"
    html_text = ""
    try:
        html_text = render(result["renderer_input"])
        events.append("HTML_RENDER=PASS")
    except Exception as exc:
        events.append(f"HTML_RENDER=FAIL:{type(exc).__name__}:{exc}")

    save: dict[str, str] = {}
    # Attempt independent outputs even if an earlier one fails.
    payloads = {
        "html": html_text,
        "text": result["morning_report"] + "\n",
    }
    for name, content in payloads.items():
        if not content:
            save[name] = "NOT_RUN"
            continue
        try:
            _atomic_write(paths[name], content)
            save[name] = "PASS"
        except Exception as exc:
            save[name] = f"FAIL:{type(exc).__name__}:{exc}"
            events.append(f"SAVE_{name.upper()}={save[name]}")

    pdf_state = "NOT_RUN"
    if pdf_enabled and save.get("html") == "PASS":
        converter = script_dir / "html_to_pdf.py"
        if not converter.is_file():
            pdf_state = "NOT_RUN:converter_missing"
        else:
            try:
                proc = subprocess.run(
                    [sys.executable, str(converter), str(paths["html"]), "--output", str(paths["pdf"]), "--no-web-logo"],
                    capture_output=True, text=True, timeout=60, check=False,
                )
                detail = (proc.stdout or proc.stderr).strip()
                try:
                    parsed = json.loads(detail)
                except (json.JSONDecodeError, TypeError):
                    parsed = {}
                if proc.returncode == 0 and paths["pdf"].is_file():
                    pdf_state = "PASS"
                    events.append(f"PDF=PASS:{parsed.get('bytes', paths['pdf'].stat().st_size)}bytes")
                else:
                    pdf_state = f"FAIL:{parsed.get('reason') or detail or f'exit_{proc.returncode}'}"
                    events.append(f"PDF={pdf_state}")
            except Exception as exc:
                pdf_state = f"FAIL:{type(exc).__name__}:{exc}"
                events.append(f"PDF={pdf_state}")
    elif pdf_enabled:
        pdf_state = "NOT_RUN:html_unavailable"
    else:
        pdf_state = "NOT_RUN:disabled"
    result["outputs"] = {
        "html": save.get("html", "NOT_RUN"),
        "text": save.get("text", "NOT_RUN"),
        "pdf": pdf_state,
        "json": "PENDING",
        "log": "PENDING",
        "paths": {key: str(value) for key, value in paths.items()},
    }
    result["execution_log"] = events
    run_log = "\n".join([datetime.now(JST).isoformat(), *events, f"PDF_STATE={pdf_state}", ""])
    try:
        existing = paths["log"].read_text(encoding="utf-8") if paths["log"].is_file() else ""
        _atomic_write(paths["log"], existing + run_log)
        result["outputs"]["log"] = "PASS"
    except Exception as exc:
        result["outputs"]["log"] = f"FAIL:{type(exc).__name__}:{exc}"
        events.append(f"SAVE_LOG={result['outputs']['log']}")
    # JSON is last so it records conversion and log status. Failure cannot
    # suppress the already-built morning report emitted by main().
    try:
        _atomic_write(paths["json"], json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        result["outputs"]["json"] = "PASS"
    except Exception as exc:
        result["outputs"]["json"] = f"FAIL:{type(exc).__name__}:{exc}"
        events.append(f"SAVE_JSON={result['outputs']['json']}")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate one private secretary dashboard from authorized 10-section JSON.")
    parser.add_argument("input", type=Path, help="existing authorized worksheet data as UTF-8 JSON")
    parser.add_argument("--out-dir", type=Path, default=Path(tempfile.gettempdir()) / "adnc-secretary")
    parser.add_argument("--date", help="override snapshot date YYYY-MM-DD for deterministic tests")
    parser.add_argument("--no-pdf", action="store_true", help="skip optional PDF conversion")
    args = parser.parse_args(argv)
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        result = generate(data, args.out_dir, today=args.date, pdf_enabled=not args.no_pdf)
    except Exception as exc:
        message = f"生成器入力／前処理エラー: {type(exc).__name__}: {exc}"
        print(message)
        try:
            _atomic_write(args.out_dir / "run.log", datetime.now(JST).isoformat() + "\n" + message + "\n")
        except Exception:
            print("ログ保存=FAIL（出力先へ書込不能）", file=sys.stderr)
        return 1

    # Always preserve the text result as a stdout fallback, even when any save
    # or PDF operation failed.
    print(result["morning_report"])
    print("出力状態=" + json.dumps(result["outputs"], ensure_ascii=False))
    return 0 if result["outputs"].get("text") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())

