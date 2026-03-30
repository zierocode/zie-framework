---
approved: false
backlog: backlog/agentic-pipeline-v2.md
spec: specs/2026-03-30-agentic-pipeline-v2-design.md
---

# Plan: Agentic Pipeline v2

**Goal:** Remove 7 redundant human approval gates from zie-framework SDLC by auto-accepting validated reviewer verdicts and replacing plugin-specific subagent types with general-purpose agents.

**Architecture:**
- Preserve human control at decision gates (title input, CHANGELOG narrative, explicit user overrides)
- Auto-accept when reviewers return APPROVED
- Replace plugin-specific subagent types (zie-framework:retro-format, zie-framework:docs-sync-check) with Agent(subagent_type="general-purpose")
- Auto-commit retro outputs; auto-accept version suggestions
- Add pre-flight warning in zie-implement for agent-mode validation

**Tech Stack:** Markdown commands + Python hooks, no new dependencies

---

## Task 1 — spec-design: Remove step 6 review confirmation + step 8 manual review gate

**File:** `skills/spec-design/SKILL.md`
**Test:** `tests/unit/test_spec_design_auto_approve.py`

**RED:** Write test that verifies:
- When spec-reviewer returns ✅ APPROVED in step 5, step 6 human review prompt ("Does this look right?") is skipped
- Execution proceeds directly to step 7 (write frontmatter)
- Step 8 ("Ask user to review") is removed entirely from the command flow
- Backlog input still required; spec-reviewer still runs

Test should mock spec-reviewer returning APPROVED and verify no user input prompt is presented.

**GREEN:** Modify `skills/spec-design/SKILL.md`:
1. Remove step 6 entirely: "**Record approval** — once spec-reviewer returns ✅ APPROVED, prepend frontmatter to the spec file"
   - Move directly from step 5 ("Spec reviewer loop returns ✅ APPROVED") to step 6 (was step 7): write frontmatter atomically
   - Remove the human prompt "Does this look right?" — reviewer verdict IS the gate
2. Remove step 8 ("Ask user to review") entirely
3. Renumber remaining steps (7→6, 8→7 becomes the final handoff)
4. Update handoff text to reflect auto-approval: "Spec approved ✓ (reviewed by spec-reviewer)"

**AC:**
- [ ] Spec file receives frontmatter automatically when spec-reviewer returns APPROVED, no user confirmation required
- [ ] Human review confirmation prompt ("Does this look right?") no longer appears
- [ ] Step 8 ("Ask user to review") is removed from workflow description
- [ ] Test verifies auto-proceed path with mocked spec-reviewer APPROVED verdict
- [ ] Spec-reviewer loop (step 5) remains unchanged — issues found still ask user to fix and re-submit

---

## Task 2 — zie-plan: Auto-approve when plan-reviewer returns APPROVED

**File:** `commands/zie-plan.md`
**Test:** `tests/unit/test_plan_auto_approve_gate.py`

**RED:** Write test that verifies:
- When plan-reviewer returns ✅ APPROVED, the "Approve this plan? (yes / re-draft / drop)" prompt is skipped
- Plan file receives frontmatter (approved: true, approved_at: TODAY) automatically
- Git commit happens without user confirmation
- Plan moves to Ready lane in ROADMAP atomically
- User can still explicitly call `/zie-plan re-draft` or `/zie-plan drop` to interrupt before execution
- If plan-reviewer returns ❌ Issues Found, old flow preserved (ask user to fix or drop)

**GREEN:** Modify `commands/zie-plan.md` section "ขออนุมัติ plan":
1. After plan-reviewer returns ✅ APPROVED:
   - Skip the prompt "Approve this plan? (yes / re-draft / drop)"
   - Auto-add frontmatter:
     ```yaml
     ---
     approved: true
     approved_at: YYYY-MM-DD
     backlog: backlog/<slug>.md
     spec: specs/<spec-filename>.md
     ---
     ```
   - Atomically move item in ROADMAP from Next → Ready (same logic as "yes" path)
   - Git commit: `git commit -m "plan: <slug>"`
2. Display confirmation message: `"✓ Plan approved & moved to Ready. Run /zie-implement to start building."`
3. Keep `/zie-plan re-draft` and `/zie-plan drop` as explicit user-override commands (documented in output)
4. If plan-reviewer issues found, ask user: "Fix and re-run, re-draft, or drop?" (preserve old flow)

**AC:**
- [ ] When plan-reviewer returns APPROVED, frontmatter is added automatically without user prompt
- [ ] ROADMAP moves plan from Next to Ready without "Approve this plan?" confirmation
- [ ] Git commit happens atomically; no manual commit required
- [ ] Test mocks plan-reviewer APPROVED and verifies auto-path
- [ ] User can still override with `/zie-plan re-draft` or `/zie-plan drop` (documented)
- [ ] If plan-reviewer returns Issues, user prompted to fix or drop (old flow preserved)

---

## Task 3 — zie-release: Auto-accept version suggestion, display only

**File:** `commands/zie-release.md`
**Test:** `tests/unit/test_release_auto_version.py`

