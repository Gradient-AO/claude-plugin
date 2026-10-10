#!/usr/bin/env python3
"""Run the local release gate, including Claude validation when available."""

from __future__ import annotations

import argparse
import os
import pathlib
import shutil
import subprocess
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
REPOSITORY = ROOT.parents[1]
TESTS = ROOT / "tests" / "run_tests.py"


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
    tests = subprocess.run(
        test_command,
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    if tests.returncode != 0:
        return tests.returncode

    claude = shutil.which("claude")
    if claude is None:
        if args.require_claude:
            print("FAIL — Claude CLI is required but unavailable", file=sys.stderr)
            return 2
        print("SKIP — Claude CLI unavailable; run `claude plugin validate .` before release")
        return 0
    validated = subprocess.run(
        [claude, "plugin", "validate", "."],
        cwd=REPOSITORY,
        env=environment,
        check=False,
    )
    return validated.returncode


if __name__ == "__main__":
    raise SystemExit(main())
