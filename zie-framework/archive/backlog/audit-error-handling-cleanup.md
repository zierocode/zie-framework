---
tags: [debt]
---

# Replace Silent Error Swallowing with Structured Logging

## Problem

34% of all except blocks silently swallow errors (`except Exception: pass` or `sys.exit(0)`). 90% use broad `except Exception` (144 instances) vs only 16 specific catches. This makes debugging nearly impossible — errors are invisible.

## Motivation

External validation confirms structured error reporting is essential for observability in Claude Code hooks. The current pattern masks real failures and makes incident diagnosis extremely difficult.

## Rough Scope

- Phase 1: Add `sys.stderr.write()` to all bare `except` blocks with context (hook name, operation, error message)
- Phase 2: Replace broad `except Exception` with specific catches where feasible (FileNotFoundError, json.JSONDecodeError, etc.)
- Phase 3: Introduce structured JSON error envelope for hook output
- Priority order: stop-handler (11), session-resume (13), intent-sdlc (10), utils_roadmap (12), post-tool-use (4)