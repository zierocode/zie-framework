---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-tests-tmp-path.md
spec: specs/2026-03-24-audit-tests-tmp-path-design.md
---

# Migrate Tests from /tmp Hardcoded Paths to pytest tmp_path — Implementation Plan

**Goal:** Replace all hardcoded `/tmp/zie-*` path construction in `test_session_cleanup.py` and `test_hooks_wip_checkpoint.py` with paths derived from pytest's `tmp_path` fixture so tests are hermetic and parallelism-safe.
**Architecture:** Tests inject a `CLAUDE_CWD` whose `.name` drives `project_tmp_path()` inside the hook; test-side path assertions and teardown compute the same path via the `project_tmp_path()` helper — both sides agree on the path without hardcoding `/tmp`. `test_session_cleanup.py` uses a unique project name derived from `tmp_path.name` so the hook's glob hits the right files and not real state.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_session_cleanup.py` | Replace hardcoded `/tmp/zie-<project>-*` paths with `project_tmp_path()`-derived paths; inject matching `CLAUDE_CWD` |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Replace `counter_path()` helper with `project_tmp_path()`; fix `reset_counter()` and `_cleanup_counter` teardown |
| Read-only | `hooks/utils.py` | Reference for `project_tmp_path(name, project)` signature — no changes |

---

## Task 1: Migrate test_session_cleanup.py to tmp_path-derived paths

**Acceptance Criteria:**
- `test_deletes_project_scoped_tmp_files` no longer writes to literal `/tmp/zie-zie-cleanup-test-proj-*`; it derives the path from `tmp_path.name`
- `test_does_not_delete_other_project_files` derives the "other project" path from `tmp_path.name` with a suffix, not a hardcoded constant
- All three tests remain green after the change
- No `/tmp/zie-zie-cleanup-*` files are left behind after the test run

**Files:**
- Modify: `tests/unit/test_session_cleanup.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a `test_paths_are_tmp_path_scoped` canary test that fails when paths are still hardcoded:

  ```python
  # At top of file, add import:
  import re
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
  from utils import project_tmp_path

  def test_paths_are_tmp_path_scoped(tmp_path):
      """Canary: verify test infrastructure uses tmp_path-derived names."""
      project = tmp_path.name  # e.g. "test_paths_are0"
      p = project_tmp_path("last-test", project)
      # Verify the path encodes tmp_path.name, not a hardcoded constant
      assert tmp_path.name.replace("_", "-")[:6] in str(p) or re.sub(r'[^a-zA-Z0-9]', '-', tmp_path.name) in str(p)
  ```

  Run: `make test-unit` — must FAIL (hardcoded paths in existing tests are the problem, not this canary — but it documents the intended contract)

- [ ] **Step 2: Implement (GREEN)**

  Rewrite the two path-creating tests in `test_session_cleanup.py`:

  ```python
  # Add at top of file
  import re
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
  from utils import project_tmp_path


  def run_hook(cwd_name, stdin_data=None):
      hook = os.path.join(REPO_ROOT, "hooks", "session-cleanup.py")
      env = os.environ.copy()
      env["CLAUDE_CWD"] = f"/fake/path/{cwd_name}"
      if stdin_data is None:
          stdin_data = json.dumps({"stop_reason": "end_turn"})
      return subprocess.run(
          [sys.executable, hook],
          input=stdin_data,
          capture_output=True,
          text=True,
          env=env,
      )


  class TestSessionCleanupDeletes:
      def test_deletes_project_scoped_tmp_files(self, tmp_path):
          project = tmp_path.name  # unique per test invocation
          tmp1 = project_tmp_path("last-test", project)
          tmp2 = project_tmp_path("edit-count", project)
          tmp1.write_text("x")
          tmp2.write_text("1")
          assert tmp1.exists()
          assert tmp2.exists()

          r = run_hook(project)
          assert r.returncode == 0
          assert not tmp1.exists(), f"{tmp1} should have been deleted"
          assert not tmp2.exists(), f"{tmp2} should have been deleted"

      def test_does_not_delete_other_project_files(self, tmp_path):
          our_project = tmp_path.name
          # "other" project gets a distinct name derived from tmp_path to stay isolated
          other_project = tmp_path.name + "-other"
          other_file = project_tmp_path("last-test", other_project)
          other_file.write_text("keep me")

          r = run_hook(our_project)
          assert r.returncode == 0
          assert other_file.exists(), "File from other project must not be deleted"
          # cleanup
          other_file.unlink(missing_ok=True)

      def test_exits_cleanly_when_no_matching_files(self, tmp_path):
          r = run_hook(tmp_path.name + "-nonexistent-xyz")
          assert r.returncode == 0
          assert r.stdout.strip() == ""
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the `test_paths_are_tmp_path_scoped` canary test added in Step 1 (it was a scaffolding check, not a permanent test). Confirm the import of `project_tmp_path` is at the top of the file alongside existing imports.

  Run: `make test-unit` — still PASS

