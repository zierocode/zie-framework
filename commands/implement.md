---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
model: sonnet
effort: medium
---

# /implement — TDD Feature Implementation Loop

## ตรวจสอบก่อนเริ่ม

**Live context:**
!`git log -5 --oneline`
!`git status --short`

0. **Pre-flight: Agent mode advisory** — if not running with `--agent zie-framework:zie-implement-mode`:
   print `ℹ️ Tip: run inside \`claude --agent zie-framework:zie-implement-mode\` for best results. On non-Claude models, /implement works directly in the current session.`
   (advisory only — do not block, continue immediately)

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight).
(ROADMAP.md not found → STOP and run /init to initialize this project.)

1. **Pre-flight: Ready lane guard** — read Ready lane:
   - Empty → auto-run `/plan` → get approval → continue. If still empty → STOP: "No approved plan in Ready lane. Run /plan first."
   - Read plan header only: everything up to (not including) the first `### Task` heading — check frontmatter for `approved: true`.
   - Not approved → STOP: "Plan in Ready lane is not approved — run /plan to get approval."

2. **Pre-flight: WIP=1 guard** — read Now lane:
   - Not empty → STOP: "WIP=1 active: '<task>'. Finish or release before starting new work."
   - (Pass-through if Now lane is empty — proceed.)

3. Pull first Ready item → move to Now.
4. Check uncommitted work: warn if implementation files untracked.
5. Read `zie-framework/.config` for context.
6. If `zie_memory_enabled=true` and resuming: `mcp__plugin_zie-memory_zie-memory__recall` `tags=[wip]` to restore context.
7. `TaskCreate` for each plan task.

## Task Parallelism

Tasks without `depends_on` run in parallel (max 4 concurrent). Tasks with `<!-- depends_on: TN -->` run after listed tasks. File-write conflict → add implicit `depends_on`.

## Context Bundle

<!-- context: ROADMAP already injected by session-resume/subagent-context hook; re-read only if Now lane may have changed -->
<!-- context-load: adrs + project context -->

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
(calls `write_adr_cache`, bundles `adr_cache_path` + `decisions/` + `project/context.md`).
Pass `context_bundle` to every impl-reviewer call.

**TDD:** Every task uses RED → GREEN → REFACTOR via `Skill(zie-framework:tdd-loop)`.

Test level selection (print once before task loop, not per task):
- unit — isolated logic, pure functions, single-module behavior
- integration — cross-module, file I/O, external config
- e2e — full UI flows, end-to-end user journeys

## Steps

### Task Loop

0. Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF).
1. Print `[T{N}/{total}] {description}`
2. **→ TDD loop** — Print `→ RED` before writing tests; print `→ GREEN` before
   implementing; print `→ REFACTOR` before cleanup. Then invoke
   `Skill(zie-framework:tdd-loop)`. Follow it exactly.
   If tests already pass before writing any test → feature exists, skip task.
   After each TDD phase print, write current phase to `zie-framework/.sprint-state`:
   update `tdd_phase` field to "RED"/"GREEN"/"REFACTOR" (skip silently if file absent).
   Skill exits after REFACTOR; continue to step 2a.
2a. **Simplify pass (conditional):**
   1. Run `git diff --stat HEAD` → parse summary line (e.g. `3 files changed, 87 insertions(+), 12 deletions(-)`) → sum insertions + deletions = total Δ
   2. Run `git diff --name-only HEAD` → collect recently modified files list
   3. If total Δ > 50 → invoke `Skill(simplify)` on recently modified files list
   4. If Δ ≤ 50 → print `[simplify] skipped (Δ{n} lines < 50 threshold)` and continue
   5. After simplify (if run) → re-run `make test-fast` to confirm no regressions introduced
3. **Risk Classification** — set `risk_level = HIGH` or `LOW`:
   - HIGH: new function/class, changed behavior, external API call, file I/O, subprocess, non-test production code changed, or `<!-- review: required -->`
   - LOW: test-only, docs/config, rename/reformat, minor constant addition
4. **impl-reviewer** (HIGH only): <!-- BLOCKING: do not mark task complete until all checks pass -->
   Invoke `Skill(zie-framework:impl-reviewer)` with `context_bundle`.
   - ✅ APPROVED → continue
   - ❌ Issues Found → auto-fix inline → `make test-unit` → if pass continue; if fail after 1 retry → surface to Zie
5. **→ LOW risk:** `make test-unit` + print `[risk: LOW] Skipping impl-reviewer`.
6. `TaskUpdate` → completed. Mark `[x]` in plan. Print `✓ T{N} done — {remaining} remaining`.
   - Checkpoint every 3 tasks. If `zie_memory_enabled=true`: Brain write every 5: `mcp__plugin_zie-memory_zie-memory__remember` `tags=[wip] supersedes=[wip, <project>, <slug>]`. Friction: `tags=[build-learning]`.
7. **Per-task checkpoint commit** — after marking task complete:
   `git add -A && git commit -m "feat(<slug>): T{N} {description}"`
   This ensures progress is saved even if context overflows before all tasks complete.
   If commit fails (e.g., nothing to commit), skip silently — the task may have been docs-only or already committed.

## When All Tasks Complete

1. Run `make test-unit 2>&1 | tail -30` → capture output as `last_test_output`. **Run once — never re-run just to grep differently.** Fail → `Skill(zie-framework:debug)`. Also run `make test-int` (if available).
2. `TaskCreate` verify task → `Skill(zie-framework:verify)` with `$ARGUMENTS={"test_output": "<last_test_output>", "scope": "tests-only"}` — passes captured output so verify skips re-running tests. → `TaskUpdate` completed.
3. Update ROADMAP.md Now lane: `[ ]` → `[x]`.
4. `git add -A` → collect verify result:
   - ✅ APPROVED → commit
   - ❌ Issues Found → `git reset HEAD`, fix, re-verify, re-stage
5. `git commit -m "feat: <slug>" && git push origin dev`
6. Print summary: `All tasks complete: <name> | Tests: ✓ | Next: /release`

## เมื่อ test ล้มเหลว

Fail unexpectedly → `Skill(zie-framework:debug)`. Stuck after 2 → surface error, ask Zie.
Never silently skip tests.

## ขั้นตอนถัดไป

→ `/release`

