---
slug: audit-docs-standards
approved: true
approved_at: 2026-03-23
backlog: backlog/audit-docs-standards.md
---

# Spec: Docs + Standards Sprint

## Problem

`plugin.json` reports version 1.3.0 while the actual release is 1.4.0, causing
marketplace consumers to see the wrong version. README.md references
`project/decisions.md`, a path that was renamed to `project/context.md` in
v1.3.0, breaking navigation for new users. ADR entries use inconsistent
prefixes (`D-` in context.md vs `ADR-` in the decisions/ directory), and the
CHANGELOG v1.1.0 section is written in Thai while all other versions are in
English — both gaps degrade discoverability and contributor trust.

## Approach

Apply one-shot corrections to all stale artefacts (plugin.json version,
README.md path, architecture.md timestamp, context.md ADR prefixes, CHANGELOG
v1.1.0 translation). Add the missing `SECURITY.md` to satisfy OpenSSF
scorecard requirements. Prevent future version drift structurally: introduce a
`make sync-version` target that writes the VERSION file value into plugin.json,
a pre-commit hook that blocks commits when the two diverge, and a commitizen
config (`.cz.toml`) that enforces conventional commit messages so CHANGELOG
entries stay machine-readable going forward.

## Acceptance Criteria

- [ ] AC-1: `plugin.json` `.version` field equals `1.4.0`; confirmed by
  `jq -r .version .claude-plugin/plugin.json`.
- [ ] AC-2: README.md line 87 reads `project/context.md`; no occurrence of
  `project/decisions.md` remains in README.md.
- [ ] AC-3: `zie-framework/project/architecture.md` "Last updated" timestamp
  reads `2026-03-23` and includes a brief summary of v1.3.0 and v1.4.0
  changes.
- [ ] AC-4: All ADR references in `zie-framework/project/context.md` use the
  `ADR-NNN` prefix; no `D-` prefixed entries remain.
- [ ] AC-5: `SECURITY.md` exists at the repo root and contains: a
  vulnerability reporting method, maintainer contact, and a disclosure policy
  (responsible disclosure / 90-day embargo).
- [ ] AC-6: CHANGELOG v1.1.0 section is written entirely in English; no Thai
  text remains in that section.
- [ ] AC-7: `make sync-version` target exists in Makefile; running it updates
  `.claude-plugin/plugin.json` version to match `VERSION` without manual
  editing.
- [ ] AC-8: A pre-commit hook (via `.githooks/pre-commit` or
  `.pre-commit-config.yaml`) exits non-zero when `plugin.json` version differs
  from `VERSION`; error output includes `Run: make sync-version`.
- [ ] AC-9: `.cz.toml` exists at repo root with commitizen configured for
  conventional commits (`feat`, `fix`, `chore`, `BREAKING CHANGE`); `cz
  commit` is usable as a drop-in for `git commit`.

## Out of Scope

- Migrating historical ADR files in `decisions/` to a new naming scheme beyond
  prefix canonicalization in context.md.
- Adding CI enforcement of commitizen (reserved for a separate CI hardening
  spec).
- Translating any CHANGELOG section other than v1.1.0.
- Updating `architecture.md` content beyond the timestamp and version summary
  lines.

## Files Changed

- `.claude-plugin/plugin.json` — version field bump to 1.4.0
- `README.md` — line 87: `decisions.md` → `context.md`
- `zie-framework/project/architecture.md` — timestamp + version summary
- `zie-framework/project/context.md` — ADR prefix canonicalization
- `CHANGELOG.md` — v1.1.0 section translated to English
- `SECURITY.md` — new file (repo root)
- `Makefile` — add `sync-version` target
- `.githooks/pre-commit` — add version-drift check (or `.pre-commit-config.yaml`)
- `.cz.toml` — new file (repo root)
