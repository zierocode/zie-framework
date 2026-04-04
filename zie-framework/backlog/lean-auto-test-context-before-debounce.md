# Backlog: Move auto-test additionalContext emit to after debounce check

**Problem:**
auto-test.py emits its `additionalContext` JSON payload ("Affected test: ..." or
"No test file found...") before running the debounce check. This means context is
injected into every Edit/Write turn even when the debounce will shortly cause a
sys.exit(0) on the next run. "No test file found" is especially wasteful — it fires
on every edit to a non-test file and injects noise when no test run will happen.

**Motivation:**
Hook output is not prompt-cached — every non-empty additionalContext burns live
tokens on that turn. Moving the emit to after the debounce check + test file check
means context only fires when a test run will actually happen. Eliminates noise on
the majority of edits.

**Rough scope:**
- Move `print(json.dumps({"additionalContext": ...}))` call in auto-test.py to after:
  (1) debounce check passes, (2) test file is found
- For "no test file found" case: suppress additionalContext entirely; rely on
  test-failure stdout to carry signal if tests were somehow expected
- Tests: Edit to non-test file → no additionalContext emitted; Edit with matching
  test file after debounce → additionalContext emitted
