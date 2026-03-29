---
approved: true
approved_at: 2026-03-24
approved_by: spec-reviewer agent
backlog: backlog/parallel-execution-patterns.md
priority: MEDIUM
spec_type: design
---

# Parallel Execution Patterns — Best Practices for zie-framework

**Problem:** zie-framework uses parallel execution in multiple places (Agents, tasks, quality checks) but patterns are inconsistent and under-documented. Some commands use "Fork" incorrectly (still blocking), task dependency annotations are optional, and there's no guidance on safe parallelism limits.

**Goal:** Document and standardize parallel execution patterns across zie-framework — when to parallelize, how to express dependencies, resource limits, and file conflict prevention.

**Architecture:** Documentation + targeted fixes to align existing commands with documented patterns. No new infrastructure.

**Tech Stack:** Markdown (command definitions, documentation), pytest (pattern assertions)

---

## Context

### Current State — Parallel Patterns in Use

| Pattern | Location | Status |
|---------|----------|--------|
| `<!-- depends_on: T1, T2 -->` | `zie-implement.md`, `write-plan/SKILL.md` | ✅ Documented, implemented |
| Parallel Agents (no explicit limit) | `zie-plan.md` (multi-slug) | ⚠️ No max limit defined |
| "Fork Skill" (pseudo-parallel) | `zie-retro.md`, `zie-release.md` | ❌ Misleading — still blocking |
| Parallel quality checks | `zie-release.md` (docs-sync + TODO scan) | ✅ True parallel via simultaneous invocation |
| Context bundle (shared read) | `zie-implement.md` | ✅ Loaded once, passed to all tasks |

### Current State — Dependency Annotations

**Plan files use `<!-- depends_on: -->` in two places:**

1. **Task-level dependencies** (in plan `.md` files):
   ```markdown
   ## Task 1: Add SDLC_STAGES constant
   <!-- depends_on: none -->

   ## Task 2: Add warn_on_empty to parse_roadmap
   <!-- depends_on: Task 1 -->
   ```

2. **Skill-level guidance** (`skills/write-plan/SKILL.md` line 75, 98-99):
   ```markdown
   <!-- depends_on: Task M -->
   Use `<!-- depends_on: Task N, Task M -->` to express task dependencies.
   Tasks without depends_on can run in parallel.
   ```

**Problem:** Dependency annotations are optional — authors may forget to add them, causing incorrect parallel execution.

---

## Requirements

### Functional

1. **Document parallel execution patterns:**
   - When to parallelize (independent work, read-only operations, different output files)
   - When NOT to parallelize (shared state, write conflicts, rate limits)
   - How to express dependencies (`<!-- depends_on: -->` syntax)
   - Safe default limits (max parallel Agents, max concurrent file writes)

2. **Fix misleading "Fork" terminology:**
   - Rename "Fork Skill" to "Invoke Skills simultaneously" (still blocking)
   - OR convert to true async via `Agent + run_in_background` (see: `async-skills-background-execution-design.md`)

3. **Add dependency hint enforcement:**
   - Plan reviewer suggests `<!-- depends_on: -->` when tasks share output files
   - Implement reviewer checks task parallelism hints before approval

4. **Define safe parallelism limits:**
   - Max parallel Agents: **4** (balance speed vs. API rate limits)
   - Max concurrent file writes: **1 per file** (obvious, but enforce via review)
   - Max parallel "Fork" operations: **unlimited** (read-only, no conflicts)

5. **Add file conflict detection:**
   - Before launching parallel tasks/Agents, check for overlapping output files
   - If conflict detected: force sequential execution or reject plan

### Non-Functional

1. **Backward compatible** — existing plans without `depends_on` still work (default parallel)
2. **Graceful degradation** — if parallel execution fails, fall back to sequential
3. **Visible progress** — use `TaskCreate` to show what's running in parallel
4. **No silent failures** — if a parallel task fails, error is reported with task ID

---

## Design

### Pattern 1: Task-Level Parallelism (`zie-implement.md`)

**Current (line 81-88):**
```markdown
Default: parallel. Tasks with no depends_on annotation run in parallel.
Tasks annotated with `<!-- depends_on: T1, T2 -->` run sequentially after all
listed dependencies complete.
```

**Enhancement:** Add explicit max limit and file conflict check:

```markdown
**Max parallel tasks: 4.** If more than 4 tasks are ready simultaneously,
queue excess tasks and start them as slots become available.

**File conflict check:** Before launching parallel tasks, verify that no two
tasks write to the same output file. If conflict detected:
1. Add implicit `<!-- depends_on: TN -->` to serialize conflicting tasks
2. Print warning: "Task N and Task M both write to X.py — serializing"
```

### Pattern 2: Agent-Level Parallelism (`zie-plan.md`, reviewer agents)

**Current:** Multi-slug plan launches parallel Agents without explicit limit.

**Enhancement:** Add limit + dependency hints:

```markdown
**Max parallel Agents: 4.** When processing multiple slugs in parallel,
spawn up to 4 Agents simultaneously. Queue excess slugs and start them
as Agents complete.

**Dependency hint:** If multiple slugs share a common output directory
or file pattern, add `<!-- depends_on: slug-1 -->` to serialize them.
```

