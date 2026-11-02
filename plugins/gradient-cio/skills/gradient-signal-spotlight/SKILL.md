---
name: gradient-signal-spotlight
description: "Create a Signal Spotlight Quick Take from Gradient relative-return signals. Triggers: 'Signal Spotlight', 'relative-value post', 'growth vs value', 'chart of the day', 'this week's market post'."
metadata:
  group: "Quick Takes"
  subject: "relative-return signals"
  output: "canvas"
  menu_order: "20"
  modules: "gradientSignals"
  contracts: "quick-takes,macro-signals"
  handoffs: "none"
  delivery: files
  status: "core"
  version: "1.0.0"
  summary: "Explain an unusual relative-return move and its likely driver."
---

# Signal Spotlight (Quick Take)

Produces a ready-to-post image from Gradient's relative-return signals, with matching copy. One of the five Quick Takes; every Quick Take follows one canvas spec. **Read `references/canvas-spec.md` before writing any copy**: it defines the visual system, the co-branding rules and the narrative voice.

The idea: *the market move is the hook; Gradient's data does the explaining.* The image is all results and analysis; the post text tells readers the question asked in Claude and how the post was made, so a CIO wants to run it on their own portfolio.

Each run produces:
1. Two PNGs: square 1080×1080 (LinkedIn, X) and portrait 1080×1350 (LinkedIn feed).
2. Post copy for LinkedIn, Substack and X, saved as `post_copy.md` next to the PNGs.
3. An evidence note for the user (not for posting).

## Flexibility: choosing the angle
The defaults reproduce the classic post. Change them when the story is better told another way.

| Option | Flag | When to use |
|---|---|---|
| Pair | `--pair-id` (and the same `pairId` in the data call) | The user names a pair, or the top-ranked pair repeats a recent post. |
| Hero horizon | `--horizon auto\|5\|21\|3m` | `auto` = the pair's winning horizon. Use `21` for a "past month" story, `3m` for a slower allocator-relevant drift (no percentile is shown in 3m mode). |
| Chart window | `--chart one_year\|three_month` | `three_month` zooms in when the recent path is the story. |
| Brand | `--brand cobrand\|gradient` | `gradient` shows the Gradient logo alone if co-brand approval is pending (see `references/canvas-spec.md`). |

Rotate themes across weeks (regions → sectors → styles → cross-asset) so the feed stays varied. `board_total` shows every pair's rank, move and 3-month return, which is useful for picking a fresh angle.

## Workflow

### 1. Get the data
Call `get_macro_signals` with `view: "relative_returns"` and `envelope: "compact"` (the `minimal` envelope has returned a contract error). Default is no `pairId`: Gradient's `selected` pair is the top-ranked one by |z| across 5-day and 21-day windows. If the user named a pair, map it to a `pair_id` from `board_total` and call again with `pairId`.

The result is often saved to a file; use that path as `--input`. If it comes back inline, write it to a JSON file first. The renderer needs: `as_of_date`, `data_state`, `quiet_day`, `eligible_pair_count`, `notable_pair_count`, `validation`, `provenance`, `methodology_version`, and the full `selected` object (including `signals`, `three_month`, `one_year_range`, `highlight_window`, `one_year_path`, and `three_month_path` if you use the 3-month chart). Copy values exactly; never retype or round them.

### 2. Gate the data (the script enforces these)
- `validation.status` must be `passed` and `data_state` must be `available`, or the script stops. Tell the user and don't post.
- Data more than 3 business days old stops the script. Use `--allow-stale` only if the user accepts dated data, and then say the date in the copy.
- `quiet_day: true` triggers a warning: no pair is statistically notable. Offer a "quiet market" framing or skip.

### 3. Pull the facts
```
python3 scripts/render_spotlight.py --input <payload.json> [--pair-id ID] [--horizon ...] --facts-only
```
Write all copy from this JSON. Key fields:
- `at_chart_extreme`: `low` or `high` when the spread sits at the extreme of the chart period. This is often the best headline; say "since <month year of one_year_path_start_date>", never "ever" or "past year".
- `largest_since_date` is only newsworthy when well over 3 months back or `percentile_abs` is 100.
- `one_year_path_start_date` can be ~15 months back: say "since <month year>".
- `three_month` carries its own `start_date`; quote it as "since <month>".
- The chart end label and `three_month.relative_return_pct` cover different windows. Never present them as the same "current" number.

### 4. Research the driver (required)
Build a hypothesis for why the spread moved over `highlight_window` (or the 3-month window in `3m` mode).
1. **Gradient data first** (governed numbers): use `get_macro_signals` view `signal_changes` and the selected pair's relative-return payload. Quote a Gradient number only if its `validation.status` is `passed`, and note its as-of date.
2. **Web search** for dated catalysts inside the window: policy decisions, data surprises, earnings, flows, commodity moves and relevant macro releases. Prefer primary or reputable sources and keep the URLs. Search each leg separately.
3. **Match the mechanism to the pair**: sectors and styles → rates, growth, commodities; regions → policy divergence, currency, sector mix, flows; FX → relative policy surprises and rate gaps.

