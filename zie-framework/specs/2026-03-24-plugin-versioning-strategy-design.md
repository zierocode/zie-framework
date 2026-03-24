---
approved: true
approved_at: 2026-03-24
backlog: backlog/plugin-versioning-strategy.md
---

# Plugin Versioning Strategy — Semver Auto-Bump — Design Spec

**Problem:** Version bumps require manually updating both `VERSION` and `.claude-plugin/plugin.json`. There is no enforcement that they stay in sync. The `/zie-release` gate relies on the developer remembering both updates — a silent drift risk on every release.

**Approach:** Add `make bump NEW=<v>` as a single atomic operation that updates both files. Add a version consistency gate to `/zie-release` that reads both files and fails with a clear message if they diverge. The bump target is the single source of truth for version changes.

**Components:**
- Modify: `Makefile` — add `bump` target: validates `NEW` is set and is valid semver; writes `NEW` to `VERSION`; updates `version` field in `.claude-plugin/plugin.json` using `sed` or Python inline; prints "Bumped to vNEW" on success
- Modify: `commands/zie-release.md` — add version consistency gate as first check: read `VERSION` and `.claude-plugin/plugin.json`; compare; fail with "Version mismatch: VERSION=X, plugin.json=Y — run `make bump NEW=<v>`" if diverged

**Acceptance Criteria:**
- [ ] `make bump NEW=1.7.0` updates `VERSION` to `1.7.0` and `plugin.json` version to `1.7.0`
- [ ] Both files updated atomically — no partial state if one write fails
- [ ] `make bump` without `NEW` prints usage error and exits non-zero
- [ ] `/zie-release` gate fails clearly when VERSION != plugin.json version
- [ ] `/zie-release` gate passes when both files are in sync
- [ ] Existing `make push` and `make release` targets unchanged

**Out of Scope:**
- Automatic semantic version inference from commit messages
- Changelog generation
- Version bumping as part of the `/zie-release` flow itself (developer runs `make bump` manually before release)
