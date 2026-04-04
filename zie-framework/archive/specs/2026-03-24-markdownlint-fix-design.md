---
approved: true
approved_at: 2026-03-24
backlog: backlog/markdownlint-fix.md
---

# Fix markdownlint-cli Pre-commit Hook — Design Spec

**Problem:** `markdownlint-cli@0.48.0` in `.pre-commit-config.yaml` is broken — it always prints the help text and exits 0 regardless of file violations. The markdown lint gate appears to run but catches nothing. This is a silently-disabled quality gate.

**Approach:** Identify the last working version of `markdownlint-cli` (likely 0.37.x or earlier), or switch to `markdownlint-cli2` which has no known equivalent breakage. Update the hook pin. Validate by running `pre-commit run markdownlint` against a file with a known violation (e.g., missing blank line before a heading) and confirming non-zero exit.

**Components:**
- Modify: `.pre-commit-config.yaml` — update `markdownlint-cli` hook to a working version (or replace with `markdownlint-cli2`); pin the version explicitly

**Acceptance Criteria:**
- [ ] `pre-commit run markdownlint` exits non-zero on a file with known violations
- [ ] `pre-commit run markdownlint` exits 0 on a clean markdown file
- [ ] Version is explicitly pinned (no floating `latest`)
- [ ] No change to existing markdown rules or configuration
- [ ] Pre-commit hook runs without errors in the CI environment

**Out of Scope:**
- Adding new markdown lint rules
- Changing `.markdownlint.json` or equivalent config
