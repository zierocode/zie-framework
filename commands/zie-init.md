---
description: Initialize zie-framework in the current project. Run once per project to create SDLC structure, ROADMAP, Makefile, and VERSION.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
model: sonnet
effort: medium
---

# /zie-init — Initialize zie-framework in current project

Bootstrap zie-framework in the current working directory. Run this once per project.

## ตรวจสอบก่อนเริ่ม

Verify a git repository exists:

```bash
git rev-parse --git-dir 2>/dev/null
```

Non-zero → **STOP**: `"No git repository found. Run 'git init' first,
then re-run /zie-init."`

## Steps

0. **Re-run guard**: if `zie-framework/` already exists, check completeness:

   **Complete** = `zie-framework/PROJECT.md` exists AND
   `zie-framework/project/architecture.md` exists AND
   `zie-framework/.config` contains `"knowledge_hash"` with a non-empty value.

   - **If complete**: print "Already initialized." then **skip to Step 3**
     (create missing files only — all steps idempotent). Knowledge scan is
     not repeated; run `/zie-resync` to update knowledge docs.

   - **If incomplete** (missing knowledge docs or missing/empty
     `knowledge_hash`): print "Existing framework found, but knowledge scan
     not yet done. Scanning codebase..." then proceed to Step 2 (skip Step 1
     project-type detection only if `.config` already exists with
     `project_type`).

   - **If `zie-framework/` does not exist**: proceed normally from Step 1.

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
      - **Before scanning code**: read existing project docs as
        primary sources — prefer documented intent over inferred
        code structure:
        `README.md`, `CHANGELOG.md`, `ARCHITECTURE.md`, `AGENTS.md`,
        `docs/**`, any `**/specs/*.md`, `**/plans/*.md`,
        `**/decisions/*.md` outside `zie-framework/`
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
      - Additionally, detect migratable documentation: list all files
        matching `**/specs/*.md`, `**/spec/*.md`, `**/plans/*.md`,
        `**/plan/*.md`, `**/decisions/*.md`, `**/adr/*.md`,
        `ADR-*.md` (at project root), `**/backlog/*.md` —
        exclude any files already inside `zie-framework/`.
        Return these as a `migratable_docs` object in the report with
        keys `specs`, `plans`, `decisions`, `backlog` (each an array
        of relative file paths). Example:
        ```json
        {
          "migratable_docs": {
            "specs": ["docs/specs/foo.md"],
            "plans": [],
            "decisions": ["docs/adr-001.md"],
            "backlog": []
          }
        }
        ```

   b. Read Agent report and draft all four knowledge files:
      - `zie-framework/PROJECT.md`
      - `zie-framework/project/architecture.md`
      - `zie-framework/project/components.md`
      - `zie-framework/project/context.md`
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
      python3 hooks/knowledge-hash.py
      ```

   g. Read current `zie-framework/.config`, merge in two new fields
      (never remove existing fields), write back:

      ```json
      {
        "knowledge_hash": "<computed hex string>",
        "knowledge_synced_at": "<YYYY-MM-DD>"
      }
      ```

   h. **Present migratable documentation** — parse `migratable_docs`
      from the Explore agent report produced in step 2a:

      - If `migratable_docs` key is missing or all arrays are empty →
        skip silently.
      - If agent returned malformed JSON or omitted `migratable_docs` →
        warn: "Could not detect migratable docs from agent report" then
        skip (no error, continue to step 3).
      - If agent timed out before completing → warn: "Agent scan
        incomplete, skipping migration detection" then skip.
      - Otherwise: map each path to its destination using the same
        destination table as before:

        | Source key | Destination |
        | --- | --- |
        | `specs` | `zie-framework/specs/` |
        | `plans` | `zie-framework/plans/` |
        | `decisions` | `zie-framework/decisions/` |
        | `backlog` | `zie-framework/backlog/` |

        Skip always: `README.md`, `CHANGELOG.md`, `LICENSE*`,
        `CLAUDE.md`, `AGENTS.md`, files already inside
        `zie-framework/`, and any `docs/` tree that contains
        `index.md` or `_sidebar.md` at its root (public doc site).

        Validate each reported path exists on disk before presenting
        (graceful degradation for symlinks or stale agent results).

        If candidates remain after filtering, print:

        ```text
        Found documentation that can be migrated into zie-framework/:

          docs/specs/foo.md  →  zie-framework/specs/foo.md
          docs/plans/bar.md  →  zie-framework/plans/bar.md

        Migrate these files? (yes / no / select)
        ```

        - `yes` → migrate all using `git mv`
        - `no` → skip silently
        - `select` → confirm each file individually (y/n per file)

        If `git mv` fails for a candidate (e.g. destination already
        exists) → present error to user with retry option.

        After migration, print the list of moved files.

   i. Continue to step 3 (create zie-framework/ directory structure —
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
   │   └── context.md
   ├── backlog/
   ├── specs/
   ├── plans/
   ├── decisions/
   └── evidence/          # local-only: screenshots, test outputs, debug dumps
   ```

   Create a `.gitignore` inside `zie-framework/` with: `evidence/`
   (evidence/ is gitignored — never committed; use it for local artifacts)
   Create `zie-framework/backlog/.gitkeep` so the directory is tracked by git.
   Generate from templates with substitutions (`{{project_name}}`, `{{date}}`, `{{version}}`):
   - `PROJECT.md` from `templates/PROJECT.md.template`
   - `project/architecture.md` from `templates/project/architecture.md.template`
   - `project/components.md` from `templates/project/components.md.template`
   - `project/context.md` from `templates/project/context.md.template`
   (For existing projects: skip the four knowledge docs —
   already written in step 2.)

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
   Use `templates/ROADMAP.md.template` — set project name from
   current directory name.

