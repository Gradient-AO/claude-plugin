"""Shared paths, result collection, and dynamic module loaders."""

import importlib.util, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIX = ROOT / "tests" / "fixtures"
RENDER = ROOT / "shared" / "gradient_report.py"
CONTRACT_CHECKER = ROOT / "skills" / "gradient-setup" / "scripts" / "check_contract.py"
CONTRACTS = ROOT / "skills" / "gradient-setup" / "references" / "contracts.json"
CONTRACT_CHECKS = ROOT / "skills" / "gradient-setup" / "references" / "contract-checks.md"
PUBLIC_TOOLS = ROOT / "skills" / "gradient-setup" / "references" / "public-tools.json"
SHARED_REPORT_STYLE = ROOT / "shared" / "report-style.md"
SHARED_MODULE_SCOPE = ROOT / "shared" / "module-scope.md"
SHARED_CHART_DATA = ROOT / "shared" / "chart-data.md"
REPORT_CONSTANTS = ROOT / "tools" / "report_constants.py"
SKILL_REQUIREMENTS = ROOT / "skills" / "gradient-setup" / "references" / "skill-requirements.md"
MACRO_BRIEF_SKILL = ROOT / "skills" / "gradient-macro-brief" / "SKILL.md"
IC_MEMO_SKILL = ROOT / "skills" / "gradient-ic-memo" / "SKILL.md"
IC_MEMO_DATA_MAP = ROOT / "skills" / "gradient-ic-memo" / "references" / "data-map.md"
IC_MEMO_CALCULATIONS = ROOT / "skills" / "gradient-ic-memo" / "references" / "calculations.md"
IC_MEMO_VALIDATOR = ROOT / "skills" / "gradient-ic-memo" / "scripts" / "validate_memo.py"
IC_MEMO_COMPOSER = ROOT / "skills" / "gradient-ic-memo" / "scripts" / "compose_memo_json.py"
IC_MEMO_EVIDENCE = FIX / "ic_evidence.json"
IC_MEMO_EXAMPLE = ROOT / "skills" / "gradient-ic-memo" / "assets" / "example-memo.md"
ODD_REPORT_SKILL = ROOT / "skills" / "gradient-odd-report" / "SKILL.md"
GIPS_MANAGER_DILIGENCE_SKILL = ROOT / "skills" / "gradient-gips-manager-diligence" / "SKILL.md"
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
    / "gradient-portfolio-attribution-report"
    / "scripts"
    / "validate_attribution.py"
)
GIPS_REPORT_COMPOSER = (
    ROOT
    / "skills"
    / "gradient-gips-standards"
    / "scripts"
    / "compose_gips_report.py"
)
GIPS_REPORT_VALIDATOR = (
    ROOT
    / "skills"
    / "gradient-gips-standards"
    / "scripts"
    / "validate_gips_report.py"
)
GIPS_VARIANTS = [
    ("manager diligence", "gips", 4, 7, ["GIPS Manager Diligence", "Evidence status"]),
    ("asset-owner review", "gips-asset-owner-review", 4, 7, ["GIPS Asset Owner Review", "Evidence status"]),
    ("policies gap check", "gips-policies-gap-check", 4, 7, ["GIPS Policies Gap Check", "Findings by severity"]),
    ("report review", "gips-report-review", 4, 7, ["GIPS Report Review", "Findings by severity"]),
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
        / "gradient-ddq-reconcile"
        / "scripts"
        / "validate_ddq_report.py",
        FIX / "ddq.json",
    ),
    (
        "equity note",
        ROOT
        / "skills"
        / "gradient-equity-note"
        / "scripts"
        / "validate_equity_note.py",
        FIX / "equity.json",
    ),
    (
        "manager comparison",
        ROOT
        / "skills"
        / "gradient-manager-compare"
        / "scripts"
        / "validate_manager_compare.py",
        FIX / "compare.json",
    ),
    (
        "manager monitor",
        ROOT
        / "skills"
        / "gradient-manager-monitor"
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
        / "gradient-private-markets-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-private-markets.json",
    ),
    (
        "fixed-income construction",
        ROOT
        / "skills"
        / "gradient-fixed-income-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-fixed-income.json",
    ),
    (
        "global-public-equity construction",
        ROOT
        / "skills"
        / "gradient-global-public-equity-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "construction-global-public-equity.json",
    ),
    (
        "marketable-alternatives construction",
        ROOT
        / "skills"
        / "gradient-marketable-alternatives-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "portfolio-construction-marketable-alternatives.json",
    ),
    (
        "real-assets construction",
        ROOT
        / "skills"
        / "gradient-real-assets-portfolio-construction"
        / "scripts"
        / "validate_construction.py",
        FIX / "portfolio-construction-real-assets.json",
    ),
]
SETUP_SKILL = ROOT / "skills" / "gradient-setup" / "SKILL.md"
STALE = re.compile(r"(?<!gradient-)\bgips-(compliance|standards|manager-diligence|report-review|asset-owner-review|policies-gap-check)\b|gradient-capabilities")

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

