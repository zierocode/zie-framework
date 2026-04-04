---
approved: false
approved_at:
backlog: backlog/zie-init-delegate-scan.md
---

# zie-init Delegate Scan to Explore Agent — Implementation Plan

**Goal:** Replace the ~150-line scanning pseudocode in `commands/zie-init.md` Step 2 with a single `Agent(subagent_type=Explore)` call using a self-contained prompt that returns a structured `scan_report` JSON blob.
**Architecture:** The parent command Step 2 shrinks to a compact dispatch block: invoke Explore agent → receive `scan_report` JSON → drive all decisions (draft, review loop, write, hash, migrate) from that blob. All scanning logic moves into the agent prompt, which is self-contained and can run independently of parent context.
**Tech Stack:** Markdown (commands/zie-init.md), Python (tests), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-init.md` | Replace Step 2 scanning pseudocode with compact agent dispatch + `scan_report`-driven sub-steps |
| Modify | `tests/unit/test_zie_init_deep_scan.py` | Update assertions: `migratable_docs` → `migration_candidates`; add assertions for `scan_report` JSON schema fields and `existing_hooks`/`existing_config` strategy keys |
| Modify | `tests/unit/test_commands_zie_init.py` | Existing test file — pipeline summary tests reference content outside Step 2; must remain passing after rewrite |

---

## Task 1: Update tests for new scan_report schema

**Acceptance Criteria:**
- `test_zie_init_deep_scan.py` asserts `migration_candidates` present in `zie-init.md` (replacing `migratable_docs` assertion)
- Tests assert `existing_hooks` and `existing_config` keys are documented in Step 2
- Tests assert `scan_report` JSON parse strategy is documented (bare JSON + `{`…`}` fallback)
- Tests assert failure handling language: "Agent scan incomplete" and "Scan failed" present
- `make test-unit` FAILS (command file not yet updated)

**Files:**
- Modify: `tests/unit/test_zie_init_deep_scan.py`

- [ ] **Step 1: Write failing tests (RED)**

  Replace the ENTIRE `TestZieInitSingleScan` class (lines 46–94 of the current test file) with the updated class below. This removes the three old `migratable_docs`-based tests (`test_explore_agent_prompt_includes_migratable_docs`, `test_migratable_docs_fallback_on_missing_key`, `test_migratable_docs_fallback_on_malformed_json`) and replaces them plus adds new assertions:

  ```python
  class TestZieInitSingleScan:
      def test_explore_agent_prompt_includes_migration_candidates(self):
          content = read("commands/zie-init.md")
          assert "migration_candidates" in content, (
              "Explore agent prompt must request migration_candidates in its output"
          )

      def test_no_standalone_step_2h_directory_rescan(self):
          content = read("commands/zie-init.md")
          import re
          old_rescan_pattern = re.compile(
              r"h\.\s+\*\*Detect migratable documentation\*\*.*scan project root",
              re.DOTALL,
          )
          assert not old_rescan_pattern.search(content), (
              "step 2h must not describe a standalone directory rescan; "
              "migration detection must come from the Explore agent report"
          )

      def test_migration_candidates_fallback_on_missing_key(self):
          content = read("commands/zie-init.md")
          assert "missing" in content.lower() or "fallback" in content.lower() or "skip" in content.lower(), (
              "zie-init must document graceful fallback when migration_candidates "
              "is missing or empty from agent report"
          )

      def test_migration_candidates_fallback_on_malformed_json(self):
          content = read("commands/zie-init.md")
          assert (
              "malformed" in content.lower()
              or "garbled" in content.lower()
              or "Could not detect" in content
              or "graceful" in content.lower()
          ), (
              "zie-init must document graceful degradation when agent returns "
              "malformed JSON or omits migration_candidates"
          )

      def test_agent_prompt_includes_backlog_pattern(self):
          content = read("commands/zie-init.md")
          assert "**/backlog/*.md" in content, (
              "Explore agent prompt must include **/backlog/*.md in migration detection patterns"
          )

      def test_agent_prompt_excludes_zie_framework_dir(self):
          content = read("commands/zie-init.md")
          assert "zie-framework/" in content, (
              "Explore agent must still exclude zie-framework/ from scan"
          )

      def test_scan_report_has_existing_hooks_key(self):
          content = read("commands/zie-init.md")
          assert "existing_hooks" in content, (
              "scan_report must include existing_hooks field for hooks install strategy"
          )

      def test_scan_report_has_existing_config_key(self):
          content = read("commands/zie-init.md")
          assert "existing_config" in content, (
              "scan_report must include existing_config field for config preservation strategy"
          )

      def test_scan_report_json_parse_bare_json(self):
          content = read("commands/zie-init.md")
          assert "json.loads" in content or "bare JSON" in content or "strip()" in content, (
              "zie-init must document bare JSON parse strategy for agent output"
          )

      def test_scan_report_json_parse_fallback_extraction(self):
          content = read("commands/zie-init.md")
          assert 'rindex("}")' in content or "last `}`" in content or "rindex" in content or "first `{`" in content, (
              "zie-init must document fallback JSON extraction (first { to last })"
          )

      def test_step2_line_reduction_marker(self):
          """Step 2 must reference scan_report (compact dispatch) not inline pseudocode."""
          content = read("commands/zie-init.md")
          assert "scan_report" in content, (
              "zie-init Step 2 must reference scan_report returned from agent"
          )

      def test_failure_handling_agent_scan_incomplete(self):
          content = read("commands/zie-init.md")
          assert "Agent scan incomplete" in content or "scan incomplete" in content.lower(), (
              "zie-init must warn 'Agent scan incomplete' on timeout"
          )

      def test_failure_handling_scan_failed(self):
          content = read("commands/zie-init.md")
          assert "Scan failed" in content or "scan failed" in content.lower(), (
              "zie-init must warn 'Scan failed' on non-JSON agent output"
          )

      def test_scan_report_existing_hooks_drives_merge_strategy(self):
          content = read("commands/zie-init.md")
          assert "existing_hooks" in content and "merge" in content.lower(), (
              "zie-init must document that a non-null existing_hooks value drives "
              "a merge strategy for hooks installation (preserve existing handlers)"
          )

      def test_scan_report_existing_config_drives_preserve_strategy(self):
          content = read("commands/zie-init.md")
          assert "existing_config" in content and (
              "preserve" in content.lower() or "user-set" in content.lower()
          ), (
              "zie-init must document that a non-null existing_config value drives "
              "a preserve strategy (read and retain user-set keys before writing)"
          )
  ```

  Run: `make test-unit` — must FAIL (old `migratable_docs` assertion passes but new assertions fail against old command file)

- [ ] **Step 2: Implement (GREEN)**

  Replace the ENTIRE `TestZieInitSingleScan` class (lines 46–94) in `tests/unit/test_zie_init_deep_scan.py` with the updated class above. The three old tests (`test_explore_agent_prompt_includes_migratable_docs`, `test_migratable_docs_fallback_on_missing_key`, `test_migratable_docs_fallback_on_malformed_json`) are removed and replaced by new equivalents plus the two strategy-branch tests.

  Run: `make test-unit` — still FAILS (command file not yet updated — expected)

- [ ] **Step 3: Refactor**

  No refactor needed — test file is clean after replacement.

---

## Task 2: Rewrite zie-init.md Step 2 with compact agent dispatch

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `commands/zie-init.md` Step 2 is reduced by ≥100 lines vs current (current ~150 lines in Step 2; target ≤50)
- Step 2 contains exactly one `Agent(subagent_type=Explore)` invocation with the self-contained prompt from the spec
- Agent prompt includes exact `scan_report` JSON schema (all 10 fields: `architecture_pattern`, `components`, `tech_stack`, `data_flow`, `key_constraints`, `test_strategy`, `active_areas`, `existing_hooks`, `existing_config`, `migration_candidates`)
- Agent prompt is self-contained: no reference to prior context
- Parent command sub-steps 2b–2i remain in the parent, driven by `scan_report`
- `existing_hooks` drives merge vs fresh-write strategy for hooks in 2h
- `existing_config` drives preserve vs fresh-create strategy for config in 2g
- JSON parse strategy documented: bare `json.loads(output.strip())` → fallback `{`…`}` extraction → retry/greenfield fallback
- Failure paths documented: timeout → "Agent scan incomplete" → retry or greenfield; non-JSON → "Scan failed" → retry or greenfield
- All existing passing tests in `test_zie_init_deep_scan.py` and `test_commands_zie_init.py` pass
- `make test-unit` PASSES

**Files:**
- Modify: `commands/zie-init.md`

- [ ] **Step 1: Write failing tests (RED)**

  Task 1 already writes the failing tests. Confirm `make test-unit` fails on the new assertions before editing the command file.

  Run: `make test-unit` — must FAIL (new assertions not yet satisfied)

- [ ] **Step 2: Implement (GREEN)**

  Replace the Step 2 block in `commands/zie-init.md` (lines ~60–211) with the compact version below. Keep everything outside Step 2 unchanged.

  The new Step 2 replaces the current content with:

  ```markdown
  2. **Detect and scan existing project** (if existing — see greenfield
     check at top of step):

     **If existing** → print "Existing project detected. Scanning
     codebase..." then:

     a. Invoke `Agent(subagent_type=Explore)` with the following
        self-contained prompt. Receive `scan_report` JSON.

        > **Explore agent prompt (self-contained — pass verbatim):**
        >
        > ```
        > You are scanning an existing software project to help initialize zie-framework.
        >
        > Scan the project at the current working directory. Read existing documentation
        > first as primary sources (they encode deliberate intent, not just structure):
        >   README.md, CHANGELOG.md, ARCHITECTURE.md, AGENTS.md,
        >   docs/**, **/specs/*.md, **/plans/*.md, **/decisions/*.md
        >   (exclude anything inside zie-framework/)
        >
        > Then scan the codebase structure to fill in any gaps.
        >
        > Exclude from all scans:
        >   node_modules/, .git/, build/, dist/, .next/, __pycache__/, *.pyc,
        >   coverage/, zie-framework/
        >
        > Return ONLY a JSON object with this exact structure (no markdown, no prose):
        > The parent parser will extract JSON from the first '{' to the last '}' if explanation text is present — keep any explanation text before or after the JSON block.
        >
        > {
        >   "architecture_pattern": "<string>",
        >   "components": [
        >     { "name": "<string>", "purpose": "<one-line string>" }
        >   ],
        >   "tech_stack": [
        >     { "name": "<string>", "version": "<string | null>" }
        >   ],
        >   "data_flow": "<string — entry point to response>",
        >   "key_constraints": ["<string>"],
        >   "test_strategy": {
        >     "runner": "<string | null>",
        >     "coverage_areas": ["<string>"]
        >   },
        >   "active_areas": ["<string — from git log --name-only -20>"],
        >   "existing_hooks": "<path to hooks/hooks.json if present, else null>",
        >   "existing_config": "<path to zie-framework/.config if present, else null>",
        >   "migration_candidates": {
        >     "specs":      ["<relative path>"],
        >     "plans":      ["<relative path>"],
        >     "decisions":  ["<relative path>"],
        >     "backlog":    ["<relative path>"]
        >   }
        > }
        >
        > For migration_candidates: include files matching these patterns (relative to
        > project root), excluding anything already inside zie-framework/:
        >   specs:     **/specs/*.md, **/spec/*.md
        >   plans:     **/plans/*.md, **/plan/*.md
        >   decisions: **/decisions/*.md, **/adr/*.md, ADR-*.md (at project root)
        >   backlog:   **/backlog/*.md
        >
        > For existing_hooks: check if hooks/hooks.json exists at project root.
        > For existing_config: check if zie-framework/.config exists.
        >
        > If a field cannot be determined, use null for scalar fields or [] for arrays.
        > Do not invent information. Mark unknown scalars as null.
        > ```

        **Parse `scan_report`:**

        ```python
        # Attempt 1: bare JSON
        scan_report = json.loads(agent_output.strip())

        # Attempt 2 (if attempt 1 fails): extract first { to last }
        start = agent_output.index("{")
        end   = agent_output.rindex("}") + 1
        scan_report = json.loads(agent_output[start:end])
        ```

        If both attempts fail → warn "Scan failed — retrying or falling back to
        templates?" and offer:
        - Retry the scan
        - Fall back to template path (same as greenfield)

        If agent times out → warn "Agent scan incomplete — retrying or falling back
        to templates?" and offer the same two choices.

     b. Draft the four knowledge files from `scan_report` fields:
        - `zie-framework/PROJECT.md` ← `architecture_pattern`, `components`,
          `tech_stack`
        - `zie-framework/project/architecture.md` ← `architecture_pattern`,
          `data_flow`, `active_areas`
        - `zie-framework/project/components.md` ← `components`
        - `zie-framework/project/context.md` ← `key_constraints`
          (unknowns marked TBD)

     c. Present all four drafts inline as markdown code blocks.

     d. **Section-targeted revision loop** — prompt:
        ```
        Which section to revise? (project / architecture / components / context / all good)
        ```
        - User replies `"project"` → re-draft only PROJECT.md, re-present
        - User replies `"architecture"` → re-draft only architecture.md, re-present
        - User replies `"components"` → re-draft only components.md, re-present
        - User replies `"context"` → re-draft only context.md, re-present
        - User replies `"all good"` or `"y"` or `"yes"` → exit loop, proceed to 2e
        - Unrecognized input → re-prompt (no crash, no iteration limit)
        - User can loop multiple times; other sections retain prior state

     e. Write all four files to disk.

     f. Compute `knowledge_hash` via:
        ```bash
        python3 hooks/knowledge-hash.py
        ```

     g. Read `zie-framework/.config` (if `existing_config` is non-null: read
        and preserve all user-set keys; if null: create fresh). Merge in:
        ```json
        {
          "knowledge_hash": "<computed hex string>",
          "knowledge_synced_at": "<YYYY-MM-DD>"
        }
        ```
        Write back. Never remove existing fields.

     h. **Present migration candidates** from `scan_report.migration_candidates`:

        - If `migration_candidates` key is missing or all arrays empty →
          skip silently.
        - If agent returned malformed JSON → warn "Could not detect migratable
          docs from agent report" then skip (continue to step 3).
        - `existing_hooks`: if non-null → treat hooks installation as a merge
          (preserve existing event handlers, add new ones); if null → write
          fresh `hooks/hooks.json`.

        Filter candidates: skip `README.md`, `CHANGELOG.md`, `LICENSE*`,
        `CLAUDE.md`, `AGENTS.md`, files already inside `zie-framework/`, and
        any `docs/` tree with `index.md` or `_sidebar.md` at its root.
        Validate each path exists on disk before presenting.

        | Source key | Destination |
        | --- | --- |
        | `specs` | `zie-framework/specs/` |
        | `plans` | `zie-framework/plans/` |
        | `decisions` | `zie-framework/decisions/` |
        | `backlog` | `zie-framework/backlog/` |

        If candidates remain after filtering, print:
        ```text
        Found documentation that can be migrated into zie-framework/:

          docs/specs/foo.md  →  zie-framework/specs/foo.md

        Migrate these files? (yes / no / select)
        ```
        - `yes` → migrate all using `git mv`
        - `no` → skip silently
        - `select` → confirm each file individually (y/n per file)

        If `git mv` fails → present error with retry option.
        After migration, print the list of moved files.

     i. Continue to step 3 (skip writing the four knowledge docs — already written).
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Measure the actual line reduction:
  ```bash
  # Before editing: capture baseline (run this BEFORE Step 2)
  git show HEAD:commands/zie-init.md | wc -l
  # After editing: check current count
  wc -l commands/zie-init.md
  # Or use git diff stat to see the delta
  git diff --stat HEAD -- commands/zie-init.md
  ```
  Confirm ≥100 lines removed. If not, tighten prose in the new Step 2 (remove
  redundant sentences, inline comments) until the reduction target is met.
  Record the actual before/after counts in a comment here once measured.

  Run: `make test-unit` — still PASS

---

## Task 3: Full CI gate

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- `make test-ci` passes with no new failures
- Coverage gate met
- `make lint` passes

**Files:**
- No file changes (validation only)

- [ ] **Step 1: Write failing tests (RED)**

  N/A — no new tests in this task. Run full suite to confirm baseline:
  ```bash
  make test-ci
  ```
  Expected: green (Tasks 1+2 already made unit tests pass).

- [ ] **Step 2: Implement (GREEN)**

  If `make test-ci` reveals any regressions not caught by `test-unit`, fix them now.
  Common issues:
  - `test_zie_init_deep_scan.py`: any remaining reference to `migratable_docs` must pass or be updated
  - `test_commands_zie_init.py`: pipeline summary tests reference content outside Step 2 — should be unaffected

  Run: `make test-ci` — must PASS

- [ ] **Step 3: Refactor**

  Run: `make lint` — fix any lint issues.
  Run: `make test-ci` — still PASS.

---

## Summary

| Task | Scope | Parallelism |
| --- | --- | --- |
| T1: Update tests | `test_zie_init_deep_scan.py` | Start first (RED gate) |
| T2: Rewrite Step 2 | `commands/zie-init.md` | After T1 |
| T3: Full CI gate | Validation only | After T2 |
