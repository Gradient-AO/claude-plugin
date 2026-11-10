"""Shared maintainer tool helpers for paths, frontmatter, digests, and PPTX normalization."""

from __future__ import annotations

import datetime
import hashlib
import io
import json
import os
import pathlib
import re
import shutil
import tempfile
import zipfile
from typing import Any

TOOLS_DIR = pathlib.Path(__file__).resolve().parent
PLUGIN_ROOT = TOOLS_DIR.parent
REPO_ROOT = PLUGIN_ROOT.parents[1]
SKILLS_DIR = PLUGIN_ROOT / "skills"
SHARED_DIR = PLUGIN_ROOT / "shared"
PLUGIN_MANIFEST_PATH = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MARKETPLACE_MANIFEST_PATH = REPO_ROOT / ".claude-plugin" / "marketplace.json"

CHAT_DELIVERY = re.compile(r"^\s+delivery:\s*chat\s*$", re.MULTILINE)
CANVAS_OUTPUT = re.compile(r"^\s+output:\s*[\"']?canvas[\"']?\s*$", re.MULTILINE)
TEXT_SUFFIXES = frozenset({".py", ".md", ".json", ".txt"})

FIXED_TIME = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
ZIP_TIME = (2020, 1, 1, 0, 0, 0)
CORE_TIMESTAMP = re.compile(
    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)"
)

CANVAS_RENDERERS = {
    "gradient-portfolio-lens": "pa_viz.py",
    "gradient-signal-spotlight": "render_spotlight.py",
    "gradient-risk-pulse": "render_riskpulse.py",
    "gradient-tactical-dashboard": "render_dashboard.py",
    "gradient-ask-gradient": "render_ask.py",
}

EXAMPLE_DIRECT_SOURCES = {
    "gradient-odd-ddq-reconcile": "ddq.json",
    "gradient-manager-evaluation-single": "idd-manager-performance-single.json",
    "gradient-manager-evaluation-compare": "idd-manager-performance-compare.json",
    "gradient-manager-evaluation-fit": "idd-portfolio-fit.json",
    "gradient-idd-private-markets-pme": "idd-private-markets-pme.json",
    "gradient-allocation-study-total-plan": "allocation-total-plan.json",
    "gradient-allocation-study-fixed-income": "construction-fixed-income.json",
    "gradient-allocation-study-global-public-equity": "construction-global-public-equity.json",
    "gradient-decision-ic-memo": "ic-memo.json",
    "gradient-odd-report-compare": "compare.json",
    "gradient-odd-manager-monitor": "digest.json",
    "gradient-odd-manager-monitor-triage": "triage.json",
    "gradient-allocation-study-marketable-alternatives": "construction-marketable-alternatives.json",
    "gradient-liquidity-pacing": "liquidity-pacing.json",
    "gradient-odd-report": "odd.json",
    "gradient-portfolio-attribution": "portfolio-attribution-report.json",
    "gradient-portfolio-attribution-lanes-fallback": "attribution-compare-fallback.json",
    "gradient-portfolio-attribution-lanes-three-lane": "attribution-compare-three-lane.json",
    "gradient-portfolio-review": "portfolio-comprehensive.json",
    "gradient-allocation-study-private-markets": "construction-private-markets.json",
    "gradient-allocation-study-real-assets": "construction-real-assets.json",
    "gradient-setup": "setup.json",
}

EXAMPLE_GIPS_SOURCES = {
    "internal-gips-review-asset-owner": (
        "gips-asset-owner-review.md",
        "gips-asset-owner-review-visuals.json",
        "gips-asset-owner-review-meta.json",
    ),
    "internal-gips-review-firm": (
        "gips-report-review.md",
        "gips-report-review-visuals.json",
        "gips-report-review-meta.json",
    ),
}


