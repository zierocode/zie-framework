---
slug: audit-subagent-stop-atomic
status: draft
date: 2026-04-01
---
# Spec: Atomic Append for subagent-stop.py Session Log

## Problem

`subagent-stop.py` appends completed subagent metadata to a JSONL session log using
`open(log_path, "a")`. Under sprint mode, multiple subagents can complete near-simultaneously,
each forking a separate Python process that calls this hook. Concurrent `open("a")` across
OS processes is not guaranteed atomic — on some platforms, the write of one process can
interleave with another mid-line, producing a corrupt JSONL entry (partial JSON or merged
lines). This silently corrupts the log without any error surfacing.

The codebase already has `atomic_write` and `safe_write_tmp` in `utils.py` (rename-based,
POSIX-atomic) as the established pattern for safe file writes. The append path in
`subagent-stop.py` bypasses this convention.

## Proposed Solution

Replace the bare `open(log_path, "a")` with a **read-append-atomic_write** pattern:

1. Read the existing log file contents (empty string if file does not exist).
2. Append the new JSONL record (`json.dumps(record) + "\n"`).
3. Write the full new content atomically via `safe_write_tmp` (which handles symlink check,
   NamedTemporaryFile, and `os.replace`).

This approach:
- Reuses the existing `safe_write_tmp` utility — no new helpers needed.
- Preserves the JSONL format exactly (one JSON object per line).
- Inherits the symlink guard already in `safe_write_tmp`, allowing removal of the
  duplicate inline symlink check in `subagent-stop.py`.
- Is correct for the actual event frequency: `SubagentStop` fires once per subagent
  completion, which is low-frequency relative to filesystem rename latency.

No locking mechanism (`fcntl.flock`) is required. The rename-based approach eliminates
corruption; the worst case under a true simultaneous write race is that one record is
lost (last-write-wins on `os.replace`), which is acceptable for an audit log. If
zero-loss guarantees were required, per-subagent shard files would be needed — that is
out of scope.

**Implementation sketch (Tier 2 block):**

```python
from utils import get_cwd, project_tmp_path, read_event, safe_write_tmp

log_path = project_tmp_path("subagent-log", cwd.name)

existing = ""
if log_path.exists():
    existing = log_path.read_text(encoding="utf-8")

new_content = existing + json.dumps(record) + "\n"
safe_write_tmp(log_path, new_content)
```

The inline symlink guard (`os.path.islink` check + early exit) is removed because
`safe_write_tmp` already performs that check and logs to stderr.

## Acceptance Criteria

- [ ] AC1: `subagent-stop.py` no longer uses `open(log_path, "a")` — the bare append is
  replaced by `safe_write_tmp` with read-then-write semantics.
- [ ] AC2: The inline `os.path.islink` guard and its `sys.exit(0)` branch are removed from
  `subagent-stop.py`; symlink protection is delegated to `safe_write_tmp`.
- [ ] AC3: The written log file remains valid JSONL — each line is a self-contained JSON
  object; existing entries are preserved across successive writes.
- [ ] AC4: `safe_write_tmp` is imported from `utils` (no new helper functions introduced).
- [ ] AC5: If the log file does not yet exist, the hook creates it containing exactly one
  JSONL line for the current record.
- [ ] AC6: Hook still exits 0 on all code paths; no unhandled exceptions propagate.
- [ ] AC7: Unit tests cover: (a) new file creation, (b) append to existing content,
  (c) symlink path returns without writing (delegates to `safe_write_tmp` behaviour).

## Out of Scope

- Per-subagent shard files with merge-on-read (over-engineered for current event frequency).
- `fcntl.flock`-based locking (POSIX-only, adds complexity, not needed for rename semantics).
- Changes to the JSONL schema or log consumer code.
- Backfilling or repairing any previously written logs.
