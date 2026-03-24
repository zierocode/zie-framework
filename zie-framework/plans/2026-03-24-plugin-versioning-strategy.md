---
approved: false
approved_at: ~
backlog: backlog/plugin-versioning-strategy.md
spec: specs/2026-03-24-plugin-versioning-strategy-design.md
---

# Plugin Versioning Strategy — Semver Auto-Bump — Implementation Plan

**Goal:** Replace manual dual-file version updates with a single `make bump NEW=<v>` target that atomically writes both `VERSION` and `.claude-plugin/plugin.json`, plus a pre-release consistency gate in `commands/zie-release.md` that catches drift before it reaches the tag.
**Architecture:** Pure Makefile (no new Python scripts). Gate is a prose instruction block inside zie-release.md that Claude reads and executes with a Bash tool call. The `bump` target uses `sed -i ''` (matching the precedent set by the existing `make release` target), not `jq` (which is used by `sync-version`). This inconsistency is intentional: `sed` is chosen to match `make release` which already writes `plugin.json` the same way. The version consistency gate is inserted as the last step of `## ตรวจสอบก่อนเริ่ม` — this satisfies the spec's "before unit tests" intent since all `ลำดับการตรวจสอบ` test gates come after that section.
**Tech Stack:** Make (bump target), Markdown (zie-release.md gate), Bash tests

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `Makefile` | Add `bump` target: validates `NEW`, writes `VERSION`, updates `plugin.json` version field |
| Modify | `commands/zie-release.md` | Add version consistency gate as first check before unit tests |
| Create | `tests/unit/test_bump.py` | Bash-level tests for `make bump` behavior |
| Create | `tests/unit/test_versioning_gate.py` | `Path.read_text()` tests confirming gate prose is present in zie-release.md |

---

## Task 1: Add `make bump` target to `Makefile`

<!-- depends_on: none -->

**Acceptance Criteria:**

- `make bump NEW=1.99.0` writes `1.99.0` to `VERSION`
- `make bump NEW=1.99.0` updates `"version"` field in `.claude-plugin/plugin.json` to `1.99.0`
- Both files are updated in the same make invocation — no partial state if the second write fails
- `make bump` without `NEW` prints a usage error and exits non-zero
- `make bump NEW=not-a-version` (non-semver) prints a validation error and exits non-zero
- Existing `make release`, `make push`, `make sync-version`, and all other targets are unchanged

**Files:**

- Modify: `Makefile`
- Create: `tests/unit/test_bump.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_bump.py
  import subprocess
  import json
  from pathlib import Path

  REPO_ROOT = Path(__file__).parents[2]
  VERSION_FILE = REPO_ROOT / "VERSION"
  PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


  def run_make(args: list[str]) -> subprocess.CompletedProcess:
      return subprocess.run(
          ["make", "-C", str(REPO_ROOT)] + args,
          capture_output=True,
          text=True,
      )


  class TestMakeBump:
      def setup_method(self, _method):
          """Capture original state before each test."""
          self._original_version = VERSION_FILE.read_text().strip()

      def teardown_method(self, _method):
          """Restore both files to original version after each test."""
          VERSION_FILE.write_text(self._original_version + "\n")
          data = json.loads(PLUGIN_JSON.read_text())
          data["version"] = self._original_version
          PLUGIN_JSON.write_text(json.dumps(data, indent=2) + "\n")

      def test_bump_updates_version_file(self):
          result = run_make(["bump", "NEW=1.99.0"])
          assert result.returncode == 0, result.stderr
          assert VERSION_FILE.read_text().strip() == "1.99.0"

      def test_bump_updates_plugin_json(self):
          result = run_make(["bump", "NEW=1.99.0"])
          assert result.returncode == 0, result.stderr
          data = json.loads(PLUGIN_JSON.read_text())
          assert data["version"] == "1.99.0"

      def test_bump_prints_confirmation(self):
          result = run_make(["bump", "NEW=1.99.0"])
          assert result.returncode == 0, result.stderr
          assert "1.99.0" in result.stdout

      def test_bump_without_new_exits_nonzero(self):
          result = run_make(["bump"])
          assert result.returncode != 0
          # Files must not be modified — version unchanged
          assert VERSION_FILE.read_text().strip() == self._original_version

      def test_bump_invalid_semver_exits_nonzero(self):
          result = run_make(["bump", "NEW=not-a-version"])
          assert result.returncode != 0
          assert VERSION_FILE.read_text().strip() == self._original_version

      def test_bump_does_not_modify_other_makefile_targets(self):
          """Regression: make help still works after bump is added."""
          result = run_make(["help"])
          assert result.returncode == 0
  ```

  Run: `make test-unit` — must FAIL (`bump` target does not exist)

