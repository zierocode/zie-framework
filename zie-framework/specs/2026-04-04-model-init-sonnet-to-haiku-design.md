# Downgrade /init Model: sonnet → haiku — Design Spec

**Problem:** `/init` uses `model: sonnet` + `effort: medium` in its frontmatter, but the main-thread work is purely mechanical file scaffolding (copy templates, write stubs, create directories). Sonnet-level reasoning is not required for this work.

**Approach:** Change `model: sonnet` to `model: haiku` in `commands/init.md` frontmatter. The Explore subagent (step 2a) runs with its own model context and is unaffected. `effort: medium` stays — haiku at medium is correct for structured multi-step file creation. No logic changes; one-line frontmatter edit.

**Components:**
- `commands/init.md` — frontmatter line `model: sonnet` → `model: haiku`
- `tests/unit/test_init_command.py` (or equivalent) — assert expected directories and files are created (confirm scaffolding still works after model change)

**Data Flow:**
1. User runs `/init`
2. Claude Code loads `commands/init.md` frontmatter → selects `haiku` model
3. Init steps 1–14 execute (unchanged logic)
4. Explore subagent (step 2a) spawns with its own model (unaffected by frontmatter change)
5. All expected files and directories created as before

**Edge Cases:**
- Re-run guard (step 0): already-initialized projects skip the scan; haiku handles the guard check correctly (simple file existence check)
- Greenfield path: haiku creates templates without reasoning — mechanical copy, no degradation
- Existing-project path with Explore subagent: subagent uses its own model; main-thread model change is transparent

**Out of Scope:**
- Changing model for any other command (spec, plan, implement, etc.)
- Changing `effort` level
- Changing the Explore subagent's model or behavior
- Adding new init steps or features
