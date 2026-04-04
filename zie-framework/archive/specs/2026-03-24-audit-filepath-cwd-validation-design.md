---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-filepath-cwd-validation.md
---

# file_path CWD Boundary Validation — Design Spec

**Problem:** `auto-test.py` uses `file_path` from the Claude hook event as a raw `Path` without validating it is within the project root, allowing paths like `/etc/passwd` to flow into `changed.stem` and appear in log output and test-file search logic.

**Approach:** After parsing `file_path` into `changed = Path(file_path)`, call `changed.is_relative_to(cwd)` and exit cleanly if the check fails. Use `Path.resolve()` on both sides to neutralize `..` traversal before the comparison.

**Components:**
- `hooks/auto-test.py` — add boundary check immediately after `changed = Path(file_path)` (line 89)
- `tests/test_auto_test.py` — add cases: path outside cwd exits 0, path with `..` traversal exits 0, normal path proceeds

**Data Flow:**
1. `file_path` string arrives from hook event JSON.
2. `changed = Path(file_path).resolve()` — resolves symlinks and `..` segments.
3. `cwd_resolved = cwd.resolve()`.
4. `if not changed.is_relative_to(cwd_resolved): sys.exit(0)` — silent exit, hook does not run.
5. Downstream: `changed.stem` is only ever a filename from within the project tree.
6. `find_matching_test()` receives a validated path; no out-of-tree stems leak to `rglob` or log output.

**Edge Cases:**
- `file_path` is an absolute path outside the project (e.g. `/etc/passwd`, `/tmp/foo`) — blocked at step 4.
- `file_path` uses `../` traversal to escape cwd — `resolve()` at step 2 neutralizes before comparison.
- `file_path` is a relative path (uncommon but possible) — `Path(file_path).resolve()` resolves relative to process cwd, which equals `CLAUDE_CWD`; check passes correctly for in-project paths.
- `file_path` is empty string — already handled by the existing early-exit guard on line 58-59.
- Symlinked files within the project that resolve outside cwd — treated as out-of-bounds (conservative; acceptable trade-off).

**Out of Scope:**
- Validating `file_path` in `wip-checkpoint.py` — that hook does not use `file_path` for path operations.
- Sanitizing `file_path` for display (log scrubbing) — boundary exit at step 4 prevents the path from ever reaching log lines.
- Input validation on other event fields (e.g. `tool_name`) — separate hardening item.
