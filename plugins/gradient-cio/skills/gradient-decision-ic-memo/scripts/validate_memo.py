#!/usr/bin/env python3
"""Validate an IC memo (markdown) against the gradient-decision-ic-memo template.

Checks
  1. All required headings present, exactly once, in order.
  2. No unresolved template placeholders (<...>) or rule text ({...}).
  3. Status cells in Sections 3, 4, 6.2, 7.1, 9.2 use only allowed status words.
  4. Rating cells in Section 14 use only High / Medium / Low; timing in Section 15 uses allowed values.
  5. Every [S#] cited in the body has a row in Appendix A, and every Appendix A row is cited.
  6. No stale local-calculation tags remain; Appendix B documents server metric methods.
  7. Executive summary has exactly five bullets with the fixed labels.
  8. Banned phrases from writing-standards.md are absent.
  9. Illustrative banner present if any Appendix A row has illustrative scope.

Exit code 0 = pass, 1 = errors (printed).
"""
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from report_vocab import IC_POLICY_STATUSES, IC_RISK_RATINGS  # noqa: E402

REQUIRED = [
    r"^# Investment Committee Memo — .+",
    r"^## 1\. Recommendation and Decision Requested$",
    r"^## 2\. Executive Summary$",
    r"^## 3\. Portfolio Snapshot$",
    r"^## 4\. IPS Compliance$",
    r"^## 5\. Performance & Attribution$",
    r"^## 6\. Factor Exposures & Concentration$",
    r"^## 7\. Expected Return & Risk$",
    r"^## 8\. Stress Tests & Scenarios$",
    r"^## 9\. Liquidity$",
    r"^## 10\. Manager & Operational Diligence$",
    r"^## 11\. Performance Integrity & GIPS$",
    r"^## 12\. Market Context$",
    r"^## 13\. Proposed Changes & Impact$",
    r"^## 14\. Risks & Mitigants$",
    r"^## 15\. Open Items & Conditions$",
    r"^## 16\. Approvals$",
    r"^## Appendix A — Sources and methods$",
    r"^## Appendix B — Server Metric Methods$",
    r"^## Appendix C — Methodology & Disclosures$",
]
STATUS = IC_POLICY_STATUSES
RATING = IC_RISK_RATINGS
TIMING = {"Before approval", "Within 30 days", "Next review"}
EXEC_LABELS = ["Positioning", "IPS", "Performance", "Outlook", "Liquidity & diligence"]
BANNED = [r"\bguaranteed?\b", r"\bwill return\b", r"\bexpected to deliver\b", r"\bverified returns\b",
          r"\bhas approved\b", r"\brisk-free\b(?! rate)"]
SOURCE_HEADER = [
    "Ref",
    "Evidence",
    "Basis",
    "Tool / view",
    "Key parameters",
    "As of",
    "Data scope",
    "Validation",
    "Digest",
]
SOURCE_BASES = {"gradient_tool", "user_document", "regulatory_filing"}
PUBLIC_TOOLS = set(
    json.loads(
        (
            PLUGIN_ROOT
            / "skills"
            / "gradient-setup"
            / "references"
            / "public-tools.json"
        ).read_text(encoding="utf-8")
    )["tools"]
)
TOOL_PATTERN = re.compile(
    r"\b(?:analyze|batch|build|check|compare|create|extract|get|list|log|"
    r"preview|reconcile|run|save|update)_[a-z0-9_]+\b"
)


def sections(lines):
    idx = {}
    for i, l in enumerate(lines):
        if l.startswith("## "):
            idx[l.strip()] = i
    return idx


def section_text(lines, start_pat, next_pat=r"^## "):
    out, on = [], False
    for l in lines:
        if re.match(start_pat, l):
            on = True
            continue
        if on and re.match(next_pat, l):
            break
        if on:
            out.append(l)
    return out


