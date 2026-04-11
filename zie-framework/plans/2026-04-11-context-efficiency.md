---
approved: true
approved_at: 2026-04-11
backlog:
spec: zie-framework/specs/2026-04-11-context-efficiency-design.md
---

# Context Efficiency — Implementation Plan

> **Implementation:** Run via `claude --agent zie-framework:zie-implement-mode`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut token waste in three places: (A) add FAST PATH headers to 4 reviewer skills so simple reviews skip loading full content; (B) cache the first SubagentStart inject per session so repeated subagent spawns don't re-inject the same project state; (C) replace the blunt Explore/Plan-only guard in `subagent-context.py` with a per-agent budget table.

**Architecture:** Four SKILL.md files get a `<!-- FAST PATH -->` block prepended. `subagent-context.py` gains a session flag check (flag at `project_tmp_path("session-context", project)`) and a `AGENT_BUDGETS` dispatch table that replaces the `re.search(r'Explore|Plan', agent_type)` early-exit (ADR-046 superseded). `session-cleanup.py` is extended to explicitly unlink the cache flag via `unlink(missing_ok=True)` (the glob already catches it, but the spec requires an explicit call).

**Tech Stack:** Python 3.x, Markdown, pytest.

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `skills/spec-reviewer/SKILL.md` | Add FAST PATH header (≤120 tokens) |
| Modify | `skills/plan-reviewer/SKILL.md` | Add FAST PATH header (≤120 tokens) |
| Modify | `skills/impl-reviewer/SKILL.md` | Add FAST PATH header (≤80 tokens) |
| Modify | `skills/load-context/SKILL.md` | Add FAST PATH header (≤60 tokens) |
| Modify | `hooks/subagent-context.py` | Session cache check + per-agent budget table |
| Modify | `hooks/session-cleanup.py` | Explicitly unlink session-context cache flag |
| Create | `tests/unit/test_context_efficiency.py` | All context-efficiency tests |

---

### Task 1: Tests for FAST PATH presence in skill files

