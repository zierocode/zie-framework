# /zie-idea — Brainstorm → Spec → Implementation Plan

Turn an idea into a written spec and actionable implementation plan. Runs brainstorming and writing-plans in sequence. Output lives in `zie-framework/specs/` and `zie-framework/plans/`.

## Pre-flight

1. Check `zie-framework/` exists → if not, tell user to run `/zie-init` first.
2. Read `zie-framework/.config` for project context.
3. If `zie_memory_enabled=true`:
   - Recall top 5 memories for this project → use as context for brainstorming.

## Steps

### Phase 1 — Brainstorm (spec)

4. If `superpowers_enabled=true`:
   - Invoke `Skill(superpowers:brainstorming)` with ARGUMENTS: `"Project context from zie-framework/.config and recalled memories. User's idea: <idea from command argument or ask user>"`
   - Follow the brainstorming skill exactly — it will ask clarifying questions, propose approaches, present design sections, write the spec, and run the spec reviewer subagent.
   - Spec is saved to `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` by the skill.
   - Copy/move spec to `zie-framework/specs/YYYY-MM-DD-<topic>-design.md`

5. If `superpowers_enabled=false`:
   - Run inline brainstorming: ask 3 targeted questions one at a time, then write spec to `zie-framework/specs/YYYY-MM-DD-<topic>-design.md`
   - Spec format: Problem, Approach, Components, Data Flow, Edge Cases, Out of Scope

6. Ask user: "Spec looks good? Proceed to implementation plan?"
   - If no → revise and re-ask.

### Phase 2 — Implementation Plan

7. If `superpowers_enabled=true`:
   - Invoke `Skill(superpowers:writing-plans)` with the approved spec.
   - Plan is saved by the skill.
   - Copy/move plan to `zie-framework/plans/YYYY-MM-DD-<topic>.md`

8. If `superpowers_enabled=false`:
   - Write plan inline to `zie-framework/plans/YYYY-MM-DD-<topic>.md`
   - Format: numbered task list with S/M/L estimate and acceptance criteria per task.

### Phase 3 — Update state

9. Update `zie-framework/ROADMAP.md`:
   - Add feature to "Now" section: `- [ ] <feature name> — [spec](specs/...) [plan](plans/...)`

10. Create `TaskCreate` for each task in the plan (so progress is tracked in this session).

11. If `zie_memory_enabled=true`:
    - Store: `remember "Spec created for <feature>. Plan: <N> tasks. Est complexity: <S/M/L>." priority=project tags=[zie-framework, spec, <feature-slug>] project=<project-name>`

12. Print:
    ```
    Spec  → zie-framework/specs/YYYY-MM-DD-<topic>-design.md
    Plan  → zie-framework/plans/YYYY-MM-DD-<topic>.md
    ROADMAP updated → Now section

    <N> tasks created. Run /zie-build to start implementing.
    ```

## Notes
- Can be run with argument: `/zie-idea "export memories as CSV"` to skip the initial prompt
- Can be run without argument: will ask for the idea first
- Always spec-first — never skips to plan without an approved spec
