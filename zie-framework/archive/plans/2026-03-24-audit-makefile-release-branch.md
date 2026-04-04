---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-makefile-release-branch.md
spec: specs/2026-03-24-audit-makefile-release-branch-design.md
---

# Makefile Release Branch Safety Check — Implementation Plan

**Goal:** Add a clean-tree and correct-branch pre-flight guard to the `release` target in `Makefile` so that `make release` fails fast with a clear message if the working tree is dirty or the current branch is not `dev`.
**Architecture:** Two guard lines inserted after the `ifndef NEW` block in the `release` target. The first uses `git diff --quiet && git diff --cached --quiet` to assert a clean tree. The second uses `git rev-parse --abbrev-ref HEAD | grep -q "^dev$$"` to assert the current branch. Both use `||` short-circuit with `echo` + `exit 1`. Tab indentation is required by Make.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Add clean-tree and correct-branch pre-flight guards to release target |

## Task 1: Add pre-flight guards to Makefile release target

**Acceptance Criteria:**
- `make release NEW=1.2.3` with a dirty working tree exits with a non-zero code and prints `ERROR: Working tree is dirty. Commit or stash changes before releasing.`
- `make release NEW=1.2.3` run from any branch other than `dev` exits with a non-zero code and prints `ERROR: Must release from 'dev' branch.`
- `make release NEW=1.2.3` run from a clean `dev` branch proceeds as before
- The existing `ifndef NEW` guard still fires when `NEW` is omitted
- `make test-unit` passes (Makefile is not executed by tests)

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — Makefile target change. Verified manually by:
  1. Making a dirty change, running `make release NEW=9.9.9` — must print error and exit non-zero
  2. Stashing, switching to a non-dev branch, running `make release NEW=9.9.9` — must print error and exit non-zero
  3. On clean `dev`, running `make release NEW=9.9.9` (interrupted after pre-flight) — must proceed past guards
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In `Makefile`, update the `release` target. After the `ifndef NEW` / `$(error ...)` / `endif` block, insert (using tab indentation):

  ```makefile
  release: ## Publish release (usage: make release NEW=1.2.3)
  ifndef NEW
  	$(error NEW is required — usage: make release NEW=1.2.3)
  endif
  	@git diff --quiet && git diff --cached --quiet || \
  		(echo "ERROR: Working tree is dirty. Commit or stash changes before releasing." && exit 1)
  	@git rev-parse --abbrev-ref HEAD | grep -q "^dev$$" || \
  		(echo "ERROR: Must release from 'dev' branch. Currently on: $$(git rev-parse --abbrev-ref HEAD)" && exit 1)
  	sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
  	git add .claude-plugin/plugin.json
  	git diff --cached --quiet || git commit --amend --no-edit
  	git checkout main
  	git merge dev --no-ff -m "release: v$(NEW)"
  	git tag -a v$(NEW) -m "release v$(NEW)"
  	git push origin main --tags
  	git checkout dev
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm Makefile uses tabs (not spaces) for all recipe lines — run `cat -A Makefile | grep "^ "` should return empty for the release block.
  Run: `make test-unit` — still PASS