**Files:**
- Create: `tests/unit/test_context_efficiency.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for context efficiency improvements (Area 2)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOKS_DIR = REPO_ROOT / "hooks"

# ── FAST PATH token budget ────────────────────────────────────────────────────
# Rough token estimate: 1 token ≈ 4 chars for English prose.
# These thresholds are generous to avoid false failures from minor content edits.
FAST_PATH_BUDGETS = {
    "spec-reviewer": 600,   # ≤120 tokens ≈ 480 chars; 600 gives 25% margin
    "plan-reviewer": 600,
    "impl-reviewer": 400,   # ≤80 tokens ≈ 320 chars; 400 gives 25% margin
    "load-context":  300,   # ≤60 tokens ≈ 240 chars; 300 gives 25% margin
}


class TestFastPathPresent:
    """FAST PATH block exists in each qualifying skill file."""

    def _fast_path_block(self, skill_name: str) -> str:
        path = REPO_ROOT / "skills" / skill_name / "SKILL.md"
        assert path.exists(), f"skills/{skill_name}/SKILL.md must exist"
        content = path.read_text()
        marker = "<!-- FAST PATH -->"
        assert marker in content, (
            f"skills/{skill_name}/SKILL.md must contain '<!-- FAST PATH -->' marker"
        )
        # Extract text between FAST PATH and DETAIL markers
        parts = content.split(marker, 1)
        if len(parts) < 2:
            return ""
        detail_marker = "<!-- DETAIL"
        fast_section = parts[1].split(detail_marker, 1)[0]
        return fast_section

    def test_spec_reviewer_has_fast_path(self):
        block = self._fast_path_block("spec-reviewer")
        assert len(block) > 0

    def test_plan_reviewer_has_fast_path(self):
        block = self._fast_path_block("plan-reviewer")
        assert len(block) > 0

    def test_impl_reviewer_has_fast_path(self):
        block = self._fast_path_block("impl-reviewer")
        assert len(block) > 0

    def test_load_context_has_fast_path(self):
        block = self._fast_path_block("load-context")
        assert len(block) > 0

    def test_spec_reviewer_fast_path_under_budget(self):
        block = self._fast_path_block("spec-reviewer")
        assert len(block) <= FAST_PATH_BUDGETS["spec-reviewer"], (
            f"spec-reviewer FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['spec-reviewer']}"
        )

    def test_plan_reviewer_fast_path_under_budget(self):
        block = self._fast_path_block("plan-reviewer")
        assert len(block) <= FAST_PATH_BUDGETS["plan-reviewer"], (
            f"plan-reviewer FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['plan-reviewer']}"
        )

    def test_impl_reviewer_fast_path_under_budget(self):
        block = self._fast_path_block("impl-reviewer")
        assert len(block) <= FAST_PATH_BUDGETS["impl-reviewer"], (
            f"impl-reviewer FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['impl-reviewer']}"
        )

    def test_load_context_fast_path_under_budget(self):
        block = self._fast_path_block("load-context")
        assert len(block) <= FAST_PATH_BUDGETS["load-context"], (
            f"load-context FAST PATH is {len(block)} chars, must be ≤{FAST_PATH_BUDGETS['load-context']}"
        )


# ── subagent-context cache tests ──────────────────────────────────────────────

HOOK = HOOKS_DIR / "subagent-context.py"


def _make_zf(tmp_path: Path) -> None:
    zf = tmp_path / "zie-framework"
    zf.mkdir()
    (zf / ".config").write_text('{"project_type": "lib"}')
    (zf / "ROADMAP.md").write_text("## Now\n\n- active-feature\n\n## Next\n\n## Done\n")


def _run_hook(tmp_path: Path, agent_type: str,
              session_id: str = "test-session") -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"agentType": agent_type, "session_id": session_id})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event, capture_output=True, text=True, env=env,
    )


def _cache_flag(tmp_path: Path, session_id: str = "test-session") -> Path:
    project = tmp_path.name
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    safe_sid = re.sub(r'[^a-zA-Z0-9]', '-', session_id)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-session-context-{safe_sid}"


class TestSubagentContextCache:
    def test_injects_on_cache_miss(self, tmp_path):
        _make_zf(tmp_path)
        flag = _cache_flag(tmp_path)
        flag.unlink(missing_ok=True)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        out = r.stdout.strip()
        assert out, "should emit additionalContext on cache miss"
        flag.unlink(missing_ok=True)

    def test_writes_cache_flag_on_inject(self, tmp_path):
        _make_zf(tmp_path)
        flag = _cache_flag(tmp_path)
        flag.unlink(missing_ok=True)
        _run_hook(tmp_path, "Explore")
        assert flag.exists(), "cache flag must be written after first inject"
        flag.unlink(missing_ok=True)

    def test_skips_inject_on_cache_hit(self, tmp_path):
        _make_zf(tmp_path)
        flag = _cache_flag(tmp_path)
        flag.write_text("cached")  # pre-write flag = cache hit
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        # On cache hit the hook exits 0 with no stdout
        assert r.stdout.strip() == "", "should emit nothing on cache hit"
        flag.unlink(missing_ok=True)


class TestSubagentContextBudgetTable:
    """Per-agent budget table routes the right context to each agent type."""

    def test_explore_agent_gets_context(self, tmp_path):
        _make_zf(tmp_path)
        _cache_flag(tmp_path).unlink(missing_ok=True)
        r = _run_hook(tmp_path, "Explore")
        assert r.returncode == 0
        assert r.stdout.strip(), "Explore agent must receive context"
        _cache_flag(tmp_path).unlink(missing_ok=True)

    def test_brainstorm_agent_gets_no_context(self, tmp_path):
        _make_zf(tmp_path)
        _cache_flag(tmp_path).unlink(missing_ok=True)
        r = _run_hook(tmp_path, "brainstorm")
        assert r.returncode == 0
        assert r.stdout.strip() == "", "brainstorm agent must receive NO context injection"
        _cache_flag(tmp_path).unlink(missing_ok=True)

    def test_unknown_agent_falls_back_to_conservative_default(self, tmp_path):
        _make_zf(tmp_path)
        _cache_flag(tmp_path).unlink(missing_ok=True)
        r = _run_hook(tmp_path, "UnknownAgentType42")
        # Unknown gets conservative default — exits 0, may or may not emit
        assert r.returncode == 0
        _cache_flag(tmp_path).unlink(missing_ok=True)

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0


class TestSessionCleanup:
    """session-cleanup.py explicitly unlinks the session-context cache flag."""

    def test_cleanup_unlinks_cache_flag(self, tmp_path):
        _make_zf(tmp_path)
        flag = _cache_flag(tmp_path)
        flag.write_text("cached")
        assert flag.exists()

        cleanup_hook = HOOKS_DIR / "session-cleanup.py"
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(cleanup_hook)],
            input=json.dumps({"session_id": "test-session", "stop_reason": "end_turn"}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
        assert not flag.exists(), "session-cleanup must delete the session-context cache flag"

    def test_cleanup_handles_missing_flag_gracefully(self, tmp_path):
        _make_zf(tmp_path)
        flag = _cache_flag(tmp_path)
        flag.unlink(missing_ok=True)
        assert not flag.exists()

        cleanup_hook = HOOKS_DIR / "session-cleanup.py"
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(cleanup_hook)],
            input=json.dumps({"session_id": "test-session", "stop_reason": "end_turn"}),
            capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0  # no exception when flag is already absent
```

