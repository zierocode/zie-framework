---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-frontmatter-hardening.md
---

# Skills Frontmatter Hardening — Design Spec

**Problem:** All zie-framework skills use minimal frontmatter — no invocation
control, no tool restrictions, no model routing — allowing Claude to
auto-trigger side-effect commands, cluttering the user command menu with
internal skills, and wasting Sonnet capacity on tasks that need only Haiku.

**Approach:** Add targeted frontmatter fields to each of the 10 SKILL.md files
based on role: `disable-model-invocation` for commands Claude must never
auto-trigger, `user-invocable: false` for internal sub-agent skills,
`allowed-tools` restrictions for read-only reviewer skills, and `model`/`effort`
tuning for skills where cost or depth matters. No skill content or logic
changes — frontmatter only.

**Components:**
- Modify: `skills/debug/SKILL.md` — add `user-invocable: false`
- Modify: `skills/retro-format/SKILL.md` — add `user-invocable: false`
- Modify: `skills/tdd-loop/SKILL.md` — add `user-invocable: false`
- Modify: `skills/test-pyramid/SKILL.md` — add `user-invocable: false`
- Modify: `skills/impl-reviewer/SKILL.md` — add `user-invocable: false`, `allowed-tools: Read, Grep, Glob`
- Modify: `skills/plan-reviewer/SKILL.md` — add `user-invocable: false`, `allowed-tools: Read, Grep, Glob`
- Modify: `skills/spec-reviewer/SKILL.md` — add `user-invocable: false`, `allowed-tools: Read, Grep, Glob`
- Modify: `skills/spec-design/SKILL.md` — add `effort: high`
- Modify: `skills/write-plan/SKILL.md` — add `effort: high`
- Modify: `skills/verify/SKILL.md` — no additional frontmatter required (user-facing, general tools, normal effort)

**Full frontmatter delta per skill:**

| Skill | `disable-model-invocation` | `user-invocable` | `allowed-tools` | `model` | `effort` |
| --- | --- | --- | --- | --- | --- |
| `spec-reviewer` | — | `false` | `Read, Grep, Glob` | — | — |
| `plan-reviewer` | — | `false` | `Read, Grep, Glob` | — | — |
| `impl-reviewer` | — | `false` | `Read, Grep, Glob` | — | — |
| `tdd-loop` | — | `false` | — | — | — |
| `retro-format` | — | `false` | — | — | — |
| `test-pyramid` | — | `false` | — | — | — |
| `debug` | — | `false` | — | — | — |
| `spec-design` | — | — | — | — | `high` |
| `write-plan` | — | — | — | — | `high` |
| `verify` | — | — | — | — | — |

Note: `disable-model-invocation: true` applies to commands (zie-release,
zie-retro, zie-backlog, zie-init), not to skills. Those are `.md` files in
`commands/`, not `skills/*/SKILL.md` files. No skills in this repo correspond
to those command names — this scope item is out of range for SKILL.md edits.

**Data Flow:**
1. User or slash command triggers Claude; Claude receives the active plugin's
   skill registry as part of its context injection.
2. For each registered skill, Claude Code reads the SKILL.md frontmatter to
   determine availability and constraints before injecting skill descriptions
   into the model context.
3. Skills with `disable-model-invocation: true` — their descriptions are NOT
   injected into context, preventing Claude from autonomously invoking them.
4. Skills with `user-invocable: false` — hidden from the `/` command picker so
   users do not see or manually trigger them; only callable via
   `Skill(zie-framework:<name>)` from another skill or command.
5. Skills with `allowed-tools` set — when Claude invokes the skill, the tool
   permission set is restricted to the listed tools only for the duration of
   that skill's execution.
6. Skills with `model: haiku` — Claude Code routes the skill invocation to
   Claude Haiku instead of the session default model.
7. Skills with `effort: high` or `effort: low` — Claude Code adjusts thinking
   budget / token allocation accordingly for that invocation.

**Edge Cases:**
- Unknown `model` value in frontmatter (e.g. a typo or a model name Claude Code
  does not recognise): Claude Code falls back to the session's default model
  (inherit); no error surfaced to the user.
- `effort` field present on a skill invoked via a model that does not support
  effort control: the field is silently ignored; no runtime error.
- `user-invocable: false` does NOT prevent a user from calling the skill
  directly via a slash command if they know the exact invocation path — it only
  hides the skill from the picker UI.
- A skill with `allowed-tools` that internally references a tool not in the
  allowlist: the tool call will be blocked by Claude Code's permission layer,
  not by the skill itself; the skill should be authored to only use allowed tools.
- If `allowed-tools` contains a tool name with inconsistent capitalisation (e.g.
  `grep` vs `Grep`): behaviour depends on Claude Code's parser; use the
  canonical PascalCase names (Read, Grep, Glob) to be safe.

**Out of Scope:**
- Changing any skill's content, instructions, or logic.
- Changing command names or command `.md` files (zie-release, zie-retro, etc.).
- Adding `disable-model-invocation` to SKILL.md files — that field is for
  commands, not skills; no skills in this repo require it.
- Adding `model: haiku` + `effort: low` to any skill — `zie-status` is a
  command (`commands/zie-status.md`), not a skill; no equivalent skill exists.
- Creating new skills or restructuring the `skills/` directory.
- Updating `hooks/hooks.json` — the plugin skill registry is derived from
  `skills/*/SKILL.md` file presence; hooks.json maps hook events, not skills.
- Tests for frontmatter parsing beyond verifying YAML is valid and fields are
  present (integration-level Claude Code plugin behaviour is not unit-testable
  in this repo's pytest suite).
