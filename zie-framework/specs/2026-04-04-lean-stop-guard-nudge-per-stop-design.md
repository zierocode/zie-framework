# Lean Stop-Guard Nudge Per Stop — Design Spec

**Problem:** `stop-guard.py` runs `_run_nudges()` on every Stop event, executing an O(history) `git log --all -p` pipe per Now lane item, an mtime filesystem scan, and a ROADMAP date parse. Since Stop fires on every Claude response, these are redundant session-level signals computed O(stop_events) times.

**Approach:** Gate `_run_nudges()` behind a session-scoped TTL using the existing `get_cached_git_status`/`write_git_status_cache` infrastructure in `utils_roadmap.py` (TTL=1800s key `"nudge-check"`). On TTL hit, skip all nudge subprocesses. On TTL miss, write the sentinel first then run nudges. Simultaneously replace `git log --all -p -- zie-framework/ROADMAP.md | grep` with `git log --all --format="%H %ai" -- zie-framework/ROADMAP.md` (eliminates patch body, 10–100× less output). Add `shlex.quote(slug)` to the grep argument as a security hardening bundled with this change.

**Components:**
- `hooks/stop-guard.py` — add TTL gate around `_run_nudges()`, replace git log command, add `shlex.quote`
- `hooks/utils_roadmap.py` — no changes needed (reuses `get_cached_git_status`/`write_git_status_cache`)
- `tests/test_stop_guard.py` — add tests: TTL gate skips nudges on cache hit, runs on miss, lighter git log format assertion
- `tests/test_utils_roadmap.py` — no new tests needed (existing cache infra already tested)

**Data Flow:**
1. Stop event fires → `stop-guard.py` main() runs
2. Read `session_id` from `CLAUDE_SESSION_ID` env var (already available)
3. Call `get_cached_git_status(session_id, "nudge-check", ttl=1800)` → returns sentinel string on hit, `None` on miss
4. Cache hit → skip `_run_nudges()` entirely; proceed to WIP block check
5. Cache miss → call `write_git_status_cache(session_id, "nudge-check", "1")` to mark session as checked
6. Then call `_run_nudges(cwd, config, subprocess_timeout)` as before
7. Inside `_run_nudges`, Nudge 1 uses `git log --all --format="%H %ai" -- zie-framework/ROADMAP.md` instead of `git log --all -p`; grep on output uses `shlex.quote(slug)` for security

**Edge Cases:**
- `CLAUDE_SESSION_ID` absent or empty → `session_id=""` → cache key `"nudge-check"` still works (safe_id will be empty string → key becomes `"git-nudge-check.cache"` in `zie-{empty}` dir). Nudges run on every stop in that degenerate case (no caching), which is the current behaviour — no regression.
- TTL expires mid-session (after 30 min) → nudges re-run once, sentinel refreshed. Acceptable; session-level signal updated.
- `project_tmp_path()` not used — we reuse `tempfile.gettempdir()` via existing cache functions, no new path dependency.
- `shlex.quote(slug)` where slug contains spaces or special chars → quoted correctly for shell=True invocation; no shell injection risk.
- git log command output format change → date extraction regex updated from `Date:` prefix to `%ai` ISO format (`\d{4}-\d{2}-\d{2}`). Existing regex already handles bare `(\d{4}-\d{2}-\d{2})` so no regex change needed.

**Out of Scope:**
- Changing the nudge logic itself (thresholds, message text)
- Configuring TTL via `.config` (hardcode 1800s for now; can be parameterised later)
- Nudge result caching (we only cache whether we ran nudges, not results)
- Any changes to `get_cached_git_status` / `write_git_status_cache` signatures
