---
approved: true
approved_at: 2026-03-23
backlog: backlog/hybrid-release.md
spec: specs/2026-03-23-hybrid-release-design.md
---

# Hybrid Release — Implementation Plan

**Goal:** Split release into SDLC layer (`/zie-release`) and project-defined
Publishing layer (`make release NEW=version`) so zie-framework stays
project-agnostic.

**Architecture:** Four-file change — both Makefile templates gain a `release`
skeleton with `ZIE-NOT-READY` marker; `zie-release.md` gains a readiness gate
and delegates git ops + publish to `make release`; `zie-init.md` gains a
skeleton-negotiation step so every new project gets a ready-to-fill target
from day one.

**Tech Stack:** Markdown (command files), Makefile (templates), Python/pytest
(template + command structure validation)

---

## แผนที่ไฟล์

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `tests/unit/test_hybrid_release.py` | Validate template markers + command structure |
| Modify | `templates/Makefile.python.template` | Add `release` skeleton with ZIE-NOT-READY |
| Modify | `templates/Makefile.typescript.template` | Add `release` skeleton with ZIE-NOT-READY |
| Modify | `commands/zie-release.md` | Readiness gate + delegate to `make release` |
| Modify | `commands/zie-init.md` | Add skeleton-negotiation step after Makefile creation |

---

## Task 1: Makefile template skeletons

**Acceptance Criteria:**

- Both templates contain a `release:` target
- Target body contains literal string `ZIE-NOT-READY`
- Target body contains `@exit 1`
- Target guards against missing `NEW` variable
- `make help` renders a `release` row

**Files:**

- Create: `tests/unit/test_hybrid_release.py`
- Modify: `templates/Makefile.python.template`
- Modify: `templates/Makefile.typescript.template`

- [x] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_hybrid_release.py
  from pathlib import Path

  ROOT = Path(__file__).parent.parent.parent
  TEMPLATES = ROOT / "templates"
  COMMANDS = ROOT / "commands"


  def test_python_template_has_release_skeleton():
      content = (TEMPLATES / "Makefile.python.template").read_text()
      assert "release:" in content
      assert "ZIE-NOT-READY" in content
      assert "@exit 1" in content


  def test_typescript_template_has_release_skeleton():
      content = (TEMPLATES / "Makefile.typescript.template").read_text()
      assert "release:" in content
      assert "ZIE-NOT-READY" in content
      assert "@exit 1" in content
  ```

  Run: `make test-unit` — must FAIL (templates have no `release` target yet)

- [x] **Step 2: Implement (GREEN)**

  Append to `templates/Makefile.python.template` (before `# ── Utilities` section):

  ```makefile
  # ── Release ───────────────────────────────────────────────────────────
  release: ## Publish release (usage: make release NEW=1.2.3)
  ifndef NEW
  	$(error NEW is required — usage: make release NEW=1.2.3)
  endif
  	@echo "ZIE-NOT-READY: implement make release NEW=$(NEW)"
  	@echo "  Replace this block with:"
  	@echo "  1. Bump version files (pyproject.toml, plugin.json…)"
  	@echo "  2. git add -A && git commit -m 'release: v\$(NEW)'"
  	@echo "  3. git checkout main && git merge dev --no-ff"
  	@echo "  4. git tag -a v\$(NEW) -m 'release v\$(NEW)'"
  	@echo "  5. git push origin main --tags && git checkout dev"
  	@echo "  6. Project-specific publish (gh release, pip publish…)"
  	@exit 1
  ```

  Append same block to `templates/Makefile.typescript.template`
  (step 6 hint: `npm publish` / `vercel deploy --prod`).

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Verify `make help` output includes `release` row (manual check).
  Run: `make test-unit` — still PASS

---

## Task 2: Update `/zie-release` — readiness gate + delegation

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `commands/zie-release.md` no longer contains `git merge dev` or
  `git push origin main`
- File contains string `ZIE-NOT-READY` (the grep command in the gate)
- File contains `make release NEW=`
- Blocked message is present when marker found
- Step numbering is consistent

**Files:**

- Modify: `commands/zie-release.md`
- Modify: `tests/unit/test_hybrid_release.py`

