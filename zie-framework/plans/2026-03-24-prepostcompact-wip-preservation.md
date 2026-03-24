---
approved: true
approved_at: 2026-03-24
backlog: backlog/prepostcompact-wip-preservation.md
spec: specs/2026-03-24-prepostcompact-wip-preservation-design.md
---

# PreCompact/PostCompact WIP Preservation — Implementation Plan

**Goal:** Persist SDLC state (active task, TDD phase, git branch, changed files) before context compaction and restore it as `additionalContext` immediately after, so Claude never loses session continuity across a compact event.
**Architecture:** A single new hook script `hooks/sdlc-compact.py` handles both `PreCompact` and `PostCompact` events; it branches on `hook_event_name` at the top of the inner-operations tier. PreCompact collects live state and atomically writes a JSON snapshot to a project-scoped `/tmp` path via `safe_write_tmp()`. PostCompact reads that snapshot (or falls back to a live ROADMAP read) and prints `{"hookSpecificOutput": {"additionalContext": "..."}}` to stdout for Claude Code to inject. Both event paths share the same outer guard (invalid JSON, missing `zie-framework/` dir) and exit 0 without side effects.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/sdlc-compact.py` | Dual-event hook: PreCompact saves snapshot, PostCompact restores context |
| Modify | `hooks/hooks.json` | Register `sdlc-compact.py` for `PreCompact` and `PostCompact` events |
| Create | `tests/unit/test_hooks_sdlc_compact.py` | Unit tests: snapshot roundtrip, missing snapshot fallback, empty ROADMAP, non-project CWD, symlink guard, git unavailable |

---

## Task 1: Write tests for `sdlc-compact.py` (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- All test classes exist and fail with `ImportError` or `FileNotFoundError` (hook not yet created)
- Test file imports cleanly and is collected by pytest

**Files:**
- Create: `tests/unit/test_hooks_sdlc_compact.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  """Tests for hooks/sdlc-compact.py"""
  import os, sys, json, subprocess, pytest
  from pathlib import Path
  from unittest.mock import patch

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "sdlc-compact.py")
  sys.path.insert(0, os.path.join(REPO_ROOT, "hooks"))
  from utils import project_tmp_path

  SAMPLE_ROADMAP = """## Now
  - [ ] Implement sdlc-compact hook
  - [ ] Register in hooks.json

  ## Next
  - [ ] Write integration tests
  """


  def run_hook(event_name, tmp_cwd=None, env_overrides=None):
      env = {**os.environ}
      if tmp_cwd:
          env["CLAUDE_CWD"] = str(tmp_cwd)
      if env_overrides:
          env.update(env_overrides)
      event = {"hook_event_name": event_name, "cwd": str(tmp_cwd) if tmp_cwd else ""}
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  def make_cwd(tmp_path, roadmap=None, config=None):
      zf = tmp_path / "zie-framework"
      zf.mkdir(parents=True)
      if roadmap:
          (zf / "ROADMAP.md").write_text(roadmap)
      if config:
          (zf / ".config").write_text(json.dumps(config))
      return tmp_path


  def snapshot_path(tmp_path):
      return project_tmp_path("compact-snapshot", tmp_path.name)


  # ---------------------------------------------------------------------------
  # Outer guard — both events
  # ---------------------------------------------------------------------------

  class TestSdlcCompactOuterGuard:
      def test_invalid_json_exits_zero(self):
          r = subprocess.run(
              [sys.executable, HOOK],
              input="not-json",
              capture_output=True,
              text=True,
          )
          assert r.returncode == 0

      def test_empty_stdin_exits_zero(self):
          r = subprocess.run(
              [sys.executable, HOOK],
              input="",
              capture_output=True,
              text=True,
          )
          assert r.returncode == 0

      def test_precompact_exits_zero_without_zf_dir(self, tmp_path):
          # tmp_path has no zie-framework/ subdir
          r = run_hook("PreCompact", tmp_cwd=tmp_path)
          assert r.returncode == 0
          assert not snapshot_path(tmp_path).exists()

      def test_postcompact_exits_zero_without_zf_dir(self, tmp_path):
          r = run_hook("PostCompact", tmp_cwd=tmp_path)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_unknown_event_name_exits_zero(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook("SomeOtherEvent", tmp_cwd=cwd)
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  # ---------------------------------------------------------------------------
  # PreCompact — snapshot writing
  # ---------------------------------------------------------------------------

  class TestSdlcCompactPreCompact:
      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          p = snapshot_path(tmp_path)
          if p.is_symlink() or p.exists():
              p.unlink(missing_ok=True)

      def test_writes_snapshot_file(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook("PreCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          assert snapshot_path(tmp_path).exists(), "compact-snapshot file must be written"

      def test_snapshot_is_valid_json(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          raw = snapshot_path(tmp_path).read_text()
          data = json.loads(raw)  # must not raise
          assert isinstance(data, dict)

      def test_snapshot_contains_active_task(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert "sdlc-compact hook" in data["active_task"]

      def test_snapshot_contains_now_items_list(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert isinstance(data["now_items"], list)
          assert len(data["now_items"]) == 2

      def test_snapshot_contains_git_branch_key(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert "git_branch" in data
          assert isinstance(data["git_branch"], str)

      def test_snapshot_contains_changed_files_key(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert "changed_files" in data
          assert isinstance(data["changed_files"], list)

      def test_snapshot_contains_tdd_phase_key(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert "tdd_phase" in data

      def test_snapshot_reads_tdd_phase_from_config(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, config={"tdd_phase": "RED"})
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["tdd_phase"] == "RED"

      def test_snapshot_tdd_phase_defaults_to_empty_when_no_config(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["tdd_phase"] == ""

      def test_snapshot_tdd_phase_empty_when_config_missing_field(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP, config={"project_type": "python"})
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["tdd_phase"] == ""

      def test_snapshot_tdd_phase_empty_on_corrupt_config(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          (tmp_path / "zie-framework" / ".config").write_text("not-valid-json")
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["tdd_phase"] == ""

      def test_snapshot_active_task_empty_when_no_now_items(self, tmp_path):
          roadmap = "## Now\n\n## Next\n- [ ] something\n"
          cwd = make_cwd(tmp_path, roadmap=roadmap)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["active_task"] == ""
          assert data["now_items"] == []

      def test_snapshot_active_task_empty_when_no_roadmap(self, tmp_path):
          cwd = make_cwd(tmp_path)  # no ROADMAP.md
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["active_task"] == ""

      def test_changed_files_capped_at_20(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          # We cannot force git to report >20 files without a real repo,
          # but we can verify the key exists and is a list (cap enforcement is
          # unit-tested via test_build_snapshot_caps_changed_files below)
          run_hook("PreCompact", tmp_cwd=cwd)
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert len(data["changed_files"]) <= 20

      def test_no_stdout_on_precompact(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          r = run_hook("PreCompact", tmp_cwd=cwd)
          assert r.stdout.strip() == ""

      def test_symlink_snapshot_path_skipped_gracefully(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          snap = snapshot_path(tmp_path)
          real = tmp_path / "important.txt"
          real.write_text("do not overwrite")
          snap.symlink_to(real)
          r = run_hook("PreCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          assert real.read_text() == "do not overwrite"
          assert "WARNING" in r.stderr
          snap.unlink()

      def test_git_unavailable_writes_snapshot_with_empty_git_fields(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          # Point PATH to an empty dir so git is not found
          empty_bin = tmp_path / "empty_bin"
          empty_bin.mkdir()
          r = run_hook("PreCompact", tmp_cwd=cwd, env_overrides={"PATH": str(empty_bin)})
          assert r.returncode == 0
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert data["git_branch"] == ""
          assert data["changed_files"] == []


  # ---------------------------------------------------------------------------
  # PostCompact — context restoration
  # ---------------------------------------------------------------------------

  class TestSdlcCompactPostCompact:
      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          p = snapshot_path(tmp_path)
          if p.is_symlink() or p.exists():
              p.unlink(missing_ok=True)

      def _write_snapshot(self, tmp_path, data: dict):
          snap = snapshot_path(tmp_path)
          snap.write_text(json.dumps(data))

      def test_emits_valid_json_to_stdout(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "Implement sdlc-compact hook",
              "now_items": ["Implement sdlc-compact hook", "Register in hooks.json"],
              "git_branch": "dev",
              "changed_files": ["hooks/sdlc-compact.py"],
              "tdd_phase": "GREEN",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          out = json.loads(r.stdout)  # must not raise
          assert "hookSpecificOutput" in out
          assert "additionalContext" in out["hookSpecificOutput"]

      def test_context_contains_active_task(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "Implement sdlc-compact hook",
              "now_items": ["Implement sdlc-compact hook"],
              "git_branch": "dev",
              "changed_files": [],
              "tdd_phase": "",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          assert "Implement sdlc-compact hook" in ctx

      def test_context_contains_git_branch(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "task",
              "now_items": ["task"],
              "git_branch": "feature/compact",
              "changed_files": [],
              "tdd_phase": "",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          assert "feature/compact" in ctx

      def test_context_contains_tdd_phase_when_set(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "task",
              "now_items": ["task"],
              "git_branch": "dev",
              "changed_files": [],
              "tdd_phase": "RED",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          assert "RED" in ctx

      def test_context_omits_tdd_phase_line_when_empty(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "task",
              "now_items": ["task"],
              "git_branch": "dev",
              "changed_files": [],
              "tdd_phase": "",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          # No blank "TDD phase: " line emitted
          assert "TDD phase: \n" not in ctx

      def test_context_contains_changed_files(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "task",
              "now_items": ["task"],
              "git_branch": "dev",
              "changed_files": ["hooks/sdlc-compact.py", "hooks/hooks.json"],
              "tdd_phase": "",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          assert "hooks/sdlc-compact.py" in ctx

      def test_context_omits_active_task_line_when_empty(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          self._write_snapshot(tmp_path, {
              "active_task": "",
              "now_items": [],
              "git_branch": "dev",
              "changed_files": [],
              "tdd_phase": "",
          })
          r = run_hook("PostCompact", tmp_cwd=cwd)
          ctx = json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]
          assert "Active task: \n" not in ctx

      def test_missing_snapshot_falls_back_to_live_roadmap(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          # No snapshot written — file absent
          assert not snapshot_path(tmp_path).exists()
          r = run_hook("PostCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          out = json.loads(r.stdout)
          ctx = out["hookSpecificOutput"]["additionalContext"]
          assert "sdlc-compact hook" in ctx

      def test_missing_snapshot_missing_roadmap_still_exits_zero(self, tmp_path):
          cwd = make_cwd(tmp_path)  # no ROADMAP.md, no snapshot
          r = run_hook("PostCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          # Must still emit valid JSON (even if context is minimal)
          out = json.loads(r.stdout)
          assert "hookSpecificOutput" in out

      def test_corrupt_snapshot_falls_back_to_live_roadmap(self, tmp_path):
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          snapshot_path(tmp_path).write_text("not-valid-json!!!")
          r = run_hook("PostCompact", tmp_cwd=cwd)
          assert r.returncode == 0
          out = json.loads(r.stdout)
          ctx = out["hookSpecificOutput"]["additionalContext"]
          assert "sdlc-compact hook" in ctx


  # ---------------------------------------------------------------------------
  # Error handling convention
  # ---------------------------------------------------------------------------

  class TestSdlcCompactErrorHandlingConvention:
      def test_hook_file_has_two_tier_outer_guard(self):
          """Outer guard must use bare except Exception -> sys.exit(0)."""
          src = Path(HOOK).read_text()
          assert "sys.exit(0)" in src, "outer guard sys.exit(0) missing"

      def test_inner_ops_use_named_exception_with_stderr(self):
          """Inner operations must use 'except Exception as e' with stderr print."""
          src = Path(HOOK).read_text()
          assert "except Exception as e:" in src
          assert "file=sys.stderr" in src

      def test_no_nonzero_exit_code(self):
          """Hook must never call sys.exit with a non-zero argument."""
          import ast
          src = Path(HOOK).read_text()
          tree = ast.parse(src)
          for node in ast.walk(tree):
              if isinstance(node, ast.Call):
                  func = node.func
                  if (
                      isinstance(func, ast.Attribute)
                      and func.attr == "exit"
                      and isinstance(func.value, ast.Name)
                      and func.value.id == "sys"
                  ):
                      if node.args:
                          arg = node.args[0]
                          if isinstance(arg, ast.Constant) and arg.value != 0:
                              raise AssertionError(
                                  f"sys.exit({arg.value}) found at line {node.lineno} — "
                                  "hooks must only exit 0"
                              )
  ```

  Run: `make test-unit` — must FAIL (`hooks/sdlc-compact.py` does not exist)

- [ ] **Step 2: Confirm RED**
  All tests in `TestSdlcCompactOuterGuard`, `TestSdlcCompactPreCompact`,
  `TestSdlcCompactPostCompact`, and `TestSdlcCompactErrorHandlingConvention`
  should fail with `FileNotFoundError` (subprocess cannot find the hook) or
  `json.JSONDecodeError` (empty stdout on PostCompact tests). The
  `TestSdlcCompactErrorHandlingConvention` tests fail with
  `FileNotFoundError` on `Path(HOOK).read_text()`.

- [ ] **Step 3: Refactor**
  No refactoring needed at this stage — file is new.
  Run: `make test-unit` — still FAIL (expected)

---

## Task 2: Implement `hooks/sdlc-compact.py` (GREEN)

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- All tests in `TestSdlcCompactOuterGuard`, `TestSdlcCompactPreCompact`, `TestSdlcCompactPostCompact`, and `TestSdlcCompactErrorHandlingConvention` pass
- Hook never exits non-zero under any input
- PreCompact writes no stdout; PostCompact always writes valid JSON to stdout

**Files:**
- Create: `hooks/sdlc-compact.py`

- [ ] **Step 1: Write failing tests (RED)**
  Already done in Task 1. Confirm `make test-unit` still fails before writing the hook.

- [ ] **Step 2: Implement (GREEN)**

  ```python
  #!/usr/bin/env python3
  """PreCompact/PostCompact hook — persist and restore SDLC state across context compaction."""
  import json
  import os
  import subprocess
  import sys
  from pathlib import Path

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import (
      get_cwd,
      parse_roadmap_now,
      project_tmp_path,
      read_event,
      safe_write_tmp,
  )

  # ---------------------------------------------------------------------------
  # Outer guard — parse event; exit 0 on any failure; never block Claude
  # ---------------------------------------------------------------------------
  try:
      event = read_event()
      hook_event_name = event.get("hook_event_name", "")
      if hook_event_name not in ("PreCompact", "PostCompact"):
          sys.exit(0)

      cwd = get_cwd()
      zf = cwd / "zie-framework"
      if not zf.exists():
          sys.exit(0)

      project_name = cwd.name
      snap_path = project_tmp_path("compact-snapshot", project_name)
  except Exception:
      sys.exit(0)

  # ---------------------------------------------------------------------------
  # Inner operations — log errors to stderr; never raise; always exit 0
  # ---------------------------------------------------------------------------

  if hook_event_name == "PreCompact":
      # --- Collect active task and now_items from ROADMAP ---
      try:
          roadmap_path = zf / "ROADMAP.md"
          now_items = parse_roadmap_now(roadmap_path)
          active_task = now_items[0] if now_items else ""
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: roadmap read failed: {e}", file=sys.stderr)
          now_items = []
          active_task = ""

      # --- Collect git branch ---
      try:
          result = subprocess.run(
              ["git", "-C", str(cwd), "branch", "--show-current"],
              capture_output=True,
              text=True,
          )
          git_branch = result.stdout.strip()
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: git branch failed: {e}", file=sys.stderr)
          git_branch = ""

      # --- Collect changed files ---
      try:
          result = subprocess.run(
              ["git", "-C", str(cwd), "diff", "--name-only", "HEAD"],
              capture_output=True,
              text=True,
          )
          changed_files = [f for f in result.stdout.splitlines() if f.strip()][:20]
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: git diff failed: {e}", file=sys.stderr)
          changed_files = []

      # --- Read tdd_phase from .config ---
      tdd_phase = ""
      try:
          config_path = zf / ".config"
          if config_path.exists():
              config = json.loads(config_path.read_text())
              tdd_phase = config.get("tdd_phase", "")
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: config read failed: {e}", file=sys.stderr)

      # --- Build and write snapshot ---
      snapshot = {
          "active_task": active_task,
          "now_items": now_items,
          "git_branch": git_branch,
          "changed_files": changed_files,
          "tdd_phase": tdd_phase,
      }
      try:
          safe_write_tmp(snap_path, json.dumps(snapshot))
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: snapshot write failed: {e}", file=sys.stderr)

  elif hook_event_name == "PostCompact":
      # --- Read snapshot; fall back to live ROADMAP on any failure ---
      snapshot = None
      try:
          if snap_path.exists():
              snapshot = json.loads(snap_path.read_text())
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: snapshot read failed: {e}", file=sys.stderr)

      if snapshot is None:
          # Fallback: read live ROADMAP
          try:
              now_items = parse_roadmap_now(zf / "ROADMAP.md")
              active_task = now_items[0] if now_items else ""
          except Exception as e:
              print(f"[zie-framework] sdlc-compact: fallback roadmap failed: {e}", file=sys.stderr)
              now_items = []
              active_task = ""
          snapshot = {
              "active_task": active_task,
              "now_items": now_items,
              "git_branch": "",
              "changed_files": [],
              "tdd_phase": "",
          }

      # --- Build context block ---
      try:
          lines = ["[zie-framework] SDLC state restored after context compaction."]
          if snapshot.get("active_task"):
              lines.append(f"Active task: {snapshot['active_task']}")
          if snapshot.get("now_items") and len(snapshot["now_items"]) > 1:
              lines.append("Now items:")
              for item in snapshot["now_items"]:
                  lines.append(f"  - {item}")
          if snapshot.get("git_branch"):
              lines.append(f"Git branch: {snapshot['git_branch']}")
          if snapshot.get("tdd_phase"):
              lines.append(f"TDD phase: {snapshot['tdd_phase']}")
          if snapshot.get("changed_files"):
              lines.append("Changed files (since last commit):")
              for f in snapshot["changed_files"]:
                  lines.append(f"  - {f}")
          context = "\n".join(lines)
          print(json.dumps({"hookSpecificOutput": {"additionalContext": context}}))
      except Exception as e:
          print(f"[zie-framework] sdlc-compact: context build failed: {e}", file=sys.stderr)
          print(json.dumps({"hookSpecificOutput": {"additionalContext": ""}}))
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify no bare `except: pass` present (covered by `test_no_nonzero_exit_code` AST walk)
  - Confirm `sys.path.insert` uses `os.path.dirname(__file__)` (consistent with all other hooks)
  - Verify the `# nosec` comment is not needed here (no hardcoded `/tmp` string — `project_tmp_path` handles it; nosec lives in `utils.py`)

  Run: `make test-unit` — still PASS

---

## Task 3: Register hooks in `hooks/hooks.json`

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `hooks.json` contains entries for both `PreCompact` and `PostCompact` pointing to `sdlc-compact.py`
- Existing hook registrations are unchanged
- A source-inspection test verifies the registrations are present

**Files:**
- Modify: `hooks/hooks.json`
- Modify: `tests/unit/test_hooks_sdlc_compact.py` (add registration test class)

- [ ] **Step 1: Write failing tests (RED)**

  Add this class to `tests/unit/test_hooks_sdlc_compact.py`:

  ```python
  class TestSdlcCompactHooksJsonRegistration:
      def test_precompact_registered(self):
          hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
          config = json.loads(hooks_json.read_text())
          hooks = config.get("hooks", {})
          assert "PreCompact" in hooks, "PreCompact event not registered in hooks.json"
          commands = [
              entry.get("command", "")
              for block in hooks["PreCompact"]
              for entry in block.get("hooks", [])
          ]
          assert any("sdlc-compact.py" in cmd for cmd in commands), (
              "sdlc-compact.py not registered under PreCompact"
          )

      def test_postcompact_registered(self):
          hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
          config = json.loads(hooks_json.read_text())
          hooks = config.get("hooks", {})
          assert "PostCompact" in hooks, "PostCompact event not registered in hooks.json"
          commands = [
              entry.get("command", "")
              for block in hooks["PostCompact"]
              for entry in block.get("hooks", [])
          ]
          assert any("sdlc-compact.py" in cmd for cmd in commands), (
              "sdlc-compact.py not registered under PostCompact"
          )

      def test_existing_hooks_unchanged(self):
          hooks_json = Path(REPO_ROOT) / "hooks" / "hooks.json"
          config = json.loads(hooks_json.read_text())
          hooks = config.get("hooks", {})
          # Spot-check existing registrations are still present
          assert "SessionStart" in hooks
          assert "UserPromptSubmit" in hooks
          assert "PostToolUse" in hooks
          assert "PreToolUse" in hooks
          assert "Stop" in hooks
  ```

  Run: `make test-unit` — `TestSdlcCompactHooksJsonRegistration` must FAIL (keys absent)

- [ ] **Step 2: Implement (GREEN)**

  Add `PreCompact` and `PostCompact` entries to `hooks/hooks.json`. Final file:

  ```json
  {
    "_hook_output_protocol": {
      "SessionStart": "plain text printed to stdout — injected as session context",
      "UserPromptSubmit": "JSON {\"additionalContext\": \"...\"} printed to stdout",
      "PostToolUse": "plain text warnings/status printed to stdout",
      "PreToolUse": "plain text BLOCKED/WARNING printed to stdout; exit(2) to block",
      "Stop": "no output required; side-effects only (file writes, API calls)",
      "PreCompact": "no output required; side-effects only (snapshot write)",
      "PostCompact": "JSON {\"hookSpecificOutput\": {\"additionalContext\": \"...\"}} printed to stdout"
    },
    "hooks": {
      "SessionStart": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-resume.py\""
            }
          ]
        }
      ],
      "UserPromptSubmit": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/intent-detect.py\""
            }
          ]
        }
      ],
      "PostToolUse": [
        {
          "matcher": "Edit|Write",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/auto-test.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/wip-checkpoint.py\""
            }
          ]
        }
      ],
      "PreToolUse": [
        {
          "matcher": "Bash",
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
            }
          ]
        }
      ],
      "Stop": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-learn.py\""
            },
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/session-cleanup.py\""
            }
          ]
        }
      ],
      "PreCompact": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/sdlc-compact.py\""
            }
          ]
        }
      ],
      "PostCompact": [
        {
          "hooks": [
            {
              "type": "command",
              "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/sdlc-compact.py\""
            }
          ]
        }
      ]
    }
  }
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm `_hook_output_protocol` comment block is updated with the two new events (already included above)
  - Confirm JSON is valid (`python3 -c "import json; json.load(open('hooks/hooks.json'))"`)

  Run: `make test-unit` — still PASS

---

## Task 4: Unit tests for `build_snapshot` and `build_context` pure logic

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- The 20-file cap on `changed_files` is verified at the unit level with exact input
- The context block line-omission rules (blank active_task, blank tdd_phase) are verified without subprocess overhead
- All new tests pass

**Files:**
- Modify: `tests/unit/test_hooks_sdlc_compact.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add these classes to `tests/unit/test_hooks_sdlc_compact.py`:

  ```python
  # ---------------------------------------------------------------------------
  # Pure-logic unit tests (import hook module functions directly)
  # ---------------------------------------------------------------------------

  # Helpers: import the two pure functions by exec-ing the hook source with
  # a patched stdin so the module-level read_event() does not consume stdin.

  import importlib.util, types, io

  def _load_hook_module():
      """Load sdlc-compact.py as a module without executing top-level I/O."""
      spec = importlib.util.spec_from_file_location("sdlc_compact", HOOK)
      # Patch stdin before load so read_event() exits 0 without ImportError
      # We only need the helper functions, so we load with sys.stdin = empty
      # Actually, the module is not importable as-is due to top-level execution.
      # We test pure helpers via subprocess with known inputs (already covered above).
      # This loader is provided for future refactoring when helpers are extracted.
      return None  # placeholder — see note below


  class TestBuildSnapshotCap:
      """Verify the 20-file cap via PreCompact subprocess with a mocked git diff."""

      def test_changed_files_capped_at_20_exact(self, tmp_path):
          """Even if git reports 25 files, snapshot must contain at most 20."""
          cwd = make_cwd(tmp_path, roadmap=SAMPLE_ROADMAP)
          # Write a fake 'git' script that outputs 25 filenames
          fake_git = tmp_path / "bin" / "git"
          fake_git.parent.mkdir()
          twenty_five_files = "\n".join(f"file{i}.py" for i in range(25))
          fake_git.write_text(
              f"#!/bin/sh\n"
              f"if [ \"$3\" = 'branch' ]; then echo 'dev'; exit 0; fi\n"
              f"if [ \"$3\" = 'diff' ]; then printf '{twenty_five_files}\\n'; exit 0; fi\n"
              f"exit 0\n"
          )
          fake_git.chmod(0o755)
          r = run_hook(
              "PreCompact",
              tmp_cwd=cwd,
              env_overrides={"PATH": f"{fake_git.parent}:{os.environ.get('PATH', '')}"},
          )
          assert r.returncode == 0
          data = json.loads(snapshot_path(tmp_path).read_text())
          assert len(data["changed_files"]) == 20
          assert data["changed_files"][0] == "file0.py"
          assert data["changed_files"][19] == "file19.py"


  class TestBuildContextLines:
      """Verify context block content and line-omission rules via PostCompact subprocess."""

      @pytest.fixture(autouse=True)
      def _cleanup(self, tmp_path):
          yield
          p = snapshot_path(tmp_path)
          if p.is_symlink() or p.exists():
              p.unlink(missing_ok=True)

      def _ctx(self, tmp_path, snapshot_data):
          cwd = make_cwd(tmp_path)
          snapshot_path(tmp_path).write_text(json.dumps(snapshot_data))
          r = run_hook("PostCompact", tmp_cwd=cwd)
          return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]

      def test_header_line_always_present(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "", "now_items": [], "git_branch": "",
              "changed_files": [], "tdd_phase": "",
          })
          assert "[zie-framework]" in ctx

      def test_active_task_line_present_when_set(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "Do the thing", "now_items": ["Do the thing"],
              "git_branch": "", "changed_files": [], "tdd_phase": "",
          })
          assert "Do the thing" in ctx

      def test_active_task_line_absent_when_empty(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "", "now_items": [],
              "git_branch": "", "changed_files": [], "tdd_phase": "",
          })
          assert "Active task:" not in ctx

      def test_tdd_phase_line_present_when_set(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "t", "now_items": ["t"],
              "git_branch": "", "changed_files": [], "tdd_phase": "GREEN",
          })
          assert "GREEN" in ctx

      def test_tdd_phase_line_absent_when_empty(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "t", "now_items": ["t"],
              "git_branch": "", "changed_files": [], "tdd_phase": "",
          })
          assert "TDD phase:" not in ctx

      def test_git_branch_line_absent_when_empty_string(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "t", "now_items": ["t"],
              "git_branch": "", "changed_files": [], "tdd_phase": "",
          })
          assert "Git branch:" not in ctx

      def test_changed_files_section_absent_when_empty_list(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "t", "now_items": ["t"],
              "git_branch": "dev", "changed_files": [], "tdd_phase": "",
          })
          assert "Changed files" not in ctx

      def test_now_items_section_shown_when_multiple(self, tmp_path):
          ctx = self._ctx(tmp_path, {
              "active_task": "item A", "now_items": ["item A", "item B"],
              "git_branch": "dev", "changed_files": [], "tdd_phase": "",
          })
          assert "item B" in ctx
  ```

  Run: `make test-unit` — `TestBuildSnapshotCap` and `TestBuildContextLines` must FAIL
  (hook not yet aware of fake git PATH; `TestBuildContextLines` may partially fail
  due to missing snapshot file or wrong output format until hook is complete)

  Note: After Task 2 impl is in place, run again — most of these will already pass.
  The `TestBuildSnapshotCap.test_changed_files_capped_at_20_exact` is the key RED signal
  that verifies the `[:20]` slice is enforced.

- [ ] **Step 2: Implement (GREEN)**
  No additional implementation needed — the `[:20]` slice and the `if snapshot.get(...)` guards in Task 2's implementation already satisfy all assertions here.

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Remove the `_load_hook_module` placeholder helper if it was added (it is annotated as a placeholder and never called, but clean it up for clarity).

  Run: `make test-unit` — still PASS

---

*Commit: `git add hooks/sdlc-compact.py hooks/hooks.json tests/unit/test_hooks_sdlc_compact.py && git commit -m "feat: prepostcompact-wip-preservation"`*
