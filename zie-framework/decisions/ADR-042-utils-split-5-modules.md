---
status: Accepted
date: 2026-04-04
---

# ADR-042 — Split utils.py into Five Domain Sub-modules

## Status
Accepted

## Context
utils.py grew to 737 lines and was imported by all 22 hooks, creating a single-file bottleneck where every hook loaded all utility code regardless of what it needed.

## Decision
Split utils.py into 5 focused sub-modules: utils_config (config loading/validation), utils_safety (BLOCKS/WARNS patterns, normalize_command), utils_event (read_event, get_cwd, log_hook_timing, call_zie_memory_api), utils_io (file I/O helpers, tmp paths, project paths), utils_roadmap (SDLC stages, parse_roadmap_*, caching). The original utils.py is retained as a compatibility shim.

## Consequences
**Positive:** Each hook imports only what it needs, faster IDE navigation, easier to test in isolation.
**Negative:** 19 test files required bulk import updates.
**Neutral:** utils.py shim preserved for backwards compatibility.

## Alternatives Considered
- Keep monolith but add section comments to improve navigability without changing imports.
- Create a single utils_v2.py and migrate hooks incrementally without splitting by domain.
