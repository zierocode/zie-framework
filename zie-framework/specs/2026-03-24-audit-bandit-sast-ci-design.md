---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-bandit-sast-ci.md
---

# Bandit SAST in CI Pipeline — Design Spec

**Problem:** No static analysis tool scans the hook codebase, so security regressions (subprocess misuse, unsafe `/tmp` writes, regex on untrusted input) reach `main` undetected and OpenSSF Scorecard's SAST check fails.

**Approach:** Add `bandit -r hooks/ -ll` as a `make lint-bandit` target and wire it into the existing `make lint` target and `.githooks/pre-commit`. The `-ll` flag (medium severity + medium confidence) avoids noise from low-confidence findings while catching the known vulnerability classes. No CI YAML changes needed — pre-commit already runs on every commit, and `make test` is the merge gate.

**Components:**
- `Makefile` — new `lint-bandit` target; extend `lint` target to call `lint-bandit`
- `.githooks/pre-commit` — add `make lint-bandit` step before the markdownlint check
- `requirements-dev.txt` (or equivalent) — add `bandit>=1.7` as a dev dependency
- `tests/test_bandit_ci.py` (optional smoke test) — assert `bandit -r hooks/ -ll` exits 0

**Data Flow:**
1. Developer runs `git commit` — pre-commit hook fires.
2. Pre-commit calls `make lint-bandit`.
3. `make lint-bandit` runs `python3 -m bandit -r hooks/ -ll -q`.
4. Bandit scans all `.py` files under `hooks/`; exits 0 (clean) or non-zero (findings).
5. On non-zero exit, pre-commit prints output and blocks the commit.
6. On `make lint`, same step runs alongside `py_compile` syntax check.
7. Bandit findings surface as actionable line-level messages pointing to the exact hook and line.

**Edge Cases:**
- `bandit` not installed — pre-commit check should guard with `command -v bandit` and print a clear install instruction, then exit 0 (warn-only) so unrelated contributors are not hard-blocked; CI should treat missing bandit as a hard failure.
- False positives on `subprocess` usage that is already safe (list-form args) — add inline `# nosec B603` comments only where Bandit flags confirmed-safe patterns; document rationale inline.
- New hook files added later — `bandit -r hooks/` picks them up automatically.

**Out of Scope:**
- Semgrep integration — separate tool, separate item; Bandit is sufficient for OpenSSF SAST.
- Scanning non-hook Python files (e.g. `tests/`) — out of security scope for this item.
- GitHub Actions / CI YAML creation — pre-commit gate is the primary enforcement point for this solo-dev workflow.