- [ ] **Step 2: Commit the test file**

```bash
git add tests/unit/test_context_efficiency.py
git commit -m "test(area-2): add context-efficiency failing tests (RED)"
```

- [ ] **Step 3: Run to confirm RED state**

```bash
make test-fast -k "TestFastPath or TestSubagentContext" 2>&1 | tail -15
```
Expected: FAIL — FAST PATH markers absent, cache tests fail (implementation not yet done).

---

### Task 2: Add FAST PATH headers to the 4 skill files
<!-- depends_on: T1 -->

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `skills/load-context/SKILL.md`

Read each file before editing to confirm current first line.

- [ ] **Step 1: Prepend FAST PATH block to skills/spec-reviewer/SKILL.md**

Insert after the YAML frontmatter (after the closing `---`) and before the existing `# spec-reviewer` heading:

```markdown
<!-- FAST PATH -->
**Purpose:** Review a design spec for completeness, YAGNI, and testability.
**When to use fast path:** Spec is short (<40 lines) and problem/approach/components/testing sections are all present.
**Quick steps:** (1) Read spec. (2) Check 9-item Phase 2 checklist. (3) Check 3-item Phase 3 context checks. (4) Output ✅ APPROVED or ❌ Issues Found.
<!-- DETAIL: load only if fast path insufficient -->
```

- [ ] **Step 2: Prepend FAST PATH block to skills/plan-reviewer/SKILL.md**

```markdown
<!-- FAST PATH -->
**Purpose:** Review an implementation plan for TDD structure, spec coverage, and task granularity.
**When to use fast path:** Plan has ≤10 tasks and each task has explicit test steps.
**Quick steps:** (1) Read plan + spec. (2) Check 10-item Phase 2 checklist. (3) Check Phase 3 context. (4) Output ✅ APPROVED or ❌ Issues Found.
<!-- DETAIL: load only if fast path insufficient -->
```

- [ ] **Step 3: Prepend FAST PATH block to skills/impl-reviewer/SKILL.md**

```markdown
<!-- FAST PATH -->
**Purpose:** Review completed task implementation against acceptance criteria.
**When to use fast path:** Changed files are small and ACs are explicitly listed.
**Quick steps:** (1) Read changed files + ACs. (2) Check 8-item Phase 2 checklist. (3) Output verdict.
<!-- DETAIL: load only if fast path insufficient -->
```

- [ ] **Step 4: Prepend FAST PATH block to skills/load-context/SKILL.md**

```markdown
<!-- FAST PATH -->
**Purpose:** Load ADR + project context bundle once per session for downstream reviewers.
**When to use fast path:** context_bundle already provided as argument → return it immediately.
**Quick steps:** (1) If context_bundle provided → return it. (2) Else: cache check → disk fallback → return bundle.
<!-- DETAIL: load only if fast path insufficient -->
```

- [ ] **Step 5: Run FAST PATH token budget tests**

```bash
make test-fast -k "TestFastPath" 2>&1 | tail -15
```
Expected: PASS — all 8 FAST PATH tests green.

- [ ] **Step 6: Commit**

```bash
git add skills/spec-reviewer/SKILL.md skills/plan-reviewer/SKILL.md \
        skills/impl-reviewer/SKILL.md skills/load-context/SKILL.md
git commit -m "feat(area-2): add FAST PATH headers to reviewer + load-context skills"
```

---

### Task 3: Refactor subagent-context.py — session cache + per-agent budget table
<!-- depends_on: T1 -->

**Files:**
- Modify: `hooks/subagent-context.py`

Read `hooks/subagent-context.py` fully before editing. The key change is:
- Replace the `re.search(r'Explore|Plan', agent_type)` early-exit guard (lines 17-18) with a budget table dispatch.
- Add session cache check at the top of inner operations.

- [ ] **Step 1: Rewrite subagent-context.py with cache + budget table**

