# wip-checkpoint counter file not guarded against ValueError

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`wip-checkpoint.py:39` does `int(counter_file.read_text())` without a try/except
for `ValueError`. If the counter file is corrupted (partial write, non-numeric
content), the hook crashes with an unhandled exception and wip-checkpoint silently
stops working for the session.

## Motivation

One-line fix: `int(counter_file.read_text().strip() or "0")` with a fallback, or
wrap in try/except ValueError with reset to 0.
