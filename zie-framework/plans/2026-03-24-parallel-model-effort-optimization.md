---
approved: true
approved_at: 2026-03-24
backlog: backlog/parallel-model-effort-optimization.md
spec: specs/2026-03-24-parallel-model-effort-optimization-design.md
---

# Parallel Execution + Model/Effort Optimization — Implementation Plan

**Goal:** Upgrade model routing for quality-critical tasks, add `context: fork` to
prevent haiku context truncation, introduce parallel skill execution in retro/implement/release
commands, and remove dead frontmatter fields.
**Architecture:** Pure configuration/content changes to SKILL.md and command .md files. One new
skill (docs-sync-check). One test file update. No new Python code.
**Tech Stack:** Markdown (commands, skills), pytest (test assertions for frontmatter)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/tdd-loop/SKILL.md` | Remove `type: process` (non-official field) |
| Modify | `skills/test-pyramid/SKILL.md` | Remove `type: reference` (non-official field) |
| Modify | `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED + add type-field test |
| Modify | `skills/impl-reviewer/SKILL.md` | Upgrade model: haiku→sonnet, effort: low→medium |
| Modify | `commands/zie-spec.md` | Lower effort: high→medium |
| Modify | `commands/zie-plan.md` | Lower effort: high→medium |
| Create | `skills/docs-sync-check/SKILL.md` | New skill: haiku+fork, docs vs. disk comparison |
| Modify | `skills/retro-format/SKILL.md` | Remove `type: reference`; add `context: fork`; add `$ARGUMENTS` input section |
| Modify | `skills/verify/SKILL.md` | Add `context: fork`; add `$ARGUMENTS` input section with fallback |
| Modify | `commands/zie-retro.md` | Fork retro-format + docs-sync-check in parallel while parent writes ADRs |
| Modify | `commands/zie-implement.md` | Fork verify after final test run, overlap with ROADMAP update + commit prep |
| Modify | `commands/zie-release.md` | Fork docs-sync-check + TODOs grep after Gate 1, run parallel with Gate 2/3 |

---

## Task 1: Remove unofficial type fields from tdd-loop and test-pyramid

**Acceptance Criteria:**
- `skills/tdd-loop/SKILL.md` frontmatter has no `type:` key
- `skills/test-pyramid/SKILL.md` frontmatter has no `type:` key
- New test `test_no_unofficial_type_field` passes for all EXPECTED files

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`
- Modify: `skills/tdd-loop/SKILL.md`
- Modify: `skills/test-pyramid/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  Add to `TestAllFilesHaveBothKeys` class in `test_model_effort_frontmatter.py`:

  ```python
  def test_no_unofficial_type_field(self):
      unofficial = []
      for rel_path in EXPECTED:
          fm = parse_frontmatter(rel_path)
          if "type" in fm:
              unofficial.append(rel_path)
      assert unofficial == [], \
          "Unofficial 'type' field found in:\n" + "\n".join(unofficial)
  ```

  Run: `make test-unit` — must FAIL (tdd-loop has `type: process`, test-pyramid has `type: reference`)

