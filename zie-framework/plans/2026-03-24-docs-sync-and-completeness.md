---
approved: true
approved_at: 2026-03-24
backlog: backlog/docs-sync-and-completeness.md
spec: specs/2026-03-24-docs-sync-and-completeness-design.md
---

# Docs: Sync and Completeness Pass — Implementation Plan

**Goal:** Six targeted doc edits to fix version drift, stale table headers, missing version history entries, an undocumented utility script, missing optional-deps table, and a missing Skills section in README.
**Architecture:** All doc changes, no code changes. Each task follows RED (write failing assertion test) → GREEN (apply doc edit) → REFACTOR (verify no regressions).
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Add `$(MAKE) sync-version` as a step inside the `bump` target |
| Modify | `zie-framework/PROJECT.md` | Fix version 1.6.0 → 1.8.0; rename "ทำอะไร" → "Description" |
| Modify | `zie-framework/project/architecture.md` | Add v1.5.0–v1.8.0 version history entries |
| Modify | `zie-framework/project/components.md` | Add `knowledge-hash.py` utility script entry |
| Modify | `CLAUDE.md` | Add Optional Dependencies table; add `make sync-version` to Development Commands |
| Modify | `README.md` | Add Skills section after Commands |
| Create | `tests/unit/test_docs_sync.py` | Doc-state assertion tests for all six changes |

---

## Task 1: Makefile — wire `sync-version` into `bump`

**Acceptance Criteria:**
- `make bump NEW=x.y.z` calls `$(MAKE) sync-version` after updating VERSION and plugin.json
- `make bump` comment reflects that PROJECT.md is now also updated
- Running `make bump NEW=1.8.0` twice produces no diff (idempotent)

**Files:**
- Modify: `Makefile`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Create tests/unit/test_docs_sync.py

  """Doc-state assertions for docs-sync-and-completeness pass."""
  from pathlib import Path

  REPO_ROOT = Path(__file__).parent.parent.parent


  class TestMakfileBumpCallsSyncVersion:
      def test_bump_target_calls_sync_version(self):
          """bump target must call $(MAKE) sync-version."""
          content = (REPO_ROOT / "Makefile").read_text()
          # Find the bump: block and check it contains sync-version
          in_bump = False
          for line in content.splitlines():
              if line.startswith("bump:"):
                  in_bump = True
              elif in_bump and line.startswith(("# ", "release:", "sync-version:", "setup:")):
                  break
              if in_bump and "sync-version" in line:
                  return  # found
          raise AssertionError("bump target does not call sync-version")
  ```

  Run: `make test-unit` — must FAIL (bump target currently ends at `@echo "Bumped to v$(NEW)"` with no sync-version call)

---

- [ ] **Step 2: Implement (GREEN)**

  In `Makefile`, replace the `bump` target comment and add the `$(MAKE) sync-version` line:

  ```makefile
  # BEFORE:
  bump: ## Atomically bump VERSION + plugin.json (usage: make bump NEW=1.2.3)
      ...
      @sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
      @echo "Bumped to v$(NEW)"

  # AFTER:
  bump: ## Atomically bump VERSION + plugin.json + PROJECT.md (usage: make bump NEW=1.2.3)
      ...
      @sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
      @$(MAKE) sync-version
      @echo "Bumped to v$(NEW)"
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  `sync-version` is already idempotent (sed regex replaces the exact pattern, jq overwrites with the same value on re-run). No cleanup needed.

  Run: `make test-unit` — still PASS

---

## Task 2: PROJECT.md — version + table header fix

**Acceptance Criteria:**
- Line 7 reads `**Version**: 1.8.0  **Status**: active`
- Commands table header reads `| Command | Description |`

**Files:**
- Modify: `zie-framework/PROJECT.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Append to tests/unit/test_docs_sync.py

  class TestProjectMd:
      def _content(self):
          return (REPO_ROOT / "zie-framework" / "PROJECT.md").read_text()

      def test_version_is_1_8_0(self):
          """PROJECT.md must show Version 1.8.0."""
          assert "**Version**: 1.8.0" in self._content(), (
              "PROJECT.md version is not 1.8.0 — run: make sync-version"
          )

      def test_commands_table_header_is_english(self):
          """Commands table header must use 'Description', not Thai."""
          content = self._content()
          assert "ทำอะไร" not in content, (
              "PROJECT.md still contains Thai header 'ทำอะไร'"
          )
          assert "| Command | Description |" in content, (
              "Commands table header 'Description' not found"
          )
  ```

  Run: `make test-unit` — must FAIL (version shows 1.6.0; header is "ทำอะไร")

---

- [ ] **Step 2: Implement (GREEN)**

  Run `make sync-version` first to fix the version. Then manually replace the table header.

  In `zie-framework/PROJECT.md`:
  - Run: `make sync-version` (fixes version 1.6.0 → 1.8.0 via sed)
  - Edit line 13: `| Command | ทำอะไร |` → `| Command | Description |`

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Verify the Skills and Agents tables still render correctly (no unintended edits).
  The "ทำอะไร" change is isolated to the Commands table header only.

  Run: `make test-unit` — still PASS

