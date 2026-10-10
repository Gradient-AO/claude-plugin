"""Dependency-free static repository checks and suite ordering."""

from suites.harness import *
from suites.connector_contracts import (
    contract_checker,
    contract_checker_static_edges,
    contract_manifest,
)
from suites.renderer_regressions import chart_renderer
from suites.report_validators import connector_cutover

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
        description = fm.get("description", "")
        chat_only = fm.get("delivery") == "chat"
        check(bool(description), f"{s.name}: has description")
        check(
            len(description) <= 250,
            f"{s.name}: description at most 250 characters ({len(description)})",
        )
        check(
            chat_only or (s / "scripts" / "gradient_report.py").exists(),
            f"{s.name}: has renderer copy unless chat-only",
        )
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(
            chat_only or ".pdf" in body.lower() or "pdf" in description.lower(),
            f"{s.name}: declares PDF output unless chat-only",
        )
        check(
            len(text.splitlines()) <= 160,
            f"{s.name}: SKILL.md at most 160 lines ({len(text.splitlines())})",
        )
        check(
            len(text.split()) <= 1800,
            f"{s.name}: SKILL.md at most 1,800 words ({len(text.split())})",
        )
    stale = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in (".md", ".py", ".json") and "tests" not in p.parts and STALE.search(p.read_text(encoding="utf-8", errors="ignore")):
            stale.append(str(p.relative_to(ROOT)))
    check(not stale, "no stale skill names" + (f": {stale}" if stale else ""))
    r = subprocess.run([sys.executable, str(ROOT / "tools" / "sync_shared.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    check(r.returncode == 0, "shared renderer and style guide in sync in every skill")
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "tools" / "generate_skill_catalog.py"),
            "--check",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    check(
        r.returncode == 0,
        "README, menu and readiness requirements match installed skills",
    )
    py311 = shutil.which("python3.11")
    if py311:
        r = subprocess.run([py311, "-m", "py_compile", str(RENDER)], capture_output=True, text=True, encoding="utf-8", errors="replace")
        check(r.returncode == 0, "renderer compiles on Python 3.11")
    b = json.loads((ROOT / "branding.json").read_text(encoding="utf-8"))
    check(
        allow_branded or not b.get("client_name"),
        "public branding.json keeps the client override empty "
        "(use --allow-branded for a private client build)",
    )
    check(b.get("brand") == "gradient", "branding.json declares Gradient as the default brand")
    template_ok = False
    if PPTX_TEMPLATE.is_file():
        with zipfile.ZipFile(PPTX_TEMPLATE) as archive:
            content_types = archive.read("[Content_Types].xml")
            layouts = [
                name
                for name in archive.namelist()
                if re.fullmatch(r"ppt/slideLayouts/slideLayout\d+\.xml", name)
            ]
            template_ok = (
                b'typeface="Inter"' in archive.read("ppt/theme/theme1.xml")
                and b"presentationml.template.main+xml" in content_types
                and len(layouts) == 7
            )
    check(
        template_ok,
        "PowerPoint master is a seven-layout POTX with Inter theme fonts",
    )
    branded = json.loads((FIX / "branding-test.json").read_text(encoding="utf-8"))
    check(branded.get("brand") == "client", "client branding fixture declares the client brand")
    run_source_checks(check)
    connector_cutover()
    chart_renderer()
    contract_manifest()
    contract_checker_static_edges()
    contract_checker()
