# Phase/Step Explanatory Prose Cleanup — Design Spec

**Problem:** Phase headers in zie-audit, sprint, retro, release, tdd-loop, and debug contain 2–3 redundant explanatory sentences that restate what the first imperative step already says (~700 words total). In tdd-loop and debug, "Never do X" rules appear both in a dedicated rules block and inline within each phase step, doubling the rule surface.

**Approach:** Surgical delete-only pass across 6 files: remove the explanatory paragraph immediately beneath each phase header where the first imperative step already covers the same ground. Consolidate "Never do X" duplicates in tdd-loop and debug into the existing rules block only; strip the inline repetitions. No logic changes, no restructuring — pure prose deletion. Run `make test-unit` gate after each file to catch broken test assertions.

**Components:**
- `skills/zie-audit/SKILL.md` — Phase 2 has "Spawn 5 parallel agents..." prose after header
- `commands/sprint.md` — Phase headers contain explanatory paragraphs before imperative steps
- `commands/retro.md` — section headers with narrative sentences before the step lists
- `commands/release.md` — phase headers with explanatory prose before gate steps
- `skills/tdd-loop/SKILL.md` — "Never" rules duplicated in rules block and inline steps
- `skills/debug/SKILL.md` — "Never" rules duplicated in rules block and inline steps

**Data Flow:**
1. Read each file
2. Identify explanatory prose: sentences immediately after a phase/section header that restate what the first `1.` step says
3. Delete those sentences only — leave headers, steps, and rules intact
4. For tdd-loop and debug: identify inline "Never do X" sentences within step bodies that already appear in the `## กฎที่ต้องทำตาม` block; delete inline occurrences, keep the rules block
5. Run `make test-unit` after each file edit
6. Verify final word-count reduction ~600–700 words

**Edge Cases:**
- Test assertions may match on prose strings — check test files before deleting any line
- Some explanatory sentences may be the ONLY place a constraint is stated — keep those
- "Never" rules that appear ONLY inline (not in rules block) must NOT be deleted — consolidate to rules block first if missing
- Phase 2 of zie-audit has `active_agents` logic embedded in prose — retain functional content, delete only pure restatement

**Out of Scope:**
- Restructuring phase order or renaming sections
- Changes to commands not listed (backlog, spec, plan, implement, chore, hotfix, spike, status, fix, init)
- Editing any Python hook files
- Adding new content or improving clarity beyond deletion
- Modifying test files
