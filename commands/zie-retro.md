---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /zie-retro — Retrospective + ADRs + Brain Storage

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
     `agent_type`. Print table: Type | Count | Last Agent ID | Last Message.
   - If file does not exist or `FileNotFoundError`: print
     "No subagent activity recorded this session." and continue.
   - If a line fails JSON parse: skip silently.

3. Count ADR files in `zie-framework/decisions/` → get next ADR number.

4. **ADR auto-summarization** — if count > 30: keep 10 most-recent;
   `generate_summary_table(to_compress)` → write `decisions/ADR-000-summary.md`,
   delete compressed files. ≤30 → skip.

### สร้าง compact summary

Build compact JSON bundle for retro-format fork:

```json
{
  "shipped": ["<commit message 1>", "<commit message 2>"],
  "commits_since_tag": "<count from git log>",
  "pain_points": [],
  "decisions": [],
  "done_section_current": "<Done section text — pre-extracted for agents>"
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

<!-- fallback: if Agent tool unavailable, call Skill(zie-framework:retro-format) and Skill(zie-framework:docs-sync-check) inline -->

### รวมผลลัพธ์ forks

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

### บันทึก ADRs + อัปเดต ROADMAP (parallel)

Launch both as parallel Agent calls — two Agent tool uses in one message. No write conflict (different paths):

1. `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt="Write ADRs: {decisions_json}. Next ADR: {next_adr_n}. Path: zie-framework/decisions/ADR-<NNN>-<slug>.md. Done context: {done_section_current}")` — creates ADR files, printing `[ADR N/total]` for each
2. `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt="Update ROADMAP Done section: {shipped_items}. Done context: {done_section_current}. File: zie-framework/ROADMAP.md. Re-read file before writing; replace ## Done block to next --- (or EOF).")` — updates Done lane in `zie-framework/ROADMAP.md`

Await both. Then proceed to brain store.

**Failure mode:** If either Agent fails → skip brain store. Do not retry.

<!-- fallback: if Agent tool unavailable, run ADR write and ROADMAP update inline (blocking, sequential). ADR format: see zie-framework/decisions/ for examples. Only create for decisions with lasting consequences. ROADMAP: move shipped items to Done with date; if standalone ask Zie to re-prioritize Next. -->

### อัปเดต project knowledge

Print: "Updating knowledge docs..."

- ถ้า `project/` ไม่มี → skip + note "run /zie-resync to generate them"
- อ่าน `project/components.md` → อัปเดต components ที่เปลี่ยน behavior
- ถ้า architecture เปลี่ยน → อัปเดต `project/architecture.md`

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

