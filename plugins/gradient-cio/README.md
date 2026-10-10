# Gradient CIO — client skills

Skills for institutional allocators that turn GradientCIO evidence into decision-ready documents. Report
skills deliver a branded PDF in the same Gradient house style (dark cover with lime accents, executive band,
status chips, source tags, sources appendix); `gradient-menu` replies in chat without loading report tooling.

## Skills

<!-- BEGIN GENERATED SKILL CATALOG -->
Start with `gradient-menu` to browse commands in chat or `gradient-setup` to check connection and data readiness.

### Review

| Skill | Produces / routes |
|---|---|
| `gradient-portfolio-review` | Create a branded brief or comprehensive portfolio monitoring report. Triggers: 'portfolio review', 'quarterly review', 'board performance report', 'policy ranges'. Hands decisions to gradient-ic-memo and focused attribution to its report skill. |
| `gradient-portfolio-attribution-report` | Create a branded historical and governed ex ante attribution report. Triggers: 'attribution report', 'Brinson analysis', 'sources of active return'. Hands broad monitoring to portfolio review and decisions to IC memo. |
| `gradient-equity-note` | Create a branded, sourced note on one US-listed issuer. Triggers: 'equity note on a ticker', 'top holding', 'concentrated position', 'what changed in the filing', 'who holds this ticker'. Hands manager diligence to ODD and decisions to IC memo. |

### Decide

| Skill | Produces / routes |
|---|---|
| `gradient-macro-brief` | Produce an IC macro briefing from The Read, rates, credit, signals, GRIP, events, and CMAs. Use for macro brief, market outlook, rates and credit, or IC macro deck. For a portfolio decision use gradient-ic-memo. |
| `gradient-ic-memo` | Create a deterministic, sourced IC decision memo. Triggers: 'IC memo', 'board memo', 'allocation recommendation', 'rebalance proposal', 'manager hire/fire', 'committee vote'. Accepts handoffs from portfolio, diligence, and GIPS skills. |
| `gradient-fixed-income-portfolio-construction` | Build a fixed-income allocation report covering bonds, duration, credit, benchmarks, liquidity, and scenarios. Use for bond portfolio, core/core-plus, duration, or credit sleeve. For a cross-portfolio decision use gradient-ic-memo. |
| `gradient-global-public-equity-portfolio-construction` | Build a global public-equity allocation report covering regions, managers, factors, concentration, and benchmarks. Use for global equity, active/passive, factor tilt, or manager lineup. For a committee vote use gradient-ic-memo. |
| `gradient-marketable-alternatives-portfolio-construction` | Build a marketable-alternatives report covering hedge funds, strategy mix, factor risk, redemption terms, and liquidity. Use for hedge fund portfolio, alternatives sleeve, or redemptions. For a committee vote use gradient-ic-memo. |
| `gradient-private-markets-portfolio-construction` | Build a private-markets allocation report covering PE/private credit, commitments, pacing, cash flows, and liquidity. Use for private markets portfolio, commitment plan, or pacing. For a committee vote use gradient-ic-memo. |
| `gradient-real-assets-portfolio-construction` | Build a real-assets allocation report covering real estate, infrastructure, commodities, inflation linkage, and liquidity. Use for real assets portfolio, inflation hedge, or real estate mix. For a committee vote use gradient-ic-memo. |

### Diligence

| Skill | Produces / routes |
|---|---|
| `gradient-manager-compare` | Create a branded evidence comparison for 2–5 managers or screen a mandate. Triggers: 'compare managers', 'shortlist managers', 'screen advisers', 'manager overlap'. Hands off selected managers to gradient-odd-report or gradient-ic-memo. |
| `gradient-odd-report` | Create a branded, sourced ODD report or roster triage. Triggers: 'ODD report', 'due diligence report', 'run diligence', 'ODD on my roster'. Hands findings to DDQ reconciliation, manager comparison, monitoring, or an IC memo. |
| `gradient-ddq-reconcile` | Create a branded DDQ-versus-Form-ADV discrepancy report. Triggers: 'check this DDQ', 'verify the questionnaire', 'reconcile DDQ', 'does this match the ADV'. Hands confirmed gaps to diligence findings and ODD. |

