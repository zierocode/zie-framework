# Lean Reviewer Context Chain Depth — Design Spec

**Problem:** All three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) invoke `Skill(reviewer-context)` as Phase 1, creating a skill→skill→disk chain (3–4 hops deep in sprint path) that adds ~200–400 tokens of overhead and one extra skill-invocation roundtrip per reviewer call.

**Approach:** Remove the `Skill(reviewer-context)` invocation from each reviewer's Phase 1 and replace it with an inline two-branch block: fast-path (if `context_bundle` provided by caller → extract `adrs_content`/`context_content` directly) and disk-fallback (if absent → inline ADR cache-first load + `project/context.md` read). This eliminates one skill invocation per reviewer call while preserving the disk-fallback path and the `reviewer-context` SKILL.md for standalone use. All callers that already hold a `context_bundle` (spec-design, write-plan, implement) are updated to pass it to the reviewer.

**Components:**
- `skills/spec-reviewer/SKILL.md` — replace Phase 1 `Skill(reviewer-context)` call with inline two-branch block
- `skills/plan-reviewer/SKILL.md` — replace Phase 1 `Skill(reviewer-context)` call with inline two-branch block
- `skills/impl-reviewer/SKILL.md` — replace Phase 1 `Skill(reviewer-context)` call with inline two-branch block
- `skills/spec-design/SKILL.md` — pass `context_bundle` when invoking spec-reviewer
- `skills/write-plan/SKILL.md` — pass `context_bundle` when invoking plan-reviewer
- `skills/reviewer-context/SKILL.md` — keep as-is; document it is now for standalone direct use only (not invoked by the three reviewers)
- `tests/` — update/add structural tests verifying no reviewer invokes `Skill(reviewer-context)` in its nominal phase 1 block

**Data Flow:**

1. Caller (spec-design or write-plan) loads `context_bundle` (via `load-context` skill or inline).
2. Caller passes `context_bundle` to reviewer skill as an argument.
3. Reviewer Phase 1 detects `context_bundle` present → fast-path: extract `adrs_content = context_bundle.adrs`, `context_content = context_bundle.context`. No skill invocation, no disk reads.
4. If `context_bundle` absent (direct reviewer invocation without caller context): Phase 1 disk-fallback inline logic — ADR cache-first load, then `project/context.md` read. Same protocol as current `reviewer-context` skill, but inlined.
5. Phase 2 and Phase 3 continue unchanged with `adrs_content` and `context_content` in scope.

**Edge Cases:**
- `context_bundle` present but `context_bundle.adrs` is empty string — treat as valid (no ADRs found), do not fall through to disk read.
- `context_bundle` present but `context_bundle.context` is missing key — treat as `context_content = ""`, continue.
- `impl-reviewer` called from sprint path (4 hops deep) — fast-path applies when `implement` command passes `context_bundle`; if not passed, disk-fallback runs correctly.
- Tests asserting on `write_adr_cache`, `adr_cache_path`, `decisions/`, `project/context.md` string anchors — these must remain present in reviewer Phase 1 comment blocks after the change (inline fallback path retains them).
- `reviewer-context` SKILL.md — file is kept and unchanged; it must NOT be updated to remove its own disk-read logic (it remains the canonical standalone loader).

**Out of Scope:**
- Removing or deprecating `reviewer-context` SKILL.md itself
- Changing Phase 2 or Phase 3 logic in any reviewer
- Changing the ADR cache protocol or `load-context` skill logic
- Updating hooks or Python files
- Any change to `impl-reviewer` that removes the "also read each file listed in caller's files changed" step
