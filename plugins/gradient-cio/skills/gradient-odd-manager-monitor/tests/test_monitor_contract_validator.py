#!/usr/bin/env python3
"""Focused tests for manager-monitor evidence-derived metadata checks."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import ModuleType
from typing import Any

VALIDATOR_PATH = (
    Path(__file__).resolve().parents[1] / "scripts" / "validate_monitor_digest.py"
)
ACTIVE_DIGEST_FIXTURE = (
    Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "digest.json"
)


def _load_validator() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "gradient_odd_monitor_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load monitor validator")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator()


def _root(*, week_kind: str = "quiet") -> dict[str, Any]:
    return {
        "meta": {
            "week_kind": week_kind,
            "event_date_from": "2026-10-01",
            "event_date_to": "2026-10-07",
            "latest_published_event": {
                "event_id": "event_TEST",
                "event_date": "2026-10-06",
                "publication_date": "2026-10-06",
            },
            "not_evaluated_count": 0,
            "completeness": {
                "distinct_funds": 1,
                "unique_parent_firms": 1,
                "evaluated_subjects": 2,
                "not_evaluated_subjects": 0,
                "used": 2,
                "expected": 2,
                "state": "complete",
            },
            "attention_items": [],
        },
        "executive": {
            "tiles": [
                {"label": "New alerts", "value": "0"},
                {"label": "Changes since review", "value": "0"},
            ]
        },
        "sections": [],
    }


class MonitorContractValidatorTests(unittest.TestCase):
    def validate(self, root: dict[str, Any]) -> list[str]:
        return VALIDATOR._validate_monitoring_contract(root)

    def test_quiet_week_requires_distinct_fund_and_parent_firm_denominator(
        self,
    ) -> None:
        self.assertEqual(self.validate(_root()), [])

        invalid = _root()
        invalid["meta"]["completeness"]["expected"] = 1
        errors = self.validate(invalid)

        self.assertTrue(
            any("distinct_funds plus unique_parent_firms" in error for error in errors)
        )

    def test_not_evaluated_forces_active_week_and_caveat(self) -> None:
        active = _root(week_kind="active")
        active["meta"]["not_evaluated_count"] = 1
        active["meta"]["completeness"].update(
            {
                "evaluated_subjects": 1,
                "not_evaluated_subjects": 1,
                "used": 1,
                "state": "partial",
            }
        )
        active["meta"]["not_evaluated_caveat"] = (
            "not_evaluated — one subject lacked a prior period; this is not "
            "zero or negative assurance."
        )
        self.assertEqual(self.validate(active), [])

        active["meta"]["week_kind"] = "quiet"
        del active["meta"]["not_evaluated_caveat"]
        errors = self.validate(active)

        self.assertTrue(any("must be 'active'" in error for error in errors))
        self.assertTrue(any("not_evaluated_caveat" in error for error in errors))

    def test_firm_overdue_maps_to_schedule_review(self) -> None:
        root = _root(week_kind="active")
        root["executive"]["tiles"][0]["value"] = "1"
        root["meta"]["attention_items"] = [
            {
                "subject_kind": "firm",
                "attention_reason": "overdue",
                "severity": "high",
                "action": "Schedule review",
            }
        ]

        self.assertEqual(self.validate(root), [])

    def test_reason_severity_and_action_are_cross_checked(self) -> None:
        root = _root(week_kind="active")
        root["executive"]["tiles"][1]["value"] = "1"
        root["meta"]["attention_items"] = [
            {
                "subject_kind": "firm",
                "attention_reason": "material_change",
                "severity": "low",
                "action": "No action",
            }
        ]
        errors = self.validate(root)

        self.assertTrue(any(".severity must be 'medium'" in error for error in errors))
        self.assertTrue(
            any(".action must be 'Review new ADV filing'" in error for error in errors)
        )

    def test_fund_only_reason_is_rejected_for_firm(self) -> None:
        root = _root(week_kind="active")
        root["executive"]["tiles"][0]["value"] = "1"
        root["meta"]["attention_items"] = [
            {
                "subject_kind": "firm",
                "attention_reason": "form_d_signals_detected",
                "severity": "medium",
                "action": "Run ODD refresh",
            }
        ]
        errors = self.validate(root)

        self.assertTrue(any("fund-only reason" in error for error in errors))

    def test_policy_covers_all_server_attention_reasons(self) -> None:
        self.assertEqual(
            set(VALIDATOR.ATTENTION_REASON_POLICY),
            {
                "identity_attention",
                "overdue",
                "unreviewed",
                "material_change",
                "form_d_signals_detected",
                "evidence_unavailable",
                "form_d_baseline_upgrade_required",
                "stale_evidence",
            },
        )

    def test_event_window_and_latest_publication_are_separate(self) -> None:
        root = _root()
        root["meta"]["latest_published_event"] = {
            "event_id": "event_OLDER",
            "event_date": "2026-09-30",
            "publication_date": "2026-09-30",
        }

        self.assertEqual(self.validate(root), [])

        root["meta"]["latest_published_event"] = "2026-09-30"
        self.assertTrue(
            any(
                "must be an object or null" in error
                for error in self.validate(root)
            )
        )

    def test_normal_cli_accepts_augmented_active_digest(self) -> None:
        report = json.loads(ACTIVE_DIGEST_FIXTURE.read_text(encoding="utf-8"))
        report["meta"].update(
            {
                "week_kind": "active",
                "event_date_from": "2026-09-28",
                "event_date_to": "2026-10-04",
                "latest_published_event": None,
                "not_evaluated_count": 0,
                "attention_items": [
                    {
                        "subject_kind": "firm",
                        "attention_reason": "material_change",
                        "severity": "medium",
                        "action": "Review new ADV filing",
                    }
                ],
            }
        )
        report["meta"]["completeness"].update(
            {
                "distinct_funds": 1,
                "unique_parent_firms": 1,
                "evaluated_subjects": 2,
                "not_evaluated_subjects": 0,
            }
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            report_path = Path(temporary_directory) / "monitor-active.json"
            report_path.write_text(json.dumps(report), encoding="utf-8")
            output = StringIO()
            with redirect_stdout(output):
                result = VALIDATOR.main(
                    ["validate_monitor_digest.py", str(report_path)]
                )

        self.assertEqual(result, 0, output.getvalue())
        self.assertIn("PASS — manager monitoring digest", output.getvalue())


if __name__ == "__main__":
    unittest.main()
