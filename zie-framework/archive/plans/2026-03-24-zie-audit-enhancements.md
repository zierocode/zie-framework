---
approved: false
approved_at: ~
backlog: backlog/zie-audit-enhancements.md
spec: specs/2026-03-24-zie-audit-enhancements-design.md
---

# /zie-audit Enhancements — Hard Data + Historical Diff + Auto-Fix — Implementation Plan

**Goal:** Add four targeted enhancements to `commands/zie-audit.md`: hard-data tool runs in Phase 1, historical diff after synthesis, version-specific research queries in Phase 3, and auto-fix offer after backlog selection.
**Architecture:** All changes are prose edits to a single Markdown command file. No new files, no new hooks. Tests assert `Path.read_text()` patterns against the modified file.
**Tech Stack:** Markdown (command definition), pytest (pattern assertions)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-audit.md` | Add hard-data block (Phase 1), historical diff step (post-synthesis), version-specific queries (Phase 3), auto-fix offer (post-backlog) |
| Create | `tests/unit/test_zie_audit_enhancements.py` | Assert all four enhancement patterns are present in commands/zie-audit.md |

---

## Task 1: Hard data tools in Phase 1 (`pytest --cov`, `radon cc`, `pip audit`)

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-audit.md` Phase 1 contains a "Hard Data" block that runs `pytest --cov`, `radon cc`, and `pip audit` (or `npm audit`) via `Bash`
- Output of each tool is stored in a named variable and passed to Agent C (coverage/complexity) and Agent A (CVEs) in Phase 2
- Block is conditional: runs only when tools are available; skips gracefully with a note if missing
- All existing Phase 1 prose and `research_profile` structure are preserved

**Files:**
- Modify: `commands/zie-audit.md`
- Create: `tests/unit/test_zie_audit_enhancements.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_audit_enhancements.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"


  def read_audit() -> str:
      return (COMMANDS_DIR / "zie-audit.md").read_text()


  class TestHardDataPhase1:
      def test_pytest_cov_present(self):
          assert "pytest --cov" in read_audit(), \
              "Phase 1 must include pytest --cov run"

      def test_radon_cc_present(self):
          assert "radon cc" in read_audit(), \
              "Phase 1 must include radon cc run"

      def test_pip_audit_present(self):
          text = read_audit()
          assert "pip audit" in text or "npm audit" in text, \
              "Phase 1 must include pip audit or npm audit run"

      def test_hard_data_feeds_agents(self):
          text = read_audit()
          assert "hard_data" in text, \
              "Phase 1 must define a hard_data variable fed to agents"

      def test_graceful_skip_present(self):
          text = read_audit()
          assert "skip" in text.lower() or "unavailable" in text.lower(), \
              "Hard data block must note graceful skip when tools absent"
  ```
  Run: `make test-unit` — must FAIL (patterns not yet present)

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md`, insert the following block at the end of Phase 1,
  immediately after the `research_profile` definition block and before Phase 2:

  ```markdown
  ### Hard Data Collection

  Before spawning agents, run toolchain instrumentation to produce hard numbers.
  Store results in `hard_data` and pass to relevant agents in Phase 2.

  ```text
  hard_data = {
    coverage_report: "",   # pytest --cov stdout (% per module)
    complexity_report: "", # radon cc -s stdout (cyclomatic complexity per file)
    vuln_report: "",       # pip audit / npm audit stdout (CVE list)
  }
  ```

  Run each command if the tool is present; skip gracefully with a note if unavailable:

  - **Coverage** (Python): `pytest --cov --cov-report=term-missing -q`
    - If pytest or coverage not installed → set `hard_data.coverage_report = "unavailable"`
  - **Complexity** (Python): `radon cc -s -a .`
    - If radon not installed → set `hard_data.complexity_report = "unavailable"`
  - **Vulnerabilities**:
    - Python: `pip audit` (if pip-audit installed)
    - Node: `npm audit --json` (if package.json present)
    - If neither available → set `hard_data.vuln_report = "unavailable"`

  Pass `hard_data.coverage_report` and `hard_data.complexity_report` to Agent C
  context. Pass `hard_data.vuln_report` to Agent A context. Agents must use these
  numbers directly in their findings rather than estimating from code patterns.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Re-read `commands/zie-audit.md` Phase 1 section. Confirm `research_profile`
  block is unmodified. Confirm hard data block follows it without disrupting the
  section heading hierarchy. Confirm `hard_data` variable name is consistent
  across all references.
  Run: `make test-unit` — still PASS

