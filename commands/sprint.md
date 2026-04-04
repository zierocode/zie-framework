---
description: Sprint clear — process all backlog items through full pipeline (spec→plan→implement→release→retro) with phase-parallel optimization, batch release, and single retro.
argument-hint: "[slug1 slug2...] [--dry-run] [--skip-ready] [--version=X.Y.Z]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, Skill
model: sonnet
effort: high
---

# /sprint — Sprint Clear (Backlog → Ship → Retro)

Run a complete sprint cycle: spec all items in parallel, plan all items in parallel, implement sequentially (WIP=1), batch release once, and run single sprint retro. Optimized for throughput and context efficiency.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Read `zie-framework/.config` → zie_memory_enabled, project_type.
3. Read `zie-framework/ROADMAP.md` → check all lanes.
4. Check current branch is `dev`.
5. Verify no uncommitted changes (warn if found).

## Parse Arguments

```python
dry_run = "--dry-run" in ARGUMENTS
skip_ready = "--skip-ready" in ARGUMENTS
version_override = None

# Extract --version=X.Y.Z
for arg in ARGUMENTS.split():
    if arg.startswith("--version="):
        version_override = arg.split("=")[1]

# Extract slugs (remaining args)
slugs = [arg for arg in ARGUMENTS.split() if not arg.startswith("--")]
```

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

6. **--dry-run branch**: if `dry_run=true` → print audit table and stop. Say "Run without --dry-run to execute."

7. **User confirmation**:

   ```
   Sprint ready. Process:
   - Phase 1: Spec <N> items (parallel)
   - Phase 2: Plan <N> items (parallel)
   - Phase 3: Impl <N> items (sequential, WIP=1)
   - Phase 4: Release v<suggested-version>
   - Phase 5: Retro

   Start sprint? (yes / edit / cancel)
   ```

   - `yes` → continue to Phase 1
   - `edit` → ask which items to include/skip (filter slugs)
   - `cancel` → stop

## Load Context Bundle (Once Per Sprint)

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
(reads `decisions/*.md` ADRs + `project/context.md`).
This bundle is passed to every downstream agent/skill call.

## PHASE 1: SPEC ALL (Parallel)

TaskCreate subject="Phase 1/5 — Spec All"

Skip items that already have approved specs.

**Items to spec**: `needs_spec` (from Step 0).

```
For each item in needs_spec (parallel, max 4 agents):
  - TaskCreate subject="Spec <slug>"
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

Print: `"Phase 1: Speccing <N> items in parallel..."`

Wait for all Phase 1 agents → collect results.
- Each spec result: approved → mark in audit
- Any failed → print error, halt sprint

After Phase 1: reload ROADMAP (items moved from Next → Ready by skill chain).
TaskUpdate → Phase 1/5 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 1/5 — 4 phases remaining`

## PHASE 2: PLAN ALL (Parallel)

TaskCreate subject="Phase 2/5 — Plan All"

Items still needing plans (those not covered by Phase 1's skill chain).

**Items to plan**: filter Ready items that have spec but no approved plan.

Invoke `/plan slug1 slug2 ... ` with multiple slugs:

```bash
zie-plan slug1 slug2 slug3
```

(Existing /plan already supports parallel.)

Print: `"Phase 2: Planning <N> items in parallel..."`

Wait for all plans to be approved (plan-reviewer gates).

Reload ROADMAP (items now in Ready).
TaskUpdate → Phase 2/5 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 2/5 — 3 phases remaining`

## PHASE 3: IMPLEMENT (Sequential, WIP=1)

TaskCreate subject="Phase 3/5 — Implement"

Read Ready items from ROADMAP (ordered by priority: CRITICAL → HIGH → MEDIUM → LOW).

For each item in priority order:

1. Move item from Ready → Now in ROADMAP
2. Read `zie-framework/plans/*-<slug>.md` (only this file per item)
3. Invoke: `Skill(zie-framework:zie-implement, <slug>)`
4. Success: `[impl N/total] <slug> ✓ <commit>`
5. Failure: `[impl N/total] <slug> ❌ <issue>` → halt sprint

After all impl complete: all items marked `[x]` in Now.
TaskUpdate → Phase 3/5 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 3/5 — 2 phases remaining`

## PHASE 4: BATCH RELEASE

TaskCreate subject="Phase 4/5 — Release"

Invoke `/release` (which already handles moving all `[x]` items from Now → Done):

```bash
zie-release
```

With version override if provided:

```bash
zie-release --bump-to=<version_override>
```

Print: `"Phase 4: Batch release..."`

On success: single git merge dev→main, tag, version bump.
TaskUpdate → Phase 4/5 complete
Print progress bar: `{"█" * done_blocks}{"░" * empty_blocks} {done}/{total} ({pct}%)`
Print ETA: `Phase 4/5 — 1 phase remaining`

## PHASE 5: SPRINT RETRO

TaskCreate subject="Phase 5/5 — Retro"

After release completes, invoke `/retro`:

```bash
zie-retro
```

This runs single retro covering all shipped items in batch.

Print: `"Phase 5: Sprint retro..."`

On complete: print sprint summary.
TaskUpdate → Phase 5/5 complete
Print progress bar: `████████████████████ 5/5 (100%)`
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
  1. Spec    — <N> items, <elapsed>
  2. Plan    — <N> items, <elapsed>
  3. Impl    — <N> items, <elapsed> | WIP=1
  4. Release — v<version>, <elapsed>
  5. Retro   — <N> ADRs, <elapsed>

Next: /backlog to queue new items.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

- **Phase 1 fails**: halt sprint, surface issue. User can fix and restart from that item.
- **Phase 2 fails**: halt sprint, re-run plan-reviewer, re-draft if needed.
- **Phase 3 fails**: halt sprint, invoke `/fix`, re-implement.
- **Phase 4 fails**: halt before merge, print error. User can debug and retry release manually.
- **Phase 5 fails**: non-blocking, print warning. Retro can be run manually later.

## ขั้นตอนถัดไป

→ Next sprint: `/backlog` to capture new ideas.

## Notes

- Sprint operates on **all Next + Ready items** by default (no args needed).
- Specify subset with: `/sprint slug1 slug2 slug3`
- `--dry-run` shows plan without executing.
- `--skip-ready` skips items already in Ready lane (goes straight to impl phase).
- `--version=X.Y.Z` overrides auto-suggested version bump.
- Context bundle loaded once, reused everywhere — O(1) context loads.
- Dependencies respected: items with `<!-- depends_on: slug-N -->` serialize automatically.
