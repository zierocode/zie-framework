---
approved: true
approved_at: 2026-03-29
backlog: backlog/dry-utils-cleanup.md
spec: specs/2026-03-29-dry-utils-cleanup-design.md
---

# DRY Utils Cleanup — Implementation Plan

**Goal:** Eliminate two DRY violations in `hooks/utils.py` by consolidating the duplicate roadmap-parsing functions and centralising `.config` defaults.
**Architecture:** `parse_roadmap_section()` becomes a thin delegator to `parse_roadmap_section_content()`; a new `CONFIG_DEFAULTS` constant in `utils.py` is merged into every `load_config()` return value, allowing all hook call sites to drop inline default arguments.
**Tech Stack:** Python 3.x, pytest, hooks/utils.py shared library.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils.py` | Add `CONFIG_DEFAULTS`, update `load_config()`, replace `parse_roadmap_section()` body |
| Modify | `tests/unit/test_utils.py` | Update existing `load_config` tests whose assertions break; add new tests for delegation + default merge |
| Modify | `hooks/auto-test.py` | Remove inline defaults from 3 `config.get()` call sites |
| Modify | `hooks/task-completed-gate.py` | Remove inline default from 1 `config.get()` call site |
| Modify | `hooks/session-resume.py` | Remove inline defaults from 4 `config.get()` call sites |
| Modify | `hooks/safety-check.py` | Remove inline default from 1 `config.get()` call site |
| Modify | `hooks/safety_check_agent.py` | Remove inline default from 1 `config.get()` call site |

---

## Task 1: Consolidate parse_roadmap_section → delegates to parse_roadmap_section_content

**Acceptance Criteria:**
- `parse_roadmap_section(path, section)` returns identical results to calling `parse_roadmap_section_content(path.read_text(), section)` for every valid path.
- Missing-file guard is preserved: returns `[]` when file does not exist.
- All existing `TestParseRoadmapSection` tests pass without modification.
- New test `test_parse_roadmap_section_delegates_to_content` passes.

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing test (RED)**

  Add to `TestParseRoadmapSection` in `tests/unit/test_utils.py`:

  ```python
  def test_parse_roadmap_section_delegates_to_content(self, tmp_path, monkeypatch):
      """parse_roadmap_section must call parse_roadmap_section_content, not re-implement."""
      from utils import parse_roadmap_section, parse_roadmap_section_content
      f = tmp_path / "ROADMAP.md"
      f.write_text("## Alpha\n- [ ] task one\n")
      calls = []
      original = parse_roadmap_section_content
      def spy(content, section_name):
          calls.append((content, section_name))
          return original(content, section_name)
      monkeypatch.setattr("utils.parse_roadmap_section_content", spy)
      result = parse_roadmap_section(f, "alpha")
      assert result == ["task one"]
      assert len(calls) == 1, "parse_roadmap_section must delegate to parse_roadmap_section_content"
  ```

  Run: `make test-unit` — must FAIL (spy never called, parse_roadmap_section has its own loop)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/utils.py`, replace the body of `parse_roadmap_section` (lines 44–61):

  ```python
  def parse_roadmap_section(roadmap_path, section_name: str) -> list:
      """Extract cleaned items from a named ## section of ROADMAP.md.

      section_name is matched case-insensitively against ## headers.
      Returns [] if file missing, section absent, or section empty.
      Accepts Path or str. Delegates to parse_roadmap_section_content.
      """
      path = Path(roadmap_path)
      if not path.exists():
          return []
      return parse_roadmap_section_content(path.read_text(), section_name)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Update the docstring of `parse_roadmap_section_content` to remove the phrase "Identical logic to parse_roadmap_section but" — it is now the canonical implementation. Replace with: "Canonical implementation for section parsing; parse_roadmap_section delegates here."

  Run: `make test-unit` — still PASS

---

## Task 2: Add CONFIG_DEFAULTS and update load_config()

<!-- depends_on: none -->

**Acceptance Criteria:**
- `CONFIG_DEFAULTS` dict exists in `utils.py` at module level with exactly these 7 keys and values:
  - `safety_check_mode`: `"regex"`
  - `test_runner`: `""`
  - `auto_test_debounce_ms`: `3000`
  - `auto_test_timeout_ms`: `30000`
  - `test_indicators`: `""`
  - `project_type`: `"unknown"`
  - `zie_memory_enabled`: `False`
- `load_config()` returns a dict containing all `CONFIG_DEFAULTS` keys when `.config` is missing.
- `load_config()` returns a dict containing all `CONFIG_DEFAULTS` keys when `.config` is invalid JSON.
- Loaded values override defaults (e.g. `safety_check_mode: "agent"` in file → `"agent"` returned).
- All existing passing tests still pass (some must be updated — see Step 1 below).

**Files:**
- Modify: `hooks/utils.py`
- Modify: `tests/unit/test_utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  Note: two existing tests assert `load_config(tmp_path) == {}` for missing/empty file. These will be updated to match the new contract. Add new tests at the end of `TestLoadConfig` in `tests/unit/test_utils.py`:

  ```python
  def test_returns_config_defaults_when_no_config_file(self, tmp_path):
      from utils import load_config, CONFIG_DEFAULTS
      result = load_config(tmp_path)
      assert result == CONFIG_DEFAULTS

  def test_returns_config_defaults_when_empty_file(self, tmp_path):
      from utils import load_config, CONFIG_DEFAULTS
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text("")
      result = load_config(tmp_path)
      assert result == CONFIG_DEFAULTS

  def test_returns_config_defaults_when_invalid_json(self, tmp_path):
      from utils import load_config, CONFIG_DEFAULTS
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text("not valid json")
      result = load_config(tmp_path)
      assert result == CONFIG_DEFAULTS

  def test_loaded_values_override_defaults(self, tmp_path):
      from utils import load_config, CONFIG_DEFAULTS
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text('{"safety_check_mode": "agent", "auto_test_debounce_ms": 500}')
      result = load_config(tmp_path)
      assert result["safety_check_mode"] == "agent"
      assert result["auto_test_debounce_ms"] == 500
      # all other keys still present via defaults
      assert result["test_runner"] == CONFIG_DEFAULTS["test_runner"]
      assert result["zie_memory_enabled"] == CONFIG_DEFAULTS["zie_memory_enabled"]

  def test_config_defaults_has_all_required_keys(self):
      from utils import CONFIG_DEFAULTS
      required = {
          "safety_check_mode", "test_runner", "auto_test_debounce_ms",
          "auto_test_timeout_ms", "test_indicators", "project_type", "zie_memory_enabled",
      }
      assert required <= set(CONFIG_DEFAULTS.keys())

  def test_config_defaults_correct_types(self):
      from utils import CONFIG_DEFAULTS
      assert isinstance(CONFIG_DEFAULTS["safety_check_mode"], str)
      assert isinstance(CONFIG_DEFAULTS["test_runner"], str)
      assert isinstance(CONFIG_DEFAULTS["auto_test_debounce_ms"], int)
      assert isinstance(CONFIG_DEFAULTS["auto_test_timeout_ms"], int)
      assert isinstance(CONFIG_DEFAULTS["test_indicators"], str)
      assert isinstance(CONFIG_DEFAULTS["project_type"], str)
      assert isinstance(CONFIG_DEFAULTS["zie_memory_enabled"], bool)
  ```

  Also update the two existing tests that assert `== {}`:

  ```python
  # OLD (line ~607):
  def test_returns_empty_dict_when_no_config(self, tmp_path):
      from utils import load_config
      assert load_config(tmp_path) == {}

  # NEW:
  def test_returns_defaults_dict_when_no_config(self, tmp_path):
      from utils import load_config, CONFIG_DEFAULTS
      assert load_config(tmp_path) == CONFIG_DEFAULTS

  # OLD (line ~617):
  def test_returns_empty_on_empty_file(self, tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text("")
      from utils import load_config
      assert load_config(tmp_path) == {}

  # NEW:
  def test_returns_defaults_on_empty_file(self, tmp_path):
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text("")
      from utils import load_config, CONFIG_DEFAULTS
      assert load_config(tmp_path) == CONFIG_DEFAULTS
  ```

  Also update `test_utils_sanitize.py` — the two `== {}` assertions there:

  ```python
  # test_load_config_malformed_json_returns_empty  →  result != {} after change
  # test_load_config_missing_file_no_stderr        →  result != {} after change
  # test_load_config_valid_json                    →  no change needed (asserts a specific key)
  ```

  Update `test_utils_sanitize.py` accordingly:

  ```python
  def test_load_config_malformed_json_returns_defaults(tmp_path, capsys):
      from utils import load_config, CONFIG_DEFAULTS
      zf = tmp_path / "zie-framework"
      zf.mkdir()
      (zf / ".config").write_text("{bad json")
      result = load_config(tmp_path)
      assert result == CONFIG_DEFAULTS
      captured = capsys.readouterr()
      assert "config parse error" in captured.err

  def test_load_config_missing_file_returns_defaults(tmp_path, capsys):
      from utils import load_config, CONFIG_DEFAULTS
      result = load_config(tmp_path)
      assert result == CONFIG_DEFAULTS
      captured = capsys.readouterr()
      assert captured.err == ""
  ```

  Run: `make test-unit` — must FAIL (CONFIG_DEFAULTS not yet defined)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/utils.py`, after the `SDLC_STAGES` list (after line 26), add:

  ```python
  CONFIG_DEFAULTS: dict = {
      "safety_check_mode": "regex",
      "test_runner": "",
      "auto_test_debounce_ms": 3000,
      "auto_test_timeout_ms": 30000,
      "test_indicators": "",
      "project_type": "unknown",
      "zie_memory_enabled": False,
  }
  ```

  Replace `load_config()` (lines 329–342) with:

  ```python
  def load_config(cwd: Path) -> dict:
      """Read zie-framework/.config as JSON and return a dict merged with CONFIG_DEFAULTS.

      CONFIG_DEFAULTS provides all known keys and their default values.
      Loaded values override defaults. Returns CONFIG_DEFAULTS on any error
      (missing file, parse failure, permission denied).
      Logs parse errors to stderr for operator visibility (ADR-019).
      """
      config_path = cwd / "zie-framework" / ".config"
      try:
          loaded = json.loads(config_path.read_text())
          return {**CONFIG_DEFAULTS, **loaded}
      except FileNotFoundError:
          return dict(CONFIG_DEFAULTS)
      except Exception as e:
          print(f"[zie-framework] config parse error: {e}", file=sys.stderr)
          return dict(CONFIG_DEFAULTS)
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No structural changes needed. Verify the module docstring still describes `.config` correctly — no update required.

  Run: `make test-unit` — still PASS

