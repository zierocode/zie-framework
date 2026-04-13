---
tags: [feature]
---

# Context Loader Sprint — Auto-load zie-framework context at session start

## Problem

Claude Code ต้องลองผิดลองถูกกับ commands/skills ของ zie-framework เพราะไม่มี context กลางที่โหลดอัตโนมัติ ทำให้:
- ไม่รู้ว่า command ไหนใช้ agent mode อะไร
- ต้องอ่าน error ก่อนถึงรู้ว่าต้องแก้ที่ไหน
- คนนอกที่เอา plugin ไปใช้ต้องศึกษา docs นาน

## Motivation

ทำให้ zie-framework "crystal clear" สำหรับ Claude Code ตั้งแต่เริ่ม session:
- Context โหลดอัตโนมัติ — ไม่ต้องเรียก load-context ในทุก command
- Intent detection รู้เองว่า user อยากใช้ zie-framework
- Lean — command/skill ไม่ต้องแก้โค้ดเพิ่ม
- Token-efficient — cache context, ไม่อ่าน disk ซ้ำ

## Rough Scope

**In:**
- hooks/zie-context-loader.py — scan agents/commands/skills, build context
- hooks/session-start.py — call context loader if zie-framework project
- hooks/intent-sdlc.py — inject context hint for zie-framework commands
- Standard headers for agents/*.md, commands/*.md, skills/*/SKILL.md
- make resync — auto-generate context.md

**Out:**
- MCP server config (ไม่จำเป็น — ใช้ hook แทน)
- แก้ command/skill ทุกตัว (context โหลดอัตโนมัติที่ session start)

<!-- priority: HIGH -->
<!-- depends_on: none -->
