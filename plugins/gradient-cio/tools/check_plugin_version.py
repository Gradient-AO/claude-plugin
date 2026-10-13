#!/usr/bin/env python3
"""Report the active plugin version and detect newer duplicate installs."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Iterable


PLUGIN_NAME = "gradient-cio"
MANIFEST_PATH = Path(".claude-plugin") / "plugin.json"
SEMVER = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")


def version_tuple(version: str) -> tuple[int, int, int]:
    """Parse the release's strict three-part semantic version."""
    match = SEMVER.fullmatch(version)
    if match is None:
        raise ValueError(f"invalid semantic version '{version}'")
    return tuple(int(part) for part in match.groups())


def plugin_version(plugin_root: Path) -> str:
    """Read one gradient-cio plugin manifest."""
    manifest = plugin_root / MANIFEST_PATH
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    if payload.get("name") != PLUGIN_NAME:
        raise ValueError(f"{manifest} is not a {PLUGIN_NAME} manifest")
    version = payload.get("version")
    if not isinstance(version, str):
        raise ValueError(f"{manifest} has no string version")
    version_tuple(version)
    return version


def known_scan_roots(active_plugin: Path) -> list[Path]:
    """Return repository-sibling and common Claude/Cursor cache roots."""
    home = Path.home()
    roots = [
        active_plugin.parent,
        home / ".claude" / "plugins" / "cache",
        home / ".cursor" / "plugins" / "cache",
    ]
    for variable, suffix in (
        ("APPDATA", ("Claude", "plugins", "cache")),
        ("LOCALAPPDATA", ("Cursor", "plugins", "cache")),
    ):
        base = os.environ.get(variable)
        if base:
            roots.append(Path(base).joinpath(*suffix))
    return roots


def scan_duplicates(
    active_plugin: Path,
    scan_roots: Iterable[Path],
) -> list[tuple[Path, str]]:
    """Find valid duplicate gradient-cio manifests below known roots."""
    active = active_plugin.resolve()
    found: dict[Path, str] = {}
    for root in scan_roots:
        if not root.is_dir():
            continue
        for manifest in root.rglob(MANIFEST_PATH.as_posix()):
            plugin_root = manifest.parent.parent.resolve()
            if plugin_root == active:
                continue
            try:
                version = plugin_version(plugin_root)
            except (OSError, json.JSONDecodeError, ValueError):
                continue
            found[plugin_root] = version
    return sorted(found.items(), key=lambda item: str(item[0]).casefold())


def evaluate_versions(
    active_plugin: Path,
    scan_roots: Iterable[Path],
) -> tuple[str, list[tuple[Path, str]], list[tuple[Path, str]]]:
    """Return active version, all duplicates and only newer duplicates."""
    active_version = plugin_version(active_plugin)
    duplicates = scan_duplicates(active_plugin, scan_roots)
    active_key = version_tuple(active_version)
    newer = [
        (path, version)
        for path, version in duplicates
        if version_tuple(version) > active_key
    ]
    return active_version, duplicates, newer


def main() -> int:
    """Run the deterministic plugin-version preflight."""
    default_active = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active-plugin", type=Path, default=default_active)
    parser.add_argument(
        "--scan-root",
        action="append",
        type=Path,
        help="additional install root to scan (repeatable)",
    )
    args = parser.parse_args()
    scan_roots = known_scan_roots(args.active_plugin)
    scan_roots.extend(args.scan_root or [])
    try:
        active_version, duplicates, newer = evaluate_versions(
            args.active_plugin,
            scan_roots,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"ERROR — plugin version preflight failed: {error}")
        return 2
    print(f"Active {PLUGIN_NAME} version: {active_version}")
    if not duplicates:
        print("Duplicate installs: none found")
    for path, version in duplicates:
        relation = "NEWER" if (path, version) in newer else "not newer"
        print(f"Duplicate install: {version} ({relation}) — {path}")
    if newer:
        print("FAIL — a newer gradient-cio duplicate exists; use that install.")
        return 1
    print("PASS — no newer gradient-cio duplicate exists.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
