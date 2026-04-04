---
slug: sprint-agent-audit
status: draft
date: 2026-04-04
---
# Spec: Replace Phase 3 Agent with Inline Skill in /zie-sprint

## Problem

`/zie-sprint` Phase 3 currently spawns a `Agent(subagent_type="general-purpose",
run_in_background=True)` for each implementation item. Each Agent invocation
opens a new context window, re-loads shared context, and introduces inter-process
communication overhead — all for a single sequential `Invoke /zie-implement <slug>`
call. Because Phase 3 is `WIP=1` (strictly sequential), the `run_in_background=True`
flag is misleading: the next item cannot start until the current Agent finishes, so
there is no parallelism benefit. The Agent wrapper adds cost without adding value.

Phase 1 (spec) spawns Agents for genuine parallelism (`max 4 agents` running
concurrently). This is correct and remains unchanged.

## Proposed Solution

**Approach C**: Keep Phase 1 agents (genuine parallelism). Replace Phase 3's
per-item `Agent(...)` with an inline `Skill(zie-framework:zie-implement, slug)`
call in the sprint context.

### Phase 1 — No change

Phase 1 spawns up to 4 background Agents in parallel to run spec+plan concurrently
across items. This is genuine parallelism and the Agent overhead is justified.
No change.

### Phase 3 — Replace Agent with inline Skill

Current Phase 3 (per item):

```
Spawn Agent(subagent_type="general-purpose", run_in_background=True):
  prompt: "Invoke /zie-implement <slug> ..."
  context_bundle: <from Step 0>
```

Replacement Phase 3 (per item):

```
1. Read zie-framework/plans/*-<slug>.md  ← ONLY this file; no re-reading completed items
2. Invoke: Skill(zie-framework:zie-implement, slug)
3. On success: print "[impl N/total] <slug> ✓ <commit-hash>"
4. On failure: print "[impl N/total] <slug> ❌ <issue>"; halt sprint
5. Move to next item
```

### Context discipline

Before each implementation item, sprint reads ONLY the plan file for that slug.
Completed items' files are NOT re-read. There is no pre-loading of the next
item's context during the current item's execution (see Out of Scope).

### Failure handling

When `Skill(zie-framework:zie-implement, slug)` fails, the failure surfaces
directly into the sprint context (no Agent boundary to cross). Sprint halts
immediately and reports:

```
[impl N/total] <slug> ❌ <issue>
```

No automatic retry. User must invoke `/zie-fix <slug>` and resume manually.

### What does NOT change

- Phase 1: parallel Agent spawns for spec (genuine parallelism — retained)
- Phase 2: parallel plan invocations
- Phase 4: batch release (`/zie-release`)
- Phase 5: sprint retro (`/zie-retro`)
- WIP=1 constraint: Phase 3 remains strictly sequential
- Priority ordering: CRITICAL → HIGH → MEDIUM → LOW
- ROADMAP mutations: Ready → Now → Done transitions unchanged
- Error handling prose for Phase 3 in the command

## Acceptance Criteria

- [ ] AC1: `commands/zie-sprint.md` Phase 3 section contains zero `Agent(...)`
  calls for per-item implementation (grep for `Agent(` in Phase 3 block must
  return zero matches)
- [ ] AC2: Phase 3 per-item invocation uses `Skill(zie-framework:zie-implement, <slug>)`
  (or equivalent inline Skill tool call notation)
- [ ] AC3: Before each impl item, the command instructs sprint to read ONLY the
  plan file for that slug — no read of completed items' files
- [ ] AC4: Phase 3 failure handling emits `[impl N/total] <slug> ❌ <issue>` and
  halts sprint immediately (no retry, no continuation to next item)
- [ ] AC5: Phase 1 Agent spawns remain unchanged (parallel spec Agents intact)
- [ ] AC6: The `run_in_background=True` annotation is removed from the Phase 3
  per-item loop (not applicable to inline Skill calls)
- [ ] AC7: The "pre-load next item context during wait" optimization step is
  explicitly removed from Phase 3 (it was a no-op given WIP=1 + Agent swap)

## Out of Scope

- Changing Phase 1 (parallel Agents for spec) — retained as-is
- Changing Phase 2 (parallel plan invocations)
- Changing Phase 4 (batch release) or Phase 5 (retro)
- Adding parallelism to Phase 3 — WIP=1 is a deliberate constraint
- Pre-loading next item context during current item execution — explicitly
  dropped; acceptable tradeoff for implementation simplicity
- Changes to `zie-implement` skill itself
- Changes to any hook, Makefile, or test file
- Unit tests — the command file is Markdown prose; ACs verified by reading
  the updated `commands/zie-sprint.md` and confirming absence of `Agent(`
  in Phase 3

## Test Plan

No unit tests applicable (command file is Markdown, not executable code).
Verification:

1. Read `commands/zie-sprint.md` after implementation.
2. Grep for `Agent(` in the Phase 3 section — must return zero matches.
3. Grep for `Skill(zie-framework:zie-implement` — must appear in Phase 3 loop.
4. Grep for `run_in_background` in Phase 3 — must return zero matches.
5. Confirm Phase 3 reads only `plans/*-<slug>.md` before each item (no
   completed-item re-reads).
6. Confirm Phase 1 Agent spawns are still present and unchanged.