---

## Task 3: Remove inline defaults from hook config.get() call sites

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- All 11 `config.get("key", default)` calls across 5 hook files are replaced with `config.get("key")`.
- No behavioural change: `config` now always contains all keys via `CONFIG_DEFAULTS`, so `.get("key")` returns the same value as `.get("key", default)` did.
- `make test-unit` passes with no regressions.

**Files:**
- Modify: `hooks/auto-test.py` (3 call sites: lines 80, 102, 104, 112)
- Modify: `hooks/task-completed-gate.py` (1 call site: line 36)
- Modify: `hooks/session-resume.py` (4 call sites: lines 31, 32, 40, 45)
- Modify: `hooks/safety-check.py` (1 call site: line 43)
- Modify: `hooks/safety_check_agent.py` (1 call site: line 91)

- [ ] **Step 1: Write failing test (RED)**

  Add to `tests/unit/test_architecture_cleanup.py` (or a new `test_no_inline_config_defaults.py`):

  ```python
  import re
  from pathlib import Path

  HOOKS_DIR = Path(__file__).parents[2] / "hooks"
  HOOK_FILES = [
      "auto-test.py",
      "task-completed-gate.py",
      "session-resume.py",
      "safety-check.py",
      "safety_check_agent.py",
  ]

  def test_no_inline_config_defaults():
      """config.get() calls in hook files must not pass a second default argument.

      CONFIG_DEFAULTS in utils.py is the single source of truth for defaults;
      inline defaults are redundant and risk diverging.
      """
      pattern = re.compile(r'config\.get\(["\']([^"\']+)["\']\s*,\s*[^)]+\)')
      violations = []
      for filename in HOOK_FILES:
          content = (HOOKS_DIR / filename).read_text()
          for lineno, line in enumerate(content.splitlines(), 1):
              if pattern.search(line):
                  violations.append(f"{filename}:{lineno}: {line.strip()}")
      assert not violations, (
          "Inline config.get() defaults found — remove second arg, rely on CONFIG_DEFAULTS:\n"
          + "\n".join(violations)
      )
  ```

  Run: `make test-unit` — must FAIL (all 11 violations detected)

