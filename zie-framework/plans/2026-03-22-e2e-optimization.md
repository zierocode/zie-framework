---
approved: true
approved_at: 2026-03-22
backlog: backlog/e2e-optimization.md
spec: specs/2026-03-22-e2e-optimization-design.md
---

# E2E Optimization — Implementation Plan

**Goal:** ลด redundancy ในการ load context, ปรับ steps เป็น intent-driven, ทำให้ handoff ระหว่าง command เป็น seamless, standardize memory patterns

**Tech Stack:** Markdown command/skill files, pytest

**หมายเหตุ:** ควรทำหลัง Spec 1 (branding-communication) — จะ build on top ของ renamed sections

---

## Task 1 — Collapse config reads ใน zie-build.md [S]

**Files:** `commands/zie-build.md`

**เปลี่ยนอะไร:**
- Pre-flight step ที่อ่าน `.config`: collapse เป็น 1 บรรทัด
  - ปัจจุบัน: "5. Read `zie-framework/.config` → project_type, test_runner."
  - ใหม่: "5. อ่าน `zie-framework/.config` — ใช้ project_type, test_runner เป็น context"
  - ไม่ enumerate ทุก key — trust AI ว่ารู้ว่าต้องอ่านอะไร

**Acceptance criteria:** ไม่มี bullet list ของ config keys ใน pre-flight

---

## Task 2 — Collapse config reads ใน zie-fix.md [S]

**Files:** `commands/zie-fix.md`

**เปลี่ยนอะไร:**
- Pre-flight: "1. Read `zie-framework/.config` → project_type, test_runner."
  → "1. อ่าน `zie-framework/.config` เพื่อ context"

---

## Task 3 — Collapse config reads ใน zie-ship.md [S]

**Files:** `commands/zie-ship.md`

**เปลี่ยนอะไร:**
- Pre-flight: "2. Read `zie-framework/.config` → has_frontend, playwright_enabled, test_runner."
  → "2. อ่าน `zie-framework/.config` — ใช้ has_frontend, playwright_enabled เป็น context"

---

## Task 4 — Collapse config read ใน zie-status.md [S]

**Files:** `commands/zie-status.md`

**เปลี่ยนอะไร:**
- Step 2: แทนที่จะ enumerate ทุก key ให้เป็น 1 line:
  - "อ่าน `zie-framework/.config`, `zie-framework/ROADMAP.md`, `VERSION` เพื่อ context"

---

## Task 5 — Simplify pre-flight ใน zie-idea.md + เพิ่ม handoff [S]

**Files:** `commands/zie-idea.md`

**เปลี่ยนอะไร:**
- Pre-flight ปัจจุบัน (3 steps verbose) → checklist สั้น:
  ```
  ## ตรวจสอบก่อนเริ่ม
  - `zie-framework/` มีอยู่ — ถ้าไม่มี: แจ้งให้ run /zie-init ก่อน
  - อ่าน `.config` + recall memories (ถ้า zie_memory_enabled) ใน 1 รอบ
  ```
- เพิ่ม "## ขั้นตอนถัดไป" ท้าย command:
  ```
  ## ขั้นตอนถัดไป
  → /zie-plan <slug> — เพื่อ draft implementation plan
  → /zie-status — ดูภาพรวม backlog
  ```

**Acceptance criteria:** Pre-flight ≤ 3 items, มี handoff block

---

## Task 6 — Simplify pre-flight ใน zie-plan.md + เพิ่ม handoff [S]

**Files:** `commands/zie-plan.md`

**เปลี่ยนอะไร:**
- Pre-flight: collapse เหลือ 2 items
- เพิ่ม "## ขั้นตอนถัดไป" ท้าย command:
  ```
  ## ขั้นตอนถัดไป
  → /zie-build — เริ่ม implement feature ที่อนุมัติแล้ว
  → /zie-status — ดูภาพรวม
  ```

---

## Task 7 — Intent-driven steps ใน zie-build.md [M]

**Files:** `commands/zie-build.md`

