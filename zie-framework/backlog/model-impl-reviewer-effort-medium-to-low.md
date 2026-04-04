# Backlog: Drop impl-reviewer effort medium → low (haiku can't leverage medium)

**Problem:**
impl-reviewer uses `model: haiku` + `effort: medium`. The skill's own comment says:
"Routine checks (AC coverage, test exists, security scanning) run on haiku."
haiku at medium effort is the same model with a larger token budget it cannot
effectively use. The skill already documents escalation to sonnet for complex cases —
so medium effort on haiku is the wrong lever; the right lever is model escalation.

**Motivation:**
haiku+medium wastes budget. Routine AC/test/security checks are pattern-matching
tasks — haiku+low handles them correctly. If a review genuinely needs more depth,
the escalation path to sonnet is the correct mechanism, not higher effort on haiku.

**Rough scope:**
- Change `effort: medium` → `effort: low` in skills/impl-reviewer/SKILL.md frontmatter
- Tests: impl-reviewer still catches AC gaps and missing tests at low effort
