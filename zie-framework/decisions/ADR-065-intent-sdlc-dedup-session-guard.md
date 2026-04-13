---
id: ADR-065
title: Content-based dedup cache with session_id=="default" test guard
status: accepted
date: 2026-04-13
---

## Context

`intent-sdlc.py` re-injects SDLC context on every user message. When context is unchanged (same ROADMAP state, same stage), re-injection wastes tokens and is noisy. Hooks are separate subprocesses — module-level dict doesn't persist between invocations. Session caching must be file-based.

Test isolation problem: pytest test helpers hardcode `session_id="default"` as the fallback value. File-based dedup keyed by session_id persisted between test runs, causing `test_plan_intent_detected_thai` to fail when a dedup file from a previous test blocked emission.

## Decision

1. **Content-based dedup**: Use `/tmp/zie-<project>-intent-dedup-<safe_session_id>-<cwd_hash>` files. On emit, read the file — if content matches, skip (no output). If differs, write new content and emit. TTL = 600s.

2. **CWD hash**: Include full CWD path hash (not just `cwd.name`) in the filename to prevent cross-test-run collisions when pytest creates directories with the same base name.

3. **Test guard**: Skip dedup entirely when `session_id == "default"`. Real Claude sessions always have unique session_ids; `"default"` is the stdlib fallback for missing `CLAUDE_SESSION_ID`. This guard preserves test determinism without requiring test teardown.

## Consequences

- Context re-injection suppressed within same session window (10min TTL)
- Different sessions always get fresh context (no cross-session bleed)
- Tests using `session_id="default"` bypass dedup — no cache pollution across test runs
- Pattern extends ADR-062 (once-per-session flags) with content comparison + TTL
