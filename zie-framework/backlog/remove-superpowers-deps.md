# Remove All Superpowers Dependencies

## Problem

zie-framework ยังมี references ถึง `superpowers:*` skills อยู่ใน commands,
hooks, config, และ docs ทำให้ framework ไม่ self-contained — ถ้าไม่มี
superpowers plugin ติดตั้ง บาง path จะพัง หรือ fallback ไปใช้ inline
brainstorming ที่ด้อยกว่า

Skills ที่จำเป็น (`spec-design`, `write-plan`, `debug`, `verify`) ถูก fork
มาแล้ว แต่ commands ยังไม่ได้อัปเดต

## Goal

zie-framework ทำงานได้สมบูรณ์โดยไม่ต้องมี superpowers plugin — ลบ
`superpowers_enabled` flag และ conditional branching ทั้งหมด

## Scope

### Commands ที่ต้องอัปเดต

- `commands/zie-plan.md` — ลบ `superpowers_enabled` reference (line 15)
- ตรวจสอบ commands อื่นๆ ที่อาจมี `superpowers_enabled` guard

### Hooks

- `hooks/session-resume.py` — ลบ `superpowers_enabled` ออกจาก config
  reading (line 69)

### Config

- `commands/zie-init.md` — ลบ `"superpowers_enabled"` field ออกจาก `.config`
  template
- `.config` ที่ existing projects — field นี้จะกลายเป็น unused (backward
  compatible, แค่ ignore)

### Skills

- `skills/spec-design/SKILL.md` — ตรวจสอบไม่มี `superpowers:*` reference
- `skills/write-plan/SKILL.md` — ตรวจสอบ
- `skills/debug/SKILL.md` — ตรวจสอบ
- `skills/verify/SKILL.md` — ตรวจสอบ

### Tests

- `tests/unit/test_fork_superpowers_skills.py` — update assertions ให้สอดคล้อง
  กับ command ใหม่

### Docs

- `CLAUDE.md` — ลบ "Graceful degradation (superpowers)" ออก
- `README.md` — ลบ row superpowers จาก optional dependencies table
- `zie-framework/project/decisions.md` — เพิ่ม ADR ว่า fork เสร็จแล้ว
  superpowers ไม่ required อีกต่อไป

## Out of Scope

- ลบ skills ที่ fork มา (เก็บไว้ใช้งาน)
- เปลี่ยน behavior ของ commands ใดๆ — แค่ลบ conditional branching
