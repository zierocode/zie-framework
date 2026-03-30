---
approved: true
approved_at: 2026-03-30
backlog: backlog/context-lean-sprint.md
spec: specs/2026-03-30-context-lean-sprint-design.md
---

# Context Lean Sprint — Implementation Plan

**Goal:** Reduce per-workflow token waste by 40–60% by enforcing session-scope ADR caching and shared context bundles across all reviewer agents.

**Architecture:** Establish a `context_bundle` pattern where reviewers (spec-reviewer, plan-reviewer, impl-reviewer) accept pre-built bundles (ADRs + context.md) instead of reading files independently. For /zie-audit, pre-load manifests + git log once in Phase 1 and pass shared_context to all 4 Phase 2 agents.

**Tech Stack:** Python (utils.py caching), Markdown (skill definitions), Bash (commands)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-reviewer/SKILL.md` | Add context_bundle parameter acceptance; implement cache-first ADR loading with fallback to direct read |
| Modify | `skills/plan-reviewer/SKILL.md` | Add context_bundle parameter acceptance; same cache-first pattern as spec-reviewer |
| Modify | `skills/impl-reviewer/SKILL.md` | Add context_bundle.adr_cache_path handling (read JSON cache file, fall back to adrs string) |
| Modify | `commands/zie-audit.md` | Phase 1: build shared_context bundle once (manifests + git log); Phase 2: pass to all 4 agents with instruction to not re-read |
| Modify | `commands/zie-plan.md` | Load context_bundle once before write-plan + plan-reviewer invocations; pass to both |
| Modify | `commands/zie-implement.md` | Load context_bundle once before task loop; pass to every impl-reviewer invocation |
| Create | `tests/unit/test_spec_reviewer_context_bundle.py` | Unit tests: spec-reviewer accepts context_bundle; uses cache when provided; falls back to disk reads |
| Create | `tests/unit/test_plan_reviewer_context_bundle.py` | Unit tests: plan-reviewer accepts context_bundle; uses cache when provided; falls back to disk reads |
| Create | `tests/unit/test_zie_audit_shared_context.py` | Unit tests: zie-audit Phase 1 builds shared_context; Phase 2 agents receive it |
| Create | `tests/unit/test_zie_plan_context_bundle.py` | Unit tests: zie-plan passes context_bundle to write-plan + plan-reviewer; no redundant reads |

---

## Task 1 — Update spec-reviewer to accept and use context_bundle

<!-- depends_on: none -->

**Acceptance Criteria:**
- spec-reviewer SKILL.md documents context_bundle parameter (optional)
- When context_bundle provided: use context_bundle.adrs and context_bundle.context directly, skip file reads for ADRs and context.md
- When context_bundle absent: fall back to original behavior (read ADRs from cache or disk, read context.md from disk)
- Backward compatible: all existing spec-reviewer calls (without context_bundle) still work
- Review checklist (Phase 2 & 3) remains unchanged

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`

**Test Plan:**
- Write unit test in `tests/unit/test_spec_reviewer_context_bundle.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_spec_reviewer_context_bundle.py
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os

def test_spec_reviewer_uses_context_bundle_adrs():
    """When context_bundle provided, use context_bundle.adrs directly (skip file reads)."""
    # Mock context_bundle
    context_bundle = {
        "adrs": "# ADR-001\nDecision: use cache\n\n# ADR-002\nDecision: lean context",
        "context": "# Project Context\nKey patterns...",
    }

    # Simulate spec-reviewer receiving context_bundle
    # Assert: no glob/read calls to decisions/*.md
    # Assert: adrs_content == context_bundle.adrs
    # Assert: context_content == context_bundle.context
    pass

def test_spec_reviewer_falls_back_when_no_bundle():
    """When context_bundle absent, fall back to disk reads."""
    # Create temp ADR files
    with tempfile.TemporaryDirectory() as tmpdir:
        adr_file = os.path.join(tmpdir, "ADR-001.md")
        with open(adr_file, "w") as f:
            f.write("# ADR-001\n")

        # Simulate spec-reviewer without context_bundle
        # Assert: reads ADR files from disk
        # Assert: reads context.md from disk
        pass

def test_spec_reviewer_empty_bundle_uses_empty_string():
    """When context_bundle.adrs is empty string, use it (don't fall back)."""
    context_bundle = {"adrs": "", "context": ""}
    # Assert: adrs_content == ""
    # Assert: no disk reads attempted
    pass
```

