"""Public-example and analytical-writing contract checks."""

import importlib.util
import json
import re

from suites.harness import FIX, ROOT, check, review_callout
from report_layout import prepare_report_for_render
from report_theme import DEFAULT_COVER_DISCLOSURE, FULL_SAMPLE_DISCLOSURE


ANALYSIS_EXAMPLE_CONTRACTS = {
    "gradient-portfolio-construction": (
        True,
        (
            r"Target Portfolio Structure",
            r"Forward Return and Risk",
            r"Liquidity and Denominator Risk",
            r"Rates and Credit Context",
            r"Factor Exposures and Concentration",
            r"Manager and Issuer Concentration",
            r"Target Strategy and Manager Structure",
            r"Factor, Currency and Concentration Evidence",
            r"Target Sub-Segment Structure",
            r"Inflation, Commodity and Diversification Context",
        ),
    ),
    "gradient-idd-manager-performance": (
        True,
        (
            r"Absolute risk and return",
            r"Relative performance",
            r"Reliability and date-window sensitivity",
            r"Risk and return",
            r"Relative performance and capture",
            r"Correlation and robustness",
            r"Window sensitivity",
            r"Rolling evidence",
            r"Regime evidence",
            r"Candidate evidence",
            r"Performance comparison",
            r"Advance/reserve/reject rationale",
        ),
    ),
    "gradient-idd-private-markets-pme": (
        True,
        (
            r"PME and direct alpha",
            r"IRR and multiples",
            r"Benchmark sensitivity",
            r"Partial evidence",
        ),
    ),
    "gradient-portfolio-review": (
        True,
        (
            r"Summary",
            r"Performance",
            r"Allocation",
            r"Look-through",
            r"Risk",
            r"Outlook",
            r"Historical Returns",
            r"Historical Attribution",
            r"Allocation and Policy Compliance",
            r"Exposures and Concentration",
            r"Realized Risk and Decomposition",
            r"Projected Return and Risk Decomposition",
            r"Liquidity and Commitments",
        ),
    ),
    "gradient-portfolio-attribution": (
        True,
        (
            r"Historical Returns Context",
            r"Historical Attribution",
            r"Governed Ex Ante Attribution",
            r"Historical-versus-Ex-Ante Scope and Comparison",
            r"Simulated Attribution",
            r"Cross-Lane Comparison",
        ),
    ),
    "gradient-odd-report": (
        False,
        (
            r"Firm profile & ownership",
            r"Regulatory, conflicts & custody",
            r"Peer positioning",
            r"Fund operations & service providers",
            r"Reported equity holdings \(Form 13F\)",
            r"Monitoring, findings & DDQ",
            r"Side-by-side comparison",
            r"Operational flags",
            r"Form 13F overlap",
            r"ADV–13F consistency and events",
        ),
    ),
    "gradient-odd-manager-monitor": (
        False,
        (r"Changes and alerts", r"Review calendar"),
    ),
    "gradient-odd-ddq-reconcile": (
        True,
        (
            r"Discrepancies and follow-ups",
            r"Firm reconciliation",
            r"Fund reconciliation(?: — .+)?",
        ),
    ),
    "gradient-decision-ic-memo": (
        True,
        (
            r"Executive Summary",
            r"Portfolio Snapshot",
            r"IPS Compliance",
            r"Performance & Attribution",
            r"Factor Exposures & Concentration",
            r"Expected Return & Risk",
            r"Stress Tests & Scenarios",
            r"Liquidity",
            r"Manager & Operational Diligence",
            r"Market Context",
            r"Proposed Changes & Impact",
            r"Risks & Mitigants",
        ),
    ),
}


ANALYSIS_EXAMPLE_PATHS = {
    "gradient-idd-manager-performance": (
        "references/analysis-examples.md",
        "references/modes/shortlist-analysis-examples.md",
    ),
    "gradient-odd-report": (
        "references/analysis-examples.md",
        "references/modes/compare-analysis-examples.md",
    ),
    "gradient-portfolio-attribution": (
        "references/analysis-examples.md",
        "references/modes/compare-lanes-analysis-examples.md",
    ),
}