---

## Task 3: architecture.md — version history v1.5.0–v1.8.0

**Acceptance Criteria:**
- Four new entries appear after the v1.4.0 bullet
- v1.5.0, v1.6.0, v1.7.0, v1.8.0 are all present with correct dates and summaries

**Files:**
- Modify: `zie-framework/project/architecture.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Append to tests/unit/test_docs_sync.py

  class TestArchitectureMd:
      def _content(self):
          return (REPO_ROOT / "zie-framework" / "project" / "architecture.md").read_text()

      def test_v1_5_0_entry_exists(self):
          assert "**v1.5.0**" in self._content(), "v1.5.0 entry missing from architecture.md"

      def test_v1_6_0_entry_exists(self):
          assert "**v1.6.0**" in self._content(), "v1.6.0 entry missing from architecture.md"

      def test_v1_7_0_entry_exists(self):
          assert "**v1.7.0**" in self._content(), "v1.7.0 entry missing from architecture.md"

      def test_v1_8_0_entry_exists(self):
          assert "**v1.8.0**" in self._content(), "v1.8.0 entry missing from architecture.md"

      def test_v1_5_0_mentions_knowledge_hash(self):
          """v1.5.0 entry must reference knowledge-hash.py extraction."""
          assert "knowledge-hash.py" in self._content(), (
              "v1.5.0 entry should mention knowledge-hash.py"
          )
  ```

  Run: `make test-unit` — must FAIL (version history stops at v1.4.0)

---

- [ ] **Step 2: Implement (GREEN)**

  In `zie-framework/project/architecture.md`, append after the v1.4.0 bullet:

  ```markdown
  - **v1.5.0** (2026-03-23) — `parse_roadmap_section()` dedup; `knowledge-hash.py`
    extracted as standalone utility; `read_event()`/`get_cwd()` boilerplate dedup
    in utils; CHANGELOG annotations + SECURITY.md + Dependabot config.
  - **v1.6.0** (2026-03-23) — Session-wide agent modes (`zie-implement-mode`,
    `zie-audit-mode`); `notification-log` hook for permission/idle events;
    model+effort pinned on all skills and commands.
  - **v1.7.0** (2026-03-23) — 23-item sprint implementing v1.6.0 audit findings;
    Bandit B108 suppressions via config; pre-existing test pollution fixes.
  - **v1.8.0** (2026-03-24) — Parallel model-effort optimization — faster skill
    execution via parallel model selection; model:haiku for fast-path reviewers.
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Confirm "Last updated" date at the top of architecture.md reflects 2026-03-24 (current date). Update if still showing 2026-03-23.

  Run: `make test-unit` — still PASS

---

## Task 4: components.md — document `knowledge-hash.py`

**Acceptance Criteria:**
- `knowledge-hash.py` appears in components.md under a "Utility Scripts" subsection
- Entry explicitly states it is not registered in hooks.json
- Entry links its invocation context (`/zie-resync`)

**Files:**
- Modify: `zie-framework/project/components.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Append to tests/unit/test_docs_sync.py

  class TestComponentsMd:
      def _content(self):
          return (REPO_ROOT / "zie-framework" / "project" / "components.md").read_text()

      def test_knowledge_hash_entry_exists(self):
          assert "knowledge-hash.py" in self._content(), (
              "knowledge-hash.py not documented in components.md"
          )

      def test_knowledge_hash_not_in_hooks_section(self):
          """knowledge-hash.py must be in a utility section, not listed as a hook."""
          content = self._content()
          # The Hooks table header line must NOT contain knowledge-hash.py
          in_hooks = False
          for line in content.splitlines():
              if line.startswith("## Hooks"):
                  in_hooks = True
              elif in_hooks and line.startswith("## "):
                  break
              if in_hooks and "knowledge-hash.py" in line:
                  raise AssertionError(
                      "knowledge-hash.py is listed inside the Hooks section — "
                      "it should be in a Utility Scripts section"
                  )

      def test_utility_scripts_section_exists(self):
          assert "Utility Scripts" in self._content(), (
              "No 'Utility Scripts' section found in components.md"
          )
  ```

  Run: `make test-unit` — must FAIL (knowledge-hash.py not in components.md)

---

- [ ] **Step 2: Implement (GREEN)**

  In `zie-framework/project/components.md`, add a new section after the Hooks table:

  ```markdown
  ### Utility Scripts (not hook event handlers)

  | Script | Purpose |
  | --- | --- |
  | `hooks/knowledge-hash.py` | Compute SHA-256 of project structure for drift detection. Called by `make resync` / `/zie-resync`. Not registered in hooks.json. |
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Confirm the section heading level is consistent with the rest of components.md (use `###` to match the Agents field-reference section). No content changes needed.

  Run: `make test-unit` — still PASS

---

## Task 5: CLAUDE.md — Optional Dependencies table + sync-version command

