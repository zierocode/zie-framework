---
tags: [bug]
---

# Fix /release skill vs make release conflict

## Problem

`/release` skill และ `make release` ทำ git operations ซ้ำกัน:

| Operation | /release skill | make release | ผลกระทบ |
|-----------|----------------|--------------|----------|
| Bump VERSION | Step 2 | Line 114 (`$(MAKE) bump`) | ✅ OK (ทำครั้งเดียว) |
| Commit bump | Step 7 | Line 116 | ❌ ซ้ำ |
| Merge dev→main | Step 8 (ภายใน make release) | Line 118 | ❌ ซ้ำ |
| Create tag | Step 8 (ภายใน make release) | Line 119 | ❌ Tag already exists |
| Push main+tags | Step 8 (ภายใน make release) | Line 120 | ❌ ซ้ำ |
| Merge main→dev | Step 8 (ภายใน make release) | Line 123 | ❌ ซ้ำ |

**Root cause:** `/release` skill line 162 เรียก `make release NEW=<version>` ซึ่งทำทุกอย่างที่ skill ทำไปแล้ว

## Motivation

1. **Hotfix ล้มเหลว** — tag already exists error
2. **Retro outputs ไม่ commit** — ROADMAP.md, ADR-000-summary.md ยังไม่ commit แต่ `make release` ต้องการ clean tree
3. **Confusing workflow** — ไม่ชัดเจนว่าใครทำอะไร

## Rough Scope

**In:**
- แก้ `commands/release.md` Step 8 — แทนที่จะเรียก `make release` ให้ทำ git ops เอง + เรียกแค่ `make _publish`
- หรือแก้ `Makefile` line 106-125 — ให้เป็น no-op + warning

**Out:**
- แก้ test files (ถ้ามี)

## Approach (Recommended)

**Done:**
1. แก้ `commands/release.md` Step 8 — ทำ git ops โดยตรง + เรียก `make _publish`
2. เพิ่ม `make _publish` target ใน `Makefile` (no-op, override ใน `Makefile.local`)
3. เพิ่ม deprecation warning ใน `make release` target

<!-- priority: HIGH -->
<!-- depends_on: none -->
<!-- status: IMPLEMENTED -->
