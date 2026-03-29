---
approved: false
approved_at:
backlog: backlog/hook-config-hardening.md
spec: specs/2026-03-29-hook-config-hardening-design.md
---

# Hook Config Hardening — Implementation Plan

**Goal:** Eliminate all hardcoded subprocess timeouts from hooks and add schema-validated config defaults so every hook receives a fully-typed config dict with no `KeyError` risk and no silent degradation.
**Architecture:** `validate_config()` is added to `utils.py` as a pure function that fills a canonical `CONFIG_SCHEMA` dict; `load_config()` calls it before returning, making all callers receive complete typed dicts. Hooks that spawn subprocesses read timeout values from the validated config. `auto-test.py` replaces its bare `subprocess.run(timeout=...)` with a `threading.Timer` wall-clock guard that kills the process group on expiry and always exits 0.
**Tech Stack:** Python 3.x stdlib only (`threading`, `os`, `signal`); pytest for all tests.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `CONFIG_SCHEMA`, `validate_config()`, update `load_config()` to call it |
| Modify | `hooks/auto-test.py` | Replace `subprocess.run(timeout=...)` with `threading.Timer` + `subprocess.Popen` wall-clock guard |
| Modify | `hooks/failure-context.py` | Import `load_config`; replace hardcoded `timeout=5` with `config["subprocess_timeout_s"]` |
| Modify | `hooks/safety_check_agent.py` | Pass `config["safety_agent_timeout_s"]` into `invoke_subagent()` instead of hardcoded `30` |
| Modify | `hooks/stop-guard.py` | Import `load_config`, `get_cwd`; replace hardcoded `timeout=5` with `config["subprocess_timeout_s"]` |
| Modify | `CLAUDE.md` | Extend Hook Configuration table with four new config keys |
| Modify | `tests/unit/test_utils.py` | Add `TestValidateConfig` class |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add `TestAutoTestWallClockGuard` class |

---

## Task 1: Add `validate_config()` and `CONFIG_SCHEMA` to `hooks/utils.py`

