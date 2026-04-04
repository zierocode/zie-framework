---
description: Initialize zie-framework in the current project. Run once per project to create SDLC structure, ROADMAP, Makefile, and VERSION.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Glob, Grep, Agent
model: haiku
effort: medium
---

# /init — Initialize zie-framework in current project

Bootstrap zie-framework in the current working directory. Run this once per project.

## ตรวจสอบก่อนเริ่ม

Verify a git repository exists:

```bash
git rev-parse --git-dir 2>/dev/null
```

Non-zero → **STOP**: `"No git repository found. Run 'git init' first,
then re-run /init."`

## Steps

0. **Re-run guard**: if `zie-framework/` already exists, check completeness:

   **Complete** = `zie-framework/PROJECT.md` exists AND
   `zie-framework/project/architecture.md` exists AND
   `zie-framework/.config` contains `"knowledge_hash"` with a non-empty value.

   - **If complete**: print "Already initialized." then **skip to Step 3**
     (create missing files only — all steps idempotent). Knowledge scan is
     not repeated; run `/resync` to update knowledge docs.

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

   a. Invoke `Agent(subagent_type=Explore)` with the following
      self-contained prompt. Receive `scan_report` JSON.

      > **Explore agent prompt (self-contained — pass verbatim):**
      >
      > ```
      > You are scanning an existing software project to help initialize zie-framework.
      >
      > Scan the project at the current working directory. Read existing documentation
      > first as primary sources (they encode deliberate intent, not just structure):
      >   README.md, CHANGELOG.md, ARCHITECTURE.md, AGENTS.md,
      >   docs/**, **/specs/*.md, **/plans/*.md, **/decisions/*.md
      >   (exclude anything inside zie-framework/)
      >
      > Then scan the codebase structure to fill in any gaps.
      >
      > Exclude from all scans:
      >   node_modules/, .git/, build/, dist/, .next/, __pycache__/, *.pyc,
      >   coverage/, zie-framework/
      >
      > Return ONLY a JSON object with this exact structure (no markdown, no prose).
      > The parent parser will extract JSON from the first '{' to the last '}'.
      >
      > {
      >   "architecture_pattern": "<string>",
      >   "components": [{ "name": "<string>", "purpose": "<one-line string>" }],
      >   "tech_stack": [{ "name": "<string>", "version": "<string | null>" }],
      >   "data_flow": "<string>",
      >   "key_constraints": ["<string>"],
      >   "test_strategy": { "runner": "<string | null>", "coverage_areas": ["<string>"] },
      >   "active_areas": ["<string>"],
      >   "existing_hooks": "<path to hooks/hooks.json if present, else null>",
      >   "existing_config": "<path to zie-framework/.config if present, else null>",
      >   "migration_candidates": {
      >     "specs":      ["<relative path>"],
      >     "plans":      ["<relative path>"],
      >     "decisions":  ["<relative path>"],
      >     "backlog":    ["<relative path>"]
      >   }
      > }
      >
      > For migration_candidates: include files matching these patterns (excluding
      > anything already inside zie-framework/):
      >   specs:     **/specs/*.md, **/spec/*.md
      >   plans:     **/plans/*.md, **/plan/*.md
      >   decisions: **/decisions/*.md, **/adr/*.md, ADR-*.md (at project root)
      >   backlog:   **/backlog/*.md
      >
      > For existing_hooks: check if hooks/hooks.json exists at project root.
      > For existing_config: check if zie-framework/.config exists.
      > If a field cannot be determined, use null for scalars or [] for arrays.
      > ```

      **Parse `scan_report`:**

      ```python
      # Attempt 1: bare JSON
      scan_report = json.loads(agent_output.strip())

      # Attempt 2 (if attempt 1 fails): extract first { to last }
      start = agent_output.index("{")
      end   = agent_output.rindex("}") + 1
      scan_report = json.loads(agent_output[start:end])
      ```

      If both fail → warn "Scan failed — retrying or falling back to templates?"
      and offer: retry or fall back to greenfield template path.
      If agent times out → warn "Agent scan incomplete — retrying or falling back
      to templates?" and offer the same two choices.

   b. Draft the four knowledge files from `scan_report` fields:
      - `zie-framework/PROJECT.md` ← `architecture_pattern`, `components`, `tech_stack`
      - `zie-framework/project/architecture.md` ← `architecture_pattern`, `data_flow`, `active_areas`
      - `zie-framework/project/components.md` ← `components`
      - `zie-framework/project/context.md` ← `key_constraints` (unknowns marked TBD)

   c. Present all four drafts inline as markdown code blocks.

   d. **Section-targeted revision loop** — prompt:
      ```
      Which section to revise? (project / architecture / components / context / all good)
      ```
      - User replies `"project"` → re-draft only PROJECT.md, re-present
      - User replies `"architecture"` → re-draft only architecture.md, re-present
      - User replies `"components"` → re-draft only components.md, re-present
      - User replies `"context"` → re-draft only context.md, re-present
      - User replies `"all good"` or `"y"` or `"yes"` → exit loop, proceed to 2e
      - Unrecognized input → re-prompt (no crash, no iteration limit)

   e. Write all four files to disk.

   f. Compute `knowledge_hash` via:
      ```bash
      python3 hooks/knowledge-hash.py
      ```

   g. Read `zie-framework/.config` (if `existing_config` is non-null: read
      and preserve all user-set keys; if null: create fresh). Merge in:
      ```json
      { "knowledge_hash": "<computed hex string>", "knowledge_synced_at": "<YYYY-MM-DD>" }
      ```
      Write back. Never remove existing fields.

   h. **Present migration candidates** from `scan_report.migration_candidates`:

      - If `migration_candidates` key is missing or all arrays empty → skip silently.
      - If agent returned malformed JSON → warn "Could not detect migratable
        docs from agent report" then skip (continue to step 3).
      - `existing_hooks`: if non-null → treat hooks installation as a merge
        (preserve existing event handlers, add new ones); if null → fresh write.

      Filter candidates: skip `README.md`, `CHANGELOG.md`, `LICENSE*`,
      `CLAUDE.md`, `AGENTS.md`, files already inside `zie-framework/`.
      Validate each path exists on disk before presenting.

      | Source key | Destination |
      | --- | --- |
      | `specs` | `zie-framework/specs/` |
      | `plans` | `zie-framework/plans/` |
      | `decisions` | `zie-framework/decisions/` |
      | `backlog` | `zie-framework/backlog/` |

      If candidates remain, print:
      ```text
      Found documentation that can be migrated into zie-framework/:
        docs/specs/foo.md  →  zie-framework/specs/foo.md
      Migrate these files? (yes / no / select)
      ```
      - `yes` → migrate all using `git mv`
      - `no` → skip silently
      - `select` → confirm each file individually (y/n per file)

      If `git mv` fails → present error with retry option.

   i. Continue to step 3 (skip writing the four knowledge docs — already written).

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

