# Spec: zie-init — Generate CLAUDE.md + Seed zie-memory

**Date**: 2026-03-22
**Status**: active

---

## Problem

`/zie-init` sets up the SDLC scaffolding but leaves two critical gaps:

1. No `CLAUDE.md` — Claude Code has no project-level context on first run.
2. No zie-memory seeding — future sessions start cold with no project history.

## Goal

After running `/zie-init`, a project should be immediately usable by Claude
Code:

- `CLAUDE.md` exists at root with project name, tech stack, and build commands.
- zie-memory contains initial project context for brain recall in future
  sessions.

## Scope

### In scope

- Create `CLAUDE.md` from template (skip if already exists — idempotent)
- Store structured initial memories via zie-memory when
  `zie_memory_enabled=true`
- Templates: `templates/CLAUDE.md.template`
- Pytest tests verifying template existence and command structure

### Out of scope

- Auto-updating CLAUDE.md after changes
- Local `~/.claude` memory path manipulation (not zie-memory)
- Playwright or zie-memory API implementation details

## Acceptance Criteria

1. `templates/CLAUDE.md.template` exists with placeholders: `{{project_name}}`,
   `{{project_description}}`, `{{tech_stack}}`, `{{test_runner}}`,
   `{{build_commands}}`
2. `commands/zie-init.md` contains a CLAUDE.md step (step 7) that skips if file
   exists
3. `commands/zie-init.md` zie-memory step stores: project name, type, test
   runner, and tech stack
4. `commands/zie-init.md` does NOT reference local `~/.claude/projects` path
   manipulation
5. Pytest tests pass verifying (1)–(4)

## zie-memory Step Detail

When `zie_memory_enabled=true`, store the following memories:

```text
project bootstrap: "Project <name> initialized with zie-framework.
  Type: <type>. Stack: <stack>. Test runner: <runner>."
```

Tags: `[zie-framework, init, <project_name>]`

## Non-Goals

- No schema changes to `.config`
- No changes to other `/zie-*` commands
