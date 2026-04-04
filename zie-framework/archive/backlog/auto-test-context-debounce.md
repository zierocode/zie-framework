# auto-test: Move additionalContext Injection After Debounce Check

## Problem

`auto-test.py` prints the `additionalContext` JSON ("Affected test: X" or "No test file found for X") at lines 148-153 unconditionally, before the debounce check at line 164. During rapid TDD edits within the debounce window, the test run is skipped — but the context injection still fires. Claude receives the same test-file hint on every rapid-fire edit with zero new information.

## Motivation

In a typical RED/GREEN loop with 10 quick edits per minute, the debounce fires 8-9 times but the context injection fires all 10. Each duplicate injection consumes context window space and adds token cost to every subsequent turn. Moving the print inside the test-run result block eliminates all debounced injections.

## Rough Scope

- Move `additionalContext` stdout print to after the debounce check (only emit when tests actually ran)
- Update tests that assert context injection happens
- Impact: eliminates context inflation during active TDD sessions
