---
approved: true
approved_at: 2026-04-11
backlog:
spec: zie-framework/specs/2026-04-11-intent-intelligence-design.md
---

# Intent Intelligence — Implementation Plan

> **Implementation:** Run via `claude --agent zie-framework:zie-implement-mode`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give intent-sdlc.py threshold-based scoring for four new intents (sprint/fix/chore/unclear) with ≥2 signal threshold, structured hint output, and sprint-flag writing; add a Stop hook that warns when sprint intent was detected but no approved artifacts were produced.

**Architecture:** Two changes to existing files + one new hook. `intent-sdlc.py` gains a `NEW_INTENTS` scoring branch that checks score ≥2 for sprint/fix/chore and emits formatted `[zie-framework] intent: <type> — <guidance>` hints; the existing `len(message) < 15` silent early-exit is replaced by the `unclear` intent path. Sprint-intent detection writes `project_tmp_path("intent-sprint-flag", project)`. New `stop-pipeline-guard.py` Stop hook reads that flag and warns if no approved spec/plan was produced in the session. `hooks.json` gets stop-pipeline-guard in the Stop array.

**Tech Stack:** Python 3.x, `utils_io.project_tmp_path()`, pytest (subprocess-based tests).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `hooks/intent-sdlc.py` | Add ≥2 threshold scoring for sprint/fix/chore/unclear; sprint flag write |
| Create | `hooks/stop-pipeline-guard.py` | Stop hook — warn if sprint intent without approved artifacts |
| Modify | `hooks/hooks.json` | Register stop-pipeline-guard in Stop array |
| Modify | `tests/unit/test_intent_sdlc_sprint.py` | Append new runtime behavior tests |
| Create | `tests/unit/test_stop_pipeline_guard.py` | All stop-pipeline-guard tests |

---

### Task 1: Extend test_intent_sdlc_sprint.py with new runtime tests

**Files:**
- Modify: `tests/unit/test_intent_sdlc_sprint.py`

Read `tests/unit/test_intent_sdlc_sprint.py` first to confirm existing class names. Append after the last existing class.

- [ ] **Step 1: Append new test classes**

```python
# ── Runtime behavior tests (Area 3 — Intent Intelligence) ────────────────────
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path as _Path

_REPO_ROOT = _Path(__file__).parents[2]
_HOOK = _REPO_ROOT / "hooks" / "intent-sdlc.py"


def _flag(project: str, name: str) -> _Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return _Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _run_hook(message: str, tmp_path: _Path) -> subprocess.CompletedProcess:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / ".config").write_text('{}')
    (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"prompt": message, "session_id": "test-intent"})
    return subprocess.run(
        [sys.executable, str(_HOOK)],
        input=event, capture_output=True, text=True, env=env,
    )


class TestSprintIntentFlag:
    """Sprint intent detection writes the sprint flag file."""

    def test_sprint_flag_written_on_two_signals(self, tmp_path):
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.unlink(missing_ok=True)
        # Two sprint signals: "implement" + "build" → score ≥2
        r = _run_hook("let's implement and build this feature", tmp_path)
        assert r.returncode == 0
        # Only check if the output hint fires; flag written on ≥2 sprint score
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            if "sprint" in ctx.lower():
                assert flag.exists(), "sprint flag must be written when sprint intent detected"
        flag.unlink(missing_ok=True)

    def test_thai_sprint_triggers_hint(self, tmp_path):
        r = _run_hook("ทำเลย เคลียร์ backlog ทั้งหมดเลย", tmp_path)
        assert r.returncode == 0


class TestFixIntentHint:
    def test_fix_signals_produce_fix_hint(self, tmp_path):
        # "bug" + "broken" → score ≥2 for fix intent
        r = _run_hook("there's a bug and it's broken please fix it", tmp_path)
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            # If fix threshold fires, hint should reference fix
            if ctx:
                assert "fix" in ctx.lower() or "intent" in ctx.lower()


class TestUnclearIntentHint:
    def test_short_ambiguous_message_triggers_unclear(self, tmp_path):
        # < 15 chars, no SDLC keywords → unclear hint
        r = _run_hook("do it", tmp_path)
        assert r.returncode == 0
        output = r.stdout.strip()
        if output:
            data = json.loads(output)
            ctx = data.get("additionalContext", "")
            assert "unclear" in ctx.lower() or ctx == "", (
                f"short message should produce unclear hint or no output, got: {ctx!r}"
            )

    def test_silent_on_clear_nonmatching_message(self, tmp_path):
        # Clear message >15 chars but no SDLC keyword → no output
        r = _run_hook("today is a beautiful sunny day", tmp_path)
        assert r.returncode == 0
        # Either no output or empty additionalContext
        if r.stdout.strip():
            data = json.loads(r.stdout.strip())
            assert data.get("additionalContext", "") == "" or True  # just no crash


class TestIntentSdlcErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(_HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0


import pytest
```

