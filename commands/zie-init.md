---
description: Initialize zie-framework in the current project. Run once per project to create SDLC structure, ROADMAP, Makefile, and VERSION.
argument-hint: (no arguments needed)
allowed-tools: Read, Write, Bash, Glob, Grep
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

2. **Create `zie-framework/` structure** in project root:

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

3. **Generate `zie-framework/.config`** (JSON):

   ```json
   {
     "project_type": "<detected>",
     "test_runner": "<pytest|vitest|jest>",
     "has_frontend": <true|false>,
     "playwright_enabled": <true if has_frontend>,
     "zie_memory_enabled": <true if ZIE_MEMORY_API_KEY set>,
     "superpowers_enabled": <true if superpowers plugin found>,
     "auto_test_debounce_ms": 3000,
     "auto_test_timeout_ms": 30000
   }
   ```

4. **Generate `zie-framework/ROADMAP.md`** from template:
   Use the ROADMAP template — set project name from current directory name.

5. **Create `Makefile`** at project root:
   - If Makefile already exists: ADD the standard targets (test-unit, test-int, test-e2e, test, push, ship) only if they don't already exist. Never overwrite existing targets.
   - If no Makefile: create from template matching project_type (python or typescript).

6. **Create `VERSION`** at project root:
   - If exists: keep as-is.
   - If not: create with content `0.1.0`

7. **Create `CLAUDE.md`** at project root:
   - If exists: skip (never overwrite).
   - If not: generate from `templates/CLAUDE.md.template` with these substitutions:
     - `{{project_name}}` → current directory name
     - `{{project_description}}` → `<project_type> project`
     - `{{tech_stack}}` → detected stack (e.g. `Python 3.x`, `Node.js / TypeScript`)
     - `{{test_runner}}` → detected test runner
     - `{{build_commands}}` → appropriate commands for project_type:
       - python: `make test-unit   # unit tests\nmake test        # full suite\nmake push m="msg"  # commit + push`
       - typescript: `make test-unit   # unit tests\nmake test        # full suite\nmake push m="msg"  # commit + push`

8. **If `playwright_enabled=true`**:
   - Check if `@playwright/test` in package.json devDependencies
   - If not: `npm install --save-dev @playwright/test` + `npx playwright install chromium`
   - Create `playwright.config.ts` from template if it doesn't exist
   - Create `tests/e2e/` directory with `fixtures.ts`

9. **If `zie_memory_enabled=true`**:
   - Store project bootstrap memory:
     `remember "Project <name> initialized with zie-framework. Type: <project_type>. Stack: <tech_stack>. Test runner: <test_runner>." tags=[zie-framework, init, <project_name>]`

10. **Print summary**:

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
         Run /zie-idea to start your first feature.
   ```

## Notes

- Safe to re-run (idempotent) — never overwrites existing files, only creates missing ones
- If `zie-framework/` already exists, skip creation and print "already initialized"
