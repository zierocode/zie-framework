---
approved: true
approved_at: 2026-03-23
backlog: backlog/remove-superpowers-deps.md
---

# Remove Superpowers Dependencies — Implementation Plan

**Goal:** Remove all `superpowers_enabled` references and `Skill(superpowers:*)`
calls from zie-framework so it is fully self-contained.

**Architecture:** Skills were already forked in a previous release. This plan
removes the last remaining references — config key in 2 commands + 1 hook,
plus doc updates. Pure deletion/simplification, no new behaviour.

**Tech Stack:** Python (hooks, tests), Markdown (commands, skills, docs)

---

## แผนที่ไฟล์

| Action | File | Change |
| --- | --- | --- |
| Modify | `tests/unit/test_fork_superpowers_skills.py` | Add 3 failing tests (RED) |
| Modify | `commands/zie-plan.md` | Remove `superpowers_enabled` from pre-flight |
| Modify | `hooks/session-resume.py` | Remove unused `superpowers` variable |
| Modify | `commands/zie-init.md` | Remove field from `.config` template |
| Modify | `CLAUDE.md` | Update graceful degradation rule |
| Modify | `README.md` | Remove superpowers row from dependencies table |
| Modify | `zie-framework/project/decisions.md` | Add ADR |

---

## Task 1: Write failing tests (RED)

<!-- No depends_on — first task -->

**Files:**

- Modify: `tests/unit/test_fork_superpowers_skills.py`

- [ ] **Step 1: Add 3 new test methods to `TestCommandsNoSuperpowersDependency`**

  Append to the class in `tests/unit/test_fork_superpowers_skills.py`:

  ```python
  def test_zie_plan_no_superpowers_enabled(self):
      content = read("commands/zie-plan.md")
      assert "superpowers_enabled" not in content, (
          "zie-plan must not read superpowers_enabled from .config"
      )

  def test_zie_init_no_superpowers_enabled_in_config_template(self):
      content = read("commands/zie-init.md")
      assert "superpowers_enabled" not in content, (
          "zie-init .config template must not include superpowers_enabled field"
      )

  def test_session_resume_no_superpowers_enabled(self):
      content = read("hooks/session-resume.py")
      assert "superpowers_enabled" not in content, (
          "session-resume hook must not read superpowers_enabled from config"
      )
  ```

- [ ] **Step 2: Run tests — must FAIL**

  ```bash
  python3 -m pytest tests/unit/test_fork_superpowers_skills.py \
    -k "superpowers_enabled" -v
  ```

  Expected: 3 FAILED (references still exist in files)

- [ ] **Step 3: Commit RED tests**

  ```bash
  git add tests/unit/test_fork_superpowers_skills.py
  git commit -m "test: add failing tests for superpowers_enabled removal"
  ```

---

## Task 2: Remove superpowers_enabled from zie-plan.md (GREEN)

<!-- No depends_on -->

**Files:**

- Modify: `commands/zie-plan.md:15`

Current line 15:

```text
2. Read `zie-framework/.config` → zie_memory_enabled, superpowers_enabled.
```

- [ ] **Step 1: Update line 15**

  Replace with:

  ```text
  2. Read `zie-framework/.config` → zie_memory_enabled.
  ```

- [ ] **Step 2: Run test**

  ```bash
  python3 -m pytest \
    tests/unit/test_fork_superpowers_skills.py::TestCommandsNoSuperpowersDependency::test_zie_plan_no_superpowers_enabled \
    -v
  ```

  Expected: PASS

- [ ] **Step 3: Commit**

  ```bash
  git add commands/zie-plan.md
  git commit -m "fix: remove superpowers_enabled from zie-plan pre-flight"
  ```

---

## Task 3: Remove superpowers_enabled from session-resume.py (GREEN)

<!-- No depends_on -->

**Files:**

- Modify: `hooks/session-resume.py:69`

Current line 69:

```python
superpowers = config.get("superpowers_enabled", False)
```

The variable `superpowers` is read but never used in output. Remove it.

- [ ] **Step 1: Delete line 69**

  Remove the entire line. No other lines reference this variable.

