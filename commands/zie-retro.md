---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
---

# /zie-retro — Retrospective + ADRs + Brain Storage

Post-release or end-of-session retrospective. Documents what happened, extracts
architectural decisions as ADRs, updates ROADMAP, and stores learnings in the
brain.

## ตรวจสอบก่อนเริ่ม

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project, zie_memory_enabled.
3. Read `zie-framework/ROADMAP.md` → current state.
4. Get git context:
   - `git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list
     --max-parents=0 HEAD)..HEAD --oneline` → changes since last tag
   - `git log -20 --oneline` → recent activity

## Steps

### รวบรวม context

1. If `zie_memory_enabled=true`:
   - `recall project=<project> tags=[wip, build-learning, shipped] limit=20`
   - Use recalled learnings and decisions as context for retro analysis.

2. Count ADR files in `zie-framework/decisions/` → get next ADR number.

### วิเคราะห์และสรุป

Invoke `Skill(zie-framework:retro-format)` to structure the retrospective:

- **What shipped**: list of features/fixes in this release or session.
- **What worked well**: patterns, approaches, tools that helped.
- **What was painful**: friction points, unexpected complexity.
- **Key decisions made**: any significant architectural or design choices.
- **Patterns to remember**: techniques, approaches worth storing in brain.

### บันทึก ADRs

For each significant architectural decision identified:

- Create `zie-framework/decisions/ADR-<NNN>-<slug>.md` from ADR template:

  ```text
  # ADR-<NNN>: <Title>
  Date: YYYY-MM-DD
  Status: Accepted

  ## Context
  <what situation required this decision>

  ## Decision
  <what was decided>

  ## Consequences
  <what this means going forward — positive and negative>
  ```

- Only create ADR for decisions with lasting consequences. Skip routine
  implementation choices.

### อัปเดต project knowledge

หลัง ADRs เขียนเสร็จ:

- ตรวจก่อน: ถ้า `zie-framework/project/` ไม่มี → skip knowledge sync พร้อม note:
  "Project knowledge docs not found — run /zie-resync to generate them."
- อ่าน `zie-framework/project/components.md` → อัปเดต components ที่เปลี่ยน
  behavior ใน session นี้
- อ่าน `zie-framework/project/decisions.md` → append ADRs ใหม่
- ถ้า architecture เปลี่ยน → อัปเดต `zie-framework/project/architecture.md`
- ถ้า `zie_memory_enabled=true`: `remember "Project snapshot: <version>.
  Components changed: <list>. Decisions: <new ADR slugs>."
  tags=[project-knowledge, zie-framework, <version>]
  supersedes=[project-knowledge, zie-framework]`

### อัปเดต ROADMAP

Update `zie-framework/ROADMAP.md`:

- Ensure all shipped items are in "Done" with date.
- If running **standalone** (not called from /zie-release): re-read "Next"
  section, re-prioritize based on what was learned, and ask Zie: "Anything
  to add to Next or Later?"
- If called **from /zie-release**: skip interactive re-prioritize prompt
  (release already handled ROADMAP). Print: "Run /zie-retro standalone to
  review and reprioritize backlog."

### บันทึกสู่ brain

If `zie_memory_enabled=true`:

- Store P1 preferences (what worked): `remember "<what worked>. Preference:
  always use this approach for <context>." priority=preference tags=[retro,
  <slug>]`
- Store P2 project learnings: `remember "Retro <version>: <key learning>.
  Decision: <ADR slug>." priority=project tags=[retro, <project>]
  project=<project>`
- Downvote any memories that turned out to be incorrect via `downvote_memory`.

### สรุปผล

Print:

```text
Retrospective complete

Shipped  : <N features/fixes>
ADRs     : <list of ADR files created>
ROADMAP  : Done section updated

Learnings stored: <N memories>

Next session: Run /zie-status to see current state.
```

## Notes

- Can run standalone (not just after /zie-release): `/zie-retro` at any time
- When called from /zie-release: skips interactive backlog re-prioritize
- Lightweight when nothing major happened — won't create empty ADRs
- ADR numbers are auto-incremented from existing files in
  `zie-framework/decisions/`
