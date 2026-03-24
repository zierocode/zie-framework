---
approved: false
approved_at: ~
backlog: backlog/async-skills-background-execution.md
priority: HIGH
spec_type: design
---

# Async Skills: Background Execution for Long-Running Operations

**Problem:** Commands like `/zie-retro` and `/zie-release` invoke `Skill()` calls that block for 1-3 minutes with no progress visibility. The "Fork Skill" pattern (calling multiple Skills simultaneously) still runs sequentially in foreground — user sees nothing until all complete.

**Goal:** Convert long-running Skill invocations to `Agent(subagent_type, run_in_background=true)` with `TaskCreate` progress tracking, while keeping Skill tool for short operations (<30s).

**Architecture:**
- **Skill tool** — foreground, immediate result needed (verify, debug, tdd-loop)
- **Agent tool + background** — long operations (retro-format, docs-sync-check, reviewer agents)
- **TaskCreate** — progress visibility for any operation >30s expected

**Tech Stack:** Python 3.x, Claude Code Agent tool, TaskCreate/TaskUpdate tools

---

## Context

### Current State

**zie-retro.md** (lines 83-84):
```markdown
1. Fork `Skill(zie-framework:retro-format)` — pass compact summary as `$ARGUMENTS`
2. Fork `Skill(zie-framework:docs-sync-check)` — pass output of `git diff --name-only`
```

Both Skills run in foreground. User waits 1-3 minutes with no feedback.

**zie-release.md** (line 90):
```markdown
1. Fork `Skill(zie-framework:docs-sync-check)` with changed files
```

Runs in foreground after Gate 1. User waits at "Quality Checks" step.

**zie-implement.md** (line 238):
```markdown
Fork `Skill(zie-framework:verify)` with captured output
```

Runs in foreground at end of session.

### Skill vs Agent Comparison

| Feature | Skill tool | Agent tool + `run_in_background` |
|---------|------------|----------------------------------|
| **Async** | ❌ foreground only — block จนกว่า skill จะเสร็จ | ✅ true background — return ทันที |
| **Output** | แสดงใน chat โดยตรง | เขียนลง output file + notify เมื่อเสร็จ |
| **Use case** | skill ที่ต้องรอ result ทันที | agent ที่ทำงานนานๆ โดยไม่ block |

---

## Requirements

### Functional

1. **Convert `/zie-retro` long-running Skills to Agent + background:**
   - `retro-format` → `Agent(subagent_type="zie-framework:retro-format", run_in_background=true)`
   - `docs-sync-check` → `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=true)`

2. **Add TaskCreate progress tracking:**
   - Before each background Agent starts: create task with clear description
   - When Agent completes: update task to "completed"
   - User sees progress in real-time via task list

3. **Convert `/zie-release` docs-sync-check:**
   - Same pattern as `/zie-retro`

4. **Preserve Skill tool for short operations:**
   - `verify`, `debug`, `tdd-loop`, `test-pyramid` remain as Skill calls
   - These are expected to complete in <30s

5. **Graceful degradation:**
   - If Agent subagent_type not found: fall back to Skill() inline call
   - If TaskCreate unavailable: continue without progress tracking

### Non-Functional

1. **No breaking changes** — existing command behavior preserved, only execution mode changes
2. **Backward compatible** — works with Claude Code versions that may not support Agent tool
3. **Progress visible** — user always knows what's running and what completed
4. **No silent failures** — if background Agent fails, error is reported clearly

---

## Design

### File Changes

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/zie-retro.md` | Convert retro-format + docs-sync-check to Agent + background + TaskCreate |
| Modify | `commands/zie-release.md` | Convert docs-sync-check to Agent + background + TaskCreate |
| Modify | `commands/zie-implement.md` | Add TaskCreate for verify step (keep as Skill) |
| Create | `agents/retro-format.md` | Agent wrapper for retro-format skill (optional, for consistency) |
| Create | `agents/docs-sync-check.md` | Agent wrapper for docs-sync-check skill (optional, for consistency) |
| Modify | `tests/unit/test_async_skills.py` | Test that Agent invocations are present, TaskCreate patterns correct |

### Agent Wrapper Pattern (Optional)

For consistency with existing reviewer agents (`agents/spec-reviewer.md`, etc.), create wrapper agents:

**`agents/retro-format.md`:**
```markdown
# @agent-retro-format — Retro Format Agent

