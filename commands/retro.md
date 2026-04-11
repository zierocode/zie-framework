---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
model: sonnet
effort: low
---

# /retro — Retrospective + ADRs + Brain Storage

## ตรวจสอบก่อนเริ่ม

**Live context (injected at command load):**

Commits since last tag:
!`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

Recent activity (last 50 commits — bound as `git_log_raw` at pre-flight):
!`git log -50 --oneline`

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Read `zie-framework/.config` → project, zie_memory_enabled.
3. Bind `roadmap_raw` — load `zie-framework/ROADMAP.md` once (reused by all downstream sections, no second read). Extract: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines only (bind as `done_section_raw`). Grep `## Next` → read to next `---` (cache as `next_lane`).
4. Bind `git_log_raw` — the `!git log -50 --oneline` bang output injected above. Used by self-tuning and docs-sync guard — no Bash call needed.
   Print: "Analyzing git log..." — git context already injected above, no Bash needed.

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

```json
{
  "shipped": ["<commit message 1>", "<commit message 2>"],
  "commits_since_tag": "<count from git log>",
  "pain_points": [],
  "decisions": [],
  "done_section_current": "<Done section text — pre-extracted for agents>"
}
```

### รูปแบบ retrospective (inline)

1. **Format retrospective inline.** Using `compact_json` from the context above, structure output as five sections:
   - **สิ่งที่ Ship ออกไป** — list shipped features/fixes with versions
   - **สิ่งที่ทำงานได้ดี** — patterns, approaches, tools that saved time (only worth repeating)
   - **สิ่งที่เจ็บปวด** — friction points, unexpected complexity, slowdowns (specific, not vague)
   - **การตัดสินใจสำคัญ** — decisions with lasting consequences; each: what → why → consequence (candidates for ADRs)
   - **Pattern ที่ควรจำ** — reusable techniques worth storing in brain as P1/P2 memories

2. **Check docs sync.**
   Skip guard: if the first line of `git_log_raw` starts with `release:` → print `"Docs-sync: skipped (ran during release)"` and skip.
   Invoke `Skill(zie-framework:docs-sync-check)`. Print the returned `details` string as the verdict.

### รวมผลลัพธ์

- If any step returned an error → print the error and continue. Retro is not blocked by inline step failures.

- ถ้า `zie_memory_enabled=true`: Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"Project snapshot: <version>. Components changed: <list>. Decisions: <new ADR slugs>."`
  `tags=[project-knowledge, zie-framework, <version>] supersedes=[project-knowledge, zie-framework]`

### บันทึก ADRs + อัปเดต ROADMAP

**ADR gate (light mode):**
Scan plan files for shipped slugs (`zie-framework/plans/` — match shipped commit slugs):
- If any plan contains `<!-- adr: required -->` → write full ADRs as normal (continue below)
- If no plan has this tag → skip full ADR writing; update `decisions/ADR-000-summary.md` only
  (append one-line entry: `| — | <version> | <one-sentence summary of shipped features> | Accepted |`)
  then jump directly to **Update ROADMAP Done inline**

**Write ADRs inline** (parallel with ROADMAP update — different target files, no race):
Launch ADR writes and ROADMAP update as two parallel tool calls in a single message:

→ **ADR writes:** For each decision in `decisions_json`:
- Compose ADR content: 5-section format — Status (Accepted), Context (1–3 sentences),
  Decision (1–3 sentences), Consequences (Positive/Negative/Neutral), Alternatives.
- Call `Write` → `zie-framework/decisions/ADR-<NNN>-<slug>.md`
- Print `[ADR N/total]` after each file.
- On error: print `[zie-framework] retro: ADR write failed — <error>` and continue.

→ **Update ROADMAP Done** (parallel with ADR writes):
- Use `roadmap_raw` (bound at pre-flight — no re-read needed).
- Move shipped items from `shipped_items` to the `## Done` section with date and version tag.
- Call `Edit` (or `Write`) to persist the updated file.
- On error: print `[zie-framework] retro: ROADMAP update failed — <error>` and continue.

Wait for both to complete, then:

**Update ADR-000-summary.md** — if any new ADR files were written this session:
- For each new `ADR-<NNN>-<slug>.md` just written: append 1-line entry to
  `zie-framework/decisions/ADR-000-summary.md`:
  `| ADR-NNN | Title | One-sentence decision | Accepted |`
- If `ADR-000-summary.md` missing → create it with table header then append entries.
- Skip if no new ADRs were written.

### Done-rotation (inline)

1. Parse `## Done` from `roadmap_raw` (already bound at pre-flight — no re-read). ≤ 10 items → skip entirely.
2. Extract date from each item: all `YYYY-MM-DD` matches, take last. No date → keep inline always.
3. Sort by date desc (no-date last). Keep top 10 inline regardless of age.
4. Candidates: rank 11+ items where `today − date > 90 days`.
5. Archive to `zie-framework/archive/ROADMAP-archive-YYYY-MM.md` (YYYY-MM from item's date). Create with header if absent; append `## Archived YYYY-MM-DD` section. Never truncate archive.
6. Rewrite `## Done` to kept items only. Print: `Done-rotation: kept <N>, archived <M> to <K> file(s)` or `≤10 items, skipped`.

### Auto-commit retro outputs

```bash
git add zie-framework/decisions/*.md zie-framework/project/components.md zie-framework/ROADMAP.md zie-framework/archive/ROADMAP-archive-*.md
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

Print: `Retrospective complete | Shipped: <N> | ADRs: <list> | Learnings: <N> | Next: /status`

### Archive prune (post-release cleanup)

```bash
make archive-prune || true
```

### Suggest next

Use pre-loaded `next_lane` from pre-flight step 3 (no re-read).

Rank by: Critical → High → Medium → unlabelled; break ties by retro-theme alignment.

Print top 1–3: `<slug> — <title> [<priority>] | Run: /plan <slug>`
If Next lane empty: `"Backlog is empty — add items with /backlog"`

### Self-tuning proposals

Non-blocking — runs last, after all commits, ROADMAP updates, and Suggest next.

1. Read `zie-framework/.config`. If absent → print `"Self-tuning: skipped (no .config)"` and skip.
2. Check `self_tuning_enabled` key in `.config`. If `false` → skip silently.
3. Scan `git_log_raw` (already bound at pre-flight) for commits matching `RED` + a numeric day count (e.g. "RED phase stuck 3 days").
   Parse up to 5 RED cycle durations. If average > 3 days → propose `auto_test_max_wait_s: <current> → 30`.
4. Check current `safety_check_mode`; if `"agent"` and no `"BLOCK"` found in `git_log_raw` →
   propose `safety_check_mode: "agent" → "regex"`.
5. If no proposals → print `"Self-tuning: no changes proposed"` and return.
6. Otherwise print (advisory, non-blocking — no user input required):
   ```
   [zie-framework] Self-tuning proposals:
     <key>: <from_val> → <to_val>  (<reason>)

   To apply: run /chore with the proposal above, or set self_tuning_enabled: false in .config to opt out.
   ```

