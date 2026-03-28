---
approved: true
approved_at: 2026-03-22
backlog: backlog/branding-communication.md
spec: specs/2026-03-22-branding-communication-design.md
---

# Branding, Communication & Naming Consistency — Implementation Plan

**Goal:** ปรับ command/skill files ทั้งหมดให้ใช้ภาษาไทยเป็นหลัก, ใช้ Claude Code native markdown แทน ASCII art, ตั้งชื่อ phase/step ให้สื่อ intent จริงๆ

**Tech Stack:** Markdown command/skill files, pytest

---

## Task 1 — Update `commands/zie-status.md` [M]

**Files:** `commands/zie-status.md`

**เปลี่ยนอะไร:**

- Step 5 print block: แทน `┌─ ... ─┐` ASCII box ด้วย markdown headings + table
- Label ใน print block ให้ใช้ภาษาไทย: "โปรเจกต์", "สถานะ", "งานปัจจุบัน", "ขั้นตอนถัดไป"
- Technical terms คงไว้เป็น English (VERSION, unit, integration, e2e, ROADMAP)

**Print block ใหม่:**

```text
## สถานะ zie-framework

| | |
| --- | --- |
| โปรเจกต์ | <directory name> (<project_type>) |
| Version | <VERSION> |
| Brain | <enabled\ | disabled> |

**ROADMAP**
- Now: <N> in progress
- Next: <N> queued
- Done: <N> shipped

**งานปัจจุบัน**: <item or "ยังไม่มีงาน">
**Plan**: <path or "ยังไม่มี plan">

| Tests | สถานะ |
| --- | --- |
| unit | <✓ pass \ | ✗ fail \ | ? stale \ | n/a> |
| integration | <✓ pass \ | ✗ fail \ | ? stale \ | n/a> |
| e2e | <✓ pass \ | ✗ fail \ | ? stale \ | n/a> |

**ขั้นตอนถัดไป**: <context-appropriate suggestion>
```

**Acceptance criteria:** ไม่มี `┌`, `│`, `└` ใน command file, print block ใช้ markdown

---

## Task 2 — Update `commands/zie-ship.md` [M]

**Files:** `commands/zie-ship.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "### Gate 1 — Unit Tests" → "### ตรวจสอบ: Unit Tests"
- "### Gate 2 — Integration Tests" → "### ตรวจสอบ: Integration Tests"
- "### Gate 3 — E2E Tests" → "### ตรวจสอบ: E2E Tests"
- "### Gate 4 — Visual Verification" → "### ตรวจสอบ: Visual (ถ้ามี frontend)"
- "### Gate 5 — Verification Checklist" → "### ตรวจสอบ: Checklist ก่อน release"
- "### Gate 6 — Code Review" → "### ตรวจสอบ: Code diff ก่อน merge"
- Step 13 print block: แทน ASCII ด้วย markdown
- ใช้ภาษาไทยสำหรับ instruction text ทั้งหมด

**Acceptance criteria:** ไม่มี "Gate N —" pattern, ไม่มี ASCII box ใน print block

---

## Task 3 — Update `commands/zie-build.md` [M]

**Files:** `commands/zie-build.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "**Gate 1 — WIP check**" → "**ตรวจสอบ: งานที่ค้างอยู่**"
- "**Gate 2 — Approved plan check**" → "**ตรวจสอบ: แผนที่อนุมัติแล้ว**"
- "### Dependency resolution" → "### วิเคราะห์ dependency ระหว่าง tasks"
- "### Per task (repeat until all tasks complete):" → "### วนรอบ task จนครบ"
- "**RED phase**" → "**เขียน test ที่ล้มเหลวก่อน (RED)**" พร้อมปรับ description เป็น intent-driven
- "**GREEN phase**" → "**เขียน code ให้ผ่าน test (GREEN)**"
- "**REFACTOR phase**" → "**ปรับปรุง code โดยไม่ทำให้ test พัง (REFACTOR)**"
- "**Mark task complete**" → "**บันทึก task เสร็จ**"
- "**Brain checkpoint**" → "**บันทึก WIP สู่ brain**"
- "### After all tasks complete:" → "### เมื่อทำครบทุก task"
- Step ต่างๆ: ปรับเป็น intent-driven (บอก what+why ไม่ต้อง spell out ทุก micro-action)
- Step 14 print block: แทน code block ASCII ด้วย markdown
- "## Handling Failures" → "## เมื่อ test ล้มเหลว"
- เพิ่ม "## ขั้นตอนถัดไป" block ท้าย command

**Acceptance criteria:** ไม่มี "Gate N —", "Phase N", ไม่มี instruction text เป็น English ที่ไม่ใช่ technical term

---

## Task 4 — Update `commands/zie-fix.md` [S]

