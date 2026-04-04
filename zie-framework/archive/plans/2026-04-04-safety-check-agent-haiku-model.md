# Plan: safety_check_agent — Use Haiku for Binary ALLOW/BLOCK Decision

status: approved

## Tasks

- [ ] Task 1 (RED): Add test to `tests/unit/test_safety_check_agent_injection.py` — assert `--model` and `claude-haiku-4-5-20251001` appear in the subprocess args captured by the mock. Confirm test fails before the fix.
- [ ] Task 2 (GREEN): In `hooks/safety_check_agent.py`, update `invoke_subagent` — change `["claude", "--print", prompt]` to `["claude", "--print", "--model", "claude-haiku-4-5-20251001", prompt]`. Confirm all tests pass.
- [ ] Task 3 (DOCS): Update `CLAUDE.md` config table — add a note under `safety_agent_timeout_s` (or as a new row) clarifying that the subagent model is hardcoded to Haiku and is not configurable.

## Test Strategy

- Unit: mock `subprocess.run`, capture the `cmd` list, assert `"--model"` and `"claude-haiku-4-5-20251001"` are present. Add to existing `tests/unit/test_safety_check_agent_injection.py` alongside the prompt-injection tests.
- No integration test needed — this is a subprocess arg change, fully covered by the mock.
- Run `make test-fast` after RED, `make test-ci` before commit.

## Files to Change

| File | Change |
| ---- | ------ |
| `hooks/safety_check_agent.py` | Add `"--model", "claude-haiku-4-5-20251001"` to subprocess args in `invoke_subagent` |
| `tests/unit/test_safety_check_agent_injection.py` | Add `test_invoke_subagent_uses_haiku_model` test |
| `CLAUDE.md` | Note in hook config section that subagent model is hardcoded to Haiku |
