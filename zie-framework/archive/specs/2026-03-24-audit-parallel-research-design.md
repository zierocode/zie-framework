---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-parallel-research.md
---

# /zie-audit Parallel External Research — Design Spec

**Problem:** Phase 3 of `/zie-audit` runs up to 15 WebSearch queries sequentially. Each query is fully independent — none depends on a prior result — but the sequential loop adds 30–45 seconds of pure latency to every audit run.

**Approach:** Construct all queries upfront from `research_profile` as today, then dispatch all WebSearch calls simultaneously in one parallel batch. Collect results and synthesize into `external_standards_report` identically to current behavior. Failed queries skip with "Research unavailable" as before.

**Components:**
- Modify: `commands/zie-audit.md` — change Phase 3 from sequential `for query in queries` loop to single parallel WebSearch dispatch; collect results dict keyed by query; synthesize as before; WebFetch follow-up calls remain sequential (they depend on search results)

**Acceptance Criteria:**
- [ ] All WebSearch calls in Phase 3 dispatched in a single parallel batch
- [ ] Results collected and synthesized identically to sequential behavior
- [ ] Failed queries noted as "Research unavailable" with no crash
- [ ] WebFetch follow-up calls remain sequential
- [ ] Query construction logic unchanged (still capped at 15 queries)
- [ ] `external_standards_report` content equivalent to sequential version

**Out of Scope:**
- Changing the query construction logic or the 15-query cap
- Parallelizing WebFetch follow-ups
- Parallelizing other audit phases
