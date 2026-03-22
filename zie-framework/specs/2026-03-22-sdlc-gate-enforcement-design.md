# Spec: SDLC Gate Enforcement + Parallel Agents

**Date**: 2026-03-22
**Status**: approved
**Author**: zie

---

## Problem

The current zie-framework allows (and accidentally encourages) skipping SDLC stages:
- `/zie-idea` moves features directly to Now without a plan approval gate
- `/zie-build` runs without checking if a plan exists or has been approved
- No backlog stage — ideas go straight to active work
- No parallel execution — planning and building are always sequential even when independent

## Goal

Enforce a strict stage gate: **idea → backlog → approved plan → build**, with auto-fallback when gates are skipped, and optional parallel agent execution for independent work.

---

## ROADMAP Lanes (4 lanes)

```
Next (backlog) → Ready (approved plans) → Now (WIP=1) → Done
```

**Next**: raw backlog items — lightweight idea files, not yet planned
**Ready**: approved implementation plans — ready to build, waiting for WIP slot
**Now**: active build — strictly one item at a time (WIP=1)
**Done**: shipped features

---

## Backlog Item Format

File: `zie-framework/backlog/<slug>.md`

```markdown
# Feature Name

1-2 paragraph description — what it is, why it's needed.

ref: <optional links>
```

ROADMAP Next entry:
```markdown
- [ ] Feature Name — [idea](backlog/slug.md)
```

No template enforcement. Freeform 1-2 paragraphs max.

---

## Plan Lifecycle

A plan file has two states:

| State | frontmatter | Meaning |
|-------|-------------|---------|
| **pending** | no `approved` key | Drafted, not yet approved |
| **approved** | `approved: true` + `approved_at: YYYY-MM-DD` | Approved, moves to Ready lane |

There is no `approved: false` state — a rejected plan is simply re-drafted (pending).

Plan files live at: `zie-framework/plans/<slug>.md`

Plan frontmatter format when approved:
```yaml
---
approved: true
approved_at: 2026-03-22
backlog: backlog/slug.md
---
```

---

## Command Redesign

### `/zie-idea`
- Captures idea → writes `zie-framework/backlog/<slug>.md`
- Adds entry to **ROADMAP Next** only
- Does NOT create plan
- Does NOT move to Now

### `/zie-plan [slug...]`

**No arguments**: list all Next items with index numbers → ask Zie to pick (e.g. "1, 3"). If Next is empty → print "No backlog items. Run /zie-idea first." and stop.

**With slug(s)**:
- Reads each backlog file as the lightweight spec
- If multiple slugs → spawn parallel agents (max 4) to draft plans simultaneously
- Presents each drafted plan to Zie for approval one at a time (sequential approval, parallel writing)
- **On approval**: set `approved: true` + `approved_at` in plan frontmatter → move ROADMAP Next → **Ready**
- **On rejection**: ask "re-draft or drop back to Next?" → re-draft keeps pending state and retries; drop back leaves item in Next unchanged

### `/zie-build [slug?]`

**Pre-flight checks (in order)**:
1. If Now is occupied → print "Now: `<current>` in progress. Finish it or run /zie-ship." and stop.
2. If Ready lane is empty → auto-fallback: print "[zie-build] No approved plan. Running /zie-plan first..." → run `/zie-plan` flow → after approval, continue to build automatically.
3. If Ready has items → pull first item → move to **Now**

**AC#3 exact behavior**: if plan file exists but `approved: true` is absent → treat as missing approved plan → trigger auto-fallback (same as no Ready item). Never silently skip this check.

**Build execution**:
- Parse tasks in plan for `depends_on` markers (see Task Format below)
- Tasks without `depends_on` → group as independent → spawn parallel agents (max 4)
- If 0 independent tasks (all have `depends_on`) → execute all sequentially in dependency order; no agents spawned
- Tasks with `depends_on` → run after all listed tasks complete
- TDD loop per task (RED → GREEN → REFACTOR)

---

## Task Format in Plans

Tasks use a structured markdown comment for dependency declaration:

```markdown
- [ ] T1: Write tests for hook A
- [ ] T2: Write tests for hook B
- [ ] T3: Integrate A + B
  <!-- depends_on: T1, T2 -->
```

The `<!-- depends_on: -->` comment is the machine-readable marker. Claude reads this when building the dependency graph. Tasks without this comment are treated as independent.

---

## Parallel Agent Rules

**`/zie-plan` parallelism** (planning phase):
- N slugs selected → spawn min(N, 4) agents
- Each agent: reads its backlog file → drafts plan → returns to main thread
- Main thread presents plans to Zie one at a time for approval

**`/zie-build` parallelism** (build phase):
- Count independent tasks → spawn min(count, 4) agents simultaneously
- If count = 0 (all dependent) → sequential execution, no agents
- Tasks with dependencies → run after all blocking tasks complete

**Hard cap**: max 4 parallel agents at any time (both planning and building)

---

## Auto-fallback Logic (complete)

```
/zie-build called
  → Now occupied?
      → "Now: <X> in progress. Finish it or run /zie-ship." → STOP

  → Ready lane empty?
      → "[zie-build] No approved plan. Running /zie-plan first..."
      → Next empty?
          → "No backlog items. Run /zie-idea first." → STOP
      → Next has items?
          → run /zie-plan (show list, Zie picks)
          → get approval → continue to build

  → Ready has item, Now empty?
      → proceed normally
```

---

## Acceptance Criteria

