---
approved: false
approved_at:
backlog: backlog/roadmap-done-compaction.md
spec: specs/2026-03-29-roadmap-done-compaction-design.md
---

# ROADMAP Done Section Auto-Compaction — Implementation Plan

**Goal:** Add `compact_roadmap_done()` to `hooks/utils.py` and wire it into the `zie-framework:retro-format` skill so the Done section auto-archives entries older than 6 months when entry count exceeds 20.
**Architecture:** A single pure utility function `compact_roadmap_done(roadmap_path, threshold=20, cutoff_months=6)` is added to `hooks/utils.py`; it reads the Done section, decides whether to compact, writes the archive file, rewrites ROADMAP.md, and returns a result tuple. The `retro-format` skill gains one new step that calls this function after the ROADMAP Done update and logs the result. No new modules, no new hooks — additive changes only.
**Tech Stack:** Python 3.x (`re`, `datetime`, `pathlib`), Markdown (ROADMAP.md + archive files), pytest

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `hooks/utils.py` | Add `compact_roadmap_done()` function |
| Modify | `skills/retro-format/SKILL.md` | Add compaction invocation step after ROADMAP Done update |
| Create | `tests/unit/test_compact_roadmap_done.py` | Unit tests for `compact_roadmap_done()` |
| Create | `zie-framework/archive/` | Directory for archived ROADMAP entries (created at runtime by the function) |

---

## Batch 1 — Independent (Tasks 1–2 parallel)

## Task 1: Unit tests for `compact_roadmap_done()`
<!-- depends_on: none -->

**Acceptance Criteria:**
- Tests cover: no compaction when count <= 20, no compaction when no entries older than 6 months, compaction triggers at count > 20 with old entries, archive file created with correct content, summary line format matches spec, already-archived `[archive]` lines preserved, malformed-date entries skipped safely, idempotency (second call on already-compacted ROADMAP is a no-op), return tuple format `(bool, int, str)`
- All tests use `tmp_path` fixture — no real ROADMAP.md touched
- `make test-unit` collects and fails (function not yet implemented)

