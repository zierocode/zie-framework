---
approved: true
approved_at: 2026-04-15
backlog: backlog/deeper-thinking-backlog-spec-plan.md
---

# Deeper Thinking in Backlog Spec Plan — Design Spec

**Problem:** Current backlog/spec/plan phases transcribe user input rather than think ahead — they capture what's said but don't surface blind spots, edge cases, or downstream implications. The user has to notice gaps themselves and come back to fix them, wasting iteration cycles.
**Approach:** Add explicit "think deeper" prompts to each SDLC phase (backlog, spec-design, write-plan) that force consideration of edge cases, alternatives, risks, and non-obvious impacts — without adding process steps. Each phase gets a structured addition: backlog gets a "Considerations" section, spec-design gets a "Blind Spots" check, and write-plan gets a "Risk Review" step. All additions are inline prompts, not new phases.
**Components:**
- `commands/backlog.md` — add "Considerations" section after Rough Scope with 2-3 auto-suggested edge cases/risks
- `skills/spec-design/SKILL.md` — add "Blind Spots" check between Step 3 (draft) and Step 5 (reviewer): explicitly list what the spec doesn't cover, failure modes, and alternatives considered
- `skills/write-plan/SKILL.md` — add "Risk Review" step before file map: check for hidden dependencies, ordering risks, and rollback strategies
- `skills/spec-reviewer/SKILL.md` — extend YAGNI check to also flag "unquestioned assumptions" (things the spec takes for granted without evidence)
- `skills/plan-reviewer/SKILL.md` — extend review to flag "missing rollback" and "hidden dependency" patterns
**Data Flow:**

*Current flow:*
1. User describes idea → backlog captures Problem/Motivation/Scope
2. Spec-design writes spec from backlog content (transcription-heavy)
3. Write-plan decomposes spec into tasks (decomposition-heavy)
4. Reviewers check format and completeness (checklist-heavy)

*Proposed flow (additions in bold):*
1. User describes idea → backlog captures Problem/Motivation/Scope **+ auto-suggests 2-3 Considerations (edge cases, risks, dependencies)**
2. Spec-design writes spec from backlog content **+ explicitly lists Blind Spots (what's NOT covered, failure modes, alternatives)**
3. Write-plan decomposes spec into tasks **+ Risk Review (hidden deps, ordering risks, rollback per task)**
4. Reviewers check format, completeness, **and flag unquestioned assumptions / missing rollbacks**

**Edge Cases:**
- **Considerations generate irrelevant suggestions:** The prompt asks for 2-3 items — if none are relevant, the section can be empty. Better to have an empty section than force irrelevant content.
- **Blind Spots overlap with Edge Cases in spec:** Blind Spots focus on what the spec DOESN'T cover (gaps), while Edge Cases cover known edge cases (what IS covered but unusual). They serve different purposes — both are valuable.
- **Risk Review makes plans longer:** Risk Review adds one sentence per task about rollback strategy. This is minimal overhead (1 line per task) and prevents "how do we revert if this fails?" questions during implementation.
- **Autonomous mode:** Sprint already uses autonomous mode where all phases run without user input. The "think deeper" prompts run automatically — they don't require user interaction. The Considerations section in backlog gets auto-filled; Blind Spots and Risk Review run inline.
- **Reviewers flag assumptions that are actually fine:** The "unquestioned assumptions" check is advisory (non-blocking) — it surfaces items for the author to consider, not mandatory fixes. Same pattern as YAGNI check: flag but don't block unless clearly wrong.
- **Existing specs/plans lack these sections:** Only new specs/plans get the new sections. No retroactive changes to existing artifacts.

**Out of Scope:**
- Changing the reviewer invocation model (that's the "optimize-review-loop-token-waste" backlog item)
- Adding new SDLC phases or quality gates
- Making the "think deeper" prompts interactive (they run inline, not as user Q&A)
- Changing the autonomous mode flow (it already skips Q&A — the prompts run automatically)
- Enforcing Considerations/Blind Spots/Risk Review as blocking (they're advisory additions)