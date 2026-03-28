---
approved: true
approved_at: 2026-03-24
backlog: backlog/add-subprocess-timeouts.md
---

# Add Subprocess Timeouts to All Hooks — Design Spec

**Problem:** `hooks/sdlc-compact.py` calls `subprocess.run()` for two git operations (lines 54, 66) without a `timeout=` parameter. If git hangs (lock file, slow network mount, large repo index), the hook blocks the Claude session indefinitely. All other hooks that call subprocess already have timeouts.

**Approach:** Add `timeout=5` to the two bare `subprocess.run()` calls in `sdlc-compact.py`. The `except Exception` blocks already present around each call will catch `subprocess.TimeoutExpired` (a subclass of `Exception`) and fall through to the graceful degraded value — no additional error handling code needed. No changes to any other hook.

**Components:**
- `hooks/sdlc-compact.py`
  - Line 54: add `timeout=5` to `subprocess.run(["git", "-C", ..., "branch", "--show-current"], ...)`
  - Line 66: add `timeout=5` to `subprocess.run(["git", "-C", ..., "diff", "--name-only", "HEAD"], ...)`

**Current state audit (all hooks with subprocess.run):**
| Hook | Line | Timeout | Status |
|------|------|---------|--------|
| `failure-context.py` | 46, 60 | 5s | ✅ Already correct |
| `stop-guard.py` | 53 | 5s | ✅ Already correct |
| `task-completed-gate.py` | 61 | 5s | ✅ Already correct |
| `auto-test.py` | 138 | `auto_test_timeout_ms ÷ 1000` (default 30s) | ✅ Already correct |
| `safety_check_agent.py` | 80 | 30s | ✅ Already correct |
| `sdlc-compact.py` | 54 | **none** | ❌ Needs fix |
| `sdlc-compact.py` | 66 | **none** | ❌ Needs fix |

**Data Flow:**

BEFORE (`sdlc-compact.py:54`):
```python
result = subprocess.run(
    ["git", "-C", str(cwd), "branch", "--show-current"],
    capture_output=True,
    text=True,
)
```

AFTER:
```python
result = subprocess.run(
    ["git", "-C", str(cwd), "branch", "--show-current"],
    capture_output=True,
    text=True,
    timeout=5,
)
```

Same pattern applied to line 66 (`git diff --name-only HEAD`). The surrounding `except Exception` at each site already catches `subprocess.TimeoutExpired` and sets `git_branch = ""` / `changed_files = []` with a stderr log — no new error handling code required.

**Why 5s:** Mirrors the existing pattern in `failure-context.py`, `stop-guard.py`, and `task-completed-gate.py`. Git branch/diff operations on local repos complete in milliseconds; 5s is generous for slow disks and large repos while being tight enough to prevent indefinite hangs.

**Edge Cases:**
- `subprocess.TimeoutExpired` is a subclass of `Exception` — caught by the existing bare `except Exception` at each call site. The hook degrades gracefully: `git_branch = ""` and `changed_files = []` are already the fallback values.
- On git lock contention (`.git/index.lock` held by another process), the 5s timeout fires and the hook exits cleanly. The compact context output will omit branch and changed-file info for that invocation — acceptable degradation.
- `auto-test.py` uses `auto_test_timeout_ms ÷ 1000` (default 30s) — intentionally higher because pytest suites take longer than git commands. Not changed.
- `safety_check_agent.py` uses `timeout=30` for the `claude --print` subagent call — intentionally higher for LLM latency. Not changed.

**Out of Scope:**
- Changing timeout values in hooks that already have them
- Adding timeout to hooks that don't call subprocess
- Adding separate `subprocess.TimeoutExpired` except clauses (existing `except Exception` is sufficient)
- Configurable timeout for sdlc-compact git calls (YAGNI — 5s is appropriate and consistent)