---

## Task 2: Migrate test_hooks_wip_checkpoint.py counter_path() to project_tmp_path()

**Acceptance Criteria:**
- `counter_path()` local helper is replaced by direct use of `project_tmp_path("edit-count", name)`
- `_cleanup_counter` fixture in both `TestWipCheckpointCounter` and `TestWipCheckpointRoadmapEdgeCases` calls `project_tmp_path("edit-count", tmp_path.name)`
- `test_counter_increments_each_call` reads the counter at `project_tmp_path("edit-count", tmp_path.name)` — matching what the hook writes when `CLAUDE_CWD` points to `tmp_path`
- `test_no_crash_on_fifth_edit_with_bad_url` seeds the counter at the correct path

**Files:**
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a path-contract canary that exposes the mismatch:

  ```python
  # In TestWipCheckpointCounter, add:
  def test_counter_path_matches_hook_path(self, tmp_path):
      """Counter path used in tests must match what the hook writes."""
      from utils import project_tmp_path as util_path
      hook_path = util_path("edit-count", tmp_path.name)
      local_path = counter_path(tmp_path.name)
      # This will FAIL if counter_path() uses different logic than project_tmp_path()
      assert hook_path == local_path
  ```

  Run: `make test-unit` — this test will PASS if the logic already matches, but the overall migration goal is to remove the duplication entirely; the canary documents the contract.

- [ ] **Step 2: Implement (GREEN)**

  Replace the `counter_path()` and `reset_counter()` helpers with `project_tmp_path`:

  ```python
  # Remove these helpers entirely:
  # def counter_path(project_name: str) -> Path: ...
  # def reset_counter(project_name: str): ...

  # Add import at top of file (alongside existing sys.path.insert for HOOK):
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
  from utils import project_tmp_path

  # Update _cleanup_counter in TestWipCheckpointCounter:
  @pytest.fixture(autouse=True)
  def _cleanup_counter(self, tmp_path):
      yield
      p = project_tmp_path("edit-count", tmp_path.name)
      p.unlink(missing_ok=True)

  # Update test_counter_increments_each_call:
  def test_counter_increments_each_call(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      for _ in range(3):
          run_hook(tmp_cwd=cwd, env_overrides={
              "ZIE_MEMORY_API_KEY": "fake-key",
              "ZIE_MEMORY_API_URL": "https://localhost:19999",
          })
      counter = project_tmp_path("edit-count", tmp_path.name)
      assert counter.exists()
      assert int(counter.read_text().strip()) == 3

  # Update test_no_crash_on_fifth_edit_with_bad_url:
  def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      project_tmp_path("edit-count", tmp_path.name).write_text("4")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "http://localhost:19999",
      })
      assert r.returncode == 0

  # Update _cleanup_counter in TestWipCheckpointRoadmapEdgeCases identically:
  @pytest.fixture(autouse=True)
  def _cleanup_counter(self, tmp_path):
      yield
      p = project_tmp_path("edit-count", tmp_path.name)
      p.unlink(missing_ok=True)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the `test_counter_path_matches_hook_path` canary added in Step 1. Verify there are no remaining references to the old `counter_path()` or `reset_counter()` functions anywhere in the file.

  Run: `make test-unit` — still PASS