Invokes `Skill(zie-framework:retro-format)` with background execution support.

## Usage

```python
Agent(
    subagent_type="zie-framework:retro-format",
    run_in_background=True,
    prompt="Format retrospective summary from: {compact_json}"
)
```

## Fallback

If agent not found, caller falls back to:
```python
Skill(zie-framework:retro-format)
```
```

**`agents/docs-sync-check.md`:**
```markdown
# @agent-docs-sync-check — Docs Sync Check Agent

Invokes `Skill(zie-framework:docs-sync-check)` with background execution support.

## Usage

```python
Agent(
    subagent_type="zie-framework:docs-sync-check",
    run_in_background=True,
    prompt="Check docs sync for changed files: {changed_files}"
)
```

## Fallback

If agent not found, caller falls back to:
```python
Skill(zie-framework:docs-sync-check)
```
```

### Command Modifications

#### `/zie-retro` (zie-retro.md)

**Current (lines 83-84):**
```markdown
1. Fork `Skill(zie-framework:retro-format)` — pass compact summary as `$ARGUMENTS`
2. Fork `Skill(zie-framework:docs-sync-check)` — pass output of `git diff --name-only`
```

**New:**
```markdown
1. **TaskCreate** — "Format retrospective summary"
2. **TaskCreate** — "Check docs sync for changed files"

3. Invoke both Agents **simultaneously** with `run_in_background=true`:
   - `Agent(subagent_type="zie-framework:retro-format", run_in_background=True, prompt=...)`
   - `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True, prompt=...)`

4. Print: "Running retro-format and docs-sync-check in background. Use /tasks to see progress."

5. Wait for both Agents to complete (poll via TaskOutput or wait for task notifications).

6. **TaskUpdate** — mark both tasks as "completed" when Agents finish.

7. Collect results and continue to "บันทึก ADRs" step.
```

**Fallback comment:**
```markdown
<!-- fallback: if Agent tool unavailable or subagent_type not found,
     call Skill(zie-framework:retro-format) and Skill(zie-framework:docs-sync-check) inline -->
```

#### `/zie-release` (zie-release.md)

**Current (line 90):**
```markdown
1. Fork `Skill(zie-framework:docs-sync-check)` with changed files
```

**New:**
```markdown
1. **TaskCreate** — "Check docs sync for changed files"

2. Invoke Agent with `run_in_background=true`:
   - `Agent(subagent_type="zie-framework:docs-sync-check", run_in_background=True, prompt=...)`

3. Print: "Running docs-sync-check in background. Use /tasks to see progress."

4. Continue to Gate 2/3 while Agent runs.

5. **TaskUpdate** — mark task as "completed" when Agent finishes.

6. Collect results in "รวมผลลัพธ์ Quality Forks" step.
```

#### `/zie-implement` (zie-implement.md)

**Current (line 238):**
```markdown
Fork `Skill(zie-framework:verify)` with captured output
```

**New:**
```markdown
1. **TaskCreate** — "Pre-ship verification"

2. Invoke `Skill(zie-framework:verify)` inline (expected <30s).

