---
description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
---

# /zie-plan — Backlog → Draft Plan → Approve → Ready

Draft implementation plans for backlog items and get Zie's approval before
building. Supports multiple items in parallel (max 4 agents).

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → zie_memory_enabled.

## ไม่มี argument — แสดงรายการ backlog

1. If called with no args:
   - Read `zie-framework/ROADMAP.md` → list all Next items with index numbers.
   - If Next is empty → print "No backlog items. Run /zie-idea first." and stop.
   - Ask: "Which items to plan? Enter numbers (e.g. 1, 3)"

## ร่าง plan สำหรับ slug ที่เลือก

1. If `zie_memory_enabled=true` — READ (1 batch query per slug):
   - `recall project=<project> domain=<domain> tags=[shipped,retro,bug,decision] limit=20`
   - Returns approaches, pain points, ADRs, known bugs in one round-trip.
   - Bake key findings into plan as a "## Context from brain" section.
   - /zie-build will read this section — no need to re-recall domain context at
     build time.

2. If multiple slugs → spawn parallel agents (max 4) to draft plans
   simultaneously:
   - Each agent: reads `zie-framework/backlog/<slug>.md` → drafts plan → returns
   - Plans saved to `zie-framework/plans/<slug>.md` with no frontmatter yet
     (pending)

3. If single slug → draft plan inline.

## ขออนุมัติ plan (ทีละ plan)

1. For each drafted plan:
   - Display plan to Zie.
   - Ask: "Approve this plan? (yes / re-draft / drop back to Next)"
   - **yes** → add frontmatter to plan file:

     ```yaml
     ---
     approved: true
     approved_at: YYYY-MM-DD
     backlog: backlog/<slug>.md
     ---
     ```

     Move item in `zie-framework/ROADMAP.md` from Next → Ready:
     `- [ ] <feature name> — [plan](plans/<slug>.md) ✓ approved`
   - **re-draft** → revise plan and re-present (keeps pending state)
   - **drop** → leave item in Next unchanged, skip this plan

2. If `zie_memory_enabled=true` — WRITE after approval:
   - `remember "Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>. Key
     decisions: [<d1>]." tags=[plan, <project>, <domain>]`

## สรุปผล

1. Print:

   ```text
   Plans processed: <N>

   Approved → Ready : <list of approved slugs>
   Re-drafted       : <list if any>
   Dropped → Next   : <list if any>

   Next: Run /zie-build to start building.
   ```

## ขั้นตอนถัดไป

→ `/zie-build` — เริ่ม implement feature ที่อนุมัติแล้ว
→ `/zie-status` — ดูภาพรวม

## Notes

- Plan files live at `zie-framework/plans/<slug>.md`
- Pending plan = no `approved` key in frontmatter
- Approved plan = `approved: true` + `approved_at` in frontmatter
- Max 4 parallel agents when multiple slugs provided
- Rejection path: re-draft (stays pending) or drop (returns to Next)
