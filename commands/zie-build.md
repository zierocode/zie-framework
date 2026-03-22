---
description: Implement the active feature using TDD — RED/GREEN/REFACTOR loop per task. Reads active plan from ROADMAP.md.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, TaskCreate, TaskUpdate
---

# /zie-build — TDD Feature Implementation Loop

Implement the active feature using Test-Driven Development. Reads the active plan from ROADMAP.md and guides through RED → GREEN → REFACTOR per task.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.

2. **ตรวจสอบ: งานที่ค้างอยู่** — อ่าน `zie-framework/ROADMAP.md` → ตรวจ Now lane.
   - `[ ]` item in Now → feature ยังค้างอยู่ → STOP: "Now: `<current>` ยังไม่เสร็จ ทำต่อหรือ /zie-fix ก่อน"
   - `[x]` item(s) in Now → feature(s) เสร็จแล้ว รอ batch release → ปล่อยไว้ใน Now (/zie-ship จะย้ายไป Done พร้อม version) → ดำเนินต่อ
   - Now empty → ดำเนินต่อ

3. **ตรวจสอบ: แผนที่อนุมัติแล้ว** — หา item ใน Ready lane.
   - If Ready is empty → auto-fallback: print "[zie-build] No approved plan. Running /zie-plan first..."
     → run `/zie-plan` (show Next list, Zie selects) → get approval → continue.
   - If Next is also empty during fallback → print "No backlog items. Run /zie-idea first." and STOP.
   - Read plan file → check frontmatter for `approved: true`.
   - If `approved: true` absent → treat as unapproved → trigger auto-fallback above.

4. Pull first Ready item → move to Now in ROADMAP.md.

5. อ่าน `zie-framework/.config` เพื่อ context

6. If `zie_memory_enabled=true` (resume only — domain context already in plan):
   - `recall project=<project> tags=[wip] feature=<slug> limit=1`
   - Read plan's "## Context from brain" section for domain context.
   - Do NOT re-recall domain patterns — /zie-plan already baked them into the plan.

### วิเคราะห์ dependency ระหว่าง tasks

Before starting tasks:
- Parse all tasks in plan for `<!-- depends_on: T1, T2 -->` comments
- Group tasks with no depends_on → **independent** (can run in parallel)
- Tasks with depends_on → **dependent** (run after blocking tasks complete)
- Spawn min(independent_count, 4) parallel agents for independent tasks
- If 0 independent tasks → execute all sequentially in dependency order

## Steps

### วนรอบ task จนครบ:

6. **Announce task**: "Working on: [Task N] — <task description>"

7. For non-trivial tasks, invoke `Skill(zie-framework:tdd-loop)` for RED/GREEN/REFACTOR guidance.

8. **เขียน test ที่ล้มเหลวก่อน (RED)**
   Invoke `Skill(zie-framework:test-pyramid)` เพื่อเลือก test level (unit / integration / e2e) ที่เหมาะสม แล้วเขียน test ที่ capture behavior ที่ต้องการ — test ต้อง fail ก่อนเสมอ รัน `make test-unit` เพื่อยืนยัน
   ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว ข้ามไป task ถัดไป

9. **เขียน code ให้ผ่าน test (GREEN)**
   เขียน code น้อยที่สุดที่ทำให้ test ผ่าน — ไม่ over-engineer ไม่เดาล่วงหน้า รัน `make test-unit` เพื่อยืนยัน

10. **ปรับปรุง code โดยไม่ทำให้ test พัง (REFACTOR)**
    ลด duplication ปรับชื่อให้ชัด ทำให้ง่ายขึ้น — รัน `make test-unit` เพื่อยืนยัน

11. **บันทึก task เสร็จ**:
    - Update `TaskUpdate` → completed.
    - Update plan file: mark task as `[x]`.
    - Update ROADMAP.md task counter if tracking.

11b. **บันทึก WIP สู่ brain** (เฉพาะเมื่อ task มี friction สูงกว่าคาด):
    - `remember "Task harder than estimated: <why>. Next time: <tip>." tags=[build-learning, <project>, <domain>]`
    - Skip this write if task went smoothly — only capture signal, not noise. This is a micro-learning: conditional write on friction only.

12. **Brain checkpoint** (every 5 tasks or on natural stopping point):
    - If `zie_memory_enabled=true`:
      `remember "WIP: <feature> — T<N>/<total> done." tags=[wip, <project>, <feature-slug>] supersedes=[wip, <project>, <feature-slug>]`
      - supersedes replaces previous WIP memory — no duplicate WIPs accumulate.

### เมื่อทำครบทุก task:

13. Run full test suite: `make test-unit` (required) + `make test-int` (if available).

14. Print:
    ```
    All tasks complete for: <feature name>

    Tests: unit ✓ | integration ✓|n/a

    Next: Run /zie-ship to release, or /zie-idea for the next feature.
    ```

## เมื่อ test ล้มเหลว

- If a test fails unexpectedly → invoke `Skill(zie-framework:debug)` before trying fixes.
- If stuck after 2 attempts → surface the error, explain options, ask Zie which path to take.
- Never silently skip tests or comment them out.

## ขั้นตอนถัดไป

→ `/zie-ship` — เมื่อทุก task เสร็จและ test ผ่านหมด
→ `/zie-idea` — เริ่ม feature ถัดไป

## Notes
- Works for any language — test runner detected from `.config`
- If no active plan in ROADMAP.md → suggest running `/zie-idea` first
- Can be run mid-task to resume after a break
- The PostToolUse:auto-test hook fires on every file save — this command sets the strategic direction, hooks handle the feedback loop
