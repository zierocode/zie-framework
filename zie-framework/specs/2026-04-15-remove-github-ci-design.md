---
approved: true
approved_at: 2026-04-15
backlog: backlog/remove-github-ci.md
---

# Remove GitHub CI — Design Spec

**Problem:** GitHub Actions workflows and Dependabot run on every push/PR but serve no deployment purpose — the project releases by pushing to main via `/release`, not via CI.
**Approach:** Delete all `.github/` CI files and their dedicated test files. Keep local Makefile targets (`test-ci`, `test-unit`, `lint`) which are used independently of GitHub CI. Remove test files that directly validate CI workflow YAML structure.
**Components:**
- `.github/workflows/ci.yml` — DELETE
- `.github/workflows/release-provenance.yml` — DELETE
- `.github/dependabot.yml` — DELETE
- `.github/` directory — DELETE (empty after above)
- `tests/unit/test_ci_workflow.py` — DELETE (validates ci.yml structure)
- `tests/unit/test_ci_config.py` — DELETE (reads ci.yml directly)

**Data Flow:**
1. Delete `.github/workflows/ci.yml`
2. Delete `.github/workflows/release-provenance.yml`
3. Delete `.github/dependabot.yml`
4. Delete `.github/` directory (now empty)
5. Delete `tests/unit/test_ci_workflow.py`
6. Delete `tests/unit/test_ci_config.py`
7. Run `make test-unit` to confirm no regressions

**Edge Cases:**
- `test_makefile_targets.py` references `test-ci` Makefile target — KEEP, it tests the local Makefile target which still exists
- `test_claude_md_commands.py` documents `test-ci` in CLAUDE.md — KEEP, documentation is still valid
- `test_tdd_loop_skill.py` references `test_ci` as a Makefile target — KEEP, not related to GitHub CI
- No other files import from `test_ci_workflow` or `test_ci_config` — safe to delete

**Out of Scope:**
- Makefile targets (`test-ci`, `test-unit`, `lint`, `test-int`, `test`) — these are local dev tools, not CI
- CLAUDE.md documentation about test commands — still accurate for local use
- Any ADR or spec references to CI in archived files — historical, no action needed