1. `/zie-idea` writes to `zie-framework/backlog/` and ROADMAP Next only — never Ready or Now
2. `/zie-plan` with no args lists Next items; if Next empty → error message + stop
3. `/zie-plan` sets `approved: true` + `approved_at` in plan frontmatter on approval; on rejection → re-draft or drop to Next
4. `/zie-build` checks plan frontmatter for `approved: true` before proceeding; if absent → auto-fallback (not hard error)
5. `/zie-build` blocks with clear message if Now is already occupied (WIP=1)
6. `/zie-build` auto-runs `/zie-plan` when Ready is empty; if Next also empty → error + stop
7. Parallel agents capped at max 4 in both `/zie-plan` and `/zie-build`
8. `/zie-build` falls back to sequential execution gracefully when all tasks have `depends_on` (0 independent tasks)
9. ROADMAP template updated to include Ready lane section

---

## zie-memory Integration

zie-memory functions as a **compounding intelligence layer** — every cycle stores learnings that make the next cycle smarter.

### Optimization Principles

| Principle | Rule |
|-----------|------|
| **Batch recall** | One query per command, not multiple round-trips |
| **WIP supersede** | Update existing WIP memory, never append duplicates |
| **Conditional write** | Store micro-learnings only on friction — not every task |
| **Retro compression** | Synthesize + forget individual learnings at retro time |
| **Session cache** | Within one session, recall once — reuse result, don't re-query |
| **Context handoff** | /zie-plan recall result is baked into plan → /zie-build skips domain re-recall |

---

### `/zie-idea`
```
READ (1 batch query):
  recall project=<project> domain=<domain> limit=15
  → returns: past backlog items, shipped features, retro patterns in one call
  → use to: detect duplicates, surface prior approaches

WRITE:
  "Backlog: <slug>. Problem: <why>. Domain: <domain>."
  tags: [backlog, <project>, <domain>]
```

### `/zie-plan`
```
READ (1 batch query):
  recall project=<project> domain=<domain> tags=[shipped,retro,bug,decision] limit=20
  → returns: past approaches, pain points, ADRs, known bugs — one round-trip
  → bake key findings into plan document as "context notes" section
  → /zie-build reads notes from plan — no need to re-recall

WRITE (on approval):
  "Plan approved: <feature>. Tasks: N. Complexity: S/M/L. Decisions: [<d1>]."
  tags: [plan, <project>, <domain>]
```

### `/zie-build`
```
READ (resume only — domain context already in plan):
  recall project=<project> tags=[wip] feature=<slug> limit=1
  → only retrieve WIP snapshot for session resume — skip domain re-recall

WRITE (WIP checkpoint, every 5 tasks — SUPERSEDE previous):
  "WIP: <feature> — T<N>/<total> done."
  tags: [wip, <project>, <feature-slug>]
  supersedes: previous memory with same tags

WRITE (micro-learning — ONLY on friction, not every task):
  IF task took significantly longer than expected OR hit unexpected complexity:
    "Task harder than estimated: <why>. Next time: <tip>."
    tags: [build-learning, <project>, <domain>]
```

### `/zie-ship`
```
READ (1 batch query):
  recall project=<project> tags=[wip, plan] feature=<slug> limit=5
  → pull WIP notes + plan estimate → compute actual vs estimated complexity

WRITE:
  "Shipped: <feature> v<version>. Tasks: N. Actual: <vs estimate>."
  tags: [shipped, <project>, <domain>]
```

### `/zie-retro`
```
READ (1 batch query):
  recall project=<project> since=<last_retro_date> limit=50
  → returns all: shipped, build-learnings, bugs, WIPs, plans since last retro

SYNTHESIZE → COMPRESS → FORGET:
  1. Identify recurring patterns in build-learnings
  2. Store compressed summary: "Pattern: <X> — seen N times this sprint. Fix: <Y>."
     tags: [retro-learning, <project>]
  3. Forget individual build-learning memories (replaced by summary)

WRITE:
  "Retro <date>: N features. Pain: [X]. Pattern: <Z>. Next: <improvement>."
  tags: [retro, <project>]
```

### `/zie-fix`
```
READ (1 batch query):
  recall project=<project> domain=<domain> tags=[bug, build-learning] limit=10
  → detect recurring patterns, surface known fragile areas

WRITE (after fix confirmed):
  "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>."
  tags: [bug, <project>, <domain>]
```

### Compound Loop
```
/zie-plan recall (batched) → context baked into plan
  → /zie-build reads plan context (no re-recall)
  → friction triggers micro-learning (conditional)
  → /zie-retro compresses learnings → forgets noise
  → next /zie-plan recall gets richer signal, less noise
```
Brain stays lean — compression prevents unbounded growth.

---

## Implementation Notes

- `intent-detect.py` should add a `plan` pattern to suggest `/zie-plan` (e.g. on "plan", "ต้องการ plan", "วางแผน")
- New `zie-framework/backlog/` directory created by `/zie-init`
- ROADMAP.md.template updated with Ready section

---

## Out of Scope

- Spec as a separate artifact (backlog item = lightweight spec)
- Multi-item Now (WIP stays at 1)
- Agent orchestration UI
- Changing `/zie-ship`, `/zie-retro`, `/zie-fix` gate/flow logic — zie-memory integration for these is additive-only (read/write calls added, existing behavior unchanged)
- Parallel agent partial failure handling (halt vs continue) — deferred to future spec
- Machine validation of `depends_on` syntax (Claude reads it, no parser needed)