**Files:**
- Create: `tests/unit/test_compact_roadmap_done.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_compact_roadmap_done.py
"""Unit tests for hooks/utils.py::compact_roadmap_done."""
import sys
from pathlib import Path
from datetime import date, timedelta

import pytest

REPO_ROOT = Path(__file__).parents[2]
sys.path.insert(0, str(REPO_ROOT / "hooks"))

from utils import compact_roadmap_done


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _date_str(months_ago: int) -> str:
    """Return an ISO date string N months in the past."""
    today = date.today()
    # Approximate: 30 days per month is fine for tests
    d = today - timedelta(days=months_ago * 30)
    return d.strftime("%Y-%m-%d")


def _make_roadmap(tmp_path: Path, done_entries: list[str]) -> Path:
    """Write a minimal ROADMAP.md with the given Done entries."""
    lines = ["# ROADMAP\n", "\n", "## Done\n", "\n"]
    for entry in done_entries:
        lines.append(entry + "\n")
    lines += ["\n", "## Icebox\n"]
    p = tmp_path / "ROADMAP.md"
    p.write_text("".join(lines))
    return p


# ---------------------------------------------------------------------------
# No-compaction cases
# ---------------------------------------------------------------------------

class TestNoCompaction:
    def test_count_exactly_20_no_compaction(self, tmp_path):
        """Exactly 20 entries — threshold is >20, so no compaction."""
        entries = [
            f"- [x] feature-{i} — v1.{i}.0 {_date_str(8)}"
            for i in range(20)
        ]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_count_below_20_no_compaction(self, tmp_path):
        """10 entries — no compaction regardless of age."""
        entries = [
            f"- [x] feature-{i} — v1.{i}.0 {_date_str(8)}"
            for i in range(10)
        ]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_count_above_20_but_all_recent_no_compaction(self, tmp_path):
        """21 entries but all within 6 months — no compaction."""
        entries = [
            f"- [x] feature-{i} — v1.{i}.0 {_date_str(1)}"
            for i in range(21)
        ]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(str(p))
        assert result == (False, 0, "")

    def test_missing_file_no_compaction(self, tmp_path):
        """Missing ROADMAP.md returns (False, 0, '')."""
        result = compact_roadmap_done(str(tmp_path / "nonexistent.md"))
        assert result == (False, 0, "")


# ---------------------------------------------------------------------------
# Compaction triggers
# ---------------------------------------------------------------------------

class TestCompactionTriggers:
    def test_21_entries_with_old_ones_triggers(self, tmp_path):
        """21 entries, some older than 6 months — compaction triggered."""
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        p = _make_roadmap(tmp_path, old + recent)
        was_compacted, old_count, version_range = compact_roadmap_done(str(p))
        assert was_compacted is True
        assert old_count == 5
        assert version_range != ""

    def test_return_tuple_types(self, tmp_path):
        """Return value is (bool, int, str)."""
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        p = _make_roadmap(tmp_path, old + recent)
        result = compact_roadmap_done(str(p))
        assert isinstance(result[0], bool)
        assert isinstance(result[1], int)
        assert isinstance(result[2], str)


# ---------------------------------------------------------------------------
# Archive file creation
# ---------------------------------------------------------------------------

class TestArchiveFile:
    def test_archive_file_created(self, tmp_path):
        """After compaction, an archive file exists under zie-framework/archive/."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(5)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(16)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        archive_dir = zie_dir / "archive"
        assert archive_dir.exists()
        archive_files = list(archive_dir.glob("ROADMAP-*.md"))
        assert len(archive_files) == 1

    def test_archive_file_contains_old_entries(self, tmp_path):
        """Archive file contains the original text of compacted entries."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] special-old-feature — v1.0.0 {_date_str(8)}"]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(20)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        archive_files = list((zie_dir / "archive").glob("ROADMAP-*.md"))
        content = archive_files[0].read_text()
        assert "special-old-feature" in content


# ---------------------------------------------------------------------------
# ROADMAP.md rewrite
# ---------------------------------------------------------------------------

class TestRoadmapRewrite:
    def test_old_entries_replaced_with_summary_line(self, tmp_path):
        """Old entries are replaced by a single [archive] summary line."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        assert "[archive]" in content
        assert "old-0" not in content
        assert "old-1" not in content
        assert "old-2" not in content

    def test_recent_entries_preserved(self, tmp_path):
        """Recent entries are untouched after compaction."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] keep-this-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        for i in range(18):
            assert f"keep-this-{i}" in content

    def test_summary_line_format(self, tmp_path):
        """Summary line matches: - [archive] <range> (<dates>): N features shipped — see <path>"""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        import re
        assert re.search(r"\[archive\].*features shipped.*see", content)

    def test_existing_archive_lines_preserved(self, tmp_path):
        """Pre-existing [archive] lines are preserved as-is."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        existing_archive = "- [archive] v1.0–v1.2 (2025-01 to 2025-03): 10 features shipped — see zie-framework/archive/ROADMAP-v1.0-v1.2.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            existing_archive + "\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        content = roadmap.read_text()
        assert existing_archive in content


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_malformed_date_entry_skipped_safely(self, tmp_path):
        """Entry with unparseable date is preserved, not crashed on."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        malformed = "- [x] mystery feature — v1.0.0 not-a-date"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            malformed + "\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        # Must not raise
        result = compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_idempotent_second_call_noop(self, tmp_path):
        """Second call on already-compacted ROADMAP returns (False, 0, '')."""
        zie_dir = tmp_path / "zie-framework"
        zie_dir.mkdir()
        roadmap = zie_dir.parent / "ROADMAP.md"
        old = [f"- [x] old-{i} — v1.{i}.0 {_date_str(8)}" for i in range(3)]
        recent = [f"- [x] new-{i} — v1.{i}.0 {_date_str(1)}" for i in range(18)]
        roadmap.write_text(
            "# ROADMAP\n\n## Done\n\n" +
            "\n".join(old + recent) +
            "\n\n## Icebox\n"
        )
        compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        result2 = compact_roadmap_done(str(roadmap), archive_base=str(zie_dir / "archive"))
        assert result2 == (False, 0, "")

    def test_accepts_path_object(self, tmp_path):
        """compact_roadmap_done accepts a Path object, not just str."""
        entries = [f"- [x] feature-{i} — v1.{i}.0 {_date_str(1)}" for i in range(5)]
        p = _make_roadmap(tmp_path, entries)
        result = compact_roadmap_done(p)
        assert result == (False, 0, "")
```

