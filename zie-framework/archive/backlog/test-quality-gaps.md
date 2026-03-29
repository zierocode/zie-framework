# Test Quality: Fill Edge Case and Error Path Gaps

**Source**: audit-2026-03-24b H4-H7 + M4-M6 + M13 (Agents A, C)
**Effort**: L
**Score impact**: +8×4 High + +3×3 Medium = +41 (Quality dimension major lift)

## Problem

Multiple categories of untested behavior across hooks:

### 1. Subprocess timeout error paths (H4)
Hooks that use subprocess but have no timeout tests:
- `auto-test.py:138` — no TimeoutExpired test
- `safety_check_agent.py:80` — no timeout/claude-not-found test
- `sdlc-compact.py:54,66` — no git timeout test
- `stop-guard.py:53` — no git timeout test
- `task-completed-gate.py:61` — TimeoutExpired treated as "no failures", untested

### 2. JSON edge cases (H5)
- Corrupted `.config` file (only 2 of 14 hooks have corrupt JSON tests)
- Empty `{}` config (different from missing config — fallback behavior untested)
- `.pytest_cache/v/cache/lastfailed` with empty dict vs missing file
- Counter file in wip-checkpoint.py not an int

### 3. None/empty inputs (H6, H7)
- `None` tool_input — hooks use `(event.get("tool_input") or {})` but never tested
- Missing event keys (no `tool_name`, no `command`)
- stop-guard.py rename detection: ` -> ` in actual filename vs rename notation

### 4. Regex pattern coverage (H7)
- safety-check.py BLOCKS/WARNS: no unit tests for each pattern individually
- Verify `git push -u origin main` is correctly blocked
- Verify `git push --force-with-lease` is blocked (force push pattern)
- input-sanitizer.py CONFIRM_PATTERNS: only implicit integration testing

### 5. Git unavailable (M6)
- Only `failure-context.py` tests git absence (mocked PATH)
- `sdlc-compact.py`, `stop-guard.py`, `task-completed-gate.py` don't test git
  not found / detached HEAD / bare repo

### 6. Time-boundary tests (M4)
- `sdlc-context.py:58` staleness check at STALE_THRESHOLD=300
- Tests for 299s (not stale), 300s (boundary), 301s (stale)

### 7. File I/O race + mock completeness (M5)
- safety-check.py tests don't mock BLOCKS/WARNS pattern lists
- wip-checkpoint.py: symlink in path, zie-memory unreachable
- notification-log.py: log file corrupted mid-write

### 8. Path traversal completeness (M13)
- `/home/user-evil/` prefix edge case
- NUL byte in path
- Symlink loop handling

## Scope

Add targeted test cases across relevant test files. Group by hook to keep test
files cohesive. Prefer adding to existing test files over creating new ones.

## Acceptance Criteria

- [ ] TimeoutExpired tested in all 5 affected hooks
- [ ] Corrupted JSON tested in all hooks that read JSON files
- [ ] None/empty event input tested in all PreToolUse hooks
- [ ] Each BLOCKS/WARNS pattern has at least 1 dedicated unit test
- [ ] Git unavailable tested in sdlc-compact, stop-guard, task-completed-gate
- [ ] Staleness boundary test at 299/300/301 seconds
- [ ] All edge cases documented above have at least 1 test
