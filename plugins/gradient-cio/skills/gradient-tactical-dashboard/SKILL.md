---
name: gradient-tactical-dashboard
description: "Create a Tactical Dashboard Quick Take comparing Gradient momentum, signals and long-run assumptions. Triggers: 'tactical dashboard', 'monthly scorecard', 'TAA post', 'momentum vs value', 'where signals disagree'."
metadata:
  group: "Quick Takes"
  subject: "tactical market signals"
  output: "canvas"
  menu_order: "40"
  modules: "research,gradientSignals"
  contracts: "quick-takes,macro-signals"
  handoffs: "none"
  delivery: files
  status: "core"
  version: "1.0.0"
  summary: "Compare momentum, signals and assumptions without making an allocation call."
---

# Tactical Dashboard (Quick Take)

A monthly scorecard post. One of the five Quick Takes; every Quick Take follows one canvas spec. **Read `references/canvas-spec.md` (brand, voice, copy) and `references/spec_format.md` (how to write the spec) before starting.**

The idea: tactical allocation weighs momentum, value, positioning and macro. The big houses publish verdicts; this post shows the inputs side by side, sourced, with no verdict, so the CIO's committee makes the call and sees that Gradient can build this view for them.

Each run produces two PNGs, `post_copy.md` and an evidence note.

## Workflow

### 1. Get the data (save each result to a JSON file)
- **Relative returns:** `get_macro_signals` `view: "relative_returns"`, `envelope: "compact"`. `board_total` gives every pair's 3-month relative return, winning-horizon move and percentile.
- **Gradient CMAs:** `get_capital_market_assumptions` `view: "baseline"`, `per_page: 10` (and page 2 if you need alternatives). Use `excess_return_effective` and `volatility_effective`.
- **Regime state (optional):** `get_macro_signals` `view: "regime_state"`, `history_limit: 3`. It is monthly. If it returns no published data (it currently fails for every region while Gradient resumes publication), drop the regime tile and say "regime: publication pending" in the footnotes; the dashboard still ships. Always give the regime's date when it is shown.
- **GRIP:** `get_macro_signals` `view: "grip_index"`, `envelope: "compact"`.
- Optional: `cftc_positioning` (futures, rates/FX/commodities) or `hedge_fund_crowding` (13F, quarterly and lagged) when a row genuinely maps to them. Say the date; 13F data can be months old.

Do **not** use licensed third-party CMA consensus numbers on the image. Use Gradient's own CMAs.

### 2. Choose the rows (up to 8 on the portrait, 6 on the square)
Pick allocator-relevant pairs from `board_total` and group them with `{"group": "Styles & factors"}` and `{"group": "Regions"}` header rows (add a cross-asset group when relevant). Good defaults: Growth vs. Value, Small Caps vs. Market, Quality vs. US Market, Momentum vs. US Market, US vs. EM, US vs. Europe, Japan vs. US, Germany vs. UK. Mark the two least important rows `"square": false` so the square shows six. Rotate a pair or two each month so the dashboard stays fresh. For the CMA column, map each pair to Gradient factors honestly:
- **Direct:** growth vs value → DM growth (2) minus DM value (3).
- **Proxy (mark with †):** US vs EM → DM equity (1) minus EM (6); small caps vs market → DM small (5) minus DM large (4).
- **No factor:** show `{"text": "n/a"}` with the note "no regional factor" or "no matching factor". Never invent a mapping.

The fourth column, **Agree?**, is computed, never typed: an `{"agree": [momentum ref, CMA-edge ref]}` cell shows **Agree** when the two signs match, **Split** when they differ, and "—" where there is no CMA. It is the dashboard's headline insight, so build the headline and analysis around it.

### 3. Write the spec
Copy `examples/dashboard_2026-10-21.json` and edit it. Words are typed; every number is a reference. Row labels are set in Title Case automatically; write pair names the same way in the headline and analysis. Sign convention: positive = first-named side ahead (momentum) or favored (assumptions); say so in the subtitle.

### 4. Check every number
```
python3 scripts/render_dashboard.py --spec <spec.json> --facts-only
```
Confirm each displayed value, and that any number in the headline or analysis appears here.

### 5. Write the words
- `headline` (≤90): the tension, e.g. "Where momentum and Gradient's 10-year assumptions disagree".
- `explain` (≤700) and a shorter `explain_square` for the square image: name the pair(s) where inputs agree and where they conflict, add one line of macro context, and end by handing the decision back ("the call stays with your committee").
- `watch` (optional, ≤200): what would change the read, as a condition. Shown on the portrait; add `"watch_on_square": true` to show it on the square too.
- `post_question` (not drawn): the question a CIO would type into Claude, e.g. "Show me momentum, this week's signal and Gradient's 10-year assumptions side by side for five allocator pairs." Use it in the post text.
- `footnotes`: define each column and list proxies.

### 6. Render and inspect
```
python3 scripts/render_dashboard.py --spec <spec.json> --out <OUTPUT_DIR>/dashboard
```
Open both PNGs. Check that notes don't run into the next column, tiles don't overlap, and the footer and disclaimer fit. If the script reports an overlap, use `explain_square`, drop a row or a footnote, or shorten the headline. Deliver the PNGs and `post_copy.md` with the session's file tool.

### 7. Post copy
Use the patterns in `references/canvas-spec.md`. Lead with the tension the dashboard reveals, not a view. Last LinkedIn line: "Data: Gradient relative returns, ICAPM CMAs, regime state and GRIP, as of <date>. Not investment advice. GradientCIO.com"

## Rules (non-negotiable)
- **No verdicts.** No overweight/underweight, "favor", "rotate" or "time to". Describe what each input says and where they disagree.
- **Horizons are different on purpose.** Momentum is 3 months, the signal is 5 or 21 days, CMAs are 10-year assumptions. Never blend them into one score.
- CMAs are forward-looking model assumptions, not forecasts of realized returns; they are arithmetic excess returns over cash, USD, unhedged.
- Mark every proxy. Show "n/a" rather than force a mapping.
- Regime state is model-detected and monthly; always give its date, and leave it out rather than show a stale or unpublished value.

## Evidence note to the user (not for posting)
List each input's validation status, as-of date, methodology reference and digest (from `--facts-only`), every proxy used, and the source for each claim in the analysis.

## Files
- `scripts/render_dashboard.py`: renderer.
- `scripts/spec.py`: shared reference resolver (identical in Ask Gradient).
- `scripts/brand.py`: the shared Gradient brand kit, synced from the plugin's shared Quick Take kit (`tools/sync_quicktake_shared.py`). Never edit it here.
- `assets/logos/`, `assets/fonts/`: synced from the shared kit; add official logo files there (see `references/canvas-spec.md` §5).
- `references/canvas-spec.md`, `references/spec_format.md`.
- `examples/`: the spec and saved inputs behind the Oct 21, 2026 sample.
