---
approved: true
approved_at: 2026-03-24
backlog: backlog/skills-advanced-features.md
spec: specs/2026-03-24-skills-advanced-features-design.md
---

# Skills Advanced Features — Implementation Plan

**Goal:** Add `$ARGUMENTS[N]` indexed-argument documentation to spec-design and write-plan skills, add `argument-hint:` frontmatter to all skills, and create `skills/zie-audit/` with a supporting `reference.md` extracted from the zie-audit command's reference content.
**Architecture:** Three independent SKILL.md edits (Tasks 1–3) followed by one new-file creation task (Task 4) and a test suite (Task 5). No hook scripts, no hooks.json, no command files are touched. All changes are in `skills/*/SKILL.md` and `tests/unit/test_skills_advanced_features.py`.
**Tech Stack:** Python 3.x, pytest, stdlib only

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `skills/spec-design/SKILL.md` | Add `argument-hint:` frontmatter; document `$ARGUMENTS[0]` as slug, `$ARGUMENTS[1]` as mode |
| Modify | `skills/write-plan/SKILL.md` | Add `argument-hint:` frontmatter; document `$ARGUMENTS[0]` as slug, `$ARGUMENTS[1]` as optional flags |
| Modify | `skills/spec-reviewer/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/plan-reviewer/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/impl-reviewer/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/debug/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/tdd-loop/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/verify/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/retro-format/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Modify | `skills/test-pyramid/SKILL.md` | Add `argument-hint:` frontmatter (no args — explicit empty) |
| Create | `skills/zie-audit/SKILL.md` | New zie-audit skill entry point (< 500 lines) |
| Create | `skills/zie-audit/reference.md` | Supporting file: dimension definitions, scoring rubric, query template library |
| Create | `tests/unit/test_skills_advanced_features.py` | All tests for this feature set |

---

## Task 1: Add `$ARGUMENTS[N]` documentation to spec-design and write-plan SKILL.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-design/SKILL.md` frontmatter contains `argument-hint:` with a quoted value listing `<slug> [full|quick]`
- `skills/spec-design/SKILL.md` documents `$ARGUMENTS[0]` as the backlog slug and `$ARGUMENTS[1]` as the mode hint (`full|quick`), with explicit defaults when absent
- `skills/write-plan/SKILL.md` frontmatter contains `argument-hint:` with a quoted value listing `<slug> [--no-memory]`
- `skills/write-plan/SKILL.md` documents `$ARGUMENTS[0]` as slug and `$ARGUMENTS[1]` as optional flags string, with explicit defaults when absent
- Both files document the `${CLAUDE_SKILL_DIR}/scripts/` pattern as a note for future skill authors
- Both files document graceful fallback when `$ARGUMENTS[0]` is absent (prompt user for slug)

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skills_advanced_features.py — initial file, Task 1 tests only

  from pathlib import Path

  ROOT = Path(__file__).parent.parent.parent
  SKILLS = ROOT / "skills"


  def read_skill(name):
      return (SKILLS / name / "SKILL.md").read_text()


  class TestArgumentIndexedDocs:
      def test_spec_design_has_argument_hint_frontmatter(self):
          content = read_skill("spec-design")
          assert "argument-hint:" in content, \
              "spec-design/SKILL.md must have argument-hint: in frontmatter"

      def test_spec_design_documents_arguments_0_as_slug(self):
          content = read_skill("spec-design")
          assert "$ARGUMENTS[0]" in content, \
              "spec-design/SKILL.md must document $ARGUMENTS[0] as slug"

      def test_spec_design_documents_arguments_1_as_mode(self):
          content = read_skill("spec-design")
          assert "$ARGUMENTS[1]" in content, \
              "spec-design/SKILL.md must document $ARGUMENTS[1] as mode"

      def test_spec_design_documents_mode_values(self):
          content = read_skill("spec-design")
          assert "full" in content and "quick" in content, \
              "spec-design/SKILL.md must document full and quick mode values"

      def test_spec_design_documents_absent_arg_fallback(self):
          content = read_skill("spec-design")
          assert "absent" in content or "fallback" in content or "default" in content, \
              "spec-design/SKILL.md must document default behaviour when args are absent"

      def test_write_plan_has_argument_hint_frontmatter(self):
          content = read_skill("write-plan")
          assert "argument-hint:" in content, \
              "write-plan/SKILL.md must have argument-hint: in frontmatter"

      def test_write_plan_documents_arguments_0_as_slug(self):
          content = read_skill("write-plan")
          assert "$ARGUMENTS[0]" in content, \
              "write-plan/SKILL.md must document $ARGUMENTS[0] as slug"

      def test_write_plan_documents_arguments_1_as_flags(self):
          content = read_skill("write-plan")
          assert "$ARGUMENTS[1]" in content, \
              "write-plan/SKILL.md must document $ARGUMENTS[1] as optional flags"

      def test_write_plan_documents_absent_arg_fallback(self):
          content = read_skill("write-plan")
          assert "absent" in content or "fallback" in content or "default" in content, \
              "write-plan/SKILL.md must document default behaviour when args are absent"

      def test_spec_design_documents_skill_dir_pattern(self):
          content = read_skill("spec-design")
          assert "CLAUDE_SKILL_DIR" in content, \
              "spec-design/SKILL.md must document ${CLAUDE_SKILL_DIR}/scripts/ pattern"

      def test_write_plan_documents_skill_dir_pattern(self):
          content = read_skill("write-plan")
          assert "CLAUDE_SKILL_DIR" in content, \
              "write-plan/SKILL.md must document ${CLAUDE_SKILL_DIR}/scripts/ pattern"
  ```

  Run: `make test-unit` — must FAIL (no `argument-hint:` or `$ARGUMENTS[N]` in current SKILL.md files)

- [ ] **Step 2: Implement (GREEN)**

  Edit `skills/spec-design/SKILL.md`:

  1. In the frontmatter block, add after the `description:` line:
     ```yaml
     argument-hint: "<slug> [full|quick]"
     ```

  2. Add a new section immediately after the opening description paragraph and before `## เตรียม context`:
     ```markdown
     ## Arguments

     | Position | Variable | Description | Default |
     | --- | --- | --- | --- |
     | 0 | `$ARGUMENTS[0]` | Backlog slug (e.g. `my-feature`) | absent → prompt user for slug |
     | 1 | `$ARGUMENTS[1]` | Mode: `full` (full dialogue) or `quick` (skip clarification, draft directly) | absent/empty → `full` |

     When `$ARGUMENTS[0]` is absent, fall back to listing the backlog menu and
     prompting the user to choose — matching the behaviour of `/zie-spec` with no
     argument.

     When `$ARGUMENTS[1]` is absent or empty, default to `full` mode. Never raise
     an error for a missing second argument.

     > **Note for future skill authors:** if this skill bundles helper scripts,
     > reference them via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — Claude Code
     > resolves this to the skill's own directory regardless of CWD.
     ```

  Edit `skills/write-plan/SKILL.md`:

  1. In the frontmatter block, add after the `description:` line:
     ```yaml
     argument-hint: "<slug> [--no-memory]"
     ```

  2. Add a new section immediately after the opening description paragraph and before `## เตรียม context`:
     ```markdown
     ## Arguments

     | Position | Variable | Description | Default |
     | --- | --- | --- | --- |
     | 0 | `$ARGUMENTS[0]` | Backlog slug — used to locate the spec file (`zie-framework/specs/YYYY-MM-DD-<slug>-design.md`) | absent → prompt user for slug |
     | 1 | `$ARGUMENTS[1]` | Optional flags string (e.g. `--no-memory` to skip zie-memory recall) | absent/empty → all defaults apply |

     When `$ARGUMENTS[0]` is absent, prompt the user to provide the slug or select
     from the approved specs in `zie-framework/specs/`. Never block or error.

     When `$ARGUMENTS[1]` is absent or empty, treat as no flags — all default
     behaviour applies. Parse flags by splitting on whitespace and checking for
     known flag names.

     > **Note for future skill authors:** if this skill bundles helper scripts,
     > reference them via `${CLAUDE_SKILL_DIR}/scripts/<script-name>` — Claude Code
     > resolves this to the skill's own directory regardless of CWD.
     ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review both SKILL.md files for formatting consistency:
  - Ensure the `## Arguments` section uses the same table column order in both files.
  - Ensure the `${CLAUDE_SKILL_DIR}` note uses a blockquote (`>`) consistently in both.
  - No content changes — only whitespace/formatting alignment.

  Run: `make test-unit` — still PASS

