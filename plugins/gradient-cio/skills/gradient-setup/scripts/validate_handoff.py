#!/usr/bin/env python3
"""Validate a GradientCIO IDD → ODD → IC handoff sidecar or report payload."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "gradient-idd-odd-ic-handoff/v1"
STAGES = {"idd", "odd", "decision"}
IDENTITY_STATUSES = {"canonical", "linked", "advisory", "unresolved"}
SELECTION_STATUSES = {"selected", "reserve", "rejected", "not_assessed"}
BENCHMARK_STATUSES = {"server_matched", "advisory", "unavailable"}
EVIDENCE_STATUSES = {"ok", "failed", "unavailable", "not_run"}
NO_PAYLOAD_DIGEST = "not_available:no_payload"
SHA256_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

TOP_LEVEL_FIELDS = {
    "schema_version",
    "stage",
    "subject",
    "return_series",
    "evidence",
    "limitations",
    "selection",
    "odd_findings",
}
SUBJECT_FIELDS = {
    "manager_id",
    "firm_id",
    "fund_id",
    "name",
    "identity_status",
}
RETURN_SERIES_FIELDS = {
    "return_series_id",
    "benchmark_series_id",
    "benchmark_rationale",
    "benchmark_status",
    "unavailable_reason",
    "start_date",
    "end_date",
    "observation_count",
}
EVIDENCE_FIELDS = {
    "source_tag",
    "tool",
    "as_of",
    "methodology_version",
    "digest",
    "status",
    "error_code",
    "request_id",
    "unavailable_reason",
}
SELECTION_FIELDS = {"status", "rationale"}
ODD_FINDING_FIELDS = {"title", "severity", "source_tags"}


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _reject_unknown(
    errors: list[str],
    value: dict[str, Any],
    allowed: set[str],
    path: str,
) -> None:
    for field in sorted(set(value) - allowed):
        errors.append(f"{path}.{field} is not allowed")


def _validate_success_digest(errors: list[str], value: Any, path: str) -> None:
    if value is not None and (
        not isinstance(value, str) or SHA256_DIGEST.fullmatch(value) is None
    ):
        errors.append(f"{path} must be sha256:<64 lowercase hex> or null")


def validate_handoff(value: Any) -> list[str]:
    """Return deterministic contract errors for one handoff object."""
    if not isinstance(value, dict):
        return ["handoff must be an object"]
    errors: list[str] = []
    _reject_unknown(errors, value, TOP_LEVEL_FIELDS, "handoff")
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    if value.get("stage") not in STAGES:
        errors.append("stage must be idd, odd, or decision")

    subject = value.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
        _reject_unknown(errors, subject, SUBJECT_FIELDS, "subject")
        if not _non_empty(subject.get("name")):
            errors.append("subject.name must be a non-empty string")
        if subject.get("identity_status") not in IDENTITY_STATUSES:
            errors.append("subject.identity_status is invalid")

    series = value.get("return_series")
    if not isinstance(series, list) or len(series) > 20:
        errors.append("return_series must be an array with at most 20 rows")
    else:
        for index, row in enumerate(series):
            if not isinstance(row, dict) or not _non_empty(row.get("return_series_id")):
                errors.append(f"return_series[{index}].return_series_id is required")
                continue
            path = f"return_series[{index}]"
            _reject_unknown(errors, row, RETURN_SERIES_FIELDS, path)
            status = row.get("benchmark_status")
            if "benchmark_status" in row and status not in BENCHMARK_STATUSES:
                errors.append(f"{path}.benchmark_status is invalid")
            if (
                "benchmark_rationale" in row
                and not _non_empty(row.get("benchmark_rationale"))
            ):
                errors.append(f"{path}.benchmark_rationale must be non-empty")
            if (
                "unavailable_reason" in row
                and not _non_empty(row.get("unavailable_reason"))
            ):
                errors.append(f"{path}.unavailable_reason must be non-empty")

            if "benchmark_status" not in row:
                if "benchmark_series_id" not in row:
                    errors.append(f"{path}.benchmark_series_id is required")
                elif row["benchmark_series_id"] is not None and not _non_empty(
                    row["benchmark_series_id"]
                ):
                    errors.append(
                        f"{path}.benchmark_series_id must be null or non-empty"
                    )
                if not _non_empty(row.get("benchmark_rationale")):
                    errors.append(f"{path}.benchmark_rationale is required")
            elif status in {"server_matched", "advisory"}:
                if not _non_empty(row.get("benchmark_series_id")):
                    errors.append(
                        f"{path}.benchmark_series_id is required for {status}"
                    )
                if not _non_empty(row.get("benchmark_rationale")):
                    errors.append(
                        f"{path}.benchmark_rationale is required for {status}"
                    )
            elif status == "unavailable":
                if "benchmark_series_id" not in row:
                    errors.append(
                        f"{path}.benchmark_series_id is required for unavailable"
                    )
                elif row["benchmark_series_id"] is not None:
                    errors.append(
                        f"{path}.benchmark_series_id must be null for unavailable"
                    )
                if not _non_empty(row.get("unavailable_reason")):
                    errors.append(
                        f"{path}.unavailable_reason is required for unavailable"
                    )

    evidence = value.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must contain at least one source row")
    else:
        for index, row in enumerate(evidence):
            if not isinstance(row, dict):
                errors.append(f"evidence[{index}] must be an object")
                continue
            path = f"evidence[{index}]"
            _reject_unknown(errors, row, EVIDENCE_FIELDS, path)
            tag = row.get("source_tag")
            if not isinstance(tag, str) or re.fullmatch(r"S[0-9]+", tag) is None:
                errors.append(f"{path}.source_tag must match S<number>")
            if not _non_empty(row.get("tool")):
                errors.append(f"{path}.tool is required")
            if "as_of" not in row:
                errors.append(f"{path}.as_of is required")
            for field in ("error_code", "request_id", "unavailable_reason"):
                if field in row and not _non_empty(row.get(field)):
                    errors.append(f"{path}.{field} must be non-empty")

            status = row.get("status")
            if "status" in row and status not in EVIDENCE_STATUSES:
                errors.append(f"{path}.status is invalid")
            if "status" not in row:
                if "methodology_version" not in row:
                    errors.append(
                        f"{path} must preserve as_of and methodology_version"
                    )
                _validate_success_digest(errors, row.get("digest"), f"{path}.digest")
            elif status == "ok":
                if not _non_empty(row.get("methodology_version")):
                    errors.append(
                        f"{path}.methodology_version is required for status ok"
                    )
                _validate_success_digest(errors, row.get("digest"), f"{path}.digest")
            elif status == "failed":
                if not (
                    _non_empty(row.get("error_code"))
                    or _non_empty(row.get("unavailable_reason"))
                ):
                    errors.append(
                        f"{path} failed status requires error_code or unavailable_reason"
                    )
                if row.get("digest") != NO_PAYLOAD_DIGEST:
                    errors.append(
                        f"{path}.digest must equal {NO_PAYLOAD_DIGEST} "
                        "for non-success status"
                    )
            elif status in {"unavailable", "not_run"}:
                if not _non_empty(row.get("unavailable_reason")):
                    errors.append(
                        f"{path}.unavailable_reason is required for status {status}"
                    )
                if row.get("digest") != NO_PAYLOAD_DIGEST:
                    errors.append(
                        f"{path}.digest must equal {NO_PAYLOAD_DIGEST} "
                        "for non-success status"
                    )

    limitations = value.get("limitations")
    if not isinstance(limitations, list) or any(
        not _non_empty(item) for item in limitations
    ):
        errors.append("limitations must be an array of non-empty strings")

    selection = value.get("selection")
    if not isinstance(selection, dict):
        errors.append("selection must be an object")
    else:
        _reject_unknown(errors, selection, SELECTION_FIELDS, "selection")
        if selection.get("status") not in SELECTION_STATUSES:
            errors.append("selection.status is invalid")
        if not _non_empty(selection.get("rationale")):
            errors.append("selection.rationale is required")

    odd_findings = value.get("odd_findings")
    if odd_findings is not None:
        if not isinstance(odd_findings, list):
            errors.append("odd_findings must be an array")
        else:
            for index, finding in enumerate(odd_findings):
                path = f"odd_findings[{index}]"
                if not isinstance(finding, dict):
                    errors.append(f"{path} must be an object")
                    continue
                _reject_unknown(errors, finding, ODD_FINDING_FIELDS, path)
                if not _non_empty(finding.get("title")):
                    errors.append(f"{path}.title is required")
                if finding.get("severity") not in {"low", "medium", "high"}:
                    errors.append(f"{path}.severity is invalid")
                source_tags = finding.get("source_tags")
                if not isinstance(source_tags, list) or any(
                    not isinstance(tag, str)
                    or re.fullmatch(r"S[0-9]+", tag) is None
                    for tag in source_tags
                ):
                    errors.append(f"{path}.source_tags must contain S<number> values")
    return errors


def handoff_from_document(document: Any) -> Any:
    """Accept a sidecar directly or a report carrying meta.handoff."""
    if isinstance(document, dict) and document.get("schema_version") == SCHEMA_VERSION:
        return document
    if isinstance(document, dict):
        meta = document.get("meta")
        if isinstance(meta, dict):
            return meta.get("handoff")
    return None


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_handoff.py <handoff-or-report.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — {error}", file=sys.stderr)
        return 2
    errors = validate_handoff(handoff_from_document(document))
    if errors:
        for error in errors:
            print(f"FAIL — {error}", file=sys.stderr)
        return 1
    print("PASS — handoff contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
