---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-session-learn-concurrent-write.md
---

# Session-Learn Atomic Pending File Write — Design Spec

**Problem:** `session-learn.py` writes `pending_learn.txt` directly with `write_text()`, which is not atomic — two simultaneous Stop hook invocations (e.g., two terminal tabs closing) can interleave writes and corrupt the file.

**Approach:** Replace the direct `write_text()` call with an atomic write: write content to a sibling `.tmp` file in the same directory, then `Path.rename()` it over the target. On POSIX (macOS/Linux), `rename()` is atomic at the filesystem level. Extract the pattern into a `atomic_write(path, content)` helper in `utils.py` so other hooks can reuse it.

**Components:**
- `hooks/utils.py` — add `atomic_write(path: Path, content: str) -> None` helper
- `hooks/session-learn.py` — replace `pending_learn_file.write_text(...)` with `atomic_write(pending_learn_file, ...)`

**Data Flow:**
1. `session-learn.py` builds `content` string (project + wip_context) as before
2. Calls `atomic_write(pending_learn_file, content)`
3. `atomic_write` writes to `pending_learn_file.with_suffix(".tmp")`
4. Calls `tmp_path.rename(pending_learn_file)` — atomic on POSIX
5. If rename fails (e.g., cross-device), exception propagates and is caught by existing outer try/except in caller or logged

**Edge Cases:**
- Parent directory does not exist — `mkdir(parents=True, exist_ok=True)` already called before write; `.tmp` sibling is in the same dir so this is safe
- Rename across filesystems (unlikely for `~/.claude/projects/`) — `rename()` raises `OSError`; caller should catch and log
- `.tmp` file left behind after a crash — harmless stale file; next run overwrites it
- Concurrent writes race on `.tmp` itself — last writer wins on rename, which is the correct behavior (idempotent content)

**Out of Scope:**
- Locking `pending_learn.txt` for read-modify-write cycles (file is write-only here)
- Migrating `pending_learn.txt` format to JSON
- Applying atomic write to the zie-memory API call
