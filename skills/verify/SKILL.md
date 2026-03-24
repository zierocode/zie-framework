---
name: verify
description: Pre-ship verification checklist — tests, lint, no regressions, no TODOs left open.
metadata:
  zie_memory_enabled: true
argument-hint: ""
---

# verify — Pre-Ship Verification

Run this before claiming work is complete or opening a PR. Catch problems before
they reach main.

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

Ready to ship: /zie-release
```

If anything fails → fix before proceeding. Never claim "done" with a failing
check.
