---
slug: audit-knowledge-hash-mtime-gate
status: approved
approved: true
date: 2026-04-01
---

# Implementation Plan: Knowledge Hash mtime Gate

## Overview

Add an mtime gate to `sync_knowledge` in `hooks/session-resume.py` to skip the
expensive `rglob` + SHA-256 loop when no `.md` file has changed since the hash
was last written. Two pure helper functions added to `hooks/utils.py`.

**Spec:** `zie-framework/specs/2026-04-01-audit-knowledge-hash-mtime-gate-design.md`

---

## Acceptance Criteria

| ID | Criterion |
|----|----------|
| AC-1 | `compute_max_mtime` returns `0.0` when no `.md` files exist |
| AC-2 | `compute_max_mtime` returns the max mtime across all `.md` files |
| AC-3 | `is_mtime_fresh(t, t)` → `True`; `is_mtime_fresh(t+1, t)` → `False` |
| AC-4 | `sync_knowledge` skips hash recomputation when mtime gate passes |
| AC-5 | `sync_knowledge` runs full hash loop when any `.md` file is newer |
| AC-6 | `sync_knowledge` runs full hash loop on first run (no stored hash) |
| AC-7 | Cache-hit emits log line containing `"mtime gate"` |

---

## Task List

### Task 1 — Add helpers to `hooks/utils.py`

**Where to insert:** After the `run_auto_test` function, before end of file.

```python
# ---------------------------------------------------------------------------
# mtime gate helpers
# ---------------------------------------------------------------------------

def compute_max_mtime(base_dir: Path, pattern: str = "**/*.md") -> float:
    """Return max mtime (float) of files matching pattern under base_dir.
    Returns 0.0 if no files match."""
    mtimes = [p.stat().st_mtime for p in base_dir.rglob(pattern.lstrip("**/"))]
    return max(mtimes) if mtimes else 0.0


def is_mtime_fresh(max_mtime: float, written_at: float) -> bool:
    """Return True if max_mtime <= written_at (no file newer than last write)."""
    return max_mtime <= written_at
```

### Task 2 — Update `sync_knowledge` in `hooks/session-resume.py`

#### 2a. Extend the import block

```python
from utils import (
    load_config,
    load_hook_input,
    log_failure_context,
    run_auto_test,
    compute_max_mtime,
    is_mtime_fresh,
)
```

#### 2b. Replace `sync_knowledge` body

**Before:**
```python
def sync_knowledge(base_dir: Path, hash_file: Path) -> None:
    """Recompute and persist the knowledge hash if files changed."""
    stored = load_hash_record(hash_file)
    new_hash = compute_hash(base_dir)
    if stored and stored.get("hash") == new_hash:
        print("[zie-framework] session-resume: knowledge hash unchanged")
        return
    write_hash_record(hash_file, new_hash)
    if stored:
        print("[zie-framework] session-resume: knowledge hash updated")
    else:
        print("[zie-framework] session-resume: knowledge hash initialised")
```

**After:**
```python
def sync_knowledge(base_dir: Path, hash_file: Path) -> None:
    """Recompute and persist the knowledge hash if files changed."""
    stored = load_hash_record(hash_file)

    # mtime gate: skip expensive rglob+hash when no .md file has changed
    if stored:
        max_mtime = compute_max_mtime(base_dir)
        if is_mtime_fresh(max_mtime, stored["written_at"]):
            print("[zie-framework] session-resume: knowledge hash cache hit (mtime gate)")
            return

    new_hash = compute_hash(base_dir)
    if stored and stored.get("hash") == new_hash:
        print("[zie-framework] session-resume: knowledge hash unchanged")
        return
    write_hash_record(hash_file, new_hash)
    if stored:
        print("[zie-framework] session-resume: knowledge hash updated")
    else:
        print("[zie-framework] session-resume: knowledge hash initialised")
```

---

## TDD Steps

### RED Phase

Add to `tests/unit/test_utils.py`:

