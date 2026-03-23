---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-safe-project-dedup.md
spec: specs/2026-03-24-audit-safe-project-dedup-design.md
---

# Safe Project Sanitization Deduplication — Implementation Plan

**Goal:** Extract `safe_project_name()` from `utils.project_tmp_path()` and replace the inlined `re.sub` copy in `session-cleanup.py` so there is a single authoritative sanitization rule.
**Architecture:** A new public helper `safe_project_name(project: str) -> str` lives in `utils.py` and is called by both `project_tmp_path()` and `session-cleanup.py`. The hook drops its own `import re` dependency for the sanitization pattern, importing `safe_project_name` from `utils` instead. No change to sanitization semantics.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `safe_project_name()` helper; refactor `project_tmp_path()` to call it |
| Modify | `hooks/session-cleanup.py` | Remove inline `re.sub`; import and call `safe_project_name()` |
| Modify | `tests/unit/test_utils.py` | Add tests for `safe_project_name()` |
| Modify | `tests/unit/test_session_cleanup.py` | Add test asserting dedup behaviour via shared helper |

## Task 1: Extract `safe_project_name` and update `session-cleanup.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `utils.safe_project_name("my project!")` returns `"my-project-"` (same rule as current inline)
- `utils.safe_project_name("")` returns `""`
- `project_tmp_path()` produces identical output before and after refactor (existing tests pass)
- `session-cleanup.py` no longer contains a bare `re.sub(r'[^a-zA-Z0-9]'` expression
- All existing `TestProjectTmpPath` and `TestSessionCleanup*` tests continue to pass

**Files:**
- Modify: `hooks/utils.py`
- Modify: `hooks/session-cleanup.py`
- Modify: `tests/unit/test_utils.py`
- Modify: `tests/unit/test_session_cleanup.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_utils.py — add inside the file after TestProjectTmpPath class

  class TestSafeProjectName:
      def test_alphanumeric_unchanged(self):
          from utils import safe_project_name
          assert safe_project_name("myproject") == "myproject"

      def test_spaces_replaced_with_dash(self):
          from utils import safe_project_name
          assert safe_project_name("my project") == "my-project"

      def test_special_chars_replaced(self):
          from utils import safe_project_name
          assert safe_project_name("my project!") == "my-project-"

      def test_empty_string_returns_empty(self):
          from utils import safe_project_name
          assert safe_project_name("") == ""

      def test_already_safe_no_change(self):
          from utils import safe_project_name
          assert safe_project_name("zie-framework") == "zie-framework"

      def test_project_tmp_path_uses_safe_project_name(self):
          """project_tmp_path output must equal /tmp/zie-{safe_project_name(p)}-{name}."""
          from utils import safe_project_name, project_tmp_path
          from pathlib import Path
          p = "my project!"
          expected = Path(f"/tmp/zie-{safe_project_name(p)}-last-test")
          assert project_tmp_path("last-test", p) == expected

  # tests/unit/test_session_cleanup.py — add inside TestSessionCleanupDeletes class

      def test_cleanup_uses_same_rule_as_utils(self):
          """Glob pattern used by session-cleanup must match safe_project_name() output."""
          import sys, os
          sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
          from utils import safe_project_name
          project = "my project!"
          safe = safe_project_name(project)
          tmp1 = Path(f"/tmp/zie-{safe}-last-test")
          tmp1.write_text("x")
          r = run_hook(project)
          assert r.returncode == 0
          assert not tmp1.exists(), f"{tmp1} should have been deleted"
  ```
  Run: `make test-unit` — must FAIL (`safe_project_name` does not exist yet)

- [ ] **Step 2: Implement (GREEN)**
  ```python
  # hooks/utils.py — replace project_tmp_path with the following two functions

  def safe_project_name(project: str) -> str:
      """Sanitize a project name to alphanumeric-and-dash only.

      Single source of truth for the sanitization rule used in tmp paths and
      session-cleanup globs. Replaces any non-alphanumeric character with '-'.
      """
      return re.sub(r'[^a-zA-Z0-9]', '-', project)


  def project_tmp_path(name: str, project: str) -> Path:
      """Return a project-scoped /tmp path to prevent cross-project collisions.

      Example: project_tmp_path("last-test", "my-project") -> Path("/tmp/zie-my-project-last-test")
      """
      return Path(f"/tmp/zie-{safe_project_name(project)}-{name}")
  ```

  ```python
  # hooks/session-cleanup.py — replace lines 5-16 (re import + safe_project derivation)
  # Remove:  import re
  # Remove:  safe_project = re.sub(r'[^a-zA-Z0-9]', '-', cwd.name)
  # Add import from utils, add safe_project_name call

  #!/usr/bin/env python3
  """Stop hook — remove project-scoped /tmp files on session end."""
  import json
  import os
  import sys
  from pathlib import Path

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import safe_project_name

  try:
      event = json.loads(sys.stdin.read())
  except Exception:
      # intentional — malformed event must not crash hook
      sys.exit(0)

  cwd = Path(os.environ.get("CLAUDE_CWD", os.getcwd()))
  safe_project = safe_project_name(cwd.name)

  for tmp_file in Path("/tmp").glob(f"zie-{safe_project}-*"):
      try:
          tmp_file.unlink()
      except Exception as e:
          print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
  ```
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Verify `import re` is removed from `session-cleanup.py` (no longer needed).
  Confirm `test_spaces_replaced` in `TestProjectTmpPath` still passes (uses `safe_project_name` internally now).
  Run: `make test-unit` — still PASS

---
*Commit: `git add hooks/utils.py hooks/session-cleanup.py tests/unit/test_utils.py tests/unit/test_session_cleanup.py && git commit -m "fix: extract safe_project_name helper, dedup sanitization logic"`*
