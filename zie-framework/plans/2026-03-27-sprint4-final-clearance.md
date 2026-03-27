---
approved: false
approved_at:
backlog: backlog/audit-weak-nocrash-assertions.md
---

# Sprint 4 — Final Backlog Clearance — Implementation Plan

**Goal:** Clear the 3 remaining backlog items: weak hook test assertions, git subprocess caching on hot paths, and undocumented safety_check_mode config key.
**Architecture:** All changes are additive — new cache helpers in utils.py, assertion additions in existing tests, one CLAUDE.md section. No new files outside tests.
**Tech Stack:** Python 3.x, pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add git status cache helpers |
| Modify | `hooks/failure-context.py` | Use cached git calls |
| Modify | `hooks/sdlc-compact.py` | Use cached git calls |
| Modify | `tests/unit/test_utils.py` | Tests for git cache helpers |
| Modify | `tests/unit/test_hooks_failure_context.py` | Strengthen weak assertions |
| Modify | `tests/unit/test_hooks_sdlc_compact.py` | Strengthen weak assertions |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Strengthen weak assertions |
| Modify | `tests/unit/test_hooks_auto_test.py` | Strengthen weak assertions |
| Modify | `tests/unit/test_hooks_notification_log.py` | Strengthen weak assertions |
| Modify | `CLAUDE.md` | Document safety_check_mode config key |

---

## Task 1: Git status caching helpers in utils.py

**Acceptance Criteria:**
- `get_cached_git_status(session_id, key, ttl=5)` returns cached string or `None` on miss/expiry
- `write_git_status_cache(session_id, key, content)` writes to `/tmp/zie-<session>/git-<key>.cache`
- Cache miss (file missing) returns `None`
- Cache hit within TTL returns content string
- Cache hit beyond TTL returns `None`
- Invalid session_id characters are safe (no path injection)

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # In tests/unit/test_utils.py — create new class TestGitStatusCache
  import time
  from utils import get_cached_git_status, write_git_status_cache

  class TestGitStatusCache:
      def test_cache_miss_returns_none(self, tmp_path, monkeypatch):
          monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
          result = get_cached_git_status("sid-001", "log", ttl=5)
          assert result is None

      def test_cache_hit_within_ttl(self, tmp_path, monkeypatch):
          monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
          write_git_status_cache("sid-002", "log", "abc def")
          result = get_cached_git_status("sid-002", "log", ttl=60)
          assert result == "abc def"

      def test_cache_miss_after_ttl(self, tmp_path, monkeypatch):
          monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
          write_git_status_cache("sid-003", "log", "old")
          cache_dir = tmp_path / "zie-sid-003"
          cache_file = cache_dir / "git-log.cache"
          # backdate mtime by 10s
          old_mtime = time.time() - 10
          import os; os.utime(cache_file, (old_mtime, old_mtime))
          result = get_cached_git_status("sid-003", "log", ttl=5)
          assert result is None

      def test_write_creates_parent_dir(self, tmp_path, monkeypatch):
          monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
          write_git_status_cache("sid-004", "branch", "main")
          assert (tmp_path / "zie-sid-004" / "git-branch.cache").exists()

      def test_path_injection_sanitized(self, tmp_path, monkeypatch):
          """session_id with path separators must not escape tmp dir."""
          monkeypatch.setattr("tempfile.gettempdir", lambda: str(tmp_path))
          # Should not raise; cache key sanitization prevents directory traversal
          write_git_status_cache("../../evil", "log", "data")
          result = get_cached_git_status("../../evil", "log", ttl=60)
          # Either works safely or returns None — must not write outside tmp_path
          import os
          for root, dirs, files in os.walk(str(tmp_path)):
              for f in files:
                  full = os.path.join(root, f)
                  assert full.startswith(str(tmp_path)), f"file escaped tmp: {full}"
  ```
  Run: `make test-unit` — must FAIL (functions not yet defined)

- [ ] **Step 2: Implement (GREEN)**
  Add to `hooks/utils.py` after `write_roadmap_cache`:

  ```python
  def get_cached_git_status(session_id: str, key: str, ttl: int = 5) -> str | None:
      """Return cached git output if fresh (age < ttl seconds), else None.

      key identifies the git command (e.g. 'log', 'branch', 'diff').
      Returns None on cache miss, expiry, or any read error.
      """
      try:
          safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
          safe_key = re.sub(r'[^a-zA-Z0-9_-]', '-', key)
          cache_path = Path(tempfile.gettempdir()) / f"zie-{safe_id}" / f"git-{safe_key}.cache"
          if cache_path.exists():
              age = time.time() - cache_path.stat().st_mtime
              if age < ttl:
                  return cache_path.read_text()
          return None
      except Exception:
          return None


  def write_git_status_cache(session_id: str, key: str, content: str) -> None:
      """Write git output to the session cache.

      key identifies the git command (e.g. 'log', 'branch', 'diff').
      Silently ignores all errors.
      """
      try:
          safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
          safe_key = re.sub(r'[^a-zA-Z0-9_-]', '-', key)
          cache_dir = Path(tempfile.gettempdir()) / f"zie-{safe_id}"
          cache_dir.mkdir(parents=True, exist_ok=True)
          (cache_dir / f"git-{safe_key}.cache").write_text(content)
      except Exception:
          pass
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactor needed — implementation is minimal and clean.
  Run: `make test-unit` — still PASS

