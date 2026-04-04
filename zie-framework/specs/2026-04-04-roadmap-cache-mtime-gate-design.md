# Spec: Replace ROADMAP Cache TTL with mtime-Gate

**status:** draft
**slug:** roadmap-cache-mtime-gate
**date:** 2026-04-04

---

## Problem

`read_roadmap_cached()` in `hooks/utils_roadmap.py` (line 98) uses a 30-second wall-clock TTL to validate its cache. This causes redundant disk reads whenever the TTL expires — even when ROADMAP.md has not changed. In slow editing sessions (edit, pause, edit), stale reads accumulate unnecessarily.

The sibling function `get_cached_adrs()` already uses an mtime-gate (compare stored mtime against current file mtime) — a strictly better pattern. The ROADMAP cache is the only inconsistent outlier.

---

## Solution

Replace the TTL-based validity check in `read_roadmap_cached()` / `get_cached_roadmap()` with an mtime-gate, matching the pattern of `get_cached_adrs()`:

1. When writing the cache (`write_roadmap_cache`), persist the ROADMAP.md mtime alongside the content in a JSON payload — `{"mtime": <float>, "content": "<str>"}`.
2. When reading the cache (`get_cached_roadmap`), compare the stored mtime against `os.path.getmtime(roadmap_path)`. Return cached content only when mtimes match (within 0.001s tolerance, same as ADR cache). Otherwise return `None`.
3. `read_roadmap_cached()` signature gains a `roadmap_path` parameter so the cache reader can compare against the live file mtime. The `ttl` parameter is removed entirely.
4. Remove all `time.time()` / TTL logic from these functions.
5. Remove unused `import time` if no other callers remain.

The cache file format changes from a plain text file (`roadmap.cache`) to a JSON file (`roadmap-cache.json`) — consistent with `adr-cache.json`.

---

## Acceptance Criteria

- [ ] `get_cached_roadmap` no longer accepts or uses a `ttl` parameter.
- [ ] `get_cached_roadmap` accepts `roadmap_path` and uses `os.path.getmtime` to validate the cache.
- [ ] Cache hit: returns content when stored mtime matches current ROADMAP.md mtime (within 0.001s).
- [ ] Cache miss (mtime changed): returns `None`; caller re-reads from disk and re-writes cache with fresh mtime.
- [ ] Cache miss (no cache file): returns `None`.
- [ ] `write_roadmap_cache` writes `{"mtime": <float>, "content": "<str>"}` JSON to `roadmap-cache.json`.
- [ ] `read_roadmap_cached` signature: `(roadmap_path, session_id, tmp_dir=None)` — `ttl` removed.
- [ ] `import time` removed from `utils_roadmap.py` if no other usage remains.
- [ ] Existing callers of `read_roadmap_cached` in hook files updated to drop the `ttl` argument.
- [ ] Unit tests cover: cache hit, cache miss on mtime change, cache miss on missing file, write round-trip.
- [ ] `make test-fast` passes with no regressions.

---

## Out of Scope

- Changing `get_cached_git_status` / `write_git_status_cache` (TTL is appropriate for git output).
- Changing `get_cached_adrs` / `write_adr_cache` (already correct).
- Adding mtime-gating to any hook other than the ROADMAP cache path.
- Migration of existing cache files on disk (stale plain-text files will simply miss and regenerate).