- [ ] **Step 2: Run test**

  ```bash
  python3 -m pytest \
    tests/unit/test_fork_superpowers_skills.py::TestCommandsNoSuperpowersDependency::test_session_resume_no_superpowers_enabled \
    -v
  ```

  Expected: PASS

- [ ] **Step 3: Run session-resume tests to confirm no regression**

  ```bash
  python3 -m pytest tests/unit/test_hooks_session_resume.py -v
  ```

  Expected: all PASS

- [ ] **Step 4: Commit**

  ```bash
  git add hooks/session-resume.py
  git commit -m "fix: remove unused superpowers_enabled from session-resume hook"
  ```

---

## Task 4: Remove superpowers_enabled from zie-init.md (GREEN)

<!-- No depends_on -->

**Files:**

- Modify: `commands/zie-init.md`

Find and remove this line from the `.config` JSON template in step 3:

```text
"superpowers_enabled": <true if superpowers plugin found>,
```

- [ ] **Step 1: Remove the field from the .config template**

  The template block will shrink from 8 fields to 7 fields. Do not remove any
  other fields.

- [ ] **Step 2: Run test**

  ```bash
  python3 -m pytest \
    tests/unit/test_fork_superpowers_skills.py::TestCommandsNoSuperpowersDependency::test_zie_init_no_superpowers_enabled_in_config_template \
    -v
  ```

  Expected: PASS

- [ ] **Step 3: Run full fork-superpowers test file**

  ```bash
  python3 -m pytest tests/unit/test_fork_superpowers_skills.py -v
  ```

  Expected: all PASS

- [ ] **Step 4: Commit**

  ```bash
  git add commands/zie-init.md
  git commit -m "fix: remove superpowers_enabled from zie-init .config template"
  ```

---

## Task 5: Update CLAUDE.md and README.md

<!-- depends_on: Task 2, Task 3, Task 4 -->

**Files:**

- Modify: `CLAUDE.md`
- Modify: `README.md`

- [ ] **Step 1: Update CLAUDE.md graceful degradation rule**

  Find:

  ```text
  **Graceful degradation** — every feature must work without optional
    dependencies (zie-memory, superpowers, playwright)
  ```

  Replace with:

  ```text
  **Graceful degradation** — every feature must work without optional
    dependencies (zie-memory, playwright)
  ```

- [ ] **Step 2: Update README.md dependencies table**

  Find and remove the superpowers row:

  ```text
  | superpowers plugin | No | Inline Q&A mode |
  ```

- [ ] **Step 3: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all PASS

- [ ] **Step 4: Commit**

  ```bash
  git add CLAUDE.md README.md
  git commit -m "docs: remove superpowers as optional dependency"
  ```

---

## Task 6: Add ADR to decisions.md

<!-- depends_on: Task 5 -->

**Files:**

- Modify: `zie-framework/project/decisions.md`

- [ ] **Step 1: Append ADR entry**

  Add to `zie-framework/project/decisions.md`:

  ```markdown
  ## D-005: Remove superpowers dependency (2026-03-23)

  **Decision:** zie-framework no longer depends on the superpowers plugin.

  **Context:** zie-framework previously used superpowers:brainstorming,
  superpowers:writing-plans, superpowers:systematic-debugging, and
  superpowers:verification-before-completion. These were forked into
  zie-framework/skills/ as spec-design, write-plan, debug, and verify.
  The last remaining references (superpowers_enabled config key) are now
  removed.

  **Consequence:** zie-framework is fully self-contained. The
  superpowers_enabled field in existing .config files is ignored (backward
  compatible — no migration needed).
  ```

- [ ] **Step 2: Commit**

  ```bash
  git add zie-framework/project/decisions.md
  git commit -m "docs: add ADR for superpowers dependency removal"
  ```

---

## Task 7: Final verify

<!-- depends_on: Task 6 -->

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all tests PASS, no regressions

- [ ] **Step 2: Invoke Skill(zie-framework:verify)**

- [ ] **Step 3: Confirm no remaining superpowers references in active code**

  ```bash
  grep -r "superpowers" commands/ hooks/ skills/ CLAUDE.md README.md \
    --include="*.md" --include="*.py" -l
  ```

  Expected: no output (zero files)
