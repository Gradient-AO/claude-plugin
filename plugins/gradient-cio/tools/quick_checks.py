#!/usr/bin/env python3
"""Fast release checks shared by the pre-push hook and CI.

    python plugins/gradient-cio/tools/quick_checks.py
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import subprocess
import sys

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (
    MARKETPLACE_MANIFEST_PATH,
    PLUGIN_ROOT,
    REPO_ROOT,
    TOOLS_DIR,
    load_plugin_manifest,
    resolve_claude_command,
)

ROOT = PLUGIN_ROOT
REPOSITORY = REPO_ROOT
TOOLS = TOOLS_DIR


def version_check() -> int:
    plugin = load_plugin_manifest()["version"]
    marketplace = json.loads(
        MARKETPLACE_MANIFEST_PATH.read_text(encoding="utf-8")
    )
    listed = next(
        entry["version"]
        for entry in marketplace["plugins"]
        if entry["name"] == "gradient-cio"
    )
    if plugin != listed:
        print(f"FAIL — plugin.json {plugin} != marketplace.json {listed}")
        return 1
    release_references = sorted(
        (ROOT / "skills").glob("*/references/plugin-release.json")
    )
    skill_count = sum(
        1 for path in (ROOT / "skills").iterdir() if (path / "SKILL.md").is_file()
    )
    if len(release_references) != skill_count:
        print(
            "FAIL — plugin-release.json must be packaged with every skill "
            f"({len(release_references)}/{skill_count})"
        )
        return 1
    mismatched = []
    for reference in release_references:
        release = json.loads(reference.read_text(encoding="utf-8"))
        if (
            release.get("plugin") != "gradient-cio"
            or release.get("release_version") != plugin
        ):
            mismatched.append(reference.parent.parent.name)
    if mismatched:
        print(
            f"FAIL — plugin release metadata does not match {plugin}: "
            + ", ".join(mismatched)
        )
        return 1
    print(f"version {plugin}")
    return 0


def run_fast_script_checks(environment: dict[str, str] | None = None) -> int:
    env = dict(os.environ if environment is None else environment)
    env.setdefault("PYTHONUTF8", "1")
    if version_check() != 0:
        return 1
    for script in (
        "sync_shared.py",
        "sync_quicktake_shared.py",
        "generate_skill_catalog.py",
        "check_tool_references.py",
    ):
        arguments = ["--check"] if script != "check_tool_references.py" else []
        completed = subprocess.run(
            [sys.executable, str(TOOLS / script), *arguments],
            cwd=REPOSITORY,
            env=env,
            check=False,
        )
        if completed.returncode != 0:
            return completed.returncode
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-claude-validate",
        action="store_true",
        help="run Python fast checks without invoking `claude plugin validate .`",
    )
    args = parser.parse_args()
    environment = dict(os.environ)
    environment.setdefault("PYTHONUTF8", "1")
    fast_rc = run_fast_script_checks(environment)
    if fast_rc != 0:
        return fast_rc
    if args.skip_claude_validate:
        return 0
    command = resolve_claude_command()
    if command is None:
        print("FAIL — install Node.js or the Claude CLI to run `claude plugin validate .`")
        return 1
    return subprocess.run(
        [*command, "plugin", "validate", "."],
        cwd=REPOSITORY,
        env=environment,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
