---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
model: sonnet
effort: medium
---

# /zie-implement — TDD Feature Implementation Loop

Implement the active feature using Test-Driven Development. Reads the active
plan from ROADMAP.md and guides through RED → GREEN → REFACTOR per task.

## ตรวจสอบก่อนเริ่ม

**Live context (injected at command load):**

Recent commits:
!`git log -5 --oneline`

Working tree:
!`git status --short`

Knowledge hash:
!`python3 ${CLAUDE_SKILL_DIR}/../../hooks/knowledge-hash.py --now 2>/dev/null || echo "knowledge-hash: unavailable"`

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.

2. **ตรวจสอบ: งานที่ค้างอยู่** — อ่าน `zie-framework/ROADMAP.md` → ตรวจ Now
   lane.
   - `[ ]` item in Now → feature ยังค้างอยู่ → STOP: "Now: `<current>`
     ยังไม่เสร็จ ทำต่อหรือ /zie-fix ก่อน"
   - `[x]` item(s) in Now → feature(s) เสร็จแล้ว รอ batch release → ปล่อยไว้ใน
     Now (/zie-release จะย้ายไป Done พร้อม version) → ดำเนินต่อ
   - Now empty → ดำเนินต่อ

3. **ตรวจสอบ: แผนที่อนุมัติแล้ว** — หา item ใน Ready lane.
   - If Ready is empty → auto-fallback: print "[zie-implement] No approved plan.
     Running /zie-plan first..."
     → run `/zie-plan` (show Next list, Zie selects) → get approval → continue.
   - If Next is also empty during fallback → print "No backlog items.
     Run /zie-backlog to start a new feature, or
     /zie-spec to write a quick spec inline." and STOP.
   - Read plan header only: everything up to (not including) the first `### Task` heading
     — check frontmatter for `approved: true`.
   - If `approved: true` absent → treat as unapproved → trigger auto-fallback
     above.

4. Pull first Ready item → move to Now in ROADMAP.md.

5. **ตรวจสอบ uncommitted work** — ตรวจก่อนเริ่ม task loop ทุกครั้ง:

   ```bash
   git status --short
   ```

   - ถ้ามี modified/untracked files ที่เกี่ยวกับ feature นี้ →
     print: "Uncommitted work found from prior session: [list] —
     will be included in the feat: commit at the end of this feature."
   - ไม่ต้องทำอะไรตอนนี้ — `git add -A` ตอน feature จบจะ capture ทุกอย่าง
   - ถ้าเจอ backlog/spec/plan ที่ยังไม่ได้ commit → warn:
     "SDLC files uncommitted — commit them before starting implementation."

6. อ่าน `zie-framework/.config` เพื่อ context

7. If `zie_memory_enabled=true`:
   - If **resuming** (feature was already in Now lane):
     Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip] feature=<slug> limit=1`
     to restore in-progress context.
   - If **starting fresh** (just pulled from Ready): skip WIP recall — no WIP
     memory exists yet.
   - Read plan's "## Context from brain" section for domain context.
   - Do NOT re-recall domain patterns — /zie-plan already baked them in.

8. **Create task tracker**: `TaskCreate` for each plan task with name +
   description. Use returned task IDs for `TaskUpdate` progress tracking.

### วิเคราะห์ dependency ระหว่าง tasks

Before starting tasks:

**Default: parallel.** Tasks with no `depends_on` annotation run in parallel.
Tasks annotated with `<!-- depends_on: T1, T2 -->` run sequentially after all
listed dependencies complete.

**Max parallel tasks: 4.** If more than 4 tasks are ready simultaneously,
queue excess tasks and start them as slots become available.

**File conflict check:** Before launching parallel tasks, verify that no two
tasks write to the same output file. If conflict detected:
1. Add implicit `<!-- depends_on: TN -->` to serialize conflicting tasks
2. Print warning: "Task N and Task M both write to X.py — serializing"

- Parse all tasks in plan for `<!-- depends_on: TN -->` comments
- Tasks without `depends_on` → **parallel** (default path) — spawn up to 4 concurrent agents
- Tasks with `depends_on` → **sequential** — start only after each listed task ID is complete
- If all tasks have `depends_on` chains → execute in full dependency order (no parallelism)

## โหลด context bundle (ครั้งเดียวต่อ session)

<!-- context-load: adrs + project context -->

Before entering the task loop, load shared context once:

1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
   (list of `{filename, content}` pairs; empty list if directory missing)
2. Read `zie-framework/project/context.md` → store as `context_content`
   (string; empty string if file missing)
3. Bundle as `context_bundle = { adrs: adrs_content, context: context_content }`

Pass `context_bundle` to every impl-reviewer invocation in the task loop.

### TDD Guidance (printed once at session start)

Print this block before starting the task loop — do not repeat per task:

```text
TDD Cycle — RED → GREEN → REFACTOR
- RED:     Write a failing test that captures the desired behavior. Run make test-unit to confirm it fails.
- GREEN:   Write the minimum code to make the test pass. No speculation, no extras. Run make test-unit.
- REFACTOR: Clean up — remove duplication, clarify names, simplify logic. Run make test-unit to confirm still passing.

