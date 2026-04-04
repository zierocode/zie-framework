---
approved: false
approved_at:
backlog: backlog/split-utils-py.md
---

# Split utils.py into Sub-Modules — Implementation Plan

**Goal:** Break the 737-line `hooks/utils.py` monolith into five single-responsibility sub-modules (`utils_config`, `utils_io`, `utils_roadmap`, `utils_safety`, `utils_event`), update all 18+ hook imports and 7+ test file imports, then delete the original file.
**Architecture:** One-pass direct migration (Approach B from spec): all sub-modules are created first as exact relocations of existing symbols (no renames, no logic changes), then all hook/test imports are redirected in grouped batches, and finally `utils.py` is deleted. Each sub-module is independently importable with only stdlib dependencies; no circular imports exist between sub-modules. No facade is kept.
**Tech Stack:** Python 3 (stdlib only), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `hooks/utils_config.py` | Config loading: `CONFIG_SCHEMA`, `CONFIG_DEFAULTS`, `validate_config`, `load_config` |
| Create | `hooks/utils_io.py` | File I/O helpers: `atomic_write`, `safe_write_tmp`, `safe_write_persistent`, `project_tmp_path`, `get_plugin_data_dir`, `persistent_project_path`, `is_zie_initialized`, `get_project_name`, `safe_project_name` |
| Create | `hooks/utils_roadmap.py` | ROADMAP/ADR parsing+caching: `SDLC_STAGES`, `parse_roadmap_section`, `parse_roadmap_section_content`, `parse_roadmap_now`, `parse_roadmap_ready`, `read_roadmap_cached`, `get_cached_roadmap`, `write_roadmap_cache`, `compact_roadmap_done`, `get_cached_git_status`, `write_git_status_cache`, `get_cached_adrs`, `write_adr_cache`, `compute_max_mtime`, `is_mtime_fresh` |
| Create | `hooks/utils_safety.py` | Safety patterns: `BLOCKS`, `WARNS`, `COMPILED_BLOCKS`, `COMPILED_WARNS`, `normalize_command` |
| Create | `hooks/utils_event.py` | Hook event I/O + session utils: `read_event`, `get_cwd`, `sanitize_log_field`, `log_hook_timing`, `call_zie_memory_api` |
| Modify | `hooks/safety-check.py` | Import update: `utils` → `utils_safety`, `utils_event`, `utils_io`, `utils_config` |
| Modify | `hooks/safety_check_agent.py` | Import update: `utils` → `utils_safety`, `utils_event`, `utils_io`, `utils_config` |
| Modify | `hooks/sdlc-permissions.py` | Import update: `utils` → `utils_safety`, `utils_event` |
| Modify | `hooks/stopfailure-log.py` | Import update: `utils` → `utils_event`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/input-sanitizer.py` | Import update: `utils` → `utils_event`, `utils_io` |
| Modify | `hooks/notification-log.py` | Import update: `utils` → `utils_event`, `utils_io` |
| Modify | `hooks/subagent-stop.py` | Import update: `utils` → `utils_event`, `utils_io` |
| Modify | `hooks/session-cleanup.py` | Import update: `utils` → `utils_event`, `utils_io` |
| Modify | `hooks/stop-guard.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io` |
| Modify | `hooks/task-completed-gate.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io` |
| Modify | `hooks/auto-test.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io` |
| Modify | `hooks/session-resume.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/failure-context.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/sdlc-compact.py` | Import update: `utils` → `utils_event`, `utils_config`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/wip-checkpoint.py` | Import update: `utils` → `utils_event`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/intent-sdlc.py` | Import update: `utils` → `utils_event`, `utils_io`, `utils_roadmap` |
| Modify | `hooks/subagent-context.py` | Import update: `utils` → `utils_event`, `utils_roadmap` |
| Modify | `hooks/session-learn.py` | Import update: `utils` → `utils_event`, `utils_io`, `utils_roadmap` |
| Modify | `tests/unit/test_utils.py` | Update `from utils import` → correct sub-modules |
| Modify | `tests/unit/test_utils_helpers.py` | Update `from utils import` → `utils_io` |
| Modify | `tests/unit/test_utils_ready.py` | Update `from utils import` → `utils_roadmap` |
| Modify | `tests/unit/test_utils_sanitize.py` | Update `from utils import` → `utils_config`, `utils_event` |
| Modify | `tests/unit/test_utils_write_permissions.py` | Update `from utils import` → `utils_io` |
| Modify | `tests/unit/test_compact_roadmap_done.py` | Update `from utils import` → `utils_roadmap` |
| Modify | `tests/unit/test_safety_check_precompile.py` | Update `import utils` → `import utils_safety as utils` |
| Modify | `tests/unit/test_adr_cache.py` | Update `from utils import` → `utils_roadmap` |
| Modify | `tests/unit/test_architecture_cleanup.py` | Update `"from utils import"` assertion to accept `utils_config` / `utils_event` |
| Delete | `hooks/utils.py` | Replaced by five sub-modules |

---

## Task 1: Create utils_config.py

**Acceptance Criteria:**
- `hooks/utils_config.py` exists and exports: `CONFIG_SCHEMA`, `CONFIG_DEFAULTS`, `validate_config`, `load_config`
- File is independently importable: `python3 -c "import sys; sys.path.insert(0,'hooks'); from utils_config import CONFIG_SCHEMA, CONFIG_DEFAULTS, validate_config, load_config; print('ok')"` → `ok`
- No import from `utils` anywhere in the file
- `make test-unit` — no new failures (other tests unaffected; `utils.py` still present)

**Files:**
- Create: `hooks/utils_config.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add to a new `tests/unit/test_utils_submodules_importable.py`:

  ```python
  """Smoke tests: each sub-module is independently importable."""
  import subprocess, sys

  def _import_ok(module, symbols):
      cmd = (
          f"import sys; sys.path.insert(0, 'hooks'); "
          f"from {module} import {', '.join(symbols)}; print('ok')"
      )
      r = subprocess.run([sys.executable, "-c", cmd],
                        capture_output=True, text=True,
                        cwd="/Users/zie/Code/zie-framework")
      assert r.returncode == 0 and "ok" in r.stdout, r.stderr

  def test_utils_config_importable():
      _import_ok("utils_config", ["CONFIG_SCHEMA", "CONFIG_DEFAULTS", "validate_config", "load_config"])

  def test_utils_io_importable():
      _import_ok("utils_io", ["atomic_write", "safe_write_tmp", "safe_write_persistent",
                              "project_tmp_path", "get_plugin_data_dir", "persistent_project_path",
                              "is_zie_initialized", "get_project_name", "safe_project_name"])

  def test_utils_roadmap_importable():
      _import_ok("utils_roadmap", ["SDLC_STAGES", "parse_roadmap_section", "parse_roadmap_section_content",
                                   "parse_roadmap_now", "parse_roadmap_ready", "read_roadmap_cached",
                                   "get_cached_roadmap", "write_roadmap_cache", "compact_roadmap_done",
                                   "get_cached_git_status", "write_git_status_cache",
                                   "get_cached_adrs", "write_adr_cache", "compute_max_mtime", "is_mtime_fresh"])

  def test_utils_safety_importable():
      _import_ok("utils_safety", ["BLOCKS", "WARNS", "COMPILED_BLOCKS", "COMPILED_WARNS", "normalize_command"])

  def test_utils_event_importable():
      _import_ok("utils_event", ["read_event", "get_cwd", "sanitize_log_field",
                                 "log_hook_timing", "call_zie_memory_api"])

  def test_no_import_from_utils_in_hooks():
      """After full migration: no hook file imports from bare 'utils'."""
      import re
      from pathlib import Path
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for f in sorted(hooks_dir.glob("*.py")):
          if f.name == "utils.py":
              continue  # utils.py itself is being deleted
          content = f.read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(f.name)
      assert not violations, f"Hooks still importing from bare 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_utils_config_importable` FAILS (file not yet created). Others may pass if previously green.

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_config.py` by extracting the config symbols from `hooks/utils.py` (lines with `CONFIG_SCHEMA`, `CONFIG_DEFAULTS`, `validate_config`, `load_config`). Copy the exact implementations — no logic changes.

  ```python
  #!/usr/bin/env python3
  """Config loading and validation for zie-framework hooks."""
  import json
  import os
  import sys
  from pathlib import Path

  CONFIG_SCHEMA: dict = {
      # <exact copy from utils.py — do not alter>
  }

  CONFIG_DEFAULTS: dict = {
      # <exact copy from utils.py — do not alter>
  }


  def validate_config(config: dict) -> dict:
      # <exact copy from utils.py — do not alter>
      ...


  def load_config(cwd: Path) -> dict:
      # <exact copy from utils.py — do not alter>
      ...
  ```

  Note: Copy the complete function bodies verbatim from `utils.py`. No stdlib imports beyond `json`, `os`, `sys`, `pathlib.Path` are needed.

  Run: `make test-unit` — `test_utils_config_importable` PASSES

- [ ] **Step 3: Refactor**

  Verify independence: `python3 -c "import sys; sys.path.insert(0,'hooks'); from utils_config import load_config; print('ok')"` → `ok`
  Verify no circular imports: the file must not import from any other `utils_*.py`.

  Run: `make test-unit` — still PASS

---

## Task 2: Create utils_safety.py

**Acceptance Criteria:**
- `hooks/utils_safety.py` exists and exports: `BLOCKS`, `WARNS`, `COMPILED_BLOCKS`, `COMPILED_WARNS`, `normalize_command`
- Independently importable
- `COMPILED_BLOCKS` and `COMPILED_WARNS` are pre-compiled at import time with `re.IGNORECASE`

**Files:**
- Create: `hooks/utils_safety.py`

- [ ] **Step 1: Write failing tests (RED)**

  Task 1 wrote `test_utils_submodules_importable.py` which includes `test_utils_safety_importable`. Confirm it fails:

  Run: `make test-unit` — `test_utils_safety_importable` FAILS (file not yet created)

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_safety.py`:

  ```python
  #!/usr/bin/env python3
  """Safety pattern constants and command normalization for zie-framework hooks."""
  import re

  # <exact copy of BLOCKS list from utils.py — do not alter patterns or messages>
  BLOCKS = [...]

  # <exact copy of WARNS list from utils.py — do not alter patterns or messages>
  WARNS = [...]

  COMPILED_BLOCKS = [(re.compile(p, re.IGNORECASE), msg) for p, msg in BLOCKS]
  COMPILED_WARNS  = [(re.compile(p, re.IGNORECASE), msg) for p, msg in WARNS]


  def normalize_command(cmd: str) -> str:
      # <exact copy from utils.py — do not alter>
      ...
  ```

  Only stdlib import: `re`.

  Run: `make test-unit` — `test_utils_safety_importable` PASSES; `test_safety_check_precompile.py` still works (imports `utils` which still exists)