**RED:** Write test that verifies:
- Version bump calculation happens as before
- Instead of prompt "Confirm version? (yes/no/custom)", display message only: "Bumped to vX.Y.Z (minor). Send override if wrong."
- Release pipeline proceeds without waiting for user confirmation
- User can still send `/zie-release --bump-to=X.Y.Z` to override the suggestion
- Test checks that the prompt is never displayed and process continues to test gate

**GREEN:** Modify `commands/zie-release.md`:
1. Find section that displays version bump confirmation prompt
2. Replace prompt logic with display-only message:
   ```text
   Bumped to vX.Y.Z (CHANGE_TYPE). Send override if wrong.
   ```
3. Remove the `(yes/no/custom)` confirmation prompt entirely
4. Continue directly to test gate (make test-ci) without stopping
5. Update notes to document override syntax: `/zie-release --bump-to=X.Y.Z` (if command supports this)

**AC:**
- [ ] Version suggestion displayed without confirmation prompt
- [ ] Release pipeline auto-proceeds to test gate after version calculation
- [ ] Test verifies version message appears and pipeline continues without user input
- [ ] User can override with `--bump-to` flag (if supported) or documented alternative
- [ ] All downstream release gates (tests, merge, tag, retro) unchanged

---

## Task 4 — zie-retro: Replace plugin-specific subagent with general-purpose agent + inline prompt

**File:** `commands/zie-retro.md`
**Test:** `tests/unit/test_retro_general_purpose_agent.py`

**RED:** Write test that verifies:
- When retro command invokes agent for ADR+docs formatting, it uses `Agent(subagent_type="general-purpose")` instead of `Agent(subagent_type="zie-framework:retro-format")`
- Agent receives inline instructions covering: ADR structure (5-section format), components.md update rules, output format
- Agent output is parsed and written to files as before
- Retro flow (user input, decision capture) unchanged

**GREEN:** Modify `commands/zie-retro.md`:
1. Locate the line(s) calling `Agent(subagent_type="zie-framework:retro-format")`
2. Replace with:
   ```python
   Agent(
     subagent_type="general-purpose",
     instructions="""You are a retro format assistant. Given session notes and decisions:

   1. Structure ADRs as 5-section: Status, Context, Decision, Consequences, Alternatives
   2. Write to zie-framework/decisions/ADR-NNN-<slug>.md
   3. Update zie-framework/project/components.md with new or changed components
   4. Preserve existing ADRs; add new ones only
   5. Return JSON: { "adr_file": "path", "components_updated": true|false }
   """
   )
   ```
3. Parse agent response (JSON) and write ADR + components.md files
4. Continue to step 5 (auto-commit, see Task 5)

**AC:**
- [ ] Retro command uses Agent(subagent_type="general-purpose") with inline instructions
- [ ] Agent instructions cover ADR 5-section format and components.md rules
- [ ] Agent output is parsed and written to files correctly
- [ ] Retro user input/decision capture unchanged
- [ ] Test mocks general-purpose agent and verifies ADR/components files created

---

## Task 5 — zie-retro: Add auto-commit of ADRs + components.md at end

**File:** `commands/zie-retro.md`
**Test:** `tests/unit/test_retro_auto_commit.py` (can be combined with Task 4 test)

**RED:** Write test that verifies:
- After retro ADRs and components.md are written (by Task 4 agent), auto-commit happens:
  ```bash
  git add zie-framework/decisions/*.md zie-framework/project/components.md
  git commit -m "chore: retro vX.Y.Z"
  git push origin dev
  ```
