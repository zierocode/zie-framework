---
description: Initialize zie-framework in the current project. Run once per project to create SDLC structure, ROADMAP, Makefile, and VERSION.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
---

# /zie-init — Initialize zie-framework in current project

Bootstrap zie-framework in the current working directory. Run this once per project.

## Steps

1. **Detect project type** by reading existing files:
   - `requirements.txt` or `pyproject.toml` → `python-api`
   - `package.json` with Next.js/React → `typescript-fullstack`
   - `package.json` without frontend framework → `typescript-cli`
   - `docker-compose.yml` + Python → `python-api` (confirm)
   - Check if `templates/` or `*.html` present → set `has_frontend=true`

2. **Detect greenfield vs existing project**:

   A project is **existing** if any of the following are true:
   - Any of these directories exist at project root: `src/`, `app/`,
     `lib/`, `api/`, `hooks/`, `components/`, `routes/`, `models/`,
     `services/`, `pkg/`
   - `git rev-list --count HEAD` returns a value greater than 1

   Otherwise: **greenfield** — continue with template path (step 3+).

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
      import hashlib, os
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

3. **Create `zie-framework/` structure** in project root:

   ```text
   zie-framework/
   ├── .config
   ├── ROADMAP.md
   ├── PROJECT.md
   ├── project/
   │   ├── architecture.md
   │   ├── components.md
   │   └── decisions.md
   ├── backlog/
   ├── specs/
   ├── plans/
   ├── decisions/
   └── evidence/
   ```

   Create a `.gitignore` inside `zie-framework/` with: `evidence/`
   Create `zie-framework/backlog/.gitkeep` so the directory is tracked by git.
   Generate from templates with substitutions (`{{project_name}}`, `{{date}}`, `{{version}}`):
   - `PROJECT.md` from `templates/PROJECT.md.template`
   - `project/architecture.md` from `templates/project/architecture.md.template`
   - `project/components.md` from `templates/project/components.md.template`
   - `project/decisions.md` from `templates/project/decisions.md.template`
   (For existing projects: skip the four knowledge docs — already written in step 2.)

4. **Generate `zie-framework/.config`** (JSON):

   ```json
   {
     "project_type": "<detected>",
     "test_runner": "<pytest|vitest|jest>",
     "has_frontend": <true|false>,
     "playwright_enabled": <true if has_frontend>,
     "zie_memory_enabled": <true if ZIE_MEMORY_API_KEY set>,
     "knowledge_hash": "<sha256 hex | empty string for greenfield>",
     "knowledge_synced_at": "<YYYY-MM-DD | empty string for greenfield>",
     "auto_test_debounce_ms": 3000,
     "auto_test_timeout_ms": 30000
   }
   ```

5. **Generate `zie-framework/ROADMAP.md`** from template:
   Use the ROADMAP template — set project name from current directory name.

6. **Create `Makefile`** at project root:
   - If Makefile already exists: ADD the standard targets (test-unit,
     test-int, test-e2e, test, push, ship) only if they don't already
     exist. Never overwrite existing targets.
   - If no Makefile: create from template matching project_type (python or typescript).

7. **Create `VERSION`** at project root:
   - If exists: keep as-is.
   - If not: create with content `0.1.0`

8. **Create `CLAUDE.md`** at project root:
   - If exists: skip (never overwrite).
   - If not: generate from `templates/CLAUDE.md.template` with these
     substitutions:
     - `{{project_name}}` → current directory name
     - `{{project_description}}` → `<project_type> project`
     - `{{tech_stack}}` → detected stack (e.g. `Python 3.x`,
       `Node.js / TypeScript`)
     - `{{test_runner}}` → detected test runner
     - `{{build_commands}}` → appropriate commands for project_type:
       - python: `make test-unit   # unit tests\nmake test        # full
         suite\nmake push m="msg"  # commit + push`
       - typescript: `make test-unit   # unit tests\nmake test        # full
         suite\nmake push m="msg"  # commit + push`

9. **Install Markdown lint enforcement**:
   - Create `.markdownlint.json` at project root from
     `templates/markdownlint.json.template` — skip if already exists.
   - Create `.githooks/pre-commit` from
     `templates/githooks-pre-commit.template` — skip if already exists.
     Run `chmod +x .githooks/pre-commit` after.
   - Run `git config core.hooksPath .githooks` to activate the hook.

10. **If `playwright_enabled=true`**:
    - Check if `@playwright/test` in package.json devDependencies
    - If not: `npm install --save-dev @playwright/test` +
      `npx playwright install chromium`
    - Create `playwright.config.ts` from template if it doesn't exist
    - Create `tests/e2e/` directory with `fixtures.ts`

11. **If `zie_memory_enabled=true`**:
    - Store project bootstrap memory:
      `remember "Project <name> initialized with zie-framework. Type:
      <project_type>. Stack: <tech_stack>. Test runner: <test_runner>."
      tags=[zie-framework, init, <project_name>]`

12. **Print summary**:

   ```text
   zie-framework initialized in <project>/

   Project type : <type>
   Test runner  : <runner>
   Frontend     : <yes|no>
   Playwright   : <enabled|disabled>
   Brain        : <enabled|disabled>

   Created:
     zie-framework/  (specs, plans, decisions, ROADMAP.md)
     CLAUDE.md       (<created|skipped — already exists>)
     Makefile        (<created|updated>)
     VERSION         (<created|kept>)

   Next: Run /zie-status to see current state.
         Run /zie-backlog to start your first feature.
   ```

## Notes

- Safe to re-run (idempotent) — never overwrites existing files, only
  creates missing ones
- If `zie-framework/` already exists, skip creation and print "already initialized"