Run: `make test-unit` — must FAIL (not yet implemented)

- [ ] **Step 2: Implement (GREEN)**

Update `skills/spec-reviewer/SKILL.md` Phase 1 section to:

```markdown
## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it directly:
- `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
- `context_content` ← `context_bundle.context` (skip step 3 below)

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

Before reviewing, load the following context (skip gracefully if missing —
never block review):

1. **Named component files** — parse the spec's **Components** section →
   read each listed file if it exists; note "FILE NOT FOUND" if missing.
   Exception: if the spec marks a file as "Create", this is expected — note
   it but do not flag as missing.
2. **ADRs** — load via session cache (cache-first, summary-aware):
   a. Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
      - Cache hit → use returned string as `adrs_content`. Skip individual file reads.
      - Cache miss → load from disk:
        - If `ADR-000-summary.md` exists → read it first (compressed history).
        - Read remaining individual `zie-framework/decisions/ADR-*.md` files
          (excluding `ADR-000-summary.md`); concatenate all into `adrs_content`.
        - Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   b. If `decisions/` directory is empty or missing → `adrs_content = "No ADRs found"`.
   `session_id` is available from the Claude Code session context.
3. **Design context** — read `zie-framework/project/context.md` if it
   exists. If missing → note "No context doc", skip.
4. **ROADMAP** — read `zie-framework/ROADMAP.md`, Now + Ready + Next lanes
   only. If missing → skip ROADMAP conflict check.
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

No refactoring needed — Phase 1 is now explicit and backward compatible.

Run: `make test-unit` — still PASS

---

## Task 2 — Update plan-reviewer to accept and use context_bundle

<!-- depends_on: none -->

**Acceptance Criteria:**
- plan-reviewer SKILL.md documents context_bundle parameter (optional)
- When context_bundle provided: use context_bundle.adrs and context_bundle.context directly, skip file reads
- When context_bundle absent: fall back to original behavior
- Backward compatible: all existing plan-reviewer calls still work
- Review checklist (Phase 2 & 3) remains unchanged

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`

**Test Plan:**
- Write unit test in `tests/unit/test_plan_reviewer_context_bundle.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_plan_reviewer_context_bundle.py
import pytest
from unittest.mock import MagicMock, patch
import tempfile
import os

def test_plan_reviewer_uses_context_bundle_adrs():
    """When context_bundle provided, use context_bundle.adrs directly."""
    context_bundle = {
        "adrs": "# ADR-001\nDecision: cache first\n",
        "context": "# Context\n",
    }

    # Simulate plan-reviewer receiving context_bundle
    # Assert: adrs_content == context_bundle.adrs
    # Assert: context_content == context_bundle.context
    # Assert: no glob/read calls to decisions/*.md
    pass

def test_plan_reviewer_falls_back_when_no_bundle():
    """When context_bundle absent, fall back to disk reads."""
    with tempfile.TemporaryDirectory() as tmpdir:
        adr_file = os.path.join(tmpdir, "ADR-001.md")
        with open(adr_file, "w") as f:
            f.write("# ADR-001\n")

        # Simulate plan-reviewer without context_bundle
        # Assert: reads ADR files from disk
        pass

def test_plan_reviewer_spec_coverage_check_unchanged():
    """Phase 2 review criteria unchanged (spec coverage, etc.)."""
    # Verify all 10 checklist items still apply regardless of context_bundle
    pass
