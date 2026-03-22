---
description: Turn a backlog item into a written spec with Acceptance Criteria. Second stage of the SDLC pipeline.
argument-hint: "[slug] — backlog item slug (e.g. zie-spec add-csv-export)"
allowed-tools: Read, Write, Glob, Skill
---

# /zie-spec — Backlog → Spec

Write a design spec for a backlog item. Invokes spec-design skill with
reviewer loop. Output lives in `zie-framework/specs/`.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project_type, zie_memory_enabled.
3. Read `zie-framework/ROADMAP.md` → check Now lane.
   - If a `[ ]` item exists → warn: "WIP active: `<feature>`. Specs can be
     written in parallel but focus is split. Continue? (yes/no)"
   - If no → stop.

## Steps

1. If slug provided → read `zie-framework/backlog/<slug>.md`.
   If not → read ROADMAP.md Next section, list items, ask: "Which to
   spec? Enter number."
2. Pass to `Skill(zie-framework:spec-design)`:
   - Backlog content as context
   - `zie_memory_enabled` from .config
   - The skill asks clarifying questions, proposes approaches, presents
     design, writes spec, runs spec-reviewer loop, records approval in
     frontmatter, and returns without auto-invoking write-plan.
   - Spec saved to `zie-framework/specs/YYYY-MM-DD-<slug>-design.md`
     with `approved: true` in frontmatter once reviewed.
3. Print:

   ```text
   Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md

   Next: /zie-plan <slug> to create the implementation plan.
   ```

## ขั้นตอนถัดไป

→ `/zie-plan <slug>` — เมื่อ spec approved แล้ว
→ `/zie-retro` — ถ้า spec session ยาวและมี learnings ที่ควรบันทึก
→ `/zie-status` — ดูภาพรวม

## Notes

- Always spec-first — never skips to plan without an approved spec
- spec-design writes `approved: true` frontmatter after reviewer passes
- /zie-plan checks this frontmatter — draft specs do not proceed to plan
- spec-design does NOT auto-invoke write-plan (commands are control plane)
