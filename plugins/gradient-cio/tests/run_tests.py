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
import json, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
FIX = ROOT / "tests" / "fixtures"
RENDER = ROOT / "shared" / "gradient_report.py"
STALE = re.compile(r"(?<!gradient-)\bgips-(compliance|standards|manager-diligence|report-review|asset-owner-review|policies-gap-check)\b|gradient-capabilities")

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
