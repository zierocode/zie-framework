# Smarter Framework Intelligence — Design Spec

**Problem:** The framework is stateless between sessions — it can't proactively warn about workflow drift, treats every project identically regardless of history, and requires users to manually observe backlog health and config adequacy.

**Approach:** Add three targeted intelligence layers that operate entirely within existing infrastructure (Stop hook, `/zie-backlog`, `/zie-retro`) with no external storage or ML: (1) proactive nudges in the Stop hook that surface actionable warnings about RED phase duration, coverage drops, and stale backlog; (2) backlog intelligence in `/zie-backlog` that auto-tags items and detects near-duplicates before writing; (3) self-tuning proposals in `/zie-retro` that suggest `.config` changes based on observed patterns, requiring user approval before application. All three degrade gracefully — if any data source is missing, the feature is silently skipped.

**Note on velocity tracking:** Release interval velocity is already implemented in `/zie-status` (Step 6). The existing `2026-03-24-velocity-tracking-design.md` spec covers it. This spec does not re-specify velocity — it extends it minimally only where needed by nudges (stale backlog detection uses date arithmetic already available).

**Components:**
- Modify: `hooks/stop-guard.py` — add proactive nudge checks (RED phase duration, coverage drop, stale backlog) as informational plain-text output (not block)
- Modify: `commands/zie-backlog.md` — add auto-tagging step (bug/feature/chore/debt) and duplicate-detection step before writing the backlog file
- Modify: `commands/zie-retro.md` — add self-tuning proposal step: analyze observed patterns, propose `.config` changes, require user approval before applying
- Modify: `hooks/utils_roadmap.py` — add `parse_roadmap_items_with_dates()` helper for stale backlog detection
- No new files, hooks, commands, or external storage

**Acceptance Criteria:**
- [ ] `stop-guard.py` prints an informational nudge (plain text, no block) when: RED phase (`[ ]` task in Now) has been active > 2 days per git log dates, OR coverage has dropped since last run (`.coverage` mtime older than newest test file), OR any backlog item in Next is older than 30 days by ROADMAP entry date
- [ ] All three nudge conditions are independent — each fires or suppresses individually; if all pass, nothing is printed
- [ ] Nudge output is prefixed `[zie-framework] nudge:` so it is clearly identifiable
- [ ] `/zie-backlog` infers a tag (bug/feature/chore/debt) from the title+description and writes it to the frontmatter of the new backlog file; tag inference uses keyword matching (no LLM call)
- [ ] `/zie-backlog` performs slug-based duplicate check against existing `zie-framework/backlog/*.md` files before writing; warns with existing file path if similarity found; does not block creation
- [ ] `/zie-retro` proposes `.config` key changes based on at least two observable patterns: (a) if RED phase repeatedly exceeded 2 days → suggest raising `auto_test_max_wait_s`; (b) if safety_check_mode="agent" caused slowdowns in prior retro session data → suggest switching to "regex"
- [ ] Self-tuning proposals are printed as a diff-style summary; user must type "apply" or approve explicitly before `/zie-retro` writes to `.config`
- [ ] All new code paths have unit tests; existing tests remain green (`make test-unit` passes)
- [ ] Graceful degradation: if `.coverage` missing, if ROADMAP parse fails, if `.config` is absent — each check silently skips; hook always exits 0

**Data Flow:**

1. **Stop hook nudges:**
   - `stop-guard.py` runs after its existing block-check
   - If `stop_hook_active` → skip (same guard as existing)
   - Parse ROADMAP Now lane → find `[ ]` items → determine add-time via `git log --follow -S "[ ] <slug>" -- zie-framework/ROADMAP.md` (first commit that introduced the unchecked item) → if > 2 days elapsed since that commit → print nudge
   - Read `.coverage` mtime vs newest `tests/*.py` mtime → if coverage is stale or missing → print nudge
   - Parse ROADMAP Next lane items with entry dates via `parse_roadmap_items_with_dates()` → if any item date > 30 days ago → print nudge

2. **Backlog auto-tag:**
   - `/zie-backlog` derives tag via keyword map: {bug: [fix, error, crash, broken], chore: [cleanup, update, bump, refactor], debt: [tech debt, debt, legacy, slow], feature: [add, new, implement, support]} — first match wins, default = "feature"
   - Write tag to frontmatter: `tags: [<tag>]`
   - Duplicate check: split each slug by hyphens and spaces, lowercase → token sets; for each existing `backlog/*.md`, if ≥2 tokens overlap → warn "Similar item exists: backlog/<slug>.md". Example: "add-csv-export" (tokens: [add, csv, export]) vs "csv-export-tool" (tokens: [csv, export, tool]) → 2 overlapping tokens → warn.

3. **Self-tuning proposals in retro:**
   - After existing retro steps complete, read `.config` + scan `git log --oneline` commit messages for pattern matching: commits that mention "RED" alongside duration words (e.g., "stuck", "slow", "days", a number followed by "day") are treated as RED-phase signals. No ADR keyword matching. No external file scanning beyond git log.
   - Parse these commit messages to approximate `[ ]` → `[x]` transition durations across the last 5 RED cycles
   - Generate proposal list: at most 3 config key changes; format as:
     ```
     [zie-framework] Self-tuning proposals:
       auto_test_max_wait_s: 15 → 30  (RED cycles averaged >3 days across last 5 cycles)
       safety_check_mode: "agent" → "regex"  (no agent-level blocks in last 10 sessions)
     Apply? Type "apply" to write to .config, or skip.
     ```
   - Note: two distinct thresholds apply here — the Stop hook nudge fires when a single RED phase exceeds 2 days (AC 1); the self-tuning proposal fires when the average across the last 5 RED cycles exceeds 3 days (Data Flow 3). These are independent and intentionally different.
   - On "apply" → write changes to `.config` atomically via `atomic_write()`; print confirmation
   - On skip or no proposals → print "Self-tuning: no changes proposed" and continue

**Edge Cases:**
- ROADMAP Now is empty → all nudge checks skip silently
- Git log unavailable (not a git repo) → skip RED phase timing nudge; exits 0
- `.coverage` file absent → coverage nudge skipped
- Backlog duplicate check with 0 existing items → skip check (no files to compare)
- Self-tuning with no prior retro data → "no changes proposed"
- `.config` missing in retro → self-tuning skipped entirely (no base config to modify)
- All nudge conditions fire simultaneously → print all three as separate lines, not concatenated

**Out of Scope:**
- External integrations (GitHub, Jira, Slack)
- Multi-project or cross-repo analytics
- ML-based inference or embedding-based duplicate detection
- Persistent per-cycle timing database (uses only git log and file mtimes)
- Velocity tracking (already implemented in `/zie-status` Step 6)
- Per-stage timing breakdown beyond RED-phase duration
