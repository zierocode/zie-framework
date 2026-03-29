---
approved: false
approved_at:
backlog: backlog/adr-session-cache.md
---

# ADR Session Cache — Implementation Plan

**Goal:** Eliminate redundant ADR file reads across reviewer skills by adding a session-scoped mtime-keyed JSON cache to `hooks/utils.py`, then updating all three reviewer skills and `zie-implement` to use it.
**Architecture:** Two new helpers (`get_cached_adrs` / `write_adr_cache`) follow the exact pattern of `get_cached_git_status` / `write_git_status_cache` (ADR-024): `tempfile.gettempdir()` base, `re.sub` session-ID sanitization, `safe_write_tmp` for the atomic write, and silent fallback on any error. Reviewer skills adopt a cache-first load in Phase 1; `zie-implement` passes `adr_cache_path` in its context bundle instead of the full ADR text. Session cleanup already handles the `zie-<session_id>/` directory — no change needed there.
**Tech Stack:** Python 3.x, pytest, Markdown (skills)

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `hooks/utils.py` | Add `get_cached_adrs(session_id)` and `write_adr_cache(session_id, content)` helpers |
| Create | `tests/unit/test_adr_cache.py` | Unit tests for the two new helpers |
| Modify | `skills/spec-reviewer/SKILL.md` | Replace direct `decisions/*.md` read with cache-first load |
| Modify | `skills/plan-reviewer/SKILL.md` | Replace direct `decisions/*.md` read with cache-first load |
| Modify | `skills/impl-reviewer/SKILL.md` | Cache-first load; accept `adr_cache_path` in context_bundle |
| Modify | `commands/zie-implement.md` | Pass `adr_cache_path` in context bundle instead of full `adrs_content` |

---

## Task 1: Add `get_cached_adrs` and `write_adr_cache` to `hooks/utils.py`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `get_cached_adrs(session_id, decisions_dir)` returns cached ADR content string when cache is fresh (stored mtime equals current max mtime of `decisions_dir/*.md`).
- `get_cached_adrs` returns `None` on cache miss, mtime mismatch, missing `decisions_dir`, or any I/O error.
- `write_adr_cache(session_id, content, decisions_dir)` writes `{"mtime": <max_mtime>, "content": "<text>"}` as JSON to `<tempfile.gettempdir()>/zie-<sanitized_session_id>/adr-cache.json` via `safe_write_tmp`.
- `write_adr_cache` returns `True` on success, `False` on failure (disk full, symlink, etc.).
- Session ID is sanitized via `re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)` before path construction.
- `decisions_dir` empty or missing → `get_cached_adrs` returns `None`; `write_adr_cache` returns `False`.

