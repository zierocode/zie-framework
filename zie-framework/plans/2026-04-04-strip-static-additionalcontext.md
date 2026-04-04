# Plan: Strip Static Boilerplate from Per-Event additionalContext
status: approved

## Tasks

- [ ] **RED**: Add `test_no_quick_fix_string` to `test_hooks_failure_context.py`
  — assert `"Quick fix:"` is NOT in `additionalContext`. Confirm it fails.

- [ ] **GREEN**: Edit `hooks/failure-context.py` — remove the static `"Quick fix: ..."` line
  from `context_string`. Test passes.

- [ ] **RED**: Add `test_no_sdlc_restored_header` to `test_hooks_sdlc_compact.py`
  — assert `"SDLC state restored after context compaction"` is NOT in PostCompact
  `additionalContext`. Confirm it fails.

- [ ] **GREEN**: Edit `hooks/sdlc-compact.py` — remove the static header line
  `"[zie-framework] SDLC state restored after context compaction."` from the
  PostCompact `lines` list. Test passes.

- [ ] **RED**: Add `test_no_context_md_path_hint` to `test_hooks_subagent_context.py`
  — assert `"see zie-framework/project/context.md"` is NOT in payload. Confirm it fails.

- [ ] **GREEN**: Edit `hooks/subagent-context.py` — remove the `" (see zie-framework/project/context.md)"`
  suffix from the `payload` string. Test passes.

- [ ] **GREEN**: Update `test_hooks_failure_context.py` line 78 — change
  `assert "make test-unit" in data["additionalContext"]` to assert it is NOT
  present (or delete the test case if it exclusively tests the removed string).

- [ ] **CLAUDE.md**: Add **Hook Context Hints** section after the Hook Configuration
  table in `CLAUDE.md` with the three removed static strings.

- [ ] **REFACTOR**: Run `make test-fast` — confirm all unit tests pass with no
  regressions.

- [ ] **VERIFY**: Run `make lint` — confirm no lint errors.

## Files to Change

| File | Change |
| ---- | ------ |
| `hooks/failure-context.py` | Remove `"Quick fix: run \`make test-unit\` ..."` line from `context_string` |
| `hooks/sdlc-compact.py` | Remove `"[zie-framework] SDLC state restored after context compaction."` from PostCompact `lines` |
| `hooks/subagent-context.py` | Remove `"(see zie-framework/project/context.md)"` suffix from `payload` |
| `CLAUDE.md` | Add **Hook Context Hints** section with all three removed strings |
| `tests/unit/test_hooks_failure_context.py` | Replace/delete assertion on `"make test-unit"`; add negative assertion for `"Quick fix:"` |
| `tests/unit/test_hooks_sdlc_compact.py` | Add negative assertion for `"SDLC state restored after context compaction"` |
| `tests/unit/test_hooks_subagent_context.py` | Add negative assertion for `"see zie-framework/project/context.md"` |