- [ ] **Step 2: Implement (GREEN)**

  **hooks/auto-test.py** — 4 call sites:
  - Line 80: `config.get("test_runner", "")` → `config.get("test_runner")`
  - Line 102: `config.get("auto_test_debounce_ms", 3000)` → `config.get("auto_test_debounce_ms")`
  - Line 104: `config.get("auto_test_debounce_ms", 3000)` → `config.get("auto_test_debounce_ms")`
  - Line 112: `config.get("auto_test_timeout_ms", 30000)` → `config.get("auto_test_timeout_ms")`

  **hooks/task-completed-gate.py** — 1 call site:
  - Line 36: `config.get("test_indicators", "")` → `config.get("test_indicators")`

  **hooks/session-resume.py** — 4 call sites:
  - Line 31: `config.get("project_type", "unknown")` → `config.get("project_type")`
  - Line 32: `config.get("zie_memory_enabled", False)` → `config.get("zie_memory_enabled")`
  - Line 40: `config.get("auto_test_debounce_ms", 3000)` → `config.get("auto_test_debounce_ms")`
  - Line 45: `config.get('test_runner', '')` → `config.get('test_runner')`

  **hooks/safety-check.py** — 1 call site:
  - Line 43: `config.get("safety_check_mode", "regex")` → `config.get("safety_check_mode")`

  **hooks/safety_check_agent.py** — 1 call site:
  - Line 91: `config.get("safety_check_mode", "regex")` → `config.get("safety_check_mode")`

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  No structural changes needed. The hook files are now simpler — no cleanup beyond what was done in Step 2.

  Run: `make test-unit` — still PASS