**Files:**
- Modify: `hooks/utils.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_adr_cache.py
import json
import os
import time
from pathlib import Path

import pytest

# conftest adds hooks/ to sys.path
from utils import get_cached_adrs, write_adr_cache


class TestGetCachedAdrs:
    def test_miss_when_no_cache_file(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        result = get_cached_adrs("sess-adr-001", decisions)
        assert result is None

    def test_hit_when_mtime_matches(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        content = "# ADR-001"
        assert write_adr_cache("sess-adr-002", content, decisions, tmp_dir=tmp_path) is True
        result = get_cached_adrs("sess-adr-002", decisions, tmp_dir=tmp_path)
        assert result == content

    def test_miss_when_adr_newer_than_cache(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        write_adr_cache("sess-adr-003", "# ADR-001", decisions, tmp_dir=tmp_path)
        # Advance mtime of ADR file past cache write time
        future = time.time() + 10
        os.utime(adr, (future, future))
        result = get_cached_adrs("sess-adr-003", decisions, tmp_dir=tmp_path)
        assert result is None

    def test_miss_when_decisions_dir_missing(self, tmp_path):
        result = get_cached_adrs("sess-adr-004", tmp_path / "nonexistent", tmp_dir=tmp_path)
        assert result is None

    def test_miss_when_decisions_dir_empty(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        result = get_cached_adrs("sess-adr-005", decisions, tmp_dir=tmp_path)
        assert result is None

    def test_session_id_sanitized(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        write_adr_cache("../evil/id", "content", decisions, tmp_dir=tmp_path)
        for root, dirs, files in os.walk(str(tmp_path)):
            for f in files:
                full = os.path.join(root, f)
                assert full.startswith(str(tmp_path)), f"file escaped tmp: {full}"

    def test_returns_none_on_read_error(self, tmp_path, monkeypatch):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        write_adr_cache("sess-adr-006", "# ADR-001", decisions, tmp_dir=tmp_path)
        # Corrupt the cache file
        cache_path = tmp_path / "zie-sess-adr-006" / "adr-cache.json"
        cache_path.write_text("not valid json")
        result = get_cached_adrs("sess-adr-006", decisions, tmp_dir=tmp_path)
        assert result is None


class TestWriteAdrCache:
    def test_returns_true_on_success(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        result = write_adr_cache("sess-adr-w01", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result is True

    def test_returns_false_when_decisions_empty(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        result = write_adr_cache("sess-adr-w02", "", decisions, tmp_dir=tmp_path)
        assert result is False

    def test_returns_false_when_decisions_missing(self, tmp_path):
        result = write_adr_cache("sess-adr-w03", "", tmp_path / "nonexistent", tmp_dir=tmp_path)
        assert result is False

    def test_cache_file_has_correct_structure(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        adr = decisions / "ADR-001.md"
        adr.write_text("# ADR-001")
        write_adr_cache("sess-adr-w04", "# ADR-001", decisions, tmp_dir=tmp_path)
        cache_path = tmp_path / "zie-sess-adr-w04" / "adr-cache.json"
        assert cache_path.exists()
        data = json.loads(cache_path.read_text())
        assert "mtime" in data
        assert data["content"] == "# ADR-001"
        assert data["mtime"] == pytest.approx(adr.stat().st_mtime, abs=0.01)

    def test_returns_false_on_symlink(self, tmp_path):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        cache_dir = tmp_path / "zie-sess-adr-w05"
        cache_dir.mkdir(parents=True)
        cache_file = cache_dir / "adr-cache.json"
        link_target = tmp_path / "other.json"
        link_target.write_text("{}")
        cache_file.symlink_to(link_target)
        result = write_adr_cache("sess-adr-w05", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result is False

    def test_silently_returns_false_on_os_error(self, tmp_path, monkeypatch):
        decisions = tmp_path / "decisions"
        decisions.mkdir()
        (decisions / "ADR-001.md").write_text("# ADR-001")
        monkeypatch.setattr(Path, "mkdir", lambda *a, **kw: (_ for _ in ()).throw(OSError("no perms")))
        result = write_adr_cache("sess-adr-w06", "# ADR-001", decisions, tmp_dir=tmp_path)
        assert result is False
```

  Run: `make test-unit` — must FAIL (ImportError: cannot import name 'get_cached_adrs' from 'utils')

- [ ] **Step 2: Implement (GREEN)**

Add to `hooks/utils.py` after the `write_git_status_cache` function:

