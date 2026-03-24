---
approved: false
backlog: backlog/consolidate-utils-patterns.md
spec: specs/2026-03-24-consolidate-utils-patterns-design.md
---

# Consolidate Duplicate Patterns into utils.py — Implementation Plan

**Goal:** Fix a silent bug where `load_config()` uses KEY=VALUE parsing incompatible with the actual JSON `.config` format (so `safety_check_mode` is never read), add a shared `normalize_command()` utility, move `BLOCKS`/`WARNS` to utils to remove a 39-line importlib workaround, and migrate 3 inline config loaders and 3 inline re.sub normalizations to use the new shared functions.
**Architecture:** All changes are contained within `hooks/` and `tests/unit/`. No new files. No changes to plugin.json, commands, or skills.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Fix `load_config()` (JSON); add `normalize_command()`; add `BLOCKS`, `WARNS` |
| Modify | `hooks/safety-check.py` | Remove BLOCKS/WARNS literals; import from utils; use `normalize_command()` |
| Modify | `hooks/safety_check_agent.py` | Remove `_load_blocks()` + importlib; import BLOCKS/`normalize_command` from utils |
| Modify | `hooks/auto-test.py` | Replace inline `json.loads()` config block with `load_config(cwd)` |
| Modify | `hooks/session-resume.py` | Replace inline `json.loads()` config block with `load_config(cwd)` |
| Modify | `hooks/sdlc-compact.py` | Replace inline `json.loads()` config block with `load_config(cwd)` |
| Modify | `hooks/sdlc-permissions.py` | Replace `re.sub(r'\s+', ' ', command.strip())` with `normalize_command(command)` |
| Modify | `hooks/input-sanitizer.py` | Add clarifying comment only — do NOT use `normalize_command()` |
| Modify | `tests/unit/test_utils.py` | Rewrite `TestLoadConfig` for JSON; add `TestNormalizeCommand`; add `TestBlocksWarns` |

---

## Task 1: Fix `load_config()` + update tests

