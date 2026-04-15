---
description: Plan a backlog item — draft implementation plan, present for approval, move to Ready lane.
argument-hint: "[slug...] — one or more backlog item slugs (e.g. zie-plan feature-x feature-y)"
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Skill, Agent, TaskCreate
model: sonnet
effort: low
---

# /plan — Spec → Draft Plan → Review → Approve → Ready

<!-- preflight: full -->

Draft implementation plans for approved backlog specs and get Zie's approval
before building. Supports multiple items in parallel.

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (checks Now lane — warns if WIP active).

## ไม่มี argument — แสดงรายการ backlog

1. If called with no args:
   - Read `zie-framework/ROADMAP.md` → list all Next items with index numbers.
   - Filter to items with an **approved spec**: check
     `zie-framework/specs/*-<slug>-design.md` for a file containing slug **and**
     `approved: true` in its frontmatter.
   - If Next is empty → print "No backlog items. Run /backlog first." STOP
   - If no Next items have an approved spec → print "No approved specs found.
     Run /spec SLUG first." STOP:
   - Ask: "Which items to plan? Enter numbers (e.g. 1, 3)"

## ตรวจสอบ spec ก่อน plan (ทุก slug)

For each resolved slug (whether from args or from no-args selection):

1. Glob `zie-framework/specs/*-<slug>-design.md`.
   - If no file found → print:
     `STOP: No spec found for '<slug>'. Run /spec <slug> first.`
   - If file found → read frontmatter.
2. Check `approved: true` in frontmatter.
   - If `approved: false` or key absent → print:
     `STOP: Spec exists but not approved. Complete /spec <slug> review first.`
   - If `approved: true` → gate passes, continue.

## ร่าง plan สำหรับ slug ที่เลือก

1. If `zie_memory_enabled=true` — READ (1 batch query per slug):
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[shipped,retro,bug,decision] limit=20`
   - Returns approaches, pain points, ADRs, known bugs in one round-trip.
   - Bake key findings into plan as a "## Context from brain" section.
   - /implement will read this section — no need to re-recall at build time.

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

<!-- context: ROADMAP already injected by session-resume/subagent-context hook; re-read only if Now lane may have changed -->

<!-- context-load: adrs + project context -->

Invoke `Skill(zie-framework:load-context)` → result available as `context_bundle`
(calls `write_adr_cache`, bundles `adr_cache_path` + `decisions/` + `project/context.md`).
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
   - **Auto-approve** — when plan-reviewer returns ✅ APPROVED, proceed automatically
     (no user confirmation required — reviewer verdict IS the gate):
   - Add `spec:` field to plan frontmatter via Edit (still `approved: false`):

     ```yaml
     spec: specs/<spec-filename>.md
     ```

   - Run Bash to flip to approved (reviewer-gate blocks Write/Edit path):

     ```bash
     python3 hooks/approve.py zie-framework/plans/YYYY-MM-DD-<slug>.md
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

     Display: `"✓ Plan approved & moved to Ready. Run /implement to start building."`
     Override options (send as next message if needed):
     - **re-draft** → revise plan and re-run plan-reviewer gate (keeps pending state)
     - **drop** → leave item in Next unchanged, skip this plan

   - **If plan-reviewer returns ❌ Issues Found**: ask user: "Fix and re-run, re-draft, or drop?" (old flow preserved)

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

   Next: Run /implement to start building.
   ```

## ขั้นตอนถัดไป

→ `/implement`