**Files:** `commands/zie-fix.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "### Phase 1 — Understand the bug" → "### ทำความเข้าใจ bug"
- "### Phase 2 — Regression test first (TDD)" → "### เขียน regression test ก่อน (RED)"
- "### Phase 3 — Fix" → "### แก้ bug (GREEN)"
- "### Phase 4 — Verify" → "### ยืนยันว่าแก้ถูกต้อง"
- "### Phase 5 — Document + Learn" → "### บันทึกและเรียนรู้"
- Instruction text: ปรับเป็นภาษาไทย, intent-driven
- เพิ่ม "## ขั้นตอนถัดไป" block

**Acceptance criteria:** ไม่มี "Phase N —" pattern

---

## Task 5 — Update `commands/zie-idea.md` [S]

**Files:** `commands/zie-idea.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "### Phase 1 — Brainstorm (spec)" → "### สร้าง spec"
- "### Phase 2 — Implementation Plan" → "### เขียน implementation plan"
- "### Phase 3 — Update state" → "### อัปเดต ROADMAP และ backlog"
- Instruction text: ปรับเป็นภาษาไทย สำหรับ description ที่ไม่ใช่ technical
- เพิ่ม "## ขั้นตอนถัดไป" block

**Acceptance criteria:** ไม่มี "Phase N —" ที่เป็น English label

---

## Task 6 — Update `commands/zie-plan.md` [S]

**Files:** `commands/zie-plan.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "## No arguments — list and select" → "## ไม่มี argument — แสดงรายการ backlog"
- "## With slug(s) — draft plans" → "## ร่าง plan สำหรับ slug ที่เลือก"
- "## Approval gate (sequential, one plan at a time)" → "## ขออนุมัติ plan"
- "## Print summary" → "## สรุปผล"
- Instruction text: ปรับเป็นภาษาไทย
- เพิ่ม "## ขั้นตอนถัดไป" block

---

## Task 7 — Update `commands/zie-retro.md` [S]

**Files:** `commands/zie-retro.md`

**เปลี่ยนอะไร:**

- "## Pre-flight" → "## ตรวจสอบก่อนเริ่ม"
- "### Phase 1 — Gather context" → "### รวบรวม context"
- "### Phase 2 — Generate retrospective" → "### วิเคราะห์และสรุป"
- "### Phase 3 — Write ADRs" → "### บันทึก ADRs"
- "### Phase 4 — Update ROADMAP" → "### อัปเดต ROADMAP"
- "### Phase 5 — Brain storage" → "### บันทึกสู่ brain"
- "### Phase 6 — Print summary" → "### สรุปผล"
- Instruction text: ปรับเป็นภาษาไทย

---

## Task 8 — Update skill files (Thai-primary) [M]

**Files:** `skills/spec-design/SKILL.md`, `skills/write-plan/SKILL.md`, `skills/debug/SKILL.md`, `skills/verify/SKILL.md`, `skills/tdd-loop/SKILL.md`, `skills/test-pyramid/SKILL.md`, `skills/retro-format/SKILL.md`

**เปลี่ยนอะไร (สำหรับทุก skill):**

- Section headings และ instruction text: ปรับเป็นภาษาไทยสำหรับ user-facing text
- Technical terms คงไว้ (RED/GREEN/REFACTOR, TDD, pytest, unit/integration/e2e)
- ใช้ `##` headings, bold, bullets — ไม่มี ASCII art
- Steps: intent-driven (what+why) ไม่ต้อง spell out micro-actions
- อย่าเปลี่ยน logic หรือ structure ของ skill — แค่ปรับ language + format

**Acceptance criteria:** ทุก skill file ไม่มี ASCII box, instruction text เป็นภาษาไทย > 50%

---

## Task 9 — Add tests [S]

**Files:** `tests/unit/test_branding.py`

**Tests:**

- `test_no_ascii_boxes_in_commands` — ตรวจว่าไม่มี `┌`, `│`, `└` ใน command files
- `test_no_ascii_boxes_in_skills` — ตรวจว่าไม่มี ASCII box ใน skill files
- `test_phase_labels_renamed_build` — ตรวจว่า zie-build.md ไม่มี "Phase 1" / "Gate 1 —"
- `test_phase_labels_renamed_fix` — ตรวจว่า zie-fix.md ไม่มี "Phase 1 —"
- `test_phase_labels_renamed_ship` — ตรวจว่า zie-ship.md ไม่มี "Gate 1 —"
- `test_handoff_blocks_present` — ตรวจว่า zie-build.md และ zie-fix.md มี "ขั้นตอนถัดไป"
- `test_status_uses_markdown_table` — ตรวจว่า zie-status.md ไม่มี ASCII box

**Run:** `make test-unit` → all 7 tests pass

---

## Notes

- ลำดับ tasks: 1–8 ทำได้ parallel, task 9 รอหลัง 1–8 เสร็จ
- อย่าเปลี่ยน logic (gates, TDD loop, memory patterns) — แค่ปรับ language + naming + format
- Spec 2 (e2e-optimization) จะ build on top ของ spec 1 นี้ — ควรทำ spec 1 ก่อน
