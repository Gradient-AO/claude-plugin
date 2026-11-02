#!/usr/bin/env python3
"""Package release metadata with every skill.

Common report files live once at plugin-level ``shared/`` and are resolved
through ``CLAUDE_PLUGIN_ROOT``. Run after a plugin version bump:
    python tools/sync_shared.py          # sync
    python tools/sync_shared.py --check  # exit 1 if any copy differs (use before packaging)
"""
import hashlib, json, pathlib, shutil, sys
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_RELEASE_REFERENCE = pathlib.Path("references/plugin-release.json")
FILES = {}
TREES = {}
INTERNAL_RENDER_TARGETS = ()
INTERNAL_SCRIPT_FILES = set()
INTERNAL_REFERENCE_FILES = set()

CHAT_DELIVERY = re.compile(r"^\s+delivery:\s*chat\s*$", re.MULTILINE)


def is_chat_only(skill):
    """Return whether a skill deliberately produces only an in-chat response."""
    return bool(CHAT_DELIVERY.search((skill / "SKILL.md").read_text(encoding="utf-8")))

def chat_shared_files(skill):
    """Shared references are no longer copied into skill folders."""
    return ()


TEXT_SUFFIXES = {".py", ".md", ".json", ".txt"}


def digest(p):
    data = p.read_bytes()
    if p.suffix in TEXT_SUFFIXES:
        # Windows checkouts with core.autocrlf rewrite line endings per file.
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()[:12]


def plugin_release_text():
    """Return skill-visible metadata for the installed marketplace release."""
    manifest = json.loads(
        (ROOT / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )
    payload = {
        "schema": "gradient-cio-plugin-release/v1",
        "marketplace": "gradientcio",
        "plugin": manifest["name"],
        "release_version": manifest["version"],
        "update_command": "/plugin marketplace update gradientcio",
        "version_semantics": (
            "SKILL.md metadata.version values are component contract versions, "
            "not the plugin release version."
        ),
    }
    return json.dumps(payload, indent=2) + "\n"


def sync_plugin_release(skill, check, expected):
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


def shared_files():
    """Yield canonical source/destination pairs, including contract trees."""
    yield from FILES.items()
    for source_root, destination_root in TREES.items():
        for source in sorted((ROOT / source_root).rglob("*")):
            if source.is_file():
                relative = source.relative_to(ROOT / source_root)
                yield (
                    str(source.relative_to(ROOT)),
                    str(pathlib.Path(destination_root) / relative),
                )

def main():
    check = "--check" in sys.argv
    bad = 0
    release_text = plugin_release_text()
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        bad += sync_plugin_release(skill, check, release_text)
        pairs = chat_shared_files(skill) if is_chat_only(skill) else shared_files()
        for src, rel in pairs:
            s, d = ROOT / src, skill / rel
            if s.resolve() == d.resolve():
                continue
            if check:
                if not d.exists() or digest(d) != digest(s):
                    print(f"OUT OF SYNC: {skill.name}/{rel}"); bad += 1
            else:
                d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(s, d)
                print(f"synced {skill.name}/{rel} ({digest(s)})")
    for target in INTERNAL_RENDER_TARGETS:
        for src, rel in shared_files():
            if not (
                rel in INTERNAL_SCRIPT_FILES
                or rel in INTERNAL_REFERENCE_FILES
            ):
                continue
            s, d = ROOT / src, target / rel
            if check:
                if not d.exists() or digest(d) != digest(s):
                    print(f"OUT OF SYNC: {target.relative_to(ROOT)}/{rel}")
                    bad += 1
            else:
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(s, d)
                print(
                    f"synced {target.relative_to(ROOT)}/{rel} ({digest(s)})"
                )
    if check:
        print("all copies in sync" if not bad else f"{bad} copies out of sync")
        sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