Run: `make test-unit` — must FAIL (`compact_roadmap_done` does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

No implementation in this task — tests must fail to establish RED baseline.

Run: `make test-unit` — must still FAIL (confirms RED)

- [ ] **Step 3: Refactor**

No refactor needed in RED step. Move to Task 2.

Run: `make test-unit` — still FAIL (expected)

---

## Task 2: Implement `compact_roadmap_done()` in `hooks/utils.py`
<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `compact_roadmap_done(roadmap_path, threshold=20, cutoff_months=6, archive_base=None)` added to `hooks/utils.py`
- Returns `(False, 0, "")` when count <= threshold or no entries older than cutoff
- When triggered: creates archive file, rewrites ROADMAP.md Done section, returns `(True, N, version_range_str)`
- Archive file path: `<archive_base>/ROADMAP-<slug>.md` where slug is derived from version range or date range
- `archive_base` defaults to `<roadmap_path.parent>/zie-framework/archive` when not provided
- Existing `[archive]` lines in Done section are preserved as-is
- Malformed-date entries are skipped (not archived, not crashed on), logged to stderr
- Uses `atomic_write()` from utils for all file writes
- All tests in `test_compact_roadmap_done.py` pass

**Files:**
- Modify: `hooks/utils.py`

- [ ] **Step 1: Write failing tests (RED)**

Tests already written in Task 1. Confirm they still fail:

Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**

Add to `hooks/utils.py` (after the `parse_roadmap_section_content` function):

```python
def compact_roadmap_done(
    roadmap_path,
    threshold: int = 20,
    cutoff_months: int = 6,
    archive_base: str | None = None,
) -> tuple:
    """Compact the Done section of ROADMAP.md by archiving old entries.

    Reads the Done section, counts non-archive entries. If count > threshold
    and some entries are older than cutoff_months, archives those entries to
    a Markdown file under archive_base and replaces them with a single summary
    line.

    Returns:
        (was_compacted: bool, old_entry_count: int, version_range: str)
        On no-op: (False, 0, "")

    archive_base defaults to <roadmap parent>/zie-framework/archive when None.
    Accepts str or Path for roadmap_path.
    """
    import datetime as _dt

    path = Path(roadmap_path)
    if not path.exists():
        return (False, 0, "")

    raw = path.read_text()
    lines = raw.splitlines(keepends=True)

    # ------------------------------------------------------------------ #
    # 1. Extract Done section boundaries
    # ------------------------------------------------------------------ #
    done_start = None  # index of line AFTER "## Done" header
    done_end = None    # index of first line AFTER Done section

    for idx, line in enumerate(lines):
        if line.startswith("##") and "done" in line.lower() and done_start is None:
            done_start = idx + 1
            continue
        if line.startswith("##") and done_start is not None and done_end is None:
            done_end = idx
            break

    if done_start is None:
        return (False, 0, "")
    if done_end is None:
        done_end = len(lines)

    done_lines = lines[done_start:done_end]

    # ------------------------------------------------------------------ #
    # 2. Separate entry types
    # ------------------------------------------------------------------ #
    _ARCHIVE_RE = re.compile(r"^\s*-\s+\[archive\]", re.IGNORECASE)
    _ENTRY_RE = re.compile(r"^\s*-\s+\[")
    _DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")

    existing_archive_lines = []
    normal_entries = []  # (line_str, parsed_date_or_None)

    for line in done_lines:
        stripped = line.rstrip("\n")
        if not stripped.strip():
            continue
        if _ARCHIVE_RE.match(stripped):
            existing_archive_lines.append(stripped)
            continue
        if _ENTRY_RE.match(stripped):
            m = _DATE_RE.search(stripped)
            if m:
                try:
                    parsed = _dt.date.fromisoformat(m.group(1))
                    normal_entries.append((stripped, parsed))
                except ValueError:
                    print(
                        f"[zie-framework] compact_roadmap_done: skipping entry with malformed date: {stripped!r}",
                        file=sys.stderr,
                    )
                    normal_entries.append((stripped, None))
            else:
                normal_entries.append((stripped, None))

    total_parseable = len(normal_entries)
    if total_parseable <= threshold:
        return (False, 0, "")

    # ------------------------------------------------------------------ #
    # 3. Identify old entries (older than cutoff_months)
    # ------------------------------------------------------------------ #
    today = _dt.date.today()
    cutoff = today - _dt.timedelta(days=cutoff_months * 30)

    old_entries = [
        (line, d) for line, d in normal_entries
        if d is not None and d < cutoff
    ]

    if not old_entries:
        return (False, 0, "")

    # ------------------------------------------------------------------ #
    # 4. Derive version range for archive file name + summary line
    # ------------------------------------------------------------------ #
    _VERSION_RE = re.compile(r"v(\d+\.\d+(?:\.\d+)?)")
    versions = []
    dates_found = []
    for line, d in old_entries:
        vm = _VERSION_RE.search(line)
        if vm:
            versions.append(vm.group(0))
        if d:
            dates_found.append(d)

    if versions:
        v_start = versions[-1]   # oldest entry listed last
        v_end = versions[0]      # newest of old entries listed first
        version_range = f"{v_start}-{v_end}"
        label = f"{v_start}–{v_end}"
    else:
        version_range = "unknown"
        label = "unknown"

    if dates_found:
        d_start = min(dates_found).strftime("%Y-%m")
        d_end = max(dates_found).strftime("%Y-%m")
        date_range_label = f"{d_start} to {d_end}"
    else:
        date_range_label = "unknown"

    n_old = len(old_entries)

    # ------------------------------------------------------------------ #
    # 5. Resolve archive_base
    # ------------------------------------------------------------------ #
    if archive_base is None:
        # Default: roadmap_path is typically inside project root;
        # archive lives at zie-framework/archive/ relative to roadmap's dir
        archive_dir = path.parent / "zie-framework" / "archive"
    else:
        archive_dir = Path(archive_base)

    archive_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # 6. Write archive file
    # ------------------------------------------------------------------ #
    safe_range = re.sub(r"[^a-zA-Z0-9._-]", "-", version_range)
    archive_filename = f"ROADMAP-{safe_range}.md"
    archive_path = archive_dir / archive_filename

    archive_content = (
        f"# ROADMAP Archive — {label} ({date_range_label})\n\n"
        f"Archived by compact_roadmap_done on {today.isoformat()}.\n"
        f"{n_old} entries older than {cutoff_months} months.\n\n"
        + "\n".join(line for line, _ in old_entries)
        + "\n"
    )
    atomic_write(archive_path, archive_content)

    # ------------------------------------------------------------------ #
    # 7. Build summary line
    # ------------------------------------------------------------------ #
    archive_rel = str(archive_path).replace(str(path.parent) + "/", "")
    summary_line = (
        f"- [archive] {label} ({date_range_label}): "
        f"{n_old} features shipped — see {archive_rel}"
    )

    # ------------------------------------------------------------------ #
    # 8. Rebuild Done section
    # ------------------------------------------------------------------ #
    old_entry_lines = {line for line, _ in old_entries}
    kept_normal = [
        line for line, d in normal_entries
        if line not in old_entry_lines
    ]

    new_done_lines = (
        [summary_line + "\n"]
        + [l + "\n" for l in existing_archive_lines]
        + [l + "\n" for l in kept_normal]
    )

    new_lines = (
        lines[:done_start]
        + ["\n"]
        + new_done_lines
        + ["\n"]
        + lines[done_end:]
    )

    atomic_write(path, "".join(new_lines))

    return (True, n_old, version_range)
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Review:
- Confirm all compiled regex (`_ARCHIVE_RE`, `_ENTRY_RE`, `_DATE_RE`, `_VERSION_RE`) are defined inside the function (they are local helpers; moving them to module level would pollute the global namespace with test-only patterns — keep local).
- Confirm `import datetime as _dt` is local import inside function to avoid name collision with module-level imports.
- Verify `atomic_write` is called for both the archive file and the ROADMAP rewrite — no bare `open()` writes.
- Confirm stderr log prefix matches `[zie-framework] <function-name>:` convention (ADR-019).

Run: `make test-unit` — still PASS

---

## Batch 2 — Depends on Task 2

## Task 3: Wire compaction into `retro-format` skill
<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `skills/retro-format/SKILL.md` gains a new "## Compaction Check" step after the "Checklist อัปเดต ROADMAP" section
- Step instructs the retro-format agent to call `compact_roadmap_done()` from `hooks/utils.py` with the ROADMAP path and log the result
- Log output matches spec: "Compacted X old entries (vA–vB) into archive. Keep 20 recent entries in ROADMAP." or "Done section has only recent entries, no archival needed"
- Step is guarded: if ROADMAP path cannot be resolved, skip with a warning (do not block retro)
- `make test-unit` passes (test verifies the skill contains the compaction step wording)

**Files:**
- Modify: `skills/retro-format/SKILL.md`
- Create: `tests/unit/test_retro_format_skill.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_retro_format_skill.py
"""Verify retro-format skill contains the compaction step."""
from pathlib import Path

SKILL_PATH = Path(__file__).parents[2] / "skills" / "retro-format" / "SKILL.md"


def test_skill_contains_compaction_step():
    """retro-format skill must reference compact_roadmap_done."""
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert "compact_roadmap_done" in content, (
        "retro-format/SKILL.md must call compact_roadmap_done after ROADMAP update"
    )


def test_skill_contains_compaction_log_messages():
    """retro-format skill must document both log message variants."""
    content = SKILL_PATH.read_text(encoding="utf-8")
    assert "no archival needed" in content, (
        "retro-format/SKILL.md must include 'no archival needed' message variant"
    )
    assert "features shipped" in content, (
        "retro-format/SKILL.md must include 'features shipped' message variant"
    )


def test_skill_contains_guard_for_missing_roadmap():
    """retro-format skill must guard against missing ROADMAP path."""
    content = SKILL_PATH.read_text(encoding="utf-8")
    # Any mention of skip/guard/missing for the compaction step
    assert any(word in content for word in ("skip", "missing", "not found", "cannot")), (
        "retro-format/SKILL.md compaction step must guard against missing ROADMAP"
    )
```

Run: `make test-unit` — must FAIL (skill does not yet reference `compact_roadmap_done`)

- [ ] **Step 2: Implement (GREEN)**

Append to `skills/retro-format/SKILL.md` after the "Checklist อัปเดต ROADMAP" section:

```markdown
## Compaction Check

After updating the ROADMAP Done section, run compaction:

```python
import sys
from pathlib import Path

# Resolve ROADMAP path — typically zie-framework/ROADMAP.md relative to project root
roadmap_path = Path("zie-framework/ROADMAP.md")
if not roadmap_path.exists():
    print("[zie-framework] retro-format: ROADMAP.md not found, skipping compaction", file=sys.stderr)
else:
    sys.path.insert(0, str(Path("hooks")))
    from utils import compact_roadmap_done
    was_compacted, old_count, version_range = compact_roadmap_done(str(roadmap_path))
    if was_compacted:
        print(f"Compacted {old_count} old entries ({version_range.replace('-', '–')}) into archive. Keep 20 recent entries in ROADMAP.")
    else:
        print("Done section has only recent entries, no archival needed")
```
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

- Verify the Compaction Check section is placed after "Checklist อัปเดต ROADMAP" and before any closing content.
- Confirm the print messages match spec wording exactly (including "features shipped" phrasing — adjust if needed to match test assertions).
- Re-read the full SKILL.md to ensure no unintended formatting issues (no broken fenced code blocks).

Run: `make test-unit` — still PASS

---

## Task 4: ADR + final verification
<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `zie-framework/decisions/ADR-026-roadmap-done-compaction.md` created documenting this architectural decision
- Full `make test-unit` run passes with no regressions
- `compact_roadmap_done` is importable from `hooks/utils.py` in a fresh Python session
- Archive directory is created at runtime (not pre-committed)

**Files:**
- Create: `zie-framework/decisions/ADR-026-roadmap-done-compaction.md`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_adr_026_exists.py
"""Verify ADR-026 exists for the roadmap-done-compaction decision."""
from pathlib import Path

DECISIONS_DIR = Path(__file__).parents[2] / "zie-framework" / "decisions"


def test_adr_026_file_exists():
    """ADR-026 file must exist in decisions/."""
    matches = list(DECISIONS_DIR.glob("ADR-026-*.md"))
    assert matches, "ADR-026-roadmap-done-compaction.md must exist in zie-framework/decisions/"


def test_adr_026_has_required_sections():
    """ADR-026 must have Context, Decision, and Consequences sections."""
    matches = list(DECISIONS_DIR.glob("ADR-026-*.md"))
    assert matches, "ADR-026 not found"
    content = matches[0].read_text(encoding="utf-8")
    assert "## Context" in content
    assert "## Decision" in content
    assert "## Consequences" in content


def test_compact_roadmap_done_importable():
    """compact_roadmap_done must be importable from hooks/utils.py."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parents[2] / "hooks"))
    from utils import compact_roadmap_done
    assert callable(compact_roadmap_done)
```

Run: `make test-unit` — must FAIL (ADR-026 does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

Create `zie-framework/decisions/ADR-026-roadmap-done-compaction.md`:

```markdown
# ADR-026: ROADMAP Done Section Auto-Compaction

Date: 2026-03-29
Status: Accepted

## Context

ROADMAP.md Done section grows ~2 entries per release. At 36 entries today,
it will reach 150+ entries within 6 months, making the file unwieldy for
manual review. The existing 20-line read limit in `/zie-retro` mitigates
context impact today but could drift if the limit is removed or relaxed.
A self-managing state file aligns with the zie-framework principle that
SDLC artifacts stay readable as the project ages.

## Decision

Add `compact_roadmap_done()` to `hooks/utils.py`. When invoked by the
`retro-format` skill after every ROADMAP Done update: if entry count > 20
and some entries are older than 6 months, compact those old entries into a
single `[archive]` summary line and write their detail to
`zie-framework/archive/ROADMAP-<version-range>.md`. The 20 most-recent
entries always remain in full detail. Threshold and cutoff are hardcoded
(not config) per YAGNI.

## Consequences

**Positive:** Done section stays at ≤ 20 full-detail entries automatically.
Archive files preserve full history. No manual cleanup required.
**Negative:** Old entries are no longer visible in ROADMAP.md directly;
reviewer must follow the archive link.
**Neutral:** Threshold (20) and cutoff (6 months) are hardcoded. Future
parameterization possible via zie-framework/.config (separate backlog item).
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Run full suite:

```bash
make test-unit
```

Expected: all tests pass including `test_compact_roadmap_done.py`,
`test_retro_format_skill.py`, `test_adr_026_exists.py`.

Confirm `compact_roadmap_done` is exported (importable from `utils` with no star-import
needed — direct `from utils import compact_roadmap_done` works).

Run: `make test-unit` — still PASS
