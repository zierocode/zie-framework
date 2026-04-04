# Backlog: Eliminate triple load-context invocation in sprint→implement chain

**Problem:**
/implement, /plan, and /sprint each independently invoke Skill(zie-framework:load-context).
When sprint calls implement via Skill(), the inner implement calls load-context again
even though sprint already loaded it. impl-reviewer and plan-reviewer also invoke
reviewer-context (their own Phase 1) even when context_bundle is already available
from the caller.

**Motivation:**
Each extra load-context call re-reads the ADR bundle + context.md — ~500–1000 tokens
of redundant content per extra call. The session-scoped ADR cache (ADR-031) helps
but the cache check itself still costs a read + comparison. The fix is to pass
`context_bundle` as an explicit argument through the call chain so inner skills
can hit the fast-path and return immediately.

**Rough scope:**
- Add `context_bundle` parameter support to load-context SKILL.md (already has
  fast-path "if context_bundle provided")
- Update /sprint to pass `context_bundle` when invoking Skill(zie-framework:zie-implement)
- Update /implement to pass `context_bundle` when invoking impl-reviewer
- Enforce the fast-path contract in reviewer skills: if `context_bundle` present → skip Phase 1
- Tests: verify context is not re-read when bundle passed through
