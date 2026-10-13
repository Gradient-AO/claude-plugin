---
name: gradient-idd-private-markets-pme
description: "Create a private-markets PME report for one fund or manager. Triggers: 'run private-markets PME', 'compare this fund to public markets', 'assess PME performance'. For program construction use gradient-portfolio-construction."
metadata:
  version: "0.1.1"
  style_contract: "2.3.0"
  group: "Investment due diligence"
  subject: "private-markets performance"
  output: "PME Report"
  menu_order: "30"
  modules: "strategyLab"
  contracts: "idd-methodology,idd-odd-ic-handoff"
  handoffs: "gradient-odd-report,gradient-decision-ic-memo"
  summary: "Assess private-market performance against public-market equivalents."
---

# Private-Markets Performance

Assess one private fund from dated cash flows against returned public-market benchmarks using server-computed PME and direct alpha. Deliver a branded PDF by default and PowerPoint only when requested.

## Non-negotiable rules

- Read `references/contracts/idd-methodology.md` before analysis and use only server-returned values.
- Read `references/module-scope.md` before using Portfolio Analytics or Strategy Lab tools.
- Read `references/data-map.md` and `references/analysis-examples.md` before collection and analysis.
- Resolve one canonical `portfolio_id` and one canonical `commitment_id`; do not substitute a return-series, fund, manager, or benchmark ID.
- Resolve the commitment by matching both returned `manager_name` and returned `commitment_name`. Never resolve on either name alone.
- Treat `get_portfolio_exposure.pme_ready` and `cash_flow_coverage` as the readiness gate before holdings collection or benchmark discovery.
- Select one primary benchmark first and, only after a successful primary path, one distinct sensitivity benchmark from `get_benchmarks`; record each returned ID and the rationale for its selection.
- Never substitute a Strategy Lab demo-series ID, including an ID from `get_benchmarks.demo_set`, for a returned `commitment_id` or selected catalog `benchmark_id`.
- Preserve methods, units, dates, observations, coverage, truncation, and request IDs.
- Holdings and ILPA company detail provide context only. Never pass holdings or ILPA values into the PME calculator or use them to replace PME output.
- Do not rank quality, recommend a hire, or turn missing evidence into a neutral result.
- Label illustrative evidence exactly as required by `references/report-style.md`.

## 1. Resolve and collect

Follow the tool order and source roles in `references/data-map.md`:

1. Resolve the selected portfolio through `list_portfolios` and use its returned `portfolio_id`.
2. Call `get_portfolio_exposure` for the canonical portfolio and page the relevant private-market classifications to completion. Match the user's target against both returned `manager_name` and `commitment_name`, then use that row's returned `commitment_id`. If more than one row remains plausible, stop and ask with a short list containing only returned `commitment_name`, `commitment_amount`, and NAV (`nav_base`); do not guess. If no canonical row is returned, ask for clarification.
3. Immediately inspect the matched row's `pme_ready` and `cash_flow_coverage.status`, `reason`, `first_flow_date`, `last_flow_date`, and `flow_count`. If `pme_ready` is not true or coverage is not `available`, fail fast before `get_private_markets_holdings` or `get_benchmarks`. This readiness branch has checked **0 builder paths**.
4. Query `get_benchmarks` with `view: "catalog"` for one primary candidate using the smallest bounded query practical: apply returned mandate classifications as exact supported filters, set a small `limit`, and widen or page only until one suitable primary is identified. Do not page the full catalog pre-emptively. Use only returned identity and classification fields. For private credit, prefer a returned suitable leveraged-loan or high-yield candidate; never invent or force one.
5. Call `build_strategy_lab_session` for that primary benchmark with exactly:

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

Omit absent optional date bounds. Inspect the builder's `status`, `coverage`, `unavailable_reason`, `error_code`, `request_id`, and provenance IDs. Run `run_strategy_lab_private_markets_pme` only when `status` is `available` and `strategy_lab_session` is non-null; pass that returned session object unchanged. If the primary builder is unavailable, or the primary run returns no usable PME evidence, stop with the canonical chat-only response after **1 builder path**.

