# Design Spec: zie-status Git Velocity Cache

**Slug:** `zie-status-git-velocity-cache`
**Date:** 2026-04-04
**Status:** Approved

## Problem

Every `/zie-status` invocation runs `git tag --sort=-version:refname | head -6`
followed by up to 5 sequential `git log -1 --format=%ai <tag>` calls — one per
tag pair. That is up to 6 Bash subprocesses for a display-only metric that
changes at most once per session (when a release is cut).

## Goal

Reduce velocity subprocess calls from up to 6 down to 1, with no loss of
displayed information.

## Chosen Approach: Single `git log` Call (Approach A)

Replace the two-phase shell loop with one command that retrieves both tag names
and their commit dates in a single pass:

```bash
git log --tags --simplify-by-decoration --pretty="%D %ai" | \
  grep -oP '(?:tag: )(v?[0-9]+\.[0-9]+\.[0-9]+).*\K(?<=\s)\d{4}-\d{2}-\d{2}' 
```

More readable alternative (what the command will actually use):

```bash
git log --tags --simplify-by-decoration --pretty="%D|%ai" | \
  grep -E 'tag: v?[0-9]+\.[0-9]+\.[0-9]+' | head -6
```

Each output line contains the ref decorations and the author date. Claude
parses the semver tag name and ISO date from each line, computes intervals, and
formats the velocity string — identical output to the current approach.

## Acceptance Criteria

| # | Criterion |
| --- | --- |
| AC-1 | `/zie-status` velocity section issues exactly **1** Bash call (was up to 6) |
| AC-2 | Velocity string format is unchanged: `"Velocity (last N): Xd, Yd, …"` |
| AC-3 | "not enough releases yet" path still works when fewer than 2 semver tags exist |
| AC-4 | Change is **markdown-only** — no Python hook or config touched |
| AC-5 | Existing `/zie-status` tests (output format, section presence) continue to pass |

## Out of Scope

- Session-level temp-file caching (`/tmp/zie-velocity-<session_id>`)
- Changes to `auto-test.py`, `failure-context.py`, or any Python hook
- Changes to `zie-framework/.config`

## Impact

- **File changed:** `commands/zie-status.md` (step 6 only)
- **Risk:** Low — display-only, no state mutation, single Bash call is well-supported on macOS and Linux git
