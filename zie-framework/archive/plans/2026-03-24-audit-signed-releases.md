---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-signed-releases.md
spec: specs/2026-03-24-audit-signed-releases-design.md
---

# Signed Releases and SLSA Provenance — Implementation Plan

**Goal:** Implement SLSA Level 1 for zie-framework by switching `make release` to signed tags (`git tag -s`), adding a GitHub Actions provenance workflow, and documenting the signing approach in `SECURITY.md`.
**Architecture:** Three coordinated changes: (1) one-character Makefile edit (`-a` → `-s` in `git tag`); (2) new `.github/workflows/release-provenance.yml` triggered on `v*` tag pushes using `actions/attest-build-provenance@v1`; (3) new `## Release Signing` section in `SECURITY.md`. The `.github/` directory may need creating (also required by the Dependabot plan). GPG key requirement is documented, not enforced by Makefile fallback.
**Tech Stack:** Python 3.x, pytest, markdown, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Change `git tag -a` to `git tag -s` in release target |
| Create | `.github/workflows/release-provenance.yml` | GitHub Actions workflow generating SLSA provenance on tag push |
| Modify | `SECURITY.md` | Add Release Signing section with verification instructions |

## Task 1: Switch Makefile release target to signed tags

**Acceptance Criteria:**
- `Makefile` `release` target uses `git tag -s v$(NEW)` instead of `git tag -a v$(NEW)`
- All other release target lines are unchanged
- `make test-unit` passes

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — Makefile one-character change. Verified manually by reading `Makefile` line 37 and confirming `-a` is present before fix, `-s` after.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  In `Makefile` `release` target, change:

  ```makefile
  	git tag -a v$(NEW) -m "release v$(NEW)"
  ```

  to:

  ```makefile
  	git tag -s v$(NEW) -m "release v$(NEW)"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  No cleanup needed — single character change.
  Run: `make test-unit` — still PASS

## Task 2: Create GitHub Actions release provenance workflow

**Acceptance Criteria:**
- `.github/workflows/release-provenance.yml` exists
- The workflow triggers on `push` of tags matching `v*`
- The workflow has `id-token: write`, `contents: write`, and `attestations: write` permissions
- The workflow uses `actions/attest-build-provenance@v1` with `subject-path: '.claude-plugin/plugin.json'`
- The YAML is valid (parseable)
- `make test-unit` passes

**Files:**
- Create: `.github/workflows/release-provenance.yml`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — YAML config file creation. Verified manually by confirming the file exists and `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release-provenance.yml'))"` succeeds.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  Create `.github/workflows/` directory if it does not exist. Create `.github/workflows/release-provenance.yml`:

  ```yaml
  name: Release Provenance
  on:
    push:
      tags:
        - 'v*'
  permissions:
    id-token: write
    contents: write
    attestations: write
  jobs:
    provenance:
      runs-on: ubuntu-latest
      steps:
        - uses: actions/checkout@v4
        - name: Generate SLSA provenance
          uses: actions/attest-build-provenance@v1
          with:
            subject-path: '.claude-plugin/plugin.json'
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Validate YAML: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/release-provenance.yml'))"` — must not raise.
  Run: `make test-unit` — still PASS

## Task 3: Add Release Signing section to SECURITY.md

**Acceptance Criteria:**
- `SECURITY.md` contains a `## Release Signing` section
- The section documents `git verify-tag v<version>` for GPG tag verification
- The section documents `gh attestation verify` for SLSA provenance verification
- The section includes the correct `--repo zierocode/zie-framework` flag
- No other content in `SECURITY.md` is changed
- `make test-unit` passes

**Files:**
- Modify: `SECURITY.md`

- [ ] **Step 1: Write failing tests (RED)**
  No automated test required — docs-only change. Verified manually by reading `SECURITY.md` and confirming the section is absent before, present after.
  Run: `make test-unit` — existing tests pass (baseline)

- [ ] **Step 2: Implement (GREEN)**
  Append to `SECURITY.md` after the `## Disclosure Policy` section:

  ```markdown
  ## Release Signing

  All release tags are GPG-signed. To verify a tag:

  ```bash
  git verify-tag v<version>
  ```

  SLSA provenance attestations are published automatically via GitHub
  Actions on each tagged release. Verify via:

  ```bash
  gh attestation verify .claude-plugin/plugin.json \
    --repo zierocode/zie-framework
  ```

  GPG signing requires `gpg` installed locally with `git config user.signingkey`
  set. If GPG is not configured, `git tag -s` will fail with a clear error —
  do not fall back to an unsigned tag.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Confirm the code fences inside the section are properly closed and the Markdown renders correctly.
  Run: `make test-unit` — still PASS
