# UX Output Formatting and Progress Visibility — Design Spec

**Problem:** zie-framework output is inconsistent across commands — some steps are verbose, some silent, formatting varies between hooks and commands. For long-running tasks like `/zie-sprint`, there is no way to know how far along the session is, what is left, or how long it will take.

**Approach:** Four-layer improvement: (1) complete the phase/step counter rollout to the three commands that still lack it (`zie-implement`, `zie-audit`, `zie-resync`); (2) add Unicode progress bars to multi-step sprint phases; (3) use `TaskCreate`/`TaskUpdate` in `/zie-sprint` as a live progress tracker; (4) formalize hook output as structured `key: value` pairs under the existing `[zie-framework]` prefix. A lightweight phase-count ETA signal ("Phase 3/5 — 2 phases remaining") is included; wall-clock ETA is not.

**Components:**
- Modify: `commands/zie-implement.md` — print `[T{N}/{total}]` at each task start; print `→ RED`, `→ GREEN`, `→ REFACTOR` phase markers; print `✓ T{N} done — {remaining} remaining` at task end
- Modify: `commands/zie-audit.md` — print `[Phase 1/5]` … `[Phase 5/5]` at each audit phase; print `Agent {X} (Domain) ✓` per spawned agent; print `[Research {N}/15]` per search call
- Modify: `commands/zie-resync.md` — print `[Exploring codebase...]` at scan start; print completion summary line
- Modify: `commands/zie-sprint.md` — wrap each phase with `TaskCreate` (Phase 1 Spec / Phase 2 Plan / Phase 3 Impl / Phase 4 Release / Phase 5 Retro); call `TaskUpdate` to mark complete; add progress bar line after each agent batch completes (`████████░░ 8/10 (80%)`)
- Modify: `hooks/session-resume.py` — already structured; no change needed
- Document: `CLAUDE.md` hook output convention — `[zie-framework] key: value` format applies to **INFO-level progress output only**; error output in hooks keeps its existing free-form format. Existing hooks (`wip-checkpoint`, `task-completed-gate`) already comply for errors and do not need changes. No hook Python code changes are required — only CLAUDE.md is updated. Sections to update: **Hook Output Convention** (new subsection under "Hook Context Hints") and **Hook Error Handling Convention** (add a note clarifying the INFO vs error distinction).

**Data Flow:**
1. Command starts a multi-step sequence → prints `[Phase N/M]` or `[TN/M]` header before work begins
2. For sprint phases: `TaskCreate` called with phase label → work executes → `TaskUpdate` marks done
3. After each sprint batch: progress bar computed as `done/total` → printed as `████…░░ done/total (pct%)`
4. Hook fires → prints `[zie-framework] <noun>: <value>` to stdout/stderr per existing convention (INFO-level only)

**Edge Cases:**
- `zie-implement` with 0 tasks (empty plan) → skip counter printing entirely, print "No tasks found in plan"
- `zie-audit` with fewer than 5 phases → print only as many `[Phase N/M]` as phases present; M is dynamic
- Progress bar with total=0 → skip bar line entirely
- Unicode not supported in terminal → progress bar still renders (Unicode blocks are broadly supported; no ASCII fallback added per YAGNI)
- Sprint agent failure mid-batch → progress bar shows partial count; failure message printed; sprint halts

**Out of Scope:**
- Wall-clock ETA estimation — requires timing that commands cannot access reliably
- Real-time overwrite / streaming progress bars (terminal control codes)
- Graphical UI or external dashboard
- Adding `[zie-framework]` prefix to hooks that do not yet have it (all hooks already comply per audit)
- Hook output refactoring — existing hooks already follow `[zie-framework] noun: value` convention; no code change needed
- Progress tracking in hooks (hooks are stateless per-event, not multi-step)

**Acceptance Criteria:**
- [ ] `zie-implement` prints `[T{N}/{total}]` before each task and `✓ T{N} done — {remaining} remaining` after
- [ ] `zie-implement` prints `→ RED`, `→ GREEN`, `→ REFACTOR` phase markers per task
- [ ] `zie-audit` prints `[Phase 1/5]` through `[Phase 5/5]` at each phase start
- [ ] `zie-resync` prints `[Exploring codebase...]` at scan start and a completion summary
- [ ] `zie-sprint` calls `TaskCreate` for each of the 5 phases before the phase begins
- [ ] `zie-sprint` calls `TaskUpdate` to mark each phase complete after it finishes
- [ ] `zie-sprint` prints a Unicode progress bar after each phase-batch completes
- [ ] Progress bar format: `████████░░ {done}/{total} ({pct}%)`
- [ ] `zie-sprint` prints a phase-count ETA signal after each phase: `Phase {N}/{total} — {remaining} phases remaining`
- [ ] No change to command logic, only output additions
- [ ] All changes are to command `.md` files only — no hook Python changes required
