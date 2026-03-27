---
approved: true
approved_at: 2026-03-27
backlog: backlog/audit-weak-nocrash-assertions.md
---

# Sprint 4 — Final Backlog Clearance Design Spec

**Problem:** Three backlog items remain open: weak hook test assertions, git subprocess caching on hot paths, and undocumented safety_check_mode config key.
**Approach:** Address each item directly with minimal scope. Path traversal fix (security-path-traversal backlog) is already shipped — confirmed `is_relative_to()` in place and edge-case tests exist. Sprint 4 covers only the genuinely remaining work.
**Components:** `hooks/utils.py`, `hooks/failure-context.py`, `hooks/sdlc-compact.py`, `tests/unit/test_hooks_failure_context.py`, `tests/unit/test_hooks_notification_log.py`, `tests/unit/test_hooks_sdlc_compact.py`, `tests/unit/test_hooks_auto_test.py`, `CLAUDE.md`

---

## Problem & Motivation

### 1. Weak "no-crash" test assertions (audit-weak-nocrash-assertions)
Several hook tests assert only `returncode == 0`. A hook that exits early with `sys.exit(0)` — doing nothing — passes those tests. The tests must verify the observable outcome: file written, stdout content, or explicit empty-stdout assertion for "no action" paths.

Audit identified `test_hooks_wip_checkpoint.py:121,130` as primary examples. Many tests in `test_hooks_failure_context.py`, `test_hooks_notification_log.py`, `test_hooks_sdlc_compact.py`, and `test_hooks_auto_test.py` share the same pattern.

### 2. Hot-path git subprocess caching (architecture-cleanup M3)
`failure-context.py` (PostToolUse) and `sdlc-compact.py` (PostToolUse/Edit) each call `git log` and `git branch`/`git diff` subprocess on every event. At high edit frequency this is wasteful. `utils.py` already has a ROADMAP session cache pattern — the same approach applies to git status (5s TTL).

### 3. safety_check_mode undocumented (architecture-cleanup M8)
`safety_check_agent.py` reads `config.get("safety_check_mode", "regex")` and only activates the AI subagent when mode is `"agent"` or `"both"`. This config key is undocumented in CLAUDE.md — operators enabling it are flying blind.

---

## Architecture & Components

### Git status cache (M3)
Add to `utils.py`:
- `get_cached_git_status(session_id, key, ttl=5)` — returns `str | None`
- `write_git_status_cache(session_id, key, content)` — writes to `/tmp/zie-<session>/git-<key>.cache`

Update `failure-context.py` and `sdlc-compact.py` to call the cache wrapper before spawning subprocess. Cache key = command string hash (e.g. `"log"`, `"branch"`, `"diff"`). TTL = 5s (fast-moving data, but hooks fire multiple times per second).

### Weak assertions (test depth)
Strategy per test category:
- **"no action" path**: add `assert r.stdout.strip() == ""` (hook exited cleanly without output)
- **"hook wrote file" path**: add `assert output_file.exists()` and content check
- **"hook produced JSON stdout" path**: add `json.loads(r.stdout)` round-trip check
- **"error/fallback" path**: add `assert "zie-framework" in r.stderr` (hook logged the error)

Target ~15 tests across 4 test files. Do NOT change tests that already have side-effect assertions.

### safety_check_mode documentation (M8)
Add a `## Hook Configuration` section to `CLAUDE.md` documenting:
- `safety_check_mode`: `"regex"` (default, fast), `"agent"` (Claude subagent on every Bash), `"both"` (regex + agent)

---

## Data Flow

**Git cache flow:**
1. Hook called → reads `CLAUDE_SESSION_ID` env var
2. Calls `get_cached_git_status(session_id, "log", ttl=5)`
3. Cache hit → return cached string (no subprocess)
4. Cache miss → run subprocess → call `write_git_status_cache` → return string

**Test assertion flow:**
- Tests that call `run_hook(...)` → verify `r.returncode == 0` AND at least one side-effect

---

## Edge Cases

- `CLAUDE_SESSION_ID` absent → fall back to `"default"` as session_id key (cache still works, may collide across sessions but still correct)
- Cache file missing or unreadable → return None → fall through to subprocess (graceful degradation)
- Git not installed → subprocess raises → existing `except` handles it → cache never written (correct)
- TTL=5s may return stale git log in rapid-fire edits → acceptable; log context is informational only

---

## Out of Scope

- path traversal fix: already shipped (`is_relative_to()` + 3 edge-case tests)
- Architecture-cleanup items L1/L2/L5/L6/L7/L8: already shipped in Sprint 2/3
- Strengthening ALL 88 potentially-weak tests: only strengthen tests where hooks have observable positive-path behavior to verify. Pure error-handling tests (invalid JSON, missing env vars) are correct with just `returncode == 0`
- Adding git caching to `stop-guard.py` and `task-completed-gate.py`: those hooks use git for different operations (diff count, commit check) — profile before caching
