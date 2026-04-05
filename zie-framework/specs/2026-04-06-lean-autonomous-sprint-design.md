---
title: Lean Autonomous Sprint
slug: lean-autonomous-sprint
approved: true
date: 2026-04-06
---

# Lean Autonomous Sprint

## Problem

The full pipeline (backlog → spec → plan → implement → release → retro) consumes excessive
Claude Code usage — both in token cost and wall-clock time. The main culprits are:

1. `spec-design` skill runs interactive multi-turn brainstorm + spec-reviewer agent per feature
2. `plan-reviewer` spawns a dedicated Agent per plan
3. `impl-reviewer` spawns background Agents per HIGH-risk task
4. Sprint halts at ~9 user gates before reaching retro

Zie's actual workflow: batch backlog items, run `/sprint` once, want it to finish unattended.

## Goals

- Reduce sprint token usage by ~55–65% for a typical 3-feature sprint
- Remove all non-essential user interruptions during `/sprint`
- Keep interactive behavior when commands run standalone (`/spec`, `/plan`, `/implement`)
- Preserve review quality: inline review replaces agent review (not removed)

## Non-Goals

- Changing `/chore`, `/hotfix`, `/fix` — already lean
- Removing TDD loop from implement
- Changing behavior of standalone commands (non-sprint context)

## Acceptance Criteria

- [ ] `/sprint` runs from backlog audit → retro with zero user gates for clear backlog items
- [ ] `spec-design` skips interactive brainstorm when called with `autonomous_mode=true`
- [ ] `spec-reviewer`, `plan-reviewer` run inline (no `Agent()` spawn) in autonomous mode
- [ ] `impl-reviewer` runs inline after each HIGH-risk task (no background Agent spawn)
- [ ] Auto-fix protocol: issues found → fix → test → continue; interrupt only on fix failure
- [ ] `/sprint` auto-runs retro in Phase 5 (no user prompt)
- [ ] Retro runs in light mode by default: ROADMAP update + ADR summary only
- [ ] Full ADR written only when plan contains `<!-- adr: required -->` tag
- [ ] Backlog clarity detection gates spec Q&A: vague backlog → max 1 question; clear → write direct
- [ ] All behavior changes are internal to sprint context — standalone commands unchanged

---

## Design

### Autonomous Mode Flag

`/sprint` sets an internal `autonomous_mode=true` context variable before Phase 1.
This is passed to every skill invocation: `spec-design`, `write-plan`, reviewer skills, `verify`.
**Not a user-facing flag** — only sprint sets it.

### Interruption Protocol

Sprint interrupts the user in exactly 3 cases:

1. **Backlog too vague** — clarity score fails (see below) → ask 1 question → continue
2. **Auto-fix failed** — reviewer found issues → Claude fixed → tests still fail after 1 retry → surface + ask
3. **Dependency conflict** — backlog items have unresolvable ordering conflict → ask once before Phase 1

All other decisions are made autonomously.

### Spec Stage — Clarity Detection + Direct Write

**Clarity scoring** (applied per backlog item in Phase 1 audit):

| Signal | Points |
|--------|--------|
| `## Problem` has ≥ 2 sentences | +1 |
| `## Rough Scope` has content | +1 |
| Title names a concrete action ("add X", "fix Y", "remove Z") | +1 |

Score ≥ 2 → **direct-write mode**: `spec-design` writes spec from backlog without asking  
Score < 2 → **1-question mode**: ask one clarifying question, then write

**`spec-design` skill changes:**

- Add `autonomous_mode` param
- When `true`: skip brainstorm loop (no clarifying Qs, no approaches, no approval rounds)
- Write spec directly from backlog content + clarity signals
- `spec-reviewer` runs inline (same context, single pass) instead of spawning Agent
- No issues → `approved: true` written automatically
- Issues found → fix inline → re-check once → approve

### Plan Stage — Inline Review + Auto-Approve

**`write-plan` skill changes:**

- Add `autonomous_mode` param
- When `true`: write plan tasks, run `plan-reviewer` inline (not Agent spawn)
- No issues → `approved: true` written, ROADMAP Next → Ready automatically
- Issues found → fix inline → approve

### Implement Stage — Inline Reviewer

**`commands/implement.md` changes:**

Replace background `Agent()` impl-reviewer pattern with inline check:

```
After each HIGH-risk task:
  → inline review (Claude checks changed files in current context)
  → issues found → auto-fix → make test-unit
    → pass → mark task done, continue
    → fail after 1 retry → interrupt (Interruption Protocol case 2)
  → no issues → mark task done, continue
```

LOW-risk tasks: unchanged (skip review).

### Sprint Phase 5 — Auto Retro

- Remove "→ /retro" prompt at sprint end
- Auto-invoke retro inline as Phase 5
- **Light mode** (default): ROADMAP Done lane update + ADR-000-summary.md update only
- **Full ADR mode**: triggered only when any shipped plan contains `<!-- adr: required -->` tag
- docs-sync still runs (lightweight)

### Files to Modify

| File | Change |
|------|--------|
| `commands/sprint.md` | Add autonomous_mode context, clarity detection in Step 0, auto-run Phase 5 retro |
| `skills/spec-design/SKILL.md` | Add autonomous_mode path: direct-write, inline spec-reviewer |
| `skills/spec-reviewer/SKILL.md` | Add inline mode (skip Agent spawn, run in caller context) |
| `skills/plan-reviewer/SKILL.md` | Add inline mode (skip Agent spawn, run in caller context) |
| `skills/write-plan/SKILL.md` | Add autonomous_mode path: inline plan-reviewer, auto-approve |
| `commands/implement.md` | Replace background impl-reviewer Agent with inline check + auto-fix |
| `commands/retro.md` | Add light mode: ROADMAP + summary only; full ADR gated on tag |

### Estimated Impact

For a 3-feature sprint:

| Metric | Before | After |
|--------|--------|-------|
| Interactive turns | ~30–50 | 0–3 |
| Agent spawns | ~15 | 0 |
| User gates | ~9 | 0–3 |
| Token usage | baseline | ~55–65% reduction |
