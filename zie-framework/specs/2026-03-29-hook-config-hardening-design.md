---
approved: true
approved_at: 2026-03-29
backlog: backlog/hook-config-hardening.md
---
# Hook Config Hardening — Design Spec

**Problem:** Three hook configuration gaps cause unpredictable behavior in CI and TDD sessions: subprocess timeouts in `failure-context.py`, `safety_check_agent.py`, and `stop-guard.py` are hardcoded and cannot be tuned; `load_config()` silently returns `{}` on any parse failure with no schema enforcement, so invalid or incomplete `.config` files degrade hooks silently; and `auto-test.py` uses `subprocess.TimeoutExpired` from `subprocess.run()` which only catches the timeout after the process is killed by the OS — if the subprocess spawns children that outlive the parent, those orphans can hold the session.

**Approach:** Add `validate_config(config: dict) -> dict` to `utils.py` that fills every known key with its documented default and emits a single stderr warning line if any key was defaulted due to missing or wrong type. Update `load_config()` to call `validate_config()` before returning so all callers receive a fully-typed dict with no `KeyError` risk. Update `failure-context.py`, `safety_check_agent.py`, and `stop-guard.py` to read their timeout values from the validated config. Wrap the `auto-test.py` subprocess in a `threading.Timer` wall-clock guard keyed to `auto_test_max_wait_s` (default 15s) that kills the process group on expiry and exits 0 with a user-visible message, ensuring Claude is never blocked by a hanging test run.

**Components:**
- `hooks/utils.py` — add `validate_config()`, update `load_config()` to call it
- `hooks/auto-test.py` — replace bare `subprocess.run(timeout=...)` with `threading.Timer` wall-clock guard
- `hooks/failure-context.py` — replace hardcoded `timeout=5` with config `subprocess_timeout_s`
- `hooks/safety_check_agent.py` — replace hardcoded `timeout=30` in `invoke_subagent()` with config `safety_agent_timeout_s`
- `hooks/stop-guard.py` — replace hardcoded `timeout=5` with config `subprocess_timeout_s`
- `CLAUDE.md` — extend Hook Configuration table with four new keys
- `tests/unit/test_utils.py` — new tests for `validate_config()`
- `tests/unit/test_auto_test.py` — new test for wall-clock kill behavior

**Data Flow:**
1. Any hook that needs config calls `load_config(cwd)`.
2. `load_config()` reads `zie-framework/.config`, parses JSON, then calls `validate_config(raw_dict)`.
3. `validate_config()` iterates the canonical `CONFIG_SCHEMA` dict (key → `(default, type)`), fills missing or wrong-type keys with defaults, collects the list of defaulted keys, logs one `[zie-framework] config: defaulted keys: subprocess_timeout_s, auto_test_max_wait_s` line (comma-separated) to stderr if any keys were touched, and returns the completed dict.
4. Caller receives a fully-typed config dict. `config["subprocess_timeout_s"]` is always an `int`; no `.get("key", fallback)` fallback needed at call sites.
5. `failure-context.py` and `stop-guard.py` read `config["subprocess_timeout_s"]` and pass it to `subprocess.run(timeout=...)`.
6. `safety_check_agent.py` reads `config["safety_agent_timeout_s"]` and passes it to `subprocess.run(timeout=...)` inside `invoke_subagent()`.
7. `auto-test.py` reads `config["auto_test_max_wait_s"]`. A `threading.Timer` is armed before `subprocess.Popen()` fires. On expiry the timer calls `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` (with fallback `proc.kill()` if `os.getpgid` raises), prints the timeout message, and sets a flag. After `proc.wait()` returns, the flag is checked and the hook exits 0.

**Edge Cases:**
- `.config` file is absent — `load_config()` returns `{}`, `validate_config({})` fills all defaults; no warning emitted (absent file is the normal zero-config state).
- `.config` has a key with the wrong type (e.g. `"subprocess_timeout_s": "fast"`) — `validate_config()` replaces it with the default and includes the key in the defaulted-keys warning.
- `os.getpgid()` raises `ProcessLookupError` because the process already exited before the timer fires — `auto-test.py` catches `OSError` and calls `proc.kill()` instead; if that also raises, the exception is silently swallowed and the hook still exits 0.
- `threading.Timer` fires after `proc.wait()` has already returned normally — the timer is cancelled inside the finally block; the kill path is never reached.
- `validate_config()` is called with `None` (defensive) — treated the same as `{}`, all defaults applied.
- User sets `auto_test_max_wait_s: 0` — treated as "no wall-clock guard", timer is not armed, behavior falls back to `auto_test_timeout_ms`-based `subprocess.run(timeout=...)`.
- Config file is valid JSON but not a dict (e.g. a JSON array) — `load_config()` `except` catches the `AttributeError` from `validate_config({})` being called on a list; returns fully-defaulted dict, logs parse error to stderr.

**Out of Scope:**
- Config file hot-reload between hook invocations within the same session.
- Validation of `safety_check_mode` enum values (already handled at call site in `safety_check_agent.py`).
- Process group management on Windows (only POSIX `os.killpg` is required; Windows is not a supported platform).
- Exposing `validate_config()` as a public command or slash-command output.
- Migrating existing `.config` files in user projects — defaults make migration transparent.
- Schema version fields or backward-compat migration logic.