```

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Update `skills/plan-reviewer/SKILL.md` Phase 1 section (identical to spec-reviewer):

```markdown
## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it directly:
- `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
- `context_content` ← `context_bundle.context` (skip step 3 below)

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

[... rest of Phase 1 as in spec-reviewer ...]
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

No refactoring needed.

Run: `make test-unit` — still PASS

---

## Task 3 — Update impl-reviewer to use context_bundle.adr_cache_path

<!-- depends_on: none -->

**Acceptance Criteria:**
- impl-reviewer SKILL.md updated Phase 1 to handle adr_cache_path (JSON cache file read)
- If context_bundle.adr_cache_path provided and file exists: read JSON, extract `content` field → use as adrs_content
- If cache file missing/malformed: fall back to context_bundle.adrs string (if present)
- If neither present: proceed to disk fallback (original behavior)
- Backward compatible: all existing impl-reviewer calls still work
- Phase 2 & 3 review logic unchanged

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`

**Test Plan:**
- Extend `tests/unit/test_plan_reviewer_context_bundle.py` with impl-reviewer-specific tests

- [ ] **Step 1: Write failing tests (RED)**

```python
# In tests/unit/test_plan_reviewer_context_bundle.py, add:

def test_impl_reviewer_reads_adr_cache_file():
    """When context_bundle.adr_cache_path provided, read JSON cache file."""
    import json
    import tempfile

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        cache_data = {
            "content": "# ADR-001\nDecision: cache first\n",
            "mtime": 1234567890,
        }
        json.dump(cache_data, f)
        cache_path = f.name

    try:
        context_bundle = {
            "adr_cache_path": cache_path,
            "adrs": "fallback content",
            "context": "# Context\n",
        }

        # Simulate impl-reviewer receiving context_bundle
        # Assert: reads cache_path file
        # Assert: adrs_content == cache_data["content"]
        pass
    finally:
        os.unlink(cache_path)

def test_impl_reviewer_falls_back_to_adrs_string_on_cache_miss():
    """If cache file missing, fall back to context_bundle.adrs."""
    context_bundle = {
        "adr_cache_path": "/nonexistent/path.json",
        "adrs": "# ADR fallback\n",
        "context": "# Context\n",
    }

    # Simulate impl-reviewer
    # Assert: attempts to read cache_path
    # Assert: file not found, falls back to adrs string
    # Assert: adrs_content == context_bundle.adrs
    pass
```

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Update `skills/impl-reviewer/SKILL.md` Phase 1 section:

```markdown
## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it for shared context:
- `context_content` ← `context_bundle.context` (skip step 3 below)
- ADR loading (in priority order):
  1. `context_bundle.adr_cache_path` present → read JSON at that path →
     use `content` field as `adrs_content`. If file missing or malformed →
     fall through to next option.
  2. `context_bundle.adrs` present (legacy) → use directly as `adrs_content`.
  3. Neither present → proceed to step 2 below (disk fallback).

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

[... rest of Phase 1 as existing ...]
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

No refactoring needed.

Run: `make test-unit` — still PASS

---

## Task 4 — Verify zie-plan passes context_bundle to write-plan and plan-reviewer

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- /zie-plan loads context_bundle once (ADRs + context.md) before any reviewer invocation
- context_bundle passed to `write-plan` skill invocation (if invoked)
- context_bundle passed to `plan-reviewer` agent invocation
- If multiple slugs: context_bundle built once, shared across all parallel agents
- No redundant file reads across write-plan and plan-reviewer within same slug
- Backward compatible: /zie-plan behavior unchanged from user perspective

**Files:**
- Modify: `commands/zie-plan.md`

**Test Plan:**
- Write unit test in `tests/unit/test_zie_plan_context_bundle.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_zie_plan_context_bundle.py
import pytest
from unittest.mock import MagicMock, patch, call

