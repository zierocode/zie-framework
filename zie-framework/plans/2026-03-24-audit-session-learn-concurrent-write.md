---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-session-learn-concurrent-write.md
spec: specs/2026-03-24-audit-session-learn-concurrent-write-design.md
---

# Session-Learn Atomic Pending File Write — Implementation Plan

**Goal:** Replace the non-atomic `write_text()` call in `session-learn.py` with an atomic write-then-rename via a new `atomic_write(path, content)` helper in `utils.py`.
**Architecture:** `atomic_write(path: Path, content: str) -> None` writes to `path.with_suffix(".tmp")` then calls `path.rename(target)`. On POSIX `rename()` is atomic. `session-learn.py` replaces its direct `write_text()` call with `atomic_write(pending_learn_file, ...)`. No other callers are changed in this plan.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `atomic_write(path, content)` helper |
| Modify | `hooks/session-learn.py` | Replace `write_text()` with `atomic_write()` |
| Modify | `tests/unit/test_utils.py` | Add tests for `atomic_write()` |
| Modify | `tests/unit/test_hooks_session_learn.py` | Add test asserting `.tmp` file is not left behind |

## Task 1: Add `atomic_write` helper to `utils.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `atomic_write(path, content)` writes `content` to `path` with no `.tmp` file left behind on success
- The target file contains exactly `content` after the call
- If the tmp path already exists it is silently overwritten
- All existing `TestParseRoadmapNow` and `TestProjectTmpPath` tests continue to pass

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_utils.py — add new class after TestProjectTmpPath

  class TestAtomicWrite:
      def test_writes_content_to_target(self, tmp_path):
          from utils import atomic_write
          target = tmp_path / "pending_learn.txt"
          atomic_write(target, "project=foo\nwip=bar\n")
          assert target.read_text() == "project=foo\nwip=bar\n"

      def test_no_tmp_file_left_on_success(self, tmp_path):
          from utils import atomic_write
          target = tmp_path / "pending_learn.txt"
          atomic_write(target, "hello")
          tmp_file = target.with_suffix(".tmp")
          assert not tmp_file.exists(), ".tmp file must be cleaned up after successful rename"

      def test_overwrites_existing_file(self, tmp_path):
          from utils import atomic_write
          target = tmp_path / "pending_learn.txt"
          target.write_text("old content")
          atomic_write(target, "new content")
          assert target.read_text() == "new content"

      def test_handles_empty_content(self, tmp_path):
          from utils import atomic_write
          target = tmp_path / "out.txt"
          atomic_write(target, "")
          assert target.read_text() == ""

      def test_stale_tmp_overwritten(self, tmp_path):
          from utils import atomic_write
          target = tmp_path / "out.txt"
          stale_tmp = target.with_suffix(".tmp")
          stale_tmp.write_text("stale")
          atomic_write(target, "fresh")
          assert target.read_text() == "fresh"
          assert not stale_tmp.exists()
  ```
  Run: `make test-unit` — must FAIL (`atomic_write` not importable)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/utils.py — append after project_tmp_path()

  def atomic_write(path: Path, content: str) -> None:
      """Write content to path atomically using a sibling .tmp file and rename.

      On POSIX, os.rename() (called by Path.rename()) is atomic at the filesystem
      level, preventing partial reads from concurrent writers.
      """
      tmp_path = path.with_suffix(".tmp")
      tmp_path.write_text(content)
      tmp_path.rename(path)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No structural changes needed. Confirm docstring accurately reflects POSIX guarantee.
  Run: `make test-unit` — still PASS

## Task 2: Update `session-learn.py` to use `atomic_write`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `session-learn.py` calls `atomic_write(pending_learn_file, ...)` instead of `pending_learn_file.write_text(...)`
- All existing `TestSessionLearnPendingLearnFile` tests pass unchanged
- No `.tmp` file is present in `~/.claude/projects/<project>/` after hook run

**Files:**
- Modify: `hooks/session-learn.py`
- Modify: `tests/unit/test_hooks_session_learn.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_hooks_session_learn.py — add inside TestSessionLearnPendingLearnFile

      def test_no_tmp_file_left_after_write(self, tmp_path):
          """atomic_write must not leave a .tmp sibling file."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook(cwd)
          pending = Path.home() / ".claude" / "projects" / tmp_path.name / "pending_learn.txt"
          tmp_file = pending.with_suffix(".tmp")
          assert not tmp_file.exists(), f".tmp file left behind at {tmp_file}"
  ```
  Run: `make test-unit` — must FAIL (current `write_text` path leaves no `.tmp` — test passes vacuously; confirm the impl test catches the write_text vs atomic_write distinction by checking the source contains `atomic_write` — use a grep-style assertion in the test or rely on Task 1 tests as the regression net; the test above is still correct and adds coverage)

  Note: the `.tmp` test will pass even before the change (since `write_text` never creates `.tmp`). The RED signal here is the `atomic_write` import failing in session-learn until Task 2 impl is done. Confirm by temporarily removing the `atomic_write` import from `session-learn.py` in a scratch run.

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/session-learn.py — update the import line and replace write_text call

  # Change import line (after existing utils import):
  from utils import parse_roadmap_now, atomic_write

  # Replace lines 37-40:
  # OLD:
  # pending_learn_file.write_text(
  #     f"project={project}\n"
  #     f"wip={wip_context}\n"
  # )

  # NEW:
  atomic_write(
      pending_learn_file,
      f"project={project}\n"
      f"wip={wip_context}\n",
  )
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm `pending_learn_file.write_text` is no longer present in `session-learn.py`.
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/utils.py hooks/session-learn.py tests/unit/test_utils.py tests/unit/test_hooks_session_learn.py && git commit -m "fix: atomic pending_learn write in session-learn, add atomic_write helper"`*