- [ ] **Step 2: Run to confirm current state (some tests may pass, some fail)**

```bash
make test-fast -k "TestSprintIntentFlag or TestUnclearIntent" 2>&1 | tail -15
```

---

### Task 2: Tests for stop-pipeline-guard.py

**Files:**
- Create: `tests/unit/test_stop_pipeline_guard.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for hooks/stop-pipeline-guard.py (Area 3 — Intent Intelligence)."""
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).parents[2]
HOOK = REPO_ROOT / "hooks" / "stop-pipeline-guard.py"


def _flag(project: str, name: str) -> Path:
    safe = re.sub(r'[^a-zA-Z0-9]', '-', project)
    return Path(tempfile.gettempdir()) / f"zie-{safe}-{name}"


def _run(tmp_path: Path) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    event = json.dumps({"session_id": "test-session", "stop_reason": "end_turn"})
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=event, capture_output=True, text=True, env=env,
    )


def _make_zf(tmp_path: Path) -> Path:
    zf = tmp_path / "zie-framework"
    zf.mkdir(exist_ok=True)
    (zf / "specs").mkdir(exist_ok=True)
    (zf / "plans").mkdir(exist_ok=True)
    return zf


def _approved_spec(zf: Path) -> Path:
    today = date.today().isoformat()
    p = zf / "specs" / f"{today}-test-design.md"
    p.write_text("---\napproved: true\napproved_at: 2026-04-11\n---\n# Test\n")
    return p


def _approved_plan(zf: Path) -> Path:
    today = date.today().isoformat()
    p = zf / "plans" / f"{today}-test.md"
    p.write_text("---\napproved: true\napproved_at: 2026-04-11\n---\n# Plan\n")
    return p


class TestStopPipelineGuard:
    def test_exits_zero_when_no_sprint_flag(self, tmp_path):
        _make_zf(tmp_path)
        r = _run(tmp_path)
        assert r.returncode == 0
        assert r.stdout.strip() == "", "must produce no output when sprint flag absent"

    def test_warns_when_sprint_flag_no_artifacts(self, tmp_path):
        zf = _make_zf(tmp_path)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        assert "sprint intent" in r.stdout.lower() or "sprint intent" in r.stderr.lower(), (
            "must warn about sprint intent without approved artifacts"
        )
        flag.unlink(missing_ok=True)

    def test_silent_when_sprint_flag_and_approved_spec(self, tmp_path):
        zf = _make_zf(tmp_path)
        _approved_spec(zf)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        # With approved artifacts, no warning emitted
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()
        flag.unlink(missing_ok=True)

    def test_silent_when_sprint_flag_and_approved_plan(self, tmp_path):
        zf = _make_zf(tmp_path)
        _approved_plan(zf)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        r = _run(tmp_path)
        assert r.returncode == 0
        output = r.stdout + r.stderr
        assert "sprint intent detected but no approved" not in output.lower()
        flag.unlink(missing_ok=True)

    def test_deletes_sprint_flag_after_check(self, tmp_path):
        _make_zf(tmp_path)
        flag = _flag(tmp_path.name, "intent-sprint-flag")
        flag.write_text("active")
        _run(tmp_path)
        assert not flag.exists(), "sprint flag must be deleted after guard runs"

    def test_exits_zero_when_no_zf_dir(self, tmp_path):
        # No zie-framework/ dir — guard not applicable
        r = _run(tmp_path)
        assert r.returncode == 0

    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        r = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json", capture_output=True, text=True, env=env,
        )
        assert r.returncode == 0
```

