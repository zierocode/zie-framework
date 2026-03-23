---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-project-md-version-stale.md
---

# PROJECT.md Version Stale — Design Spec

**Problem:** `zie-framework/PROJECT.md` shows `**Version**: 1.4.0` but the
current version is 1.4.1 per `VERSION` and `.claude-plugin/plugin.json`.

**Approach:** Update the version field in `PROJECT.md` from `1.4.0` to
`1.4.1`. Additionally, extend the `sync-version` Makefile target to also
update the version field in `PROJECT.md` so future releases stay in sync
automatically.

**Components:**

- `zie-framework/PROJECT.md` — direct version field fix
- `Makefile` (`sync-version` target) — add `sed` line to update `PROJECT.md`

**Data Flow:**

1. Edit `zie-framework/PROJECT.md` line 7: change `**Version**: 1.4.0` →
   `**Version**: 1.4.1`
2. In `Makefile` `sync-version` target, after the `jq` call that updates
   `plugin.json`, add:

   ```makefile
   sed -i '' 's/\*\*Version\*\*: [0-9.]*/\*\*Version\*\*: '"$$(cat VERSION)"'/' \
     zie-framework/PROJECT.md
   ```

3. `make sync-version` now touches both `plugin.json` and `PROJECT.md` in
   one step.

**Edge Cases:**

- `VERSION` file missing → `sync-version` already errors; no new guard needed
- `PROJECT.md` version field absent or in different format → `sed` is a no-op,
  will need manual fix; acceptable given the field format is stable
- Future templates: `templates/PROJECT.md.template` should use
  `{{version}}` substitution (already intended by `/zie-init`)

**Out of Scope:**

- Automating `sync-version` as a pre-commit hook (separate concern)
- Updating `README.md` version references (no version number in README)
