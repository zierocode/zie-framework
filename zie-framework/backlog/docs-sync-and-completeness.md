# Docs: Sync and Completeness Pass

**Source**: audit-2026-03-24b H8+H9+H10 + M10-M12 + L11-L14 (Agent D)
**Effort**: S
**Score impact**: +8+8 High + +9 Medium + +4 Low = +29 (Docs dimension to ~95)

## Problem

Multiple doc sync issues discovered in audit:

### Critical/High
- **PROJECT.md:7**: Shows "Version: 1.6.0" — actual version is 1.8.0
- **CLAUDE.md:15-22**: Tech Stack section missing optional deps (pytest, zie-memory,
  playwright) — README has Dependencies table but CLAUDE.md doesn't
- **README.md:175-176**: References `zie_memory_enabled` config key not explained
  anywhere in CLAUDE.md

### Medium
- **README.md**: No Skills section — PROJECT.md lists 11 skills but README shows none
- **CLAUDE.md**: Agent modes documented only in README; no cross-reference
- **architecture.md:61-69**: Version history stops at v1.4.0; missing v1.5.0–v1.8.0
- **PROJECT.md**: Thai/English mixing in table headers ("ทำอะไร" vs "Description")
- **README.md:84-87**: Project structure shows extra `project/` nesting level

### Low
- **CHANGELOG.md:35-50**: v1.7.0 and v1.8.0 descriptions overlap in language
- **hooks/knowledge-hash.py**: Exists on disk, not in hooks.json or components.md
  (clarify: is it active, legacy, or internal?)
- **README.md Troubleshooting**: Generic placeholders without inline explanation

## Scope

- Run `make sync-version` to fix PROJECT.md version (should be automated)
- Update CLAUDE.md Tech Stack with optional deps table
- Add Skills section to README.md (copy from PROJECT.md)
- Add cross-reference from CLAUDE.md → README.md for agent modes and zie-memory
- Extend architecture.md with v1.5.0–v1.8.0 delta summaries
- Standardize PROJECT.md table headers to English
- Fix README project structure diagram (remove extra `project/` level)
- Clarify knowledge-hash.py status (active → add to hooks.json? or legacy → note it)
- Add `make sync-version` to release checklist in CLAUDE.md

## Acceptance Criteria

- [ ] PROJECT.md shows v1.8.0
- [ ] CLAUDE.md has dependency table matching README
- [ ] README has Skills section
- [ ] architecture.md covers v1.5.0 through v1.8.0
- [ ] PROJECT.md table headers all English
- [ ] README structure diagram accurate
- [ ] knowledge-hash.py status documented
- [ ] `make sync-version` in release checklist
