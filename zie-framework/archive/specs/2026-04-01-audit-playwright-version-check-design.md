---
slug: audit-playwright-version-check
status: draft
date: 2026-04-01
---
# Spec: Playwright Minimum Version Check at Session Start

## Problem

**CVE-2025-59288** — Playwright versions below 1.55.1 download browser binaries
using `curl -k` (SSL certificate verification disabled). This enables a
man-in-the-middle attack that can deliver arbitrary executables to any developer
running `playwright install`.

zie-framework supports `playwright_enabled: true` in `zie-framework/.config`
but performs no version check at startup. Users who enable this feature while
running an older Playwright install are silently exposed to this vulnerability.

## Proposed Solution

Add a Playwright version check inside `hooks/session-resume.py`, executed
immediately after config is loaded and only when `playwright_enabled: true`.

**Check flow:**

1. `config.get("playwright_enabled")` is `True` → proceed, else skip entirely.
2. Run `subprocess.run(["playwright", "--version"], capture_output=True, text=True, timeout=5)`.
3. Parse the version string from stdout (expected format: `Version X.Y.Z`).
4. Compare parsed version against the minimum safe version `1.55.1` using
   `packaging.version.Version` or a manual tuple comparison (no new deps
   required — manual tuple compare preferred to stay dependency-free).
5. Outcomes:
   - **Not installed** (`FileNotFoundError` or non-zero return code) →
     print warning to stderr, set `playwright_enabled` to `False` in the
     in-memory config dict (graceful disable for this session).
   - **Version < 1.55.1** → print a CVE warning to stderr identifying
     CVE-2025-59288 and the minimum safe version, set `playwright_enabled`
     to `False` in-memory (graceful disable for this session).
   - **Parse error** (stdout does not match expected format) → print a
     warning to stderr, skip the check, do NOT disable playwright, do NOT
     crash.
   - **Version >= 1.55.1** → no output, proceed normally.

All paths exit 0. The hook must never raise an unhandled exception.

**Minimum safe version constant:** `PLAYWRIGHT_MIN_VERSION = (1, 55, 1)`

**Stderr message format (version too old):**
```
[zie-framework] WARNING: Playwright X.Y.Z is below minimum safe version 1.55.1 (CVE-2025-59288). playwright_enabled disabled for this session. Run: playwright self-update
```

**Stderr message format (not installed):**
```
[zie-framework] WARNING: playwright not found. playwright_enabled disabled for this session.
```

**Stderr message format (parse error):**
```
[zie-framework] session-resume: could not parse playwright version from: "<raw stdout>"
```

The check is placed in the existing outer `try/except Exception` guard block
in `session-resume.py`, consistent with the two-tier hook error handling
convention.

## Acceptance Criteria

- [ ] AC1: When `playwright_enabled: false` in config, no subprocess is spawned
  and no playwright-related output appears.
- [ ] AC2: When `playwright_enabled: true` and playwright is not installed,
  a warning is printed to stderr and playwright is disabled for the session
  (no crash, exit 0).
- [ ] AC3: When `playwright_enabled: true` and installed version is below
  1.55.1, a CVE-2025-59288 warning is printed to stderr identifying the
  installed version and minimum safe version, and playwright is disabled for
  the session (exit 0).
- [ ] AC4: When `playwright_enabled: true` and installed version is >= 1.55.1,
  no warning is emitted and the session proceeds normally.
- [ ] AC5: When `playwright_enabled: true` and the version string cannot be
  parsed, a stderr parse-error notice is emitted but the hook does not crash
  and playwright is NOT disabled.
- [ ] AC6: The version check uses manual tuple comparison only — no new
  third-party dependencies introduced.
- [ ] AC7: Unit tests cover all five outcome branches (disabled, not installed,
  too old, ok, parse error) using mocked `subprocess.run`.
- [ ] AC8: The hook exits 0 in every code path.

## Out of Scope

- Auto-updating Playwright (we warn and disable, not auto-fix).
- Checking Playwright browser binary versions (only the CLI version is checked).
- Persisting the in-session disable back to `.config` (session-only change).
- Adding a `playwright_min_version` config key (hardcoded to 1.55.1 is
  sufficient; the CVE defines the boundary).
- Windows `playwright.cmd` shim handling beyond standard `FileNotFoundError`
  graceful disable.
