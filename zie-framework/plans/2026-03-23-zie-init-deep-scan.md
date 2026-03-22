---
approved: true
approved_at: 2026-03-23
backlog: backlog/zie-init-deep-scan.md
spec: specs/2026-03-23-zie-init-deep-scan-design.md
---

# zie-init Deep Scan + Knowledge Drift Detection — Implementation Plan

**Goal:** Make `/zie-init` on an existing project produce accurate knowledge
docs via `Agent(Explore)` scan, and add drift detection to `/zie-status` plus
a new `/zie-resync` command.

**Architecture:** Three command files change — `zie-init.md` gets
greenfield/existing branching + deep scan path; `zie-status.md` gets a
Knowledge row with hash recompute; new `zie-resync.md` command runs the same
scan on demand. No new Python code — all logic is LLM instruction in Markdown
command files.

**Tech Stack:** Markdown command files, hashlib.sha256 (via bash/python
inline), Agent(subagent_type=Explore)

---

## แผนที่ไฟล์

| Action | File | Change |
| --- | --- | --- |
| Create | `tests/unit/test_zie_init_deep_scan.py` | 9 tests for all new behaviour |
| Modify | `commands/zie-init.md` | Add detection + existing project path |
| Modify | `commands/zie-status.md` | Add Knowledge drift check row |
| Create | `commands/zie-resync.md` | New resync command |

---

## Task 1: Write failing tests (RED)

<!-- No depends_on -->

**Files:**

- Create: `tests/unit/test_zie_init_deep_scan.py`

- [ ] **Step 1: Create test file**

  ```python
  import os

  REPO_ROOT = os.path.abspath(
      os.path.join(os.path.dirname(__file__), "..", "..")
  )


  def read(rel_path):
      with open(os.path.join(REPO_ROOT, rel_path)) as f:
          return f.read()


  class TestZieInitDeepScan:
      def test_zie_init_has_existing_project_detection(self):
          content = read("commands/zie-init.md")
          assert "existing" in content.lower(), (
              "zie-init must detect existing vs greenfield projects"
          )

      def test_zie_init_has_agent_explore_scan(self):
          content = read("commands/zie-init.md")
          assert "Agent" in content and "Explore" in content, (
              "zie-init must invoke Agent(subagent_type=Explore) for "
              "existing projects"
          )

      def test_zie_init_updates_knowledge_hash(self):
          content = read("commands/zie-init.md")
          assert "knowledge_hash" in content, (
              "zie-init must compute and store knowledge_hash in .config"
          )

      def test_zie_init_updates_knowledge_synced_at(self):
          content = read("commands/zie-init.md")
          assert "knowledge_synced_at" in content, (
              "zie-init must store knowledge_synced_at in .config"
          )

      def test_zie_init_config_template_has_knowledge_fields(self):
          content = read("commands/zie-init.md")
          # After superpowers removal, config template should have
          # knowledge_hash and knowledge_synced_at added
          assert "knowledge_hash" in content, (
              "zie-init .config must include knowledge_hash field doc"
          )


  class TestZieStatusDriftDetection:
      def test_zie_status_has_knowledge_line(self):
          content = read("commands/zie-status.md")
          assert "Knowledge" in content, (
              "zie-status must include a Knowledge row in status output"
          )

      def test_zie_status_has_drift_detection(self):
          content = read("commands/zie-status.md")
          assert "knowledge_hash" in content or "drift" in content, (
              "zie-status must check knowledge_hash for drift detection"
          )


  class TestZieResyncCommand:
      def test_zie_resync_command_exists(self):
          path = os.path.join(REPO_ROOT, "commands", "zie-resync.md")
          assert os.path.exists(path), (
              "commands/zie-resync.md must exist"
          )

      def test_zie_resync_has_agent_explore(self):
          content = read("commands/zie-resync.md")
          assert "Agent" in content and "Explore" in content, (
              "zie-resync must invoke Agent(subagent_type=Explore)"
          )

      def test_zie_resync_updates_hash(self):
          content = read("commands/zie-resync.md")
          assert "knowledge_hash" in content, (
              "zie-resync must update knowledge_hash in .config after resync"
          )
  ```

