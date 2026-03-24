---
approved: true
approved_at: 2026-03-24
backlog: backlog/sessionstart-env-file.md
spec: specs/2026-03-24-sessionstart-env-file-design.md
---

# SessionStart CLAUDE_ENV_FILE Config Injection — Implementation Plan

**Goal:** Write four project config values as exported shell variables to `CLAUDE_ENV_FILE` during `SessionStart` so every subsequent hook reads them from the environment instead of re-parsing `.config`.
**Architecture:** `session-resume.py` gains a single env-file write block after config is loaded; it checks `CLAUDE_ENV_FILE`, applies single-quote wrapping and a symlink guard, then writes four `export VAR=value` lines. Downstream hooks (`auto-test.py`, `wip-checkpoint.py`, `session-learn.py`) each gain an `os.environ.get()` fast-path before their `.config` read, falling back to the existing parse path when the env vars are absent so behaviour is unchanged outside a SessionStart context.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/session-resume.py` | Add env-file write block after config load |
| Modify | `hooks/auto-test.py` | Add env var fast-path for `ZIE_TEST_RUNNER` and `ZIE_AUTO_TEST_DEBOUNCE_MS` |
| Modify | `hooks/wip-checkpoint.py` | Add `ZIE_MEMORY_ENABLED` fast-path guard |
| Modify | `hooks/session-learn.py` | Add `ZIE_MEMORY_ENABLED` fast-path guard |
| Modify | `tests/unit/test_hooks_session_resume.py` | Add `TestSessionResumeEnvFile` test class |
| Modify | `tests/unit/test_hooks_auto_test.py` | Add env var fast-path tests |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Add `ZIE_MEMORY_ENABLED=0` skip tests |
| Modify | `tests/unit/test_hooks_session_learn.py` | Add `ZIE_MEMORY_ENABLED=0` skip tests |

---

## Task 1: Write env vars to `CLAUDE_ENV_FILE` in `session-resume.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- When `CLAUDE_ENV_FILE` is set to a writable path, the hook writes exactly four `export VAR='value'` lines to that file
- All four vars use single-quote wrapping for shell safety
- `ZIE_MEMORY_ENABLED` is `'1'` when `zie_memory_enabled` is truthy, `'0'` otherwise
- `ZIE_AUTO_TEST_DEBOUNCE_MS` is always a clean integer string; falls back to `'3000'` if the config value is non-integer
- When `CLAUDE_ENV_FILE` is absent or empty, the hook exits 0 silently with no write attempted
- When `CLAUDE_ENV_FILE` is a symlink, the hook logs `[zie-framework] WARNING` to stderr and skips the write
- When `.config` is missing, all four vars use their default values; existing stderr warning from the config parse step fires but the env-file write still runs
- All existing `TestSessionResumeHappyPath`, `TestSessionResumeGracefulDegradation`, `TestHookExceptionConvention`, and `TestSessionResumeConfigParseWarning` tests continue to pass

