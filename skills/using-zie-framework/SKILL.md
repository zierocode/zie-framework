---
name: using-zie-framework
description: Command map, workflow map, and anti-patterns for zie-framework. Read as static data by session-resume.py — NOT a callable skill.
user-invocable: false
argument-hint: ""
---

# using-zie-framework — Framework Reference

## Command Map

- `/backlog` — capture new idea
- `/spec` — design a backlog item
- `/plan` — plan from approved spec
- `/implement` — TDD implementation (agent mode)
- `/sprint` — full pipeline: backlog→spec→plan→implement→release→retro
- `/fix` — debug & fix failing tests/features
- `/chore` — maintenance, no spec needed
- `/hotfix` — emergency fix, ship fast
- `/status` — current SDLC state
- `/audit` — project audit
- `/retro` — post-release retrospective
- `/release` — merge dev→main, bump version
- `/resync` — refresh project knowledge
- `/init` — bootstrap in a new project
- `/guide` — walkthrough + next actions
- `/health` — hook health dashboard
- `/rescue` — diagnose stuck pipeline + recovery
- `/next` — prioritize backlog + next item

## Workflow Map

backlog → spec (reviewer) → plan (reviewer) → implement → release → retro

Use `/sprint` to run the full pipeline in one session.

## Anti-Patterns

- Never write `approved: true` directly — use `python3 hooks/approve.py`
- Never skip spec/plan steps on "ทำเลย" or similar shortcuts
- Never run `/implement` without an approved plan
- Never approve without running the corresponding reviewer skill first