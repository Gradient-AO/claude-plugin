---
name: gradient-ask-gradient
description: "Create an Ask Gradient Quick Take answering one investment question with Gradient data. Triggers: 'Ask Gradient post', 'investment Q&A', 'one question post', 'Gradient demo post', 'turn this answer into social content'."
metadata:
  group: "Quick Takes"
  subject: "investment question and answer"
  output: "canvas"
  menu_order: "50"
  modules: "research,gradientSignals"
  contracts: "quick-takes,portfolio,macro-signals"
  handoffs: "gradient-portfolio-lens"
  delivery: files
  status: "core"
  version: "1.0.0"
  summary: "Answer one investment question with governed Gradient data."
---

# Ask Gradient (Quick Take)

The most flexible of the five Quick Takes. It is a product demo disguised as content: one CIO question, answered live in Claude with Gradient data. The image carries the answer; the post text carries the question. **Read `references/canvas-spec.md` (brand, voice, copy) and `references/spec_format.md` (spec schema) first.**

Each run produces two PNGs, `post_copy.md` and an evidence note.

## Choosing the question
Good questions are ones a CIO would actually type, that Gradient data answers cleanly, and that the reader could ask about their own portfolio. Rotate topics so the series covers the whole platform:

| Topic | Gradient tools | Example question |
|---|---|---|
| Long-run assumptions | `get_capital_market_assumptions` (baseline) | "What do Gradient's 10-year assumptions say about value vs growth?" |
| Diversification | CMA `correlations` (with frequency sensitivity) | "Are bonds still diversifying equities in Gradient's assumptions?" |
| Portfolio risk | CMA `portfolio_analytics` (server-computed risk contribution) for a reference portfolio or archetype | "How much of a 60/40's risk comes from equities on Gradient's assumptions?" |
| Regime context | CMA `regime` overlays; `get_macro_signals` `regime_state` when published | "How do Gradient's stagflation assumptions change bond returns?" |
| Risk posture | `get_macro_signals` `grip_index` (when GRIP is not saturated) | "Which part of the market is driving risk pressure this month?" |
| Liquidity | `check_portfolio_policy` liquidity and `get_portfolio_exposure` `liquidity_scorecard` on a Gradient model (illustrative) | "How liquid is a Total Plan-style portfolio in a stress month?" |

For the deeper portfolio canvases (equity dial, diversifier scorecard, stress map), use `gradient-portfolio-lens` instead. Never use Strategy Lab demo series (synthetic) or peer data (Gradient no longer publishes peer analysis). Avoid questions that ask for a recommendation ("What should I overweight?"). Never use client portfolios or client data; use Gradient's illustrative data or public data. Don't show licensed third-party CMA consensus numbers.

## Workflow

### 1. Answer the question in Claude
Call the tools the question needs and save each result to a JSON file (write inline results to a file; copy values exactly). Note each result's `validation.status`; anything not `passed` can't be used.

### 2. Write the spec
Copy `examples/ask_value_growth_2026-10-21.json` and edit it:
- `post_question` (not drawn): the question as the CIO would type it. It opens the post text.
- `eyebrow` (optional): e.g. "Ask Gradient · Value vs. growth".
- `headline` (≤90): the answer in one plain claim, readable without the question.
- `subtitle` (optional): what the numbers are, e.g. "Gradient ICAPM 10-year assumptions for developed-market equity styles, USD".
- `tiles` (≤3): the two or three numbers that answer the question. Use `"color": "accent"` for the headline number and `"sign"` for signed moves.
- `chart` (optional, ≤8 bars): a ranking that puts the answer in context; set `highlight: true` on the bars the question is about. Add `value2` to each bar (with `value_label` and `value2_label` on the chart) to show a second measure beside it, such as volatility next to expected return, so the reader sees return and risk together.
- `explain` (≤700) and a shorter `explain_square`: what the answer means, a second layer of insight (risk-adjusted, ranking, or how it compares), what it doesn't mean, and a hedged "Our read:".
- `watch` (optional, ≤200): what would change the read. Shown on the portrait; `"watch_on_square": true` shows it on the square.
- `check_values` (optional, not drawn): references for any derived number you use in the analysis (for example a return-to-volatility ratio), so `--facts-only` prints and checks it.
- `source_line`: datasets and dates for the footer.

### 3. Check every number
```
python3 scripts/render_ask.py --spec <spec.json> --facts-only
```
Every number in the headline, analysis and post copy must appear here or in a cited source.

### 4. Render and inspect
```
python3 scripts/render_ask.py --spec <spec.json> --out <OUTPUT_DIR>/ask
```
Open both PNGs. Check that the headline isn't left with a one-word last line, tiles don't overlap, bar labels and values align, and the logos, footer and disclaimer show. Fix and re-render. Deliver the PNGs and `post_copy.md` with the session's file tool.

### 5. Post copy
Use the patterns in `references/canvas-spec.md`, with one change: open the LinkedIn post with the question itself (`post_question`), then the answer. The "How we made this" line says what Claude did. End with: "GradientCIO.com"

## Rules
- Model assumptions are assumptions, not forecasts. Say "Gradient's model expects" or "assumes", never "will return".
- Answer the question asked. If the data only partly answers it, say what's missing rather than stretching.
- No recommendations or positioning advice.
- Public and Gradient-calculated data only. Never use client portfolios or client data in a public Quick Take.

## Evidence note to the user (not for posting)
List each input's validation status, as-of date, methodology reference and digest (from `--facts-only`), and the source for each claim.

## Files
- `scripts/render_ask.py`: renderer.
- `scripts/spec.py`: shared reference resolver (identical in Tactical Dashboard).
- `scripts/brand.py`: the shared Gradient brand kit, synced from the plugin's shared Quick Take kit (`tools/sync_quicktake_shared.py`). Never edit it here.
- `assets/logos/`, `assets/fonts/`: synced from the shared kit; add official logo files there (see `references/canvas-spec.md` §5).
- `references/canvas-spec.md`, `references/spec_format.md`.
- `examples/`: the spec and saved inputs behind the Oct 21, 2026 sample.
