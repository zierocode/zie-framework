# ADR-016: debounce_ms=0 Means Disabled — Guard with `> 0`

Date: 2026-03-24
Status: Accepted

## Context

`auto-test.py` reads `auto_test_debounce_ms` from `.config` and uses it to
suppress rapid re-runs. The original guard was:

```python
if debounce_file.exists():
    if (time.time() - last_run) < (debounce_ms / 1000):
        sys.exit(0)
```

With `debounce_ms=0`, the condition becomes `elapsed < 0.0`. This should never
be true, but APFS/HFS+ can round file modification timestamps, making a freshly
written file appear to have a mtime slightly ahead of `time.time()`, yielding a
small negative elapsed and a spurious suppression.

## Decision

Guard the entire debounce block with `if debounce_ms > 0`:

```python
if debounce_ms > 0 and debounce_file.exists():
    if (time.time() - last_run) < (debounce_ms / 1000):
        sys.exit(0)
```

`debounce_ms=0` is the canonical way to disable debouncing in tests and configs.

## Consequences

**Positive:** `debounce_ms=0` reliably disables the debounce window regardless of
filesystem clock precision; test assertions about symlink detection and counter
writes are now stable.
**Negative:** None — the old behaviour was unintentional.
**Neutral:** Any future time-based guards in hooks should apply the same `> 0`
pattern.
