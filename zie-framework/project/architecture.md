# Architecture — zie-framework

**Last updated:** 2026-03-22

## Overview

zie-framework เป็น Claude Code plugin ที่ใช้ hooks + commands + skills
เพื่อสร้าง structured SDLC workflow ใน Claude Code session ใดก็ได้ โดยไม่ต้องใช้
external tools และ graceful degradation เมื่อ optional dependencies (zie-memory,
superpowers) ไม่พร้อมใช้งาน

## Plugin Structure

```text
.claude-plugin/plugin.json   # plugin metadata + marketplace entry
hooks/hooks.json             # hook event → script mapping
hooks/*.py                   # hook implementations (Python 3.x)
commands/zie-*.md            # slash command definitions (markdown)
skills/*/SKILL.md            # skill definitions (invoked via Skill tool)
templates/                   # file templates for /zie-init
zie-framework/               # self-managed SDLC state (this repo uses itself)
  ├── .config                # project config (JSON)
  ├── ROADMAP.md             # backlog + active work
  ├── PROJECT.md             # hub: project overview + knowledge links
  ├── project/               # spokes: detailed knowledge docs
  ├── specs/                 # feature design docs
  ├── plans/                 # implementation plans
  └── decisions/             # ADR log
```

## Component Relationships

- **Commands** invoke **Skills** via `Skill(zie-framework:<name>)` for reusable
  guidance
- **Hooks** fire on Claude Code events (PostToolUse, PreToolUse, SessionStart) —
  always exit 0
- **zie-memory** (optional) provides persistent brain storage via `recall` /
  `remember`
- **ROADMAP.md** is the single source of truth for work state (Now / Ready /
  Next / Done)

## Data Flow

```text
User runs /zie-command
  → Claude loads command markdown
  → Steps execute (read files, invoke skills, run tools)
  → Hooks fire on each tool use (auto-test, safety-check, intent-detect)
  → State written to ROADMAP.md / plan files / brain
```

## Key Constraints

- **WIP=1**: one active feature in Now at a time (`[ ]` item blocks new builds)
- **Batch release**: `[x]` items accumulate in Now until `/zie-release` moves
  them to Done with version
- **Graceful degradation**: all features work without zie-memory or superpowers
- **Hook safety**: hooks must never crash — every hook has try/except + exit(0)
  on error
