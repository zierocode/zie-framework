---
approved: true
approved_at: 2026-04-04
backlog: backlog/smarter-framework-intelligence.md
spec: specs/2026-04-04-smarter-framework-intelligence-design.md
---

# Smarter Framework Intelligence — Implementation Plan

**Goal:** Add three targeted intelligence layers — proactive Stop hook nudges, backlog auto-tagging with duplicate detection, and self-tuning config proposals in retro — operating entirely within existing infrastructure with graceful degradation.
**Architecture:** All three layers are additive modifications to existing files (`stop-guard.py`, `utils_roadmap.py`, `commands/zie-backlog.md`, `commands/zie-retro.md`). The Stop hook nudges use git log + file mtime inspection; backlog intelligence uses keyword matching + token-set overlap; self-tuning proposals parse git log commit messages and read `.config`. No external storage, no new files, no LLM calls.
**Tech Stack:** Python 3.x, stdlib only (subprocess, os, pathlib, re, datetime); pytest for tests; Markdown commands.

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `hooks/utils_roadmap.py` | Add `parse_roadmap_items_with_dates()` helper |
| Modify | `hooks/stop-guard.py` | Add three nudge checks after existing block-check |
| Modify | `commands/zie-backlog.md` | Add auto-tag step + duplicate-detection step |
| Modify | `commands/zie-retro.md` | Add self-tuning proposal step after existing retro steps |
| Create | `tests/unit/test_nudges_stop_guard.py` | Unit tests for all three nudge conditions |
| Create | `tests/unit/test_utils_roadmap_with_dates.py` | Unit tests for `parse_roadmap_items_with_dates()` |
| Create | `tests/unit/test_backlog_intelligence.py` | Unit tests for auto-tag keyword matching + duplicate detection logic |
| Create | `tests/unit/test_retro_self_tuning.py` | Unit tests for self-tuning proposal parsing logic |

---

## Task Sizing Check

- 4 tasks, each single-file or single-concern: M plan (right-sized)
- Tasks 1 and 2 share `utils_roadmap.py` → Task 2 depends on Task 1
- Tasks 3 and 4 are independent of each other and of Tasks 1–2 (Markdown commands)
- Task 5 (integration: new test files) depends on Tasks 1–4

Parallel batch: Tasks 3 + 4 can run concurrently. Task 2 must follow Task 1.

---

## Task 1: Add `parse_roadmap_items_with_dates()` to utils_roadmap.py

**Acceptance Criteria:**
- `parse_roadmap_items_with_dates(roadmap_path, section_name)` returns a list of `(item_text: str, date: datetime.date | None)` tuples for items in the named section
- Date is parsed from ISO format `YYYY-MM-DD` anywhere in the item line; if none found, `date=None`
- Returns `[]` if file missing, section absent, or empty
- Function follows the same two-tier error handling convention as other helpers in this module

**Files:**
- Modify: `hooks/utils_roadmap.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_utils_roadmap_with_dates.py`:

  ```python
  """Tests for parse_roadmap_items_with_dates() in utils_roadmap.py."""
  import datetime
  import os
  import sys

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
  from utils_roadmap import parse_roadmap_items_with_dates


  class TestParseRoadmapItemsWithDates:
      def test_returns_list_of_tuples(self, tmp_path):
          """Returns list of (text, date) tuples."""
          roadmap = tmp_path / "ROADMAP.md"
          roadmap.write_text("## Next\n- [ ] old-feature — 2026-01-01\n- [ ] new-feature\n")
          result = parse_roadmap_items_with_dates(roadmap, "next")
          assert len(result) == 2
          texts = [r[0] for r in result]
          assert any("old-feature" in t for t in texts)
          assert any("new-feature" in t for t in texts)

      def test_parses_iso_date_from_item(self, tmp_path):
          """ISO date YYYY-MM-DD in item line is returned as datetime.date."""
          roadmap = tmp_path / "ROADMAP.md"
          roadmap.write_text("## Next\n- [ ] stale-item — [backlog](backlog/stale-item.md) 2025-12-01\n")
          result = parse_roadmap_items_with_dates(roadmap, "next")
          assert result[0][1] == datetime.date(2025, 12, 1)

      def test_none_date_when_no_date_in_item(self, tmp_path):
          """date=None when item line has no ISO date."""
          roadmap = tmp_path / "ROADMAP.md"
          roadmap.write_text("## Next\n- [ ] no-date-item\n")
          result = parse_roadmap_items_with_dates(roadmap, "next")
          assert result[0][1] is None

      def test_empty_on_missing_file(self, tmp_path):
          """Returns [] when file does not exist."""
          result = parse_roadmap_items_with_dates(tmp_path / "MISSING.md", "next")
          assert result == []

      def test_empty_on_missing_section(self, tmp_path):
          """Returns [] when named section is absent."""
          roadmap = tmp_path / "ROADMAP.md"
          roadmap.write_text("## Now\n- [ ] thing\n")
          result = parse_roadmap_items_with_dates(roadmap, "next")
          assert result == []

      def test_multiple_dates_takes_first(self, tmp_path):
          """When multiple dates appear in one item, the first is returned."""
          roadmap = tmp_path / "ROADMAP.md"
          roadmap.write_text("## Next\n- [ ] item 2025-01-01 2025-06-01\n")
          result = parse_roadmap_items_with_dates(roadmap, "next")
          assert result[0][1] == datetime.date(2025, 1, 1)
  ```

  Run: `make test-unit` — must FAIL (`ImportError: cannot import name 'parse_roadmap_items_with_dates'`)

