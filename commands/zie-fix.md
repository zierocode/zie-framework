---
description: Debug path — skip ideation, go straight to systematic bug investigation and fix.
argument-hint: Optional bug description or error message
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
---

# /zie-fix — Bug Fix Path

Fast path for fixing bugs. Skips brainstorming and planning — goes directly to debugging, regression test, fix, and verify. Use this instead of /zie-build for bugs and regressions.

## ตรวจสอบก่อนเริ่ม

1. อ่าน `zie-framework/.config` เพื่อ context
2. If `zie_memory_enabled=true`:
   - `recall project=<project> domain=<domain> tags=[bug, build-learning] limit=10`
   - → detect recurring patterns, surface known fragile areas

## Steps

### ทำความเข้าใจ bug

1. If bug description provided as argument → use it.
   If not → ask: "What's the bug? Paste error output or describe the behavior."

2. Invoke `Skill(zie-framework:debug)`:
   - Reproduce the bug
   - Isolate the root cause (not just the symptom)
   - Confirm the minimal reproduction case

### เขียน regression test ก่อน (RED)

1. เขียน failing test ที่ capture bug (`test_<bug_slug>`) — รัน `make test-unit` เพื่อยืนยันว่า test FAILS ก่อนแก้เสมอ

### แก้ bug (GREEN)

1. Implement minimal fix ที่แก้ root cause (ไม่แก้ code ที่ไม่เกี่ยว) — รัน `make test-unit` เพื่อยืนยัน regression test PASSES และไม่มี regression ใหม่

### ยืนยันว่าแก้ถูกต้อง

1. Invoke `Skill(zie-framework:verify)`.

2. If `has_frontend=true` and bug is UI-related:
   - Start dev server and verify visually with agent-browser if needed.

### บันทึกและเรียนรู้

1. Update ROADMAP.md if bug was tracked there (move to Done).

2. If `zie_memory_enabled=true`:
   - `remember "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`

3. Print:

   ```text
   Bug fixed: <description>
   Root cause: <cause>
   Fix: <brief description>
   Pattern: <recurring|one-off>
   Regression test: <test name> ✓

   Run /zie-ship when ready to release.
   ```

## ขั้นตอนถัดไป

→ `/zie-ship` — เมื่อ fix เสร็จและ test ผ่านหมด
→ `/zie-idea` — ถ้า bug reveal design problem ที่ต้องแก้อย่างถูกต้อง

## Notes

- Always write the regression test BEFORE fixing — this is non-negotiable
- If the bug reveals a design problem → after fixing, run /zie-idea to plan a proper solution
- Never use /zie-fix for features — use /zie-build
