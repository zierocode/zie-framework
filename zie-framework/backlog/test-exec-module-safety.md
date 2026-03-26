# quality: fix fragile exec_module test pattern and bare except

## Problem

Two test quality issues in the test suite:

1. `test_hooks_intent_detect.py:100-114` uses `importlib.util.exec_module` +
   bare `except SystemExit: pass` to load hooks as modules. This mutates
   `sys.stdin` and `os.environ` directly; if exec_module raises a non-SystemExit
   exception, the `os.environ.clear()` + `os.environ.update()` cleanup is not
   atomic and can corrupt the environment for other tests.

2. `test_hooks_auto_test.py:179, 616` has bare `except: pass` that swallows
   all exceptions in fixture cleanup and JSON parsing loops. If cleanup fails,
   the test continues with no signal.

## Motivation

- **Severity**: High
- **Source**: /zie-audit 2026-03-26 findings #8, #9
- These patterns can cause cascading test failures that are hard to diagnose

## Scope

- Replace exec_module pattern with subprocess-based testing (consistent with
  other hook tests)
- Replace bare `except: pass` with specific exception types
