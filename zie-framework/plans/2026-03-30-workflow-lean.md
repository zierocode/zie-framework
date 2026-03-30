---
approved: false
approved_at:
backlog: backlog/workflow-lean.md
spec: specs/2026-03-30-workflow-lean-design.md
---

# Plan: Workflow Lean

**Goal:** Reduce friction in three high-frequency workflows by adding targeted opt-in flags and smarter loops, without changing default behavior or quality outputs.

**Architecture:** Three independent control-plane enhancements in `commands/` files (zie-audit, zie-spec, zie-init), one skill documentation pass (spec-design Arguments table), and one reviewer invocation in zie-spec for auto-planning. All changes backward-compatible.

**Tech Stack:** Python (arg parsing), Bash (ROADMAP update), Markdown (skill documentation).

---

## File Map

| File | Purpose | Status |
| --- | --- | --- |
| `commands/zie-audit.md` | Add `--focus` parsing; conditionally spawn agents Phase 2 | Modify |
| `commands/zie-spec.md` | Add `--draft-plan` parsing; auto-invoke write-plan + plan-reviewer + ROADMAP move | Modify |
| `commands/zie-init.md` | Replace full-bundle approval loop with section-targeted revision prompt | Modify |
| `skills/spec-design/SKILL.md` | Document `--draft-plan` as pass-through flag in Arguments table (position 2) | Modify |

---

## Task 1 — `/zie-audit --focus` Argument Parsing and Conditional Agent Spawn

**File:** `commands/zie-audit.md`

**Test:** `tests/test_zie_audit_focus.py` (new)

**RED:** Write test validating:
- Parse `--focus security` → `active_agents = [Agent1]`
- Parse `--focus code` → `active_agents = [Agent2]`
- Parse `--focus structure` → `active_agents = [Agent3]`
- Parse `--focus external` → `active_agents = [Agent4]`
- Parse `--focus security,deps` → `active_agents = [Agent1]` (union)
- Parse `--focus code,structure` → `active_agents = [Agent2, Agent3]` (union)
- Parse `--focus typo` (unrecognized) → `active_agents = [all 4]` + warning printed
- No flag provided → `active_agents = [all 4]` (default)
- Agent spawn is conditional: if Agent1 not in `active_agents`, Phase 2 section updates header but skips its invocation

**GREEN:**
1. In `commands/zie-audit.md` Phase 2 section, after context bundle build, add:
   ```python
   # Parse --focus flag if present
   focus_param = ""
   for arg in ARGUMENTS.split():
       if arg.startswith("--focus"):
           focus_param = arg.split("=")[-1] if "=" in arg else next_arg
           break

   # Map focus tokens to agent sets
   focus_map = {
       "security": [1],
       "deps": [1],
       "code": [2],
       "perf": [2],
       "structure": [3],
       "obs": [3],
       "external": [4],
   }

   active_agents = focus_map.get(focus_param.lower(), None)
   if active_agents is None:
       if focus_param:
           print(f"⚠ Unknown focus value '{focus_param}' — running full audit")
       active_agents = [1, 2, 3, 4]
   ```

2. Update Phase 2 header:
   ```markdown
   ## Phase 2 — Parallel Dimension Scan (active: Agent{}, Agent{}, ...)
   ```
   where `{}` are the active agent numbers joined with `, `.

3. For each Agent 1–4 invocation, wrap with:
   ```python
   if <agent_number> in active_agents:
       # Run Agent(...)
   ```

4. Phase 3 (Synthesis) and Phase 4 (Backlog Integration) unchanged — they consume agent outputs regardless of which were spawned.

**AC:**
- [ ] `--focus security` spawns only Agent 1
- [ ] `--focus code,structure` spawns Agent 2 + Agent 3
- [ ] Unrecognized `--focus typo` spawns all 4 + warning
- [ ] No flag spawns all 4 (backward compatible)
- [ ] Phase 2 header lists active agents dynamically
- [ ] Tests pass: `make test-unit`

---

## Task 2 — `/zie-spec --draft-plan` Argument Parsing and Plan-Draft Invocation

**File:** `commands/zie-spec.md`

**Test:** `tests/test_zie_spec_draft_plan_parsing.py` (new)

**RED:** Write test validating:
- Parse `/zie-spec slug --draft-plan` → `draft_plan=true`, slug extracted correctly
- Parse `/zie-spec "idea" --draft-plan` → `draft_plan=true`, idea extracted correctly
- Parse `/zie-spec slug` (no flag) → `draft_plan=false`
- Both slug mode and quick-spec mode detect `--draft-plan`
- `--draft-plan` flag is removed from slug/idea extraction

