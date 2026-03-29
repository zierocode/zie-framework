---
approved: true
approved_at: 2026-03-24
backlog: backlog/posttooluse-additionalcontext.md
spec: specs/2026-03-24-posttooluse-additionalcontext-design.md
---

# PostToolUse additionalContext Test File Hints — Implementation Plan

**Goal:** Extend `hooks/auto-test.py` to emit a `hookSpecificOutput.additionalContext` JSON block on stdout after every Write/Edit event, injecting the matched test file path (or a "write one" prompt when no match exists). Context injection fires before the debounce check so Claude always receives the hint, even when the test run is suppressed.

**Architecture:** `find_matching_test()` already resolves the relevant test file — this plan surfaces that result directly to Claude via the `additionalContext` mechanism. No changes to `find_matching_test()` itself, no changes to `hooks.json`, no changes to debounce or test-run logic.

**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/auto-test.py` | Emit `hookSpecificOutput.additionalContext` JSON before debounce check |
| Modify | `tests/unit/test_hooks_auto_test.py` | New class `TestAdditionalContextInjection` with all context-injection cases |

---

## Task 1: Add `hookSpecificOutput` context injection to `auto-test.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- After a Write/Edit event on a file inside cwd, with `test_runner` configured, stdout contains exactly one line of JSON with the form `{"hookSpecificOutput": {"additionalContext": "<string>"}}`
- When `find_matching_test()` returns a path: `additionalContext` is `"Affected test: <absolute_path>"`
- When `find_matching_test()` returns `None`: `additionalContext` is `"No test file found for <filename> — write one"`
- The JSON line appears before any test-run output (pass/fail/timeout messages)
- The JSON line appears even when debounce suppresses the test run
- All existing tests in `test_hooks_auto_test.py` continue to pass unchanged
- No JSON is emitted when the hook exits early (non-Edit/Write tool, missing file_path, missing zie-framework dir, missing test_runner, out-of-cwd path)

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `tests/unit/test_hooks_auto_test.py`

---

### Step 1: Write failing tests (RED)

Add a new class `TestAdditionalContextInjection` to `tests/unit/test_hooks_auto_test.py`.

