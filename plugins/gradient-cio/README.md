# Gradient CIO — client skills

Skills for institutional allocators that turn GradientCIO evidence into decision-ready documents. Report
skills deliver a branded PDF in the same Gradient house style (dark cover with lime accents, executive band,
status chips, source tags, sources appendix); `gradient-menu` replies in chat without loading report tooling.

## Skills

<!-- BEGIN GENERATED SKILL CATALOG -->
Start with `gradient-menu` to browse commands in chat or `gradient-setup` to check connection and data readiness.

### Start

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-menu` | Browse a command catalog for GradientCIO workflows. Triggers: 'show the skill menu', 'list GradientCIO commands', 'help me choose a workflow'. For connection readiness use gradient-setup. | none |
| `gradient-setup` | Create a readiness report for GradientCIO access and data. Triggers: 'check GradientCIO setup', 'test connector readiness', 'which workflows are ready'. For workflow selection use gradient-menu. | none |

### Research

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-research-macro-brief` | Create a macro briefing deck for an investment committee. Triggers: 'prepare a macro brief', 'review rates and credit conditions', 'build an IC macro deck'. For a committee decision use gradient-decision-ic-memo. | macroDesk,research,gradientSignals |
| `gradient-research-equity-note` | Create a sourced equity research note for one US-listed issuer. Triggers: 'research this ticker', 'review our concentrated holding', 'summarize filing changes'. For operational manager diligence use gradient-odd-report. | research,gradientSignals |

### Investment due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-idd-manager-performance` | Create a manager performance comparison report using governed return evidence. Triggers: 'compare manager track records', 'assess return performance', 'compare managers to benchmarks'. For operational comparison use gradient-odd-manager-compare. | strategyLab |
| `gradient-idd-manager-track-record` | Create a single-manager track-record assessment using governed return evidence. Triggers: 'is this track record good', 'assess one manager performance', 'is performance meaningful'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-robustness` | Create a manager robustness report for persistence across windows. Triggers: 'test performance persistence', 'run date-window robustness', 'check rolling consistency'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-portfolio-fit` | Create a portfolio-fit report for one prospective manager. Triggers: 'test manager portfolio fit', 'add this hedge fund manager', 'assess diversification impact'. For whole-sleeve design use gradient-portfolio-construction. | strategyLab |
| `gradient-idd-private-markets-pme` | Create a private-markets PME report for one fund or manager. Triggers: 'run private-markets PME', 'compare this fund to public markets', 'assess PME performance'. For program construction use gradient-portfolio-construction. | strategyLab |
| `gradient-idd-manager-shortlist` | Create a manager shortlist report for a defined mandate. Triggers: 'build a manager shortlist', 'screen this mandate', 'identify return finalists'. For operational comparison use gradient-odd-manager-compare. | strategyLab |

### Operational due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-odd-report` | Create an operational due-diligence report for a manager or fund. Triggers: 'run operational due diligence', 'prepare an ODD report', 'review manager operations'. For return performance use gradient-idd-manager-performance. | firmFundDiligence |
| `gradient-odd-manager-compare` | Create an operational comparison report for named managers. Triggers: 'compare manager operations', 'compare Form ADV disclosures', 'review service providers'. For return performance use gradient-idd-manager-performance. | firmFundDiligence,research |
| `gradient-odd-ddq-reconcile` | Create a DDQ reconciliation report against Form ADV evidence. Triggers: 'reconcile this DDQ', 'verify questionnaire answers', 'check DDQ discrepancies'. For a full operational review use gradient-odd-report. | firmFundDiligence |
| `gradient-odd-manager-monitor` | Create a manager-monitoring digest for a diligence roster. Triggers: 'prepare the weekly manager digest', 'show roster changes', 'review manager alerts'. For a full operational review use gradient-odd-report. | firmFundDiligence |

### Portfolio

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-portfolio-review` | Create a portfolio monitoring review for a board or committee. Triggers: 'review our total portfolio', 'prepare a quarterly portfolio review', 'monitor portfolio risks'. For a decision memo use gradient-decision-ic-memo. | portfolio,research,peerIntelligence,strategyLab |
| `gradient-portfolio-attribution` | Create a single-lane attribution report for one saved portfolio. Triggers: 'prepare an attribution report', 'run Brinson analysis', 'show sources of active return'. For broader portfolio monitoring use gradient-portfolio-review. | portfolio |
| `gradient-private-markets-portfolio-construction` | Create a private-markets construction report for an allocation program. Triggers: 'design private equity pacing', 'review private-markets commitments', 'build a private-markets program'. For one manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research,firmFundDiligence,strategyLab |
| `gradient-fixed-income-portfolio-construction` | Create a fixed-income construction report for a bond sleeve. Triggers: 'design a bond portfolio', 'review duration and credit', 'build a fixed-income sleeve'. For one manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research,macroDesk |
| `gradient-global-public-equity-portfolio-construction` | Create a global-equity construction report for a public-markets sleeve. Triggers: 'design global equity', 'review active passive mix', 'build an equity manager lineup'. For one manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research |
| `gradient-marketable-alternatives-portfolio-construction` | Create a marketable-alternatives construction report for a hedge-fund sleeve. Triggers: 'design a hedge fund portfolio', 'review redemption liquidity', 'build an alternatives strategy mix'. For one manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |
| `gradient-real-assets-portfolio-construction` | Create a real-assets construction report for an inflation-sensitive sleeve. Triggers: 'design real estate allocation', 'review infrastructure mix', 'build a real-assets portfolio'. For one manager fit use gradient-idd-manager-portfolio-fit. | portfolio,research,macroDesk,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |

### GIPS

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-gips-standards` | Create a GIPS standards briefing for a compliance question. Triggers: 'explain GIPS requirements', 'what is the compliance statement', 'compare GIPS and SEC rules'. For a document review use gradient-gips-report-review. | none |
| `gradient-gips-manager-diligence` | Create a GIPS diligence report for an investment manager. Triggers: 'verify a GIPS claim', 'review manager GIPS compliance', 'assess performance integrity'. For an operational review use gradient-odd-report. | firmFundDiligence |
| `gradient-gips-report-review` | Create a GIPS report review for a composite or pooled fund. Triggers: 'review this GIPS report', 'check a composite presentation', 'review a GIPS advertisement'. For general requirements use gradient-gips-standards. | none |
| `gradient-gips-asset-owner-review` | Create a GIPS asset-owner review for a total-fund report. Triggers: 'review an asset-owner report', 'check a board performance report', 'assess total-fund GIPS compliance'. For firm reports use gradient-gips-report-review. | none |
| `gradient-gips-policies-gap-check` | Create a GIPS policies gap report for a compliance manual. Triggers: 'review our GIPS manual', 'check missing GIPS policies', 'gap-check policies and procedures'. For report disclosures use gradient-gips-report-review. | none |

### Decision

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-decision-ic-memo` | Create a sourced decision memo for an investment committee. Triggers: 'draft an IC memo', 'prepare an allocation vote', 'write a manager hire memo'. For portfolio monitoring use gradient-portfolio-review. | portfolio,research,strategyLab,firmFundDiligence |

<!-- END GENERATED SKILL CATALOG -->

The skills work together: the asset-class construction skills select an existing portfolio and produce
read-only decision packs for a whole sleeve; the `gradient-idd-*` skills supply return-based manager evidence,
while `gradient-odd-manager-compare`, the ODD report and GIPS reviews supply operational evidence; the IC memo
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
