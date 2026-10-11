#!/usr/bin/env python3
"""Advisory prose-quality checks for analytical report callouts."""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import Any

SOURCE_TAG = re.compile(r"\[S\d+(?:\s*,\s*S?\d+)*\]", re.IGNORECASE)
SENTENCE_END = re.compile(r"[.!?][\"')\]]*\s*$")
SENTENCE = re.compile(r"[^.!?]+[.!?](?=\s|$)", re.MULTILINE)
SPECIFIC_EVIDENCE = re.compile(
    r"(?:\d|%|\$|\b(?:than|largest|smallest|exceeds?|versus|vs\.?|"
    r"above|below|higher|lower|increased?|decreased?|rose|fell|"
    r"filings?|reports?|returns?|holdings?|allocations?|exposures?|"
    r"alerts?|findings?|records?|schedules?|statements?|policies?|"
    r"benchmarks?)\b)",
    re.IGNORECASE,
)
OBSERVATION_SPECIFIC = re.compile(
    r"(?:\d|%|\$|\b(?:zero|one|two|three|four|five|six|seven|eight|"
    r"nine|ten|none|no|than|while|against|differs?|mismatch|largest|"
    r"smallest|exceeds?|versus|vs\.?|above|below|higher|lower|"
    r"increased?|decreased?|rose|fell)\b)",
    re.IGNORECASE,
)
LIMITATION = re.compile(
    r"\b(?:coverage|lags?|lagged|staleness|stale|bases?|models?|assumptions?|"
    r"samples?|provisional|partial|limited|excludes?|omits?|outside|"
    r"supplied|dated|dates?|timing|newer|older|prior-day|as-of|only|"
    r"unavailable|availability|missing|not supplied|not provided|"
    r"not reported|not disclosed|not evidenced|unclear|unknown)\b",
    re.IGNORECASE,
)
TRIGGER = re.compile(
    r"(?:\d|%|\$|\b(?:threshold|above|below|exceeds?|falls?|rises?|"
    r"reaches?|breach|filings?|refresh|results?|reports?|records?|schedules?|"
    r"statements?|policies?|responses?|approvals?|confirmations?|follow-up)\b)",
    re.IGNORECASE,
)
BOILERPLATE = (
    "frames the review",
    "anchors the executive view",
    "identifies a monitoring priority",
)
STRUCTURED_LABELS = (
    "Observation:",
    "Why it matters:",
    "Uncertainty:",
    "What would change the view:",
)


def _without_source_tags(text: str) -> str:
    """Remove source tags and lightweight Markdown used around labels."""
    return SOURCE_TAG.sub("", text).replace("**", "").strip()


def _word_count(text: str) -> int:
    """Count prose words consistently across validator entry points."""
    return len(text.split())


def _complete_sentence(text: str) -> bool:
    """Return whether text is a minimally substantive complete sentence."""
    return _word_count(text) >= 6 and SENTENCE_END.search(text.strip()) is not None


def _structured_parts(text: str) -> dict[str, str] | None:
    """Split a four-part callout when all labels occur once and in order."""
    positions = [text.find(label) for label in STRUCTURED_LABELS]
    if any(position < 0 for position in positions) or positions != sorted(positions):
        return None
    parts: dict[str, str] = {}
    for index, label in enumerate(STRUCTURED_LABELS):
        start = positions[index] + len(label)
        end = positions[index + 1] if index + 1 < len(positions) else len(text)
        parts[label.removesuffix(":")] = text[start:end].strip()
    return parts


def review_callout(title: str, text: str, structured: bool) -> list[str]:
    """Return non-blocking quality notes for one analytical callout."""
    del title  # Kept in the public API so callers can attach their own location.
    prose = _without_source_tags(text)
    notes: list[str] = []
    words = _word_count(prose)
    if words < 35:
        notes.append(f"use at least 35 words of analysis (found {words})")

    if not structured:
        if len(SENTENCE.findall(prose)) < 2:
            notes.append("use at least two complete sentences")
        if SPECIFIC_EVIDENCE.search(prose) is None:
            notes.append("name specific evidence, such as a value or explicit comparison")
        return notes

    parts = _structured_parts(prose)
    if parts is None:
        notes.append(
            "use Observation, Why it matters, Uncertainty, and "
            "What would change the view in order"
        )
        return notes

    for label, part in parts.items():
        if not _complete_sentence(part):
            notes.append(
                f"{label} should be a complete sentence of at least six words"
            )

    observation = parts["Observation"]
    if OBSERVATION_SPECIFIC.search(observation) is None:
        notes.append("Observation should name a value, date, count, or comparison")

    why_it_matters = parts["Why it matters"].casefold()
    matched_boilerplate = next(
        (phrase for phrase in BOILERPLATE if phrase in why_it_matters),
        None,
    )
    if matched_boilerplate is not None:
        notes.append(
            "Why it matters should state the report-specific implication, "
            f"not boilerplate such as '{matched_boilerplate}'"
        )

    if LIMITATION.search(parts["Uncertainty"]) is None:
        notes.append("Uncertainty should name the actual evidence or model limitation")

    if TRIGGER.search(parts["What would change the view"]) is None:
        notes.append(
            "What would change the view should name a measurable trigger "
            "or evidence item"
        )
    return notes


def _blocks(values: object) -> Iterable[dict[str, Any]]:
    """Yield report blocks recursively, including two-column branches."""
    if not isinstance(values, list):
        return
    for value in values:
        if not isinstance(value, dict):
            continue
        yield value
        if value.get("type") == "two_col":
            yield from _blocks(value.get("left"))
            yield from _blocks(value.get("right"))


def review_report(
    document: object,
    role_names: tuple[str, ...] = ("analysis", "key_judgment"),
    *,
    structured: bool = False,
) -> list[str]:
    """Review matching callouts in every report section without affecting validity."""
    if not isinstance(document, dict):
        return []
    sections = document.get("sections")
    if not isinstance(sections, list):
        return []

    notes: list[str] = []
    roles = set(role_names)
    for section in sections:
        if not isinstance(section, dict):
            continue
        section_title = str(section.get("title", "Untitled section")).strip()
        for block in _blocks(section.get("blocks")):
            if block.get("role") not in roles:
                continue
            callout_title = str(block.get("title", "Untitled callout")).strip()
            text = str(block.get("text", "")).strip()
            for note in review_callout(callout_title, text, structured):
                notes.append(f"{section_title} / {callout_title}: {note}")
    return notes
