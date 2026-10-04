---
name: gradient-macro-brief
description: "Build a branded investment-committee macro briefing deck (16:9 PDF) from GradientCIO evidence: The Read, rates and credit conditions, Gradient macro signals and GRIP, the 30-day event calendar and capital market assumptions, with sources and what would change the view."
---

# Macro briefing deck

Use when the user asks for a macro deck, market update for the committee or board, IC macro briefing,
"turn The Read into slides", "what should the committee know about markets this month", or a pre-meeting
macro pack.

The deliverable is a 9–12 slide landscape PDF in the Gradient house style,
**"<Org> - Macro Briefing <YYYY-MM-DD>.pdf"**, rendered with `--deck`. Audience: an investment committee.
Each slide has one message in its title and a one-line takeaway.

Evidence rules (from GradientCIO):
- Use numbers only from structured fields: `read.facts`, `market_highlights`, indicator `latest` values,
  signal scores, calendar rows, CMA items. Never pull numbers out of `read.prose`; quote prose only as
  The Read's narrative, attributed.
- Signals, percentiles and GRIP describe stated historical or modeled context. They are not forecasts, fair
  values or return predictions. Say "points to", "consistent with", not "will".
- CMAs are Gradient house assumptions (10-year, excess over local risk-free, arithmetic). State base currency,
  horizon and return basis, disclose `quality_receipt.status` and quality flags, and make no comparison with
  other providers unless the receipt is validated.
- Every number carries its observation date. Every slide lists its source tags in a note.

## 1. Collect

Pick the as-of date: the last business day (or the user's meeting date minus one business day).

| Evidence | Call | Notes |
|---|---|---|
| The Read | `get_the_read` with `asOfDate` (required — omitting it fails) | If unpublished, step back one day, up to 3. Keep headline, governing thesis, read units, facts, market highlights, follow-ups, reading list, coverage |
| Rates | `get_macro_conditions` `view: indicators`, `theme: rates`, `limit: 8` | Levels, 1m/3m change, 1y/5y percentile |
| Inflation, growth | same, `theme: inflation` and `theme: growth` | Optional; use when The Read is about them |
| Credit | `get_macro_conditions` `view: credit_spreads` (no `limit`) | |
| Gradient signal | `get_macro_signals` `view: gradient_signal` | Composite, regime, driver scores, supportive/detracting signals, GRIP (`sources.grip.current`), degraded sources |
| Regime state | `get_macro_signals` `view: regime_state`, `regions: ["NA","EU"]` | Optional; retry once on 500, then omit and note it |
| Calendar | `get_macro_calendar` `view: scheduled_events`, `windowDays: 30`, `limit: 15` | Keep decision rules |
| CMAs | `get_capital_market_assumptions` `view: baseline`, `per_page: 10` (page 1–2) | Primary factors; risk-free rate and freshness |

Record for each call: as-of, validation status, coverage/degradation reasons, payload digest. If The Read or the
calendar is unavailable, stop and tell the user — the deck needs both. Other gaps: build the deck and say what
is missing on the slide and in the sources slide.

## 2. Storyline

1. **Cover** (automatic): title "Macro Briefing", subtitle "<Org> investment committee · <meeting date>",
   cover facts: As of, The Read edition, GRIP stance, Next major event.
2. **The Read in one slide** — title = The Read headline. `statement` block with the governing thesis;
   tiles with 2–4 `read.facts` values (value, unit, date). Takeaway: the thesis in plain words.
3. **What moved** — `table` of market highlights (category, series, move, horizon, date).
4. **Rates and the curve** — `bars` or `table` of rate indicators: level, 1m change (bps), 1y percentile.
   Use `line` charts only when The Read returns `visuals` series.
5. **Risk posture** — Gradient signal composite and regime; `bars` of driver scores (0–100, label stance);
   GRIP stance and score with coverage. State that higher scores mean more risk pressure.
6. **What supports / what detracts** — `two` layout: supportive signals vs detracting signals (label, driver,
   z-score).
7. **The other side** — The Read's rival view and the levels that would confirm or break the thesis
   (from the `read_rival` and `read_monitoring` units, quoted and attributed).
8. **Next 30 days** — calendar `table`: date, event, importance (chip), what to watch (decision rule, shortened).
9. **Long-run assumptions** — CMA `bars` of 10-year expected excess return by primary factor with volatility in
   the label; note risk-free rate, release, `quality_receipt.status` and flags (bond rows ≈ 0 must be caveated).
10. **Questions for the committee** — `questions` block from `recommended_followups` (3–4), each with why it
    matters for the portfolio.
11. **Sources and method** — `table`: tag, source, as-of, validation, notes (degradations); disclaimer.

Use a `section` layout slide only if the deck exceeds 11 slides. Use `two` for side-by-side content and `wide`
for chart-plus-commentary.

## 3. Render and check

Write `deck.json` (deck format in `references/report-style.md`). Meta: `eyebrow` "Investment Committee",
`header_label` "Macro Briefing", `title` "Macro Briefing", `data_as_of`.

```
python <this skill's directory>/scripts/gradient_report.py --deck deck.json "<Org> - Macro Briefing <date>.pdf"
```

The renderer exits with code 3 and names the slides whose content overflows: split the slide or cut content,
then re-render. Rasterize (`pdftoppm -r 40 -png`) and look at every slide. Then follow "Check and deliver".
Chat summary: The Read headline, the risk posture in one line, and the next high-importance event.

If the user wants to edit slides, offer to rebuild the content in their slide tool of choice after delivering
the PDF.
