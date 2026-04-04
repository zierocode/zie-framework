# Plan: auto-test: Move additionalContext Injection After Debounce Check

status: approved

## Tasks

- [ ] Task 1 — RED: add failing test for AC-1 (debounce suppresses context injection)
  - In `tests/unit/test_hooks_auto_test.py`, extend
    `TestAutoTestDebounce.test_debounce_suppresses_rapid_second_call` to also assert
    `"additionalContext" not in r.stdout`.
  - Run `make test-fast` — expect this assertion to FAIL (current code emits context before
    debounce).

- [ ] Task 2 — GREEN: move the `additionalContext` print in `hooks/auto-test.py`
  - Remove the three-line block at lines 147–153:
    ```python
    # additionalContext injection — fires before debounce so Claude always gets the hint
    _ctx_test = find_matching_test(changed, test_runner, cwd)
    if _ctx_test:
        _additional_context = f"Affected test: {_ctx_test}"
    else:
        _additional_context = f"No test file found for {changed.name} — write one"
    print(json.dumps({"additionalContext": _additional_context}))
    ```
  - Insert equivalent block immediately after `safe_write_tmp(debounce_file, file_path)`
    (currently line 168), before the `auto_test_timeout_ms` assignment:
    ```python
    # additionalContext injection — only emit when tests will actually run
    _ctx_test = find_matching_test(changed, test_runner, cwd)
    if _ctx_test:
        _additional_context = f"Affected test: {_ctx_test}"
    else:
        _additional_context = f"No test file found for {changed.name} — write one"
    print(json.dumps({"additionalContext": _additional_context}))
    ```
  - Run `make test-fast` — expect RED test to go GREEN; all existing context-injection tests
    still pass.

- [ ] Task 3 — REFACTOR: remove duplicate `find_matching_test` call for pytest cmd building
  - After the move in Task 2, `find_matching_test` is called twice: once for
    `additionalContext` and once inside `if test_runner == "pytest"` at line 176.
  - Reuse `_ctx_test` in the pytest branch:
    ```python
    if test_runner == "pytest":
        matching_test = _ctx_test  # already resolved above
        ...
    ```
  - Run `make test-fast` — all tests pass, no behaviour change.

- [ ] Task 4 — VERIFY: full suite + lint
  - `make lint` — no violations.
  - `make test-ci` — all tests pass, coverage gate met.

## Test Strategy

- **Unit (RED first)**: extend `test_debounce_suppresses_rapid_second_call` in
  `tests/unit/test_hooks_auto_test.py` — asserts `additionalContext` absent when debounce
  fires.
- **Regression**: entire `TestAdditionalContextInjection` class must continue passing —
  confirms non-debounced path still emits exactly one context line.
- **No integration tests needed** — change is purely structural (print reordering).

## Files to Change

| File | Change |
| --- | --- |
| `hooks/auto-test.py` | Move `additionalContext` print block from pre-debounce (lines 147–153) to post-debounce (after line 168); reuse `_ctx_test` in pytest command builder |
| `tests/unit/test_hooks_auto_test.py` | Extend `test_debounce_suppresses_rapid_second_call` to assert `additionalContext` absent; no other test changes needed |
