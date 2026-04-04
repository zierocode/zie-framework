---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-changelog-stale-commands.md
spec: specs/2026-03-24-audit-changelog-stale-commands-design.md
---

# CHANGELOG Stale Command References — Implementation Plan

**Goal:** Annotate the v1.1.0 section of `CHANGELOG.md` with `*(command removed in v1.2.0 — use /zie-release)*` and `*(command removed in v1.2.0 — use /zie-implement)*` on the `/zie-ship` and `/zie-build` entries respectively.
**Architecture:** Surgical inline annotation on two lines in the v1.1.0 `### Changed` block. No entries are deleted or reordered. The CHANGELOG remains a historical record; annotations are appended inline as italicised notes per the spec.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `CHANGELOG.md` | Annotate /zie-ship and /zie-build entries in v1.1.0 section |

## Task 1: Annotate stale /zie-ship and /zie-build entries in CHANGELOG

**Acceptance Criteria:**
- The `/zie-ship` entry in `CHANGELOG.md` v1.1.0 ends with `*(command removed in v1.2.0 — use /zie-release)*`
- The `/zie-build` entry in `CHANGELOG.md` v1.1.0 ends with `*(command removed in v1.2.0 — use /zie-implement)*`
- No other content in `CHANGELOG.md` is changed
- `make test-unit` passes (existing `test_docs_standards.py` tests do not regress)

**Files:**
- Modify: `CHANGELOG.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading `CHANGELOG.md` lines 161–166 and confirming the annotations are absent before the fix, present after.
  Run: `make test-unit` — existing tests pass (baseline; confirm `test_docs_standards.py` does not assert exact line content for v1.1.0 entries)

- [ ] **Step 2: Implement (GREEN)**
  In `CHANGELOG.md` v1.1.0 `### Changed` section (around lines 161–166):

  Find the `/zie-ship` bullet (line ~163):
  ```markdown
  - **Batch release support** — `[x]` items in the Now lane accumulate pending
    release. `/zie-ship` moves them to Done with a version tag — no need to
    ship features individually.
  ```
  Append inline at end of the last line of this bullet:
  ```markdown
    ship features individually. *(command removed in v1.2.0 — use `/zie-release`)*
  ```

  Find the `/zie-build` bullet (line ~164):
  ```markdown
  - **Intent-driven steps** — RED/GREEN/REFACTOR in `/zie-build` are short
    paragraphs instead of bullet micro-steps; config reads collapsed to one
    line.
  ```
  Append inline at end of the last line of this bullet:
  ```markdown
    line. *(command removed in v1.2.0 — use `/zie-implement`)*
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Read the v1.1.0 section visually to confirm no accidental reformatting or whitespace changes.
  Run: `make test-unit` — still PASS
