# Plan: retro-inline-agents — Replace Parallel Agent Spawns with Inline Writes

- **slug:** retro-inline-agents
- **status:** approved
- **spec:** zie-framework/specs/2026-04-04-retro-inline-agents-design.md
- **date:** 2026-04-04

## Tasks

### Task 1 — Edit `commands/zie-retro.md`: replace parallel-agent section

**File:** `commands/zie-retro.md`

Replace the section `### บันทึก ADRs + อัปเดต ROADMAP (parallel)` (lines 92–113) with:

```
### บันทึก ADRs + อัปเดต ROADMAP

**Write ADRs inline.** For each decision in `decisions_json`:
- Compose ADR content: 5-section format — Status (Accepted), Context (1–3 sentences),
  Decision (1–3 sentences), Consequences (Positive/Negative/Neutral), Alternatives.
- Call `Write` → `zie-framework/decisions/ADR-<NNN>-<slug>.md`
- Print `[ADR N/total]` after each file.
- On error: print `[zie-framework] retro: ADR write failed — <error>` and continue.

**Update ROADMAP Done inline.**
- Read `zie-framework/ROADMAP.md`.
- Move shipped items from `shipped_items` to the `## Done` section with date and version tag.
- Call `Edit` (or `Write`) to persist the updated file.
- On error: print `[zie-framework] retro: ROADMAP update failed — <error>` and continue.
```

Also remove the `<!-- fallback: ... -->` comment block (lines 114) entirely — inline is now the primary path.

### Task 2 — Update `tests/unit/test_retro_parallel.py`

Replace the three existing tests with inline-write equivalents:

- `test_retro_has_parallel_agent_note` → `test_retro_writes_adrs_inline`: assert `"Write"` and `"ADR"` present; assert `"run_in_background"` NOT in text.
- `test_retro_brain_store_after_agents` → `test_retro_brain_store_after_writes`: find position of `"Write ADR"` or `"Write` …`decisions/"`, assert `"บันทึกสู่ brain"` appears after it.
- `test_retro_failure_mode_documented` → keep (assert `"fail"` or `"error"` or `"continue"` in text — still satisfied).
- `TestRetroLeanContextExtension.test_retro_compact_bundle_has_done_section_current` → keep as-is (still valid; `done_section_current` stays in the bundle).

### Task 3 — Update `tests/unit/test_zie_retro_parallel_agents.py`

Replace the class `TestRetroParallelAgents` with `TestRetroInlineWrites`:

- `test_adr_roadmap_agents_both_present` → `test_adr_and_roadmap_both_present`: assert `"ADR"` and `"ROADMAP"` in text; drop `"parallel"` assertion.
- `test_agents_use_general_purpose` → remove entirely (no agents).
- `test_agents_run_in_background` → `test_no_run_in_background_in_retro`: assert `"run_in_background"` NOT in text (for retro).
- `test_no_skill_references_in_prompts` → keep intent, simplify: assert `'subagent_type='` not in text.
- `test_await_both_before_brain_store` → remove (no async await needed).

### Task 4 — Update `tests/unit/test_async_skills.py`

In `TestAsyncSkillPatterns.test_zie_retro_uses_agent_for_file_writing`:

- Rename to `test_zie_retro_writes_adrs_inline`.
- Remove: `general-purpose` assertion, `run_in_background` assertion.
- Keep: `"Write ADR"` or `"Write"` + `"ADR"` assertion.
- Add: assert `"Agent("` not in the ADR/ROADMAP section of retro (check text before the brain-store heading).

`test_fallback_handling_present` — update retro assertion: remove `"Failure mode"` check, keep `"fail"` or `"error"` or `"continue"` check (non-blocking error-continue note satisfies this).

### Task 5 — Verify

```bash
make test-fast
make lint
```

Zero failures required before done.

## Files to Change

| File | Change |
| --- | --- |
| `commands/zie-retro.md` | Replace lines 92–114: parallel Agent section → inline Write/Edit instructions; remove fallback comment |
| `tests/unit/test_retro_parallel.py` | Replace agent-centric assertions with inline-write assertions |
| `tests/unit/test_zie_retro_parallel_agents.py` | Replace `TestRetroParallelAgents` with `TestRetroInlineWrites`; remove agent-specific tests |
| `tests/unit/test_async_skills.py` | Update `test_zie_retro_uses_agent_for_file_writing` → `test_zie_retro_writes_adrs_inline`; update fallback assertion |

No Python files change. No new files needed.
