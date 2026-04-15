---
name: impl-review
description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "context_bundle=<context_bundle>"
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Review completed task implementation against acceptance criteria.
**When to use fast path:** Changed files are small and ACs are explicitly listed.
**Quick steps:** (1) Read changed files + ACs. (2) Check 8-item Phase 2 checklist. (3) Output verdict.
<!-- DETAIL: load only if fast path insufficient -->

# impl-review — Task Implementation Review

Subagent reviewer for completed task implementations. Called by `zie-implement` after each REFACTOR phase. Returns structured verdict.

## Input Expected

| Field | Required | Description |
| --- | --- | --- |
| context_bundle | yes | ADR + project context from `/implement`. Missing → validation error. |
| Task description + ACs | yes | From plan |
| Files changed list | yes | Changed in this task |

## Phase 1 — Validate Context Bundle (inline)

- Required: `context_bundle` from caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context`
- Missing → `❌ Issues Found: context_bundle required — pass from zie-implement skill (do not read from disk)`

Read each file in "files changed" (note "FILE NOT FOUND" if missing).

Returns: `adrs_content`, `context_content`.

## Phase 2 — Review Checklist

1. **AC coverage** — Implementation satisfies every acceptance criterion?
2. **Tests exist** — Tests for the new behavior?
3. **Tests pass** — `make test-unit` exit 0? (Caller confirms — reviewer checks logic)
4. **No over-engineering** — Minimal for the AC? Flag speculative code.
5. **No regressions** — Changes break existing contracts or interfaces?
6. **Code clarity** — Names clear? Logic self-evident? Flag confusing parts.
7. **Security** — Hardcoded secrets, command injection, SQL injection?
8. **Dead code** — Commented-out code or unreachable branches?

## Phase 3 — Context Checks

1. **File existence** — flag missing files in changed-files list (incomplete implementation).
2. **ADR compliance** — flag contradictions with loaded ADRs. No ADRs → skip.
3. **Pattern match** — flag divergence from patterns in read files. Surface for Zie to accept/reject — reviewer notes, doesn't decide.

Phase 3 issues merge into the same `❌ Issues Found` block as Phase 2.

## Output Format

All pass:
```
✅ APPROVED
```

Issues found:
```
❌ Issues Found

1. [File:line] <specific issue and what to fix>
2. [File:line] <specific issue and what to fix>

Fix these, re-run make test-unit, and re-invoke impl-review.
```

## Max Iterations Reached

2 invocations with persistent issues → output:
```
⚠️ Max review iterations reached (2). Persistent issues:
<list remaining issues>
Next steps:
- Fix issues above and re-run: make test-unit
- Or discuss the issue with Zie before re-submitting
- Or run /fix to debug the root cause
```

## Notes

- Be specific about file and line when flagging issues
- Don't nitpick style unless it causes real confusion
- Return ALL issues in one response — don't stop at the first
- Max 2 iterations: initial scan (all issues) + confirm pass. 0 issues → APPROVED immediately.