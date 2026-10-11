#!/usr/bin/env python3
"""Validate a GradientCIO IDD → ODD → IC handoff sidecar or report payload."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "gradient-idd-odd-ic-handoff/v1"
STAGES = {"idd", "odd", "decision"}
IDENTITY_STATUSES = {"canonical", "linked", "advisory", "unresolved"}
SELECTION_STATUSES = {"selected", "reserve", "rejected", "not_assessed"}


def _non_empty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_handoff(value: Any) -> list[str]:
    """Return deterministic contract errors for one handoff object."""
    if not isinstance(value, dict):
        return ["handoff must be an object"]
    errors: list[str] = []
    if value.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SCHEMA_VERSION}")
    if value.get("stage") not in STAGES:
        errors.append("stage must be idd, odd, or decision")

    subject = value.get("subject")
    if not isinstance(subject, dict):
        errors.append("subject must be an object")
    else:
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
            benchmark = row.get("benchmark_series_id")
            if benchmark is not None and not _non_empty(benchmark):
                errors.append(
                    f"return_series[{index}].benchmark_series_id must be null or non-empty"
                )
            if not _non_empty(row.get("benchmark_rationale")):
                errors.append(f"return_series[{index}].benchmark_rationale is required")

    evidence = value.get("evidence")
    if not isinstance(evidence, list) or not evidence:
        errors.append("evidence must contain at least one source row")
    else:
        for index, row in enumerate(evidence):
            if not isinstance(row, dict):
                errors.append(f"evidence[{index}] must be an object")
                continue
            tag = row.get("source_tag")
            if not _non_empty(tag) or not tag[1:].isdigit() or not tag.startswith("S"):
                errors.append(f"evidence[{index}].source_tag must match S<number>")
            if not _non_empty(row.get("tool")):
                errors.append(f"evidence[{index}].tool is required")
            if "as_of" not in row or "methodology_version" not in row:
                errors.append(
                    f"evidence[{index}] must preserve as_of and methodology_version"
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
        if selection.get("status") not in SELECTION_STATUSES:
            errors.append("selection.status is invalid")
        if not _non_empty(selection.get("rationale")):
            errors.append("selection.rationale is required")
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
