# Backlog: Remove redundant sprint Phase 2 (error recovery masquerading as normal phase)

**Problem:**
sprint.md Phase 1 runs the full spec+plan chain per item (spec-design → spec-reviewer
→ write-plan → plan-reviewer). Phase 2 then filters for "items that have spec but no
approved plan" and re-runs /plan. If Phase 1 succeeds, Phase 2's filter yields zero
items — it's a structural no-op by design. The only case Phase 2 fires is if a Phase 1
subagent failed mid-chain. Yet Phase 2 always creates a TaskCreate, prints progress
bars, and re-reads ROADMAP (~500–2000 tokens per sprint).

**Motivation:**
Phase 2 exists solely as error recovery but is framed as a normal sequential phase,
adding overhead to every sprint invocation. Error recovery should be inline in Phase 1's
failure handler, not a separate named phase with its own task tracking.

**Rough scope:**
- Remove sprint.md Phase 2 as a distinct phase
- Add failure handler to Phase 1: if a subagent returns without approved plan, log
  warning and add to retry list
- Add a single retry pass at the end of Phase 1 (not a full separate phase)
- Update phase numbering in sprint.md (Phase 3→2, Phase 4→3, etc.)
- Tests: sprint with partial Phase 1 failure triggers inline retry, not Phase 2
