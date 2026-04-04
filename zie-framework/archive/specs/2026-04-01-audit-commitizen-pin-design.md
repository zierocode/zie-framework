---
slug: audit-commitizen-pin
status: draft
date: 2026-04-01
blocked-by: audit-pytest-cve-requirements
---
# Spec: Pin commitizen version in requirements-dev.txt

## Problem

`commitizen` (the Python `cz` CLI used for conventional commits and version
bumping) has no pinned version in any dependency manifest. No
`requirements-dev.txt` exists yet (that is handled by `audit-pytest-cve-requirements`).
Without a version pin, any developer or CI runner doing a fresh `pip install
commitizen` could silently pick up a breaking major/minor release, causing
`cz bump`, `cz commit`, or changelog generation to behave differently or fail.

The `.cz.toml` config uses `cz_conventional_commits` schema with a custom
commit parser — changes in commitizen's internal API have historically broken
custom configurations across major versions.

## Proposed Solution

Once `audit-pytest-cve-requirements` is implemented and `requirements-dev.txt`
exists, add a single lower-bound pin entry:

```
commitizen>=4.0.0
```

The minimum version (`4.0.0`) is a safe lower bound that covers the current
commitizen 4.x line. No upper-bound cap is added — semver promises no breaking
changes within a major, so `>=4.0.0` is sufficient to prevent accidental
downgrades while allowing patch/minor upgrades.

`make setup` already installs from `requirements-dev.txt` after
`audit-pytest-cve-requirements` updates it, so no Makefile changes are needed
in this item.

## Acceptance Criteria

- [ ] AC1: `requirements-dev.txt` contains an entry matching
  `commitizen>=4.0.0` (or a more specific version if the installed version at
  implementation time demands it).
- [ ] AC2: `pip install -r requirements-dev.txt` in a clean virtualenv
  resolves and installs commitizen without error.
- [ ] AC3: After install, `cz version` exits 0 and the reported version
  satisfies `>=4.0.0`.
- [ ] AC4: The entry does not introduce an upper-bound cap (no `<5.0.0` or
  `==` pin unless a concrete breakage is found).
- [ ] AC5: `make setup` (as updated by `audit-pytest-cve-requirements`) picks
  up the new entry automatically — no additional Makefile changes required.

## Out of Scope

- Upgrading commitizen to a specific patch version — this spec only establishes
  a lower-bound floor.
- Pinning commitizen's own transitive dependencies (e.g. `questionary`,
  `rich`) — stdlib + commitizen pin is sufficient.
- CI pipeline changes — covered by `audit-github-actions-ci` and related items.
- Updating `.cz.toml` configuration — config is already valid and working.
