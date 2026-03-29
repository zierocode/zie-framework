---
approved: true
approved_at: 2026-03-29
backlog: backlog/archive-ttl-rotation.md
---

# Archive TTL Rotation — Design Spec

**Problem:** `zie-framework/archive/` grows without bound (~3 files per feature), projected to reach 7,500 files within 1 year, adding unnecessary repo noise and making the directory impractical to navigate.

**Approach:** Implement a configurable TTL-based pruning system that removes archive files (backlog, specs, plans) older than 90 days via `make archive-prune`, integrated into the post-release step of `/zie-retro` with a safety guard preventing pruning on young projects (< 20 total archive files).

**Components:**
- `Makefile` — add `archive-prune` target (new rule)
- `zie-framework/archive/` — source directory for pruning operations
- `commands/zie-retro.md` — integrate archive pruning call
- `CLAUDE.md` — document new target in Development Commands section
- `tests/` — unit tests for prune logic (new test file)

**Data Flow:**

1. **Trigger:** `/zie-retro` executes post-release cleanup phase
2. **Pre-flight check:** Count total files in `zie-framework/archive/{backlog,specs,plans}/`
   - If count < 20 → print "Archive too young (N files), skipping prune" and return
   - Else → proceed to Step 3
3. **Scan & filter:** Walk each of `zie-framework/archive/backlog/`, `zie-framework/archive/specs/`, and `zie-framework/archive/plans/` for all `*.md` files
   - Get mtime for each file via `stat`
   - Compare against 90-day window: `(today - mtime) > 90 days`
   - Collect matching file paths
4. **Prune:** Delete each matching file (safe, non-recursive — only files in direct subdirs)
5. **Report:** Print count of files removed (format: `"[zie-framework] Archive prune: removed N file(s)"`)

**Edge Cases:**

- Archive directory doesn't exist — silently skip (graceful degradation)
- No files older than 90 days — print "Archive prune: 0 files removed" and exit cleanly
- Permission denied on file deletion — log to stderr, continue (don't block retro)
- Young project (< 20 files) — guard prevents premature pruning
- Symlinks in archive — treat as regular files; use `os.remove()` (deletes link, not target)

**Out of Scope:**

- Configurable TTL (fixed at 90 days in this spec — future config knob)
- Compression or archiving to external storage
- Selective pruning (e.g., by feature type or author)
- Pre-flight confirmation dialog (automated via guard only)
- Prune target as standalone `make` command (only via `/zie-retro` pipeline)
- Pruning files in subdirectories deeper than `archive/{backlog,specs,plans}/`
