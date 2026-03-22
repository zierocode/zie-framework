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
   ```
   zie-framework/
   ├── .config
   ├── ROADMAP.md
   ├── specs/
   ├── plans/
   ├── decisions/
   └── evidence/
   ```
   Create a `.gitignore` inside `zie-framework/` with: `evidence/`

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

7. **If `playwright_enabled=true`**:
   - Check if `@playwright/test` in package.json devDependencies
   - If not: `npm install --save-dev @playwright/test` + `npx playwright install chromium`
   - Create `playwright.config.ts` from template if it doesn't exist
   - Create `tests/e2e/` directory with `fixtures.ts`

8. **If `zie_memory_enabled=true`**:
   - Store project bootstrap as P2 memory:
     `remember "Project <name> initialized with zie-framework. Type: <project_type>. Test runner: <test_runner>." priority=project tags=[zie-framework, init]`

9. **Print summary**:
   ```
   zie-framework initialized in <project>/

   Project type : <type>
   Test runner  : <runner>
   Frontend     : <yes|no>
   Playwright   : <enabled|disabled>
   Brain        : <enabled|disabled>

   Created:
     zie-framework/  (specs, plans, decisions, ROADMAP.md)
     Makefile        (<created|updated>)
     VERSION         (<created|kept>)

   Next: Run /zie-status to see current state.
         Run /zie-idea to start your first feature.
   ```

## Notes
- Safe to re-run (idempotent) — never overwrites existing files, only creates missing ones
- If `zie-framework/` already exists, skip creation and print "already initialized"