Test level selection:
- unit        — isolated logic, pure functions, single-module behavior
- integration — cross-module, file I/O, database, external config
- e2e         — full UI flows, browser interactions, end-to-end user journeys

If tdd: deep is set in the plan frontmatter, invoke Skill(zie-framework:tdd-loop) for each task instead of using this summary.
```

## Steps

### วนรอบ task จนครบ

0. **Read task section**: Read this task's full section from the plan file (from its `### Task N` heading to the next `### Task` heading or EOF). This is the only time this task's detail enters context.

1. **Announce task**: Print `[T{N}/{total}] {task description}` — where N is
   the 1-based task index and total is the count of tasks in the plan.

2. **เขียน test ที่ล้มเหลวก่อน (RED)**
   Print: `→ RED`
   เลือก test level จาก inline guidance ด้านบน (unit / integration / e2e)
   แล้วเขียน test ที่ capture behavior ที่ต้องการ
   — test ต้อง fail ก่อนเสมอ รัน `make test-unit` เพื่อยืนยัน
   ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว ข้ามไป task ถัดไป
   If the plan frontmatter has `tdd: deep` → invoke `Skill(zie-framework:tdd-loop)` for this task instead.

3. **เขียน code ให้ผ่าน test (GREEN)**
   Print: `→ GREEN`
   เขียน code น้อยที่สุดที่ทำให้ test ผ่าน — ไม่ over-engineer ไม่เดาล่วงหน้า
   รัน `make test-unit` เพื่อยืนยัน

4. **ปรับปรุง code โดยไม่ทำให้ test พัง (REFACTOR)**
   Print: `→ REFACTOR`
   ลด duplication ปรับชื่อให้ชัด ทำให้ง่ายขึ้น — รัน `make test-unit`
   เพื่อยืนยัน

5. **Risk Classification** — Classify this task immediately after REFACTOR
   completes, before deciding whether to invoke the reviewer.

   **Signals → HIGH** (invoke reviewer):
   - Task description contains: new function/class, changed behavior,
     external API call, auth, file I/O, subprocess
   - Files changed include non-test production code (i.e., not solely
     `tests/` or `test_*.py` files)
   - Task description or plan task header contains `<!-- review: required -->`
     (forces HIGH regardless of other signals)

   **Signals → LOW** (skip reviewer):
   - Task is add/edit test only (all changed files are under `tests/` or
     match `test_*.py`)
   - Task is docs/config change only (changed files are `.md`, `.json`,
     `.toml`, `.yaml`, `.cfg`, `.ini`, or similar non-code files)
   - Task is rename/reformat only (no behavioral change — variable rename,
     formatting fix, import reorder)
   - Task is minor addition (new field in existing dict/list, extend existing
     list constant, update string constant — no new function/class)

   Set `risk_level = HIGH` or `risk_level = LOW` based on the above. When
   signals are mixed (e.g., test added alongside a new function), default to
   HIGH.

   **If `risk_level == LOW`:**
   - Run `make test-unit` to confirm tests still pass.
   - Print: `[risk: LOW] Skipping impl-reviewer — make test-unit passed.`
   - Proceed to Step 7 (task complete bookkeeping).

6. **Spawn async impl-reviewer** (HIGH risk only):
   - Skip this step entirely if `risk_level == LOW`.
   - Invoke `@agent-impl-reviewer` (background: true):
     pass task description, **Acceptance Criteria** from plan task header,
     list of files changed in this task, and `context_bundle`.
   - Record returned handle in the pending-reviewers list:
     `{ task_id: <N>, reviewer_handle: <handle>, reviewer_status: pending }`
   - Do NOT block — proceed immediately to announce the next task.
   - **Deferred-check** (start of each task loop iteration): for each entry
     in the pending-reviewers list, poll handle → check `reviewer_status`:
     - `reviewer_status: pending` — still running; continue current task,
       check again at the next iteration.
     - `reviewer_status: approved` — clear entry from list; no action needed.
     - `reviewer_status: issues_found` — HIGH risk path: halt current task;
       surface reviewer feedback to human; apply ALL fixes listed; re-run
       `make test-unit`; re-invoke `@agent-impl-reviewer` synchronously as a
       confirm pass (blocking).
       Max 2 total iterations: background spawn = pass 1 (initial scan),
       synchronous re-invoke = pass 2 (confirm pass).
       If confirm pass returns ❌ Issues Found → surface to Zie: "Reviewer
       found persistent issues after fix pass. Review manually."
       If 0 issues on initial (background) pass → APPROVED immediately,
       no confirm pass needed.
       On APPROVED at any pass: clear entry from list; resume current task.

7. **บันทึก task เสร็จ**: Update `TaskUpdate` → completed. Update plan file:
   mark task as `[x]`. Update ROADMAP.md task counter if tracking.
   Print: `✓ done — {remaining} remaining`
   Checkpoint (every 3 tasks or at halfway): Print:
   `Checkpoint [{N}/{total}]: completed: {done_list} | remaining: {remaining_list}`
   If task had unexpected friction: Call
   `mcp__plugin_zie-memory_zie-memory__remember` with
   `"Task harder than estimated: <why>. Next time: <tip>." tags=[build-learning, <project>, <domain>]`
   — conditional write only, not every task.

