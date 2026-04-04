# Plan: zie-sprint Phase 1 — Invoke Skills Directly Instead of Commands

- **slug**: sprint-phase1-skill-direct
- **spec**: `zie-framework/specs/2026-04-04-sprint-phase1-skill-direct-design.md`
- **status**: approved
- **date**: 2026-04-04

---

## Tasks

### Task 1 — Rewrite Phase 1 agent prompt block in `zie-sprint.md`

**File**: `commands/zie-sprint.md` (lines ~122–132)

Replace the current agent prompt:

```
prompt: "Run spec + plan workflow. Slug: <slug>.
(1) Invoke /zie-spec <slug> --draft-plan
(2) Capture approved spec + plan from outputs
(3) Confirm both are approved before returning.
Report: [spec-<slug>] ✓ or ❌ <issue>"
```

With a direct skill-chain prompt:

```
prompt: "Run spec + plan workflow for slug: <slug>.
(1) Skill(spec-design, '<slug> quick') — write the spec
(2) Skill(spec-reviewer, '<slug>') — review and approve spec
(3) Skill(write-plan, '<slug>') — write the implementation plan
(4) Skill(plan-reviewer, '<slug>') — review and approve plan
Confirm both spec and plan are approved before returning.
Report: [spec-<slug>] ✓ or ❌ <issue>"
```

### Task 2 — Update Phase 2 stale `--draft-plan` reference

**File**: `commands/zie-sprint.md` (lines ~141–143)

The comment reads:

```
## PHASE 2: PLAN ALL (Parallel)

Items still needing plans (those not covered by Phase 1's --draft-plan).
```

Update to reflect direct skill chain:

```
## PHASE 2: PLAN ALL (Parallel)

Items still needing plans (those not covered by Phase 1's skill chain).
```

### Task 3 — Verify lint passes

Run `make lint` and confirm zero errors.

---

## Files to Change

| File | Change |
| --- | --- |
| `commands/zie-sprint.md` | Replace Phase 1 agent prompt (Task 1) + Phase 2 comment (Task 2) |

No other files change. No new files are created.