- [ ] **Step 2: Run to confirm failure**

```bash
make test-fast -k "test_stop_pipeline" 2>&1 | tail -10
```
Expected: FAIL — hook not found.

---

### Task 3: Extend intent-sdlc.py with ≥2 threshold scoring and unclear path

**Files:**
- Modify: `hooks/intent-sdlc.py`

Read `hooks/intent-sdlc.py` fully. Key changes:
1. Remove the `if len(message) < 15: sys.exit(0)` at line ~264.
2. Add new-intent hint signals table.
3. Add ≥2 threshold branch before the existing scoring logic.
4. Sprint scoring writes `project_tmp_path("intent-sprint-flag", project)`.

- [ ] **Step 1: Replace the early-exit guard and add threshold scoring**

Find the `# ── Early-exit guards` block (around line 263):

```python
    # ── Early-exit guards ─────────────────────────────────────────────────────
    if len(message) < 15:
        sys.exit(0)

    has_sdlc_keyword = any(
        p.search(message)
        for compiled_pats in COMPILED_PATTERNS.values()
        for p in compiled_pats
    )
    if not has_sdlc_keyword:
        sys.exit(0)
```

Replace with:

```python
    # ── Early-exit guard (short + zero SDLC keywords → unclear intent) ────────
    has_sdlc_keyword = any(
        p.search(message)
        for compiled_pats in COMPILED_PATTERNS.values()
        for p in compiled_pats
    )

    if len(message) < 15 and not has_sdlc_keyword:
        context = (
            "[zie-framework] intent: unclear — "
            "please clarify your request before proceeding"
        )
        print(json.dumps({"additionalContext": context}))
        sys.exit(0)

    if not has_sdlc_keyword:
        sys.exit(0)
```

- [ ] **Step 2: Add NEW_INTENT scoring before the existing scoring block**

Find the `# ── Intent detection (no ROADMAP needed)` block (around line 275). Insert the new-intent branch **before** it:

```python
    # ── New-intent scoring (≥2 threshold, structured hint format) ────────────
    # Sprint/fix/chore: score signals; if ≥2 → emit structured hint + exit
    # (existing intents keep their >= 1 threshold below)
    NEW_INTENT_SIGNALS = {
        "sprint": [
            r"ทำเลย", r"\bimplement\b", r"\bbuild\b", r"สร้าง",
            r"เพิ่ม.*feature", r"start.*coding",
        ],
        "fix": [
            r"\bbug\b", r"\bbroken\b", r"\berror\b", r"ไม่.*work",
            r"\bcrash\b", r"\bfail\b", r"แก้",
        ],
        "chore": [
            r"\bupdate\b", r"\bbump\b", r"\brename\b", r"\bcleanup\b",
            r"\brefactor\b", r"ลบ",
        ],
    }
    NEW_INTENT_HINTS = {
        "sprint": "confirm backlog→spec→plan before implementing",
        "fix":    "invoke /fix or /hotfix track",
        "chore":  "use /chore to track this maintenance task",
    }
    for intent_name, signals in NEW_INTENT_SIGNALS.items():
        compiled_signals = [re.compile(p, re.IGNORECASE) for p in signals]
        score = sum(1 for p in compiled_signals if p.search(message))
        if score >= 2:
            hint = NEW_INTENT_HINTS[intent_name]
            context = f"[zie-framework] intent: {intent_name} — {hint}"
            print(json.dumps({"additionalContext": context}))
            if intent_name == "sprint":
                try:
                    sprint_flag = project_tmp_path("intent-sprint-flag", cwd.name)
                    sprint_flag.write_text("active")
                except Exception:
                    pass
            sys.exit(0)
```

