---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-docs-sync-blind-to-project-md.md
---

# lean-docs-sync-blind-to-project-md — Implementation Plan

**Goal:** Extend `docs-sync-check` skill to cross-reference PROJECT.md Commands and Skills tables against disk, emitting a `project_md_stale` verdict field.

**Architecture:** The existing `skills/docs-sync-check/SKILL.md` gains a new Step 3b that reads PROJECT.md, parses its Commands and Skills Markdown tables, and cross-references them against globbed disk state. The returned JSON verdict gains three new additive fields. All existing behavior and tests are preserved — the change is purely additive.

**Tech Stack:** Markdown skill prose (no Python); pytest static-text assertions in existing test file.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/docs-sync-check/SKILL.md` | Add Step 3b (PROJECT.md parse + cross-ref) + extended verdict JSON |
| Modify | `tests/unit/test_docs_sync_check_general_agent.py` | Add `TestDocsSyncCheckProjectMd` class — 6 tests asserting skill prose + verdict schema |

---

## Task 1: Add PROJECT.md Check Step to docs-sync-check Skill

**Acceptance Criteria:**
- `skills/docs-sync-check/SKILL.md` contains a "Step 3b" block that reads `PROJECT.md`
- Step 3b extracts Commands table rows (`| /command |`) and Skills table rows (`| skill-name |`)
- Step 3b documents the `/`-strip rule for commands and bare-name rule for skills
- Step 3b documents header row exclusion (`| Command |`, `| --- |`)
- Step 3b documents the PROJECT.md-missing edge case (`project_md_stale: false` + note in `details`)
- Step 3b documents the missing-table edge case (treat as empty table → flag all disk items)
- Returned JSON verdict block includes `project_md_stale`, `missing_from_project_md`, `extra_in_project_md`
- Existing Steps 1–5 are unchanged

**Files:**
- Modify: `skills/docs-sync-check/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_docs_sync_check_general_agent.py — add class:

  SKILL_PATH = Path(__file__).parents[2] / "skills" / "docs-sync-check" / "SKILL.md"

  class TestDocsSyncCheckProjectMd:
      def _skill(self):
          return SKILL_PATH.read_text()

      def test_skill_reads_project_md(self):
          """Skill must instruct reading PROJECT.md."""
          assert "PROJECT.md" in self._skill(), \
              "docs-sync-check SKILL.md must mention PROJECT.md"

      def test_skill_has_step_3b(self):
          """Skill must contain a Step 3b block."""
          assert "3b" in self._skill(), \
              "docs-sync-check SKILL.md must have a Step 3b"

      def test_skill_strips_slash_prefix(self):
          """Skill must document stripping / prefix from command names."""
          skill = self._skill()
          assert "strip" in skill.lower() or "strip `/`" in skill or "strip the `/`" in skill, \
              "Skill must document stripping / prefix from PROJECT.md command rows"

      def test_skill_excludes_header_rows(self):
          """Skill must document skipping header rows."""
          skill = self._skill()
          assert "header" in skill.lower() or "| Command |" in skill or "| --- |" in skill, \
              "Skill must document skipping table header rows"

      def test_verdict_has_project_md_stale(self):
          """Returned JSON verdict must include project_md_stale field."""
          assert "project_md_stale" in self._skill(), \
              "docs-sync-check verdict JSON must include project_md_stale"

      def test_verdict_has_missing_and_extra_fields(self):
          """Returned JSON verdict must include missing_from_project_md and extra_in_project_md."""
          skill = self._skill()
          assert "missing_from_project_md" in skill, \
              "Verdict must include missing_from_project_md"
          assert "extra_in_project_md" in skill, \
              "Verdict must include extra_in_project_md"
  ```

  Run: `make test-unit` — must **FAIL** (6 new tests fail: no Step 3b in skill yet)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/docs-sync-check/SKILL.md`. After existing Step 3, insert new Step 3b and
  update the returned JSON block in Step 5.

  **Insert after Step 3 block** (before "4. **Compare**"):

  ```markdown
  3b. **Read PROJECT.md** — parse Commands and Skills tables:
      - Read `PROJECT.md` at the project root. If missing → set `project_md_stale: false`,
        append "PROJECT.md not found — skipped" to `details`, skip cross-reference.
      - Extract Commands table: every `| /command |` row. Skip header rows
        (`| Command |`, `| --- |`). Strip the leading `/` from each command name.
        Strip `.md` suffix from disk basenames before comparing.
      - Extract Skills table: every `| skill-name |` row. Skip header rows
        (`| Skill |`, `| --- |`). Skill names are bare (no path prefix).
      - If a Commands or Skills table is absent from PROJECT.md, treat as empty
        (all disk items → `missing_from_project_md`).
      - Cross-reference:
        - `missing_from_project_md`: commands/skills on disk NOT in PROJECT.md tables.
        - `extra_in_project_md`: entries in PROJECT.md tables NOT found on disk.
      - Set `project_md_stale: true` if either list is non-empty; `false` otherwise.
  ```

  **Update Step 5 JSON block** — replace the existing JSON example with:

  ```json
  {
    "claude_md_stale": false,
    "readme_stale": false,
    "project_md_stale": false,
    "missing_from_docs": [],
    "extra_in_docs": [],
    "missing_from_project_md": [],
    "extra_in_project_md": [],
    "details": "CLAUDE.md in sync | README.md in sync | PROJECT.md in sync"
  }
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  - Verify `make lint` is clean (no markdownlint violations — line length ≤ 120).
  - Confirm the existing six tests in `TestDocsSyncCheckGeneralAgent` still pass.
  - Confirm Step 3b is positioned correctly between Step 3 and Step 4 in the skill.

  Run: `make test-unit` — still **PASS**

---

## Task 2: Update Verdict JSON Rendering in Skill

<!-- depends_on: Task 1 -->

**Note:** This task is included only if Task 1's Step 5 JSON update did not fully land in a single edit. If Task 1 fully updates both the step prose and the JSON block, this task is a no-op and can be skipped after verifying the verdict output section.

**Acceptance Criteria:**
- The JSON example in Step 5 of `skills/docs-sync-check/SKILL.md` contains all seven fields:
  `claude_md_stale`, `readme_stale`, `project_md_stale`, `missing_from_docs`,
  `extra_in_docs`, `missing_from_project_md`, `extra_in_project_md`
- The `details` string in the example reflects PROJECT.md sync status

**Files:**
- Modify: `skills/docs-sync-check/SKILL.md` (Step 5 JSON only, if not already updated in Task 1)

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Extend TestDocsSyncCheckProjectMd with:
  def test_verdict_details_mentions_project_md(self):
      """details string in verdict example must mention PROJECT.md."""
      assert "PROJECT.md" in self._skill(), \
          "Verdict details must mention PROJECT.md sync status"
  ```

  Run: `make test-unit` — only fails if Task 1 didn't include the details string

- [ ] **Step 2: Implement (GREEN)**

  If the `details` string in Step 5 does not mention `PROJECT.md`, update it:

  ```
  "details": "CLAUDE.md in sync | README.md in sync | PROJECT.md in sync"
  ```

  Run: `make test-unit` — must **PASS**

- [ ] **Step 3: Refactor**

  No additional refactor needed — skill is now fully updated.

  Run: `make test-unit` — still **PASS**

---

## Verification

After both tasks pass:

```bash
make test-fast    # changed files only — expect green
make lint         # markdownlint on all .md files
make test-unit    # full unit suite — expect green, coverage ≥ 48%
```

Expected: all green, no regressions.
