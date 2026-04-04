# Design Spec: Remove Dead sanitize_log_field Copy from utils_roadmap.py

**Slug:** sanitize-log-field-dead-copy
**Date:** 2026-04-04
**Status:** Approved

## Problem

`sanitize_log_field` is defined twice with identical bodies:

- `hooks/utils_roadmap.py:20` — never imported by any file
- `hooks/utils_event.py:32` — imported by `notification-log.py` and `stopfailure-log.py`

The `utils_roadmap` copy is dead code. All `from utils_roadmap import` statements in hooks import only roadmap-specific functions (`parse_roadmap_now`, `parse_roadmap_section_content`, `read_roadmap_cached`) — never `sanitize_log_field`.

## Decision

Remove the dead definition from `utils_roadmap.py`. The canonical location is `utils_event.py`.

No callers need updating — all existing callers already import from `utils_event`.

## Acceptance Criteria

- `sanitize_log_field` does not appear in `utils_roadmap.py`
- `sanitize_log_field` still exists and is unchanged in `utils_event.py`
- No `from utils_roadmap import sanitize_log_field` anywhere in the codebase
- `make test-ci` passes (existing tests cover `sanitize_log_field` via `utils_event` paths)

## Out of Scope

- No new tests needed — function is unchanged, just the dead copy is removed
- No docstring or behavior changes
