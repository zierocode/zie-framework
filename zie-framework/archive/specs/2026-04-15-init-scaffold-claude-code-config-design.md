---
date: 2026-04-15
status: approved
slug: init-scaffold-claude-code-config
---

# Init Scaffold Claude Code Config Files

## Problem

`/init` creates `zie-framework/` structure, Makefile, VERSION, and CLAUDE.md, but skips `.claude/` configuration entirely. Users must manually create `settings.json` for permissions and hook wiring, `.claude/rules/sdlc.md` for path-scoped workflow rules, and a `.ignore` file for context filtering. This friction hurts onboarding.

## Solution

Add a new step to `/init` (after step 11, before playwright/zie_memory steps) that scaffolds three files:

1. **`.claude/settings.json`** — project-scoped permissions: auto-approve `make test-fast`, `make lint`, `make test-ci`, `python3 hooks/*`, and `pytest`. Skip if file exists.
2. **`.claude/rules/sdlc.md`** — path-scoped rules for SDLC workflow (when to use which command, pipeline order). Skip if exists.
3. **`.ignore`** — context-filter patterns: `__pycache__/`, `node_modules/`, `dist/`, `.env`, `zie-framework/evidence/`, `zie-framework/archive/`, `.zie/`. Skip if exists; if present, append missing entries.

## Rough Scope

**In:** Scaffold `.claude/settings.json`, `.claude/rules/sdlc.md`, `.ignore` during `/init`. Templates live in `templates/`.

**Out:** Global `~/.claude/` config. Changes to existing templates (CLAUDE.md, Makefile). MCP server config (handled by `.claude-plugin/.mcp.json` already).

## Files Changed

- `commands/init.md` — add step 12 for config scaffolding
- `templates/claude-settings.json.template` — new: permission defaults
- `templates/claude-rules-sdlc.md.template` — new: SDLC workflow rules
- `templates/dot-ignore.template` — new: context-filter patterns