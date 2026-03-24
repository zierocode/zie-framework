# Backlog: Skills Advanced Features — $ARGUMENTS[N], Session Vars, Supporting Files

**Problem:**
zie-framework skills use only basic `$ARGUMENTS` (full string). Indexed access
(`$ARGUMENTS[0]`), session variables (`${CLAUDE_SESSION_ID}`,
`${CLAUDE_SKILL_DIR}`), and supporting files (scripts/, reference.md) are all
unused. Skills that need multiple arguments parse them manually.

**Motivation:**
These are low-effort improvements that make skills more expressive: indexed args
for multi-param skills (e.g. /zie-spec slug type), session ID for per-session
logging, SKILL_DIR for bundled scripts that don't depend on CWD.

**Rough scope:**
- Update zie-spec to use `$ARGUMENTS[0]` (slug) and `$ARGUMENTS[1]` (type: full|quick)
- Update zie-plan to use `$ARGUMENTS[0]` (slug) + optional `$ARGUMENTS[1]` (flags)
- Update hooks that reference scripts to use `${CLAUDE_SKILL_DIR}/scripts/`
  instead of hardcoded paths
- Add `argument-hint:` to skills that take arguments (for autocomplete UX)
- Extract large reference sections from zie-audit SKILL.md into
  `zie-audit/reference.md` (supporting file pattern — keeps SKILL.md < 500 lines)
- Tests: argument substitution correct, SKILL_DIR resolves
