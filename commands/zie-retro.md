---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /zie-retro — Retrospective + ADRs + Brain Storage

Post-release or end-of-session retrospective. Documents what happened, extracts
architectural decisions as ADRs, updates ROADMAP, and stores learnings in the
brain.

## ตรวจสอบก่อนเริ่ม

**Live context (injected at command load):**

Commits since last tag:
!`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

Recent activity window:
!`git log -20 --oneline`

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` → project, zie_memory_enabled.
3. Targeted ROADMAP reads (do not read full file):
   - **Now section**: Grep `## Now` in `zie-framework/ROADMAP.md` → Read from
     that line to next `---` separator.
   - **Done section (recent)**: Grep `## Done` → Read from that line, limit
     to ~20 lines (recent shipped items only — full Done history not needed).
4. Print: "Analyzing git log..."
   Git context is available in the injected snapshots above ("Commits since last
   tag" and "Recent activity window"). No additional Bash call needed.

## Steps

### รวบรวม context

1. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip, build-learning, shipped] limit=20`
   - Use recalled learnings and decisions as context for retro analysis.

2. **Subagent Activity** — read subagent log for this session:

   - Resolve log path: `project_tmp_path("subagent-log", project)` →
     `/tmp/zie-<project>-subagent-log`
   - If file exists: read line-by-line, parse each JSON record, group by
     `agent_type`. Print summary:

     ```text
     Subagent Activity This Session
     ─────────────────────────────────────────────────────
     Type              Count   Last Agent ID   Last Message
     spec-reviewer     2       abc-123         "The spec lo..."
     plan-reviewer     1       def-456         "Plan looks s..."
     ─────────────────────────────────────────────────────
     ```

   - If file does not exist or `FileNotFoundError`: print
     "No subagent activity recorded this session." and continue.
   - If a line fails JSON parse: skip it silently (partial log is still useful).

3. Count ADR files in `zie-framework/decisions/` → get next ADR number.

### สร้าง compact summary

Build compact JSON bundle for retro-format fork:

```json
{
  "shipped": ["<commit message 1>", "<commit message 2>"],
  "commits_since_tag": "<count from git log>",
  "pain_points": [],
  "decisions": [],
  "roadmap_done_tail": "<last 5 lines of Done section>"
}
```

### Invoke Background Agents (concurrent)

Invoke both Agents **simultaneously** with `run_in_background=true` — do NOT wait for either before starting:

**TaskCreate** — create tasks before launching Agents:
```python
TaskCreate(subject="Format retrospective summary", description="Run retro-format to structure retro output", activeForm="Formatting retro summary")
TaskCreate(subject="Check docs sync", description="Check CLAUDE.md/README.md against changed files", activeForm="Checking docs sync")
```

**Invoke Agents:**
1. `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt="Format retrospective summary from: {compact_json}")`
2. `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True, prompt="Check docs sync for changed files: {changed_files}")`

Print: "Running retro-format and docs-sync-check in background. Use /tasks to see progress."

**Wait for completion:**
- Wait for both Agents to complete (via task completion notifications or TaskOutput polling)
- **TaskUpdate** — mark both tasks as "completed" when Agents finish

Collect results and continue to "บันทึก ADRs" step.

<!-- fallback: if Agent tool unavailable or subagent_type not found,
     call Skill(zie-framework:retro-format) and Skill(zie-framework:docs-sync-check) inline (blocking) -->

### บันทึก ADRs

For each significant architectural decision identified (`[ADR {N}/{total}]`):

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

Print: "Updating knowledge docs..."

หลัง ADRs เขียนเสร็จ:

- ตรวจก่อน: ถ้า `zie-framework/project/` ไม่มี → skip knowledge sync พร้อม note:
  "Project knowledge docs not found — run /zie-resync to generate them."
- อ่าน `zie-framework/project/components.md` → อัปเดต components ที่เปลี่ยน
  behavior ใน session นี้
- อ่าน `zie-framework/project/context.md` → เป็น background เท่านั้น (read-only)
- เขียน ADR ใหม่แต่ละอันเป็นไฟล์แยกใน `zie-framework/decisions/ADR-NNN-<slug>.md`
  (ใช้ NNN = running number ถัดจากไฟล์ล่าสุดใน decisions/)
- ถ้า architecture เปลี่ยน → อัปเดต `zie-framework/project/architecture.md`

### รวมผลลัพธ์ forks

Collect both fork results (forks ran while ADRs were being written above):

- **retro-format result** → print the five structured retro sections.
- **docs-sync-check result** → if `claude_md_stale=true`: update `CLAUDE.md` now
  and print `"Updated CLAUDE.md: added <X>, removed <Y>"`. If `readme_stale=true`:
  update `README.md` and print `"Updated README.md: added <X>, removed <Y>"`.
  If both in sync → print "CLAUDE.md in sync | README.md in sync".
- If either fork returned an error → print the error and continue.
  Retro is not blocked by fork failures.

- ถ้า `zie_memory_enabled=true`: Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"Project snapshot: <version>. Components changed: <list>. Decisions: <new ADR slugs>."`
  `tags=[project-knowledge, zie-framework, <version>] supersedes=[project-knowledge, zie-framework]`

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

- Store P1 preferences (what worked): Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"<what worked>. Preference: always use this approach for <context>." priority=preference tags=[retro, <slug>]`
- Store P2 project learnings: Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"Retro <version>: <key learning>. Decision: <ADR slug>." priority=project tags=[retro, <project>] project=<project>`
- Downvote incorrect memories via `mcp__plugin_zie-memory_zie-memory__downvote_memory`.

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

### Suggest next

After printing the retrospective summary, read `zie-framework/ROADMAP.md` and
extract all items in the **Next** lane.

**Ranking order:**
1. Priority: Critical first, then High, then Medium, then unlabelled.
2. Retro-theme alignment: items whose title or description overlaps with pain
   points or themes identified in the retro write-up rank higher within the
   same priority tier.

**Output — items found (print top 1–3):**

```text
Suggested next
──────────────────────────────────────────
1. <slug> — <title> [<priority>]
   Run: /zie-plan <slug> to start

2. <slug> — <title> [<priority>]
   Run: /zie-plan <slug> to start

3. <slug> — <title> [<priority>]
   Run: /zie-plan <slug> to start
──────────────────────────────────────────
```

**Output — Next lane is empty:**

```text
Backlog is empty — add items with /zie-backlog
```

This step is advisory only. Nothing is automatically started.

## Notes

- Can run standalone (not just after /zie-release): `/zie-retro` at any time
- When called from /zie-release: skips interactive backlog re-prioritize
- Lightweight when nothing major happened — won't create empty ADRs
- ADR numbers are auto-incremented from existing files in
  `zie-framework/decisions/`