---

## Task 2: Update failure-context.py and sdlc-compact.py to use git cache

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `failure-context.py` calls `get_cached_git_status` before spawning git subprocess
- `sdlc-compact.py` (PreCompact) calls `get_cached_git_status` before spawning git subprocess
- Cache hit skips subprocess; cache miss runs subprocess then writes cache
- Existing tests for both hooks continue to pass

**Files:**
- Modify: `hooks/failure-context.py`
- Modify: `hooks/sdlc-compact.py`

- [ ] **Step 1: Write failing tests (RED)**
  In `tests/unit/test_hooks_failure_context.py` add a cache integration test:

  ```python
  class TestFailureContextGitCache:
      """Verify failure-context reads git data from cache when available."""

      def test_git_log_from_cache(self, tmp_path):
          """Cached git log is used — no subprocess needed."""
          from utils import write_git_status_cache
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          sid = "test-git-cache-fc-77x"
          write_git_status_cache(sid, "log", "abc1234 cached commit message")
          event = {"tool_name": "Bash", "session_id": sid}
          env = {**os.environ, "CLAUDE_CWD": str(cwd)}
          r = subprocess.run(
              [sys.executable, HOOK], input=json.dumps(event),
              capture_output=True, text=True, env=env,
          )
          assert r.returncode == 0
          ctx = json.loads(r.stdout)["additionalContext"]
          assert "abc1234 cached commit message" in ctx
  ```

  Run: `make test-unit` — must FAIL (cache not yet consulted in hook)

