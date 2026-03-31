---
description: Sprint clear — process all backlog items through full pipeline (spec→plan→implement→release→retro) with phase-parallel optimization, batch release, and single retro.
argument-hint: "[slug1 slug2...] [--dry-run] [--skip-ready] [--version=X.Y.Z]"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, TaskCreate, TaskUpdate, Skill
model: sonnet
effort: high
---

# /zie-sprint — Sprint Clear (Backlog → Ship → Retro)

Run a complete sprint cycle: spec all items in parallel, plan all items in parallel, implement sequentially (WIP=1), batch release once, and run single sprint retro. Optimized for throughput and context efficiency.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
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

Before Phase 1 starts, load shared context that will be passed to every downstream step:

1. Read all `zie-framework/decisions/*.md` → concatenate → `adrs_content`
2. Read `zie-framework/project/context.md` → `context_content`
3. Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")` (from utils)
   - Returns `(True, adr_cache_path)` → save path
   - Returns `(False, None)` → set `adr_cache_path = None`
4. Bundle as `context_bundle = { adr_cache_path: <path or None>, adrs: adrs_content, context: context_content }`

This bundle is passed to every downstream agent/skill call.

## PHASE 1: SPEC ALL (Parallel)

Skip items that already have approved specs.

**Items to spec**: `needs_spec` (from Step 0).

```
For each item in needs_spec (parallel, max 4 agents):
  - TaskCreate subject="Spec <slug>"
  - Spawn Agent(subagent_type="general-purpose", run_in_background=True):
    prompt: "Run spec + plan workflow. Slug: <slug>.
    (1) Invoke /zie-spec <slug> --draft-plan
    (2) Capture approved spec + plan from outputs
    (3) Confirm both are approved before returning.
    Report: [spec-<slug>] ✓ or ❌ <issue>"
    context_bundle: <from Step 0>
```

Print: `"Phase 1: Speccing <N> items in parallel..."`

Wait for all Phase 1 agents → collect results.
- Each spec result: approved → mark in audit
- Any failed → print error, halt sprint

After Phase 1: reload ROADMAP (items moved from Next → Ready by --draft-plan).

## PHASE 2: PLAN ALL (Parallel)

Items still needing plans (those not covered by Phase 1's --draft-plan).

**Items to plan**: filter Ready items that have spec but no approved plan.

Invoke `/zie-plan slug1 slug2 ... ` with multiple slugs:

```bash
zie-plan slug1 slug2 slug3
```

(Existing /zie-plan already supports parallel.)

Print: `"Phase 2: Planning <N> items in parallel..."`

Wait for all plans to be approved (plan-reviewer gates).

Reload ROADMAP (items now in Ready).

## PHASE 3: IMPLEMENT (Sequential, WIP=1)

Read Ready items from ROADMAP (ordered by priority: CRITICAL → HIGH → MEDIUM → LOW).

```
For each item in Ready:
  [impl N/total] <slug>

  1. Move item from Ready → Now in ROADMAP
  2. Spawn Agent(subagent_type="general-purpose", run_in_background=True):
     prompt: "Implement item. Slug: <slug>.
     (1) Invoke /zie-implement <slug>
     (2) All tasks complete and tests pass (skipping retro)
     (3) Capture final git commit hash
     Report: [impl-<slug>] ✓ <commit-hash> or ❌ <issue>"
     context_bundle: <from Step 0>
  3. (Non-blocking) Pre-load context for next item:
     - Read next item's plan file (cache it for step 4)
     - Warm up brain recall if enabled
  4. Wait for agent to complete before moving to next item (sequential)
```

Print progress: `[impl N/total] <slug> ✓ | ❌ <issue>`

After all impl complete: all items marked `[x]` in Now.

## PHASE 4: BATCH RELEASE

Invoke `/zie-release` (which already handles moving all `[x]` items from Now → Done):

```bash
zie-release
```

With version override if provided:

```bash
zie-release --bump-to=<version_override>
```

Print: `"Phase 4: Batch release..."`

On success: single git merge dev→main, tag, version bump.

## PHASE 5: SPRINT RETRO

After release completes, invoke `/zie-retro`:

```bash
zie-retro
```

This runs single retro covering all shipped items in batch.

Print: `"Phase 5: Sprint retro..."`

On complete: print sprint summary.

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

Next: /zie-backlog to queue new items.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Error Handling

- **Phase 1 fails**: halt sprint, surface issue. User can fix and restart from that item.
- **Phase 2 fails**: halt sprint, re-run plan-reviewer, re-draft if needed.
- **Phase 3 fails**: halt sprint, invoke `/zie-fix`, re-implement.
- **Phase 4 fails**: halt before merge, print error. User can debug and retry release manually.
- **Phase 5 fails**: non-blocking, print warning. Retro can be run manually later.

## ขั้นตอนถัดไป

→ Next sprint: `/zie-backlog` to capture new ideas.

## Notes

- Sprint operates on **all Next + Ready items** by default (no args needed).
- Specify subset with: `/zie-sprint slug1 slug2 slug3`
- `--dry-run` shows plan without executing.
- `--skip-ready` skips items already in Ready lane (goes straight to impl phase).
- `--version=X.Y.Z` overrides auto-suggested version bump.
- Context bundle loaded once, reused everywhere — O(1) context loads.
- Dependencies respected: items with `<!-- depends_on: slug-N -->` serialize automatically.
