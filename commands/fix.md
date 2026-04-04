---
description: Debug path — skip ideation, go straight to systematic bug investigation and fix.
argument-hint: Optional bug description or error message
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill
model: sonnet
effort: low
---

# /fix — Bug Fix Path

Fast path for fixing bugs. Skips brainstorming and planning — goes directly to
debugging, regression test, fix, and verify. Use this instead of /implement
for bugs and regressions. **Use for non-urgent bugs. Does not trigger an immediate release. For production incidents requiring immediate release, use /hotfix instead.**

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. อ่าน `zie-framework/.config` เพื่อ context.
3. Read `zie-framework/ROADMAP.md` → check Now lane.
   - If a `[ ]` item exists → warn: "WIP active: `<feature>`. Bug fix will be
     a separate commit outside the current feature. Proceed? (yes/no)"
   - If no → stop.
4. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__recall`
     with `project=<project> domain=<domain> tags=[bug, build-learning] limit=10`
   - → detect recurring patterns, surface known fragile areas

## Steps

### ทำความเข้าใจ bug

1. If bug description provided as argument → use it.
   If not → ask: "What's the bug? Paste error output or describe the
   behavior."

2. Invoke `Skill(zie-framework:debug)`:
   - Reproduce the bug
   - Isolate the root cause (not just the symptom)
   - Confirm the minimal reproduction case

### เขียน regression test ก่อน (RED)

1. Write failing test that captures the bug. Use naming convention:
   `test_should_not_<failure_description>` or
   `test_<feature>_when_<condition>_should_<result>`
   Run `make test-unit` — must FAIL before fix. This is non-negotiable.

### แก้ bug (GREEN)

1. Implement minimal fix targeting root cause (not symptoms, not unrelated
   code).
   Run `make test-unit` — regression test must PASS, no new failures.

### ยืนยันว่าแก้ถูกต้อง

1. Invoke `Skill(zie-framework:verify)` with `scope=tests-only` (bug fixes
   do not require full docs-sync check or code review).

2. If `has_frontend=true` and bug is UI-related:
   - Start dev server and verify visually.

### บันทึกและเรียนรู้

1. If bug was already tracked in `zie-framework/ROADMAP.md` → move to Done.
   If not tracked → no ROADMAP update needed.

2. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`

3. Print:

   ```text
   Bug fixed: <description>
   Root cause: <cause>
   Fix: <brief description>
   Pattern: <recurring|one-off>
   Regression test: <test name> ✓

   Run /release when ready to release.
   ```

## ขั้นตอนถัดไป

→ `/release` — เมื่อ fix เสร็จและ test ผ่านหมด
→ `/backlog` — ถ้า bug reveal design problem ที่ต้องแก้อย่างถูกต้อง

## Notes

- Always write the regression test BEFORE fixing — non-negotiable
- If the bug reveals a design problem → after fixing, run /backlog to
  capture and /spec to plan a proper solution
- Never use /fix for features — use /implement
