# Silent exception swallow in write_roadmap_cache / write_git_status_cache

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`write_roadmap_cache` (utils.py:292–294) and `write_git_status_cache`
(utils.py:328–329) both use bare `except: pass` — no stderr log, no return
value distinction. A cache write failure (full disk, permission error) is
completely invisible.

The ADR-defined two-tier hook convention requires inner operation failures to
log to stderr: `except Exception as e: print(f"[zie-framework] <name>: {e}",
file=sys.stderr)`.

## Motivation

Replace `except: pass` with the standard stderr log pattern in both functions.
This makes cache degradation visible without blocking Claude.
