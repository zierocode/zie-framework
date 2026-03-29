---
name: plan-reviewer
description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: ""
model: haiku
effort: low
---

# plan-reviewer — Implementation Plan Review

Subagent reviewer for implementation plans. Called by `write-plan` after
drafting the plan. Returns a structured verdict.

## Input Expected

Caller must provide:

- Path to plan file (`zie-framework/plans/YYYY-MM-DD-<slug>.md`)
- Path to spec file (for context on what must be implemented)

## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it directly:
- `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
- `context_content` ← `context_bundle.context` (skip step 3 below)

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

Before reviewing, load the following context (skip gracefully if missing —
never block review):

1. **File map files** — parse the plan's file map section → read each listed
   file if it exists; note "FILE NOT FOUND" if missing. Files marked "Create"
   are expected to not exist — note but do not flag.
2. **ADRs** — load via session cache (cache-first, summary-aware):
   a. Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
      - Cache hit → use returned string as `adrs_content`. Skip individual file reads.
      - Cache miss → load from disk:
        - If `ADR-000-summary.md` exists → read it first (compressed history).
        - Read remaining individual `zie-framework/decisions/ADR-*.md` files
          (excluding `ADR-000-summary.md`); concatenate all into `adrs_content`.
        - Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   b. If `decisions/` directory is empty or missing → `adrs_content = "No ADRs found"`.
   `session_id` is available from the Claude Code session context.
3. **Design context** — read `zie-framework/project/context.md` if it
   exists. If missing → note "No context doc", skip.
4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
   only. If missing → skip ROADMAP conflict check.

## Phase 2 — Review Checklist

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
10. **Dependency hints** — For each pair of tasks, check whether they modify
   any common files or share a sequential data dependency. If a pair has
   neither, and neither task has a `depends_on` annotation, output a
   suggestion (not a blocking issue):
   "Tasks N and M appear independent — consider adding `<!-- depends_on: -->` to enable parallel execution"

   **File conflict detection:** If two tasks write to the same output file
   but lack `depends_on` annotation, flag as a blocking issue:
   "Tasks N and M both write to X.py — add `<!-- depends_on: TN -->` to prevent file conflict"

   Suggestions do not prevent an APPROVED verdict, but file conflict warnings do.

## Phase 3 — Context Checks

1. **File existence** — list any file-map files that don't exist and are not
   marked "Create".
2. **ADR conflict** — flag any planned approach that contradicts a loaded ADR.
   If no ADRs → skip.
3. **ROADMAP conflict** — flag if this plan overlaps a Ready or Now item
   (same feature or duplicate scope). If ROADMAP missing → skip.
4. **Pattern match** — flag if the planned approach diverges from patterns
   observed in the read files. Surface the divergence for Zie to accept or
   reject — reviewer notes, does not decide.

Surface Phase 3 issues in the same `❌ Issues Found` block as Phase 2 issues.

## Output Format

If all checks pass:

```text
✅ APPROVED
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
- Return ALL issues found in this single response — do not stop at the first issue.
- Max 2 total iterations: initial scan (all issues at once) + confirm pass. If 0 issues → APPROVED immediately, no confirm pass needed.