- [ ] **Step 2: Implement (GREEN)**

  Add to `hooks/utils_roadmap.py` after the existing `is_mtime_fresh` function:

  ```python
  def parse_roadmap_items_with_dates(
      roadmap_path,
      section_name: str,
  ) -> list:
      """Extract items from a named ## section with parsed ISO dates.

      Returns a list of (item_text: str, date: datetime.date | None) tuples.
      item_text is the cleaned item text (same stripping as parse_roadmap_section).
      date is the first YYYY-MM-DD found in the raw line, or None if absent.

      Returns [] if file missing, section absent, or empty.
      """
      import datetime as _dt
      _DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")
      try:
          path = Path(roadmap_path)
          if not path.exists():
              return []
          content = path.read_text()
          results = []
          in_section = False
          for line in content.splitlines():
              if line.startswith("##") and section_name.lower() in line.lower():
                  in_section = True
                  continue
              if line.startswith("##") and in_section:
                  break
              if in_section and line.strip().startswith("- "):
                  clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line.strip())
                  clean = clean.lstrip("- ").lstrip("[ ]").lstrip("[x]").strip()
                  if not clean:
                      continue
                  m = _DATE_RE.search(line)
                  date = None
                  if m:
                      try:
                          date = _dt.date.fromisoformat(m.group(1))
                      except ValueError:
                          date = None
                  results.append((clean, date))
          return results
      except Exception:
          return []
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify the `import datetime as _dt` is inside the function (avoids module-level import change). Confirm `_DATE_RE` pattern is consistent with the existing `_DATE_RE` used in `compact_roadmap_done`. If identical, consider hoisting to module level in a follow-up — YAGNI for now.

  Run: `make test-unit` — still PASS

---

## Task 2: Add proactive nudges to stop-guard.py

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- After the existing uncommitted-file block-check exits with no block, stop-guard runs up to three nudge checks
- RED phase nudge: finds `[ ]` items in ROADMAP Now lane, runs `git log --all -p -- zie-framework/ROADMAP.md | grep -B5 "+- \[ \] <slug>"` to find the commit that added the `[ ]` item to the Now lane; if > 2 days elapsed → prints `[zie-framework] nudge: RED phase '<slug>' has been active for N days — consider splitting or committing partial progress`
- Coverage nudge: compares `.coverage` mtime vs newest `tests/*.py` mtime; if `.coverage` missing OR coverage mtime < newest test mtime → prints `[zie-framework] nudge: coverage data is stale — run 'make test-unit' to refresh`
- Stale backlog nudge: calls `parse_roadmap_items_with_dates(roadmap_path, "next")`; if any item date > 30 days ago → prints `[zie-framework] nudge: N backlog item(s) in Next are older than 30 days — review or defer`
- All three nudge checks are independent; each fires or suppresses individually
- If `stop_hook_active` is set → nudges are fully skipped (existing guard already handles this)
- All nudge paths exit 0; any exception in a nudge check is caught and silently skipped
- Nudges are printed to stdout as plain text (NOT as JSON block decisions)

**Files:**
- Modify: `hooks/stop-guard.py`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_nudges_stop_guard.py`:

  ```python
  """Tests for proactive nudge checks added to stop-guard.py."""
  import json
  import os
  import subprocess
  import sys
  import uuid
  from pathlib import Path

  REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
  HOOK = os.path.join(REPO_ROOT, "hooks", "stop-guard.py")


  def run_hook(event: dict, cwd: str, env_overrides: dict = None):
      env = {**os.environ, "CLAUDE_CWD": cwd, "CLAUDE_SESSION_ID": str(uuid.uuid4())}
      if env_overrides:
          env.update(env_overrides)
      return subprocess.run(
          [sys.executable, HOOK],
          input=json.dumps(event),
          capture_output=True,
          text=True,
          env=env,
      )


  class TestCoverageNudge:
      def test_nudge_when_coverage_missing(self, tmp_path):
          """Prints coverage nudge when .coverage file is absent."""
          # Create tests dir with a test file but no .coverage
          tests_dir = tmp_path / "tests"
          tests_dir.mkdir()
          (tests_dir / "test_something.py").write_text("def test_x(): pass\n")
          # ROADMAP with no Now items (skip RED + stale nudges)
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "[zie-framework] nudge:" in r.stdout
          assert "coverage" in r.stdout.lower()

      def test_no_coverage_nudge_when_coverage_fresh(self, tmp_path):
          """No coverage nudge when .coverage is newer than all test files."""
          import time
          tests_dir = tmp_path / "tests"
          tests_dir.mkdir()
          test_file = tests_dir / "test_something.py"
          test_file.write_text("def test_x(): pass\n")
          time.sleep(0.02)
          cov_file = tmp_path / ".coverage"
          cov_file.write_text("coverage data")
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          # coverage nudge should NOT appear
          assert "coverage data is stale" not in r.stdout

      def test_no_coverage_nudge_when_no_tests_dir(self, tmp_path):
          """No nudge when tests/ directory does not exist."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text("## Now\n\n## Next\n\n## Done\n")
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "coverage data is stale" not in r.stdout


  class TestStaleBacklogNudge:
      def test_nudge_when_next_item_older_than_30_days(self, tmp_path):
          """Prints stale backlog nudge when a Next item date is > 30 days ago."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] old-item — [backlog](backlog/old-item.md) 2020-01-01\n\n"
              "## Done\n"
          )
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "[zie-framework] nudge:" in r.stdout
          assert "30 days" in r.stdout

      def test_no_stale_nudge_when_next_items_recent(self, tmp_path):
          """No stale backlog nudge when all Next items are within 30 days."""
          import datetime
          recent = (datetime.date.today() - datetime.timedelta(days=5)).isoformat()
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              f"## Now\n\n"
              f"## Next\n"
              f"- [ ] recent-item — {recent}\n\n"
              "## Done\n"
          )
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "30 days" not in r.stdout

      def test_no_stale_nudge_when_no_roadmap(self, tmp_path):
          """No nudge when zie-framework/ROADMAP.md is missing."""
          r = run_hook({}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "30 days" not in r.stdout

      def test_nudge_prefix_format(self, tmp_path):
          """Nudge output starts with '[zie-framework] nudge:' prefix."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] stale — 2020-06-01\n\n"
              "## Done\n"
          )
          r = run_hook({}, cwd=str(tmp_path))
          assert "[zie-framework] nudge:" in r.stdout

      def test_all_three_nudges_independent(self, tmp_path):
          """All three nudges fire independently and as separate lines."""
          import datetime
          tests_dir = tmp_path / "tests"
          tests_dir.mkdir()
          (tests_dir / "test_x.py").write_text("def test_x(): pass\n")
          # No .coverage → coverage nudge fires
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n"
              "## Next\n"
              "- [ ] old — 2019-01-01\n\n"
              "## Done\n"
          )
          r = run_hook({}, cwd=str(tmp_path))
          nudge_lines = [ln for ln in r.stdout.splitlines() if "[zie-framework] nudge:" in ln]
          # At least 2 nudges (coverage + stale backlog)
          assert len(nudge_lines) >= 2

      def test_stop_hook_active_skips_all_nudges(self, tmp_path):
          """stop_hook_active guard skips nudge checks entirely."""
          zf = tmp_path / "zie-framework"
          zf.mkdir()
          (zf / "ROADMAP.md").write_text(
              "## Now\n\n## Next\n- [ ] stale — 2019-01-01\n\n## Done\n"
          )
          r = run_hook({"stop_hook_active": True}, cwd=str(tmp_path))
          assert r.returncode == 0
          assert "[zie-framework] nudge:" not in r.stdout
  ```

  Run: `make test-unit` — must FAIL (nudge output not yet emitted)

- [ ] **Step 2: Implement (GREEN)**

  In `hooks/stop-guard.py`, add the nudge section after the existing `sys.exit(0)` at line 91 (after the `if not uncommitted: sys.exit(0)` block). The flow must be:

  1. Existing block-check runs first.
  2. If uncommitted files → block (print JSON, exit 0). No nudges.
  3. If no uncommitted files → run nudge checks, then exit 0.

  Restructure the inner try block to separate the two concerns:

  ```python
  # Inside the existing inner try block, replace:
  #   if not uncommitted:
  #       sys.exit(0)
  # with nudge logic after the uncommitted check:

  if uncommitted:
      file_list = "\n".join(f"  {p}" for p in sorted(uncommitted))
      reason = (
          f"Uncommitted implementation files detected:\n{file_list}\n\n"
          "Commit this work before ending:\n"
          "  git add -A && git commit -m 'feat: <describe change>'"
      )
      print(json.dumps({"decision": "block", "reason": reason}))
      sys.exit(0)

  # --- Proactive nudges ---
  _run_nudges(cwd, config, subprocess_timeout)
  sys.exit(0)
  ```

  Add `_run_nudges` as a module-level helper function:

  ```python
  def _run_nudges(cwd, config, subprocess_timeout):
      """Run proactive nudge checks. Each check is independent and silently skipped on error."""
      import datetime as _dt
      from utils_roadmap import parse_roadmap_items_with_dates

      roadmap_path = cwd / "zie-framework" / "ROADMAP.md"

      # Nudge 1: RED phase duration
      try:
          now_items_raw = []
          if roadmap_path.exists():
              content = roadmap_path.read_text()
              in_now = False
              for line in content.splitlines():
                  if line.startswith("##") and "now" in line.lower():
                      in_now = True
                      continue
                  if line.startswith("##") and in_now:
                      break
                  if in_now and "[ ]" in line:
                      # Extract slug from line
                      slug_match = re.search(r'\[([^\]]+)\]\(backlog/([^\)]+)\.md\)', line)
                      slug = slug_match.group(2) if slug_match else line.strip()
                      now_items_raw.append(slug)
          for slug in now_items_raw:
              try:
                  # Use git log -p piped through grep to find the commit that added
                  # the [ ] item to the Now lane specifically
                  result = subprocess.run(
                      f"git log --all -p -- zie-framework/ROADMAP.md "
                      f"| grep -B5 '+- \\[ \\] {slug}'",
                      cwd=str(cwd),
                      capture_output=True,
                      text=True,
                      timeout=subprocess_timeout,
                      shell=True,
                  )
                  if result.returncode == 0 and result.stdout.strip():
                      # Extract date from "Date:" line in context (git log -p includes headers)
                      date_match = re.search(r'^Date:\s+(\d{4}-\d{2}-\d{2})', result.stdout, re.MULTILINE)
                      if not date_match:
                          # fallback: try commit header line format
                          date_match = re.search(r'(\d{4}-\d{2}-\d{2})', result.stdout)
                      if date_match:
                          commit_date = _dt.date.fromisoformat(date_match.group(1))
                          days = (_dt.date.today() - commit_date).days
                          if days > 2:
                              print(
                                  f"[zie-framework] nudge: RED phase '{slug}' has been active for "
                                  f"{days} days — consider splitting or committing partial progress"
                              )
              except Exception:
                  pass
      except Exception:
          pass

      # Nudge 2: Coverage staleness
      try:
          tests_dir = cwd / "tests"
          if tests_dir.exists():
              test_files = list(tests_dir.glob("*.py"))
              if test_files:
                  newest_test_mtime = max(f.stat().st_mtime for f in test_files)
                  cov_file = cwd / ".coverage"
                  if not cov_file.exists():
                      print("[zie-framework] nudge: coverage data is stale — run 'make test-unit' to refresh")
                  elif cov_file.stat().st_mtime < newest_test_mtime:
                      print("[zie-framework] nudge: coverage data is stale — run 'make test-unit' to refresh")
      except Exception:
          pass

      # Nudge 3: Stale backlog items in Next
      try:
          items_with_dates = parse_roadmap_items_with_dates(roadmap_path, "next")
          today = _dt.date.today()
          stale_count = sum(
              1 for _, d in items_with_dates
              if d is not None and (today - d).days > 30
          )
          if stale_count > 0:
              print(
                  f"[zie-framework] nudge: {stale_count} backlog item(s) in Next are older than "
                  "30 days — review or defer"
              )
      except Exception:
          pass
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Ensure `_run_nudges` is defined before the inner try block that calls it (module-level, not inside try). Verify the existing block-check tests still pass — nudges must not interfere with block output.

  Run: `make test-unit` — still PASS

---

## Task 3: Add auto-tag and duplicate detection to /zie-backlog

**Acceptance Criteria:**
- After slug derivation and re-run guard, `/zie-backlog` infers a tag using keyword matching: `{bug: [fix, error, crash, broken], chore: [cleanup, update, bump, refactor], debt: [tech debt, debt, legacy, slow], feature: [add, new, implement, support]}` — first match wins, default = `"feature"`
- Tag is written to backlog file frontmatter: `tags: [<tag>]`
- After tag inference, before writing the file, checks existing `zie-framework/backlog/*.md` slugs; if any existing slug shares ≥2 tokens with the new slug → warns `"Similar item exists: backlog/<existing-slug>.md"` (does NOT block)
- Tokens: split slug by `-` → lowercase set; check token overlap with each existing file's basename (without `.md`)

**Files:**
- Modify: `commands/zie-backlog.md`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_backlog_intelligence.py` to test the pure logic functions:

  ```python
  """Tests for backlog auto-tag keyword matching and duplicate detection logic.

  These test the pure Python functions extracted from the /zie-backlog command
  logic. The functions are defined in hooks/utils_backlog.py (new file created
  in Task 3 Step 2).
  """
  import os
  import sys

  import pytest

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
  from utils_backlog import infer_tag, find_duplicate_slugs

  TAG_KEYWORD_MAP = {
      "bug": ["fix", "error", "crash", "broken"],
      "chore": ["cleanup", "update", "bump", "refactor"],
      "debt": ["tech debt", "debt", "legacy", "slow"],
      "feature": ["add", "new", "implement", "support"],
  }


  class TestInferTag:
      def test_bug_tag_on_fix_keyword(self):
          assert infer_tag("fix login error", TAG_KEYWORD_MAP) == "bug"

      def test_chore_tag_on_refactor_keyword(self):
          assert infer_tag("refactor utils module", TAG_KEYWORD_MAP) == "chore"

      def test_debt_tag_on_legacy_keyword(self):
          assert infer_tag("migrate legacy auth system", TAG_KEYWORD_MAP) == "debt"

      def test_feature_tag_on_add_keyword(self):
          assert infer_tag("add CSV export", TAG_KEYWORD_MAP) == "feature"

      def test_default_feature_when_no_match(self):
          assert infer_tag("smarter framework intelligence", TAG_KEYWORD_MAP) == "feature"

      def test_first_match_wins(self):
          # "fix" matches bug; "refactor" matches chore — bug wins (first in map)
          assert infer_tag("fix and refactor error handler", TAG_KEYWORD_MAP) == "bug"

      def test_case_insensitive_match(self):
          assert infer_tag("Fix Crash on startup", TAG_KEYWORD_MAP) == "bug"

      def test_empty_title_returns_feature(self):
          assert infer_tag("", TAG_KEYWORD_MAP) == "feature"


  class TestFindDuplicateSlugs:
      def test_no_duplicates_when_backlog_empty(self, tmp_path):
          """Returns [] when no existing backlog files."""
          result = find_duplicate_slugs("add-csv-export", tmp_path)
          assert result == []

      def test_detects_two_token_overlap(self, tmp_path):
          """Returns existing slug when ≥2 tokens overlap."""
          (tmp_path / "csv-export-tool.md").write_text("")
          result = find_duplicate_slugs("add-csv-export", tmp_path)
          # tokens of add-csv-export: {add, csv, export}
          # tokens of csv-export-tool: {csv, export, tool}
          # overlap: {csv, export} → 2 tokens → duplicate
          assert "csv-export-tool" in result

      def test_no_duplicate_on_one_token_overlap(self, tmp_path):
          """No duplicate when only 1 token overlaps."""
          (tmp_path / "csv-summary.md").write_text("")
          result = find_duplicate_slugs("add-csv-export", tmp_path)
          # tokens: {add, csv, export} vs {csv, summary} → overlap: {csv} → 1 token → no warn
          assert result == []

      def test_ignores_self_match(self, tmp_path):
          """Exact same slug is ignored (re-run guard handles it separately)."""
          (tmp_path / "add-csv-export.md").write_text("")
          result = find_duplicate_slugs("add-csv-export", tmp_path)
          assert "add-csv-export" not in result

      def test_multiple_duplicates_returned(self, tmp_path):
          """Returns all matching slugs when multiple overlap."""
          (tmp_path / "csv-export-tool.md").write_text("")
          (tmp_path / "csv-export-report.md").write_text("")
          result = find_duplicate_slugs("add-csv-export", tmp_path)
          assert len(result) == 2
  ```

  Run: `make test-unit` — must FAIL (`ImportError: cannot import name 'infer_tag'`)

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_backlog.py`:

  ```python
  #!/usr/bin/env python3
  """Backlog intelligence helpers — auto-tag and duplicate detection."""
  import re
  from pathlib import Path


  def infer_tag(title: str, keyword_map: dict) -> str:
      """Infer a tag from title text using keyword_map.

      keyword_map: {tag: [keyword, ...]} — first match wins.
      Default tag is 'feature' when no keyword matches.
      Matching is case-insensitive substring.
      """
      title_lower = title.lower()
      for tag, keywords in keyword_map.items():
          for kw in keywords:
              if kw.lower() in title_lower:
                  return tag
      return "feature"


  def find_duplicate_slugs(new_slug: str, backlog_dir) -> list:
      """Return list of existing slugs with ≥2 token overlap against new_slug.

      backlog_dir: Path to directory containing backlog *.md files.
      Tokens: split slug by '-', lowercase. Exact self-match is excluded.
      Returns [] when backlog_dir is empty or missing.
      """
      backlog_path = Path(backlog_dir)
      if not backlog_path.exists():
          return []
      new_tokens = set(new_slug.lower().split("-"))
      duplicates = []
      for f in backlog_path.glob("*.md"):
          existing_slug = f.stem
          if existing_slug == new_slug:
              continue
          existing_tokens = set(existing_slug.lower().split("-"))
          if len(new_tokens & existing_tokens) >= 2:
              duplicates.append(existing_slug)
      return duplicates
  ```

  Update `commands/zie-backlog.md` — add steps 2b and 2c between the existing re-run guard (step 3) and file write (step 4):

  ```markdown
  2b. **Infer tag** from title + description using keyword map:
      - `{bug: [fix, error, crash, broken], chore: [cleanup, update, bump, refactor], debt: [tech debt, debt, legacy, slow], feature: [add, new, implement, support]}`
      - First keyword match wins (case-insensitive); default = `"feature"`
      - Tag will be written to frontmatter as `tags: [<tag>]`
      - Run the following Bash step to compute the tag:

        ```bash
        python3 -c "
        import sys; sys.path.insert(0, 'hooks')
        from hooks.utils_backlog import infer_tag
        TAG_MAP = {'bug': ['fix','error','crash','broken'], 'chore': ['cleanup','update','bump','refactor'], 'debt': ['tech debt','debt','legacy','slow'], 'feature': ['add','new','implement','support']}
        print(infer_tag('<title> <description>', TAG_MAP))
        "
        ```

        Capture output as `<inferred-tag>`.

  2c. **Duplicate check**: split new slug by `-` → token set. For each file in `zie-framework/backlog/*.md`:
      - Tokenize its basename (strip `.md`, split by `-`)
      - If ≥2 tokens overlap with new slug tokens → warn: `"Similar item exists: backlog/<slug>.md"`
      - Does NOT block creation. Print all warnings before continuing.
      - Run the following Bash step to check duplicates:

        ```bash
        python3 -c "
        import sys; sys.path.insert(0, 'hooks')
        from hooks.utils_backlog import find_duplicate_slugs
        from pathlib import Path
        dupes = find_duplicate_slugs('<new-slug>', Path('zie-framework/backlog'))
        for d in dupes:
            print(f'Similar item exists: backlog/{d}.md')
        "
        ```
  ```

  Update the backlog file template in step 4 to include frontmatter:

  ```markdown
  ---
  tags: [<inferred-tag>]
  ---

  # <Idea Title>
  ...
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `utils_backlog.py` is added to `IMPL_PATTERNS` in `stop-guard.py` if needed (hooks/*.py already covers it). Confirm test file doesn't import from command (pure function extraction is clean).

  Run: `make test-unit` — still PASS

---

## Task 4: Add self-tuning proposals to /zie-retro

**Acceptance Criteria:**
- After the existing retro steps complete (before auto-commit), `/zie-retro` runs self-tuning analysis
- Reads `.config` — if absent → prints `"Self-tuning: skipped (no .config)"` and skips entirely
- Scans `git log --oneline` for commits mentioning RED alongside duration words (`stuck`, `slow`, `days`, or a number followed by `day`)
- Parses these to approximate last 5 RED cycle durations; if average > 3 days → proposes `auto_test_max_wait_s: <current> → 30`
- Checks current `safety_check_mode`; if `"agent"` and no agent-level blocks found in last 10 sessions (no `"BLOCK"` in recent git log) → proposes `safety_check_mode: "agent" → "regex"`
- Proposals are printed as diff-style summary (at most 3 proposals)
- User must type `"apply"` to write changes to `.config`; any other input → `"Self-tuning: no changes applied"`
- On `"apply"` → writes `.config` atomically via `atomic_write()`; prints confirmation
- If no proposals → prints `"Self-tuning: no changes proposed"`

**Files:**
- Modify: `commands/zie-retro.md`

- [ ] **Step 1: Write failing tests (RED)**

  Create `tests/unit/test_retro_self_tuning.py`:

  ```python
  """Tests for self-tuning proposal logic extracted from /zie-retro.

  Tests the pure Python helpers in hooks/utils_self_tuning.py.
  """
  import json
  import os
  import sys
  from pathlib import Path

  import pytest

  sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../hooks"))
  from utils_self_tuning import (
      parse_red_cycle_durations_from_log,
      build_tuning_proposals,
  )


  class TestParseRedCycleDurations:
      def test_returns_empty_on_no_red_commits(self):
          log = "abc1234 feat: add new feature\ndef5678 fix: resolve bug\n"
          result = parse_red_cycle_durations_from_log(log)
          assert result == []

      def test_detects_red_stuck_commit(self):
          log = "abc1234 RED phase stuck for 3 days — split task\n"
          result = parse_red_cycle_durations_from_log(log)
          assert 3 in result

      def test_detects_red_slow_commit(self):
          log = "abc1234 RED: slow going, took 5 days\n"
          result = parse_red_cycle_durations_from_log(log)
          assert 5 in result

      def test_returns_at_most_5_cycles(self):
          log = "\n".join(
              [f"abc{i} RED phase stuck {i+2} days" for i in range(10)]
          )
          result = parse_red_cycle_durations_from_log(log)
          assert len(result) <= 5

      def test_ignores_commits_without_duration_word(self):
          log = "abc1234 RED phase completed\n"
          result = parse_red_cycle_durations_from_log(log)
          assert result == []


  class TestBuildTuningProposals:
      def test_no_proposals_when_no_patterns(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
          proposals = build_tuning_proposals(config, red_durations=[], recent_log="")
          assert proposals == []

      def test_proposes_auto_test_wait_when_avg_exceeds_3_days(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
          # Average of [4, 5, 3, 4, 5] = 4.2 > 3
          proposals = build_tuning_proposals(config, red_durations=[4, 5, 3, 4, 5], recent_log="")
          keys = [p["key"] for p in proposals]
          assert "auto_test_max_wait_s" in keys

      def test_no_auto_test_proposal_when_avg_under_3_days(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "regex"}
          proposals = build_tuning_proposals(config, red_durations=[1, 2, 1], recent_log="")
          keys = [p["key"] for p in proposals]
          assert "auto_test_max_wait_s" not in keys

      def test_proposes_safety_mode_when_agent_and_no_blocks(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
          recent_log = "abc feat: add thing\ndef fix: small bug\n"
          proposals = build_tuning_proposals(config, red_durations=[], recent_log=recent_log)
          keys = [p["key"] for p in proposals]
          assert "safety_check_mode" in keys

      def test_no_safety_mode_proposal_when_blocks_present(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
          recent_log = "abc BLOCK: safety check blocked rm -rf\n"
          proposals = build_tuning_proposals(config, red_durations=[], recent_log=recent_log)
          keys = [p["key"] for p in proposals]
          assert "safety_check_mode" not in keys

      def test_at_most_3_proposals(self):
          config = {"auto_test_max_wait_s": 15, "safety_check_mode": "agent"}
          proposals = build_tuning_proposals(config, red_durations=[4, 5, 4, 5, 4], recent_log="no blocks")
          assert len(proposals) <= 3
  ```

  Run: `make test-unit` — must FAIL (`ImportError: cannot import name 'parse_red_cycle_durations_from_log'`)

- [ ] **Step 2: Implement (GREEN)**

  Create `hooks/utils_self_tuning.py`:

  ```python
  #!/usr/bin/env python3
  """Self-tuning proposal helpers for /zie-retro."""
  import re


  # Pattern: commit mentions "RED" (case-insensitive) + duration word + optional number
  _RED_DURATION_RE = re.compile(
      r'\bRED\b.*?(\d+)\s*day',
      re.IGNORECASE,
  )
  _RED_SIGNAL_RE = re.compile(
      r'\bRED\b.*?\b(stuck|slow|days)\b',
      re.IGNORECASE,
  )


  def parse_red_cycle_durations_from_log(log: str) -> list:
      """Parse approximate RED cycle durations (in days) from git log oneline output.

      Returns a list of int durations, capped at 5 cycles (most recent first).
      Only includes commits where a numeric day count is found.
      Commits matching RED + (stuck|slow|days) but without a number are excluded.
      """
      durations = []
      for line in log.splitlines():
          if not re.search(r'\bRED\b', line, re.IGNORECASE):
              continue
          m = _RED_DURATION_RE.search(line)
          if m:
              try:
                  days = int(m.group(1))
                  durations.append(days)
              except ValueError:
                  pass
          if len(durations) >= 5:
              break
      return durations


  def build_tuning_proposals(config: dict, red_durations: list, recent_log: str) -> list:
      """Build list of config change proposals based on observed patterns.

      Returns list of dicts: [{key, from_val, to_val, reason}].
      At most 3 proposals returned.
      """
      proposals = []

      # Proposal 1: auto_test_max_wait_s — if avg RED cycle > 3 days
      if red_durations:
          avg_days = sum(red_durations) / len(red_durations)
          if avg_days > 3:
              current = config.get("auto_test_max_wait_s", 15)
              proposals.append({
                  "key": "auto_test_max_wait_s",
                  "from_val": current,
                  "to_val": 30,
                  "reason": f"RED cycles averaged >{avg_days:.1f} days across last {len(red_durations)} cycles",
              })

      # Proposal 2: safety_check_mode — if "agent" and no BLOCKs in recent log
      if config.get("safety_check_mode") == "agent":
          if "BLOCK" not in recent_log:
              proposals.append({
                  "key": "safety_check_mode",
                  "from_val": "agent",
                  "to_val": "regex",
                  "reason": "no agent-level blocks in last 10 sessions",
              })

      return proposals[:3]
  ```

  Update `commands/zie-retro.md` — add a new `### Self-tuning proposals` subsection inside `### รวมผลลัพธ์` (after docs-sync verdict, before auto-commit):

  ```markdown
  ### Self-tuning proposals

  After docs-sync verdict, before auto-commit:

  1. Read `zie-framework/.config`. If absent → print `"Self-tuning: skipped (no .config)"` and skip this section.
  2. Run the following Bash step to parse RED cycle durations:

     ```bash
     git log --oneline -50 | python3 -c "
     import sys; sys.path.insert(0, 'hooks')
     from hooks.utils_self_tuning import parse_red_cycle_durations_from_log
     import json
     log = sys.stdin.read()
     print(json.dumps(parse_red_cycle_durations_from_log(log)))
     "
     ```

     Capture JSON list as `<red_durations>`.

  3. Run the following Bash step to build tuning proposals:

     ```bash
     python3 -c "
     import sys, json; sys.path.insert(0, 'hooks')
     from hooks.utils_self_tuning import build_tuning_proposals
     from pathlib import Path
     config = json.loads(Path('zie-framework/.config').read_text())
     red_durations = json.loads('<red_durations_json>')
     recent_log = '''<git_log_oneline_20>'''
     proposals = build_tuning_proposals(config, red_durations, recent_log)
     print(json.dumps(proposals))
     "
     ```

     Capture JSON list as `<proposals>`. (`<git_log_oneline_20>` = output of `git log --oneline -20`.)

  4. If `proposals == []` → print `"Self-tuning: no changes proposed"` and continue.
  5. Otherwise print diff-style summary:

     ```
     [zie-framework] Self-tuning proposals:
       <key>: <from_val> → <to_val>  (<reason>)
       ...
     Apply? Type "apply" to write to .config, or skip.
     ```

  6. Wait for user input:
     - `"apply"` → write updated `.config` atomically (merge proposals into existing config); print `"Self-tuning: applied N change(s) to .config"`
     - Any other input → print `"Self-tuning: no changes applied"` and continue
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify `utils_self_tuning.py` is covered by `hooks/*.py` in `IMPL_PATTERNS`. Confirm `build_tuning_proposals` docstring matches the spec's two thresholds (2-day single-cycle for Stop nudge vs 3-day average for retro proposal).

  Run: `make test-unit` — still PASS

---

## Task 5: Integration — verify all new code paths green

<!-- depends_on: Task 1, Task 2, Task 3, Task 4 -->

**Acceptance Criteria:**
- `make test-unit` passes with all new test files collected and green
- `make lint` passes with no new violations
- All graceful degradation paths verified: missing `.coverage`, missing ROADMAP, missing `.config`, empty backlog dir
- No regression in existing `test_stop_guard.py` tests

**Files:**
- No new files. Runs existing test suite.

- [ ] **Step 1: Run full test suite**

  ```bash
  make test-unit
  ```

  Expected: all tests pass, including new test files:
  - `tests/unit/test_utils_roadmap_with_dates.py`
  - `tests/unit/test_nudges_stop_guard.py`
  - `tests/unit/test_backlog_intelligence.py`
  - `tests/unit/test_retro_self_tuning.py`

- [ ] **Step 2: Run lint**

  ```bash
  make lint
  ```

  Expected: exit 0, no new violations.

- [ ] **Step 3: Smoke-test graceful degradation**

  Manually verify (or add assertions to existing tests) that:
  - `stop-guard.py` exits 0 when `zie-framework/ROADMAP.md` is missing (no stale nudge)
  - `stop-guard.py` exits 0 when `.coverage` is missing but `tests/` also absent (no nudge)
  - `utils_backlog.infer_tag("")` returns `"feature"` (empty title edge case)
  - `utils_self_tuning.build_tuning_proposals({}, [], "")` returns `[]` (no config edge case)

  Run: `make test-unit` — still PASS

---

## Parallel Execution Plan

```
[Task 1] utils_roadmap.py helper
    ↓
[Task 2] stop-guard.py nudges  ←→  [Task 3] /zie-backlog  ←→  [Task 4] /zie-retro
    ↓                                       ↓                           ↓
                        [Task 5] Full suite green + lint
```

- Task 1 must complete before Task 2 (Task 2 imports `parse_roadmap_items_with_dates`)
- Tasks 3 and 4 are independent and can run in parallel with Task 2
- Task 5 depends on all prior tasks
