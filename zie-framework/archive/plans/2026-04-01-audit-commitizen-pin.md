---
slug: audit-commitizen-pin
status: approved
approved: true
date: 2026-04-01
---

# Plan: Verify commitizen Pin in requirements-dev.txt

<!-- depends_on: audit-pytest-cve-requirements -->

## Overview

`audit-pytest-cve-requirements` creates `requirements-dev.txt` and already
includes `commitizen>=4.13.9`. This plan's only task is to confirm the pin is
present after that plan is implemented and verify `make setup` installs it.

No new files. No code changes beyond what `audit-pytest-cve-requirements` provides.

**Spec:** `zie-framework/specs/2026-04-01-audit-commitizen-pin-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|-----------|
| AC-1 | `requirements-dev.txt` contains `commitizen>=4.13.9` (or a more specific pin) |
| AC-2 | `cz version` exits 0 after `make setup` |
| AC-3 | `make test-ci` exits 0 |

---

## Pre-condition

This plan must run **after** `audit-pytest-cve-requirements` is implemented.
`requirements-dev.txt` must exist.

---

## Tasks

### Task 1 — Confirm commitizen entry

```bash
grep 'commitizen' requirements-dev.txt
```

Expected: `commitizen>=4.13.9` (or similar).

If `commitizen` is absent from `requirements-dev.txt` (the audit-pytest-cve
plan was implemented without it), add the line:

**File:** `requirements-dev.txt`

Append:
```
commitizen>=4.13.9
```

---

### Task 2 — Confirm installation

```bash
make setup
cz version
```

Both must exit 0.

---

### Task 3 — Full suite gate

```bash
make test-ci
```

Must exit 0.

---

## Test Strategy

No new unit tests — this is a dependency manifest verification. Correctness
criterion: `cz version` exits 0 after `make setup`.

---

## Rollout

1. Run after `audit-pytest-cve-requirements` is complete.
2. Confirm grep (Task 1) — add line if missing.
3. Run `make setup && cz version` (Task 2).
4. Run `make test-ci` (Task 3).
5. Mark ROADMAP Done.