---

## Task 2: Historical diff step after Phase 4 synthesis

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-audit.md` contains a "Since Last Audit" step positioned after Phase 4 scoring and before Phase 5 report printing
- Step loads the most recent `evidence/audit-*.md` using glob sort, extracts per-dimension scores, diffs them against current scores, and prepends a "Since last audit" section to the report
- When no previous audit exists in `evidence/` the step is skipped silently
- All existing Phase 4 scoring logic is preserved

**Files:**
- Modify: `commands/zie-audit.md`
- Modify: `tests/unit/test_zie_audit_enhancements.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_audit_enhancements.py — add new class

  class TestHistoricalDiff:
      def test_since_last_audit_heading_present(self):
          assert "Since last audit" in read_audit() or \
                 "Since Last Audit" in read_audit(), \
              "Audit must have a 'Since last audit' section"

      def test_evidence_glob_present(self):
          text = read_audit()
          assert "evidence/audit-" in text, \
              "Historical diff must glob evidence/audit-*.md"

      def test_skip_when_no_previous_audit(self):
          text = read_audit()
          assert "no previous audit" in text.lower() or \
                 "skip" in text.lower(), \
              "Historical diff must skip gracefully when no prior audit exists"

      def test_diff_positioned_before_phase5(self):
          text = read_audit()
          diff_pos = text.lower().find("since last audit")
          phase5_pos = text.find("## Phase 5")
          assert diff_pos != -1, "Since last audit section not found"
          assert diff_pos < phase5_pos, \
              "Historical diff must appear before Phase 5"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md`, insert the following block between Phase 4 and
  Phase 5:

  ```markdown
  ## Historical Diff — Since Last Audit

  After scoring, compare against the most recent previous audit:

  1. Glob `zie-framework/evidence/audit-*.md` sorted descending by filename date.
  2. If no previous file exists → skip this section entirely; proceed to Phase 5.
  3. Parse the previous report's dimension score table (lines matching
     `  <Dimension>  XX`) to extract last scores.
  4. For each active dimension compute delta: `current_score − last_score`.
  5. Prepend the following section to the Phase 5 report, immediately after the
     Overall Score line:

  ```text
  Since last audit (<YYYY-MM-DD>)

    Security      +N / -N  (was XX → now XX)
    Lean          +N / -N  (was XX → now XX)
    Quality       +N / -N  (was XX → now XX)
    Docs          +N / -N  (was XX → now XX)
    Architecture  +N / -N  (was XX → now XX)
    ...

  Improved: N dimensions  |  Regressed: N dimensions  |  Unchanged: N
  ```

  If parsing fails for any dimension (format mismatch) → show "N/A" for that row.
  Never block Phase 5 due to historical diff errors.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Re-read Phase 4 scoring block and the new historical diff block. Confirm Phase 4
  ends with the overall score formula and the diff block begins immediately after.
  Confirm Phase 5 heading follows the diff block without extra blank sections.
  Run: `make test-unit` — still PASS

---

## Task 3: Version-specific research queries in Phase 3

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-audit.md` Phase 3 query-building block extracts top 10 pinned deps with versions from `research_profile.deps`
- For each dep, a version-specific query is added: `"<dep> <version> CVE"` and `"<dep> <version> security"`
- Version-specific queries are appended to the existing generic queries list — generic queries are preserved unchanged
- Cap note is updated to account for the additional queries (or dep loop is capped internally)

**Files:**
- Modify: `commands/zie-audit.md`
- Modify: `tests/unit/test_zie_audit_enhancements.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_audit_enhancements.py — add new class

  class TestVersionSpecificQueries:
      def test_version_specific_query_block_present(self):
          text = read_audit()
          assert "version" in text and "CVE" in text, \
              "Phase 3 must include version-specific CVE queries"

      def test_deps_loop_present(self):
          text = read_audit()
          assert "research_profile.deps" in text or \
                 "for dep" in text, \
              "Phase 3 must loop over research_profile.deps for version queries"

      def test_version_query_format(self):
          text = read_audit()
          assert "{dep}" in text and "{version}" in text or \
                 "<dep>" in text and "<version>" in text, \
              "Phase 3 must interpolate dep name and version into queries"

      def test_generic_queries_preserved(self):
          text = read_audit()
          # Existing generic queries must still be present
          assert "best practices" in text, \
              "Existing generic best-practices queries must be preserved"
          assert "security vulnerabilities checklist" in text, \
              "Existing security checklist queries must be preserved"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md` Phase 3, insert the following block immediately
  after the existing `queries += ["OpenSSF best practices scorecard criteria", ...]`
  lines and before the `Run WebSearch` instruction:

  ```text
  # Dependency version-specific queries (first 10 deps from manifest)
  top_deps = first 10 entries from research_profile.deps
  for each dep, version in top_deps:
      if version is not empty:
          add "{dep} {version} CVE" to queries
          add "{dep} {version} security vulnerability" to queries
  ```

  Also update the cap comment from `cap at 15 queries` to:

  ```markdown
  Run `WebSearch` for each query (cap at 25 queries total to keep latency
  manageable; generic queries run first, version-specific queries fill remaining
  slots).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Re-read the full Phase 3 query block. Confirm all original query groups
  (language standards, framework guides, domain-specific, OSS/supply chain) are
  intact. Confirm the dep loop and cap update are the only additions. Confirm
  no duplicate query groups were introduced.
  Run: `make test-unit` — still PASS

