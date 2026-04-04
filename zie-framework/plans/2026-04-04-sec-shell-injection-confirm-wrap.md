---
approved: true
approved_at: 2026-04-04
backlog: backlog/sec-shell-injection-confirm-wrap.md
---

# sec-shell-injection-confirm-wrap — Implementation Plan

**Goal:** Prevent shell injection via unquoted redirect/pipe metacharacters in the confirm-wrap compound statement by extending the safety guard regex in `hooks/safety-check.py`.
**Architecture:** One-line regex extension in `_DANGEROUS_COMPOUND_RE` to add `>`, `<`, `|`, and `\n` as rejected characters. New unit test file covers the four new rejected cases and confirms safe commands still pass the guard.
**Tech Stack:** Python 3.x, pytest, re (stdlib)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/safety-check.py` | Extend `_DANGEROUS_COMPOUND_RE` character class |
| Create | `tests/unit/test_safety_check_confirm_wrap.py` | Unit tests for guard function and confirm-wrap path |

---

## Task 1: Extend `_DANGEROUS_COMPOUND_RE` to reject `>`, `<`, `|`, `\n`

**Acceptance Criteria:**
- `_is_safe_for_confirmation_wrapper("rm -rf ./foo > /etc/passwd")` returns `False`
- `_is_safe_for_confirmation_wrapper("rm -rf ./foo < /dev/urandom")` returns `False`
- `_is_safe_for_confirmation_wrapper("rm -rf ./foo | tee /etc/passwd")` returns `False`
- `_is_safe_for_confirmation_wrapper("rm -rf ./foo\necho pwned")` returns `False`
- `_is_safe_for_confirmation_wrapper("rm -rf ./foo")` returns `True` (safe, no change)

**Files:**
- Modify: `hooks/safety-check.py`
- Create: `tests/unit/test_safety_check_confirm_wrap.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_safety_check_confirm_wrap.py` with:

  ```python
  """Unit tests for _is_safe_for_confirmation_wrapper in safety-check.py."""
  import re
  import sys
  from pathlib import Path

  # We test the guard function in isolation by re-defining the regex
  # and guard function as they appear in safety-check.py.
  # This tests the CURRENT (buggy) regex state — until Task 1 Step 2 extends it.

  # Current regex (BEFORE the fix) — missing >, <, |, \n
  _DANGEROUS_COMPOUND_RE_BUGGY = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}])')

  def _is_safe_for_confirmation_wrapper_buggy(command: str) -> bool:
      return not _DANGEROUS_COMPOUND_RE_BUGGY.search(command)

  # After the fix, the regex will be:
  # _DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')

  class TestIsSafeForConfirmationWrapper:
      """Test the guard function under the FIXED regex."""

      def test_stdout_redirect_rejected(self):
          """FIXED: > (stdout redirect) must be rejected."""
          # This test FAILS with the buggy regex (current state)
          # It will PASS after Task 1 Step 2 extends the regex
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo > /etc/passwd") is False

      def test_stdin_redirect_rejected(self):
          """FIXED: < (stdin redirect) must be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo < /dev/urandom") is False

      def test_pipe_rejected(self):
          """FIXED: | (pipe) must be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo | tee /etc/passwd") is False

      def test_newline_rejected(self):
          """FIXED: literal newline must be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo\necho pwned") is False

      def test_safe_command_passes(self):
          """FIXED: plain safe command must still pass."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo") is True

      def test_safe_command_with_path_passes(self):
          """FIXED: path-only rm commands must still pass."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./build") is True

      def test_semicolon_still_rejected(self):
          """FIXED: ; (semicolon) must still be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo; echo pwned") is False

      def test_double_ampersand_still_rejected(self):
          """FIXED: && must still be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo && echo pwned") is False

      def test_double_pipe_still_rejected(self):
          """FIXED: || must still be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./foo || echo pwned") is False

      def test_backtick_still_rejected(self):
          """FIXED: ` (backtick) must still be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./`echo foo`") is False

      def test_subshell_still_rejected(self):
          """FIXED: $() must still be rejected."""
          _DANGEROUS_COMPOUND_RE_FIXED = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
          fixed_guard = lambda cmd: not _DANGEROUS_COMPOUND_RE_FIXED.search(cmd)
          assert fixed_guard("rm -rf ./$(echo foo)") is False
  ```

  Run: `make test-unit` — must **FAIL** (all fixed-guard tests fail because the actual code still has the buggy regex)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/safety-check.py`, change line 32:

  **Before:**
  ```python
  _DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}])')
  ```

  **After:**
  ```python
  _DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}>|<\n])')
  ```

  Characters added to the character class: `>`, `<`, `|`, `\n`

  Note: `|` already appears in the alternation as `\|\|` (double-pipe) but NOT as a single pipe. The single `|` in the character class is a literal pipe character inside `[...]` — no escaping needed.

  Run: `make test-unit` — must **PASS** (the fixed regex now makes all tests pass)

- [ ] **Step 3: Refactor**

  No structural refactoring required. Verify the regex reads cleanly — the character class `[{}>|<\n]` groups all single-char metacharacters together, which is idiomatic.

  Run: `make test-unit` — still PASS

---

## Task 2: Refactor tests to use the actual hook function (GREEN → final form)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `tests/unit/test_safety_check_confirm_wrap.py` tests the actual `_is_safe_for_confirmation_wrapper` from `hooks/safety-check.py`
- All tests pass under `make test-unit` with the fixed regex
- Tests import and call the real guard function (not a local copy)

**Files:**
- Modify: `tests/unit/test_safety_check_confirm_wrap.py`

- [ ] **Step 1: Import and test the actual function (GREEN)**

  Replace Task 1's local regex copies with direct imports from `hooks/safety-check.py`:

  ```python
  """Unit tests for _is_safe_for_confirmation_wrapper in safety-check.py."""
  import re
  import sys
  from pathlib import Path

  # Add hooks/ to path so we can import the actual guard function
  HOOKS_DIR = str(Path(__file__).parent.parent.parent / "hooks")
  if HOOKS_DIR not in sys.path:
      sys.path.insert(0, HOOKS_DIR)

  # Stub out side-effectful imports so we can load safety-check.py's module-level code
  sys.modules.setdefault("utils_safety", __import__("types").ModuleType("utils_safety"))
  sys.modules.setdefault("utils_event", __import__("types").ModuleType("utils_event"))
  sys.modules.setdefault("utils_io", __import__("types").ModuleType("utils_io"))
  sys.modules.setdefault("utils_config", __import__("types").ModuleType("utils_config"))

  # Now we can import the actual guard function
  from safety_check import _is_safe_for_confirmation_wrapper

  class TestIsSafeForConfirmationWrapper:
      """Test the guard function with the FIXED regex in hooks/safety-check.py."""

      def test_stdout_redirect_rejected(self):
          """> (stdout redirect) must be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo > /etc/passwd") is False

      def test_stdin_redirect_rejected(self):
          """< (stdin redirect) must be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo < /dev/urandom") is False

      def test_pipe_rejected(self):
          """| (pipe) must be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo | tee /etc/passwd") is False

      def test_newline_rejected(self):
          """Literal newline must be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo\necho pwned") is False

      def test_safe_command_passes(self):
          """Plain safe command must still pass."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo") is True

      def test_safe_command_with_path_passes(self):
          """Path-only rm commands must still pass."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./build") is True

      # Verify previously-blocked chars still blocked
      def test_semicolon_still_rejected(self):
          """; (semicolon) must still be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo; echo pwned") is False

      def test_double_ampersand_still_rejected(self):
          """&& must still be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo && echo pwned") is False

      def test_double_pipe_still_rejected(self):
          """|| must still be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./foo || echo pwned") is False

      def test_backtick_still_rejected(self):
          """` (backtick) must still be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./`echo foo`") is False

      def test_subshell_still_rejected(self):
          """$() must still be rejected."""
          assert _is_safe_for_confirmation_wrapper("rm -rf ./$(echo foo)") is False
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 2: Refactor**

  Verify test docstrings are one-liners and clearly describe what is being rejected. No structural changes needed.

  Run: `make test-unit` — still PASS

---

## Verification

After both tasks complete:

```bash
make test-unit    # all new tests pass
make lint         # no ruff violations
```

Expected output: all tests green, zero lint errors.
