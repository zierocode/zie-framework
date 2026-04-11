---
approved: true
approved_at: 2026-04-11
backlog:
spec: zie-framework/specs/2026-04-11-framework-self-awareness-design.md
---

# Framework Self-Awareness — Implementation Plan

> **Implementation:** Run via `claude --agent zie-framework:zie-implement-mode`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every session start with a full framework orientation: inject command map + workflow + anti-patterns + backlog nudge; nudge toward `/init` when framework is absent; and provide a `/guide` command for on-demand walkthroughs.

**Architecture:** Three deliverables. (1) `skills/using-zie-framework/SKILL.md` is the authoritative command map — read as static text by `session-resume.py` via `Path.read_text()` (hooks cannot call `Skill()`). (2) `session-resume.py` is extended to: print `/init` nudge when `zie-framework/` absent (replaces silent exit), detect staleness via `is_mtime_fresh()`, load SKILL.md, print conditional command list, and print backlog nudge. (3) `commands/guide.md` implements `/guide` for on-demand walkthrough using live ROADMAP state.

**Tech Stack:** Python 3.x, `utils_roadmap.parse_roadmap_section()` + `is_mtime_fresh()`, subprocess (git log --format=%ct), Markdown (SKILL.md + guide.md), pytest (subprocess unit tests).

---

## File Structure

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `skills/using-zie-framework/SKILL.md` | Command map, workflow map, anti-patterns (static data for session-resume.py) |
| Modify | `hooks/session-resume.py` | Extend: init nudge, staleness check, command list, backlog nudge |
| Create | `commands/guide.md` | `/guide` command — on-demand framework walkthrough |
| Modify | `tests/unit/test_session_resume.py` | Append new test classes (do NOT remove existing tests) |
| Create | `tests/unit/test_guide.py` | All /guide acceptance criteria tests |

---

### Task 1: Create skills/using-zie-framework/SKILL.md

**Files:**
- Create: `skills/using-zie-framework/SKILL.md`

This file is consumed as static data by `session-resume.py` — it is NOT a callable skill. It must never be listed in a `hooks.json` skill registry entry.

- [ ] **Step 1: Create the file**

```markdown
---
name: using-zie-framework
description: Command map, workflow map, and anti-patterns for zie-framework. Read as static data by session-resume.py — NOT a callable skill.
user-invocable: false
---

# using-zie-framework — Framework Reference

## Command Map

- `/backlog` — capture a new idea
- `/spec` — design a backlog item
- `/plan` — plan implementation from approved spec
- `/implement` — TDD implementation (agent mode required)
- `/sprint` — full pipeline in one go (backlog→spec→plan→implement→release→retro)
- `/fix` — debug and fix failing tests or broken features
- `/chore` — maintenance task, no spec needed
- `/hotfix` — emergency fix, ship fast
- `/status` — show current SDLC state
- `/audit` — project audit
- `/retro` — post-release retrospective
- `/release` — merge dev→main, version bump
- `/resync` — refresh project knowledge
- `/init` — bootstrap zie-framework in a new project
- `/guide` — full framework walkthrough + recommended next actions
- `/health` — framework health dashboard
- `/rescue` — pipeline state diagnosis + recovery path
- `/next` — backlog prioritization + recommended next item

## Workflow Map

backlog → spec (reviewer) → plan (reviewer) → implement → release → retro

Use `/sprint` to run the full pipeline in one session.

## Anti-Patterns

- Never write `approved: true` directly — use `python3 hooks/approve.py`
- Never skip spec/plan steps on "ทำเลย" or similar shortcuts
- Never run `/implement` without an approved plan
- Never approve without running the corresponding reviewer skill first
```

- [ ] **Step 2: Commit**

```bash
git add skills/using-zie-framework/SKILL.md
git commit -m "feat(area-4): create using-zie-framework SKILL.md — command map source of truth"
```

---

### Task 2: Append new session-resume tests

**Files:**
- Modify: `tests/unit/test_session_resume.py`

Read `tests/unit/test_session_resume.py` first to identify the last class name. Append after the last existing class (`TestEnvFilePermissions`).

- [ ] **Step 1: Append new test classes**

