"""Shared paths, loaders, fixtures, and result collection."""

import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

from release_quality import run_artifact_checks, run_source_checks

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
RENDER = ROOT / "shared" / "gradient_report.py"
PPTX_TEMPLATE = ROOT / "assets" / "gradient-master.potx"
CONTRACT_CHECKER = ROOT / "skills" / "gradient-setup" / "scripts" / "check_contract.py"
CONTRACTS = ROOT / "skills" / "gradient-setup" / "references" / "contracts.json"
CONTRACT_CHECKS = ROOT / "skills" / "gradient-setup" / "references" / "contract-checks.md"
PUBLIC_TOOLS = ROOT / "skills" / "gradient-setup" / "references" / "public-tools.json"
SHARED_REPORT_STYLE = ROOT / "shared" / "report-style.md"
SHARED_MODULE_SCOPE = ROOT / "shared" / "module-scope.md"
SHARED_CHART_DATA = ROOT / "shared" / "chart-data.md"
SKILL_REQUIREMENTS = ROOT / "skills" / "gradient-setup" / "references" / "skill-requirements.md"
IC_MEMO_SKILL = ROOT / "skills" / "gradient-decision-ic-memo" / "SKILL.md"
IC_MEMO_DATA_MAP = ROOT / "skills" / "gradient-decision-ic-memo" / "references" / "data-map.md"
IC_MEMO_CALCULATIONS = ROOT / "skills" / "gradient-decision-ic-memo" / "references" / "calculations.md"
IC_MEMO_VALIDATOR = ROOT / "skills" / "gradient-decision-ic-memo" / "scripts" / "validate_memo.py"
IC_MEMO_COMPOSER = ROOT / "skills" / "gradient-decision-ic-memo" / "scripts" / "compose_memo_json.py"
IC_MEMO_EVIDENCE = FIX / "ic_evidence.json"
IC_MEMO_EXAMPLE = ROOT / "skills" / "gradient-decision-ic-memo" / "assets" / "example-memo.md"
ODD_REPORT_SKILL = ROOT / "skills" / "gradient-odd-report" / "SKILL.md"
PORTFOLIO_REVIEW_SKILL = ROOT / "skills" / "gradient-portfolio-review" / "SKILL.md"
PORTFOLIO_REVIEW_TEMPLATE = (
    ROOT
    / "skills"
    / "gradient-portfolio-review"
    / "references"
    / "review-template.md"
)
PORTFOLIO_REVIEW_DATA_MAP = (
    ROOT
    / "skills"
    / "gradient-portfolio-review"
    / "references"
    / "data-map.md"
)
PORTFOLIO_REVIEW_VALIDATOR = (
    ROOT / "skills" / "gradient-portfolio-review" / "scripts" / "validate_review.py"
)
PORTFOLIO_ATTRIBUTION_VALIDATOR = (
    ROOT
    / "skills"
    / "gradient-portfolio-attribution"
    / "scripts"
    / "validate_attribution.py"
)
GIPS_REPORT_COMPOSER = (
    ROOT
    / "internal"
    / "gips-evidence-review"
    / "scripts"
    / "compose_gips_report.py"
)
GIPS_REPORT_VALIDATOR = (
    ROOT
    / "internal"
    / "gips-evidence-review"
    / "scripts"
    / "validate_gips_report.py"
)
GIPS_VARIANTS = [
    ("asset-owner review", "gips-asset-owner-review", 4, 7, ["GIPS Asset Owner Review", "Oversight summary"]),
    ("report review", "gips" "-report-review", 4, 7, ["GIPS Report Review", "Preparer fix list"]),
]
ANALYTICAL_REPORT_VALIDATORS = [
    (
        "brief portfolio review",
        PORTFOLIO_REVIEW_VALIDATOR,
        FIX / "portfolio.json",
    ),
    (
        "ODD report",
        ROOT / "skills" / "gradient-odd-report" / "scripts" / "validate_odd_report.py",
        FIX / "odd.json",
    ),
    (
        "DDQ reconciliation",
        ROOT
        / "skills"
        / "gradient-odd-ddq-reconcile"
        / "scripts"
        / "validate_ddq_report.py",
        FIX / "ddq.json",
    ),
    (
        "manager comparison",
        ROOT
        / "skills"
        / "gradient-odd-report"
        / "scripts"
        / "validate_odd_report.py",
        FIX / "compare.json",
    ),
    (
        "manager monitor",
        ROOT
        / "skills"
        / "gradient-odd-manager-monitor"
        / "scripts"
        / "validate_monitor_digest.py",
        FIX / "digest.json",
    ),
]
CONSTRUCTION_VALIDATORS = [
    (
        "private-markets construction",
        ROOT
        / "skills"
        / "gradient-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-private-markets.json",
    ),
    (
        "fixed-income construction",
        ROOT
        / "skills"
        / "gradient-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-fixed-income.json",
    ),
    (
        "global-public-equity construction",
        ROOT
        / "skills"
        / "gradient-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-global-public-equity.json",
    ),
    (
        "marketable-alternatives construction",
        ROOT
        / "skills"
        / "gradient-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-marketable-alternatives.json",
    ),
    (
        "real-assets construction",
        ROOT
        / "skills"
        / "gradient-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-real-assets.json",
    ),
]
SETUP_SKILL = ROOT / "skills" / "gradient-setup" / "SKILL.md"
STALE = re.compile(r"(?<!gradient-)\bgips-(compliance|standards|manager-diligence|report-review|asset-owner-review|policies-gap-check)\b|gradient-capabilities")
REPORT_CONSTANTS = ROOT / "tools" / "report_constants.py"
if str(ROOT / "shared") not in sys.path:
    sys.path.insert(0, str(ROOT / "shared"))