---

## Task 2: Add `argument-hint:` frontmatter to all remaining skills

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/spec-reviewer/SKILL.md`, `skills/plan-reviewer/SKILL.md`, `skills/impl-reviewer/SKILL.md`, `skills/debug/SKILL.md`, `skills/tdd-loop/SKILL.md`, `skills/verify/SKILL.md`, `skills/retro-format/SKILL.md`, and `skills/test-pyramid/SKILL.md` each contain `argument-hint:` in their frontmatter
- Skills with no meaningful user-facing arguments have `argument-hint: ""` (empty string, explicit)
- No existing skill content is modified — only the frontmatter block changes

**Files:**
- Modify: `skills/spec-reviewer/SKILL.md`
- Modify: `skills/plan-reviewer/SKILL.md`
- Modify: `skills/impl-reviewer/SKILL.md`
- Modify: `skills/debug/SKILL.md`
- Modify: `skills/tdd-loop/SKILL.md`
- Modify: `skills/verify/SKILL.md`
- Modify: `skills/retro-format/SKILL.md`
- Modify: `skills/test-pyramid/SKILL.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skills_advanced_features.py — append to existing file

  class TestArgumentHintFrontmatter:
      NO_ARG_SKILLS = [
          "spec-reviewer",
          "plan-reviewer",
          "impl-reviewer",
          "debug",
          "tdd-loop",
          "verify",
          "retro-format",
          "test-pyramid",
      ]

      def test_all_no_arg_skills_have_argument_hint(self):
          for skill in self.NO_ARG_SKILLS:
              content = read_skill(skill)
              assert "argument-hint:" in content, \
                  f"skills/{skill}/SKILL.md must have argument-hint: in frontmatter"

      def test_no_arg_skills_hint_is_empty_string(self):
          """Skills with no user-facing args must set argument-hint to empty string,
          not leave it absent. This makes intent explicit."""
          for skill in self.NO_ARG_SKILLS:
              content = read_skill(skill)
              # must have argument-hint: "" or argument-hint: '' or argument-hint:
              # followed immediately by newline (bare empty)
              assert 'argument-hint: ""' in content \
                  or "argument-hint: ''" in content \
                  or "argument-hint:\n" in content, \
                  f"skills/{skill}/SKILL.md argument-hint must be empty string (not absent)"

      def test_all_skills_have_argument_hint(self):
          """Every skill directory must have argument-hint: — including the two
          updated in Task 1."""
          all_skills = [d.name for d in SKILLS.iterdir() if (d / "SKILL.md").exists()]
          for skill in all_skills:
              content = read_skill(skill)
              assert "argument-hint:" in content, \
                  f"skills/{skill}/SKILL.md must have argument-hint: in frontmatter"
  ```

  Run: `make test-unit` — must FAIL (8 skills missing `argument-hint:`)

- [ ] **Step 2: Implement (GREEN)**

  For each of the 8 skills, add `argument-hint: ""` to the frontmatter.
  Each file has a different frontmatter structure; insert after the last existing
  frontmatter key, before the closing `---`.

  `skills/spec-reviewer/SKILL.md` — current frontmatter ends with `description: ...`:
  ```yaml
  argument-hint: ""
  ```

  `skills/plan-reviewer/SKILL.md` — same pattern:
  ```yaml
  argument-hint: ""
  ```

  `skills/impl-reviewer/SKILL.md` — same pattern:
  ```yaml
  argument-hint: ""
  ```

  `skills/debug/SKILL.md` — frontmatter ends with `zie_memory_enabled: true` under `metadata:`:
  ```yaml
  argument-hint: ""
  ```
  (Add at top-level, after `metadata:` block, before closing `---`)

  `skills/tdd-loop/SKILL.md` — frontmatter ends with `type: process`:
  ```yaml
  argument-hint: ""
  ```

  `skills/verify/SKILL.md` — frontmatter ends with `zie_memory_enabled: true` under `metadata:`:
  ```yaml
  argument-hint: ""
  ```

  `skills/retro-format/SKILL.md` — frontmatter ends with `type: reference`:
  ```yaml
  argument-hint: ""
  ```

  `skills/test-pyramid/SKILL.md` — frontmatter ends with `type: reference`:
  ```yaml
  argument-hint: ""
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Verify that for skills with a `metadata:` sub-block (`debug`, `verify`), the
  `argument-hint:` key is at the top YAML level (same indentation as `name:`,
  `description:`), not nested inside `metadata:`. If misplaced, correct indentation.

  Run: `make test-unit` — still PASS