- [ ] **Step 2: Implement (GREEN)**
  In `hooks/failure-context.py`, update the import and git log + branch blocks:

  ```python
  # Update import:
  from utils import read_event, get_cwd, parse_roadmap_section_content, read_roadmap_cached, get_cached_git_status, write_git_status_cache

  # Replace git log block (lines 47-58):
  try:
      cached = get_cached_git_status(session_id, "log")
      if cached is not None:
          last_commit = cached
      else:
          log_result = subprocess.run(
              ["git", "log", "-1", "--pretty=%h %s"],
              capture_output=True, text=True, cwd=str(cwd), timeout=5,
          )
          last_commit = (
              log_result.stdout.strip()
              if log_result.returncode == 0
              else "(git unavailable)"
          )
          if log_result.returncode == 0:
              write_git_status_cache(session_id, "log", last_commit)
  except Exception:
      last_commit = "(git unavailable)"

  # Replace git branch block (lines 61-72):
  try:
      cached = get_cached_git_status(session_id, "branch")
      if cached is not None:
          branch = cached
      else:
          branch_result = subprocess.run(
              ["git", "rev-parse", "--abbrev-ref", "HEAD"],
              capture_output=True, text=True, cwd=str(cwd), timeout=5,
          )
          branch = (
              branch_result.stdout.strip()
              if branch_result.returncode == 0
              else "(git unavailable)"
          )
          if branch_result.returncode == 0:
              write_git_status_cache(session_id, "branch", branch)
  except Exception:
      branch = "(git unavailable)"
  ```

  In `hooks/sdlc-compact.py`, update the import and git branch + diff blocks similarly:

  ```python
  # Update import:
  from utils import (
      get_cached_git_status,
      get_cwd,
      load_config,
      parse_roadmap_section_content,
      project_tmp_path,
      read_event,
      read_roadmap_cached,
      safe_write_tmp,
      write_git_status_cache,
  )

  # Replace git branch block (lines 57-67):
  try:
      cached = get_cached_git_status(session_id, "branch")
      if cached is not None:
          git_branch = cached
      else:
          result = subprocess.run(
              ["git", "-C", str(cwd), "branch", "--show-current"],
              capture_output=True, text=True, timeout=5,
          )
          git_branch = result.stdout.strip()
          if result.returncode == 0 and git_branch:
              write_git_status_cache(session_id, "branch", git_branch)
  except Exception as e:
      print(f"[zie-framework] sdlc-compact: git branch failed: {e}", file=sys.stderr)
      git_branch = ""

  # Replace git diff block (lines 70-80) — diff changes per edit, use shorter TTL or no cache:
  # Note: git diff --name-only HEAD changes frequently; cache with ttl=2 to avoid stale data
  try:
      cached = get_cached_git_status(session_id, "diff", ttl=2)
      if cached is not None:
          changed_files = [f for f in cached.splitlines() if f.strip()][:20]
      else:
          result = subprocess.run(
              ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
              capture_output=True, text=True, timeout=5,
          )
          changed_files = [f for f in result.stdout.splitlines() if f.strip()][:20]
          if result.returncode == 0:
              write_git_status_cache(session_id, "diff", result.stdout)
  except Exception as e:
      print(f"[zie-framework] sdlc-compact: git diff failed: {e}", file=sys.stderr)
      changed_files = []
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactor needed.
  Run: `make test-unit` — still PASS

---

## Task 3: Strengthen weak test assertions

<!-- depends_on: none -->

**Acceptance Criteria:**
- Each targeted test asserts at least one observable side-effect beyond `returncode == 0`
- "no action" path tests assert `stdout.strip() == ""`
- "file write" path tests assert the output file exists or has expected content
- No existing passing tests are broken

**Files:**
- Modify: `tests/unit/test_hooks_failure_context.py`
- Modify: `tests/unit/test_hooks_sdlc_compact.py`
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`
- Modify: `tests/unit/test_hooks_auto_test.py`
- Modify: `tests/unit/test_hooks_notification_log.py`

- [ ] **Step 1: Write failing tests (RED)**
  Assertion additions to existing tests. Each change below represents the RED state — the assertion is being added BEFORE verifying it passes. Add assertions to each function first, then confirm they pass in Step 2.

  Examples of what the RED state looks like in 2 files:

  **test_hooks_failure_context.py** — add `assert result.stdout == ""` to `test_exit_zero_on_interrupt`:
  ```python
  def test_exit_zero_on_interrupt(self, tmp_path):
      cwd = make_cwd(tmp_path)
      event = {"tool_name": "Write", "is_interrupt": True}
      result = run_hook(event, tmp_cwd=cwd)
      assert result.returncode == 0
      assert result.stdout == ""   # ← RED: adding this assertion
  ```

  **test_hooks_wip_checkpoint.py** — add counter check to `test_no_network_call_before_fifth_edit`:
  ```python
  def test_no_network_call_before_fifth_edit(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      for _ in range(4):
          r = run_hook(tmp_cwd=cwd, env_overrides={
              "ZIE_MEMORY_API_KEY": "fake-key",
              "ZIE_MEMORY_API_URL": "http://localhost:19999",
          })
          assert r.returncode == 0  # must not crash even on network error
      counter = persistent_project_path("edit-count", tmp_path.name)  # ← RED: adding these
      assert counter.exists()
      assert int(counter.read_text().strip()) == 4
  ```

  These additions SHOULD pass on first run since they assert correct existing behavior. If any fail, the hook has a bug — do NOT remove the assertion; fix the hook instead.

  Run: `make test-unit` — must PASS (assertions are correct) and confirm pass count increases by number of assertions added

