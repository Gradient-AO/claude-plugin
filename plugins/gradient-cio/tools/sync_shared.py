#!/usr/bin/env python3
"""Package canonical shared files and release metadata with every skill.

Run after a plugin version bump or any change to a file listed in FILES:
    python tools/sync_shared.py          # sync
    python tools/sync_shared.py --check  # exit 1 if any copy differs (use before packaging)
"""
import hashlib, json, pathlib, shutil, sys
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
PLUGIN_RELEASE_REFERENCE = pathlib.Path("references/plugin-release.json")
FILES = {"shared/gradient_report.py": "scripts/gradient_report.py",
         "shared/gradient_pptx.py": "scripts/gradient_pptx.py",
         "shared/report_theme.py": "scripts/report_theme.py",
         "shared/report_layout.py": "scripts/report_layout.py",
         "shared/render.py": "scripts/render.py",
         "shared/compose_report.py": "scripts/compose_report.py",
         "shared/check_layout.py": "scripts/check_layout.py",
         "shared/qa_report.py": "scripts/qa_report.py",
         "shared/analysis_quality.py": "scripts/analysis_quality.py",
         "shared/validate_handoff.py": "scripts/validate_handoff.py",
         "tools/layout_budget_schema.py": "scripts/layout_budget_schema.py",
         "tools/report_constants.py": "scripts/report_constants.py",
         "tools/report_json_validator.py": "scripts/report_json_validator.py",
         "tools/report_vocab.py": "scripts/report_vocab.py",
         "tools/construction_report_validator.py": "scripts/construction_report_validator.py",
         "tools/idd_report_validator.py": "scripts/idd_report_validator.py",
         "skills/gradient-setup/references/public-tools.json": "references/public-tools.json",
         "shared/report-style.md": "references/report-style.md",
         "shared/writing-standards.md": "references/writing-standards.md",
         "shared/chart-data.md": "references/chart-data.md",
         "shared/module-scope.md": "references/module-scope.md"}

TREES = {
    "assets/fonts": "assets/fonts",
    "shared/contracts": "references/contracts",
}
INTERNAL_RENDER_TARGETS = (
    ROOT / "internal" / "gips-evidence-review",
)
INTERNAL_SCRIPT_FILES = {
    "scripts/gradient_report.py",
    "scripts/gradient_pptx.py",
    "scripts/report_theme.py",
    "scripts/report_layout.py",
    "scripts/render.py",
    "scripts/compose_report.py",
    "scripts/check_layout.py",
    "scripts/qa_report.py",
    "scripts/analysis_quality.py",
    "scripts/validate_handoff.py",
    "scripts/layout_budget_schema.py",
}
INTERNAL_REFERENCE_FILES = {
    "references/module-scope.md",
    "references/report-style.md",
}

CHAT_DELIVERY = re.compile(r"^\s+delivery:\s*chat\s*$", re.MULTILINE)


def is_chat_only(skill):
    """Return whether a skill deliberately produces only an in-chat response."""
    return bool(CHAT_DELIVERY.search((skill / "SKILL.md").read_text(encoding="utf-8")))

def chat_shared_files(skill):
    """Yield shared references needed by chat skills with module boundaries."""
    text = (skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r'^\s+modules:\s*["\']?([^"\'\n]+)', text, re.MULTILINE)
    if match is None or match.group(1).strip() == "none":
        return ()
    return (("shared/module-scope.md", "references/module-scope.md"),)


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