---

## Task 4: Auto-fix offer after backlog selection

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-audit.md` Phase 5, after backlog items are written to `backlog/` and ROADMAP, contains an auto-fix offer step
- Offer applies only to findings with severity Low or Medium AND tagged `auto-fixable: true` in their metadata
- Offer is skipped silently if no auto-fixable findings exist in the selected set
- High and Critical findings are explicitly excluded from auto-fix
- Auto-fix invokes `/zie-fix` (or equivalent inline fix loop) for each qualifying finding, one at a time, with user confirmation per finding

**Files:**
- Modify: `commands/zie-audit.md`
- Modify: `tests/unit/test_zie_audit_enhancements.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_zie_audit_enhancements.py — add new class

  class TestAutoFixOffer:
      def test_auto_fix_section_present(self):
          text = read_audit()
          assert "auto-fix" in text.lower() or "auto_fix" in text.lower(), \
              "Phase 5 must contain an auto-fix offer section"

      def test_auto_fix_scoped_to_low_medium(self):
          text = read_audit()
          assert "Low" in text and "Medium" in text, \
              "Auto-fix offer must reference Low and Medium severity"
          assert "High" in text and "Critical" in text, \
              "Auto-fix offer must explicitly exclude High and Critical"

      def test_auto_fixable_tag_referenced(self):
          text = read_audit()
          assert "auto-fixable" in text, \
              "Auto-fix offer must check for auto-fixable tag on findings"

      def test_auto_fix_positioned_after_backlog_write(self):
          text = read_audit()
          backlog_pos = text.find("zie-framework/backlog/")
          autofix_pos = text.lower().find("auto-fix")
          assert backlog_pos != -1, "Backlog write section not found"
          assert autofix_pos != -1, "Auto-fix section not found"
          assert autofix_pos > backlog_pos, \
              "Auto-fix offer must appear after backlog items are written"

      def test_skip_when_no_auto_fixable(self):
          text = read_audit()
          assert "skip" in text.lower() or "none" in text.lower(), \
              "Auto-fix section must skip gracefully when no qualifying findings"
  ```
  Run: `make test-unit` — must FAIL

- [ ] **Step 2: Implement (GREEN)**
  In `commands/zie-audit.md` Phase 5, append the following block immediately
  after the ROADMAP update step and before the closing Notes section:

  ```markdown
  ### Auto-Fix Offer

  After writing backlog items, scan the selected findings for auto-fixable candidates:

  ```text
  auto_fixable = [f for f in selected_findings
                  if f.severity in ("Low", "Medium")
                  and f.get("auto-fixable") is True]
  ```

  - If `auto_fixable` is empty → skip this section entirely.
  - High and Critical findings are never offered for auto-fix — they require
    deliberate SDLC treatment.

  For each qualifying finding, present:

  ```text
  Auto-fix available: [Dimension] <description> (Low/Medium)
  Apply fix now? (y/n)
  ```

  On "y":
  - Invoke `/zie-fix` with the finding description and file location as context.
  - Report result ("Fixed" or "Needs manual review") before offering the next item.

  On "n" → skip to the next item.

  After all items are processed (or skipped), close the audit session normally.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**
  Re-read the full Phase 5 section. Confirm backlog write logic (create
  `backlog/<slug>.md`, update ROADMAP) is intact before the auto-fix block.
  Confirm the auto-fix block is the last substantive step before the Notes section.
  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-audit.md tests/unit/test_zie_audit_enhancements.py && git commit -m "feat: zie-audit-enhancements"`*
