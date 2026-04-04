# Plan: Remove Dead sanitize_log_field Copy from utils_roadmap.py

**Slug:** sanitize-log-field-dead-copy
**Spec:** `specs/2026-04-04-sanitize-log-field-dead-copy-design.md`
**Date:** 2026-04-04

## Steps

### 1. Remove dead function from utils_roadmap.py

Delete lines 20–22 from `hooks/utils_roadmap.py`:

```python
def sanitize_log_field(value: object) -> str:
    """Strip ASCII control characters from a log field value."""
    return re.sub(r'[\x00-\x1f\x7f]', '?', str(value))
```

The blank line before `parse_roadmap_section` (previously line 24) becomes the separator after the `SDLC_STAGES` block.

### 2. Verify

```bash
grep -n "sanitize_log_field" hooks/utils_roadmap.py   # expect: no output
grep -n "sanitize_log_field" hooks/utils_event.py     # expect: line 32 definition
make lint
make test-ci
```

## Risk

None — dead code removal with no callers affected.

## Estimated Diff

~4 lines deleted from `hooks/utils_roadmap.py`.
