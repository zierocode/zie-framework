---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-symlink-tmp-attack.md
---

# Symlink Attack on /tmp State Files — Design Spec

**Problem:** `auto-test.py` and `wip-checkpoint.py` write to `/tmp/zie-{project}-*` paths without checking whether the target is a symlink, allowing a local attacker to pre-create a symlink to an arbitrary writable file and have the hook overwrite it.

**Approach:** Add a `safe_write_tmp(path, content)` helper to `hooks/utils.py` that checks `os.path.islink(path)` before writing; if the path is a symlink, skip the write and emit a stderr warning. All `/tmp` writes in `auto-test.py` and `wip-checkpoint.py` are routed through this helper.

**Components:**
- `hooks/utils.py` — new `safe_write_tmp(path: Path, content: str) -> bool` helper
- `hooks/auto-test.py` — replace `debounce_file.write_text(file_path)` with `safe_write_tmp()`
- `hooks/wip-checkpoint.py` — replace `counter_file.write_text(str(count))` with `safe_write_tmp()`
- `tests/test_utils.py` — unit tests for `safe_write_tmp` (symlink detected, normal write, missing parent)

**Data Flow:**
1. Hook calls `safe_write_tmp(target_path, content)`.
2. `safe_write_tmp` calls `os.path.islink(target_path)`.
3. If symlink: print `[zie-framework] WARNING: tmp path is a symlink, skipping write: {target_path}` to stderr; return `False`.
4. If not symlink: perform atomic write (write to `.tmp` sibling, then `os.replace`) per TOCTOU spec; return `True`.
5. Caller receives bool; on `False`, hook exits or skips the dependent logic (debounce treated as cold, counter increment lost).

**Edge Cases:**
- Symlink pointing to a non-existent target — `os.path.islink` still returns `True`; correctly blocked.
- Race between `islink` check and subsequent write (TOCTOU on the check itself) — mitigated by combining with the atomic-rename approach from the TOCTOU spec; window is negligible in practice.
- Path does not exist yet (normal first-run) — `islink` returns `False`; write proceeds normally.
- Parent `/tmp` directory missing — `OSError` caught; hook exits cleanly.

**Out of Scope:**
- Using `O_NOFOLLOW` via `os.open()` — correct but more complex; `islink` check achieves the same protection with less code.
- Changing the `/tmp` path naming scheme to use a random suffix.
- Protecting reads from `/tmp` (only writes are the attack surface here).
