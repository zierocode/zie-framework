# Reviewer Context Dedup — Design Spec

**Problem:** Phase 1 context-loading prose (~270 words) is copy-pasted verbatim in spec-reviewer, plan-reviewer, and impl-reviewer; any protocol change must be applied three times. The `reviewer-context` skill exists but is never invoked, making it dead code.

**Approach:** Compress Phase 1 in all three reviewer skills to a concise 2-line summary (fast-path + disk fallback key steps), removing ~400 words of duplicated prose. Delete `skills/reviewer-context/SKILL.md` with a tombstone note referencing ADR-054. Net result: ~600 word reduction, single-source protocol documentation in ADR-054.

**Components:**
- `skills/spec-reviewer/SKILL.md` — compress Phase 1 block
- `skills/plan-reviewer/SKILL.md` — compress Phase 1 block
- `skills/impl-reviewer/SKILL.md` — compress Phase 1 block
- `skills/reviewer-context/SKILL.md` — delete (dead code)

**Data Flow:**
1. Each reviewer's Phase 1 block is replaced with a 2-line summary using this exact form:
   - Fast-path: `if context_bundle provided → adrs_content = context_bundle.adrs · context_content = context_bundle.context · skip disk reads.`
   - Disk fallback: `Cache miss → read ADR-000-summary.md first, then decisions/*.md → write_adr_cache(); read project/context.md → context_content.`
2. `skills/reviewer-context/SKILL.md` is deleted; a tombstone comment or note is left referencing ADR-054 as the canonical context-loading protocol doc
3. Existing tests `test_reviewer_context_chain.py` and `test_lean_load_context.py` are run to confirm no regressions — they test ordering logic, not word counts

**Edge Cases:**
- impl-reviewer Phase 1 also reads caller's "files changed" list — that line must be preserved in the compressed form
- Deleting reviewer-context must not break any test import or skill reference (grep for `reviewer-context` before delete; if any non-test reference found → add a tombstone redirect comment in that file pointing to ADR-054 before deleting)
- All three reviewers must still produce identical context-loading behavior after compression — the prose changes, the semantics do not

**Out of Scope:**
- Changing the actual context-loading protocol or cache behavior
- Modifying `load-context` skill or any non-reviewer skills
- Adding new tests (existing tests already cover the protocol)
- Updating ADR-054 content (it already documents the inlining rationale)
