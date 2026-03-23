---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-toctou-tmp-race.md
---

# TOCTOU Race on /tmp Debounce File — Design Spec

**Problem:** `auto-test.py` checks `debounce_file.exists()` + `stat().st_mtime`, then writes to the same path — a non-atomic sequence that lets a concurrent session race the check and bypass debounce.

**Approach:** Replace the direct `debounce_file.write_text()` call with an atomic write via write-to-tmp-then-rename: write content to a sibling temp file (`debounce_file.with_suffix('.tmp')`), then call `os.replace()` (POSIX-atomic rename) to move it into place. This collapses the check-then-write gap to a single atomic filesystem operation.

**Components:**
- `hooks/auto-test.py` — debounce write block (lines 83-87)
- `hooks/utils.py` — `project_tmp_path()` used by both hooks (no change needed)
- `tests/test_auto_test.py` — new test asserting atomic write path is used

**Data Flow:**
1. `debounce_file = project_tmp_path("last-test", cwd.name)` — same as before.
2. Existence + mtime check runs as before (read-only, unchanged).
3. On cache miss: write `file_path` content to `debounce_file.parent / (debounce_file.name + ".tmp")`.
4. Call `os.replace(tmp_path, debounce_file)` — atomic on POSIX; on Windows this is best-effort but acceptable.
5. Subsequent concurrent checks see either the old file or the new file — never a partial state.

**Edge Cases:**
- `/tmp` full — `os.replace` raises `OSError`; wrap in `try/except` and continue (debounce skipped, tests run).
- `.tmp` sibling left behind on crash — harmless; next write overwrites it.
- Two hooks racing simultaneously — last writer wins on rename; debounce may fire twice in a tight race, which is the same failure mode as the current code but no worse.

**Out of Scope:**
- OS-level file locking (`fcntl.flock`) — adds complexity beyond the stated fix.
- Fixing the predictable `/tmp` path naming (`zie-{project}-*`) — separate symlink-attack item.
- Changes to `wip-checkpoint.py` counter write (low-impact counter, covered by symlink spec).
