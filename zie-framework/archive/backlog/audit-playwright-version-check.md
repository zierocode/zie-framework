# CVE-2025-59288: Playwright <1.55.1 MitM + no startup version check

**Severity**: Medium | **Source**: audit-2026-04-01

## Problem

**CVE-2025-59288** — Playwright versions below 1.55.1 download browser
binaries using `curl -k` (SSL certificate verification disabled), enabling
a MitM attack that could deliver arbitrary executables to any developer
running `playwright install`.

zie-framework supports `playwright_enabled: true` in config but has no
minimum version check at startup. Users with an older Playwright install
who enable this feature are silently exposed.

## Motivation

Fix: add a version check in the hook that activates Playwright (or in
`session-resume.py` config validation) that warns to stderr when
`playwright --version` reports < 1.55.1. Fail gracefully (disable feature,
do not crash) if version check fails.