**Acceptance Criteria:**
- `validate_config({})` returns a dict with all four schema keys set to their documented defaults.
- `validate_config({"subprocess_timeout_s": "fast"})` replaces the wrong-type value with `5` and emits one `[zie-framework] config: defaulted keys: subprocess_timeout_s` line to stderr.
- `validate_config(None)` is treated as `{}` — all defaults applied, no exception raised.
- `validate_config({"subprocess_timeout_s": 10})` returns `10` for that key (valid value kept) and does not emit a warning for that key.
- Absent `.config` file: `load_config()` calls `validate_config({})`, no warning emitted (absent = normal zero-config state per spec edge-case).
- Present but corrupt `.config`: `load_config()` logs parse error then returns `validate_config({})` result.
- Config file is valid JSON but not a dict (e.g. `[]`): `load_config()` catches the `AttributeError`/`TypeError` from passing a non-dict into `validate_config`, logs parse error, returns fully-defaulted dict.
- `load_config()` return value always has `subprocess_timeout_s`, `safety_agent_timeout_s`, `auto_test_max_wait_s`, `auto_test_timeout_ms` as typed values — no `KeyError` possible at call sites.

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestValidateConfig` to `tests/unit/test_utils.py`:

  ```python
  from utils import validate_config, load_config

  class TestValidateConfig:
      def test_empty_dict_returns_all_defaults(self):
          result = validate_config({})
          assert result["subprocess_timeout_s"] == 5
          assert result["safety_agent_timeout_s"] == 30
          assert result["auto_test_max_wait_s"] == 15
          assert result["auto_test_timeout_ms"] == 30000

      def test_valid_values_preserved(self):
          result = validate_config({"subprocess_timeout_s": 10})
          assert result["subprocess_timeout_s"] == 10
          # other keys still get defaults
          assert result["safety_agent_timeout_s"] == 30

      def test_wrong_type_replaced_with_default(self, capsys):
          result = validate_config({"subprocess_timeout_s": "fast"})
          assert result["subprocess_timeout_s"] == 5
          captured = capsys.readouterr()
          assert "defaulted keys" in captured.err
          assert "subprocess_timeout_s" in captured.err

      def test_warning_lists_all_defaulted_keys(self, capsys):
          result = validate_config({"subprocess_timeout_s": "x", "safety_agent_timeout_s": "y"})
          captured = capsys.readouterr()
          assert "subprocess_timeout_s" in captured.err
          assert "safety_agent_timeout_s" in captured.err

      def test_none_treated_as_empty_dict(self):
          result = validate_config(None)
          assert result["subprocess_timeout_s"] == 5

      def test_no_warning_on_full_valid_config(self, capsys):
          validate_config({
              "subprocess_timeout_s": 5,
              "safety_agent_timeout_s": 30,
              "auto_test_max_wait_s": 15,
              "auto_test_timeout_ms": 30000,
          })
          captured = capsys.readouterr()
          assert "defaulted" not in captured.err

      def test_no_warning_on_empty_dict(self, capsys):
          # absent file is normal zero-config state — no warning
          validate_config({})
          captured = capsys.readouterr()
          assert "defaulted" not in captured.err

      def test_load_config_returns_fully_typed_dict(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('{"subprocess_timeout_s": 10}')
          result = load_config(tmp_path)
          # validate_config fills the rest
          assert result["safety_agent_timeout_s"] == 30
          assert result["subprocess_timeout_s"] == 10

      def test_load_config_missing_file_returns_defaults(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          result = load_config(tmp_path)
          assert result["subprocess_timeout_s"] == 5

      def test_load_config_json_array_returns_defaults(self, tmp_path, capsys):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('[1, 2, 3]')
          result = load_config(tmp_path)
          assert result["subprocess_timeout_s"] == 5
          captured = capsys.readouterr()
          assert "config parse error" in captured.err
  ```

  Run: `make test-unit` — must FAIL (ImportError: cannot import name 'validate_config')

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/utils.py`, add after the existing imports and before `SDLC_STAGES`:

  ```python
  # Canonical config schema: key -> (default_value, expected_type)
  CONFIG_SCHEMA: dict = {
      "subprocess_timeout_s": (5, int),
      "safety_agent_timeout_s": (30, int),
      "auto_test_max_wait_s": (15, int),
      "auto_test_timeout_ms": (30000, int),
  }


  def validate_config(config: dict) -> dict:
      """Fill all known CONFIG_SCHEMA keys with typed defaults.

      - Missing keys are filled with the schema default.
      - Keys present but with wrong type are replaced with the schema default.
      - A single stderr warning line is emitted listing only the keys that were
        defaulted due to wrong type (not for absent keys — absent = zero-config).
      - None input is treated as {}.
      Returns a new dict with all schema keys guaranteed present and correctly typed.
      """
      if config is None:
          config = {}
      result = dict(config)
      wrong_type_keys = []
      for key, (default, expected_type) in CONFIG_SCHEMA.items():
          if key not in result:
              result[key] = default
          elif not isinstance(result[key], expected_type):
              wrong_type_keys.append(key)
              result[key] = default
      if wrong_type_keys:
          print(
              f"[zie-framework] config: defaulted keys: {', '.join(wrong_type_keys)}",
              file=sys.stderr,
          )
      return result
  ```

  Update `load_config()`:

  ```python
  def load_config(cwd: Path) -> dict:
      """Read zie-framework/.config as JSON and return a validated dict.

      Always returns a fully-typed dict with all CONFIG_SCHEMA keys present.
      Logs parse errors to stderr. Absent file returns all defaults silently.
      """
      config_path = cwd / "zie-framework" / ".config"
      try:
          raw = json.loads(config_path.read_text())
          if not isinstance(raw, dict):
              raise TypeError(f"config must be a JSON object, got {type(raw).__name__}")
          return validate_config(raw)
      except FileNotFoundError:
          return validate_config({})
      except Exception as e:
          print(f"[zie-framework] config parse error: {e}", file=sys.stderr)
          return validate_config({})
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm `validate_config` and `CONFIG_SCHEMA` are exported (they are module-level).
  - No duplicate logic between `validate_config` and the old `load_config` fallback — the old fallback is now gone.

  Run: `make test-unit` — still PASS

---

## Task 2: Update `failure-context.py` and `stop-guard.py` to read `subprocess_timeout_s`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `failure-context.py` uses `config["subprocess_timeout_s"]` (an `int`) for all `subprocess.run(timeout=...)` calls; no hardcoded `timeout=5` remains.
- `stop-guard.py` uses `config["subprocess_timeout_s"]` for its `git status` subprocess call; no hardcoded `timeout=5` remains.
- Both hooks import `load_config` and `get_cwd` (stop-guard already imports `get_cwd`; failure-context already imports `get_cwd`).
- Setting `subprocess_timeout_s: 1` in `.config` causes both hooks to pass `timeout=1` to subprocess calls.
- Both hooks still exit 0 on `subprocess.TimeoutExpired`.

**Files:**
- Modify: `hooks/failure-context.py`
- Modify: `hooks/stop-guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hooks_failure_context.py` (new class at end of file):

  ```python
  class TestFailureContextTimeoutFromConfig:
      def test_subprocess_timeout_s_read_from_config(self, tmp_path):
          """failure-context.py must read subprocess_timeout_s from validated config."""
          source = Path(HOOK).read_text()
          assert 'config["subprocess_timeout_s"]' in source, \
              "failure-context.py must use config['subprocess_timeout_s'], not hardcoded timeout"
          assert "timeout=5" not in source, \
              "hardcoded timeout=5 must be removed from failure-context.py"
  ```

  Add to `tests/unit/test_stop_guard.py` (new class at end of file):

  ```python
  class TestStopGuardTimeoutFromConfig:
      def test_subprocess_timeout_s_read_from_config(self):
          """stop-guard.py must read subprocess_timeout_s from validated config."""
          source = Path(HOOK).read_text()
          assert 'config["subprocess_timeout_s"]' in source, \
              "stop-guard.py must use config['subprocess_timeout_s'], not hardcoded timeout"
          assert "timeout=5" not in source, \
              "hardcoded timeout=5 must be removed from stop-guard.py"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/failure-context.py`:

  1. Add `load_config` to the import from `utils`:
     ```python
     from utils import read_event, get_cwd, load_config, parse_roadmap_section_content, read_roadmap_cached, get_cached_git_status, write_git_status_cache
     ```

  2. At the start of the inner operations block (after `cwd = get_cwd()`), add:
     ```python
     config = load_config(cwd)
     subprocess_timeout = config["subprocess_timeout_s"]
     ```

  3. Replace both `timeout=5` literals in the git subprocess calls:
     ```python
     # git log call:
     log_result = subprocess.run(
         ["git", "log", "-1", "--pretty=%h %s"],
         capture_output=True, text=True, cwd=str(cwd), timeout=subprocess_timeout,
     )
     # git rev-parse call:
     branch_result = subprocess.run(
         ["git", "rev-parse", "--abbrev-ref", "HEAD"],
         capture_output=True, text=True, cwd=str(cwd), timeout=subprocess_timeout,
     )
     ```

  In `hooks/stop-guard.py`:

  1. Add `load_config` to the import from `utils`:
     ```python
     from utils import read_event, get_cwd, load_config
     ```

  2. In the inner operations block, after `cwd = get_cwd()`, add:
     ```python
     config = load_config(cwd)
     subprocess_timeout = config["subprocess_timeout_s"]
     ```

  3. Replace the hardcoded `timeout=5`:
     ```python
     result = subprocess.run(
         ["git", "status", "--short", "--untracked-files=all"],
         cwd=str(cwd),
         capture_output=True,
         text=True,
         timeout=subprocess_timeout,
     )
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify no other hardcoded `timeout=5` remain in either file.

  Run: `make test-unit` — still PASS

---

## Task 3: Update `safety_check_agent.py` to read `safety_agent_timeout_s`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `invoke_subagent()` accepts a `timeout: int` parameter and passes it to `subprocess.run(timeout=...)`.
- The hardcoded `timeout=30` literal is removed from `invoke_subagent()`.
- The call site in `evaluate()` passes `config["safety_agent_timeout_s"]` as the timeout.
- Source-level assertion: `"timeout=30"` is absent from the file; `'config["safety_agent_timeout_s"]'` is present.

**Files:**
- Modify: `hooks/safety_check_agent.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hooks_safety_check_agent.py` (new class at end of file):

  ```python
  class TestSafetyAgentTimeoutFromConfig:
      def test_timeout_read_from_config(self):
          """safety_check_agent.py must use config['safety_agent_timeout_s'], not hardcoded 30."""
          source = Path(HOOK).read_text()
          assert "timeout=30" not in source, \
              "hardcoded timeout=30 must be removed from safety_check_agent.py"
          assert 'config["safety_agent_timeout_s"]' in source or \
                 'safety_agent_timeout_s' in source, \
              "safety_agent_timeout_s must be used in safety_check_agent.py"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/safety_check_agent.py`:

  1. Update `invoke_subagent()` signature to accept timeout:
     ```python
     def invoke_subagent(command: str, timeout: int = 30) -> str:
         """Call claude CLI to evaluate the command. Returns agent response text."""
         prompt = (
             "You are a safety agent for a developer terminal. "
             "Evaluate whether this shell command is safe to run:\n\n"
             f"```\n{command}\n```\n\n"
             "Reply with exactly one word: ALLOW (if safe) or BLOCK (if dangerous)."
         )
         result = subprocess.run(
             ["claude", "--print", prompt],
             capture_output=True,
             text=True,
             timeout=timeout,
         )
         return result.stdout.strip()
     ```

  2. Update `evaluate()` to accept and forward the timeout:
     ```python
     def evaluate(command: str, mode: str, timeout: int = 30) -> int:
         """Evaluate command via agent with regex fallback. Returns 0 (allow) or 2 (block)."""
         try:
             response = invoke_subagent(command, timeout=timeout)
             decision = parse_agent_response(response)
             return 2 if decision == "BLOCK" else 0
         except Exception as e:
             print(
                 f"[zie-framework] safety_check_agent: agent error, falling back to regex: {e}",
                 file=sys.stderr,
             )
             return _regex_evaluate(command)
     ```

  3. In `__main__` block, read config and pass timeout to `evaluate()`:
     ```python
     if __name__ == "__main__":
         try:
             event = read_event()

             tool_name = event.get("tool_name", "")
             if tool_name != "Bash":
                 sys.exit(0)

             command = (event.get("tool_input") or {}).get("command", "")
             if not command:
                 sys.exit(0)

             cwd = get_cwd()
             config = load_config(cwd)
             mode = config.get("safety_check_mode", "regex")

             if mode not in ("agent", "both"):
                 sys.exit(0)  # defer to safety-check.py in regex mode

             result = evaluate(command, mode, timeout=config["safety_agent_timeout_s"])
             sys.exit(result)
         except Exception:
             sys.exit(0)
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm `invoke_subagent` default `timeout=30` is a fallback for direct callers/tests only; production path always passes from config.

  Run: `make test-unit` — still PASS

---

## Task 4: Replace `subprocess.run(timeout=...)` in `auto-test.py` with `threading.Timer` wall-clock guard

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- When `auto_test_max_wait_s > 0`, the hook arms a `threading.Timer` before `subprocess.Popen()` fires; on expiry the timer kills the process group via `os.killpg(os.getpgid(proc.pid), signal.SIGKILL)` with `proc.kill()` fallback.
- On expiry, the hook prints `[zie-framework] auto-test: timed out after Xs — tests may be hanging. Run make test-unit manually.` (where X = `auto_test_max_wait_s`) and exits 0.
- When `auto_test_max_wait_s == 0`, no timer is armed; the hook falls back to the existing `subprocess.run(timeout=auto_test_timeout_ms//1000)` path.
- Timer is cancelled in a `finally` block if the process completes normally before expiry.
- `OSError` from `os.killpg` (process already gone) is caught; `proc.kill()` fallback is tried; if that also raises, the exception is swallowed and hook still exits 0.

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add `TestAutoTestWallClockGuard` to `tests/unit/test_hooks_auto_test.py`:

  ```python
  import signal
  import stat

  class TestAutoTestWallClockGuard:
      """Wall-clock timer kills hanging subprocess and hook exits 0."""

      @pytest.fixture(autouse=True)
      def _cleanup_debounce(self, tmp_path):
          yield
          p = project_tmp_path("last-test", tmp_path.name)
          if p.exists():
              p.unlink()

      def _make_slow_runner(self, bin_dir: Path, sleep_s: int = 60) -> None:
          """Write a fake test runner that sleeps indefinitely."""
          runner = bin_dir / "python3"
          runner.write_text(f"#!/bin/sh\nsleep {sleep_s}\n")
          runner.chmod(runner.stat().st_mode | stat.S_IEXEC)

      def test_wall_clock_timeout_exits_zero(self, tmp_path):
          """Hook must exit 0 when wall-clock guard fires."""
          bin_dir = tmp_path / "fakebin"
          bin_dir.mkdir()
          self._make_slow_runner(bin_dir)

          cwd = make_cwd(tmp_path, config={
              "test_runner": "pytest",
              "auto_test_max_wait_s": 2,
              "auto_test_debounce_ms": 0,
          })
          target = cwd / "hooks" / "utils.py"
          target.parent.mkdir(parents=True, exist_ok=True)
          target.write_text("# stub")

          env = {
              **os.environ,
              "CLAUDE_CWD": str(cwd),
              "PATH": str(bin_dir) + ":" + os.environ.get("PATH", ""),
              "ZIE_TEST_RUNNER": "",
              "ZIE_AUTO_TEST_DEBOUNCE_MS": "0",
          }
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps({"tool_name": "Edit",
                                "tool_input": {"file_path": str(target)}}),
              capture_output=True, text=True, env=env, timeout=10,
          )
          assert r.returncode == 0
          assert "timed out" in r.stdout or "timed out" in r.stderr

      def test_wall_clock_timeout_message_format(self, tmp_path):
          """Timeout message must include the configured wait value."""
          bin_dir = tmp_path / "fakebin"
          bin_dir.mkdir()
          self._make_slow_runner(bin_dir)

          cwd = make_cwd(tmp_path, config={
              "test_runner": "pytest",
              "auto_test_max_wait_s": 2,
              "auto_test_debounce_ms": 0,
          })
          target = cwd / "hooks" / "utils.py"
          target.parent.mkdir(parents=True, exist_ok=True)
          target.write_text("# stub")

          env = {
              **os.environ,
              "CLAUDE_CWD": str(cwd),
              "PATH": str(bin_dir) + ":" + os.environ.get("PATH", ""),
              "ZIE_TEST_RUNNER": "",
              "ZIE_AUTO_TEST_DEBOUNCE_MS": "0",
          }
          r = subprocess.run(
              [sys.executable, HOOK],
              input=json.dumps({"tool_name": "Edit",
                                "tool_input": {"file_path": str(target)}}),
              capture_output=True, text=True, env=env, timeout=10,
          )
          combined = r.stdout + r.stderr
          assert "2s" in combined or "2" in combined

      def test_zero_max_wait_does_not_arm_timer(self):
          """Source must check auto_test_max_wait_s > 0 before arming timer."""
          source = Path(HOOK).read_text()
          assert "auto_test_max_wait_s" in source
          # The guard condition must be present
          assert 'auto_test_max_wait_s' in source

      def test_normal_completion_cancels_timer(self, tmp_path):
          """Hook must cancel timer when subprocess completes normally."""
          source = Path(HOOK).read_text()
          assert "timer.cancel()" in source, \
              "threading.Timer must be cancelled in finally block"

      def test_uses_process_group_kill(self):
          """Source must use os.killpg for process group kill."""
          source = Path(HOOK).read_text()
          assert "os.killpg" in source, \
              "auto-test.py must use os.killpg to kill hanging process group"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`:

  1. Add imports at top:
     ```python
     import os
     import signal
     import threading
     ```

  2. Replace the subprocess execution block (currently `subprocess.run(...)` inside the `try`) with:
     ```python
     max_wait = config["auto_test_max_wait_s"]

     if max_wait > 0:
         # Wall-clock guard path: Popen + threading.Timer
         timed_out = threading.Event()

         def _kill_on_timeout(proc):
             try:
                 os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
             except OSError:
                 try:
                     proc.kill()
                 except Exception:
                     pass
             timed_out.set()
             print(
                 f"[zie-framework] auto-test: timed out after {max_wait}s"
                 f" — tests may be hanging. Run make test-unit manually."
             )

         proc = subprocess.Popen(
             cmd,
             cwd=str(cwd),
             stdout=subprocess.PIPE,
             stderr=subprocess.PIPE,
             text=True,
             start_new_session=True,
         )
         timer = threading.Timer(max_wait, _kill_on_timeout, args=[proc])
         try:
             timer.start()
             stdout_data, stderr_data = proc.communicate()
             rc = proc.returncode
         finally:
             timer.cancel()

         if timed_out.is_set():
             sys.exit(0)

         if rc == 0:
             print("[zie-framework] Tests pass ✓")
         else:
             print("[zie-framework] Tests FAILED — fix before continuing")
             lines = (stdout_data + stderr_data).splitlines()
             for line in lines[:20]:
                 if line.strip():
                     print(f"  {line}")
     else:
         # Fallback path: subprocess.run with auto_test_timeout_ms
         timeout = config["auto_test_timeout_ms"] // 1000
         result = subprocess.run(
             cmd,
             cwd=str(cwd),
             capture_output=True,
             text=True,
             timeout=timeout,
         )
         if result.returncode == 0:
             print("[zie-framework] Tests pass ✓")
         else:
             print("[zie-framework] Tests FAILED — fix before continuing")
             lines = (result.stdout + result.stderr).splitlines()
             for line in lines[:20]:
                 if line.strip():
                     print(f"  {line}")
     ```

  3. The existing `except subprocess.TimeoutExpired` clause covers only the fallback path (when `max_wait == 0`). Ensure the outer `except Exception as e` still catches other errors.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Extract the kill-on-timeout callback into a named inner function for readability (already done above as `_kill_on_timeout`).
  - Confirm `start_new_session=True` is used on Popen so `os.getpgid` returns a valid process group.

  Run: `make test-unit` — still PASS

---

## Task 5: Update `CLAUDE.md` Hook Configuration table

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- The Hook Configuration table in `CLAUDE.md` includes all four new keys: `subprocess_timeout_s`, `safety_agent_timeout_s`, `auto_test_max_wait_s`, `auto_test_timeout_ms`.
- Each row documents: key, default value, description.
- `auto_test_max_wait_s: 0` is documented as "no wall-clock guard".
- No existing rows are removed.

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_claude_md_config_docs.py` (new assertions):

  ```python
  class TestConfigTableHardeningKeys:
      def test_subprocess_timeout_s_documented(self):
          source = Path(REPO_ROOT / "CLAUDE.md").read_text()
          assert "subprocess_timeout_s" in source

      def test_safety_agent_timeout_s_documented(self):
          source = Path(REPO_ROOT / "CLAUDE.md").read_text()
          assert "safety_agent_timeout_s" in source

      def test_auto_test_max_wait_s_documented(self):
          source = Path(REPO_ROOT / "CLAUDE.md").read_text()
          assert "auto_test_max_wait_s" in source

      def test_auto_test_max_wait_zero_escape_hatch_documented(self):
          source = Path(REPO_ROOT / "CLAUDE.md").read_text()
          # The 0 = no guard escape hatch must be in the docs
          assert "0" in source and "auto_test_max_wait_s" in source
  ```

  Run: `make test-unit` — must FAIL (keys absent from CLAUDE.md)

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, extend the Hook Configuration table under `## Hook Configuration`:

  ```markdown
  | `subprocess_timeout_s` | `5` | `int` | Timeout in seconds for `git` subprocess calls in `failure-context.py` and `stop-guard.py`. |
  | `safety_agent_timeout_s` | `30` | `int` | Timeout in seconds for the Claude subagent subprocess in `safety_check_agent.py`. |
  | `auto_test_max_wait_s` | `15` | `int` | Wall-clock kill limit for `auto-test.py` subprocess. Set to `0` to disable the wall-clock guard (falls back to `auto_test_timeout_ms`). |
  | `auto_test_timeout_ms` | `30000` | `int` | Fallback subprocess timeout (ms) used by `auto-test.py` when `auto_test_max_wait_s` is `0`. |
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Re-read the table to verify formatting is consistent with existing rows.

  Run: `make test-unit` — still PASS

---

## Commit Sequence

After all five tasks pass `make test-unit`:

```
git add hooks/utils.py tests/unit/test_utils.py
git commit -m "feat(config): add validate_config + CONFIG_SCHEMA to utils"

git add hooks/failure-context.py hooks/stop-guard.py tests/unit/test_hooks_failure_context.py tests/unit/test_stop_guard.py
git commit -m "feat(hooks): read subprocess_timeout_s from validated config"

git add hooks/safety_check_agent.py tests/unit/test_hooks_safety_check_agent.py
git commit -m "feat(hooks): read safety_agent_timeout_s from config in invoke_subagent"

git add hooks/auto-test.py tests/unit/test_hooks_auto_test.py
git commit -m "feat(hooks): wall-clock timer guard for auto-test subprocess"

git add CLAUDE.md tests/unit/test_claude_md_config_docs.py
git commit -m "docs: document four new config keys in CLAUDE.md config table"
```

Run full suite: `make test` — all green before marking approved.
