# Maintainer guide (read this first)

This repo is a **public** Claude plugin marketplace. Clients install from it directly, so everything on `main` ships.

## Layout
- `.claude-plugin/marketplace.json` — marketplace `gradientcio`; lists each plugin with its `version`.
- `plugins/gradient-cio/` — the plugin. `.claude-plugin/plugin.json` (name, version), `.mcp.json` (GradientCIO connector URL, no credentials), `skills/<name>/SKILL.md`, `shared/` (canonical report renderers and standards), `tools/`, `tests/`, and pinned `requirements-test.txt`.
- `CHANGELOG.md`, `README.md` (client install instructions).

## Rules
1. **Never commit secrets, client data or client names.** No API keys, tokens, real portfolio data or client-specific branding. `branding.json` stays blank on `main`. Test fixtures use fictional names marked (TEST).
2. Edit shared files in `plugins/gradient-cio/shared/`, then run `python plugins/gradient-cio/tools/sync_shared.py` to copy them into every skill. Never hand-edit the per-skill copies.
3. Skill folder name = `name:` in its SKILL.md frontmatter.

## Making a change (every time)
1. Work on a branch: `git checkout -b <short-change-name>`.
2. Make the change. If shared files changed, run `sync_shared.py`.
3. Bump the version in **both** `plugins/gradient-cio/.claude-plugin/plugin.json` and the matching entry in `.claude-plugin/marketplace.json` (semver: patch = fixes/wording, minor = new skill or feature, major = breaking change). Clients only receive an update when the version changes.
4. Add an entry at the top of `CHANGELOG.md`.
5. Install `plugins/gradient-cio/requirements-test.txt` plus Poppler, qpdf, LibreOffice and Inter, then run and fix until both pass:
   - `python plugins/gradient-cio/tools/release_quality_gate.py` (runs `tests/run_tests.py`; skips Claude validation only when the CLI is unavailable)
   - `claude plugin validate .` (required before release even when CI reports that the CLI was unavailable)
   - for deterministic visual review artifacts: `python plugins/gradient-cio/tools/generate_golden_example.py --out <temporary-directory>`
   - if the change adds or changes which GradientCIO tools a skill calls: update `skills/gradient-setup/references/contracts.json` and `skill-requirements.md`, then run the gradient-setup full self-test against the live connector and record any reproducible failure as a plain finding with its error code, HTTP status and request ID.
   - a secrets scan: `git diff main --stat` plus `grep -rInE "(api[_-]?key|secret|token|password|bearer)" plugins/ | grep -v -i "no credentials"` and review any hits.
6. Commit with a clear message, push the branch, open a PR, wait for the `validate` check to pass, then merge to `main` (squash). If the owner asks to publish directly, push to `main` only after step 5 passes.
7. Tag the release: `git tag v<version> && git push origin v<version>`, and create a GitHub release with the changelog entry (`gh release create v<version> --notes-from-tag` or paste the notes).
8. Report back: the new version, what changed, and the client update line: `/plugin marketplace update gradientcio`.
