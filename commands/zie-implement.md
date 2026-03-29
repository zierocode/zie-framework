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

Load once before the task loop:
1. Read `zie-framework/decisions/*.md` → concatenate → `adrs_content`
2. `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
   `True` → save path as `adr_cache_path` | `False` → `adr_cache_path = None`
3. Read `zie-framework/project/context.md` → `context_content`

Pass `context_bundle` to every impl-reviewer call:
- `adr_cache_path` (preferred, if not None) or `adrs` = `adrs_content` (fallback)
- `context` = `context_content`

**TDD:** RED → GREEN → REFACTOR per task. `tdd: deep` in plan → invoke `Skill(zie-framework:tdd-loop)`.

Test level selection (print once before task loop, not per task):
- unit — isolated logic, pure functions, single-module behavior
- integration — cross-module, file I/O, external config
- e2e — full UI flows, end-to-end user journeys

## Steps

### Task Loop

0. Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF).
1. Print `[T{N}/{total}] {description}`
2. **→ RED (failing test)** — write failing test (RED). `make test-unit` must FAIL. (Test pass → feature exists, skip task.)
3. **→ GREEN (implementation)** — minimum code to pass (GREEN). `make test-unit` must PASS.
4. **→ REFACTOR (cleanup)** — clean up. `make test-unit` still PASS.
5. **Risk Classification** — set `risk_level = HIGH` or `LOW`:
   - HIGH: new function/class, changed behavior, external API call, file I/O, subprocess, non-test production code changed, or `<!-- review: required -->`
   - LOW: test-only, docs/config, rename/reformat, minor constant addition
6. **Spawn async impl-reviewer** (HIGH only): `@agent-impl-reviewer` (background: true) with task description, Acceptance Criteria, changed files, `context_bundle`. Record in pending-reviewers list. Do NOT block.
   - Deferred-check at each loop start: poll `reviewer_status` for pending reviewers.
     - `reviewer_status: approved` → clear, continue
     - `reviewer_status: issues_found` → halt, fix all, re-run `make test-unit`, re-invoke synchronously (confirm pass). Max 2 total iterations. If 0 issues → APPROVED immediately.
7. **→ LOW risk:** `make test-unit` + `[risk: LOW] Skipping impl-reviewer`.
8. `TaskUpdate` → completed. Mark `[x]` in plan. Print `✓ done — {remaining} remaining`.
   - Checkpoint every 3 tasks or halfway.
   - Brain write (every 5 tasks): `tags=[wip]` WIP memory with `supersedes=[wip, <project>, <slug>]`.
   - Unexpected friction: `mcp__plugin_zie-memory_zie-memory__remember` `tags=[build-learning]`.

## When All Tasks Complete

0. Wait for any still-pending reviewers (max 120s). Apply `issues_found` loop if needed.
1. `make test-unit` (required) + `make test-int` (if available). Fail → `Skill(zie-framework:debug)`.
2. `TaskCreate` verify task → `Skill(zie-framework:verify)` → `TaskUpdate` completed.
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