```python
# tests/unit/test_hooks_auto_test.py — append after TestFindMatchingTestEdgeCases


def parse_additional_context(stdout: str) -> str | None:
    """Extract the additionalContext string from hook stdout, or None if absent."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            hso = obj.get("hookSpecificOutput", {})
            if "additionalContext" in hso:
                return hso["additionalContext"]
        except (json.JSONDecodeError, AttributeError):
            continue
    return None


class TestAdditionalContextInjection:
    """hookSpecificOutput.additionalContext must be emitted after Write/Edit."""

    @pytest.fixture(autouse=True)
    def _cleanup_debounce(self, tmp_path):
        yield
        p = project_tmp_path("last-test", tmp_path.name)
        if p.exists():
            p.unlink()

    # --- match found ---

    def test_context_emitted_with_matching_test(self, tmp_path):
        """When a test file exists for the changed module, context names it."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_payments.py"
        test_file.write_text("# test")
        changed = str(cwd / "src" / "payments.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None, f"No additionalContext found in stdout: {r.stdout!r}"
        assert ctx.startswith("Affected test: "), f"Unexpected context prefix: {ctx!r}"
        assert "test_payments.py" in ctx

    def test_context_contains_absolute_path(self, tmp_path):
        """Matched test path in context must be absolute."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_utils.py"
        test_file.write_text("# test")
        changed = str(cwd / "src" / "utils.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        path_part = ctx.removeprefix("Affected test: ")
        assert Path(path_part).is_absolute(), f"Path is not absolute: {path_part!r}"

    def test_context_emitted_for_write_tool(self, tmp_path):
        """Context injection fires on Write tool, not only Edit."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        (tests_dir / "test_models.py").write_text("# test")
        changed = str(cwd / "src" / "models.py")
        r = run_hook({"tool_name": "Write", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "test_models.py" in ctx

    # --- no match ---

    def test_context_write_one_when_no_test_found(self, tmp_path):
        """When no matching test exists, context prompts Claude to write one."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "billing.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None, f"No additionalContext found in stdout: {r.stdout!r}"
        assert "billing.py" in ctx
        assert "write one" in ctx

    def test_context_write_one_message_format(self, tmp_path):
        """'write one' message must match exact format from spec."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "stripe.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx == "No test file found for stripe.py — write one", (
            f"Message format mismatch: {ctx!r}"
        )

    # --- debounce does not suppress context ---

    def test_context_emitted_even_when_debounced(self, tmp_path):
        """Context injection fires before debounce check — hint always reaches Claude."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        tests_dir = cwd / "tests" / "unit"
        tests_dir.mkdir(parents=True)
        test_file = tests_dir / "test_payments.py"
        test_file.write_text("# test")
        # Write a fresh debounce file to activate the debounce window
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("payments.py")
        changed = str(cwd / "src" / "payments.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        # Test run must be suppressed
        assert "[zie-framework] Tests" not in r.stdout
        # But context must still be present
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None, (
            f"Context missing when debounced — must be emitted before debounce check. "
            f"stdout: {r.stdout!r}"
        )
        assert "test_payments.py" in ctx

    def test_no_match_context_emitted_even_when_debounced(self, tmp_path):
        """'write one' context also fires when debounced."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest", "auto_test_debounce_ms": 999999})
        (cwd / "tests").mkdir()
        debounce = project_tmp_path("last-test", cwd.name)
        debounce.write_text("billing.py")
        changed = str(cwd / "src" / "billing.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "write one" in ctx

    # --- no context on early exits ---

    def test_no_context_when_no_test_runner(self, tmp_path):
        """No context emitted when test_runner is absent — hook exits early."""
        cwd = make_cwd(tmp_path, config={})
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/some/file.py"}},
                     tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    def test_no_context_when_not_edit_or_write(self, tmp_path):
        """No context emitted for non-Edit/Write tools."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Bash", "tool_input": {"command": "ls"}}, tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    def test_no_context_when_path_outside_cwd(self, tmp_path):
        """No context emitted when file_path is outside cwd."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": "/etc/passwd"}},
                     tmp_cwd=cwd)
        assert parse_additional_context(r.stdout) is None

    # --- JSON structure ---

    def test_additional_context_valid_json_line(self, tmp_path):
        """The hookSpecificOutput line must be valid JSON parseable independently."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "auth.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        json_lines = []
        for line in r.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if "hookSpecificOutput" in obj:
                    json_lines.append(obj)
            except json.JSONDecodeError:
                pass
        assert len(json_lines) == 1, (
            f"Expected exactly one hookSpecificOutput JSON line, found {len(json_lines)}: "
            f"{r.stdout!r}"
        )
        assert "additionalContext" in json_lines[0]["hookSpecificOutput"]

    def test_additional_context_is_string(self, tmp_path):
        """additionalContext value must be a string, not a dict or list."""
        cwd = make_cwd(tmp_path, config={"test_runner": "pytest"})
        (cwd / "tests").mkdir()
        changed = str(cwd / "src" / "auth.py")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert isinstance(ctx, str), f"additionalContext must be str, got {type(ctx)}: {ctx!r}"

    # --- vitest runner ---

    def test_context_emitted_for_vitest_match(self, tmp_path):
        """Context injection works for vitest runner when .test.ts file exists."""
        cwd = make_cwd(tmp_path, config={"test_runner": "vitest"})
        src_dir = cwd / "src"
        src_dir.mkdir()
        test_file = src_dir / "button.test.ts"
        test_file.write_text("// test")
        changed = str(src_dir / "button.tsx")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "button.test.ts" in ctx

    def test_context_write_one_for_vitest_no_match(self, tmp_path):
        """'write one' context emitted for vitest when no .test.ts found."""
        cwd = make_cwd(tmp_path, config={"test_runner": "vitest"})
        (cwd / "src").mkdir()
        changed = str(cwd / "src" / "modal.tsx")
        r = run_hook({"tool_name": "Edit", "tool_input": {"file_path": changed}}, tmp_cwd=cwd)
        ctx = parse_additional_context(r.stdout)
        assert ctx is not None
        assert "modal.tsx" in ctx
        assert "write one" in ctx
```

Run: `make test-unit` — must FAIL (no `hookSpecificOutput` JSON emitted yet, `parse_additional_context` returns `None` where a value is expected).

---

### Step 2: Implement (GREEN)

