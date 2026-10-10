# IC Memo Report Layout — visuals and Claude analysis (v0.2.0)

The memo text stays deterministic: `memo.md` follows `memo-template.md` and passes `validate_memo.py`.
This file defines the separate visual and Claude-analysis layer. `scripts/compose_memo_json.py` merges
`memo.md`, `visuals.json`, and `meta.json` into `memo.json`; `gradient_report.py` renders it in JSON block mode.
Never restyle the renderer or hand-edit `memo.json`.

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
- Block types are those in `report-style.md`: `tiles`, `bars`, `line`, `chart`, `callout`, `findings`,
  `coverage`, `two_col`, `statement`, `table`, and `kv`.
- A required visual whose evidence is unavailable becomes a `callout` with tone `watch` and text
  `Not available — <specific reason>`. Never silently drop a slot.

## Required visuals

The composer validates these semantic slots by block type and title.

| Section | Required visual(s) | Evidence and constraints |
|---|---|---|
| Executive band | Four `executive.tiles`: **Trailing 1Y vs benchmark**, **IPS breaches**, **Expected return vs objective**, **T1 liquidity** | Values and subtitles carry the existing memo source tags. |
| 1 | `statement` **Recommendation** before the memo text | One-line recommendation, no more than 25 words; `sub` states the decision requested. |
| 3 | `two_col` containing `bars` **Current weight by asset class** and **Active weight vs policy (bps)** | Both bars are `narrow`; active weights use the signed-bar convention. |
| 4 | `coverage` **Policy constraint status** before the text | Allocation, Return, Risk, Liquidity, Concentration; status values map to renderer chips. |
| 4 | `bars` **Concentration vs limit** | Include manager and issuer rows that breach, are on Watch, or sit within 5 percentage points of a cap. |
| 5 | `line` **Growth of 100** | Use the separate `cumulative_growth` result; multiply returned index values by 100 only for display; `ref` is 100. |
| 5 | `bars` **Calendar-year returns** | Signed bars; preserve partial-year month labels. |
| 5 | `bars` **1Y attribution — total effect by asset class (bps)** | Signed bars ordered by absolute returned total effect descending. |
| 6 | `chart` **Factor and currency exposure** | Pass the returned `get_chart_data` item unchanged. |
| 7 | `bars` **Gradient vs consensus gap (bps)** and `tiles` **Forward context** | Signed bars; tiles show GRIP score/stance, policy expected return, and return objective. |
| 9 | `bars` **Liquidity tiers (% NAV)** plus returned commitments charts | Pass liquidity-scorecard, pacing, and cash-flow chart items unchanged when available. |
| 10 | `findings` **Exposure-weighted diligence findings** | Include severity, exposure, and due date; use `empty_title` when none are returned. |
| 12 | `tiles` **Macro readings** | Three or four dated, sourced facts only. |
| 13 | `two_col` **Current vs proposed weights**, or `callout` **No change proposed** | Never manufacture a proposed case. |
| 14 | `tiles` **Risk count by rating** before the text | High / Medium / Low use bad / watch / good tones. |

### Signed bars

The renderer draws non-negative bar lengths. For signed quantities set `value` to `abs(x)`, put the signed
formatted figure in `display` (for example `−550 bps`), use coral `#E8735A` for negatives and lime
`#B5E52A` for positives, and set `all_accent: false`.

## Claude analysis

Analytical sections 2, 3, 4, 5, 6, 7, 9, 10, 12, and 13 end with analysis callouts. Section 2 contains
three to five **Key judgments** connecting evidence across sections; every other analytical section contains
one to three callouts.

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

Sections flow by default. Section 1 opens after the cover; Sections 5, 7, and 14 and Appendix A start on new
pages. Target 14–18 pages without adding filler. Use `narrow: true` for bars inside `two_col`.
