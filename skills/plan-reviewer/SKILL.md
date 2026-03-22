---
name: plan-reviewer
description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
---

# plan-reviewer — Implementation Plan Review

Subagent reviewer for implementation plans. Called by `write-plan` after
drafting the plan. Returns a structured verdict.

## Input Expected

Caller must provide:

- Path to plan file (`zie-framework/plans/YYYY-MM-DD-<slug>.md`)
- Path to spec file (for context on what must be implemented)

## Review Checklist

Read the plan and check each item:

1. **Header** — Does the plan have `approved: false`, `backlog:`, Goal,
   Architecture, Tech Stack?
2. **File map** — Are all files to be created or modified listed with
   responsibilities?
3. **TDD structure** — Does each task follow RED → GREEN → REFACTOR with
   explicit `make test-unit` steps?
4. **Task granularity** — Is each task completable in one focused session? Flag
   tasks that try to do too much at once.
5. **Exact paths** — Are all file paths exact (no "add to the relevant file")?
6. **Complete code** — Does each step include actual code, not "implement X"?
7. **Dependencies** — Are task dependencies expressed with `depends_on` comments
   where needed?
8. **Spec coverage** — Does the plan cover every requirement in the spec?
9. **YAGNI** — Does the plan include anything the spec doesn't require?

## Output Format

If all checks pass:

```text
✅ APPROVED

Plan is complete, TDD-structured, and covers the spec.
```

If issues found:

```text
❌ Issues Found

1. [Task N / Section] <specific issue and what to fix>
2. [Task N / Section] <specific issue and what to fix>

Fix these and re-submit for review.
```

## Notes

- Reject plans with vague steps like "implement the feature" or "add tests"
- Reject plans where TDD steps are missing `make test-unit` verification
- Max 3 review iterations before surfacing to human
