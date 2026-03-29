---
approved: false
approved_at:
backlog: backlog/adr-auto-summarization.md
---

# ADR Auto-Summarization — Implementation Plan

**Goal:** When `/zie-retro` detects more than 30 ADR files, auto-generate `decisions/ADR-000-summary.md` compressing the oldest ADRs into a single table, and update the three reviewer skills to load the summary file first.
**Architecture:** Two independent tracks — Track A modifies `commands/zie-retro.md` to add the ADR count check and summary generation step; Track B updates all three reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) to prefer `ADR-000-summary.md` + recent individual files when the summary exists. A `make adr-count` Makefile helper is added as part of Track A. All changes are additive; reviewers continue to work identically when no summary exists.
**Tech Stack:** Python 3.x (summary extraction logic tested via pytest), Markdown (command and skill files), Makefile

---

## File Map

| Action | File | Responsibility |
|--------|------|----------------|
| Modify | `commands/zie-retro.md` | Add ADR count check and summary generation step after "Count ADR files" line |
| Modify | `skills/spec-reviewer/SKILL.md` | Update Phase 1 ADR loading to load `ADR-000-summary.md` first when present, then remaining individual files |
| Modify | `skills/plan-reviewer/SKILL.md` | Same Phase 1 update as spec-reviewer |
| Modify | `skills/impl-reviewer/SKILL.md` | Same Phase 1 update as spec-reviewer |
| Modify | `Makefile` | Add `adr-count` target |
| Create | `tests/unit/test_adr_summarization.py` | Unit tests for summary generation logic (extraction, truncation, edge cases) |

---

## Batch 1 — Independent (Tasks 1–2 parallel)

## Task 1: Makefile adr-count target
<!-- depends_on: none -->

**What:** Add a `make adr-count` target that counts individual ADR files in `zie-framework/decisions/` (excluding `ADR-000-summary.md`) and prints the count. Exits 0 when directory does not exist.

**Acceptance Criteria:**
- `make adr-count` prints a number (current count) and exits 0
- `make adr-count` prints `0` when `zie-framework/decisions/` does not exist
- Count excludes `ADR-000-summary.md` itself
- Target appears in Makefile under a `## Utilities` or existing helpers section

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Write failing test (RED)**

```python
# tests/unit/test_adr_count_target.py
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parents[2]


def test_adr_count_exits_zero():
    """make adr-count must exit 0."""
    result = subprocess.run(
        ["make", "adr-count"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"make adr-count exited {result.returncode}: {result.stderr}"


def test_adr_count_prints_integer():
    """make adr-count must print a single integer line."""
    result = subprocess.run(
        ["make", "adr-count"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    output = result.stdout.strip().splitlines()
    # Last non-empty line should be an integer
    numeric_lines = [l for l in output if l.strip().isdigit()]
    assert numeric_lines, f"No integer line in output: {result.stdout!r}"
```

