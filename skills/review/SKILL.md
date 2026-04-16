---
name: zie-framework:review
description: Review a spec, plan, or implementation. Pass phase via argument. Returns APPROVED or Issues Found with specific feedback.
user-invocable: false
context: fork
agent: Explore
allowed-tools: Read, Grep, Glob, Bash
argument-hint: "phase=spec|plan|impl  context_bundle=<context_bundle>"
model: haiku
effort: low
---

<!-- FAST PATH -->
**Purpose:** Review a spec, plan, or implementation for completeness and quality.
**When to use fast path:** Document is short (<40 lines for spec, ≤10 tasks for plan, small changes for impl) and all key sections are present.
**Quick steps:** (1) Read document + context. (2) Check phase-specific checklist. (3) Check context checks. (4) Output ✅ APPROVED or ❌ Issues Found.
<!-- DETAIL: load only if fast path insufficient -->

# review — Unified Reviewer

Subagent reviewer for spec, plan, or implementation. Called after writing/editing a document.
Pass `phase=spec`, `phase=plan`, or `phase=impl` to select the checklist.

## Input Expected

| Field | Required | Description |
| --- | --- | --- |
| phase | yes | `spec`, `plan`, or `impl` |
| Document file path | yes | Spec, plan, or changed-files list |
| context_bundle | yes | ADR + project context from caller |

## Phase 1 — Validate Context Bundle (inline)

- Required: `context_bundle` from caller → `adrs_content = context_bundle.adrs` · `context_content = context_bundle.context`
- Missing → `❌ Issues Found: context_bundle required — pass from calling skill (do not read from disk)`

Returns: `adrs_content`, `context_content`.

## Phase 2 — Review Checklist

### spec (10 items)

1. **Problem** — Clearly stated in 1-3 sentences?
2. **Approach** — One approach chosen with rationale?
3. **Components** — All affected files/modules listed?
4. **Data Flow** — Step-by-step flow described?
5. **Edge Cases** — Known edge cases listed?
6. **Out of Scope** — Scope explicitly bounded?
7. **YAGNI** — Anything not needed for the stated problem?
8. **Unquestioned assumptions** — Assumptions not validated? Flag them.
9. **Ambiguity** — Requirements interpretable multiple ways?
10. **Testability** — Acceptance criteria derivable from this spec?

### plan (12 items)

1. **Header** — `approved: false`, `backlog:`, Goal, Architecture, Tech Stack?
2. **File map** — All created/modified files listed with responsibilities?
3. **TDD structure** — Each task follows RED → GREEN → REFACTOR with `make test-unit` steps?
4. **Task granularity** — Each task completable in one session? Flag over-ambitious tasks.
5. **Exact paths** — All file paths exact (no "add to the relevant file")?
6. **Complete code** — Each step includes actual code, not "implement X"?
7. **Dependencies** — `depends_on` comments where needed?
8. **Spec coverage** — Every requirement in the spec covered?
9. **YAGNI** — Anything included that the spec doesn't require?
10. **Rollback plan** — For each task modifying existing files: safe rollback path? Flag tasks with no rollback.
11. **Hidden dependencies** — Tasks depend on systems/services/files not in spec? Flag implicit deps.
12. **Dependency hints** — Build file→tasks map. File in 2+ tasks without `depends_on` → flag blocking conflict. No shared files → suggest parallel execution.

### impl (8 items)

1. **AC coverage** — Implementation satisfies every acceptance criterion?
2. **Tests exist** — Tests for the new behavior?
3. **Tests pass** — `make test-unit` exit 0? (Caller confirms — reviewer checks logic)
4. **No over-engineering** — Minimal for the AC? Flag speculative code.
5. **No regressions** — Changes break existing contracts or interfaces?
6. **Code clarity** — Names clear? Logic self-evident? Flag confusing parts.
7. **Security** — Hardcoded secrets, command injection, SQL injection?
8. **Dead code** — Commented-out code or unreachable branches?

## Phase 3 — Context Checks

Cross-reference document against loaded bundle:

1. **File existence** — Extract paths from Components/File Map/changed files. Scope Glob/Grep to those directories. Flag files that don't exist and aren't marked "Create".
2. **ADR conflict** — Decision contradicting a loaded ADR. No ADRs → skip.
3. **ROADMAP conflict** — Overlap with Ready/Now item (same feature/duplicate scope). ROADMAP missing → skip.
4. **Pattern match** — (impl/plan only) Divergence from patterns in read files. Surface for Zie to accept/reject.

Phase 3 issues merge into the same `❌ Issues Found` block as Phase 2.

## Output Format

All pass:
```
✅ APPROVED
```

Issues found:
```
❌ Issues Found

1. [Section/File:line] <specific issue and what to fix>
2. [Section/File:line] <specific issue and what to fix>

Fix these and re-submit for review.
```

## Plan Size Warning (plan phase only)

>15 tasks → advisory (does not block APPROVED):
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
- Fix issues above, then re-run review
- Or simplify scope and re-submit
- Or ask Zie to review manually
```

## Notes

- Be specific — don't approve vague documents
- Return ALL issues found — don't stop at the first issue
- Max 2 iterations: initial scan (all issues) + confirm pass. 0 issues → APPROVED immediately.