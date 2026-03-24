---
approved: true
approved_at: 2026-03-24
backlog: backlog/standards-compliance.md
---

# Standards: Compliance and Consistency Gaps — Design Spec

**Problem:** Four small compliance gaps: (1) `test_versioning_gate.py` only checks that `zie-release.md` *mentions* VERSION/plugin.json, not that the files actually match; (2) Two hooks use `[zie] warning:` instead of the standard `[zie-framework] <hook>:` log prefix; (3) The 63 integration tests deselected by `make test-unit` are undocumented; (4) `notification-log.py:65` assigns raw `cwd.name` to `project`, inconsistent with other hooks that use `safe_project_name()`.

**Approach:** Four targeted fixes. GitHub Actions CI and SLSA provenance workflows already exist (`.github/workflows/ci.yml` and `release-provenance.yml`) — no action needed there.

**Components:**

- `tests/unit/test_versioning_gate.py`
  - Add `test_version_files_match()` — read `VERSION` and `plugin.json`, assert versions are equal
  - Keep existing 5 tests unchanged (they check zie-release.md documentation, which is separate)

- `hooks/auto-test.py`
  - Line 83: change `f"[zie] warning: .config unreadable ({e}), using defaults"` → `f"[zie-framework] auto-test: .config unreadable ({e}), using defaults"`

- `hooks/session-resume.py`
  - Line 26: same fix — change `f"[zie] warning: .config unreadable ({e}), using defaults"` → `f"[zie-framework] session-resume: .config unreadable ({e}), using defaults"`

- `CLAUDE.md`
  - Add integration test note to Development Commands section

- `Makefile`
  - Add comment on integration test exclusion above `test-unit` target

- `hooks/notification-log.py`
  - Line 65: change `project = get_cwd().name` → `project = safe_project_name(get_cwd().name)`
  - Add `safe_project_name` to the utils import

**Data Flow:**

**1. Version consistency test:**
```python
# tests/unit/test_versioning_gate.py (new test in existing class)
import json
from pathlib import Path

ROOT = Path(__file__).parents[2]

def test_version_files_match():
    version_file = (ROOT / "VERSION").read_text().strip()
    plugin_json = json.loads((ROOT / ".claude-plugin" / "plugin.json").read_text())
    assert version_file == plugin_json["version"], (
        f"VERSION file ({version_file}) does not match "
        f"plugin.json version ({plugin_json['version']}). "
        f"Run 'make bump NEW={version_file}' to sync them."
    )
```

**2. Log prefix standardization:**

BEFORE (auto-test.py:83 and session-resume.py:26):
```python
f"[zie] warning: .config unreadable ({e}), using defaults"
```

AFTER:
```python
f"[zie-framework] auto-test: .config unreadable ({e}), using defaults"
f"[zie-framework] session-resume: .config unreadable ({e}), using defaults"
```

**3. Integration test documentation:**

CLAUDE.md Development Commands section — add:
```markdown
make test-unit   # fast unit tests only (excludes 63 integration tests)
                 # integration tests require a live Claude session — run manually with make test-int
```

Makefile — add comment:
```makefile
# Note: -m "not integration" deselects ~63 integration tests that require a live
# Claude session. Run 'make test-int' to execute them in a configured environment.
test-unit: ...
```

**4. notification-log.py project name:**

BEFORE:
```python
from utils import ... get_cwd, project_tmp_path, safe_write_tmp
...
project = get_cwd().name
```

AFTER:
```python
from utils import ... get_cwd, project_tmp_path, safe_project_name, safe_write_tmp
...
project = safe_project_name(get_cwd().name)
```

Note: `project_tmp_path(name, project)` already calls `safe_project_name()` internally, so the behavior is unchanged. This is a consistency fix only.

**Edge Cases:**
- `test_version_files_match()` reads `VERSION` relative to the test file — `Path(__file__).parents[2]` reaches the repo root (`tests/unit/` → `tests/` → repo root). Verify this path is correct.
- The test will fail on the first run if VERSION (1.8.0) already matches plugin.json (1.8.0) — it should PASS. The test will catch future drift.
- The version test does not catch `make release` drift (release patches plugin.json but not PROJECT.md) — that's handled separately by the docs-sync-and-completeness spec.
- Log prefix change is purely cosmetic — no behavior change, no test changes needed.
- `safe_project_name()` is already imported in most hooks; notification-log.py just needs to add it to the import.

**GitHub Actions / SLSA (already done):**
- `.github/workflows/ci.yml` — runs `make test` on push/PR to main and dev ✓
- `.github/workflows/release-provenance.yml` — generates SLSA provenance on tag push ✓
- No action needed for these items.

**Out of Scope:**
- `notification-log.py:65` raw `cwd.name` in project dict keys — already sanitized by downstream `project_tmp_path()`. The fix here is for consistency, not correctness.
- Adding branch protection documentation — repo config, not code
- CHANGELOG.md overlap between v1.7.0/v1.8.0 — cosmetic, not a compliance gap
