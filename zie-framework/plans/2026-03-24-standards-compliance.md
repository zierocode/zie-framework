---
approved: true
approved_at: 2026-03-24
backlog: backlog/standards-compliance.md
spec: specs/2026-03-24-standards-compliance-design.md
---

# Standards: Compliance and Consistency Gaps — Implementation Plan

**Goal:** Close four small compliance gaps: version consistency test, log prefix standardization, integration test documentation, and notification-log.py project name sanitization.
**Architecture:** Pure targeted edits — one new test function, two one-line hook fixes, two documentation additions, one import + call-site fix. One new test file (`tests/unit/test_hook_log_prefix.py`) for Tasks 2, 3, and 4.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_versioning_gate.py` | Add `test_version_files_match()` |
| Modify | `hooks/auto-test.py` | Fix log prefix at line 83 |
| Modify | `hooks/session-resume.py` | Fix log prefix at line 26 |
| Modify | `CLAUDE.md` | Document integration test exclusion in Development Commands |
| Modify | `Makefile` | Add comment above `test-unit` target |
| Modify | `hooks/notification-log.py` | Add `safe_project_name` to import; use it at line 65 |
| Create | `tests/unit/test_hook_log_prefix.py` | Enforce [zie-framework] log prefix, integration test docs assertion, notification-log safe_project_name assertion |

---

## Task 1: Version consistency test

**Acceptance Criteria:**
- `test_version_files_match()` exists in `tests/unit/test_versioning_gate.py`
- Test reads `VERSION` and `.claude-plugin/plugin.json` via `Path(__file__).parents[2]` (repo root)
- Test passes when both files contain the same version string
- Test fails with a clear message (including `make bump` remediation) when they diverge
- All 5 existing tests remain unchanged and passing

**Files:**
- Modify: `tests/unit/test_versioning_gate.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  The test itself IS the deliverable. Because `VERSION` and `plugin.json` currently both contain `1.8.0`, the test will PASS as soon as it is added — there is no prior "failing" state for this case. The RED phase is defined as: run `make test-unit` before adding the test, observe that `test_version_files_match` does not exist (test collection will not include it). This documents intent coverage gap, which is the defect being fixed.

  Run: `make test-unit` — confirm `test_version_files_match` is absent from output

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # Append to tests/unit/test_versioning_gate.py, inside class TestVersioningGate
  import json
  # (json is stdlib — add import at top of file alongside existing imports)

  ROOT = Path(__file__).parents[2]

  def test_version_files_match(self):
      version_file = (ROOT / "VERSION").read_text().strip()
      plugin_json = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
      assert version_file == plugin_json["version"], (
          f"VERSION file ({version_file}) does not match "
          f"plugin.json version ({plugin_json['version']}). "
          f"Run 'make bump NEW={version_file}' to sync them."
      )
  ```

  Note: `ROOT = Path(__file__).parents[2]` resolves as `tests/unit/` → `tests/` → repo root. `Path` is already imported at the top of the file. Add `import json` to the existing imports.

  Run: `make test-unit` — must PASS (all 6 tests green)

---

- [ ] **Step 3: Refactor**

  No structural changes needed. Verify the test name matches the spec exactly: `test_version_files_match`. Confirm the error message includes `make bump` as remediation hint.

  Run: `make test-unit` — still PASS

---

## Task 2: Log prefix standardization

**Acceptance Criteria:**
- `hooks/auto-test.py` line 83: `[zie] warning:` replaced with `[zie-framework] auto-test:`
- `hooks/session-resume.py` line 26: `[zie] warning:` replaced with `[zie-framework] session-resume:`
- No other behavior change — log still goes to `sys.stderr`, exits 0
- `make test-unit` still passes (no test changes needed for this fix)

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `hooks/session-resume.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  The standard log prefix `[zie-framework]` is the convention enforced by code review and hook convention docs. Write a grep-based test to lock it in:

  ```python
  # Append to tests/unit/ — create tests/unit/test_hook_log_prefix.py

  """Ensure all hooks use the [zie-framework] log prefix convention."""
  import re
  from pathlib import Path

  HOOKS_DIR = Path(__file__).parents[2] / "hooks"
  BAD_PREFIX = re.compile(r'\[zie\] warning:')


  class TestHookLogPrefix:
      def test_no_old_zie_warning_prefix_in_hooks(self):
          """No hook must use the deprecated '[zie] warning:' prefix."""
          violations = []
          for hook in sorted(HOOKS_DIR.glob("*.py")):
              text = hook.read_text()
              for lineno, line in enumerate(text.splitlines(), 1):
                  if BAD_PREFIX.search(line):
                      violations.append(f"{hook.name}:{lineno}: {line.strip()}")
          assert not violations, (
              "Found deprecated '[zie] warning:' prefix in hooks:\n"
              + "\n".join(violations)
              + "\nReplace with '[zie-framework] <hook-name>:'"
          )
  ```

  Run: `make test-unit` — must FAIL (`auto-test.py:83` and `session-resume.py:26` reported as violations)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/auto-test.py — line 83 (inside except block):
  # BEFORE:
  f"[zie] warning: .config unreadable ({e}), using defaults"
  # AFTER:
  f"[zie-framework] auto-test: .config unreadable ({e}), using defaults"
  ```

  ```python
  # hooks/session-resume.py — line 26 (inside except block):
  # BEFORE:
  f"[zie] warning: .config unreadable ({e}), using defaults"
  # AFTER:
  f"[zie-framework] session-resume: .config unreadable ({e}), using defaults"
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Scan remaining hooks for any other `[zie]` prefixes that should be standardized. If found, fix in this same step. This task's scope is the two known violations; record any extras as a follow-up backlog item if they exist.

  Run: `make test-unit` — still PASS

