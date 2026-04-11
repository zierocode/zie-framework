---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-hotfix-model-overkill.md
---

# Lean Hotfix Model Overkill — Implementation Plan

**Goal:** Swap `commands/hotfix.md` frontmatter from `model: claude-opus-4-6` / `effort: high` to `model: claude-sonnet-4-6` / `effort: low`, and pin those correct values in the test suite.
**Architecture:** Single-file YAML frontmatter edit plus a test update to the `EXPECTED` dict in `test_model_effort_frontmatter.py`. No runtime logic changes; the fix is purely declarative.
**Tech Stack:** Markdown/YAML frontmatter, pytest.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/hotfix.md` | Swap `model` and `effort` frontmatter values |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Add `commands/hotfix.md` to `EXPECTED` with `("sonnet", "low")` |

---

## Task Sizing

S plan — 2 tasks, single session.

---

## Task 1: Swap frontmatter values in commands/hotfix.md

**Acceptance Criteria:**
- `commands/hotfix.md` frontmatter has `model: claude-sonnet-4-6`
- `commands/hotfix.md` frontmatter has `effort: low`
- All other content in the file is unchanged

**Files:**
- Modify: `commands/hotfix.md`

- [ ] **Step 1: Write failing test (RED)**

  Add a pinning test to `tests/unit/test_zie_hotfix_command.py`:

  ```python
  def test_frontmatter_model_is_sonnet():
      import re, yaml
      text = CMD.read_text()
      match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
      assert match, "No frontmatter block"
      fm = yaml.safe_load(match.group(1))
      assert fm.get("model") == "claude-sonnet-4-6", \
          f"hotfix must use claude-sonnet-4-6, got {fm.get('model')!r}"

  def test_frontmatter_effort_is_low():
      import re, yaml
      text = CMD.read_text()
      match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
      assert match, "No frontmatter block"
      fm = yaml.safe_load(match.group(1))
      assert fm.get("effort") == "low", \
          f"hotfix must have effort: low, got {fm.get('effort')!r}"
  ```

  Run: `make test-unit` — must FAIL (current values are `claude-opus-4-6` / `high`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/hotfix.md`, replace:

  ```yaml
  model: claude-opus-4-6
  effort: high
  ```

  with:

  ```yaml
  model: claude-sonnet-4-6
  effort: low
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No structural cleanup needed. Verify no other file references the old `claude-opus-4-6` value for hotfix.

  Run: `make test-unit` — still PASS

---

## Task 2: Pin hotfix.md values in test_model_effort_frontmatter.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `EXPECTED` dict in `test_model_effort_frontmatter.py` includes `"commands/hotfix.md": ("sonnet", "low")`
- `TestExpectedValues.test_correct_model_values` and `test_correct_effort_values` cover `commands/hotfix.md`
- Note: the test uses short model names (`"sonnet"`) via `model` field matching — confirm the test's `parse_frontmatter` vs. the full `claude-sonnet-4-6` string used in the actual file

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`

- [ ] **Step 1: Write failing test (RED)**

  The `EXPECTED` dict currently lacks `commands/hotfix.md`. The existing `TestExpectedValues` tests will not catch a regression if hotfix drifts back to opus. Confirm by running:

  ```bash
  python -m pytest tests/unit/test_model_effort_frontmatter.py -v 2>&1 | grep hotfix
  ```

  Expected: no output (hotfix not covered). This is the observable gap — no test failure yet, but coverage is absent.

  Add a standalone coverage-gap test first:

  ```python
  def test_hotfix_command_is_in_expected_map():
      """Regression guard: hotfix.md must be covered by EXPECTED."""
      assert "commands/hotfix.md" in EXPECTED, \
          "commands/hotfix.md must be added to EXPECTED to prevent model drift"
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  In `test_model_effort_frontmatter.py`, find the `EXPECTED` dict. After:

  ```python
      "commands/audit.md":     ("sonnet", "medium"),
  ```

  Add:

  ```python
      "commands/hotfix.md":    ("sonnet", "low"),
  ```

  Also add the temporary coverage-gap test from Step 1 permanently (remove the standalone guard test — the `EXPECTED` entry itself is the regression guard).

  Note: `parse_frontmatter` reads the YAML and returns raw values. The file now has `model: claude-sonnet-4-6` — but `VALID_MODELS = {"haiku", "sonnet", "opus"}` uses short names. Inspect the actual assertion path:

  - `test_correct_model_values` compares `fm.get("model")` to `expected_model` (`"sonnet"`)
  - The file uses `model: claude-sonnet-4-6` — these will NOT match

  Resolution: the `EXPECTED` dict must use `"claude-sonnet-4-6"` to match the literal frontmatter value, OR the test normalises to short names. Check the existing passing entries (e.g. `commands/fix.md` has `model: sonnet` in its file). Confirm by reading `commands/fix.md` frontmatter before finalising the `EXPECTED` entry value.

  If all existing commands use short names (`sonnet`, `haiku`), then `commands/hotfix.md` must also be changed to `model: sonnet` (not `claude-sonnet-4-6`) for consistency.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the temporary standalone gap test if it was added; the `EXPECTED` entry is sufficient.

  Run: `make test-unit` — still PASS

---

## Implementation Notes

- **Model name normalisation:** Before finalising the `commands/hotfix.md` value, check the existing command files to confirm whether they use `sonnet` or `claude-sonnet-4-6`. The test `VALID_MODELS` contains only short names (`haiku`, `sonnet`, `opus`), so the file should use `sonnet` for consistency.
- **No sprint.md conflict:** `test_zie_sprint.py` asserts `effort: high` for `commands/sprint.md` — that is unrelated.
- **effort_audit.py:** Scans only `skills/` directory, not `commands/` — no conflict.
- **Commit message:** `fix: lean-hotfix-model-overkill — sonnet+low for mechanical fix track`
