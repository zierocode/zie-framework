---
description: Post-release or end-of-session retrospective — document learnings, write ADRs, update ROADMAP, store in brain.
allowed-tools: Read, Write, Bash, Glob, Grep, Skill
model: sonnet
effort: low
---

# /retro — Retrospective + ADRs + Brain Storage

<!-- preflight: full -->

## ตรวจสอบก่อนเริ่ม

See [Pre-flight standard](../zie-framework/project/command-conventions.md#pre-flight) (reads config, ROADMAP, checks WIP).

**Live context (injected at command load):**

Commits since last tag:
!`git log $(git describe --tags --abbrev=0 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD --oneline`

4. Bind `roadmap_raw` — load `ROADMAP.md` once. Extract: Grep `## Now` → read to next `---`. Grep `## Done` → read ~20 lines (bind as `done_section_raw`). Grep `## Next` → read to next `---` (cache as `next_lane`).

## Steps

### รวบรวม context

1. If `zie_memory_enabled=true`: recall `project=<project> tags=[wip, build-learning, shipped] limit=20`
2. **Subagent Activity** — read subagent-log; if exists: parse JSON lines, group by `agent_type`, print Type/Count table. Missing → "No subagent activity recorded."
3. Count ADR files → get next ADR number.
4. **ADR auto-summarization** — if count > 30: keep 10 most-recent, compress to `ADR-000-summary.md`, delete compressed files. ≤30 → skip.

### สร้าง compact summary

```json
{
  "shipped": ["<commit messages>"],
  "commits_since_tag": "<count>",
  "pain_points": [],
  "decisions": [],
  "done_section_current": "<Done section text>"
}
```

### รูปแบบ retrospective (inline)

Five sections:
- **สิ่งที่ Ship ออกไป** — shipped features/fixes with versions
- **สิ่งที่ทำงานได้ดี** — patterns worth repeating
- **สิ่งที่เจ็บปวด** — specific friction points
- **การตัดสินใจสำคัญ** — decisions: what → why → consequence (ADR candidates)
- **Pattern ที่ควรจำ** — P1/P2 memories for brain

**Docs-sync check** — skip if `git_log_raw` starts with `release:`. Otherwise: `Skill(zie-framework:docs-sync)`.

### บันทึก ADRs + อัปเดต ROADMAP

**ADR gate:**

| Condition | Action |
| --- | --- |
| Any plan has `<!-- adr: required -->` | Write full ADRs + update ADR-000-summary |
| No plan has this tag | Skip full ADRs; append one-line to ADR-000-summary; jump to Done-rotation |

**Write ADRs + Update ROADMAP** (parallel — different target files):

→ ADR writes: 5-section format (Status, Context, Decision, Consequences, Alternatives) → `decisions/ADR-<NNN>-<slug>.md`. Print `[ADR N/total]` after each.

→ ROADMAP Done: move shipped items to `## Done` with date + version tag.

Then: append new ADR entries to `ADR-000-summary.md` (create if missing).

### Done-rotation (inline)

1. Parse `## Done` from `roadmap_raw` (pre-loaded). ≤ 10 items → skip.
2. Extract date per item (last `YYYY-MM-DD`). No date → keep inline.
3. Sort by date desc. Keep top 10 inline regardless.
4. Candidates: rank 11+ where `today − date > 90 days`.
5. Archive to `zie-framework/archive/ROADMAP-archive-YYYY-MM.md`. Append if exists.
6. Rewrite `## Done` to kept items only. Print: `Done-rotation: kept <N>, archived <M>`

### Auto-commit retro outputs

```bash
git add zie-framework/decisions/*.md zie-framework/project/components.md zie-framework/ROADMAP.md zie-framework/archive/ROADMAP-archive-*.md
git commit -m "chore: retro v${VERSION}"
git push origin dev
```

Push fails → `⚠️ Retro git push failed. Manual push: git push origin dev` (non-blocking).
Success → `"✓ Retro complete. Committed <hash>"`

### อัปเดต project knowledge

If `project/` missing → skip. Update `components.md` for changed behavior; `architecture.md` if architecture changed.

### บันทึกสู่ brain

If `zie_memory_enabled=true`:
- P1 preferences: `remember` `"<what worked>. Preference: always use this approach for <context>."`
- P2 learnings: `remember` `"Retro <version>: <key learning>. Decision: <ADR slug>."`
- Downvote incorrect: `mcp__plugin_zie-memory_zie-memory__downvote_memory`

### Self-tuning proposals

Non-blocking — runs last, after all commits.

| Condition | Proposal |
| | --- | --- |
| `.config` missing or `self_tuning_enabled=false` | Skip silently |
| Avg RED cycle > 3 days (from `git_log_raw`) | `auto_test_max_wait_s: <current> → 30` |
| `safety_check_mode="agent"` + no `BLOCK` in log | `safety_check_mode: "agent" → "regex"` |
| No proposals | `"Self-tuning: no changes proposed"` |

If proposals exist: print advisory (non-blocking, no user input required).

### Archive prune

```bash
make archive-prune || true
```

### สรุปผล + Suggest next

Print: `Retrospective complete | Shipped: <N> | ADRs: <list> | Learnings: <N> | Next: /status`

Rank Next items: Critical → High → Medium → unlabelled; break ties by retro-theme alignment.
Print top 1-3: `<slug> — <title> [<priority>] | Run: /plan <slug>`. Empty → "Backlog is empty — add items with /backlog"

→ /status to check pipeline state