- [ ] **Step 2: Run tests — must FAIL**

  ```bash
  python3 -m pytest tests/unit/test_zie_init_deep_scan.py -v
  ```

  Expected: 9 FAILED (commands not yet updated)

- [ ] **Step 3: Commit RED tests**

  ```bash
  git add tests/unit/test_zie_init_deep_scan.py
  git commit -m "test: add failing tests for deep scan + drift detection"
  ```

---

## Task 2: Update zie-init.md (GREEN — 5 tests)

<!-- No depends_on -->

**Files:**

- Modify: `commands/zie-init.md`

The spec defines two paths: **greenfield** (current behaviour) and
**existing** (deep scan). Insert detection between current step 1 and step 2.

- [ ] **Step 1: Add detection step after step 1**

  After the existing "1. **Detect project type**" block, insert new step 2
  (renumbering the rest):

  ```markdown
  2. **Detect greenfield vs existing project**:

     A project is **existing** if any of the following are true:
     - Any of these directories exist at project root: `src/`, `app/`,
       `lib/`, `api/`, `hooks/`, `components/`, `routes/`, `models/`,
       `services/`, `pkg/`
     - `git rev-list --count HEAD` returns a value greater than 1

     Otherwise: **greenfield** — continue with template path (steps 3+).

     **If existing** → print "Existing project detected. Scanning
     codebase..." then:

     a. Invoke `Agent(subagent_type=Explore)`:
        - Task: scan every file, return a structured analysis report:
          - Architecture pattern and overall structure
          - Every significant component/module (name + one-line purpose)
          - Full tech stack with versions (from config files)
          - Data flow from entry point to response
          - Key constraints or decisions in code/comments/docs
          - Test strategy (runner, coverage areas)
          - Active areas (from `git log --name-only -20`)
        - Exclude: `node_modules/`, `.git/`, `build/`, `dist/`,
          `.next/`, `__pycache__/`, `*.pyc`, `coverage/`,
          `zie-framework/`
        - Return: structured markdown report (not the final docs)

     b. Read Agent report and draft all four knowledge files:
        - `zie-framework/PROJECT.md`
        - `zie-framework/project/architecture.md`
        - `zie-framework/project/components.md`
        - `zie-framework/project/decisions.md`
          (only real decisions found; unknowns marked TBD)

     c. Present all four drafts inline as markdown code blocks. Ask:
        "Does this look accurate? Reply 'yes' to write, or describe
        corrections."

     d. If corrections → apply → re-present → repeat until user replies
        'yes' or 'y' (case-insensitive). No iteration limit.

     e. Write all four files to disk.

     f. Compute `knowledge_hash` (SHA-256):
        1. Enumerate all directory paths recursively, excluding
           `node_modules/`, `.git/`, `build/`, `dist/`, `.next/`,
           `__pycache__/`, `coverage/`, `zie-framework/`
        2. Sort paths lexicographically and join with `\n`
        3. Append literal `\n---\n`
        4. For each directory, compute `<path>:<file_count>`, sort, join
           with `\n`
        5. Append literal `\n---\n`
        6. Append content of any found config files, sorted by filename:
           `package.json`, `requirements.txt`, `pyproject.toml`,
           `Cargo.toml`, `go.mod`
        7. Feed full UTF-8 string into
           `hashlib.sha256(s.encode()).hexdigest()`

        Run as inline Python:

        ```bash
        python3 -c "
        import hashlib, os, json
        from pathlib import Path

        EXCLUDE = {
            'node_modules', '.git', 'build', 'dist', '.next',
            '__pycache__', 'coverage', 'zie-framework'
        }
        CONFIG_FILES = [
            'package.json', 'requirements.txt', 'pyproject.toml',
            'Cargo.toml', 'go.mod'
        ]

        root = Path('.')
        dirs = sorted(
            str(p.relative_to(root))
            for p in root.rglob('*')
            if p.is_dir()
            and not any(ex in p.parts for ex in EXCLUDE)
        )
        counts = sorted(
            f'{d}:{len(list((root / d).iterdir()))}'
            for d in dirs
        )
        configs = ''
        for cf in CONFIG_FILES:
            p = root / cf
            if p.exists():
                configs += p.read_text()

        s = '\n'.join(dirs) + '\n---\n'
        s += '\n'.join(counts) + '\n---\n'
        s += configs
        print(hashlib.sha256(s.encode()).hexdigest())
        "
        ```

     g. Read current `zie-framework/.config`, merge in two new fields
        (never remove existing fields), write back:

        ```json
        {
          "knowledge_hash": "<computed hex string>",
          "knowledge_synced_at": "<YYYY-MM-DD>"
        }
        ```

     h. Continue to step 3 (create zie-framework/ directory structure —
        skip the four knowledge docs since they were already written).

     **Failure handling:** If Agent scan fails or returns empty → warn
     "Scan failed — retrying or falling back to templates?" and offer:
     - Retry the scan
     - Fall back to template path (same as greenfield)
  ```

