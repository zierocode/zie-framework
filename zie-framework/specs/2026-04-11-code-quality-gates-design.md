---
approved: false
approved_at:
backlog:
---

# Code Quality Gates — Design Spec

**Problem:** impl-reviewer does an inline check after implementation, but there are no structured pre-commit quality gates. Issues like coverage regression, dead code, and security violations can slip through undetected.

**Approach:** Extend the existing pre-commit hook (or add a new PreToolUse hook on Bash git commit) to run lightweight quality checks: coverage delta, dead code scan, security scan. Warn-only — never block commit. Generic across all project types.

**Components:**
- `hooks/quality-gate.py` — PreToolUse hook on Bash tool when command contains `git commit`
- Reads: coverage reports if present, git diff for dead code signals, bandit/semgrep if available

**Data Flow:**

1. Detect `git commit` in Bash tool_input command
2. Run checks in parallel (best-effort — skip if tool unavailable):

*Check A — Coverage delta:*
- Read last coverage report from `/tmp/zie-<project>-coverage-last`
- Run `coverage report` or parse existing `.coverage` file
- If coverage drops > 2% → warn: "Coverage dropped from X% to Y% — consider adding tests"

*Check B — Dead code signals:*
- Scan git diff for: functions defined but never called (simple heuristic), imports added but unused
- If found → warn: "Possible dead code in diff: <file>:<line>"

*Check C — Security scan:*
- Run `bandit -r <changed files> -ll -q` if bandit available
- Run `semgrep --config auto <changed files>` if semgrep available
- If issues found → warn with finding summary

3. All checks warn-only — print to stderr, never exit non-zero
4. Summary line: "Quality gate: 0 warnings" or "Quality gate: 2 warnings (see above)"

**Generic behavior:**
- Python project: bandit + coverage
- JS project: skip bandit, attempt eslint if available
- Unknown project type: skip language-specific checks, run only dead code heuristic
- No tools available: exit 0 silently (graceful degradation)

**Error Handling:**
- Any check tool missing: skip that check, continue
- Check times out (>10s): skip and warn "check timed out"
- Tier 1 outer guard: bare except → exit 0, never blocks commit
- All checks are advisory — Zie decides whether to address warnings

**Testing:**
- Unit: coverage drop > 2% triggers warning
- Unit: no coverage data → skip coverage check gracefully
- Unit: bandit unavailable → skip security check, exit 0
- Unit: non-git-commit Bash command → hook exits 0 immediately
- Unit: exits 0 on malformed event (@pytest.mark.error_path)