- [x] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hybrid_release.py`:

  ```python
  def test_zie_release_has_readiness_gate():
      content = (COMMANDS / "zie-release.md").read_text()
      assert "ZIE-NOT-READY" in content
      assert "make release NEW=" in content


  def test_zie_release_no_direct_git_ops():
      content = (COMMANDS / "zie-release.md").read_text()
      assert "git merge dev" not in content
      assert "git push origin main" not in content
  ```

  Run: `make test-unit` — must FAIL

- [x] **Step 2: Implement (GREEN)**

  In `commands/zie-release.md`, under "All Gates Passed — Release":

  Remove step 5 (Commit release files) and step 6 (Merge to main) entirely.

  Replace with:

  ```markdown
  5. **Readiness gate — verify `make release` is implemented**:

     ```bash
     grep -q "ZIE-NOT-READY" Makefile && echo "NOT_READY" || echo "READY"
     ```

     - `NOT_READY` → **STOP**. Print:

       ```text
       Release blocked: make release is not implemented yet.

       Open Makefile, replace the ZIE-NOT-READY skeleton with real
       publish steps for this project, then re-run /zie-release.
       ```

     - `READY` → proceed.

  6. **Delegate publish to project**:

     ```bash
     make release NEW=<version>
     ```

     - Exit 0 → proceed.
     - Non-zero → **STOP**. Surface make error. Print: "Release failed —
       fix make release and re-run /zie-release."
  ```

  Renumber remaining steps: brain store → 7, auto-retro → 8, print → 9.
  Remove the note "Never call `make release` directly" (now it IS the pattern).

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Read updated `zie-release.md` end-to-end. Verify step numbering is
  sequential (1 → 9). Run: `make test-unit` — still PASS

---

## Task 3: Update `/zie-init` — negotiate `make release` skeleton

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**

- `commands/zie-init.md` contains `make release` and `ZIE-NOT-READY`
- New step placed after the Makefile creation step
- Step checks for existing `release:` target before writing (idempotent)
- Step shows user the draft and waits for `yes / no / edit`
- Skeletons differ by `project_type`

**Files:**

- Modify: `commands/zie-init.md`
- Modify: `tests/unit/test_hybrid_release.py`

- [x] **Step 1: Write failing tests (RED)**

  Add to `tests/unit/test_hybrid_release.py`:

  ```python
  def test_zie_init_has_release_negotiation():
      content = (COMMANDS / "zie-init.md").read_text()
      assert "make release" in content
      assert "ZIE-NOT-READY" in content
      assert "project_type" in content
  ```

  Run: `make test-unit` — must FAIL

- [x] **Step 2: Implement (GREEN)**

  In `commands/zie-init.md`, insert a new step immediately after the current
  Makefile creation step (step 6), before the VERSION step:

  ````markdown
  6a. **Negotiate `make release` skeleton** (both greenfield + existing paths):

      1. Check if `Makefile` already contains a `release` target:
         `grep -q "^release:" Makefile 2>/dev/null` → if found: **skip**
         (idempotent — never overwrite an existing target).
      2. Draft skeleton body based on `project_type` from `.config`:

         | project\_type | Skeleton hint |
         | --- | --- |
         | `python-api` | `sed` VERSION + pyproject.toml bump + pip publish |
         | `python-plugin` | `sed` VERSION + plugin.json bump + gh release |
         | `typescript-cli` | `npm version` + `npm publish` |
         | `typescript-fullstack` | `npm version` + `vercel deploy --prod` |
         | (other) | generic with detailed TODO comment |

      3. Present to user:

         ```text
         Here's the make release target I'll add to your Makefile:

         <draft skeleton with ZIE-NOT-READY + @exit 1>

         Does this look right? (yes / no / edit)
         ```

      4. `yes` → append skeleton to `Makefile`.
         `no` → skip (user implements manually later).
         `edit` → user describes change → redraft → re-present → repeat.
  ````

  Run: `make test-unit` — must PASS

- [x] **Step 3: Refactor**

  Verify step numbering in `zie-init.md` is consistent after insertion.
  Run: `make test-unit` — still PASS

---

## Context from brain

_zie_memory_enabled=false — no brain context available._