- [ ] **Step 3: Refactor**

  Verify independence: `python3 -c "import sys; sys.path.insert(0,'hooks'); import utils_safety; print(len(utils_safety.BLOCKS))"` → non-zero integer

  Run: `make test-unit` — still PASS

---

## Task 3: Create utils_event.py

**Acceptance Criteria:**
- `hooks/utils_event.py` exists and exports: `read_event`, `get_cwd`, `sanitize_log_field`, `log_hook_timing`, `call_zie_memory_api`
- Independently importable with no import from `utils_config`, `utils_io`, `utils_roadmap`, or `utils_safety`

**Files:**
- Create: `hooks/utils_event.py`

- [ ] **Step 1: Write failing tests (RED)**

  `test_utils_event_importable` from Task 1 covers this. Confirm it fails:

  Run: `make test-unit` — `test_utils_event_importable` FAILS

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_event.py`:

  ```python
  #!/usr/bin/env python3
  """Hook event I/O and session utilities for zie-framework hooks."""
  import json
  import os
  import sys
  import urllib.request
  from pathlib import Path

  # <exact copy of read_event(), get_cwd(), sanitize_log_field(),
  #  log_hook_timing(), call_zie_memory_api() from utils.py — no logic changes>
  ```

  Stdlib imports: `json`, `os`, `sys`, `urllib.request`, `pathlib.Path`, `time` (for `log_hook_timing`).

  Run: `make test-unit` — `test_utils_event_importable` PASSES

- [ ] **Step 3: Refactor**

  Verify no cross-dependency: `python3 -c "import sys; sys.path.insert(0,'hooks'); from utils_event import read_event, get_cwd; print('ok')"` → `ok`

  Run: `make test-unit` — still PASS

---

## Task 4: Create utils_io.py

**Acceptance Criteria:**
- `hooks/utils_io.py` exists and exports all 9 I/O symbols from spec
- Independently importable; no imports from other `utils_*.py` sub-modules

**Files:**
- Create: `hooks/utils_io.py`

- [ ] **Step 1: Write failing tests (RED)**

  `test_utils_io_importable` from Task 1 covers this. Confirm it fails:

  Run: `make test-unit` — `test_utils_io_importable` FAILS

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_io.py`:

  ```python
  #!/usr/bin/env python3
  """File I/O helpers (tmp + persistent storage tiers) for zie-framework hooks."""
  import os
  import sys
  import tempfile
  from pathlib import Path

  # <exact copy of all 9 functions/constants from utils.py:
  #   atomic_write, safe_write_tmp, safe_write_persistent, project_tmp_path,
  #   get_plugin_data_dir, persistent_project_path, is_zie_initialized,
  #   get_project_name, safe_project_name — no logic changes>
  ```

  Note: `safe_write_tmp` and `safe_write_persistent` use `atomic_write` internally — both are in the same file, so no cross-dependency.

  Run: `make test-unit` — `test_utils_io_importable` PASSES

