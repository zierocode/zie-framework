---
slug: audit-cache-write-silent-failure
status: approved
approved: true
date: 2026-04-01
---

# Plan: Replace bare `except: pass` in Cache Write Helpers

## Overview

Replace silent `except Exception: pass` in `write_roadmap_cache` and
`write_git_status_cache` (both in `hooks/utils.py`) with the standard
two-tier hook stderr log pattern. Cache write failures (full disk, permission
error) will now be visible in Claude's stderr output without blocking Claude.

**Spec:** `zie-framework/specs/2026-04-01-audit-cache-write-silent-failure-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `write_roadmap_cache` failure logs `[zie-framework] write_roadmap_cache: <error>` to stderr |
| AC-2 | `write_git_status_cache` failure logs `[zie-framework] write_git_status_cache: <error>` to stderr |
| AC-3 | Both functions still return normally (no raise) — caller is never blocked |
| AC-4 | Both unit tests pass; `make test-ci` exits 0 |

---

## Tasks

### Task 1 — Write failing tests (RED)

**File:** `tests/unit/test_utils.py`

Add to the existing test file:

```python
class TestCacheWriteStderrLogs:
    def test_write_roadmap_cache_logs_on_mkdir_error(self, tmp_path, capsys, monkeypatch):
        """AC-1: mkdir failure → stderr log, no raise."""
        from hooks.utils import write_roadmap_cache
        # Patch Path.mkdir to raise PermissionError
        import pathlib
        original_mkdir = pathlib.Path.mkdir

        def bad_mkdir(self, **kwargs):
            raise PermissionError("no permission")

        monkeypatch.setattr(pathlib.Path, "mkdir", bad_mkdir)
        # Must not raise
        write_roadmap_cache("test-session", "content")
        err = capsys.readouterr().err
        assert "write_roadmap_cache" in err
        assert "no permission" in err

    def test_write_git_status_cache_logs_on_mkdir_error(self, tmp_path, capsys, monkeypatch):
        """AC-2: mkdir failure → stderr log, no raise."""
        from hooks.utils import write_git_status_cache
        import pathlib

        def bad_mkdir(self, **kwargs):
            raise PermissionError("disk full")

        monkeypatch.setattr(pathlib.Path, "mkdir", bad_mkdir)
        # Must not raise
        write_git_status_cache("test-session", "log", "content")
        err = capsys.readouterr().err
        assert "write_git_status_cache" in err
        assert "disk full" in err
```

Run `make test-unit` — RED confirmed (2 failures).

---

### Task 2 — Implement (GREEN)

**File:** `hooks/utils.py`

**Change 1 — `write_roadmap_cache` (lines 293–294):**

Before:
```python
    except Exception:
        pass
```

After:
```python
    except Exception as e:
        print(f"[zie-framework] write_roadmap_cache: {e}", file=sys.stderr)
```

**Change 2 — `write_git_status_cache` (lines 328–329):**

Before:
```python
    except Exception:
        pass
```

After:
```python
    except Exception as e:
        print(f"[zie-framework] write_git_status_cache: {e}", file=sys.stderr)
```

Run `make test-unit` — GREEN.

---

### Task 3 — Full suite gate

Run `make test-ci` — must exit 0.

---

## Test Strategy

| Layer | Test | AC |
|-------|------|----|
| Unit | test_write_roadmap_cache_logs_on_mkdir_error | AC-1, AC-3 |
| Unit | test_write_git_status_cache_logs_on_mkdir_error | AC-2, AC-3 |

---

## Rollout

1. Write failing tests (Task 1) — RED.
2. Apply two str_replace edits to utils.py (Task 2) — GREEN.
3. Run `make test-ci` (Task 3) — no regression.
4. Mark ROADMAP Done.

**Note:** `write_roadmap_cache` also has a path injection issue (hardcoded `/tmp/zie-{session_id}`)
being addressed separately by `audit-roadmap-cache-sanitize`. These plans do not conflict — this
plan only changes exception handling, leaving the path construction intact.
