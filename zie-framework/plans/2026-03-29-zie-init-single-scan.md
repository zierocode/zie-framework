---
approved: false
approved_at:
backlog: backlog/zie-init-single-scan.md
spec: specs/2026-03-29-zie-init-single-scan-design.md
---

# zie-init Single-Pass Scan — Implementation Plan

**Goal:** Eliminate the duplicate filesystem scan in `/zie-init` by extending the Explore agent prompt to include migration detection, removing the separate step 2h directory rescan.

**Architecture:** A single change to `commands/zie-init.md` — the Explore agent invocation at step 2a gains an explicit migration-detection instruction and returns `migratable_docs` as part of its JSON output. Step 2h is replaced with a parse-and-present block that reads from the agent report instead of rescanning disk. No Python hook changes, no new files.

**Tech Stack:** Markdown (commands/zie-init.md), pytest (existing test suite), Python 3.x (no new code)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-init.md` | Expand Explore agent prompt to include migration detection; remove step 2h directory rescan; parse `migratable_docs` from agent JSON |
| Modify | `tests/unit/test_zie_init_deep_scan.py` | Add tests asserting single-scan behavior and `migratable_docs` parsing |

---

## Task 1: Add tests asserting single-scan and migratable_docs behavior (RED)

<!-- depends_on: none -->

**Acceptance Criteria:**
- A new test asserts that `commands/zie-init.md` contains `migratable_docs` (agent prompt expansion)
- A new test asserts that `commands/zie-init.md` does NOT contain a standalone `step 2h` directory rescan (the old glob-based scan block)
- A new test asserts that `commands/zie-init.md` contains graceful fallback language for missing/malformed `migratable_docs`
- All new tests FAIL against the current `commands/zie-init.md` (which still has the old step 2h)
- Existing passing tests remain green

**Files:**
- Modify: `tests/unit/test_zie_init_deep_scan.py`

- [ ] **Step 1: Write failing tests (RED)**

  Add a new test class `TestZieInitSingleScan` to `tests/unit/test_zie_init_deep_scan.py`:

  ```python
  class TestZieInitSingleScan:
      def test_explore_agent_prompt_includes_migratable_docs(self):
          content = read("commands/zie-init.md")
          assert "migratable_docs" in content, (
              "Explore agent prompt must request migratable_docs in its output"
          )

      def test_no_standalone_step_2h_directory_rescan(self):
          content = read("commands/zie-init.md")
          # The old step 2h used Glob/filesystem scan outside the agent.
          # After the refactor the heading "2h" must no longer describe a
          # directory rescan — it should be gone entirely or describe
          # parsing from agent report.
          import re
          # Match the old pattern: a heading containing "2h" followed by
          # "Detect migratable" and a table of glob patterns scanned
          # directly (not parsed from agent output).
          old_rescan_pattern = re.compile(
              r"h\.\s+\*\*Detect migratable documentation\*\*.*scan project root",
              re.DOTALL,
          )
          assert not old_rescan_pattern.search(content), (
              "step 2h must not describe a standalone directory rescan; "
              "migration detection must come from the Explore agent report"
          )

      def test_migratable_docs_fallback_on_missing_key(self):
          content = read("commands/zie-init.md")
          # Spec requires: if migratable_docs missing → skip silently
          assert "missing" in content.lower() or "fallback" in content.lower() or "skip" in content.lower(), (
              "zie-init must document graceful fallback when migratable_docs "
              "is missing or empty from agent report"
          )

      def test_migratable_docs_fallback_on_malformed_json(self):
          content = read("commands/zie-init.md")
          assert (
              "malformed" in content.lower()
              or "garbled" in content.lower()
              or "Could not detect" in content
              or "graceful" in content.lower()
          ), (
              "zie-init must document graceful degradation when agent returns "
              "malformed JSON or omits migratable_docs"
          )

      def test_agent_prompt_includes_backlog_pattern(self):
          content = read("commands/zie-init.md")
          assert "**/backlog/*.md" in content, (
              "Explore agent prompt must include **/backlog/*.md in migration detection patterns"
          )

      def test_agent_prompt_excludes_zie_framework_dir(self):
          content = read("commands/zie-init.md")
          # Spec: agent should exclude files already inside zie-framework/
          # This was already present in step 2a exclusions; verify it remains.
          assert "zie-framework/" in content, (
              "Explore agent must still exclude zie-framework/ from scan"
          )
  ```

  Run: `make test-unit` — the three new `TestZieInitSingleScan` tests MUST FAIL (old step 2h
  rescan still present, `migratable_docs` not yet in prompt).

- [ ] **Step 2: Implement (GREEN)**

  See Task 2 below.

- [ ] **Step 3: Refactor**

  No refactor needed for the test file itself. Verify no duplicate assertions with existing class.
  Run: `make test-unit` — must still PASS after Task 2 implementation.

---

## Task 2: Update commands/zie-init.md — single-pass scan

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- The Explore agent invocation at step 2a includes explicit instruction to return `migratable_docs` object with `specs`, `plans`, `decisions`, `backlog` keys
- The agent prompt specifies the glob patterns: `**/specs/*.md`, `**/spec/*.md`, `**/plans/*.md`, `**/plan/*.md`, `**/decisions/*.md`, `**/adr/*.md`, `ADR-*.md` at project root, `**/backlog/*.md`
- The agent prompt instructs the agent to exclude files already inside `zie-framework/`
- Step 2h is replaced: instead of scanning disk, it parses `agent_report.migratable_docs`
- Fallback behavior documented: missing key → skip silently; malformed JSON → warn "Could not detect migratable docs from agent report" + skip; agent timeout → warn "Agent scan incomplete, skipping migration detection" + skip
- All six new `TestZieInitSingleScan` tests PASS
- All pre-existing `TestZieInitDeepScan` tests continue to PASS

**Files:**
- Modify: `commands/zie-init.md`

- [ ] **Step 1: Write failing tests (RED)**

  Already written in Task 1. Confirm they fail before editing:

  ```bash
  make test-unit 2>&1 | grep -A3 "TestZieInitSingleScan"
  ```

  Expected: `FAILED` for the three new tests targeting `migratable_docs`.

- [ ] **Step 2: Implement (GREEN)**

  **2a — Expand the Explore agent prompt (step 2a of zie-init.md):**

  In the existing Explore agent bullet list under step 2a, after the "Return: structured markdown report (not the final docs)" line, add:

  ```markdown
     - Additionally, detect migratable documentation: list all files
       matching `**/specs/*.md`, `**/spec/*.md`, `**/plans/*.md`,
       `**/plan/*.md`, `**/decisions/*.md`, `**/adr/*.md`,
       `ADR-*.md` (at project root), `**/backlog/*.md` —
       exclude any files already inside `zie-framework/`.
       Return these as a `migratable_docs` object in the report with
       keys `specs`, `plans`, `decisions`, `backlog` (each an array
       of relative file paths). Example:
       ```json
       {
         "migratable_docs": {
           "specs": ["docs/specs/foo.md"],
           "plans": [],
           "decisions": ["docs/adr-001.md"],
           "backlog": []
         }
       }
       ```
  ```

  **2b — Replace step 2h with parse-and-present block:**

  Replace the existing step 2h ("Detect migratable documentation — scan project root...") with:

  ```markdown
   h. **Present migratable documentation** — parse `migratable_docs`
      from the Explore agent report produced in step 2a:

      - If `migratable_docs` key is missing or all arrays are empty →
        skip silently.
      - If agent returned malformed JSON or omitted `migratable_docs` →
        warn: "Could not detect migratable docs from agent report" then
        skip (no error, continue to step 3).
      - If agent timed out before completing → warn: "Agent scan
        incomplete, skipping migration detection" then skip.
      - Otherwise: map each path to its destination using the same
        destination table as before:

        | Source key | Destination |
        | --- | --- |
        | `specs` | `zie-framework/specs/` |
        | `plans` | `zie-framework/plans/` |
        | `decisions` | `zie-framework/decisions/` |
        | `backlog` | `zie-framework/backlog/` |

        Skip always: `README.md`, `CHANGELOG.md`, `LICENSE*`,
        `CLAUDE.md`, `AGENTS.md`, files already inside
        `zie-framework/`, and any `docs/` tree that contains
        `index.md` or `_sidebar.md` at its root (public doc site).

        Validate each reported path exists on disk before presenting
        (graceful degradation for symlinks or stale agent results).

        If candidates remain after filtering, print:

        ```text
        Found documentation that can be migrated into zie-framework/:

          docs/specs/foo.md  →  zie-framework/specs/foo.md
          docs/plans/bar.md  →  zie-framework/plans/bar.md

        Migrate these files? (yes / no / select)
        ```

        - `yes` → migrate all using `git mv`
        - `no` → skip silently
        - `select` → confirm each file individually (y/n per file)

        If `git mv` fails for a candidate (e.g. destination already
        exists) → present error to user with retry option.

        After migration, print the list of moved files.
  ```

  Run: `make test-unit` — all `TestZieInitSingleScan` and `TestZieInitDeepScan` tests MUST PASS.

- [ ] **Step 3: Refactor**

  - Re-read the updated `commands/zie-init.md` to confirm the old step 2h glob-scan language is fully removed (no stray "scan project root" line outside of the Explore agent context).
  - Confirm step numbering (2a–2i) remains consistent and step 2h now reads "Present migratable documentation".
  - Run: `make test-unit` — must still PASS.

---

## Verification

After both tasks complete:

```bash
make test-unit
```

Expected: all existing tests pass + 6 new `TestZieInitSingleScan` tests pass.

Check the final state of `commands/zie-init.md`:
- Step 2a prompt includes `migratable_docs` instruction with all four key names
- Step 2h reads "Present migratable documentation" (not "Detect migratable documentation — scan project root")
- No standalone Glob/filesystem scan for `**/specs/*.md` outside the agent prompt
