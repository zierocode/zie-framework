# Lean Dual Audit Pipeline — Design Spec

**Problem:** `commands/audit.md` contains a standalone 4-agent, 4-phase audit pipeline that duplicates context-bundle logic, ADR cache writes, and synthesis already present in `skills/zie-audit/SKILL.md`. Every audit invocation loads both, burning ~3,000–5,000 tokens on redundant setup. CLAUDE.md states `/audit` should invoke the skill, but the command runs its own pipeline independently first.

**Approach:** Make `skills/zie-audit/SKILL.md` the single canonical audit implementation. Merge the unique agent dimensions from `commands/audit.md` (Code Health/Performance detail, Structural/Observability detail, MCP server usage check) into the skill's existing agent roster. Reduce `commands/audit.md` to a thin dispatcher (~5 lines) that parses `--focus` and delegates to `Skill(zie-framework:zie-audit)`. Add a structural test asserting `audit.md` stays under a line threshold.

**Components:**
- `commands/audit.md` — stripped to thin dispatcher; frontmatter preserved; body becomes invocation + argument pass-through
- `skills/zie-audit/SKILL.md` — expanded to absorb unique checks from the command's 4-agent pipeline (MCP server usage check, code health/perf detail, structural/obs detail)
- `skills/zie-audit/reference.md` — may need scoring rubric updates if dimensions change
- `tests/test_structural.py` — new assertion: `audit.md` line count ≤ N (thin dispatcher threshold)

**Data Flow:**

1. User invokes `/audit [--focus <dim>]`
2. `commands/audit.md` (thin dispatcher) parses `--focus` from `$ARGUMENTS`
3. Dispatcher calls `Skill(zie-framework:zie-audit)` passing `--focus <dim>` or no args
4. `skills/zie-audit/SKILL.md` runs Phase 1 (build `research_profile` + `shared_context` once)
5. Phase 2 spawns 5 parallel agents (A–E) using `shared_context`; Agent B (Lean/Efficiency) already exists in skill; MCP usage check absorbed into Agent B or Agent E
6. Phase 3 (External Research) runs as before; Phase 4 (Synthesis) deduplicates + scores; Phase 5 (Report + Backlog Selection) presents findings
7. No duplicate Phase 1 context build; ADR cache written once by skill

**Agent merge map (command → skill):**

| Command agent | Skill agent | Merge action |
| --- | --- | --- |
| Agent 1 — Security/Deps | Agent A — Security | Security checks already covered; dep health checks: merge unique dep-health language (overly-loose pins, license risks, actively-maintained alternatives) into Agent A |
| Agent 2 — Code Health/Perf | Agent B — Lean/Efficiency + Agent E — Architecture | Dead code/duplication → Agent B; async/N+1/hot-path perf checks → Agent E (or B where applicable) |
| Agent 2 — MCP Server Usage check | Agent B or Agent E | Absorb MCP server usage check (grep commands/*.md + skills/*/SKILL.md for mcp__<name>__) into Agent E (Architecture dimension) |
| Agent 3 — Structural/Obs | Agent D — Docs + Agent E — Architecture | Stale docs/broken examples → Agent D; coupling/SRP/naming → Agent E; observability (health checks, log levels, graceful shutdown) → Agent E |
| Agent 4 — External Research | Phase 3 External Research | Already covered; query cap 15 maintained |

**--focus pass-through:**

The dispatcher parses `--focus <dim>` from `$ARGUMENTS` and passes it as-is to the skill. The skill's existing `--focus` logic (run only the matching agent in Phase 2, research only that dimension in Phase 3) handles routing. The command's old focus-map (`security→1`, `code→2`, etc.) is removed; the skill uses its own dimension naming.

**Edge Cases:**
- `--focus` with old command dimension names (`code`, `perf`, `structure`, `obs`) may not match skill dimension names (security, lean, quality, docs, arch) — dispatcher should pass through raw; skill resolves unknown values by running full audit (existing behavior)
- `reference.md` missing in skill dir — already handled by graceful skip (existing behavior)
- Thin dispatcher line threshold: set at 20 lines to allow frontmatter + argument block + invocation; structural test fails build if exceeded
- Existing `.config` files unchanged — no migration needed
- `zie-framework/evidence/` save path unchanged (skill already handles this)

**Out of Scope:**
- Changing the 5-agent structure inside the skill (only absorbing missing checks, not restructuring)
- Adding new audit dimensions not present in either current file
- Changing the scoring rubric or report format
- Migrating the `--focus` dimension names to a new vocabulary (deferred — separate backlog item if needed)
- Any changes to hooks or other commands