try:
    from analysis_quality import review_callout, review_report
except ImportError:
    review_callout = None
    review_report = None

_report_constants_spec = importlib.util.spec_from_file_location(
    "gradient_report_constants",
    REPORT_CONSTANTS,
)
if _report_constants_spec is None or _report_constants_spec.loader is None:
    raise RuntimeError("Unable to load the shared report constants")
_report_constants_module = importlib.util.module_from_spec(_report_constants_spec)
_report_constants_spec.loader.exec_module(_report_constants_module)
ILLUSTRATIVE_LABEL = _report_constants_module.ILLUSTRATIVE_LABEL

_contract_checker_spec = importlib.util.spec_from_file_location(
    "gradient_contract_checker",
    CONTRACT_CHECKER,
)
if _contract_checker_spec is None or _contract_checker_spec.loader is None:
    raise RuntimeError("Unable to load the Gradient contract checker")
_contract_checker_module = importlib.util.module_from_spec(_contract_checker_spec)
_contract_checker_spec.loader.exec_module(_contract_checker_module)
validate_contract_manifest = _contract_checker_module.validate_manifest
approximately_equal = _contract_checker_module._approximately_equal

_renderer_spec = importlib.util.spec_from_file_location(
    "gradient_report_renderer",
    RENDER,
)
if _renderer_spec is None or _renderer_spec.loader is None:
    raise RuntimeError("Unable to load the Gradient report renderer")
_renderer_module = importlib.util.module_from_spec(_renderer_spec)
_renderer_spec.loader.exec_module(_renderer_module)

