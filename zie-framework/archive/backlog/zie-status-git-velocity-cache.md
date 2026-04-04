# zie-status: Cache Release Velocity or Reduce Sequential git tag Calls

## Problem

Every `/zie-status` invocation runs `git tag --sort=-version:refname | head -6` then loops over tag pairs calling `git log -1 --format=%ai <tag>` — up to 5 sequential Bash calls just to display release velocity. This is informational data that doesn't change between status calls within a session.

## Motivation

Up to 5 sequential git subprocess calls for a display-only metric on every `/zie-status` invocation. The velocity metric changes at most once per session (on a release commit). Caching in a session temp file or reducing to a single git log call would eliminate 4 of the 5 subprocess calls.

## Rough Scope

- Replace the per-tag `git log` loop with a single `git log --tags --simplify-by-decoration` call
- Or: cache the velocity result in `/tmp/zie-velocity-<session_id>` and skip recomputation within a session
- Haiku model already handles `/zie-status` so overhead is lower, but still worth fixing