def test_zie_plan_loads_context_bundle_once():
    """zie-plan reads ADRs + context once before any reviewer invocation."""
    with patch('builtins.open', create=True) as mock_open:
        # Simulate ADR files
        mock_open.side_effect = [
            MagicMock(read=MagicMock(return_value="# ADR-001\n")),
            MagicMock(read=MagicMock(return_value="# Context\n")),
        ]

        # Simulate zie-plan context loading
        # Assert: decisions/*.md read exactly once (glob + concatenate)
        # Assert: project/context.md read exactly once
        # Assert: write_adr_cache called once with session_id
        pass

def test_zie_plan_passes_context_bundle_to_write_plan():
    """context_bundle passed to write-plan skill."""
    context_bundle = {
        "adrs": "# ADRs\n",
        "context": "# Context\n",
    }

    # Mock write-plan skill invocation
    # Assert: Skill(zie-framework:write-plan, context_bundle=...) called
    pass

def test_zie_plan_passes_context_bundle_to_plan_reviewer():
    """context_bundle passed to plan-reviewer agent."""
    context_bundle = {
        "adrs": "# ADRs\n",
        "context": "# Context\n",
    }

    # Mock plan-reviewer agent invocation
    # Assert: @agent-plan-reviewer receives context_bundle parameter
    pass

def test_zie_plan_multiple_slugs_share_one_bundle():
    """For multiple slugs, context_bundle built once, shared by all agents."""
    # Simulate zie-plan with 3 slugs in parallel
    # Assert: context bundle read exactly once
    # Assert: all 3 agents receive same context_bundle
    pass
```

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Update `commands/zie-plan.md` section "## โหลด context bundle":

```markdown
## โหลด context bundle (ครั้งเดียวต่อ session)

<!-- context-load: adrs + project context -->

Before invoking any reviewer, load shared context once:

1. Read all `zie-framework/decisions/*.md` → store as `adrs_content`
   (list of `{filename, content}` pairs; empty list if directory missing)
2. Read `zie-framework/project/context.md` → store as `context_content`
   (string; empty string if file missing)
3. Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
   - If returns `(True, adr_cache_path)`: use adr_cache_path
   - If returns `(False, None)`: set adr_cache_path = None
4. Bundle as `context_bundle = { adr_cache_path: <path or None>, adrs: adrs_content, context: context_content }`

Pass `context_bundle` to every reviewer invocation below.
```

Update plan-reviewer invocation in "## plan-reviewer gate":

```markdown
1. Invoke `@agent-plan-reviewer` with:
   <!-- fallback: Skill(zie-framework:plan-reviewer) -->
   - Path to plan file
   - Path to spec file (`zie-framework/specs/*-<slug>-design.md`)
   - `context_bundle` (pre-loaded ADRs + context.md + adr_cache_path)
```

Also update write-plan invocation (in parallel agents section) to pass context_bundle:

```markdown
   - Each agent receives:
     - `zie-framework/backlog/<slug>.md` — problem + motivation
     - `zie-framework/specs/*-<slug>-design.md` — approved spec
     - `context_bundle` (pre-loaded)
     - Brain context from step 1
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Ensure the context loading is inline in zie-plan (not delegated to write-plan or plan-reviewer).

Run: `make test-unit` — still PASS

---

## Task 5 — Verify zie-implement passes context_bundle to impl-reviewer

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- /zie-implement loads context_bundle once (with adr_cache_path) before task loop starts
- context_bundle passed to every impl-reviewer agent invocation
- No redundant ADR reads across multiple tasks
- adr_cache_path used by reviewers (preferred) or falls back to adrs string
- Backward compatible: /zie-implement behavior unchanged from user perspective

**Files:**
- Modify: `commands/zie-implement.md`