- [ ] **Step 2: Implement (GREEN)**

  In `Makefile`, add the following target in the `# ── Release` section, immediately before the existing `release:` target:

  ```makefile
  bump: ## Atomically bump VERSION + plugin.json (usage: make bump NEW=1.2.3)
  ifndef NEW
  	$(error NEW is required — usage: make bump NEW=1.2.3)
  endif
  	@echo "$(NEW)" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+$$' || \
  		(echo "ERROR: NEW must be a semver string (e.g. 1.2.3), got: $(NEW)" && exit 1)
  	@printf '%s\n' "$(NEW)" > VERSION
  	@sed -i '' 's/"version": "[^"]*"/"version": "$(NEW)"/' .claude-plugin/plugin.json
  	@echo "Bumped to v$(NEW)"
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Confirm `make help` still lists `bump` alongside `release` with a correct description. Confirm `sync-version` target is still present and unchanged.
  Run: `make test-unit` — still PASS

---

## Task 2: Add version consistency gate to `commands/zie-release.md`

<!-- depends_on: none -->

**Acceptance Criteria:**

- `commands/zie-release.md` contains a version consistency gate section before the unit test gate
- The gate instructs Claude to read `VERSION` and `.claude-plugin/plugin.json`, compare their version strings, and fail with a specific message if they diverge
- The failure message includes the literal text `make bump NEW=<v>` to guide the user
- The gate passes silently when both files are in sync
- All existing gate sections and release steps are unchanged

**Files:**

- Modify: `commands/zie-release.md`
- Create: `tests/unit/test_versioning_gate.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_versioning_gate.py
  from pathlib import Path

  RELEASE_CMD = Path(__file__).parents[2] / "commands" / "zie-release.md"


  class TestVersioningGate:
      def test_versioning_gate_section_present(self):
          text = RELEASE_CMD.read_text()
          assert "Version Consistency" in text or "version consistency" in text, \
              "zie-release.md must contain a version consistency gate section"

      def test_gate_references_version_file(self):
          text = RELEASE_CMD.read_text()
          assert "VERSION" in text

      def test_gate_references_plugin_json(self):
          text = RELEASE_CMD.read_text()
          assert "plugin.json" in text

      def test_gate_includes_bump_remediation(self):
          text = RELEASE_CMD.read_text()
          assert "make bump" in text, \
              "zie-release.md version gate must reference 'make bump' as the remediation"

      def test_gate_includes_mismatch_message(self):
          text = RELEASE_CMD.read_text()
          assert "mismatch" in text.lower() or "diverge" in text.lower() or \
              "not match" in text.lower() or "do not match" in text.lower(), \
              "zie-release.md version gate must describe a mismatch failure condition"
  ```

  Run: `make test-unit` — must FAIL (gate prose not yet in file)

- [ ] **Step 2: Implement (GREEN)**

  In `commands/zie-release.md`, under `## ตรวจสอบก่อนเริ่ม`, insert the following as step 5 (after the existing step 4 that reads the current branch):

  ```markdown
  5. **Version Consistency Gate** — before running any tests, verify that `VERSION`
     and `.claude-plugin/plugin.json` are in sync:

     ```bash
     VERSION_VAL=$(cat VERSION)
     PLUGIN_VAL=$(python3 -c "import json; print(json.load(open('.claude-plugin/plugin.json'))['version'])")
     if [ "$VERSION_VAL" != "$PLUGIN_VAL" ]; then
       echo "Version mismatch: VERSION=$VERSION_VAL, plugin.json=$PLUGIN_VAL — run \`make bump NEW=<v>\` to sync before releasing."
       exit 1
     fi
     ```

     - Exit 0 (versions match) → continue.
     - Exit 1 (mismatch) → **STOP**. Print the error message from the script
       and do not proceed to test gates.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Read the full `## ตรวจสอบก่อนเริ่ม` section to confirm steps 1-4 are intact and the new step 5 is cleanly inserted. Confirm all downstream gate sections (`### ตรวจสอบ: Unit Tests` onwards) are unchanged.
  Run: `make test-unit` — still PASS

---

*Commit: `git add Makefile commands/zie-release.md tests/unit/test_bump.py tests/unit/test_versioning_gate.py && git commit -m "feat: plugin-versioning-strategy"`*
