---
description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
model: sonnet
effort: medium
---

# /zie-plan — Spec → Draft Plan → Review → Approve → Ready

Draft implementation plans for approved backlog specs and get Zie's approval
before building. Supports multiple items in parallel.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → zie_memory_enabled.
3. Read `zie-framework/ROADMAP.md` → check Now lane.
   - If a `[ ]` item exists in Now → warn: "WIP active: `<feature>`. Planning
     new items while one is in progress splits focus. Continue? (yes/no)"
   - If no → stop.

## ไม่มี argument — แสดงรายการ backlog

1. If called with no args:
   - Read `zie-framework/ROADMAP.md` → list all Next items with index numbers.
   - Filter to items with an **approved spec**: check
     `zie-framework/specs/*-<slug>-design.md` for a file containing slug **and**
     `approved: true` in its frontmatter.
   - If Next is empty → print "No backlog items. Run /zie-backlog first." STOP.
   - If no Next items have an approved spec → print "No approved specs found.
     Run /zie-spec SLUG first." STOP.
   - Ask: "Which items to plan? Enter numbers (e.g. 1, 3)"

## ตรวจสอบ spec ก่อน plan (ทุก slug)

For each resolved slug (whether from args or from no-args selection):

1. Glob `zie-framework/specs/*-<slug>-design.md`.
   - If no file found → print:
     `⛔ No spec found for '<slug>'. Run /zie-spec <slug> first.`
     STOP — do not proceed with this slug.
   - If file found → read frontmatter.
2. Check `approved: true` in frontmatter.
   - If `approved: false` or key absent → print:
     `⛔ Spec exists but not approved. Complete /zie-spec <slug> review first.`
     STOP — do not proceed with this slug.
   - If `approved: true` → gate passes, continue.

## ร่าง plan สำหรับ slug ที่เลือก

1. If `zie_memory_enabled=true` — READ (1 batch query per slug):
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[shipped,retro,bug,decision] limit=20`
   - Returns approaches, pain points, ADRs, known bugs in one round-trip.
   - Bake key findings into plan as a "## Context from brain" section.
   - /zie-implement will read this section — no need to re-recall at build time.

2. If multiple slugs → spawn parallel Agents simultaneously:
   - **Dependency hint:** If multiple slugs share a common output directory
     or file pattern, add `<!-- depends_on: slug-1 -->` to serialize them.
   - Each agent receives:
     - `zie-framework/backlog/<slug>.md` — problem + motivation
     - `zie-framework/specs/*-<slug>-design.md` — approved spec (exact glob
       match `*-<slug>-design.md`, first match wins)
     - Brain context from step 1
   - Each agent: drafts plan using `Skill(zie-framework:write-plan)` → returns
   - Plans saved to `zie-framework/plans/YYYY-MM-DD-<slug>.md` (no frontmatter
     yet, pending)

3. If single slug → invoke `Skill(zie-framework:write-plan)` inline with:
   - Backlog file + spec file + brain context

## โหลด context bundle (ครั้งเดียวต่อ session)

<!-- context-load: adrs + project context -->

Before invoking any reviewer, load shared context once:

1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
   (list of `{filename, content}` pairs; empty list if directory missing)
2. Read `zie-framework/project/context.md` → store as `context_content`
   (string; empty string if file missing)
3. Bundle as `context_bundle = { adrs: adrs_content, context: context_content }`

Pass `context_bundle` to every reviewer invocation below.

## plan-reviewer gate (ทุก plan ต้องผ่าน)

For each drafted plan `[Plan {N}/{total}]`, before showing to Zie:

Print: `[Plan {N}/{total}] plan-reviewer pass`

1. Invoke `@agent-plan-reviewer` with:
   <!-- fallback: Skill(zie-framework:plan-reviewer) -->
   - Path to plan file
   - Path to spec file (`zie-framework/specs/*-<slug>-design.md`)
   - `context_bundle` (pre-loaded ADRs + context.md)
2. If ❌ Issues Found → fix ALL issues listed → invoke reviewer once more
   as a confirm pass (pass 2 of 2).
   - If confirm pass returns ✅ APPROVED → proceed to Zie approval below.
   - If confirm pass returns ❌ Issues Found again → surface to Zie:
     "Reviewer found persistent issues after fix pass. Review plan manually."
   Max 2 total iterations: initial scan (pass 1) + confirm pass (pass 2).
   If 0 issues on initial scan → APPROVED immediately, no confirm pass needed.
3. If ✅ Approved on initial scan → proceed to Zie approval below.

## ขออนุมัติ plan (ทีละ plan)

1. For each reviewer-approved plan:
   - Display plan to Zie.
   - Ask: "Approve this plan? (yes / re-draft / drop back to Next)"
   - **yes** → add frontmatter to plan file:

     ```yaml
     ---
     approved: true
     approved_at: YYYY-MM-DD
     backlog: backlog/<slug>.md
     spec: specs/<spec-filename>.md
     ---
     ```

     **Atomically move** item in `zie-framework/ROADMAP.md` from Next → Ready:
     1. **Remove from Next**: find and DELETE the line matching `- [ ] <title>`
        (or `- [x] <title>`) in the Next section — this line must be removed.
     2. **Guard**: if a line matching `<title>` already exists in Ready →
        skip add, print "Already in Ready: <slug>" and continue.
     3. **Add to Ready**: insert `- [ ] <title> — [plan](plans/YYYY-MM-DD-<slug>.md) ✓`
        in the correct priority group (CRITICAL / HIGH / MEDIUM / LOW).

     Commit plan + ROADMAP:

     ```bash
     git add zie-framework/plans/YYYY-MM-DD-<slug>.md \
       zie-framework/ROADMAP.md
     git commit -m "plan: <slug>"
     ```

   - **re-draft** → revise plan and re-run plan-reviewer gate before
     re-presenting (keeps pending state)
   - **drop** → leave item in Next unchanged, skip this plan

2. If `zie_memory_enabled=true` — WRITE after approval:
   - Complexity: ≤3 tasks = S, 4–7 = M, 8+ = L
   - Call `mcp__plugin_zie-memory_zie-memory__remember`
     with `"Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>. Key decisions: [<d1>]." tags=[plan, <project>, <domain>]`

## สรุปผล

1. Print:

   ```text
   Plans processed: <N>

   Approved → Ready    : <list of approved slugs>
   Still pending       : <list if any — re-draft queued>
   Dropped → Next      : <list if any>

   Next: Run /zie-implement to start building.
   ```

## ขั้นตอนถัดไป

→ `/zie-implement` — เริ่ม implement feature ที่อนุมัติแล้ว
→ `/zie-status` — ดูภาพรวม

## Notes

- Plan files: `zie-framework/plans/YYYY-MM-DD-<slug>.md`
- Spec match: exact glob `zie-framework/specs/*-<slug>-design.md`
- Pending plan = no `approved` key in frontmatter
- Approved plan = `approved: true` + `approved_at` in frontmatter
- plan-reviewer runs automatically before every Zie approval prompt
- Rejection path: re-draft (stays pending, re-runs reviewer) or drop (Next)