- Exit code is 0 (success) or 1 (git push failed) with error message
- Test checks that git commands are called in correct order
- If push fails, error is logged and retro completes (doesn't block)

**GREEN:** Add to end of `commands/zie-retro.md`:
1. After ADR + components.md files are written (Task 4):
   ```bash
   git add zie-framework/decisions/*.md zie-framework/project/components.md
   git commit -m "chore: retro v${VERSION}"
   git push origin dev
   ```
2. Wrap in try-except; on failure: log error and display: "⚠️ Retro git push failed. Manual push: `git push origin dev`"
3. Return success message with commit hash: `"✓ Retro complete. Committed <hash>"`

**AC:**
- [ ] ADR + components.md files automatically committed after retro writes them
- [ ] Commit message format: "chore: retro vX.Y.Z"
- [ ] Git push to origin dev happens automatically
- [ ] If git push fails, error is logged and retro workflow continues (non-blocking)
- [ ] Test verifies git add/commit/push sequence with mocked git calls

---

## Task 6 — zie-implement: Add pre-flight warning if not in --agent session

**File:** `commands/zie-implement.md`
**Test:** `tests/unit/test_implement_agent_mode_warning.py`

**RED:** Write test that verifies:
- At start of /zie-implement, detect if session is running in `--agent zie-framework:zie-implement-mode`
- If not, display warning: "⚠️ Running /zie-implement outside agent session. Recommend: `claude --agent zie-framework:zie-implement-mode`. Continue anyway? (yes/cancel)"
- User can choose "yes" to proceed or "cancel" to exit
- If in agent mode, no warning is shown
- Test checks environment variable or session context to determine agent mode

**GREEN:** Modify `commands/zie-implement.md` — add step at beginning:
1. Check if session context includes `--agent zie-framework:zie-implement-mode`
   - Method: check `process.env.CLAUDE_AGENT_MODE` or similar session indicator (implementation detail per plugin harness)
2. If NOT in agent mode:
   ```text
   ⚠️ Running /zie-implement outside agent session.

   Recommend: claude --agent zie-framework:zie-implement-mode

   Continue anyway? (yes / cancel)
   ```
3. If "yes" → proceed with normal flow
4. If "cancel" → exit with message "Retrying in recommended mode is safer. Run: claude --agent zie-framework:zie-implement-mode"
5. If already in agent mode → display nothing, proceed

**AC:**
- [ ] Warning displayed when /zie-implement run outside --agent session
- [ ] User can choose to continue or cancel
- [ ] No warning if already in agent mode
- [ ] Test verifies agent mode detection and warning logic
- [ ] Normal implement flow unchanged if user chooses continue

---

## Task 7 — docs-sync-check: Replace plugin-specific agent with general-purpose agent (zie-release + zie-retro)

**Files:** `commands/zie-release.md`, `commands/zie-retro.md`
**Test:** `tests/unit/test_docs_sync_check_general_agent.py`

**RED:** Write test that verifies:
- docs-sync-check invocations in BOTH zie-release and zie-retro use `Agent(subagent_type="general-purpose", instructions="<inline>")` instead of plugin-specific type
- Agent receives inline instructions covering: verify CLAUDE.md and README.md are in sync with actual commands/skills/hooks on disk
- Agent returns JSON: `{ "in_sync": true|false, "mismatches": [...] }`
- Release and retro flows process result as before
- Both commands can run in parallel or background with general-purpose agent (same as before)

**GREEN:** Replace both invocations:
1. In `commands/zie-release.md` line 83: Replace `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True)` with:
   ```python
   Agent(
     subagent_type="general-purpose",
     run_in_background=True,
     instructions="""Verify CLAUDE.md and README.md are in sync with actual codebase:
   1. Scan zie-framework/commands/*.md — extract all `/zie-*` command names
   2. Scan zie-framework/skills/*/*.md — extract all skill names
   3. Scan zie-framework/hooks/*.py — extract all hook event types
   4. Check that CLAUDE.md Development Commands section lists all commands
   5. Check that README.md skills table lists all skills
   6. Return JSON: { "in_sync": bool, "mismatches": [list of divergences] }
   """
   )
   ```
2. In `commands/zie-retro.md` line 81: Replace `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True, prompt="...")` with:
   ```python
   Agent(
     subagent_type="general-purpose",
     run_in_background=True,
     instructions="""Verify CLAUDE.md and README.md are in sync with changed files:
   1. Scan zie-framework/commands/*.md — extract all `/zie-*` command names
   2. Scan zie-framework/skills/*/*.md — extract all skill names
   3. For each changed file: verify it's documented in CLAUDE.md or README.md
   4. Return JSON: { "in_sync": bool, "mismatches": [list of divergences], "needs_update": [files] }
   """
   )
   ```
3. Parse response JSON in both commands and surface any mismatches as warnings (non-blocking)

**AC:**
- [ ] Both zie-release.md (line 83) and zie-retro.md (line 81) use Agent(subagent_type="general-purpose") with inline instructions
- [ ] Agent instructions cover CLAUDE.md + README.md sync verification (tailored for each context)
- [ ] Agent returns JSON with sync status and mismatches
- [ ] Mismatches are surfaced as warnings in both release and retro output (non-blocking)
- [ ] Both commands can still run background agents; general-purpose agent respects run_in_background=True flag
- [ ] Test mocks general-purpose agent and verifies sync check logic in both commands

---

## Summary

| Task | Component | Changes | Tests |
|------|-----------|---------|-------|
| 1 | spec-design SKILL.md | Remove steps 6 & 8, auto-approve on reviewer APPROVED | test_spec_design_auto_approve.py |
| 2 | zie-plan command | Skip approval prompt, auto-commit on reviewer APPROVED | test_plan_auto_approve_gate.py |
| 3 | zie-release command | Auto-accept version suggestion, display only | test_release_auto_version.py |
| 4 | zie-retro command | Replace retro-format subagent with general-purpose agent | test_retro_general_purpose_agent.py |
| 5 | zie-retro command | Auto-commit ADRs + components.md at end | test_retro_auto_commit.py |
| 6 | zie-implement command | Add pre-flight --agent mode warning | test_implement_agent_mode_warning.py |
| 7 | zie-release + zie-retro commands | Replace docs-sync-check subagent with general-purpose agent (2 locations) | test_docs_sync_check_general_agent.py |

**Dependencies:**
- Tasks 4 & 5 share zie-retro.md; no file conflicts (both write to same file, sequential steps)
- Task 7 touches zie-retro.md (line 81) but does not conflict with Tasks 4 & 5 (different line ranges)
  - <!-- depends_on: Task 4 completion before Task 7 retro modification -->
- All other tasks are independent (no shared output files)

