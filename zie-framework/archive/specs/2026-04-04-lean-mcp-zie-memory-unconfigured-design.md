# lean-mcp-zie-memory-unconfigured — Design Spec

**Problem:** Commands and skills call `mcp__plugin_zie-memory_zie-memory__*` tools without checking `zie_memory_enabled`, causing "tool not found" errors when the zie-memory MCP plugin is absent from `settings.json`.

**Approach:** Audit every command (`commands/*.md`) and skill (`skills/*/SKILL.md`) that references a zie-memory MCP tool. For each bare call, wrap it in the existing `If zie_memory_enabled=true:` conditional guard — normalising to the same pattern already used by `session-learn.py`, `wip-checkpoint.py`, and several commands. No new abstractions, no new files.

**Components:**
- `commands/backlog.md` — recall call at Step 3 already guarded; remember call at Step 7 already guarded (verify)
- `commands/fix.md` — recall at Step 4; remember at Step 67 (verify both are guarded)
- `commands/implement.md` — recall at Step 36; brain write at Step 76 (verify both guarded)
- `commands/plan.md` — recall at Phase B Step 1; remember at Phase B Step 2 (verify both guarded)
- `commands/release.md` — recall + remember at Step 9 (verify guarded)
- `commands/retro.md` — recall at Phase 1 Step 1; remember at Phase 4 and self-tuning section (verify all guarded)
- `commands/init.md` — remember at Step 13 (verify guarded)
- `commands/spec.md` — delegates to spec-design skill; verify note is accurate
- `skills/spec-design/SKILL.md` — recall in "เตรียม context" section; remember at Step 7 (verify both guarded)
- Any other skill files that reference `mcp__plugin_zie-memory_zie-memory__*`

**Data Flow:**
1. Command/skill reads `zie-framework/.config` → extracts `zie_memory_enabled` (default `false`)
2. All brain steps evaluate `If zie_memory_enabled=true:` before calling any MCP tool
3. When `false` → brain steps are skipped silently; command continues normally
4. When `true` → MCP calls proceed as before
5. No change to hook behaviour (hooks already gate correctly via `utils_config.py`)

**Edge Cases:**
- `.config` absent → `zie_memory_enabled` defaults to `false` → all brain calls skipped (safe)
- `.config` present but `zie_memory_enabled` key missing → same default applies
- MCP tool present but `zie_memory_enabled=false` → calls still skipped (conservative; user must opt in)
- Skill invoked from a command that already read `.config` — skill re-reads its own config section or uses passed-in value; no cross-invocation state assumed

**Out of Scope:**
- Runtime detection of whether the MCP plugin is actually registered (that would require a tool probe call)
- Changing the `zie_memory_enabled` config key name or semantics
- Hook code changes (hooks already correct)
- Adding tests beyond existing command-flow unit tests
