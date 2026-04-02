---
slug: audit-hook-outer-guard
status: draft
date: 2026-04-01
---

# Spec: Add Outer Try/Except Guard to session-resume, session-learn, wip-checkpoint

## Problem

Three hooks run live code at module level without an outer `try/except` guard,
violating the two-tier hook safety contract documented in CLAUDE.md:

- `session-resume.py` — `read_event()`, `load_config()`, `parse_roadmap_now()`,
  and `version_file.read_text()` all execute unguarded at module scope. Any
  exception here (malformed event JSON, missing config keys, unreadable files)
  propagates unhandled and kills the hook process.
- `session-learn.py` — `read_event()`, `get_cwd()`, `parse_roadmap_now()`, and
  `atomic_write()` all run unguarded. `atomic_write()` in `utils.py` re-raises
  `OSError` on rename failure (e.g. full disk, permission error), which crashes
  the hook.
- `wip-checkpoint.py` — `read_event()` and subsequent early-exit logic run
  unguarded at module scope.

An unhandled exception in any of these kills the hook process with a non-zero
exit, which can block or degrade the Claude session unexpectedly — exactly the
failure mode the two-tier pattern is designed to prevent.

The reference implementation (`auto-test.py`) guards all top-level logic inside
`if __name__ == "__main__":` with inner `try/except` blocks, ensuring the
process always exits 0.

## Proposed Solution

Wrap each hook's top-level logic in the standard outer guard pattern:

```python
try:
    # all existing module-level logic here
except Exception:
    sys.exit(0)
```

Specific changes per hook:

**`session-resume.py`**: Wrap everything from `event = read_event()` through
the final `print("\n".join(lines))` and drift-detection block in a top-level
`try/except Exception: sys.exit(0)`. The inner env-file write and drift-check
blocks already have their own `except Exception as e: print(...)` handlers —
these remain unchanged as the inner tier.

**`session-learn.py`**: Wrap everything from `event = read_event()` through the
final `call_zie_memory_api` try/except block in a top-level
`try/except Exception: sys.exit(0)`. The existing `except Exception as e:
print(...)` around `call_zie_memory_api` remains as the inner tier.

**`wip-checkpoint.py`**: Wrap everything from `event = read_event()` through
the final `call_zie_memory_api` try/except block in a top-level
`try/except Exception: sys.exit(0)`. The existing `except Exception as e:
print(...)` blocks around counter reads and API calls remain as the inner tier.

No logic changes. No new behaviour. Pure defensive wrapping.

## Acceptance Criteria

- [ ] AC1: `session-resume.py` top-level logic is wrapped in `try/except Exception: sys.exit(0)` — an exception from `read_event()`, `load_config()`, or `parse_roadmap_now()` causes the hook to exit 0, not crash.
- [ ] AC2: `session-learn.py` top-level logic is wrapped in `try/except Exception: sys.exit(0)` — an `OSError` from `atomic_write()` or any other unguarded call causes exit 0, not a crash.
- [ ] AC3: `wip-checkpoint.py` top-level logic is wrapped in `try/except Exception: sys.exit(0)` — an exception from `read_event()` or `get_cwd()` causes exit 0, not a crash.
- [ ] AC4: All existing inner `except Exception as e: print(f"[zie-framework] ...", file=sys.stderr)` handlers are preserved unchanged.
- [ ] AC5: Unit tests cover the outer guard for each hook — inject a bad/empty event JSON and assert the hook exits 0 without raising.
- [ ] AC6: `make test-ci` passes with no regressions.

## Out of Scope

- Refactoring hook logic or extracting helper functions.
- Changing the behaviour of `atomic_write()` in `utils.py`.
- Adding outer guards to any hooks not listed (other hooks are separate items).
- Adding logging to the outer guard catch (bare `sys.exit(0)` is intentional per convention).
