# /zie-audit Enhancements — Hard Data + Historical Diff

## Problem

`/zie-audit` relies on Claude pattern-matching to estimate coverage, detect
CVEs, and assess complexity. Findings are directionally correct but lack hard
numbers. There is also no comparison with previous audit runs, so it is
impossible to know if the project is improving or regressing over time.

## Motivation

Four concrete gaps limit audit quality for a solo developer:

1. **No hard data** — coverage %, cyclomatic complexity, and real CVEs are
   all guessable from tools already present in the stack (`pytest --cov`,
   `radon`, `pip audit`). Running these before agents start gives Agent C
   and Agent A actual numbers to reason from, not estimates.

2. **No historical diff** — `evidence/` already stores past audit reports.
   Comparing current score vs. last run ("Security: 72 → 68, regressed")
   surfaces what was fixed and what got worse since the last audit.

3. **Generic external research** — current queries like "python security
   vulnerabilities checklist" miss dep-specific issues. Detecting exact
   dependency versions from `requirements.txt` / `package.json` and querying
   for those specifically (e.g., "bandit 1.7.x CVE") yields more actionable
   findings.

4. **No auto-fix for low-hanging fruit** — Low/Medium findings that are
   purely mechanical (unused imports, trivial dead code, formatting) get
   queued to the backlog but could be fixed immediately during the audit
   session, saving a full SDLC cycle.

## Rough Scope

- Phase 1 of audit: run hard-data tools (`pytest --cov`, `radon cc`, `pip
  audit` / `npm audit`) and feed output into relevant agents
- After synthesis: load most recent `evidence/audit-*.md`, diff scores per
  dimension, prepend a "Since last audit" section to the report
- Phase 3: extract top 10 deps with pinned versions from manifest, include
  version-specific queries alongside generic ones
- After backlog selection: offer immediate fix for findings flagged as
  auto-fixable (Low/Medium, mechanical) before closing the audit
- Out of scope: CI integration, scheduled audits, external dashboard