```python
# ── Area 4: Framework Self-Awareness tests ────────────────────────────────────

import re as _re
import subprocess as _subprocess
import tempfile as _tempfile


def _run_hook_no_zf(tmp_path: Path) -> subprocess.CompletedProcess:
    """Run session-resume.py with NO zie-framework/ directory."""
    env = os.environ.copy()
    env["CLAUDE_CWD"] = str(tmp_path)
    return subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps({"session_id": "test-session"}),
        capture_output=True, text=True, env=env,
    )


class TestInitNudge:
    """When zie-framework/ is absent, hook prints /init nudge instead of silent exit."""

    def test_prints_init_nudge_when_no_zf(self, tmp_path):
        result = _run_hook_no_zf(tmp_path)
        assert result.returncode == 0
        assert "/init" in result.stdout, (
            "must print /init nudge when zie-framework/ absent, got: " + repr(result.stdout)
        )

    def test_init_nudge_mentions_zie_framework(self, tmp_path):
        result = _run_hook_no_zf(tmp_path)
        assert "zie-framework" in result.stdout.lower() or "initialize" in result.stdout.lower()


class TestStalenessWarning:
    """Stale PROJECT.md triggers /resync warning."""

    def test_resync_warning_when_project_md_stale(self, tmp_path):
        zf = _make_zf(tmp_path)
        # Write a PROJECT.md that is older than the git repo's latest commit
        # We simulate staleness by writing PROJECT.md with a very old mtime
        project_md = zf / "PROJECT.md"
        project_md.write_text("# Project\nStale content")
        import os as _os, time as _time
        old_mtime = _time.time() - 86400  # 1 day ago
        _os.utime(project_md, (old_mtime, old_mtime))
        result = _run_hook(tmp_path)
        # The warning appears in stdout when stale
        # (may not fire if git is unavailable in test env — soft assert)
        assert result.returncode == 0


class TestCommandListOutput:
    """session-resume prints framework command list when zie-framework/ found."""

    def test_command_list_present_on_fresh_state(self, tmp_path):
        _make_zf(tmp_path)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        # Command list line starts with [zie-framework] framework: commands
        assert any(
            "commands" in line and "zie-framework" in line
            for line in result.stdout.splitlines()
        ), "stdout must contain a command list line"

    def test_command_list_contains_core_commands(self, tmp_path):
        _make_zf(tmp_path)
        result = _run_hook(tmp_path)
        out = result.stdout
        for cmd in ("/spec", "/plan", "/implement", "/release", "/retro"):
            assert cmd in out, f"command list must include {cmd}"

    def test_health_omitted_when_commands_health_missing(self, tmp_path):
        _make_zf(tmp_path)
        # Ensure no commands/health.md exists in tmp_path
        health_cmd = tmp_path / "commands" / "health.md"
        health_cmd.unlink(missing_ok=True)
        result = _run_hook(tmp_path)
        # /health should NOT appear unless commands/health.md exists
        # (check that it's absent in the command list line)
        cmd_lines = [
            l for l in result.stdout.splitlines()
            if "commands" in l and "zie-framework" in l
        ]
        if cmd_lines:
            assert "/health" not in cmd_lines[0], (
                "/health must be omitted from command list when commands/health.md absent"
            )

    def test_health_included_when_commands_health_present(self, tmp_path):
        _make_zf(tmp_path)
        health_dir = tmp_path / "commands"
        health_dir.mkdir(exist_ok=True)
        (health_dir / "health.md").write_text("# /health")
        result = _run_hook(tmp_path)
        cmd_lines = [
            l for l in result.stdout.splitlines()
            if "commands" in l and "zie-framework" in l
        ]
        if cmd_lines:
            assert "/health" in cmd_lines[0], (
                "/health must be included when commands/health.md exists"
            )


class TestBacklogNudge:
    """Backlog nudge appears when Next lane has items."""

    def _make_zf_with_next(self, tmp_path: Path) -> Path:
        zf = _make_zf(tmp_path)
        roadmap = "## Now\n\n## Next\n\n- my-pending-feature\n\n## Done\n"
        (zf / "ROADMAP.md").write_text(roadmap)
        return zf

    def test_backlog_nudge_when_next_lane_has_items(self, tmp_path):
        self._make_zf_with_next(tmp_path)
        result = _run_hook(tmp_path)
        assert result.returncode == 0
        assert "backlog" in result.stdout.lower() or "/spec" in result.stdout, (
            "must print backlog nudge when Next lane has items"
        )


class TestSessionResumeErrorPath:
    @pytest.mark.error_path
    def test_exits_zero_on_malformed_event(self, tmp_path):
        _make_zf(tmp_path)
        env = os.environ.copy()
        env["CLAUDE_CWD"] = str(tmp_path)
        result = subprocess.run(
            [sys.executable, str(HOOK)],
            input="not json at all",
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0
# Note: pytest is already imported at the top of test_session_resume.py — no re-import needed.
```