- [ ] **Step 2: Run tests**

  ```bash
  python3 -m pytest tests/unit/test_zie_init_deep_scan.py \
    -k "TestZieInitDeepScan" -v
  ```

  Expected: 5 PASS

- [ ] **Step 3: Run all tests — confirm no regression**

  ```bash
  make test-unit
  ```

  Expected: all PASS

- [ ] **Step 4: Commit**

  ```bash
  git add commands/zie-init.md
  git commit -m "feat: add deep scan path to zie-init for existing projects"
  ```

---

## Task 3: Update zie-status.md (GREEN — 2 tests)

<!-- No depends_on -->

**Files:**

- Modify: `commands/zie-status.md`

Add Knowledge drift check to step 2 (Read files) and add Knowledge row to
the status table in step 5.

- [ ] **Step 1: Add knowledge_hash read to step 2**

  In step 2 "Read files", add:
  `zie-framework/.config` → also read `knowledge_hash`, `knowledge_synced_at`

- [ ] **Step 2: Add Knowledge row to status table**

  In step 5 (status output), after the Brain row, add:

  ```markdown
  | Knowledge | \<✓ synced (YYYY-MM-DD) \| ⚠ drift detected — run
  /zie-resync \| ? no baseline — run /zie-resync> |
  ```

- [ ] **Step 3: Add drift check logic**

  Add to steps (between step 4 and step 5):

  ```markdown
  4b. **Check knowledge drift**:
      - Read `knowledge_hash` from `zie-framework/.config`
      - If missing → Knowledge status: `? no baseline — run /zie-resync`
      - If present → recompute hash using same algorithm as zie-init
        (dirs + file counts + config files, same exclusion list)
        - Equal → `✓ synced (<knowledge_synced_at>)`
        - Differs → `⚠ drift detected — run /zie-resync`
      - Knowledge row is informational only — does not block suggestions
  ```

- [ ] **Step 4: Run tests**

  ```bash
  python3 -m pytest tests/unit/test_zie_init_deep_scan.py \
    -k "TestZieStatusDriftDetection" -v
  ```

  Expected: 2 PASS

- [ ] **Step 5: Run all tests**

  ```bash
  make test-unit
  ```

  Expected: all PASS

- [ ] **Step 6: Commit**

  ```bash
  git add commands/zie-status.md
  git commit -m "feat: add knowledge drift detection to zie-status"
  ```

---

## Task 4: Create zie-resync.md (GREEN — 2 tests)

<!-- No depends_on -->

**Files:**

- Create: `commands/zie-resync.md`

