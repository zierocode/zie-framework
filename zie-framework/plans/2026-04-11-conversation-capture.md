---
approved: true
approved_at: 2026-04-11
backlog:
spec: zie-framework/specs/2026-04-11-conversation-capture-design.md
---

# Conversation Capture — Implementation Plan

> **Implementation:** Run via `claude --agent zie-framework:zie-implement-mode`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Capture implicit design conversations and bridge them to `/sprint` via `.zie/handoff.md` — without requiring the user to explicitly invoke the brainstorm skill.

**Architecture:** Two new hooks wire up the secondary write path: `design-tracker.py` (UserPromptSubmit, async) detects design signals and sets a session flag; `stop-capture.py` (Stop, synchronous) reads that flag and writes `.zie/handoff.md` only when the brainstorm skill did not already run. `/brief` displays the artifact; `/sprint` detects and consumes it automatically.

**Tech Stack:** Python 3.x (hooks), `utils_io.project_tmp_path()` + `atomic_write()`, Markdown (commands), pytest (subprocess-based unit tests).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `hooks/design-tracker.py` | UserPromptSubmit hook — detect design signals, write design-mode flag |
| Create | `hooks/stop-capture.py` | Stop hook — write .zie/handoff.md when design-mode flag present |
| Modify | `hooks/hooks.json` | Register both new hooks |
| Modify | `.gitignore` | Add `.zie/` entry |
| Create | `commands/brief.md` | `/brief` command — display handoff.md summary |
| Modify | `commands/sprint.md` | Auto-read .zie/handoff.md when present |
| Create | `tests/unit/test_design_tracker.py` | Unit tests for design-tracker |
| Create | `tests/unit/test_stop_capture.py` | Unit tests for stop-capture |

---

### Task 1: Tests for design-tracker.py

**Files:**
- Create: `tests/unit/test_design_tracker.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for hooks/design-tracker.py (Area 1 — Conversation Capture)."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "design-tracker.py"


def _run(message: str, tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"prompt": message, "session_id": "test-session"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


def _flag_path(tmp_path: Path) -> Path:
    from pathlib import Path as _P
    import re, tempfile
    project = _P(tmp_path).name
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return _P(tempfile.gettempdir()) / f"zie-{safe}-design-mode"


class TestDesignTrackerWritesFlag:
    def test_writes_flag_on_design_signal(self, tmp_path):
        flag = _flag_path(tmp_path)
        flag.unlink(missing_ok=True)
        r = _run("let's design a new feature for the API", tmp_path)
        assert r.returncode == 0
        assert flag.exists(), "design-mode flag must be written when design signal detected"
        flag.unlink(missing_ok=True)

    def test_no_flag_when_no_signals(self, tmp_path):
        flag = _flag_path(tmp_path)
        flag.unlink(missing_ok=True)
        r = _run("print hello world", tmp_path)
        assert r.returncode == 0
        assert not flag.exists(), "design-mode flag must NOT be written with no signals"

    def test_exits_zero_on_empty_message(self, tmp_path):
        r = _run("", tmp_path)
        assert r.returncode == 0

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0


import pytest
```

- [ ] **Step 2: Run to confirm failure**

```bash
make test-fast 2>&1 | tail -10
```
Expected: FAIL — `hooks/design-tracker.py` not found.

---

### Task 2: Create hooks/design-tracker.py

**Files:**
- Create: `hooks/design-tracker.py`

- [ ] **Step 1: Write the hook**

```python
#!/usr/bin/env python3
"""UserPromptSubmit hook — detect design-intent signals and write design-mode flag.

Async (background: true in hooks.json) — never blocks Claude.
Checks for design signals in the user's message; writes a session flag that
stop-capture.py reads at Stop time to write .zie/handoff.md.
"""
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path

DESIGN_SIGNALS = [
    r"\bdesign\b", r"\bspec\b", r"\bfeature\b", r"\bimprove\b",
    r"discuss.*sprint", r"let.*s build", r"what if", r"\barchitect",
    r"สร้าง.*ใหม่", r"ออกแบบ", r"วางแผน.*สร้าง",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in DESIGN_SIGNALS]


try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    message = (event.get("prompt") or "").strip()
    if not message or len(message) < 5:
        sys.exit(0)

    cwd = get_cwd()

    hits = sum(1 for p in _COMPILED if p.search(message))
    if hits < 2:
        sys.exit(0)

    flag = project_tmp_path("design-mode", cwd.name)
    try:
        flag.write_text("active")
    except Exception:
        pass  # never block on flag write failure

except Exception:
    sys.exit(0)
```

