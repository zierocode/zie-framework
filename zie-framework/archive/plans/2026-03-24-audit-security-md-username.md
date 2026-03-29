---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-security-md-username.md
spec: specs/2026-03-24-audit-security-md-username-design.md
---

# SECURITY.md Hardcoded Username — Implementation Plan

**Goal:** Add a fork note to the advisory URL line in `SECURITY.md` making the hardcoded `zierocode` username explicit and instructing fork owners to update it.
**Architecture:** Single line edit in `SECURITY.md`. The URL itself is the correct canonical upstream URL and does not change. The fix is a documentation clarification: append `*(forks: replace with your repository path)*` to the Contact line so the obligation is explicit. No code changes.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `SECURITY.md` | Append fork note to the advisory URL line |

## Task 1: Add fork note to the advisory URL in SECURITY.md

**Acceptance Criteria:**
- `SECURITY.md` Contact line contains the original advisory URL unchanged
- The line ends with `*(forks: replace with your repository path)*`
- No other content in `SECURITY.md` is changed
- `make test-unit` passes (existing `test_docs_standards.py` SECURITY.md assertions do not regress)

**Files:**
- Modify: `SECURITY.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading `SECURITY.md` line 17 and confirming the fork note is absent before the fix, present after.
  Run: `make test-unit` — existing tests pass (baseline; confirm `test_docs_standards.py` does not assert exact content of the Contact line in a way that would break)

- [ ] **Step 2: Implement (GREEN)**
  In `SECURITY.md`, the Contact bullet (line 16–17) currently reads:

  ```markdown
  - **Contact:** Open a private GitHub Security Advisory at
    `https://github.com/zierocode/zie-framework/security/advisories/new`
  ```

  Change to:

  ```markdown
  - **Contact:** Open a private GitHub Security Advisory at
    `https://github.com/zierocode/zie-framework/security/advisories/new`
    *(forks: replace with your repository path)*
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read `SECURITY.md` in full to confirm no surrounding lines were accidentally altered.
  Run: `make test-unit` — still PASS