- [ ] **Step 2: Implement (GREEN)**
  In `skills/tdd-loop/SKILL.md` frontmatter: remove the line `type: process`
  In `skills/test-pyramid/SKILL.md` frontmatter: remove the line `type: reference`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 2: Upgrade impl-reviewer to sonnet/medium

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/impl-reviewer/SKILL.md` has `model: sonnet` and `effort: medium`
- `TestExpectedValues` passes for impl-reviewer entry
- `TestHaikuFiles` does not include impl-reviewer in EXPECTED_HAIKU

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  In `test_model_effort_frontmatter.py`:

  1. Update EXPECTED:
     ```python
     "skills/impl-reviewer/SKILL.md": ("sonnet", "medium"),  # was ("haiku", "low")
     ```

  2. Remove from `TestHaikuFiles.EXPECTED_HAIKU`:
     ```python
     "skills/impl-reviewer/SKILL.md",  # remove this line
     ```

  Run: `make test-unit` — must FAIL (`test_correct_model_values` and `test_correct_effort_values`)

- [ ] **Step 2: Implement (GREEN)**
  In `skills/impl-reviewer/SKILL.md` frontmatter:
  - Line `model: haiku` → `model: sonnet`
  - Line `effort: low` → `effort: medium`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 3: Lower zie-spec and zie-plan effort to medium

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/zie-spec.md` has `effort: medium`
- `commands/zie-plan.md` has `effort: medium`
- `TestExpectedValues` passes for both

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`
- Modify: `commands/zie-spec.md`
- Modify: `commands/zie-plan.md`

- [ ] **Step 1: Write failing tests (RED)**
  In EXPECTED, update:
  ```python
  "commands/zie-spec.md": ("sonnet", "medium"),  # was ("sonnet", "high")
  "commands/zie-plan.md": ("sonnet", "medium"),  # was ("sonnet", "high")
  ```

  Run: `make test-unit` — must FAIL (`test_correct_effort_values` for both commands)

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-spec.md` frontmatter: `effort: high` → `effort: medium`
  In `commands/zie-plan.md` frontmatter: `effort: high` → `effort: medium`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 4: Create docs-sync-check skill

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/docs-sync-check/SKILL.md` exists with `model: haiku`, `effort: low`, `context: fork`
- `TestExpectedValues` passes for the new entry
- Skill documents `$ARGUMENTS` JSON input with `changed_files` field
- Skill returns structured JSON: `{claude_md_stale, readme_stale, missing_from_docs, extra_in_docs, details}`
- Graceful handling when CLAUDE.md or README.md missing (stale=false, note in details)

**Files:**
- Modify: `tests/unit/test_model_effort_frontmatter.py`
- Create: `skills/docs-sync-check/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  Add to EXPECTED:
  ```python
  "skills/docs-sync-check/SKILL.md": ("haiku", "low"),
  ```

  Run: `make test-unit` — must FAIL (FileNotFoundError when test tries to read missing file)

