---
tags: [chore]
---

# Create Shared Command Conventions

## Problem

Cross-cutting patterns appear nearly identically in 5+ commands, each costing 30-60 tokens per invocation:
- **Context bundle loading** — appears in spec, plan, implement, sprint (4 times, ~30-50 words each)
- **Approval gate pattern** — appears in spec, plan, sprint, spec-design, write-plan (5 times, ~25-70 words each)
- **Brain read/write** — appears in backlog, fix, implement, plan, sprint, retro (6+ times)
- **Git commit pattern** — appears in backlog, spec, plan, implement, chore, hotfix, release, retro (8 times)
- **Pre-flight standard** — referenced in most commands but the referenced file doesn't exist in the expected path

Estimated waste: ~600-800 tokens per command invocation once models learn the convention.

## Motivation

A shared `command-conventions.md` file that all commands reference would:
1. Reduce token usage by 600-800 per command invocation
2. Ensure consistency across commands (same brain read tags, same commit format)
3. Make updates single-point (change convention once, all commands benefit)

## Rough Scope

**In:**
- Create `zie-framework/project/command-conventions.md` with 5 sections:
  - Context Bundle: `Skill(load-context)` call pattern + pass-through convention
  - Approval Gate: `python3 hooks/approve.py <file>` + ROADMAP move pattern
  - Brain Read/Write: recall/remember call patterns with tag conventions
  - Git Commit: `git add <files> && git commit -m "type(slug): description"` pattern
  - Pre-flight: initialization check + config read pattern
- Update all commands to reference `→ See [conventions](project/command-conventions.md#section)` instead of inline repetition
- Verify each command still works correctly (conventions must be loaded)

**Out:**
- Changing command behavior
- Changing command names or workflow