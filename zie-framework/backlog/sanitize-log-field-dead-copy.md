# Remove Dead sanitize_log_field Copy from utils_roadmap.py

## Problem

`sanitize_log_field` is defined in both `utils_roadmap.py:20` and `utils_event.py:32` with identical bodies. All hooks that use it (`notification-log.py`, `stopfailure-log.py`) import it from `utils_event` — the copy in `utils_roadmap.py` is never imported and is dead code.

## Motivation

Dead function creates silent divergence risk — a future edit to one copy won't propagate to the other. Clean removal keeps the codebase honest about where each utility lives.

## Rough Scope

- Remove `sanitize_log_field` definition from `utils_roadmap.py`
- Verify no file imports it from `utils_roadmap`
- One-line removal + test verification
