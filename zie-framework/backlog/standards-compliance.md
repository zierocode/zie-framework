# Standards: Compliance and Consistency Gaps

**Source**: audit-2026-03-24b L10+L14+L15 + integration test + project name (Agents A,C,E)
**Effort**: S
**Score impact**: +5 Low = +5 (Standards → 87, Developer Exp → 90)

## Problem

5 low-severity compliance and consistency gaps:

### 1. Version drift enforcement absent (L15)
VERSION file and plugin.json must stay in sync but no automated test enforces this.
`make bump` updates both but `make release` doesn't verify they match before tagging.
Add a test: `assert open("VERSION").read().strip() == plugin_json["version"]`.

### 2. Error message format inconsistent (L14)
Most hooks log `[zie-framework] <hook-name>: <message>` to stderr.
`session-resume.py:26` uses `[zie] warning: ...` (different prefix).
Standardize all hooks to `[zie-framework] <hook-name>: <message>`.

### 3. Integration test deselection undocumented (Agent C)
`make test-unit` deselects 63 integration tests via `-m "not integration"`.
No CI/CD runs these integration tests (would require live Claude session).
Document this explicitly in CLAUDE.md and add a comment in Makefile.

### 4. Project name sanitization inconsistent (L — Agent E)
`notification-log.py:65` uses `get_cwd().name` directly as a dict key without
`safe_project_name()`. Even though dict keys don't need sanitization, the
inconsistency creates maintenance confusion. Standardize to always use
`get_project_name()` helper (from consolidate-utils-patterns backlog item).

### 5. OpenSSF Scorecard gaps
- No GitHub Actions CI workflow detected (Scorecard penalizes)
- No branch protection rules documented
- SLSA Level 1 provenance not generated at release
Add `.github/workflows/ci.yml` running `make test lint-bandit` on push/PR.

## Scope

- `tests/unit/test_versioning_gate.py`: add version consistency assertion
- `hooks/session-resume.py:26`: fix log prefix to `[zie-framework]`
- `CLAUDE.md`: document integration test exclusion and how to run them
- `Makefile`: add comment on 63 deselected integration tests
- `hooks/notification-log.py:65`: use `get_project_name()` after consolidation
- `.github/workflows/ci.yml`: basic CI pipeline (test + lint-bandit)

## Acceptance Criteria

- [ ] Test fails if VERSION != plugin.json version
- [ ] All hooks use consistent `[zie-framework] <hook>:` log prefix
- [ ] Integration test exclusion documented in CLAUDE.md and Makefile
- [ ] project name always via safe_project_name() / get_project_name()
- [ ] GitHub Actions CI workflow created