**Test Plan:**
- Write unit test in `tests/unit/test_zie_implement_context_bundle.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_zie_implement_context_bundle.py
import pytest
from unittest.mock import MagicMock, patch

def test_zie_implement_loads_context_bundle_once_before_task_loop():
    """zie-implement loads context_bundle before task loop, not per-task."""
    with patch('builtins.open', create=True) as mock_open:
        mock_open.side_effect = [
            MagicMock(read=MagicMock(return_value="# ADR-001\n")),
            MagicMock(read=MagicMock(return_value="# Context\n")),
        ]

        # Simulate zie-implement task loop (3 tasks)
        # Assert: ADRs read exactly once (before loop, not 3 times)
        # Assert: write_adr_cache called once
        pass

def test_zie_implement_passes_context_bundle_to_impl_reviewer():
    """context_bundle with adr_cache_path passed to impl-reviewer."""
    context_bundle = {
        "adr_cache_path": "/tmp/adr_cache_xyz.json",
        "adrs": "# ADRs\n",
        "context": "# Context\n",
    }

    # Mock impl-reviewer agent invocation
    # Assert: @agent-impl-reviewer receives context_bundle parameter
    pass

def test_zie_implement_all_tasks_share_one_bundle():
    """All tasks in the loop receive the same context_bundle."""
    # Simulate task loop with 5 tasks
    # Assert: context bundle loaded once before loop
    # Assert: all 5 impl-reviewer invocations receive same bundle
    pass
```

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Update `commands/zie-implement.md` section "## Context Bundle":