---

## Task 3: Create `skills/zie-audit/` with SKILL.md and reference.md

<!-- depends_on: none -->

**Acceptance Criteria:**
- `skills/zie-audit/SKILL.md` exists and is under 500 lines
- `skills/zie-audit/SKILL.md` contains `argument-hint: "[--focus <dimension>]"` in frontmatter
- `skills/zie-audit/SKILL.md` contains `Skill(zie-framework:zie-audit)` as the invocation pattern (for command wiring documentation)
- `skills/zie-audit/SKILL.md` covers all 9 dimensions by name
- `skills/zie-audit/SKILL.md` explicitly reads `${CLAUDE_SKILL_DIR}/reference.md` in its steps with a graceful-skip note
- `skills/zie-audit/reference.md` exists
- `skills/zie-audit/reference.md` contains dimension definitions, scoring rubric (start-at-100, Critical/High/Medium/Low deductions), and query template library structure
- `commands/zie-audit.md` is NOT modified

**Files:**
- Create: `skills/zie-audit/SKILL.md`
- Create: `skills/zie-audit/reference.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skills_advanced_features.py — append to existing file

  class TestZieAuditSkill:
      SKILL_PATH = SKILLS / "zie-audit" / "SKILL.md"
      REF_PATH = SKILLS / "zie-audit" / "reference.md"

      def test_skill_file_exists(self):
          assert self.SKILL_PATH.exists(), \
              "skills/zie-audit/SKILL.md must exist"

      def test_reference_file_exists(self):
          assert self.REF_PATH.exists(), \
              "skills/zie-audit/reference.md must exist"

      def test_skill_under_500_lines(self):
          lines = self.SKILL_PATH.read_text().splitlines()
          assert len(lines) < 500, \
              f"skills/zie-audit/SKILL.md must be under 500 lines (got {len(lines)})"

      def test_skill_has_argument_hint(self):
          content = self.SKILL_PATH.read_text()
          assert "argument-hint:" in content, \
              "skills/zie-audit/SKILL.md must have argument-hint: in frontmatter"

      def test_skill_argument_hint_includes_focus(self):
          content = self.SKILL_PATH.read_text()
          assert "--focus" in content, \
              "skills/zie-audit/SKILL.md argument-hint must document --focus flag"

      def test_skill_covers_all_9_dimensions(self):
          content = self.SKILL_PATH.read_text()
          dimensions = [
              "Security", "Lean", "Quality", "Docs", "Architecture",
              "Performance", "Depend", "Developer", "Standards",
          ]
          for dim in dimensions:
              assert dim in content, \
                  f"skills/zie-audit/SKILL.md must reference the {dim} dimension"

      def test_skill_reads_reference_md_via_skill_dir(self):
          content = self.SKILL_PATH.read_text()
          assert "CLAUDE_SKILL_DIR" in content, \
              "skills/zie-audit/SKILL.md must reference ${CLAUDE_SKILL_DIR}/reference.md"
          assert "reference.md" in content, \
              "skills/zie-audit/SKILL.md must explicitly read reference.md"

      def test_skill_has_graceful_skip_for_reference(self):
          content = self.SKILL_PATH.read_text()
          assert "graceful" in content.lower() or "not found" in content.lower() \
              or "skip" in content.lower(), \
              "skills/zie-audit/SKILL.md must document graceful skip if reference.md is missing"

      def test_reference_has_scoring_rubric(self):
          content = self.REF_PATH.read_text()
          assert "100" in content, \
              "reference.md must document the start-at-100 scoring system"
          assert "Critical" in content and "High" in content, \
              "reference.md must document Critical and High severity deductions"

      def test_reference_has_dimension_definitions(self):
          content = self.REF_PATH.read_text()
          dimensions = ["Security", "Lean", "Quality", "Docs", "Architecture"]
          for dim in dimensions:
              assert dim in content, \
                  f"reference.md must define the {dim} dimension"

      def test_reference_has_query_template_section(self):
          content = self.REF_PATH.read_text()
          assert "query" in content.lower() or "queries" in content.lower(), \
              "reference.md must contain a query template library section"

      def test_zie_audit_command_unchanged(self):
          """commands/zie-audit.md must not be modified — it stays as-is."""
          cmd_path = ROOT / "commands" / "zie-audit.md"
          content = cmd_path.read_text()
          # Command still owns Phase 1-5 logic; skill does not duplicate it
          assert "Phase 1" in content and "Phase 5" in content, \
              "commands/zie-audit.md must retain all 5 phases unchanged"
  ```

  Run: `make test-unit` — must FAIL (`skills/zie-audit/` does not exist)