The change inserts a context-injection block in `hooks/auto-test.py` after the `is_relative_to` guard (so out-of-cwd paths still emit no context, consistent with the spec's preferred simplicity), and before the debounce check block. Move the `changed` and `cwd_resolved` resolve lines up to immediately after the `test_runner` config read so they are available for context injection.

Exact diff:

```python
# hooks/auto-test.py
# ── current ordering after test_runner guard (lines 83-112) ──────────────────
#
#   # Debounce check
#   debounce_ms = ...
#   ...
#   safe_write_tmp(debounce_file, file_path)
#
#   changed = Path(file_path).resolve()
#   cwd_resolved = cwd.resolve()
#   if not changed.is_relative_to(cwd_resolved):
#       sys.exit(0)
#
#   timeout = ...
#   # Build test command
#   ...
#
# ── new ordering ─────────────────────────────────────────────────────────────
#
#   changed = Path(file_path).resolve()           # MOVED UP
#   cwd_resolved = cwd.resolve()                  # MOVED UP
#   if not changed.is_relative_to(cwd_resolved):  # MOVED UP
#       sys.exit(0)
#
#   # additionalContext injection                  # NEW BLOCK
#   matching_test_for_context = find_matching_test(changed, test_runner, cwd)
#   if matching_test_for_context:
#       additional_context = f"Affected test: {matching_test_for_context}"
#   else:
#       additional_context = f"No test file found for {changed.name} — write one"
#   print(json.dumps({"hookSpecificOutput": {"additionalContext": additional_context}}))
#
#   # Debounce check                               # UNCHANGED, just moved after context
#   debounce_ms = ...
#   ...
```

Full replacement of the relevant section (lines 83–112 in the current file):

```python
    changed = Path(file_path).resolve()
    cwd_resolved = cwd.resolve()
    if not changed.is_relative_to(cwd_resolved):
        sys.exit(0)

    # additionalContext injection — fires before debounce so Claude always gets the hint
    matching_test_for_context = find_matching_test(changed, test_runner, cwd)
    if matching_test_for_context:
        additional_context = f"Affected test: {matching_test_for_context}"
    else:
        additional_context = f"No test file found for {changed.name} — write one"
    print(json.dumps({"hookSpecificOutput": {"additionalContext": additional_context}}))

    # Debounce: skip test run if same file was tested recently (within debounce window)
    debounce_ms = config.get("auto_test_debounce_ms", 3000)
    debounce_file = project_tmp_path("last-test", cwd.name)
    if debounce_file.exists():
        last_run = debounce_file.stat().st_mtime
        if (time.time() - last_run) < (debounce_ms / 1000):
            sys.exit(0)
    safe_write_tmp(debounce_file, file_path)

    timeout = config.get("auto_test_timeout_ms", 30000) // 1000
```

The `# Build test command` block that follows (the `if test_runner == "pytest"` chain) keeps its existing `find_matching_test` call for building `cmd` — no change needed there. That call is a second independent lookup, which is fine: it is only reached when the debounce is not active.

The stdout JSON format emitted is:

```json
{"hookSpecificOutput": {"additionalContext": "Affected test: /abs/path/to/tests/unit/test_payments.py"}}
```

or when no match:

```json
{"hookSpecificOutput": {"additionalContext": "No test file found for billing.py — write one"}}
```

Run: `make test-unit` — must PASS (all new and existing tests green).

---

### Step 3: Refactor

No structural changes needed. Confirm two things by inspection:

1. The `hookSpecificOutput` `print()` call appears before `debounce_file.exists()` — guaranteed by the new ordering above.
2. The `find_matching_test` call inside the test-command build block (the `if test_runner == "pytest"` chain) is still present and unchanged — it uses a local variable `matching_test` scoped to that block, distinct from `matching_test_for_context` used for context injection.

If the local variable name collision is unclear, rename the context-injection variable to `_ctx_test` for clarity. Either name is acceptable as long as the two lookup results do not alias each other.

Run: `make test-unit` — still PASS.

---

## Regression Verification

Run the full unit suite to confirm no existing test classes regress:

```bash
make test-unit
```

Expected: all pre-existing classes pass:

- `TestAutoTestGuardrails` — early-exit paths unchanged; these events never reach the context-injection block
- `TestAutoTestDebounce` — debounce suppresses test run; new tests confirm context still emits, old `assert "[zie-framework] Tests" not in r.stdout` remains true
- `TestFindMatchingTest` — direct unit tests on the function; function is not modified
- `TestAutoTestRunnerSelection` — unknown runner exits before context block; no context emitted
- `TestAutoTestDebounceBoundary` — boundary assertions on test-run suppression; unaffected
- `TestAutoTestAtomicDebounceWrite` — safe_write_tmp and symlink guards; position in file unchanged
- `TestAutoTestFilePathCwdValidation` — out-of-cwd paths exit before context block; `assert r.stdout.strip() == ""` remains valid because the only stdout for those paths is nothing (context injection is after the `is_relative_to` guard)
- `TestAutoTestConfigParseWarning` — stderr warning tests; unaffected

---

*Commit: `git add hooks/auto-test.py tests/unit/test_hooks_auto_test.py && git commit -m "feat: emit additionalContext test file hint in auto-test hook"`*
