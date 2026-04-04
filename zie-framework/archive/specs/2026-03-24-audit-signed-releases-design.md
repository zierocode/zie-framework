---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-signed-releases.md
---

# Signed Releases and SLSA Provenance — Design Spec

**Problem:** Release tags are unsigned and there is no SLSA provenance file,
failing OpenSSF Scorecard's `Signed-Releases` check and leaving no supply
chain trust signal for users installing the plugin.

**Approach:** Implement SLSA Level 1: (1) sign git tags with GPG via
`git tag -s`, (2) add a GitHub Actions workflow that generates a provenance
attestation using `actions/attest-build-provenance` on each release, and
(3) document the signing key fingerprint in `SECURITY.md`.

**Components:**

- `Makefile` (`release` target) — change `git tag -a` to `git tag -s`
- `.github/workflows/release-provenance.yml` — new workflow (triggers on
  push of `v*` tags)
- `SECURITY.md` — add "Release Signing" section with key fingerprint

**Data Flow:**

1. **Signed tags** — in `Makefile` `release` target, change:

   ```makefile
   git tag -a v$(NEW) -m "release v$(NEW)"
   ```

   to:

   ```makefile
   git tag -s v$(NEW) -m "release v$(NEW)"
   ```

   Requires GPG key configured locally (`git config user.signingkey`).
   If GPG is not available, fall back to annotated tag with a warning.

2. **SLSA provenance workflow** — create
   `.github/workflows/release-provenance.yml`:

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

   This satisfies SLSA L1 by attesting the build artifact (plugin.json)
   with a GitHub-signed provenance statement tied to the source commit.

3. **SECURITY.md update** — add a `## Release Signing` section:

   ```markdown
   ## Release Signing

   All release tags are GPG-signed. To verify a tag:

   \```bash
   git verify-tag v<version>
   \```

   SLSA provenance attestations are published automatically via GitHub
   Actions on each tagged release. Verify via:

   \```bash
   gh attestation verify .claude-plugin/plugin.json \
     --repo zierocode/zie-framework
   \```
   ```

**Edge Cases:**

- If `.github/` directory does not exist, it must be created first (also
  needed for the Dependabot spec)
- `actions/attest-build-provenance@v1` requires `id-token: write` permission
  — this is fine for a public repo; no secrets exposed
- GPG signing on local machine requires `gpg` installed and a key with
  `user.signingkey` set in git config — document this in `SECURITY.md`
- If the developer machine has no GPG key, `git tag -s` will fail; the
  Makefile should print a clear error rather than falling back silently to
  an unsigned tag

**Out of Scope:**

- SLSA Level 2 or 3 (hermetic builds, reproducible builds)
- Cosign / Sigstore signing (GPG + GitHub attestations is sufficient for
  this project scale)
- Publishing to a package registry (no PyPI/npm publish currently)
