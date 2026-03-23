---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-tests-tmp-path.md
---

# Migrate Tests from /tmp Hardcoded Paths to pytest tmp_path — Design Spec

**Problem:** `test_session_cleanup.py` (lines 30-31, 45) and `test_hooks_wip_checkpoint.py` (lines 32-34) write state files to real `/tmp/zie-*` paths, causing cross-test contamination and parallel-run collisions.

**Approach:** Replace all hardcoded `/tmp/zie-*` path construction in tests with paths derived from pytest's `tmp_path` fixture, which provides a unique, auto-cleaned directory per test invocation. The hooks under test read `CLAUDE_CWD` to compute their own tmp paths, so tests must inject a matching `CLAUDE_CWD` that routes hook state into `tmp_path`. Where tests directly create or assert on state files, they must derive those paths from `tmp_path` using the same `project_tmp_path()` helper the hook uses.

**Components:**
- `tests/unit/test_session_cleanup.py` — lines 29-31, 43-52
- `tests/unit/test_hooks_wip_checkpoint.py` — `counter_path()` helper (line 32-34), `reset_counter()`, `_cleanup_counter` fixture teardown
- `hooks/utils.py` — `project_tmp_path()` (read-only reference, no change)

**Data Flow:**
1. Each test receives `tmp_path` from pytest (e.g. `/private/var/folders/.../pytest-xyz/test_foo0/`).
2. Test sets `CLAUDE_CWD` env var to a subdirectory of `tmp_path` whose `.name` is the project name being tested.
3. Hook executes; internally calls `project_tmp_path(name, cwd.name)` → writes state to `/tmp/zie-<project>-<name>` — this is still real `/tmp`, but the project name is derived from `tmp_path.name` which is unique per test invocation.
4. Test's `counter_path()` / assertion paths are computed via `project_tmp_path("edit-count", tmp_path.name)` rather than hardcoded strings, ensuring test and hook agree on the same path.
5. Fixture teardown calls `p.unlink(missing_ok=True)` on the computed path — already the pattern in `_cleanup_counter`; just needs the path derivation to be correct.

**Edge Cases:**
- `tmp_path.name` may contain pytest-generated suffixes (e.g. `test_counter_increments0`); `project_tmp_path` sanitises non-alphanumeric chars with `-`, so the resulting path is always valid.
- Parallel pytest workers (`-n auto`) will have different `tmp_path` values, so project-scoped `/tmp` files will also differ — no collision.
- If a test fails mid-run and teardown is skipped (e.g. pytest crash), leftover files have unique names and will not affect other tests.
- `test_does_not_delete_other_project_files` creates a file for a second "other" project: that path must also be routed through `tmp_path`-derived naming to avoid colliding with real state.

**Out of Scope:**
- Changing the hook's own use of `/tmp` (hooks intentionally use real `/tmp` for persistence across hook invocations).
- Migrating integration tests or subprocess-level tests that cannot inject `CLAUDE_CWD`.
- Adding `tmp_path`-based isolation to hooks that don't use `project_tmp_path()`.
