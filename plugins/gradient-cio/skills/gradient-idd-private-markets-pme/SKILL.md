---
name: gradient-idd-private-markets-pme
description: "Create a private-markets PME report for one fund or manager. Triggers: 'run private-markets PME', 'compare this fund to public markets', 'assess PME performance'. For program construction use gradient-portfolio-construction."
metadata:
  version: "0.1.0"
  style_contract: "2.2.0"
  group: "Investment due diligence"
  subject: "private-markets performance"
  output: "PME Report"
  menu_order: "50"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Assess private-market performance against public-market equivalents."
---

# Private-Markets Performance

Assess one private fund from dated cash flows against returned public-market benchmarks using server-computed PME and direct alpha. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Read `references/data-map.md` and `references/analysis-examples.md` before collection and analysis.
- Resolve one canonical `portfolio_id` and one canonical `commitment_id`; do not substitute a return-series, fund, manager, or benchmark ID.
- Select one primary benchmark and one distinct sensitivity benchmark from `get_benchmarks`; record both IDs and the rationale for each selection.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Holdings and ILPA company detail provide context only. Never pass holdings or ILPA values into the PME calculator or use them to replace PME output.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Follow the tool order and source roles in `references/data-map.md`:

1. Resolve the selected portfolio through `list_portfolios` and use its returned `portfolio_id`.
2. Resolve the target commitment from that portfolio's returned exposure evidence and use its returned `commitment_id`. If the user's name is ambiguous or no canonical commitment is returned, ask for clarification; do not guess.
3. Call `get_private_markets_holdings` with the canonical `portfolio_id` and `commitment_id`. Request holdings, ILPA company detail, and aggregates; paginate until `has_more` is false. Preserve coverage, reconciliation, artifact, exact-cell, and methodology fields as context.
4. Query `get_benchmarks` with `view: "catalog"` and page until `truncated` is false. Select a mandate-suitable primary benchmark and a distinct, mandate-suitable sensitivity benchmark using only returned identity and classification fields. Record the returned `benchmark_id`, name, metadata, and selection rationale. For private credit, prefer a returned leveraged-loan or high-yield candidate when it is suitable; do not invent a candidate or force an unsuitable one. If two distinct suitable benchmarks cannot be supported, retain the primary run and type the sensitivity gap.
5. For each selected benchmark, call `build_strategy_lab_session` separately with exactly:

```json
{
  "domain": "private-markets-pme",
  "portfolio_id": "<canonical portfolio_id>",
  "commitment_id": "<canonical commitment_id>",
  "benchmark_id": "<that run's benchmark_id>",
  "start_date": "<optional YYYY-MM-DD>",
  "end_date": "<optional YYYY-MM-DD>"
}
```

Omit absent optional date bounds. Before each PME run, inspect the builder's `status`, `coverage`, `unavailable_reason`, `error_code`, `request_id`, and provenance IDs. Run `run_strategy_lab_private_markets_pme` only when `status` is `available` and `strategy_lab_session` is non-null; pass that returned session object unchanged. Never reuse the primary session for sensitivity.

Save every response used in the report. Independent discovery reads may run in parallel, but each PME run depends on its own successful builder response. If a required public capability is unavailable or not licensed, preserve the typed status.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Treat a PME response as usable only when it contains at least one server-returned analytical evidence field named in `references/data-map.md`; nulls, empty rows, and a success envelope alone are not evidence.

- If all attempted benchmark paths produce zero usable PME evidence, stop. Return chat only with a typed reason such as `Not available — <returned reason>` and include `error_code` and `request_id` when present. Do not create `report.json`, render a report, run the validator, or run QA.
- If at least one path has usable evidence, produce the normal report. Missing metrics, unavailable benchmark paths, partial coverage, diagnostics, and truncated fields remain explicit limitations; partial evidence is not a reason to suppress the report.

Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Cash-flow and benchmark coverage; PME and direct alpha; IRR and multiple context; Benchmark sensitivity; Limitations and follow-ups; Appendix A — Sources and methods. Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

- Set `meta.report_kind` to exactly `private_markets_pme`.
- Map PME and direct-alpha discussion only from returned `ks_pme`, `direct_alpha`, benchmark basis/comparison, coverage, metric-basis, and diagnostic fields.
- Map IRR and multiple discussion from returned `irr`, `tvpi`, `dpi`, and `rvpi`, then add clearly separated holdings/ILPA context from `get_private_markets_holdings`. Holdings context may explain company inventory, value, reconciliation, or reported ILPA fields, but it is not a PME calculator input and must not be presented as one.
- Compare the separately returned primary and sensitivity runs in Benchmark sensitivity. Do not calculate deltas or fill a missing run locally.

## 4. Handoff

Validate and attach a `gradient-idd-odd-ic-handoff/v1` object using `references/contracts/idd-odd-ic-handoff.schema.json`. Include canonical or advisory identity status, canonical portfolio and commitment links where the schema permits, both benchmark IDs, evidence, limitations, and benchmark-selection rationale.

A viable fund → `gradient-odd-report`; a commitment decision → `gradient-decision-ic-memo`.

## 5. Validate and deliver

Run the shared IDD contract validator, then canonical delivery QA:

```text
python <skill>/scripts/validate_private_markets_pme.py report.json
python <skill>/scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Subject> - PME Report <YYYY-MM-DD>" --budget <skill>/references/layout-budget.json
```

Inspect every requested contact sheet and spot-check every number against saved evidence. QA failures block delivery. Return the file plus three lines: conclusion, largest limitation, and follow-up count.
