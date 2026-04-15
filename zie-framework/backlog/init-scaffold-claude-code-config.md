---
tags: [feature]
---

# Init Scaffold Claude Code Config Files

## Problem

The `/init` command currently only scans the project and generates knowledge files, but doesn't scaffold a `.claude/` directory with `settings.json`, key configuration for hooks, permissions, and MCP servers. New users have to manually configure these after `/init`.

## Rough Scope

**In:**
- Add `settings.json` scaffolding to `/init` — create `.claude/` directory structure
- Populate default permissions (auto-approve `make test-fast`, `make lint`, `python3 *`)
- Add hook config entries for zie-framework hooks
- Add MCP server stubs for zie-memory
- Template `.claude/rules/sdlc.md` with path-scoped SDLC workflow rules
- Template `.ignore` for context filtering (`__pycache__/`, `node_modules/`, `dist/`, `.env`, `zie-framework/evidence/`, `zie-framework/archive/`)

**Out:**
- Global `~/.claude/` configuration (user's responsibility)
- Changes to existing template files (`CLAUDE.md.template`, `Makefile`, etc.)

## Priority

HIGH — critical for onboarding experience