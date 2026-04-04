# Plan: stop-guard: Use Session Cache + Faster git status

status: approved

## Tasks

- [ ] RED: Add failing tests to `tests/unit/test_hooks_stop_guard.py`
  - TC-1: cache hit — mock `get_cached_git_status` to return clean status string;
    assert `subprocess.run` is NOT called.
  - TC-2: cache miss — mock `get_cached_git_status` to return `None`; assert
    `subprocess.run` IS called with `--untracked-files=no` (not `=all`); assert
    `write_git_status_cache` is called with key `"status"`.
  - TC-3: cache miss with dirty file — mock cache miss + subprocess returns an
    uncommitted impl file; assert hook prints block JSON.
  - TC-4: `stop_hook_active` early-exit still works (existing behavior, confirm
    no regression).
  - TC-5: subprocess error path — mock subprocess raises `Exception`; assert
    hook exits 0 and does not print block JSON.

- [ ] GREEN: Update `hooks/stop-guard.py`
  - Add import of `get_cached_git_status`, `write_git_status_cache` from
    `utils_roadmap` (after existing `utils_event` / `utils_config` imports).
  - Remove `import subprocess` only if it becomes unused after refactor
    (keep if still needed for the subprocess.run fallback path — it is needed).
  - In the inner block, after `subprocess_timeout = config["subprocess_timeout_s"]`:
    - Add `session_id = event.get("session_id", "default")`
    - Check `cached = get_cached_git_status(session_id, "status")`
    - On hit: set `stdout_text = cached`, skip subprocess
    - On miss: run `subprocess.run(["git", "status", "--short",
      "--untracked-files=no"], ...)`, on `returncode == 0` call
      `write_git_status_cache(session_id, "status", result.stdout)`, set
      `stdout_text = result.stdout`
  - Replace `result.stdout.splitlines()` loop to use `stdout_text.splitlines()`

- [ ] REFACTOR: Run `make lint-fix` — no logic changes, only import ordering

## Files to Change

| File | Change |
| --- | --- |
| `hooks/stop-guard.py` | Add cache import + session_id + cache-then-run pattern; change `--untracked-files=all` → `--untracked-files=no` |
| `tests/unit/test_hooks_stop_guard.py` | New file — unit tests for cache hit/miss/dirty/error paths |

## Verification

```bash
make test-fast          # RED → GREEN loop
make lint               # must pass clean
make test-ci            # full suite + coverage gate before commit
```