**เปลี่ยนอะไร (หลัง Task 1 + Spec 1):**
- Dependency resolution section: ลด verbose bullet list → 3 bullets สั้นที่บอก intent
- "วนรอบ task จนครบ" section: ปรับ step 8 RED, 9 GREEN, 10 REFACTOR ให้เป็น intent-driven

  **RED (ปัจจุบัน — verbose):**
  ```
  - Before writing the test, invoke Skill(...)...
  - Create or update test file matching the module...
  - Test must fail before any implementation.
  - Run: make test-unit → confirm test fails (expected).
  - If test already passes → the feature already exists, move to next task.
  ```
  **RED (ใหม่ — intent-driven):**
  ```
  ก่อน implement: invoke Skill(zie-framework:test-pyramid) เพื่อเลือก test level แล้วเขียน test
  ที่ capture behavior ที่ต้องการ — test ต้อง fail ก่อนเสมอ, รัน `make test-unit` เพื่อยืนยัน
  ถ้า test ผ่านแล้ว → feature มีอยู่แล้ว, ข้ามไป task ถัดไป
  ```
  (ทำเหมือนกันสำหรับ GREEN และ REFACTOR)

- เพิ่ม handoff block ถ้ายังไม่มี:
  ```
  ## ขั้นตอนถัดไป
  → /zie-ship — เมื่อทุก task เสร็จและ test ผ่าน
  → /zie-idea — เริ่ม feature ถัดไป
  ```

**Acceptance criteria:** ไม่มี micro-step list ใน RED/GREEN/REFACTOR, มี handoff block

---

## Task 8 — Intent-driven steps ใน zie-fix.md [S]

**Files:** `commands/zie-fix.md`

**เปลี่ยนอะไร (หลัง Spec 1):**
- Phase "ทำความเข้าใจ bug": ลด instructions verbose → intent statement
- Phase "เขียน regression test": ลด verbose → intent
- เพิ่ม handoff block ถ้ายังไม่มี

---

## Task 9 — Simplify gate descriptions ใน zie-ship.md [S]

**Files:** `commands/zie-ship.md`

**เปลี่ยนอะไร (หลัง Spec 1):**
- แต่ละ gate: ลด description verbose → 1-2 บรรทัดที่บอก intent + failure action
- ตัวอย่าง Gate Unit Tests:
  - ปัจจุบัน: 3+ bullet points
  - ใหม่: "รัน `make test-unit` — ต้อง exit 0. ถ้าล้มเหลว: หยุดทันที แจ้ง `/zie-fix` ก่อน"

---

## Task 10 — Standardize memory patterns ทุก command [S]

**Files:** `commands/zie-build.md`, `commands/zie-fix.md`, `commands/zie-ship.md`, `commands/zie-idea.md`, `commands/zie-plan.md`, `commands/zie-retro.md`

**Pattern recall standard:**
```
recall project=<p> domain=<d> tags=[<context-tags>] limit=<n>
```
ทุก command ที่มี recall: ตรวจสอบว่าใช้ format นี้ และ collapse multiple recalls → single batch call

**Pattern remember standard (ตาม event type):**
- Build learning: `remember "..." tags=[build-learning, <project>, <domain>]`
- Bug fix: `remember "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`
- WIP: `remember "WIP: <feature> — T<N>/<total> done." tags=[wip, <project>, <slug>] supersedes=[wip, <project>, <slug>]`
- Shipped: `remember "Shipped: <feature> v<VERSION>. Tasks: N." tags=[shipped, <project>, <domain>]`
- Plan approved: `remember "Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>." tags=[plan, <project>, <domain>]`

ตรวจสอบทุก command ว่า recall/remember patterns match standard นี้

---

## Task 11 — Reduce skill chain depth [M]

**Files:** `skills/spec-design/SKILL.md`, `skills/write-plan/SKILL.md`

**เปลี่ยนอะไร:**
- ถ้ามี step ที่ invoke skill แล้ว skill invoke อีก skill: inline instruction แทน
- ตรวจสอบ spec-design และ write-plan ว่ามี hop ที่ไม่จำเป็น
- ถ้า hop มี value (เช่น tdd-loop ใน zie-build): คงไว้
- ถ้า hop เป็น แค่ boilerplate: inline

---

## Notes
- Tasks 1–4 (config collapse): independent, ทำ parallel ได้
- Tasks 5–6 (pre-flight + handoff): independent
- Tasks 7–8 (intent-driven): ทำหลัง Spec 1 เพื่อให้ section names ถูกต้อง
- Tasks 9–10 (gate simplify + memory): independent
- Task 11 (skill chain): สุดท้าย หลัง 1–10 เสร็จ