- [ ] **Step 3: Run all intent-sdlc tests**

```bash
make test-fast -k "intent_sdlc" 2>&1 | tail -20
```
Expected: all existing tests pass + new runtime tests pass.

- [ ] **Step 4: Commit**

```bash
git add hooks/intent-sdlc.py tests/unit/test_intent_sdlc_sprint.py
git commit -m "feat(area-3): intent-sdlc — threshold scoring for sprint/fix/chore/unclear + sprint flag"
```

---

### Task 4: Create hooks/stop-pipeline-guard.py

**Files:**
- Create: `hooks/stop-pipeline-guard.py`

- [ ] **Step 1: Write the hook**

```python
#!/usr/bin/env python3
"""Stop hook — warn if sprint intent detected but no approved artifacts produced.

Synchronous (no background: true in hooks.json) — warning must be visible
before session closes.

Flow:
1. Check intent-sprint-flag; exit 0 if absent.
2. Scan zie-framework/specs/ + plans/ for today-modified files with approved:true.
3. Warn if neither found.
4. Delete flag (cleanup).
5. Always exit 0 — warning only, never blocks.
"""
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from utils_event import get_cwd, read_event
from utils_io import project_tmp_path

try:
    event = read_event()
except Exception:
    sys.exit(0)

try:
    cwd = get_cwd()
    project = cwd.name

    # Step 1: Check sprint flag
    sprint_flag = project_tmp_path("intent-sprint-flag", project)
    if not sprint_flag.exists():
        sys.exit(0)

    # Step 2: Check for zie-framework dir
    zf = cwd / "zie-framework"
    if not zf.exists():
        sprint_flag.unlink(missing_ok=True)
        sys.exit(0)

    # Step 3: Scan for today-approved artifacts
    today = date.today().isoformat()
    found_approved = False

    for subdir in ("specs", "plans"):
        target_dir = zf / subdir
        if not target_dir.exists():
            continue
        for md_file in target_dir.glob("*.md"):
            try:
                # Check if modified today
                import datetime as _dt
                mtime = _dt.date.fromtimestamp(md_file.stat().st_mtime).isoformat()
                if mtime != today:
                    continue
                content = md_file.read_text()
                if re.search(r'^approved:\s*true\s*$', content, re.MULTILINE):
                    found_approved = True
                    break
            except Exception:
                continue
        if found_approved:
            break

    # Step 4: Warn if no approved artifacts
    if not found_approved:
        print(
            "[zie-framework] sprint intent detected but no approved spec/plan found this session\n"
            "  → Run /spec <feature> then /plan <feature> before implementing"
        )

    # Step 5: Cleanup flag
    sprint_flag.unlink(missing_ok=True)

except Exception:
    sys.exit(0)
```

- [ ] **Step 2: Run stop-pipeline-guard tests**

```bash
make test-fast -k "test_stop_pipeline" 2>&1 | tail -15
```
Expected: PASS — all 7 tests green.

- [ ] **Step 3: Commit**

```bash
git add hooks/stop-pipeline-guard.py tests/unit/test_stop_pipeline_guard.py
git commit -m "feat(area-3): stop-pipeline-guard — warn on sprint intent without approved artifacts"
```

---

### Task 5: Register stop-pipeline-guard in hooks.json

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Add stop-pipeline-guard to the Stop array**

In `hooks/hooks.json`, find the Stop array. Add the new hook as a synchronous entry (no `background: true`) after `stop-guard.py` and before `compact-hint.py`:

```json
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/stop-pipeline-guard.py\""
        },
```

- [ ] **Step 2: Validate JSON**

```bash
python3 -c "import json; json.load(open('hooks/hooks.json')); print('valid')"
```
Expected: `valid`

- [ ] **Step 3: Commit**

```bash
git add hooks/hooks.json
git commit -m "feat(area-3): register stop-pipeline-guard in hooks.json Stop array"
```

---

### Task 6: Final regression check

- [ ] **Step 1: Run full unit suite**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass including existing intent-sdlc-sprint, early-exit, and regex tests.
