# Context Lean Sprint

## Problem

zie-framework wastes 50,000–150,000 tokens per workflow session due to redundant file reads. Every reviewer agent (spec-reviewer, plan-reviewer) reads all 28+ ADR files fresh on each invocation instead of using the session cache already built in utils.py. The /zie-audit command has 4 parallel agents that each independently re-read the same project manifests, README, and git log — paying 4x the context cost for identical content.

## Motivation

Token waste directly translates to cost and latency. A 3-slug /zie-plan invocation reads 28 ADRs five times (write-plan ×2 + plan-reviewer ×3) instead of once. The ADR cache infrastructure (get_cached_adrs, write_adr_cache) already exists in utils.py but spec-reviewer and plan-reviewer don't use it — they read raw files. Fixing this is purely a discipline issue: enforce the cache pattern everywhere it's not yet applied, reducing per-workflow token cost by an estimated 40–60%.

## Rough Scope

**In Scope:**
- Update spec-reviewer SKILL.md to require context_bundle.adr_cache_path (stop reading ADRs directly)
- Update plan-reviewer SKILL.md same fix
- Update /zie-audit Phase 1 to pre-load shared_context (manifests + git log) once and pass to all 4 agents in Phase 2 — agents must not re-read these files independently
- Verify /zie-plan and /zie-implement correctly pre-load and pass context_bundle to all spawned reviewers

**Out of Scope:**
- Changing caching TTL or cache invalidation logic
- Adding new cache types beyond ADR and git status
