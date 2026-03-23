---
approved: true
approved_at: 2026-03-24
backlog: backlog/sessionstart-env-file.md
---

# SessionStart CLAUDE_ENV_FILE Config Injection — Design Spec

**Problem:** `session-resume.py` injects project config values into Claude's context only as prose in `additionalContext`, forcing every hook that needs those values to independently re-read and re-parse `.config` on every invocation.

**Approach:** At the end of `session-resume.py`, check for the `CLAUDE_ENV_FILE` environment variable provided by Claude Code on `SessionStart` events. If present, write four `export VAR=value` lines derived from `.config` into that file so Claude Code promotes them to real session-level environment variables. All other hooks (`auto-test.py`, `wip-checkpoint.py`, `session-learn.py`) can then read these vars directly via `os.environ.get()` as a fast path, falling back to their existing `.config` parse only when the env vars are absent (backward compatibility). The `additionalContext` stdout output is retained but narrowed to the human-readable ROADMAP state summary; config values no longer need to appear there.

**Components:**
- `hooks/session-resume.py` — add env-file write block after config is loaded
- `hooks/auto-test.py` — add `os.environ.get()` fast-path for `ZIE_TEST_RUNNER` and `ZIE_AUTO_TEST_DEBOUNCE_MS` before the `.config` parse
- `hooks/wip-checkpoint.py` — already reads `ZIE_MEMORY_API_KEY` / `ZIE_MEMORY_API_URL` from env; add `ZIE_MEMORY_ENABLED` fast-path guard
- `hooks/session-learn.py` — add `ZIE_MEMORY_ENABLED` fast-path guard (mirrors wip-checkpoint pattern)
- `tests/unit/test_hooks_session_resume.py` — new test class `TestSessionResumeEnvFile`

**Data Flow:**

1. Claude Code fires `SessionStart` and sets `CLAUDE_ENV_FILE` to a writable temp file path in the hook's environment.
2. `session-resume.py` runs; reads `zf/.config` into `config` dict (existing logic, unchanged).
3. Hook resolves the four values from `config` with defaults:
   - `ZIE_PROJECT` ← `cwd.name` (directory name, same as current `project_name` local var)
   - `ZIE_TEST_RUNNER` ← `config.get("test_runner", "")`
   - `ZIE_MEMORY_ENABLED` ← `"1"` if `config.get("zie_memory_enabled", False)` else `"0"`
   - `ZIE_AUTO_TEST_DEBOUNCE_MS` ← `str(config.get("auto_test_debounce_ms", 3000))`
4. Hook checks `os.environ.get("CLAUDE_ENV_FILE", "")`. If empty or blank, skip silently (no `CLAUDE_ENV_FILE` means not a SessionStart context or Claude version pre-dating the feature).
5. If `CLAUDE_ENV_FILE` is set, write the four lines to that path:
   ```
   export ZIE_PROJECT=<value>
   export ZIE_TEST_RUNNER=<value>
   export ZIE_MEMORY_ENABLED=<0|1>
   export ZIE_AUTO_TEST_DEBOUNCE_MS=<value>
   ```
   Write uses `Path(env_file).write_text(...)` inside a `try/except Exception as e` block that logs to stderr and exits 0 on failure (inner-ops error handling convention).
6. Claude Code reads `CLAUDE_ENV_FILE` after the hook exits and sets the exported vars for the session.
7. On subsequent hook invocations (`auto-test.py`, `wip-checkpoint.py`, `session-learn.py`), each hook checks `os.environ.get("ZIE_TEST_RUNNER")` etc. first. If the env var is present and non-empty it is used directly; the `.config` file read is skipped. If absent (e.g., hook invoked outside a properly initialized session), the existing `.config` read path runs as fallback.

**Edge Cases:**

- `CLAUDE_ENV_FILE` env var absent or empty string — skip silently; no write attempted, no warning. This is the normal path for non-SessionStart hooks and older Claude Code versions.
- `CLAUDE_ENV_FILE` path is a symlink — do not follow; check `os.path.islink()` before writing and log a `[zie-framework] WARNING` to stderr, then skip. Reuse the same guard pattern as `safe_write_tmp()` in `utils.py`.
- `.config` missing or unreadable — `config` is already `{}` by the time the env-file write runs; all four vars get their default values (`""`, `""`, `"0"`, `"3000"`). `ZIE_TEST_RUNNER=""` is safe — `auto-test.py` already exits early when `test_runner` is empty.
- `.config` parse warning fires (corrupt JSON) — env-file write still runs using defaults; the stderr warning from the parse step already signals the problem to the user.
- Value contains shell-special characters (e.g., a project name with spaces or quotes) — `ZIE_PROJECT` is derived from `cwd.name` (a filesystem path component; spaces are possible). Wrap the value in single quotes in the exported line: `export ZIE_PROJECT='<value>'`. Apply single-quote wrapping to all four values for consistency.
- `auto_test_debounce_ms` is not an integer in `.config` (e.g., string or float) — cast with `str(int(config.get("auto_test_debounce_ms", 3000)))` so the env var is always a clean integer string; wrap in try/except falling back to `"3000"`.
- `zie-framework/` directory absent — `session-resume.py` already exits 0 at line 16 before config load; env-file write is never reached.
- Multiple simultaneous sessions for the same project — `CLAUDE_ENV_FILE` is session-scoped by Claude Code; each session writes its own file. No cross-session collision risk.

**Out of Scope:**

- Writing `ZIE_MEMORY_API_KEY` or `ZIE_MEMORY_API_URL` to the env file — these are secrets; they are already sourced from the user's shell environment and must never be written to a framework-managed file.
- Centralizing `.config` loading into `utils.py` — that is a separate refactor backlog item.
- Removing the `.config` fallback read from `auto-test.py` — kept for backward compatibility with sessions started without the `CLAUDE_ENV_FILE` feature.
- Validating or enforcing the presence of `ZIE_TEST_RUNNER` during session start — intent-detect and auto-test already handle the empty-runner case gracefully.
- Supporting env-file injection in non-SessionStart hooks (e.g., PreToolUse) — `CLAUDE_ENV_FILE` is only set on SessionStart; no other hook type needs this.
