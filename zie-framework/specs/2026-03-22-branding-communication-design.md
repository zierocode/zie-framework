# Branding, Communication & Naming Consistency — Design Spec

**Problem:** zie-framework ยังสื่อสารด้วย plaintext ภาษาอังกฤษ, ASCII art, และ step ที่ตั้งชื่อแบบ generic — ไม่ได้ reflect ว่านี่คือ AI-native framework ที่ออกแบบมาโดยเฉพาะ

**Approach:** ปรับ command/skill files ทั้งหมดให้ใช้ภาษาไทยเป็นหลัก, ใช้ Claude Code native markdown แทน ASCII art, ตั้งชื่อ phase/step ให้สื่อ intent จริงๆ และ maximise การใช้ AI reasoning แทนการระบุ step-by-step แบบ rigid

**Tech Stack:** Markdown command files, pytest

---

## Identity

zie-framework คือ **AI-native SDLC framework** ที่ออกแบบมาให้ทำงานกับ Claude โดยเฉพาะ:
- ไว้วางใจ AI reasoning — ไม่ over-specify สิ่งที่ AI ควรคิดเองได้
- ภาษาไทยเป็นหลัก — professional, ไม่ informal
- Output ใช้ Claude Code native rendering — ไม่ print เอง

---

## Communication Guidelines

### ภาษา
- **Thai primary** สำหรับ user-facing text ทั้งหมดใน command/skill files
- **English** สำหรับ: technical terms (TDD, RED/GREEN, pytest), code snippets, file paths, tool names
- ตัวอย่าง: "ตรวจสอบ gate ก่อนเริ่ม" ไม่ใช่ "Pre-flight check"

### Format
- ใช้ markdown headings (`##`, `###`) แทน ASCII boxes
- ใช้ bold (`**`)  สำหรับ key actions
- ใช้ bullet lists สำหรับ steps
- **ห้าม** print ASCII box art เช่น `┌─ ... ─┐` — ให้ใช้ `##` + table แทน
- Code blocks เฉพาะ code จริงๆ เท่านั้น

### Tone
- Professional, direct — ไม่ verbose, ไม่ informal
- ให้ AI ใช้ judgment ของตัวเองได้ — ไม่ต้อง specify ทุก micro-step

---

## Naming Consistency Audit

### Commands (ชื่อภายนอก — ไม่เปลี่ยน)
| Command | ทำอะไร | ชื่อสื่อถูกต้องมั้ย |
|---|---|---|
| `/zie-idea` | brainstorm → spec → backlog | ✓ idea → spec เป็น natural flow |
| `/zie-plan` | backlog item → implementation plan | ✓ |
| `/zie-build` | implement ด้วย TDD | ✓ |
| `/zie-fix` | debug + fix bug | ✓ |
| `/zie-ship` | release gate + merge | ✓ |
| `/zie-status` | snapshot สถานะปัจจุบัน | ✓ |
| `/zie-retro` | retrospective + learnings | ✓ |

### Internal Step Naming (เปลี่ยน)
| ปัจจุบัน | ใหม่ | เหตุผล |
|---|---|---|
| Pre-flight | ตรวจสอบก่อนเริ่ม | สื่อตรง, Thai-primary |
| Gate 1 — WIP check | ตรวจสอบ: งานที่ค้างอยู่ | บอก intent ไม่ใช่แค่ลำดับ |
| Gate 2 — Approved plan | ตรวจสอบ: แผนที่อนุมัติแล้ว | เหมือนกัน |
| Phase 1, Phase 2 | ชื่อสื่อ intent จริงๆ ต่อ command | generic เกินไป |
| RED phase / GREEN phase / REFACTOR phase | คงไว้ — standard TDD terms | |

---

## AI-Native Maximization

แทนที่จะระบุ rigid steps ให้ AI follow ให้ปรับเป็น **intent-driven instructions**:

```markdown
# ❌ แบบเดิม (rigid)
8. RED phase — Write failing test first:
   - Create or update test file matching the module being implemented.
   - Test must fail before any implementation.
   - Run: `make test-unit` → confirm test fails (expected).

# ✅ แบบใหม่ (intent-driven)
8. **เขียน test ที่ล้มเหลวก่อน (RED)**
   ก่อน implement ให้เขียน test ที่ capture behavior ที่ต้องการ
   — test ต้อง fail ก่อนเสมอ, รัน `make test-unit` เพื่อยืนยัน
```

---

## Components

| Action | File | เปลี่ยนอะไร |
|---|---|---|
| Modify | `commands/zie-idea.md` | Thai-primary, rename phases |
| Modify | `commands/zie-plan.md` | Thai-primary, rename phases |
| Modify | `commands/zie-build.md` | Thai-primary, rename gates/phases, intent-driven steps |
| Modify | `commands/zie-fix.md` | Thai-primary, rename phases |
| Modify | `commands/zie-ship.md` | Thai-primary, rename gates, remove ASCII status print |
| Modify | `commands/zie-status.md` | Thai-primary, remove ASCII box spec, ใช้ markdown table แทน |
| Modify | `commands/zie-retro.md` | Thai-primary |
| Modify | `skills/*/SKILL.md` | Thai-primary communication style |

---

## Out of Scope
- เปลี่ยนชื่อ command (`/zie-*`) — ไม่เปลี่ยน เพราะ user จำแล้ว
- เปลี่ยน logic/behavior ของ command — แค่ปรับ language + format
- เปลี่ยน hook output (hooks/*.py) — scope แยก
