---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-docs-sync-blind-to-project-md.md
---

# lean-docs-sync-blind-to-project-md — Design Spec

**Problem:** `docs-sync-check` verifies CLAUDE.md and README.md against disk but never reads `PROJECT.md`, leaving the primary user-facing knowledge hub unchecked for stale or missing command/skill entries.

**Approach:** Extend `skills/docs-sync-check/SKILL.md` with a new Step 3b that enumerates `PROJECT.md`'s Commands and Skills tables and cross-references them against disk. Add a `project_md_stale` field to the returned JSON verdict. No new files or skills are created — the existing skill is the single source of truth (per the docs-sync-consolidate consolidation in v1.18.1).

**Components:**
- `skills/docs-sync-check/SKILL.md` — primary change: new PROJECT.md enumeration step + verdict field
- `tests/test_docs_sync_check_general_agent.py` — new unit tests asserting PROJECT.md coverage + `project_md_stale` in verdict schema

**Data Flow:**
1. Skill reads `CLAUDE.md` and `README.md` (existing steps 1–2, unchanged)
2. Skill globs `commands/*.md`, `skills/*/SKILL.md`, `hooks/*.py` (existing step 3, unchanged)
3. **New step 3b:** Skill reads `PROJECT.md` — extract every `| /command |` row from the Commands table and every `| skill-name |` row from the Skills table
4. Cross-reference: commands on disk vs. PROJECT.md Commands table rows → `missing_from_project_md` (on disk, not in table) + `extra_in_project_md` (in table, not on disk)
5. Cross-reference: skill dirnames on disk vs. PROJECT.md Skills table rows → same two categories
6. Set `project_md_stale: true` if either cross-reference has entries; `false` otherwise
7. Return extended JSON verdict including `project_md_stale`, `missing_from_project_md`, `extra_in_project_md`

**Edge Cases:**
- PROJECT.md missing entirely → set `project_md_stale: false`, add note in `details` ("PROJECT.md not found — skipped")
- Commands or Skills table absent from PROJECT.md → treat as empty table, flag all disk items as `missing_from_project_md`
- Commands table uses `/command` prefix in PROJECT.md; strip `/` before comparing to basename of `commands/*.md` (strip `.md` suffix from filenames)
- Skills table rows use bare names (no path prefix); compare directly to parent dirname of `skills/*/SKILL.md`
- Rows that are headers (`| Command |`, `| --- |`) must be skipped

**Out of Scope:**
- Auto-fixing PROJECT.md (read-only check only)
- Checking PROJECT.md's Agents, Knowledge, or Links sections
- Checking hooks against PROJECT.md (hooks are not listed in PROJECT.md)
- Modifying zie-retro or zie-release callers (verdict JSON is additive; callers already surface the verdict to the user)
- Template PROJECT.md for /init (separate feature)
