---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-readme-troubleshooting.md
spec: specs/2026-03-24-audit-readme-troubleshooting-design.md
---

# README Troubleshooting Section — Implementation Plan

**Goal:** Add a `## Troubleshooting` FAQ and a `## More` links section to `README.md` so users have a self-service path when setup fails.
**Architecture:** Two new Markdown sections appended after the existing `## Plugin Coexistence` section. No code changes; the README currently ends at line 102. Both sections are short — the troubleshooting table has three rows, the More section has two links.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `README.md` | Append Troubleshooting and More sections |

## Task 1: Add Troubleshooting section to README.md

**Acceptance Criteria:**
- `README.md` contains a `## Troubleshooting` section after `## Plugin Coexistence`
- The section contains a table with exactly three rows: hook not firing, zie-memory not connecting, tests not auto-running
- Each row has a Symptom and a Fix column

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading the file and confirming the section exists with correct content.
  Run: `make test-unit` — existing tests pass

- [ ] **Step 2: Implement (GREEN)**
  Append to `README.md` after the `## Plugin Coexistence` section:

  ```markdown
  ## Troubleshooting

  | Symptom | Fix |
  | --- | --- |
  | Hook not firing | Run `make setup` to activate `.githooks/`; verify Python 3 is on `PATH` |
  | zie-memory not connecting | Check `ZIE_MEMORY_API_KEY` env var; `zie_memory_enabled` must be `true` in `.config` |
  | Tests not auto-running | Verify `test_runner` is set in `.config`; run `make test-unit` manually to confirm runner works |
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm no trailing whitespace or extra blank lines introduced.
  Run: `make test-unit` — still PASS

## Task 2: Add More section with links to SECURITY and CHANGELOG

**Acceptance Criteria:**
- `README.md` contains a `## More` section after `## Troubleshooting`
- The section contains direct Markdown links to `CHANGELOG.md` and `SECURITY.md`
- Link text and descriptions match the spec exactly

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading the file and confirming both links are present and resolve correctly.
  Run: `make test-unit` — existing tests pass

- [ ] **Step 2: Implement (GREEN)**
  Append to `README.md` after the `## Troubleshooting` section:

  ```markdown
  ## More

  - [CHANGELOG](CHANGELOG.md) — release history
  - [SECURITY](SECURITY.md) — vulnerability reporting policy
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed.
  Run: `make test-unit` — still PASS