### Monitor

| Skill | Produces / routes |
|---|---|
| `gradient-manager-monitor` | Create a branded manager-roster digest. Triggers: 'weekly monitoring', 'what changed across managers', 'roster digest', 'any alerts'. Hands flagged subjects to ODD or DDQ reconciliation and can schedule read-only runs. |

### GIPS

| Skill | Produces / routes |
|---|---|
| `gradient-gips-standards` | Produce a sourced GIPS requirements briefing. Use for what does GIPS require, compliance statement, verification, required disclosures, or GIPS vs SEC Marketing Rule. For a document review use the matching gradient-gips-* skill. |
| `gradient-gips-manager-diligence` | Produce a GIPS manager-diligence report. Use for verify GIPS claim, manager GIPS review, performance integrity, or GIPS DDQ. For a report or presentation line review use gradient-gips-report-review. |
| `gradient-gips-report-review` | Produce a line-by-line GIPS report or advertisement review. Use for review this GIPS report, composite presentation, pooled fund report, or advertising guidelines. For general requirements use gradient-gips-standards. |
| `gradient-gips-asset-owner-review` | Produce a GIPS Asset Owner Report review for pensions, endowments, foundations, and sovereign funds. Use for asset owner GIPS, total fund report, or board performance report. For firm reports use gradient-gips-report-review. |
| `gradient-gips-policies-gap-check` | Produce a GIPS policies-and-procedures gap report. Use for review our GIPS manual, policy gap check, missing GIPS policies, or asset-owner P&P. For report disclosures use gradient-gips-report-review. |

<!-- END GENERATED SKILL CATALOG -->

The skills work together: the asset-class construction skills select an existing portfolio and produce
read-only decision packs; manager comparison, ODD and GIPS reviews supply implementation evidence; the IC memo
provides the formal 16-section vote format; and the portfolio review monitors the approved portfolio. The
portfolio attribution report provides a focused realized-versus-expected effect analysis without prescribing
portfolio changes. The
monitoring digest and ODD report can log reviews, update findings and start monitoring in GradientCIO —
always as a preview first, and only after you confirm.

## Requirements

- **GradientCIO connector** — bundled with the plugin (`https://mcp.gradientcio.com/mcp`); each user signs in
  once from their connector settings. Run gradient-setup to confirm access. The GIPS skills also work from
  documents alone.
- **Python 3.11+ with Playwright (Chromium)** and poppler (`pdftoppm`, `pdfunite`) or `qpdf` to render PDFs.
  These are available in Cowork; elsewhere run `pip install playwright && python -m playwright install chromium`.

## House style

All skills render with the same `scripts/gradient_report.py` and follow `references/report-style.md`
(cover, labels, signal levels, writing rules, file naming and delivery). Reports never change colours or fonts.

## Client branding

Reports can carry a client's name and logo with "Powered by GradientCIO"; colours and fonts never change.
Before distributing a client build: `python tools/set_branding.py --client "<Client>" --logo <logo.png|svg>`,
then run the tests with `--allow-branded` and repackage. `python tools/set_branding.py --reset` restores
Gradient branding. A single report can also be branded at run time (see `shared/report-style.md`).

## Maintainers

Follow `CLAUDE.md` at the repository root: it is the single source for the change, test, versioning and
release process. Edit the renderer and style guide only in `shared/`, then run `python tools/sync_shared.py`.

Validation policy shared by multiple JSON reports lives in `tools/report_constants.py`; generic report
contracts live in `tools/report_json_validator.py`, and construction contracts live in
`tools/construction_report_validator.py`. Skill-local validators retain their small `parents[3]` path
bootstrap so they can be invoked directly from a skill while importing the plugin-level tools.

`tests/run_tests.py` is the test entry point. It orchestrates the focused modules under `tests/suites/`; use
`--static` for the fast contract and validator lane, or run it without flags for the complete PDF, PowerPoint,
layout and release-quality regression suite. CI checks manifest version parity and shared-file sync before
installing the heavier renderer dependencies.
