# Project Knowledge Architecture — Design Spec

**Problem:** ความรู้เกี่ยวกับ project กระจายอยู่ใน spec/plan files ที่เป็น historical artifacts — ไม่มี single source of truth ที่บอก "project ปัจจุบันเป็นยังไง" และ agent ต้องอ่านไฟล์หลายไฟล์เพื่อ reconstruct context

**Approach:** สร้าง hub-and-spoke knowledge structure — `PROJECT.md` เป็น hub ที่อ่านแล้วเข้าใจภาพรวมทันที, `project/*.md` เป็น spoke ที่ deep-dive แต่ละ domain, `/zie-retro` ทำ sync เข้า zie-memory หลัง ship ทุกครั้ง

**Tech Stack:** Markdown files, zie-memory API, pytest

---

## Architecture

```text
zie-framework/
  PROJECT.md              ← hub: overview + links (max ~2 หน้า, ไม่บวมขึ้น)
  project/
    architecture.md       ← current system design decisions
    components.md         ← command/skill/hook แต่ละตัวทำอะไร (current state)
    decisions.md          ← ADR-style: ทำไมถึงตัดสินใจแบบนั้น

zie-memory (agent-facing)
  project-knowledge/*     ← sync มาจาก md หลัง /zie-retro
```

---

## File Responsibilities

### PROJECT.md (hub)

- **ไม่เกิน 2 หน้า** — ถ้าบวมขึ้น แสดงว่า detail ไม่ได้ย้ายไป spoke
- ประกอบด้วย:
  - What is zie-framework (1 paragraph)
  - Current version + status
  - Command map (ตารางสั้น: command → ทำอะไร)
  - Links ไปยัง spoke files
  - Links ไปยัง ROADMAP, specs, plans

### project/architecture.md (spoke)

- Current system design
- Component relationships
- Data flow overview
- เปลี่ยนเมื่อ: architecture เปลี่ยนจริงๆ (ไม่ใช่ทุก ship)

### project/components.md (spoke)

- แต่ละ command/skill/hook: ทำอะไร, input/output, dependencies
- **Current state** — ไม่ใช่ historical
- เปลี่ยนเมื่อ: command/skill/hook เปลี่ยน behavior

### project/decisions.md (spoke)

- ADR format: Decision → Context → Rationale → Consequences
- เปลี่ยนเมื่อ: มี architectural decision ใหม่
- ไม่ลบ decisions เก่า — mark เป็น superseded แทน

---

## Growth Management

| File | Growth Strategy |
|---|---|
| `PROJECT.md` | Hard cap ~2 หน้า — ถ้าบวมขึ้น → ย้าย detail ไป spoke |
| `project/architecture.md` | เขียนทับ section ที่เปลี่ยน — ไม่ append ตลอด |
| `project/components.md` | Update เฉพาะ component ที่เปลี่ยน |
| `project/decisions.md` | Append-only — แต่ mark superseded decisions ชัดเจน |
| zie-memory | /zie-retro curate ก่อน sync — ไม่ dump ทุกอย่าง |

---

## Update Triggers

| Event | Action |
|---|---|
| `/zie-ship` completes | auto-trigger `/zie-retro` |
| `/zie-retro` | อ่าน project/*.md → distill changes → sync เข้า zie-memory |
| Architecture เปลี่ยน | Update `project/architecture.md` ทันที (ไม่รอ retro) |
| Component เปลี่ยน behavior | Update `project/components.md` ทันที |
| Decision ใหม่ | Append ใน `project/decisions.md` ทันที |

---

## zie-memory Sync Pattern

หลัง /zie-retro:

```text
remember "Project snapshot: <version>. Components: <changed>. Decisions: <new>."
  tags=[project-knowledge, zie-framework, <version>]
  supersedes=[project-knowledge, zie-framework]
```

การ recall ของ agent:

```text
recall project=zie-framework tags=[project-knowledge] limit=1
```

→ ได้ current snapshot ทันที ไม่ต้องอ่าน md files

---

## Components

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `zie-framework/PROJECT.md` | Hub document |
| Create | `zie-framework/project/architecture.md` | System design |
| Create | `zie-framework/project/components.md` | Component registry |
| Create | `zie-framework/project/decisions.md` | Decision log |
| Modify | `commands/zie-retro.md` | เพิ่ม md update + zie-memory sync steps |
| Modify | `templates/` | เพิ่ม PROJECT.md + project/ ใน /zie-init template |
| Add | `tests/unit/test_knowledge_arch.py` | ตรวจว่า files ครบและ format ถูก |

---

## Out of Scope

- Auto-generate PROJECT.md จาก code (ต้อง write manually)
- Full-text search ใน project knowledge
- Version history ของ knowledge (git เป็น history แล้ว)
