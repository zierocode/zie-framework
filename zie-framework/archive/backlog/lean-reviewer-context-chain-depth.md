# Backlog: Reduce reviewer skill chain depth (3–4 hops → 1–2)

**Problem:**
All three reviewer skills (impl-reviewer, spec-reviewer, plan-reviewer) invoke
Skill(reviewer-context) as Phase 1. reviewer-context in turn reads PROJECT.md,
context.md, and the ADR cache. This creates a skill→skill→file-read chain:
command → reviewer skill → reviewer-context skill → disk reads.

When called from sprint (sprint → implement → impl-reviewer → reviewer-context),
the chain is 4 hops deep with 3 context boundaries. Each hop adds latency and
context-passing overhead (~200–400 tokens per reviewer call).

**Motivation:**
ADR-048 created the shared load-context skill to reduce duplication, but reviewer-context
adds another layer on top. The reviewer-context content is short (ADR cache path +
context.md path). Inlining it into each reviewer's Phase 1 with a fast-path guard
eliminates one skill-invocation roundtrip per reviewer call.

**Rough scope:**
- Inline reviewer-context Phase 1 logic into each reviewer's preamble (3 files)
- Add explicit guard: "if context_bundle provided by caller → skip Phase 1 entirely"
- Document in reviewer skills that callers MUST pass context_bundle to hit fast-path
- Remove reviewer-context as a standalone skill invocation from all three reviewers
  (keep the SKILL.md file for direct use if ever needed standalone)
- Tests: verify no reviewer skill invokes Skill(reviewer-context) in nominal path
