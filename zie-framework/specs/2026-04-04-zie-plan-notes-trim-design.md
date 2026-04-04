---
slug: zie-plan-notes-trim
status: approved
created: 2026-04-04
---

# Design: zie-plan Notes Section Trim

## Problem

`commands/zie-plan.md` lines 173–181 contain a Notes section that restates
information already defined precisely in the command body: plan file path
format, spec match glob, pending/approved semantics, plan-reviewer behavior,
and rejection flow. ~9 lines of pure redundancy loaded on every `/zie-plan`
invocation.

## Solution

Delete the Notes section (lines 173–181) from `commands/zie-plan.md`.

No information is lost — every bullet is covered inline in the command body.

## Acceptance Criteria

- `commands/zie-plan.md` no longer contains the `## Notes` heading or its
  content (lines 173–181).
- All existing tests pass.
- No test asserts the presence of Notes section content.