**Acceptance Criteria:**
- An "Optional Dependencies" section exists under Tech Stack with a 4-row table
- `make sync-version` appears in Development Commands with a descriptive comment

**Files:**
- Modify: `CLAUDE.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Append to tests/unit/test_docs_sync.py

  class TestClaudeMd:
      def _content(self):
          return (REPO_ROOT / "CLAUDE.md").read_text()

      def test_optional_dependencies_section_exists(self):
          assert "Optional Dependencies" in self._content(), (
              "CLAUDE.md missing 'Optional Dependencies' section"
          )

      def test_optional_deps_table_has_playwright(self):
          assert "playwright" in self._content(), (
              "Optional Dependencies table missing playwright row"
          )

      def test_optional_deps_table_has_zie_memory(self):
          assert "zie-memory" in self._content() or "zie_memory" in self._content(), (
              "Optional Dependencies table missing zie-memory row"
          )

      def test_sync_version_in_dev_commands(self):
          assert "sync-version" in self._content(), (
              "CLAUDE.md Development Commands missing 'make sync-version'"
          )
  ```

  Run: `make test-unit` — must FAIL (no Optional Dependencies section; sync-version not in dev commands)

---

- [ ] **Step 2: Implement (GREEN)**

  In `CLAUDE.md`, after the Tech Stack bullet list and before Project Structure, add:

  ```markdown
  ### Optional Dependencies

  | Dependency | Purpose | Required? |
  | --- | --- | --- |
  | `pytest` + `pytest-cov` | Unit + integration test runner | For `make test` |
  | `coverage` | Subprocess coverage measurement | For `make test-unit` |
  | `playwright` | Browser automation for frontend hooks | Only if `playwright_enabled: true` |
  | zie-memory API | Cross-session memory persistence | Only if `zie_memory_enabled: true` |
  ```

  In `CLAUDE.md`, inside the Development Commands code block, add:

  ```bash
  make sync-version  # sync plugin.json + PROJECT.md version to match VERSION file
                     # also call before make release — release does not call bump
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Confirm the new section does not break `make lint-md` (markdownlint). Table syntax must use `| --- |` separators and not have trailing spaces.

  Run: `make test-unit` — still PASS
  Run: `make lint-md` — exits 0

---

## Task 6: README.md — add Skills section

**Acceptance Criteria:**
- A "Skills" section exists in README.md with a table of 11 skills
- Content mirrors the Skills table in PROJECT.md
- Section is positioned after Commands (before Pipeline or Configuration)

**Files:**
- Modify: `README.md`

---

- [ ] **Step 1: Write failing test (RED)**

  ```python
  # Append to tests/unit/test_docs_sync.py

  class TestReadmeMd:
      def _content(self):
          return (REPO_ROOT / "README.md").read_text()

      def test_skills_section_exists(self):
          assert "## Skills" in self._content(), (
              "README.md missing ## Skills section"
          )

      def test_skills_table_has_tdd_loop(self):
          assert "tdd-loop" in self._content(), (
              "Skills table missing tdd-loop entry"
          )

      def test_skills_table_has_zie_audit(self):
          assert "zie-audit" in self._content(), (
              "Skills table missing zie-audit entry"
          )

      def test_skills_section_mentions_subagents(self):
          content = self._content()
          assert "subagent" in content.lower() or "automatically" in content.lower(), (
              "Skills section should explain skills are invoked automatically"
          )
  ```

  Run: `make test-unit` — must FAIL (no Skills section in README.md)

---

- [ ] **Step 2: Implement (GREEN)**

  In `README.md`, insert the following section after the `## Commands` table block and before `## Pipeline`:

  ```markdown
  ## Skills

  Skills are invoked automatically by commands as subagents — not called directly.

  | Skill | Purpose |
  | --- | --- |
  | `spec-design` | Draft design spec from backlog item |
  | `spec-reviewer` | Review spec for completeness and correctness |
  | `write-plan` | Convert approved spec into implementation plan |
  | `plan-reviewer` | Review plan for feasibility and test coverage |
  | `tdd-loop` | RED/GREEN/REFACTOR loop for a single task |
  | `impl-reviewer` | Review implementation against spec and plan |
  | `verify` | Post-implementation verification gate |
  | `test-pyramid` | Test strategy advisor |
  | `retro-format` | Format retrospective findings as ADRs |
  | `debug` | Systematic bug diagnosis and fix path |
  | `zie-audit` | 9-dimension audit analysis (invoked by /zie-audit) |
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Run `make lint-md` to confirm no markdownlint violations from the new section. Verify the README project structure tree (line 87: `project/context.md` shows extra nesting as `project/project/context.md`) — fix only if the nesting is incorrect in the current file.

  Run: `make test-unit` — still PASS
  Run: `make lint-md` — exits 0

---

**Commit:** `git add Makefile zie-framework/PROJECT.md zie-framework/project/architecture.md zie-framework/project/components.md CLAUDE.md README.md tests/unit/test_docs_sync.py && git commit -m "fix: docs-sync-and-completeness — version drift, headers, history, utility scripts, optional deps, README skills"`
