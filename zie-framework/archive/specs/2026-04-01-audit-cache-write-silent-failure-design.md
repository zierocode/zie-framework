---
slug: audit-cache-write-silent-failure
status: approved
date: 2026-04-01
---
# Spec: Log Cache Write Failures to Stderr

## Problem

`write_roadmap_cache` (`hooks/utils.py:287–294`) and `write_git_status_cache`
(`hooks/utils.py:316–329`) both swallow all exceptions with `except Exception: pass`.
A failure during cache write — full disk, permission error, unexpected path
issue — is completely invisible. There is no signal to the developer that cache
degradation is occurring.

The ADR-defined two-tier hook convention requires inner operation failures to
log to stderr:

```python
except Exception as e:
    print(f"[zie-framework] <name>: {e}", file=sys.stderr)
```

Both functions currently violate this convention.

## Components

- `hooks/utils.py` — `write_roadmap_cache` (lines 287–294), `write_git_status_cache` (lines 316–329) — modify existing

## Proposed Solution

Replace the `except Exception: pass` in both functions with the standard stderr
log pattern. No other behavior changes: both functions still return `None` on
failure and callers are unaffected. Claude is never blocked.

```python
# write_roadmap_cache — before
except Exception:
    pass

# write_roadmap_cache — after
except Exception as e:
    print(f"[zie-framework] cache-write: {e}", file=sys.stderr)
```

```python
# write_git_status_cache — before
except Exception:
    pass

# write_git_status_cache — after
except Exception as e:
    print(f"[zie-framework] cache-write: {e}", file=sys.stderr)
```

This is a 2-line change per function (4 lines total). The docstring of
`write_git_status_cache` also states "Silently ignores all errors" — that
comment must be updated to reflect the new logging behavior.

## Acceptance Criteria

- [ ] AC1: `write_roadmap_cache` replaces `except Exception: pass` with `except Exception as e: print(f"[zie-framework] cache-write: {e}", file=sys.stderr)`
- [ ] AC2: `write_git_status_cache` replaces `except Exception: pass` with `except Exception as e: print(f"[zie-framework] cache-write: {e}", file=sys.stderr)`
- [ ] AC3: The docstring of `write_git_status_cache` no longer claims the function "silently ignores all errors"
- [ ] AC4: Both functions still return `None` on failure — no new exceptions propagate to callers
- [ ] AC5: Unit tests verify that a write failure (mocked `Path.write_text` raising `OSError`) causes the expected stderr message and does not raise
- [ ] AC6: `make test-ci` passes with no regressions

## Out of Scope

- Changing the return type of either function (both remain `None`-returning)
- Adding retry logic or fallback write paths
- Modifying `get_cached_roadmap`, `get_cached_git_status`, or any read-path cache functions
- Changing the log prefix format beyond `[zie-framework] cache-write:`
- Any other `except: pass` patterns elsewhere in `utils.py` (separate audit items)