6. Only after the primary run returns usable PME evidence, call `get_private_markets_holdings` with the canonical IDs. Request holdings, ILPA company detail, and aggregates; paginate until `has_more` is false. Preserve coverage, reconciliation, artifact, exact-cell, and methodology fields as context only.
7. Only after primary success, finish sensitivity selection with another bounded `get_benchmarks` query. Select one distinct, decision-useful benchmark using returned mandate metadata, then call its builder separately with the same canonical IDs and date bounds. Inspect the same builder fields and, only for an available non-null session, run PME with that session unchanged. Never reuse the primary session. If no distinct suitable sensitivity is returned, retain the primary report and type the sensitivity gap.

Save every response used in the report. A builder path means one `build_strategy_lab_session` call; readiness checks, catalog queries, holdings reads, and calculator calls do not increment `<n>`. If a required public capability is unavailable or not licensed, preserve the typed status.

## 2. Assess

Apply the approved metric and reliability rules in the shared IDD methodology contract. Treat a PME response as usable only when it contains at least one server-returned analytical evidence field named in `references/data-map.md`; nulls, empty rows, and a success envelope alone are not evidence.

- If all attempted benchmark paths produce zero usable PME evidence, stop. Return chat only with a typed reason such as `Not available — <returned reason>` and include `error_code` and `request_id` when present. Do not create `report.json`, render a report, run the validator, or run QA.
- If at least one path has usable evidence, produce the normal report. Missing metrics, unavailable benchmark paths, partial coverage, diagnostics, and truncated fields remain explicit limitations; partial evidence is not a reason to suppress the report.

Use this exact canonical chat-only template for readiness failure or zero usable PME evidence:

`PME not available for <commitment> (<portfolio>): <unavailable_reason>. Checked <n> builder path(s) on <date>. [request_id if returned] Next: <one allowed next step>.`

Fill the commitment, portfolio, reason, date, path count, and request ID only from the saved run context and server responses; omit the bracketed request-ID clause when none was returned. For readiness failure, use the returned `cash_flow_coverage.reason` and `<n>` = `0`. The one next step must be limited to supplying or linking the missing dated cash flows, resolving a returned identity ambiguity, restoring access to the typed capability, or repairing the returned benchmark-coverage gap, whichever the returned reason supports.

Keep investment evidence separate from Form ADV, Form 13F, and other operational evidence. State what would change the conclusion.

## 3. Build the report

Use these fixed sections: Executive conclusion; Cash-flow and benchmark coverage; PME and direct alpha; IRR and multiple context; Benchmark sensitivity; Limitations and follow-ups; Appendix A — Sources and methods (`num: "A"`). Keep each section even when evidence is unavailable. Every figure carries a unit, date, and `[S#]` source tag.

Read `references/report-style.md` and `references/writing-standards.md`. Build one validated `report.json`; do not hand-build HTML, Word, PDF, or slides and do not override the shared theme.

- Set `meta.report_kind` to exactly `private_markets_pme`.
- Map PME and direct-alpha discussion only from returned `ks_pme`, `direct_alpha`, benchmark basis/comparison, coverage, metric-basis, and diagnostic fields.
- Map IRR and multiple discussion from returned `irr`, `tvpi`, `dpi`, and `rvpi`, then add clearly separated holdings/ILPA context from `get_private_markets_holdings`. Holdings context may explain company inventory, value, reconciliation, or reported ILPA fields, but it is not a PME calculator input and must not be presented as one.
- Compare the separately returned primary and sensitivity runs in Benchmark sensitivity. Do not calculate deltas or fill a missing run locally.
- Use exactly four sourced executive tiles: Result, Benchmark, Coverage, and Reliability. State one evidence-bounded executive verdict; unavailable or partial server fields must remain unavailable or partial in both the tiles and verdict.
- Use the four server-returned series — `cash_flow_series`, `multiples_series`, `pme_series`, and `irr_series` — only when each is returned. Preserve its status, date basis, currency, method, payload digest, point dates, and values unchanged; never derive, splice, or backfill a missing series locally.

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
