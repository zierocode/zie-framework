# E2E Optimization — Design Spec

**Problem:** zie-framework มี redundancy ในการ load context, ขั้นตอนบางอย่างที่
AI ควรทำเองได้กลับถูก over-specify และ handoff ระหว่าง command ไม่ smooth

**Approach:** Audit flow ทั้งหมด end-to-end แล้วตัด/รวม/simplify จุดที่ซ้ำซ้อน
ปรับให้ AI ใช้ judgment มากขึ้น และทำให้ transition ระหว่าง command เป็น
seamless

**Tech Stack:** Markdown command files, pytest

---

## Pain Points ที่ระบุได้

### 1. Context Loading ซ้ำซ้อน

ทุก command อ่าน `.config` + `ROADMAP.md` ใหม่ทุกครั้ง —
ควรอ่านครั้งเดียวแล้วใช้ตลอด session

### 2. Over-specified Steps

บาง step ที่ AI ควรรู้เองถูก spell out ทุก micro-action:

- "Read the file → check the value → if X do Y else do Z" → ควรบอกแค่ intent
- AI ฉลาดพอที่จะรู้ว่าต้องอ่านไฟล์ก่อน ไม่ต้องบอกทุกครั้ง

### 3. Skill Invocation Overhead

บาง command invoke skill แล้ว skill ก็ invoke อีก skill — chain ยาวเกินไป
ควร inline instruction ที่ใช้บ่อยแทนการ hop ระหว่าง skills

### 4. Handoff ระหว่าง Commands ไม่ชัด

หลังจาก `/zie-idea` เสร็จ → user ต้องรู้เองว่าต้อง run `/zie-plan` ต่อ
ควรมี "next step" suggestion ที่ชัดเจนและ context-aware ทุกจุด

### 5. Memory Pattern ยัง Fragmented

recall/remember กระจายอยู่ใน command ต่างๆ โดยไม่มี pattern ที่สอดคล้องกัน
บาง command recall แบบ batch บาง command ยังใช้ bare recall

---

## Optimization Areas

### A. Reduce Config Re-reads

**ปัจจุบัน:** ทุก command มี "Read `zie-framework/.config`" เป็น step แรก
**ใหม่:** คงไว้ แต่ collapse เป็น 1 line และไม่ enumerate ทุก key — trust AI
ว่ารู้ว่าต้องอ่านอะไร

### B. Simplify Pre-flight Pattern

**ปัจจุบัน:** Pre-flight มี 3-5 steps ที่ verbose
**ใหม่:** Pre-flight เป็น checklist สั้น → AI ตรวจเองและ proceed หรือ block

### C. Intent-Driven Step Descriptions

**ปัจจุบัน:** Steps ระบุ "how" ทุก micro-action
**ใหม่:** Steps ระบุ "what + why" — AI เลือก "how" เอง

### D. Cleaner Command Handoffs

เพิ่ม consistent "ขั้นตอนถัดไป" block ทุก command:

```text
## ขั้นตอนถัดไป
→ /zie-plan <slug> — เพื่อสร้าง implementation plan
→ /zie-status — ดูภาพรวม
```

### E. Memory Pattern Standardization

กำหนด standard recall pattern ทุก command:

```text
recall project=<p> domain=<d> tags=[<context-tags>] limit=<n>
```

กำหนด standard remember pattern ทุก command ตาม type ของ event

---

## Components

| Action | File | เปลี่ยนอะไร |
| --- | --- | --- |
| Modify | `commands/zie-idea.md` | Simplify pre-flight, add handoff |
| Modify | `commands/zie-plan.md` | Simplify pre-flight, add handoff |
| Modify | `commands/zie-build.md` | Intent-driven steps, collapse config read |
| Modify | `commands/zie-fix.md` | Intent-driven steps |
| Modify | `commands/zie-ship.md` | Simplify gate descriptions |
| Modify | `commands/zie-status.md` | Collapse config read |
| Modify | `skills/*/SKILL.md` | Reduce chain depth |

---

## Out of Scope

- เปลี่ยน logic หลัก (gate enforcement, TDD loop, dependency graph)
- เปลี่ยน hook implementations
- Performance ของ Python hooks (separate concern)
