---
name: gradient-private-markets-portfolio-construction
description: "Build a private-markets allocation report covering PE/private credit, commitments, pacing, cash flows, and liquidity. Use for private markets portfolio, commitment plan, or pacing. For a committee vote use gradient-ic-memo."
---

# Private Markets Portfolio Construction

Produce a deterministic, fully sourced, decision-ready private-markets construction report. Select an
existing Gradient portfolio, assess the current private-markets program, and recommend a target program and
implementation path. The committee decides; this skill never creates, updates or rebalances a portfolio in
GradientCIO.

The deliverable is a branded report. Its PDF form is normally 10–14 pages and uses the base name
`"<Portfolio> - Private Markets Portfolio Construction <YYYY-MM-DD>"`.

## Files in this skill

| File | Read when |
|---|---|
| `references/data-map.md` | Always — tools, arguments, evidence fields and fallbacks. |
| `references/construction-template.md` | Always — exact section order and required blocks. |
| `references/writing-standards.md` | Before drafting — recommendation, private-market and uncertainty rules. |
| `references/module-scope.md` | Always — Portfolio Analytics and Strategy Lab stay separate. |
| `references/chart-data.md` | Always — chart discovery, basis and unchanged chart blocks. |
| `references/report-style.md` | Before rendering — metadata, blocks and delivery checks. |
| `scripts/validate_construction.py` | After drafting — validates structure, evidence and decision language. |
| `scripts/render.py` | Renders validated `report.json` to PDF, PPTX or both. Never restyle it. |

## 1. Scope

1. Resolve the organization with `list_organizations`; ask only if more than one is available and none is
   named.
2. Call `get_gradient_capabilities` once and record Portfolio Analytics access.
3. Use `list_portfolios` to select or switch to the named existing portfolio. If multiple user portfolios
   remain plausible, ask one focused question. Never call a portfolio create, update, save or delete tool.
4. Default the as-of date to the latest common date returned by the required evidence.
5. Capture the committee objective, target private-markets range, commitment horizon and any user-supplied
   constraints. Missing constraints remain `Not assessed — constraint not provided`.

If the selected record is illustrative, apply the exact label
**Illustrative, Gradient Maintained — demo data, not the client's holdings or managers** on the cover, in
the first affected section and every affected source row. Never describe it as the user's portfolio.

## 2. Collect

Follow `references/data-map.md`. Save each raw result and record a source row with tool, key arguments,
as-of date, data-scope label, validation status and payload digest.

Required evidence:

- portfolio record, allocation tree, full exposure pages and policy result;
- historical returns and governed attribution, preserving typed unavailable states;
- `get_chart_data` availability, then `allocations` and `commitments` one pack at a time, or up to four
  targeted `chart_ids` (never both selectors); `max_rows` defaults to 40 and is capped at 100; disclose
  `truncated: true`;
- active assumption set and baseline capital-market assumptions.

Manager diligence, CMA consensus and selected-series Strategy Lab results are optional. An entitlement block
is `Not licensed`, not an outage. Retry only once and only when the error says it is retryable.

## 3. Assess

- Use returned private-market exposure classifications, NAV, commitment amount and unfunded values. Do not
  treat unfunded as NAV or add it to server exposure aggregates.
- Use returned total-portfolio targets and governed policy statuses. Do not multiply parent and child
  targets or infer a policy status.
- Lead liquidity analysis with unfunded coverage, near-term calls and denominator sensitivity. State every
  valuation date and lag.
- Preserve chart `basis` and `context.fingerprint`; preserve the assumption set, regime, horizon and currency
  on governed policy / CMA forward evidence. Forward values are assumptions, not forecasts.
- Keep selected-series Strategy Lab evidence optional and label it
  **Selected-series sandbox — not saved-portfolio analytics**.
- Recommend a target structure only from user-stated constraints and returned evidence. If the evidence
  cannot support a numeric target, recommend the decision process and mark the target `Not available`.

## 4. Build and validate

Use JSON block mode and follow `references/construction-template.md` exactly. Put the recommendation and
requested committee action first. Every number in text or tables carries an `[S#]` tag. Embed usable
`get_chart_data` items unchanged as `{"type":"chart","chart":<item>}`.

Match ODD-quality report polish. Use exactly the four template tiles; source the bottom line, tiles and
analysis. Add the template-required charts/graphics and 1–3 structured `role: analysis` callouts in each
named analytical section. A required visual may be replaced only when governed evidence is unavailable,
using a `callout` with `Not available — <reason>`. Analysis explains evidence supporting the fixed Committee
Action Requested; it must not introduce another recommendation or action. Validation failure blocks
delivery. After rendering, inspect every PDF page for clipping, overflow, hierarchy, chart legibility,
orphaned headings and excess whitespace.

Run until clean:

```text
python scripts/validate_construction.py report.json
```

Select PDF by default; select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select
both when it says `both` or `board pack`. Both formats must come from the same validated `report.json`.

```text
python scripts/render.py report.json --format <pdf|pptx|both> --out "<Portfolio> - Private Markets Portfolio Construction <YYYY-MM-DD>"
```

Inspect every requested output, reconcile each displayed figure to saved evidence and follow the shared
“Check and deliver” instructions. Reply with three lines: recommendation, program/policy status,
open-item count, plus the requested file(s).

## 5. Handoffs

- Candidate-manager selection → `gradient-manager-compare`.
- Manager or fund diligence → `gradient-odd-report` and `gradient-gips-manager-diligence`.
- Hedge-fund or liquid-alternatives construction → `gradient-marketable-alternatives-portfolio-construction`.
- Broad liquid/illiquid real-assets construction → `gradient-real-assets-portfolio-construction`.
- Formal 16-section committee memo → `gradient-ic-memo` with memo type `New Commitment` or
  `Allocation Change`.
- Ongoing monitoring after approval → `gradient-portfolio-review`.
