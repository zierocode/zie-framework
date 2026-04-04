---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
model: sonnet
effort: medium
---

# /retro — Retrospective + ADRs + Brain Storage

## ตรวจสอบก่อนเริ่ม

**Live context (injected at command load):**

Commits since last tag:
!`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

Recent activity window:
!`git log -20 --oneline`

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Read `zie-framework/.config` → project, zie_memory_enabled.
3. Bind `roadmap_raw` — load `zie-framework/ROADMAP.md` once (reused by all downstream sections, no second read). Extract: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines only (bind as `done_section_raw`). Grep `## Next` → read to next `---` (cache as `next_lane`).
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

Build compact JSON bundle:

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

   Print the five sections immediately after formatting. Candidates for ADRs (decisions with lasting consequences) are passed to the ADR writer agent below.

2. **Check docs sync.**
   Skip guard: if `git log -1 --format="%s"` starts with `release:` → print `"Docs-sync: skipped (ran during release)"` and skip.
   Invoke `Skill(zie-framework:docs-sync-check)`. Print the returned `details` string as the verdict.

### รวมผลลัพธ์

- Five retro sections already printed above.
- Docs-sync verdict already printed above.
- If any step returned an error → print the error and continue. Retro is not blocked by inline step failures.

- ถ้า `zie_memory_enabled=true`: Call `mcp__plugin_zie-memory_zie-memory__remember`
  with `"Project snapshot: <version>. Components changed: <list>. Decisions: <new ADR slugs>."`
  `tags=[project-knowledge, zie-framework, <version>] supersedes=[project-knowledge, zie-framework]`

### บันทึก ADRs + อัปเดต ROADMAP

**Write ADRs inline.** For each decision in `decisions_json`:
- Compose ADR content: 5-section format — Status (Accepted), Context (1–3 sentences),
  Decision (1–3 sentences), Consequences (Positive/Negative/Neutral), Alternatives.
- Call `Write` → `zie-framework/decisions/ADR-<NNN>-<slug>.md`
- Print `[ADR N/total]` after each file.
- On error: print `[zie-framework] retro: ADR write failed — <error>` and continue.

**Update ROADMAP Done inline.**
- Use `roadmap_raw` (bound at pre-flight — no re-read needed).
- Move shipped items from `shipped_items` to the `## Done` section with date and version tag.
- Call `Edit` (or `Write`) to persist the updated file.
- On error: print `[zie-framework] retro: ROADMAP update failed — <error>` and continue.

### Done-rotation (inline)

Inline after ROADMAP update — no Agent call:

1. Parse `## Done` from `roadmap_raw` (already bound at pre-flight — no re-read). ≤ 10 items → skip entirely.
2. Extract date from each item: all `YYYY-MM-DD` matches, take last. No date → keep inline always.
3. Sort by date desc (no-date last). Keep top 10 inline regardless of age.
4. Candidates: rank 11+ items where `today − date > 90 days`.
5. Archive to `zie-framework/archive/ROADMAP-archive-YYYY-MM.md` (YYYY-MM from item's date). Create with header if absent; append `## Archived YYYY-MM-DD` section. Never truncate archive.
6. Rewrite `## Done` to kept items only. Print: `Done-rotation: kept <N>, archived <M> to <K> file(s)` or `≤10 items, skipped`.

### Self-tuning proposals

After docs-sync verdict, before auto-commit:

1. Read `zie-framework/.config`. If absent → print `"Self-tuning: skipped (no .config)"` and skip.
2. Scan `git log --oneline -50` for commits matching `RED` + a numeric day count (e.g. "RED phase stuck 3 days").
   Parse up to 5 RED cycle durations. If average > 3 days → propose `auto_test_max_wait_s: <current> → 30`.
3. Check current `safety_check_mode`; if `"agent"` and no `"BLOCK"` found in `git log --oneline -20` →
   propose `safety_check_mode: "agent" → "regex"`.
4. If no proposals → print `"Self-tuning: no changes proposed"` and continue.
5. Otherwise print:
   ```
   [zie-framework] Self-tuning proposals:
     <key>: <from_val> → <to_val>  (<reason>)
   Apply? Type "apply" to write to .config, or skip.
   ```
6. Wait for user input:
   - `"apply"` → merge proposals into `.config`, write atomically; print `"Self-tuning: applied N change(s)"`
   - Any other → print `"Self-tuning: no changes applied"` and continue

### Auto-commit retro outputs

After ADR + ROADMAP agents complete, auto-commit:

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

Run archive TTL rotation — non-blocking (skip on failure):

```bash
make archive-prune || true
```

This removes `zie-framework/archive/` files older than 90 days.
Guard: skips automatically when archive has fewer than 20 files.

### Suggest next

Use pre-loaded `next_lane` from pre-flight step 3 (no re-read).

Rank by: Critical → High → Medium → unlabelled; break ties by retro-theme alignment.

Print top 1–3: `<slug> — <title> [<priority>] | Run: /plan <slug>`
If Next lane empty: `"Backlog is empty — add items with /backlog"`

Advisory only — nothing auto-started.

