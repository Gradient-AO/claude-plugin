#!/usr/bin/env python3
"""Check that every skill works inside the installed plugin bundle.

The report runtime, references, tool catalog, and fonts are canonical at the
plugin level. This copies the complete plugin into an empty temporary
directory, imports every skill validator against that shared runtime, checks
the Inter fonts and release descriptor, and confirms the manifest versions and
the shipped skill list agree.

    python plugins/gradient-cio/tools/check_skill_packaging.py
"""

from __future__ import annotations

import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (
    CANVAS_OUTPUT,
    CANVAS_RENDERERS,
    CHAT_DELIVERY,
    PLUGIN_ROOT,
    REPO_ROOT,
    build_plugin_release_payload,
    load_plugin_manifest,
)

ROOT = PLUGIN_ROOT
REPOSITORY = REPO_ROOT
REQUIRED_FONTS = ("inter-latin-regular.ttf", "inter-latin-semibold.ttf")
NAME_LINE = re.compile(r"^name:\s*(\S+)\s*$", re.MULTILINE)
PLUGIN_ROOT_ASSIGNMENT = re.compile(
    r"^\s*(\w+)\s*=\s*Path\(__file__\)\.resolve\(\)\.parents\[\d+\]",
    re.MULTILINE,
)


def shipped_skills() -> list[pathlib.Path]:
    """Return skill folders that contain a SKILL.md."""
    return sorted(
        path
        for path in (ROOT / "skills").iterdir()
        if path.is_dir() and (path / "SKILL.md").is_file()
    )


def tracked_skill_names() -> set[str] | None:
    """Return skill folders present in the releasable working tree."""
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--cached",
            "--others",
            "--exclude-standard",
            "--",
            "plugins/gradient-cio/skills/*/SKILL.md",
        ],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None
    return {
        pathlib.PurePosixPath(line).parent.name
        for line in result.stdout.splitlines()
        if line and (REPOSITORY / pathlib.PurePosixPath(line)).is_file()
    }


def plugin_manifest() -> dict[str, str]:
    """Read the canonical plugin identity used by packaging checks."""
    return load_plugin_manifest(ROOT)


def is_repository_checkout(
    repository: pathlib.Path = REPOSITORY,
    plugin_root: pathlib.Path = ROOT,
) -> bool:
    """Return whether the plugin is running from this repository layout."""
    expected_root = repository / "plugins" / "gradient-cio"
    markers = (
        repository / ".git",
        repository / "CLAUDE.md",
        repository / "CHANGELOG.md",
    )
    return plugin_root.resolve() == expected_root.resolve() and any(
        marker.exists() for marker in markers
    )


def check_versions(
    plugin: dict[str, str],
    repository: pathlib.Path = REPOSITORY,
    plugin_root: pathlib.Path = ROOT,
) -> list[str]:
    marketplace_path = repository / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.is_file():
        if is_repository_checkout(repository, plugin_root):
            return ["repository marketplace.json is missing"]
        return []
    marketplace = json.loads(
        marketplace_path.read_text(encoding="utf-8")
    )
    entries = [entry for entry in marketplace.get("plugins", []) if entry.get("name") == plugin["name"]]
    if len(entries) != 1:
        return [f"marketplace.json must list {plugin['name']} exactly once"]
    if entries[0].get("version") != plugin["version"]:
        return [
            f"plugin.json version {plugin['version']} does not match "
            f"marketplace.json version {entries[0].get('version')}"
        ]
    return []


def check_skill(
    skill: pathlib.Path,
    scratch: pathlib.Path,
    installed_root: pathlib.Path,
    plugin: dict[str, str],
) -> list[str]:
    failures: list[str] = []
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    match = NAME_LINE.search(text)
    if match is None or match.group(1) != skill.name:
        failures.append(f"{skill.name}: SKILL.md name does not match the folder name")
    release_path = skill / "references" / "plugin-release.json"
    try:
        release = json.loads(release_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        failures.append(f"{skill.name}: plugin-release.json is unavailable ({error})")
    else:
        expected_release = build_plugin_release_payload(plugin)
        if any(release.get(key) != value for key, value in expected_release.items()):
            failures.append(
                f"{skill.name}: plugin-release.json does not match the plugin manifest"
            )
    scripts = skill / "scripts"
    for script in sorted(scripts.glob("*.py")):
        source = script.read_text(encoding="utf-8")
        for assignment in PLUGIN_ROOT_ASSIGNMENT.finditer(source):
            root_name = re.escape(assignment.group(1))
            if re.search(rf"{root_name}\s*/\s*[\"']tools[\"']", source):
                failures.append(
                    f"{skill.name}: {script.name} imports plugin-root tools instead "
                    "of its bundled scripts"
                )
    if CHAT_DELIVERY.search(text):
        return failures
    if CANVAS_OUTPUT.search(text):
        renderer = CANVAS_RENDERERS.get(skill.name, "")
        required = (
            skill / "scripts" / renderer,
            skill / "scripts" / "brand.py",
            skill / "references" / "canvas-spec.md",
            skill / "assets" / "fonts" / "Inter-Regular.ttf",
        )
        for path in required:
            if not path.is_file():
                failures.append(
                    f"{skill.name}: missing canvas runtime "
                    f"{path.relative_to(skill)}"
                )
        return failures

    isolated = installed_root / "skills" / skill.name
    scripts = isolated / "scripts"
    for font in REQUIRED_FONTS:
        if not (installed_root / "assets" / "fonts" / font).is_file():
            failures.append(f"{skill.name}: plugin assets/fonts/{font} is missing")
    validators = sorted(path.stem for path in scripts.glob("*valid*.py")) if scripts.is_dir() else []
    if not validators:
        failures.append(f"{skill.name}: no validator scripts found in scripts/")
        return failures
    importer = (
        "import importlib, sys\n"
        f"sys.path.insert(0, {str(scripts)!r})\n"
        f"for name in {validators!r}:\n"
        "    importlib.import_module(name)\n"
    )
    result = subprocess.run(
        [sys.executable, "-I", "-c", importer],
        cwd=scratch,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        last_line = (result.stderr.strip().splitlines() or ["unknown error"])[-1]
        failures.append(f"{skill.name}: validators fail to import on their own ({last_line})")
    return failures


def main() -> int:
    plugin = plugin_manifest()
    failures = check_versions(plugin)
    skills = shipped_skills()
    tracked = tracked_skill_names()
    if tracked is not None:
        shipped_names = {skill.name for skill in skills}
        for name in sorted(shipped_names - tracked):
            failures.append(f"{name}: skill folder is not tracked by git and would not ship")
        for name in sorted(tracked - shipped_names):
            failures.append(f"{name}: tracked SKILL.md is missing from the working tree")
    with tempfile.TemporaryDirectory(prefix="gradient-skill-packaging-") as directory:
        scratch = pathlib.Path(directory)
        installed_root = scratch / "install" / "gradient-cio"
        shutil.copytree(
            ROOT,
            installed_root,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        for skill in skills:
            failures.extend(check_skill(skill, scratch, installed_root, plugin))
    if failures:
        for failure in failures:
            print(f"FAIL — {failure}", file=sys.stderr)
        return 1
    print(f"OK — {len(skills)} skills resolve the installed plugin bundle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
