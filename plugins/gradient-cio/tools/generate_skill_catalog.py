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
PLUGIN_MANIFEST = ROOT / ".claude-plugin" / "plugin.json"
REQUIREMENTS = (
    SKILLS / "gradient-setup" / "references" / "skill-requirements.md"
)

GROUP_ORDER = (
    "Research",
    "Investment due diligence",
    "Operational diligence",
    "Portfolio",
    "Compliance",
    "Decision",
    "Admin",
)

EXAMPLES = {
    "Research": "Prepare a macro brief for the next IC meeting.",
    "Investment due diligence": "Compare these managers' track records.",
    "Operational diligence": "Prepare ODD on the finalist.",
    "Portfolio": "Review our total portfolio for the quarter.",
    "Compliance": "Review this report against the GIPS standards.",
    "Decision": "Draft an IC memo for this allocation change.",
    "Admin": "Check which GradientCIO workflows are ready.",
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


def descriptions() -> dict[str, dict[str, str]]:
    """Return every installed skill's catalog copy keyed by public name."""
    result: dict[str, dict[str, str]] = {}
    for skill_file in sorted(SKILLS.glob("*/SKILL.md")):
        data = frontmatter(skill_file)
        name = data.get("name", "")
        description = data.get("description", "")
        summary = data.get("summary", "")
        required_metadata = (
            "group",
            "subject",
            "output",
            "menu_order",
            "modules",
            "contracts",
            "handoffs",
        )
        if (
            not name
            or not description
            or not summary
            or any(not data.get(key) for key in required_metadata)
        ):
            raise ValueError(
                f"{skill_file}: catalog metadata is incomplete"
            )
        if data["group"] not in GROUP_ORDER:
            raise ValueError(f"{skill_file}: unsupported group {data['group']}")
        if not data["menu_order"].isdigit():
            raise ValueError(f"{skill_file}: menu_order must be an integer")
        if len(summary.split()) > 12:
            raise ValueError(
                f"{skill_file}: metadata.summary exceeds 12 words"
            )
        result[name] = {
            "description": description,
            "summary": summary,
            **{key: data[key] for key in required_metadata},
        }
    return result


def grouped_items(
    items: dict[str, dict[str, str]],
) -> dict[str, list[tuple[str, dict[str, str]]]]:
    """Group and order skills entirely from their frontmatter metadata."""
    grouped: dict[str, list[tuple[str, dict[str, str]]]] = {
        group: [] for group in GROUP_ORDER
    }
    for name, item in items.items():
        grouped[item["group"]].append((name, item))
    for rows in grouped.values():
        rows.sort(key=lambda row: (int(row[1]["menu_order"]), row[0]))
    return grouped


def readme_catalog(items: dict[str, dict[str, str]]) -> str:
    """Build the grouped README catalog from frontmatter descriptions."""
    lines = [
        README_BEGIN,
        "Start with `gradient-menu` to browse commands in chat or "
        "`gradient-setup` to check connection and data readiness.",
        "",
    ]
    for group, rows in grouped_items(items).items():
        if not rows:
            continue
        lines.extend((
            f"### {group}",
            "",
            "| Skill | Produces / routes | Modules |",
            "|---|---|---|",
        ))
        lines.extend(
            f"| `{name}` | {item['description']} | {item['modules']} |"
            for name, item in rows
        )
        lines.append("")
    lines.append(README_END)
    return "\n".join(lines)


def menu_catalog(items: dict[str, dict[str, str]]) -> str:
    """Build the concise in-chat command menu."""
    plugin_name = json.loads(
        PLUGIN_MANIFEST.read_text(encoding="utf-8")
    )["name"]
    lines = [
        MENU_BEGIN,
        "For connection, entitlement, or data-readiness checks, use "
        f"`/{plugin_name}:gradient-setup`.",
        "",
    ]
    for group, rows in grouped_items(items).items():
        if not rows:
            continue
        lines.append(f"## {group}")
        lines.extend(
            (
                f"- `/{plugin_name}:{name}` — {item['summary']}"
                + (
                    f" Next: {item['handoffs'].replace(',', ', ')}."
                    if item["handoffs"] != "none"
                    else ""
                )
            )
            for name, item in rows
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