# name, args (relative to fixtures; OUT = output pdf), min pages, max pages, must-contain text
CASES = [
    ("odd",      ["odd.json", "OUT"],                                3, 6,  ["Operational Due Diligence"]),
    ("ddq",      ["ddq.json", "OUT"],                                3, 8,  ["DDQ Reconciliation"]),
    ("ic_memo",  ["ic-memo.json", "OUT"],                          14, 18, ["Recommendation", "Key judgment", "Growth of 100"]),
    ("gips_note",["--md", "note.md", "--meta", "note_meta.json", "OUT"], 1, 4, ["GIPS"]),
    ("digest",   ["digest.json", "OUT"],                             3, 5,  ["Manager Monitoring Digest", "Needs attention"]),
    ("setup",    ["setup.json", "OUT"],                              3, 6,  ["Readiness", "Contract checks"]),
    ("blocks",   ["blocks.json", "OUT"],                             2, 4,  ["Synthetic TEST series", "A single large message"]),
    ("deck",     ["--deck", "deck.json", "OUT"],                     11, 11, ["Macro Briefing", "Takeaway"]),
    ("branded",  ["--brand", "branding-test.json", "blocks.json", "OUT"], 2, 4, ["Northwind Pension Plan (TEST)", "Powered by GradientCIO.com"]),
    ("portfolio", ["portfolio.json", "OUT"],                         5, 8,  ["Portfolio Review", "Standard periods to", "Growth of 100", "Look-through concentration"]),
    ("portfolio_comprehensive", ["portfolio-comprehensive.json", "OUT"], 15, 20, ["Comprehensive Portfolio Review", "Historical Attribution", "Projected Return and Risk Decomposition", "Analysis and Considerations"]),
    ("portfolio_attribution_report", ["portfolio-attribution-report.json", "OUT"], 10, 14, ["Portfolio Attribution Report", "Historical Attribution", "Governed Ex Ante Attribution", "Analysis and Considerations"]),
    ("construction_private_markets", ["construction-private-markets.json", "OUT"], 10, 14, ["Private Markets Portfolio Construction", "Commitments, Pacing and Cash Flow", "Committee action requested"]),
    ("construction_fixed_income", ["construction-fixed-income.json", "OUT"], 10, 14, ["Fixed Income Portfolio Construction", "Rates and Credit Context", "Committee action requested"]),
    ("construction_global_public_equity", ["construction-global-public-equity.json", "OUT"], 10, 14, ["Global Public Equity Portfolio Construction", "Factor Exposures and Concentration", "Committee action requested"]),
    ("construction_marketable_alternatives", ["portfolio-construction-marketable-alternatives.json", "OUT"], 10, 14, ["Marketable Alternatives Portfolio Construction", "Liquidity, Redemption and Operational Terms", "Committee action requested"]),
    ("construction_real_assets", ["portfolio-construction-real-assets.json", "OUT"], 10, 14, ["Real Assets Portfolio Construction", "Commitments, Liquidity and Valuation", "Committee action requested"]),
    ("compare",  ["compare.json", "OUT"],                            5, 9,  ["Manager Comparison", "Side-by-side comparison", "Form 13F overlap"]),
    ("equity",   ["equity.json", "OUT"],                             5, 8,  ["Equity Research Note", "Review flags", "not a recommendation"]),
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

