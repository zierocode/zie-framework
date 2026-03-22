---
approved: true
approved_at: 2026-03-22
backlog: backlog/knowledge-architecture.md
spec: specs/2026-03-22-knowledge-architecture-design.md
---

# Project Knowledge Architecture — Implementation Plan

**Goal:** สร้าง hub-and-spoke knowledge structure — PROJECT.md เป็น hub, project/*.md เป็น spokes, /zie-retro sync เข้า zie-memory หลัง ship

**Tech Stack:** Markdown files, Python (tests), pytest

---

## Task 1 — Create `zie-framework/PROJECT.md` [S]

**Files:** `zie-framework/PROJECT.md` (create)

**โครงสร้าง:**

```markdown
# zie-framework

<paragraph: what is zie-framework — AI-native SDLC framework for Claude Code>

**Version**: <current from VERSION file>  **Status**: active

## Commands

| Command | ทำอะไร |
| --- | --- |
| /zie-idea | Brainstorm → spec → backlog item |
| /zie-plan | Backlog → draft plan → approval → Ready |
| /zie-build | Ready → TDD implementation → Now → complete |
| /zie-fix | Bug → regression test → fix → verify |
| /zie-ship | Release gate → merge dev→main → tag → retro |
| /zie-status | Snapshot สถานะปัจจุบัน |
| /zie-retro | Retrospective → ADRs → brain storage |

## Knowledge

- [Architecture](project/architecture.md) — system design, component relationships
- [Components](project/components.md) — command/skill/hook registry
- [Decisions](project/decisions.md) — ADR log

## Links

- [ROADMAP](ROADMAP.md) — current backlog + active work
- [Specs](specs/) — feature designs
- [Plans](plans/) — implementation plans
```

**Constraint:** ไม่เกิน 2 หน้า (ถ้าบวมขึ้น → detail ต้องอยู่ใน spoke)

**Acceptance criteria:** ไฟล์สร้างเสร็จ, มีทุก section, ≤ 60 lines

---

## Task 2 — Create `zie-framework/project/architecture.md` [S]

**Files:** `zie-framework/project/architecture.md` (create new directory + file)

**โครงสร้าง:**

```markdown
# Architecture — zie-framework

**Last updated:** 2026-03-22

## Overview

<2-3 sentences: zie-framework เป็น Claude Code plugin ที่ใช้ hooks + commands + skills>

## Plugin Structure

<diagram หรือ list ของ: .claude-plugin/plugin.json, hooks/hooks.json, hooks/*.py,
commands/zie-*.md, skills/*/SKILL.md, templates/, zie-framework/>

## Component Relationships

<อธิบาย: commands invoke skills, hooks fire on events, zie-memory เป็น optional brain>

## Data Flow

<อธิบาย: user runs /zie-command → markdown loaded → steps execute → hooks fire>

## Key Constraints

- WIP=1 (one active feature at a time)
- Graceful degradation (works without zie-memory, without superpowers)
- Hook safety (hooks must never crash Claude)
```

---

## Task 3 — Create `zie-framework/project/components.md` [S]

**Files:** `zie-framework/project/components.md` (create)

**โครงสร้าง:**

```markdown
# Components Registry — zie-framework

**Last updated:** 2026-03-22

## Commands

| Command | Input | Output | Dependencies |
| --- | --- | --- | --- |
| /zie-idea | idea (optional) | spec + backlog item | spec-design skill, write-plan skill |
| /zie-plan | slug(s) | approved plan in Ready | write-plan skill |
| /zie-build | (reads ROADMAP Now) | implemented feature | tdd-loop, test-pyramid, debug skills |
| /zie-fix | bug description | regression test + fix | debug, verify skills |
| /zie-ship | (reads ROADMAP Now) | release tag + ADRs | verify skill |
| /zie-status | (reads files) | status snapshot | none |
| /zie-retro | (reads git log) | ADRs + brain memories | retro-format skill |

## Skills

| Skill | ทำอะไร | Invoked by |
| --- | --- | --- |
| spec-design | Brainstorm → spec | /zie-idea |
| write-plan | Spec → task plan | /zie-idea, /zie-plan |
| tdd-loop | RED/GREEN/REFACTOR guide | /zie-build |
| test-pyramid | Choose test level | /zie-build (RED phase) |
| debug | Reproduce → isolate → fix | /zie-build, /zie-fix |
| verify | Pre-ship verification checklist | /zie-fix, /zie-ship |
| retro-format | ADR + retro structure | /zie-retro |

## Hooks

| Hook | Event | ทำอะไร |
| --- | --- | --- |
| auto-test.py | PostToolUse:Write/Edit | รัน test suite หลัง save |
| safety-check.py | PreToolUse:Bash | บล็อก dangerous commands |
| intent-detect.py | PreToolUse:Bash | ตรวจ intent จาก bash pattern |
| session-resume.py | SessionStart | แสดง project state |
| session-learn.py | PostToolUse | สังเกต patterns |
| wip-checkpoint.py | PeriodicTask | บันทึก WIP สู่ brain |
```

---

## Task 4 — Create `zie-framework/project/decisions.md` [S]

**Files:** `zie-framework/project/decisions.md` (create)

**โครงสร้าง:** ADR format, append-only

```markdown
# Decisions — zie-framework

> Append-only — ไม่ลบ decisions เก่า, ใช้ Status: Superseded แทน

---

## D-001: WIP=1 Rule

**Date:** 2026-03-22
**Status:** Accepted

**Context:** ต้องการให้ focus — หลาย feature พร้อมกันทำให้ context แตก

