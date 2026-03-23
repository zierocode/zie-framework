---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-project-md-version-stale.md
spec: specs/2026-03-24-audit-project-md-version-stale-design.md
---

# PROJECT.md Version Stale — Implementation Plan

**Goal:** Update `zie-framework/PROJECT.md` from version 1.4.0 to 1.4.1 and extend `sync-version` so future releases stay in sync automatically.
**Architecture:** Direct one-line edit to `PROJECT.md` corrects the immediate stale field. A `sed` line added to the `Makefile` `sync-version` target ensures the field is updated on every future release alongside `plugin.json`. No new files are needed; both changes are surgical.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `zie-framework/PROJECT.md` | Fix stale version field from 1.4.0 to 1.4.1 |
| Modify | `Makefile` | Add `sed` line to `sync-version` target to update `PROJECT.md` |

## Task 1: Fix stale version field in PROJECT.md

**Acceptance Criteria:**
- `zie-framework/PROJECT.md` line 7 reads `**Version**: 1.4.1` (not 1.4.0)
- The file is otherwise unchanged

**Files:**
- Modify: `zie-framework/PROJECT.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading the file and confirming the version field value.
  Run: `make test-unit` — existing tests pass (no regressions)

- [ ] **Step 2: Implement (GREEN)**
  In `zie-framework/PROJECT.md` line 7, change:
  `**Version**: 1.4.0  **Status**: active`
  to:
  `**Version**: 1.4.1  **Status**: active`
  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed — single character change.
  Run: `make test-unit` — still PASS

## Task 2: Extend sync-version to cover PROJECT.md

**Acceptance Criteria:**
- Running `make sync-version` updates the version field in both `plugin.json` and `zie-framework/PROJECT.md`
- The `sed` pattern matches `**Version**: <any semver>` and replaces with the content of `VERSION`
- If `PROJECT.md` version field is absent or malformatted, the `sed` command is a no-op (does not error)

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — Makefile target change. Verified manually by running `make sync-version` after the edit and confirming both files are updated.
  Run: `make test-unit` — existing tests pass

- [ ] **Step 2: Implement (GREEN)**
  In `Makefile`, after the `jq` + `mv` block in the `sync-version` target, append:

  ```makefile
  	sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: '"$$(cat VERSION)"'/' \
  	  zie-framework/PROJECT.md
  	@echo "PROJECT.md version synced to $$(cat VERSION)"
  ```

  Full updated `sync-version` target:

  ```makefile
  sync-version: ## Sync plugin.json version to match VERSION
  	jq --arg v "$$(cat VERSION)" '.version = $$v' .claude-plugin/plugin.json \
  	  > .claude-plugin/plugin.json.tmp \
  	  && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
  	sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: '"$$(cat VERSION)"'/' \
  	  zie-framework/PROJECT.md
  	@echo "plugin.json + PROJECT.md version synced to $$(cat VERSION)"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Consolidate the two `@echo` lines into one (as shown above).
  Run: `make test-unit` — still PASS
