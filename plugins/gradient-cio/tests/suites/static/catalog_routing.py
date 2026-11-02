"""Skill catalog, metadata, routing, and validator registration checks."""

import json
import re

from suites.harness import FIX, ROOT, check, frontmatter


def catalog_routing_checks():
    pj = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    check(re.fullmatch(r"[a-z0-9-]+", pj.get("name", "")) is not None, f"plugin name kebab-case ({pj.get('name')})")
    check(re.fullmatch(r"\d+\.\d+\.\d+", pj.get("version", "")) is not None, f"plugin version semver ({pj.get('version')})")
    mcp = json.loads((ROOT / ".mcp.json").read_text(encoding="utf-8"))
    url = mcp.get("mcpServers", {}).get("GradientCIO", {}).get("url", "")
    check(url.startswith("https://"), f"GradientCIO connector url https ({url})")
    theme_text = (ROOT / "shared" / "report_theme.py").read_text(encoding="utf-8")
    theme_match = re.search(r'^THEME_VERSION = "([^"]+)"$', theme_text, re.MULTILINE)
    theme_version = theme_match.group(1) if theme_match else ""
    check(bool(theme_version), "shared report theme declares THEME_VERSION")
    skills = sorted(p for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").exists())
    check(len(skills) == 19, f"exactly 19 shipped skills found ({len(skills)})")
    release_references = [
        json.loads(
            (skill / "references" / "plugin-release.json").read_text(
                encoding="utf-8"
            )
        )
        for skill in skills
        if (skill / "references" / "plugin-release.json").is_file()
    ]
    check(
        len(release_references) == len(skills)
        and all(
            release.get("plugin") == pj["name"]
            and release.get("release_version") == pj["version"]
            and release.get("marketplace") == "gradientcio"
            for release in release_references
        ),
        "every skill exposes the overall marketplace release version",
    )
    menu_text = (
        ROOT / "skills" / "gradient-menu" / "SKILL.md"
    ).read_text(encoding="utf-8")
    normalized_menu = " ".join(menu_text.split())
    check(
        "references/plugin-release.json" in menu_text
        and "metadata.version" in menu_text
        and "individual skill contracts" in normalized_menu,
        "menu reports the overall release without confusing skill contract versions",
    )
    validator_manifest = json.loads(
        (FIX / "validator-manifest.json").read_text(encoding="utf-8")
    )
    descriptions_by_name = {}
    frontmatter_by_name = {}
    triggers_by_skill = {}
    for s in skills:
        text = (s / "SKILL.md").read_text(encoding="utf-8"); fm = frontmatter(text)
        check(fm.get("name") == s.name and s.name.startswith("gradient-"), f"{s.name}: name matches folder and starts with gradient-")
        description = fm.get("description", "")
        descriptions_by_name[s.name] = description
        frontmatter_by_name[s.name] = fm
        chat_only = fm.get("delivery") == "chat"
        canvas_output = fm.get("output") == "canvas"
        alias = fm.get("status") == "alias"
        check(bool(description), f"{s.name}: has description")
        check(
            len(description) <= 300,
            f"{s.name}: description at most 300 characters ({len(description)})",
        )
        check(
            description.startswith(("Create ", "Produce ", "Build ", "Check ", "Browse ", "Route ")),
            f"{s.name}: description starts with its output",
        )
        check(
            any(marker in description for marker in ("Triggers:", "Use for ", "Use when ", "For ")),
            f"{s.name}: description includes trigger or routing language",
        )
        redirects = re.findall(r"\bFor [^.]+ use gradient-[a-z0-9-]+", description)
        check(
            len(redirects) <= 1,
            f"{s.name}: description has at most one redirect",
        )
        triggers = tuple(
            value.casefold()
            for value in re.findall(r"'([^']+)'", description.partition("Triggers:")[2])
        )
        triggers_by_skill[s.name] = triggers
        check(
            len(triggers) == len(set(triggers)),
            f"{s.name}: description triggers are unique within the skill",
        )
        modes = tuple(
            mode.strip() for mode in fm.get("modes", "").split(",") if mode.strip()
        )
        check(
            not modes or len(modes) == len(set(modes)),
            f"{s.name}: metadata.modes contains unique values",
        )
        for metadata_key in (
            "group",
            "subject",
            "output",
            "menu_order",
            "modules",
            "contracts",
            "handoffs",
        ):
            check(bool(fm.get(metadata_key)), f"{s.name}: metadata.{metadata_key} is set")
        check(
            fm.get("menu_order", "").isdigit(),
            f"{s.name}: metadata.menu_order is an integer",
        )
        check(
            chat_only
            or canvas_output
            or (ROOT / "shared" / "gradient_report.py").exists(),
            f"{s.name}: can resolve its output renderer",
        )
        check(
            chat_only
            or canvas_output
            or fm.get("style_contract") == theme_version,
            f"{s.name}: report style contract matches shared theme {theme_version}",
        )
        canonical_report_files = (
            ROOT / "shared" / "gradient_report.py",
            ROOT / "shared" / "gradient_pptx.py",
            ROOT / "shared" / "report_theme.py",
            ROOT / "shared" / "report_layout.py",
            ROOT / "shared" / "render.py",
            ROOT / "shared" / "qa_report.py",
            ROOT / "shared" / "report-style.md",
            ROOT / "shared" / "public-tools.json",
        )
        check(
            chat_only
            or canvas_output
            or all(path.is_file() for path in canonical_report_files),
            f"{s.name}: resolves its complete output bundle",
        )
        check(
            bool(fm.get("summary")) and len(fm.get("summary", "").split()) <= 12,
            f"{s.name}: has a menu summary of at most 12 words",
        )
        check(
            chat_only
            or canvas_output
            or (s / "references" / "layout-budget.json").is_file(),
            f"{s.name}: report output has a layout budget",
        )
        body = text + "".join(p.read_text(encoding="utf-8") for p in (s / "references").glob("*.md")) if (s / "references").exists() else text
        check(
            chat_only
            or canvas_output
            or ".pdf" in body.lower()
            or "pdf" in description.lower()
            or (ROOT / "shared" / "report-style.md").is_file(),
            f"{s.name}: resolves its delivery contract",
        )
        check(
            len(text.splitlines()) <= 160,
            f"{s.name}: SKILL.md at most 160 lines ({len(text.splitlines())})",
        )
        check(
            len(text.split()) <= 1800,
            f"{s.name}: SKILL.md at most 1,800 words ({len(text.split())})",
        )
    installed_names = set(descriptions_by_name)
    canvas_renderers = {
        "gradient-portfolio-lens": "pa_viz.py",
        "gradient-signal-spotlight": "render_spotlight.py",
        "gradient-risk-pulse": "render_riskpulse.py",
        "gradient-tactical-dashboard": "render_dashboard.py",
        "gradient-ask-gradient": "render_ask.py",
    }
    canvas_errors = []
    for skill_name, renderer_name in canvas_renderers.items():
        skill = ROOT / "skills" / skill_name
        required_paths = (
            skill / "scripts" / renderer_name,
            skill / "scripts" / "brand.py",
            skill / "references" / "canvas-spec.md",
            skill / "assets" / "fonts" / "Inter-Regular.ttf",
        )
        if frontmatter_by_name.get(skill_name, {}).get("output") != "canvas":
            canvas_errors.append(f"{skill_name}: output is not canvas")
        canvas_errors.extend(
            str(path.relative_to(ROOT))
            for path in required_paths
            if not path.is_file()
        )
    check(
        not canvas_errors,
        "every Quick Take ships its renderer and synchronized canvas kit"
        + (f": {canvas_errors}" if canvas_errors else ""),
    )
    handoff_errors = []
    mode_reference_errors = []
    group_orders = {}
    for skill_name, fm in frontmatter_by_name.items():
        handoffs = tuple(
            name.strip()
            for name in fm.get("handoffs", "").split(",")
            if name.strip() and name.strip() != "none"
        )
        missing_handoffs = sorted(set(handoffs) - installed_names)
        if missing_handoffs:
            handoff_errors.append(f"{skill_name}: {missing_handoffs}")
        modes = tuple(
            mode.strip()
            for mode in fm.get("modes", "").split(",")
            if mode.strip()
        )
        for mode in modes:
            mode_path = (
                ROOT
                / "skills"
                / skill_name
                / "references"
                / "modes"
                / f"{mode}.md"
            )
            if not mode_path.is_file():
                mode_reference_errors.append(
                    f"{skill_name}: references/modes/{mode}.md"
                )
        if fm.get("status") != "alias":
            order_group = f"{fm['group']}::{fm.get('status', 'core')}"
            group_orders.setdefault(order_group, []).append(int(fm["menu_order"]))
    menu_order_errors = {
        group: sorted(orders)
        for group, orders in group_orders.items()
        if sorted(orders) != list(range(10, 10 * (len(orders) + 1), 10))
    }
    check(
        not handoff_errors,
        "all metadata handoffs target installed skills"
        + (f": {handoff_errors}" if handoff_errors else ""),
    )
    check(
        not mode_reference_errors,
        "all metadata modes have mode reference files"
        + (f": {mode_reference_errors}" if mode_reference_errors else ""),
    )
    check(
        not menu_order_errors,
        "group menu_order values are contiguous 10-point increments"
        + (f": {menu_order_errors}" if menu_order_errors else ""),
    )
    illustrative_title_rules = []
    for template_path in (ROOT / "skills").rglob("*template*.md"):
        template_text = template_path.read_text(encoding="utf-8")
        if re.search(
            r"(?:meta\.title[^\n]*with the standard illustrative suffix|"
            r"meta\.title(?![^\n]*\bnever\b)[^\n]*\b(?:append|include|add)\b|"
            r"meta\.title[^\n]*\n\s*(?!never\b)(?:append|include|add)\b)",
            template_text,
            re.IGNORECASE,
        ):
            illustrative_title_rules.append(
                str(template_path.relative_to(ROOT))
            )
    check(
        not illustrative_title_rules,
        "skill templates never append illustrative labels to meta.title"
        + (
            f": {illustrative_title_rules}"
            if illustrative_title_rules
            else ""
        ),
    )
    routing_fixtures = json.loads(
        (FIX / "skill-routing.json").read_text(encoding="utf-8")
    )
    routing_errors = []
    for fixture in routing_fixtures:
        expected = fixture["expected"]
        rejected = fixture["not"]
        description = descriptions_by_name.get(expected, "")
        if expected not in descriptions_by_name or rejected not in descriptions_by_name:
            routing_errors.append(f"{expected}: missing route skill")
            continue
        missing_terms = [
            term
            for term in fixture["description_terms"]
            if term.casefold() not in description.casefold()
        ]
        if missing_terms:
            routing_errors.append(f"{expected}: missing {missing_terms}")
    check(
        not routing_errors,
        "ambiguous IDD and ODD prompts have explicit description routes"
        + (f": {routing_errors}" if routing_errors else ""),
    )
    routing_counts = {
        name: sum(item.get("expected") == name for item in routing_fixtures)
        for name in descriptions_by_name
    }
    check(
        all(count >= 5 for count in routing_counts.values()),
        "routing fixtures include at least five prompts per skill"
        + (
            f": {routing_counts}"
            if any(count < 5 for count in routing_counts.values())
            else ""
        ),
    )
    output_skills = {
        name
        for name, fm in frontmatter_by_name.items()
        if name != "gradient-menu"
        and fm.get("status") != "alias"
        and fm.get("output") != "canvas"
    }
    manifest_errors = []
    if set(validator_manifest) != output_skills:
        manifest_errors.append(
            f"keys differ: missing={sorted(output_skills - set(validator_manifest))}, "
            f"stale={sorted(set(validator_manifest) - output_skills)}"
        )
    for skill_name, registration in validator_manifest.items():
        default_validator = registration.get("validator")
        if default_validator is not None:
            validator = ROOT / str(default_validator)
            if not validator.is_file():
                manifest_errors.append(f"{skill_name}: missing validator {validator}")
        fixture_names = list(registration.get("fixtures", []))
        declared_modes = set(
            frontmatter_by_name.get(skill_name, {}).get("modes", "").split(",")
        ) - {""}
        registered_modes = set(registration.get("modes", {}))
        if declared_modes and registered_modes != declared_modes:
            manifest_errors.append(
                f"{skill_name}: modes differ; declared={sorted(declared_modes)}, "
                f"registered={sorted(registered_modes)}"
            )
        for mode, mode_registration in registration.get("modes", {}).items():
            if isinstance(mode_registration, dict):
                mode_validator = ROOT / str(mode_registration.get("validator", ""))
                if not mode_validator.is_file():
                    manifest_errors.append(
                        f"{skill_name}/{mode}: missing validator {mode_validator}"
                    )
                fixture_names.extend(mode_registration.get("fixtures", []))
            else:
                if default_validator is None:
                    manifest_errors.append(
                        f"{skill_name}/{mode}: missing default validator"
                    )
                fixture_names.extend(mode_registration)
        fixture_names.extend(registration.get("chat_fixtures", []))
        for fixture_name in fixture_names:
            if not (FIX / fixture_name).is_file():
                manifest_errors.append(f"{skill_name}: missing fixture {fixture_name}")
    check(
        not manifest_errors,
        "every output skill has a registered validator and fixture"
        + (f": {manifest_errors}" if manifest_errors else ""),
    )
    return skills, validator_manifest
