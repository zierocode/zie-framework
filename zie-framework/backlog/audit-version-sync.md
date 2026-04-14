---
tags: [chore]
---

# Sync VERSION, PROJECT.md, and plugin.json After Releases

## Problem

VERSION file reads 1.29.0, PROJECT.md shows 1.28.4, but v1.30.0 retro commit exists on dev. `make bump` should sync all three but PROJECT.md was not updated. SECURITY.md shows "1.4.x | Yes" — massively outdated.

## Motivation

Version drift across files breaks semver tracking, confuses contributors, and makes SECURITY.md misleading about which versions are supported.

## Rough Scope

- Fix VERSION to match current dev state
- Update PROJECT.md version to match
- Update SECURITY.md Supported Versions table to reflect current versioning
- Add `make sync-version` validation to catch drift in CI