---
name: using-zie-framework
description: Command map, workflow map, and anti-patterns for zie-framework. Read as static data by session-resume.py — NOT a callable skill.
user-invocable: false
argument-hint: ""
---

# using-zie-framework — Framework Reference

## Command Map

- `/backlog` — capture a new idea
- `/spec` — design a backlog item
- `/plan` — plan implementation from approved spec
- `/implement` — TDD implementation (agent mode required)
- `/sprint` — full pipeline in one go (backlog→spec→plan→implement→release→retro)
- `/fix` — debug and fix failing tests or broken features
- `/chore` — maintenance task, no spec needed
- `/hotfix` — emergency fix, ship fast
- `/status` — show current SDLC state
- `/audit` — project audit
- `/retro` — post-release retrospective
- `/release` — merge dev→main, version bump
- `/resync` — refresh project knowledge
- `/init` — bootstrap zie-framework in a new project
- `/guide` — full framework walkthrough + recommended next actions
- `/health` — framework health dashboard
- `/rescue` — pipeline state diagnosis + recovery path
- `/next` — backlog prioritization + recommended next item

## Workflow Map

backlog → spec (reviewer) → plan (reviewer) → implement → release → retro

Use `/sprint` to run the full pipeline in one session.

## Anti-Patterns

- Never write `approved: true` directly — use `python3 hooks/approve.py`
- Never skip spec/plan steps on "ทำเลย" or similar shortcuts
- Never run `/implement` without an approved plan
- Never approve without running the corresponding reviewer skill first
