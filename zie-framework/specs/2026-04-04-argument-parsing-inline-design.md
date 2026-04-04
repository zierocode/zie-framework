# Argument Parsing Block Compression — Design Spec

**Problem:** `commands/spec.md` and `commands/sprint.md` contain verbose Python-style argument parsing blocks (~80–120 words each) that duplicate prose with actual usage sites, inflating token cost and increasing distance between flag declaration and flag action.

**Approach:** Replace pre-amble parsing blocks with a compact 1-row-per-flag argument table (flag name, description, default) and move flag-handling logic inline at the step that consumes the flag. `clean_args` and per-flag extraction prose are removed; each step already knows its flag context from the table.

**Components:**
- `commands/spec.md` — remove Python parsing block; replace with argument table; inline `--draft-plan` handling at step 4
- `commands/sprint.md` — remove Python parsing block; replace with argument table; retain existing `--dry-run`, `--skip-ready`, `--version=` references inline at their usage steps
- `tests/unit/test_workflow_lean.py` — `TestZieSpecDraftPlanFlag.test_flag_removed_from_slug_extraction` checks `clean_args` OR `remove` OR `!= "--draft-plan"` — refactor must satisfy at least one of those tokens
- `tests/unit/test_zie_sprint.py` — `TestArgumentParsing` checks `--skip-ready`, `--version=`, `slugs`/`slug` presence — all must survive

**Data Flow:**
1. Reader reaches `## Arguments` table in command file → sees flag name + description in one line
2. At the step that consumes the flag, an inline conditional note covers handling (e.g., "if `--draft-plan` present → invoke write-plan")
3. No intermediate parsing block is evaluated; the argument table is the single source of truth
4. Test suite reads raw file text — tests pass as long as keyword tokens survive in the inline form

**Edge Cases:**
- `test_flag_removed_from_slug_extraction` checks `clean_args` OR `remove` OR `!= "--draft-plan"` — the inline note at step 4 of spec.md must include at least one of these tokens (prefer `remove` in prose: "remove `--draft-plan` from slug extraction")
- `--version=X.Y.Z` must appear in sprint.md argument table (not just the Python block) so the test still matches
- Do not touch any flags documented in skills (spec-design/SKILL.md already has its own table — no change needed)
- The `slugs` identifier must survive in sprint.md (keep it in the inline note where slug filtering is explained)

**Out of Scope:**
- Changing flag semantics or adding new flags
- Modifying any test assertions
- Touching any skill SKILL.md files
- Changing any other command files (audit.md, plan.md, etc.)