**GREEN:**
1. In `commands/zie-spec.md`, before step 1 (Detect input mode), add:
   ```python
   # Parse --draft-plan flag
   draft_plan = "--draft-plan" in ARGUMENTS
   # Extract slug cleanly (remove flag from argument list)
   clean_args = " ".join(arg for arg in ARGUMENTS.split() if arg != "--draft-plan")
   ```

2. Update step 2 (slug mode) to use `clean_args` instead of raw ARGUMENTS for `Skill(spec-design)` invocation.

3. Update step 3 (quick mode) to use `clean_args` for deriving slug and idea string.

4. After step 2/3 spec-design completes and spec is committed, add conditional branch:
   ```python
   if draft_plan:
       print("\n--draft-plan active — proceeding to plan draft...\n")
       # Invoke write-plan skill (Task 2b will handle approval + ROADMAP)
       Skill(zie-framework:write-plan)(slug)
   else:
       # Existing handoff (no --draft-plan flag)
       print(f"""
Spec approved ✓ → zie-framework/specs/YYYY-MM-DD-{slug}-design.md

Next: /zie-plan {slug} to create the implementation plan.
       """)
   ```

**AC:**
- [ ] `--draft-plan` flag detected in ARGUMENTS
- [ ] Flag removed from slug/idea extraction
- [ ] Plan-draft invoked when flag present
- [ ] No flag = existing `/zie-spec` behavior (handoff message printed, no plan invocation)
- [ ] Works in both slug mode and quick-spec mode
- [ ] Tests pass: `make test-unit`

---

## Task 2b — `/zie-spec --draft-plan` Plan Approval and ROADMAP Move

**File:** `commands/zie-spec.md` (same file as Task 2)

**Test:** `tests/test_zie_spec_draft_plan_approval.py` (new)

**Depends on:** Task 2

**RED:** Write test validating:
- When `write-plan` completes with "APPROVED", frontmatter is written: `approved: true, approved_at: YYYY-MM-DD`
- When `write-plan` completes with "APPROVED", ROADMAP is updated: slug moved from Next → Ready lane
- When `write-plan` completes with "APPROVED", plan file is committed with git
- When `write-plan` completes with "ISSUES", plan is left in draft state (no frontmatter)
- When `write-plan` completes with "ISSUES", spec remains approved, user directed to `/zie-plan <slug>`
- Combined handoff message on success shows spec + plan + ROADMAP status

**GREEN:**
1. After `write-plan` skill returns (from Task 2 conditional branch), capture its output and check for plan-reviewer result:
   ```python
   if draft_plan:
       # write-plan has already invoked plan-reviewer internally
       # Check its result by parsing output for APPROVED/ISSUES
       plan_result_text = <write-plan skill output>

       if "APPROVED" in plan_result_text:
           # Write plan frontmatter
           plan_file = f"zie-framework/plans/{get_date_today()}-{slug}.md"
           with open(plan_file, 'r') as f:
               plan_content = f.read()

           # Replace frontmatter: approved: false → true, add approved_at
           new_frontmatter = f"""---
approved: true
approved_at: {get_date_today()}
backlog: backlog/{slug}.md
spec: specs/{get_date_today()}-{slug}-design.md
---"""
           plan_content = re.sub(
               r"^---.*?^---",
               new_frontmatter,
               plan_content,
               flags=re.MULTILINE | re.DOTALL
           )
           with open(plan_file, 'w') as f:
               f.write(plan_content)

           # Move slug from ROADMAP Next → Ready
           with open("zie-framework/ROADMAP.md", 'r') as f:
               roadmap = f.read()

           # Find "- [ ] <slug>" in Next section, move to Ready
           roadmap = re.sub(
               f"(## Next.*?)(\\s*- \\[ \\] {re.escape(slug)}.*)",
               r"\1",  # Remove from Next
               roadmap,
               flags=re.DOTALL
           )
           roadmap = re.sub(
               "(## Ready.*?<!-- MEDIUM -->)",
               f"\\1\n- [ ] {slug} — [spec](specs/{get_date_today()}-{slug}-design.md)",
               roadmap,
               flags=re.DOTALL
           )
           with open("zie-framework/ROADMAP.md", 'w') as f:
               f.write(roadmap)

           # Commit
           run(["git", "add",
               f"zie-framework/plans/{get_date_today()}-{slug}.md",
               "zie-framework/ROADMAP.md"])
           run(["git", "commit", "-m", f"plan: {slug}"])

           # Combined handoff
           print(f"""
Spec approved ✓ → zie-framework/specs/{get_date_today()}-{slug}-design.md
Plan approved ✓ → zie-framework/plans/{get_date_today()}-{slug}.md
                   ROADMAP: {slug} moved Next → Ready

Next: /zie-implement {slug}
           """)
       else:
           # plan-reviewer found ISSUES
           print("Plan review found issues. Spec remains approved.")
           print(f"Address plan issues and re-run: /zie-plan {slug}")
   ```

