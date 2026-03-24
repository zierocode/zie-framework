---
approved: true
approved_at: 2026-03-24
backlog: backlog/subagentstart-sdlc-context.md
spec: specs/2026-03-24-subagentstart-sdlc-context-design.md
---

# SubagentStart SDLC Context Injection — Implementation Plan

**Goal:** Inject active feature slug, first incomplete task, and ADR count into every Explore/Plan subagent spawned by Claude Code so research is purposeful rather than generic.
**Architecture:** A new `SubagentStart` hook (`hooks/subagent-context.py`) reads three files — `ROADMAP.md`, the most-recent plan file, and `project/context.md` — using only stdlib file I/O, then emits a JSON `additionalContext` payload; a matcher `"Explore|Plan"` gates injection so non-research agents (Task, Build, Coding) receive zero overhead. The hook is registered as a new `SubagentStart` entry in `hooks/hooks.json` with that matcher.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/subagent-context.py` | SubagentStart hook — reads SDLC files, emits additionalContext |
| Modify | `hooks/hooks.json` | Add SubagentStart entry with matcher `"Explore\|Plan"` |
| Create | `tests/unit/test_hooks_subagent_context.py` | Unit tests (subprocess + fixture helpers) |
| Modify | `zie-framework/project/components.md` | Add `subagent-context.py` row to Hooks table |

---

## Task 1: Create `hooks/subagent-context.py`

<!-- depends_on: none -->

**Acceptance Criteria:**

- Explore and Plan agent types receive a JSON `additionalContext` payload containing `Active:`, `Task:`, and `ADRs:` fields.
- Non-matching agent types (Task, Build, Coding, empty string) produce no stdout and exit 0.
- Missing ROADMAP / plan files / context.md each trigger safe fallback values, not crashes.
- All plan tasks marked `[x]` produces `Task: all tasks complete`.
- No ROADMAP Now items produces `Active: none | Task: none`.
- Invalid JSON on stdin exits 0 with no output.
- No subprocesses are spawned. Hook exits 0 in every path.

**Files:**

- Create: `hooks/subagent-context.py`
- Create: `tests/unit/test_hooks_subagent_context.py`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_subagent_context.py

"""Tests for hooks/subagent-context.py"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

SAMPLE_ROADMAP = """\
## Now

- [ ] [subagentstart-sdlc-context](plans/2026-03-24-subagentstart-sdlc-context.md)

## Next

- [ ] some-future-feature
"""

SAMPLE_PLAN = """\
# SubagentStart SDLC Context Injection — Implementation Plan

## Task 1: Create hooks/subagent-context.py

- [ ] **Step 1: Write failing tests (RED)**
- [ ] **Step 2: Implement (GREEN)**
- [ ] **Step 3: Refactor**
"""

SAMPLE_PLAN_ALL_DONE = """\
# SubagentStart SDLC Context Injection — Implementation Plan

## Task 1: Create hooks/subagent-context.py

- [x] **Step 1: Write failing tests (RED)**
- [x] **Step 2: Implement (GREEN)**
- [x] **Step 3: Refactor**
"""

SAMPLE_CONTEXT_MD = """\
## ADR-001

Some decision.

## ADR-002

Another decision.
"""


def make_cwd(tmp_path, roadmap=None, plan=None, context_md=None):
    """Build a minimal zie-framework directory structure for testing."""
    zf = tmp_path / "zie-framework"
    (zf / "plans").mkdir(parents=True)
    (zf / "project").mkdir(parents=True)

    if roadmap is not None:
        (zf / "ROADMAP.md").write_text(roadmap)

    if plan is not None:
        (zf / "plans" / "2026-03-24-subagentstart-sdlc-context.md").write_text(plan)

    if context_md is not None:
        (zf / "project" / "context.md").write_text(context_md)

    return tmp_path


def run_hook(event, tmp_cwd=None, env_overrides=None):
    hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
    env = {**os.environ, "ZIE_MEMORY_API_KEY": ""}
    if tmp_cwd:
        env["CLAUDE_CWD"] = str(tmp_cwd)
    if env_overrides:
        env.update(env_overrides)
    return subprocess.run(
        [sys.executable, hook],
        input=json.dumps(event),
        capture_output=True,
        text=True,
        env=env,
    )


def parse_context(r):
    """Assert stdout is non-empty JSON and return the additionalContext string."""
    assert r.stdout.strip() != "", f"Expected stdout, got empty. stderr={r.stderr}"
    return json.loads(r.stdout)["additionalContext"]


# ── Happy path ────────────────────────────────────────────────────────────────

class TestSubagentContextHappyPath:
    def test_explore_agent_receives_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "[zie-framework]" in ctx
        assert "Active:" in ctx
        assert "Task:" in ctx
        assert "ADRs:" in ctx

    def test_plan_agent_receives_context(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Plan"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active:" in ctx

    def test_feature_slug_derived_from_roadmap_now(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "subagentstart-sdlc-context" in ctx

    def test_first_incomplete_task_extracted(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Step 1: Write failing tests (RED)" in ctx

    def test_adr_count_correct(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "ADRs: 2" in ctx

    def test_all_tasks_complete_message(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN_ALL_DONE,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "all tasks complete" in ctx

    def test_returns_valid_json(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        parsed = json.loads(r.stdout)
        assert "additionalContext" in parsed
        assert isinstance(parsed["additionalContext"], str)

    def test_exit_code_zero_on_success(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        assert r.returncode == 0


# ── Agent-type filter ─────────────────────────────────────────────────────────

class TestSubagentContextAgentFilter:
    def test_task_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Task"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""
        assert r.returncode == 0

    def test_build_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Build"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_coding_agent_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Coding"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_empty_agent_type_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": ""}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_missing_agent_type_field_produces_no_output(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""

    def test_case_insensitive_explore_match(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active:" in ctx


# ── Edge cases: missing files ─────────────────────────────────────────────────

class TestSubagentContextMissingFiles:
    def test_no_roadmap_emits_active_none(self, tmp_path):
        cwd = make_cwd(tmp_path, plan=SAMPLE_PLAN, context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Active: none" in ctx

    def test_no_plan_files_emits_task_unknown(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "Task: unknown" in ctx

    def test_missing_context_md_emits_adr_unknown(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        ctx = parse_context(r)
        assert "ADRs: unknown" in ctx

    def test_no_roadmap_no_plan_still_exits_zero(self, tmp_path):
        cwd = make_cwd(tmp_path)
        r = run_hook({"agentType": "Explore"}, tmp_cwd=cwd)
        assert r.returncode == 0

    def test_no_zf_dir_produces_no_output(self, tmp_path):
        r = run_hook({"agentType": "Explore"}, tmp_cwd=tmp_path)
        assert r.stdout.strip() == ""
        assert r.returncode == 0


# ── Guardrails ────────────────────────────────────────────────────────────────

class TestSubagentContextGuardrails:
    def test_invalid_json_stdin_exits_zero(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, hook],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0
        assert r.stdout.strip() == ""

    def test_empty_stdin_exits_zero(self, tmp_path):
        hook = os.path.join(REPO_ROOT, "hooks", "subagent-context.py")
        env = {**os.environ, "CLAUDE_CWD": str(tmp_path)}
        r = subprocess.run(
            [sys.executable, hook],
            input="",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0

    def test_no_stdout_for_non_matching_agent_even_with_full_files(self, tmp_path):
        cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, plan=SAMPLE_PLAN,
                       context_md=SAMPLE_CONTEXT_MD)
        r = run_hook({"agentType": "Task"}, tmp_cwd=cwd)
        assert r.stdout.strip() == ""
        assert r.returncode == 0
```

