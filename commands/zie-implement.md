---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
model: sonnet
effort: medium
---

# /zie-implement — TDD Feature Implementation Loop

## ตรวจสอบก่อนเริ่ม

**Live context:**
!`git log -5 --oneline`
!`git status --short`
!`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now 2>/dev/null || echo "knowledge-hash: unavailable"`

0. **Pre-flight: Agent mode check** — if not running with `--agent zie-framework:zie-implement-mode`:
   print `⚠️ Running /zie-implement outside agent session. For best results use: claude --agent zie-framework:zie-implement-mode` and continue immediately.

1. Check `zie-framework/` exists → if not, run `/zie-init` first.
2. **Pre-flight: ROADMAP guard** — check `zie-framework/ROADMAP.md` exists:
   - Missing → STOP: "ROADMAP.md not found — run /zie-init to initialize this project."
   - Read Now lane:
     - `[ ]` in Now → STOP: "WIP task in progress — complete it or run /zie-fix before starting a new one."
     - `[x]` in Now → batch pending release, continue
     - Now empty → continue
3. **Pre-flight: Ready lane guard** — read Ready lane:
   - Empty → auto-run `/zie-plan` → get approval → continue. If still empty → STOP: "Ready lane is empty."
   - Read plan header only: everything up to (not including) the first `### Task` heading — check frontmatter for `approved: true`.
   - Not approved → STOP: "Plan in Ready lane is not approved — run /zie-plan to get approval."
4. Pull first Ready item → move to Now.
5. Check uncommitted work: warn if implementation files untracked.
6. Read `zie-framework/.config` for context.
7. If `zie_memory_enabled=true` and resuming: `mcp__plugin_zie-memory_zie-memory__recall` `tags=[wip]` to restore context.
8. `TaskCreate` for each plan task.

## Task Parallelism

Tasks without `depends_on` run in parallel (max 4 concurrent). Tasks with `<!-- depends_on: TN -->` run after listed tasks. File-write conflict → add implicit `depends_on`.

## Context Bundle

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
2. **→ TDD loop** — Invoke `Skill(zie-framework:tdd-loop)`. Follow it exactly.
   If tests already pass before writing any test → feature exists, skip task.
   Skill exits after REFACTOR; continue to step 3.
3. **Risk Classification** — set `risk_level = HIGH` or `LOW`:
   - HIGH: new function/class, changed behavior, external API call, file I/O, subprocess, non-test production code changed, or `<!-- review: required -->`
   - LOW: test-only, docs/config, rename/reformat, minor constant addition
4. **Spawn async impl-reviewer** (HIGH only): `@agent-impl-reviewer` (background) with task description, AC, changed files, `context_bundle`. Record in pending list. Do NOT block.
   - At each loop start: poll `reviewer_status` → `approved` clear; `issues_found` halt, fix, re-run `make test-unit`, re-invoke. Max 2 total iterations; confirm pass required. If 0 issues → APPROVED immediately.
5. **→ LOW risk:** `make test-unit` + `[risk: LOW] Skipping impl-reviewer`.
6. `TaskUpdate` → completed. Mark `[x]` in plan. Print `✓ done — {remaining} remaining`.
   - Checkpoint every 3 tasks. Brain write every 5: `mcp__plugin_zie-memory_zie-memory__remember` `tags=[wip] supersedes=[wip, <project>, <slug>]`. Friction: `tags=[build-learning]`.

## When All Tasks Complete

0. Wait for any still-pending reviewers (max 120s). Apply `issues_found` loop if needed.
1. Run `make test-unit` → capture output as `last_test_output`. Fail → `Skill(zie-framework:debug)`. Also run `make test-int` (if available).
2. `TaskCreate` verify task → `Skill(zie-framework:verify)` with `$ARGUMENTS={"test_output": "<last_test_output>", "scope": "tests-only"}` — passes captured output so verify skips re-running tests. → `TaskUpdate` completed.
3. Update ROADMAP.md Now lane: `[ ]` → `[x]`.
4. `git add -A` → collect verify result:
   - ✅ APPROVED → commit
   - ❌ Issues Found → `git reset HEAD`, fix, re-verify, re-stage
5. `git commit -m "feat: <slug>" && git push origin dev`
6. Print summary: `All tasks complete: <name> | Tests: ✓ | Next: /zie-release`

## เมื่อ test ล้มเหลว

Fail unexpectedly → `Skill(zie-framework:debug)`. Stuck after 2 → surface error, ask Zie.
Never silently skip tests.

## ขั้นตอนถัดไป

→ `/zie-release`
