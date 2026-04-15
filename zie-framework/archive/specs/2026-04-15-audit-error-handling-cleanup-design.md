---
date: 2026-04-15
status: approved
slug: audit-error-handling-cleanup
---

# Audit Error Handling Cleanup

## Problem

144 broad `except Exception` blocks across 31 hook files silently swallow errors. Only 16 catches use specific exception types. This makes debugging nearly impossible — failures are invisible.

## Solution

**Phase 1** — Add `sys.stderr.write()` to every bare `except Exception` that currently has no logging. Include hook name, operation, and error message. This is the highest-impact, lowest-risk change.

**Phase 2** — Narrow broad catches to specific types where the operation clearly maps to a known error: `FileNotFoundError` for path reads, `json.JSONDecodeError` for JSON parsing, `OSError`/`PermissionError` for I/O, `subprocess.TimeoutExpired` for subprocess calls.

**Phase 3** — (Out of scope for this spec) Structured JSON error envelope for hook output.

Priority order by bare-except count: stop-handler (11), session-resume (13), intent-sdlc (10), utils_roadmap (12), post-tool-use (4).

## Rough Scope

**In scope:** All 31 hook files under `hooks/`. Phase 1 (stderr logging) and Phase 2 (specific catches). Utility modules (`utils_*.py`) included.

**Out of scope:** Phase 3 JSON envelope, test files, non-hook Python files, behavior changes to hook logic.

## Files Changed

All 31 files with `except Exception` patterns. Highest-priority: `stop-handler.py`, `session-resume.py`, `utils_roadmap.py`, `intent-sdlc.py`, `post-tool-use.py`, `sdlc-compact.py`, `failure-context.py`, `knowledge-hash.py`, `safety-check.py`, `auto-test.py`.