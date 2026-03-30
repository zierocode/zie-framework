---
approved: true
approved_at: 2026-03-30
backlog: backlog/model-routing-v2.md
spec: specs/2026-03-30-model-routing-v2-design.md
---

# Plan: Model Routing v2

## Goal
Reduce cost and latency of `/zie-release` and `impl-reviewer` by downgrading their default model from sonnet to haiku, while preserving reasoning quality for the specific steps that genuinely require sonnet-level analysis.

## Architecture
- **Frontmatter model downgrades:** beide commands/skills change default to `model: haiku`
- **Inline overrides:** specific steps annotated with `<!-- model: sonnet -->` comments for human interpretation
- **Test alignment:** update EXPECTED map in test file to reflect haiku model for both files

## Tech Stack
- **Markup:** Markdown comments (`<!-- -->`) for inline model hints
- **Test framework:** pytest (read frontmatter YAML, validate against EXPECTED map)
- **No dependencies:** changes are metadata-only, no runtime behavior changes

---

## File Map

| File | Responsibility | Status |
|------|---|---|
| `commands/zie-release.md` | Frontmatter model sonnet→haiku; annotate version + CHANGELOG steps | Modify |
| `skills/impl-reviewer/SKILL.md` | Frontmatter model sonnet→haiku; add escalation guidance comment | Modify |
| `tests/unit/test_model_effort_frontmatter.py` | Update EXPECTED map for zie-release and impl-reviewer | Modify |

---

## Task 1 — Update zie-release.md frontmatter and annotate sonnet-only steps

**File:** `commands/zie-release.md`

**Test:** `tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_model_values`

**RED:** Test fails because zie-release.md has `model: sonnet` but EXPECTED expects `model: haiku`

**GREEN:**
1. Change zie-release.md frontmatter from `model: sonnet` to `model: haiku`
2. Add inline comment before "Step 1/10 Suggest version bump" section:
   ```markdown
   <!-- model: sonnet reasoning: version suggestion compares commits against semver rules and requires judgment about breaking changes vs new features. -->
   ```
3. Add inline comment before "Step 5 Draft CHANGELOG entry" section:
   ```markdown
   <!-- model: sonnet reasoning: narrative rewrite of commit messages into human-readable feature/fix groups requires editorial judgment and understanding of change impact. -->
   ```
4. Update test EXPECTED map: `"commands/zie-release.md": ("haiku", "medium")`
5. Run `make test-unit` → test should pass

**AC:**
- [ ] zie-release.md frontmatter has `model: haiku`
- [ ] Version suggestion section has sonnet escalation comment
- [ ] CHANGELOG draft section has sonnet escalation comment
- [ ] test_model_effort_frontmatter.py EXPECTED map includes zie-release as haiku
- [ ] `make test-unit` exits 0

---

## Task 2 — Update impl-reviewer SKILL.md frontmatter and add escalation guidance

**File:** `skills/impl-reviewer/SKILL.md`

**Test:** `tests/unit/test_model_effort_frontmatter.py::TestExpectedValues::test_correct_model_values`

**RED:** Test fails because impl-reviewer/SKILL.md has `model: sonnet` but EXPECTED expects `model: haiku`

**GREEN:**
1. Change impl-reviewer/SKILL.md frontmatter from `model: sonnet` to `model: haiku`
2. Add guidance comment in Phase 2 (Review Checklist), after the "Read the changed files and check each item:" line:
   ```markdown
   <!-- model: sonnet escalation note: Routine checks (AC coverage, test exists, security scanning) run on haiku. If this review detects new patterns, security concerns, or architectural changes that conflict with existing ADRs, flag for human review or escalate to sonnet reasoning. -->
   ```
3. Update test EXPECTED map: `"skills/impl-reviewer/SKILL.md": ("haiku", "medium")`
4. Run `make test-unit` → test should pass

**AC:**
- [ ] impl-reviewer/SKILL.md frontmatter has `model: haiku`
- [ ] Phase 2 section includes escalation guidance comment
- [ ] test_model_effort_frontmatter.py EXPECTED map includes impl-reviewer as haiku
- [ ] `make test-unit` exits 0

---

## Task 3 — Update test EXPECTED map and verify all tests pass

**File:** `tests/unit/test_model_effort_frontmatter.py`

**Test:** `tests/unit/test_model_effort_frontmatter.py` (full test suite)

**RED:** Run `make test-unit` — tests fail due to model mismatch in EXPECTED

**GREEN:**
1. Update line 23 in test_model_effort_frontmatter.py:
   ```python
   "commands/zie-release.md":   ("haiku", "medium"),  # was ("sonnet", "medium")
   ```
2. Update line 34 in test_model_effort_frontmatter.py:
   ```python
   "skills/impl-reviewer/SKILL.md": ("haiku", "medium"),  # was ("sonnet", "medium")
   ```
3. Add "commands/zie-release.md" to the EXPECTED_HAIKU list if needed for the TestHaikuFiles class (currently at line 150-159, add at line 153):
   ```python
   "commands/zie-release.md",
   ```
4. Run `make test-unit` → all tests should exit 0
5. Verify no regressions: run full test suite `make test` if available

**AC:**
- [ ] test_model_effort_frontmatter.py EXPECTED map has zie-release as haiku
- [ ] test_model_effort_frontmatter.py EXPECTED map has impl-reviewer as haiku
- [ ] zie-release.md added to TestHaikuFiles.EXPECTED_HAIKU list
- [ ] TestExpectedValues::test_correct_model_values passes for both files
- [ ] TestHaikuFiles::test_haiku_files_have_correct_model passes
- [ ] `make test-unit` exits 0
- [ ] No test regressions in full suite

---

## Dependencies & Ordering

**Task 1 and Task 2 are independent** — both modify different files (zie-release.md vs impl-reviewer/SKILL.md) and neither depends on the other. Can be executed in parallel.

**Task 3 depends on Tasks 1 and 2** — the test file must be updated after both command and skill are modified, since EXPECTED values need to match the actual frontmatter in both files.

Suggested execution order: Task 1 + Task 2 in parallel, then Task 3 to verify.

---

## Verification

After all tasks complete:
```bash
make test-unit    # Should exit 0
make test         # Full suite should pass without regressions
```

Spot check:
- `zie-release.md` frontmatter contains `model: haiku`
- `impl-reviewer/SKILL.md` frontmatter contains `model: haiku`
- Both files have escalation comments visible in their content
- EXPECTED map in test reflects both as haiku
