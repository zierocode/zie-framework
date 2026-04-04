# TOCTOU race condition on /tmp debounce file

**Severity**: High | **Source**: audit-2026-03-24

## Problem

`auto-test.py` checks debounce file existence and mtime, then writes — unatomic.
The file path `/tmp/zie-{project}-last-test` is predictable. A concurrent
session or local user can race between the check and the write, bypassing
debounce and causing multiple test runs to fire simultaneously.

## Motivation

Debounce logic is critical for performance in busy sessions. A bypassed debounce
floods the terminal with test output mid-edit. Fix: use atomic write (write to
temp, then rename) and consider OS file locking.
