#!/usr/bin/env python3
"""Package release metadata and controlled shared contracts with skills.

Common report files live once at plugin-level ``shared/`` and are resolved
through ``CLAUDE_PLUGIN_ROOT`` unless explicitly packaged for a skill. Run
after a plugin version bump or shared-contract edit:
    python plugins/gradient-cio/tools/sync_shared.py          # sync
    python plugins/gradient-cio/tools/sync_shared.py --check  # exit 1 if any copy differs
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import (
    PLUGIN_ROOT,
    build_plugin_release_payload,
    load_plugin_manifest,
    normalized_digest,
)

ROOT = PLUGIN_ROOT
PLUGIN_RELEASE_REFERENCE = pathlib.Path("references/plugin-release.json")
EXPECTED_RETURN_SKILLS = frozenset(
    {
        "gradient-allocation-study",
        "gradient-decision-ic-memo",
        "gradient-portfolio-attribution",
        "gradient-portfolio-review",
    }
)
TARGETED_FILES = {
    (
        "shared/contracts/expected-return-sources.md",
        "references/contracts/expected-return-sources.md",
    ): EXPECTED_RETURN_SKILLS,
}


def digest(path: pathlib.Path) -> str:
    return normalized_digest(path, length=12)


def plugin_release_text() -> str:
    """Return skill-visible metadata for the installed marketplace release."""
    payload = build_plugin_release_payload(load_plugin_manifest(ROOT))
    return json.dumps(payload, indent=2) + "\n"


def sync_plugin_release(
    skill: pathlib.Path, check: bool, expected: str
) -> int:
    """Write or validate the release reference included with every skill."""
    destination = skill / PLUGIN_RELEASE_REFERENCE
    if check:
        actual = (
            destination.read_text(encoding="utf-8").replace("\r\n", "\n")
            if destination.exists()
            else ""
        )
        if actual != expected:
            print(f"OUT OF SYNC: {skill.name}/{PLUGIN_RELEASE_REFERENCE}")
            return 1
        return 0
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(expected, encoding="utf-8")
    checksum = hashlib.sha256(expected.encode("utf-8")).hexdigest()[:12]
    print(f"synced {skill.name}/{PLUGIN_RELEASE_REFERENCE} ({checksum})")
    return 0


def targeted_shared_files(skill: pathlib.Path) -> tuple[tuple[str, str], ...]:
    """Return canonical files packaged only with their declared skills."""
    return tuple(
        (source, destination)
        for (source, destination), skill_names in TARGETED_FILES.items()
        if skill.name in skill_names
    )


def main() -> int:
    check = "--check" in sys.argv
    bad = 0
    release_text = plugin_release_text()
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        bad += sync_plugin_release(skill, check, release_text)
        for src, rel in targeted_shared_files(skill):
            source, destination = ROOT / src, skill / rel
            if source.resolve() == destination.resolve():
                continue
            if check:
                if not destination.exists() or digest(destination) != digest(source):
                    print(f"OUT OF SYNC: {skill.name}/{rel}")
                    bad += 1
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
                print(f"synced {skill.name}/{rel} ({digest(source)})")
    if check:
        print("all copies in sync" if not bad else f"{bad} copies out of sync")
        return 1 if bad else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