### Pattern 3: "Fork" Pattern (Quality Checks)

**Current (`zie-release.md` line 88-90):**
```markdown
Invoke simultaneously:
1. Fork `Skill(zie-framework:docs-sync-check)`
2. Bash: TODOs and secrets scan
```

**Problem:** "Fork" implies async, but both Skills run in foreground (blocking).

**Fix:** Rename to avoid confusion:

```markdown
Invoke in the same message (both run, but block until complete):
1. `Skill(zie-framework:docs-sync-check)` with changed files
2. Bash: TODOs and secrets scan
```

OR (better): Convert to true async per `async-skills-background-execution-design.md`.

### Pattern 4: Shared Context Bundle (`zie-implement.md`)

**Current (line 90-102):**
```markdown
Load context bundle (once per session):
1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
2. Read `zie-framework/project/context.md` → store as `context_content`
3. Bundle as `context_bundle = { adrs: adrs_content, context: context_content }`
Pass `context_bundle` to every impl-reviewer invocation in the task loop.
```

**Status:** ✅ Correct pattern — load once, share across parallel tasks.

**Enhancement:** Document as best practice:

```markdown
**Best Practice:** For any parallel operation that needs shared context
(ADRs, project docs, config), load once at session start and pass as
a bundle to all parallel workers. Do NOT re-load per task.
```

---

## File Changes

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/zie-implement.md` | Add max parallel tasks (4), file conflict check |
| Modify | `commands/zie-plan.md` | Add max parallel Agents (4), dependency hint for shared outputs |
| Modify | `commands/zie-release.md` | Rename "Fork" to "Invoke simultaneously" (or convert to Agent + background) |
| Modify | `skills/write-plan/SKILL.md` | Add file conflict check guidance, max parallel tasks note |
| Modify | `skills/plan-reviewer/SKILL.md` | Add dependency hint enforcement — suggest `depends_on` when tasks share files |
| Create | `zie-framework/docs/parallel-execution-patterns.md` | Central documentation for all parallel patterns |
| Create | `tests/unit/test_parallel_execution_patterns.py` | Assert patterns are correctly implemented |

---

## Parallel Execution Rules

### When to Parallelize ✅

| Scenario | Safe to Parallelize? | Rationale |
|----------|---------------------|-----------|
| Tasks write to different files | ✅ Yes | No conflict possible |
| Tasks read-only (no writes) | ✅ Yes | No side effects |
| Agents with `run_in_background: true` | ✅ Yes | True async, no blocking |
| Tasks with `<!-- depends_on: none -->` | ✅ Yes | Explicitly independent |
| Quality checks (docs-sync + TODO scan) | ✅ Yes | Different output, read-only |
| Context bundle loading | ✅ Yes | Read-only, cached |

### When NOT to Parallelize ❌

| Scenario | Safe to Parallelize? | Rationale |
|----------|---------------------|-----------|
| Tasks write to same file | ❌ No | Write conflict, data loss |
| Tasks share mutable state | ❌ No | Race condition possible |
| Agents without `run_in_background` | ❌ No | Blocking, no benefit |
| Tasks with circular `depends_on` | ❌ No | Deadlock |
| API rate-limited operations | ❌ No | Hit rate limit, failures |
| Sequential build steps (A → B → C) | ❌ No | B depends on A output |

---

## Dependency Annotation Syntax

### Task-Level Dependencies

```markdown
## Task 1: Add SDLC_STAGES constant
<!-- depends_on: none -->

## Task 2: Use SDLC_STAGES in check_impl_files
<!-- depends_on: Task 1 -->

## Task 3: Add tests for Task 2
<!-- depends_on: Task 2 -->

## Task 4: Unrelated feature
<!-- depends_on: none -->
```

**Execution order:**
- Task 1 and Task 4 run in parallel (both `depends_on: none`)
- Task 2 waits for Task 1
- Task 3 waits for Task 2
- Task 4 independent, runs anytime

### Agent-Level Dependencies

```markdown
Processing slugs: `security-path-traversal`, `security-shell-injection`, `docs-sync`

<!-- docs-sync reads files modified by security-* slugs -->
<!-- depends_on: security-path-traversal, security-shell-injection -->
```

**Execution order:**
- `security-path-traversal` and `security-shell-injection` run in parallel
- `docs-sync` waits for both security slugs to complete

---

## File Conflict Detection Algorithm

```python
def detect_file_conflicts(tasks: list) -> dict:
    """
    Returns: { filepath: [task_ids] } for files written by multiple tasks
    """
    file_writers = {}  # filepath → [task_id, ...]

    for task in tasks:
        output_files = extract_output_files(task)  # Parse task description for file paths
        for filepath in output_files:
            if filepath not in file_writers:
                file_writers[filepath] = []
            file_writers[filepath].append(task["id"])

    conflicts = {fp: writers for fp, writers in file_writers.items() if len(writers) > 1}
    return conflicts
