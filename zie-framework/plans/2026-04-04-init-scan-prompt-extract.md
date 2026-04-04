---
approved: true
approved_at: 2026-04-04
backlog: backlog/init-scan-prompt-extract.md
---

# Init Scan Prompt Extract — Implementation Plan

**Goal:** Extract the ~400-word Explore agent prompt from `commands/init.md` into `templates/init-scan-prompt.md` and compress two prose-heavy sections to reduce command bloat without changing any behaviour.

**Architecture:** Single-file extraction — the inline prompt block moves verbatim to a new template file; `init.md` gains a one-line reference `Prompt: see templates/init-scan-prompt.md`. Two prose sections (re-run guard, Makefile negotiation) are compressed from narrative paragraphs to tight checklists. All tests that grep `commands/init.md` for strings inside the extracted block must be confirmed absent before extraction proceeds.

**Tech Stack:** Markdown, Python/pytest (`make test-unit`)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `templates/init-scan-prompt.md` | Verbatim Explore agent prompt extracted from `init.md` |
| Modify | `commands/init.md` | Remove inline prompt block; add reference line; compress re-run guard + Makefile sections |
| Create | `tests/unit/test_init_scan_prompt_extract.py` | Verify template exists, reference line present, compressed sections pass existing assertions |

---

## Task Sizing

3 tasks — S plan (single-session).

---

## Task 1: Write tests and audit existing grep targets

**Acceptance Criteria:**
- `tests/unit/test_init_scan_prompt_extract.py` exists with 4 tests covering: template exists, reference line present, inline prompt body absent, template contains body.
- Confirm no existing test file greps for strings inside lines 68–115 of `commands/init.md` (those strings will move to the template).