6. **Create `Makefile` + `Makefile.local`** at project root:

   - **`Makefile`**:
     - If already exists: **skip** (never overwrite — user owns it).
     - If missing: copy from `templates/Makefile`.

   - **`Makefile.local`**:
     - If already exists: **skip**.
     - If missing: copy from matching example:
       - `python-api` / `python-plugin` → `templates/Makefile.local.python.example`
       - `typescript-cli` / `typescript-fullstack` → `templates/Makefile.local.typescript.example`
       - Other → `templates/Makefile.local.python.example` (closest generic)
     - Rename to `Makefile.local` (remove `.example` suffix).

7. **Negotiate `_bump-extra` + `_publish`** in `Makefile.local`:

   - Read `Makefile.local` — check if `_bump-extra` already has real commands
     (not just `@true`).
   - If stub: ask "Which version files need bumping on release?"
     Present options by `project_type`:

     | project\_type | Suggested `_bump-extra` |
     | --- | --- |
     | `python-api` | `sed` pyproject.toml version |
     | `python-plugin` | `jq` plugin.json version |
     | `typescript-cli` | `npm version $(NEW) --no-git-tag-version` |
     | `typescript-fullstack` | `npm version $(NEW) --no-git-tag-version` |
     | (other) | prompt user to describe version files |

   - Present draft and ask: "Does this look right? (yes / no / edit)"
   - `yes` → write into `Makefile.local`; `no` → leave as `@true`; `edit` → redraft.

   - Ask separately: "Does this project need a publish step after release?
     (e.g. gh release, npm publish, docker push, vercel deploy — or 'no')"
   - If yes: add appropriate `_publish` recipe to `Makefile.local`.
   - If no: leave `_publish` as `@true`.

8. **Create `VERSION`** at project root — keep as-is if exists;
   create with content `0.1.0` if missing.

9. **Create `CLAUDE.md`** at project root:
   - If exists: skip (never overwrite).
   - If not: generate from `templates/CLAUDE.md.template` with these
     substitutions:
     - `{{project_name}}` → current directory name
     - `{{project_description}}` → `<project_type> project`
     - `{{tech_stack}}` → detected stack (e.g. `Python 3.x`,
       `Node.js / TypeScript`)
     - `{{test_runner}}` → detected test runner
     - `{{build_commands}}` → appropriate commands for project_type:
       - python:

         ```bash
         make test-unit        # unit tests
         make test             # full suite
         make push m="msg"     # commit + push
         make start            # start dev environment
         make deploy ENV=prod  # deploy to prod
         ```

       - typescript:

         ```bash
         make test-unit        # unit tests
         make test             # full suite
         make push m="msg"     # commit + push
         make start            # start dev server
         make deploy ENV=prod  # deploy to prod
         ```

10. **Install Markdown lint enforcement**:
    - Create `.markdownlint.json` at project root from
      `templates/markdownlint.json.template` — skip if already exists.
    - Create `.githooks/pre-commit` from
      `templates/githooks-pre-commit.template` — skip if already exists.
      Run `chmod +x .githooks/pre-commit` after.
    - Run `git config core.hooksPath .githooks` to activate the hook.

11. **If `playwright_enabled=true`**:
    - Check if `@playwright/test` in package.json devDependencies
    - If not: ask "Install @playwright/test? This will run npm install. (yes/no)"
      → If yes: `npm install --save-dev @playwright/test` +
        `npx playwright install chromium`
      → If no: set `playwright_enabled=false` in `.config` and skip
    - Create `playwright.config.ts` from template if it doesn't exist
    - Create `tests/e2e/` directory with `fixtures.ts`

12. **If `zie_memory_enabled=true`**:
    - Store project bootstrap memory:
      Call `mcp__plugin_zie-memory_zie-memory__remember` with
      `"Project <name> initialized with zie-framework. Type: <project_type>. Stack: <tech_stack>. Test runner: <test_runner>."
      tags=[zie-framework, init, <project_name>]`

13. **Print summary**:

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

   SDLC pipeline:
     /zie-backlog → /zie-spec → /zie-plan → /zie-implement → /zie-release → /zie-retro
   Each stage enforces quality gates. Run /zie-status to see where you are.
   First feature: /zie-backlog "your idea"
   ```

   If migration ran in step 2.h, append:
   ```text
   Migration complete: <N> files moved to zie-framework/specs|plans|decisions/
   ```

## Notes

- Safe to re-run (idempotent) — never overwrites existing files, only
  creates missing ones
- If `zie-framework/` already exists, skip creation and print "already initialized"