```python
def get_cached_adrs(
    session_id: str,
    decisions_dir,
    tmp_dir: str | None = None,
) -> str | None:
    """Return cached ADR content if stored mtime matches current max mtime.

    decisions_dir: Path or str pointing to zie-framework/decisions/.
    tmp_dir: override tempfile.gettempdir() (test injection point).
    Returns None on cache miss, mtime mismatch, empty/missing dir, or any error.
    """
    try:
        decisions_path = Path(decisions_dir)
        adr_files = list(decisions_path.glob("*.md"))
        if not adr_files:
            return None
        current_max_mtime = max(f.stat().st_mtime for f in adr_files)
        base = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir())
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        cache_path = base / f"zie-{safe_id}" / "adr-cache.json"
        if not cache_path.exists():
            return None
        data = json.loads(cache_path.read_text())
        if abs(data["mtime"] - current_max_mtime) > 0.001:
            return None
        return data["content"]
    except Exception:
        return None


def write_adr_cache(
    session_id: str,
    content: str,
    decisions_dir,
    tmp_dir: str | None = None,
) -> bool:
    """Write ADR content to session cache keyed by max mtime of decisions_dir.

    decisions_dir: Path or str pointing to zie-framework/decisions/.
    tmp_dir: override tempfile.gettempdir() (test injection point).
    Returns True on success, False if decisions_dir is empty/missing or write fails.
    """
    try:
        decisions_path = Path(decisions_dir)
        adr_files = list(decisions_path.glob("*.md"))
        if not adr_files:
            return False
        max_mtime = max(f.stat().st_mtime for f in adr_files)
        base = Path(tmp_dir) if tmp_dir else Path(tempfile.gettempdir())
        safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', session_id)
        cache_dir = base / f"zie-{safe_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = cache_dir / "adr-cache.json"
        payload = json.dumps({"mtime": max_mtime, "content": content})
        return safe_write_tmp(cache_path, payload)
    except Exception:
        return False
```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm docstrings are consistent with `get_cached_git_status` doc style.
  - Verify `tmp_dir` parameter is the only injection point needed (no global state).
  - Run: `make test-unit` — still PASS

---

## Task 2: Update `skills/spec-reviewer/SKILL.md` — cache-first ADR load

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Phase 1 fallback path reads cache via `get_cached_adrs` before reading `decisions/*.md` directly.
- On cache miss: reads directory, concatenates content, calls `write_adr_cache`; result stored as `adrs_content`.
- On cache hit: uses cached string directly as `adrs_content`; no individual ADR file reads.
- If `decisions/` missing/empty: `adrs_content = "No ADRs found"` — existing behavior preserved.
- `context_bundle` fast-path (when provided by caller) is unchanged.

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_reviewer_skill_adr_cache.py
"""Structural tests: reviewer skills must reference cache helpers in Phase 1."""
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"


def _skill_text(name: str) -> str:
    return (SKILLS_DIR / name / "SKILL.md").read_text()


def test_spec_reviewer_references_get_cached_adrs():
    text = _skill_text("spec-reviewer")
    assert "get_cached_adrs" in text, "spec-reviewer Phase 1 must reference get_cached_adrs"


def test_spec_reviewer_references_write_adr_cache():
    text = _skill_text("spec-reviewer")
    assert "write_adr_cache" in text, "spec-reviewer Phase 1 must reference write_adr_cache"
```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

In `skills/spec-reviewer/SKILL.md`, replace the existing Phase 1 step 2 block:

Old text (lines inside "**If `context_bundle` absent**" block, step 2):
```
2. **ADRs** — read all `zie-framework/decisions/*.md`.
   If directory empty or missing → note "No ADRs found", skip ADR checks.
```

New text:
```
2. **ADRs** — load via session cache (cache-first):
   a. Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
      - Cache hit → use returned string as `adrs_content`. Skip individual file reads.
      - Cache miss or `None` returned → read all `zie-framework/decisions/*.md` files,
        concatenate into `adrs_content`, then call
        `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   b. If `decisions/` directory is empty or missing → `adrs_content = "No ADRs found"`;
      skip ADR checks. (Existing behavior preserved.)
   `session_id` is available from the Claude Code session context.
```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify wording is consistent with plan-reviewer and impl-reviewer (Tasks 3 and 4).
  - Run: `make test-unit` — still PASS

---

## Task 3: Update `skills/plan-reviewer/SKILL.md` — cache-first ADR load

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Phase 1 fallback path uses cache-first ADR load identical to spec-reviewer (Task 2).
- `context_bundle` fast-path unchanged.

