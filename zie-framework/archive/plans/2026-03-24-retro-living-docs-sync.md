---
approved: false
approved_at: ~
backlog: backlog/retro-living-docs-sync.md
spec: specs/2026-03-24-retro-living-docs-sync-design.md
---

# Retro Living Docs Sync — Implementation Plan

**Goal:** Add a systematic `CLAUDE.md` + `README.md` docs sync step to `commands/zie-retro.md`, integrated into the existing "อัปเดต project knowledge" step (Option A). The step enumerates actual `commands/`, `hooks/`, `skills/` contents and `VERSION`, compares against what the docs currently say, applies any gaps, and logs what changed.
**Architecture:** Single Markdown edit — no new files, no new hooks. The sync step is prose instructions added to `zie-retro.md`'s "อัปเดต project knowledge" section, between the existing `project/components.md` updates and the `ROADMAP` step.
**Tech Stack:** Markdown (command definition), pytest + `Path.read_text()` (test validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-retro.md` | Add CLAUDE.md + README.md sync sub-step inside "อัปเดต project knowledge" |
| Create | `tests/unit/test_retro_living_docs_sync.py` | Validate sync step prose is present in zie-retro.md |

---

## Task 1: Add living docs sync step to `commands/zie-retro.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-retro.md` contains a sub-step that reads `CLAUDE.md`
- `commands/zie-retro.md` contains a sub-step that reads `README.md`
- The step includes an "in sync" fallback message (e.g. "CLAUDE.md in sync")
- The step includes a change-logging instruction (e.g. "Updated CLAUDE.md: added X, removed Y")
- The sync step is positioned within or directly after the existing "อัปเดต project knowledge" section
- All existing steps in `zie-retro.md` are preserved unchanged

**Files:**
- Modify: `commands/zie-retro.md`
- Create: `tests/unit/test_retro_living_docs_sync.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_retro_living_docs_sync.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  class TestRetroLivingDocsSync:
      def _retro_text(self) -> str:
          return (COMMANDS_DIR / "zie-retro.md").read_text()

      def test_claude_md_sync_step_present(self):
          assert "CLAUDE.md" in self._retro_text(), \
              "zie-retro.md must contain a CLAUDE.md sync step"

      def test_readme_md_sync_step_present(self):
          assert "README.md" in self._retro_text(), \
              "zie-retro.md must contain a README.md sync step"

      def test_in_sync_fallback_present(self):
          assert "in sync" in self._retro_text(), \
              "zie-retro.md must include an 'in sync' fallback message"

      def test_change_logging_instruction_present(self):
          text = self._retro_text()
          assert "Updated CLAUDE.md" in text, \
              "zie-retro.md must include 'Updated CLAUDE.md' change-logging instruction"
  ```

  Run: `make test-unit` — must FAIL (sync step not yet present in `zie-retro.md`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-retro.md`, inside the `### อัปเดต project knowledge` section, add the following sub-step after the `project/components.md` and `project/architecture.md` update bullets and before the `zie_memory_enabled` brain-store block:

  ```markdown
  #### Living docs sync — CLAUDE.md + README.md

  - Read `CLAUDE.md` (project root).
  - Read `README.md` (project root).
  - Enumerate actual codebase state:
    - `commands/` — list all `*.md` filenames → these are the slash commands.
    - `hooks/` — list all `*.py` filenames → these are the hook scripts.
    - `skills/` — list all subdirectory names → these are the skills.
    - `VERSION` file (if present) → current version string.
  - Compare actual vs. documented in each file:
    - Commands section in `CLAUDE.md` / `README.md` — add any commands not listed,
      remove any listed commands whose file no longer exists.
    - Hooks section — same: add new, remove deleted.
    - Skills section — same: add new, remove deleted.
    - Build commands / tech stack — flag any obvious drift (e.g. test runner changed).
  - Apply all updates in the same session.
  - Log what changed:
    - If changes were made: print `"Updated CLAUDE.md: added <X>, removed <Y>"` and/or
      `"Updated README.md: added <X>, removed <Y>"` for each file touched.
    - If no changes needed: print `"CLAUDE.md in sync"` and `"README.md in sync"`.
  - This step runs even when no changes are found — the "in sync" confirmation is
    itself useful signal.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Re-read the full `commands/zie-retro.md` to confirm:
  - All original sections (`รวบรวม context`, `วิเคราะห์และสรุป`, `บันทึก ADRs`,
    `อัปเดต project knowledge`, `อัปเดต ROADMAP`, `บันทึกสู่ brain`, `สรุปผล`)
    are intact and unmodified beyond the new sub-step.
  - The new sub-step sits logically within "อัปเดต project knowledge" — after
    `project/components.md` / `project/architecture.md` updates, before the
    brain-store block.
  - No trailing whitespace issues or broken Markdown.

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-retro.md tests/unit/test_retro_living_docs_sync.py && git commit -m "feat: retro-living-docs-sync"`*
