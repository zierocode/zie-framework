---
tags: [chore]
---

# Adopt CacheManager in Subagent Context

## Problem

`subagent-context.py` reads `project/context.md` directly from disk for ADR counting, despite `read_project_context_unified()` and `read_adrs_unified()` being available in `utils_cache.py`. It also globs and stats plan files without caching.

## Motivation

Subagent-start events are frequent during implementation (reviewers, Explore agents). Each uncached read adds 5-50KB of disk I/O per subagent. Using existing cache helpers eliminates this waste.

## Rough Scope

**In:**
- Replace direct `context_file.read_text()` with `read_project_context_unified()` from CacheManager
- Replace ADR regex counting with `read_adrs_unified()` from CacheManager (returns cached content)
- Cache plan file glob results (short TTL — plans change during implementation)

**Out:**
- Changing CacheManager API
- Changing subagent-context output format