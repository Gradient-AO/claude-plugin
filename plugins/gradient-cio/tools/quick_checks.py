#!/usr/bin/env python3
"""Fast release checks shared by the pre-push hook and CI.

    python plugins/gradient-cio/tools/quick_checks.py
"""

from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
TOOLS = ROOT / "tools"


def version_check() -> int:
    plugin = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )["version"]
    marketplace = json.loads(
        (REPOSITORY / ".claude-plugin" / "marketplace.json").read_text(
            encoding="utf-8"
        )
    )
    listed = next(
        entry["version"]
        for entry in marketplace["plugins"]
        if entry["name"] == "gradient-cio"
    )
    if plugin != listed:
        print(f"FAIL — plugin.json {plugin} != marketplace.json {listed}")
        return 1
    print(f"version {plugin}")
    return 0


def claude_command() -> list[str] | None:
    claude = shutil.which("claude")
    if claude is not None:
        return [claude]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "-y", "@anthropic-ai/claude-code"]
    return None


def main() -> int:
    environment = dict(os.environ)
    environment.setdefault("PYTHONUTF8", "1")
    if version_check() != 0:
        return 1
    for script in ("sync_shared.py", "generate_skill_catalog.py"):
        completed = subprocess.run(
            [sys.executable, str(TOOLS / script), "--check"],
            cwd=REPOSITORY,
            env=environment,
            check=False,
        )
        if completed.returncode != 0:
            return completed.returncode
    command = claude_command()
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