3. **TaskUpdate** — mark task as "completed" when verify finishes.
```

**Rationale:** `verify` is expected to complete quickly (<30s), so keep as Skill but add TaskCreate for visibility.

### TaskCreate Pattern

Each long-running operation gets a task:

```python
TaskCreate(
    subject="Format retrospective summary",
    description="Run retro-format skill to structure retro output into 5 sections",
    activeForm="Formatting retro summary"
)
```

When Agent completes:

```python
TaskUpdate(
    taskId="<task_id_from_create>",
    status="completed"
)
```

### Test Plan

**New file: `tests/unit/test_async_skills.py`**

```python
class TestAsyncSkillPatterns:
    def test_zie_retro_uses_agent_background(self):
        """zie-retro.md must use Agent + run_in_background for retro-format and docs-sync-check."""
        text = (REPO_ROOT / "commands" / "zie-retro.md").read_text()
        assert 'Agent(subagent_type="zie-framework:retro-format"' in text or \
               '@agent-retro-format' in text
        assert 'run_in_background' in text
        assert "TaskCreate" in text  # progress tracking present

    def test_zie_release_uses_agent_background(self):
        """zie-release.md must use Agent + run_in_background for docs-sync-check."""
        text = (REPO_ROOT / "commands" / "zie-release.md").read_text()
        assert 'Agent(subagent_type="zie-framework:docs-sync-check"' in text or \
               '@agent-docs-sync-check' in text
        assert 'run_in_background' in text
        assert "TaskCreate" in text

    def test_zie_implement_uses_taskcreate_for_verify(self):
        """zie-implement.md must use TaskCreate for verify step."""
        text = (REPO_ROOT / "commands" / "zie-implement.md").read_text()
        assert "TaskCreate" in text
        assert "verify" in text.lower()
        # Skill call should still be present (not converted to Agent)
        assert 'Skill(zie-framework:verify)' in text

    def test_fallback_comments_present(self):
        """Fallback comments must be present for graceful degradation."""
        retro = (REPO_ROOT / "commands" / "zie-retro.md").read_text()
        assert "<!-- fallback:" in retro and "Skill(zie-framework:retro-format)" in retro

        release = (REPO_ROOT / "commands" / "zie-release.md").read_text()
        assert "<!-- fallback:" in release and "Skill(zie-framework:docs-sync-check)" in release
```

---

## Out of Scope

1. **Converting all Skill calls to Agent** — only long-running operations (>1min expected) are converted
2. **Changing Skill behavior** — Skills themselves are unchanged, only how they're invoked
3. **New Skills or Agents** — no new functionality, only execution mode change
4. **zie-memory integration changes** — memory calls within Skills remain unchanged

---

## Acceptance Criteria

- [ ] `commands/zie-retro.md` uses `Agent + run_in_background` for `retro-format` and `docs-sync-check`
- [ ] `commands/zie-retro.md` uses `TaskCreate` before each background Agent
- [ ] `commands/zie-release.md` uses `Agent + run_in_background` for `docs-sync-check`
- [ ] `commands/zie-release.md` uses `TaskCreate` before background Agent
- [ ] `commands/zie-implement.md` uses `TaskCreate` for verify step (Skill remains inline)
- [ ] Fallback comments present in all modified files
- [ ] `tests/unit/test_async_skills.py` created with 4 test methods
- [ ] All tests pass: `make test-unit` exits 0
- [ ] Optional: `agents/retro-format.md` and `agents/docs-sync-check.md` created with wrapper pattern

---

## Edge Cases

1. **Agent subagent_type not found** — fallback to inline Skill() call with warning printed
2. **Agent tool unavailable** — fallback to inline Skill() call (older Claude Code version)
3. **TaskCreate unavailable** — continue without progress tracking (non-critical)
4. **Agent crashes mid-execution** — TaskOutput returns error, TaskUpdate marks as "failed" with error message
5. **User interrupts session while Agent running** — Agent continues in background, output file written but user may not see result

---

## Dependency Note

This spec depends on:
- **Agent tool availability** — Claude Code must support `Agent(subagent_type, run_in_background)`
- **TaskCreate/TaskUpdate tools** — must be available for progress tracking

If either is unavailable in the target environment, the fallback comments ensure graceful degradation.

---

## Success Metrics

- **User-visible progress** — task list shows what's running during retro/release
- **Reduced perceived wait time** — user can see other work while Agents run
- **No regressions** — existing tests pass, command behavior unchanged
- **Backward compatible** — works with/without Agent tool support