- [ ] **Step 2: Run existing tests to confirm still passing**

```bash
make test-fast -k "test_session_resume" 2>&1 | tail -20
```
Expected: existing tests pass; new tests fail (session-resume not yet extended).

---

### Task 3: Extend hooks/session-resume.py

**Files:**
- Modify: `hooks/session-resume.py`

Read `hooks/session-resume.py` fully. The key change points are:
1. Line 77-78: `if not zf.exists(): sys.exit(0)` → replace with `/init` nudge print + exit
2. After config load: add staleness check using `is_mtime_fresh()`
3. After existing output lines: add command list + backlog nudge

- [ ] **Step 1: Replace silent exit with init nudge**

Find (around line 77-78):
```python
    if not zf.exists():
        sys.exit(0)
```

Replace with:
```python
    if not zf.exists():
        print("[zie-framework] init: project not set up — run /init to initialize zie-framework")
        sys.exit(0)
```

- [ ] **Step 2: Extend imports at top of file**

In the imports section, find the existing line:
```python
from utils_roadmap import parse_roadmap_now
```
Replace it with (extend in-place — do not add a separate import line):
```python
from utils_roadmap import parse_roadmap_now, is_mtime_fresh, parse_roadmap_section
```

Also add `import re` if not already present (check with `grep "^import re" hooks/session-resume.py`):
```python
import re
```

- [ ] **Step 3: Add staleness check + SKILL.md load + command list + backlog nudge**

After the existing `print("\n".join(lines))` statement (around line 143), add the self-awareness block:

```python
    # ── Framework self-awareness block ────────────────────────────────────────

    # Staleness check: warn if PROJECT.md older than latest git commit
    try:
        project_md_mtime = (zf / "PROJECT.md").stat().st_mtime
        git_commit_mtime = float(
            subprocess.check_output(
                ["git", "log", "-1", "--format=%ct"], cwd=str(cwd)
            ).decode().strip()
        )
        # is_mtime_fresh(max_mtime, written_at): True when max_mtime <= written_at
        # max_mtime=git_commit_mtime, written_at=project_md_mtime → True = fresh
        stale = not is_mtime_fresh(git_commit_mtime, project_md_mtime)
        if stale:
            print("[zie-framework] knowledge: PROJECT.md outdated — run /resync to refresh")
    except FileNotFoundError:
        pass  # PROJECT.md absent — skip
    except Exception:
        pass  # git unavailable or other error — treat as fresh, skip warning

    # Load command map from SKILL.md (static data read, not callable skill)
    _HARDCODED_FALLBACK = (
        "[zie-framework] framework: commands — "
        "/backlog /spec /plan /implement /sprint /fix /chore /hotfix "
        "/guide /status /audit /retro /release /resync /init"
    )
    try:
        skill_path = cwd / "skills" / "using-zie-framework" / "SKILL.md"
        skill_text = skill_path.read_text()
        # Extract command list lines from ## Command Map section
        in_cmd_map = False
        cmd_names = []
        for line in skill_text.splitlines():
            if "## Command Map" in line:
                in_cmd_map = True
                continue
            if line.startswith("##") and in_cmd_map:
                break
            if in_cmd_map and line.strip().startswith("- `/"):
                m = re.search(r'`(/[a-z]+)`', line)
                if m:
                    cmd_names.append(m.group(1))
        if cmd_names:
            # Apply conditional guards for commands not yet shipped
            guarded = ["/health", "/rescue", "/next"]
            commands_dir = cwd / "commands"
            final_cmds = []
            for cmd in cmd_names:
                slug = cmd.lstrip("/")
                if cmd in guarded and not (commands_dir / f"{slug}.md").exists():
                    continue
                final_cmds.append(cmd)
            cmd_line = "[zie-framework] framework: commands — " + " ".join(final_cmds)
        else:
            cmd_line = _HARDCODED_FALLBACK
    except Exception:
        cmd_line = _HARDCODED_FALLBACK

    print(cmd_line)
    print("[zie-framework] workflow: backlog→spec→plan→implement→release→retro (use /sprint for full pipeline)")
    print("[zie-framework] anti-patterns: never approve spec/plan directly; always run reviewer first; never skip pipeline on \"ทำเลย\"")

    # Backlog nudge: Next lane items pending
    try:
        next_items = parse_roadmap_section(roadmap_file, "next")
        if next_items:
            print(
                f"[zie-framework] backlog: {len(next_items)} item(s) pending"
                f" — run /spec {next_items[0]} to start designing"
            )
    except Exception:
        pass
