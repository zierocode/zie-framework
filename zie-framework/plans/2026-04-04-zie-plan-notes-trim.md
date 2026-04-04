---
slug: zie-plan-notes-trim
spec: zie-framework/specs/2026-04-04-zie-plan-notes-trim-design.md
status: pending
created: 2026-04-04
---

# Plan: zie-plan Notes Section Trim

## Steps

1. **Delete Notes section** — Remove lines 173–181 from
   `commands/zie-plan.md` (the `## Notes` heading and its 8 bullet lines).

2. **Verify** — Run `make test-fast` to confirm no regressions.

## Notes

- No new tests needed — deletion only, no behavior change.
- Grep confirmed: `tests/unit/test_command_zie_plan*.py` has zero assertions
  on Notes section content.
