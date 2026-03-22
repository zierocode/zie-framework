# Decisions — zie-framework

> Append-only — ไม่ลบ decisions เก่า ใช้ `Status: Superseded` แทน

---

## D-001: WIP=1 Rule

**Date:** 2026-03-22
**Status:** Accepted

**Context:** ต้องการให้ focus — หลาย feature พร้อมกันทำให้ context แตก และเพิ่ม
risk ของ merge conflicts

**Decision:** มีแค่ 1 `[ ]` (in-progress) feature ใน Now lane ต่อครั้ง `[x]`
(complete) items สามารถสะสมใน Now เพื่อ batch release

**Consequences:** developer ต้อง complete หรือ fix ก่อนเริ่ม feature ใหม่; ลด
WIP ในระบบ; รองรับ batch release โดยไม่ต้อง ship ทุก feature แยกกัน

---

## D-002: Graceful Degradation

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-memory และ superpowers เป็น optional dependencies
ที่ไม่ใช่ทุกคนจะมี

**Decision:** ทุก feature ต้องทำงานได้โดยไม่มี optional deps — ใช้ `if
zie_memory_enabled:` guard เสมอ

**Consequences:** code มี conditional paths; แต่ผู้ใช้ที่ไม่มี deps
ก็ยังใช้งานได้ครบทุก command

---

## D-003: Hook Safety — Never Crash Claude

**Date:** 2026-03-22
**Status:** Accepted

**Context:** hooks ที่ crash จะทำให้ Claude Code ใช้ไม่ได้ทั้ง session

**Decision:** ทุก hook ต้องมี try/except ครอบทั้ง main() และ exit(0) เสมอเมื่อ
error — silent fail ดีกว่า crash

**Consequences:** bugs ใน hooks อาจ silent fail; ต้องมี logging ที่ดีเพื่อ
debug; pytest unit tests ครอบทุก hook

---

## D-004: Native Skills แทน Superpowers Dependency

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-framework ขึ้นกับ superpowers:brainstorming,
superpowers:writing-plans ซึ่งเป็น external dependency

**Decision:** fork skills ที่ใช้บ่อยมาไว้ใน `zie-framework/skills/` โดยตรง
(spec-design, write-plan, debug, verify, tdd-loop, test-pyramid, retro-format)

**Consequences:** ต้อง maintain skills เอง; แต่ได้ independence + customization
สำหรับ zie-framework context

---

## D-005: Batch Release Pattern

**Date:** 2026-03-22
**Status:** Accepted

**Context:** Solo developer workflow — ไม่จำเป็นต้อง ship ทุก feature แยกกัน;
อยากสะสม features แล้ว release พร้อมกัน

**Decision:** `[x]` items ใน Now = "complete, pending release" — ค้างไว้จนกว่า
/zie-ship จะย้ายทั้งหมดไป Done พร้อม version; /zie-build ไม่ย้าย items ไป Done

**Consequences:** Now lane อาจมีหลาย `[x]` items; Done = shipped จริง; /zie-ship
batch-moves ทั้งหมดพร้อมกัน

---

## D-006: Remove superpowers dependency (2026-03-23)

**Date:** 2026-03-23
**Status:** Accepted

**Context:** zie-framework previously used superpowers:brainstorming,
superpowers:writing-plans, superpowers:systematic-debugging, and
superpowers:verification-before-completion. These were forked into
zie-framework/skills/ as spec-design, write-plan, debug, and verify (D-004).
The last remaining references (`superpowers_enabled` config key in
zie-plan.md, zie-init.md, and session-resume.py hook) were not cleaned up
at the time of the fork.

**Decision:** zie-framework is fully self-contained. Remove all
`superpowers_enabled` references from commands and hooks. Remove
superpowers from the optional dependencies list in docs.

**Consequences:** zie-framework no longer depends on the superpowers plugin
in any form. The `superpowers_enabled` field in existing `.config` files is
silently ignored (backward compatible — no migration needed).