- [ ] **Step 2: Run tests to confirm they pass**

```bash
make test-fast 2>&1 | tail -10
```
Expected: PASS — design signal and no-signal tests green.

- [ ] **Step 3: Commit**

```bash
git add hooks/design-tracker.py tests/unit/test_design_tracker.py
git commit -m "feat(area-1): design-tracker hook — detect design intent, write session flag"
```

---

### Task 3: Tests for stop-capture.py

**Files:**
- Create: `tests/unit/test_stop_capture.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for hooks/stop-capture.py (Area 1 — Conversation Capture)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-capture.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"session_id": "test-session", "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event,
        capture_output=True,
        text=True,
        env=env,
    )


class TestStopCapture:
    def test_skips_write_when_brainstorm_active(self, tmp_path):
        project = tmp_path.name
        _flag(project, "brainstorm-active").write_text("active")
        _flag(project, "design-mode").write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when brainstorm-active flag present"
        _flag(project, "brainstorm-active").unlink(missing_ok=True)
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_skips_write_when_no_design_mode_flag(self, tmp_path):
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert not handoff.exists(), "must skip write when design-mode flag absent"

    def test_writes_handoff_when_design_mode_active(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        handoff = tmp_path / ".zie" / "handoff.md"
        assert handoff.exists(), "must write .zie/handoff.md when design-mode flag set"
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_handoff_has_correct_frontmatter(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        assert "captured_at:" in content
        assert "source: design-tracker" in content
        _flag(project, "design-mode").unlink(missing_ok=True)

    def test_deletes_design_mode_flag_after_write(self, tmp_path):
        project = tmp_path.name
        flag = _flag(project, "design-mode")
        flag.write_text("active")
        _run(tmp_path)
        assert not flag.exists(), "design-mode flag must be deleted after handoff write"

    def test_handoff_has_required_sections(self, tmp_path):
        project = tmp_path.name
        _flag(project, "design-mode").write_text("active")
        _run(tmp_path)
        content = (tmp_path / ".zie" / "handoff.md").read_text()
        for section in ("## Goals", "## Key Decisions", "## Next Step"):
            assert section in content, f"handoff.md must contain '{section}'"
        _flag(project, "design-mode").unlink(missing_ok=True)

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json",
            capture_output=True,
            text=True,
            env=env,
        )
        assert r.returncode == 0


import pytest
```

- [ ] **Step 2: Run to confirm failure**

```bash
make test-fast 2>&1 | tail -10
```
Expected: FAIL — `hooks/stop-capture.py` not found.

---

### Task 4: Create hooks/stop-capture.py

**Files:**
- Create: `hooks/stop-capture.py`

- [ ] **Step 1: Write the hook**

```python
#!/usr/bin/env python3
"""Stop hook — write .zie/handoff.md from implicit design conversations.

Synchronous (no background: true) — handoff.md must be flushed before session
closes so /sprint can read it in the next session.

Secondary write path: only fires when brainstorm skill did NOT already run.
Brainstorm skill sets the 'brainstorm-active' flag; this hook skips if set.
"""
import datetime
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import atomic_write, project_tmp_path

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    cwd = get_cwd()
    project = cwd.name

    # Skip if brainstorm skill already ran (it's the primary writer)
    brainstorm_flag = project_tmp_path("brainstorm-active", project)
    if brainstorm_flag.exists():
        sys.exit(0)

    # Skip if no design conversation detected this session
    design_flag = project_tmp_path("design-mode", project)
    if not design_flag.exists():
        sys.exit(0)

    # Create .zie/ dir if absent
    zie_dir = cwd / ".zie"
    try:
        zie_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"[zie-framework] stop-capture: cannot create .zie/: {e}", file=sys.stderr)
        sys.exit(0)

    # Write handoff.md
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    handoff_content = f"""---
captured_at: {now}
feature: design-session
source: design-tracker
---

## Goals
- (captured from design conversation — review and refine before running /sprint)

## Key Decisions
- (key decisions made during this session)

## Constraints
- (constraints mentioned during discussion)

## Open Questions
- (unresolved questions to address)

## Context Refs
- (relevant file paths or commands mentioned)

## Next Step
/sprint <feature-name>
"""
    handoff_path = zie_dir / "handoff.md"
    try:
        atomic_write(handoff_path, handoff_content)
    except Exception as e:
        print(f"[zie-framework] stop-capture: handoff write failed: {e}", file=sys.stderr)
        sys.exit(0)

    # Cleanup design-mode flag
    try:
        design_flag.unlink(missing_ok=True)
    except Exception:
        pass

except Exception:
    sys.exit(0)
```

