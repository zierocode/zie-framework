# Spec: retro-inline-agents — Replace Parallel Agent Spawns with Inline Writes

- **slug:** retro-inline-agents
- **status:** draft
- **date:** 2026-04-04

## Problem

`commands/zie-retro.md` (lines 94–99) spawns 2 parallel background Agents:

1. **ADR agent** — writes ≤5 ADR files to `zie-framework/decisions/`
2. **ROADMAP agent** — moves shipped items to the Done lane in `zie-framework/ROADMAP.md`

Both tasks are deterministic structured file writes. Using `Agent(run_in_background=True, ...)` for them adds:
- Agent spawn latency (round-trip overhead per agent)
- Context serialization overhead (1k–2k tokens to package `done_section_current`, `decisions_json`, `shipped_items` into each subprompt)
- An additional failure vector (`"Failure mode: If either Agent fails → skip brain store"`)

The retro command already holds all required data in its live context at the point of the agent launch. No independent reasoning is needed — only structured writes.

## Solution

Replace both `Agent(...)` spawns with inline Write/Edit operations executed directly in the retro command flow:

1. **ADR writes (inline):** For each decision in `decisions_json`, call `Write` to create `zie-framework/decisions/ADR-<NNN>-<slug>.md` directly. Print `[ADR N/total]` per file. No agent spawn.
2. **ROADMAP update (inline):** Read `zie-framework/ROADMAP.md`, locate the `## Done` section, prepend shipped items with date + version tag, then `Edit` or `Write` the file back. No agent spawn.

The parallel section heading (`### บันทึก ADRs + อัปเดต ROADMAP (parallel)`) becomes sequential but is renamed to remove the `(parallel)` qualifier. The fallback comment block (`<!-- fallback: ... -->`) is removed since the inline path IS the only path.

The failure-mode paragraph is updated: individual step failures print an error and continue (same non-blocking pattern used elsewhere in retro).

### Affected tests

Three test files assert the old parallel-agent behavior. They must be updated alongside the command:

| File | Assertions to remove / replace |
| --- | --- |
| `tests/unit/test_retro_parallel.py` | `run_in_background` presence, parallel/concurrent wording, brain-store ordering by agent position |
| `tests/unit/test_zie_retro_parallel_agents.py` | `run_in_background=True` ×2, `general-purpose` ×2, `Await both`, parallel wording |
| `tests/unit/test_async_skills.py` | `general-purpose` + `run_in_background` + `Write ADR` assertions for retro |

New assertions replace them: inline `Write` call for ADRs, inline `Edit`/`Write` for ROADMAP, no `Agent(` in the ADR+ROADMAP section, no `run_in_background` in retro.

## Acceptance Criteria

1. `commands/zie-retro.md` contains no `Agent(` call in the ADR + ROADMAP update section.
2. `commands/zie-retro.md` contains no `run_in_background` keyword (retro-specific; `<!-- fallback` comment removed).
3. The command instructs inline `Write` for each ADR file.
4. The command instructs inline `Edit` or `Write` for the ROADMAP Done section.
5. The `(parallel)` qualifier is removed from the section heading.
6. The old failure-mode paragraph (`"If either Agent fails → skip brain store"`) is replaced with a non-blocking inline error-continue note.
7. All three affected test files are updated: old parallel-agent assertions removed, new inline-write assertions added.
8. `make test-fast` passes with zero failures after changes.

## Out of Scope

- Python hook changes — none required (markdown-only change).
- Done-rotation logic — unchanged (already inline).
- Brain store step — unchanged.
- Auto-commit step — unchanged.
- `zie-release.md` — not touched; its `run_in_background` Bash gates are unrelated.
