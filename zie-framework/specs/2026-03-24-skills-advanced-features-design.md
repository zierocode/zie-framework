---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-advanced-features.md
---

# Skills Advanced Features ($ARGUMENTS[N], Session Vars, Supporting Files) — Design Spec

**Problem:** zie-framework skills receive only the raw `$ARGUMENTS` string, forcing
multi-parameter skills (zie-spec, zie-plan) to parse arguments manually, leaving
`$ARGUMENTS[0]`/`$ARGUMENTS[1]` indexed access unused, `${CLAUDE_SKILL_DIR}`
unreferenced in script paths, and zie-audit's SKILL.md bloated with reference
content that should live in a supporting file.

**Approach:** Three targeted changes, each independent: (1) update zie-spec and
zie-plan skills to document and use `$ARGUMENTS[0]`/`$ARGUMENTS[1]` indexed
syntax, replacing prose-described manual parsing with explicit field names and
semantics; (2) add `argument-hint:` frontmatter to every skill that accepts
arguments, matching the pattern already established in commands; (3) extract
the large reference sections from zie-audit's SKILL.md into a
`skills/zie-audit/reference.md` supporting file, keeping SKILL.md under 500
lines and establishing the supporting-file pattern for future skills. No changes
to hooks.json, hook scripts, or the `${CLAUDE_SKILL_DIR}` variable itself — the
variable is already resolved by Claude Code; skills simply need to reference it
correctly when they bundle scripts.

**Components:**
- Modify: `skills/spec-design/SKILL.md` — add `argument-hint:` to frontmatter;
  document `$ARGUMENTS[0]` as slug, `$ARGUMENTS[1]` as mode (`full|quick`)
- Modify: `skills/write-plan/SKILL.md` — add `argument-hint:` to frontmatter;
  document `$ARGUMENTS[0]` as slug, `$ARGUMENTS[1]` as optional flags
- Modify: `skills/spec-reviewer/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/plan-reviewer/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/impl-reviewer/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/debug/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/tdd-loop/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/verify/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/retro-format/SKILL.md` — add `argument-hint:` to frontmatter
- Modify: `skills/test-pyramid/SKILL.md` — add `argument-hint:` to frontmatter
- Create: `skills/zie-audit/SKILL.md` — new zie-audit skill entry point
  (< 500 lines); replaces oversized reference content in zie-audit command
- Create: `skills/zie-audit/reference.md` — supporting file: extracted reference
  sections (dimension definitions, scoring rubric, query template library)
- Create: `tests/unit/test_skills_advanced_features.py` — argument substitution
  correctness, argument-hint presence, SKILL_DIR reference, supporting file
  existence, SKILL.md line-count guard

**Data Flow:**

1. User invokes `/zie-spec my-feature full` — Claude Code tokenises the argument
   string and makes `$ARGUMENTS[0]` = `"my-feature"`, `$ARGUMENTS[1]` = `"full"`
   available as substitution variables when rendering the skill's SKILL.md
   instructions.
2. `spec-design/SKILL.md` reads `$ARGUMENTS[0]` as the backlog slug (passed from
   `/zie-spec`) and `$ARGUMENTS[1]` as the mode hint. The skill uses these
   directly in its steps without manual string splitting.
3. Similarly, `write-plan/SKILL.md` reads `$ARGUMENTS[0]` as slug and
   `$ARGUMENTS[1]` as an optional flags string (e.g. `--no-memory`). If
   `$ARGUMENTS[1]` is absent/empty the skill falls back to defaults.
4. Skills that bundle external scripts (future pattern) reference their scripts
   via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — this path is resolved by
   Claude Code to the absolute path of the skill's own directory, making the
   reference CWD-independent. No hook scripts in this repo currently need this
   change; the pattern is documented in spec-design and write-plan as a note for
   future skill authors.
5. When Claude Code renders the `argument-hint:` frontmatter field, it surfaces
   the hint string in the slash-command autocomplete UI next to the skill name.
   Skills invoked only programmatically (reviewers, tdd-loop, retro-format,
   test-pyramid) still get `argument-hint:` so their invocation signatures are
   self-documenting in the skill file itself.
6. For zie-audit: `/zie-audit` command invokes
   `Skill(zie-framework:zie-audit)` — Claude Code loads
   `skills/zie-audit/SKILL.md` as the instruction set. When the skill reaches
   the dimension-definitions or query-template steps, it reads
   `${CLAUDE_SKILL_DIR}/reference.md` via the Read tool. The supporting file is
   never injected automatically — the skill must explicitly read it.

**Edge Cases:**
- `$ARGUMENTS[1]` absent: skill must treat it as empty string / use default
  behaviour — never raise an error or block execution. Both spec-design and
  write-plan must document their defaults explicitly in SKILL.md.
- `$ARGUMENTS[0]` absent when slug is required: skill should fall back to
  prompting the user for the slug, matching existing behaviour in the commands
  (no arg → list menu). Document this fallback in spec-design and write-plan.
- `${CLAUDE_SKILL_DIR}` unresolved (Claude Code version that does not support
  it): the Read path will fail. Skill must wrap any `${CLAUDE_SKILL_DIR}` reads
  in a graceful-skip note — "If reference.md is not found, proceed without it."
  This follows ADR-002 (graceful degradation) and ADR-003 (never crash Claude).
- zie-audit SKILL.md > 500 lines after extraction: the spec mandates keeping
  SKILL.md < 500 lines. The 500-line guard test will fail CI, catching
  unintentional bloat. Current `commands/zie-audit.md` is ~218 lines — the new
  `skills/zie-audit/SKILL.md` must stay well under the limit.
- `argument-hint:` value with special YAML characters (colons, brackets): must
  be quoted in frontmatter. Follow the existing pattern in
  `commands/zie-spec.md` (already uses a quoted `argument-hint:` with brackets).
- Skills that have no meaningful arguments (retro-format, test-pyramid, tdd-loop,
  reviewers): set `argument-hint:` to an empty string or omit value — document
  as "no arguments" to make the intent explicit rather than leaving the field
  absent and ambiguous.
- Supporting file `reference.md` missing from a deployed plugin: the skill reads
  it via `${CLAUDE_SKILL_DIR}/reference.md`; if absent, skip gracefully and note
  the gap in output. Never block the skill.

**Out of Scope:**
- Changing any hook script (`hooks/*.py`) to use `${CLAUDE_SKILL_DIR}` — hooks
  already use `${CLAUDE_PLUGIN_ROOT}` via hooks.json and have no skill directory
  concept.
- Adding `${CLAUDE_SESSION_ID}` session variable usage to any skill or hook —
  backlog mentions it as motivation context but no concrete use case is defined
  for this feature set; defer to a separate backlog item if needed.
- Migrating the existing `commands/zie-audit.md` content into the new skill —
  the command file stays as the control-plane entry point; the skill is a new
  addition that the command will invoke.
- Adding scripts/ subdirectories to existing skills (spec-design, write-plan,
  etc.) — no bundled scripts are needed now; SKILL_DIR is documented as a
  pattern note only.
- Changing `hooks/hooks.json` or any hook event wiring.
- Updating `commands/zie-spec.md` or `commands/zie-plan.md` — the indexed
  argument syntax is a skill-layer concern; command files pass the raw argument
  string through and are not affected.
- Adding `argument-hint:` to command `.md` files in `commands/` — several
  already have it; this spec covers only `skills/*/SKILL.md` files.
- Auto-injection of `reference.md` content into skill context — the skill must
  explicitly Read it; Claude Code does not auto-load supporting files.
