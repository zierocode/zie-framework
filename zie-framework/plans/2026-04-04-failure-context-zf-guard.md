# Implementation Plan: failure-context — zie-framework Existence Guard

**Slug:** `failure-context-zf-guard`
**Spec:** `specs/2026-04-04-failure-context-zf-guard-design.md`
**Date:** 2026-04-04

## Steps

### 1. Edit `hooks/failure-context.py`

After `cwd = get_cwd()` (line 40), insert the existence guard before `load_config`:

```python
if not (Path(cwd) / "zie-framework").exists():
    sys.exit(0)
```

Add `from pathlib import Path` if not already imported (it is not — add it to
the stdlib imports block at the top).

### 2. Add test — `tests/unit/test_hooks_failure_context.py`

Add a new class `TestNoZieFrameworkDir` with one test:

```python
class TestNoZieFrameworkDir:
    """TC-8: No zie-framework/ dir — hook must exit 0 with no stdout."""

    def test_no_output_when_zf_missing(self, tmp_path):
        # tmp_path has no zie-framework/ subdirectory
        event = {"tool_name": "Bash"}
        result = run_hook(event, tmp_cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout == ""
```

### 3. Verify

```bash
make test-fast   # confirm new test passes + no regressions
make lint        # ruff clean
```

## Affected Files

| File | Change |
|------|--------|
| `hooks/failure-context.py` | +3 lines: `Path` import + existence guard |
| `tests/unit/test_hooks_failure_context.py` | +1 test class (TC-8) |
