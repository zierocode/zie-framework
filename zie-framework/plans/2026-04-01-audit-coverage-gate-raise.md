---
slug: audit-coverage-gate-raise
status: approved
approved: true
date: 2026-04-01
---

# Plan: Raise Coverage Gate from 43% to 55%

## Overview

Single-line Makefile change plus a new ADR. No new test code required.
Existing suite already exceeds 55%. Total estimated time: ~10 minutes.

## Source Documents

- Spec: `zie-framework/specs/2026-04-01-audit-coverage-gate-raise-design.md`
- Backlog: `zie-framework/backlog/audit-coverage-gate-raise.md`
- Supersedes: ADR-027 (`zie-framework/decisions/ADR-027-coverage-gate.md`)

---

## Tasks

### Task 1 — Raise the gate in Makefile

**File:** `Makefile`
**Target:** `test-ci` (line ~46, `--cov-fail-under` flag)

Exact diff:

```diff
-		--cov-fail-under=43 \
+		--cov-fail-under=55 \
```

No other lines change.

**Verification:** After the edit, run:

```bash
make test-unit
```

Expected: exit 0, coverage report shows >= 55%. If it fails, re-evaluate
the actual coverage level before proceeding — do not lower the target without
a new spec decision.

---

### Task 2 — Write ADR-037

**File:** `zie-framework/decisions/ADR-037-coverage-gate-55.md`

```markdown
# ADR-037: Raise Coverage Gate from 43% to 55%

**Date:** 2026-04-01
**Status:** Accepted
**Deciders:** Zie

## Context

ADR-027 set the coverage gate at 43% — the actual coverage level at the time
(v1.7.0). That ADR explicitly noted the gate should be raised incrementally as
coverage grows. As of v1.15.x the suite consistently exceeds 55%.

## Decision

Raise `--cov-fail-under` from `43` to `55` in the `Makefile` `test-ci` target.
This was verified to pass before the change was committed.

## Consequences

- CI fails if coverage drops below 55% (previously 43%).
- Closes the 12-point gap that allowed silent regressions.
- No new test code required — existing suite already exceeds the new threshold.
- Future gate raises should follow the same pattern: measure first, raise
  second, document in a new ADR.

## Related

- ADR-027: Original coverage gate (43%)
- ADR-026: Coverage report format
- Makefile `test-ci` target
```

---

### Task 3 — Update ROADMAP

Move the `audit-coverage-gate-raise` item from Next lane to Done in
`zie-framework/ROADMAP.md`.

---

## Test Strategy

| Step | Command | Expected result |
| --- | --- | --- |
| Confirm gate is live | `make test-unit` | exit 0, coverage >= 55% |
| Confirm CI target passes | `make test-ci` | exit 0 |

Test pyramid classification: configuration change. Verification is an
integration-level check (runs the full unit suite under coverage measurement).
No new unit tests written — the gate value is a numeric constant.

---

## Rollout

1. Apply Task 1 (Makefile edit).
2. Run `make test-unit` — must exit 0 before proceeding.
3. Apply Task 2 (write ADR-037).
4. Apply Task 3 (ROADMAP update).
5. Proceed to `/zie-release`.

---

## Acceptance Criteria Traceability

| Spec criterion | Covered by |
| --- | --- |
| `--cov-fail-under=55` in Makefile `test-ci` | Task 1 |
| `make test-unit` exits 0 at new threshold | Task 1 verification step |
| ADR-037 exists in `zie-framework/decisions/` | Task 2 |
| ROADMAP item moved to Done | Task 3 |
