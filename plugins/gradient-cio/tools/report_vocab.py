#!/usr/bin/env python3
"""Canonical family vocabulary profiles for report validators."""

from __future__ import annotations

from dataclasses import dataclass


BASE_TONES = frozenset({"", "good", "watch", "bad", "info"})
WARNING_TONES = BASE_TONES | {"warning"}
CONSTRUCTION_TONES = BASE_TONES | {"accent"}
BASE_STATUSES = frozenset(
    {
        "advisory",
        "aligned",
        "available",
        "breach",
        "clear",
        "complete",
        "compliant",
        "consistent",
        "contradicted",
        "corroborated",
        "current",
        "degraded",
        "due soon",
        "elevated",
        "failed",
        "high",
        "insufficient",
        "low",
        "matched",
        "medium",
        "missing",
        "needs review",
        "needs_review",
        "new",
        "not assessed",
        "not found",
        "not licensed",
        "not_applicable",
        "not_assessed",
        "not_run",
        "overdue",
        "partial",
        "passed",
        "ready",
        "review",
        "unavailable",
        "unverifiable",
        "watch",
    }
)


@dataclass(frozen=True)
class VocabularyProfile:
    """One report family's accepted semantic vocabulary."""

    signal_levels: frozenset[str]
    completeness_states: frozenset[str]
    allowed_tones: frozenset[str] = BASE_TONES
    allowed_statuses: frozenset[str] = BASE_STATUSES


DILIGENCE_VOCAB = VocabularyProfile(
    signal_levels=frozenset({"clear", "watch", "elevated", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
)

DDQ_VOCAB = VocabularyProfile(
    signal_levels=frozenset(
        {"discrepancies", "review", "consistent", "insufficient"}
    ),
    completeness_states=frozenset({"complete", "partial"}),
)

ATTRIBUTION_VOCAB = VocabularyProfile(
    signal_levels=frozenset({"satisfactory", "watch", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
    allowed_tones=WARNING_TONES,
)

REVIEW_VOCAB = VocabularyProfile(
    signal_levels=frozenset({"breach", "watch", "satisfactory", "insufficient"}),
    completeness_states=frozenset({"complete", "partial"}),
)

CONSTRUCTION_VOCAB = VocabularyProfile(
    signal_levels=DILIGENCE_VOCAB.signal_levels,
    completeness_states=DILIGENCE_VOCAB.completeness_states,
    allowed_tones=CONSTRUCTION_TONES,
)

GIPS_ASSESSMENT_TONES = {
    "Met": "good",
    "Partially met": "watch",
    "Not met": "bad",
    "Not found": "watch",
}
GIPS_SEVERITIES = ("High", "Medium", "Low")
GIPS_COMPLETENESS_STATES = frozenset({"complete", "partial"})
GIPS_CALLOUT_TONES = frozenset({"good", "watch", "bad", "info"})

IC_POLICY_STATUSES = frozenset(
    {"Compliant", "Watch", "Breach", "Not assessed", "n/a", ""}
)
IC_RISK_RATINGS = frozenset({"High", "Medium", "Low"})