ANALYSIS_LABELS = (
    "Observation:",
    "Why it matters:",
    "Uncertainty:",
    "What would change the view:",
)


def _clean_example_heading(heading):
    heading = re.sub(r"^\d+(?:\.\d+)*[.)]?\s+", "", heading.strip())
    return heading.strip().strip("`*_")


def _clean_example_text(text):
    lines = []
    for line in text.splitlines():
        line = re.sub(r"^\s*(?:>\s*)?(?:[-*]\s+)?", "", line)
        if line.strip() == "```":
            continue
        lines.append(line.strip())
    cleaned = " ".join(line for line in lines if line)
    cleaned = re.sub(r"[*_`]", "", cleaned)
    cleaned = re.sub(
        r"^Strong(?: example)?(?:\s*\(TEST\))?\s*:?\s*",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def _strong_examples(markdown):
    headings = list(re.finditer(r"(?m)^#{2,4}\s+(.+?)\s*$", markdown))
    examples = {}
    for index, heading_match in enumerate(headings):
        body_end = (
            headings[index + 1].start()
            if index + 1 < len(headings)
            else len(markdown)
        )
        body = markdown[heading_match.end():body_end]
        strong = re.search(r"(?im)^.*\bstrong\b.*$", body)
        if strong is None:
            continue
        candidate = body[strong.start():]
        weak = re.search(
            r"(?im)^\s*(?:>\s*)?(?:\*\*)?weak"
            r"(?: example| contrast| version)?(?:\*\*)?\s*:?.*$",
            candidate,
        )
        if weak is not None:
            candidate = candidate[:weak.start()]
        examples[_clean_example_heading(heading_match.group(1))] = (
            _clean_example_text(candidate),
            "(TEST)" in candidate,
        )
    return examples


def public_example_cover_checks():
    """Keep committed examples polished while retaining truthful disclosure."""
    generator_path = ROOT / "tools" / "generate_examples.py"
    spec = importlib.util.spec_from_file_location(
        "public_example_generator_checks",
        generator_path,
    )
    if spec is None or spec.loader is None:
        check(False, "public example generator can be loaded")
        return
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    forbidden = re.compile(
        r"(?i)\b(?:test|fixture|render test|synthetic test|mcp|probe|"
        r"contract checks?|request[_ -]?id)\b"
    )
    public_source_forbidden = re.compile(
        r"\bTEST\b|(?i:\b(?:fixture|fictional|render test|synthetic test)\b)"
    )
    errors = []
    for filename in sorted(set(module.DIRECT_SOURCES.values())):
        report = json.loads((FIX / filename).read_text(encoding="utf-8"))
        source_match = public_source_forbidden.search(
            json.dumps(report, ensure_ascii=False)
        )
        if source_match:
            errors.append(
                f"{filename}: public report contains {source_match.group(0)!r}"
            )
        metadata = report.get("meta", {})
        cover_values = [
            metadata.get(field, "")
            for field in (
                "title",
                "subtitle",
                "eyebrow",
                "running_head",
                "confidentiality",
            )
        ]
        cover_values.extend(
            value
            for fact in metadata.get("cover_facts", [])
            for value in fact
        )
        match = forbidden.search(" ".join(str(value) for value in cover_values))
        if match:
            errors.append(f"{filename}: cover contains {match.group(0)!r}")
        if metadata.get("cover_disclosure") != DEFAULT_COVER_DISCLOSURE:
            errors.append(f"{filename}: missing compact cover disclosure")
        facts = metadata.get("cover_facts", [])
        if not isinstance(facts, list) or not 1 <= len(facts) <= 4:
            errors.append(f"{filename}: cover must use one to four facts")
        try:
            prepared = prepare_report_for_render(report)
        except Exception as error:
            errors.append(f"{filename}: disclosure preparation failed: {error}")
            continue
        appendix = next(
            (
                section
                for section in prepared.get("sections", [])
                if section.get("num") == "A"
                or "Sources and methods" in str(section.get("title", ""))
            ),
            {},
        )
        appendix_text = " ".join(
            json.dumps(appendix, ensure_ascii=False)
            .replace("\\r", " ")
            .replace("\\n", " ")
            .split()
        )
        disclosure_text = " ".join(FULL_SAMPLE_DISCLOSURE.split())
        if disclosure_text not in appendix_text:
            errors.append(f"{filename}: appendix lacks full sample disclosure")
    for markdown_name, visuals_name, metadata_name in module.GIPS_SOURCES.values():
        metadata = json.loads((FIX / metadata_name).read_text(encoding="utf-8"))
        markdown = (FIX / markdown_name).read_text(encoding="utf-8")
        visuals = (FIX / visuals_name).read_text(encoding="utf-8")
        source_match = public_source_forbidden.search(
            f"{markdown}\n{visuals}\n{json.dumps(metadata, ensure_ascii=False)}"
        )
        if source_match:
            errors.append(
                f"{markdown_name}: public report contains {source_match.group(0)!r}"
            )
        cover_text = json.dumps(metadata, ensure_ascii=False)
        match = forbidden.search(cover_text)
        if match:
            errors.append(f"{metadata_name}: cover contains {match.group(0)!r}")
        if metadata.get("cover_disclosure") != DEFAULT_COVER_DISCLOSURE:
            errors.append(f"{metadata_name}: missing compact cover disclosure")
        if len(metadata.get("cover_facts", [])) != 4:
            errors.append(f"{metadata_name}: cover must use four facts")
        markdown_text = " ".join(markdown.split())
        disclosure_text = " ".join(FULL_SAMPLE_DISCLOSURE.split())
        if disclosure_text not in markdown_text:
            errors.append(f"{markdown_name}: appendix lacks full sample disclosure")
    check(
        not errors,
        "public example covers are committee-ready and fully disclosed"
        + (f": {errors}" if errors else ""),
    )


def analysis_example_checks():
    missing_files = []
    coverage_errors = []
    format_errors = []
    quality_errors = []
    reviewed_count = 0
    for skill_name, (structured, section_patterns) in ANALYSIS_EXAMPLE_CONTRACTS.items():
        relative_paths = ANALYSIS_EXAMPLE_PATHS.get(
            skill_name,
            ("references/analysis-examples.md",),
        )
        paths = [ROOT / "skills" / skill_name / path for path in relative_paths]
        absent = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
        if absent:
            missing_files.extend(absent)
            continue
        examples = {}
        for path in paths:
            examples.update(_strong_examples(path.read_text(encoding="utf-8")))
        headings = tuple(examples)
        for pattern in section_patterns:
            if not any(re.fullmatch(pattern, heading, re.IGNORECASE) for heading in headings):
                coverage_errors.append(f"{skill_name}: {pattern}")
        for heading, (text, marked_test) in examples.items():
            reviewed_count += 1
            word_count = len(text.split())
            if not marked_test:
                format_errors.append(f"{skill_name}/{heading}: missing (TEST)")
            if word_count > 60:
                format_errors.append(
                    f"{skill_name}/{heading}: {word_count} words"
                )
            if re.search(r"\[S\d+\]", text) is None:
                format_errors.append(f"{skill_name}/{heading}: missing [S#]")
            if structured:
                positions = [text.find(label) for label in ANALYSIS_LABELS]
                if any(position < 0 for position in positions) or positions != sorted(positions):
                    format_errors.append(
                        f"{skill_name}/{heading}: four labels not in order"
                    )
            if callable(review_callout):
                notes = review_callout(heading, text, structured=structured)
                if notes:
                    quality_errors.append(
                        f"{skill_name}/{heading}: {'; '.join(notes)}"
                    )
    check(
        not missing_files,
        "analysis examples exist for every analytical skill"
        + (f": {missing_files}" if missing_files else ""),
    )
    check(
        not coverage_errors,
        "analysis examples cover every validator analysis section"
        + (f": {coverage_errors}" if coverage_errors else ""),
    )
    check(
        reviewed_count > 0 and not format_errors,
        "strong examples are TEST-marked, sourced, ordered and at most 60 words"
        + (f": {format_errors}" if format_errors else ""),
    )
    check(
        callable(review_callout) and reviewed_count > 0 and not quality_errors,
        "strong examples produce zero analysis-quality notes"
        + (f": {quality_errors}" if quality_errors else ""),
    )
