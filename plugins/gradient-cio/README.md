# Gradient CIO — client skills

Skills for institutional allocators that turn GradientCIO evidence into decision-ready documents. Report
skills deliver a branded PDF in the same Gradient house style (dark cover with lime accents, executive band,
status chips, source tags, sources appendix); `gradient-menu` replies in chat without loading report tooling.

## Skills

<!-- BEGIN GENERATED SKILL CATALOG -->
Start with `gradient-menu` to browse commands in chat or `gradient-setup` to check connection and data readiness.

### Research

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-macro-brief` | Produce an IC macro briefing from The Read, rates, credit, signals, GRIP, events, and CMAs. Use for macro brief, market outlook, rates and credit, or IC macro deck. For a portfolio decision use gradient-ic-memo. | macroDesk,research,gradientSignals |
| `gradient-equity-note` | Create a branded, sourced note on one US-listed issuer. Triggers: 'equity note on a ticker', 'top holding', 'concentrated position', 'what changed in the filing', 'who holds this ticker'. Hands manager diligence to ODD and decisions to IC memo. | research,gradientSignals |

### Investment due diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-idd-manager-compare` | Create a sourced manager-performance comparison report. Triggers: 'compare track records', 'risk and return comparison', 'compare managers to benchmarks'. For operational comparison use gradient-manager-compare. | strategyLab |
| `gradient-idd-manager-track-record` | Create a sourced single-manager track-record assessment. Triggers: 'is this track record good', 'assess this manager performance', 'is performance meaningful'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-robustness` | Create a sourced manager persistence and robustness report. Triggers: 'does performance persist', 'test start dates', 'rolling performance', 'regime robustness'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-portfolio-fit` | Create a sourced one-manager portfolio-fit and diversification report. Triggers: 'what does adding this manager do', 'portfolio fit', 'diversification impact'. For whole-sleeve design use a portfolio-construction skill. | strategyLab |
| `gradient-idd-private-markets-pme` | Create a sourced private-markets PME report. Triggers: 'private markets PME', 'public market equivalent', 'direct alpha', 'cash-flow performance'. For operational diligence use gradient-odd-report. | strategyLab |
| `gradient-idd-manager-shortlist` | Create a sourced return-based IDD manager-shortlist report. Triggers: 'build a manager shortlist', 'screen this mandate', 'which managers advance'. For a Form ADV-only screen use gradient-manager-compare. | strategyLab |

