---
approved: true
approved_at: 2026-03-29
backlog: backlog/roadmap-done-compaction.md
---

# ROADMAP Done Section Auto-Compaction — Design Spec

**Problem:** ROADMAP.md Done section grows ~2 entries per release with no cleanup, currently 36 entries / 100 lines. At this pace, it will reach 150+ entries / 400+ lines within 6 months, making manual review unwieldy and creating drift risk if the current 20-line read limit is ever relaxed.

**Approach:** Add a compaction step to `/zie-retro` that auto-archives entries older than 6 months when Done count exceeds 20. Old entries are replaced with a single dated summary line, and detailed history is preserved in `zie-framework/archive/`. Recent entries (latest 20) remain in full detail for easy current-session review.

**Components:**
- `hooks/utils.py` — add `compact_roadmap_done(roadmap_path: str, threshold: int = 20, cutoff_months: int = 6)` utility function
- `zie-framework/ROADMAP.md` — modified Done section (replaced entries + archive summary line)
- `zie-framework/archive/` — new directory storing archived ROADMAP entries by version range
- `skills/retro-format/SKILL.md` — updated to invoke compaction after ROADMAP Done update
- Tests: `tests/test_utils.py` — add tests for `compact_roadmap_done()` function (trigger, format, idempotency)

**Data Flow:**

1. `/zie-retro` updates ROADMAP.md Done section with new shipped items (existing flow, handled by retro-format skill)
2. After Done section is updated in ROADMAP.md, `zie-framework:retro-format` skill calls `compact_roadmap_done()` from `hooks/utils.py`
3. `compact_roadmap_done()` parses Done section entries from ROADMAP.md
4. Count entries in Done section
5. If count > 20:
   - Identify entries with `[archive]` marker already present (skip, already archived)
   - Parse remaining entries to extract versions and dates (e.g., `v1.11.1 2026-03-29`)
   - Identify entries older than 6 months from today's date
   - Group old entries by version range: `v1.0–v1.5 (2026-03 to 2026-09): N features shipped`
   - Create archive file: `zie-framework/archive/ROADMAP-<start-version>-<end-version>.md`
   - Write grouped old entries to archive file with original formatting preserved
   - Replace old entries in ROADMAP.md with single summary line:
     `- [archive] v1.0–v1.5 (2026-03 to 2026-09): 42 features shipped — see zie-framework/archive/ROADMAP-v1.0-v1.5.md`
   - Leave latest 20 entries in ROADMAP.md unchanged
6. Write updated ROADMAP.md back to disk
7. Return compaction result tuple: `(was_compacted: bool, old_entry_count: int, version_range: str)` or `(False, 0, "")` if no compaction occurred
8. `zie-framework:retro-format` skill logs result: "Compacted X old entries (v1.0–v1.5) into archive. Keep 20 recent entries in ROADMAP." or "Done section has only recent entries, no archival needed"

**Edge Cases:**

- **No entries older than 6 months** — skip compaction, print "Done section has only recent entries, no archival needed"
- **Entries with malformed dates** — safely skip those entries (do not crash), log warning
- **Already-archived entries** — detect `[archive]` lines, preserve them as-is
- **Exactly 20 entries** — no compaction triggered; only >20 triggers
- **Multiple archive cycles** — merge new archives with existing ones by date range
- **Entry without version/date** — preserve in Done section (treat as unparseable, keep recent)
- **Empty archive file** — should not happen; if created, next cycle will detect and consolidate

**Out of Scope:**

- Manual archive cleanup or TTL rotation (separate backlog item: archive-ttl-rotation)
- Changing the 20-entry threshold via config (hardcoded to 20, can be parameterized in future via zie-framework/.config)
- Rewriting Done section from scratch (only removes old entries, keeps recent intact)
- Compression of archive files (stored as plain Markdown)
- Changing the 6-month cutoff duration (hardcoded to 6 months; future config option if needed)
- Archive file merging (if multiple archive cycles occur, creates separate archive files; future consolidation possible)
- Integration with archive-ttl-rotation or other archive management strategies (planned as separate feature)
