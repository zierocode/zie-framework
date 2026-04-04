---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-parse-section-dedup.md
spec: specs/2026-03-24-audit-parse-section-dedup-design.md
---

# parse_section() Deduplication — Implementation Plan

**Goal:** Generalise `parse_roadmap_now()` in `utils.py` into `parse_roadmap_section(roadmap_path, section_name)`, keep `parse_roadmap_now()` as a thin wrapper, and remove the inline `parse_section()` from `session-resume.py`.
**Architecture:** `parse_roadmap_section` replaces the inline copy in `session-resume.py` for the "next" and "done" sections, and backs `parse_roadmap_now` via delegation. The `roadmap_text` variable in `session-resume.py` is retained solely for the 200-line truncation print block — only the `parse_section` call sites are replaced. Behaviour improves slightly: next/done items now get markdown link stripping and `[x]`/`[ ]` prefix removal, consistent with now items.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `parse_roadmap_section()`; refactor `parse_roadmap_now()` as thin wrapper |
| Modify | `hooks/session-resume.py` | Remove inline `parse_section()`; replace 3 call sites |
| Modify | `tests/unit/test_utils.py` | Add tests for `parse_roadmap_section` with "next" and "done" headers |

## Task 1: Add parse_roadmap_section() to utils.py

**Acceptance Criteria:**
- `hooks/utils.py` exports `parse_roadmap_section(roadmap_path, section_name)`
- `parse_roadmap_section` matches the section case-insensitively
- `parse_roadmap_section` strips markdown links and `[x]`/`[ ]` prefixes from items
- `parse_roadmap_section` returns `[]` for missing file, absent section, or empty section
- `parse_roadmap_now(roadmap_path)` delegates to `parse_roadmap_section(roadmap_path, "now")`
- All existing `TestParseRoadmapNow` tests still pass (thin wrapper preserves behaviour)

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**
  Add to `tests/unit/test_utils.py`:

  ```python
  from utils import parse_roadmap_now, project_tmp_path, parse_roadmap_section

  class TestParseRoadmapSection:
      def test_next_section_returns_items(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] a\n## Next\n- [ ] b\n- [ ] c\n## Done\n- [x] d\n")
          assert parse_roadmap_section(f, "next") == ["b", "c"]

      def test_done_section_returns_items(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Done\n- [x] finished task\n")
          assert parse_roadmap_section(f, "done") == ["finished task"]

      def test_case_insensitive_match(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## NEXT\n- [ ] item\n")
          assert parse_roadmap_section(f, "next") == ["item"]

      def test_missing_section_returns_empty(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] a\n")
          assert parse_roadmap_section(f, "done") == []

      def test_missing_file_returns_empty(self, tmp_path):
          assert parse_roadmap_section(tmp_path / "none.md", "next") == []

      def test_strips_markdown_links(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Next\n- [ ] my task — [plan](plans/foo.md)\n")
          assert parse_roadmap_section(f, "next") == ["my task — plan"]

      def test_parse_roadmap_now_still_works_via_wrapper(self, tmp_path):
          f = tmp_path / "ROADMAP.md"
          f.write_text("## Now\n- [ ] now item\n## Next\n- [ ] next item\n")
          assert parse_roadmap_now(f) == ["now item"]
  ```

  Run: `make test-unit` — must FAIL (ImportError: cannot import `parse_roadmap_section`)

- [ ] **Step 2: Implement (GREEN)**
  In `hooks/utils.py`, add `parse_roadmap_section()` and refactor `parse_roadmap_now()`:

  ```python
  def parse_roadmap_section(roadmap_path, section_name: str) -> list:
      """Extract cleaned items from a named ## section of ROADMAP.md.

      section_name is matched case-insensitively against ## headers.
      Returns [] if file missing, section absent, or section empty.
      """
      path = Path(roadmap_path)
      if not path.exists():
          return []
      lines = []
      in_section = False
      for line in path.read_text().splitlines():
          if line.startswith("##") and section_name.lower() in line.lower():
              in_section = True
              continue
          if line.startswith("##") and in_section:
              break
          if in_section and line.strip().startswith("- "):
              clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
              clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
              if clean:
                  lines.append(clean)
      return lines


  def parse_roadmap_now(roadmap_path) -> list:
      """Extract cleaned items from the ## Now section of ROADMAP.md.

      Returns [] if the file is missing, the Now section is absent, or it is empty.
      Accepts Path or str.
      """
      return parse_roadmap_section(roadmap_path, "now")
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm all `TestParseRoadmapNow` tests still pass (they now run through the thin wrapper).
  Run: `make test-unit` — still PASS

## Task 2: Remove inline parse_section() from session-resume.py

**Acceptance Criteria:**
- `hooks/session-resume.py` no longer defines an inline `parse_section()` function
- The three call sites use `parse_roadmap_now` (now lane) and `parse_roadmap_section(..., "next")` / `parse_roadmap_section(..., "done")`
- `parse_roadmap_section` is added to the `from utils import` line in `session-resume.py`
- The `roadmap_text` variable is retained for the 200-line truncation print block
- All existing `test_hooks_session_resume.py` tests pass

**Files:**
- Modify: `hooks/session-resume.py`

- [ ] **Step 1: Write failing tests (RED)**
  Existing `test_hooks_session_resume.py` tests cover the output of `session-resume.py`. Confirm they pass as baseline before changes.
  Run: `make test-unit` — must PASS (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In `hooks/session-resume.py`:
  1. Add `parse_roadmap_section` to the `from utils import` line
  2. Delete the inline `parse_section(text, header)` function (lines 41–52)
  3. Delete the `roadmap_text` variable assignment used only by `parse_section` calls (retain it if still needed for the print block)
  4. Replace `parse_section(roadmap_text, "next")` → `parse_roadmap_section(roadmap_file, "next")`
  5. Replace `parse_section(roadmap_text, "done")` → `parse_roadmap_section(roadmap_file, "done")`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Grep for `parse_section` in `hooks/session-resume.py` — must return empty.
  Confirm `roadmap_text` is still present if used by the truncation print block; remove if truly unused.
  Run: `make test-unit` — still PASS
