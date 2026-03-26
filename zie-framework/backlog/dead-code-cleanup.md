# lean: remove dead code and unused artifacts

## Problem

Several artifacts are dead or never consumed:

1. `skills/zie-audit/SKILL.md` — command implements all phases inline; skill
   is never called and diverges from command scope (finding #18)
2. `hooks/notification-log.py:79-81` — idle-log tmp file written but never
   read by any hook, command, or test (finding #41)
3. `hooks/sdlc-compact.py:144` — `if __name__ == "__main__": pass` scaffolding
   leftover (finding covered in architecture-cleanup)
4. `hooks/intent-detect.py:10`, `hooks/sdlc-context.py:10` — SDLC_STAGES
   imported passively for validation with no runtime use (finding #40)

## Motivation

- **Severity**: Medium (dead skill), Low (others)
- **Source**: /zie-audit 2026-03-26 findings #18, #40, #41

## Scope

- Delete or archive skills/zie-audit/SKILL.md
- Remove idle-log write or add a consumer
- Remove dead __main__ block
- Move SDLC_STAGES validation to test suite
