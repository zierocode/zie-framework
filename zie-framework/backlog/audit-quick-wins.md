---
tags: [chore]
---

# Audit Quick Wins Batch — Low-Effort High-Impact Fixes

## Problem

Multiple small findings from the 2026-04-14 audit that each take XS-S effort but have meaningful impact.

## Motivation

Quick wins reduce audit debt fast and improve overall project health with minimal risk.

## Rough Scope

Batch of independent XS-S fixes:

1. **session-learn /tmp hardening** — Use atomic_write instead of open(_log_path, 'a') for pattern-log
2. **session-stop atomic write** — Replace write_text()+chmod with existing atomic_write()
3. **session-stop symlink validation** — Check symlink target is within memory directory
4. **stop-handler git log caching** — Cache `git log --all -p` result with TTL
5. **session-resume mtime** — Replace subprocess git log with `.git/refs/heads/<branch>` mtime for staleness check
6. **Unify stage keywords** — Consolidate STAGE_KEYWORDS, _STAGE_KEYWORDS, and SDLC_STAGES into utils_roadmap
7. **Consolidate atomic write** — Merge safe_write_tmp/safe_write_persistent into parameterized function
8. **Single pending_learn owner** — Decide session-learn vs session-stop ownership
9. **config-drift read_event** — Replace manual stdin parse with utils_event.read_event()
10. **Fix ADR-012 reference** — Update CLAUDE.md to reference ADR-022/ADR-063 instead of non-existent ADR-012
11. **README zie-release-mode** — Add missing agent to Agent Modes table
12. **context-loader test coverage** — Add tests for zie_context_loader.py (build_context_map, _get_skill_mtime, _build_cache_key, get_cached_context)