**Files:**
- Modify: `hooks/session-resume.py`
- Modify: `tests/unit/test_hooks_session_resume.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_session_resume.py — add after TestSessionResumeConfigParseWarning

  def run_hook_with_env_file(tmp_cwd, env_file_path=None, extra_env=None):
      """Run session-resume.py with an optional CLAUDE_ENV_FILE set."""
      env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
      if tmp_cwd:
          env["CLAUDE_CWD"] = str(tmp_cwd)
      if env_file_path is not None:
          env["CLAUDE_ENV_FILE"] = str(env_file_path)
      else:
          env.pop("CLAUDE_ENV_FILE", None)
      if extra_env:
          env.update(extra_env)
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps({}),
          capture_output=True, text=True, env=env,
      )


  class TestSessionResumeEnvFile:
      def test_writes_four_export_lines(self, tmp_path):
          """When CLAUDE_ENV_FILE is set, four export lines must be written."""
          env_file = tmp_path / "claude_env"
          cwd = make_cwd(tmp_path / "proj", config={
              "test_runner": "pytest",
              "zie_memory_enabled": True,
              "auto_test_debounce_ms": 5000,
          }, roadmap=SAMPLE_ROADMAP)
          run_hook_with_env_file(cwd, env_file_path=env_file)
          assert env_file.exists(), "CLAUDE_ENV_FILE was not created"
          content = env_file.read_text()
          assert "export ZIE_PROJECT=" in content
          assert "export ZIE_TEST_RUNNER=" in content
          assert "export ZIE_MEMORY_ENABLED=" in content
          assert "export ZIE_AUTO_TEST_DEBOUNCE_MS=" in content

      def test_correct_values_written(self, tmp_path):
          """Written values must match config entries."""
          env_file = tmp_path / "claude_env"
          proj_dir = tmp_path / "myproject"
          cwd = make_cwd(proj_dir, config={
              "test_runner": "pytest",
              "zie_memory_enabled": True,
              "auto_test_debounce_ms": 5000,
          }, roadmap=SAMPLE_ROADMAP)
          run_hook_with_env_file(cwd, env_file_path=env_file)
          content = env_file.read_text()
          assert "ZIE_PROJECT='myproject'" in content
          assert "ZIE_TEST_RUNNER='pytest'" in content
          assert "ZIE_MEMORY_ENABLED='1'" in content
          assert "ZIE_AUTO_TEST_DEBOUNCE_MS='5000'" in content

      def test_memory_disabled_writes_zero(self, tmp_path):
          """zie_memory_enabled=False must produce ZIE_MEMORY_ENABLED='0'."""
          env_file = tmp_path / "claude_env"
          cwd = make_cwd(tmp_path / "proj2", config={
              "zie_memory_enabled": False,
          }, roadmap=SAMPLE_ROADMAP)
          run_hook_with_env_file(cwd, env_file_path=env_file)
          content = env_file.read_text()
          assert "ZIE_MEMORY_ENABLED='0'" in content

      def test_defaults_when_config_missing(self, tmp_path):
          """Missing .config must produce default values in env file."""
          env_file = tmp_path / "claude_env"
          # make_cwd with no config — no .config file created
          cwd = make_cwd(tmp_path / "proj3", roadmap=SAMPLE_ROADMAP)
          run_hook_with_env_file(cwd, env_file_path=env_file)
          content = env_file.read_text()
          assert "ZIE_TEST_RUNNER=''" in content
          assert "ZIE_MEMORY_ENABLED='0'" in content
          assert "ZIE_AUTO_TEST_DEBOUNCE_MS='3000'" in content

      def test_no_write_when_claude_env_file_absent(self, tmp_path):
          """No CLAUDE_ENV_FILE set — hook must exit 0 and write nothing."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"}, roadmap=SAMPLE_ROADMAP)
          r = run_hook_with_env_file(cwd, env_file_path=None)
          assert r.returncode == 0
          # Confirm no stray env file created in tmp_path
          env_files = list(tmp_path.glob("claude_env*"))
          assert env_files == []

      def test_no_write_when_claude_env_file_empty_string(self, tmp_path):
          """CLAUDE_ENV_FILE='' must be treated as absent — no write, exits 0."""
          cwd = make_cwd(tmp_path / "proj5", config={}, roadmap=SAMPLE_ROADMAP)
          r = run_hook_with_env_file(cwd, env_file_path="")
          assert r.returncode == 0

      def test_symlink_skipped_with_warning(self, tmp_path):
          """CLAUDE_ENV_FILE pointing to a symlink must log WARNING and skip write."""
          real_file = tmp_path / "real_target"
          real_file.write_text("original")
          symlink = tmp_path / "claude_env_link"
          symlink.symlink_to(real_file)
          cwd = make_cwd(tmp_path / "proj6", config={}, roadmap=SAMPLE_ROADMAP)
          r = run_hook_with_env_file(cwd, env_file_path=symlink)
          assert r.returncode == 0
          assert "WARNING" in r.stderr
          assert real_file.read_text() == "original", "symlink target must not be modified"

      def test_debounce_non_integer_falls_back_to_3000(self, tmp_path):
          """Non-integer auto_test_debounce_ms must fall back to '3000' in env file."""
          env_file = tmp_path / "claude_env"
          cwd = make_cwd(tmp_path / "proj7", config={
              "auto_test_debounce_ms": "not-a-number",
          }, roadmap=SAMPLE_ROADMAP)
          run_hook_with_env_file(cwd, env_file_path=env_file)
          content = env_file.read_text()
          assert "ZIE_AUTO_TEST_DEBOUNCE_MS='3000'" in content

      def test_exit_0_when_env_file_not_writable(self, tmp_path):
          """Unwritable CLAUDE_ENV_FILE path must log to stderr and exit 0."""
          bad_path = tmp_path / "no_such_dir" / "claude_env"
          cwd = make_cwd(tmp_path / "proj8", config={}, roadmap=SAMPLE_ROADMAP)
          r = run_hook_with_env_file(cwd, env_file_path=bad_path)
          assert r.returncode == 0

      def test_returncode_0_when_zf_missing(self, tmp_path):
          """No zie-framework dir — hook exits 0 before env-file write; no write attempted."""
          env_file = tmp_path / "claude_env"
          r = run_hook_with_env_file(tmp_path, env_file_path=env_file)
          assert r.returncode == 0
          assert not env_file.exists()
  ```

  Run: `make test-unit` — must FAIL (`TestSessionResumeEnvFile` tests fail because no env-file write block exists yet)