2. Helper functions:
   - `get_date_today()` → returns YYYY-MM-DD string
   - Parse write-plan output to detect APPROVED vs ISSUES status

**AC:**
- [ ] On plan APPROVED: frontmatter written with `approved: true` + `approved_at`
- [ ] On plan APPROVED: ROADMAP updated (Next → Ready)
- [ ] On plan APPROVED: commit executed
- [ ] On plan APPROVED: combined handoff shows full status chain
- [ ] On plan ISSUES: plan left in draft, spec remains approved, user redirected
- [ ] ROADMAP Next lane correctly updated (item moved, not duplicated)
- [ ] All file operations atomic (commit = single operation)
- [ ] Tests pass: `make test-unit`

---

## Task 3 — `spec-design/SKILL.md` Arguments Table Documentation

**File:** `skills/spec-design/SKILL.md`

**Test:** `tests/test_spec_design_skill_args.py` (grep-based documentation audit)

**RED:** Write test validating:
- Arguments table has 3 rows (header + positions 0, 1, 2)
- Position 2 exists and is documented as `--draft-plan` pass-through flag
- `$ARGUMENTS[2]` references are absent in skill logic (flag is control-plane responsibility)

**GREEN:**
1. In `skills/spec-design/SKILL.md`, update the Arguments section to:
   ```markdown
   | Position | Variable | Description | Default |
   | --- | --- | --- | --- |
   | 0 | `$ARGUMENTS[0]` | Backlog slug (e.g. `my-feature`) | absent → prompt user for slug |
   | 1 | `$ARGUMENTS[1]` | Mode: `full` (full dialogue) or `quick` (skip clarification, draft directly) | absent/empty → `full` |
   | 2 | `$ARGUMENTS[2]` | Pass-through flags (e.g. `--draft-plan`); handled by `/zie-spec` control plane, not evaluated by skill | absent/empty → no flags |
   ```

2. Add a note after the Arguments table:
   ```markdown
   **Flag Handling:** `--draft-plan` is parsed and handled by `/zie-spec` command (control plane, per ADR-003).
   The skill receives the flag string but does not act on it. Spec-design always writes the spec and runs
   the spec-reviewer loop; zie-spec decides whether to auto-proceed to planning.
   ```

3. Ensure skill logic contains no `if "--draft-plan"` checks — this is control-plane responsibility only.

**AC:**
- [ ] Arguments table documents position 2 as pass-through flags
- [ ] ADR-003 referenced in documentation (commands = control plane)
- [ ] Skill logic contains zero flag-handling code for `--draft-plan`
- [ ] Tests pass: `make test-unit`

---

## Task 4 — `/zie-init` Section-Targeted Knowledge Loop

**File:** `commands/zie-init.md`

**Test:** `tests/test_zie_init_section_loop.py` (new)

**RED:** Write test validating:
- After first draft of all four docs is presented, ask: `"Which section to revise? (project / architecture / components / context / all good)"`
- User replies `"architecture"` → only `architecture.md` agent regenerates; other three retain prior state
- User replies `"project"` → only `project.md` agent regenerates
- User replies `"components"` → only `components.md` agent regenerates
- User replies `"context"` → only `context.md` agent regenerates
- User replies `"all good"` or `"y"` → exit loop, proceed to step 2e (write all four)
- User can loop multiple times (e.g. `"architecture"` → revise → `"components"` → revise → `"all good"`)
- Unrecognized input (e.g. `"xyz"`) → re-prompt: `"Which section to revise?..."`
- Loop has no iteration limit

