# Spec: stop-guard: Use Session Cache + Faster git status

status: draft

## Problem

`stop-guard.py` (lines 56–62) runs `git status --short --untracked-files=all` on
every Stop event using a raw `subprocess.run` call with no caching.
`--untracked-files=all` is the slowest git status scan mode (recurses into every
untracked directory).

Two other hooks — `sdlc-compact.py` and `failure-context.py` — already use
`get_cached_git_status` / `write_git_status_cache` from `utils_roadmap.py` to
avoid repeated subprocess spawns within a session. Stop-guard is the outlier.

In a long read-only session (planning, audit, review), the Stop hook fires on
every Claude response. Each fire spawns an uncached git subprocess with the
heaviest scan flags, despite zero chance of new uncommitted changes appearing
between responses.

## Solution

1. Add `session_id = event.get("session_id", "default")` in the inner block,
   immediately after `config = load_config(cwd)`.
2. Import `get_cached_git_status` and `write_git_status_cache` from `utils_roadmap`
   (same import already used by `failure-context.py` and `sdlc-compact.py`).
3. Replace the raw `subprocess.run` call with the cache-then-run pattern:
   - Check cache with key `"status"`.
   - On cache miss: run `git status --short --untracked-files=no`, write result
     to cache, then proceed.
   - On cache hit: use cached stdout string directly.
4. Change the git flag from `--untracked-files=all` to `--untracked-files=no`.
   This is consistent with the other hooks and eliminates the slow untracked
   directory walk. Stop-guard only cares about tracked-file modifications and
   staged changes — untracked files are irrelevant to the "uncommitted impl files"
   guard.

### Cache key and TTL

- Key: `"status"` (distinguishes from `"log"`, `"branch"`, `"diff"` used elsewhere)
- TTL: 5 seconds (default — same as other hooks)

### Session ID source

`event.get("session_id", "default")` — the Stop event JSON always includes
`session_id`; the `"default"` fallback keeps the hook safe when running in tests
without a real session.

## Acceptance Criteria

- AC-1: When the cache is warm (written within TTL), stop-guard does NOT spawn a
  `git` subprocess — it reads from the cache file.
- AC-2: When the cache is cold (miss or expired), stop-guard runs
  `git status --short --untracked-files=no` and writes the result to the cache.
- AC-3: The git command no longer uses `--untracked-files=all`.
- AC-4: Functional behavior is unchanged — block/pass decision identical to
  current behavior for the same set of uncommitted impl files.
- AC-5: Hook still exits 0 on all error paths; no exception escapes.
- AC-6: Existing stop-guard tests continue to pass (no regression).

## Out of Scope

- Changing the block/pass logic or `IMPL_PATTERNS` list.
- Moving `get_cached_git_status` / `write_git_status_cache` to `utils_io.py`
  (separate refactor).
- Changing TTL policy or adding per-hook TTL config keys.
- Integration tests (Stop hook integration already covered by existing suite).
