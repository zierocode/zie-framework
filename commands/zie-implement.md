---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
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
   - Read plan file → check frontmatter for `approved: true`.
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

- Parse all tasks in plan for `<!-- depends_on: T1, T2 -->` comments
- Group tasks with no depends_on → **independent** (can run in parallel)
- Tasks with depends_on → **dependent** (run after blocking tasks complete)
- Spawn min(independent_count, 4) parallel agents for independent tasks
- If 0 independent tasks → execute all sequentially in dependency order

## Steps

### วนรอบ task จนครบ

1. **Announce task**: "Working on: [Task N] — {task description}"

2. Invoke `Skill(zie-framework:tdd-loop)` for RED/GREEN/REFACTOR guidance.
   Skip only for pure documentation tasks (no code changes).

3. **เขียน test ที่ล้มเหลวก่อน (RED)**
   Invoke `Skill(zie-framework:test-pyramid)` เพื่อเลือก test level (unit /
   integration / e2e) ที่เหมาะสม แล้วเขียน test ที่ capture behavior ที่ต้องการ
   — test ต้อง fail ก่อนเสมอ รัน `make test-unit` เพื่อยืนยัน
   ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว ข้ามไป task ถัดไป

4. **เขียน code ให้ผ่าน test (GREEN)**
   เขียน code น้อยที่สุดที่ทำให้ test ผ่าน — ไม่ over-engineer ไม่เดาล่วงหน้า
   รัน `make test-unit` เพื่อยืนยัน

5. **ปรับปรุง code โดยไม่ทำให้ test พัง (REFACTOR)**
   ลด duplication ปรับชื่อให้ชัด ทำให้ง่ายขึ้น — รัน `make test-unit`
   เพื่อยืนยัน

6. **Spawn async impl-reviewer**:
   - Invoke `@agent-impl-reviewer` (background: true):
     pass task description, **Acceptance Criteria** from plan task header,
     and list of files changed in this task.
   - Record returned handle in the pending-reviewers list:
     `{ task_id: <N>, reviewer_handle: <handle>, reviewer_status: pending }`
   - Do NOT block — proceed immediately to announce the next task.
   - **Deferred-check** (start of each task loop iteration): for each entry
     in the pending-reviewers list, poll handle → check `reviewer_status`:
     - `reviewer_status: pending` — still running; continue current task,
       check again at the next iteration.
     - `reviewer_status: approved` — clear entry from list; no action needed.
     - `reviewer_status: issues_found` — halt current task; surface reviewer
       feedback to human; apply fixes; re-run `make test-unit`; re-invoke
       `@agent-impl-reviewer` synchronously (blocking).
       Max 3 total iterations — background spawn counts as iteration 1.
       On APPROVED: clear entry from list; resume current task.

7. **บันทึก task เสร็จ**: Update `TaskUpdate` → completed. Update plan file:
   mark task as `[x]`. Update ROADMAP.md task counter if tracking.
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

1. Run full test suite: `make test-unit` (required) + `make test-int` (if
   available).

2. Invoke `Skill(zie-framework:verify)` — checks TODOs, docs sync, secrets,
   and confirms feature is release-ready before leaving implementation context.

3. Mark feature complete and commit to dev:
   - Update `zie-framework/ROADMAP.md` Now lane: change feature from `[ ]`
     to `[x]` (complete, pending release — see D-005 batch release pattern).
   - Review what will be committed:

     ```bash
     git status --short
     ```

     Expected: implementation files (code, tests, hooks, commands) +
     `zie-framework/ROADMAP.md`. If backlog/spec/plan files appear here they
     were not committed at their stage — commit them now too.

   - Commit all feature code to dev:

     ```bash
     git add -A
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
