---
description: Sprint clear — process all backlog items through full pipeline (spec→plan→implement→release→retro) with phase-parallel optimization, batch release, and single retro.
argument-hint: "[slug1 slug2...] [--dry-run] [--skip-ready] [--version=X.Y.Z]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, Skill
model: sonnet
effort: high
---

# /sprint — Sprint Clear (Backlog → Ship → Retro)

<!-- preflight: full -->

Run a complete sprint cycle: spec+plan all items concurrently (no cap), implement sequentially (WIP=1), batch release once, single retro. Delta-only progress during Phase 1; full table at phase end.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (checks all 3 steps + WIP guard).

4. Check current branch is `dev`.
5. Verify no uncommitted changes (warn if found).
6. Check `.zie/handoff.md` — if present, read it. After the sprint completes (after retro), delete `.zie/handoff.md`. If malformed (missing frontmatter) → warn and fall back to manual prompt mode.
7. **Sprint resume check** — Read `zie-framework/.sprint-state` if it exists:
   - Parse JSON: `{phase, items, completed_phases, remaining_items, started_at}`
   - If found: `"Incomplete sprint found (phase {phase}/4, {N} items remaining). Resume? (yes / restart)"`
   - `yes` → skip audit, jump to stored phase, use remaining_items
   - `restart` → delete `.sprint-state`, proceed fresh
   - Malformed → delete it, proceed fresh

## Arguments

| Flag / Positional | Description | Default |
| --- | --- | --- |
| `slugs` (positional) | Space-separated backlog slugs; omit for all Next+Ready | all items |
| `--dry-run` | Print sprint audit table and stop | off |
| `--skip-ready` | Skip items already in Ready lane | off |
| `--version=X.Y.Z` | Override version bump for Phase 3 release | auto |

## "All" means ALL — No Silent Drops

Every item in Next+Ready MUST be included. No silent drops. Missing items = error.

**Consolidation** (allowed, must declare): merge small items sharing a file/component, each <15 min, no spec/plan yet.
Print: `[MERGED] <slug-a> + <slug-b> → <combined-slug> — both touch <X>`. Never merge items with existing specs/plans or HIGH/CRITICAL priority.

## Step 0: AUDIT — Build Sprint Plan

1. **Read ROADMAP lanes** — Next (awaiting spec), Ready (approved plan), Now (active), Done (shipped)
2. **Classify items** — per slug: `[backlog ✓/—] [spec ✓/pending] [plan ✓/pending] [impl ✓/—]`
3. **Compute phase assignment**: needs_spec, needs_plan, ready_impl
4. **Check dependencies** — scan backlog files for `<!-- depends_on: slug-N -->` → serialize in PLAN/IMPL
5. **Compute suggested version** — bump patch from last `release:` git tag, store in `.zie/sprint-state.json`
6. **Print sprint audit table** — Needs Spec/Plan/Impl counts + per-item status
7. **--dry-run** → print table and stop
8. **User confirmation** → `yes`/`edit`/`cancel`

## Load Context Bundle

Invoke `Skill(zie-framework:load-context)` → `context_bundle` (ADRs + project context). Used by all downstream phases.

## Autonomous Mode

`autonomous_mode=true` for all skill invocations. Suppresses interactive turns, approval gates, agent spawns.

**Interruption Protocol** — sprint pauses for user only in 3 cases:
1. Clarity score < 2 → ask 1 question per vague item
2. Auto-fix failed after 1 retry → surface issue + interrupt
3. Unresolvable dependency conflict → ask once before Phase 1

**Clarity scoring** (per Next item needing spec):

| Criterion | Score |
| --- | --- |
| `## Problem` has ≥ 2 sentences | +1 |
| `## Rough Scope` has content | +1 |
| Title names a concrete action | +1 |
| Score ≥ 2 → direct; Score < 2 → ask 1 question | |

## PHASE 1: SPEC ALL (Parallel)

TaskCreate subject="Phase 1/4 — Spec All"

For `[clarity: ask]` items: ask 1 question per item first, then proceed.

