# IC Memo Report Layout — visuals and Claude analysis (v0.2.0)

The memo text stays deterministic: `memo.md` follows `memo-template.md` and passes `validate_memo.py`.
This file defines the separate visual and Claude-analysis layer. `scripts/compose_memo_json.py` merges
`memo.md`, `visuals.json`, and `meta.json` into `report.json`; `render.py` renders that same validated source
to the selected output format. Never restyle the renderer or hand-edit `report.json`.

## `visuals.json`

```json
{
  "1": {
    "before": [],
    "after": [],
    "analysis": [{"title": "...", "text": "... [S1]", "tone": "info"}]
  }
}
```

- Keys are section numbers `"1"` through `"16"`. Appendices have no visual layer.
- `before` renders after the section's opening markdown paragraph; `after` renders after its remaining
  markdown; `analysis` renders last as `Analysis — <title>` callouts.
- Block types are those in `report-style.md`: `tiles`, `bars`, `line`, `chart`, `waterfall`, `band`,
  `stacked`, `heat`, `callout`, `findings`, `coverage`, `two_col`, `statement`, `table`, and `kv`.
- A required visual whose evidence is unavailable becomes a `callout` with tone `watch` and text
  `Not available — <specific reason>`. Never silently drop a slot.
- In each analytical section, put a decision-useful visual or its typed unavailable substitute in `before`,
  ahead of the first markdown table. Never place more than two tables consecutively, including inside
  `two_col`.

## Required visuals

The composer validates these semantic slots by block type and title.

| Section | Required visual(s) | Evidence and constraints |
|---|---|---|
| Executive band | Four `executive.tiles`: **Trailing 1Y vs benchmark**, **IPS breaches**, **Expected return vs objective**, **T1 liquidity** | Values and subtitles carry the existing memo source tags. |
| 1 | `statement` **Recommendation** before the memo text | One-line recommendation, no more than 25 words; `sub` states the decision requested. |
| 3 | `two_col` containing `bars` **Current weight by asset class** and **Active weight vs policy (bps)** | Both bars are `narrow`; active weights use the signed-bar convention. |
| 4 | `coverage` **Policy constraint status** before the text | Allocation, Return, Risk, Liquidity, Concentration; status values map to renderer chips. |
| 4 | `bars` **Concentration vs limit** | Include manager and issuer rows that breach, are near their limit, or sit within 5 percentage points of a cap. |
| 5 | `line` **Growth of 100** | Use the separate `cumulative_growth` result; multiply returned index values by 100 only for display; `ref` is 100. |
| 5 | `bars` **Calendar-year returns** | Signed bars; preserve partial-year month labels. |
| 5 | `bars` **1Y attribution — total effect by asset class (bps)** | Signed bars ordered by absolute returned total effect descending. |
| 6 | `chart` with exact `chart_id` **bar-portfolio-factor-currency-exposure** | Pass the complete chart item from `get_portfolio_exposure` include `factor_currency_exposure` unchanged, including its title and payload. If unavailable, use that exact chart ID as the `callout` title. |
| 7 | `bars` **Gradient vs consensus gap (bps)** and `tiles` **Forward context** | Signed bars; tiles show GRIP score/stance, policy expected return, and return objective. |
| 8 | `bars` **Scenario impacts (%)** before the text | Portfolio impacts use signed bars ordered worst first. If no governed scenario result is available, use a typed unavailable callout with this exact title. |
| 9 | `bars` **Liquidity tiers (% NAV)** plus returned commitments charts | Pass liquidity-scorecard, pacing, and cash-flow chart items unchanged when available. |
| 10 | `findings` **Exposure-weighted diligence findings** | Include severity, exposure, and due date; use `empty_title` when none are returned. |
| 11 | `coverage` **GIPS review coverage** and `callout` **GIPS follow-ups** | Keep total-fund and in-scope manager coverage compact; the callout carries material findings, follow-ups, or a typed none/unavailable state. |
| 12 | `tiles` **Macro readings** | Three or four dated, sourced facts only. |
| 13 | `two_col` **Current vs proposed weights**, or `callout` **No change proposed** | Never manufacture a proposed case. |
| 14 | `tiles` **Risk count by rating** before the text | High / Medium / Low use bad / watch / good tones. |

### Signed bars

For signed quantities preserve the finite signed number in `value` and the sign in `display` (for example
`−550 bps`). Use coral `#E8735A` for negatives and lime `#B5E52A` for positives, and set
`all_accent: false`. Do not convert negative values to absolute magnitudes.

## Claude analysis

Analytical sections 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, and 14 end with analysis callouts. Section 2 contains
three to five `role: "key_judgment"` **Key judgment —** callouts connecting evidence across sections; every
other analytical section contains one to three `role: "analysis"` **Analysis —** callouts.

Each callout follows:

1. Observation with at least one `[S#]`.
2. Why it matters for the decision.
3. Uncertainty from coverage, staleness, basis, or model limits.
4. What evidence or threshold would change the view.

Every number carries a source tag. Comparisons and rankings of returned figures are allowed; new local
metrics, forecasts, and characterizations of manager skill are not. Analysis can support only the action in
Section 1. Titles are six words or fewer, text is about 60 words or fewer, and tones are `info`, `watch`,
`bad`, or `good`.

## Page flow

Sections flow by default. Section 1 opens after the cover; Section 5 has a preferred page start that QA may
remove, while Appendix A is the only authored forced page start. Sections 14–16 flow contiguously.
The soft target is 13–20 pages and the hard ceiling is 22; never add filler to reach the target.
`references/layout-budget.json` controls section words, body rows, visuals and page spans. Long returned chart
tables show a 12-row body preview and move their complete returned rows to the generated Chart data appendix.
Sections 4 and 10 place required visuals before their first markdown table. Use `narrow: true` for bars inside
`two_col`. Before delivery run
`python scripts/qa_report.py report.json --format <pdf|pptx|both> --out "<Portfolio> - IC Memo" --budget references/layout-budget.json`;
apply its specific repair levers, re-compose and rerun until clean.
