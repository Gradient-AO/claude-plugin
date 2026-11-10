"""Exact constants and JSON traversal helpers shared by JSON report validators and renderers."""

from __future__ import annotations

import re
from typing import Any

ILLUSTRATIVE_LABEL = (
    "Illustrative, Gradient Maintained — demo data, "
    "not the client's holdings or managers"
)
METADATA_RESPONSE_DIGEST = "not_applicable_metadata_response"

SHA256_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
SHA256_DIGEST_VALUE_PATTERN = re.compile(r"^sha256:([0-9a-fA-F]{64})$")

PLACEHOLDER_PATTERNS = (
    re.compile(r"<[^<>\n]{2,100}>"),
    re.compile(r"\{\{[^{}\n]+\}\}"),
    re.compile(r"\b(?:TBD|TODO|FIXME|TK)\b", re.IGNORECASE),
    re.compile(r"\[(?:INSERT|PLACEHOLDER)[^\]]*\]", re.IGNORECASE),
)
PLACEHOLDER_COMBINED_PATTERN = re.compile(
    r"<[^<>\n]{2,100}>|\{\{[^{}\n]+\}\}|\b(?:TBD|TODO|FIXME|TK)\b",
    re.IGNORECASE,
)

ATTRIBUTION_STATUS_PATTERNS = (
    r"\bsimulated attribution\b",
    r"\bprojected attribution\b",
)
FORWARD_ATTRIBUTION_PATTERNS = (r"\bforward attribution\b",)
LOCAL_CALC_TAG_PATTERNS = (r"\[Calc(?:\s+C(?:\d+|#))?\]",)

NEUTRAL_RECOMMENDATION_PATTERNS = (r"\bwe recommend\b",)
NEUTRAL_DIRECTION_PATTERNS = (
    r"\bshould\b",
    r"\bmust\b",
    r"\bbuy\b",
    r"\bsell\b",
)
NEUTRAL_APPROVAL_ALLOCATION_PATTERNS = (
    r"\bapprove\b",
    r"\bincrease (?:the )?allocation\b",
    r"\breduce (?:the )?allocation\b",
)
NEUTRAL_REBALANCE_PATTERNS = (r"\brebalance\b",)


def collect_strings(value: Any) -> list[str]:
    """Return every string nested in a JSON-compatible value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for child in value for item in collect_strings(child)]
    if isinstance(value, dict):
        return [item for child in value.values() for item in collect_strings(child)]
    return []
