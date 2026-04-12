---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-dep-pinning-inconsistency.md
---

# Lean Dep Pinning Inconsistency — Design Spec

**Problem:** `requirements-dev.txt` uses inconsistent pinning strategies: `>=` for pytest, pytest-cov, coverage, bandit, and commitizen, but exact `==` for ruff. This split policy is inconsistent and blocks Dependabot from auto-merging ruff upgrades (exact pins require a PR approval, not just a version bump). It also creates confusion about the project's intended update policy for dev tools.

**Approach:** Adopt compatible-release pinning (`~=X.Y.Z`) for all dev dependencies. This strategy allows patch-level upgrades automatically (e.g. `~=0.11.2` allows `0.11.x` but not `0.12.x`), is semantically tighter than `>=` (no unexpected major/minor jumps), and makes Dependabot auto-merge viable across all deps. Add a header comment explaining the pinning policy choice.

**Components:**
- `requirements-dev.txt` — switch all six deps from mixed `>=` / `==` to `~=X.Y.Z`, add policy comment header

**Data Flow:**
1. Developer runs `pip install -r requirements-dev.txt` — pip resolves `~=X.Y.Z` as `>= X.Y.Z, == X.Y.*`
2. Dependabot opens a PR bumping e.g. ruff `~=0.11.2` → `~=0.11.3` — auto-merge is unblocked
3. If a dep releases a breaking minor bump, Dependabot still opens a PR but it requires manual review (correct behavior)

**Edge Cases:**
- Existing CI/CD may have cached a virtualenv with exact ruff `==0.11.2`; `~=0.11.2` is a superset so no breakage
- If a patch release of any dep introduces a regression, `~=` still pins the minor — only a minor-bump PR would introduce the regression, which requires manual review

**Out of Scope:**
- Switching to a lock file (`pip-compile`, `poetry.lock`, `uv.lock`) — separate concern
- Changing pinning strategy for production dependencies (none exist in this repo)
- Setting up Dependabot auto-merge rules in CI (separate chore)
- Updating CLAUDE.md or project docs — pinning policy is self-documented in requirements-dev.txt header comment