def resolve_claude_command() -> list[str] | None:
    """Resolve the Claude CLI or an npx fallback."""
    claude = shutil.which("claude")
    if claude is not None:
        return [claude]
    npx = shutil.which("npx")
    if npx is not None:
        return [npx, "-y", "@anthropic-ai/claude-code"]
    return None


def normalized_digest(path: pathlib.Path, *, length: int | None = None) -> str:
    """Compute a CRLF-normalized SHA-256 hex digest for text/binary files."""
    data = path.read_bytes()
    if path.suffix in TEXT_SUFFIXES:
        data = data.replace(b"\r\n", b"\n")
    digest = hashlib.sha256(data).hexdigest()
    return digest[:length] if length is not None else digest


def parse_skill_frontmatter_text(text: str) -> dict[str, str]:
    """Parse flat YAML frontmatter key/value pairs from SKILL.md text."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        raw = raw.strip()
        if raw.startswith('"'):
            try:
                values[key.strip()] = json.loads(raw)
                continue
            except json.JSONDecodeError:
                pass
        values[key.strip()] = raw.strip("'\"")
    return values


def parse_skill_frontmatter(path: pathlib.Path) -> dict[str, str]:
    """Read and parse flat YAML frontmatter from a SKILL.md path."""
    text = path.read_text(encoding="utf-8")
    values = parse_skill_frontmatter_text(text)
    if not values:
        raise ValueError(f"{path}: missing frontmatter")
    return values


def load_plugin_manifest(plugin_root: pathlib.Path = PLUGIN_ROOT) -> dict[str, Any]:
    """Load the plugin manifest JSON."""
    return json.loads(
        (plugin_root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
    )


def build_plugin_release_payload(manifest: dict[str, Any]) -> dict[str, str]:
    """Build the canonical references/plugin-release.json dictionary."""
    return {
        "schema": "gradient-cio-plugin-release/v1",
        "marketplace": "gradientcio",
        "plugin": str(manifest["name"]),
        "release_version": str(manifest["version"]),
        "update_command": "/plugin marketplace update gradientcio",
        "version_semantics": (
            "SKILL.md metadata.version values are component contract versions, "
            "not the plugin release version."
        ),
    }


def _normalized_zip_bytes(payload: bytes) -> bytes:
    source_buffer = io.BytesIO(payload)
    target_buffer = io.BytesIO()
    with zipfile.ZipFile(source_buffer, "r") as source, zipfile.ZipFile(
        target_buffer, "w"
    ) as target:
        for source_info in source.infolist():
            content = source.read(source_info.filename)
            if source_info.filename == "docProps/core.xml":
                content = CORE_TIMESTAMP.sub(
                    rb"\g<1>2020-01-01T00:00:00Z\g<2>", content
                )
            info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
            info.compress_type = source_info.compress_type
            info.comment = source_info.comment
            info.extra = source_info.extra
            info.internal_attr = source_info.internal_attr
            info.external_attr = source_info.external_attr
            info.create_system = source_info.create_system
            target.writestr(info, content)
    return target_buffer.getvalue()


def normalize_pptx(path: pathlib.Path, *, nested_xlsx: bool = True) -> None:
    """Remove volatile Office timestamps and normalize ZIP member dates."""
    from pptx import Presentation

    presentation = Presentation(path)
    presentation.core_properties.created = FIXED_TIME
    presentation.core_properties.modified = FIXED_TIME
    presentation.core_properties.last_modified_by = "GradientCIO"
    presentation.save(path)

    with tempfile.NamedTemporaryFile(
        dir=path.parent, suffix=".pptx", delete=False
    ) as handle:
        temporary = pathlib.Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary, "w"
        ) as target:
            for source_info in source.infolist():
                content = source.read(source_info.filename)
                if nested_xlsx and source_info.filename.endswith(".xlsx"):
                    content = _normalized_zip_bytes(content)
                info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
                info.compress_type = source_info.compress_type
                info.comment = source_info.comment
                info.extra = source_info.extra
                info.internal_attr = source_info.internal_attr
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                target.writestr(info, content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