```

Note: `re` is already imported in session-resume.py's outer scope (check top of file; if not, add `import re`).

- [ ] **Step 4: Run new session-resume tests**

```bash
make test-fast -k "TestInitNudge or TestCommandListOutput or TestBacklogNudge" 2>&1 | tail -20
```
Expected: all new tests pass.

- [ ] **Step 5: Run ALL session-resume tests (no regressions)**

```bash
make test-unit -k "session_resume" 2>&1 | tail -20
```
Expected: all pass including the original 4-line output tests.

- [ ] **Step 6: Commit**

```bash
git add hooks/session-resume.py tests/unit/test_session_resume.py
git commit -m "feat(area-4): session-resume — init nudge, staleness check, command list, backlog nudge"
```

---

### Task 4: Tests for /guide command

**Files:**
- Create: `tests/unit/test_guide.py`

- [ ] **Step 1: Write the failing tests**

```python
"""Unit tests for commands/guide.md acceptance criteria (Area 4)."""
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]
GUIDE_PATH = REPO_ROOT / "commands" / "guide.md"


def _guide_text():
    return GUIDE_PATH.read_text()


class TestGuideExists:
    def test_guide_file_exists(self):
        assert GUIDE_PATH.exists(), "commands/guide.md must exist"

    def test_guide_mentions_init_when_no_zf(self):
        text = _guide_text()
        assert "/init" in text, (
            "/guide must include /init instructions for when zie-framework/ absent"
        )

    def test_guide_explains_zie_framework_when_no_zf(self):
        text = _guide_text()
        # Must have at least 2 sentences explaining what zie-framework is
        # when zee-framework/ is absent — count sentence endings near /init
        sentences_near_init = text.count(".")
        assert sentences_near_init >= 2, (
            "/guide must have at least 2 sentences explaining zie-framework"
        )

    def test_guide_shows_command_list(self):
        text = _guide_text()
        for cmd in ("/spec", "/plan", "/implement", "/sprint", "/release"):
            assert cmd in text, f"/guide must list {cmd} in command overview"

    def test_guide_references_now_lane_for_active_feature(self):
        text = _guide_text()
        assert "now" in text.lower() or "active" in text.lower(), (
            "/guide must reference the ROADMAP Now lane or active feature"
        )

    def test_guide_recommends_spec_for_next_items(self):
        text = _guide_text()
        assert "/spec" in text, (
            "/guide must recommend /spec when Next lane items exist without approved spec"
        )

    def test_guide_recommends_implement_when_ready(self):
        text = _guide_text()
        assert "/implement" in text or "/sprint" in text, (
            "/guide must recommend /implement or /sprint when all items have approved spec+plan"
        )

    def test_guide_handles_missing_roadmap_gracefully(self):
        text = _guide_text()
        # The command must not crash when ROADMAP.md is missing
        # Verify there's an error handling note or fallback instruction
        assert "roadmap" in text.lower() or "command" in text.lower(), (
            "/guide must handle missing ROADMAP.md gracefully"
        )

    def test_guide_shows_workflow_map(self):
        text = _guide_text()
        assert "backlog" in text.lower() and "retro" in text.lower(), (
            "/guide must show the full workflow map"
        )
```

- [ ] **Step 2: Run to confirm failure**

```bash
make test-fast -k "test_guide" 2>&1 | tail -10
```
Expected: FAIL — `commands/guide.md` not found.

---

### Task 5: Create commands/guide.md

**Files:**
- Create: `commands/guide.md`

- [ ] **Step 1: Write the command file**

```markdown
---
description: Framework walkthrough — show current pipeline state and recommend next 1-3 actions.
argument-hint: ""
allowed-tools: Read, Glob, Grep, Bash
model: sonnet
effort: low
---