### Operational diligence

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-odd-report` | Create a branded, sourced ODD report or roster triage. Triggers: 'ODD report', 'operational due diligence', 'run diligence', 'ODD on my roster'. For return performance use gradient-idd-manager-track-record. | firmFundDiligence |
| `gradient-manager-compare` | Create a branded ODD comparison or Form ADV screen from adviser, service-provider, disclosure, and 13F evidence. Triggers: 'compare advisers', 'compare operational risk', 'screen ADV records'. For returns use gradient-idd-manager-compare. | firmFundDiligence,research |
| `gradient-ddq-reconcile` | Create a branded DDQ-versus-Form-ADV discrepancy report. Triggers: 'check this DDQ', 'verify the questionnaire', 'reconcile DDQ', 'does this match the ADV'. Hands confirmed gaps to diligence findings and ODD. | firmFundDiligence |
| `gradient-manager-monitor` | Create a branded manager-roster digest. Triggers: 'weekly monitoring', 'what changed across managers', 'roster digest', 'any alerts'. Hands flagged subjects to ODD or DDQ reconciliation and can schedule read-only runs. | firmFundDiligence |

### Portfolio

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-portfolio-review` | Create a branded brief or comprehensive portfolio monitoring report. Triggers: 'portfolio review', 'quarterly review', 'board performance report', 'policy ranges'. Hands decisions to gradient-ic-memo and focused attribution to its report skill. | portfolio,research,peerIntelligence,strategyLab |
| `gradient-portfolio-attribution-report` | Create a branded historical and governed ex ante attribution report. Triggers: 'attribution report', 'Brinson analysis', 'sources of active return'. Hands broad monitoring to portfolio review and decisions to IC memo. | portfolio |
| `gradient-private-markets-portfolio-construction` | Build a private-markets program report covering PE/private credit, commitments, pacing, cash flows, and liquidity. Use for private markets portfolio, commitment plan, or pacing. For one fund's PME use gradient-idd-private-markets-pme. | portfolio,research,firmFundDiligence,strategyLab |
| `gradient-fixed-income-portfolio-construction` | Build a fixed-income sleeve report covering bonds, duration, credit, benchmarks, liquidity, and scenarios. Use for bond portfolio, core/core-plus, or credit sleeve. For one manager's fit use gradient-idd-manager-portfolio-fit. | portfolio,research,macroDesk |
| `gradient-global-public-equity-portfolio-construction` | Build a global public-equity sleeve report covering regions, managers, factors, concentration, and benchmarks. Use for global equity, active/passive, or manager lineup. For one manager's fit use gradient-idd-manager-portfolio-fit. | portfolio,research |
| `gradient-marketable-alternatives-portfolio-construction` | Build a marketable-alternatives sleeve report covering hedge funds, strategy mix, factor risk, redemption terms, and liquidity. Use for hedge fund portfolio or redemptions. For one manager's fit use gradient-idd-manager-portfolio-fit. | portfolio,research,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |
| `gradient-real-assets-portfolio-construction` | Build a real-assets sleeve report covering real estate, infrastructure, commodities, inflation linkage, and liquidity. Use for real assets portfolio, inflation hedge, or real estate mix. For one manager's fit use gradient-idd-manager-portfolio-fit. | portfolio,research,macroDesk,peerIntelligence,gradientSignals,firmFundDiligence,strategyLab |

### Compliance

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-gips-standards` | Produce a sourced GIPS requirements briefing. Use for what does GIPS require, compliance statement, verification, required disclosures, or GIPS vs SEC Marketing Rule. For a document review use the matching gradient-gips-* skill. | none |
| `gradient-gips-manager-diligence` | Produce a GIPS manager-diligence report. Use for verify GIPS claim, manager GIPS review, performance integrity, or GIPS DDQ. For a report or presentation line review use gradient-gips-report-review. | firmFundDiligence |
| `gradient-gips-report-review` | Produce a line-by-line GIPS report or advertisement review. Use for review this GIPS report, composite presentation, pooled fund report, or advertising guidelines. For general requirements use gradient-gips-standards. | none |
| `gradient-gips-asset-owner-review` | Produce a GIPS Asset Owner Report review for pensions, endowments, foundations, and sovereign funds. Use for asset owner GIPS, total fund report, or board performance report. For firm reports use gradient-gips-report-review. | none |
| `gradient-gips-policies-gap-check` | Produce a GIPS policies-and-procedures gap report. Use for review our GIPS manual, policy gap check, missing GIPS policies, or asset-owner P&P. For report disclosures use gradient-gips-report-review. | none |

### Decision

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-ic-memo` | Create a deterministic, sourced IC decision memo. Triggers: 'IC memo', 'board memo', 'allocation recommendation', 'rebalance proposal', 'manager hire/fire', 'committee vote'. Accepts portfolio, IDD, ODD, and GIPS handoffs. | portfolio,research,strategyLab,firmFundDiligence |

### Admin

| Skill | Produces / routes | Modules |
|---|---|---|
| `gradient-setup` | Check GradientCIO connection, organization, entitlements, data readiness, and connector contracts; produces a readiness report. Use for setup, connection check, or what is ready. For a command catalog use gradient-menu. | none |
| `gradient-menu` | Browse GradientCIO skills by task. Use for what can I do, show commands, help me choose, or skill menu. For connection diagnostics and data-readiness checks use gradient-setup. | none |

<!-- END GENERATED SKILL CATALOG -->

The skills work together: the asset-class construction skills select an existing portfolio and produce
read-only decision packs for a whole sleeve; the `gradient-idd-*` skills supply return-based manager evidence,
while `gradient-manager-compare`, the ODD report and GIPS reviews supply operational evidence; the IC memo
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
