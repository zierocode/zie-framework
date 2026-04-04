---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-parse-roadmap-edge-cases.md
spec: specs/2026-03-24-audit-parse-roadmap-edge-cases-design.md
---

# parse_roadmap_now() — Edge Case Tests for Inline Markdown and Malformed Links — Implementation Plan

**Goal:** Add a `TestParseRoadmapNowEdgeCases` class to `test_utils.py` covering inline markdown formatting, malformed link syntax, and HTML entities to make `parse_roadmap_now()` behaviour explicit and regression-proof.
**Architecture:** Pure test addition. Each test writes a minimal ROADMAP fixture to `tmp_path`, calls `parse_roadmap_now()` directly, and asserts the exact returned list. If any test reveals a real parser defect, `hooks/utils.py` is patched before merge. The existing `re.sub` in `parse_roadmap_now` handles well-formed `[text](url)` links; the tests document what happens to malformed variants.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `tests/unit/test_utils.py` | Add class `TestParseRoadmapNowEdgeCases` with 5 test methods |
| Modify (if needed) | `hooks/utils.py` | Fix `parse_roadmap_now()` if any test exposes a real defect |

---

## Task 1: Add TestParseRoadmapNowEdgeCases to test_utils.py

**Acceptance Criteria:**
- `test_bold_inline_markdown_in_task` passes: bold markers are preserved as-is in the returned string
- `test_italic_inline_markdown_in_task` passes: italic markers are preserved as-is
- `test_malformed_link_missing_closing_paren` passes and explicitly documents the regex's behaviour on partial link syntax
- `test_html_entity_in_task_description` passes: HTML entities are passed through unchanged
- `test_nested_bold_link_combo` passes: link text is extracted, bold markers around it are preserved
- No changes to `hooks/utils.py` are required (these tests document existing correct behaviour)

**Files:**
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append the new class to `test_utils.py`. All five tests are written with the expected values derived from a manual trace of the current `parse_roadmap_now()` logic. They are the RED step because the class does not yet exist:

  ```python
  class TestParseRoadmapNowEdgeCases:
      def test_bold_inline_markdown_in_task(self, tmp_path):
          # Bold markers are not in the link regex — they pass through unchanged
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] **Refactor** the payment module\n")
          result = parse_roadmap_now(f)
          # RED: class does not exist yet — this test will not be collected
          assert result == ["**Refactor** the payment module"]

      def test_italic_inline_markdown_in_task(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] fix _memory leak_ in cache\n")
          result = parse_roadmap_now(f)
          assert result == ["fix _memory leak_ in cache"]

      def test_malformed_link_missing_closing_paren(self, tmp_path):
          # re.sub pattern requires closing ) — without it, the link is NOT stripped
          # Contract: raw text is preserved (no partial stripping)
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] my feature — [plan](plans/foo.md\n")
          result = parse_roadmap_now(f)
          # The regex \([^\)]+\) requires a closing ) — the malformed link is NOT matched
          # so the entire bracket+paren construct is passed through as raw text
          assert result == ["my feature — [plan](plans/foo.md"]

      def test_html_entity_in_task_description(self, tmp_path):
          # HTML entities are never decoded — plain text passthrough
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] support &amp; operator\n")
          result = parse_roadmap_now(f)
          assert result == ["support &amp; operator"]

      def test_nested_bold_link_combo(self, tmp_path):
          # Link is stripped (well-formed), bold markers around link text are preserved
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] **bold link** — [spec](specs/foo.md)\n")
          result = parse_roadmap_now(f)
          # re.sub replaces [spec](specs/foo.md) with "spec"
          assert result == ["**bold link** — spec"]
  ```

  Run: `make test-unit` — must FAIL (class not yet present in file, so tests are not collected; add the class to make collection succeed, then the assertions drive pass/fail)

- [ ] **Step 2: Implement (GREEN)**

  The implementation for this item IS the test code itself — `parse_roadmap_now()` in `hooks/utils.py` is expected to already handle all cases correctly. The step is to confirm by running:

  Run: `make test-unit` — must PASS

  If `test_malformed_link_missing_closing_paren` fails with a different value (e.g. partial stripping occurs), update the assertion to match actual behaviour AND add a docstring noting it is a known limitation. Do NOT change the regex behaviour unless Zie explicitly approves.

- [ ] **Step 3: Refactor**

  Add a module-level docstring to the `TestParseRoadmapNowEdgeCases` class explaining the "document the contract" intent — these tests exist to make implicit parser behaviour explicit, not to enforce new constraints:

  ```python
  class TestParseRoadmapNowEdgeCases:
      """Edge case tests for parse_roadmap_now().

      These tests document the parser's existing behaviour for inputs that are
      valid ROADMAP content but outside the basic happy path. They are
      contract tests — if behaviour changes, update the assertion AND the spec.
      """
  ```

  Run: `make test-unit` — still PASS
