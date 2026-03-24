---
approved: false
approved_at: ~
backlog: backlog/session-resume-compression.md
spec: specs/2026-03-24-session-resume-compression-design.md
---

# Session-Resume Hook Output Compression — Implementation Plan

**Goal:** Compress `hooks/session-resume.py` output from 5–6 lines (active-feature path) down to exactly 4 lines, matching the spec's target format.
**Architecture:** Single-file change — replace the multi-line active-feature branch with a single `Active:` line. All data-gathering logic (config, roadmap, version) is unchanged; only the print section changes.
**Tech Stack:** Python 3.x (hook), pytest (unit tests)

---

## Current vs Target Output

Current output when a feature is active (5–6 lines — exceeds spec):
```
[zie-framework] <project> (<type>) v<version>
  Active  : <feature>
  Plan    : zie-framework/plans/<plan>.md
  Backlog : N items in Next
  Brain   : enabled|disabled
  → Run /zie-status for full state
```

Target output (always exactly 4 lines):
```
[zie-framework] <project> (<type>) v<version>
  Active: <feature name or "No active feature — run /zie-backlog to start one">
  Brain: enabled|disabled
  → Run /zie-status for full state
```

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/session-resume.py` | Replace 5-6 line print block with 4-line format |
| Create | `tests/unit/test_session_resume.py` | Unit tests: mock inputs, assert output format |

---

## Task 1: Write tests + implement the 4-line output

<!-- depends_on: none -->

**Acceptance Criteria:**
- Hook output is always exactly 4 lines regardless of whether a feature is active
- Line 1: `[zie-framework] <project> (<type>) v<version>`
- Line 2: `  Active: <feature>` or `  Active: No active feature — run /zie-backlog to start one`
- Line 3: `  Brain: enabled` or `  Brain: disabled`
- Line 4: `  → Run /zie-status for full state`
- Hook still exits 0 and never crashes (existing outer guard unchanged)
- `tests/unit/test_session_resume.py` passes under `make test-unit`

**Files:**
- Create: `tests/unit/test_session_resume.py`
- Modify: `hooks/session-resume.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_session_resume.py
  """Unit tests for hooks/session-resume.py output format.

  Strategy: run the hook as a subprocess with a synthetic CLAUDE_CWD pointing
  to a temp directory that contains a minimal zie-framework/ tree, then assert
  on stdout directly.
  """
  import json
  import os
  import sys
  import subprocess
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  HOOK = REPO_ROOT / "hooks" / "session-resume.py"


  def _make_zf(tmp_path: Path, *, version="1.0.0", project_type="lib",
               zie_memory=False, now_items=None) -> Path:
      """Build a minimal zie-framework scaffold under tmp_path."""
      zf = tmp_path / "zie-framework"
      zf.mkdir()

      # VERSION file at project root (tmp_path acts as project root)
      (tmp_path / "VERSION").write_text(version)

      # .config
      config = {"project_type": project_type, "zie_memory_enabled": zie_memory}
      (zf / ".config").write_text(json.dumps(config))

      # ROADMAP.md — build minimal Now section
      if now_items:
          now_block = "\n".join(f"- {item}" for item in now_items)
          roadmap = f"## Now\n\n{now_block}\n\n## Next\n\n## Backlog\n"
      else:
          roadmap = "## Now\n\n## Next\n\n## Backlog\n"
      (zf / "ROADMAP.md").write_text(roadmap)

      return zf


  def _run_hook(tmp_path: Path) -> subprocess.CompletedProcess:
      """Run session-resume.py with CLAUDE_CWD pointing at tmp_path."""
      env = os.environ.copy()
      env["CLAUDE_CWD"] = str(tmp_path)
      # Provide valid JSON on stdin (SessionStart event shape)
      stdin_data = json.dumps({"session_id": "test-session"})
      return subprocess.run(
          [sys.executable, str(HOOK)],
          input=stdin_data,
          capture_output=True,
          text=True,
          env=env,
      )


  class TestOutputLineCount:
      def test_no_active_feature_is_exactly_4_lines(self, tmp_path):
          _make_zf(tmp_path, now_items=None)
          result = _run_hook(tmp_path)
          assert result.returncode == 0
          lines = result.stdout.strip().splitlines()
          assert len(lines) == 4, (
              f"Expected 4 lines, got {len(lines)}:\n{result.stdout}"
          )

      def test_with_active_feature_is_exactly_4_lines(self, tmp_path):
          _make_zf(tmp_path, now_items=["session-resume-compression"])
          result = _run_hook(tmp_path)
          assert result.returncode == 0
          lines = result.stdout.strip().splitlines()
          assert len(lines) == 4, (
              f"Expected 4 lines, got {len(lines)}:\n{result.stdout}"
          )


  class TestOutputFormat:
      def test_line1_contains_project_type_version(self, tmp_path):
          _make_zf(tmp_path, version="2.3.4", project_type="plugin")
          result = _run_hook(tmp_path)
          assert result.returncode == 0
          line1 = result.stdout.strip().splitlines()[0]
          assert "[zie-framework]" in line1
          assert "(plugin)" in line1
          assert "v2.3.4" in line1

      def test_line2_active_feature_present(self, tmp_path):
          _make_zf(tmp_path, now_items=["my-cool-feature"])
          result = _run_hook(tmp_path)
          lines = result.stdout.strip().splitlines()
          assert lines[1].startswith("  Active:")
          assert "my-cool-feature" in lines[1]

      def test_line2_no_active_feature_fallback(self, tmp_path):
          _make_zf(tmp_path, now_items=None)
          result = _run_hook(tmp_path)
          lines = result.stdout.strip().splitlines()
          assert lines[1].startswith("  Active:")
          assert "No active feature" in lines[1]
          assert "/zie-backlog" in lines[1]

      def test_line3_brain_enabled(self, tmp_path):
          _make_zf(tmp_path, zie_memory=True)
          result = _run_hook(tmp_path)
          lines = result.stdout.strip().splitlines()
          assert lines[2] == "  Brain: enabled"

      def test_line3_brain_disabled(self, tmp_path):
          _make_zf(tmp_path, zie_memory=False)
          result = _run_hook(tmp_path)
          lines = result.stdout.strip().splitlines()
          assert lines[2] == "  Brain: disabled"

      def test_line4_zie_status_hint(self, tmp_path):
          _make_zf(tmp_path)
          result = _run_hook(tmp_path)
          lines = result.stdout.strip().splitlines()
          assert lines[3] == "  → Run /zie-status for full state"


  class TestHookSafety:
      def test_exits_zero_when_no_zf_directory(self, tmp_path):
          """Hook must exit 0 and produce no output when zie-framework/ absent."""
          result = _run_hook(tmp_path)
          assert result.returncode == 0

      def test_exits_zero_on_malformed_stdin(self, tmp_path):
          _make_zf(tmp_path)
          env = os.environ.copy()
          env["CLAUDE_CWD"] = str(tmp_path)
          result = subprocess.run(
              [sys.executable, str(HOOK)],
              input="not json at all",
              capture_output=True,
              text=True,
              env=env,
          )
          assert result.returncode == 0

      def test_exits_zero_on_empty_stdin(self, tmp_path):
          _make_zf(tmp_path)
          env = os.environ.copy()
          env["CLAUDE_CWD"] = str(tmp_path)
          result = subprocess.run(
              [sys.executable, str(HOOK)],
              input="",
              capture_output=True,
              text=True,
              env=env,
          )
          assert result.returncode == 0
  ```

  Run: `make test-unit` — `test_with_active_feature_is_exactly_4_lines` must FAIL (current hook outputs 6 lines when active)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/session-resume.py`, replace lines 80–96 (the `lines = [...]` build block through `print`) with:

  ```python
  # Active feature: first Now item, or fallback message
  if now_items:
      active_label = now_items[0]
  else:
      active_label = "No active feature — run /zie-backlog to start one"

  lines = [
      f"[zie-framework] {project_name} ({project_type}) v{version}",
      f"  Active: {active_label}",
      f"  Brain: {'enabled' if zie_memory else 'disabled'}",
      "  → Run /zie-status for full state",
  ]

  print("\n".join(lines))
  ```

  All variables (`project_name`, `project_type`, `version`, `now_items`, `zie_memory`) are already computed above this block — no other changes needed.

  Run: `make test-unit` — all tests must PASS

- [ ] **Step 3: Refactor**

  Read `hooks/session-resume.py` in full. Confirm:
  - The env-file injection block (lines ~50–78) is completely untouched
  - The `active_plan` and `next_items` variables are still computed (they may be used by future hooks or `/zie-status`) — if they are now unused in this file, remove only those assignments to avoid dead code. Do not remove the `parse_roadmap_section` call if it is referenced elsewhere.
  - No logic beyond the print block has changed.

  Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/session-resume.py tests/unit/test_session_resume.py && git commit -m "feat: compress session-resume hook output to 4 lines"`*
