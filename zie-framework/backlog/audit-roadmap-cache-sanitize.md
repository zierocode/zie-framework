# roadmap cache: unsanitized session_id + /tmp hardcode + cleanup leak

**Severity**: High | **Source**: audit-2026-04-01

## Problem

`get_cached_roadmap` and `write_roadmap_cache` in `utils.py` have three
related issues that every other cache function in the same file already avoids:

1. **No session_id sanitization** — path is built as
   `Path(f"/tmp/zie-{session_id}/roadmap.cache")` without
   `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)`. A crafted session_id
   containing `../` could write outside the intended namespace.

2. **Hardcoded `/tmp/`** — all other caching helpers use
   `tempfile.gettempdir()`. On non-macOS/Linux systems (e.g., Windows) this
   breaks. It also bypasses `tmp_dir` injection used in tests.

3. **Cleanup never runs** — `session-cleanup.py` globs `zie-{project}-*` in
   `tempfile.gettempdir()`. Roadmap cache dirs are named `zie-{session_id}/`
   — a different scheme — so they are never cleaned up and accumulate across
   sessions.

## Motivation

All three issues are in the same two functions and share a single fix: align
`get_cached_roadmap`/`write_roadmap_cache` with the `write_git_status_cache`
pattern (sanitize session_id, use `tempfile.gettempdir()`, use `safe_write_tmp`).
Then update `session-cleanup.py` to also glob `zie-{session_id_prefix}-*` or
use a unified naming convention.