```python
from hooks.utils import compute_max_mtime, is_mtime_fresh

class TestComputeMaxMtime:
    def test_returns_zero_when_no_md_files(self, tmp_path):
        assert compute_max_mtime(tmp_path) == 0.0

    def test_returns_mtime_of_single_file(self, tmp_path):
        f = tmp_path / "a.md"
        f.write_text("hello")
        result = compute_max_mtime(tmp_path)
        assert result == pytest.approx(f.stat().st_mtime)

    def test_returns_max_mtime_across_files(self, tmp_path):
        import time
        f1 = tmp_path / "old.md"
        f1.write_text("old")
        time.sleep(0.01)
        f2 = tmp_path / "new.md"
        f2.write_text("new")
        result = compute_max_mtime(tmp_path)
        assert result == pytest.approx(f2.stat().st_mtime)

    def test_ignores_non_md_files(self, tmp_path):
        (tmp_path / "skip.txt").write_text("x")
        assert compute_max_mtime(tmp_path) == 0.0


class TestIsMtimeFresh:
    def test_equal_timestamps_returns_true(self):
        assert is_mtime_fresh(1000.0, 1000.0) is True

    def test_older_mtime_returns_true(self):
        assert is_mtime_fresh(999.0, 1000.0) is True

    def test_newer_mtime_returns_false(self):
        assert is_mtime_fresh(1001.0, 1000.0) is False
```

Add to `tests/unit/test_session_resume.py`:

```python
class TestMtimeGateInSyncKnowledge:
    def test_cache_hit_skips_hash_recomputation(self, sr, tmp_path, capsys, monkeypatch):
        """AC-4 and AC-7."""
        md = tmp_path / "a.md"
        md.write_text("hello")
        hf = tmp_path / "knowledge.hash"
        sr.sync_knowledge(tmp_path, hf)
        capsys.readouterr()

        called = []
        original = sr.compute_hash
        monkeypatch.setattr(sr, "compute_hash", lambda d: called.append(1) or original(d))

        sr.sync_knowledge(tmp_path, hf)
        out = capsys.readouterr().out
        assert "mtime gate" in out
        assert len(called) == 0  # AC-4

    def test_cache_miss_runs_full_hash(self, sr, tmp_path, capsys, monkeypatch):
        """AC-5."""
        md = tmp_path / "a.md"
        md.write_text("hello")
        hf = tmp_path / "knowledge.hash"
        sr.sync_knowledge(tmp_path, hf)
        capsys.readouterr()

        import json
        rec = json.loads(hf.read_text())
        rec["written_at"] = rec["written_at"] - 10.0
        hf.write_text(json.dumps(rec))

        called = []
        original = sr.compute_hash
        monkeypatch.setattr(sr, "compute_hash", lambda d: called.append(1) or original(d))

        sr.sync_knowledge(tmp_path, hf)
        assert len(called) == 1  # AC-5

    def test_first_run_runs_full_loop(self, sr, tmp_path, capsys, monkeypatch):
        """AC-6."""
        md = tmp_path / "a.md"
        md.write_text("hello")
        hf = tmp_path / "knowledge.hash"

        called = []
        original = sr.compute_hash
        monkeypatch.setattr(sr, "compute_hash", lambda d: called.append(1) or original(d))

        sr.sync_knowledge(tmp_path, hf)
        assert len(called) == 1  # AC-6
        assert "initialised" in capsys.readouterr().out
```

Run `make test-unit` — RED confirmed.

### GREEN Phase

1. Implement Task 1 (append helpers to `hooks/utils.py`).
2. Run `make test-unit` — `TestComputeMaxMtime` and `TestIsMtimeFresh` pass.
3. Implement Task 2 (update imports + `sync_knowledge`).
4. Run `make test-unit` — full GREEN.

### REFACTOR Phase

No structural refactor needed. Run `make test-ci` for full regression check.

---

## Test Strategy

| Layer | Location | What it tests |
|-------|----------|---------------|
| Unit | `test_utils.py::TestComputeMaxMtime` | AC-1, AC-2 |
| Unit | `test_utils.py::TestIsMtimeFresh` | AC-3 |
| Unit | `test_session_resume.py::TestMtimeGateInSyncKnowledge` | AC-4, AC-5, AC-6, AC-7 |

---

## Rollout

1. Write failing tests — RED via `make test-unit`.
2. Add helpers to `hooks/utils.py` — partial GREEN.
3. Update `sync_knowledge` in `hooks/session-resume.py` — full GREEN.
4. Run `make test-ci` — confirm no regression.
5. Mark backlog item done in ROADMAP.md.