- [ ] **Step 2: Run tests to confirm they pass**

```bash
make test-fast 2>&1 | tail -10
```
Expected: PASS — all stop-capture tests green.

- [ ] **Step 3: Commit**

```bash
git add hooks/stop-capture.py tests/unit/test_stop_capture.py
git commit -m "feat(area-1): stop-capture hook — write .zie/handoff.md from design conversations"
```

---

### Task 5: Register hooks in hooks.json and add .gitignore entry

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `.gitignore`

- [ ] **Step 1: Add design-tracker.py to UserPromptSubmit array in hooks.json**

In `hooks/hooks.json`, find the UserPromptSubmit array (currently has one entry for `intent-sdlc.py`). Add a second hook entry with `background: true`:

```json
  "UserPromptSubmit": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-sdlc.py\""
        }
      ]
    },
    {
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/design-tracker.py\"",
          "background": true
        }
      ]
    }
  ],
```

- [ ] **Step 2: Add stop-capture.py to Stop array in hooks.json**

In the Stop array (currently has stop-guard.py, compact-hint.py, session-learn.py, session-cleanup.py), add stop-capture.py as a synchronous entry (no `background: true`) before session-cleanup.py:

```json
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stop-capture.py\""
        },
```

- [ ] **Step 3: Add .zie/ to .gitignore**

In `.gitignore`, add at the end:

```
.zie/
```

- [ ] **Step 4: Verify hooks.json is valid JSON**

```bash
python3 -c "import json; json.load(open('hooks/hooks.json')); print('valid')"
```
Expected: `valid`

- [ ] **Step 5: Commit**

```bash
git add hooks/hooks.json .gitignore
git commit -m "feat(area-1): register design-tracker + stop-capture in hooks.json; add .zie/ to .gitignore"
```

---

### Task 6: Create commands/brief.md

**Files:**
- Create: `commands/brief.md`

- [ ] **Step 1: Write the command file**

```markdown
---
description: Display the active design brief from .zie/handoff.md, or report when none exists.
argument-hint: ""
allowed-tools: Read
model: sonnet
effort: low
---

# /brief — Design Brief Review

Display the captured design brief and confirm readiness for `/sprint`.

## Steps

1. Check `$CWD/.zie/handoff.md`:
   - If absent → print:
     ```
     No active design brief — run a design conversation first,
     or invoke zie-framework:brainstorm to start a structured session.
     ```
     Stop here.

2. Read `.zie/handoff.md` — display its full content formatted.

3. Print:
   ```
   Brief captured at: <captured_at value>
   Source: <source value>

   Run /sprint <feature-name> to start the pipeline with this brief.
   Run /sprint without arguments to be prompted for a topic.
   ```
```

- [ ] **Step 2: Commit**

```bash
git add commands/brief.md
git commit -m "feat(area-1): /brief command — display .zie/handoff.md"
```

---

### Task 7: Extend commands/sprint.md to auto-read handoff.md

**Files:**
- Modify: `commands/sprint.md`

Read `commands/sprint.md` first. Find the `## ตรวจสอบก่อนเริ่ม` section (the pre-flight checklist). Add handoff.md detection as step 6:

- [ ] **Step 1: Add handoff detection to sprint pre-flight**

After the existing step 5 ("Verify no uncommitted changes"), add:

```markdown
6. Check `.zie/handoff.md` — if present, read it. Use its Goals, Key Decisions,
   and Constraints as context brief for this sprint run. After the sprint
   completes successfully (after retro), delete `.zie/handoff.md`.
   If handoff.md is malformed (missing frontmatter) → warn and fall back to
   manual prompt mode.
```

- [ ] **Step 2: Verify sprint.md still passes existing tests**

```bash
make test-unit -k sprint 2>&1 | tail -10
```
Expected: all sprint-related tests pass.

- [ ] **Step 3: Commit**

```bash
git add commands/sprint.md
git commit -m "feat(area-1): /sprint auto-reads .zie/handoff.md when present"
```

---

### Task 8: Final regression check

- [ ] **Step 1: Run full unit suite**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass.
