#!/usr/bin/env python3
"""Run the local release gate, including Claude validation when available."""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import PLUGIN_ROOT, REPO_ROOT, TOOLS_DIR, resolve_claude_command
from quick_checks import run_fast_script_checks

ROOT = PLUGIN_ROOT
REPOSITORY = REPO_ROOT
TESTS = ROOT / "tests" / "run_tests.py"
ROUTING_EVALUATOR = TOOLS_DIR / "evaluate_skill_routing.py"
PACKAGING_CHECK = TOOLS_DIR / "check_skill_packaging.py"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--static", action="store_true")
    parser.add_argument("--allow-branded", action="store_true")
    parser.add_argument(
        "--require-claude",
        action="store_true",
        help="fail instead of skipping when the Claude CLI is unavailable",
    )
    args = parser.parse_args()

    test_command = [sys.executable, str(TESTS)]
    if args.static:
        test_command.append("--static")
    if args.allow_branded:
        test_command.append("--allow-branded")
    environment = dict(os.environ)
    environment.setdefault("PYTHONUTF8", "1")
    fast_rc = run_fast_script_checks(environment)
    if fast_rc != 0:
        return fast_rc

    packaging = subprocess.run(
        [sys.executable, str(PACKAGING_CHECK)],
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    if packaging.returncode != 0:
        return packaging.returncode

    tests = subprocess.run(
        test_command,
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    if tests.returncode != 0:
        return tests.returncode

    routing_command = [sys.executable, str(ROUTING_EVALUATOR)]
    if args.require_claude:
        routing_command.append("--require-claude")
    routing = subprocess.run(
        routing_command,
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    if routing.returncode != 0:
        return routing.returncode

    claude_command = resolve_claude_command()
    if claude_command is None:
        if args.require_claude:
            print("FAIL — Claude CLI is required but unavailable", file=sys.stderr)
            return 2
        print("SKIP — Claude CLI unavailable; run `claude plugin validate .` before release")
        return 0
    validated = subprocess.run(
        [*claude_command, "plugin", "validate", "."],
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    return validated.returncode


if __name__ == "__main__":
    raise SystemExit(main())
