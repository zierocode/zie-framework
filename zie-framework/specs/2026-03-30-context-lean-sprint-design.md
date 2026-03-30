---
approved: true
approved_at: 2026-03-30
backlog: backlog/context-lean-sprint.md
---

# Context Lean Sprint — Design Spec

**Problem:** zie-framework wastes 40–60% of session token budget by redundantly reading ADR caches and project manifests across multiple reviewer agents, even though session-scope caching (get_cached_adrs, write_adr_cache) already exists in utils.py but is not systematized.

**Approach:** Establish a shared context_bundle pattern where reviewers (spec-reviewer, plan-reviewer, impl-reviewer) accept a pre-built context bundle instead of reading files independently. For /zie-audit, pre-load manifests + git log once in Phase 1 and pass the shared bundle to all 4 Phase 2 agents. This enforces the cache pattern and reduces per-workflow token cost by 40–60%.

**Components:**
- skills/spec-reviewer/SKILL.md — accept context_bundle parameter; use adr_cache_path if provided, fall back to direct read
- skills/plan-reviewer/SKILL.md — accept context_bundle parameter; same fallback pattern
- skills/impl-reviewer/SKILL.md (existing, verify not modified)
- commands/zie-audit.md Phase 1 — build shared_context bundle (manifests + git log) once, pass to Phase 2 agents
- commands/zie-plan.md — pre-load context_bundle once before invoking write-plan and plan-reviewer
- commands/zie-implement.md — pre-load context_bundle once before task loop, pass to all impl-reviewer invocations
- hooks/utils.py — existing caching infrastructure (get_cached_adrs, write_adr_cache) remains unchanged

**Data Flow:**

1. **Bundle initialization** (once per command invocation):
   - Read zie-framework/decisions/*.md → concatenate into adrs_content
   - Call write_adr_cache(session_id, adrs_content, "zie-framework/decisions/") → returns True + adr_cache_path or False
   - Read zie-framework/project/context.md → context_content
   - Bundle as: `{ adr_cache_path, adrs: adrs_content, context: context_content }`

2. **Bundle handoff** (to reviewers):
   - Caller passes context_bundle to reviewer agent as a parameter
   - Reviewer receives bundle and uses adr_cache_path (if non-None) in preference to re-reading ADRs
   - If adr_cache_path is None (fallback), reviewer reads directly from adrs string

3. **Reviewer logic** (spec-reviewer, plan-reviewer):
   - Phase 1 check: is context_bundle provided by caller?
     - Yes → use `context_bundle.adrs` and `context_bundle.context` directly; skip file reads
     - No → fall back to disk reads (backward compatible)
   - Phase 2 & 3: review logic unchanged

4. **/zie-audit Phase 1 → Phase 2**:
   - Phase 1: build shared_context = { stack, domain, deps, backlog_slugs, adrs_filenames, git_log, adr_cache_path }
   - Phase 2: spawn 4 agents in parallel, pass shared_context to each
   - Agent instructions: "Do not re-read manifests/git log — they are in shared_context; use them directly"

5. **/zie-plan gate**:
   - Load context_bundle once before any plan/reviewer invocation
   - Pass to write-plan (if invoked) and plan-reviewer
   - plan-reviewer uses it without re-reading

6. **/zie-implement task loop**:
   - Load context_bundle once before task loop
   - Pass to every impl-reviewer invocation
   - impl-reviewer uses it without re-reading

**Edge Cases:**
- `decisions/` directory missing or empty → get_cached_adrs returns None, write_adr_cache returns False; reviewers use empty string as fallback
- `project/context.md` missing → context_content is empty string; reviewers skip context checks gracefully
- Session restart between commands → ADR cache keyed by session_id; new session re-reads and re-caches (expected)
- adr_cache_path becomes stale if ADR files modified mid-session → write_adr_cache checks mtime; cache miss on next reviewer invocation triggers fallback to direct read
- Multiple reviewers in flight with different context_bundles → each reviewer receives its own bundle parameter; no cross-reviewer cache sharing (isolation by design)

**Out of Scope:**
- Changing ADR cache TTL or expiration logic
- Adding cache types beyond ADR + context.md
- Modifying reviewer logic (Phase 2 & 3 review criteria unchanged)
- Changing /zie-spec or /zie-backlog behavior
- Refactoring utils.py caching infrastructure
