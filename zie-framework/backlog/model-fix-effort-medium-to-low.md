# Backlog: Drop /fix effort medium → low (systematic checklist, not extended reasoning)

**Problem:**
/fix uses `model: sonnet` + `effort: medium`. fix follows a systematic debug
checklist: reproduce, isolate, identify root cause, fix, write regression test,
verify. This is sequential structured work — not the kind of open-ended reasoning
that benefits from extended thinking (medium effort).

**Motivation:**
Debugging quality comes from methodical steps and good test coverage, not from
extended thinking time. sonnet+low follows the checklist correctly and produces
the same fix + test output at lower cost.

**Rough scope:**
- Change `effort: medium` → `effort: low` in commands/fix.md frontmatter
- Tests: fix correctly produces regression test + passing suite at low effort