10. **Set up `dev` branch**:
    - Run `git branch --list dev` to check if `dev` exists.
    - If not: run `git checkout -b dev` to create it (or `git checkout dev` if
      it exists on remote). `make release` requires the `dev` branch to exist.
    - If already on `dev` or `dev` already exists: skip silently.

11. **Install Markdown lint enforcement**:
    - Create `.markdownlint.json` at project root from
      `templates/markdownlint.json.template` — skip if already exists.
    - Create `.markdownlintignore` at project root — skip if already exists.
      Content:
      ```
      zie-framework/backlog/
      zie-framework/specs/
      zie-framework/plans/
      ```
    - Create `.githooks/pre-commit` from
      `templates/githooks-pre-commit.template` — skip if already exists.
      Run `chmod +x .githooks/pre-commit` after.
    - Run `git config core.hooksPath .githooks` to activate the hook.

12. **If `playwright_enabled=true`**:
    - Check if `@playwright/test` in package.json devDependencies
    - If not: ask "Install @playwright/test? This will run npm install. (yes/no)"
      → If yes: `npm install --save-dev @playwright/test` +
        `npx playwright install chromium`
      → If no: set `playwright_enabled=false` in `.config` and skip
    - Create `playwright.config.ts` from template if it doesn't exist
    - Create `tests/e2e/` directory with `fixtures.ts`

13. **If `zie_memory_enabled=true`**:
    - Store project bootstrap memory:
      Call `mcp__plugin_zie-memory_zie-memory__remember` with
      `"Project <name> initialized with zie-framework. Type: <project_type>. Stack: <tech_stack>. Test runner: <test_runner>."
      tags=[zie-framework, init, <project_name>]`

14. **Print summary**:

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

   Next: Run /status to see current state.
         Run /backlog to start your first feature.

   SDLC pipeline:
     /backlog → /spec → /plan → /implement → /release → /retro
   Each stage enforces quality gates. Run /status to see where you are.
   First feature: /backlog "your idea"
   ```

   If migration ran in step 2.h, append:
   ```text
   Migration complete: <N> files moved to zie-framework/specs|plans|decisions/
   ```

## Notes

- Safe to re-run (idempotent) — never overwrites existing files, only
  creates missing ones
- If `zie-framework/` already exists, skip creation and print "already initialized"
