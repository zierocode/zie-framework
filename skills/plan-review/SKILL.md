---
name: zie-framework:plan-review
description: Review an implementation plan for completeness, TDD structure, and task granularity. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob
argument-hint: ""
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Review an implementation plan for TDD structure, spec coverage, and task granularity.
**When to use fast path:** Plan has ≤10 tasks and each task has explicit test steps.
**Quick steps:** (1) Read plan + spec. (2) Check 12-item Phase 2 checklist. (3) Check Phase 3 context. (4) Output ✅ APPROVED or ❌ Issues Found.
<!-- DETAIL: load only if fast path insufficient -->

# plan-review — Implementation Plan Review

Subagent reviewer for implementation plans. Called by `write-plan` after drafting. Returns structured verdict.

## Input Expected

| Field | Required | Description |
| --- | --- | --- |
| Plan file path | yes | `zie-framework/plans/YYYY-MM-DD-<slug>.md` |
| Spec file path | yes | For spec coverage context |
| context_bundle | yes | ADR + project context from caller |

## Phase 1 — Validate Context Bundle (inline)

- Required: `context_bundle` from caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context`
- Missing → output `❌ Issues Found: context_bundle required — pass from write-plan skill (do not read from disk)`
- Fallback (legacy): read ADRs from `zie-framework/decisions/*.md` and `zie-framework/project/context.md` from disk (slower, not recommended).

Returns: `adrs_content`, `context_content`.

## Phase 2 — Review Checklist

1. **Header** — `approved: false`, `backlog:`, Goal, Architecture, Tech Stack?
2. **File map** — All created/modified files listed with responsibilities?
3. **TDD structure** — Each task follows RED → GREEN → REFACTOR with explicit `make test-unit` steps?
4. **Task granularity** — Each task completable in one focused session? Flag over-ambitious tasks.
5. **Exact paths** — All file paths exact (no "add to the relevant file")?
6. **Complete code** — Each step includes actual code, not "implement X"?
7. **Dependencies** — `depends_on` comments where needed?
8. **Spec coverage** — Every requirement in the spec covered?
9. **YAGNI** — Anything included that the spec doesn't require?
10. **Rollback plan** — For each task that modifies existing files: is there a safe rollback path? Can changes be reverted without data loss? Flag tasks with no rollback strategy.
11. **Hidden dependencies** — Does any task depend on a system, service, or file not mentioned in the spec? Flag implicit dependencies (e.g., "assumes DB migration already ran", "depends on env var X").
12. **Dependency hints** — Build file→tasks map: for each task, collect file paths it creates/modifies; record `file → [task IDs]`. Then:
    - **File conflict (blocking):** File in 2+ task IDs without `depends_on` → flag: "Tasks N and M both write to X.py — add `<!-- depends_on: TN -->`"
    - **Independent tasks (advisory):** No shared files and no `depends_on` → suggest: "Tasks N and M appear independent — consider `<!-- depends_on: -->` for parallel execution"
    - Skip when ≤1 tasks. Conflicts block APPROVED; suggestions do not.

## Phase 3 — Context Checks

1. **File existence** — extract directory paths from plan's File Map. Scope Glob/Grep to those directories only. If no paths found → use current broad scope. List file-map files that don't exist and aren't marked "Create".
2. **ADR conflict** — flag planned approach contradicting a loaded ADR. No ADRs → skip.
3. **ROADMAP conflict** — flag overlap with Ready/Now item (same feature/duplicate scope). ROADMAP missing → skip.
4. **Pattern match** — flag divergence from patterns in read files. Surface for Zie to accept/reject — reviewer notes, doesn't decide.

Phase 3 issues merge into the same `❌ Issues Found` block as Phase 2.

## Output Format

All pass:
```
✅ APPROVED
```

Issues found:
```
❌ Issues Found

1. [Task N / Section] <specific issue and what to fix>
2. [Task N / Section] <specific issue and what to fix>

Fix these and re-submit for review.
```

## Plan Size Warning

>15 tasks → output advisory (does not block APPROVED):
```
⚠️ Large plan detected (N tasks). Consider splitting into:
1. <slug>-core — essential tasks only
2. <slug>-extras — enhancements that can ship separately
Large plans increase WIP time and context overhead.
```

## Max Iterations Reached

2 invocations with persistent issues → output:
```
⚠️ Max review iterations reached (2). Persistent issues:
<list remaining issues>
Next steps:
- Fix issues above, then re-run: /plan <slug>
- Or split plan into smaller tasks and re-submit
- Or ask Zie to review the plan section manually
```

## Notes

- Reject vague steps ("implement the feature", "add tests")
- Reject missing `make test-unit` verification in TDD steps
- Return ALL issues found — don't stop at the first issue
- Max 2 iterations: initial scan (all issues) + confirm pass. 0 issues → APPROVED immediately.