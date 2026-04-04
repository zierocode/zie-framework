# Remove zie- prefix from command names — Design Spec

**Problem:** Command names carry a redundant `zie-` prefix (e.g. `zie-fix.md`), making the full invocation `zie-framework:zie-fix`. The namespace already identifies the plugin; the prefix in the command name adds no value and creates visual noise.

**Approach:** Rename all 12 command files from `commands/zie-*.md` → `commands/*.md`, then do a targeted sweep of all internal references. The plugin namespace `zie-framework` stays untouched — only the command name segment changes. References in hooks, skills, tests, docs, and template files are updated in place. No backwards-compat shim needed since this is a solo-dev internal tool.

**Components:**
- `commands/zie-*.md` × 12 — rename to plain verb names (backlog, spec, plan, implement, fix, release, retro, sprint, status, init, audit, resync)
- `hooks/intent-sdlc.py` — SUGGESTIONS dict + STAGE_COMMANDS dict + gate message strings
- `hooks/session-resume.py` — any `/zie-*` strings in session context output
- `hooks/config-drift.py` — `/zie-resync` reference
- `hooks/knowledge-hash.py` — `/zie-resync` reference
- `skills/*/SKILL.md` × 13 — all `/zie-*` command references in skill prose
- `tests/unit/test_sdlc_gates.py` — file path references (`commands/zie-plan.md` etc.) + literal `/zie-*` command assertions
- `tests/unit/test_hooks_intent_sdlc.py` — assertions that check for `/zie-plan` etc. in hook output
- `tests/unit/*.py` — any other tests asserting `/zie-*` command strings (298 occurrences across 39 files)
- `commands/*.md` — cross-references inside command files themselves (`→ /zie-plan`, etc.)
- `CLAUDE.md` — SDLC Commands table + Development Commands section
- `README.md` — Commands table + Pipeline diagram
- `templates/ROADMAP.md.template` — if any `/zie-*` references exist
- `zie-framework/PROJECT.md`, `ROADMAP.md`, `project/architecture.md`, `project/components.md` — knowledge docs

**Data Flow:**
1. Rename 12 `commands/zie-*.md` files → `commands/*.md` (git mv)
2. Update `hooks/intent-sdlc.py`: SUGGESTIONS dict values, STAGE_COMMANDS dict values, all inline gate message strings
3. Update `hooks/session-resume.py`, `hooks/config-drift.py`, `hooks/knowledge-hash.py`: inline `/zie-*` strings
4. Update all `skills/*/SKILL.md` files: prose references to `/zie-*` commands
5. Update all `commands/*.md` files: cross-references to sibling commands
6. Update test files: both file-path strings (`commands/zie-plan.md`) and command invocation strings (`/zie-plan`)
7. Update `CLAUDE.md` SDLC Commands table
8. Update `README.md` Commands table + Pipeline diagram
9. Update `zie-framework/` knowledge docs (PROJECT.md, ROADMAP.md, architecture.md, components.md, ADR-000-summary.md as needed)
10. Run `make test-ci` — all 298+ occurrences must be green with new names

**Edge Cases:**
- Tests that check the file path `commands/zie-plan.md` (must update to `commands/plan.md`)
- Tests that assert `/zie-plan` in hook stdout (must update assertion to `/plan`)
- `test_sdlc_gates.py::TestIntentDetectPlan::test_plan_suggestion_maps_to_zie_plan` — name implies old command; rename test class + assertion
- `hooks/adr_summary.py` comment `Used by /zie-retro` — update to `/retro`
- Archive files under `zie-framework/archive/` mention old names in prose — leave untouched (historical record, not active code)
- `zie-framework/backlog/*.md` slugs like `zie-plan-notes-trim` reference the feature name, not the command — leave untouched
- `skills/zie-audit/SKILL.md` invocation line `Invoked by: Skill(zie-framework:zie-audit) from /zie-audit` — update to `/audit`
- `intent-sdlc.py` line 250: `if message.startswith("/zie-"):` — update to check `/` prefix more generically or list new command names

**Out of Scope:**
- Skill names (spec-design, write-plan, etc.) — already without zie- prefix
- Hook script filenames (hooks/*.py) — internal, not user-facing
- Plugin name (`zie-framework`) — namespace stays
- Agent filenames (`agents/*.md`)
- `plugin.json` metadata fields unrelated to command invocation
- Archive files under `zie-framework/archive/` — historical, not executed
- Backlog item slugs that happen to contain `zie-` as a feature name (e.g. `zie-plan-notes-trim`)
