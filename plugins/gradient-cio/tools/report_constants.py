"""Exact constants shared by JSON report validators."""

ILLUSTRATIVE_LABEL = (
    "Illustrative, Gradient Maintained — demo data, "
    "not the client's holdings or managers"
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