```python
#!/usr/bin/env python3
"""SubagentStart hook — inject SDLC context into subagents per per-agent budget table.

ADR-046 superseded: the Explore/Plan-only guard is replaced by AGENT_BUDGETS
which handles all agent types explicitly with a conservative default for unknowns.

Session cache: first inject per session writes a flag; subsequent SubagentStart
events for the same project skip inject to avoid redundant context.
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import atomic_write, project_tmp_path
from utils_roadmap import parse_roadmap_section_content, read_roadmap_cached

# Per-agent context budget table (supersedes ADR-046 Explore/Plan guard).
# Value: True = inject context; False = skip inject entirely.
AGENT_BUDGETS = {
    "spec-reviewer":  True,   # receives spec file + ADR summary
    "plan-reviewer":  True,   # receives plan + spec + ADR summary
    "impl-reviewer":  True,   # receives changed files + plan
    "resync":         True,   # receives git log + file structure
    "Explore":        True,
    "Plan":           True,
    "brainstorm":     False,  # skill has own Phase 1 discovery — no injection
}
_DEFAULT_INJECT = True  # conservative default for unknown agent types


# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
    agent_type = event.get("agentType", "")
    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Budget table check ────────────────────────────────────────────────────────

# Normalize: case-insensitive match against budget table keys
_should_inject = _DEFAULT_INJECT
for key, inject in AGENT_BUDGETS.items():
    if re.search(re.escape(key), agent_type, re.IGNORECASE):
        _should_inject = inject
        break

if not _should_inject:
    sys.exit(0)

# ── Session cache check ───────────────────────────────────────────────────────
# Cache is session-scoped: key on session_id so a new session always injects.
# If session_id is absent (spec: fallback to always-inject), skip cache entirely.

session_id = event.get("session_id", "")
project = cwd.name

if session_id:
    safe_sid = re.sub(r'[^a-zA-Z0-9]', '-', session_id)
    cache_flag = project_tmp_path(f"session-context-{safe_sid}", project)
    if cache_flag.exists():
        # Already injected this session — skip to avoid redundant context
        sys.exit(0)
else:
    cache_flag = None  # no session_id → always inject (spec fallback)

# ── Inner operations ──────────────────────────────────────────────────────────

feature_slug = "none"
active_task = "unknown"
adr_count = "unknown"

# Read ROADMAP Now lane (via session cache)
try:
    roadmap_content = read_roadmap_cached(cwd / "zie-framework" / "ROADMAP.md", session_id)
    now_items = parse_roadmap_section_content(roadmap_content, "now")
    if now_items:
        raw = now_items[0]
        slug = raw.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug.strip())
        slug = re.sub(r'-+', '-', slug).strip('-')
        feature_slug = slug if slug else "none"
    else:
        feature_slug = "none"
        active_task = "none"
except Exception as e:
    print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

# Early exit when idle
if active_task == "none" and feature_slug == "none":
    sys.exit(0)

# Find most-recent plan file and extract first incomplete task (Plan agents only)
if re.search(r'Plan', agent_type, re.IGNORECASE):
    if feature_slug != "none" or active_task == "unknown":
        try:
            plans_dir = cwd / "zie-framework" / "plans"
            plan_files = sorted(
                plans_dir.glob("*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if plan_files:
                plan_text = plan_files[0].read_text()
                found = None
                for line in plan_text.splitlines():
                    if re.search(r'- \[ \]', line):
                        found = line
                        break
                if found is not None:
                    task = re.sub(r'^\s*-\s*\[\s*\]\s*', '', found)
                    task = re.sub(r'\*\*', '', task).strip()
                    active_task = task if task else "unknown"
                else:
                    active_task = "all tasks complete"
            else:
                active_task = "unknown"
        except Exception as e:
            print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)
else:
    active_task = "n/a"

# Count ADRs from project/context.md
try:
    context_file = cwd / "zie-framework" / "project" / "context.md"
    if context_file.exists():
        text = context_file.read_text()
        adr_count = str(len(re.findall(r'^## ADR-\d+', text, re.MULTILINE)))
    else:
        adr_count = "unknown"
except Exception as e:
    print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)

# Emit additionalContext
if active_task == "n/a":
    payload = f"[zie-framework] Active: {feature_slug} | ADRs: {adr_count}"
else:
    payload = (
        f"[zie-framework] Active: {feature_slug} | "
        f"Task: {active_task} | "
        f"ADRs: {adr_count}"
    )
print(json.dumps({"additionalContext": payload}))

# Write session cache flag so subsequent SubagentStart events skip inject
# cache_flag is None when session_id was absent (spec fallback: always inject)
if cache_flag is not None:
    try:
        atomic_write(cache_flag, "cached")
    except Exception as e:
        print(f"[zie-framework] subagent-context: cache write failed: {e}", file=sys.stderr)
        # Non-fatal — next subagent will just inject again
```