---

## Task 4: Final verification

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- Full test suite passes with no regressions: `make test-unit`
- All 7 spec acceptance criteria are satisfied (verified by reading code)
- No `config.get(…, …)` with inline defaults remain in any hook file

**Files:**
- No file modifications — verification only

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all tests pass, 0 failures

- [ ] **Step 2: Verify spec acceptance criteria**

  Manually check each criterion:
  1. `parse_roadmap_section()` body: must be `if not path.exists(): return []` + `return parse_roadmap_section_content(...)` — read `hooks/utils.py`
  2. `CONFIG_DEFAULTS` dict at module level with 7 keys — read `hooks/utils.py`
  3. `load_config()` uses `{**CONFIG_DEFAULTS, **loaded}` merge — read `hooks/utils.py`
  4. Grep hook files confirm zero `config.get("key", default)` patterns:
     ```bash
     grep -n 'config\.get(' hooks/auto-test.py hooks/task-completed-gate.py hooks/session-resume.py hooks/safety-check.py hooks/safety_check_agent.py
     ```
     Every line must show `config.get("key")` with no second argument.
  5. All tests pass (done in Step 1)
  6. New unit tests present and passing (done in Step 1)
  7. `parse_roadmap_now` and `parse_roadmap_ready` call sites unchanged — grep confirms they still call `parse_roadmap_section(path, "now"/"ready")`

- [ ] **Step 3: Refactor**

  Nothing to do.
