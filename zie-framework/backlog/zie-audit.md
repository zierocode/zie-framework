# zie-audit

**Problem:** No systematic way to identify improvement opportunities across all
quality dimensions, or to compare the project against current external
standards, best practices, and industry benchmarks.

**Motivation:** Ad-hoc reviews rely on what Claude knows at training time and
what the user happens to ask about. A dedicated audit command proactively
surfaces issues using live external research (OWASP, community standards,
framework docs, similar projects on GitHub), covers all 9 quality dimensions in
one run, and feeds findings directly into the SDLC backlog — turning
observations into tracked work items.

**Rough scope:**

- New command `/zie-audit [--focus <dimension>]`
- Phase 1: detect project stack → build `research_profile`
- Phase 2: 5 parallel internal analysis agents (security, lean, quality, docs,
  architecture — plus performance, deps, DX, standards as sub-checks)
- Phase 3: dynamic external research (WebSearch + WebFetch; queries built from
  `research_profile`, not hardcoded)
- Phase 4: cross-reference + score per dimension (0-100) + severity
  classification (Critical / High / Medium / Low)
- Phase 5: scored report → interactive backlog selection → backlog files created

**Out of scope:**

- Auto-fixing issues (audit produces findings, not fixes)
- Scheduling (manual run only)
- Historical trend tracking / diff with previous audit
- CI pipeline integration
