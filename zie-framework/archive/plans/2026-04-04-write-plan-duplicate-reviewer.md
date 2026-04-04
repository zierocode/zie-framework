# Plan: Remove Duplicate Reviewer Loop from write-plan Skill
status: approved

## Tasks

- [ ] **Task 1: Remove reviewer loop + ROADMAP update block from write-plan skill**

  **Acceptance Criteria:**
  - `skills/write-plan/SKILL.md` ends after saving the plan file (`zie-framework/plans/YYYY-MM-DD-<feature-slug>.md`)
  - The "After saving, run the plan reviewer loop" block is gone
  - The "Then update zie-framework/ROADMAP.md" block is gone
  - The `## Notes` section at the bottom remains intact

  **Files:**
  - Modify: `skills/write-plan/SKILL.md`

  - [ ] **Step 1: Write failing tests (RED)**

    In `tests/unit/test_sdlc_pipeline.py`, replace `test_write_plan_invokes_plan_reviewer`:
    ```python
    def test_write_plan_invokes_plan_reviewer(self):
        # Reviewer gate lives in zie-plan.md, NOT inside the skill
        skill_content = read("skills/write-plan/SKILL.md")
        assert "plan-reviewer" not in skill_content, \
            "write-plan skill must NOT invoke plan-reviewer (reviewer gate belongs in zie-plan.md)"
        command_content = read("commands/zie-plan.md")
        assert "plan-reviewer" in command_content, \
            "zie-plan.md must contain the plan-reviewer gate"
    ```

    In `tests/unit/test_skills_advanced_features.py`, replace `test_write_plan_documents_plan_reviewer`:
    ```python
    def test_write_plan_does_not_invoke_plan_reviewer(self):
        content = read_skill("write-plan")
        assert "plan-reviewer" not in content, \
            "write-plan/SKILL.md must NOT reference the plan-reviewer loop (reviewer gate belongs in zie-plan.md)"
    ```

    Run: `make test-fast` — must FAIL (skill still has reviewer block)

  - [ ] **Step 2: Implement (GREEN)**

    Edit `skills/write-plan/SKILL.md` — remove the two blocks after the `## บันทึกไว้ที่` section:

    Remove from "After saving, run the **plan reviewer loop**:" through the end of the ROADMAP update block ("- Wait for explicit approval before marking `approved: true` in frontmatter"), leaving only the `## Notes` section.

    The `## บันทึกไว้ที่` section should end at:
    ```
    Save plan to: `zie-framework/plans/YYYY-MM-DD-<feature-slug>.md`
    ```

    Run: `make test-fast` — must PASS

  - [ ] **Step 3: Refactor**

    Verify `commands/zie-plan.md` reviewer gate wording is unchanged and complete. No changes needed.

    Run: `make test-ci` — still PASS

## Test Strategy

- No new test files needed
- Update two existing tests that assert the old (incorrect) behavior
- Tests pivot: skill must NOT have reviewer, command MUST have reviewer
- `make test-ci` is the full gate — covers lint + unit suite

## Files to Change

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/write-plan/SKILL.md` | Remove reviewer loop + ROADMAP update block |
| Modify | `tests/unit/test_sdlc_pipeline.py` | Flip assertion: reviewer must NOT be in skill |
| Modify | `tests/unit/test_skills_advanced_features.py` | Flip assertion + rename test to reflect new ownership |