---

## Task 3: Integration test documentation

**Acceptance Criteria:**
- `CLAUDE.md` Development Commands section notes that `make test-unit` excludes ~63 integration tests and explains why
- `Makefile` has a comment above the `test-unit` target explaining the `-m "not integration"` exclusion
- No functional changes to any commands or tests

**Files:**
- Modify: `CLAUDE.md`
- Modify: `Makefile`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hook_log_prefix.py (or new file — either is fine)

  class TestDocumentation:
      def test_claude_md_documents_integration_test_exclusion(self):
          """CLAUDE.md must document that make test-unit excludes integration tests."""
          root = Path(__file__).parents[2]
          text = (root / "CLAUDE.md").read_text()
          assert "integration" in text.lower() and "test-unit" in text, (
              "CLAUDE.md must explain that make test-unit excludes integration tests"
          )

      def test_makefile_has_integration_exclusion_comment(self):
          """Makefile must have a comment explaining -m 'not integration' on test-unit."""
          root = Path(__file__).parents[2]
          text = (root / "Makefile").read_text()
          # The comment must appear near the test-unit target
          assert "integration" in text and "test-unit" in text, (
              "Makefile must have a comment documenting integration test exclusion"
          )
  ```

  Run: `make test-unit` — `test_claude_md_documents_integration_test_exclusion` will FAIL (CLAUDE.md currently has no integration test note in the commands section; Makefile test may pass due to existing content — verify both)

---

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, update the Development Commands section:

  ```markdown
  ## Development Commands

  ```bash
  make test-unit   # fast unit tests only — excludes ~63 integration tests
                   # integration tests require a live Claude session; run manually with make test-int
  make test-int    # run integration tests (subprocess hook events)
  make test        # full test suite (unit + integration + md lint)
  make bump NEW=x.y.z  # atomically bump VERSION + plugin.json
  make push m="msg"  # commit + push to dev
  ```
  ```

  In `Makefile`, add comment above `test-unit`:

  ```makefile
  # Note: -m "not integration" deselects ~63 integration tests that require a live
  # Claude session. Run 'make test-int' to execute them in a configured environment.
  test-unit: ## Fast unit tests (run constantly during /zie-build)
  	python3 -m pytest tests/ -x -q --tb=short --no-header -m "not integration"
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No structural changes needed. Verify the CLAUDE.md edit preserves the existing command descriptions accurately.

  Run: `make test-unit` — still PASS

---

## Task 4: notification-log.py project name fix

**Acceptance Criteria:**
- `hooks/notification-log.py` line 13 import includes `safe_project_name`
- `hooks/notification-log.py` line 65: `project = get_cwd().name` → `project = safe_project_name(get_cwd().name)`
- `make test-unit` still passes
- No behavior change for valid project names; sanitization now applied for names with special characters

**Files:**
- Modify: `hooks/notification-log.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_hook_log_prefix.py

  class TestNotificationLogProjectName:
      def test_notification_log_uses_safe_project_name(self):
          """notification-log.py must call safe_project_name() on cwd.name."""
          root = Path(__file__).parents[2]
          text = (root / "hooks" / "notification-log.py").read_text()
          assert "safe_project_name" in text, (
              "notification-log.py must import and use safe_project_name() "
              "for consistency with other hooks"
          )
  ```

  Run: `make test-unit` — must FAIL (`safe_project_name` not present in notification-log.py)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # hooks/notification-log.py — line 13:
  # BEFORE:
  from utils import get_cwd, project_tmp_path, read_event, safe_write_tmp
  # AFTER:
  from utils import get_cwd, project_tmp_path, read_event, safe_project_name, safe_write_tmp
  ```

  ```python
  # hooks/notification-log.py — line 65:
  # BEFORE:
  project = get_cwd().name
  # AFTER:
  project = safe_project_name(get_cwd().name)
  ```

  Note: `project_tmp_path()` already calls `safe_project_name()` internally, so this is a consistency fix only — no behavior change for normal project names.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Scan other hooks for any remaining raw `get_cwd().name` usages without `safe_project_name()`. If found, note as follow-up; this task's scope is notification-log.py only.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add tests/unit/test_versioning_gate.py tests/unit/test_hook_log_prefix.py hooks/auto-test.py hooks/session-resume.py hooks/notification-log.py CLAUDE.md Makefile && git commit -m "fix: standards-compliance — version test, log prefixes, integration test docs, safe_project_name"`