- [ ] **Step 3: Refactor**

  Verify: `python3 -c "import sys; sys.path.insert(0,'hooks'); from utils_io import atomic_write, project_tmp_path, is_zie_initialized; print('ok')"` → `ok`

  Run: `make test-unit` — still PASS

---

## Task 5: Create utils_roadmap.py

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- `hooks/utils_roadmap.py` exists and exports all 15 symbols from spec (including `SDLC_STAGES`)
- `compute_max_mtime` and `is_mtime_fresh` are in `utils_roadmap.py` (not `utils_io.py`) per spec note
- Independently importable; imports from `utils_io` are acceptable only if `utils_io` is listed (but spec says no cross-dependencies — verify `utils_roadmap` only uses stdlib)

**Files:**
- Create: `hooks/utils_roadmap.py`

- [ ] **Step 1: Write failing tests (RED)**

  `test_utils_roadmap_importable` from Task 1 covers this. Confirm it fails:

  Run: `make test-unit` — `test_utils_roadmap_importable` FAILS

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_roadmap.py`:

  ```python
  #!/usr/bin/env python3
  """ROADMAP parsing, caching, ADR caching, and mtime gate helpers."""
  import json
  import os
  import sys
  import time
  from datetime import date, timedelta
  from pathlib import Path

  SDLC_STAGES: list = [...]  # <exact copy from utils.py>

  # <exact copy of all roadmap/cache/mtime functions from utils.py:
  #   parse_roadmap_section, parse_roadmap_section_content, parse_roadmap_now,
  #   parse_roadmap_ready, read_roadmap_cached, get_cached_roadmap,
  #   write_roadmap_cache, compact_roadmap_done, get_cached_git_status,
  #   write_git_status_cache, get_cached_adrs, write_adr_cache,
  #   compute_max_mtime, is_mtime_fresh — no logic changes>
  ```

  Note: `compact_roadmap_done` uses `project_tmp_path` internally. Check if it does — if so, it must be inlined or `project_tmp_path` must be copied here too. Verify from actual utils.py source and add the dependency accordingly (keeping stdlib-only constraint means inline it if needed).

  Run: `make test-unit` — `test_utils_roadmap_importable` PASSES

- [ ] **Step 3: Refactor**

  Verify: `python3 -c "import sys; sys.path.insert(0,'hooks'); from utils_roadmap import parse_roadmap_now, compact_roadmap_done, SDLC_STAGES; print(SDLC_STAGES)"` → list output

  Run: `make test-unit` — still PASS

---

## Task 6: Hook import group A — safety hooks

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- `hooks/safety-check.py`: `from utils import ...` replaced with separate imports from `utils_safety`, `utils_event`, `utils_io`, `utils_config`
- `hooks/safety_check_agent.py`: same treatment with its imported symbols
- `hooks/sdlc-permissions.py`: `from utils import normalize_command, read_event` → `from utils_safety import normalize_command` + `from utils_event import read_event`
- No import from bare `utils` in any of these three files
- `make test-unit` — all safety-check and safety-agent tests still PASS

**Files:**
- Modify: `hooks/safety-check.py`
- Modify: `hooks/safety_check_agent.py`
- Modify: `hooks/sdlc-permissions.py`

- [ ] **Step 1: Write failing tests (RED)**

  `test_no_import_from_utils_in_hooks` from Task 1's test file will eventually gate this (it runs after all hooks are migrated). For now, add a targeted check:

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_group_a_hooks_no_bare_utils_import():
      """Group A hooks must not import from bare 'utils'."""
      import re
      from pathlib import Path
      group_a = ["safety-check.py", "safety_check_agent.py", "sdlc-permissions.py"]
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for name in group_a:
          content = (hooks_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Group A hooks still importing from 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_group_a_hooks_no_bare_utils_import` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/safety-check.py`** — replace:
  ```python
  # BEFORE:
  from utils import COMPILED_BLOCKS, COMPILED_WARNS, get_cwd, load_config, normalize_command, project_tmp_path, read_event
  # AFTER:
  from utils_safety import COMPILED_BLOCKS, COMPILED_WARNS, normalize_command
  from utils_event import get_cwd, read_event
  from utils_io import project_tmp_path
  from utils_config import load_config
  ```

  **`hooks/safety_check_agent.py`** — replace:
  ```python
  # BEFORE:
  from utils import BLOCKS, get_cwd, load_config, normalize_command, read_event
  # AFTER:
  from utils_safety import BLOCKS, normalize_command
  from utils_event import get_cwd, read_event
  from utils_config import load_config
  ```

  **`hooks/sdlc-permissions.py`** — replace:
  ```python
  # BEFORE:
  from utils import normalize_command, read_event
  # AFTER:
  from utils_safety import normalize_command
  from utils_event import read_event
  ```

  Run: `make test-unit` — `test_group_a_hooks_no_bare_utils_import` PASSES; all safety tests still green

- [ ] **Step 3: Refactor**

  Run: `python3 hooks/safety-check.py < /dev/null` → exits 0 (no import errors)
  Run: `make test-unit` — still PASS

---

## Task 7: Hook import group B — simple io+event hooks

<!-- depends_on: Task 3, Task 4 -->

**Acceptance Criteria:**
- `hooks/stopfailure-log.py`, `hooks/input-sanitizer.py`, `hooks/notification-log.py`, `hooks/subagent-stop.py`, `hooks/session-cleanup.py` have no import from bare `utils`
- All use only `utils_event`, `utils_io`, and (for stopfailure-log.py) `utils_roadmap`
- `make test-unit` — no regressions

**Files:**
- Modify: `hooks/stopfailure-log.py`
- Modify: `hooks/input-sanitizer.py`
- Modify: `hooks/notification-log.py`
- Modify: `hooks/subagent-stop.py`
- Modify: `hooks/session-cleanup.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_group_b_hooks_no_bare_utils_import():
      import re
      from pathlib import Path
      group_b = ["stopfailure-log.py", "input-sanitizer.py",
                 "notification-log.py", "subagent-stop.py", "session-cleanup.py"]
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for name in group_b:
          content = (hooks_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Group B hooks still importing from 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_group_b_hooks_no_bare_utils_import` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/stopfailure-log.py`** — replace `from utils import get_cwd, parse_roadmap_now, project_tmp_path, read_event, safe_project_name, sanitize_log_field`:
  ```python
  from utils_event import get_cwd, read_event, sanitize_log_field
  from utils_io import project_tmp_path, safe_project_name
  from utils_roadmap import parse_roadmap_now
  ```

  **`hooks/input-sanitizer.py`** — replace `from utils import get_cwd, read_event`:
  ```python
  from utils_event import get_cwd, read_event
  ```

  **`hooks/notification-log.py`** — replace `from utils import get_cwd, project_tmp_path, read_event, safe_project_name, safe_write_tmp, sanitize_log_field`:
  ```python
  from utils_event import get_cwd, read_event, sanitize_log_field
  from utils_io import project_tmp_path, safe_project_name, safe_write_tmp
  ```

  **`hooks/subagent-stop.py`** — replace `from utils import atomic_write, get_cwd, project_tmp_path, read_event`:
  ```python
  from utils_event import get_cwd, read_event
  from utils_io import atomic_write, project_tmp_path
  ```

  **`hooks/session-cleanup.py`** — replace `from utils import get_cwd, read_event, safe_project_name`:
  ```python
  from utils_event import get_cwd, read_event
  from utils_io import safe_project_name
  ```

  Run: `make test-unit` — `test_group_b_hooks_no_bare_utils_import` PASSES

- [ ] **Step 3: Refactor**

  Spot-check each hook loads without error:
  ```bash
  echo '{}' | python3 hooks/stopfailure-log.py; echo '{}' | python3 hooks/notification-log.py
  ```
  Both should exit 0 (outer guard catches bad event, exits 0).

  Run: `make test-unit` — still PASS

---

## Task 8: Hook import group C — config+io+event hooks

<!-- depends_on: Task 1, Task 3, Task 4 -->

**Acceptance Criteria:**
- `hooks/stop-guard.py`, `hooks/task-completed-gate.py`, `hooks/auto-test.py` have no import from bare `utils`
- `make test-unit` — no regressions

**Files:**
- Modify: `hooks/stop-guard.py`
- Modify: `hooks/task-completed-gate.py`
- Modify: `hooks/auto-test.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_group_c_hooks_no_bare_utils_import():
      import re
      from pathlib import Path
      group_c = ["stop-guard.py", "task-completed-gate.py", "auto-test.py"]
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for name in group_c:
          content = (hooks_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Group C hooks still importing from 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_group_c_hooks_no_bare_utils_import` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/stop-guard.py`** — replace `from utils import get_cwd, load_config, read_event`:
  ```python
  from utils_event import get_cwd, read_event
  from utils_config import load_config
  ```

  **`hooks/task-completed-gate.py`** — replace `from utils import get_cwd, load_config, read_event`:
  ```python
  from utils_event import get_cwd, read_event
  from utils_config import load_config
  ```

  **`hooks/auto-test.py`** — replace `from utils import get_cwd, load_config, log_hook_timing, project_tmp_path, read_event, safe_write_tmp`:
  ```python
  from utils_event import get_cwd, read_event, log_hook_timing
  from utils_config import load_config
  from utils_io import project_tmp_path, safe_write_tmp
  ```

  Run: `make test-unit` — `test_group_c_hooks_no_bare_utils_import` PASSES

- [ ] **Step 3: Refactor**

  Run: `make test-unit` — still PASS

---

## Task 9: Hook import group D — roadmap-heavy hooks

<!-- depends_on: Task 1, Task 3, Task 4, Task 5 -->

**Acceptance Criteria:**
- `hooks/session-resume.py`, `hooks/failure-context.py`, `hooks/sdlc-compact.py`, `hooks/wip-checkpoint.py` have no import from bare `utils`
- `make test-unit` — no regressions

**Files:**
- Modify: `hooks/session-resume.py`
- Modify: `hooks/failure-context.py`
- Modify: `hooks/sdlc-compact.py`
- Modify: `hooks/wip-checkpoint.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_group_d_hooks_no_bare_utils_import():
      import re
      from pathlib import Path
      group_d = ["session-resume.py", "failure-context.py", "sdlc-compact.py", "wip-checkpoint.py"]
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for name in group_d:
          content = (hooks_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Group D hooks still importing from 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_group_d_hooks_no_bare_utils_import` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/session-resume.py`** — replace `from utils import get_cwd, load_config, log_hook_timing, parse_roadmap_now, read_event`:
  ```python
  from utils_event import get_cwd, read_event, log_hook_timing
  from utils_config import load_config
  from utils_roadmap import parse_roadmap_now
  ```

  **`hooks/failure-context.py`** — replace:
  ```python
  # BEFORE:
  from utils import (
      get_cached_git_status, get_cwd, load_config, parse_roadmap_section_content,
      read_event, read_roadmap_cached, write_git_status_cache,
  )
  # AFTER:
  from utils_event import get_cwd, read_event
  from utils_config import load_config
  from utils_roadmap import (
      get_cached_git_status, parse_roadmap_section_content,
      read_roadmap_cached, write_git_status_cache,
  )
  ```

  **`hooks/sdlc-compact.py`** — replace:
  ```python
  # BEFORE:
  from utils import (
      get_cached_git_status, get_cwd, load_config, parse_roadmap_section_content,
      project_tmp_path, read_event, read_roadmap_cached, safe_write_tmp, write_git_status_cache,
  )
  # AFTER:
  from utils_event import get_cwd, read_event
  from utils_config import load_config
  from utils_io import project_tmp_path, safe_write_tmp
  from utils_roadmap import (
      get_cached_git_status, parse_roadmap_section_content,
      read_roadmap_cached, write_git_status_cache,
  )
  ```

  **`hooks/wip-checkpoint.py`** — replace:
  ```python
  # BEFORE:
  from utils import (
      call_zie_memory_api, get_cwd, parse_roadmap_now, persistent_project_path,
      read_event, safe_write_persistent,
  )
  # AFTER:
  from utils_event import get_cwd, read_event, call_zie_memory_api
  from utils_io import persistent_project_path, safe_write_persistent
  from utils_roadmap import parse_roadmap_now
  ```

  Run: `make test-unit` — `test_group_d_hooks_no_bare_utils_import` PASSES

- [ ] **Step 3: Refactor**

  Run: `make test-unit` — still PASS

---

## Task 10: Hook import group E — remaining roadmap hooks

<!-- depends_on: Task 3, Task 4, Task 5 -->

**Acceptance Criteria:**
- `hooks/intent-sdlc.py`, `hooks/subagent-context.py`, `hooks/session-learn.py` have no import from bare `utils`
- `make test-unit` — no regressions

**Files:**
- Modify: `hooks/intent-sdlc.py`
- Modify: `hooks/subagent-context.py`
- Modify: `hooks/session-learn.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_group_e_hooks_no_bare_utils_import():
      import re
      from pathlib import Path
      group_e = ["intent-sdlc.py", "subagent-context.py", "session-learn.py"]
      hooks_dir = Path("/Users/zie/Code/zie-framework/hooks")
      violations = []
      for name in group_e:
          content = (hooks_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Group E hooks still importing from 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_group_e_hooks_no_bare_utils_import` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`hooks/intent-sdlc.py`** — replace:
  ```python
  # BEFORE:
  from utils import (
      get_cwd, parse_roadmap_section_content, project_tmp_path,
      read_event, read_roadmap_cached,
  )
  # AFTER:
  from utils_event import get_cwd, read_event
  from utils_io import project_tmp_path
  from utils_roadmap import parse_roadmap_section_content, read_roadmap_cached
  ```

  **`hooks/subagent-context.py`** — replace `from utils import get_cwd, parse_roadmap_section_content, read_event, read_roadmap_cached`:
  ```python
  from utils_event import get_cwd, read_event
  from utils_roadmap import parse_roadmap_section_content, read_roadmap_cached
  ```

  **`hooks/session-learn.py`** — replace `from utils import atomic_write, call_zie_memory_api, get_cwd, parse_roadmap_now, persistent_project_path, read_event`:
  ```python
  from utils_event import get_cwd, read_event, call_zie_memory_api
  from utils_io import atomic_write, persistent_project_path
  from utils_roadmap import parse_roadmap_now
  ```

  Run: `make test-unit` — `test_group_e_hooks_no_bare_utils_import` PASSES

- [ ] **Step 3: Refactor**

  Run: `make test-unit` — still PASS

---

## Task 11: Update test file imports

<!-- depends_on: Task 1, Task 2, Task 3, Task 4, Task 5 -->

**Acceptance Criteria:**
- All 7 spec-listed test files + `test_adr_cache.py` have no `from utils import` targeting the old monolith
- `test_safety_check_precompile.py` imports `utils_safety` (not bare `utils`)
- `test_architecture_cleanup.py` assertion updated to accept `utils_config` or `utils_event` instead of bare `utils`
- `make test-unit` — all tests still PASS (sub-modules provide same symbols)

**Files:**
- Modify: `tests/unit/test_utils.py`
- Modify: `tests/unit/test_utils_helpers.py`
- Modify: `tests/unit/test_utils_ready.py`
- Modify: `tests/unit/test_utils_sanitize.py`
- Modify: `tests/unit/test_utils_write_permissions.py`
- Modify: `tests/unit/test_compact_roadmap_done.py`
- Modify: `tests/unit/test_safety_check_precompile.py`
- Modify: `tests/unit/test_adr_cache.py`
- Modify: `tests/unit/test_architecture_cleanup.py`

- [ ] **Step 1: Write failing tests (RED)**

  The `test_no_import_from_utils_in_hooks` test in `test_utils_submodules_importable.py` is for hooks. Add a parallel check for test files:

  ```python
  # Append to tests/unit/test_utils_submodules_importable.py:

  def test_no_bare_utils_import_in_spec_test_files():
      """After migration: none of the 7 spec test files import from bare 'utils'."""
      import re
      from pathlib import Path
      spec_test_files = [
          "test_utils.py", "test_utils_helpers.py", "test_utils_ready.py",
          "test_utils_sanitize.py", "test_utils_write_permissions.py",
          "test_compact_roadmap_done.py", "test_safety_check_precompile.py",
          "test_adr_cache.py",
      ]
      tests_dir = Path("/Users/zie/Code/zie-framework/tests/unit")
      violations = []
      for name in spec_test_files:
          content = (tests_dir / name).read_text()
          if re.search(r"from utils import|import utils\b", content):
              violations.append(name)
      assert not violations, f"Spec test files still importing from bare 'utils': {violations}"
  ```

  Run: `make test-unit` — `test_no_bare_utils_import_in_spec_test_files` FAILS

- [ ] **Step 2: Implement (GREEN)**

  **`tests/unit/test_utils_helpers.py`** — replace `from utils import get_project_name, is_zie_initialized`:
  ```python
  from utils_io import get_project_name, is_zie_initialized
  ```

  **`tests/unit/test_utils_ready.py`** — replace `from utils import parse_roadmap_ready`:
  ```python
  from utils_roadmap import parse_roadmap_ready
  ```

  **`tests/unit/test_utils_sanitize.py`** — replace `from utils import load_config, sanitize_log_field`:
  ```python
  from utils_config import load_config
  from utils_event import sanitize_log_field
  ```

  **`tests/unit/test_utils_write_permissions.py`** — replace `from utils import atomic_write, safe_write_persistent, safe_write_tmp`:
  ```python
  from utils_io import atomic_write, safe_write_persistent, safe_write_tmp
  ```

  **`tests/unit/test_compact_roadmap_done.py`** — replace `from utils import compact_roadmap_done`:
  ```python
  from utils_roadmap import compact_roadmap_done
  ```

  **`tests/unit/test_adr_cache.py`** — replace `from utils import get_cached_adrs, write_adr_cache`:
  ```python
  from utils_roadmap import get_cached_adrs, write_adr_cache
  ```

  **`tests/unit/test_safety_check_precompile.py`** — replace `import utils` with:
  ```python
  import utils_safety as utils
  ```
  All assertions use `utils.COMPILED_BLOCKS` etc. — the alias preserves them unchanged.

  **`tests/unit/test_utils.py`** — this file has many inline `from utils import ...` calls inside test methods. Update each `from utils import X` → `from utils_X_module import X` per the mapping:
  - `BLOCKS`, `WARNS`, `COMPILED_BLOCKS`, `COMPILED_WARNS`, `normalize_command` → `utils_safety`
  - `CONFIG_DEFAULTS`, `load_config`, `validate_config` → `utils_config`
  - `SDLC_STAGES` → `utils_roadmap`
  - `atomic_write`, `safe_write_tmp`, `safe_write_persistent`, `get_plugin_data_dir`, `safe_project_name`, `persistent_project_path` → `utils_io`
  - `call_zie_memory_api` → `utils_event`
  - `get_cached_git_status`, `write_git_status_cache`, `compute_max_mtime`, `is_mtime_fresh` → `utils_roadmap`
  - `log_hook_timing` → `utils_event`
  Also update: `from utils import (` at top of file and `from utils import compute_max_mtime, is_mtime_fresh` and `from utils import get_cached_git_status, write_git_status_cache` and `from utils import log_hook_timing`.

  **`tests/unit/test_architecture_cleanup.py`** — update the assertion:
  ```python
  # BEFORE:
  assert "from utils import" in content
  # AFTER:
  assert "from utils_config import" in content or "from utils_event import" in content, (
      "task-completed-gate.py must import from utils_config or utils_event sub-modules"
  )
  ```

  Run: `make test-unit` — all tests PASS

- [ ] **Step 3: Refactor**

  Run: `make test-unit` — still PASS

---

## Task 12: Delete utils.py and full CI gate

<!-- depends_on: Task 6, Task 7, Task 8, Task 9, Task 10, Task 11 -->

**Acceptance Criteria:**
- `hooks/utils.py` does not exist
- `make test-ci` passes with no new failures and coverage gate met
- `make lint` passes
- `test_no_import_from_utils_in_hooks` (from Task 1) PASSES — no hook imports bare `utils`

**Files:**
- Delete: `hooks/utils.py`

- [ ] **Step 1: Write failing tests (RED)**

  N/A — no new tests. Confirm the final guard:

  ```bash
  python3 -m pytest tests/unit/test_utils_submodules_importable.py -v
  ```

  All sub-module importability tests and all group tests must be PASS. Only `test_no_import_from_utils_in_hooks` might still FAIL if any hook still imports bare `utils` — fix before proceeding.

- [ ] **Step 2: Implement (GREEN)**

  Delete `utils.py`:
  ```bash
  git rm hooks/utils.py
  ```

  Run: `make test-unit` — must PASS (no test directly imports `utils.py` by path anymore)
  Run: `make test-ci` — must PASS

- [ ] **Step 3: Refactor**

  ```bash
  make lint
  ```
  Fix any lint issues (unused imports, etc.).

  ```bash
  make test-ci
  ```
  Must still PASS.

---

## Task Parallelism Map

| Phase | Tasks | Can run parallel |
| --- | --- | --- |
| Phase 1: Create sub-modules | T1, T2, T3, T4 | Yes — all independent |
| Phase 1 continued | T5 | After T4 (uses T4's `project_tmp_path` check) |
| Phase 2: Hook groups A+B+C | T6, T7, T8 | Yes — different files; T6 needs T1+T2+T3+T4, T7 needs T3+T4, T8 needs T1+T3+T4 |
| Phase 2 continued | T9, T10 | Yes — T9 needs T1+T3+T4+T5, T10 needs T3+T4+T5 |
| Phase 3: Test updates | T11 | After T1-T5 (imports sub-modules directly) |
| Phase 4: Delete + CI | T12 | After ALL |
