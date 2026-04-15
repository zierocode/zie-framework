---
tags: [feature]
---

# Auto-Inject Skill Context by Phase

## Problem

Skills currently require manual `Skill()` invocation. For commonly-used patterns (like reviewers during implement), the framework should auto-inject skill context when the relevant phase is active.

## Rough Scope

**In:**
- Add auto-injection in `session-resume.py` and `intent-sdlc.py`
- When TDD phase matches (e.g., implement phase), inject relevant skill content as `additionalContext`
- Define phase-to-skill mapping (implement → reviewer, spec → spec-design, plan → write-plan)
- Make mapping configurable in `.config`

**Out:**
- Removing manual `Skill()` invocation (keep as fallback)
- Auto-injecting skills that aren't phase-relevant

## Priority

MEDIUM