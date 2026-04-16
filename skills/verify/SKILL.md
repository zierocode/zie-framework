---
name: zie-framework:verify
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
| `scope` | `full`, `tests-only` | `full` | `tests-only` runs checks 1, 2, and secrets scan from 4 only — skips TODOs (3), full code review (4), and docs sync (5). |

## Input

`$ARGUMENTS` (optional JSON from caller):

```json
{
  "test_output": "===== 1234 passed in 5.23s =====",
  "changed_files": ["hooks/auto-test.py"],
  "scope": "tests-only"
}
```

| Key | Description |
| --- | --- |
| `test_output` | If provided and non-empty, use as test result — skip `make test-unit`. Contains `failed`/`error` → treat as failed. |
| `scope` | Overrides skill's scope parameter if provided. |
| `changed_files` | Restrict TODO/secrets scan to these files if provided. |

Fallback: empty/unparseable `$ARGUMENTS` → run all checks normally (fully backward compatible).

## Scope: tests-only

Runs: Check 1, 2, and secrets scan from 4 only. Skips TODOs (3), full code review (4), docs sync (5).
`scope=full` or no scope → run all 5 checks below.

## รายการตรวจสอบ

### 1. ตรวจ Tests

Guard: `test_output` provided and non-empty → use it; skip `make test-unit`.

```bash
make test-unit
```

- All tests pass? ✓
- New tests added for this feature? If not, explain why.

If integration tests exist: `make test-int`
If e2e enabled (`playwright_enabled=true`): `make test-e2e`

### 2. ไม่มี regressions

Guard: `test_output` provided → use it (already ran in check 1); do NOT re-run `make test-unit`.

- Compare pass count in `test_output` to previous run — no unexpected changes.

### 3. ไม่มี TODO ค้างอยู่

```bash
grep -r "TODO\|FIXME\|PLACEHOLDER\|pass  #" --include="*.py" .
```

- Hits in new code? Fix or create tracked backlog item.

### 4. ตรวจ code ตัวเอง

- Implementation matches the plan?
- Obvious simplifications (dead code, duplication)?
- Secrets or credentials in code? → STOP, remove immediately.

### 5. Documentation

- `CLAUDE.md` needs updating? (new commands, changed deps, new rules)
- `README.md` needs updating? (new features, changed setup steps)

## สรุปผล

```
Verification complete:

Tests   : unit ✓ | integration ✓|n/a | e2e ✓|n/a
TODOs   : none found | <N> found (see above)
Docs    : up to date | updated
Secrets : none detected

Ready to ship: /release
```

Anything fails → fix before proceeding. Never claim "done" with a failing check.