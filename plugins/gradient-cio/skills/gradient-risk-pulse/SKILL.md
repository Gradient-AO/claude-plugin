---
name: gradient-risk-pulse
description: "Create a Risk Pulse Quick Take from Gradient's GRIP risk gauge. Triggers: 'Risk Pulse', 'GRIP post', 'weekly risk reading', 'risk gauge', 'market stress post', 'this week's GRIP'."
metadata:
  group: "Quick Takes"
  subject: "market risk posture"
  output: "canvas"
  menu_order: "30"
  modules: "gradientSignals"
  contracts: "quick-takes,macro-signals"
  handoffs: "none"
  delivery: files
  status: "core"
  version: "1.0.0"
  summary: "Explain GRIP's score, path and underlying risk-pressure pillars."
---

# Risk Pulse (Quick Take)

A weekly post built from the GRIP Index. One of the five Quick Takes; every Quick Take follows one canvas spec. **Read `references/canvas-spec.md` before writing copy**: it covers the visual system, co-branding rules, narrative voice and copy patterns.

GRIP is proprietary, so nobody else can post it. The weekly rhythm trains readers to come back; the post text's "How we made this" line shows them they could ask the same question themselves.

Each run produces two PNGs (square 1080×1080, portrait 1080×1350), `post_copy.md` with LinkedIn, Substack and X copy, and an evidence note for the user.

## Workflow

### 1. Get the data
Call `get_macro_signals` with `view: "grip_index"`, `envelope: "compact"` and `lookbackDays: 400`. (The `minimal` envelope has returned a contract error.) History comes back 30 rows at a time: call again with `historyCursor` set to `history_truncation.next_cursor` until you have roughly 60 observations or the cursor runs out, and merge the pages by date.

Save one JSON file with: `as_of_date`, `availability`, `index_metadata` (for `laggingSeriesIds`), `current`, `decomposition.pillars` and `decomposition.top_contributors`, the merged `history` (`date`, `gripScore`, `stance`), `provenance` and `validation`. Copy values exactly.

### 2. Gates (the script enforces these)
- `validation.status` must be `passed`.
- **Saturation:** if 10 or more of the last 20 readings are at or above 95 (or `saturationDetected` is `true`), the render stops. A gauge pinned at its ceiling cannot show change; use `--allow-saturated` only for a one-off post that says so explicitly.
- `availability.status` must be `available` or `degraded`. When degraded, the footer automatically names the lagging input; mention it in the evidence note.
- Data more than 3 business days old stops the render unless the user accepts it (`--allow-stale`).

### 3. Pull the facts
```
python3 scripts/render_riskpulse.py --input <grip.json> --facts-only
```
Key fields: `score`, `stance`, `band`; `one_week_ago` and `four_weeks_ago` (latest observation at least 7 and 28 days back, with the change in points); `window_high` and `window_low`; `stance_run_obs` and `stance_run_since`; `pillars` (score, stance, weight); `top_contributors` (z-scores and weighted pressure).

### 4. Find the story
Pick the one thing a CIO would want to know this week:
- **Change:** did GRIP move a lot, or flip stance? (`one_week_ago`, `four_weeks_ago`, `stance_run_since`)
- **Composition:** which pillar is doing the work, and which is calm? A split such as "rates stressed, credit calm" is often the most useful read.
- **Persistence:** a long run in one stance is a story even when the score barely moves.

Then evidence the driver. Start with the top contributors in the payload and use other validated `get_macro_signals` views when relevant. Quote a Gradient number only if its `validation.status` is `passed`, and note its date. Add a web search for dated rates, credit, FX, inflation or growth catalysts in the window when needed.

### 5. Write the words
- `--headline` (≤90 characters): one plain claim, e.g. "Risk pressure eased this week, but GRIP is still Defensive".
- `--subtitle`: defaults to the scale explanation; keep a short "0–100 scale: higher = more risk pressure" unless you have a better reading aid.
- `--explain` (aim for 420–560 characters, max 700) for the portrait, and `--explain-square` (about 300–360) for the square: lead with where the pressure is coming from, give one or two dated numbers, contrast with the calm pillar, close with "Our read:". Don't restate the chart.
- `--watch` (optional, ≤200, portrait only): what would change the read, as a condition.
- Also write down the question a CIO would type, e.g. "Where does Gradient's GRIP risk gauge stand this week, and what's driving it?" It goes in the post text, not on the image.

### What the image shows automatically
- Score, stance and band, with the change vs. one and four weeks earlier and the window high.
- The GRIP path with Defensive-or-worse periods shaded.
- The five pillars in Title Case with their weight in GRIP, score and stance.
- Portrait only: the top contributors by weighted pressure, with z-scores.

### 6. Render and inspect
```
python3 scripts/render_riskpulse.py --input <grip.json> --out <OUTPUT_DIR>/riskpulse \
  --headline "..." --subtitle "..." --explain "..." --explain-square "..." [--watch "..."]
```
Open both PNGs and look. Check the lockup, the pillar labels and scores (no overlap), the chart's end label, the logos, footer and disclaimer. If the script stops on chart height, shorten the analysis first. Deliver the PNGs and `post_copy.md` with the session's file tool.

### 7. Post copy
Follow the patterns in `references/canvas-spec.md`. The LinkedIn closing line is: "Data: Gradient GRIP Index, as of <date>. Not investment advice. GradientCIO.com"

## Accuracy rules
- GRIP measures current risk pressure. It is not a forecast, a timing signal or a recommendation. Never write "GRIP says sell", "expect", "will" or anything similar.
- Use the payload's stance and band labels exactly; never invent thresholds between stances.
- Changes are in **points** ("−4 pts"), not percent.
- Top-contributor z-scores describe pressure on GRIP's own scale. Don't translate them into claims about valuations unless a governed indicator or cited source supports the claim.
- Every number in the copy must appear in the facts JSON, a validated Gradient payload, or a cited source.

## Evidence note to the user (not for posting)
One line with as-of date, validation, availability (and any lagging input), `gradient://methodology/grip-index` and the first 12 characters of `payload_digest`; then one bullet per claim in the analysis with its source.

## Files
- `scripts/render_riskpulse.py`: renderer (gates, facts, layout, pillar bars).
- `scripts/brand.py`: the shared Gradient brand kit, synced from the plugin's shared Quick Take kit (`tools/sync_quicktake_shared.py`). Never edit it here.
- `assets/logos/`, `assets/fonts/`: synced from the shared kit; add official logo files there (see `references/canvas-spec.md` §5).
- `references/canvas-spec.md`: the one canvas spec for every Gradient post (grammar, brand, data rules, copy patterns).