# name, args (relative to fixtures; OUT = output PDF), min pages, max pages, required text
CASES = [
    ("odd",      ["odd.json", "OUT"],                                5, 8,  ["Operational Due Diligence"]),
    ("ddq",      ["ddq.json", "OUT"],                                3, 8,  ["DDQ Reconciliation"]),
    ("ic_memo",  ["ic-memo.json", "OUT"],                          13, 18, ["Recommendation", "Key judgment", "Growth of 100"]),
    ("digest",   ["digest.json", "OUT"],                             3, 5,  ["Manager Monitoring Digest", "Needs attention"]),
    ("setup",    ["setup.json", "OUT"],                              4, 5,  ["Readiness", "Connection checks"]),
    ("blocks",   ["blocks.json", "OUT"],                             2, 4,  ["Synthetic TEST series", "A single large message"]),
    ("branded",  ["--brand", "branding-test.json", "blocks.json", "OUT"], 2, 4, ["Northwind Pension Plan (TEST)", "Powered by GradientCIO.com"]),
    ("portfolio", ["portfolio.json", "OUT"],                         6, 8,  ["Portfolio Review", "Calendar-year excess returns", "Growth of 100", "Manager × asset class"]),
    ("portfolio_comprehensive", ["portfolio-comprehensive.json", "OUT"], 13, 20, ["Comprehensive Portfolio Review", "Historical Attribution", "Projected Return and Risk Decomposition", "Analysis —"]),
    ("portfolio_attribution_report", ["portfolio-attribution-report.json", "OUT"], 8, 12, ["Portfolio Attribution Report", "Historical Attribution", "Governed Ex Ante Attribution", "Largest sub-allocation effect", "Analysis —"]),
    ("portfolio_attribution_compare_fallback", ["attribution-compare-fallback.json", "OUT"], 6, 10, ["Attribution Comparison", "Historical Attribution", "Cross-Lane Comparison"]),
    ("portfolio_attribution_compare_three_lane", ["attribution-compare-three-lane.json", "OUT"], 6, 10, ["Attribution Comparison", "Simulated Attribution", "Cross-Lane Comparison"]),
    ("idd_manager_performance_single", ["idd-manager-performance-single.json", "OUT"], 3, 10, ["Northstar Select Equity Composite", "Absolute risk and return", "Reliability and date-window sensitivity"]),
    ("idd_manager_performance_compare", ["idd-manager-performance-compare.json", "OUT"], 3, 9, ["Manager Comparison", "Relative performance and capture", "Correlation and robustness"]),
    ("idd_manager_performance_robustness", ["idd-manager-performance-robustness.json", "OUT"], 3, 9, ["Manager Robustness", "Window sensitivity", "Rolling evidence"]),
    ("idd_manager_portfolio_fit", ["idd-portfolio-fit.json", "OUT"], 3, 9, ["Northstar Portfolio Fit Review", "Correlation and diversification", "Simulation and stress"]),
    ("idd_manager_shortlist", ["idd-shortlist.json", "OUT"], 3, 9, ["Northstar Manager Shortlist", "Performance comparison", "Advance/reserve/reject rationale"]),
    ("idd_private_markets_pme", ["idd-private-markets-pme.json", "OUT"], 6, 8, ["PME", "J-curve cash-flow path", "Fund multiples path", "Context only — not a PME input", "benchmark_window_return"]),
    ("construction_private_markets", ["construction-private-markets.json", "OUT"], 8, 14, ["Private Markets Portfolio Construction", "Commitments, Pacing and Cash Flow", "Committee action requested"]),
    ("construction_fixed_income", ["construction-fixed-income.json", "OUT"], 8, 14, ["Fixed Income Portfolio Construction", "Rates and Credit Context", "Committee action requested"]),
    ("construction_global_public_equity", ["construction-global-public-equity.json", "OUT"], 8, 14, ["Global Public Equity Portfolio Construction", "Factor Exposures and Concentration", "Committee action requested"]),
    ("construction_marketable_alternatives", ["construction-marketable-alternatives.json", "OUT"], 8, 14, ["Marketable Alternatives Portfolio Construction", "Liquidity, Redemption and Operational Terms", "Committee action requested"]),
    ("construction_real_assets", ["construction-real-assets.json", "OUT"], 8, 14, ["Real Assets Portfolio Construction", "Commitments, Liquidity and Valuation", "Committee action requested"]),
    ("compare",  ["compare.json", "OUT"],                            5, 9,  ["Manager Comparison", "Side-by-side comparison", "Form 13F overlap"]),
]

fails = []

def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)

def markdown_handoff_bodies(markdown):
    lines = markdown.replace("\r\n", "\n").split("\n")
    preamble, order, bodies, current = [], [], {}, None
    for line in lines:
        if line.startswith("# ") and current is None:
            continue
        if line.startswith("## "):
            current = line[3:].strip()
            order.append(current)
            bodies[current] = []
        elif current is None:
            preamble.append(line)
        else:
            bodies[current].append(line)
    if order and "\n".join(preamble).strip():
        bodies[order[0]] = preamble + [""] + bodies[order[0]]
    return {
        heading: "\n".join(bodies[heading]).strip()
        for heading in order
    }

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); out[k.strip()] = v.strip().strip('"')
    return out
