---
slug: lean-sprint-phase2-redundant
approved: true
approved_at: 2026-04-04
---

# Remove Redundant Sprint Phase 2 — Design Spec

**Problem:** Sprint Phase 2 ("Plan All") is a structural no-op when Phase 1 succeeds — it filters for items with spec but no approved plan, but Phase 1 already runs spec+plan per item; Phase 2 only fires on Phase 1 mid-chain failures while still consuming a TaskCreate, progress bars, and a full ROADMAP re-read (~500–2000 tokens) on every sprint invocation regardless.

**Approach:** Remove Phase 2 as a named phase. Inline failure recovery directly into Phase 1: if a subagent returns without an approved plan, log a warning and add the slug to a `phase1_failed` list. After all Phase 1 agents complete, run a single inline retry pass for any slugs in `phase1_failed` — sequentially, no new TaskCreate phase. Renumber the remaining phases (3→2, 4→3, 5→4) and update all references (Summary table, ETA strings, Error Handling section, audit confirmation prompt). The `roadmap_post_phase2` binding is removed; Phase 2 (impl) reads from `roadmap_post_phase1`.

**Components:**
- `commands/sprint.md` — remove Phase 2 block; add inline retry pass to Phase 1; renumber Phase 3→2, 4→3, 5→4; update Summary table, ETA strings, audit confirmation prompt, Error Handling entries
- `zie-framework/ROADMAP.md` — move backlog item to Ready after spec/plan approved
- `tests/` — add/update sprint phase tests (partial Phase 1 failure triggers inline retry, no Phase 2 task created)

**Data Flow:**

1. Phase 1 spawns parallel spec+plan subagents (max 4), one per item in `needs_spec`
2. Each subagent result is collected: success → mark approved; failure → append slug to `phase1_failed`
3. After all agents resolve: if `phase1_failed` is non-empty, run inline retry pass — sequentially re-invoke spec-design → spec-reviewer → write-plan → plan-reviewer for each failed slug using synchronous `Skill()` calls (not background `Agent(run_in_background=True)`); this is error recovery, not parallel dispatch, so blocking sequential calls are appropriate and simpler to reason about
4. Inline retry success → slug added to approved set; failure → halt sprint with error
5. Reload ROADMAP unconditionally (even if `phase1_failed` was empty and no retry ran) after Phase 1 + inline retry → bind as `roadmap_post_phase1`; this single read captures all subagent writes regardless of whether retry occurred
6. Phase 2 (formerly Phase 3) reads from `roadmap_post_phase1` directly — no second ROADMAP bind

**Edge Cases:**
- All Phase 1 items succeed: `phase1_failed` is empty, inline retry is skipped (zero overhead)
- One or more Phase 1 subagents fail: inline retry runs sequentially for only the failed slugs
- Inline retry also fails: halt sprint, surface slug and error; user can fix and re-run sprint with that slug
- `needs_spec` is empty (all items already have approved spec+plan): Phase 1 and inline retry are both skipped entirely; sprint proceeds to Phase 2 (impl) directly from `roadmap_post_phase1`
- `--skip-ready` flag: skips items in Ready lane; if `needs_spec` becomes empty, Phase 1 is skipped; inline retry is also skipped
- Phase numbering in audit confirmation prompt must reflect 4-phase sprint (Spec → Impl → Release → Retro)
- **Agent timeout/hang:** Phase 1 subagents inherit Claude Code's native agent timeout. If a subagent hangs or is killed by timeout, its result is treated as a failure — the slug is appended to `phase1_failed` and inline retry is triggered. If the retry also hangs or times out, it is treated as an inline retry failure and the sprint halts. No special per-agent watchdog timer is implemented; the spec depends on Claude Code's built-in agent lifecycle enforcement.

**Out of Scope:**
- Changing Phase 1's parallel dispatch logic (max 4 agents, background spawn)
- Modifying implement, release, or retro phase behavior
- Extracting sprint orchestration to Python (ADR-035: pure Markdown command)
- Per-item release granularity (ADR-034: single batch release)