- [ ] **Step 2: Implement (GREEN)**
  Create `skills/docs-sync-check/SKILL.md`:

  ```markdown
  ---
  name: docs-sync-check
  description: Verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk. Returns JSON verdict.
  user-invocable: false
  context: fork
  allowed-tools: Read, Glob
  argument-hint: ""
  model: haiku
  effort: low
  ---

  # docs-sync-check — Living Docs Verification

  Verify that `CLAUDE.md` and `README.md` reflect the actual state of commands,
  skills, and hooks on disk. Called by `/zie-retro` and `/zie-release` as a
  parallel fork.

  ## Input

  `$ARGUMENTS` (optional JSON from caller):

  ```json
  {
    "changed_files": ["commands/zie-foo.md", "skills/bar/SKILL.md"]
  }
  ```

  If empty or unparseable: run full check across all commands/skills/hooks.

  ## Steps

  1. **Read CLAUDE.md** (project root) — extract lines mentioning `commands/`,
     `skills/`, `hooks/`. If missing → note in details, set `claude_md_stale: false`.

  2. **Read README.md** (project root) — extract commands table if present.
     If missing → note in details, set `readme_stale: false`.

  3. **Enumerate actual state**:
     - Glob `commands/*.md` → extract base filenames (strip `.md`).
     - Glob `skills/*/SKILL.md` → extract parent directory names.
     - Glob `hooks/*.py` → extract base filenames (exclude `utils.py`).

  4. **Compare** each category: docs vs. actual.
     - `missing_from_docs`: items on disk not mentioned in the doc.
     - `extra_in_docs`: items mentioned in doc but not on disk.

  5. **Return JSON**:

  ```json
  {
    "claude_md_stale": false,
    "readme_stale": false,
    "missing_from_docs": [],
    "extra_in_docs": [],
    "details": "CLAUDE.md in sync | README.md in sync"
  }
  ```

  Set `claude_md_stale: true` if `missing_from_docs` or `extra_in_docs` has entries
  relating to CLAUDE.md; `readme_stale: true` for README.md entries.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 5: Add context:fork to retro-format

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/retro-format/SKILL.md` frontmatter has `context: fork` and no `type:` key
- Skill has `## Input` section documenting `$ARGUMENTS` compact bundle
- Graceful handling for empty/malformed `$ARGUMENTS`

**Files:**
- Modify: `skills/retro-format/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  No pytest for context field. Manual RED:
  ```bash
  grep "context: fork" skills/retro-format/SKILL.md  # returns nothing → RED confirmed
  ```

- [ ] **Step 2: Implement (GREEN)**
  In `skills/retro-format/SKILL.md` frontmatter:
  - Remove `type: reference` line
  - Add `context: fork` after `effort: low`

  Add `## Input` section at the top of the body, before `## โครงสร้าง Retrospective`:

  ```markdown
  ## Input

  `$ARGUMENTS` (optional compact JSON bundle from `/zie-retro`):

  ```json
  {
    "shipped": ["feat: foo", "fix: bar"],
    "commits_since_tag": 5,
    "pain_points": [],
    "decisions": [],
    "roadmap_done_tail": "- [x] Previous feature — v1.0.0 2026-01-01"
  }
  ```

  If `$ARGUMENTS` is empty or unparseable: generate all sections using whatever
  context is available. All five retro sections must still be produced.
  ```

  Run: `make test-unit` — must PASS (no test changes; test_no_unofficial_type_field
  passes because retro-format is not in EXPECTED — verify this is the case, and if it
  is in EXPECTED, the type removal satisfies the test)

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 6: Add context:fork to verify

**Acceptance Criteria:**
- `skills/verify/SKILL.md` frontmatter has `context: fork`
- Skill has `## Input` section documenting optional `$ARGUMENTS`
- When `$ARGUMENTS.test_output` provided: skip `make test-unit`, use provided output
- When `$ARGUMENTS` empty/malformed: fall back to running `make test-unit` (backward compatible)

**Files:**
- Modify: `skills/verify/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**
  Manual RED:
  ```bash
  grep "context: fork" skills/verify/SKILL.md  # returns nothing → RED confirmed
  ```

- [ ] **Step 2: Implement (GREEN)**
  In `skills/verify/SKILL.md` frontmatter: add `context: fork` after `effort: low`

  Add `## Input` section immediately after `## Parameters` table:

  ```markdown
  ## Input

  `$ARGUMENTS` (optional JSON from caller):

  ```json
  {
    "test_output": "===== 1234 passed in 5.23s =====",
    "changed_files": ["hooks/auto-test.py"],
    "scope": "tests-only"
  }
  ```

  - `test_output`: if provided and non-empty, use as the test result — skip
    re-running `make test-unit`. If `test_output` contains `failed` or `error` →
    treat tests as failed.
  - `scope`: overrides the skill's scope parameter if provided.
  - `changed_files`: restrict TODO/secrets scan to these files if provided.

  **Fallback:** if `$ARGUMENTS` is empty or unparseable → run all checks normally,
  including `make test-unit` (existing behavior — fully backward compatible).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS

---

## Task 7: Update zie-retro for parallel forks

<!-- depends_on: Task 4, Task 5 -->

**Acceptance Criteria:**
- `/zie-retro` builds compact JSON summary before forking
- Forks `retro-format` and `docs-sync-check` simultaneously
- Parent writes ADRs while both forks run
- Collects fork results after ADRs; applies docs updates if stale
- Fork failure does not block retro completion

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing tests (RED)**
  Manual RED: current command calls `Skill(zie-framework:retro-format)` inline
  (blocking), with no parallel `docs-sync-check` fork.
  ```bash
  grep "Fork" commands/zie-retro.md  # returns nothing → RED confirmed
  ```

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-retro.md`, restructure the "วิเคราะห์และสรุป" section and
  the docs-sync portion of "อัปเดต project knowledge":

  Replace "วิเคราะห์และสรุป" section with:

  ```markdown
  ### สร้าง compact summary

  Build compact JSON bundle for retro-format fork:

  ```json
  {
    "shipped": [<commit messages from git log since last tag>],
    "commits_since_tag": <count>,
    "pain_points": [],
    "decisions": [],
    "roadmap_done_tail": "<last 5 lines of Done section>"
  }
  ```

  ### Fork ทั้งสองพร้อมกัน

  Invoke both forks **simultaneously** — do NOT wait for either before starting:

  1. Fork `Skill(zie-framework:retro-format)` — pass compact summary as `$ARGUMENTS`
  2. Fork `Skill(zie-framework:docs-sync-check)` — pass output of
     `git diff main..HEAD --name-only` as `$ARGUMENTS.changed_files`
     (full scan if command fails)
  ```

  After the existing "บันทึก ADRs" section, add "รวมผลลัพธ์ forks" section:

  ```markdown
  ### รวมผลลัพธ์ forks

  Collect both fork results (forks ran while ADRs were being written above):

  - **retro-format result** → print the five structured retro sections.
  - **docs-sync-check result** → if `claude_md_stale=true` or `readme_stale=true`:
    apply inline docs updates now. Otherwise print "Docs in sync".
  - If either fork returned an error → print the error and continue.
    Retro is not blocked by fork failures.
  ```

  Remove the "Living docs sync — CLAUDE.md + README.md" subsection from
  "อัปเดต project knowledge" (now handled by docs-sync-check fork above).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review new sections for clarity. Verify ADR writing section is unchanged.
  Run: `make test-unit` — still PASS

---

## Task 8: Update zie-implement for verify overlap

<!-- depends_on: Task 6 -->

**Acceptance Criteria:**
- Final `make test-unit` output is captured (not discarded)
- `verify scope=tests-only` is forked immediately with captured output as `$ARGUMENTS`
- Parent does ROADMAP `[x]` update + `git add -A` while verify fork runs
- Checks fork result before `git commit`; issues → unstage, fix, re-invoke verify synchronously

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**
  Manual RED: current command calls `Skill(zie-framework:verify)` inline (blocking)
  after final test run, with no captured output passing.
  ```bash
  grep "captured" commands/zie-implement.md  # returns nothing → RED confirmed
  ```

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-implement.md`, replace "เมื่อทำครบทุก task" steps 1–3 with:

  ```markdown
  1. Run full test suite: `make test-unit` — capture output to `test_output` variable.
     If `make test-int` available: run and capture. If any suite fails → STOP,
     invoke `Skill(zie-framework:debug)` before retrying.

  2. **Fork verify immediately** — do NOT wait:
     Fork `Skill(zie-framework:verify)` with captured output:
     ```json
     {
       "test_output": "<captured make test-unit output>",
       "changed_files": "<git status --short output>",
       "scope": "tests-only"
     }
     ```

  3. **Commit prep (runs while verify fork is running)**:
     - Update `zie-framework/ROADMAP.md` Now lane: change `[ ]` → `[x]`
     - Run `git status --short` — verify expected files only
     - Run `git add -A`

  4. **Collect verify fork result**:
     - ✅ APPROVED → proceed to commit
     - ❌ Issues Found → `git reset HEAD` (unstage), fix issues, re-run
       `make test-unit`, re-invoke `Skill(zie-framework:verify)` synchronously,
       then re-stage and proceed
     - Fork error/timeout → print warning and proceed with manual note:
       "Verify fork failed — proceeding. Review manually."

  5. Commit:
     ```bash
     git commit -m "feat: <feature-slug>"
     git push origin dev
     ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review new steps for clarity. Ensure error path is explicit.
  Run: `make test-unit` — still PASS

---

## Task 9: Update zie-release for quality gate parallelism

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- After Gate 1 passes, `docs-sync-check` skill is forked immediately
- TODOs grep and secrets scan run in parallel with Gate 2 and Gate 3
- Fork results collected before version bump (before "All Gates Passed" Step 1)
- If fork failed: run inline before bumping

**Files:**
- Modify: `commands/zie-release.md`

- [ ] **Step 1: Write failing tests (RED)**
  Manual RED: current command runs TODOs (Gate 5) and docs sync (Gate 6) sequentially
  after Gate 3.
  ```bash
  grep "Fork" commands/zie-release.md  # returns nothing → RED confirmed
  ```

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-release.md`:

  1. After the Gate 1 section and before the Gate 2 section, add:

  ```markdown
  ### Fork: Quality Checks (parallel with Gate 2/3)

  **Start immediately after Gate 1 passes — do NOT wait before running Gate 2:**

  Invoke simultaneously:

  1. Fork `Skill(zie-framework:docs-sync-check)` with changed files:
     Pass `git diff main..HEAD --name-only` output as `$ARGUMENTS.changed_files`.

  2. Bash: TODOs and secrets scan (run in parallel with Gate 2):
     ```bash
     grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
     ```
     Also check changed files for hardcoded API keys, tokens, or credentials.

  These run **concurrently with Gate 2 and Gate 3**.
  ```

  2. Remove Gate 5 (TODOs and Secrets) and Gate 6 (Docs sync) sections.

  3. Before "All Gates Passed — Release", add:

  ```markdown
  ### รวมผลลัพธ์ Quality Forks

  Print: `[Quality Forks] Collecting results`

  Collect results from the parallel forks started after Gate 1:

  - **Docs sync**: if `claude_md_stale=true` or `readme_stale=true` → update
    stale docs now, before version bump. If in sync → print "Docs in sync".
  - **TODOs/secrets**: any hits in new code? Fix or create a tracked backlog
    item before proceeding. Any secrets detected → STOP immediately.
  - If either fork did not complete → run inline (blocking) before continuing.
  ```

  4. Update gate count references: Gate 7 (Code Diff) becomes the final gate.
     Update print statement: `[Gate 5/5] Code Diff` (was `[Gate 7/7]`).

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Review gate numbering in all `Print:` statements for consistency.
  Run: `make test-unit` — still PASS
