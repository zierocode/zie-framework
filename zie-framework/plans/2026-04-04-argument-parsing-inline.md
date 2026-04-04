---
approved: true
approved_at: 2026-04-04
backlog: backlog/argument-parsing-inline.md
---

# Argument Parsing Block Compression — Implementation Plan

**Goal:** Replace verbose Python-style argument parsing preambles in `commands/spec.md` and `commands/sprint.md` with compact argument tables and inline flag handling, reducing token cost without breaking any test assertions.

**Architecture:** Two command files are edited independently — each has its Python parsing block removed, replaced with a `## Arguments` table, and flag-handling logic moved inline to the consuming step. Tests read raw file text and check for specific keyword tokens; edits must preserve those tokens in the inline prose.

**Tech Stack:** Markdown (command files only) — no Python, no hooks.

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/spec.md` | Remove Python parse block; add/update Arguments table; inline `--draft-plan` note at step 4; keep `remove` token |
| Modify | `commands/sprint.md` | Remove `## Parse Arguments` Python block; add Arguments table with `--dry-run`, `--skip-ready`, `--version=X.Y.Z`, `slugs`; keep inline references at consuming steps |

---

## Task 1: Compress `commands/spec.md` argument parsing

**Acceptance Criteria:**
- Python parse block (`draft_plan = ...` / `clean_args = ...`) is removed
- `## Arguments` table documents `--draft-plan` flag (already present — verify or update format)
- Step 4 contains inline note using the word `remove` (e.g., "remove `--draft-plan` from slug extraction") to satisfy `test_flag_removed_from_slug_extraction`
- `--draft-plan`, `write-plan`, `/plan`, `Next:` tokens all remain in file
- `make test-unit` passes (all `TestZieSpecDraftPlanFlag` assertions)

**Files:**
- Modify: `commands/spec.md`

- [ ] **Step 1: Write failing tests (RED)**

  Run existing suite to confirm current state:
  ```bash
  cd /Users/zie/Code/zie-framework && python -m pytest tests/unit/test_workflow_lean.py::TestZieSpecDraftPlanFlag -v
  ```
  Expected: all 4 tests PASS (baseline). Confirm `test_flag_removed_from_slug_extraction` passes via `clean_args` token currently present in the Python block. After edit removes `clean_args`, the test must still pass via `remove` token instead.

  Verify the test assertion:
  ```python
  # test_flag_removed_from_slug_extraction checks:
  assert "clean_args" in text or "remove" in text.lower() or '!= "--draft-plan"' in text
  ```
  After removing the Python block, `clean_args` will be gone — so the edit MUST include `remove` in step 4.

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/spec.md`:

  1. Remove the parse block under `## Arguments` (lines 29–34 currently):
     ```
     **Parse before step 1:**
     ```python
     draft_plan = "--draft-plan" in ARGUMENTS
     clean_args = " ".join(arg for arg in ARGUMENTS.split() if arg != "--draft-plan")
     # Use clean_args for all slug/idea extraction below
     ```
     ```
  
  2. Update the `## Arguments` section to a clean table with a default column:
     ```markdown
     ## Arguments
     
     | Flag | Description | Default |
     | --- | --- | --- |
     | `--draft-plan` | After spec approved, auto-invoke `write-plan` and move plan to Ready if approved. Skips manual `/plan` step. | off |
     ```
  
  3. In step 4 header, add an inline note that includes `remove`:
     ```markdown
     ## Steps
     ...
     4. **--draft-plan branch** (if `--draft-plan` present — remove `--draft-plan` from slug extraction before processing):
     ```
     (The note naturally communicates that the flag is stripped from the slug arg; the word `remove` satisfies the test.)

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Re-read `commands/spec.md` and confirm prose flows naturally. Ensure no orphaned references to `clean_args` or `draft_plan` variables remain.

  Run: `make test-unit` — still PASS

---

## Task 2: Compress `commands/sprint.md` argument parsing

<!-- depends_on: none -->

**Acceptance Criteria:**
- `## Parse Arguments` Python block removed
- New `## Arguments` table documents all four flags: `--dry-run`, `--skip-ready`, `--version=X.Y.Z`, and slug filtering (with `slugs` token present)
- Inline references to `--dry-run`, `--skip-ready`, `--version=` remain at their consuming steps (they already exist in Step 0.6, Phase 3, etc.)
- `slugs` token appears in the argument table or an inline note
- `make test-unit` passes (all `TestArgumentParsing` assertions)

**Files:**
- Modify: `commands/sprint.md`

- [ ] **Step 1: Write failing tests (RED)**

  Run baseline:
  ```bash
  cd /Users/zie/Code/zie-framework && python -m pytest tests/unit/test_zie_sprint.py::TestArgumentParsing -v
  ```
  Expected: all 3 tests PASS (baseline — Python block currently provides the tokens).

  After removing the block, tokens `--skip-ready`, `--version=`, and `slugs` must still be present. Confirm where they currently appear outside the block:
  - `--skip-ready`: in Step 0.6 (`skip_ready=true`) — present as `--skip-ready` in audit step already
  - `--version=`: in Phase 3 (`--bump-to=<version_override>`) — present as text, but `--version=` itself only in parse block
  - `slugs`: only in parse block currently

  The argument table must carry `--version=X.Y.Z` and `slugs` explicitly.

- [ ] **Step 2: Implement (GREEN)**

  Edit `commands/sprint.md`:

  1. Remove the `## Parse Arguments` section (the Python block, lines 22–35 currently):
     ```markdown
     ## Parse Arguments
     
     ```python
     dry_run = "--dry-run" in ARGUMENTS
     skip_ready = "--skip-ready" in ARGUMENTS
     version_override = None
     
     # Extract --version=X.Y.Z
     for arg in ARGUMENTS.split():
         if arg.startswith("--version="):
             version_override = arg.split("=")[1]
     
     # Extract slugs (remaining args)
     slugs = [arg for arg in ARGUMENTS.split() if not arg.startswith("--")]
     ```
     ```
  
  2. Add an `## Arguments` table after `## ตรวจสอบก่อนเริ่ม` and before `## Step 0`:
     ```markdown
     ## Arguments
     
     | Flag / Positional | Description | Default |
     | --- | --- | --- |
     | `slugs` (positional) | Space-separated backlog slugs to process; omit to process all Next+Ready items | all items |
     | `--dry-run` | Print sprint audit table and stop — do not execute | off |
     | `--skip-ready` | Skip items already in Ready lane (spec+plan approved) | off |
     | `--version=X.Y.Z` | Override version bump for Phase 3 release | auto |
     
     Flag handling is inline at each consuming step below.
     ```
  
  3. Verify that inline usages at consuming steps still reference the flags naturally:
     - Step 0.6 already says `if dry_run=true` — update prose to `if --dry-run present`
     - Phase 3 already says `--bump-to=<version_override>` — no change needed; `--version=` is in the table
     - No other changes required

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Re-read `commands/sprint.md` and confirm Step 0.6 dry-run prose is consistent with removed variable names. Replace any remaining `dry_run=true` variable references with plain English (`if --dry-run present`).

  Run: `make test-unit` — still PASS

---

## Final verification

After both tasks:

```bash
cd /Users/zie/Code/zie-framework && make test-unit
```

Expected: all tests green, including:
- `TestZieSpecDraftPlanFlag` (4 tests)
- `TestArgumentParsing` (3 tests)

Also run lint:
```bash
make lint
```
