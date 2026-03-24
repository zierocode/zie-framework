# Plugin Versioning Strategy — Semver Auto-Bump on Ship

## Problem

Version bumps are manual and error-prone: `VERSION` file and `plugin.json`
must both be updated on every release. There is no enforcement that they
stay in sync, and the current `/zie-release` gate relies on the developer
remembering to update both.

## Motivation

A single `make bump NEW=<v>` target that atomically updates both files removes
the manual coordination. A pre-release gate that verifies sync catches drift
before it reaches the tag.

## Rough Scope

- Add `make bump NEW=<v>` target: updates `VERSION` and `.claude-plugin/plugin.json`
  version field atomically (both succeed or neither)
- Add version consistency check to `/zie-release` gate: compare VERSION file
  vs. plugin.json; fail with clear message if they diverge
- Out of scope: automated semantic version inference from commit messages;
  changelog generation
