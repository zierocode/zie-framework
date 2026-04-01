# Narrow or document nosec B310 suppression in call_zie_memory_api

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`utils.py:416` uses `urllib.request.urlopen(req)  # nosec B310`. The `nosec`
annotation suppresses Bandit's B310 check entirely for that line. The actual
risk is low — both callers validate the URL starts with `https://` before
calling this function. However `nosec` with no justification comment masks any
future regression if the https-prefix guard were removed or bypassed.

## Motivation

Replace `# nosec B310` with `# nosec B310 — URL validated as https:// by
caller before reaching this function` to document the assumption. This makes
the suppression self-explaining and easier to audit.
