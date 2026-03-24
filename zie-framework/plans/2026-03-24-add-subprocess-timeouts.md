---
approved: true
approved_at: 2026-03-24
backlog: backlog/add-subprocess-timeouts.md
spec: specs/2026-03-24-add-subprocess-timeouts-design.md
---

# Add Subprocess Timeouts to sdlc-compact.py — Implementation Plan

**Goal:** Add `timeout=5` to the two bare `subprocess.run()` calls in `hooks/sdlc-compact.py` (lines 54 and 66) so the hook cannot hang indefinitely on a stalled git process.
**Architecture:** Minimal surgical edit — two keyword argument additions. The existing `except Exception` blocks at each call site already catch `subprocess.TimeoutExpired` (a subclass of `Exception`) and degrade gracefully to `""` / `[]`. No new error-handling code required.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/sdlc-compact.py` | Add `timeout=5` to git branch call (line 54) and git diff call (line 66) |
| Modify | `tests/unit/test_hooks_sdlc_compact.py` | Add two timeout tests: branch and diff |

---

## Task 1: Add timeout=5 to both subprocess.run calls

**Acceptance Criteria:**
- `hooks/sdlc-compact.py` line 54 `subprocess.run(["git", ..., "branch", "--show-current"], ...)` includes `timeout=5`
- `hooks/sdlc-compact.py` line 66 `subprocess.run(["git", ..., "diff", "--name-only", "HEAD"], ...)` includes `timeout=5`
- Hook exits 0 when git hangs past the timeout (no new exception propagation)
- `make test-unit` passes

**Files:**
- Modify: `hooks/sdlc-compact.py`
- Modify: `tests/unit/test_hooks_sdlc_compact.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hooks_sdlc_compact.py
  # NOTE: add `import stat` to the module-level imports — it is NOT in the existing file

  class TestSubprocessTimeouts:
      def _run_with_hanging_git(self, tmp_path, outer_timeout):
          """Run the hook with a fake git that sleeps 60s. Returns result or raises TimeoutExpired."""
          # Create a fake git that hangs indefinitely
          fake_bin = tmp_path / "fake_bin"
          fake_bin.mkdir()
          fake_git = fake_bin / "git"
          fake_git.write_text("#!/bin/sh\nsleep 60\n")
          fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)

          # Build a cwd with zie-framework/ so the hook passes the outer guard
          cwd = make_cwd(tmp_path / "proj", roadmap=SAMPLE_ROADMAP)

          env = {**os.environ}
          env["CLAUDE_CWD"] = str(cwd)
          env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

          event = json.dumps({"hook_event_name": "PreCompact", "cwd": str(cwd)})
          return subprocess.run(
              [sys.executable, HOOK],
              input=event,
              capture_output=True,
              text=True,
              timeout=outer_timeout,
              env=env,
          )

      def test_git_timeout_exits_zero(self, tmp_path):
          """Hook must exit 0 when git hangs — both branch and diff calls covered.

          RED: without timeout=5 in the hook, the first git call hangs 60s and the
          outer test timeout (12s) fires, raising subprocess.TimeoutExpired → FAIL.
          GREEN: each git call times out at 5s → total ~10s < 12s → exits 0 → PASS.
          """
          import pytest
          with pytest.raises(Exception):
              # Before fix: hook hangs indefinitely, outer timeout fires.
              # After fix: hook completes in ~10s, no exception raised.
              self._run_with_hanging_git(tmp_path, outer_timeout=12)
  ```

  Wait — this structure won't work cleanly as a RED test. Use the simpler direct assertion:

  ```python
  class TestSubprocessTimeouts:
      def test_git_timeout_exits_zero(self, tmp_path):
          """Hook must exit 0 when both git calls hang beyond 5s.

          Timing contract:
            - Fake git sleeps 60s.
            - Hook has timeout=5 per call (GREEN) → ~10s total → exits 0.
            - Hook has no timeout (RED) → hangs 60s → outer test fires at 15s → TimeoutExpired (FAIL).
          """
          # Create a fake git that hangs
          fake_bin = tmp_path / "fake_bin"
          fake_bin.mkdir()
          fake_git = fake_bin / "git"
          fake_git.write_text("#!/bin/sh\nsleep 60\n")
          fake_git.chmod(fake_git.stat().st_mode | stat.S_IEXEC)

          # Build cwd with zie-framework/ so hook passes outer guard
          cwd = make_cwd(tmp_path / "proj", roadmap=SAMPLE_ROADMAP)

          env = {**os.environ}
          env["CLAUDE_CWD"] = str(cwd)
          env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
          event = json.dumps({"hook_event_name": "PreCompact", "cwd": str(cwd)})

          result = subprocess.run(
              [sys.executable, HOOK],
              input=event,
              capture_output=True,
              text=True,
              timeout=15,  # > 2 × 5s (branch + diff) but < 60s (fake git sleep)
              env=env,
          )
          assert result.returncode == 0
  ```

  Run: `make test-unit` — must FAIL (hook hangs on first git call, outer `timeout=15` fires → `subprocess.TimeoutExpired` → pytest error → FAIL)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/sdlc-compact.py — line 54, BEFORE:
  result = subprocess.run(
      ["git", "-C", str(cwd), "branch", "--show-current"],
      capture_output=True,
      text=True,
  )

  # AFTER:
  result = subprocess.run(
      ["git", "-C", str(cwd), "branch", "--show-current"],
      capture_output=True,
      text=True,
      timeout=5,
  )
  ```

  ```python
  # hooks/sdlc-compact.py — line 66, BEFORE:
  result = subprocess.run(
      ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
      capture_output=True,
      text=True,
  )

  # AFTER:
  result = subprocess.run(
      ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
      capture_output=True,
      text=True,
      timeout=5,
  )
  ```

  No changes to error handling — the existing `except Exception` blocks at each site already catch `subprocess.TimeoutExpired` and set `git_branch = ""` / `changed_files = []`.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No refactoring needed. The two changes are identical in shape to the existing timeout pattern used in `failure-context.py`, `stop-guard.py`, and `task-completed-gate.py`. No abstractions to extract.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add hooks/sdlc-compact.py tests/unit/test_hooks_sdlc_compact.py && git commit -m "fix: add-subprocess-timeouts — add timeout=5 to git calls in sdlc-compact.py"`