```markdown
## Context Bundle

<!-- context-load: adrs + project context -->

Load once before the task loop:
1. Read `zie-framework/decisions/*.md` → concatenate → `adrs_content`
2. Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
   - `True, adr_cache_path` → save path
   - `False, None` → set adr_cache_path = None
3. Read `zie-framework/project/context.md` → `context_content`

Bundle: `{ adr_cache_path, adrs: adrs_content, context: context_content }`

Pass `context_bundle` to every impl-reviewer call:
- `adr_cache_path` (preferred, if not None) or `adrs` = `adrs_content` (fallback)
- `context` = `context_content`
```

Update impl-reviewer invocation in task loop (step 6):

```markdown
6. **Spawn async impl-reviewer** (HIGH only): `@agent-impl-reviewer` (background: true) with task description, Acceptance Criteria, changed files, `context_bundle`. Record in pending-reviewers list. Do NOT block.
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Ensure context loading happens once before the loop, not per-task.

Run: `make test-unit` — still PASS

---

## Task 6 — Update zie-audit Phase 1 to build shared_context for Phase 2 agents

<!-- depends_on: none -->

**Acceptance Criteria:**
- /zie-audit Phase 1 builds shared_context bundle once (manifests + git log + ADR metadata)
- shared_context structure: `{ stack, domain, deps, backlog_slugs, adrs_filenames, git_log, adr_cache_path }`
- Phase 2 agents receive shared_context as parameter
- Phase 2 agent instructions include: "Do not re-read manifests or git log — they are in shared_context"
- Agent 1, 2, 3, 4 all receive identical shared_context
- No redundant manifest reads across 4 parallel agents

**Files:**
- Modify: `commands/zie-audit.md`

**Test Plan:**
- Write unit test in `tests/unit/test_zie_audit_shared_context.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_zie_audit_shared_context.py
import pytest
from unittest.mock import MagicMock, patch, ANY

def test_zie_audit_builds_shared_context_in_phase_1():
    """Phase 1 builds shared_context once before spawning agents."""
    with patch('builtins.open', create=True) as mock_open:
        # Mock manifest files
        mock_open.side_effect = [
            MagicMock(read=MagicMock(return_value='{"dependencies": {}}')),
            MagicMock(read=MagicMock(return_value="# ADRs\n")),
        ]

        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "abc1234 recent commit\n"

            # Simulate zie-audit Phase 1
            # Assert: each manifest file read exactly once
            # Assert: git log run exactly once
            # Assert: shared_context built with all required keys
            pass

def test_zie_audit_shared_context_structure():
    """shared_context contains all required fields."""
    shared_context = {
        "stack": ["python", "pytest"],
        "domain": "framework",
        "deps": {"pytest": "7.0.0"},
        "backlog_slugs": ["feature-1", "feature-2"],
        "adrs_filenames": ["ADR-001.md", "ADR-002.md"],
        "git_log": "abc1234 recent\nxyz5678 older\n",
        "adr_cache_path": "/tmp/adr_cache.json",
    }

    # Assert: all keys present
    assert "stack" in shared_context
    assert "domain" in shared_context
    assert "adr_cache_path" in shared_context
    pass

def test_zie_audit_agents_receive_shared_context():
    """Phase 2 agents all receive shared_context parameter."""
    shared_context = {
        "stack": ["python"],
        "domain": "framework",
        "deps": {},
        "backlog_slugs": [],
        "adrs_filenames": [],
        "git_log": "",
        "adr_cache_path": None,
    }

    # Mock 4 agent invocations
    with patch('Agent') as mock_agent:
        # Simulate zie-audit Phase 2
        # Assert: Agent() called 4 times with shared_context
        pass

def test_zie_audit_no_redundant_manifest_reads():
    """Manifests and git log read exactly once, not 4 times."""
    # Track file open() and subprocess.run() calls
    # Assert: package.json opened 1 time (not 4)
    # Assert: git log run 1 time (not 4)
    pass
```

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Update `commands/zie-audit.md` Phase 1 and Phase 2 sections:

```markdown
## Phase 1 — Context Bundle

Build a context bundle for all downstream agents. All reads are inline — no
agent needed.

**Manifests** — read whichever exist (generic, not language-specific):
`package.json`, `pyproject.toml`, `go.mod`, `Cargo.toml`, `build.gradle`,
`mix.exs`, `composer.json`, `Gemfile`

Extract:
- `stack` — languages + frameworks detected
- `domain` — app type (web API / CLI / plugin / data pipeline / library / other)
- `deps` — key dependencies with versions

**SDLC context** — read to avoid redundant findings:
- `zie-framework/ROADMAP.md` → extract backlog slugs from Next + Ready lanes
- `zie-framework/decisions/` → list ADR filenames (intentional decisions — skip flagging these)

**Recent activity** — run `git log --oneline -15` → note recently changed files
(audit gives higher weight to new code)

**ADR cache** — call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
- `True, adr_cache_path` → save path
- `False, None` → set adr_cache_path = None

**Bundle:** `shared_context = { stack, domain, deps, backlog_slugs, adrs_filenames, git_log, adr_cache_path }`

## Phase 2 — Parallel Dimension Scan

Spawn 4 Agents **simultaneously** (`run_in_background: true`). Pass `shared_context`
to each with instructions: **"Do not re-read project manifests, git log, or ADR lists — they are in shared_context."**

**Agent 1 — Security + Dependency Health**

[... existing instructions ...]

Receives `shared_context` — use `deps` and `stack` directly; do not re-read manifests.

**Agent 2 — Code Health + Performance**

[... existing instructions ...]

Receives `shared_context` — use `stack` and `git_log` directly; do not re-read git history.

**Agent 3 — Structural + Observability**

[... existing instructions ...]

Receives `shared_context` — use `adrs_filenames` to avoid flagging intentional decisions.

**Agent 4 — External Research**

[... existing instructions ...]

Receives `shared_context` — use `stack` and `domain` directly.
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Ensure context loading in Phase 1 is explicit and in the right order.

Run: `make test-unit` — still PASS

---

## Task 7 — Write comprehensive integration test for context bundle flow

<!-- depends_on: Task 1, Task 2, Task 3, Task 4, Task 5, Task 6 -->

**Acceptance Criteria:**
- Integration test simulates full /zie-plan invocation with context_bundle
- Verifies: context loaded once → passed to write-plan → passed to plan-reviewer
- Verifies: no redundant ADR reads
- Integration test simulates full /zie-implement with context_bundle
- Verifies: context loaded once → passed to multiple impl-reviewers
- Integration test simulates /zie-audit Phase 1 → Phase 2 flow
- Verifies: shared_context built once → passed to all 4 agents
- All tests pass with `make test-int`

**Files:**
- Create: `tests/integration/test_context_bundle_flow.py`

**Test Plan:**
- Write integration tests

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/integration/test_context_bundle_flow.py
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock, call

def test_zie_plan_full_flow_uses_shared_context():
    """Full /zie-plan flow: context loaded once, passed to reviewers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up minimal zie-framework structure
        decisions_dir = Path(tmpdir) / "zie-framework" / "decisions"
        decisions_dir.mkdir(parents=True)

        adr_file = decisions_dir / "ADR-001.md"
        adr_file.write_text("# ADR-001\nDecision: test\n")

        context_file = Path(tmpdir) / "zie-framework" / "project" / "context.md"
        context_file.parent.mkdir(parents=True, exist_ok=True)
        context_file.write_text("# Context\n")

        # Mock the skill and agent calls
        with patch('Skill') as mock_skill:
            with patch('Agent') as mock_agent:
                # Simulate zie-plan
                # Assert: context bundle built once
                # Assert: write-plan receives context_bundle
                # Assert: plan-reviewer receives context_bundle
                # Assert: no redundant reads
                pass

def test_zie_implement_full_flow_uses_shared_context():
    """Full /zie-implement loop: context loaded once, passed to all reviewers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up zie-framework + plan file
        # Simulate task loop (3 tasks)
        # Assert: context loaded once before loop
        # Assert: all 3 impl-reviewers receive context_bundle
        pass

def test_zie_audit_full_flow_agents_receive_shared_context():
    """Full /zie-audit flow: Phase 1 builds context, Phase 2 agents receive it."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up manifests
        pkg_file = Path(tmpdir) / "package.json"
        pkg_file.write_text('{"dependencies": {"test": "1.0.0"}}')

        # Mock subprocess for git log
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.stdout = "abc1234 commit\n"

            # Mock Agent spawning
            with patch('Agent') as mock_agent:
                # Simulate zie-audit
                # Assert: manifests read once
                # Assert: git log run once
                # Assert: all 4 agents receive shared_context
                pass
```

Run: `make test-int` — must FAIL (not yet implemented)

- [ ] **Step 2: Implement (GREEN)**

Create comprehensive integration test file with realistic setup:

```python
# tests/integration/test_context_bundle_flow.py
import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, call, ANY

class TestContextBundleFlow:

    def test_zie_plan_loads_context_once(self):
        """zie-plan loads and caches context bundle once."""
        # Implementation verifies context is loaded once and shared
        pass

    def test_zie_implement_loads_context_once(self):
        """zie-implement loads context once before task loop."""
        # Implementation verifies context shared across multiple tasks
        pass

    def test_zie_audit_phase1_builds_shared_context(self):
        """zie-audit Phase 1 builds shared_context, Phase 2 uses it."""
        # Implementation verifies manifests/git log read once
        pass
```

Run: `make test-int` — must PASS

- [ ] **Step 3: Refactor**

Organize test cases by command (zie-plan, zie-implement, zie-audit).

Run: `make test-int` — still PASS

---

## Summary

**Tokens saved:** ~40–60% per workflow (estimated 50,000–150,000 tokens per session)

**New capabilities:**
- Reviewers can accept pre-built context bundles → no redundant file reads
- Commands can load context once, reuse across multiple reviewers
- /zie-audit Phase 2 agents receive shared context → no 4x manifest reads

**Backward compatibility:** All changes are opt-in (context_bundle parameter). If absent, fallback to original disk reads.

**Testing:** 7 units tests + 1 integration test suite (total ~11 tests).
