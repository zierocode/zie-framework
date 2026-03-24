# Backlog: Skills Frontmatter Hardening

**Problem:**
All zie-framework skills use default frontmatter — no invocation control, no
tool restrictions, no model tuning. This means: (1) Claude can auto-trigger
/zie-release or /zie-retro without being asked, (2) internal skills clutter the
/ command menu, (3) every skill uses Sonnet regardless of complexity.

**Motivation:**
Skills frontmatter supports `disable-model-invocation`, `user-invocable`,
`allowed-tools`, `model`, and `effort` fields. Applying these correctly
prevents dangerous auto-invocation, cleans up the UX, and routes fast tasks
to cheaper models.

**Rough scope:**
- `disable-model-invocation: true` on: zie-release, zie-retro, zie-backlog,
  zie-init (side-effect commands the user must trigger explicitly)
- `user-invocable: false` on: spec-reviewer, plan-reviewer, impl-reviewer,
  tdd-loop, retro-format, test-pyramid (internal skills, not user commands)
- `allowed-tools: Read, Grep, Glob` on all reviewer skills
- `model: haiku` + `effort: low` on: zie-status (fast, no deep thinking)
- `effort: high` on: zie-spec, zie-plan (need full capability)
- Update `hooks/hooks.json` plugin skill section accordingly
- Tests: frontmatter parses, no skill regression