- [ ] **Step 1: Create the file**

  ```markdown
  ---
  description: Rescan codebase and update knowledge docs + knowledge hash.
    Run when drift detected or after major structural changes.
  argument-hint: (no arguments needed)
  allowed-tools: Read, Write, Bash, Agent
  ---

  # /zie-resync — Rescan Codebase + Update Knowledge Docs

  Full rescan of project codebase. Updates PROJECT.md, project/architecture.md,
  project/components.md, project/decisions.md, and knowledge_hash in .config.
  All updates require user confirmation before writing.

  ## ตรวจสอบก่อนเริ่ม

  1. Check `zie-framework/` exists → if not, tell user to run `/zie-init`
     first.
  2. Check `zie-framework/.config` exists → if not, recommend `/zie-init`.

  ## Steps

  1. Print: "Rescanning codebase..."

  2. Invoke `Agent(subagent_type=Explore)`:
     - Same task and exclusion list as `/zie-init` existing project scan:
       scan every file, return structured analysis covering architecture,
       components, tech stack, data flow, decisions, test strategy, active
       areas.
     - Exclude: `node_modules/`, `.git/`, `build/`, `dist/`, `.next/`,
       `__pycache__/`, `*.pyc`, `coverage/`, `zie-framework/`

  3. Read Agent report and draft updated versions of all four knowledge
     files:
     - `zie-framework/PROJECT.md`
     - `zie-framework/project/architecture.md`
     - `zie-framework/project/components.md`
     - `zie-framework/project/decisions.md`

  4. Present all four drafts inline as markdown code blocks. Ask:
     "Does this look accurate? Reply 'yes' to write, or describe
     corrections."

  5. If corrections → apply → re-present → repeat until user replies 'yes'
     or 'y' (case-insensitive). No iteration limit.

  6. Overwrite all four knowledge files on disk.

  7. Recompute `knowledge_hash` using the same algorithm as `/zie-init`:
     - Enumerate dirs (excluding node_modules, .git, build, dist, .next,
       __pycache__, coverage, zie-framework)
     - Sort + join with `\n`, separator `\n---\n`
     - Append `<path>:<file_count>` sorted, separator `\n---\n`
     - Append content of found config files (package.json, requirements.txt,
       pyproject.toml, Cargo.toml, go.mod) sorted by filename
     - SHA-256 hex of full UTF-8 string

  8. Merge into `zie-framework/.config` (never remove existing fields):

     ```json
     {
       "knowledge_hash": "<new hash>",
       "knowledge_synced_at": "<YYYY-MM-DD>"
     }
     ```

  9. Print:

     ```text
     Knowledge docs updated.

     knowledge_hash : <first 8 chars of hash>...
     synced_at      : <YYYY-MM-DD>

     Run /zie-status to verify sync status.
     ```

  ## ขั้นตอนถัดไป

  → `/zie-status` — ยืนยันว่า Knowledge แสดง ✓ synced

  ## Notes

  - Idempotent — safe to run multiple times
  - All doc updates require user 'yes' — never auto-overwrites
  - Does not change ROADMAP, Makefile, VERSION, or CLAUDE.md
  ```

- [ ] **Step 2: Run tests**

  ```bash
  python3 -m pytest tests/unit/test_zie_init_deep_scan.py \
    -k "TestZieResyncCommand" -v
  ```

  Expected: 3 PASS

- [ ] **Step 3: Run all tests**

  ```bash
  make test-unit
  ```

  Expected: all PASS

- [ ] **Step 4: Commit**

  ```bash
  git add commands/zie-resync.md
  git commit -m "feat: add /zie-resync command for codebase rescan"
  ```

---

## Task 5: Final verify

<!-- depends_on: Task 2, Task 3, Task 4 -->

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS, 9 new tests green

- [ ] **Step 2: Confirm zie-resync appears in marketplace description**

  Update `.claude-plugin/marketplace.json` description to include
  `/zie-resync`:

  ```json
  "description": "Solo developer SDLC framework — /zie-init, /zie-idea,
  /zie-build, /zie-fix, /zie-ship, /zie-retro, /zie-resync with ambient
  intent detection and auto-test hooks"
  ```

- [ ] **Step 3: Invoke Skill(zie-framework:verify)**

- [ ] **Step 4: Commit**

  ```bash
  git add .claude-plugin/marketplace.json
  git commit -m "docs: add zie-resync to marketplace description"
  ```
