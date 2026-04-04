---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-playwright-version-magic-constant.md
---

# Document PLAYWRIGHT_MIN_VERSION Derivation — Implementation Plan

**Goal:** Add a self-contained block comment above `PLAYWRIGHT_MIN_VERSION` in
`hooks/session-resume.py` that records the CVE identifier, reference URL, and
version derivation rationale.

**Architecture:** Pure documentation change — no logic altered, no new files,
no new tests. A block comment added immediately above line 16 makes the
constant self-documenting for any future maintainer who needs to raise the
minimum version in response to a new CVE.

**Tech Stack:** Python 3.x (inline comment syntax only)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/session-resume.py` | Add block comment above `PLAYWRIGHT_MIN_VERSION` |

---

## Task 1: Add CVE derivation comment above PLAYWRIGHT_MIN_VERSION

**Acceptance Criteria:**
- A block comment appears on the lines directly above `PLAYWRIGHT_MIN_VERSION = (1, 55, 1)`.
- The comment names `CVE-2025-59288`.
- The comment includes a reference URL for the advisory (e.g. `https://github.com/advisories/GHSA-...` or `https://www.cve.org/CVERecord?id=CVE-2025-59288`).
- The comment states that `(1, 55, 1)` is the first Playwright release that ships the patch for the CVE.
- No other lines in `session-resume.py` are changed.
- `make lint` exits 0 with no new violations.

**Files:**
- Modify: `hooks/session-resume.py`

- [ ] **Step 1: Apply the comment edit**

  Replace line 16 in `hooks/session-resume.py`:

  ```python
  PLAYWRIGHT_MIN_VERSION = (1, 55, 1)
  ```

  With:

  ```python
  # Minimum safe Playwright version — derived from CVE-2025-59288.
  # CVE-2025-59288: arbitrary code execution via malicious CDP response.
  # Reference: https://www.cve.org/CVERecord?id=CVE-2025-59288
  # (1, 55, 1) is the first Playwright release that ships the fix.
  PLAYWRIGHT_MIN_VERSION = (1, 55, 1)
  ```

- [ ] **Step 2: Verify lint passes**

  Run: `make lint`
  Expected: exits 0, no new violations.

- [ ] **Step 3: Verify no logic changed**

  Run: `make test-unit`
  Expected: same pass count as before this change; no new failures.
