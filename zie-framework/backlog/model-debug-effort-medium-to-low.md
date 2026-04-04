# Backlog: Drop debug skill effort medium → low (systematic checklist)

**Problem:**
debug skill uses `model: sonnet` + `effort: medium`. The debug skill is a
systematic checklist: reproduce → isolate → hypothesize → test → fix → verify.
Each step is explicit and sequential. This is structured problem-solving that
follows a fixed protocol, not the kind of open-ended reasoning that benefits from
extended thinking.

**Motivation:**
sonnet+low follows the debug checklist correctly. Extended thinking (medium) doesn't
improve step-by-step debugging when the steps are already specified. Saves on every
/fix invocation that calls this skill.

**Rough scope:**
- Change `effort: medium` → `effort: low` in skills/debug/SKILL.md frontmatter
- Tests: debug skill correctly identifies and isolates root cause at low effort