For each item in needs_spec (parallel Skill calls, passing `context_bundle`):
1. `Skill(zie-framework:spec-design, '<slug> autonomous')` — writes spec, runs spec-reviewer inline, auto-approves
2. `Skill(zie-framework:write-plan, '<slug>')` — writes plan
3. Inline plan-reviewer: `Skill(zie-framework:plan-reviewer, context_bundle=<context_bundle>)`
   - ✅ APPROVED → `python3 hooks/approve.py <plan-file>` (ONLY approval path)
   - ❌ Issues Found → fix inline (1 pass), re-check once → re-run approve.py
   - Second failure → interrupt (Interruption Protocol case 2)

No Agent spawn. Skills run directly. On failure: inline retry once → still failing → interrupt.

Progress: `[spec N/total] <slug> ✓` or `[spec N/total] <slug> ❌ <issue>` (delta-only; full table at phase end).

After Phase 1: reload ROADMAP → `roadmap_post_phase1`. Write sprint context bundle to `.zie/sprint-context.json` (specs, plans, roadmap, context_bundle — passthrough for Phases 2-3).

TaskUpdate → Phase 1/4 complete. Write `.sprint-state` with phase=2.

**Context checkpoint:** Run `/compact` to clear Phase 1 history before implementation.

## PHASE 2: IMPLEMENT (Sequential, WIP=1)

TaskCreate subject="Phase 2/4 — Implement"

Read sprint context bundle from `.zie/sprint-context.json` (fallback: read from disk on resume).

For each Ready item (priority: CRITICAL → HIGH → MEDIUM → LOW):

1. Move Ready → Now in ROADMAP. Update `.sprint-state`: `current_task = <slug>`
2. `make zie-implement` — agent reads Now lane, implements, commits, exits
3. After return: check Now item `[x]` and committed → `[impl N/total] <slug> ✓`
4. Update `.sprint-state`: remove slug from remaining, `last_action = "impl-done:<slug>"`
5. If not last item: `/compact` → `[compact] context cleared after <slug>`
6. Non-zero exit → `[impl N/total] <slug> ❌ <issue>` → halt sprint

After all impl: all items `[x]` in Now. Write `.sprint-state` with phase=3.

**Context checkpoint:** Run `/compact` before release.

## PHASE 3: BATCH RELEASE

TaskCreate subject="Phase 3/4 — Release"

Read sprint context bundle + pre-computed version from `.zie/sprint-state.json`.

```bash
zie-release --bump-to=<version>
```

Override: `zie-release --bump-to=<version_override>`

Context passthrough: pass `sprint_context["specs"]` and `sprint_context["plans"]` to release for notes.

TaskUpdate → Phase 3/4 complete. Write `.sprint-state` with phase=4.

## PHASE 4: SPRINT RETRO (auto)

TaskCreate subject="Phase 4/4 — Retro"

Auto-invoke retro inline. Light mode (ROADMAP Done + ADR-000-summary only). Full ADR writing only if shipped plan has `<!-- adr: required -->`.

```bash
zie-retro
```

TaskUpdate → Phase 4/4 complete. Delete `.sprint-state`.

## Summary

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SPRINT COMPLETE

Shipped: <N> items | v<version>
Commits: <count> (phase 3)
Tests: ✓ unit | ✓ integration | ✓|n/a e2e
ADRs: <count> (phase 5)

Phases:
  1. Spec    — <N> items, <elapsed> (parallel + inline retry)
  2. Impl    — <N> items, <elapsed> | WIP=1
  3. Release — v<version>, <elapsed>
  4. Retro   — <N> ADRs, <elapsed>

Next: /backlog to queue new items.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

| Phase | Failure | Action |
| --- | --- | --- |
| Phase 1 | Retry exhausted | Halt sprint, surface issue |
| Phase 2 | Implement fails | Halt sprint, invoke `/fix` |
| Phase 3 | Release fails | Halt before merge, user debugs |
| Phase 4 | Retro fails | Non-blocking, print warning |

→ /status to check pipeline state