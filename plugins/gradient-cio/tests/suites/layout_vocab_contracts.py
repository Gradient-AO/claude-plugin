"""High-signal table-driven checks for layout schema and report vocabulary."""

from suites.harness import *


TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from layout_budget_schema import (  # noqa: E402
    CANONICAL_MINIMUM_BODY_FILL,
    CANONICAL_ORPHAN_TAIL_MAX_FILL,
    LayoutBudgetSchemaError,
    resolve_layout_budget,
    validate_layout_budget,
)
from report_layout import (  # noqa: E402
    cover_allowed_text,
    cover_fact_count_errors,
    cover_page_failures,
    ordinal_suffix,
    reader_text_failures,
)
from report_vocab import (  # noqa: E402
    ATTRIBUTION_VOCAB,
    DDQ_VOCAB,
    DILIGENCE_VOCAB,
    GIPS_COMPLETENESS_STATES,
    REVIEW_VOCAB,
)


TRACKED_BUDGETS = (
    ROOT / "internal" / "gips-evidence-review" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-decision-ic-memo" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-idd-manager-performance" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-idd-manager-portfolio-fit" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-idd-manager-performance" / "references" / "modes" / "shortlist-layout-budget.json",
    ROOT / "skills" / "gradient-idd-private-markets-pme" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-odd-ddq-reconcile" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-odd-report" / "references" / "layout-budget-compare.json",
    ROOT / "skills" / "gradient-odd-manager-monitor" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-odd-manager-monitor" / "references" / "layout-budget-triage.json",
    ROOT / "skills" / "gradient-odd-report" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-portfolio-attribution" / "references" / "modes" / "compare-lanes-layout-budget.json",
    ROOT / "skills" / "gradient-portfolio-attribution" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-portfolio-construction" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-portfolio-review" / "references" / "layout-budget.json",
    ROOT / "skills" / "gradient-setup" / "references" / "layout-budget.json",
)


def _budget(path):
    return json.loads(path.read_text(encoding="utf-8"))


