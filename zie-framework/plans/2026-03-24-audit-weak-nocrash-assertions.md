---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-weak-nocrash-assertions.md
spec: specs/2026-03-24-audit-weak-nocrash-assertions-design.md
---

# Strengthen No-Crash Assertions to Verify Hook Side-Effects — Implementation Plan

**Goal:** Add side-effect assertions to four tests in `test_hooks_wip_checkpoint.py` that currently only assert `returncode == 0`, so a hook that silently exits early would no longer pass those tests.
**Architecture:** Pure test augmentation — no hook source changes. Each target test gets a second assertion that checks the observable side-effect of the code path under test: counter file written with expected value (tests 1-3) or counter file advanced to `"5"` plus stderr containing the connection error string (test 4). `counter_path()` (or `project_tmp_path()` after audit-tests-tmp-path is applied) is used to locate the counter file.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_wip_checkpoint.py` | Add side-effect assertions to 4 existing test methods |
| Read-only | `hooks/wip-checkpoint.py` | Verify counter increment and exit-order logic — no changes |

---

## Task 1: Add side-effect assertions to TestWipCheckpointRoadmapEdgeCases

**Acceptance Criteria:**
- `test_missing_roadmap_no_crash` asserts counter file exists and contains `"1"` after the hook runs
- `test_empty_now_section_no_crash` asserts counter file exists and contains `"1"` after the hook runs
- `test_malformed_now_items_graceful_skip` asserts counter file exists and contains `"1"` after the hook runs
- All three tests still pass (the assertions reflect real hook behaviour)
- Tests in `TestWipCheckpointGuardrails` are NOT modified (silent-exit paths are correct as-is)

**Files:**
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  The "RED" step here is removing the existing weak assertion and observing that the stronger assertion is not yet present. Write the tests with the stronger assertion only — they will PASS if the hook already behaves correctly, confirming the assertions are valid. To make Step 1 strictly RED, first add a deliberately wrong assertion to confirm the test can fail:

  ```python
  # Temporarily replace the body of test_missing_roadmap_no_crash to demonstrate failure:
  def test_missing_roadmap_no_crash(self, tmp_path):
      cwd = make_cwd(tmp_path)
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      # RED: this assertion should fail because the file does not exist yet at THIS point
      # (only used to verify test infrastructure can catch a missing counter)
      counter = counter_path(tmp_path.name)
      assert counter.exists(), "RED: counter file must exist — proves hook reached counter logic"
      assert counter.read_text().strip() == "WRONG_VALUE"  # intentionally wrong
  ```

  Run: `make test-unit` — must FAIL on the `"WRONG_VALUE"` assertion

- [ ] **Step 2: Implement (GREEN)**

  Replace all three test bodies with the correct strengthened assertions:

  ```python
  def test_missing_roadmap_no_crash(self, tmp_path):
      # zie-framework/ dir exists but ROADMAP.md absent
      cwd = make_cwd(tmp_path)  # no roadmap arg
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      counter = counter_path(tmp_path.name)
      assert counter.exists(), "hook must write counter even when roadmap is absent"
      assert counter.read_text().strip() == "1"

  def test_empty_now_section_no_crash(self, tmp_path):
      roadmap = "## Now\n\n## Ready\n- [ ] Some item\n"
      cwd = make_cwd(tmp_path, roadmap=roadmap)
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      counter = counter_path(tmp_path.name)
      assert counter.exists(), "hook must write counter even when Now section is empty"
      assert counter.read_text().strip() == "1"

  def test_malformed_now_items_graceful_skip(self, tmp_path):
      roadmap = "## Now\nnot a list item\nanother line\n"
      cwd = make_cwd(tmp_path, roadmap=roadmap)
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",
      })
      assert r.returncode == 0
      counter = counter_path(tmp_path.name)
      assert counter.exists(), "hook must write counter even with malformed Now items"
      assert counter.read_text().strip() == "1"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm that `TestWipCheckpointGuardrails` tests (`test_no_action_without_api_key`, `test_no_action_for_non_edit_tool`) remain unchanged — they are intentional silent-exit paths and must NOT get counter assertions.

  Run: `make test-unit` — still PASS

---

## Task 2: Strengthen test_no_crash_on_fifth_edit_with_bad_url

**Acceptance Criteria:**
- `test_no_crash_on_fifth_edit_with_bad_url` asserts counter file now contains `"5"` (incremented from seeded `"4"`)
- Test also asserts `r.stderr` is non-empty (hook printed the connection error)
- Test still passes (hook does increment and print error on bad URL)

**Files:**
- Modify: `tests/unit/test_hooks_wip_checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add the stronger assertions with an intentionally wrong expected value first:

  ```python
  def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      counter_path(tmp_path.name).write_text("4")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "http://localhost:19999",
      })
      assert r.returncode == 0
      # RED: wrong expected value to confirm test can fail
      assert counter_path(tmp_path.name).read_text().strip() == "999"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  ```python
  def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      counter_path(tmp_path.name).write_text("4")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "http://localhost:19999",
      })
      assert r.returncode == 0  # graceful failure — never crash
      # Counter must advance from 4 to 5 — proves hook reached the network attempt
      assert counter_path(tmp_path.name).read_text().strip() == "5"
      # Hook must print a non-empty error to stderr (the connection refused message)
      assert r.stderr.strip() != "", "hook must report network error to stderr"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No structural cleanup needed. Verify the test uses `http://` (not `https://`) — this is intentional: the http guard exits early at line 27 of `wip-checkpoint.py`. Actually, re-check: the guard is `if not api_url.startswith("https://")` which exits at line 26-27. Since the URL is `http://`, the hook exits before reaching the counter. This means the counter will NOT be incremented and the assertion in Task 2 Step 2 will FAIL.

  Investigation needed: review hook exit order. The guard `if not api_url.startswith("https://")` on line 26-27 exits BEFORE the counter logic on lines 35-44. So `http://` URL causes exit before counter write — counter stays at `"4"`, not `"5"`. The correct fix: use `https://localhost:19999` (like the other tests) so the hook reaches the counter. The counter gets written to `"5"`, then the network call fails (connection refused), printing to stderr.

  Corrected final implementation:

  ```python
  def test_no_crash_on_fifth_edit_with_bad_url(self, tmp_path):
      cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
      counter_path(tmp_path.name).write_text("4")
      r = run_hook(tmp_cwd=cwd, env_overrides={
          "ZIE_MEMORY_API_KEY": "fake-key",
          "ZIE_MEMORY_API_URL": "https://localhost:19999",  # https to pass guard, bad host to fail network
      })
      assert r.returncode == 0
      assert counter_path(tmp_path.name).read_text().strip() == "5"
      assert r.stderr.strip() != "", "hook must report network error to stderr"
  ```

  Run: `make test-unit` — still PASS
