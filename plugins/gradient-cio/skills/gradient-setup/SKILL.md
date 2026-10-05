---
name: gradient-setup
description: "Start here for Gradient CIO: checks the GradientCIO connection, organization, licensed modules and data readiness, runs a contract self-test, and delivers a branded readiness PDF showing which Gradient skills are ready to use."
---

# Gradient setup and readiness check

Use when the user is new to the Gradient skills, says "set up Gradient", "get started", "is Gradient connected",
"what can I do with Gradient", "check my access", "health check", "self-test", or when another Gradient skill
fails because the connector is missing, unauthorized or returning errors. Also use after a plugin update.

The deliverable is a short branded PDF, **"Gradient Readiness Report"**, plus a three-line chat summary and two or
three prompts the user can try next. Keep the language plain: the reader may not be technical.

Read `references/portfolio-strategy-scope.md` before checking Portfolio Analytics or Strategy Lab. Test and
report them as separate modules; never use the canonical illustrative portfolio ID as Strategy Lab input.

## 1. Connection

1. Check that GradientCIO tools are available (search for `GradientCIO`). If none appear, the connector is not
   connected. The plugin bundles it (`https://mcp.gradientcio.com/mcp`), so tell the user to open their connector
   settings, find **GradientCIO** and sign in. Still produce the PDF with signal `not_ready` and the steps to fix.
2. Call `list_organizations`. An auth error means the sign-in expired or lacks scopes: ask the user to reconnect.
   If more than one organization is returned and the user has not named one, ask which to check.
   Record `licensed_modules` and `role`.

## 2. Access and data readiness

1. Call `get_gradient_capabilities` with the `organization_id` and `detail: "summary"`:
   - `capabilities` (module flags), `backend_readiness`, `version`;
   - per tool: `entitled`, `available`, `scoped`, `healthy`, `data_ready`, `availability_reason`,
     `missing_oauth_scopes`;
   - `coverage[]`: domain, status (`available`, `conditional`, `unavailable`), `as_of`.
   Request `detail: "full"` only when diagnosing per-backend readiness.
2. Map tools to skills with `references/skill-requirements.md`. A skill is **ready** when every required tool is
   entitled, available and healthy; **partial** when only optional tools are missing or a required tool has a
   known issue with a workaround; **not available** when a required tool is not entitled (name the module the
   client would need to license). When `entitled` is false but `available` is true with
   `access_mode: "illustrative"`, report **Evaluation — Illustrative, Gradient Maintained**, not Ready or Not licensed.
3. Call `get_diligence_roster_funds`: roster size, capacity used and available, and reviews due within 30 days.

## 3. Contract self-test

Run the probes in `references/contract-checks.md`. The **standard** set is 8 quick reads (default). The
**full read** set is 38 reads (the 8 standard plus 30 full probes); run it when the user asks for a health
check or self-test, or after a plugin update. The separate **writes** set is 4 dry-run previews, including
one batch-preview contract, and must never commit. The **DDQ save-preview** set is 3 calls: it intentionally persists one fictional test
document and one immutable reconciliation test run so that document identity and the chained save can be
tested with `dry_run: true`; disclose that persistence before running it. The complete matrix is 45 calls.

For each probe, record pass, fail (with error code and HTTP status) or not run (not entitled), and the
response `as_of`. Resolve `depends_on` arguments with `check_contract.py --resolve-args`; do not manually
copy or invent chained IDs.

For a saved response file you can check required paths with
`python <this skill's directory>/scripts/check_contract.py <this skill's directory>/references/contracts.json <probe_id> <response.json>`.

Compare any failure with the known-issues table in `references/contract-checks.md`. If it matches a known issue,
mark it "known issue — workaround in skill" rather than a new fault. A new failure is a finding: quote the error
code, HTTP status and request ID so the user can send it to Gradient support.

## 4. Branding

Check the plugin's `branding.json` (plugin root). `brand: "gradient"` is the explicit default and renders
the GradientCIO mark. Say how to apply client branding: an administrator sets the client name and logo before distributing the plugin
(`python tools/set_branding.py` at the plugin root); for one report, give a name and logo in the conversation
and the skill renders with `--brand`.

## 5. Build the report

Write `report.json` (JSON block mode, see `references/report-style.md`) and render:

```
python <this skill's directory>/scripts/gradient_report.py report.json "Gradient Readiness Report - <Org>.pdf"
```

Meta: `eyebrow` "Setup & Readiness", `header_label` "Readiness Check", `title` the organization name,
`subtitle` "GradientCIO connection, access and data readiness", `signal_title` "Readiness",
`meter_title` "Checks passed", `completeness` = probes passed / probes run.
`cover_facts`: Organization, Role, Licensed modules (count), Roster funds, MCP version, Checked (date).

Signal: `ready` (connected, all core skills ready, no new failures) · `partial` (connected, but some skills
partial or not licensed, or known issues present) · `not_ready` (not connected, auth failed, or any core skill
not available).

Sections (keep to 4–5 pages):

1. **Summary** (`id: executive`) — bottom line in 3 sentences; tiles: Skills ready, Partial, Not licensed,
   Checks passed.
2. **Skills you can use** — table: Skill, What it produces, Status (chip: Ready / Partial / Not licensed),
   Note (what is missing or the workaround). For the IC memo, show Portfolio Analytics core readiness and
   `Strategy Lab supplement: <Ready / Not licensed (optional) / Unavailable (optional)>` separately.
3. **Access and data** — `coverage` block for the data domains (status and as-of); kv block for organization,
   role, licensed modules, roster capacity, and the available chart packs for the first portfolio from
   `chart_availability`.
4. **Contract checks** — table: Probe, Tool, Result (chip), As of, Note. Then a `findings` block listing new
   failures only (severity high when a core skill is blocked, medium otherwise).
5. **Try next** — `questions` block with 3 prompts tailored to what is ready, e.g. "Run an ODD report on
   <first roster fund>", "Give me this week's manager monitoring digest", "Build the macro briefing deck for
   Thursday's committee".
6. **Appendix A — Sources** — tool, as-of, validation status, payload digest for each call.

Then follow "Check and deliver" in `references/report-style.md`.

## 6. Offer next steps

- If the user has roster funds and the monitoring skill is ready, offer to set up the weekly monitoring digest
  as a scheduled task (see gradient-manager-monitor).
- If something is not licensed, say which module unlocks it; do not upsell beyond that.
