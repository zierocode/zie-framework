# Missing outer try/except guard in session-resume, session-learn, wip-checkpoint

**Severity**: High | **Source**: audit-2026-04-01

## Problem

Three hooks run live code at module level without an outer `try/except` guard,
violating the two-tier hook safety contract documented in CLAUDE.md:

- `session-resume.py` — `read_event()`, `load_config()`, `parse_roadmap_now()`,
  `version_file.read_text()` all run unguarded at import time
- `session-learn.py` — `atomic_write()` re-raises `OSError` on rename failure
  (utils.py:187); a full-disk or permission error here crashes the hook
- `wip-checkpoint.py` — event read and early exits run unguarded

An unhandled exception in any of these kills the hook process, which can block
or degrade the Claude session unexpectedly.

## Motivation

CLAUDE.md mandates the two-tier pattern: outer `except Exception → sys.exit(0)`
always. These three hooks predate or missed that refactor. Fix: wrap each
hook's top-level logic in the standard outer guard.
