---
date: 2026-04-15
status: approved
slug: init-scaffold-claude-code-config
---

# Implementation Plan — init-scaffold-claude-code-config

## Steps

1. **Create `templates/claude-settings.json.template`** — JSON with `permissions.allow` array: `Bash(make test-fast*)`, `Bash(make lint*)`, `Bash(make test-ci*)`, `Bash(make test-unit*)`, `Bash(python3 hooks/*)`, `Bash(pytest*)`, `Bash(pytest)`, `Read` for project dirs. Use `{{project_dir}}` placeholder for path-specific entries.

2. **Create `templates/claude-rules-sdlc.md.template`** — Markdown with path-scoped rules: SDLC pipeline order (`/backlog` → `/spec` → `/plan` → `/implement` → `/release` → `/retro`), when to use each command, WIP=1 constraint, TDD requirement during `/implement`.

3. **Create `templates/dot-ignore.template`** — One pattern per line: `__pycache__/`, `node_modules/`, `dist/`, `.env`, `zie-framework/evidence/`, `zie-framework/archive/`, `.zie/`.

4. **Update `commands/init.md`** — Add step 12 (after markdownlint step, before playwright):
   - Create `.claude/` dir if missing.
   - Copy `templates/claude-settings.json.template` → `.claude/settings.json` (skip if exists).
   - Create `.claude/rules/` dir if missing.
   - Copy `templates/claude-rules-sdlc.md.template` → `.claude/rules/sdlc.md` (skip if exists).
   - For `.ignore`: if exists, append any missing patterns; if missing, copy from template.
   - Add these files to the summary output.

5. **Update summary output** in init.md — add lines for `.claude/settings.json`, `.claude/rules/sdlc.md`, `.ignore` with created/skipped status.

## Tests

1. **Unit: template existence** — verify all three template files exist and are valid JSON/Markdown.
2. **Unit: `.ignore` merge logic** — test that appending missing patterns preserves existing entries and adds new ones without duplicates.
3. **Integration: init dry-run** — run `/init` in a temp git repo; verify `.claude/settings.json`, `.claude/rules/sdlc.md`, `.ignore` are created with correct content.
4. **Integration: skip-if-exists** — run `/init` twice; second run must not overwrite existing files.
5. **Integration: `.ignore` append** — create `.ignore` with `__pycache__/` only, run `/init`, verify other patterns appended without duplicate.

## Acceptance Criteria

- [ ] `/init` creates `.claude/settings.json` with SDLC-relevant permissions
- [ ] `/init` creates `.claude/rules/sdlc.md` with pipeline workflow rules
- [ ] `/init` creates/updates `.ignore` with context-filter patterns
- [ ] Existing files are never overwritten (skip-if-exists)
- [ ] `.ignore` merge appends only missing patterns
- [ ] Summary output includes the three new files
- [ ] All unit + integration tests pass