#!/usr/bin/env python3
"""Regression tests for the gradient-cio plugin. Run before every release:

    python tests/run_tests.py            # static checks + render every fixture
    python tests/run_tests.py --keep     # also keep the PDFs in tests/out/ for visual review
    python tests/run_tests.py --static   # static checks only (no rendering)

Static checks: plugin manifest, connector config, skill names and frontmatter, PDF output declared,
shared-file sync, stale skill names, Python 3.11 compatibility, default (unbranded) branding.json.
Render checks: each fixture renders, page counts stay in range, key text is present, decks do not
overflow, branding appears only when requested.

Live GradientCIO contract checks are run by the gradient-setup skill (full self-test), because they
need the user's connector; see skills/gradient-setup/references/contract-checks.md.
"""
import importlib.util, json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RENDER = ROOT / "shared" / "gradient_report.py"
CONTRACT_CHECKER = ROOT / "skills" / "gradient-setup" / "scripts" / "check_contract.py"
CONTRACTS = ROOT / "skills" / "gradient-setup" / "references" / "contracts.json"
CONTRACT_CHECKS = ROOT / "skills" / "gradient-setup" / "references" / "contract-checks.md"
PUBLIC_TOOLS = ROOT / "skills" / "gradient-setup" / "references" / "public-tools.json"
SKILL_REQUIREMENTS = ROOT / "skills" / "gradient-setup" / "references" / "skill-requirements.md"
MACRO_BRIEF_SKILL = ROOT / "skills" / "gradient-macro-brief" / "SKILL.md"
IC_MEMO_SKILL = ROOT / "skills" / "gradient-ic-memo" / "SKILL.md"
PORTFOLIO_REVIEW_SKILL = ROOT / "skills" / "gradient-portfolio-review" / "SKILL.md"
SETUP_SKILL = ROOT / "skills" / "gradient-setup" / "SKILL.md"
STALE = re.compile(r"(?<!gradient-)\bgips-(compliance|standards|manager-diligence|report-review|asset-owner-review|policies-gap-check)\b|gradient-capabilities")

_contract_checker_spec = importlib.util.spec_from_file_location(
    "gradient_contract_checker",
    CONTRACT_CHECKER,
)
if _contract_checker_spec is None or _contract_checker_spec.loader is None:
    raise RuntimeError("Unable to load the Gradient contract checker")
_contract_checker_module = importlib.util.module_from_spec(_contract_checker_spec)
_contract_checker_spec.loader.exec_module(_contract_checker_module)
validate_contract_manifest = _contract_checker_module.validate_manifest

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
    ("ic_memo",  ["--md", "ic.md", "--meta", "ic_meta.json", "OUT"], 7, 14, ["Recommendation"]),
    ("gips",     ["--md", "gips.md", "--meta", "gips_meta.json", "OUT"], 3, 6, ["GIPS"]),
    ("gips_note",["--md", "note.md", "--meta", "note_meta.json", "OUT"], 1, 4, ["GIPS"]),
    ("digest",   ["digest.json", "OUT"],                             3, 5,  ["Manager Monitoring Digest", "Needs attention"]),
    ("setup",    ["setup.json", "OUT"],                              3, 6,  ["Readiness", "Contract checks"]),
    ("blocks",   ["blocks.json", "OUT"],                             2, 4,  ["Synthetic TEST series", "A single large message"]),
    ("deck",     ["--deck", "deck.json", "OUT"],                     11, 11, ["Macro Briefing", "Takeaway"]),
    ("branded",  ["--brand", "branding-test.json", "blocks.json", "OUT"], 2, 4, ["Northwind Pension Plan (TEST)", "Powered by GradientCIO.com"]),
    ("portfolio", ["portfolio.json", "OUT"],                         5, 8,  ["Portfolio Review", "Standard periods to", "Growth of 100", "Look-through concentration"]),
    ("compare",  ["compare.json", "OUT"],                            5, 9,  ["Manager Comparison", "Side-by-side comparison", "Form 13F overlap"]),
    ("equity",   ["equity.json", "OUT"],                             5, 8,  ["Equity Research Note", "Review flags", "not a recommendation"]),
]

