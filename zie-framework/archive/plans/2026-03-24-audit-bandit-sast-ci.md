---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-bandit-sast-ci.md
spec: specs/2026-03-24-audit-bandit-sast-ci-design.md
---

# Bandit SAST in CI Pipeline — Implementation Plan

**Goal:** Run `bandit -r hooks/ -ll` on every commit via `make lint-bandit` wired into `make lint` and `.githooks/pre-commit`.
**Architecture:** New `lint-bandit` Make target calls `python3 -m bandit -r hooks/ -ll -q`. The existing `lint` target gains a dependency on `lint-bandit`. The pre-commit hook gets a guarded `make lint-bandit` step before the markdownlint block — guarded with `command -v bandit` so uninstalled contributors get a warning rather than a hard block. A smoke test asserts the current hooks directory passes bandit clean.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Add `lint-bandit` target; extend `lint` to depend on it |
| Modify | `.githooks/pre-commit` | Add `make lint-bandit` step with install guard |
| Create | `tests/unit/test_bandit_ci.py` | Smoke test: bandit exits 0 on hooks/ |

---

## Task 1: `lint-bandit` Make target

**Acceptance Criteria:**
- `make lint-bandit` runs `python3 -m bandit -r hooks/ -ll -q` and exits 0 when hooks are clean
- `make lint` calls `lint-bandit` as part of its chain
- `make help` shows the `lint-bandit` target description

**Files:**
- Modify: `Makefile`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Create tests/unit/test_bandit_ci.py

  """Smoke test: bandit must exit 0 on hooks/ at medium severity + confidence."""
  import subprocess
  import sys
  import os
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  HOOKS_DIR = str(REPO_ROOT / "hooks")


  class TestBanditSast:
      def test_bandit_is_importable(self):
          """bandit must be installed in the current environment."""
          result = subprocess.run(
              [sys.executable, "-m", "bandit", "--version"],
              capture_output=True,
              text=True,
          )
          assert result.returncode == 0, (
              "bandit is not installed — run: pip install bandit>=1.7\n"
              + result.stderr
          )

      def test_bandit_hooks_exits_clean(self):
          """hooks/ must have zero bandit findings at medium severity + medium confidence."""
          result = subprocess.run(
              [sys.executable, "-m", "bandit", "-r", HOOKS_DIR, "-ll", "-q"],
              capture_output=True,
              text=True,
              cwd=str(REPO_ROOT),
          )
          assert result.returncode == 0, (
              "bandit found issues in hooks/:\n"
              + result.stdout
              + result.stderr
          )

      def test_make_lint_bandit_target_exists(self):
          """Makefile must define a lint-bandit target."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          assert "lint-bandit:" in content, "lint-bandit target not found in Makefile"

      def test_make_lint_calls_lint_bandit(self):
          """The lint target must depend on or call lint-bandit."""
          makefile = REPO_ROOT / "Makefile"
          content = makefile.read_text()
          # Find the lint: line and check it references lint-bandit
          for line in content.splitlines():
              if line.startswith("lint:") or line.startswith("lint "):
                  assert "lint-bandit" in line, (
                      f"lint target does not call lint-bandit: {line!r}"
                  )
                  break
          else:
              raise AssertionError("lint target not found in Makefile")
  ```

  Run: `make test-unit` — must FAIL (`test_bandit_is_importable` may pass if bandit is installed; `test_make_lint_bandit_target_exists` and `test_make_lint_calls_lint_bandit` fail because the target does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```makefile
  # In Makefile, replace the existing lint target and add lint-bandit:

  # BEFORE:
  lint: ## Lint Python hooks
  	python3 -m py_compile hooks/*.py && echo "All hooks compile OK"

  # AFTER:
  lint: lint-bandit ## Lint Python hooks (syntax + SAST)
  	python3 -m py_compile hooks/*.py && echo "All hooks compile OK"

  lint-bandit: ## Run Bandit SAST on hooks/ (medium severity + confidence)
  	python3 -m bandit -r hooks/ -ll -q
  ```

  Install bandit if not present: `pip install "bandit>=1.7"`

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  If bandit flags any existing patterns in `hooks/` as medium-severity findings (e.g.
  `subprocess` with `shell=False` list-form args may still trigger B603/B607),
  add inline `# nosec B603` or `# nosec B607` comments with a one-line rationale.
  Example:

  ```python
  result = subprocess.run(cmd, ...)  # nosec B603 — cmd is a list, no shell expansion
  ```

  Do not suppress findings blindly — only add `# nosec` where the pattern is confirmed
  safe and Bandit's confidence is low.

  Run: `make test-unit` — still PASS
  Run: `make lint-bandit` — exits 0

---

## Task 2: Wire into `.githooks/pre-commit`

**Acceptance Criteria:**
- `git commit` runs `make lint-bandit` before the markdownlint check
- If `bandit` is not installed, pre-commit prints an install instruction and exits 0 (warn-only)
- If bandit finds issues, commit is blocked (exit 1)

**Files:**
- Modify: `.githooks/pre-commit`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_bandit_ci.py

  class TestPreCommitBanditIntegration:
      def test_pre_commit_calls_lint_bandit(self):
          """pre-commit hook script must contain a make lint-bandit invocation."""
          pre_commit = REPO_ROOT / ".githooks" / "pre-commit"
          content = pre_commit.read_text()
          assert "lint-bandit" in content, (
              "pre-commit hook does not call lint-bandit"
          )

      def test_pre_commit_has_bandit_install_guard(self):
          """pre-commit hook must guard bandit availability with command -v or equivalent."""
          pre_commit = REPO_ROOT / ".githooks" / "pre-commit"
          content = pre_commit.read_text()
          assert "bandit" in content, "pre-commit does not mention bandit"
          # Guard pattern: 'command -v bandit' or 'python3 -m bandit' with a check
          assert (
              "command -v bandit" in content or "pip install bandit" in content
          ), "pre-commit hook lacks a bandit availability guard or install hint"
  ```

  Run: `make test-unit` — must FAIL (`test_pre_commit_calls_lint_bandit` fails)

---

- [ ] **Step 2: Implement (GREEN)**

  ```bash
  # In .githooks/pre-commit, insert the following block BEFORE the STAGED= line
  # (i.e., after the version-drift check block, before the markdown section):

  # Bandit SAST: scan hooks/ for security issues
  if ! command -v bandit &>/dev/null && ! python3 -m bandit --version &>/dev/null 2>&1; then
    echo "pre-commit: bandit not found — run: pip install 'bandit>=1.7'" >&2
  else
    if ! make lint-bandit; then
      echo ""
      echo "Commit blocked: fix bandit findings above, then re-commit."
      exit 1
    fi
  fi
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  The guard uses `command -v bandit` first (faster shell builtin) with a fallback to
  `python3 -m bandit --version` to handle environments where bandit is installed as a
  module but not on PATH. This matches the existing `command -v npx` pattern already
  in the file. No further cleanup needed.

  Run: `make test-unit` — still PASS

---

**Commit:** `git add Makefile .githooks/pre-commit tests/unit/test_bandit_ci.py && git commit -m "fix: audit-bandit-sast-ci — add bandit SAST to make lint and pre-commit"`
