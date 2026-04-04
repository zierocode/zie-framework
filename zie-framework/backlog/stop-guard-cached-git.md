# stop-guard: Use Session Cache + Faster git status Options

## Problem

`stop-guard.py:56-62` runs `git status --short --untracked-files=all` on every Stop event with no caching. `--untracked-files=all` is the slowest git status scan mode. Other hooks (`sdlc-compact.py`, `failure-context.py`) correctly use `get_cached_git_status` to avoid repeated subprocess calls within a session. Stop-guard is the outlier.

## Motivation

In a long read-only session (planning, reviewing), Stop fires on every Claude response. Each fire spawns a git subprocess with the slowest scan mode despite zero chance of uncommitted changes appearing. Switching to `--untracked-files=no` and using the session cache eliminates the overhead entirely in non-writing sessions.

## Rough Scope

- Import and use `get_cached_git_status` from `utils_io` in `stop-guard.py`
- Change git status flags to `--short --untracked-files=no` (consistent with other hooks)
- Update tests for stop-guard
