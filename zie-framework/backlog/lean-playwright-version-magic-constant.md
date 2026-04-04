# Backlog: Document PLAYWRIGHT_MIN_VERSION derivation in session-resume.py

**Problem:**
session-resume.py line 16 hardcodes `PLAYWRIGHT_MIN_VERSION = (1, 55, 1)` with a
comment referencing CVE-2025-59288. If a future CVE requires a higher minimum,
the constant must be manually updated with no mechanism to detect drift.

**Rough scope:**
- Add inline comment explaining how (1, 55, 1) was derived (first version patching CVE-2025-59288)
- Add a link to the advisory or CVE reference
- Consider adding a test or Dependabot note to catch future playwright CVEs
- Low priority: the guard is currently active and correct
