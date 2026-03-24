---
approved: false
approved_at: ~
backlog: backlog/velocity-tracking.md
spec: specs/2026-03-24-velocity-tracking-design.md
---

# Velocity Tracking in /zie-status — Implementation Plan

**Goal:** Add a single velocity line to `commands/zie-status.md` that shows release cadence derived from semver git tags.
**Architecture:** Modify one file only — `commands/zie-status.md`. No new files, hooks, or storage. All logic is expressed as instructions to the `/zie-status` command agent. Interval count is hardcoded to 5 (last 6 tags); configurable N is explicitly deferred out of scope for this iteration.
**Tech Stack:** Markdown (command definition), pytest (content validation)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-status.md` | Add velocity computation step and output line |
| Create | `tests/unit/test_velocity_tracking.py` | Validate git tag command present, output line present, graceful fallback present |

---

## Task 1: Add velocity section to `commands/zie-status.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `commands/zie-status.md` contains a `git tag --sort=-version:refname` command
- `commands/zie-status.md` contains a "Velocity" output line
- `commands/zie-status.md` contains the graceful fallback text "not enough releases yet"

**Files:**
- Modify: `commands/zie-status.md`
- Create: `tests/unit/test_velocity_tracking.py`

- [ ] **Step 1: Write failing tests (RED)**
  ```python
  # tests/unit/test_velocity_tracking.py
  from pathlib import Path

  COMMANDS_DIR = Path(__file__).parents[2] / "commands"

  def read_status_command() -> str:
      return (COMMANDS_DIR / "zie-status.md").read_text()


  class TestVelocityTracking:
      def test_git_tag_command_present(self):
          text = read_status_command()
          assert "git tag --sort=-version:refname" in text, \
              "zie-status.md must contain git tag command for velocity"

      def test_velocity_output_line_present(self):
          text = read_status_command()
          assert "Velocity" in text, \
              "zie-status.md must contain a Velocity output line"

      def test_graceful_fallback_present(self):
          text = read_status_command()
          assert "not enough releases yet" in text, \
              "zie-status.md must contain graceful fallback for <2 semver tags"
  ```
  Run: `make test-unit` — must FAIL (velocity content not yet in `zie-status.md`)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-status.md`, make two edits:

  **Edit A — add a new numbered step after Step 5 (test health) and before Step 6 (print status):**

  Add the following as a new **Step 6** (renumber existing Step 6 → Step 7, Step 7 → Step 8):

  ```markdown
  6. **Compute release velocity** via Bash:

     ```bash
     git tag --sort=-version:refname | grep -E '^v?[0-9]+\.[0-9]+\.[0-9]+$' | head -6
     ```

     - Collect the last 6 semver tags (to compute 5 intervals)
     - For each consecutive pair, compute `days = (date(tag[n]) - date(tag[n+1])).days`
       using `git log -1 --format=%ai <tag>`
     - If fewer than 2 semver tags found → set velocity string to
       `"Velocity: not enough releases yet"`
     - Otherwise → format as `"Velocity (last N): Xd, Yd, Zd, ..."` where N is the
       number of intervals computed (up to 5)
  ```

  **Edit B — add a Velocity row to the status output table in Step 7 (formerly Step 6):**

  In the markdown output block, add this row immediately after the `| Version | ... |` row:

  ```markdown
  | Velocity | \<velocity string> |
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full `commands/zie-status.md` to confirm:
  - All original steps and output sections are intact
  - Step numbering is sequential with no gaps
  - The velocity row sits between `Version` and `Brain` in the output table
  - No trailing whitespace introduced in fenced code blocks

  Run: `make test-unit` — still PASS

---

*Commit: `git add commands/zie-status.md tests/unit/test_velocity_tracking.py && git commit -m "feat: velocity-tracking"`*
