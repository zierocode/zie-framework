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
3. Targeted ROADMAP reads: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines only.
4. Print: "Analyzing git log..." — git context already injected above, no Bash needed.

## Steps

### รวบรวม context

1. If `zie_memory_enabled=true`:
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip, build-learning, shipped] limit=20`
   - Use recalled learnings and decisions as context for retro analysis.

2. **Subagent Activity** — read `project_tmp_path("subagent-log", project)`. If exists: parse JSON lines, group by `agent_type`, print Type/Count table. If missing → "No subagent activity recorded." Skip bad lines silently.

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

Invoke both simultaneously — `run_in_background=true`:

```python
TaskCreate(subject="Format retrospective summary", activeForm="Formatting retro summary")
TaskCreate(subject="Check docs sync", activeForm="Checking docs sync")
```

**Invoke Agents:**
1. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Format retrospective summary. You are a retro format assistant. Given compact_json: {compact_json}. Structure output as five sections: (1) สิ่งที่ Ship ออกไป — list shipped features/fixes; (2) สิ่งที่ทำงานได้ดี — what worked well; (3) สิ่งที่เจ็บปวด — pain points; (4) การตัดสินใจสำคัญ — key decisions with lasting consequences; (5) Pattern ที่ควรจำ — reusable techniques. ADR format: Status, Context, Decision, Consequences. Return full five-section retro text.")`
2. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Check docs sync for changed files: {changed_files}. Scan zie-framework/commands/*.md (extract /zie-* command names), zie-framework/skills/*/*.md (extract skill names), zie-framework/hooks/*.py (extract hook events). Check CLAUDE.md Development Commands section lists all commands. Check README.md skills table lists all skills. Return JSON: { 'in_sync': bool, 'missing_from_docs': [...], 'extra_in_docs': [...], 'details': str }")`

Print: "Running retro-format and docs-sync-check in background. Use /tasks to see progress."
Wait for both → **TaskUpdate** completed.

<!-- fallback: if Agent unavailable, call Skill(zie-framework:retro-format) and Skill(zie-framework:docs-sync-check) inline -->

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

1. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Write ADRs for decisions made this session. Context: done_section_current={done_section_current}. For each decision in {decisions_json}: create file zie-framework/decisions/ADR-<NNN>-<slug>.md with 5-section format: Status (Accepted), Context (1-3 sentences), Decision (1-3 sentences), Consequences (Positive/Negative/Neutral), Alternatives. Next ADR number: {next_adr_n}. Print [ADR N/total] for each file created.")` — creates ADR files, printing `[ADR N/total]` for each
2. `Agent(subagent_type="general-purpose", run_in_background=True, prompt="Update ROADMAP Done section. Read zie-framework/ROADMAP.md. Find ## Done section. Move shipped items from {shipped_items} to Done with date and version tag. Replace ## Done block (from heading to next --- separator or EOF). Done context for reference: {done_section_current}.")` — updates Done lane in `zie-framework/ROADMAP.md`

Await both. Then proceed to brain store.

**Failure mode:** If either Agent fails → skip brain store. Do not retry.

<!-- fallback: if Agent tool unavailable, run ADR write and ROADMAP update inline (blocking, sequential). ADR format: see zie-framework/decisions/ for examples. Only create for decisions with lasting consequences. ROADMAP: move shipped items to Done with date; if standalone ask Zie to re-prioritize Next. -->

### Auto-commit retro outputs

After ADR + ROADMAP agents complete, auto-commit:

```bash
git add zie-framework/decisions/*.md zie-framework/project/components.md
git commit -m "chore: retro v${VERSION}"
git push origin dev
```

If git push fails → log error and display:
`"⚠️ Retro git push failed. Manual push: git push origin dev"` then continue (non-blocking).
On success → print `"✓ Retro complete. Committed <hash>"`

### อัปเดต project knowledge

Print: "Updating knowledge docs..." — if `project/` missing → skip.
Update `project/components.md` for changed behavior; `project/architecture.md` if architecture changed.

### บันทึกสู่ brain

If `zie_memory_enabled=true`:
- P1 preferences: `remember` `"<what worked>. Preference: always use this approach for <context>." priority=preference tags=[retro, <slug>]`
- P2 learnings: `remember` `"Retro <version>: <key learning>. Decision: <ADR slug>." priority=project tags=[retro, <project>]`
- Downvote incorrect: `mcp__plugin_zie-memory_zie-memory__downvote_memory`.

### สรุปผล

Print: `Retrospective complete | Shipped: <N> | ADRs: <list> | Learnings: <N> | Next: /zie-status`

### Archive prune (post-release cleanup)

Run archive TTL rotation — non-blocking (skip on failure):

```bash
make archive-prune || true
```

This removes `zie-framework/archive/` files older than 90 days.
Guard: skips automatically when archive has fewer than 20 files.

### Suggest next

After printing the retrospective summary, read `zie-framework/ROADMAP.md` and
extract all items in the **Next** lane.

Rank by: Critical → High → Medium → unlabelled; break ties by retro-theme alignment.

Print top 1–3: `<slug> — <title> [<priority>] | Run: /zie-plan <slug>`
If Next lane empty: `"Backlog is empty — add items with /zie-backlog"`

Advisory only — nothing auto-started.

