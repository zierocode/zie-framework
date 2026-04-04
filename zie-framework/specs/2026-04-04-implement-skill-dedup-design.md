# implement-skill-dedup — Design Spec

**Problem:** `commands/zie-implement.md` lines 64–66 (Task Loop steps 2–4) contain inline RED/GREEN/REFACTOR instructions that duplicate the canonical `skills/tdd-loop/SKILL.md`, creating two places to maintain TDD guidance.

**Approach:** Remove the inline steps 2–4 (RED/GREEN/REFACTOR) from the Task Loop and replace with a 3-line pointer that unconditionally invokes `Skill(zie-framework:tdd-loop)`. Also clean up line 51, which redundantly re-states the invocation with an incorrect conditional (`tdd: deep` gate) that implies inline TDD is the default path.

**Components:**
- `commands/zie-implement.md` — only file changed

**Data Flow:**

1. During task loop execution, Claude reaches the TDD step.
2. Previously: Claude reads inline RED/GREEN/REFACTOR prose from the command file itself.
3. After change: Claude invokes `Skill(zie-framework:tdd-loop)` and follows that skill exactly.
4. The skill's loop exits; Claude continues to step 5 (Risk Classification) as before.
5. No other steps in the Task Loop change.

**Exact Lines Being Removed:**

```
Line 51 (current):
  **TDD:** RED → GREEN → REFACTOR per task. `tdd: deep` in plan → invoke `Skill(zie-framework:tdd-loop)`.

Lines 64–66 (current):
  2. **→ RED (failing test)** — write failing test (RED). `make test-unit` must FAIL. (Test pass → feature exists, skip task.)
  3. **→ GREEN (implementation)** — minimum code to pass (GREEN). `make test-unit` must PASS.
  4. **→ REFACTOR (cleanup)** — clean up. `make test-unit` still PASS.
```

**Replacement (3-line pointer, placed at step 2 in the Task Loop):**

```
2. **→ TDD loop** — Invoke `Skill(zie-framework:tdd-loop)`. Follow it exactly.
   If tests already pass before writing any test → feature exists, skip task.
   Skill exits after REFACTOR; continue to step 3.
```

**Renumbering:** After removing lines 64–66 (3 steps) and inserting 1 step, steps 3 onward in the Task Loop shift: old steps 5–8 become new steps 3–6.

**Line 51 replacement:** Replace with a single inline note in the Context Bundle section that removes the `tdd: deep` conditionality:

```
**TDD:** Every task uses RED → GREEN → REFACTOR via `Skill(zie-framework:tdd-loop)`.
```

**Edge Cases:**

- `tdd: deep` annotation in plan files: this flag currently gates skill invocation. After this change the skill is invoked unconditionally, so `tdd: deep` becomes a no-op. It should be left harmless in existing plan files (no migration needed — the annotation is ignored, not errored on).
- Test suite enforcement: existing tests that assert on zie-implement.md content must be updated to match the new pointer text. Grep test suite before trimming.
- Workflow continuity: the skill's final state (after REFACTOR) must leave Claude positioned to proceed to Risk Classification (new step 3). The tdd-loop skill exits cleanly after REFACTOR — no change needed in the skill itself.

**Acceptance Criteria:**

- AC: `commands/zie-implement.md` no longer contains inline RED/GREEN/REFACTOR prose in the Task Loop.
- AC: `commands/zie-implement.md` contains the 3-line pointer invoking `Skill(zie-framework:tdd-loop)`.
- AC: grep for `tdd-loop` in `commands/zie-implement.md` returns a match.
- AC: `commands/zie-implement.md` is shortened by ≥20 lines compared to pre-change.
- AC: `test_inline_tdd_guidance_present` updated to assert `Skill(zie-framework:tdd-loop)` appears instead of inline RED/GREEN/REFACTOR prose.
- AC: test suite passes after all changes (zero test failures).

**Test Updates Required:**

| Test | Current assertion | New assertion |
| --- | --- | --- |
| `test_inline_tdd_guidance_present` | Checks that RED/GREEN/REFACTOR text is present in zie-implement.md | Assert that `Skill(zie-framework:tdd-loop)` appears in zie-implement.md |
| `test_tdd_deep_conditional_present` | Asserts the `tdd: deep` conditional block is present | Remove or update to assert the `tdd: deep` conditional is gone |
| `test_per_task_tdd_loop_skill_absent` | Asserts the skill invocation is absent | Invert: assert the skill IS present (i.e., `Skill(zie-framework:tdd-loop)` appears) |

**Out of Scope:**

- Changes to `skills/tdd-loop/SKILL.md` — it is the canonical source, untouched.
- Changes to any other command or skill file.
- Removing `tdd: deep` from existing plan files — leave as harmless no-ops.
- Adding new TDD guidance or changing the TDD process itself.
