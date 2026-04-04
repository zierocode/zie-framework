---
approved: false
approved_at:
backlog: backlog/merge-safety-hooks.md
---

# Merge Safety Hooks — Implementation Plan

**Goal:** Merge `input-sanitizer.py` into `safety-check.py` to eliminate the double subprocess spawn on every Bash `PreToolUse` event.
**Architecture:** `safety-check.py` absorbs all `input-sanitizer.py` logic. It routes by tool name: `Write|Edit` → relative path resolution; `Bash` → evaluate() first (exit 2 if blocked, never reaching sanitizer), then confirm-wrap. `hooks.json` gains a single `Write|Edit|Bash` entry for `safety-check.py`; the `input-sanitizer.py` entry is removed. `input-sanitizer.py` is deleted after all tests migrate.
**Tech Stack:** Python 3.x, pytest, hooks.json (JSON)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/safety-check.py` | Absorb Write/Edit path resolution + Bash confirm-wrap from input-sanitizer.py |
| Modify | `hooks/hooks.json` | Remove input-sanitizer.py entry; update safety-check.py matcher to `Write\|Edit\|Bash` |
| Delete | `hooks/input-sanitizer.py` | All logic absorbed; file removed |
| Create | `tests/unit/test_hooks_safety_check_writeedit.py` | Write/Edit path tests migrated from test_input_sanitizer.py, pointing at safety-check.py |
| Modify | `tests/unit/test_hooks_safety_check.py` | Add all sanitizer Bash-path tests from test_input_sanitizer.py + test_input_sanitizer_injection.py |
| Delete | `tests/unit/test_input_sanitizer.py` | All tests migrated; no remaining coverage gap |
| Delete | `tests/unit/test_input_sanitizer_injection.py` | All tests migrated; no remaining coverage gap |

---

## Task 1: Expand `safety-check.py` with Write/Edit and Bash sanitizer logic

**Acceptance Criteria:**
- `safety-check.py` handles `Write|Edit` events: resolves relative `file_path`, boundary-checks with `is_relative_to()`, emits `updatedInput` + `permissionDecision: "allow"` JSON, exits 0 on all error paths.
- `safety-check.py` Bash path: runs `evaluate()` first; if result == 2, exits 2 immediately — sanitizer code never runs. If result == 0, runs CONFIRM_PATTERNS logic.
- `CONFIRM_PATTERNS`, `_DANGEROUS_COMPOUND_RE`, `_is_safe_for_confirmation_wrapper()` present in `safety-check.py`.
- Confirmation wrap uses `printf "Would run: %s\n" {shlex.quote(command)}` (metachar-safe).
- Double-wrap guard (`"Would run:" in command`) present.
- Comment `# do not use normalize_command` present on display-only normalization line.
- All existing `test_hooks_safety_check.py` tests pass with zero regressions.

