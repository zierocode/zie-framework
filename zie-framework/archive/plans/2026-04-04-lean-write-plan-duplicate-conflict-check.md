---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-write-plan-duplicate-conflict-check.md
---

# lean-write-plan-duplicate-conflict-check — Implementation Plan

**Goal:** Remove the duplicate "File conflict check" paragraph from `skills/write-plan/SKILL.md` and add a structural pytest test to prevent regressions.
**Architecture:** Two-task S-plan. Task 1 deletes the redundant paragraph (line 84) from the skill file; Task 2 adds a structural test that scans all `skills/*/SKILL.md` files for verbatim duplicate paragraph blocks. Tasks are independent and can run in parallel; no shared output file.
**Tech Stack:** Python 3.x (pytest), Markdown

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/write-plan/SKILL.md` | Remove duplicate "File conflict check" paragraph at line 84 |
| Create | `tests/unit/test_skill_dedup.py` | Structural test — assert no verbatim duplicate paragraphs in any SKILL.md |

---

## Task 1: Remove duplicate paragraph from write-plan/SKILL.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/write-plan/SKILL.md` contains exactly one instance of the text "File conflict check"
- The remaining instance is the one under "โครงสร้าง Task" (lines 119–121), which includes the full `depends_on` serialization guidance
- `make test-unit` passes

**Files:**
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # tests/unit/test_skill_write_plan_conflict_check.py  (temp test file — delete after Task 2 is done)
  import re

  def test_write_plan_has_one_conflict_check():
      with open("skills/write-plan/SKILL.md") as f:
          content = f.read()
      matches = [m.start() for m in re.finditer(r"File conflict check", content)]
      assert len(matches) == 1, (
          f"Expected exactly 1 'File conflict check' in write-plan/SKILL.md, found {len(matches)}"
      )
  ```

  Run: `make test-unit` — must FAIL (currently 2 matches exist)

- [ ] **Step 2: Implement (GREEN)**

  In `skills/write-plan/SKILL.md`, remove the line at line 84 (the shorter first instance under "Task Sizing Guidance"):

  Delete this line (including the trailing blank line):
  ```
  **File conflict check:** Before assigning tasks, verify no two independent tasks write to the same output file. If they do, add `<!-- depends_on: TN -->` to serialize them.
  ```

  The section after "⚠️ >15 tasks" should read directly:
  ```markdown
  - ⚠️ >15 tasks: plan is too large — split by feature boundary

  ## โครงสร้าง Task
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the remaining instance at lines 119–121 is intact. Confirm section ordering is correct:
  1. "Task Sizing Guidance" ends at the task count bullet list
  2. "โครงสร้าง Task" section opens
  3. Task template block
  4. `depends_on` note
  5. "File conflict check" paragraph (canonical, kept)
  6. "Max parallel tasks: 4" paragraph

  Run: `make test-unit` — still PASS

---

## Task 2: Add structural dedup test for all SKILL.md files

<!-- depends_on: none -->

**Acceptance Criteria:**
- `tests/unit/test_skill_dedup.py` exists and runs under `make test-unit`
- The test iterates all `skills/*/SKILL.md` files, strips YAML frontmatter, splits into paragraph blocks, and asserts no paragraph (≥2 lines or ≥80 chars) appears verbatim ≥2 times within a single file
- The test passes on the post-Task-1 state of the codebase (only one "File conflict check" paragraph remains)
- The test would have caught the bug before this fix (i.e. fails on the original `write-plan/SKILL.md`)

**Files:**
- Create: `tests/unit/test_skill_dedup.py`

- [ ] **Step 1: Write failing test (RED)**

  First confirm the test fails on current (unmodified) `write-plan/SKILL.md`:

  ```python
  # tests/unit/test_skill_dedup.py
  """Structural test: no verbatim duplicate paragraph blocks in any SKILL.md."""
  import os
  import glob

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  MIN_PARAGRAPH_CHARS = 80  # ignore short decorative lines
  MIN_PARAGRAPH_LINES = 2   # ignore single-line headings and bullets


  def _strip_frontmatter(content: str) -> str:
      """Remove YAML frontmatter block (---...---) from start of content."""
      if not content.startswith("---"):
          return content
      parts = content.split("---", 2)
      if len(parts) < 3:
          return content
      return parts[2]


  def _get_paragraphs(content: str) -> list[str]:
      """
      Split content into paragraph blocks (separated by blank lines).
      Filter out short or trivial blocks.
      """
      body = _strip_frontmatter(content)
      raw_blocks = body.split("\n\n")
      paragraphs = []
      for block in raw_blocks:
          stripped = block.strip()
          if not stripped:
              continue
          # Skip horizontal rules and single-character filler
          if stripped in ("---", "===", "***"):
              continue
          # Only flag substantial blocks
          line_count = len(stripped.splitlines())
          if len(stripped) >= MIN_PARAGRAPH_CHARS or line_count >= MIN_PARAGRAPH_LINES:
              paragraphs.append(stripped)
      return paragraphs


  def _find_skill_files() -> list[str]:
      pattern = os.path.join(REPO_ROOT, "skills", "*", "SKILL.md")
      return sorted(glob.glob(pattern))


  class TestSkillDedupNoDuplicateParagraphs:
      def test_no_verbatim_duplicate_paragraphs_in_any_skill(self):
          """Each SKILL.md must not repeat a paragraph block verbatim."""
          skill_files = _find_skill_files()
          assert skill_files, "No SKILL.md files found — check REPO_ROOT"

          violations: list[str] = []
          for path in skill_files:
              with open(path) as f:
                  content = f.read()
              paragraphs = _get_paragraphs(content)
              seen: dict[str, int] = {}
              for para in paragraphs:
                  seen[para] = seen.get(para, 0) + 1
              duplicates = {p: count for p, count in seen.items() if count >= 2}
              if duplicates:
                  rel = os.path.relpath(path, REPO_ROOT)
                  for para, count in duplicates.items():
                      preview = para[:120].replace("\n", " ")
                      violations.append(
                          f"{rel}: paragraph appears {count}x — '{preview}...'"
                      )

          assert not violations, (
              "Verbatim duplicate paragraphs found in SKILL.md files:\n"
              + "\n".join(f"  - {v}" for v in violations)
          )
  ```

  Run: `make test-unit` — must FAIL (detects duplicate in `write-plan/SKILL.md` before Task 1 fix)

  > Note: If running Task 2 after Task 1 has already been applied, temporarily revert `write-plan/SKILL.md` to verify the test catches the bug, then re-apply the fix.

- [ ] **Step 2: Implement (GREEN)**

  The test file above IS the implementation. Ensure Task 1 has been applied (one "File conflict check" paragraph only).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Remove the temporary test file `tests/unit/test_skill_write_plan_conflict_check.py` from Task 1 (if it was created).

  Verify `test_skill_dedup.py` covers the same assertion and no duplicate test exists.

  Run: `make test-unit` — still PASS

---

## Execution Order

Tasks 1 and 2 can run in parallel (no shared output file). Recommended order:
1. Apply Task 1 (skill edit — fast, no new file)
2. Apply Task 2 (new test file — verifies Task 1 result)
3. Run `make test-unit` once at the end to confirm both green
