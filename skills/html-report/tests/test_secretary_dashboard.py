import importlib.util
import json
import tempfile
import unittest
import sys
from datetime import date
from pathlib import Path

MODULE = Path(__file__).parent.parent / "secretary_dashboard.py"
sys.path.insert(0, str(MODULE.parent))
spec = importlib.util.spec_from_file_location("secretary_dashboard", MODULE)
dashboard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dashboard)

def make_input():
    sections = {}
    for key, label in dashboard.SECTION_LABELS.items():
        sections[key] = {
            "status": "PASS",
            "evidence": f"synthetic evidence for {key}",
            "owner": "synthetic",
            "next_action": "none",
            "items": [],
        }
    sections["2"]["items"] = [
        {"id": "TASK-1", "title": "Synthetic overdue", "status": "OPEN",
         "due": "2026-11-22", "evidence": "synthetic row", "source_url": "https://example.invalid/task/1"},
        {"id": "TASK-2", "title": "Synthetic future", "status": "UNKNOWN",
         "due": "2026-11-25", "evidence": "synthetic row"},
        {"id": "TASK-3", "title": "Synthetic no due", "status": "NOT_RUN"},
    ]
    return {
        "title": "Synthetic secretary report",
        "snapshot_date": "2026-11-23",
        "source_checked_at": "2026-11-23T05:00:00+09:00",
        "source_label": "synthetic worksheet",
        "source_url": "https://example.invalid/source",
        "sections": sections,
        "unresolved_for_human": None,
        "monthly_completed_on": None,
        "monthly_already_answered": None,
    }

class DashboardTests(unittest.TestCase):
    def test_all_ten_sections_renderer_schema_and_due_math(self):
        result = dashboard.build_bundle(make_input())
        self.assertEqual(len(result["sections"]), 10)
        self.assertEqual(result["missing_sections"], [])
        self.assertEqual(result["section_status_counts"], {"PASS": 10})
        self.assertEqual(result["due_counts"], {"overdue": 1, "due_today": 0, "upcoming": 1, "unknown_or_invalid": 1})
        self.assertEqual(result["sections"]["2"]["items"][0]["days_to_due"], -1)
        self.assertEqual(result["renderer_input"]["kind"], "secretary")
        self.assertEqual(result["ui_branch_data"]["one_question_entry"], "UNKNOWN")
        self.assertIn("UNKNOWN", result["morning_report"])

    def test_missing_and_no_evidence_do_not_become_pass_or_zero(self):
        data = make_input()
        data["sections"] = {"1": {"status": "PASS", "evidence": ""}}
        data.pop("unresolved_for_human")
        result = dashboard.build_bundle(data)
        self.assertEqual(result["sections"]["1"]["status"], "EVIDENCE_INSUFFICIENT")
        self.assertEqual(result["sections"]["1"]["input_status"], "PASS")
        self.assertEqual(result["sections"]["1"]["verification"], "EVIDENCE_FIELD_EMPTY")
        self.assertEqual(result["missing_sections"], [str(i) for i in range(2, 11)])
        self.assertEqual(result["ui_branch_data"]["unresolved_for_human"], None)
        self.assertEqual(result["ui_branch_data"]["one_question_entry"], "UNKNOWN")
        self.assertEqual(result["section_status_counts"]["EVIDENCE_INSUFFICIENT"], 1)

    def test_error_unknown_and_not_run_remain_distinct(self):
        data = make_input()
        data["sections"]["1"] = {"status": "ERROR", "error": "synthetic read failed", "evidence": "synthetic call"}
        data["sections"]["2"] = {"status": "NOT_RUN", "evidence": "synthetic not attempted"}
        data["sections"]["3"] = {"status": "UNKNOWN", "evidence": ""}
        result = dashboard.build_bundle(data)
        self.assertEqual(result["sections"]["1"]["status"], "ERROR")
        self.assertEqual(result["sections"]["2"]["status"], "NOT_RUN")
        self.assertEqual(result["sections"]["3"]["status"], "UNKNOWN")
        self.assertEqual(result["error_sections"], ["1"])
        self.assertEqual(result["evidence_gaps"], ["3"])

    def test_invalid_deadline_and_invalid_date_are_not_guessed(self):
        data = make_input()
        data["sections"]["2"]["items"] = [
            {"title": "bad date", "due": "next Friday", "status": "OPEN"},
            {"title": "no date", "status": "OPEN"},
        ]
        result = dashboard.build_bundle(data)
        self.assertEqual(result["due_counts"]["unknown_or_invalid"], 2)

    def test_previous_section_diff_is_explicit_and_missing_history_stays_unknown(self):
        data = make_input()
        data["previous_sections"] = {
            "1": {"status": "NOT_RUN", "due": "", "next_action": "retrieve calendar"},
            "2": {"status": "PASS", "due": "", "next_action": "none"},
        }
        result = dashboard.build_bundle(data)
        self.assertEqual(result["difference"]["state"], "COMPARED")
        self.assertEqual(result["difference"]["changed_sections"], [
            {"id": "1", "title": dashboard.SECTION_LABELS["1"], "changed_fields": ["status", "next_action"]}
        ])
        no_history = make_input()
        result2 = dashboard.build_bundle(no_history)
        self.assertEqual(result2["difference"], {"state": "NOT_AVAILABLE", "changed_sections": []})

    def test_pdf_failure_does_not_stop_text_or_json(self):
        data = make_input()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "html_to_pdf.py").write_text(
                "import json; print(json.dumps({'status':'FAIL','reason':'synthetic converter failure'})); raise SystemExit(1)\n",
                encoding="utf-8")
            result = dashboard.generate(data, root / "out", script_dir=root, today="2026-11-23")
            self.assertTrue((root / "out" / "morning_report.txt").is_file())
            self.assertTrue((root / "out" / "secretary_dashboard.json").is_file())
            self.assertIn("FAIL", result["outputs"]["pdf"])
            self.assertEqual(result["outputs"]["text"], "PASS")

    def test_unwritable_destination_still_returns_morning_text_and_status(self):
        data = make_input()
        with tempfile.TemporaryDirectory() as tmp:
            blocker = Path(tmp) / "not-a-directory"
            blocker.write_text("block", encoding="utf-8")
            result = dashboard.generate(data, blocker, script_dir=Path(tmp), pdf_enabled=True)
            self.assertIn("Synthetic secretary report", result["morning_report"])
            self.assertTrue(result["outputs"]["text"].startswith("FAIL:"))
            self.assertTrue(result["outputs"]["json"].startswith("FAIL:"))
            self.assertTrue(result["outputs"]["log"].startswith("FAIL:"))

    def test_input_is_not_mutated_and_repeat_output_is_stable(self):
        data = make_input()
        original = json.loads(json.dumps(data))
        a = dashboard.build_bundle(data)
        b = dashboard.build_bundle(data)
        self.assertEqual(a, b)
        self.assertEqual(data, original)

if __name__ == "__main__":
    unittest.main()