def table_col(sec_lines, col_name):
    vals, header = [], None
    for l in sec_lines:
        if not l.strip().startswith("|"):
            header = None if not l.strip() else header
            continue
        cells = [c.strip() for c in l.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set(l.replace("|", "").strip()) <= set("-: "):
            continue
        if col_name in header and len(cells) == len(header):
            vals.append(cells[header.index(col_name)])
    return vals


def main(path):
    text = open(path, encoding="utf-8").read()
    lines = text.splitlines()
    errors = []

    # 1. headings in order
    pos = -1
    for pat in REQUIRED:
        hits = [i for i, l in enumerate(lines) if re.match(pat, l)]
        if not hits:
            errors.append(f"Missing heading: {pat}")
            continue
        if len(hits) > 1:
            errors.append(f"Heading appears {len(hits)} times: {pat}")
        if hits[0] < pos:
            errors.append(f"Heading out of order: {pat}")
        pos = max(pos, hits[0])

    # 2. placeholders
    body = re.sub(r"`[^`]*`", "", text)
    for m in re.finditer(r"<[^<>\n]{2,80}>", body):
        if not re.match(r"<(br|/?b|/?i)>", m.group(0)):
            errors.append(f"Unresolved placeholder: {m.group(0)}")
    for m in re.finditer(r"\{[^{}\n]{4,}\}", body):
        errors.append(f"Template rule text left in memo: {m.group(0)[:60]}")

    # 3. status words
    for start in [r"^## 3\.", r"^## 4\.", r"^\*\*6\.2", r"^\*\*7\.1", r"^\*\*9\.2"]:
        sec = section_text(lines, start, r"^(## |\*\*\d+\.\d)")
        for v in table_col(sec, "Status"):
            if v not in STATUS and not v.startswith("Not assessed"):
                errors.append(f"Invalid status '{v}' in section {start}")

    # 4. ratings and timing
    for v in table_col(section_text(lines, r"^## 14\."), "Rating"):
        if v not in RATING:
            errors.append(f"Invalid rating '{v}' in Section 14")
    for v in table_col(section_text(lines, r"^## 15\."), "Timing"):
        if v not in TIMING:
            errors.append(f"Invalid timing '{v}' in Section 15")

    # 5/6. source tags and local-calculation prohibition
    appA = "\n".join(section_text(lines, r"^## Appendix A"))
    body_main = text.split("## Appendix A")[0]
    if "| Data basis | mixed |" not in body_main:
        errors.append("Header table must declare '| Data basis | mixed |'")
    cited_s = set(re.findall(r"\[S(\d+)\]", body_main))
    listed_s = set(re.findall(r"^\|\s*S(\d+)\s*\|", appA, re.M))
    for s in sorted(cited_s - listed_s, key=int):
        errors.append(f"[S{s}] cited but missing from Appendix A")
    for s in sorted(listed_s - cited_s, key=int):
        errors.append(f"S{s} listed in Appendix A but never cited")
    if re.search(r"\[Calc(?:\s+C(?:\d+|#))?\]", text):
        errors.append("Local calculation tags are not allowed; cite server or document evidence with [S#]")

    source_lines = [line for line in appA.splitlines() if line.startswith("|")]
    if source_lines:
        header = [cell.strip() for cell in source_lines[0].strip("|").split("|")]
        if header != SOURCE_HEADER:
            errors.append(
                "Appendix A columns must be, in order: " + ", ".join(SOURCE_HEADER)
            )
        else:
            for row_number, line in enumerate(source_lines[2:], start=1):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) != len(SOURCE_HEADER):
                    errors.append(
                        f"Appendix A source row {row_number} must contain "
                        f"{len(SOURCE_HEADER)} cells"
                    )
                    continue
                _tag, _evidence, basis, tool_view, parameters, as_of, scope, validation, digest = cells
                if basis not in SOURCE_BASES:
                    errors.append(
                        f"Appendix A source row {row_number} has invalid Basis '{basis}'"
                    )
                if basis == "gradient_tool":
                    tools = set(TOOL_PATTERN.findall(tool_view))
                    if not tools:
                        errors.append(
                            f"Appendix A source row {row_number} must name a Gradient tool"
                        )
                    for tool in sorted(tools - PUBLIC_TOOLS):
                        errors.append(
                            f"Appendix A source row {row_number} names unknown tool '{tool}'"
                        )
                    if digest.casefold() in {"", "n/a", "na", "none"}:
                        errors.append(
                            f"Appendix A source row {row_number} requires a digest"
                        )
                if not all((tool_view, parameters, as_of, scope, validation, digest)):
                    errors.append(
                        f"Appendix A source row {row_number} has an empty provenance field"
                    )

    # 7. executive summary
    ex = [l for l in section_text(lines, r"^## 2\.") if l.strip().startswith("- ")]
    if len(ex) != 5:
        errors.append(f"Executive summary has {len(ex)} bullets (need 5)")
    for i, lab in enumerate(EXEC_LABELS):
        if i < len(ex) and not ex[i].strip().startswith(f"- **{lab}:**"):
            errors.append(f"Executive summary bullet {i+1} must start with '- **{lab}:**'")

    # 8. banned phrases
    for pat in BANNED:
        for m in re.finditer(pat, body_main, re.I):
            errors.append(f"Banned phrase: '{m.group(0)}'")

    # 9. illustrative banner
    if re.search(r"illustrative", appA, re.I) and "**ILLUSTRATIVE DATA**" not in text:
        errors.append("Illustrative source in Appendix A but no ILLUSTRATIVE DATA banner")

    if errors:
        print(f"FAIL — {len(errors)} issue(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("PASS — memo matches the template.")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: validate_memo.py <memo.md>")
        sys.exit(2)
    main(sys.argv[1])
