---
approved: true
approved_at: 2026-03-30
backlog: backlog/workflow-lean.md
---

# Workflow Lean — Design Spec

**Problem:** Three high-frequency workflows impose unnecessary round-trips and cost:
`/zie-audit` always spawns all 4 agents even for targeted scans, `/zie-spec` requires
a separate `/zie-plan` invocation for users who always proceed sequentially, and
`/zie-init`'s knowledge-doc review loop regenerates the full 4-doc bundle even when
the user wants to revise one section.

**Approach:** Add opt-in flags and a smarter loop to reduce steps without changing the
default behavior or quality outputs. `/zie-audit` gets `--focus` to filter which agents
are spawned. `/zie-spec` (and `spec-design`) get `--draft-plan` to auto-continue through
plan drafting and review after spec approval. `/zie-init` replaces its full-bundle
re-present loop with a section-targeted revision prompt. All three changes are
backward-compatible: no flag = existing behavior unchanged.

**Components:**

- `commands/zie-audit.md` — add `--focus` argument parsing and conditional agent spawn
  in Phase 2; update Phase 2 section header to list active agents
- `commands/zie-spec.md` — add `--draft-plan` flag parsing; after spec-design skill
  returns and spec is committed, if `--draft-plan` is set: invoke
  `Skill(zie-framework:write-plan)`, run `plan-reviewer` automatically, write plan
  frontmatter on APPROVED, update ROADMAP Next→Ready, commit plan, print combined
  handoff; update both slug mode (step 2) and quick-spec mode (step 3)
- `skills/spec-design/SKILL.md` — add `--draft-plan` to the Arguments table as a
  documented pass-through flag (position 2); skill control flow and step 9 handoff are
  unchanged — spec-design does not act on the flag (commands are the control plane per
  ADR-003)
- `commands/zie-init.md` — replace step 2c/2d (present all four + loop) with a
  section-targeted revision prompt after first draft is presented

**Data Flow:**

**/zie-audit --focus flow:**

1. User runs `/zie-audit --focus security` (or `--focus code`, `--focus structure`,
   `--focus external`, or comma-separated e.g. `--focus security,deps`)
2. Phase 1 runs unchanged (context bundle build)
3. Phase 2: parse ARGUMENTS for `--focus` flag → derive active agent set:
   - `security` or `deps` → Agent 1 (Security + Dependency Health)
   - `code` or `perf` → Agent 2 (Code Health + Performance)
   - `structure` or `obs` → Agent 3 (Structural + Observability)
   - `external` → Agent 4 (External Research)
   - No flag or unrecognized value → all 4 agents (existing default)
4. Update Phase 2 section header to: `## Phase 2 — Parallel Dimension Scan (active: Agent1, Agent3)`
5. Spawn only the selected agents with `run_in_background: true`
6. Phase 3 (Synthesis) and Phase 4 (Backlog Integration) run unchanged on available
   agent outputs

**/zie-spec --draft-plan flow:**

1. User runs `/zie-spec <slug> --draft-plan`
2. `zie-spec.md` parses ARGUMENTS, sets `draft_plan=true`; passes slug (without flag)
   to `Skill(zie-framework:spec-design)` as normal — spec-design is not aware of the flag
3. `spec-design` runs its complete normal loop (Steps 1–9); writes spec file; prints
   its standard handoff; skill returns control to `zie-spec.md`
4. `zie-spec.md` commits spec (existing commit step), then checks `draft_plan` flag:
   a. If `draft_plan=false` (or absent): print existing handoff ("Next: /zie-plan
      <slug>") and stop — existing behavior unchanged
   b. If `draft_plan=true`:
      i.  Print: `"--draft-plan active — proceeding to plan draft..."`
      ii. Invoke `Skill(zie-framework:write-plan)` inline (not in background)
      iii. `write-plan` drafts the plan, calls `plan-reviewer` automatically
      iv. If plan-reviewer returns ISSUES: fix inline, re-review (max 2 iterations per
          write-plan's existing loop)
      v.  If plan-reviewer returns APPROVED: `write-plan` adds the plan to ROADMAP
          Ready lane as normal; `zie-spec.md` then writes `approved: true` and
          `approved_at: YYYY-MM-DD` into the plan frontmatter (the step normally
          requiring explicit user approval is skipped — plan-reviewer pass is
          sufficient when `--draft-plan` is active); commit plan file
      vi. Print combined handoff:
          ```text
          Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-<slug>-design.md
          Plan approved ✓ → zie-framework/plans/YYYY-MM-DD-<slug>.md
                             ROADMAP: <slug> moved Next → Ready

          Next: /zie-implement <slug>
          ```

**/zie-init section-targeted revision flow:**

1. `/zie-init` step 2b generates all four knowledge docs (unchanged)
2. Step 2c presents all four drafts as markdown code blocks (unchanged)
3. Replace step 2d (loop: "corrections → apply → re-present → repeat"):
   a. After first presentation, ask:
      `"Which section to revise? (project / architecture / components / context / all good)"`
   b. If user names a section (e.g. `"architecture"`): re-run only that section's
      Agent(subagent_type=Explore) generation using the existing report, apply user
      feedback, re-present only that section's updated draft
   c. Repeat the section prompt until user replies `"all good"` or `"y"`
   d. Once `"all good"`: proceed to step 2e (write all four files)

**Edge Cases:**

- `--focus` with an unrecognized token (e.g. `--focus typo`): treat as no flag →
  spawn all 4 agents; print a warning: `"Unknown focus value 'typo' — running full audit"`
- `--focus` with multiple values comma-separated (e.g. `--focus security,code`):
  union the agent sets — spawn Agent 1 + Agent 2
- `--draft-plan` on quick-spec mode (`/zie-spec "inline idea" --draft-plan`): supported
  — spec slug derived same as quick-spec, then plan flow proceeds after approval
- `--draft-plan` when spec-reviewer hits max 3 iterations without APPROVED: abort plan
  draft, surface spec issues to user; no partial plan written
- `--draft-plan` when write-plan hits max plan-reviewer iterations without APPROVED:
  leave plan in draft state (no frontmatter, not moved to Ready), print issues to user;
  spec remains approved
- `/zie-init` single-section re-run: only regenerate the named section; the other three
  sections retain their prior draft state and are not touched
- `/zie-init` "all good" without any revision: valid — user accepts first draft;
  proceed directly to step 2e

**Out of Scope:**

- Merging `/zie-spec` and `/zie-plan` into a single permanent command
- Changing what any reviewer checks or how scoring works
- Adding `--focus` to any command other than `/zie-audit`
- Auto-continuing past plan into `/zie-implement` (user still triggers that explicitly)
- Parallelizing `/zie-init` section re-generation
- Changing the write-plan or spec-design internal review logic