**Decision:** ให้มีแค่ 1 feature ใน Now lane ต่อครั้งเสมอ

**Consequences:** developer ต้อง ship ก่อนเริ่ม feature ใหม่; ลด WIP ในระบบ

---

## D-002: Graceful degradation

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-memory และ superpowers เป็น optional dependencies

**Decision:** ทุก feature ต้องทำงานได้โดยไม่มี optional deps — ใช้ `if zie_memory_enabled:` guard

**Consequences:** code อาจมี conditional paths มากขึ้น; แต่ผู้ใช้ที่ไม่มี deps ก็ยังใช้งานได้

---

## D-003: Hook safety — never crash Claude

**Date:** 2026-03-22
**Status:** Accepted

**Context:** hooks ที่ crash จะทำให้ Claude Code ใช้ไม่ได้

**Decision:** ทุก hook ต้องมี try/except ครอบทั้ง main() และ exit(0) เสมอเมื่อ error

**Consequences:** bugs ใน hooks อาจ silent fail; ต้องมี logging ที่ดีเพื่อ debug

---

## D-004: Native skills แทน superpowers dependency

**Date:** 2026-03-22
**Status:** Accepted

**Context:** zie-framework ขึ้นกับ superpowers:brainstorming, superpowers:writing-plans ซึ่งเป็น external

**Decision:** fork skills ที่ใช้บ่อยมาไว้ใน zie-framework/skills/ โดยตรง

**Consequences:** ต้อง maintain skills เอง; แต่ได้ independence + customization สำหรับ zie-framework context
```

---

## Task 5 — Update `commands/zie-retro.md` (knowledge sync) [S]

**Files:** `commands/zie-retro.md`

**เพิ่ม Phase ใหม่หลัง Phase 3 (Write ADRs):**

```markdown
### อัปเดต project knowledge

หลัง ADRs เขียนเสร็จ:
- อ่าน `zie-framework/project/components.md` → อัปเดต components ที่เปลี่ยน behavior ใน session นี้
- อ่าน `zie-framework/project/decisions.md` → append ADRs ใหม่ที่เพิ่งสร้าง (ถ้ายังไม่มี)
- ถ้า architecture เปลี่ยน → อัปเดต `zie-framework/project/architecture.md`

ถ้า `zie_memory_enabled=true`:
- Sync project snapshot สู่ brain:
  `remember "Project snapshot: <version>. Components changed: <list>. Decisions: <new ADR slugs>." tags=[project-knowledge, zie-framework, <version>] supersedes=[project-knowledge, zie-framework]`
```

**Acceptance criteria:** zie-retro.md มี section "อัปเดต project knowledge", มี supersedes pattern

---

## Task 6 — Update templates (`/zie-init` template) [S]

**Files:** `templates/` (ตรวจว่ามี template อะไรบ้าง แล้วเพิ่ม PROJECT.md + project/)

ขั้นตอน:

1. อ่าน templates/ ดูว่ามี zie-init template หรือไม่
2. ถ้ามี template file สำหรับ `/zie-init`:
   - เพิ่ม `PROJECT.md` ใน list of files to create
   - เพิ่ม `project/architecture.md`, `project/components.md`, `project/decisions.md`
   - ใช้ minimal stubs (placeholder content พร้อม TODO)
3. ถ้าไม่มี template (zie-init ใช้ inline content):
   - อ่าน zie-init command → เพิ่ม steps สร้าง 4 files นี้

---

## Task 7 — Add `tests/unit/test_knowledge_arch.py` [S]

**Files:** `tests/unit/test_knowledge_arch.py` (create)

**Tests:**

```python
def test_project_md_exists():
    # zie-framework/PROJECT.md ต้องมีอยู่
    assert os.path.exists("zie-framework/PROJECT.md")

def test_project_md_size_limit():
    # PROJECT.md ต้องไม่เกิน 80 lines (≈2 หน้า)
    with open("zie-framework/PROJECT.md") as f:
        lines = f.readlines()
    assert len(lines) <= 80, f"PROJECT.md มี {len(lines)} lines (เกิน 80)"

def test_project_md_has_command_table():
    # PROJECT.md ต้องมี Commands section
    content = open("zie-framework/PROJECT.md").read()
    assert "## Commands" in content

def test_project_md_has_knowledge_links():
    content = open("zie-framework/PROJECT.md").read()
    assert "project/architecture.md" in content
    assert "project/components.md" in content
    assert "project/decisions.md" in content

def test_architecture_md_exists():
    assert os.path.exists("zie-framework/project/architecture.md")

def test_components_md_exists():
    assert os.path.exists("zie-framework/project/components.md")

def test_decisions_md_exists():
    assert os.path.exists("zie-framework/project/decisions.md")

def test_decisions_md_append_only_note():
    content = open("zie-framework/project/decisions.md").read()
    assert "Superseded" in content or "append-only" in content.lower()

def test_retro_has_knowledge_sync():
    content = open("commands/zie-retro.md").read()
    assert "project/components.md" in content
    assert "supersedes" in content
```

**Run:** `make test-unit` → all 9 tests pass

---

## Notes

- Tasks 1–4 ทำ parallel ได้ (create new files)
- Task 5 (update zie-retro) ทำหลัง task 4 เสร็จ (เพื่อ reference decisions.md)
- Task 6 (templates) ต้องอ่าน templates/ ก่อน — อาจไม่มี action ถ้า zie-init ใช้ inline
- Task 7 (tests) รอหลัง 1–6 เสร็จ
