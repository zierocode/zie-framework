# ADR-045: ROADMAP Cache — mtime-Gate over TTL

**Status:** Accepted  
**Date:** 2026-04-04

## Context

`utils_roadmap.py` cached the ROADMAP file content with a 30-second TTL. This
caused stale reads when the file changed within the window and unnecessary cache
misses on re-reads of an unchanged file. The ADR cache already used
content-hash invalidation — the ROADMAP cache lagged behind.

## Decision

Replace the 30-second TTL with a file modification time (mtime) comparison.
The cache JSON now stores `{mtime, content}`. A cache hit requires the stored
mtime to match the current file's mtime; any change invalidates immediately and
forces a disk read.

## Consequences

**Positive:**
- Cache hits are exact: zero false positives on unchanged files, zero false negatives on changed files.
- Consistent with how the ADR cache handles invalidation.
- No configuration needed — works correctly without tuning.

**Negative:**
- `st_mtime` granularity is OS-dependent (typically 1ms on macOS, 1s on some Linux filesystems). Back-to-back edits within the same OS tick could cache-hit incorrectly (extremely rare in practice).

**Neutral:**
- Cache file format changed from `content` string to `{mtime, content}` JSON — callers updated.

## Alternatives

- Keep TTL: simple but causes correctness issues on rapid edits.
- Content-hash: correct but requires reading the file to compute the hash — negates the cache hit.
