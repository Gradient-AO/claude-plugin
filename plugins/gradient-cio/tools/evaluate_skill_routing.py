#!/usr/bin/env python3
"""Evaluate routing fixtures against installed skill descriptions with Claude."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "skill-routing.json"
SKILLS = ROOT / "skills"


def _frontmatter_value(text: str, key: str) -> str:
    match = re.search(rf"(?m)^{re.escape(key)}:\s*(.+?)\s*$", text)
    if match is None:
        return ""
    return match.group(1).strip().strip("\"'")


def _installed_skills() -> list[dict[str, str]]:
    installed: list[dict[str, str]] = []
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        text = path.read_text(encoding="utf-8")
        installed.append(
            {
                "name": _frontmatter_value(text, "name"),
                "description": _frontmatter_value(text, "description"),
            }
        )
    return installed


def _extract_result(stdout: str) -> list[dict[str, str]]:
    payload = json.loads(stdout)
    result = payload.get("result", payload) if isinstance(payload, dict) else payload
    if isinstance(result, str):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", result.strip())
        result = json.loads(cleaned)
    if isinstance(result, dict):
        result = result.get("routes", [])
    if not isinstance(result, list):
        raise ValueError("Claude result must be a JSON array or an object with routes")
    return [
        {"id": str(item.get("id", "")), "selected": str(item.get("selected", ""))}
        for item in result
        if isinstance(item, dict)
    ]


def _prompt(
    installed: list[dict[str, str]],
    batch: list[dict[str, object]],
    offset: int,
) -> str:
    cases = [
        {
            "id": str(offset + index),
            "prompt": item["prompt"],
            "avoid": item.get("not"),
        }
        for index, item in enumerate(batch)
    ]
    return (
        "Route each user prompt to exactly one installed GradientCIO skill. "
        "Use only the skill descriptions and the user's requested deliverable. "
        "The avoid field identifies a known wrong route. Return JSON only as "
        '[{"id":"0","selected":"gradient-example"}] in the same order.\n\n'
        f"INSTALLED SKILLS:\n{json.dumps(installed, ensure_ascii=False)}\n\n"
        f"CASES:\n{json.dumps(cases, ensure_ascii=False)}"
    )


def _claude_command() -> list[str] | None:
    claude = shutil.which("claude")
    if claude is not None:
        return [claude]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "-y", "@anthropic-ai/claude-code"]
    return None


def evaluate(
    claude_command: list[str],
    batch_size: int,
    require_claude: bool,
) -> int:
    fixtures = json.loads(FIXTURES.read_text(encoding="utf-8"))
    installed = _installed_skills()
    failures: list[str] = []
    for offset in range(0, len(fixtures), batch_size):
        batch = fixtures[offset : offset + batch_size]
        completed = subprocess.run(
            [*claude_command, "-p", "--output-format", "json"],
            input=_prompt(installed, batch, offset),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        if completed.returncode != 0:
            combined_output = completed.stdout + completed.stderr
            if "Not logged in" in combined_output and not require_claude:
                print("SKIP — Claude CLI is not logged in; routing evaluation not run")
                return 0
            print(completed.stdout, end="")
            print(completed.stderr, end="", file=sys.stderr)
            return completed.returncode
        try:
            routes = _extract_result(completed.stdout)
        except (json.JSONDecodeError, ValueError) as error:
            print(f"FAIL — invalid Claude routing result: {error}", file=sys.stderr)
            print(completed.stdout, file=sys.stderr)
            return 1
        by_id = {route["id"]: route["selected"] for route in routes}
        for index, fixture in enumerate(batch):
            case_id = str(offset + index)
            selected = by_id.get(case_id, "<missing>")
            if selected != fixture["expected"]:
                failures.append(
                    f"{case_id}: expected {fixture['expected']}, got {selected} "
                    f"for {fixture['prompt']!r}"
                )
    if failures:
        print("FAIL — Claude routing evaluation")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"PASS — Claude routed all {len(fixtures)} fixtures as expected")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-claude", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    args = parser.parse_args()
    claude_command = _claude_command()
    if claude_command is None:
        if args.require_claude:
            print("FAIL — Claude CLI is required but unavailable", file=sys.stderr)
            return 2
        print("SKIP — Claude CLI unavailable; routing evaluation not run")
        return 0
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")
    return evaluate(claude_command, args.batch_size, args.require_claude)


if __name__ == "__main__":
    raise SystemExit(main())