def layout_vocab_contracts():
    budgets = {path: _budget(path) for path in TRACKED_BUDGETS}
    errors = {
        str(path.relative_to(ROOT)): validate_layout_budget(budget)
        for path, budget in budgets.items()
        if validate_layout_budget(budget)
    }
    check(
        not errors,
        "all 16 tracked layout budgets satisfy strict schema v2"
        + (f": {errors}" if errors else ""),
    )

    legacy_fields = {
        "page_target",
        "hard_ceiling",
        "section_defaults",
        "sections",
        "default_mode",
    }
    check(
        all(
            set(budget) >= {
                "schema_version",
                "design_profile",
                "forced_breaks",
                "pdf",
                "content",
            }
            and not set(budget).intersection(legacy_fields)
            and budget["pdf"]["minimum_body_fill"]
            == CANONICAL_MINIMUM_BODY_FILL
            and budget["pdf"]["orphan_tail_max_fill"]
            == CANONICAL_ORPHAN_TAIL_MAX_FILL
            for budget in budgets.values()
        ),
        "canonical budgets use one root shape and standard PDF fill thresholds",
    )

    selector_cases = (
        (
            ROOT
            / "skills"
            / "gradient-idd-manager-performance"
            / "references"
            / "layout-budget.json",
            {"meta": {"mode": "single"}},
            "1",
        ),
        (
            ROOT
            / "skills"
            / "gradient-portfolio-construction"
            / "references"
            / "layout-budget.json",
            {"meta": {"mode": "real_assets"}},
            "13",
        ),
        (
            ROOT
            / "skills"
            / "gradient-portfolio-review"
            / "references"
            / "layout-budget.json",
            {"meta": {"mode": "comprehensive"}},
            "11",
        ),
    )
    check(
        all(
            expected_section
            in resolve_layout_budget(budgets[path], report)["content"]["sections"]
            for path, report, expected_section in selector_cases
        ),
        "meta.mode selectors resolve IDD, construction, and review budgets",
    )

    monitor_path = (
        ROOT
        / "skills"
        / "gradient-odd-manager-monitor"
        / "references"
        / "layout-budget.json"
    )
    monitor = budgets[monitor_path]
    active = resolve_layout_budget(monitor, {"meta": {"week_kind": "active"}})
    quiet = resolve_layout_budget(monitor, {"meta": {"week_kind": "quiet"}})
    check(
        "changes-alerts" in active["content"]["sections"]
        and "changes-alerts" not in quiet["content"]["sections"]
        and set(monitor["modes"]) == {"active", "quiet"},
        "monitor active-only changes budget resolves by meta.week_kind",
    )
    active_report = json.loads((FIX / "digest.json").read_text(encoding="utf-8"))
    active_report.setdefault("meta", {})["week_kind"] = "active"
    quiet_report = json.loads(json.dumps(active_report))
    quiet_report["meta"]["week_kind"] = "quiet"
    quiet_report["sections"] = [
        section
        for section in quiet_report["sections"]
        if section.get("id") != "changes-alerts"
    ]
    check(
        validate_layout_budget(active, active_report) == []
        and validate_layout_budget(quiet, quiet_report) == [],
        "monitor mode budgets resolve every active and quiet section exactly once",
    )

    valid = {
        "schema_version": 2,
        "design_profile": "analytical",
        "forced_breaks": [],
        "pdf": {
            "target_pages": {"min": 2, "max": 3},
            "hard_max_pages": 4,
            "minimum_body_fill": 0.40,
            "orphan_tail_max_fill": 0.20,
        },
        "content": {
            "defaults": {},
            "sections": {
                "1": {
                    "role": "summary",
                    "requires_analysis": False,
                }
            },
        },
    }
    invalid_cases = (
        ({**valid, "page_target": {"min": 2, "max": 3}}, "unknown field"),
        (
            {
                **valid,
                "pdf": {**valid["pdf"], "minimum_body_fill": 0.30},
            },
            "minimum_body_fill",
        ),
        (
            {
                **valid,
                "modes": {"active": {}},
            },
            "selector",
        ),
    )
    check(
        all(
            any(expected in error for error in validate_layout_budget(candidate))
            for candidate, expected in invalid_cases
        ),
        "strict schema rejects legacy fields, threshold drift, and implicit modes",
    )

    try:
        resolve_layout_budget(
            {
                **valid,
                "selector": {"path": "meta.mode", "default": "single"},
                "modes": {"single": {}},
            },
            {"meta": {"mode": "missing"}},
        )
    except LayoutBudgetSchemaError as error:
        unknown_mode_rejected = "no mode 'missing'" in str(error)
    else:
        unknown_mode_rejected = False
    check(unknown_mode_rejected, "unknown selected modes fail with stable diagnostics")

    vocabulary_cases = (
        (
            DILIGENCE_VOCAB,
            {"clear", "watch", "elevated", "insufficient"},
            {"complete", "partial"},
        ),
        (
            DDQ_VOCAB,
            {"discrepancies", "review", "consistent", "insufficient"},
            {"complete", "partial"},
        ),
        (
            ATTRIBUTION_VOCAB,
            {"satisfactory", "watch", "insufficient"},
            {"complete", "partial"},
        ),
        (
            REVIEW_VOCAB,
            {"breach", "watch", "satisfactory", "insufficient"},
            {"complete", "partial"},
        ),
    )
    check(
        all(
            profile.signal_levels == frozenset(signals)
            and profile.completeness_states == frozenset(completeness)
            for profile, signals, completeness in vocabulary_cases
        )
        and GIPS_COMPLETENESS_STATES == frozenset({"complete", "partial"}),
        "family vocabularies standardize overlap without flattening semantics",
    )

    validator_profiles = (
        ROOT / "tools" / "idd_report_validator.py",
        ROOT / "tools" / "construction_report_validator.py",
        ROOT / "internal" / "gips-evidence-review" / "scripts" / "validate_gips_report.py",
        ROOT / "skills" / "gradient-decision-ic-memo" / "scripts" / "validate_memo.py",
        ROOT / "skills" / "gradient-odd-ddq-reconcile" / "scripts" / "validate_ddq_report.py",
        ROOT / "skills" / "gradient-odd-manager-monitor" / "scripts" / "validate_monitor_digest.py",
        ROOT / "skills" / "gradient-odd-report" / "scripts" / "validate_odd_report.py",
        ROOT / "skills" / "gradient-portfolio-attribution" / "scripts" / "validate_attribution.py",
        ROOT / "skills" / "gradient-portfolio-attribution" / "scripts" / "validate_attribution_compare.py",
        ROOT / "skills" / "gradient-portfolio-review" / "scripts" / "validate_review.py",
    )
    check(
        all(
            "report_vocab import" in path.read_text(encoding="utf-8")
            for path in validator_profiles
        ),
        "all family validators import shared vocabulary profiles",
    )

    bootstrap_validator = (
        ROOT
        / "skills"
        / "gradient-odd-report"
        / "scripts"
        / "validate_odd_report.py"
    )
    bootstrapped = subprocess.run(
        [sys.executable, str(bootstrap_validator)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        bootstrapped.returncode == 2
        and "usage:" in (bootstrapped.stdout + bootstrapped.stderr),
        "skill-local validator bootstraps tool profiles without synced copies",
    )

    cover_meta = {
        "eyebrow": "Portfolio review",
        "title": "Total Fund Review",
        "subtitle": "Third quarter 2026",
        "header_label": "Portfolio Review",
        "cover_facts": [["Prepared for", "Investment Committee"], ["Reviewed", "15 October 2026"]],
    }
    allowed = cover_allowed_text(cover_meta)
    clean_cover = [
        "GradientCIO",
        "P O R T F O L I O   R E V I E W",
        "Total Fund Review",
        "Third quarter 2026",
        "PREPARED FOR      REVIEWED",
        "Investment Committee      15 October 2026",
        "Confidential — prepared for internal investment use      GradientCIO.com",
    ]
    cluttered = cover_page_failures(
        [*clean_cover, "One asset class near its policy limit", "3 of 7 evidence areas"],
        allowed,
    )
    check(
        cover_page_failures(clean_cover, allowed) == []
        and len(cluttered) == 1
        and "near its policy limit" in cluttered[0]
        and "3 of 7 evidence areas" in cluttered[0],
        "title-page gate accepts letter-spaced metadata and rejects signals and coverage counts",
    )
    check(
        cover_fact_count_errors({"cover_facts": [["a", "b"]] * 5})
        == ["cover lists 5 facts; the title page shows at most 4"]
        and cover_fact_count_errors(cover_meta) == [],
        "cover gate rejects more than four cover facts",
    )
    check(
        [ordinal_suffix(number) for number in (1, 2, 3, 4, 11, 12, 13, 21, 22, 63, 111, 112)]
        == ["st", "nd", "rd", "th", "th", "th", "th", "st", "nd", "rd", "th", "th"],
        "ordinal suffixes follow English rules including the teens",
    )
    reader_failures = reader_text_failures(
        [
            ["The fund ranks 63th of 120 peers; 11th, 22nd and 101st are fine."],
            ["Check: passed_with_warnings", "{'chip': 'Watch', 'status': 'watch'}"],
            ["This signal focuses oversight on the sleeve."],
            ["Appendix — Sources", "S1 passed_with_warnings mcp:get_portfolio"],
        ],
        raw_status_exempt_pages={4},
    )
    check(
        reader_failures
        == [
            "page 1 has ordinal '63th'; write '63rd'",
            "page 2 shows a raw chip object; render it as a status label",
            "page 2 shows raw status values (passed_with_warnings); use the plain-language label",
            "page 3 uses the templated phrase 'This signal focuses oversight'; "
            "state the specific finding instead",
        ],
        "reader-text gate rejects bad ordinals, raw statuses, chip reprs and templated phrases outside the appendix",
    )