**Files:**
- Create: `tests/unit/test_init_scan_prompt_extract.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_init_scan_prompt_extract.py` — this IS the implementation for Task 1:

  ```python
  # tests/unit/test_init_scan_prompt_extract.py
  import os, re

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  INIT_MD   = os.path.join(REPO_ROOT, "commands", "init.md")
  TEMPLATE  = os.path.join(REPO_ROOT, "templates", "init-scan-prompt.md")

  class TestTemplateExists:
      def test_template_file_exists(self):
          assert os.path.isfile(TEMPLATE), "templates/init-scan-prompt.md must exist"

      def test_init_md_has_reference_line(self):
          with open(INIT_MD) as f:
              content = f.read()
          assert "templates/init-scan-prompt.md" in content, (
              "commands/init.md must reference templates/init-scan-prompt.md"
          )

      def test_init_md_does_not_contain_inline_prompt_body(self):
          """The verbatim prompt block must not remain inline in init.md."""
          with open(INIT_MD) as f:
              content = f.read()
          # A distinctive string from inside the extracted prompt body
          assert "The parent parser will extract JSON from the first" not in content, (
              "Inline prompt body must be extracted to templates/init-scan-prompt.md"
          )

      def test_template_contains_prompt_body(self):
          with open(TEMPLATE) as f:
              content = f.read()
          assert "The parent parser will extract JSON from the first" in content, (
              "templates/init-scan-prompt.md must contain the extracted prompt body"
          )
  ```

  Run: `make test-unit` — must **FAIL** (template doesn't exist yet).

- [ ] **Step 2: Implement (GREEN)**

  Tests written in Step 1 will fail until Task 2 creates the template and Task 3 edits `init.md`. No further work in Task 1 — proceed to Task 2.

- [ ] **Step 3: Refactor**

  N/A — test file only, no refactor needed. Run: `make test-unit` — all 4 new tests should FAIL (expected at this stage).

---

## Task 2: Create `templates/init-scan-prompt.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `templates/init-scan-prompt.md` exists and contains the verbatim prompt from `commands/init.md` lines 68–115 (the full content inside the fenced code block, without the fences or surrounding blockquote markers).
- Template file is self-contained: begins with the `You are scanning...` sentence and ends with `If a field cannot be determined, use null for scalars or [] for arrays.`

**Files:**
- Create: `templates/init-scan-prompt.md`

- [ ] **Step 1: Write failing tests (RED)**

  Tests already written in Task 1 (`test_template_file_exists`, `test_template_contains_prompt_body`). Confirm they fail:

  Run: `make test-unit` — must **FAIL**.

- [ ] **Step 2: Implement (GREEN)**

  Create `templates/init-scan-prompt.md` with the extracted prompt (verbatim, no fences, no blockquote `>` prefixes):

  ```markdown
  You are scanning an existing software project to help initialize zie-framework.

  Scan the project at the current working directory. Read existing documentation
  first as primary sources (they encode deliberate intent, not just structure):
    README.md, CHANGELOG.md, ARCHITECTURE.md, AGENTS.md,
    docs/**, **/specs/*.md, **/plans/*.md, **/decisions/*.md
    (exclude anything inside zie-framework/)

  Then scan the codebase structure to fill in any gaps.

  Exclude from all scans:
    node_modules/, .git/, build/, dist/, .next/, __pycache__/, *.pyc,
    coverage/, zie-framework/

  Return ONLY a JSON object with this exact structure (no markdown, no prose).
  The parent parser will extract JSON from the first '{' to the last '}'.

  {
    "architecture_pattern": "<string>",
    "components": [{ "name": "<string>", "purpose": "<one-line string>" }],
    "tech_stack": [{ "name": "<string>", "version": "<string | null>" }],
    "data_flow": "<string>",
    "key_constraints": ["<string>"],
    "test_strategy": { "runner": "<string | null>", "coverage_areas": ["<string>"] },
    "active_areas": ["<string>"],
    "existing_hooks": "<path to hooks/hooks.json if present, else null>",
    "existing_config": "<path to zie-framework/.config if present, else null>",
    "migration_candidates": {
      "specs":      ["<relative path>"],
      "plans":      ["<relative path>"],
      "decisions":  ["<relative path>"],
      "backlog":    ["<relative path>"]
    }
  }

  For migration_candidates: include files matching these patterns (excluding
  anything already inside zie-framework/):
    specs:     **/specs/*.md, **/spec/*.md
    plans:     **/plans/*.md, **/plan/*.md
    decisions: **/decisions/*.md, **/adr/*.md, ADR-*.md (at project root)
    backlog:   **/backlog/*.md

  For existing_hooks: check if hooks/hooks.json exists at project root.
  For existing_config: check if zie-framework/.config exists.
  If a field cannot be determined, use null for scalars or [] for arrays.
  ```

  Run: `make test-unit` — `test_template_file_exists` and `test_template_contains_prompt_body` must now **PASS**.

- [ ] **Step 3: Refactor**

  Confirm no trailing whitespace or encoding issues. Run: `make test-unit` — still **PASS**.

---

## Task 3: Edit `commands/init.md` — replace inline prompt + compress prose sections

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- The inline Explore agent prompt block (lines 68–115) is removed from `commands/init.md` and replaced with a single reference line: `Prompt: see \`templates/init-scan-prompt.md\``
- Re-run guard section (step 0, ~80 words) is compressed to a checklist of ≤40 words with identical semantics.
- Makefile negotiation section (step 7, ~120 words) is compressed to a tight checklist of ≤60 words.
- All existing tests in `test_commands_zie_init.py`, `test_zie_init_deep_scan.py`, and `test_zie_init_templates.py` continue to pass — no assertions broken.
- New tests from Task 1 pass (`test_init_md_has_reference_line`, `test_init_md_does_not_contain_inline_prompt_body`).

**Files:**
- Modify: `commands/init.md`

- [ ] **Step 1: Write failing tests (RED)**

  By Task 3 start, Task 2 already created the template — so `test_template_file_exists` and `test_template_contains_prompt_body` now PASS. The two remaining failing tests are:
  - `test_init_md_has_reference_line` — fails because `init.md` doesn't have the reference yet
  - `test_init_md_does_not_contain_inline_prompt_body` — fails because the inline prompt block is still in `init.md`

  Confirm these two still fail before editing:

  Run: `make test-unit` — `test_init_md_has_reference_line` and `test_init_md_does_not_contain_inline_prompt_body` must **FAIL**.

- [ ] **Step 2: Implement (GREEN)**

  **2a. Replace the inline prompt block in `commands/init.md`.**

  Locate step 2a in `commands/init.md`:

  ```
     a. Invoke `Agent(subagent_type=Explore)` with the following
        self-contained prompt. Receive `scan_report` JSON.

        > **Explore agent prompt (self-contained — pass verbatim):**
        >
        > ```
        > You are scanning an existing software project...
        > ...If a field cannot be determined, use null for scalars or [] for arrays.
        > ```
  ```

  Replace the entire block above (from `a. Invoke` down to the closing triple-backtick and the blank line after it) with:

  ```markdown
     a. Invoke `Agent(subagent_type=Explore)` with the prompt from
        `templates/init-scan-prompt.md` (read the file verbatim — pass as prompt).
        Receive `scan_report` JSON.

        Prompt: see `templates/init-scan-prompt.md`
  ```

  **2b. Compress re-run guard (step 0).**

  Replace the current step 0 prose (from `**Re-run guard**` to just before step 1) with:

  ```markdown
  0. **Re-run guard** — if `zie-framework/` exists:
     - **Complete** (`PROJECT.md` + `project/architecture.md` + non-empty `knowledge_hash` in `.config`): print "Already initialized." → skip to Step 3.
     - **Incomplete** (missing docs or empty `knowledge_hash`): print "Existing framework found, but knowledge scan not yet done. Scanning codebase..." → Step 2 (skip project-type detect if `.config` has `project_type`).
     - **Absent**: proceed from Step 1.
  ```

  **2c. Compress Makefile negotiation (step 7).**

  Replace step 7 prose with:

  ```markdown
  7. **Negotiate `_bump-extra` + `_publish`** in `Makefile.local`:
     - If `_bump-extra` is already a real command (not `@true`): skip.
     - If stub: ask "Which version files need bumping?" — suggest by `project_type` (pyproject.toml / plugin.json / npm version). Present draft; `yes` → write, `no` → leave stub, `edit` → redraft.
     - Ask separately: "Need a publish step? (gh release / npm publish / docker push / no)" — write `_publish` recipe if yes, else leave as `@true`.
  ```

  Run: `make test-unit` — ALL tests must **PASS**.

- [ ] **Step 3: Refactor**

  - Verify `commands/init.md` line count is meaningfully reduced (target: ≥40 lines shorter).
  - Confirm `make lint` passes.
  - Run: `make test-unit` — still **PASS**.

---

## Dependency Graph

```
Task 1 (audit + write tests)
  └── Task 2 (create template) → Task 3 (edit init.md)
```

Tasks 1 and 2 are sequential (Task 2 makes Task 1's tests pass). Task 3 depends on Task 2.
