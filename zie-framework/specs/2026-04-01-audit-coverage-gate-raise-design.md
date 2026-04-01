---
slug: audit-coverage-gate-raise
status: approved
date: 2026-04-01
---
# Spec: Raise Coverage Gate and Establish Ratchet Policy

## Problem

The coverage gate has been frozen at `--fail-under=43` since ADR-027 (2026-03-30).
That decision was made because `coverage sitecustomize` measurement was unreliable
at the time — hooks spawned as subprocesses showed 0% coverage, making the
previous 50% gate unachievable without misleading test inflation.

The `sitecustomize.py` shim is now stable. `make test-unit` currently measures
**44% total coverage** with subprocess hooks contributing real line data. The gate
at 43% is therefore behind the actual measured baseline and provides no
regression protection.

There is no policy preventing a future change from lowering `--fail-under` — a
contributor could accidentally (or intentionally) drop the gate and CI would not
catch it.

## Proposed Solution

Three changes, in order:

1. **Sync the gate to current measured coverage.** Update `--fail-under` from
   `43` to `44` in both `test-unit` and `test-ci` Makefile targets. This
   reflects the actual measured baseline without requiring any new tests to be
   written.

2. **Document a ratchet policy via a new ADR.** Write ADR-037 (superseding
   ADR-027) that declares:
   - The gate is set to the current measured baseline (44%).
   - The gate must never decrease in a release commit — it may only increase or
     stay the same.
   - Target: reach 70% over the next 3–4 sprints by writing tests for uncovered
     hook paths as separate backlog items.
   - If `sitecustomize.py` is ever lost or subprocess measurement breaks, the
     correct response is to fix the measurement infra, not lower the gate.

3. **No new tests this sprint.** Coverage improvement beyond the baseline
   sync is out of scope here. This sprint establishes the policy and the floor;
   test growth follows in subsequent sprints.

## Acceptance Criteria

- [ ] AC1: `Makefile` `test-unit` target has `--fail-under=44`
- [ ] AC2: `Makefile` `test-ci` target has `--fail-under=44`
- [ ] AC3: `make test-unit` exits 0 with the updated gate
- [ ] AC4: `make test-ci` exits 0 with the updated gate
- [ ] AC5: `zie-framework/decisions/ADR-037-coverage-gate-ratchet-policy.md` exists
- [ ] AC6: ADR-037 status is `Accepted`, supersedes ADR-027
- [ ] AC7: ADR-037 states the ratchet rule: gate never decreases between releases
- [ ] AC8: ADR-037 states the 70% aspirational target over 3–4 sprints
- [ ] AC9: ADR-027 status updated to `Superseded by ADR-037`

## Out of Scope

- Writing new unit tests to increase coverage (separate backlog items)
- Reaching 70% in this sprint
- Changing the `coverage-smoke` canary target
- Modifying `.coveragerc` or `sitecustomize.py`
- Any changes to hook source code
