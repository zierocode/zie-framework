---
approved: true
approved_at: 2026-03-24
backlog: backlog/zie-audit-enhancements.md
---

# /zie-audit Enhancements — Hard Data + Historical Diff + Auto-Fix — Design Spec

**Problem:** `/zie-audit` relies on pattern-matching to estimate coverage, CVE exposure, and complexity — findings lack hard numbers. There is no comparison with previous audit runs, so regression vs. improvement is invisible. External research queries are generic and miss dep-specific issues. Low/Medium mechanical findings queue to backlog instead of being fixed immediately.

**Approach:** Four targeted enhancements added to the existing audit phases:
1. **Hard data (Phase 1):** Run `pytest --cov`, `radon cc`, `pip audit` (or `npm audit`) before agents start; feed output into relevant agents as structured data.
2. **Historical diff (post-synthesis):** Load most recent `evidence/audit-*.md`; diff scores per dimension; prepend "Since last audit" section to the report.
3. **Version-specific research (Phase 3):** Extract top 10 pinned deps from manifest; include version-specific search queries alongside generic ones.
4. **Auto-fix offer (post-backlog):** After backlog selection, offer immediate fix for findings flagged `auto-fixable: true` (Low/Medium severity, purely mechanical).

**Components:**
- Modify: `commands/zie-audit.md` — add hard-data tool run block in Phase 1; add historical diff step after synthesis; update Phase 3 research profile to include version-specific queries; add auto-fix offer step after backlog selection

**Acceptance Criteria:**
- [ ] Phase 1 includes `pytest --cov`, `radon cc`, and `pip audit` (or equivalent) output
- [ ] Hard data numbers appear in agent context for Security and Quality agents
- [ ] "Since last audit" diff section appears in report when a previous audit exists in `evidence/`
- [ ] Phase 3 search queries include pinned dep versions from manifest
- [ ] Auto-fix offer appears after backlog selection for Low/Medium mechanical findings
- [ ] All existing 5 audit phases and 9 dimensions preserved

**Out of Scope:**
- CI integration or scheduled audits
- External dashboard or metrics storage
- Auto-fix for High/Critical severity findings
