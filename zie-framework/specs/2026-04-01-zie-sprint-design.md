---
approved: true
approved_at: 2026-04-01
backlog: backlog/zie-sprint.md
---

# zie-sprint — Design Spec

**Problem:** Running the zie-framework pipeline manually on multiple backlog items is O(N) in ceremony overhead — N releases, N retros, N context loads, N test gate runs — which is wasteful when processing a full sprint.

**Approach:** `/zie-sprint` orchestrates all backlog items through a 5-phase pipeline with phase-level parallelism: (1) spec all items in parallel, (2) plan all items in parallel, (3) implement sequentially (WIP=1), (4) single batch release, (5) single sprint retro. Each phase uses existing commands/skills — no new Python code. Context bundle (ADRs + project context) is loaded once and passed to all downstream agents. This reduces N releases → 1, N retros → 1, and ~25N context loads → 1.

**Components:**
- `commands/zie-sprint.md` — new command (already created, this spec formalizes it)
- Zero new hooks or Python files — pure orchestration
- Existing: `/zie-spec --draft-plan`, `/zie-plan slug1 slug2`, `/zie-implement`, `/zie-release`, `/zie-retro`

**Data Flow:**

1. **AUDIT** — Read ROADMAP Next + Ready lanes → classify items by pipeline stage → print sprint table → get user confirmation
2. **PHASE 1 (SPEC)** — For items missing spec: spawn parallel agents, each running `/zie-spec <slug> --draft-plan` — spec + plan in one agent call. Wait for all agents.
3. **PHASE 2 (PLAN)** — For items with spec but no plan: invoke `/zie-plan slug1 slug2 ...` (already parallel). Wait for all plans approved.
4. **PHASE 3 (IMPLEMENT)** — Read Ready items (priority order). For each: invoke `/zie-implement <slug>` sequentially. While item N runs, pre-load context for item N+1 (non-blocking). All items end up `[x]` in Now.
5. **PHASE 4 (RELEASE)** — Invoke `/zie-release` (or `--bump-to=X.Y.Z`). Ships all `[x]` Now items in single merge dev→main.
6. **PHASE 5 (RETRO)** — Invoke `/zie-retro`. Single sprint retro covers all shipped items.
7. **SUMMARY** — Print sprint summary: items shipped, phases, timing.

**Edge Cases:**
- Empty backlog: AUDIT prints "Nothing to sprint. Run /zie-backlog first." and stops.
- Now lane has `[ ]` active item: AUDIT warns "WIP active: `<slug>`. Complete or run /zie-fix before sprinting." Halt.
- Now lane has only `[x]` items (impl done, release pending): skip Phase 1–3, go to Phase 4 directly.
- Phase 1 agent fails: halt sprint, surface error, leave other items unchanged.
- Phase 3 impl fails mid-sprint: halt before next item, invoke `/zie-fix`, ask Zie to resume.
- Dependency detected (`<!-- depends_on: slug-N -->`): serialize those items in Phase 1 and Phase 3, document in AUDIT table.
- `--dry-run`: print AUDIT table only, no execution.
- `--skip-ready`: skip items already in Ready lane (Phase 1–2 only); go straight to Phase 3 for those items.
- `--version=X.Y.Z`: passes `--bump-to=X.Y.Z` to `/zie-release`.
- Only 1 item: behaves identically to manual pipeline — no regression.

**Out of Scope:**
- Cross-sprint dependency tracking
- Parallel implementation (WIP=1 is intentional)
- Backlog curation / re-ordering during sprint
- Partial-retro per implemented item
- Resume from mid-sprint (restart sprint from last checkpoint — future ADR)