- [ ] **Step 2: Implement (GREEN)**

  **test_hooks_failure_context.py** — `test_exit_zero_on_interrupt` (line ~95):
  ```python
  # Add after existing assert:
  assert result.stdout == ""
  ```

  **test_hooks_sdlc_compact.py** — `test_invalid_json_exits_zero` and `test_empty_stdin_exits_zero`:
  ```python
  # Add to both:
  assert r.stdout.strip() == ""
  ```

  **test_hooks_wip_checkpoint.py**:
  - `test_no_action_when_no_zf_dir` (line ~67-69): add `assert r.stdout.strip() == ""`
  - `test_invalid_json_exits_zero` (line ~77-80): add `assert r.stdout.strip() == ""`
  - `test_no_network_call_before_fifth_edit` (lines ~104-111): after the loop, verify counter file exists with value 4:
    ```python
    counter = persistent_project_path("edit-count", tmp_path.name)
    assert counter.exists()
    assert int(counter.read_text().strip()) == 4
    ```

  **test_hooks_auto_test.py**:
  - `test_invalid_json_exits_zero` (line ~54): add `assert r.stdout.strip() == ""`
  - `test_exits_zero_on_corrupt_config` (line ~290): add `assert r.stdout.strip() == ""` (corrupt config → no test_runner → no output)

  **test_hooks_notification_log.py**:
  - `test_bad_stdin_exits_zero` (line ~284): add `assert r.stdout.strip() == ""`
  - `test_always_exits_zero` (line ~286-293): add log file existence check:
    ```python
    from utils import project_tmp_path  # or use the existing tmp_log_path helper
    log = tmp_log_path("permission-log", project)
    assert log.exists()
    ```

  Run: `make test-unit` — must PASS (all added assertions should be correct)

- [ ] **Step 3: Refactor**
  No refactor needed — these are assertion additions only.
  Run: `make test-unit` — still PASS

---

## Task 4: Document safety_check_mode in CLAUDE.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- CLAUDE.md contains a `## Hook Configuration` section documenting `safety_check_mode`
- Three valid values documented: `"regex"` (default), `"agent"`, `"both"`
- Behavior of each value clearly described

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Write failing tests (RED)**
  In a new test file `tests/unit/test_claude_md_config_docs.py`:
  ```python
  """Verify CLAUDE.md documents the safety_check_mode config key."""
  from pathlib import Path

  CLAUDE_MD = Path(__file__).parents[2] / "CLAUDE.md"


  def test_safety_check_mode_documented():
      content = CLAUDE_MD.read_text()
      assert "safety_check_mode" in content, "CLAUDE.md must document safety_check_mode config key"


  def test_safety_check_mode_values_documented():
      content = CLAUDE_MD.read_text()
      assert '"regex"' in content or "'regex'" in content, "CLAUDE.md must document regex mode"
      assert '"agent"' in content or "'agent'" in content, "CLAUDE.md must document agent mode"
  ```
  Run: `make test-unit` — must FAIL (safety_check_mode not yet in CLAUDE.md)

- [ ] **Step 2: Implement (GREEN)**
  In `CLAUDE.md`, after the `## Key Rules` section, add:

  ```markdown
  ## Hook Configuration

  Optional keys in `zie-framework/.config` (JSON):

  | Key | Default | Values | Description |
  | --- | --- | --- | --- |
  | `safety_check_mode` | `"regex"` | `"regex"`, `"agent"`, `"both"` | Controls `safety_check_agent.py` behavior. `"regex"` — fast pattern matching only (no subprocess). `"agent"` — spawns a Claude subagent on every Bash call to evaluate safety. `"both"` — runs regex first, then agent. Use `"regex"` unless you need AI-level judgment on commands. |
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No refactor needed.
  Run: `make test-unit` — still PASS
