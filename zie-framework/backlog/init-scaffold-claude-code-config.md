---
tags: [feature]
---

# Init Scaffold Claude Code Config Files

## Problem

The `/init` command bootstraps a project with `zie-framework/`, `CLAUDE.md`, `.config`, `Makefile`, and `.markdownlint.json`, but does not create Claude Code-specific configuration files that improve context efficiency and developer experience: `.ignore` (context filter), `.claude/rules/sdlc.md` (SDLC workflow rules), `.claude/settings.json` (auto-approve safe commands), and `CLAUDE.local.md` (local dev preferences template).

## Motivation

Projects using zie-framework benefit from optimized Claude Code configuration — less context waste from irrelevant files, auto-approved safe commands to reduce permission prompts, and path-scoped SDLC rules that only load when working with zie-framework internals. Currently every user must manually set these up after `/init`.

## Rough Scope

**In scope:**
- `.ignore` at project root (exclude `__pycache__/`, `node_modules/`, `dist/`, `.env`, `zie-framework/evidence/`, `zie-framework/archive/`, etc.)
- `.claude/rules/sdlc.md` (path-scoped to `zie-framework/**`, contains pipeline rules, WIP=1, reviewer enforcement)
- `.claude/settings.json` (auto-approve `make test-fast`, `make test-ci`, `make lint`, `python3 *`)
- `CLAUDE.local.md` template (local dev notes, non-Claude model compatibility, scratch pad)

**Out of scope:**
- Global `~/.claude/` configuration (user's responsibility)
- Changes to existing template files (`CLAUDE.md.template`, `Makefile`, etc.)