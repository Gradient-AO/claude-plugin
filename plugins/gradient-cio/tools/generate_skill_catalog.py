#!/usr/bin/env python3
"""Generate the public skill catalog and lightweight in-chat menu."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
README = ROOT / "README.md"
MENU = SKILLS / "gradient-menu" / "SKILL.md"
REQUIREMENTS = (
    SKILLS / "gradient-setup" / "references" / "skill-requirements.md"
)

GROUPS = {
    "Review": (
        "gradient-portfolio-review",
        "gradient-portfolio-attribution-report",
        "gradient-equity-note",
    ),
    "Decide": (
        "gradient-macro-brief",
        "gradient-ic-memo",
        "gradient-fixed-income-portfolio-construction",
        "gradient-global-public-equity-portfolio-construction",
        "gradient-marketable-alternatives-portfolio-construction",
        "gradient-private-markets-portfolio-construction",
        "gradient-real-assets-portfolio-construction",
    ),
    "Diligence": (
        "gradient-manager-compare",
        "gradient-odd-report",
        "gradient-ddq-reconcile",
    ),
    "Monitor": ("gradient-manager-monitor",),
    "GIPS": (
        "gradient-gips-standards",
        "gradient-gips-manager-diligence",
        "gradient-gips-report-review",
        "gradient-gips-asset-owner-review",
        "gradient-gips-policies-gap-check",
    ),
}

EXAMPLES = {
    "Review": "Review our total portfolio for the quarter.",
    "Decide": "Draft an IC memo for this allocation change.",
    "Diligence": "Compare these managers, then prepare ODD on the finalist.",
    "Monitor": "Show what changed across our diligence roster this week.",
    "GIPS": "Review this composite report against the 2020 GIPS standards.",
}

README_BEGIN = "<!-- BEGIN GENERATED SKILL CATALOG -->"
README_END = "<!-- END GENERATED SKILL CATALOG -->"
MENU_BEGIN = "<!-- BEGIN GENERATED SKILL MENU -->"
MENU_END = "<!-- END GENERATED SKILL MENU -->"


def frontmatter(path: Path) -> dict[str, str]:
    """Read the flat fields needed from a skill's YAML frontmatter."""
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        raise ValueError(f"{path}: missing frontmatter")
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if raw.startswith('"'):
            try:
                values[key.strip()] = json.loads(raw)
                continue
            except json.JSONDecodeError:
                pass
        values[key.strip()] = raw.strip("'\"")
    return values


def descriptions() -> dict[str, str]:
    """Return every installed skill description keyed by public name."""
    result: dict[str, str] = {}
    for skill_file in sorted(SKILLS.glob("*/SKILL.md")):
        data = frontmatter(skill_file)
        name = data.get("name", "")
        description = data.get("description", "")
        if not name or not description:
            raise ValueError(f"{skill_file}: name and description are required")
        result[name] = description
    return result


def grouped_names() -> set[str]:
    return {
        name
        for names in GROUPS.values()
        for name in names
    } | {"gradient-setup", "gradient-menu"}


def readme_catalog(items: dict[str, str]) -> str:
    """Build the grouped README catalog from frontmatter descriptions."""
    lines = [
        README_BEGIN,
        "Start with `gradient-menu` to browse commands in chat or "
        "`gradient-setup` to check connection and data readiness.",
        "",
    ]
    for group, names in GROUPS.items():
        lines.extend((f"### {group}", "", "| Skill | Produces / routes |", "|---|---|"))
        lines.extend(f"| `{name}` | {items[name]} |" for name in names)
        lines.append("")
    lines.append(README_END)
    return "\n".join(lines)


def menu_catalog(items: dict[str, str]) -> str:
    """Build the concise in-chat command menu."""
    lines = [
        MENU_BEGIN,
        "For connection, entitlement, or data-readiness checks, use "
        "`/gradient-cio:gradient-setup`.",
        "",
    ]
    for group, names in GROUPS.items():
        lines.append(f"## {group}")
        lines.extend(
            f"- `/gradient-cio:{name}` — {items[name]}"
            for name in names
        )
        lines.extend(("", f'Example: “{EXAMPLES[group]}”', ""))
    lines.extend(
        (
            "Recommend one command when the task is clear. For multi-step work, "
            "name the first command and its likely hand-off.",
            MENU_END,
        )
    )
    return "\n".join(lines)


def replace_between(
    text: str,
    begin: str,
    end: str,
    replacement: str,
) -> str:
    pattern = re.compile(
        rf"{re.escape(begin)}.*?{re.escape(end)}",
        re.DOTALL,
    )
    if not pattern.search(text):
        raise ValueError(f"missing generated markers {begin} / {end}")
    return pattern.sub(lambda _match: replacement, text)


def requirements_names() -> set[str]:
    """Read public skill names from the readiness requirements table."""
    names: set[str] = set()
    for line in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        match = re.match(r"\|\s*(gradient-[^|]+?)\s*\|", line)
        if match:
            names.add(match.group(1).split(" — ", 1)[0].strip())
    return names


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    items = descriptions()
    installed = set(items)
    grouped = grouped_names()
    if installed != grouped:
        missing = sorted(installed - grouped)
        stale = sorted(grouped - installed)
        raise SystemExit(
            f"catalog grouping mismatch; ungrouped={missing}, missing={stale}"
        )
    required = requirements_names()
    if installed != required:
        raise SystemExit(
            "skill-requirements mismatch; "
            f"missing={sorted(installed - required)}, "
            f"stale={sorted(required - installed)}"
        )

    readme_text = README.read_text(encoding="utf-8")
    menu_text = MENU.read_text(encoding="utf-8")
    expected_readme = replace_between(
        readme_text,
        README_BEGIN,
        README_END,
        readme_catalog(items),
    )
    expected_menu = replace_between(
        menu_text,
        MENU_BEGIN,
        MENU_END,
        menu_catalog(items),
    )

    changed = []
    for path, current, expected in (
        (README, readme_text, expected_readme),
        (MENU, menu_text, expected_menu),
    ):
        if current == expected:
            continue
        changed.append(str(path.relative_to(ROOT)))
        if not args.check:
            path.write_text(expected, encoding="utf-8")

    if args.check and changed:
        raise SystemExit(
            "generated skill catalog is stale: " + ", ".join(changed)
        )
    print("skill catalog is current" if not changed else "updated " + ", ".join(changed))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