- [ ] **Step 2: Run cache + budget table tests**

```bash
make test-fast -k "TestSubagent" 2>&1 | tail -15
```
Expected: PASS — cache miss/hit/write and budget table tests green.

- [ ] **Step 3: Run full unit suite for regressions**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass — existing subagent-context tests (if any) unaffected.

- [ ] **Step 4: Commit**

```bash
git add hooks/subagent-context.py
git commit -m "feat(area-2): subagent-context session cache + per-agent budget table (supersedes ADR-046)"
```

---

### Task 4: Extend session-cleanup.py to unlink session-context cache flag
<!-- depends_on: T3 -->

**Files:**
- Modify: `hooks/session-cleanup.py`

Read `hooks/session-cleanup.py` first. The file already has a glob that deletes `zie-{safe_project}-*` files (which includes the cache flag). The spec additionally requires an explicit `unlink(missing_ok=True)` call.

- [ ] **Step 1: Add explicit cache flag unlink**

After the existing `for tmp_file in Path(tempfile.gettempdir()).glob(...)` loop, add:

```python
# Explicitly unlink session-context cache flag (spec: context-efficiency Area 2)
# The glob above already catches it; this explicit call satisfies the spec requirement.
from utils_io import project_tmp_path as _ptp
_cache_flag = _ptp("session-context", safe_project)
try:
    _cache_flag.unlink(missing_ok=True)
except Exception as e:
    print(f"[zie-framework] session-cleanup: {e}", file=sys.stderr)
```

- [ ] **Step 2: Run session-cleanup-related tests**

```bash
make test-unit -k "session_cleanup or context_efficiency" 2>&1 | tail -15
```
Expected: all pass (the unlink on missing file is graceful).

- [ ] **Step 3: Commit**

```bash
git add hooks/session-cleanup.py
git commit -m "feat(area-2): session-cleanup explicitly unlinks session-context cache flag"
```

---

### Task 5: Write ADR-061 documenting ADR-046 supersession
<!-- depends_on: T3 -->

**Files:**
- Create: `zie-framework/decisions/ADR-061-context-efficiency-budget-table.md`

The context-efficiency spec explicitly supersedes ADR-046. ADR-046 restricted `subagent-context.py` to Explore and Plan agents via an early-exit guard. This ADR records the replacement decision.

- [ ] **Step 1: Create the ADR**

```markdown
# ADR-061 — Context Efficiency: Per-Agent Budget Table Supersedes ADR-046

**Date:** 2026-04-11
**Status:** Accepted
**Supersedes:** ADR-046

## Context

ADR-046 added an early-exit guard to `subagent-context.py` restricting context
injection to Explore and Plan agent types:

```python
if not re.search(r'Explore|Plan', agent_type): sys.exit(0)
```

This was a blunt instrument that correctly solved the immediate problem (don't
spam reviewers with project state) but made it impossible to add per-agent
differentiation without modifying the guard.

## Decision

Replace the binary Explore/Plan guard with an `AGENT_BUDGETS` dispatch table
that explicitly maps each agent type to an inject/skip decision:

```python
AGENT_BUDGETS = {
    "spec-reviewer": True,
    "plan-reviewer": True,
    "impl-reviewer": True,
    "resync":        True,
    "Explore":       True,
    "Plan":          True,
    "brainstorm":    False,  # skill has own Phase 1 discovery
}
_DEFAULT_INJECT = True  # conservative default for unknown types
```

The table also enables future per-agent payload differentiation (what context
each agent receives) by expanding the value from bool to a bundle descriptor.

Additionally, a session-scoped cache flag (`project_tmp_path("session-context-{session_id}", project)`)
prevents re-injecting the same project state on every SubagentStart event
within a single session.

## Consequences

- All current Explore/Plan behaviour is preserved (both map to True in the table).
- New agent types (brainstorm) can opt out of injection without code changes.
- Session cache reduces redundant context injection for multi-agent sessions.
- Unknown agent types receive a conservative default (inject) rather than a silent skip.
- ADR-046 is superseded; its guard is removed from `subagent-context.py`.
```

- [ ] **Step 2: Commit**

```bash
git add zie-framework/decisions/ADR-061-context-efficiency-budget-table.md
git commit -m "docs(adr): ADR-061 — per-agent budget table supersedes ADR-046"
```

---

### Task 6: Final regression check

- [ ] **Step 1: Run full unit suite**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass, no regressions in reviewer skill tests.
