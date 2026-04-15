---
tags: [chore]
---

# Revise SKILL.md to be Single Source of Truth

## Problem

`skills/using-zie-framework/SKILL.md` is outdated and redundant:
- Command Map section duplicates what `zie_context_loader.py` already scans dynamically
- Missing critical rules: data source declarations (ROADMAP.md is source of truth), behavioral rules
- Not read by any hook — its content is never automatically injected into sessions
- `session-resume.py` hardcodes workflow + anti-patterns that should come from SKILL.md instead

## Motivation

When Claude is asked "what's in the backlog?", it scans the `zie-framework/backlog/` directory instead of reading ROADMAP.md — because no rule tells it otherwise. SKILL.md should be the single source of truth for framework behavioral rules, read by hooks at session start and after compact.

## Rough Scope

**In:**
- Remove Command Map section (already dynamic via `zie_context_loader.py`)
- Remove Workflow Map section (moved to SKILL.md "Workflow" section, read by hooks)
- Add "Data Sources" section: ROADMAP.md is source of truth, PROJECT.md is knowledge hub, .config is runtime config
- Add "Key Rules" section: idempotent commands, hook safety, never approve without reviewer, read ROADMAP.md not directories
- Keep "Anti-Patterns" section but merge into Key Rules
- Mark as `user-invocable: false` (unchanged)

**Out:**
- Dynamic content (commands, skills list) — already handled by context loader
- Implementation details (how hooks work) — belongs in code, not SKILL.md