8. **Brain checkpoint** (every 5 tasks or on natural stopping point): If
   `zie_memory_enabled=true`:
   Call `mcp__plugin_zie-memory_zie-memory__remember` with
   `"WIP: <feature> — T<N>/<total> done." tags=[wip, <project>, <feature-slug>] supersedes=[wip, <project>, <feature-slug>]`
   supersedes replaces previous WIP memory — no duplicate WIPs accumulate.

### เมื่อทำครบทุก task

0. **Final-wait for still-pending reviewers**:
   - If the pending-reviewers list is non-empty, wait for any still-pending
     background reviewer to return before proceeding.
   - If any reviewer has not returned after 120s:
     surface: "impl-reviewer did not return — review manually before committing."
     and stop. Do not commit until all reviewers have returned or Zie explicitly
     acknowledges the outstanding review.
   - Apply the same `issues_found` fix-iterate loop as step 6 above.
   - Note: LOW-risk tasks never add to the pending-reviewers list, so this
     wait step is a no-op for plans composed entirely of LOW-risk tasks.

1. Run full test suite: `make test-unit` (required) + `make test-int` (if
   available). Capture output to `test_output`. If any suite fails → STOP,
   invoke `Skill(zie-framework:debug)` before retrying.

2. **TaskCreate + verify** — create task and run verify:

   **TaskCreate:**
   ```python
   TaskCreate(subject="Pre-ship verification", description="Run verify skill before commit", activeForm="Verifying changes")
   ```

   **Invoke Skill (expected <30s, inline):**
   `Skill(zie-framework:verify)` with captured output:

   ```json
   {
     "test_output": "<captured make test-unit output>",
     "changed_files": "<git status --short output>",
     "scope": "tests-only"
   }
   ```

   **TaskUpdate:**
   ```python
   TaskUpdate(taskId="<task_id_from_create>", status="completed")
   ```

3. **Commit prep (runs while verify fork is running)**:
   - Update `zie-framework/ROADMAP.md` Now lane: change feature from `[ ]`
     to `[x]` (complete, pending release — see D-005 batch release pattern).
   - Review what will be committed:

     ```bash
     git status --short
     ```

     Expected: implementation files (code, tests, hooks, commands) +
     `zie-framework/ROADMAP.md`. If backlog/spec/plan files appear here they
     were not committed at their stage — include them.

   - Run `git add -A`

4. **Collect verify fork result**:
   - ✅ APPROVED → proceed to commit
   - ❌ Issues Found → `git reset HEAD` (unstage), fix issues, re-run
     `make test-unit`, re-invoke `Skill(zie-framework:verify)` synchronously,
     then re-stage and proceed
   - Fork error/timeout → print warning and proceed with manual note:
     "Verify fork failed — proceeding. Review manually."

5. Commit all feature code to dev:

   ```bash
   git commit -m "feat: <feature-slug>"
   git push origin dev
   ```

   **ห้าม** commit ระหว่าง task loop — commit ครั้งเดียวตอนนี้เท่านั้น.

4. Print:

   ```text
   All tasks complete for: <feature name>

   Tests: unit ✓ | integration ✓|n/a
   Verify: ✓

   Next: Run /zie-release to release, or /zie-backlog for the next feature.
   ```

## เมื่อ test ล้มเหลว

- If a test fails unexpectedly → invoke `Skill(zie-framework:debug)` before
  trying fixes.
- If stuck after 2 attempts → surface the error, explain options, ask Zie which
  path to take.
- Never silently skip tests or comment them out.

## ขั้นตอนถัดไป

→ `/zie-release` — เมื่อทุก task เสร็จและ test ผ่านหมด
→ `/zie-backlog` — เริ่ม feature ถัดไป

## Notes

- Works for any language — test runner detected from `.config`
- If no active plan in ROADMAP.md → suggest `/zie-backlog` (full flow) or
  `/zie-spec` (quick spec, no backlog file needed)
- Can be run mid-task to resume after a break
- The PostToolUse:auto-test hook fires on every file save — this command sets
  the strategic direction, hooks handle the feedback loop

### Resume Subagent

When a reviewer subagent completes, its agent ID is captured in the session
subagent log (see `/zie-retro` Subagent Activity section). To continue a
reviewer in the same context for a follow-up question, reference the agent
by ID using `@agent:<id>` in a new message to that subagent via `SendMessage`.

**Important:** Agent IDs are session-scoped. They are valid only within the
current Claude Code session. If the session has ended (e.g., you closed the
terminal or restarted Claude Code), the agent ID is no longer valid — start
a fresh subagent instead. The subagent log in `/zie-retro` shows IDs from
the current session only; previous sessions are cleaned up by
`session-cleanup.py`.

**When to resume vs. start fresh:**

- Resume: same session, same context, follow-up question on the same artifact.
- Start fresh: new session, new artifact, or the original agent's context
  is no longer relevant.
