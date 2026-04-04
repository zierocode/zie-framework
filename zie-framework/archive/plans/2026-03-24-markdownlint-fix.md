---
approved: false
approved_at: ~
backlog: backlog/markdownlint-fix.md
spec: specs/2026-03-24-markdownlint-fix-design.md
---

# Fix markdownlint-cli Pre-commit Hook — Implementation Plan

**Goal:** Replace the broken `markdownlint-cli@0.48.0` hook in `.pre-commit-config.yaml` with a working version so the markdown lint gate actually catches violations and blocks commits.
**Architecture:** Single-file change — update (or create) `.pre-commit-config.yaml`. Strategy: try pinning `markdownlint-cli@v0.37.0` first (last known-good release before the argument-parsing regression); if v0.37.0 is also broken in this environment, fall back to `markdownlint-cli2` (no known equivalent breakage). Pin whichever version passes validation. **ADR-002 note:** ADR-002 documents the prior `.githooks/pre-commit` + `npx markdownlint-cli` approach. This plan deliberately supersedes that approach with the pre-commit framework (`.pre-commit-config.yaml`), which is more portable and standard. Add an `## Amendment` section to ADR-002 when committing this fix.
**Tech Stack:** YAML (`.pre-commit-config.yaml`), pre-commit, markdownlint-cli (v0.37.0) or markdownlint-cli2 (fallback)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify/Create | `.pre-commit-config.yaml` | Replace broken markdownlint-cli hook with markdownlint-cli2, pinned version |

---

## Task 1: Replace broken markdownlint hook

<!-- depends_on: none -->

**Acceptance Criteria:**
- `.pre-commit-config.yaml` exists at project root
- The markdownlint hook uses `markdownlint-cli2` (repo: `https://github.com/DavidAnson/markdownlint-cli2-action` or the pre-commit mirror `https://github.com/davidanson/markdownlint-cli2`)
- Version is explicitly pinned (no floating `latest`)
- `pre-commit run markdownlint` exits non-zero on a file with a known violation
- `pre-commit run markdownlint` exits 0 on a clean markdown file
- No change to existing markdown rules or configuration (`.markdownlint.json` or equivalent untouched)

**Files:**
- Modify/Create: `.pre-commit-config.yaml`

- [ ] **Step 1: RED — confirm the gate is currently broken**

  Run `pre-commit run markdownlint` against `README.md` (which contains known
  violations) and confirm it exits 0 when it should exit non-zero:

  ```bash
  cd /Users/zie/Code/zie-framework
  pre-commit run markdownlint --files README.md
  echo "exit code: $?"
  ```

  Expected: exit code 0 (broken — gate silently passes everything).
  If exit code is already non-zero, verify which violation it catches before
  proceeding — the gate may already be partially working; adjust scope accordingly.

- [ ] **Step 2: GREEN — update `.pre-commit-config.yaml`**

  Replace the `markdownlint-cli` hook entry with `markdownlint-cli2`. If
  `.pre-commit-config.yaml` does not yet exist, create it with the full content
  below. If it exists, replace only the markdownlint repo block.

  Minimal config (adjust to match existing repo structure if file already exists):

  ```yaml
  repos:
    - repo: https://github.com/igorshubovych/markdownlint-cli
      rev: v0.37.0
      hooks:
        - id: markdownlint
  ```

  > **Decision note:** Try pinning `markdownlint-cli@v0.37.0` first — this is
  > the last known-good release before the CLI argument parsing regression.
  > If `v0.37.0` is also broken in this environment, fall back to `markdownlint-cli2`:
  >
  > ```yaml
  > repos:
  >   - repo: https://github.com/DavidAnson/markdownlint-cli2
  >     rev: v0.13.0
  >     hooks:
  >       - id: markdownlint-cli2
  > ```
  >
  > Pin whichever version passes validation in Step 3.

  After editing, clear the pre-commit cache for the hook:

  ```bash
  cd /Users/zie/Code/zie-framework
  pre-commit clean
  ```

- [ ] **Step 3: GREEN — validate non-zero exit on violation**

  Create a temporary file with a known violation (missing blank line before heading),
  run the hook, confirm non-zero exit, then delete the temp file:

  ```bash
  cd /Users/zie/Code/zie-framework
  printf '# Title\nSome text\n## No blank line before this heading\n' > /tmp/test-violation.md
  pre-commit run markdownlint --files /tmp/test-violation.md
  echo "exit code (expect non-zero): $?"
  ```

  Expected: exit code 1 (violation detected). If still 0, the pinned version
  is also broken — switch to the `markdownlint-cli2` fallback and repeat.

- [ ] **Step 4: GREEN — validate zero exit on clean file**

  ```bash
  cd /Users/zie/Code/zie-framework
  printf '# Title\n\nSome clean text.\n\n## Section\n\nMore clean text.\n' > /tmp/test-clean.md
  pre-commit run markdownlint --files /tmp/test-clean.md
  echo "exit code (expect 0): $?"
  ```

  Expected: exit code 0.

- [ ] **Step 5: REFACTOR — verify pin is explicit**

  Read the final `.pre-commit-config.yaml` and confirm:
  - `rev:` is set to an exact version tag (e.g., `v0.37.0` or `v0.13.0`)
  - No `rev: latest` or unpinned SHA
  - Hook `id:` matches the chosen tool (`markdownlint` or `markdownlint-cli2`)

  ```bash
  cd /Users/zie/Code/zie-framework
  cat .pre-commit-config.yaml
  ```

  Then run the full pre-commit suite on `README.md` to confirm no unintended
  regressions from other hooks:

  ```bash
  cd /Users/zie/Code/zie-framework
  pre-commit run --files README.md
  echo "exit code: $?"
  ```

  **CI compatibility note:** Both `markdownlint-cli` and `markdownlint-cli2` require Node.js. Confirm the CI environment (GitHub Actions `ubuntu-latest`) has Node.js available. The `actions/setup-node` step is not required because `ubuntu-latest` ships with Node.js pre-installed, but note this dependency if the CI environment changes.

  **ADR-002 amendment:** After confirming the hook works, add an `## Amendment` section to `zie-framework/decisions/ADR-002-markdownlint-precommit-gate.md` documenting that the `.pre-commit-config.yaml` approach supersedes the `.githooks/pre-commit` approach.

---

*Commit: `git add .pre-commit-config.yaml && git commit -m "fix: replace broken markdownlint-cli@0.48.0 with working pinned version"`*
