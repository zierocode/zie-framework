---
description: Sprint clear — process all backlog items through full pipeline (spec→plan→implement→release→retro) with phase-parallel optimization, batch release, and single retro.
argument-hint: "[slug1 slug2...] [--dry-run] [--skip-ready] [--version=X.Y.Z]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, Skill
model: sonnet
effort: high
---

# /sprint — Sprint Clear (Backlog → Ship → Retro)

Run a complete sprint cycle: spec+plan all items concurrently (no cap), implement sequentially (WIP=1), batch release once, single retro. Delta-only progress during Phase 1; full table at phase end.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Read `zie-framework/.config` → zie_memory_enabled, project_type.
3. Read `zie-framework/ROADMAP.md` → check all lanes.
4. Check current branch is `dev`.
5. Verify no uncommitted changes (warn if found).

## Arguments

| Flag / Positional | Description | Default |
| --- | --- | --- |
| `slugs` (positional) | Space-separated backlog slugs to process; omit to process all Next+Ready items | all items |
| `--dry-run` | Print sprint audit table and stop — do not execute | off |
| `--skip-ready` | Skip items already in Ready lane (spec+plan approved) | off |
| `--version=X.Y.Z` | Override version bump for Phase 3 release | auto |

Flag handling is inline at each consuming step below.

## Step 0: AUDIT — Build Sprint Plan

1. **Read ROADMAP lanes**:
   - **Next**: items awaiting spec
   - **Ready**: items with approved plan, awaiting impl
   - **Now**: active work (should be empty at sprint start)
   - **Done**: shipped

2. **Classify items**:

   For each slug in Next + Ready lanes:
   - Check `zie-framework/backlog/<slug>.md` exists → `[backlog: ✓]`
   - Glob `zie-framework/specs/*-<slug>-design.md` + read frontmatter → `[spec: ✓/pending]`
   - Glob `zie-framework/plans/*-<slug>.md` + read frontmatter → `[plan: ✓/pending]`
   - Check if item in Now → `[impl: ✓/—]`

3. **Compute phase assignment**:

   ```
   needs_spec = Next items without approved spec
   needs_plan = (Next+Ready items with approved spec) \ Ready items with approved plan
   ready_impl = Ready items with approved plan
   ```

4. **Check for dependencies**:

   - Scan all backlog files for `<!-- depends_on: slug-N -->` comments
   - Build dependency graph
   - Items with dependencies → mark for serialization in PLAN/IMPL phases

5. **Print sprint audit table**:

   ```
   SPRINT AUDIT

   Needs Spec:  <count> items
   Needs Plan:  <count> items
   Ready to Impl: <count> items
   Dependencies: <count> edges (if any)

   [item1] backlog ✓ | spec — | plan — | impl —
   [item2] backlog ✓ | spec ✓ | plan — | impl —
   [item3] backlog ✓ | spec ✓ | plan ✓ | impl —
   ...
   ```

6. **--dry-run branch**: if `--dry-run` present → print audit table and stop. Say "Run without --dry-run to execute."

7. **User confirmation**:

   ```
   Sprint ready. Process:
   - Phase 1: Spec <N> items (parallel, with inline retry on partial failure)
   - Phase 2: Impl <N> items (sequential, WIP=1)
   - Phase 3: Release v<suggested-version>
   - Phase 4: Retro

   Start sprint? (yes / edit / cancel)
   ```

   - `yes` → continue to Phase 1
   - `edit` → ask which items to include/skip (filter slugs)
   - `cancel` → stop

## Load Context Bundle (Once Per Sprint)

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
(reads `decisions/*.md` ADRs + `project/context.md`).

## PHASE 1: SPEC ALL (Parallel)

TaskCreate subject="Phase 1/4 — Spec All"

```
For each item in needs_spec (all launched concurrently — no cap):
  - Spawn Agent(subagent_type="general-purpose", run_in_background=True):
    prompt: "Run spec + plan workflow for slug: <slug>.
    (1) Skill(spec-design, '<slug> quick') — write the spec
    (2) Skill(spec-reviewer, '<slug>') — review and approve spec
    (3) Skill(write-plan, '<slug>') — write the implementation plan
    (4) Skill(plan-reviewer, '<slug>') — review and approve plan
    Confirm both spec and plan are approved before returning.
    Report: [spec-<slug>] ✓ or ❌ <issue>"
    context_bundle: <from Step 0>
```

Print: `"Phase 1: Speccing <N> items in parallel (all concurrent)..."`

**Progress reporting (delta-only):** As each agent completes, print a single
line: `[spec N/total] <slug> ✓` or `[spec N/total] <slug> ❌ <issue>`.
Do NOT print a full tracker table on each completion — only print the full
status table once, after all agents have finished (or after retry exhausted).

Wait for all Phase 1 agents → collect results.
- Each spec result: approved → mark in audit
- Any partial failure (spec+plan chain incomplete) → inline retry: re-spawn a single
  sequential agent for each failed slug (no separate phase — retry happens before
  progress bar prints). If retry also fails → print error, halt sprint.

After Phase 1 (+ any retries): reload ROADMAP → bind as `roadmap_post_phase1`.
TaskUpdate → Phase 1/4 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 1/4 — 3 phases remaining`

## PHASE 2: IMPLEMENT (Sequential, WIP=1)

TaskCreate subject="Phase 2/4 — Implement"

Read Ready items from `roadmap_post_phase1` (ordered by priority: CRITICAL → HIGH → MEDIUM → LOW). Re-read ROADMAP only if a mutation occurred after Phase 1.

For each item in priority order:

1. Move item from Ready → Now in ROADMAP
2. Read `zie-framework/plans/*-<slug>.md` (only this file per item)
3. Invoke: `Skill(zie-framework:zie-implement, <slug>, context_bundle=<context_bundle>)`
4. Success: `[impl N/total] <slug> ✓ <commit>`
5. Failure: `[impl N/total] <slug> ❌ <issue>` → halt sprint

After all impl complete: all items marked `[x]` in Now.
TaskUpdate → Phase 2/4 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 2/4 — 2 phases remaining`

## PHASE 3: BATCH RELEASE

TaskCreate subject="Phase 3/4 — Release"

Invoke `/release`:

```bash
zie-release
```

With version override if provided:

```bash
zie-release --bump-to=<version_override>
```

Print: `"Phase 4: Batch release..."`
TaskUpdate → Phase 3/4 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 3/4 — 1 phase remaining`

## PHASE 4: SPRINT RETRO

TaskCreate subject="Phase 4/4 — Retro"

```bash
zie-retro
```

Print: `"Phase 5: Sprint retro..."`
TaskUpdate → Phase 4/4 complete
Print progress bar: `████████████████████ 4/4 (100%)`
Print ETA: `Sprint complete`

## Summary

Print final sprint summary:

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

- **Phase 1 fails** (retry exhausted): halt sprint, surface issue. User can fix and restart from that item.
- **Phase 2 fails**: halt sprint, invoke `/fix`, re-implement.
- **Phase 3 fails**: halt before merge, print error. User can debug and retry release manually.
- **Phase 4 fails**: non-blocking, print warning. Retro can be run manually later.

