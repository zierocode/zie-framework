# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 1.4.x   | Yes       |
| < 1.4   | No        |

## Reporting a Vulnerability

**Do not open a public GitHub issue for security vulnerabilities.**

To report a vulnerability, contact the maintainer directly:

- **Contact:** Open a private GitHub Security Advisory at
  `https://github.com/zierocode/zie-framework/security/advisories/new`
  *(forks: replace with your repository path)*
- **Email fallback:** Include "SECURITY" in the subject line.

Please include: a description of the issue, reproduction steps, affected
versions, and potential impact.

## Disclosure Policy

This project follows **responsible disclosure**:

1. Report the vulnerability privately.
2. The maintainer will acknowledge receipt within 7 days.
3. A fix will be developed and released within **90 days** of the report.
4. After the fix is released (or the 90-day embargo expires), the reporter
   may disclose the vulnerability publicly.

Coordinated disclosure is appreciated. Credit will be given in the release
notes unless the reporter prefers to remain anonymous.

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
