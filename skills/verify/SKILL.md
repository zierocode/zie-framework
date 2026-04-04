---
name: verify
description: Pre-ship verification checklist — tests, lint, no regressions, no TODOs left open.
metadata:
  zie_memory_enabled: true
argument-hint: "scope=full|tests-only (default: full)"
model: haiku
effort: low
context: fork
---

# verify — Pre-Ship Verification

## Parameters

| Parameter | Values | Default | Description |
| --- | --- | --- | --- |
| `scope` | `full`, `tests-only` | `full` | Controls which checks run. `tests-only` runs checks 1, 2, and secrets scan from 4 only — skips TODOs (3), full code review (4), and docs sync (5). |

## Input

`$ARGUMENTS` (optional JSON from caller):

```json
{
  "test_output": "===== 1234 passed in 5.23s =====",
  "changed_files": ["hooks/auto-test.py"],
  "scope": "tests-only"
}
```

- `test_output`: if provided and non-empty, use as the test result — skip
  re-running `make test-unit`. If `test_output` contains `failed` or `error` →
  treat tests as failed.
- `scope`: overrides the skill's scope parameter if provided.
- `changed_files`: restrict TODO/secrets scan to these files if provided.

**Fallback:** if `$ARGUMENTS` is empty or unparseable → run all checks normally,
including `make test-unit` (existing behavior — fully backward compatible).

## Scope: tests-only

When called with `scope=tests-only`, run only:

1. **Check 1** — ตรวจ Tests (full, as below)
2. **Check 2** — ไม่มี regressions (full, as below)
3. **Check 4 — secrets scan only:** Are secrets or credentials in the code? → STOP, remove immediately. Skip all other check 4 items.

Skip check 3 (TODOs), skip the remainder of check 4 (design match, simplifications), and skip check 5 (docs sync entirely).

Print a scoped verification summary:

```text
Verification complete (scope: tests-only):

Tests   : unit ✓ | integration ✓|n/a | e2e ✓|n/a
Secrets : none detected

Scope was tests-only — docs sync and full code review skipped.
```

When called with `scope=full` or with no scope argument → run all 5 checks as documented below.

## รายการตรวจสอบ

### 1. ตรวจ Tests

```bash
make test-unit
```

- All tests pass? ✓
- Any skipped tests? Investigate — skips hide real failures.
- Any new tests added for this feature? If not, explain why.

If integration tests exist:

```bash
make test-int
```

If e2e tests are enabled (playwright_enabled=true):

```bash
make test-e2e
```

### 2. ไม่มี regressions

- Run the full suite, not just the new tests.
- Compare pass count to the previous run — no unexpected changes.

### 3. ไม่มี TODO ค้างอยู่

Search for leftover stubs:

```bash
grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
```

- Any hits in new code? Fix or create a tracked backlog item.

### 4. ตรวจ code ตัวเอง

- Does the implementation match the plan?
- Are there any obvious simplifications (dead code, duplication)?
- Are secrets or credentials in the code? → STOP, remove immediately.

### 5. Documentation

- Does `CLAUDE.md` need updating? (new commands, changed dependencies, new
  rules)
- Does `README.md` need updating? (new features, changed setup steps)

## สรุปผล

Print a verification summary:

```text
Verification complete:

Tests   : unit ✓ | integration ✓|n/a | e2e ✓|n/a
TODOs   : none found | <N> found (see above)
Docs    : up to date | updated
Secrets : none detected

Ready to ship: /release
```

If anything fails → fix before proceeding. Never claim "done" with a failing
check.