**Files:**
- Modify: `skills/plan-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

Add to `tests/unit/test_reviewer_skill_adr_cache.py`:

```python
def test_plan_reviewer_references_get_cached_adrs():
    text = _skill_text("plan-reviewer")
    assert "get_cached_adrs" in text, "plan-reviewer Phase 1 must reference get_cached_adrs"


def test_plan_reviewer_references_write_adr_cache():
    text = _skill_text("plan-reviewer")
    assert "write_adr_cache" in text, "plan-reviewer Phase 1 must reference write_adr_cache"
```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

In `skills/plan-reviewer/SKILL.md`, replace step 2 under "**If `context_bundle` absent**":

Old text:
```
2. **ADRs** — read all `zie-framework/decisions/*.md`.
   If directory empty or missing → note "No ADRs found", skip ADR checks.
```

New text (identical to spec-reviewer):
```
2. **ADRs** — load via session cache (cache-first):
   a. Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
      - Cache hit → use returned string as `adrs_content`. Skip individual file reads.
      - Cache miss or `None` returned → read all `zie-framework/decisions/*.md` files,
        concatenate into `adrs_content`, then call
        `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   b. If `decisions/` directory is empty or missing → `adrs_content = "No ADRs found"`;
      skip ADR checks. (Existing behavior preserved.)
   `session_id` is available from the Claude Code session context.
```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Verify wording is identical to spec-reviewer Phase 1 step 2.
  - Run: `make test-unit` — still PASS

---

## Task 4: Update `skills/impl-reviewer/SKILL.md` — cache-first load + `adr_cache_path` support

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- Phase 1 fallback path uses same cache-first ADR load as spec-reviewer and plan-reviewer.
- Phase 1 `context_bundle` fast-path accepts `adr_cache_path` field in addition to existing `adrs` field:
  - `context_bundle.adr_cache_path` present → read `adr-cache.json` at that path, parse JSON, use `content` field as `adrs_content`.
  - `context_bundle.adrs` present (legacy) → use directly as before.
  - Neither present → fall back to disk read (backward-compatible).
- If `adr_cache_path` points to missing or malformed file → fall back to direct directory read (no crash).

**Files:**
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

Add to `tests/unit/test_reviewer_skill_adr_cache.py`:

```python
def test_impl_reviewer_references_get_cached_adrs():
    text = _skill_text("impl-reviewer")
    assert "get_cached_adrs" in text, "impl-reviewer Phase 1 must reference get_cached_adrs"


def test_impl_reviewer_references_write_adr_cache():
    text = _skill_text("impl-reviewer")
    assert "write_adr_cache" in text, "impl-reviewer Phase 1 must reference write_adr_cache"


def test_impl_reviewer_references_adr_cache_path():
    text = _skill_text("impl-reviewer")
    assert "adr_cache_path" in text, "impl-reviewer Phase 1 must reference adr_cache_path"
```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

In `skills/impl-reviewer/SKILL.md`, replace the entire Phase 1 block:

