# Spec: Document PLAYWRIGHT_MIN_VERSION Derivation in session-resume.py

**Slug:** lean-playwright-version-magic-constant
**Date:** 2026-04-04
**Status:** Draft

---

## Problem

`PLAYWRIGHT_MIN_VERSION = (1, 55, 1)` in `hooks/session-resume.py` (line 16) is
hardcoded with no comment explaining how the value was derived. A reader
updating the constant in response to a future CVE has no derivation trail —
they cannot confirm whether `(1, 55, 1)` is the first Playwright release that
patched the referenced vulnerability, or why that specific version was chosen.

---

## Goal

Add a self-contained inline comment above the constant that records:

1. The CVE identifier that drove the minimum version requirement.
2. A reference URL for the advisory.
3. A one-line explanation that `(1, 55, 1)` is the first Playwright release
   that ships the fix for that CVE.

---

## Approach

Add a multi-line block comment immediately above `PLAYWRIGHT_MIN_VERSION` in
`hooks/session-resume.py`. No new files. No new tests. No logic changes.

The comment must be self-contained so any future maintainer can update the
constant without external context.

---

## Acceptance Criteria

- [ ] A block comment appears directly above `PLAYWRIGHT_MIN_VERSION = (1, 55, 1)`.
- [ ] The comment names the CVE identifier (`CVE-2025-59288`).
- [ ] The comment includes a reference URL pointing to the advisory or CVE record.
- [ ] The comment states that `(1, 55, 1)` is the first Playwright release that
      patches the CVE.
- [ ] No other logic in `session-resume.py` is changed.
- [ ] `make lint` passes with no new violations.
- [ ] No new files are created; no existing tests are modified.

---

## Out of Scope

- Dependabot or CI integration to auto-detect Playwright CVEs.
- New test coverage for the version constant.
- Changes to any file other than `hooks/session-resume.py`.

---

## Components

| File | Change |
| --- | --- |
| `hooks/session-resume.py` | Add multi-line comment above `PLAYWRIGHT_MIN_VERSION` (line ~16) |