- [ ] **Step 2: Implement (GREEN)**

  Add the following block to `hooks/session-resume.py` after the `project_name` / `project_type` / `zie_memory` variable assignments (around line 48) and before the `lines = [...]` block:

  ```python
  # Write config vars to CLAUDE_ENV_FILE (SessionStart env injection)
  _env_file_path = os.environ.get("CLAUDE_ENV_FILE", "").strip()
  if _env_file_path:
      try:
          _debounce_ms = "3000"
          try:
              _debounce_ms = str(int(config.get("auto_test_debounce_ms", 3000)))
          except (TypeError, ValueError):
              pass
          _env_lines = (
              f"export ZIE_PROJECT='{project_name}'\n"
              f"export ZIE_TEST_RUNNER='{config.get('test_runner', '')}'\n"
              f"export ZIE_MEMORY_ENABLED='{'1' if zie_memory else '0'}'\n"
              f"export ZIE_AUTO_TEST_DEBOUNCE_MS='{_debounce_ms}'\n"
          )
          _p = Path(_env_file_path)
          if os.path.islink(_p):
              print(
                  f"[zie-framework] WARNING: CLAUDE_ENV_FILE is a symlink, skipping write: {_p}",
                  file=sys.stderr,
              )
          else:
              _p.write_text(_env_lines)
      except Exception as e:
          print(f"[zie-framework] session-resume: env-file write failed: {e}", file=sys.stderr)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Confirm `_env_file_path`, `_debounce_ms`, `_env_lines`, `_p` are prefixed with `_` to signal they are block-local (no leakage into subsequent `lines` block).
  - Confirm the symlink warning message matches the pattern used in `safe_write_tmp()` (`[zie-framework] WARNING:`).
  - Confirm no `export` line omits single-quote wrapping.

  Run: `make test-unit` — still PASS

---

## Task 2: Update `auto-test.py` to read env var fast-path

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- When `ZIE_TEST_RUNNER` is set and non-empty in the environment, `auto-test.py` uses it without reading `.config`
- When `ZIE_AUTO_TEST_DEBOUNCE_MS` is set to a valid integer string, it is used without reading `.config`
- When the env vars are absent or empty, the existing `.config` read path runs unchanged (backward compatibility)
- When both env vars are present, `config_file` is never opened (confirmed by replacing config file with unreadable content and verifying hook still runs correctly)
- All existing `auto-test.py` tests continue to pass

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_auto_test.py — add new class TestAutoTestEnvVarFastPath

  class TestAutoTestEnvVarFastPath:
      """auto-test.py must read ZIE_TEST_RUNNER / ZIE_AUTO_TEST_DEBOUNCE_MS from env
      when available, falling back to .config only when the env vars are absent."""

      def test_uses_env_var_test_runner_without_config(self, tmp_path):
          """ZIE_TEST_RUNNER env var set — hook must not need .config to get runner."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          # Write a python file to trigger the hook
          target_file = cwd / "hooks" / "utils.py"
          target_file.parent.mkdir(parents=True, exist_ok=True)
          target_file.write_text("# stub")
          r = run_hook(cwd, tool="Edit", file_path=str(target_file),
                       extra_env={"ZIE_TEST_RUNNER": "pytest", "ZIE_AUTO_TEST_DEBOUNCE_MS": "0"})
          assert r.returncode == 0
          # No .config exists, yet hook ran without error
          assert "[zie] warning" not in r.stderr

      def test_env_var_absent_falls_back_to_config(self, tmp_path):
          """No ZIE_TEST_RUNNER env var — hook must fall back to .config."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"}, roadmap=SAMPLE_ROADMAP)
          target_file = cwd / "hooks" / "utils.py"
          target_file.parent.mkdir(parents=True, exist_ok=True)
          target_file.write_text("# stub")
          r = run_hook(cwd, tool="Edit", file_path=str(target_file),
                       extra_env={"ZIE_TEST_RUNNER": "", "ZIE_AUTO_TEST_DEBOUNCE_MS": ""})
          assert r.returncode == 0

      def test_empty_env_var_falls_back_to_config(self, tmp_path):
          """ZIE_TEST_RUNNER='' must be treated as absent — .config fallback applies."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest"}, roadmap=SAMPLE_ROADMAP)
          target_file = cwd / "dummy.py"
          target_file.write_text("x = 1")
          r = run_hook(cwd, tool="Edit", file_path=str(target_file),
                       extra_env={"ZIE_TEST_RUNNER": "", "ZIE_AUTO_TEST_DEBOUNCE_MS": ""})
          assert r.returncode == 0
          assert "[zie] warning" not in r.stderr

      def test_debounce_ms_from_env_var(self, tmp_path):
          """ZIE_AUTO_TEST_DEBOUNCE_MS env var must override .config debounce value."""
          cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 99999},
                         roadmap=SAMPLE_ROADMAP)
          target_file = cwd / "dummy.py"
          target_file.write_text("x = 1")
          # debounce_ms=0 via env → hook must not skip due to debounce
          r = run_hook(cwd, tool="Edit", file_path=str(target_file),
                       extra_env={"ZIE_TEST_RUNNER": "pytest", "ZIE_AUTO_TEST_DEBOUNCE_MS": "0"})
          assert r.returncode == 0
  ```

  Run: `make test-unit` — must FAIL (fast-path logic not present yet)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/auto-test.py`, replace the config-read + `test_runner` + `debounce_ms` block (lines 71–84) with:

  ```python
  # Fast-path: read from session env vars injected by session-resume.py
  test_runner = os.environ.get("ZIE_TEST_RUNNER", "").strip()
  _debounce_env = os.environ.get("ZIE_AUTO_TEST_DEBOUNCE_MS", "").strip()

  # Fallback: read .config when env vars are absent
  config = {}
  if not test_runner or not _debounce_env:
      config_file = zf / ".config"
      if config_file.exists():
          try:
              config = json.loads(config_file.read_text())
          except Exception as e:
              print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)

  if not test_runner:
      test_runner = config.get("test_runner", "")
  if not test_runner:
      sys.exit(0)

  # Debounce
  if _debounce_env:
      try:
          debounce_ms = int(_debounce_env)
      except (TypeError, ValueError):
          debounce_ms = config.get("auto_test_debounce_ms", 3000)
  else:
      debounce_ms = config.get("auto_test_debounce_ms", 3000)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - Confirm `config` dict is still initialised to `{}` before the conditional read so the `timeout` line further down (`config.get("auto_test_timeout_ms", 30000)`) still works via fallback when env vars covered `test_runner` and `debounce_ms` but not timeout.
  - Confirm the existing `test_runner = config.get("test_runner", "")` line is fully removed (no duplicate assignment).

  Run: `make test-unit` — still PASS

