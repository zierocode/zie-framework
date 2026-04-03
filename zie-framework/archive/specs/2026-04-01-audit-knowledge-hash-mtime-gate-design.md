---
slug: audit-knowledge-hash-mtime-gate
status: approved
date: 2026-04-01
---
# Spec: mtime Gate for knowledge-hash.py to Skip Redundant rglob on SessionStart

## Problem

`knowledge-hash.py` `compute_hash()` calls `root.rglob('*')` twice on every
`SessionStart` — once to collect the filtered directory list and once implicitly
through `.iterdir()` on every directory in that list for the directory-entry
count metric. This results in O(dirs × dir_entries) filesystem work before
every Claude session, with no caching or short-circuit logic.

`session-resume.py` (line 86) spawns `knowledge-hash.py --check` as a
subprocess with a 10-second timeout. On large projects this can be the
dominant startup latency.

## Proposed Solution

Add an mtime gate inside `knowledge-hash.py` that caches both the computed
hash and the max mtime of watched paths to `/tmp/zie-{slug}-hash-mtime` (where
`{slug}` is the sanitised last component of `--root`). On the next invocation,
before calling `compute_hash()`, the script reads the cache file, recomputes
max mtime across watched paths (a pure `stat()` sweep — no directory
enumeration), and skips the full rglob if mtime is unchanged.

### Cache file format (JSON, `/tmp/zie-{slug}-hash-mtime`)

```json
{
  "mtime": 1743484800.123,
  "hash": "abc123..."
}
```

### Logic (both `--check` and default `--now` paths)

1. Compute `max_mtime` — walk `root.rglob('*')` **stat only** (no content
   read, no `.iterdir()`), filtering by the same `EXCLUDE` / `EXCLUDE_PATHS`
   rules as `compute_hash()`.
2. Read cache file if it exists.
3. If `cache["mtime"] == max_mtime` → return `cache["hash"]` (skip
   `compute_hash()`).
4. Otherwise call `compute_hash()`, write new cache
   `{"mtime": max_mtime, "hash": new_hash}`, return new hash.
5. Cache write errors must be silently swallowed (outer-guard pattern) — the
   hook must never block Claude.

The gate applies to **both** execution paths (`--check` and the default print
path) because `session-resume.py` uses `--check` and other callers use the
default path.

### Two-tier hook safety

- **Outer guard** (event parse / early-exit): if reading or writing the cache
  raises any exception, fall through to `compute_hash()` as if no cache
  existed. `sys.exit(0)` on unrecoverable outer errors.
- **Inner operations** (cache I/O): wrap in `except Exception` → log to
  `stderr` with `[zie-framework] knowledge-hash: {e}`, then continue (do not
  block). Never raise.

### Cache key / invalidation

The cache is keyed by the project slug derived from `root.resolve().name`,
lowercased and with non-alphanumeric characters replaced by `_`. If the user
runs with a different `--root` the slug differs and a fresh cache is built
automatically.

The mtime value stored is a `float` (Python `os.stat().st_mtime`). Equality
comparison (`==`) is sufficient; no tolerance window is needed because mtime
resolution on macOS/Linux is sub-second and any file write changes mtime.

## Acceptance Criteria

- [ ] AC1 — When no files have changed since the last run, `knowledge-hash.py`
  exits without calling `compute_hash()` (verified by patching `compute_hash`
  in a unit test and asserting it is not called when cache is fresh).
- [ ] AC2 — When any watched file's mtime increases, the cache is invalidated,
  `compute_hash()` is called, and the cache file is updated with the new hash
  and mtime.
- [ ] AC3 — When the cache file is absent or corrupt (invalid JSON), the script
  falls through to `compute_hash()` and writes a fresh cache file.
- [ ] AC4 — Cache read/write errors (e.g., `/tmp` not writable) are swallowed;
  the script prints the correct hash and exits 0.
- [ ] AC5 — The `--check` path (used by `session-resume.py`) also benefits from
  the gate — drift detection skips `compute_hash()` when mtime is unchanged.
- [ ] AC6 — Files and directories matching `EXCLUDE` / `EXCLUDE_PATHS` are
  excluded from the mtime sweep, consistent with `compute_hash()` filtering.
- [ ] AC7 — The cache filename follows the pattern
  `/tmp/zie-{slug}-hash-mtime` where `{slug}` is derived from
  `root.resolve().name` (lowercase, non-alphanumeric → `_`).
- [ ] AC8 — Cache writes use `safe_write_tmp()` helper (per ADR-010) to protect
  against symlink attacks; symlink detection does not block the hook.
- [ ] AC9 — All existing `knowledge-hash.py` unit tests continue to pass
  without modification.

## Out of Scope

- Changing the hash algorithm or the inputs to `compute_hash()`.
- Persisting the cache outside `/tmp` (cross-reboot persistence is not needed;
  a cold start after reboot is acceptable).
- Gating on file content changes (mtime gating is sufficient for the
  performance goal; content-hash gating is a separate concern).
- Modifying `session-resume.py` — the gate is entirely internal to
  `knowledge-hash.py`.
- Windows compatibility (framework targets macOS/Linux only).
