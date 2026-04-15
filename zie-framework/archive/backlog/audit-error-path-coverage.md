---
tags: [debt]
---

# Add Error-Path Test Coverage for Hook Modules

## Problem

35 hook modules have zero error-path test coverage — when exceptions occur, there are no tests verifying the fallback/recovery behavior. This means silent failures discovered in the audit (34% of except blocks swallow errors) have no regression safety net.

## Motivation

The audit found stop-handler (11 bare excepts), session-resume (13 except blocks), intent-sdlc (10), and utils_roadmap (12) all silently swallow errors. Without error-path tests, any fix to improve error handling risks breaking the silent fallback paths.

## Rough Scope

- Add `@pytest.mark.error_path` tests for the 15 modules with no error-path coverage
- Priority: stop-handler, session-resume, intent-sdlc, utils_roadmap, auto-test
- Each test should verify graceful degradation when dependencies are missing