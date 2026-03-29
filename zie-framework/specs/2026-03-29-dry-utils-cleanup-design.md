---
approved: true
approved_at: 2026-03-29
backlog: backlog/dry-utils-cleanup.md
---

# DRY Utils Cleanup — Design Spec

**Problem:** Two DRY violations in `hooks/utils.py` reduce consistency: `parse_roadmap_section()` and `parse_roadmap_section_content()` duplicate identical parsing logic, and `config.get()` calls scattered across 8 hook files use inconsistent defaults for the same keys.

**Approach:** Consolidate the parsing functions by delegating `parse_roadmap_section()` to `parse_roadmap_section_content()`. Centralize config defaults in a `CONFIG_DEFAULTS` constant in `utils.py`, merge them in `load_config()`, and remove inline defaults from all call sites. This reduces surface area for subtle bugs when hook behavior changes.

**Components:**
- `hooks/utils.py` — consolidate parse_roadmap functions, add CONFIG_DEFAULTS constant, update load_config()
- `hooks/auto-test.py` — remove inline defaults from config.get() calls (3 call sites)
- `hooks/task-completed-gate.py` — remove inline defaults from config.get() calls (1 call site)
- `hooks/session-resume.py` — remove inline defaults from config.get() calls (4 call sites)
- `hooks/safety-check.py` — remove inline defaults from config.get() calls (1 call site)
- `hooks/safety_check_agent.py` — remove inline defaults from config.get() calls (1 call site)
- `hooks/sdlc-compact.py` — no config.get() calls, verify no impact
- `hooks/failure-context.py` — no config.get() calls, verify no impact
- `hooks/intent-sdlc.py` — no config.get() calls, verify no impact
- `hooks/subagent-context.py` — no config.get() calls, verify no impact

**Data Flow:**

1. Read backlog file and parse call sites: grep `parse_roadmap_section`, `parse_roadmap_section_content`, and `config.get()` across hooks/*.py
2. In `utils.py`, add `CONFIG_DEFAULTS` dict with all known keys and their default values:
   - `safety_check_mode`: "regex"
   - `test_runner`: ""
   - `auto_test_debounce_ms`: 3000
   - `auto_test_timeout_ms`: 30000
   - `test_indicators`: ""
   - `project_type`: "unknown"
   - `zie_memory_enabled`: False
3. Update `load_config()` to merge loaded JSON with `CONFIG_DEFAULTS` (loaded values win)
4. Replace `parse_roadmap_section(path, section)` body with: `return parse_roadmap_section_content(path.read_text(), section)`
5. Update all call sites: replace `config.get("key", default)` with `config.get("key")` (default now in CONFIG_DEFAULTS)
6. Run existing test suite to confirm no regressions
7. Add unit test: parse_roadmap_section delegates to parse_roadmap_section_content
8. Add unit test: load_config() returns CONFIG_DEFAULTS when file is empty
9. Add unit test: loaded config values override defaults

**Edge Cases:**
- Missing ROADMAP file: parse_roadmap_section already returns [] on missing file (line 46-47 checks path.exists()). When delegating to parse_roadmap_section_content, this guard must be preserved: read file only if exists, else return [].
- Missing .config file: load_config() already returns {} on FileNotFoundError; merging with CONFIG_DEFAULTS ensures all keys present.
- Invalid JSON in .config: load_config() returns {} on parse error; merging with CONFIG_DEFAULTS ensures safe fallback to all defaults.
- Boolean vs string types: config.get("zie_memory_enabled", False) is used; CONFIG_DEFAULTS must preserve type consistency when merged.

**Out of Scope:**
- Renaming parse_roadmap_section or changing its function signature
- Adding new configuration keys beyond those currently used
- Refactoring other utility functions (atomic_write, caching, etc.)
- Changing hook behavior or test strategy
- Updating plugin.json or documentation beyond code comments

**Acceptance Criteria:**
1. `parse_roadmap_section()` delegates to `parse_roadmap_section_content()` — verify by reading implementation
2. `CONFIG_DEFAULTS` dict exists in utils.py with all 7 keys and correct default values
3. `load_config()` merges CONFIG_DEFAULTS with parsed JSON; loaded values take precedence
4. All 5 hook files with config.get() calls have defaults removed; calls now use config.get("key") only (auto-test, task-completed-gate, session-resume, safety-check, safety_check_agent)
5. All existing tests pass with no regressions
6. New unit tests cover: delegation, empty config fallback, override behavior
7. No changes to parse_roadmap_section call sites (parse_roadmap_now, parse_roadmap_ready still call it)
