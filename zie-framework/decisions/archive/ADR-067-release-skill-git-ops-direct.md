# ADR-067: Release Skill Performs Git Ops Directly

**Status:** Accepted  
**Date:** 2026-04-14  
**Version:** v1.28.4

## Context

The `/release` skill previously delegated git operations to `make release` (Makefile target). This caused duplication:

1. `/release` skill already committed release files (VERSION, CHANGELOG.md, ROADMAP.md)
2. `make release` target also did: bump, commit, merge dev→main, tag, push, merge main→dev
3. Result: **"tag already exists" error**, dirty tree check failures, double merge conflicts

## Decision

**`/release` skill performs git operations directly:**

```bash
# Step 8: Publish (git ops directly — NOT make release)
git checkout main && git merge dev --no-ff -m "release: v${NEW_VERSION}"
git tag -s v${NEW_VERSION} -m "release v${NEW_VERSION}"
git push origin main --tags
make _publish NEW=${NEW_VERSION}
git checkout dev && git merge main && git push origin dev
```

**Makefile changes:**
- `make release` → DEPRECATED with warning (backwards compatibility)
- `make _publish` → New hook target (no-op, override in `Makefile.local`)

## Consequences

**Positive:**
- No more tag duplication errors
- Single source of truth for git operations
- Projects can customize publish logic via `make _publish`

**Negative:**
- `make release` target now deprecated (breaking for direct Makefile users)
- Tests needed updates to reflect new pattern

**Neutral:**
- Release workflow now skill-centric, not Makefile-centric

## Alternatives Considered

1. **Make `make release` idempotent** — Complex, error-prone
2. **Remove `make release` entirely** — Breaking change for existing users
3. **Skill calls `make _release-internal`** — Same duplication, just renamed

**Chosen:** Skill does git ops directly + calls only `make _publish`