---

## Task 3: Update `wip-checkpoint.py` and `session-learn.py` env var fallback

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `wip-checkpoint.py`: when `ZIE_MEMORY_ENABLED='0'` is in the environment, the hook exits 0 immediately after the `api_key` / `api_url` guard (i.e. the fast-path guard short-circuits before counter file I/O and ROADMAP parse)
- `session-learn.py`: when `ZIE_MEMORY_ENABLED='0'` is in the environment, the API call block is skipped; the `pending_learn.txt` write still runs (it is not gated on memory being enabled)
- When `ZIE_MEMORY_ENABLED` is absent or empty, both hooks behave exactly as before
- All existing tests for `wip-checkpoint.py` and `session-learn.py` continue to pass

**Files:**
- Modify: `hooks/wip-checkpoint.py`
- Modify: `hooks/session-learn.py`
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`
- Modify: `tests/unit/test_hooks_session_learn.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hooks_wip_checkpoint.py — add new class

  class TestWipCheckpointMemoryEnabledFastPath:
      def test_exits_early_when_zie_memory_enabled_is_zero(self, tmp_path):
          """ZIE_MEMORY_ENABLED=0 must cause hook to exit 0 without making API call."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_ENABLED": "0",
              "ZIE_MEMORY_API_KEY": "real-key",
              "ZIE_MEMORY_API_URL": "https://example.com",
          })
          assert r.returncode == 0
          # Counter file must not have been incremented (early exit before counter I/O)
          from utils import project_tmp_path
          counter = project_tmp_path("edit-count", tmp_path.name)
          assert not counter.exists()

      def test_proceeds_normally_when_zie_memory_enabled_is_one(self, tmp_path):
          """ZIE_MEMORY_ENABLED=1 must not short-circuit the hook."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_ENABLED": "1",
              "ZIE_MEMORY_API_KEY": "",   # no key — will still exit on api_key guard
              "ZIE_MEMORY_API_URL": "",
          })
          assert r.returncode == 0

      def test_absent_env_var_falls_back_to_normal_flow(self, tmp_path):
          """ZIE_MEMORY_ENABLED absent — hook must proceed to api_key guard as before."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_API_KEY": "",
              "ZIE_MEMORY_API_URL": "",
          })
          assert r.returncode == 0
  ```

  ```python
  # tests/unit/test_hooks_session_learn.py — add new class

  class TestSessionLearnMemoryEnabledFastPath:
      def test_skips_api_call_when_zie_memory_enabled_is_zero(self, tmp_path):
          """ZIE_MEMORY_ENABLED=0 must skip the API call block; pending_learn still written."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_ENABLED": "0",
              "ZIE_MEMORY_API_KEY": "real-key",
              "ZIE_MEMORY_API_URL": "https://example.com",
          })
          assert r.returncode == 0
          # pending_learn.txt must still be written
          pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
          assert pending.exists(), "pending_learn.txt must be written regardless of ZIE_MEMORY_ENABLED"
          # No API error should appear — call was skipped
          assert "session-learn:" not in r.stderr

      def test_proceeds_to_api_when_zie_memory_enabled_is_one(self, tmp_path):
          """ZIE_MEMORY_ENABLED=1 with no valid key must fall through to api_key guard."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_ENABLED": "1",
              "ZIE_MEMORY_API_KEY": "",
              "ZIE_MEMORY_API_URL": "",
          })
          assert r.returncode == 0

      def test_absent_env_var_falls_back_to_normal_flow(self, tmp_path):
          """ZIE_MEMORY_ENABLED absent — hook must proceed normally to api_key guard."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook(cwd, extra_env={
              "ZIE_MEMORY_API_KEY": "",
              "ZIE_MEMORY_API_URL": "",
          })
          assert r.returncode == 0
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/wip-checkpoint.py`** — add fast-path guard immediately after the `api_url` check (after line 22, before `cwd = get_cwd()`):

  ```python
  # Fast-path: honour ZIE_MEMORY_ENABLED=0 injected by session-resume.py
  _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
  if _mem_enabled == "0":
      sys.exit(0)
  ```

  **`hooks/session-learn.py`** — the `pending_learn.txt` write must remain unconditional. Add the fast-path guard to replace the `if not api_key: sys.exit(0)` block so that when `ZIE_MEMORY_ENABLED=0` is set the API block is skipped but the write already happened above it:

  ```python
  # Fast-path: honour ZIE_MEMORY_ENABLED=0 injected by session-resume.py
  _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
  if _mem_enabled == "0":
      sys.exit(0)

  # If zie-memory enabled, call session-stop endpoint
  if not api_key:
      sys.exit(0)
  if not api_url.startswith("https://"):
      sys.exit(0)
  ```

  Place this block immediately after the `atomic_write(...)` call (after line 35 in current `session-learn.py`) so the pending_learn write always runs first.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  - In `wip-checkpoint.py`: confirm the `_mem_enabled` guard sits after the `api_key` / `api_url` checks, not before them. The canonical gate order is: tool filter → api_key → api_url → memory-enabled fast-path → zf.exists(). This preserves the established guard ordering convention where secret-based guards come first.

    Reorder if needed:
    ```python
    api_key = os.environ.get("ZIE_MEMORY_API_KEY", "")
    api_url = os.environ.get("ZIE_MEMORY_API_URL", "")
    if not api_key:
        sys.exit(0)
    if not api_url.startswith("https://"):
        sys.exit(0)

    _mem_enabled = os.environ.get("ZIE_MEMORY_ENABLED", "").strip()
    if _mem_enabled == "0":
        sys.exit(0)
    ```

  - In `session-learn.py`: confirm the `_mem_enabled` guard is placed *after* `atomic_write(...)` and *before* `if not api_key`.
  - Confirm no test helper needs updating — `run_hook` in both test files already passes `extra_env` through `os.environ`.

  Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/session-resume.py hooks/auto-test.py hooks/wip-checkpoint.py hooks/session-learn.py tests/unit/test_hooks_session_resume.py tests/unit/test_hooks_auto_test.py tests/unit/test_hooks_wip_checkpoint.py tests/unit/test_hooks_session_learn.py && git commit -m "feat: SessionStart CLAUDE_ENV_FILE config injection and env var fast-paths"`*
