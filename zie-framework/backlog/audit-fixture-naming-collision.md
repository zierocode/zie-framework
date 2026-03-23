# Fixture naming collision: `_cleanup_debounce` × 3 in test_hooks_auto_test.py

**Severity**: Medium | **Source**: audit-2026-03-24

## Problem

Three `autouse` fixtures named `_cleanup_debounce` exist in different test
classes within `test_hooks_auto_test.py` (lines 63, 120, 137). pytest's name
resolution may silently shadow one fixture with another, leading to incorrect
teardown — debounce files not cleaned up and state bleeding between test classes.

## Motivation

Fixtures should be uniquely named per scope. Rename to `_cleanup_debounce_basic`,
`_cleanup_debounce_timeout`, etc. or scope them to `conftest.py`.
