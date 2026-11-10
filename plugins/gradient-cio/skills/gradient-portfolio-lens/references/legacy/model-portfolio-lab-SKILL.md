---
name: "gradient-model-portfolio-lab"
description: "Gradient Model Portfolio Lab: turns Gradient's model portfolios (Total Plan and the sleeve models) plus Gradient's own capital market assumptions into branded Gradient social posts that show the allocation, estimate expected return and risk, show where the risk really sits, compute marginal return and marginal risk, and evaluate marginal allocation changes (for example 'move 5% from Public Equity to Private Debt'). Produces square and portrait images plus LinkedIn, Substack and X copy, with every number computed from validated Gradient data. Use this skill whenever the user asks for a model portfolio post, a portfolio analytics or risk post, a 'what if we moved X% from A to B' post, a capital-vs-risk, risk-budget or marginal return and risk post, a comparison of model portfolios or vs. a 60/40, or any LinkedIn/Substack/X content built from Gradient model portfolios or capital market assumptions, even if they only say 'do this week's model portfolio post'."
---

# Gradient Model Portfolio Lab

> **Archived legacy reference — do not execute directly.** Current Portfolio Lens workflows use `SKILL.md` at the skill root, `references/lens-framework.md`, and `scripts/build_cma_mcp.py`. Legacy script names below (`build_cma.py`, `lab.py`, `portfolio_math.py`) are retained for historical reference only.

The content series is built on analysis only Gradient can produce: its model portfolios combined with its own capital market assumptions (CMAs). Each post shows a real model allocation, estimates its risk, and evaluates marginal changes: marginal return and marginal risk of the next 1%, or a specific move from one sleeve to another. Readers engage even when the allocation doesn't match their own, because the question ("where does the risk sit?", "what does this move do?") applies to every plan.

**Read before starting:** `references/models_and_data.md` (models, IDs, how to fetch inputs, the real-data rules, known assumption caveats) and `references/templates_and_ideas.md` (templates, pre-tested idea menu, writing and copy rules).

Each run produces two PNGs (square 1080×1080, portrait 1080×1350), `post_copy.md` (LinkedIn, Substack, X), and an evidence note for the user.

## Non-negotiable rules
1. **Real data only.** Use model **policy target weights** and Gradient CMAs. Never publish holdings, "actual" weights, fund or manager names, holdings-based risk reports, or Strategy Lab demo series: Gradient's model holdings are fictional demo funds with synthetic returns. `portfolio_math.gate_inputs` enforces this; never bypass it.
2. **Every number is computed.** Claude writes only words. All figures on the image are drawn by `lab.py`; every figure in the headline, analysis and copy must come from `lab.py facts`.
3. **Assumptions, not forecasts.** Say "expected", "assumed", "on Gradient's assumptions". No recommendations, no "investors should", no timing.
4. **Respect the desmoothing check.** Every render recomputes the result with private-market volatilities at Gradient's house level and prints it. If the conclusion flips, the render stops; publish only as an explicitly two-sided post. See `models_and_data.md`.
5. **Disclose proxies and caveats.** List proxy mappings in the Substack Method section. Respect the assumption caveats in `models_and_data.md`.
6. **Title Case** for asset classes, sleeves and model names ("Public Equity", "Private Debt", "Total Plan").

## Workflow

### 1. Inputs
- **CMA file:** use the current build in `examples/cma_q3_2026.json` unless a newer CMA release exists. Check with `get_capital_market_assumptions` `view: "baseline"` (look at `release.version`). For a new release, rebuild with `scripts/build_cma.py` (see `models_and_data.md`).
- **Model file:** `examples/model_total_plan.json` and `examples/model_private_markets.json` are ready. For another model, fetch its allocation tree and run `scripts/build_model.py`. Rebuild a model whenever its policy changes.

### 2. Pick the template and the move
Choose from `references/templates_and_ideas.md`. Rotate templates and models so the feed stays fresh, and don't repeat a move within a quarter. A move is `{"from": <sleeve or class>, "to": <sleeve or class>, "amount": <decimal of total portfolio>}`.

### 3. Write a draft spec and pull the facts
Copy an example spec from `examples/` (`post_marginal.json`, `post_move.json`, `post_cvr.json` or `post_cmp.json`), set the template, model, CMA file and move, and use placeholder words. Then:
```
python3 scripts/lab.py facts --spec <spec.json>
```
Read: `marginal` (marginal return and marginal risk of the next 1% per class or sleeve), `sensitivity` (the desmoothing check, including `flips`), `base` and `after` (expected excess and total return, volatility, return per unit of risk, class weights and risk shares, top risk sleeves), `delta`, `bands_after` (stop and reconsider if any class is outside its band), `points` (model comparison) and `proxies`.

### 4. Write the words into the spec
`headline`, optional `subtitle` (defaults to the mandatory model note; keep it unless there's a strong reason), `explain`, `explain_square`, `watch`. Follow the writing rules in `templates_and_ideas.md`. Tie the analysis to the mechanism: concentration, correlation, volatility, and the policy band.

### 5. Render and inspect
```
python3 scripts/lab.py render --spec <spec.json> --out <OUTPUT_DIR>/lab
```
`<OUTPUT_DIR>` is the session's outputs folder. **Open both PNGs.** Check for overlapping text, labels running into bars, a crowded scatter, and that the allocation strip, sources and disclaimer are visible. If the script stops on space, shorten `explain_square`, the watch line or the headline. Deliver the PNGs and `post_copy.md` with the session's file tool.

### 6. Post copy and evidence note
Write `post_copy.md` per `templates_and_ideas.md`, including the Substack **Method** section with the full proxy list. Then give the user a short evidence note: model name and portfolio_id, structure payload digest (from the model file's provenance), CMA release and date, the move, the key `facts` numbers used, any band or caveat flags.

## Files
- `scripts/portfolio_math.py`: the engine (gate, expected return, volatility, risk contributions, marginal return and risk, moves, band checks, desmoothing sensitivity, reference 60/40).
- `scripts/lab.py`: facts and render for the four templates (capital_vs_risk, marginal_move, marginal_map, model_compare), with the desmoothing check and flip gate.
- `scripts/build_model.py`, `scripts/build_cma.py`: build model and CMA input files from Gradient payloads.
- `scripts/brand.py`: Gradient brand kit (colors, Inter font, logo lockup, footer, disclaimer, Title Case helper).
- `assets/fonts/` (Inter, OFL); `assets/logos/` (drop Gradient's official `gradient.svg` or `.png` here; text wordmark otherwise).
- `references/models_and_data.md`, `references/templates_and_ideas.md`, `references/sleeve_factor_map.json`.
- `examples/`: Q3 2026 CMA build, Total Plan and Private Markets models, and the three sample post specs.
