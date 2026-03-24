---
approved: true
approved_at: 2026-03-24
backlog: backlog/model-haiku-fast-skills.md
---

# model:haiku + effort:low for Fast/Status Skills — Design Spec

**Problem:** Every zie-framework skill and command runs on the session default
model (Sonnet), including pure read-and-format tasks like `/zie-status` and the
SessionStart additionalContext injection that need no deep reasoning.

**Approach:** Add `model` and `effort` frontmatter fields to skill and command
files based on cognitive complexity: `model: haiku` + `effort: low` for tasks
whose output is fully determined by reading files and formatting; `effort: high`
for tasks already receiving it from the frontmatter-hardening spec; and
`effort: medium` (explicit, not implied default) for balanced implementation
tasks. The `session-resume.py` hook produces plain text from file reads — it
runs outside the Claude Code model routing system and needs no change. This
change is additive-only: no skill content, logic, or tool allowlists are
modified.

**Components:**
- Modify: `commands/zie-status.md` — add `model: haiku`, `effort: low`
- Modify: `skills/spec-reviewer/SKILL.md` — add `model: haiku`, `effort: low`
- Modify: `skills/plan-reviewer/SKILL.md` — add `model: haiku`, `effort: low`
- Modify: `skills/impl-reviewer/SKILL.md` — add `model: haiku`, `effort: low`
- Modify: `skills/spec-design/SKILL.md` — add `model: sonnet`, `effort: high`
  (makes existing `effort: high` from frontmatter-hardening spec explicit with
  model pin; this file already has `effort: high` pending that spec)
- Modify: `skills/write-plan/SKILL.md` — add `model: sonnet`, `effort: high`
  (same as above)
- Modify: `commands/zie-spec.md` — add `effort: high`
- Modify: `commands/zie-plan.md` — add `effort: high`
- Modify: `commands/zie-implement.md` — add `effort: medium`
- Modify: `commands/zie-fix.md` — add `effort: medium`
- No change: `skills/tdd-loop/SKILL.md`, `skills/debug/SKILL.md`,
  `skills/retro-format/SKILL.md`, `skills/test-pyramid/SKILL.md`,
  `skills/verify/SKILL.md` — these are either process guides (model follows
  caller) or balanced utility skills with no strong cost/depth signal
- No change: `hooks/session-resume.py` — pure Python, runs outside model
  routing; additionalContext is injected as a string, not a model call

**Data Flow:**

1. User or hook triggers a command or skill invocation.
2. Claude Code reads the command/skill's frontmatter before dispatching the
   invocation to the model layer.
3. If `model: haiku` is present, Claude Code routes the invocation to Claude
   Haiku instead of the session default model.
4. If `effort: low` is present, Claude Code reduces the thinking budget /
   token allocation for that invocation.
5. If `effort: high` is present, Claude Code increases the thinking budget
   (extended thinking mode where supported).
6. If `effort: medium` is present, Claude Code uses the balanced default
   allocation, but the intent is now explicit and version-stable in the file.
7. The invoked skill or command executes normally — no behavioral change.
8. Model routing is transparent to the user; output format is unchanged.

Specific routing decisions per file:

| File | `model` | `effort` | Rationale |
| --- | --- | --- | --- |
| `commands/zie-status.md` | `haiku` | `low` | Read files + format table; zero reasoning required |
| `skills/spec-reviewer/SKILL.md` | `haiku` | `low` | Checklist evaluation against loaded text; structured output |
| `skills/plan-reviewer/SKILL.md` | `haiku` | `low` | Checklist evaluation against loaded text; structured output |
| `skills/impl-reviewer/SKILL.md` | `haiku` | `low` | Diff + criteria match; structured verdict |
| `skills/spec-design/SKILL.md` | `sonnet` | `high` | Deep design thinking; trade-off analysis |
| `skills/write-plan/SKILL.md` | `sonnet` | `high` | Full TDD plan authoring; complex dependency reasoning |
| `commands/zie-spec.md` | — | `high` | Drives spec-design; needs depth for design questions |
| `commands/zie-plan.md` | — | `high` | Drives write-plan; needs depth for plan decisions |
| `commands/zie-implement.md` | — | `medium` | TDD loop; balanced — needs some reasoning, not deep design |
| `commands/zie-fix.md` | — | `medium` | Debug + fix; balanced — diagnostic reasoning, not design |

**Edge Cases:**

- `model: haiku` on a reviewer skill that receives a large context bundle
  (Phase 1 loads up to 4 files + ADRs): Haiku's context window is sufficient
  for typical zie-framework docs; if a bundle exceeds Haiku's limit, Claude Code
  will surface a context-length error. This is acceptable — the reviewer's
  `allowed-tools: Read, Grep, Glob` constraint (from frontmatter-hardening)
  already limits what the skill can load.
- Frontmatter-hardening spec (2026-03-24) also sets `effort: high` on
  `spec-design` and `write-plan`. These two specs must be applied together or
  in sequence — both adding `effort: high` to the same files is idempotent
  (same value, same key). This spec additionally pins `model: sonnet` on those
  two skills to ensure they are never silently downgraded if a future default
  changes.
- `effort: medium` is the documented default in Claude Code; adding it
  explicitly to `zie-implement` and `zie-fix` has no runtime effect today but
  makes the intent version-stable and visible in the file.
- A future Claude Code version that does not support the `model` frontmatter
  field will silently ignore it and fall back to the session default — no
  regression in behavior, only loss of cost optimisation.
- `effort` field on a model that does not support effort control (e.g. an
  older API tier): silently ignored per Claude Code's own handling; no error.
- `commands/zie-retro.md`, `commands/zie-backlog.md`, `commands/zie-release.md`,
  `commands/zie-resync.md`, `commands/zie-audit.md`, `commands/zie-init.md`:
  not assigned `model`/`effort` in this spec — out of scope (see below).

**Out of Scope:**

- Changing `hooks/session-resume.py` — the SessionStart additionalContext is
  built by a Python script and printed as a string; it does not run through
  Claude Code's model routing and cannot receive a `model` or `effort` hint.
- Adding `model`/`effort` to `zie-retro.md`, `zie-backlog.md`,
  `zie-release.md`, `zie-resync.md`, `zie-audit.md`, `zie-init.md` — these
  commands have mixed or unclear cognitive profiles; routing decisions for them
  are deferred to a future backlog item.
- Changing any skill's content, instructions, checklist logic, or tool
  allowlists.
- Creating new skills or commands.
- Adding tests beyond verifying that YAML frontmatter parses without error and
  that the correct keys are present (integration-level model routing is not
  unit-testable in this repo's pytest suite).
- Documenting model/effort choices outside the skill/command frontmatter itself
  — the frontmatter is the authoritative source; no separate reference doc is
  needed.