Run: `make test-unit` — must FAIL (`No such file or directory: hooks/subagent-context.py`)

---

### Step 2: Implement (GREEN)

```python
# hooks/subagent-context.py

#!/usr/bin/env python3
"""SubagentStart hook — inject SDLC context into Explore/Plan subagents."""
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils import read_event, get_cwd, parse_roadmap_now

# ── Outer guard ───────────────────────────────────────────────────────────────

try:
    event = read_event()
    agent_type = event.get("agentType", "")
    if not re.search(r'Explore|Plan', agent_type, re.IGNORECASE):
        sys.exit(0)
    cwd = get_cwd()
    if not (cwd / "zie-framework").exists():
        sys.exit(0)
except Exception:
    sys.exit(0)

# ── Inner operations ──────────────────────────────────────────────────────────

feature_slug = "none"
active_task = "unknown"
adr_count = "unknown"

# Read ROADMAP Now lane
try:
    now_items = parse_roadmap_now(cwd / "zie-framework" / "ROADMAP.md")
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

# Find most-recent plan file and extract first incomplete task
if feature_slug != "none" or active_task == "unknown":
    try:
        plans_dir = cwd / "zie-framework" / "plans"
        plan_files = sorted(plans_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
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
payload = (
    f"[zie-framework] Active: {feature_slug} | "
    f"Task: {active_task} | "
    f"ADRs: {adr_count} (see zie-framework/project/context.md)"
)
print(json.dumps({"additionalContext": payload}))
```

