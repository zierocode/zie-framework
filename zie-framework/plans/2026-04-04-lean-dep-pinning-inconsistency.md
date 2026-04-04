---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-dep-pinning-inconsistency.md
---

# Lean Dep Pinning Inconsistency — Implementation Plan

**Goal:** Standardize all dev dependencies in `requirements-dev.txt` to compatible-release pinning (`~=X.Y.Z`), removing the inconsistent mix of `>=` and `==`.
**Architecture:** Single-file change to `requirements-dev.txt` with a header comment documenting the pinning policy. A structural test asserts the policy is maintained going forward.
**Tech Stack:** Python pip, pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `requirements-dev.txt` | Switch all 6 deps to `~=X.Y.Z`; add policy header comment |
| Create | `tests/unit/test_dep_pinning.py` | Structural test: assert all deps in requirements-dev.txt use `~=` |

---

## Task 1: Update requirements-dev.txt to compatible-release pinning

**Acceptance Criteria:**
- All six deps use `~=X.Y.Z` format (no `>=` or `==`)
- File begins with a comment explaining the `~=` policy choice
- `pip install -r requirements-dev.txt` resolves without error

**Files:**
- Modify: `requirements-dev.txt`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_dep_pinning.py
  """Structural test: requirements-dev.txt must use ~= pinning for all deps."""
  import re
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent
  REQ_FILE = REPO_ROOT / "requirements-dev.txt"


  class TestDepPinning:
      def test_requirements_dev_exists(self):
          assert REQ_FILE.exists(), "requirements-dev.txt not found"

      def test_all_deps_use_compatible_release_pinning(self):
          lines = REQ_FILE.read_text().splitlines()
          dep_lines = [
              line for line in lines
              if line.strip() and not line.strip().startswith("#")
          ]
          assert dep_lines, "requirements-dev.txt has no dependency lines"
          bad_lines = [
              line for line in dep_lines
              if not re.search(r"~=\d", line)
          ]
          assert bad_lines == [], (
              f"Dependencies not using ~= pinning: {bad_lines}\n"
              f"All deps must use ~=X.Y.Z (compatible-release) pinning."
          )

      def test_no_exact_pin(self):
          content = REQ_FILE.read_text()
          dep_lines = [
              line for line in content.splitlines()
              if line.strip() and not line.strip().startswith("#")
          ]
          exact_pins = [line for line in dep_lines if re.search(r"==\d", line)]
          assert exact_pins == [], (
              f"Exact pins (==) found; use ~= instead: {exact_pins}"
          )

      def test_no_lower_bound_only_pin(self):
          content = REQ_FILE.read_text()
          dep_lines = [
              line for line in content.splitlines()
              if line.strip() and not line.strip().startswith("#")
          ]
          lb_pins = [line for line in dep_lines if re.search(r">=\d", line)]
          assert lb_pins == [], (
              f"Lower-bound-only pins (>=) found; use ~= instead: {lb_pins}"
          )

      def test_policy_comment_present(self):
          content = REQ_FILE.read_text()
          assert "~=" in content and "#" in content, (
              "requirements-dev.txt should contain a policy comment explaining ~= pinning"
          )
  ```

  Run: `make test-unit` — must **FAIL** (current file has `>=` and `==` pins)

- [ ] **Step 2: Implement (GREEN)**

  Replace `requirements-dev.txt` contents:

  ```text
  # Dev dependencies — compatible-release pinning (~=X.Y.Z)
  # ~= allows patch upgrades (e.g. ~=9.0.3 → any 9.0.x) but not minor/major bumps.
  # This makes Dependabot auto-merge viable while preventing surprise breaking changes.
  pytest~=9.0.3
  pytest-cov~=7.1.0
  coverage~=7.13.5
  bandit~=1.9.4
  commitizen~=4.13.9
  ruff~=0.11.2
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  No refactor needed — change is minimal and self-contained.

  Run: `make test-unit` — still **PASS**

---

## Task 2: Verify CI install still works

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `pip install -r requirements-dev.txt` exits 0 in a clean virtualenv
- `make lint` passes (ruff resolves correctly under `~=0.11.2`)

**Files:**
- No file changes — verification only

- [ ] **Step 1: Smoke test install**

  ```bash
  python -m venv /tmp/test-pinning-venv
  /tmp/test-pinning-venv/bin/pip install -r requirements-dev.txt
  /tmp/test-pinning-venv/bin/ruff --version
  /tmp/test-pinning-venv/bin/pytest --version
  ```

  Expected: all commands exit 0, versions in `0.11.x` / `9.0.x` range.

- [ ] **Step 2: Run lint gate**

  ```bash
  make lint
  ```

  Expected: exits 0, no ruff errors.

- [ ] **Step 3: Commit**

  ```bash
  git add requirements-dev.txt tests/unit/test_dep_pinning.py
  git commit -m "chore: standardize requirements-dev.txt to ~= compatible-release pinning"
  ```