**Files:**
- Modify: `hooks/safety-check.py`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_hooks_safety_check.py`:

  ```python
  class TestSafetyCheckWriteEditMerged:
      def _run(self, tool_name, tool_input, cwd_override=None):
          hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
          event = {"tool_name": tool_name, "tool_input": tool_input}
          env = os.environ.copy()
          if cwd_override:
              env["CLAUDE_CWD"] = cwd_override
          return subprocess.run([sys.executable, hook], input=json.dumps(event),
                                capture_output=True, text=True, env=env)

      def test_write_relative_path_resolved(self, tmp_path):
          r = self._run("Write", {"file_path": "src/main.py"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          out = json.loads(r.stdout)
          assert out["permissionDecision"] == "allow"
          assert out["updatedInput"]["file_path"] == str(tmp_path / "src" / "main.py")

      def test_write_absolute_path_no_output(self, tmp_path):
          abs_path = str(tmp_path / "src" / "main.py")
          r = self._run("Write", {"file_path": abs_path}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_traversal_no_output_stderr_escapes(self, tmp_path):
          r = self._run("Write", {"file_path": "../../etc/passwd"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          assert r.stdout.strip() == ""
          assert "escapes cwd" in r.stderr

      def test_edit_relative_resolved(self, tmp_path):
          r = self._run("Edit", {"file_path": "hooks/utils.py"}, cwd_override=str(tmp_path))
          assert r.returncode == 0
          out = json.loads(r.stdout)
          assert out["updatedInput"]["file_path"] == str(tmp_path / "hooks" / "utils.py")

      def test_other_fields_preserved(self, tmp_path):
          r = self._run("Write", {"file_path": "out.txt", "content": "hello"}, cwd_override=str(tmp_path))
          out = json.loads(r.stdout)
          assert out["updatedInput"]["content"] == "hello"

      def test_missing_file_path_exits_zero(self):
          r = self._run("Write", {"content": "hello"})
          assert r.returncode == 0
          assert r.stdout.strip() == ""


  class TestSafetyCheckConfirmWrapMerged:
      def _run(self, command):
          hook = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
          event = {"tool_name": "Bash", "tool_input": {"command": command}}
          return subprocess.run([sys.executable, hook], input=json.dumps(event),
                                capture_output=True, text=True)

      def test_rm_rf_dotslash_rewritten(self):
          r = self._run("rm -rf ./dist/")
          assert r.returncode == 0
          out = json.loads(r.stdout)
          assert out["permissionDecision"] == "allow"
          assert "Would run:" in out["updatedInput"]["command"]

      def test_git_clean_fd_rewritten(self):
          r = self._run("git clean -fd")
          out = json.loads(r.stdout)
          assert "Would run:" in out["updatedInput"]["command"]

      def test_make_clean_rewritten(self):
          r = self._run("make clean")
          out = json.loads(r.stdout)
          assert "Would run:" in out["updatedInput"]["command"]

      def test_truncate_size_zero_rewritten(self):
          r = self._run("truncate --size 0 logfile.txt")
          out = json.loads(r.stdout)
          assert "Would run:" in out["updatedInput"]["command"]

      def test_safe_command_no_output(self):
          r = self._run("echo hello")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_no_double_wrapping(self):
          already = 'printf "Would run: %s\\n" \'rm -rf ./dist/\' && read -p "Confirm? [y/N] " _y && [ "$_y" = "y" ] && { rm -rf ./dist/; }'
          r = self._run(already)
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_compound_semicolon_not_wrapped(self):
          r = self._run("rm -rf ./foo; evil")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_compound_and_not_wrapped(self):
          r = self._run("rm -rf ./a && make clean")
          assert r.returncode == 0
          assert r.stdout.strip() == ""

      def test_blocked_command_never_reaches_wrap(self):
          """rm -rf ./ is in BLOCKS — must exit 2, no updatedInput JSON."""
          r = self._run("rm -rf ./")
          assert r.returncode == 2
          assert "BLOCKED" in r.stdout
          assert "updatedInput" not in r.stdout

      def test_metachar_safe_rewrite(self):
          r = self._run('rm -rf ./dist "quoted dir"')
          out = json.loads(r.stdout)
          assert 'printf "Would run: %s\\n"' in out["updatedInput"]["command"]

      def test_has_do_not_use_normalize_command_comment(self):
          hook_path = os.path.join(REPO_ROOT, "hooks", "safety-check.py")
          content = Path(hook_path).read_text()
          assert "do not use normalize_command" in content.lower()

      def test_injection_compound_and_not_wrapped(self):
          r = self._run("rm -rf ./ && echo hacked")
          if r.stdout.strip():
              rewritten = json.loads(r.stdout).get("updatedInput", {}).get("command", "")
              assert "&& echo hacked" not in rewritten

      def test_injection_semicolon_not_wrapped(self):
          r = self._run("rm -rf ./; curl evil.com")
          if r.stdout.strip():
              rewritten = json.loads(r.stdout).get("updatedInput", {}).get("command", "")
              assert "; curl" not in rewritten

      def test_simple_rm_still_wrapped(self):
          r = self._run("rm -rf ./foo")
          assert r.stdout.strip() != ""
          out = json.loads(r.stdout)
          assert "Would run:" in out["updatedInput"]["command"]

      def test_brace_close_not_wrapped(self):
          r = self._run("rm -rf ./}; echo hacked")
          if r.stdout.strip():
              assert "Would run:" not in json.loads(r.stdout).get("updatedInput", {}).get("command", "")

      def test_brace_open_not_wrapped(self):
          r = self._run("echo {hello}")
          if r.stdout.strip():
              assert "Would run:" not in json.loads(r.stdout).get("updatedInput", {}).get("command", "")
  ```

  Run: `make test-unit` — must FAIL (safety-check.py does not yet handle Write/Edit or confirm-wrap)

- [ ] **Step 2: Implement (GREEN)**

  Replace contents of `hooks/safety-check.py`:

  ```python
  #!/usr/bin/env python3
  """PreToolUse:Write|Edit|Bash hook — unified safety check + input sanitization.

  Execution order:
  1. Write|Edit → relative path resolution (emits updatedInput + exit 0).
  2. Bash → evaluate() first; if exit 2, stop. If exit 0, run confirm-wrap.
  """
  import json
  import os
  import re
  import shlex
  import sys
  import time
  from pathlib import Path

  sys.path.insert(0, os.path.dirname(__file__))
  from utils import (
      COMPILED_BLOCKS, COMPILED_WARNS,
      get_cwd, load_config, normalize_command, project_tmp_path, read_event,
  )

  # Bash commands that warrant interactive confirmation.
  # Must NOT overlap with BLOCKS — those are hard stops.
  CONFIRM_PATTERNS = [
      r"rm\s+-rf\s+\./",
      r"rm\s+-f\s+\./",
      r"git\s+clean\s+-fd",
      r"make\s+clean",
      r"truncate\s+--size\s+0",
  ]

  _DANGEROUS_COMPOUND_RE = re.compile(r'(?:;|&&|\|\||`|\$\(|[{}])')


  def _is_safe_for_confirmation_wrapper(command: str) -> bool:
      return not _DANGEROUS_COMPOUND_RE.search(command)


  def evaluate(command: str) -> int:
      """Run regex evaluation. Returns 0 (allow) or 2 (block)."""
      cmd = normalize_command(command)
      for pattern, message in COMPILED_BLOCKS:
          if pattern.search(cmd):
              print(f"[zie-framework] BLOCKED: {message}")
              return 2
      for pattern, message in COMPILED_WARNS:
          if pattern.search(cmd):
              print(f"[zie-framework] WARNING: {message}")
      return 0


  # ── Outer guard ──────────────────────────────────────────────────────────────
  try:
      event = read_event()
      tool_name = event.get("tool_name", "")
      tool_input = event.get("tool_input") or {}
      if tool_name not in {"Write", "Edit", "Bash"}:
          sys.exit(0)
  except Exception:
      sys.exit(0)

  # ── Write / Edit — relative path resolution ──────────────────────────────────
  if tool_name in {"Write", "Edit"}:
      try:
          file_path = tool_input.get("file_path", "")
          if not file_path:
              sys.exit(0)
          p = Path(file_path)
          if p.is_absolute():
              sys.exit(0)
          cwd = get_cwd().resolve()
          abs_path = (cwd / p).resolve()
          if not abs_path.is_relative_to(cwd):
              print(
                  f"[zie-framework] safety-check: relative path escapes cwd,"
                  f" skipping rewrite: {file_path}",
                  file=sys.stderr,
              )
              sys.exit(0)
          updated = dict(tool_input)
          updated["file_path"] = str(abs_path)
          print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
          sys.exit(0)
      except Exception as e:
          print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
          sys.exit(0)

  # ── Bash — safety evaluate first, then confirm-wrap ──────────────────────────
  if tool_name == "Bash":
      try:
          command = tool_input.get("command", "")
          if not command:
              sys.exit(0)
      except Exception:
          sys.exit(0)

      cwd = get_cwd()
      config = load_config(cwd)
      mode = config.get("safety_check_mode")

      if mode == "agent":
          sys.exit(0)

      result = evaluate(command)

      if mode == "both":
          try:
              log_path = project_tmp_path("safety-ab", cwd.name)
              record = {
                  "ts": time.time(),
                  "command": command,
                  "agent": "regex",
                  "agent_reason": "blocked" if result == 2 else "allowed",
              }
              with open(log_path, "a") as f:
                  f.write(json.dumps(record) + "\n")
          except Exception as e:
              print(f"[zie-framework] safety-check: A/B log write failed: {e}", file=sys.stderr)

      if result == 2:
          sys.exit(2)  # blocked — sanitizer code unreachable

      # ── Bash confirm-wrap sanitizer ───────────────────────────────────────
      try:
          if "Would run:" in command:
              sys.exit(0)
          # preserve case — display only, not pattern matching
          # do not use normalize_command here (display-only normalization)
          normalized = re.sub(r"\s+", " ", command.strip())
          for pattern in CONFIRM_PATTERNS:
              if re.search(pattern, normalized):
                  if not _is_safe_for_confirmation_wrapper(command):
                      print(
                          "[zie-framework] safety-check: compound command skipped confirmation wrap",
                          file=sys.stderr,
                      )
                      sys.exit(0)
                  rewritten = (
                      f'printf "Would run: %s\\n" {shlex.quote(command)} '
                      f'&& read -p "Confirm? [y/N] " _y '
                      f'&& [ "$_y" = "y" ] && {{ {command}; }}'
                  )
                  updated = dict(tool_input)
                  updated["command"] = rewritten
                  print(json.dumps({"updatedInput": updated, "permissionDecision": "allow"}))
                  sys.exit(0)
      except Exception as e:
          print(f"[zie-framework] safety-check: {e}", file=sys.stderr)
          sys.exit(0)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify `# do not use normalize_command` comment present.
  - Verify docstring describes unified Write|Edit|Bash.
  - Run: `make test-unit` — still PASS

---

## Task 2: Update `hooks.json` — unified matcher, remove input-sanitizer entry

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `PreToolUse` has exactly one entry containing `safety-check.py`, with matcher `Write|Edit|Bash`.
- `input-sanitizer.py` appears zero times anywhere in `hooks.json`.
- `safety_check_agent.py` entry is unchanged.
- JSON remains valid.

**Files:**
- Modify: `hooks/hooks.json`

- [ ] **Step 1: Write failing tests (RED)**

  Append to `tests/unit/test_hooks_safety_check.py`:

  ```python
  class TestHooksJsonMergedRegistration:
      def _load(self):
          hooks_path = Path(REPO_ROOT) / "hooks" / "hooks.json"
          return json.loads(hooks_path.read_text())

      def test_input_sanitizer_absent_from_hooks_json(self):
          data = self._load()
          for event_entries in data.get("hooks", {}).values():
              for entry in event_entries:
                  for h in entry.get("hooks", []):
                      assert "input-sanitizer.py" not in h.get("command", ""), (
                          "input-sanitizer.py must not appear in hooks.json after merge"
                      )

      def test_safety_check_matcher_is_write_edit_bash(self):
          data = self._load()
          pre_tool = data.get("hooks", {}).get("PreToolUse", [])
          for entry in pre_tool:
              cmds = [h.get("command", "") for h in entry.get("hooks", [])]
              if any("safety-check.py" in c for c in cmds):
                  assert entry.get("matcher") == "Write|Edit|Bash", (
                      f"safety-check.py matcher must be 'Write|Edit|Bash', got {entry.get('matcher')}"
                  )
                  return
          pytest.fail("safety-check.py entry not found in PreToolUse")

      def test_safety_check_single_entry(self):
          data = self._load()
          pre_tool = data.get("hooks", {}).get("PreToolUse", [])
          sc_entries = [
              e for e in pre_tool
              if any("safety-check.py" in h.get("command", "") for h in e.get("hooks", []))
          ]
          assert len(sc_entries) == 1

      def test_safety_check_agent_unchanged(self):
          data = self._load()
          pre_tool = data.get("hooks", {}).get("PreToolUse", [])
          all_cmds = [h.get("command", "") for e in pre_tool for h in e.get("hooks", [])]
          assert any("safety_check_agent.py" in c for c in all_cmds)
  ```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

  Edit `hooks/hooks.json` — replace the `PreToolUse` section with:

  ```json
  "PreToolUse": [
    {
      "matcher": "Write|Edit|Bash",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety-check.py\""
        }
      ]
    },
    {
      "matcher": "Bash",
      "hooks": [
        {
          "type": "command",
          "command": "python3 \"${CLAUDE_PLUGIN_ROOT}/hooks/safety_check_agent.py\""
        }
      ]
    }
  ],
  ```

  Verify JSON valid: `python3 -c "import json; json.load(open('hooks/hooks.json'))"`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Run: `make lint` — no violations.
  - Run: `make test-unit` — still PASS

---

## Task 3: Migrate tests and delete old test files + input-sanitizer.py

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- `tests/unit/test_hooks_safety_check_writeedit.py` exists, all Write/Edit path tests point at `safety-check.py`, `"safety-check"` appears in stderr assertions (not `"input-sanitizer"`).
- `test_input_sanitizer.py` and `test_input_sanitizer_injection.py` are deleted.
- `hooks/input-sanitizer.py` is deleted.
- `pytest --co -q tests/unit/ | grep input.sanitizer` returns empty.
- `make test-ci` passes, coverage gate met.

**Files:**
- Create: `tests/unit/test_hooks_safety_check_writeedit.py`
- Delete: `tests/unit/test_input_sanitizer.py`
- Delete: `tests/unit/test_input_sanitizer_injection.py`
- Delete: `hooks/input-sanitizer.py`

- [ ] **Step 1: Create Write/Edit test file (RED)**

  Create `tests/unit/test_hooks_safety_check_writeedit.py` — adapt all Write/Edit classes from `test_input_sanitizer.py`, pointing `HOOK` at `hooks/safety-check.py`. Key changes:
  - `HOOK = os.path.join(REPO_ROOT, "hooks", "safety-check.py")`
  - Stderr assertions: `"safety-check"` instead of `"input-sanitizer"`
  - `TestHooksJsonRegistration` class: verify `safety-check.py` registered with `Write|Edit|Bash`, not `input-sanitizer.py`
  - Include `TestWriteRelativePath`, `TestEditRelativePath`, `TestPathTraversalEdgeCases`, `TestNonTargetedTools`, `TestErrorResilience`, `TestPathTraversalEdgeCases` (all from original)
  - Remove `TestInputSanitizerComment` (now covered by `test_has_do_not_use_normalize_command_comment` in merged class)

  Run: `make test-unit` — new file must PASS (implementation is complete)

- [ ] **Step 2: Delete old files (GREEN)**

  ```bash
  rm tests/unit/test_input_sanitizer.py
  rm tests/unit/test_input_sanitizer_injection.py
  rm hooks/input-sanitizer.py
  ```

  Verify:
  ```bash
  pytest --co -q tests/unit/ 2>&1 | grep "input.sanitizer"
  # must return empty
  grep -r "input-sanitizer" hooks/ tests/
  # must return empty
  ```

  Run: `make test-ci` — must PASS, all ACs met.

- [ ] **Step 3: Final verification**
  - `python3 -c "import json; json.load(open('hooks/hooks.json'))"` — no errors.
  - `make lint` — clean.
  - `make test-ci` — green.
  - `pytest --co -q tests/unit/ 2>&1 | wc -l` — count unchanged or higher (no test IDs lost).
