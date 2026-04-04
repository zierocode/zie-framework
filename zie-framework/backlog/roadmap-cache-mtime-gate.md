# Replace ROADMAP Cache TTL with mtime-Gate

## Problem

`read_roadmap_cached()` in `utils_roadmap.py:98` uses a 30-second TTL. In slow editing sessions (edit, pause, edit), the TTL expires repeatedly causing redundant ROADMAP disk reads that almost certainly return identical content. The ADR cache in `get_cached_adrs()` already uses mtime-gating (correct pattern) — ROADMAP cache is the inconsistent outlier.

## Motivation

ROADMAP.md only changes when a `/zie-*` command explicitly writes to it. An mtime-gate provides perfect cache validity with zero staleness risk — it's strictly better than a time-based TTL. Using the same pattern as ADR caching also makes the codebase consistent.

## Rough Scope

- Replace the TTL check in `read_roadmap_cached()` with `os.path.getmtime` comparison (same pattern as `get_cached_adrs`)
- Remove the `time.time()` TTL logic
- Update tests for ROADMAP cache behavior