**GREEN:**
1. In `commands/zie-init.md`, replace step 2c/2d (old full-bundle regenerate loop) with:

   **Step 2c (updated):** Present all four drafts in code blocks as before (unchanged).

   **Step 2d (new section-targeted loop):**
   ```python
   section_to_revise = ""
   while True:
       section_to_revise = input(
           "Which section to revise? (project / architecture / components / context / all good): "
       ).strip().lower()

       if section_to_revise in ["all good", "y", "yes"]:
           break  # Exit loop, proceed to 2e

       if section_to_revise not in ["project", "architecture", "components", "context"]:
           print(f"Unrecognized section '{section_to_revise}' — try again")
           continue

       # Re-run only the named section's agent
       if section_to_revise == "project":
           project_draft = Agent(subagent_type=Explore)(
               existing_report,
               focus="PROJECT.md — project title, domain, key links"
           )
           # Update project_draft variable; re-present only this section
           print(f"Updated PROJECT.md draft:\n```markdown\n{project_draft}\n```")

       elif section_to_revise == "architecture":
           arch_draft = Agent(subagent_type=Explore)(
               existing_report,
               focus="architecture.md — architecture pattern, layers, key components"
           )
           print(f"Updated architecture.md draft:\n```markdown\n{arch_draft}\n```")

       elif section_to_revise == "components":
           comp_draft = Agent(subagent_type=Explore)(
               existing_report,
               focus="components.md — every significant component/module with purpose"
           )
           print(f"Updated components.md draft:\n```markdown\n{comp_draft}\n```")

       elif section_to_revise == "context":
           ctx_draft = Agent(subagent_type=Explore)(
               existing_report,
               focus="context.md — key decisions, constraints, data flow notes"
           )
           print(f"Updated context.md draft:\n```markdown\n{ctx_draft}\n```")
   ```

2. Step 2e (write all four files) remains unchanged — it writes `project_draft`, `arch_draft`, `comp_draft`, `ctx_draft` variables (which may have been updated by section revisions).

3. Step 2f onwards (knowledge_hash, .config update, migratable docs) unchanged.

**AC:**
- [ ] After first draft presentation, user prompted for section choice
- [ ] Single-section regeneration: only named section agent is re-run
- [ ] Other three sections retain their prior draft state
- [ ] User can loop multiple times revising different sections
- [ ] `"all good"` exits loop, proceeds to write
- [ ] Unrecognized input re-prompts without crashing
- [ ] No iteration limit (infinite loop safe via user input)
- [ ] Tests pass: `make test-unit`

---

## Task Dependencies

- **Task 1** (zie-audit) — independent; no dependencies
- **Task 2** (zie-spec flag parsing) — depends on Task 3 (spec-design documentation) for clarity, but logic doesn't block on it
- **Task 2b** (zie-spec plan approval + ROADMAP) — depends on Task 2 (flag parsing must be in place first)
- **Task 3** (spec-design) — independent; purely documentation
- **Task 4** (zie-init) — independent; no dependencies

**Suggested parallel execution:** Run Tasks 1, 3, 4 in parallel. Run Task 2 → Task 2b sequentially (Task 2b depends_on Task 2). Start Task 2 after Task 3 documentation is merged (minimal dependency).

---

## Test Strategy

**Unit tests (make test-unit):**
- Task 1: arg parsing logic, agent selection, header formatting
- Task 2: --draft-plan flag detection, slug extraction, no-flag behavior
- Task 2b: frontmatter writing, ROADMAP update logic, combined handoff formatting, issue-state handling
- Task 3: Arguments table structure, ADR reference in docs
- Task 4: section prompt logic, agent re-run conditionals, draft state retention, loop exit conditions

**Integration tests (make test-int):**
- Task 1: Full `/zie-audit --focus security` → Agent 1 only, compare output
- Task 2+2b: Full `/zie-spec slug --draft-plan` → spec + plan both approved + ROADMAP + commit
- Task 4: Full `/zie-init` flow with section revisions → final docs match user feedback

All tests use temporary test fixtures and git repos to avoid side effects.

---

## Acceptance Criteria

- [ ] All 5 tasks (Task 1, 2, 2b, 3, 4) complete and pass their respective test suites
- [ ] Backward compatibility: no flag defaults to existing behavior (all 4 agents in audit, separate spec/plan, full-bundle in init)
- [ ] No breaking changes to existing commands or skills
- [ ] ADR-003 (commands = control plane) honored in Task 2, 2b, and Task 3
- [ ] ROADMAP updated correctly in Task 2b (Next → Ready)
- [ ] Spec-first rule maintained: no plan without approved spec
- [ ] Combined handoff messages are clear and actionable
- [ ] All files have exact paths (no vague "add to relevant file")
- [ ] TDD flow: RED → GREEN → REFACTOR, with `make test-unit` verification per task
- [ ] Task dependencies clearly annotated; file conflicts checked
