---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-fork-context.md
---

# Skills context:fork for Isolated Reviewer Execution — Design Spec

**Problem:** Reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) run
inline in the main conversation, so their Phase 1 file reads and analysis
output pollute the main context window with noise irrelevant to the ongoing
session.

**Approach:** Add `context: fork` frontmatter to all three reviewer skills so
Claude Code executes each review in an isolated subagent context. The forked
subagent loads its context bundle, runs all three review phases, and returns
only the structured verdict (`✅ APPROVED` / `❌ Issues Found`) to the main
conversation. Because reviewers already self-contain their context load via
Phase 1, they are naturally suited to fork execution — they require no main
conversation history. `spec-reviewer` and `plan-reviewer` use `agent: Explore`
(read-only, no shell); `impl-reviewer` uses `agent: general-purpose` to retain
`Bash` access required for `make test-unit` confirmation.

**Components:**
- Modify: `skills/spec-reviewer/SKILL.md` — add `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob`
- Modify: `skills/plan-reviewer/SKILL.md` — add `context: fork`, `agent: Explore`, `allowed-tools: Read, Grep, Glob`
- Modify: `skills/impl-reviewer/SKILL.md` — add `context: fork`, `agent: general-purpose`, `allowed-tools: Read, Grep, Glob, Bash`
- Create: `tests/unit/test_skills_fork_context.py` — pytest assertions verifying frontmatter fields are present and correct per skill

**Data Flow:**

1. Caller skill (`spec-design`, `write-plan`, or `zie-implement`) invokes
   `Skill(zie-framework:<reviewer>)` with input args (spec path, plan path, or
   changed-files list).
2. Claude Code reads the target SKILL.md frontmatter; sees `context: fork`.
3. Claude Code spawns a new isolated subagent context with the specified
   `agent:` profile and `allowed-tools:` restriction. The subagent has no
   access to the main conversation's message history.
4. The forked subagent executes Phase 1 (context bundle load) — reads spec,
   ADRs, context.md, ROADMAP, and/or changed files using the allowed tools.
5. The forked subagent executes Phase 2 (review checklist) and Phase 3
   (context cross-reference checks) entirely within its own context window.
6. The forked subagent outputs only the final verdict block (`✅ APPROVED` or
   `❌ Issues Found` with numbered issues) and exits.
7. Claude Code surfaces the subagent's output back to the main conversation as
   the skill's return value.
8. The calling skill (`spec-design`, `write-plan`, or `zie-implement`) reads
   the verdict and acts: on `✅ APPROVED` continue; on `❌ Issues Found` apply
   fixes and re-invoke the reviewer (up to 3 iterations).

**Edge Cases:**

- **Verdict surfacing regression:** If `context: fork` changes how the return
  value reaches the caller, the review loop in `spec-design`/`write-plan`/
  `zie-implement` must still be able to parse `✅ APPROVED` from the subagent
  output. The verdict format (plain text block) is unchanged — no parsing logic
  changes needed.
- **impl-reviewer needs Bash:** `make test-unit` confirmation is described as
  "Caller confirms — reviewer checks logic" in Phase 2 item 3; the reviewer
  does not itself run `make test-unit`. However, `agent: general-purpose` is
  used (not `Explore`) to preserve the option for future direct test
  invocation. `allowed-tools` for impl-reviewer explicitly includes `Bash`.
- **No conversation history in fork:** Reviewers already load all required
  context via Phase 1 from files on disk. The loss of main conversation history
  in a forked context has no effect on review quality.
- **Missing files during Phase 1:** Existing graceful-skip logic ("skip if
  missing — never block review") is unchanged. The forked subagent follows the
  same rules as the inline reviewer.
- **Caller passes wrong path:** If the caller provides a non-existent spec or
  plan path, Phase 1 will note "FILE NOT FOUND" per existing convention; the
  reviewer returns `❌ Issues Found` with a file-not-found issue. This is
  identical behaviour to the current inline path.
- **Interaction with `allowed-tools` from frontmatter-hardening spec:** Both
  features write `allowed-tools:` to the same three SKILL.md files. The
  frontmatter-hardening spec (2026-03-24) already sets `allowed-tools: Read,
  Grep, Glob` on all three reviewers. This spec adds `context: fork` and
  `agent:` alongside the existing `allowed-tools:` — not in conflict. If
  frontmatter-hardening ships first, this spec's implementation must not
  overwrite those fields; it appends `context:` and `agent:` only.
- **`context: fork` on `spec-reviewer` / `plan-reviewer` with `agent: Explore`
  but no `Bash`:** These reviewers never invoke Bash in any phase — safe.
- **Max iteration count:** The 3-iteration cap is enforced by the calling skill,
  not the reviewer. Fork execution does not affect this logic.

**Out of Scope:**

- Changing any Phase 1, 2, or 3 review logic or checklist content.
- Adding `context: fork` to non-reviewer skills (spec-design, write-plan,
  tdd-loop, debug, verify, retro-format, test-pyramid).
- Changing how calling commands/skills invoke reviewers — invocation syntax
  `Skill(zie-framework:<name>)` is unchanged.
- Modifying the review iteration loop logic inside `spec-design`, `write-plan`,
  or `zie-implement`.
- Running `make test-unit` inside the forked subagent (impl-reviewer Phase 2
  item 3 notes "Caller confirms" — the reviewer does not execute tests).
- Integration-level tests that verify Claude Code actually forks a subagent at
  runtime (not testable in the pytest suite; only frontmatter field presence
  is asserted).
- Updating `hooks/hooks.json` or `plugin.json` — skill forking is declared
  entirely within SKILL.md frontmatter.
