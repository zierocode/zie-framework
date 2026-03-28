# DRY Utils Cleanup — parse_roadmap Duplication + .config Defaults

## Problem

Two minor DRY violations in `hooks/utils.py`:

1. **parse_roadmap_section (line ~38) vs parse_roadmap_section_content (line ~102):**
   Two nearly identical functions — one reads from disk path, one from a string.
   Both parse the same ROADMAP section format. If the section format ever changes,
   both functions need updating. Discovered via analysis; low risk but real violation.

2. **Scattered defensive .get() calls with inline defaults:**
   Hooks call `config.get("project_type", "unknown")`,
   `config.get("safety_check_mode", "regex")`, etc. in 12+ call sites across 8 files.
   Defaults are defined at the call site, not centrally — different files could use
   different defaults for the same key.

## Motivation

utils.py is the shared library for all hooks. Keeping it DRY and consistent reduces
the surface area for subtle bugs when hook behavior needs to change. This is a
low-risk, low-effort cleanup that improves the codebase's internal consistency.

## Rough Scope

**Consolidate parse_roadmap functions:**
- Keep `parse_roadmap_section_content(content: str, section: str) -> str`
  as the canonical implementation
- Replace `parse_roadmap_section(path: Path, section: str) -> str` with:
  `return parse_roadmap_section_content(path.read_text(), section)`
- Update all call sites (grep for both function names)

**Centralize .config defaults:**
- Add `CONFIG_DEFAULTS: dict` constant to utils.py with all known keys + defaults
- Update `load_config()` to merge `CONFIG_DEFAULTS` with parsed JSON
  (parsed values win over defaults)
- Remove all inline default arguments from `config.get()` call sites

**Tests:**
- parse_roadmap_section delegates to parse_roadmap_section_content
- load_config() returns CONFIG_DEFAULTS when config file is empty
- load_config() parsed values override defaults
- No regressions in existing utils tests
