---
name: impl-reviewer
description: Review a completed task implementation against its acceptance criteria. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: general-purpose
allowed-tools: Read, Grep, Glob, Bash
argument-hint: ""
model: sonnet
effort: medium
---

# impl-reviewer — Task Implementation Review

Subagent reviewer for completed task implementations. Called by `zie-implement`
after each REFACTOR phase. Returns a structured verdict.

## Input Expected

Caller must provide:

- Task description and Acceptance Criteria (from plan)
- List of files changed in this task

## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it for shared context:
- `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
- `context_content` ← `context_bundle.context` (skip step 3 below)

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

Before reviewing, load the following context (skip gracefully if missing —
never block review):

1. **Modified files** — read each file listed in the caller's "files changed"
   input; note "FILE NOT FOUND" if any are missing.
2. **ADRs** — read all `zie-framework/decisions/*.md`.
   If directory empty or missing → note "No ADRs found", skip ADR checks.
3. **Design context** — read `zie-framework/project/context.md` if it
   exists. If missing → note "No context doc", skip.

## Phase 2 — Review Checklist

Read the changed files and check each item:

1. **AC coverage** — Does the implementation satisfy every acceptance criterion?
2. **Tests exist** — Are there tests for the new behavior?
3. **Tests pass** — Did `make test-unit` exit 0? (Caller confirms — reviewer
   checks logic)
4. **No over-engineering** — Is the implementation minimal for the AC? Flag
   speculative code.
5. **No regressions** — Do any changes break existing contracts or interfaces?
6. **Code clarity** — Are names clear? Is logic self-evident? Flag anything
   that will confuse future readers.
7. **Security** — Any hardcoded secrets, command injection, or SQL injection?
8. **Dead code** — Any commented-out code or unreachable branches?

## Phase 3 — Context Checks

1. **File existence** — flag any file in the changed-files list that is
   missing (may indicate incomplete implementation).
2. **ADR compliance** — flag any implementation detail that contradicts a
   loaded ADR. If no ADRs → skip.
3. **Pattern match** — flag if implementation diverges from patterns in the
   read files. Surface for Zie to accept or reject — reviewer notes, does
   not decide.

Surface Phase 3 issues in the same `❌ Issues Found` block as Phase 2 issues.

## Output Format

If all checks pass:

```text
✅ APPROVED
```

If issues found:

```text
❌ Issues Found

1. [File:line] <specific issue and what to fix>
2. [File:line] <specific issue and what to fix>

Fix these, re-run make test-unit, and re-invoke impl-reviewer.
```

## Notes

- Be specific about file and line when flagging issues
- Don't nitpick style unless it causes real confusion
- Return ALL issues found in this single response — do not stop at the first issue.
- Max 2 total iterations: initial scan (all issues at once) + confirm pass. If 0 issues → APPROVED immediately, no confirm pass needed.