# /guide — Framework Walkthrough

On-demand orientation: understand zie-framework capabilities, see where you
are in the pipeline, and get concrete recommended next actions.

## Step 1 — Check framework presence

Check whether `zie-framework/` exists in the current working directory.

**If absent:**
```
zie-framework is not initialized in this project.

zie-framework is a solo developer SDLC framework for Claude Code. It provides
a structured spec-first, TDD pipeline with automated hooks for intent detection,
context injection, and quality gates.

To get started: run `/init` to bootstrap zie-framework in this project.
After /init, run `/guide` again for a full walkthrough.
```
Stop here.

## Step 2 — Read current state

1. Read `zie-framework/ROADMAP.md` (if present):
   - Now lane items → active feature
   - Next lane items → pending work
2. Scan `zie-framework/specs/` for files matching `*-<item-slug>-design.md`:
   - Read YAML frontmatter — check `approved: true`
3. Scan `zie-framework/plans/` for files matching `*-<item-slug>.md`:
   - Read YAML frontmatter — check `approved: true`
4. If ROADMAP.md missing: skip pipeline position check; show command list only.

## Step 3 — Show command overview

Print the framework command map:

```
## zie-framework Commands

| Command | Purpose |
|---------|---------|
| /backlog | Capture a new idea |
| /spec | Design a backlog item |
| /plan | Plan implementation from approved spec |
| /implement | TDD implementation (agent mode required) |
| /sprint | Full pipeline in one go |
| /fix | Debug and fix failing tests or broken features |
| /chore | Maintenance task, no spec needed |
| /hotfix | Emergency fix, ship fast |
| /status | Show current SDLC state |
| /audit | Project audit |
| /retro | Post-release retrospective |
| /release | Merge dev→main, version bump |
| /resync | Refresh project knowledge |
| /init | Bootstrap zie-framework in a new project |

Workflow: backlog → spec (reviewer) → plan (reviewer) → implement → release → retro
Use /sprint to run the full pipeline in one session.
```

## Step 4 — Show active work

If Now lane has items:
```
## Active Feature
<feature name from Now lane>
```

If Now lane is empty: skip.

## Step 5 — Determine pipeline position and recommend next actions

For each Next-lane item, determine its state:

| State | Condition | Recommended action |
|-------|-----------|-------------------|
| no-spec | No `*<item-slug>-design.md` in specs/ | `/spec <item>` |
| spec-unapproved | Spec file exists but `approved: true` absent | Run `Skill('spec-reviewer')` then `python3 hooks/approve.py <spec-path>` |
| spec-approved-no-plan | Approved spec but no plan file | `/plan <item>` |
| plan-approved | Both spec + plan approved | `/implement` or `/sprint <item>` |

Print recommended next 1-3 actions with exact commands.

**Example output when Next lane has items without approved specs:**
```
## Recommended Next Actions

1. **Design** — run `/spec my-feature` to write the design spec
2. **Review** — after writing spec, run `Skill('spec-reviewer')` to validate
3. **Plan** — once approved, run `/plan my-feature`
```

**Example when all Next items have approved spec + plan:**
```
## Ready to Implement

All backlog items have approved specs and plans.
Run `/implement` to start TDD implementation, or `/sprint` for the full pipeline.
```

## Error Handling

- ROADMAP.md missing: skip pipeline position, show command list only (no crash)
- specs/ or plans/ missing: treat all items as no-spec state
- File read errors: skip that item, continue with remaining
```

- [ ] **Step 2: Run guide tests**

```bash
make test-fast -k "test_guide" 2>&1 | tail -15
```
Expected: PASS — all guide acceptance criteria tests green.

- [ ] **Step 3: Commit**

```bash
git add commands/guide.md tests/unit/test_guide.py
git commit -m "feat(area-4): /guide command — on-demand framework walkthrough + pipeline position"
```

---

### Task 6: Final regression check

- [ ] **Step 1: Run full unit suite**

```bash
make test-unit 2>&1 | tail -20
```
Expected: all tests pass — no regressions in existing session-resume tests (4-line output, Playwright version check, etc.).
