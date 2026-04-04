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

## Phase 1 — Load Context Bundle (inline)

- **Fast-path:** if context_bundle provided by caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context` · skip disk reads.
- **Disk fallback:** read from disk — `get_cached_adrs(session_id, "zie-framework/decisions/")` → `adrs_content`; cache miss → read `decisions/ADR-000-summary.md` → `adrs_content`; if missing → fall back: read all `decisions/*.md`; `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`. Read `project/context.md` → `context_content`.

Returns: `adrs_content`, `context_content`.

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
10. **Dependency hints** — Build a file → tasks map: for each task, collect all
   file paths it creates or modifies; record `file → [task IDs]`. Then:

   - **File conflict (blocking):** Any file appearing in 2+ task IDs without a
     `depends_on` annotation connecting those tasks → flag as a blocking issue:
     "Tasks N and M both write to X.py — add `<!-- depends_on: TN -->` to prevent file conflict"
   - **Independent tasks (advisory):** Any task with no shared files and no
     `depends_on` annotation → output a suggestion (not a blocking issue):
     "Tasks N and M appear independent — consider adding `<!-- depends_on: -->` to enable parallel execution"

   Skip this check when the plan has 0 or 1 tasks. File conflict warnings
   block APPROVED; suggestions do not.

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

## Plan Size Warning

If plan has more than 15 tasks, output warning:

```text
⚠️ Large plan detected (N tasks). Consider splitting into:
1. <slug>-core — essential tasks only
2. <slug>-extras — enhancements that can ship separately
Large plans increase WIP time and context overhead.
```

This is advisory only — does not block APPROVED verdict.

## Max Iterations Reached

If plan-reviewer has been invoked 3 times and issues persist, output:

```text
⚠️ Max review iterations reached (3). Persistent issues:

<list remaining issues>

Next steps:
- Fix issues above, then re-run: /plan <slug>
- Or split plan into smaller tasks and re-submit
- Or ask Zie to review the plan section manually
```

## Notes

- Reject plans with vague steps like "implement the feature" or "add tests"
- Reject plans where TDD steps are missing `make test-unit` verification
- Return ALL issues found in this single response — do not stop at the first issue.
- Max 2 total iterations: initial scan (all issues at once) + confirm pass. If 0 issues → APPROVED immediately, no confirm pass needed.
