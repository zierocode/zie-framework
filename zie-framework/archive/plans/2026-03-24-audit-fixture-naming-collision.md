---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-fixture-naming-collision.md
spec: specs/2026-03-24-audit-fixture-naming-collision-design.md
---

# Unique Fixture Names for _cleanup_debounce in test_hooks_auto_test.py — Implementation Plan

**Goal:** Rename the three duplicate `_cleanup_debounce` autouse fixtures in `test_hooks_auto_test.py` to unique, class-scoped names so pytest cannot silently shadow one with another.
**Architecture:** Pure rename — no logic change. Each of the three fixture definitions in `TestAutoTestDebounce`, `TestAutoTestRunnerSelection`, and `TestAutoTestDebounceBoundary` gets a distinct name reflecting its owning class. Because all three are `autouse` and class-scoped, no call-site changes are needed.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_hooks_auto_test.py` | Rename three `_cleanup_debounce` fixture defs to unique names |

---

## Task 1: Rename duplicate _cleanup_debounce fixtures

**Acceptance Criteria:**
- No two fixtures share the name `_cleanup_debounce` in the module
- `TestAutoTestDebounce` teardown still removes the debounce file after each test
- `TestAutoTestRunnerSelection` teardown still removes the debounce file after each test
- `TestAutoTestDebounceBoundary` teardown still removes the debounce file after each test
- `make test-unit` passes with no warnings about fixture shadowing

**Files:**
- Modify: `tests/unit/test_hooks_auto_test.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a module-level uniqueness assertion that exposes the collision:

  ```python
  # Append to test_hooks_auto_test.py (outside all classes):
  def test_no_duplicate_fixture_names_in_module():
      """Fixture names must be unique to prevent pytest shadowing."""
      import ast, pathlib
      src = pathlib.Path(__file__).read_text()
      tree = ast.parse(src)
      fixture_names = []
      for node in ast.walk(tree):
          if isinstance(node, ast.FunctionDef):
              for dec in node.decorator_list:
                  dec_name = ""
                  if isinstance(dec, ast.Attribute):
                      dec_name = dec.attr
                  elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                      dec_name = dec.func.attr
                  elif isinstance(dec, ast.Name):
                      dec_name = dec.id
                  elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                      dec_name = dec.func.id
                  if dec_name == "fixture":
                      fixture_names.append(node.name)
      duplicates = [n for n in fixture_names if fixture_names.count(n) > 1]
      assert duplicates == [], f"Duplicate fixture names found: {set(duplicates)}"
  ```

  Run: `make test-unit` — must FAIL (reports `_cleanup_debounce` as a duplicate)

- [ ] **Step 2: Implement (GREEN)**

  Rename each fixture in its class (only the `def` line changes — decorator stays `@pytest.fixture(autouse=True)`):

  ```python
  # In class TestAutoTestDebounce (line 63):
  # BEFORE: def _cleanup_debounce(self, tmp_path):
  # AFTER:
  @pytest.fixture(autouse=True)
  def _cleanup_debounce_debounce(self, tmp_path):
      yield
      p = project_tmp_path("last-test", tmp_path.name)
      if p.exists():
          p.unlink()

  # In class TestAutoTestRunnerSelection (line 120):
  # BEFORE: def _cleanup_debounce(self, tmp_path):
  # AFTER:
  @pytest.fixture(autouse=True)
  def _cleanup_debounce_runner(self, tmp_path):
      yield
      p = project_tmp_path("last-test", tmp_path.name)
      if p.exists():
          p.unlink()

  # In class TestAutoTestDebounceBoundary (line 137):
  # BEFORE: def _cleanup_debounce(self, tmp_path):
  # AFTER:
  @pytest.fixture(autouse=True)
  def _cleanup_debounce_boundary(self, tmp_path):
      yield
      p = project_tmp_path("last-test", tmp_path.name)
      if p.exists():
          p.unlink()
  ```

  Run: `make test-unit` — must PASS (including the new uniqueness assertion)

- [ ] **Step 3: Refactor**

  Remove the `test_no_duplicate_fixture_names_in_module` canary added in Step 1 — it was a scaffolding check. The rename is the permanent fix; ongoing protection comes from code review and the spec.

  Run: `make test-unit` — still PASS
