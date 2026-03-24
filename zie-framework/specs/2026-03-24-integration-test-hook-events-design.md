---
approved: true
approved_at: 2026-03-24
backlog: backlog/integration-test-hook-events.md
---

# Integration Tests — Mock Claude Code Hook Events End-to-End — Design Spec

**Problem:** Unit tests mock hook internals but never test the full execution path. A hook that parses the wrong JSON key, crashes on a real event payload, or exits with the wrong exit code would pass unit tests but fail in production. Real event format bugs go undetected until Claude Code complains.

**Approach:** Create integration tests that run each hook script as a subprocess with a realistic event JSON payload delivered via stdin, then assert on exit code, stdout, and stderr. Sample event fixtures are stored as JSON files in `tests/integration/fixtures/`. No live Claude Code process required — just the hook scripts and realistic payloads.

**Components:**
- Create: `tests/integration/test_hook_events.py` — one test function per hook (`test_session_resume_hook`, `test_pretooluse_hook`, etc.); each runs the hook as `subprocess.run(["python", "hooks/<name>.py"], input=<event_json>, capture_output=True)`; asserts exit code == 0, stderr contains no unhandled traceback, stdout matches expected pattern
- Create: `tests/integration/fixtures/session_start_event.json` — sample SessionStart event payload
- Create: `tests/integration/fixtures/pretooluse_event.json` — sample PreToolUse event payload
- Create: `tests/integration/fixtures/posttooluse_event.json` — sample PostToolUse event payload
- Create: `tests/integration/fixtures/stop_event.json` — sample Stop event payload
- Create additional fixtures as needed per hook coverage

**Acceptance Criteria:**
- [ ] One integration test per hook script in `hooks/`
- [ ] Each test delivers a realistic event JSON via stdin as a subprocess
- [ ] Tests assert: exit code == 0, no unhandled Python traceback in stderr
- [ ] Tests run via `pytest tests/integration/` with no live Claude Code process
- [ ] Fixtures use realistic payload structure matching Claude Code's actual event format
- [ ] Integration tests run separately from unit tests (`make test-unit` excludes them; `make test` includes them)

**Out of Scope:**
- Testing hook behavior with malformed JSON (covered by existing unit tests)
- Testing Claude's response to hook stdout output
- End-to-end testing with a live Claude Code process