fails = []

def check(ok, msg):
    print(("  ok   " if ok else "  FAIL ") + msg)
    if not ok:
        fails.append(msg)

def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1); out[k.strip()] = v.strip().strip('"')
    return out

def static(allow_branded):
    print("Static checks")
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(re.fullmatch(r"[a-z0-9-]+", pj.get("name", "")) is not None, f"plugin name kebab-case ({pj.get('name')})")
    check(re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")) is not None, f"plugin version semver ({pj.get('version')})")
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    url = mcp.get("mcpServers", {}).get("GradientCIO", {}).get("url", "")
    check(url.startswith("https://"), f"GradientCIO connector url https ({url})")
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    check(len(skills) >= 14, f"{len(skills)} skills found")
    for s in skills:
        text = (s / "SKILL.md").read_text(encoding="utf-8"); fm = frontmatter(text)
        check(fm.get("name") == s.name and s.name.startswith("gradient-"), f"{s.name}: name matches folder and starts with gradient-")
        check(bool(fm.get("description")), f"{s.name}: has description")
        check((s / "scripts" / "gradient_report.py").exists(), f"{s.name}: has renderer copy")
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(".pdf" in body.lower() or "pdf" in fm.get("description", "").lower(), f"{s.name}: declares PDF output")
        check(len(text.split()) < 3000, f"{s.name}: SKILL.md under 3,000 words ({len(text.split())})")
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
    py311 = shutil.which("python3.11")
    if py311:
        r = subprocess.run([py311, "-m", "py_compile", str(RENDER)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        check(r.returncode == 0, "renderer compiles on Python 3.11")
    b = json.loads((ROOT / "branding.json").read_text(encoding="utf-8"))
    check(allow_branded or not b.get("client_name"), "branding.json is unbranded (use --allow-branded for a client build)")
    check(b.get("brand") == "gradient", "branding.json declares Gradient as the default brand")
    branded = json.loads((FIX / "branding-test.json").read_text(encoding="utf-8"))
    check(branded.get("brand") == "client", "client branding fixture declares the client brand")
    chart_renderer()
    contract_manifest()
    contract_checker()

def chart_renderer():
    percentage_column = {
        "key": "ratio",
        "title": "Ratio",
        "format": "percentage",
        "decimals": 1,
    }
    check(
        _renderer_module._chart_plot_value(percentage_column, 0.25) == 25,
        "chart renderer scales percentage axes to display units",
    )
    percentage_line = _renderer_module.b_chart({"chart": {
        "title": "Percentage line",
        "status": "ok",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
        ],
        "rows": [["2026-01-31", 0.25], ["2026-02-28", 0.4]],
        "render_hint": {"block": "line", "x": "period", "y": ["ratio"]},
    }})
    check(
        "<svg" in percentage_line and "%" in percentage_line,
        "chart renderer keeps same-unit percentage series as a line",
    )
    mixed_line = _renderer_module.b_chart({"chart": {
        "title": "Mixed units",
        "status": "ok",
        "currency": "USD",
        "columns": [
            {"key": "period", "title": "Period", "format": "date", "decimals": None},
            percentage_column,
            {"key": "nav", "title": "NAV", "format": "currency", "decimals": 0},
        ],
        "rows": [["2026-01-31", 0.25, 1_000_000]],
        "truncated": False,
        "render_hint": {
            "block": "line",
            "x": "period",
            "y": ["ratio", "nav"],
        },
    }})
    check(
        "<table" in mixed_line and "<svg" not in mixed_line,
        "chart renderer falls back to a table for mixed-unit lines",
    )

def contract_manifest():
    contracts = json.loads(CONTRACTS.read_text(encoding="utf-8"))
    probes = contracts["probes"]
    probe_ids = [probe["id"] for probe in probes]
    known_ids = set(probe_ids)
    check(len(probe_ids) == len(known_ids), "contract probe IDs are unique")
    counts = {
        name: sum(probe.get("set") == name for probe in probes)
        for name in ("standard", "full", "writes", "ddq-save-preview")
    }
    check(
        counts == {"standard": 8, "full": 30, "writes": 4, "ddq-save-preview": 3},
        f"contract probe sets have expected counts ({counts})",
    )

    public_tool_catalog = json.loads(PUBLIC_TOOLS.read_text(encoding="utf-8"))
    public_tools = public_tool_catalog["tools"]
    check(
        public_tool_catalog.get("generated") is True
        and public_tools == sorted(set(public_tools)),
        "public-tool catalog is generated, sorted, and unique",
    )
    manifest_errors = validate_contract_manifest(contracts, public_tools)
    check(
        not manifest_errors,
        "contract dependencies, placeholders, and public tools are valid"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    requirement_tokens = set(re.findall(
        r"\b(?:get|list|run|analyze|compare|create|extract|log|preview|reconcile|"
        r"save|screen|search|update|upload|batch)_[a-z0-9_]+\b",
        SKILL_REQUIREMENTS.read_text(encoding="utf-8"),
    ))
    unknown_requirement_tools = requirement_tokens - set(public_tools)
    check(
        not unknown_requirement_tools,
        "skill requirement tool names exist in the generated catalog"
        + (
            f": {sorted(unknown_requirement_tools)}"
            if unknown_requirement_tools
            else ""
        ),
    )

    write_probes = [probe for probe in probes if probe.get("set") == "writes"]
    expected_write_tools = {
        "create_diligence_finding",
        "preview_diligence_changes",
        "update_watchlist",
        "update_diligence_roster",
    }
    check(
        {probe["tool"] for probe in write_probes} == expected_write_tools,
        "writes set contains singular and batch-preview tools",
    )
    singular_write_probes = [
        probe for probe in write_probes
        if probe["tool"] != "preview_diligence_changes"
    ]
    check(
        all(
            probe["args"].get("dry_run") is True
            and probe.get("equals", {}).get("dry_run") is True
            and probe.get("equals", {}).get("committed") is False
            and "receipt_id" in probe.get("non_null", [])
            for probe in singular_write_probes
        ),
        "singular write probes are dry-run previews with non-null receipts",
    )
    check(
        not any(
            isinstance(probe.get("args"), dict)
            and probe["args"].get("dry_run") is False
            for probe in probes
        ),
        "no contract probe requests a write commit",
    )

    by_id = {probe["id"]: probe for probe in probes}
    the_read = by_id["the_read"]
    check(
        the_read["args"] == {}
        and the_read.get("equals", {}).get(
            "publication.requested_as_of_date",
            "missing",
        ) is None,
        "The Read probe uses the latest-publication contract",
    )
    sample_portfolio = by_id["sample_portfolio"]
    check(
        sample_portfolio["tool"] == "list_portfolios"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].record_kind",
        ) == "example"
        and sample_portfolio.get("equals", {}).get(
            "portfolios[0].canonical_default",
        ) is True,
        "sample-portfolio probe verifies the canonical example",
    )
    batch_preview = by_id["write_batch_preview"]
    batch_items = batch_preview["args"].get("items", [])
    check(
        len(batch_items) == 2
        and all(
            item.get("parameters", {}).get("dry_run") is True
            for item in batch_items
        )
        and batch_preview.get("equals", {}).get("dry_run") is True
        and batch_preview.get("equals", {}).get("committed") is False
        and batch_preview.get("equals", {}).get("previewed") == 2
        and {
            "items[0].receipt_id",
            "items[1].receipt_id",
        } <= set(batch_preview.get("non_null", [])),
        "batch write probe previews two changes without committing",
    )
    contract_guidance = CONTRACT_CHECKS.read_text(encoding="utf-8")
    macro_guidance = MACRO_BRIEF_SKILL.read_text(encoding="utf-8")
    check(
        "| get_the_read" not in contract_guidance
        and "get_the_read with `asOfDate`" not in contract_guidance,
        "known-issues table omits resolved The Read failures",
    )
    check(
        "get_portfolio_historical_returns | 500" not in contract_guidance
        and "ownership_weights` | `response_contract_invalid" not in contract_guidance
        and "data_scope.kind: live" not in contract_guidance,
        "known-issues table omits resolved portfolio failures",
    )
    check(
        "`get_the_read.asOfDate` is a historical-publication cutoff" in macro_guidance
        and "Omit it for the current brief" in macro_guidance,
        "macro brief distinguishes publication cutoff from meeting date",
    )
    check(
        "`status: unavailable` with `unavailable_reason`" in macro_guidance,
        "macro brief treats unavailable regime state as a valid evidence gap",
    )
    scope_reference = "`references/portfolio-strategy-scope.md`"
    check(
        all(
            scope_reference in path.read_text(encoding="utf-8")
            for path in (IC_MEMO_SKILL, PORTFOLIO_REVIEW_SKILL, SETUP_SKILL)
        ),
        "skills using Portfolio Analytics or Strategy Lab link the shared scope note",
    )
    portfolio_probe = by_id["portfolio_expected_statistics"]
    strategy_probe = by_id["strategy_expected_statistics"]
    check(
        portfolio_probe["tool"] == "get_chart_data"
        and portfolio_probe["args"].get("portfolio_id")
        == "<sample_portfolio:portfolios[0].portfolio_id>"
        and portfolio_probe["args"].get("analysis_type") == "expected-statistics",
        "Portfolio Analytics probe uses the canonical illustrative portfolio",
    )
    check(
        "depends_on" not in strategy_probe
        and "portfolio_id" not in strategy_probe["args"]
        and len(
            strategy_probe["args"]["strategy_lab_session"]["form"]["selectedRecords"],
        ) >= 1,
        "Strategy Lab probe uses inline return series without a portfolio ID",
    )
    relative_args = by_id["strategy_relative_return"]["args"]
    check(
        "envelope" not in relative_args and "fields" not in relative_args,
        "relative-return probe omits envelope and fields",
    )
    check(
        by_id["credit_spreads"]["args"] == {"view": "credit_spreads"},
        "credit-spreads probe passes only its view",
    )
    check(
        "status" in by_id["regime_state"].get("required", []),
        "regime-state probe requires an explicit status",
    )
    check(
        by_id["screen"]["args"].get("organization_id") == "<orgs:organizations[0].id>",
        "screen probe uses chained organization ID",
    )
    check(
        by_id["capabilities_summary"]["args"].get("detail") == "summary",
        "capabilities probe requests summary detail",
    )
    check(
        {"capabilities", "entitlements"}
        <= set(by_id["capabilities_summary"].get("required", [])),
        "capabilities probe distinguishes effective access from entitlements",
    )
    check(
        by_id["write_roster"]["args"].get("action") == "add"
        and by_id["write_roster"]["args"].get("subject_id")
        == "<roster:funds[0].fund_id>",
        "roster write probe exercises add with a canonical fund ID",
    )
    check(
        bool(by_id["write_roster"]["args"].get("reason")),
        "roster write probe exercises add-preview rationale",
    )
    check(
        by_id["ddq_save_preview"]["args"].get("reconciliation_id")
        == "<ddq_reconcile_persisted:run_id>"
        and by_id["ddq_save_preview"].get("equals", {}).get("outcome") == "preview",
        "DDQ save preview chains persisted run ID",
    )
    check(
        by_id["ddq_extract_persisted"]["args"].get("persist") is True
        and "document_id" in by_id["ddq_extract_persisted"].get("non_null", [])
        and by_id["ddq_reconcile_persisted"]["args"].get("document_id")
        == "<ddq_extract_persisted:document_id>",
        "DDQ extraction persists a document and reconciliation reuses it",
    )

def contract_checker():
    with tempfile.TemporaryDirectory() as directory:
        temp = pathlib.Path(directory)
        contracts = {
            "envelope": [],
            "probes": [
                {
                    "id": "source",
                    "tool": "source_tool",
                    "args": {},
                    "required": ["run_id"],
                },
                {
                    "id": "preview",
                    "tool": "preview_tool",
                    "set": "writes",
                    "depends_on": ["source"],
                    "args": {"reconciliation_id": "<source:run_id>"},
                    "required": ["receipt_id"],
                    "non_null": ["receipt_id"],
                    "equals": {"dry_run": True, "committed": False},
                },
            ],
        }
        contract_path = temp / "contracts.json"
        contract_path.write_text(json.dumps(contracts), encoding="utf-8")
        (temp / "public-tools.json").write_text(
            json.dumps({
                "generated": True,
                "tools": ["preview_tool", "source_tool"],
            }),
            encoding="utf-8",
        )
        (temp / "source.json").write_text(
            json.dumps({"run_id": "11111111-1111-4111-8111-111111111111"}),
            encoding="utf-8",
        )
        pass_path = temp / "pass.json"
        pass_path.write_text(
            json.dumps({"receipt_id": "receipt", "dry_run": True, "committed": False}),
            encoding="utf-8",
        )
        null_path = temp / "null.json"
        null_path.write_text(
            json.dumps({"receipt_id": None, "dry_run": True, "committed": False}),
            encoding="utf-8",
        )
        unequal_path = temp / "unequal.json"
        unequal_path.write_text(
            json.dumps({"receipt_id": "receipt", "dry_run": False, "committed": True}),
            encoding="utf-8",
        )
        def run(*args):
            return subprocess.run(
                [sys.executable, str(CONTRACT_CHECKER), *map(str, args)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
            )
        passed = run(contract_path, "preview", pass_path)
        null = run(contract_path, "preview", null_path)
        unequal = run(contract_path, "preview", unequal_path)
        resolved = run("--resolve-args", contract_path, "preview", temp)
        check(passed.returncode == 0 and "PASS preview" in passed.stdout, "contract checker accepts matching values")
        check(null.returncode == 1 and "null receipt_id" in null.stdout, "contract checker rejects null values")
        check(unequal.returncode == 1 and "expected True" in unequal.stdout, "contract checker rejects unequal values")
        check(
            resolved.returncode == 0
            and json.loads(resolved.stdout)["reconciliation_id"] == "11111111-1111-4111-8111-111111111111",
            "contract checker resolves chained probe arguments",
        )

def render(keep):
    print("Render checks")
    out = ROOT / "tests" / "out" if keep else pathlib.Path(tempfile.mkdtemp())
    out.mkdir(parents=True, exist_ok=True)
    for name, args, lo, hi, must in CASES:
        pdf = out / f"{name}.pdf"
        argv = [str(pdf) if a == "OUT" else (str(FIX / a) if (FIX / a).exists() else a) for a in args]
        r = subprocess.run([sys.executable, str(RENDER)] + argv, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=FIX)
        if r.returncode != 0:
            check(False, f"{name}: render exit {r.returncode}: {(r.stderr or r.stdout).strip()[-300:]}"); continue
        info = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        pages = int(re.search(r"Pages:\s+(\d+)", info).group(1))
        check(lo <= pages <= hi, f"{name}: {pages} pages (expected {lo}–{hi})")
        text = subprocess.run(["pdftotext", "-layout", str(pdf), "-"], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
        norm = lambda t: re.sub(r"\s+", "", t).upper()   # tolerate CSS uppercase and letter-spacing
        missing = [m for m in must if norm(m) not in norm(text)]
        check(not missing, f"{name}: contains {must}" + (f" — missing {missing}" if missing else ""))
        if name == "deck":
            size = re.search(r"Page size:\s+([\d.]+) x ([\d.]+)", info)
            check(size and abs(float(size.group(1)) - 960) < 2 and abs(float(size.group(2)) - 540) < 2, "deck: 16:9 page size")
        if name in ("odd", "digest", "portfolio", "compare", "equity"):
            check("Powered by" not in text, f"{name}: no client branding by default")
    print(f"PDFs in {out}")

def main():
    a = sys.argv[1:]
    static("--allow-branded" in a)
    if "--static" not in a:
        render("--keep" in a)
    print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
    sys.exit(1 if fails else 0)

if __name__ == "__main__":
    main()