```

**If conflicts detected:**
1. Print warning: `"File conflict: {filepath} written by {task_ids} — serializing"`
2. Add implicit `<!-- depends_on: TN -->` to later tasks
3. Execute conflicting tasks sequentially

---

## Test Plan

**New file: `tests/unit/test_parallel_execution_patterns.py`**

```python
class TestParallelExecutionPatterns:
    def test_zie_implement_max_parallel_tasks(self):
        """zie-implement.md must specify max parallel tasks limit."""
        text = (REPO_ROOT / "commands" / "zie-implement.md").read_text()
        assert "Max parallel tasks" in text or "up to" in text.lower()

    def test_zie_implement_file_conflict_check(self):
        """zie-implement.md must include file conflict detection."""
        text = (REPO_ROOT / "commands" / "zie-implement.md").read_text()
        assert "conflict" in text.lower() or "same file" in text.lower()

    def test_zie_plan_max_parallel_agents(self):
        """zie-plan.md must specify max parallel Agents limit."""
        text = (REPO_ROOT / "commands" / "zie-plan.md").read_text()
        assert "Max parallel Agents" in text or "up to" in text.lower()

    def test_zie_release_fork_terminology_fixed(self):
        """zie-release.md must not use misleading 'Fork Skill' terminology."""
        text = (REPO_ROOT / "commands" / "zie-release.md").read_text()
        # Either removed or converted to true async
        assert "Fork `Skill" not in text

    def test_depends_on_syntax_documented(self):
        """write-plan/SKILL.md must document depends_on syntax."""
        text = (REPO_ROOT / "skills" / "write-plan" / "SKILL.md").read_text()
        assert "depends_on" in text

    def test_plan_reviewer_suggests_depends_on(self):
        """plan-reviewer/SKILL.md must suggest depends_on for shared files."""
        text = (REPO_ROOT / "skills" / "plan-reviewer" / "SKILL.md").read_text()
        assert "depends_on" in text and "suggest" in text.lower()


class TestFileConflictDetection:
    def test_detect_conflicts_same_file(self):
        """File conflict detection must identify tasks writing to same file."""
        from zie_framework.utils import detect_file_conflicts  # hypothetical

        tasks = [
            {"id": "T1", "output_files": ["utils.py"]},
            {"id": "T2", "output_files": ["utils.py"]},
        ]
        conflicts = detect_file_conflicts(tasks)
        assert "utils.py" in conflicts
        assert "T1" in conflicts["utils.py"]
        assert "T2" in conflicts["utils.py"]

    def test_no_conflicts_different_files(self):
        """No conflicts when tasks write to different files."""
        from zie_framework.utils import detect_file_conflicts

        tasks = [
            {"id": "T1", "output_files": ["utils.py"]},
            {"id": "T2", "output_files": ["config.py"]},
        ]
        conflicts = detect_file_conflicts(tasks)
        assert conflicts == {}
```

---

## Out of Scope

1. **Automatic parallelism optimization** — no AI-based task scheduling
2. **Dynamic dependency inference** — dependencies must be explicit in plan
3. **Rate limiting implementation** — only document the limit, don't implement throttling
4. **Distributed execution** — single-machine only, no cluster support

---

## Acceptance Criteria

- [ ] `commands/zie-implement.md` specifies max parallel tasks (4)
- [ ] `commands/zie-implement.md` includes file conflict detection logic
- [ ] `commands/zie-plan.md` specifies max parallel Agents (4)
- [ ] `commands/zie-release.md` "Fork Skill" terminology fixed (renamed or converted to Agent)
- [ ] `skills/write-plan/SKILL.md` documents `depends_on` syntax + file conflict check
- [ ] `skills/plan-reviewer/SKILL.md` suggests `depends_on` when tasks share files
- [ ] `zie-framework/docs/parallel-execution-patterns.md` created (central docs)
- [ ] `tests/unit/test_parallel_execution_patterns.py` created with 6+ test methods
- [ ] All tests pass: `make test-unit` exits 0

---

## Edge Cases

1. **Circular dependencies** — `Task 1 depends_on Task 2` + `Task 2 depends_on Task 1`
   - **Handling:** Detect cycle, reject plan with error: "Circular dependency detected: T1 → T2 → T1"

2. **Missing dependency annotation** — tasks share files but no `depends_on`
   - **Handling:** File conflict detection adds implicit dependency, prints warning

3. **Agent crashes mid-parallel** — one of 4 parallel Agents fails
   - **Handling:** Other 3 continue, failed Agent error reported with task ID, session not blocked

4. **Rate limit hit** — >4 parallel Agents hit API rate limit
   - **Handling:** Backoff + retry, reduce parallelism to 2, print warning

5. **Shared read-only state** — multiple tasks read same config file
   - **Handling:** Safe, no conflict (read-only doesn't trigger serialization)

---

## Dependency Note

This spec depends on:
- **`async-skills-background-execution-design.md`** — if that spec converts "Fork Skill" to Agent + background, this spec's "Fork" terminology fix becomes moot (already done)

---

## Success Metrics

- **No write conflicts** — file conflict detection prevents data loss
- **Faster execution** — parallel-by-default reduces session time for independent tasks
- **Clear documentation** — users know when/how to use parallel execution
- **No regressions** — existing plans without `depends_on` still work
