---
approved: true
approved_at: 2026-04-04
backlog: backlog/lean-spec-design-agent-syntax.md
---

# Fix spec-design @agent-spec-reviewer → Skill() Invocation — Implementation Plan

**Goal:** Replace `@agent-spec-reviewer` with `Skill(zie-framework:spec-reviewer)` in spec-design/SKILL.md Step 5 and add a structural guard test.
**Architecture:** Two-file change — fix the one line in spec-design/SKILL.md and create a new structural test file. No runtime code, no hooks, no config changes.
**Tech Stack:** Markdown (skill file edit), Python/pytest (structural test)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-design/SKILL.md` | Replace `@agent-spec-reviewer` dispatch + remove fallback comment |
| Create | `tests/unit/test_skill_agent_syntax.py` | Structural test: no `@agent-` syntax in any SKILL.md |

---

## Task 1: Add structural test (RED)

**Acceptance Criteria:**
- `tests/unit/test_skill_agent_syntax.py` exists
- Test `test_no_agent_syntax_in_skills` collects all `skills/*/SKILL.md` files and asserts none contain `@agent-`
- Test fails on current codebase (spec-design/SKILL.md has `@agent-spec-reviewer`)

**Files:**
- Create: `tests/unit/test_skill_agent_syntax.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skill_agent_syntax.py
  """Structural guard: no SKILL.md file may use @agent- syntax.
  Skills must invoke reviewers via Skill() directly.
  @agent- syntax is reserved for commands/ that spawn subagent worktrees.
  """
  from pathlib import Path

  SKILLS_DIR = Path(__file__).parents[2] / "skills"


  class TestNoAgentSyntaxInSkills:
      def test_no_agent_syntax_in_skills(self):
          skill_files = list(SKILLS_DIR.glob("*/SKILL.md"))
          assert skill_files, "No SKILL.md files found — check SKILLS_DIR path"
          violations = []
          for skill_file in skill_files:
              text = skill_file.read_text()
              if "@agent-" in text:
                  # Find line numbers for clear error messages
                  for lineno, line in enumerate(text.splitlines(), 1):
                      if "@agent-" in line:
                          violations.append(f"{skill_file.name} (line {lineno}): {line.strip()}")
          assert not violations, (
              "Skills must not use @agent- syntax. "
              "Use Skill(zie-framework:<name>) instead.\n"
              + "\n".join(violations)
          )
  ```

  Run: `make test-unit` — must FAIL with:
  ```
  AssertionError: Skills must not use @agent- syntax.
  SKILL.md (line 115): 5. **Spec reviewer loop** — dispatch `@agent-spec-reviewer` with:
  ```

- [ ] **Step 2: Implement (GREEN)**

  No implementation yet — test must fail first. Proceed to Task 2.

- [ ] **Step 3: Refactor**

  No refactor needed for a new test file.

---

## Task 2: Fix spec-design/SKILL.md Step 5

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` Step 5 calls `Skill(zie-framework:spec-reviewer)` directly
- The HTML fallback comment `<!-- fallback: Skill(zie-framework:spec-reviewer) -->` is removed
- The text `@agent-spec-reviewer` no longer appears in the file
- All existing tests in `test_spec_design_batch_approval.py` and `test_spec_design_fast_path.py` still pass
- The new structural test from Task 1 now passes

**Files:**
- Modify: `skills/spec-design/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  Tests already written in Task 1. The structural test currently FAILS because the file still contains `@agent-spec-reviewer`. No additional test code needed here — the RED state is the Task 1 failure.

  Confirm current state:
  Run: `make test-unit` — `test_skill_agent_syntax::test_no_agent_syntax_in_skills` FAILS

- [ ] **Step 2: Implement (GREEN)**

  Replace lines 115-116 in `skills/spec-design/SKILL.md`:

  **Before (lines 115-116):**
  ```markdown
  5. **Spec reviewer loop** — dispatch `@agent-spec-reviewer` with:
     <!-- fallback: Skill(zie-framework:spec-reviewer) -->
  ```

  **After (line 115 only — line 116 deleted):**
  ```markdown
  5. **Spec reviewer loop** — invoke `Skill(zie-framework:spec-reviewer)` with:
  ```

  Run: `make test-unit` — must PASS (structural test + all existing spec-design tests)

- [ ] **Step 3: Refactor**

  Read the full Step 5 block to verify the change reads naturally in context. No further edits needed.

  Run: `make test-unit` — still PASS

---

## Verification

After both tasks complete:

```bash
make test-unit
```

Expected: all tests pass, including:
- `tests/unit/test_skill_agent_syntax.py::TestNoAgentSyntaxInSkills::test_no_agent_syntax_in_skills` ✅
- `tests/unit/test_spec_design_batch_approval.py::TestBatchApprovalStructure::test_spec_reviewer_invocation_still_present` ✅
- `tests/unit/test_spec_design_fast_path.py::TestSpecDesignFastPath::test_existing_steps_intact` ✅ (checks "Spec reviewer loop" still present)