Old text:
```
## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it for shared context:
- `adrs_content` ← `context_bundle.adrs` (skip step 2 below)
- `context_content` ← `context_bundle.context` (skip step 3 below)

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

Before reviewing, load the following context (skip gracefully if missing —
never block review):

1. **Modified files** — read each file listed in the caller's "files changed"
   input; note "FILE NOT FOUND" if any are missing.
2. **ADRs** — read all `zie-framework/decisions/*.md`.
   If directory empty or missing → note "No ADRs found", skip ADR checks.
3. **Design context** — read `zie-framework/project/context.md` if it
   exists. If missing → note "No context doc", skip.
```

New text:
```
## Phase 1 — Load Context Bundle

**if context_bundle provided by caller** — use it for shared context:
- `context_content` ← `context_bundle.context` (skip step 3 below)
- ADR loading (in priority order):
  1. `context_bundle.adr_cache_path` present → read JSON at that path →
     use `content` field as `adrs_content`. If file missing or malformed →
     fall through to next option.
  2. `context_bundle.adrs` present (legacy) → use directly as `adrs_content`.
  3. Neither present → proceed to step 2 below (disk fallback).

**If `context_bundle` absent** — read from disk as fallback (backward-compatible):

Before reviewing, load the following context (skip gracefully if missing —
never block review):

1. **Modified files** — read each file listed in the caller's "files changed"
   input; note "FILE NOT FOUND" if any are missing.
2. **ADRs** — load via session cache (cache-first):
   a. Call `get_cached_adrs(session_id, "zie-framework/decisions/")`.
      - Cache hit → use returned string as `adrs_content`. Skip individual file reads.
      - Cache miss or `None` returned → read all `zie-framework/decisions/*.md` files,
        concatenate into `adrs_content`, then call
        `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`.
   b. If `decisions/` directory is empty or missing → `adrs_content = "No ADRs found"`;
      skip ADR checks. (Existing behavior preserved.)
   `session_id` is available from the Claude Code session context.
3. **Design context** — read `zie-framework/project/context.md` if it
   exists. If missing → note "No context doc", skip.
```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm all three priority options in context_bundle block are unambiguous.
  - Run: `make test-unit` — still PASS

---

## Task 5: Update `commands/zie-implement.md` — pass `adr_cache_path` in context bundle

<!-- depends_on: Task 4 -->

**Acceptance Criteria:**
- Context Bundle section reads ADR directory once and writes cache at task-loop start.
- `context_bundle` passed to `impl-reviewer` contains `adr_cache_path` (path string) instead of full `adrs_content` text.
- Existing `context_content` field in context bundle is unchanged.
- If `write_adr_cache` fails (returns `False`) → fall back to passing full `adrs_content` text in `context_bundle.adrs` (legacy path — no regression).

**Files:**
- Modify: `commands/zie-implement.md`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_zie_implement_context_bundle.py
"""Structural test: zie-implement must use adr_cache_path in context bundle."""
from pathlib import Path

ZIE_IMPLEMENT = Path(__file__).parents[2] / "commands" / "zie-implement.md"


def test_context_bundle_references_adr_cache_path():
    text = ZIE_IMPLEMENT.read_text()
    assert "adr_cache_path" in text, (
        "zie-implement Context Bundle must pass adr_cache_path to impl-reviewer"
    )


def test_context_bundle_references_write_adr_cache():
    text = ZIE_IMPLEMENT.read_text()
    assert "write_adr_cache" in text, (
        "zie-implement Context Bundle must call write_adr_cache at task-loop start"
    )
```

  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

In `commands/zie-implement.md`, replace the Context Bundle section:

Old text:
```
## Context Bundle

<!-- context-load: adrs + project context -->

Load once before the task loop:
1. Read `zie-framework/decisions/*.md` → `adrs_content`
2. Read `zie-framework/project/context.md` → `context_content`

Pass `context_bundle` to every impl-reviewer call.
```

New text:
```
## Context Bundle

<!-- context-load: adrs + project context -->

Load once before the task loop:
1. Read all `zie-framework/decisions/*.md` → concatenate → `adrs_content`
2. Call `write_adr_cache(session_id, adrs_content, "zie-framework/decisions/")`:
   - Returns `True` → store returned cache path as `adr_cache_path`
     (`<tempfile.gettempdir()>/zie-<session_id>/adr-cache.json`)
   - Returns `False` → set `adr_cache_path = None` (will fall back to legacy path)
3. Read `zie-framework/project/context.md` → `context_content`

Pass `context_bundle` to every impl-reviewer call:
- `context_bundle.adr_cache_path` = `adr_cache_path` (if not None)
- `context_bundle.adrs` = `adrs_content` (only when `adr_cache_path` is None — fallback)
- `context_bundle.context` = `context_content`
```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  - Confirm fallback path comment is clear: legacy `adrs` field is only populated when cache write failed.
  - Run: `make test-unit` — still PASS