- [ ] **Step 2: Implement (GREEN)**

  Create `skills/zie-audit/SKILL.md`:

  ```markdown
  ---
  name: zie-audit
  description: Deep project audit — 9-dimension analysis with external research. Produces scored findings for backlog.
  argument-hint: "[--focus <dimension>]"
  metadata:
    zie_memory_enabled: false
  ---

  # zie-audit — Deep Project Audit

  Systematic 9-dimension analysis: internal codebase scan + external research.
  Produces a scored report and feeds selected findings into the backlog.

  Invoked by: `Skill(zie-framework:zie-audit)` from `/zie-audit`.

  ## Arguments

  | Position | Variable | Description | Default |
  | --- | --- | --- | --- |
  | 0 | `$ARGUMENTS[0]` | Optional `--focus <dimension>` flag | absent → full 9-dimension audit |

  When `--focus <dimension>` is provided: Phase 2 runs only the matching agent;
  Phase 3 researches only that dimension (deeply). All other phases run normally.

  ## Pre-flight

  1. Check `zie-framework/` exists — if not, tell user to run `/zie-init` first.
  2. Read `zie-framework/.config` → project name, project_type, test_runner, has_frontend.
  3. Read `zie-framework/PROJECT.md` → tech stack, description.

  ## Load Reference Material

  Read `${CLAUDE_SKILL_DIR}/reference.md` for:
  - Dimension definitions and what each agent checks
  - Scoring rubric (start-at-100, per-severity deductions)
  - Query template library for Phase 3

  If `${CLAUDE_SKILL_DIR}/reference.md` is not found, proceed without it — use
  built-in knowledge for dimension definitions and scoring. Note the gap in the
  audit report header. Never block the audit.

  ## Phase 1 — Project Intelligence

  Build `research_profile` (languages, frameworks, domain, deps, project_type,
  test_runner, has_frontend, deployment, special_ctx). Detect from:
  `requirements.txt`, `pyproject.toml`, `package.json`, `go.mod`, `Cargo.toml`,
  `Dockerfile`, `docker-compose.yml`, `.config`, source files.

  ## Phase 2 — Parallel Internal Analysis

  Spawn 5 parallel agents via `Agent` tool. Each receives `research_profile`.

  - **Agent A — Security**: secrets, shell injection, input validation, auth,
    error leakage, outdated deps with CVE hints
  - **Agent B — Lean / Efficiency**: dead code, duplicated logic, over-engineering,
    unnecessary dependencies
  - **Agent C — Quality / Testing**: untested modules, fragile tests, weak
    assertions, missing edge cases, TODO/FIXME count
  - **Agent D — Documentation**: stale references, missing docs, broken examples,
    README completeness, CHANGELOG/VERSION sync
  - **Agent E — Architecture**: high coupling, SRP violations, inconsistent
    patterns, silent failures

  Sub-checks distributed across agents: Performance (B/E), Dependency Health (A/C),
  Developer Experience (D), Standards compliance (E).

  Each agent returns: `[{severity, dimension, description, location, effort}]`

  ## Phase 3 — Dynamic External Research

  Build query list from `research_profile` using the query template library in
  `reference.md`. Cap at 15 queries. Run `WebSearch` per query; use `WebFetch`
  for high-value results. Skip failed queries gracefully — note in report.

  Synthesize into `external_standards_report`:
  each dimension → `[{standard, finding, severity}]`

  ## Phase 4 — Synthesis

  Cross-reference Phase 2 + Phase 3. Bump severity one level for findings present
  in both (external validation = higher confidence). Deduplicate. Score each
  dimension using the rubric in `reference.md`. Compute weighted overall score.

  ## Phase 5 — Report + Backlog Selection

  Print scored report (Overall Score, 9 dimension scores, findings by severity).
  Save to `zie-framework/evidence/audit-YYYY-MM-DD.md` (gitignored).

  Prompt: `Add to backlog: enter numbers, "high", "all", or "none"`

  For each selected finding: create `zie-framework/backlog/<slug>.md` and add to
  `zie-framework/ROADMAP.md` Next lane.

  ## Notes

  - Always deep — no quick mode; external research always runs
  - Typical runtime: 3–8 minutes (parallel agents + web research)
  - Evidence saved to `zie-framework/evidence/` — never committed
  ```

  Create `skills/zie-audit/reference.md`:

  ```markdown
  # zie-audit — Reference Material

  Supporting file for `skills/zie-audit/SKILL.md`. Read via
  `${CLAUDE_SKILL_DIR}/reference.md` during the audit. Never auto-injected.

  ---

  ## Dimension Definitions

  | Dimension | What it covers |
  | --- | --- |
  | Security | Secrets, injection, input validation, auth/authz, error leakage, CVE hints |
  | Lean | Dead code, duplicated logic, over-engineering, unnecessary dependencies |
  | Quality | Test coverage, fragile tests, weak assertions, edge-case gaps, TODO/FIXME debt |
  | Docs | Stale references, missing docs, broken examples, README completeness, CHANGELOG sync |
  | Architecture | Coupling, SRP violations, inconsistent patterns, silent failures |
  | Performance | Hot-path I/O, caching gaps, blocking operations, N+1 query patterns |
  | Dependencies | Outdated packages, license compatibility, abandoned libraries |
  | Developer Exp | Output clarity, error messages, onboarding friction, local setup steps |
  | Standards | semver, conventional commits, OpenSSF scorecard, SLSA supply chain levels |

  ---

  ## Scoring Rubric

  Each dimension starts at **100**.

  | Severity | Score deduction per finding |
  | --- | --- |
  | Critical | −15 |
  | High | −8 |
  | Medium | −3 |
  | Low | −1 |

  Floor: 0 (a dimension cannot go below 0).

  **Overall score** = weighted average across all active dimensions (equal weight
  unless `--focus` is used, in which case only the focused dimension is scored).

  **Severity bump rule:** a finding present in both the internal scan (Phase 2)
  and an external standard (Phase 3) is bumped one severity level upward
  (Low → Medium → High → Critical). This reflects external validation confidence.

  ---

  ## Query Template Library

  Build the Phase 3 query list dynamically from `research_profile`. Templates:

  ### Language / Runtime

  ```text
  "{lang} best practices 2026"
  "{lang} security vulnerabilities checklist"
  ```

  ### Framework-Specific

  ```text
  "{fw} security guide"
  "{fw} performance anti-patterns"
  ```

  ### Domain-Specific

  | Domain / Context | Queries to add |
  | --- | --- |
  | `claude-code-plugin` | "claude code plugin development best practices", "claude code hooks security patterns" |
  | `public-api` in special_ctx | "REST API design standards OpenAPI 2026" |
  | `handles-payments` in special_ctx | "PCI DSS compliance checklist developer" |
  | `processes-pii` in special_ctx | "GDPR technical implementation checklist" |

  ### OSS + Supply Chain (always included)

  ```text
  "OpenSSF best practices scorecard criteria"
  "SLSA supply chain security levels"
  "{project_type} github stars:>100 architecture patterns"
  ```

  **Cap:** 15 queries total. Prioritise language + framework + domain queries.
  Drop OSS/supply-chain queries last if over cap.

  ---

  ## Finding Format

  Each finding from Phase 2 agents:

  ```python
  {
    "severity": "Critical|High|Medium|Low",
    "dimension": "<dimension name>",
    "description": "<specific issue — what and where>",
    "location": "<file:line or module>",
    "effort": "XS|S|M|L"
  }
  ```

  Each finding from Phase 3 external research:

  ```python
  {
    "standard": "<standard name, e.g. OpenSSF>",
    "finding": "<gap description>",
    "severity": "Critical|High|Medium|Low"
  }
  ```
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review `skills/zie-audit/SKILL.md` line count:

  ```bash
  wc -l skills/zie-audit/SKILL.md
  ```

  Must be under 500. If over, extract any remaining prose reference sections into
  `reference.md`. Confirm the graceful-skip note for `reference.md` is present and
  clear. Check that `commands/zie-audit.md` was not touched (`git diff
  commands/zie-audit.md` must be empty).

  Run: `make test-unit` — still PASS

---

## Task 4: Add 500-line guard and SKILL_DIR reference tests

<!-- depends_on: Task 1, Task 2, Task 3 -->

**Acceptance Criteria:**
- A line-count guard test fails CI if any `SKILL.md` exceeds 500 lines
- A SKILL_DIR reference test confirms `zie-audit/SKILL.md` uses `${CLAUDE_SKILL_DIR}`
- All previously passing tests still pass

**Files:**
- Modify: `tests/unit/test_skills_advanced_features.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_skills_advanced_features.py — append to existing file

  class TestSkillFileSizeGuard:
      def test_no_skill_md_exceeds_500_lines(self):
          """Line-count guard: keeps SKILL.md files lean and forces extraction
          of large reference sections into supporting files."""
          oversized = []
          for skill_dir in SKILLS.iterdir():
              skill_file = skill_dir / "SKILL.md"
              if skill_file.exists():
                  lines = skill_file.read_text().splitlines()
                  if len(lines) >= 500:
                      oversized.append(f"{skill_dir.name}/SKILL.md ({len(lines)} lines)")
          assert not oversized, \
              "These SKILL.md files exceed 500 lines — extract reference content: " \
              + ", ".join(oversized)


  class TestSkillDirReferencePattern:
      def test_zie_audit_uses_claude_skill_dir(self):
          content = read_skill("zie-audit")
          assert "${CLAUDE_SKILL_DIR}" in content, \
              "skills/zie-audit/SKILL.md must use ${CLAUDE_SKILL_DIR} to reference supporting files"

      def test_zie_audit_reference_md_is_loaded_explicitly(self):
          """The skill must explicitly read reference.md — it is never auto-injected."""
          content = read_skill("zie-audit")
          assert "reference.md" in content, \
              "skills/zie-audit/SKILL.md must explicitly name reference.md in its steps"
  ```

  Run: `make test-unit` — these tests should PASS immediately if Tasks 1–3 are
  complete. If Task 3 produced a SKILL.md over 500 lines, the guard test fails —
  fix SKILL.md before proceeding.

- [ ] **Step 2: Implement (GREEN)**

  No implementation changes — these tests validate the outputs of Tasks 1–3.
  If any test fails here, return to the relevant task and fix the file.

  Run: `make test-unit` — must PASS across all classes

- [ ] **Step 3: Refactor**

  Consolidate all test classes in `test_skills_advanced_features.py` into a
  coherent order:

  1. `TestArgumentIndexedDocs` (Task 1)
  2. `TestArgumentHintFrontmatter` (Task 2)
  3. `TestZieAuditSkill` (Task 3)
  4. `TestSkillFileSizeGuard` (Task 4)
  5. `TestSkillDirReferencePattern` (Task 4)

  Add a module-level docstring:

  ```python
  """Tests for zie-framework skills advanced features:
  $ARGUMENTS[N] indexed access, argument-hint frontmatter,
  zie-audit skill + reference.md supporting file, SKILL.md size guard.

  Spec: zie-framework/specs/2026-03-24-skills-advanced-features-design.md
  """
  ```

  Run: `make test-unit` — still PASS

---

*Commit: `git add skills/ tests/unit/test_skills_advanced_features.py && git commit -m "feat: skills advanced features — argument-hint frontmatter, indexed args docs, zie-audit skill + reference.md"`*