**Sanity-check direction** against each leg's sign before writing. If the evidence points the other way, say so or choose another driver.

### 5. Write the words
You supply four strings; the script draws every number.
- `--headline` (≤90 characters, aim for 45–60): one plain-English claim. Concrete beats clever. For a routine move (`percentile_abs` under ~70) say so honestly.
- `--subtitle` (one line): how to read the line, e.g. "Falling line = China Equity trailing India Equity". **Always set it for currency pairs**, using the payload's `reading` field and one public spot-rate check, and describe currencies in plain words.
- `--explain` (aim for 500–680 characters, max 780): 4–6 sentences. Lead with the hypothesis, give one or two dated pieces of evidence with numbers, explain the mechanism across both legs, use the horizon chips to say whether this is a new move or part of a longer trend ("the longer windows show…"), and close with "Our read:". Don't restate the chart's numbers.
- `--explain-square` (about 300–380 characters): the shorter version for the square image. Write it whenever the square would otherwise run out of chart space.
- `--watch` (optional, ≤200): one sentence on what would change the read, phrased as a condition, never a prediction. It shows on the portrait; add `--watch-square` to show it on the square too. See `references/canvas-spec.md`.
- Also write down the real question a CIO would type into Claude to get this post. It goes in the post text ("How we made this"), not on the image.

If a render stops because the chart would be too short, trim the watch line or analysis first, then the headline.

### What the image shows automatically
- **Hero panel:** the selected move, its percentile, whether the spread is at its chart extreme, and each leg's move.
- **Horizon chips:** the same spread over 5 days, 21 days, 3 months and since the chart starts, so readers see at a glance whether the week is a new move or part of a trend.
- **Chart:** the cumulative path with the latest window shaded, the end value labeled, and the chart's high and low labeled with their month.
- Pair and leg names are set in Title Case automatically.

### 6. Render and inspect
```
python3 scripts/render_spotlight.py --input <payload.json> [--pair-id ID] [--horizon ...] [--chart ...] \
  --out <OUTPUT_DIR>/spotlight --headline "..." --subtitle "..." --explain "..." --explain-square "..." [--watch "..."]
```
`<OUTPUT_DIR>` is the session's outputs folder (for example `/mnt/user-data/outputs`). **Open both PNGs and look at them.** Check for overlapping text, a clipped headline, a squashed chart, an end label colliding with an axis label, and that the lockup (logos), footer and disclaimer are all visible. Fix the copy and re-render if needed. Deliver the PNGs and `post_copy.md` with the session's file tool (`present_files`, or `SendUserFile` in Cowork).

### 7. Write the post copy
Follow the LinkedIn, Substack and X patterns in `references/canvas-spec.md`, including the **"How we made this"** line with the question in quotes, and the GradientCIO.com close. Lead with what Gradient flagged, not with a market opinion.

## Accuracy rules (non-negotiable)
- **Units:** `move_pct` is ratio growth, ((1+long)/(1+short) − 1) × 100. Call it a "relative move" or "spread" in %, never "percentage points", and never compute long minus short.
- **Keep horizons separate.** 5-day, 21-day, 3-month and chart-period numbers are different windows; say which window every number comes from. 21 trading days is "about a month".
- **z-scores and percentiles measure statistical unusualness, not importance.** Say "bigger than 98% of 5-day moves in the past year". Don't call anything "unprecedented"; history starts at `history_start_date`.
- **Causes are hypotheses** resting on cited evidence, in hedged language. No crowd-psychology claims without a source.
- **No forecasts, no recommendations.**
- **FX pairs:** trust the payload's `reading` for direction and confirm it with one public spot-rate check for the window. A past payload's "quoted as USD per foreign currency" note was wrong; the legs behaved as foreign currency per USD.
- Every number in the copy must appear in the facts JSON (or a validated Gradient payload, or a cited source), rounded to 1 decimal place the way the image rounds it. Use the real minus sign (−).

## Evidence note to the user (not for posting)
After the files, give one line with pair, as-of date, `validation.status`, `provenance.as_of`, `gradient://methodology/relative-returns` and the first 12 characters of `payload_digest`; then one bullet per piece of evidence in the analysis with its source (Gradient tool and as-of date, or URL). Flag any caveats so the user can check every claim before posting.

## Files
- `scripts/render_spotlight.py`: the Signal Spotlight renderer (data gates, facts, layout).
- `scripts/brand.py`: the shared Gradient brand kit, synced from the plugin's shared Quick Take kit (`tools/sync_quicktake_shared.py`). Never edit it here.
- `assets/fonts/`: Inter (OFL) with its license.
- `assets/logos/`, `assets/fonts/`: synced from the shared kit; add official logo files there (see `references/canvas-spec.md` §5).
- `references/canvas-spec.md`: the one canvas spec for every Gradient post (grammar, brand, data rules, copy patterns).
