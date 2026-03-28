# audit: docs + standards sprint

## Problem

- `plugin.json` version 1.3.0 — actual version is 1.4.0. Marketplace reports wrong version.
- README.md line 87 shows `project/decisions.md` — renamed to `project/context.md` in v1.3.0.
- `architecture.md` timestamp stale: "Last updated: 2026-03-22".
- Dual ADR numbering: `D-prefix` in context.md vs `ADR-prefix` in decisions/ directory.
- No `SECURITY.md` (OpenSSF scorecard gap).
- CHANGELOG v1.1.0 written in Thai; all other versions in English.

The plugin.json version drift is a release process gap — `make release` updates
VERSION but does not update plugin.json.

## Motivation

Users installing via marketplace see v1.3.0. Developers following README to navigate
their generated project look for `decisions.md` which doesn't exist. ADR dual-numbering
creates confusion about canonical source.

## Scope

- Fix `plugin.json` version → 1.4.0
- Fix README.md: `project/decisions.md` → `project/context.md`
- Update `architecture.md` timestamp → 2026-03-23, add v1.3.0/v1.4.0 changes summary
- Canonicalize ADR numbering: `ADR-NNN` everywhere; update context.md entries
- Add `SECURITY.md` (1-page template: how to report, maintainer contact, disclosure policy)
- Translate CHANGELOG v1.1.0 to English
- Add `commitizen` config to `Makefile` or `.cz.toml` for conventional commit
  enforcement (`feat:`, `fix:`, `BREAKING CHANGE:`) — finding #27

**Prevention — add to `Makefile` release target:**
```makefile
# Sync plugin.json version to match VERSION
jq --arg v "$$(cat VERSION)" '.version = $$v' .claude-plugin/plugin.json \
  > .claude-plugin/plugin.json.tmp && mv .claude-plugin/plugin.json.tmp .claude-plugin/plugin.json
```

**Prevention — add pre-commit check:**
```bash
#!/bin/sh
# .git/hooks/pre-commit or pre-commit config
plugin_ver=$(jq -r .version .claude-plugin/plugin.json)
version_ver=$(cat VERSION)
if [ "$plugin_ver" != "$version_ver" ]; then
  echo "Version drift: plugin.json=$plugin_ver vs VERSION=$version_ver"
  echo "Run: make sync-version"
  exit 1
fi
```

## Prevention mechanism

Makefile `release` target syncs plugin.json automatically. Pre-commit hook blocks
commits where versions diverge. Version drift becomes structurally impossible.