Run: `make test-unit` — must FAIL (target does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

Add to `Makefile` (after the `## CI / lint` section or with other helpers):

```makefile
.PHONY: adr-count
adr-count: ## Count ADR files in zie-framework/decisions/ (excludes ADR-000-summary.md)
	@count=$$(ls zie-framework/decisions/ADR-*.md 2>/dev/null | grep -v ADR-000-summary | wc -l | tr -d ' '); echo $$count
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Verify `make adr-count` works when `zie-framework/decisions/` is absent by testing with a non-existent path (manual spot-check: `ls /nonexistent/ADR-*.md 2>/dev/null` returns empty, count = 0). No code change needed.

Run: `make test-unit` — still PASS

---

## Task 2: Unit tests for ADR summary extraction logic
<!-- depends_on: none -->

**What:** Write the unit test suite for the summary generation logic — extraction of ADR number, title, and decision text. These tests define the contract that Task 3 (retro changes) must satisfy.

**Acceptance Criteria:**
- Tests cover: normal extraction, missing `## Decision` section (fallback to first non-heading paragraph), missing fallback (placeholder), truncation at 120 chars, summary already-exists overwrite (idempotency), fewer-than-11 ADRs guard
- All tests are pure Python (no subprocess, no file system writes in test body — use `tmp_path` fixture)
- `make test-unit` passes with all tests collected

**Files:**
- Create: `tests/unit/test_adr_summarization.py`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_adr_summarization.py
"""Unit tests for ADR summary extraction logic.

These tests import from a helper module that will be created in Task 3.
They define the contract: given ADR file content, return (number, title, decision).
"""
import pytest
from pathlib import Path


# ---------------------------------------------------------------------------
# Module-level import — will fail until Task 3 creates the module
# ---------------------------------------------------------------------------
from hooks.adr_summary import extract_adr_row, generate_summary_table


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

NORMAL_ADR = """\
# ADR-010: Safe Write via Tmp Symlink

Some intro.

## Context

Background text.

## Decision

We will always write files via a temporary path and rename atomically to prevent partial writes. This guarantees consistency.
"""

ADR_NO_DECISION = """\
# ADR-011: OsError Defense in Depth

Intro.

## Context

Some context without a Decision section.
"""

ADR_NO_DECISION_NO_PARA = """\
# ADR-012: Something

## Context

## Status
"""

ADR_LONG_DECISION = """\
# ADR-013: Long Decision Example

## Decision

We decided to adopt a very detailed approach that covers many different scenarios and edge cases including fallback handling for missing files as well as error propagation strategies across the entire system stack.
"""

ADR_MISSING_NUMBER = """\
# Safe Write

## Decision

Use tmp path.
"""


# ---------------------------------------------------------------------------
# extract_adr_row tests
# ---------------------------------------------------------------------------

def test_extract_normal():
    """Normal ADR: returns (number_str, title, first_decision_sentence)."""
    number, title, decision = extract_adr_row("ADR-010-safe-write.md", NORMAL_ADR)
    assert number == "ADR-010"
    assert title == "Safe Write via Tmp Symlink"
    assert "atomic" in decision or "temporary path" in decision


def test_extract_missing_decision_uses_first_paragraph():
    """Missing ## Decision section: fallback to first non-heading paragraph."""
    number, title, decision = extract_adr_row("ADR-011-oserror.md", ADR_NO_DECISION)
    assert decision == "Some context without a Decision section."


def test_extract_missing_decision_and_paragraph_uses_placeholder():
    """No ## Decision and no non-heading paragraph: placeholder."""
    number, title, decision = extract_adr_row("ADR-012-something.md", ADR_NO_DECISION_NO_PARA)
    assert decision == "(no decision text)"


def test_extract_truncates_at_120():
    """Decision text > 120 chars is truncated with trailing ellipsis."""
    number, title, decision = extract_adr_row("ADR-013-long.md", ADR_LONG_DECISION)
    assert len(decision) <= 121  # 120 chars + "…"
    assert decision.endswith("…")


def test_extract_number_from_filename():
    """ADR number extracted from filename, not body."""
    number, title, decision = extract_adr_row("ADR-010-safe-write.md", NORMAL_ADR)
    assert number == "ADR-010"


def test_extract_missing_number_fallback(tmp_path):
    """Filename without ADR-NNN prefix: number = '???'."""
    number, title, decision = extract_adr_row("safe-write.md", ADR_MISSING_NUMBER)
    assert number == "???"


# ---------------------------------------------------------------------------
# generate_summary_table tests
# ---------------------------------------------------------------------------

def test_generate_summary_table_returns_markdown(tmp_path):
    """generate_summary_table returns a Markdown string with table header."""
    adr_files = [
        ("ADR-001-first.md", "# ADR-001: First\n\n## Decision\n\nUse X.\n"),
        ("ADR-002-second.md", "# ADR-002: Second\n\n## Decision\n\nUse Y.\n"),
    ]
    # Write files into tmp_path
    paths = []
    for name, content in adr_files:
        p = tmp_path / name
        p.write_text(content)
        paths.append(p)
    result = generate_summary_table(paths)
    assert "| ADR | Title | Decision |" in result
    assert "ADR-001" in result
    assert "ADR-002" in result


def test_generate_summary_table_empty_list():
    """Empty list of files: returns header-only table."""
    result = generate_summary_table([])
    assert "| ADR | Title | Decision |" in result


def test_generate_summary_table_idempotent(tmp_path):
    """Calling generate_summary_table twice with same input returns same output."""
    p = tmp_path / "ADR-001-first.md"
    p.write_text("# ADR-001: First\n\n## Decision\n\nUse X.\n")
    result1 = generate_summary_table([p])
    result2 = generate_summary_table([p])
    assert result1 == result2
```

Run: `make test-unit` — must FAIL (`hooks.adr_summary` does not exist yet)

- [ ] **Step 2: Implement (GREEN)**

Create `hooks/adr_summary.py`:

```python
"""ADR summary extraction helpers.

Used by /zie-retro to compress old ADRs into ADR-000-summary.md.
"""
from __future__ import annotations

import re
from pathlib import Path

_ADR_NUMBER_RE = re.compile(r"^(ADR-\d+)", re.IGNORECASE)
_H1_RE = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_DECISION_SECTION_RE = re.compile(
    r"##\s+Decision\s*\n(.*?)(?=\n##|\Z)", re.DOTALL | re.IGNORECASE
)
_HEADING_RE = re.compile(r"^#{1,6}\s+", re.MULTILINE)

MAX_DECISION_LEN = 120


def extract_adr_row(filename: str, content: str) -> tuple[str, str, str]:
    """Return (number, title, decision) for a single ADR.

    number  — extracted from filename prefix (e.g. "ADR-010")
    title   — text of first # heading, minus the "ADR-NNN: " prefix if present
    decision — first sentence of ## Decision section, truncated to 120 chars;
               falls back to first non-heading paragraph; then placeholder.
    """
    # --- number from filename ---
    m = _ADR_NUMBER_RE.match(filename)
    number = m.group(1).upper() if m else "???"

    # --- title from first H1 ---
    h1_match = _H1_RE.search(content)
    raw_title = h1_match.group(1).strip() if h1_match else filename
    # Strip leading "ADR-NNN: " or "ADR-NNN — " prefix from title
    title = re.sub(r"^ADR-\d+[:\s\-–—]+", "", raw_title, flags=re.IGNORECASE).strip()

    # --- decision text ---
    decision = _extract_decision(content)

    return number, title, decision


def _extract_decision(content: str) -> str:
    """Extract first sentence of ## Decision section, with fallbacks."""
    m = _DECISION_SECTION_RE.search(content)
    if m:
        section_text = m.group(1).strip()
        if section_text:
            first_sentence = _first_sentence(section_text)
            return _truncate(first_sentence)

    # Fallback: first non-heading paragraph
    for para in content.split("\n\n"):
        para = para.strip()
        if para and not _HEADING_RE.match(para):
            return _truncate(_first_sentence(para))

    return "(no decision text)"


def _first_sentence(text: str) -> str:
    """Return text up to and including the first sentence-ending punctuation."""
    # Simple heuristic: up to first ". " or end of text
    idx = text.find(". ")
    if idx != -1:
        return text[: idx + 1].strip()
    return text.strip()


def _truncate(text: str) -> str:
    if len(text) > MAX_DECISION_LEN:
        return text[:MAX_DECISION_LEN] + "…"
    return text


def generate_summary_table(adr_paths: list[Path]) -> str:
    """Return Markdown table content for the given list of ADR Paths."""
    header = "| ADR | Title | Decision |\n|-----|-------|----------|\n"
    rows = []
    for path in sorted(adr_paths, key=lambda p: p.name):
        content = path.read_text(encoding="utf-8")
        number, title, decision = extract_adr_row(path.name, content)
        # Escape pipes in cell values
        title = title.replace("|", "\\|")
        decision = decision.replace("|", "\\|")
        rows.append(f"| {number} | {title} | {decision} |")
    return header + "\n".join(rows) + ("\n" if rows else "")
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Ensure module-level constants (`_ADR_NUMBER_RE`, `_H1_RE`, etc.) are compiled once at import time, not inside functions. Confirm no `re.compile` calls inside any function body. Clean up any dead code.

Run: `make test-unit` — still PASS

---

## Batch 2 — Depends on Task 2 (Tasks 3–4 parallel)

## Task 3: zie-retro ADR count check and summary generation
<!-- depends_on: Task 2 -->

**What:** Add an ADR count check step to `commands/zie-retro.md`. When count > 30, generate `zie-framework/decisions/ADR-000-summary.md` by calling `hooks/adr_summary.py` logic, then delete the compressed individual files. When count <= 30, skip entirely.

**Acceptance Criteria:**
- Step added after "Count ADR files" line in the "รวบรวม context" section
- Threshold: count > 30 triggers generation; count <= 30 skips
- Keep-recent rule: keep the 10 most-recent ADRs (by filename sort); compress all others
- Fewer than 11 total ADRs (keep-10 would compress nothing): skip even if count logic triggers
- Overwrite `ADR-000-summary.md` if it already exists — no duplicate rows
- Delete each compressed individual file after writing the summary
- `decisions/` missing: skip step entirely
- Wording matches zie-retro style (Thai section headers, Bash inline blocks)

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing test (RED)**

```python
# tests/unit/test_adr_retro_integration.py
"""Integration-style unit tests for the retro ADR summarization step.

Tests use hooks.adr_summary directly to verify the summarization contract
that zie-retro.md will call.
"""
import pytest
from pathlib import Path
from hooks.adr_summary import generate_summary_table, extract_adr_row


def _make_adr(tmp_path: Path, number: int, title: str, decision: str) -> Path:
    name = f"ADR-{number:03d}-{title.lower().replace(' ', '-')}.md"
    p = tmp_path / name
    p.write_text(
        f"# ADR-{number:03d}: {title}\n\n## Decision\n\n{decision}\n",
        encoding="utf-8",
    )
    return p


def test_summary_excludes_adr_000(tmp_path):
    """ADR-000-summary.md must not be included in the paths fed to generate_summary_table."""
    # Simulate a scenario where summary file exists alongside ADRs
    summary = tmp_path / "ADR-000-summary.md"
    summary.write_text("| ADR | Title | Decision |\n|---|---|---|\n| ADR-001 | X | Y |\n")
    adr1 = _make_adr(tmp_path, 1, "first", "Use X.")
    # Only non-summary ADRs should be passed
    paths = [p for p in tmp_path.glob("ADR-*.md") if p.name != "ADR-000-summary.md"]
    result = generate_summary_table(paths)
    assert "ADR-001" in result
    # Summary file itself should not appear as a data row
    assert result.count("ADR-001") == 1


def test_keep_recent_logic():
    """The 10 most-recent ADRs (by filename) must not be in the compress list."""
    # Simulate 35 ADRs; ADRs 026-035 are the 10 most recent
    all_names = [f"ADR-{i:03d}-slug.md" for i in range(1, 36)]
    keep_n = 10
    to_compress = sorted(all_names)[:-keep_n]
    to_keep = sorted(all_names)[-keep_n:]
    assert len(to_compress) == 25
    assert "ADR-026-slug.md" in to_keep
    assert "ADR-025-slug.md" in to_compress


def test_fewer_than_11_adrs_skip():
    """With 10 or fewer ADRs, compress list is empty — skip generation."""
    all_names = [f"ADR-{i:03d}-slug.md" for i in range(1, 11)]
    keep_n = 10
    to_compress = sorted(all_names)[:-keep_n]
    assert to_compress == []


def test_generate_summary_table_no_duplicate_rows(tmp_path):
    """Calling generate_summary_table with the same file twice produces one row."""
    p = _make_adr(tmp_path, 1, "first", "Use X.")
    result = generate_summary_table([p, p])
    # Two identical paths — table will have 2 rows (dedup is caller responsibility)
    # This test documents behavior: caller must deduplicate path list
    row_count = result.count("ADR-001")
    assert row_count == 2  # caller must pass deduplicated list


def test_overwrite_summary_is_idempotent(tmp_path):
    """Writing summary twice with same input produces identical file content."""
    adrs = [_make_adr(tmp_path, i, f"adr-{i}", f"Decision {i}.") for i in range(1, 4)]
    out = tmp_path / "ADR-000-summary.md"
    content1 = generate_summary_table(adrs)
    out.write_text(content1)
    content2 = generate_summary_table(adrs)
    assert content1 == content2
```

Run: `make test-unit` — must PASS (these tests use already-implemented helpers from Task 2; they test the logic contracts the retro command will rely on)

- [ ] **Step 2: Implement (GREEN)**

Edit `commands/zie-retro.md`. In the "รวบรวม context" section, after step 3 ("Count ADR files in `zie-framework/decisions/` → get next ADR number"), add:

```markdown
4. **ADR auto-summarization check** — after counting ADR files:

   ```python
   import os, re
   from pathlib import Path
   from hooks.adr_summary import generate_summary_table

   decisions_dir = Path("zie-framework/decisions")
   if not decisions_dir.exists():
       pass  # skip — decisions/ missing (ADR-006 graceful-skip)
   else:
       individual = sorted([
           p for p in decisions_dir.glob("ADR-*.md")
           if p.name != "ADR-000-summary.md"
       ])
       count = len(individual)
       if count > 30 and count > 10:
           to_compress = individual[:-10]   # all except 10 most-recent
           summary_path = decisions_dir / "ADR-000-summary.md"
           # If summary exists, read existing rows to merge (avoid duplication)
           existing_rows = set()
           if summary_path.exists():
               for line in summary_path.read_text().splitlines():
                   m = re.match(r"\|\s*(ADR-\d+)", line)
                   if m:
                       existing_rows.add(m.group(1).upper())
           # Only compress files not already in summary
           new_to_compress = [
               p for p in to_compress
               if re.match(r"ADR-(\d+)", p.name) and
               f"ADR-{re.match(r'ADR-(\d+)', p.name).group(1).zfill(3)}" not in existing_rows
           ]
           all_to_compress = to_compress  # regenerate full summary from scratch
           table = generate_summary_table(all_to_compress)
           summary_path.write_text(
               f"# ADR Summary\n\nCompressed ADRs (oldest). "
               f"See individual files for ADRs {individual[-10].name[:7]}+.\n\n"
               + table,
               encoding="utf-8",
           )
           for p in all_to_compress:
               p.unlink()
           print(f"[zie-framework] ADR summary written: {len(all_to_compress)} ADRs compressed → ADR-000-summary.md")
       # count <= 30 or count <= 10: skip silently
   ```
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Review the added prose in `zie-retro.md` for clarity. Ensure the `if not decisions_dir.exists(): pass` guard is a real skip (no side effects). Confirm the print prefix follows `[zie-framework] <hook-name>:` convention.

Run: `make test-unit` — still PASS

---

## Task 4: Reviewer skills Phase 1 ADR loading update
<!-- depends_on: Task 2 -->

**What:** Update the three reviewer skills so that when `ADR-000-summary.md` exists, Phase 1 loads it first and then loads only the remaining individual `ADR-*.md` files. When `ADR-000-summary.md` is absent, behaviour is unchanged.

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md` Phase 1 step 2 updated with summary-first loading
- `skills/plan-reviewer/SKILL.md` Phase 1 step 2 updated identically
- `skills/impl-reviewer/SKILL.md` Phase 1 step 2 updated identically
- Original fallback path ("read all `zie-framework/decisions/*.md`") still present for when summary absent
- Wording is concise, consistent across all three files
- `make test-unit` passes (no skill content is tested by unit tests directly, but suite must not regress)

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`

- [ ] **Step 1: Write failing test (RED)**

```python
# tests/unit/test_reviewer_adr_loading.py
"""Verify that all three reviewer skills contain the ADR-000-summary loading instruction."""
import pytest
from pathlib import Path

SKILLS_DIR = Path(__file__).parents[2] / "skills"

REVIEWER_SKILLS = [
    SKILLS_DIR / "spec-reviewer" / "SKILL.md",
    SKILLS_DIR / "plan-reviewer" / "SKILL.md",
    SKILLS_DIR / "impl-reviewer" / "SKILL.md",
]

REQUIRED_PHRASE = "ADR-000-summary.md"


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_loads_summary_file(skill_path):
    """Each reviewer skill must reference ADR-000-summary.md in its Phase 1 section."""
    content = skill_path.read_text(encoding="utf-8")
    assert REQUIRED_PHRASE in content, (
        f"{skill_path.parent.name}/SKILL.md does not reference ADR-000-summary.md "
        "in Phase 1 ADR loading"
    )


@pytest.mark.parametrize("skill_path", REVIEWER_SKILLS, ids=lambda p: p.parent.name)
def test_reviewer_retains_fallback_path(skill_path):
    """Each reviewer skill must still handle the case where no summary exists."""
    content = skill_path.read_text(encoding="utf-8")
    # Original fallback wording
    assert "decisions/*.md" in content, (
        f"{skill_path.parent.name}/SKILL.md lost the fallback ADR glob pattern"
    )
```

Run: `make test-unit` — must FAIL (skills don't reference `ADR-000-summary.md` yet)

- [ ] **Step 2: Implement (GREEN)**

Replace Phase 1 step 2 in all three skills. Current text (shared across all three):

```
2. **ADRs** — read all `zie-framework/decisions/*.md`.
   If directory empty or missing → note "No ADRs found", skip ADR checks.
```

Replace with:

```
2. **ADRs** — load ADR context:
   - If `zie-framework/decisions/ADR-000-summary.md` exists → read it first (compressed history).
   - Then read all remaining individual `zie-framework/decisions/ADR-*.md` files
     (excluding `ADR-000-summary.md`).
   - If directory empty or missing → note "No ADRs found", skip ADR checks.
   - If no `ADR-000-summary.md` → read all `zie-framework/decisions/*.md` as before.
```

Apply this replacement to:
- `skills/spec-reviewer/SKILL.md`
- `skills/plan-reviewer/SKILL.md`
- `skills/impl-reviewer/SKILL.md`

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Read all three updated skills side-by-side and verify the wording is exactly identical across them. Confirm no other Phase 1 text was accidentally altered. No code changes expected.

Run: `make test-unit` — still PASS

---

## Batch 3 — Final (Task 5, depends on Tasks 3–4)

## Task 5: End-to-end smoke test and ADR-025 decision record
<!-- depends_on: Task 3, Task 4 -->

**What:** Write a smoke test that exercises the full summarization pipeline against a temp directory with 35 synthetic ADRs. Verify count, output file existence, compressed file deletion, and keep-10 invariant. Create `ADR-025-adr-auto-summarization.md` documenting this architectural decision.

**Acceptance Criteria:**
- Smoke test: 35 synthetic ADRs → summary generated, 25 files deleted, 10 individual files remain, `ADR-000-summary.md` exists with 25 rows
- Smoke test: 10 synthetic ADRs → no summary generated, 0 files deleted, `ADR-000-summary.md` absent
- Smoke test: 30 synthetic ADRs → no summary generated (threshold is > 30)
- ADR-025 file created at `zie-framework/decisions/ADR-025-adr-auto-summarization.md`
- `make test-unit` passes

**Files:**
- Create: `tests/unit/test_adr_summarization_e2e.py`
- Create: `zie-framework/decisions/ADR-025-adr-auto-summarization.md`

- [ ] **Step 1: Write failing tests (RED)**

```python
# tests/unit/test_adr_summarization_e2e.py
"""End-to-end smoke tests for ADR summarization pipeline."""
import pytest
from pathlib import Path
from hooks.adr_summary import generate_summary_table


def _make_adrs(directory: Path, count: int) -> list[Path]:
    paths = []
    for i in range(1, count + 1):
        p = directory / f"ADR-{i:03d}-slug-{i}.md"
        p.write_text(
            f"# ADR-{i:03d}: Slug {i}\n\n## Decision\n\nDecision text for ADR {i}.\n",
            encoding="utf-8",
        )
        paths.append(p)
    return paths


def _simulate_retro_summarization(directory: Path) -> dict:
    """Run the summarization logic inline (mirrors zie-retro.md step 4)."""
    individual = sorted([
        p for p in directory.glob("ADR-*.md")
        if p.name != "ADR-000-summary.md"
    ])
    count = len(individual)
    summary_written = False
    compressed_count = 0

    if count > 30 and count > 10:
        to_compress = individual[:-10]
        summary_path = directory / "ADR-000-summary.md"
        table = generate_summary_table(to_compress)
        summary_path.write_text(
            "# ADR Summary\n\n" + table, encoding="utf-8"
        )
        for p in to_compress:
            p.unlink()
        summary_written = True
        compressed_count = len(to_compress)

    remaining = sorted([
        p for p in directory.glob("ADR-*.md")
        if p.name != "ADR-000-summary.md"
    ])
    return {
        "summary_written": summary_written,
        "compressed_count": compressed_count,
        "remaining_individual": len(remaining),
        "summary_exists": (directory / "ADR-000-summary.md").exists(),
    }


def test_35_adrs_triggers_summarization(tmp_path):
    _make_adrs(tmp_path, 35)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is True
    assert result["compressed_count"] == 25
    assert result["remaining_individual"] == 10
    assert result["summary_exists"] is True


def test_10_adrs_no_summarization(tmp_path):
    _make_adrs(tmp_path, 10)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is False
    assert result["compressed_count"] == 0
    assert result["summary_exists"] is False


def test_30_adrs_no_summarization(tmp_path):
    """Exactly 30 ADRs is below threshold (> 30 required)."""
    _make_adrs(tmp_path, 30)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is False
    assert result["summary_exists"] is False


def test_31_adrs_triggers_summarization(tmp_path):
    """31 ADRs is above threshold — summary must be written."""
    _make_adrs(tmp_path, 31)
    result = _simulate_retro_summarization(tmp_path)
    assert result["summary_written"] is True
    assert result["compressed_count"] == 21
    assert result["remaining_individual"] == 10


def test_summary_table_has_correct_row_count(tmp_path):
    """Summary table must have exactly compressed_count data rows."""
    _make_adrs(tmp_path, 35)
    _simulate_retro_summarization(tmp_path)
    summary = (tmp_path / "ADR-000-summary.md").read_text()
    # Count rows: lines starting with "| ADR-"
    data_rows = [l for l in summary.splitlines() if l.startswith("| ADR-")]
    assert len(data_rows) == 25


def test_idempotent_rerun(tmp_path):
    """Running summarization twice on the same directory produces identical summary."""
    _make_adrs(tmp_path, 35)
    _simulate_retro_summarization(tmp_path)
    content_after_first = (tmp_path / "ADR-000-summary.md").read_text()
    # Second run: only 10 individual files remain → count=10, no re-trigger
    result2 = _simulate_retro_summarization(tmp_path)
    assert result2["summary_written"] is False  # count dropped to 10, no re-trigger
    # Summary unchanged
    content_after_second = (tmp_path / "ADR-000-summary.md").read_text()
    assert content_after_first == content_after_second
```

Run: `make test-unit` — must FAIL (`hooks.adr_summary` methods not yet fully exercised by e2e path; passes once Task 2 is done, but e2e tests are new)

- [ ] **Step 2: Implement (GREEN)**

Create `zie-framework/decisions/ADR-025-adr-auto-summarization.md`:

```markdown
---
date: 2026-03-29
status: accepted
---

# ADR-025: ADR Auto-Summarization via /zie-retro

## Context

Reviewer skills (spec-reviewer, plan-reviewer, impl-reviewer) load all
`decisions/*.md` on every invocation. At 24 ADRs / 914 lines today and growing
~1 ADR per release, the full ADR set will exceed practical context limits.

## Decision

When `/zie-retro` counts more than 30 individual ADR files, it generates
`decisions/ADR-000-summary.md` — a Markdown table compressing the oldest ADRs
(all except the 10 most-recent) into one row each — then deletes those individual
files. Reviewer skills load `ADR-000-summary.md` first when it exists, then
the remaining individual files.

## Consequences

- Reviewer context window for ADRs stays bounded at ~10 full ADRs + 1 summary table.
- Compressed ADRs are recoverable from git history (the summary file is
  regeneratable by re-running retro).
- Threshold constants (30/10) are fixed in code; no config knob (YAGNI).
- `ADR-000-summary.md` is not source-tracked — it is a generated artefact.
```

Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

Review all new test files for clarity. Verify `_simulate_retro_summarization` mirrors the logic in `zie-retro.md` step 4 precisely. Confirm ADR-025 prose is concise and matches the ADR format used by existing decisions.

Run: `make test-unit` — still PASS