**Acceptance Criteria:**
- `load_config()` uses `json.loads(config_path.read_text())` and returns `{}` on any error
- `TestLoadConfig` tests exercise JSON format, not KEY=VALUE
- `make test-unit` passes

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # In tests/unit/test_utils.py, replace the existing TestLoadConfig class:

  class TestLoadConfig:
      def test_returns_dict_for_valid_json_config(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('{"safety_check_mode": "agent"}')
          from utils import load_config
          result = load_config(tmp_path)
          assert result.get("safety_check_mode") == "agent"

      def test_returns_empty_dict_when_no_config(self, tmp_path):
          from utils import load_config
          assert load_config(tmp_path) == {}

      def test_returns_empty_on_invalid_json(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text("not valid json")
          from utils import load_config
          result = load_config(tmp_path)
          assert result == {}

      def test_returns_empty_on_empty_file(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text("")
          from utils import load_config
          assert load_config(tmp_path) == {}

      def test_boolean_value_preserved(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('{"playwright_enabled": false, "has_frontend": true}')
          from utils import load_config
          result = load_config(tmp_path)
          assert result["playwright_enabled"] is False
          assert result["has_frontend"] is True

      def test_integer_value_preserved(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('{"debounce_ms": 3000}')
          from utils import load_config
          result = load_config(tmp_path)
          assert result["debounce_ms"] == 3000

      def test_string_value_preserved(self, tmp_path):
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / ".config").write_text('{"test_runner": "pytest"}')
          from utils import load_config
          result = load_config(tmp_path)
          assert result["test_runner"] == "pytest"
  ```

  Run: `make test-unit` — must FAIL (existing KEY=VALUE tests pass; new JSON tests fail because `load_config()` still uses KEY=VALUE parser)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/utils.py, replace load_config() (lines 156–174):

  def load_config(cwd: Path) -> dict:
      """Read zie-framework/.config as JSON and return a dict.

      Returns {} on any error (missing file, parse failure, permission denied, etc.).
      """
      config_path = cwd / "zie-framework" / ".config"
      try:
          return json.loads(config_path.read_text())
      except Exception:
          return {}
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Update the `load_config()` docstring to remove the reference to "key=value pairs"
  (already done in Step 2 above). No structural refactor needed — the function is
  simpler after the fix than before.

  Run: `make test-unit` — still PASS

---

## Task 2: Add `normalize_command()` + migrate callers

**Acceptance Criteria:**
- `normalize_command(cmd)` is exported from `utils.py`: `re.sub(r'\s+', ' ', cmd.strip().lower())`
- `safety-check.py`, `safety_check_agent.py`, and `sdlc-permissions.py` call `normalize_command()` instead of inline `re.sub`
- `input-sanitizer.py` retains its inline `re.sub` with an added comment
- `TestNormalizeCommand` parametrized tests pass
- `make test-unit` passes

**Files:**
- Modify: `hooks/utils.py`
- Modify: `hooks/safety-check.py`
- Modify: `hooks/safety_check_agent.py`
- Modify: `hooks/sdlc-permissions.py`
- Modify: `hooks/input-sanitizer.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py:

  class TestNormalizeCommand:
      @pytest.mark.parametrize("cmd,expected", [
          ("git   add  .", "git add ."),
          ("  GIT ADD .  ", "git add ."),
          ("git\t\tadd\t.", "git add ."),
          ("make\n test", "make test"),
          ("git add .", "git add ."),
          ("", ""),
          ("   ", ""),
          ("GIT PUSH ORIGIN MAIN", "git push origin main"),
      ])
      def test_normalize_command(self, cmd, expected):
          from utils import normalize_command
          assert normalize_command(cmd) == expected

      def test_lowercases_command(self):
          from utils import normalize_command
          assert normalize_command("RM -RF /") == "rm -rf /"

      def test_collapses_tabs_and_newlines(self):
          from utils import normalize_command
          assert normalize_command("git\t\tcommit\n-m\r\n'msg'") == "git commit -m 'msg'"
  ```

  Run: `make test-unit` — must FAIL (`normalize_command` does not exist yet)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/utils.py, add after load_config() (after line 174):

  def normalize_command(cmd: str) -> str:
      """Normalize whitespace and lowercase a shell command for pattern matching."""
      return re.sub(r'\s+', ' ', cmd.strip().lower())
  ```

  ```python
  # In hooks/safety-check.py, update imports (line 10):
  from utils import get_cwd, load_config, normalize_command, project_tmp_path, read_event, safe_project_name

  # In hooks/safety-check.py, update evaluate() (line 47):
  # BEFORE:
  cmd = re.sub(r'\s+', ' ', command.strip().lower())
  # AFTER:
  cmd = normalize_command(command)
  ```

  ```python
  # In hooks/safety_check_agent.py, update imports (line 15):
  from utils import get_cwd, load_config, normalize_command, read_event

  # In hooks/safety_check_agent.py, update _regex_evaluate() (line 64):
  # BEFORE:
  cmd = re.sub(r'\s+', ' ', command.strip().lower())
  # AFTER:
  cmd = normalize_command(command)
  ```

  ```python
  # In hooks/sdlc-permissions.py, update imports (line 9):
  from utils import normalize_command, read_event

  # In hooks/sdlc-permissions.py, update line 41:
  # BEFORE:
  cmd = re.sub(r'\s+', ' ', command.strip())
  # AFTER:
  cmd = normalize_command(command)
  ```

  Note: `sdlc-permissions.py` SAFE_PATTERNS are all lowercase (`git add`, `make test`, etc.)
  so adding `.lower()` via `normalize_command()` is safe — patterns still match.

  ```python
  # In hooks/input-sanitizer.py, update the comment at line 85–86:
  # BEFORE:
  normalized = re.sub(r"\s+", " ", command.strip())
  # AFTER:
  # preserve case — display only, not pattern matching (do NOT use normalize_command here)
  normalized = re.sub(r"\s+", " ", command.strip())
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Check `import re` in `safety-check.py`, `safety_check_agent.py`, and
  `sdlc-permissions.py` — if `re` is no longer used elsewhere in those files after
  removing the inline `re.sub`, remove the `import re` line. Check each file:
  - `safety-check.py`: `re` is also used in `evaluate()` for `re.search()` — keep import
  - `safety_check_agent.py`: `re` is used in `_regex_evaluate()` for `re.search()` — keep import
  - `sdlc-permissions.py`: `re` is used in `re.match()` for pattern matching — keep import

  No imports to remove. No further cleanup needed.

  Run: `make test-unit` — still PASS

---

## Task 3: Move BLOCKS/WARNS to utils + remove importlib workaround

**Acceptance Criteria:**
- `BLOCKS` and `WARNS` lists are defined in `utils.py`
- `safety-check.py` imports `BLOCKS, WARNS` from utils (no local list literals)
- `safety_check_agent.py` removes `_load_blocks()`, `import importlib.util`, and the fallback inline list; imports `BLOCKS` from utils and extends locally
- `TestBlocksWarns` tests confirm BLOCKS/WARNS are importable from utils and have expected length/content
- `make test-unit` passes

**Files:**
- Modify: `hooks/utils.py`
- Modify: `hooks/safety-check.py`
- Modify: `hooks/safety_check_agent.py`
- Modify: `tests/unit/test_utils.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py:

  class TestBlocksWarns:
      def test_blocks_importable_from_utils(self):
          from utils import BLOCKS
          assert isinstance(BLOCKS, list)
          assert len(BLOCKS) > 0

      def test_warns_importable_from_utils(self):
          from utils import WARNS
          assert isinstance(WARNS, list)
          assert len(WARNS) > 0

      def test_blocks_entries_are_tuples(self):
          from utils import BLOCKS
          for entry in BLOCKS:
              assert isinstance(entry, tuple)
              assert len(entry) == 2

      def test_warns_entries_are_tuples(self):
          from utils import WARNS
          for entry in WARNS:
              assert isinstance(entry, tuple)
              assert len(entry) == 2

      def test_blocks_contains_rm_rf_pattern(self):
          from utils import BLOCKS
          patterns = [p for p, _ in BLOCKS]
          assert any("rm" in p for p in patterns)

      def test_warns_contains_docker_compose_pattern(self):
          from utils import WARNS
          patterns = [p for p, _ in WARNS]
          assert any("docker" in p for p in patterns)
  ```

  Run: `make test-unit` — must FAIL (BLOCKS/WARNS not yet in utils)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/utils.py, add BLOCKS and WARNS after normalize_command():

  BLOCKS = [
      # Filesystem destruction
      (r"rm\s+-rf\s+(/\s|/\b|/$)", "rm -rf / is blocked — this would destroy the system"),
      (r"rm\s+-rf\s+~", "rm -rf ~ is blocked — this would destroy your home directory"),
      (r"rm\s+-rf\s+\.", "rm -rf . blocked — use explicit paths"),
      # Database destruction
      (r"\bdrop\s+database\b", "DROP DATABASE blocked — use migrations to remove databases"),
      (r"\bdrop\s+table\b", "DROP TABLE blocked — use alembic/migrations for schema changes"),
      (r"\btruncate\s+table\b", "TRUNCATE TABLE blocked — be explicit with user before truncating"),
      # Force push
      (r"git\s+push\s+.*--force\b", "Force push blocked — use 'git push' normally or ask Zie explicitly"),
      (r"git\s+push\s+.*-f\b", "Force push blocked — use 'git push' normally"),
      (r"git\s+push\s+.*origin\s+main\b", "Direct push to main blocked — use 'make ship' instead"),
      (r"git\s+push\s+.*origin\s+master\b", "Direct push to master blocked — use 'make ship' instead"),
      # Hard reset
      (r"git\s+reset\s+--hard\b", "git reset --hard blocked — this discards uncommitted work. Use 'git stash' instead"),
      # Skip hooks
      (r"--no-verify\b", "--no-verify blocked — hooks exist for a reason. Fix the hook failure instead"),
  ]

  # WARNS: non-blocking notices. Do NOT add patterns already caught by BLOCKS above.
  WARNS = [
      (r"docker\s+compose\s+down\s+.*--volumes\b",
       "docker compose down --volumes will delete DB data — make sure you have a backup"),
      (r"alembic\s+downgrade\b",
       "Alembic downgrade detected — verify this won't lose production data"),
  ]
  ```

  ```python
  # In hooks/safety-check.py:
  # 1. Update imports (line 10) — add BLOCKS, WARNS:
  from utils import BLOCKS, get_cwd, load_config, normalize_command, project_tmp_path, read_event, safe_project_name, WARNS

  # 2. Remove the BLOCKS list literal (lines 12–34) and WARNS list literal (lines 37–42)
  #    They are now imported from utils.
  ```

  ```python
  # In hooks/safety_check_agent.py:
  # 1. Remove: import importlib.util  (line 7)
  # 2. Remove: the entire _load_blocks() function (lines 18–39)
  # 3. Remove: the module-level BLOCKS = _load_blocks() + [...] block (lines 42–48)
  # 4. Update imports (line 15) — add BLOCKS, normalize_command:
  from utils import BLOCKS, get_cwd, load_config, normalize_command, read_event

  # 5. Add agent-specific extension after the import block:
  _AGENT_BLOCKS = BLOCKS + [
      (r"curl\s+.*\|\s*bash\b", "curl pipe to bash blocked — potential code injection"),
      (r"curl\s+.*\|\s*sh\b", "curl pipe to sh blocked — potential code injection"),
      (r"wget\s+.*\|\s*bash\b", "wget pipe to bash blocked — potential code injection"),
      (r"wget\s+.*\|\s*sh\b", "wget pipe to sh blocked — potential code injection"),
  ]

  # 6. Update _regex_evaluate() to use _AGENT_BLOCKS instead of BLOCKS:
  def _regex_evaluate(command: str) -> int:
      cmd = normalize_command(command)
      for pattern, message in _AGENT_BLOCKS:
          if re.search(pattern, cmd):
              print(f"[zie-framework] BLOCKED: {message}")
              return 2
      return 0
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  Verify the docstring at the top of `safety_check_agent.py` no longer references
  importlib. The original docstring says "Named with underscores (safety_check_agent.py)
  to allow Python importlib to load it cleanly from tests and other hooks." — this
  rationale remains valid (tests still import it via importlib), so keep the docstring
  as-is.

  Run: `make test-unit` — still PASS
  Run: `make lint` — exits 0 (py_compile clean on all hooks)

---

## Task 4: Migrate inline config loaders in auto-test, session-resume, sdlc-compact

**Acceptance Criteria:**
- `auto-test.py` uses `load_config(cwd)` — no inline `json.loads()` or `config_file.exists()` guard
- `session-resume.py` uses `load_config(cwd)` — no inline `json.loads()` or `config_file.exists()` guard
- `sdlc-compact.py` uses `load_config(cwd)` — no inline `json.loads()` or `config_path.exists()` guard
- All three hooks behave identically when `.config` is absent (return `{}`, no crash)
- `make test-unit` passes

**Files:**
- Modify: `hooks/auto-test.py`
- Modify: `hooks/session-resume.py`
- Modify: `hooks/sdlc-compact.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  No new unit tests needed — `load_config()` is already fully covered by Task 1 tests.
  The migration is a mechanical substitution; correctness is guaranteed by `load_config()`'s
  contract (returns `{}` on any error, handles missing file).

  Verification: run `make test-unit` — must PASS (baseline before editing hooks)

---

- [ ] **Step 2: Implement (GREEN)**

  **auto-test.py** (lines 75–85 — the fallback config block):

  ```python
  # BEFORE (lines 74–85):
  # Fallback: read .config when env vars are absent
  config = {}
  if not test_runner or not _debounce_env:
      config_file = zf / ".config"
      if config_file.exists():
          try:
              config = json.loads(config_file.read_text())
          except Exception as e:
              print(
                  f"[zie] warning: .config unreadable ({e}), using defaults",
                  file=sys.stderr,
              )

  # AFTER:
  # Fallback: read .config when env vars are absent
  config = {}
  if not test_runner or not _debounce_env:
      config = load_config(cwd)
  ```

  Ensure `load_config` is added to the existing utils import in auto-test.py.
  Remove `import json` if it is no longer used elsewhere in the file (check other usages).

  **session-resume.py** (lines 19–26 — the config block at module level):

  ```python
  # BEFORE (lines 19–26):
  # Read config
  config = {}
  config_file = zf / ".config"
  if config_file.exists():
      try:
          config = json.loads(config_file.read_text())
      except Exception as e:
          print(f"[zie] warning: .config unreadable ({e}), using defaults", file=sys.stderr)

  # AFTER:
  # Read config
  config = load_config(cwd)
  ```

  Ensure `load_config` is added to the existing utils import in session-resume.py.
  Remove `import json` if no longer used elsewhere in the file.

  **sdlc-compact.py** (lines 76–84 — the tdd_phase config block):

  ```python
  # BEFORE (lines 76–84):
  # --- Read tdd_phase from .config ---
  tdd_phase = ""
  try:
      config_path = zf / ".config"
      if config_path.exists():
          config = json.loads(config_path.read_text())
          tdd_phase = config.get("tdd_phase", "")
  except Exception as e:
      print(f"[zie-framework] sdlc-compact: config read failed: {e}", file=sys.stderr)

  # AFTER:
  # --- Read tdd_phase from .config ---
  tdd_phase = load_config(cwd).get("tdd_phase", "")
  ```

  Ensure `load_config` is added to the existing utils import in sdlc-compact.py.
  Remove `import json` if no longer used elsewhere in the file.

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  For each of the three hooks, verify `import json` can be safely removed:
  - `auto-test.py`: search for other `json.` usages in the file before removing
  - `session-resume.py`: search for other `json.` usages before removing
  - `sdlc-compact.py`: search for other `json.` usages before removing

  Remove only if no other usages remain. Run `make lint` after each removal to confirm
  `py_compile` passes.

  Run: `make test-unit` — still PASS

---

## Task 5: Add `normalize_command()` comment to input-sanitizer.py

**Acceptance Criteria:**
- `input-sanitizer.py` line 86 has a comment explaining why `normalize_command()` is NOT used
- No functional change — the `re.sub` remains exactly as-is
- `make test-unit` passes

**Files:**
- Modify: `hooks/input-sanitizer.py`

---

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils.py (or a new test_input_sanitizer.py):

  class TestInputSanitizerComment:
      def test_input_sanitizer_has_preserve_case_comment(self):
          """input-sanitizer.py must have a comment explaining why normalize_command is not used."""
          sanitizer = REPO_ROOT / "hooks" / "input-sanitizer.py"
          content = sanitizer.read_text()
          assert "preserve case" in content.lower(), (
              "input-sanitizer.py must have a 'preserve case' comment near the re.sub normalization"
          )
  ```

  Run: `make test-unit` — must FAIL (comment not yet present)

---

- [ ] **Step 2: Implement (GREEN)**

  ```python
  # In hooks/input-sanitizer.py, update lines 85–86:

  # BEFORE:
  normalized = re.sub(r"\s+", " ", command.strip())

  # AFTER:
  # preserve case — display only, not pattern matching (do NOT use normalize_command here)
  normalized = re.sub(r"\s+", " ", command.strip())
  ```

  Run: `make test-unit` — must PASS

---

- [ ] **Step 3: Refactor**

  No structural changes needed. The comment is the complete deliverable for this task.

  Run: `make test-unit` — still PASS
  Run: `make lint` — exits 0

---

**Commit:** `git add hooks/utils.py hooks/safety-check.py hooks/safety_check_agent.py hooks/auto-test.py hooks/session-resume.py hooks/sdlc-compact.py hooks/sdlc-permissions.py hooks/input-sanitizer.py tests/unit/test_utils.py && git commit -m "fix: consolidate-utils-patterns — fix load_config JSON, add normalize_command, move BLOCKS/WARNS to utils"`