Run: `make test-unit` — must PASS

---

### Step 3: Refactor

- Confirm the outer `try/except Exception` covers `read_event()`, `agent_type` extraction, `get_cwd()`, and the `zie-framework` existence check — nothing else.
- Confirm the `active_task = "none"` short-circuit when `feature_slug == "none"` (empty Now lane) is correct per spec edge case: `Active: none | Task: none`.
- Audit: no subprocess calls, no file writes, no non-zero exits.

Run: `make test-unit` — still PASS

---

## Task 2: Register `SubagentStart` in `hooks.json`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `hooks.json` contains a `"SubagentStart"` top-level key.
- The entry has `"matcher": "Explore|Plan"`.
- The command path uses `${CLAUDE_PLUGIN_ROOT}` and points to `hooks/subagent-context.py`.
- All other existing hook entries are unchanged.
- `make test-unit` continues to pass.

**Files:**

- Modify: `hooks/hooks.json`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_subagent_context.py — append new class

class TestHooksJsonRegistration:
    def test_subagentstart_key_present(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        assert "SubagentStart" in data["hooks"], \
            "SubagentStart key missing from hooks.json"

    def test_subagentstart_matcher_is_explore_or_plan(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        entry = data["hooks"]["SubagentStart"]
        assert len(entry) > 0
        assert entry[0].get("matcher") == "Explore|Plan", \
            f"Expected matcher 'Explore|Plan', got {entry[0].get('matcher')!r}"

    def test_subagentstart_command_references_correct_script(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        entry = data["hooks"]["SubagentStart"]
        command = entry[0]["hooks"][0]["command"]
        assert "subagent-context.py" in command
        assert "${CLAUDE_PLUGIN_ROOT}" in command

    def test_existing_hooks_unchanged(self):
        hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
        data = json.loads(hooks_json.read_text())
        hooks = data["hooks"]
        for key in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreToolUse", "Stop"):
            assert key in hooks, f"Existing hook key {key!r} was removed"
```

Run: `make test-unit` — must FAIL (`SubagentStart key missing from hooks.json`)

---

### Step 2: Implement (GREEN)

Add the `SubagentStart` block to `hooks/hooks.json` after the `UserPromptSubmit` entry:

```json
  "SubagentStart": [
    {
      "matcher": "Explore|Plan",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/subagent-context.py\""
        }
      ]
    }
  ],
```

Full updated `hooks` object key order: `SessionStart`, `UserPromptSubmit`, `SubagentStart`, `PostToolUse`, `PreToolUse`, `Stop`.

Run: `make test-unit` — must PASS

---

### Step 3: Refactor

- Verify JSON is valid with `python3 -c "import json; json.load(open('hooks/hooks.json'))"`.
- Confirm no trailing commas or structural issues.
- Confirm `_hook_output_protocol` comment block is still intact and untouched.

Run: `make test-unit` — still PASS

---

## Task 3: Update `components.md`

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `zie-framework/project/components.md` Hooks table contains a row for `subagent-context.py`.
- Row format matches existing rows (pipe-delimited, same three columns).

**Files:**

- Modify: `zie-framework/project/components.md`

---

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_hooks_subagent_context.py — append new class

class TestComponentsRegistryUpdated:
    def test_subagent_context_in_components_md(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        text = components.read_text()
        assert "subagent-context.py" in text, \
            "subagent-context.py not found in components.md Hooks table"

    def test_subagentstart_event_listed(self):
        components = Path(REPO_ROOT) / "zie-framework" / "project" / "components.md"
        text = components.read_text()
        assert "SubagentStart" in text, \
            "SubagentStart event not listed in components.md"
```

Run: `make test-unit` — must FAIL

---

### Step 2: Implement (GREEN)

Append to the Hooks table in `zie-framework/project/components.md` (after the `utils.py` row):

```markdown
| subagent-context.py | SubagentStart:Explore/Plan | inject active feature slug, first incomplete task, ADR count into research subagents |
```

Also update `**Last updated:**` to `2026-03-24`.

Run: `make test-unit` — must PASS

---

### Step 3: Refactor

No structural changes needed. Confirm table alignment is consistent with existing rows.

Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/subagent-context.py hooks/hooks.json tests/unit/test_hooks_subagent_context.py zie-framework/project/components.md && git commit -m "feat: SubagentStart SDLC context injection for Explore/Plan subagents"`*
