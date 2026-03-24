---
approved: true
approved_at: 2026-03-24
backlog: backlog/session-agent-mode.md
spec: specs/2026-03-24-session-agent-mode-design.md
---
# Session-Wide Agent Mode — Implementation Plan

**Goal:** Add two agent definition files (`agents/zie-implement-mode.md` and `agents/zie-audit-mode.md`) to the plugin, register them via `agentsDir` in `plugin.json`, add a reference `settings.json`, and document usage in `README.md` and `CLAUDE.md`.
**Architecture:** Agent files live in `agents/` at the plugin root. Each is a Markdown file with YAML frontmatter (`model`, `permissionMode`, `tools`) followed by a system prompt body. `plugin.json` gets `"agentsDir": "agents"` to register the directory. `settings.json` at plugin root is a documentation artifact (not machine-read for session config) recording the recommended default agent. No hooks, skills, or existing commands are modified.
**Tech Stack:** Markdown (agent files), JSON (plugin.json, settings.json), pytest

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `agents/zie-implement-mode.md` | TDD-focused session agent — permissionMode: acceptEdits, tools: all |
| Create | `agents/zie-audit-mode.md` | Read-only analysis agent — permissionMode: plan, tools restricted |
| Modify | `.claude-plugin/plugin.json` | Add `"agentsDir": "agents"`, bump version to 1.6.0 |
| Create | `settings.json` | Reference doc: recommended default agent + invocation examples |
| Modify | `README.md` | Add Agent Modes section with `--agent` usage docs |
| Modify | `CLAUDE.md` | Add invocation examples under Development Commands |
| Modify | `zie-framework/project/components.md` | Add Agents section to component registry |
| Create | `tests/unit/test_agents.py` | Structural tests for both agent files |

---

## Task 1: Create `agents/zie-implement-mode.md`

<!-- depends_on: none -->

**Acceptance Criteria:**
- File exists at `agents/zie-implement-mode.md`
- Frontmatter contains `model: sonnet`, `permissionMode: acceptEdits`, `tools: all`
- System prompt body mentions: SDLC 6-stage pipeline, WIP=1 rule, `tdd-loop` skill, `test-pyramid` skill, all `/zie-*` commands, graceful degradation when `zie-framework/ROADMAP.md` is absent
- File parses as valid YAML frontmatter + Markdown body (no syntax errors)
- No secrets, API keys, or hardcoded credentials present

**Files:**
- Create: `agents/zie-implement-mode.md`
- Create: `tests/unit/test_agents.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agents.py

  """
  Structural tests for agent definition files.
  Verifies frontmatter keys, system prompt content, and safety contracts.
  """

  import re
  from pathlib import Path

  import pytest

  REPO_ROOT = Path(__file__).parent.parent.parent
  AGENTS_DIR = REPO_ROOT / "agents"


  def parse_agent_file(name: str) -> tuple[dict, str]:
      """Parse an agent .md file into (frontmatter_dict, body_str).

      Frontmatter is the YAML block between the first --- delimiters.
      Body is everything after the closing ---.
      """
      path = AGENTS_DIR / name
      content = path.read_text()
      # Split on frontmatter delimiters
      parts = content.split("---")
      # parts[0] == "" (before opening ---), parts[1] == YAML, parts[2+] == body
      assert len(parts) >= 3, f"{name}: could not parse frontmatter (need at least 2 --- delimiters)"
      fm_raw = parts[1].strip()
      body = "---".join(parts[2:]).strip()
      # Parse YAML manually for the small key set we need (avoid yaml dep assumption)
      fm: dict = {}
      for line in fm_raw.splitlines():
          if ":" in line:
              k, _, v = line.partition(":")
              fm[k.strip()] = v.strip()
      return fm, body


  class TestImplementModeAgent:
      def test_file_exists(self):
          assert (AGENTS_DIR / "zie-implement-mode.md").exists(), \
              "agents/zie-implement-mode.md not found"

      def test_frontmatter_model(self):
          fm, _ = parse_agent_file("zie-implement-mode.md")
          assert fm.get("model") == "sonnet", \
              f"Expected model: sonnet, got: {fm.get('model')}"

      def test_frontmatter_permission_mode(self):
          fm, _ = parse_agent_file("zie-implement-mode.md")
          assert fm.get("permissionMode") == "acceptEdits", \
              f"Expected permissionMode: acceptEdits, got: {fm.get('permissionMode')}"

      def test_frontmatter_tools_all(self):
          fm, _ = parse_agent_file("zie-implement-mode.md")
          assert fm.get("tools") == "all", \
              f"Expected tools: all, got: {fm.get('tools')}"

      def test_body_mentions_tdd_loop_skill(self):
          _, body = parse_agent_file("zie-implement-mode.md")
          assert "tdd-loop" in body, "System prompt must reference tdd-loop skill"

      def test_body_mentions_test_pyramid_skill(self):
          _, body = parse_agent_file("zie-implement-mode.md")
          assert "test-pyramid" in body, "System prompt must reference test-pyramid skill"

      def test_body_mentions_sdlc_pipeline_stages(self):
          _, body = parse_agent_file("zie-implement-mode.md")
          for stage in ["/zie-backlog", "/zie-spec", "/zie-plan", "/zie-implement",
                        "/zie-release", "/zie-retro"]:
              assert stage in body, f"System prompt must mention SDLC stage: {stage}"

      def test_body_mentions_wip_rule(self):
          _, body = parse_agent_file("zie-implement-mode.md")
          assert "WIP=1" in body or "WIP = 1" in body, \
              "System prompt must mention WIP=1 rule"

      def test_body_has_graceful_degradation_note(self):
          _, body = parse_agent_file("zie-implement-mode.md")
          assert "zie-init" in body or "/zie-init" in body, \
              "System prompt must instruct graceful degradation when project not initialized"

      def test_no_secrets_in_file(self):
          path = AGENTS_DIR / "zie-implement-mode.md"
          content = path.read_text()
          secret_patterns = [r"sk-[A-Za-z0-9]{20,}", r"api[_-]?key\s*=\s*\S+",
                             r"password\s*=\s*\S+", r"token\s*=\s*[A-Za-z0-9]{16,}"]
          for pat in secret_patterns:
              assert not re.search(pat, content, re.IGNORECASE), \
                  f"Possible secret found in zie-implement-mode.md matching pattern: {pat}"
  ```

  Run: `make test-unit` — must FAIL (`agents/zie-implement-mode.md` does not exist)

- [ ] **Step 2: Implement (GREEN)**

  ```markdown
  <!-- agents/zie-implement-mode.md -->
  ---
  model: sonnet
  permissionMode: acceptEdits
  tools: all
  ---

  # zie-implement-mode — TDD Implementation Agent

  You are operating inside the zie-framework SDLC pipeline as the implementation
  agent. Your role is to execute spec-driven, test-first development with full
  tool access and no per-operation confirmation prompts.

  ## Identity and Scope

  You are the implementation persona of zie-framework. You execute tasks from
  approved plans, write tests before code, and follow the pipeline stages in
  order. You do not redesign, re-spec, or re-plan unless the user explicitly
  requests it.

  ## SDLC Pipeline Awareness

  The zie-framework pipeline has six stages:

  1. /zie-backlog — capture a new backlog item
  2. /zie-spec — write a design spec with reviewer loop
  3. /zie-plan — draft implementation plan with reviewer loop
  4. /zie-implement — TDD feature loop with impl-reviewer per task
  5. /zie-release — test gates, readiness check, version tag
  6. /zie-retro — retrospective, ADRs, brain storage

  You operate primarily in stage 4 (/zie-implement). Never skip to a later stage
  without completing the current one. When a user asks you to build something,
  check whether an approved plan exists in `zie-framework/plans/` before
  proceeding. If no plan exists, recommend running /zie-plan first.

  ## WIP=1 Rule

  Only one item may be active in the ROADMAP Now lane at a time (ADR-001). Before
  starting a new task, confirm the current WIP=1 item is either complete or
  explicitly parked by the user. Do not start a second task while one is in
  progress without user confirmation.

  ## TDD Discipline

  At the start of every implementation task, invoke:

      Skill(zie-framework:tdd-loop)

  This skill enforces RED → GREEN → REFACTOR discipline. Never write
  implementation code before a failing test exists. If the Skill tool is
  unavailable (plugin not fully loaded), follow the tdd-loop steps manually:
  write a failing test, run it to confirm failure, implement the minimum code to
  pass, run tests to confirm green, then refactor.

  Before marking any task complete, invoke:

      Skill(zie-framework:test-pyramid)

  This skill confirms the test is at the correct level (unit / integration / e2e).
  If Skill is unavailable, manually verify: is this a unit test (fast, isolated,
  no I/O)? If not, escalate to integration or e2e as appropriate.

  ## Available Commands

  All /zie-* commands are available in this session:

  - /zie-backlog, /zie-spec, /zie-plan, /zie-implement, /zie-fix
  - /zie-release, /zie-retro, /zie-status, /zie-resync, /zie-audit

  Use them proactively. If the user's intent matches an SDLC stage, suggest the
  appropriate command.

  ## Hook Safety Contract (ADR-003)

  Hooks must never crash or block Claude. If a hook produces an error, log it to
  stderr and exit 0. Never use a non-zero exit code from a hook. Never raise an
  unhandled exception from a hook.

  ## Graceful Degradation — Uninitialized Project

  If `zie-framework/ROADMAP.md` does not exist in the current project, the SDLC
  state files are missing. In this case:

  1. Acknowledge that the project has not been initialized with zie-framework.
  2. Prompt the user to run /zie-init to set up the framework.
  3. Do not attempt to read ROADMAP.md, PROJECT.md, or any zie-framework/ paths
     until initialization is confirmed.

  ## Permission Mode

  This session runs with permissionMode: acceptEdits. File writes and shell
  commands execute without per-operation confirmation. Use this access
  responsibly: prefer targeted edits over broad rewrites, and always run tests
  after modifying code.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review system prompt for clarity and completeness. Confirm:
  - All six `/zie-*` pipeline stages are listed in order
  - Skill invocations use the exact `Skill(zie-framework:tdd-loop)` format
  - Graceful degradation covers both missing `ROADMAP.md` and unavailable `Skill` tool
  - No duplicate instructions

  Run: `make test-unit` — still PASS

---

## Task 2: Create `agents/zie-audit-mode.md`

<!-- depends_on: Task 1 (test file exists) -->

**Acceptance Criteria:**
- File exists at `agents/zie-audit-mode.md`
- Frontmatter contains `model: sonnet`, `permissionMode: plan`, `tools: [Read, Grep, Glob, WebSearch]`
- System prompt enforces read-only contract: no writes, no shell mutations
- System prompt instructs agent to surface findings as backlog candidates (not apply changes)
- System prompt mentions "audit mode is read-only" for clear user messaging
- File parses as valid YAML frontmatter + Markdown body

**Files:**
- Modify: `tests/unit/test_agents.py`
- Create: `agents/zie-audit-mode.md`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agents.py — add after TestImplementModeAgent

  class TestAuditModeAgent:
      def test_file_exists(self):
          assert (AGENTS_DIR / "zie-audit-mode.md").exists(), \
              "agents/zie-audit-mode.md not found"

      def test_frontmatter_model(self):
          fm, _ = parse_agent_file("zie-audit-mode.md")
          assert fm.get("model") == "sonnet", \
              f"Expected model: sonnet, got: {fm.get('model')}"

      def test_frontmatter_permission_mode(self):
          fm, _ = parse_agent_file("zie-audit-mode.md")
          assert fm.get("permissionMode") == "plan", \
              f"Expected permissionMode: plan, got: {fm.get('permissionMode')}"

      def test_frontmatter_tools_restricted(self):
          fm, _ = parse_agent_file("zie-audit-mode.md")
          tools_val = fm.get("tools", "")
          for expected in ["Read", "Grep", "Glob", "WebSearch"]:
              assert expected in tools_val, \
                  f"Expected '{expected}' in tools list, got: {tools_val}"

      def test_frontmatter_tools_excludes_write(self):
          fm, _ = parse_agent_file("zie-audit-mode.md")
          tools_val = fm.get("tools", "")
          # 'Write' must not appear as a standalone tool in the list
          # (it may appear as part of 'WebSearch' — check for standalone)
          tool_list = re.split(r"[\[\],\s]+", tools_val)
          assert "Write" not in tool_list, \
              f"Write tool must not be in audit-mode tool list: {tools_val}"

      def test_body_enforces_read_only(self):
          _, body = parse_agent_file("zie-audit-mode.md")
          assert "read-only" in body.lower() or "read only" in body.lower(), \
              "System prompt must assert read-only contract"

      def test_body_mentions_audit_mode_message(self):
          _, body = parse_agent_file("zie-audit-mode.md")
          assert "audit mode" in body.lower(), \
              "System prompt must mention 'audit mode' for user-facing messaging"

      def test_body_directs_findings_to_backlog(self):
          _, body = parse_agent_file("zie-audit-mode.md")
          assert "backlog" in body.lower(), \
              "System prompt must instruct surfacing findings as backlog candidates"

      def test_body_prohibits_writes(self):
          _, body = parse_agent_file("zie-audit-mode.md")
          # The system prompt must explicitly state no writes / no mutations
          assert "no write" in body.lower() or "do not write" in body.lower() \
              or "never write" in body.lower() or "mutation" in body.lower(), \
              "System prompt must explicitly prohibit write operations"

      def test_no_secrets_in_file(self):
          path = AGENTS_DIR / "zie-audit-mode.md"
          content = path.read_text()
          secret_patterns = [r"sk-[A-Za-z0-9]{20,}", r"api[_-]?key\s*=\s*\S+",
                             r"password\s*=\s*\S+", r"token\s*=\s*[A-Za-z0-9]{16,}"]
          for pat in secret_patterns:
              assert not re.search(pat, content, re.IGNORECASE), \
                  f"Possible secret found in zie-audit-mode.md matching pattern: {pat}"
  ```

  Run: `make test-unit` — must FAIL (`agents/zie-audit-mode.md` does not exist)

- [ ] **Step 2: Implement (GREEN)**

  ```markdown
  <!-- agents/zie-audit-mode.md -->
  ---
  model: sonnet
  permissionMode: plan
  tools: [Read, Grep, Glob, WebSearch]
  ---

  # zie-audit-mode — Read-Only Analysis Agent

  You are operating inside the zie-framework SDLC pipeline as the audit agent.
  Your role is analysis only. This session is read-only. You do not write files,
  execute shell commands, or apply any mutations to the codebase or filesystem.

  ## Read-Only Safety Contract

  Audit mode is read-only. This is a hard contract, not a preference.

  - Never write, edit, or delete any file.
  - Never execute shell commands that mutate state (no npm install, no git commit,
    no make targets that produce side effects).
  - Never invoke Write, Edit, Bash, or any tool outside the allowed set.
  - If the user asks you to apply a change, respond: "Audit mode is read-only. I
    can surface this as a backlog item for you to action in an implement session."
  - Tool restriction (tools: [Read, Grep, Glob, WebSearch]) provides hard
    enforcement at the Claude Code runtime layer — attempts to use disallowed tools
    will be blocked regardless of this system prompt.

  ## Purpose and Scope

  Use this mode for:
  - Codebase health audits (security, architecture, test coverage, dependency
    freshness, documentation quality, performance patterns)
  - Research tasks requiring WebSearch (library comparisons, best practice review,
    ecosystem scanning)
  - Pre-implementation analysis (understanding a codebase before planning a change)
  - Retrospective analysis (reviewing what happened and why)

  Do not use this mode to implement features, fix bugs, or apply any change.

  ## Output Format — Backlog Candidates

  Surface all findings as backlog candidates. For each finding:

  1. State the dimension (security / architecture / test coverage / docs /
     performance / dependency / UX / DX / observability)
  2. Summarize the problem in one sentence
  3. Suggest a backlog title (suitable for /zie-backlog)
  4. Assign a priority signal: High / Medium / Low

  Do not create backlog files yourself. Present the candidates in a structured
  table or list and ask the user which ones to capture.

  ## SDLC Pipeline Awareness

  You are aware of the zie-framework pipeline stages:

  - /zie-backlog — capture a new backlog item
  - /zie-spec — design spec
  - /zie-plan — implementation plan
  - /zie-implement — TDD build loop
  - /zie-release — test gates and release
  - /zie-retro — retrospective and ADRs

  Audit findings feed into /zie-backlog. You help identify what should be captured
  there, but you do not capture it yourself.

  ## Tool Allowlist

  You may only use: Read, Grep, Glob, WebSearch.

  If you need to examine a file: use Read.
  If you need to search for a pattern: use Grep.
  If you need to find files by name: use Glob.
  If you need external information: use WebSearch.

  Any other tool invocation will be blocked by the session runtime.

  ## Graceful Degradation

  If `zie-framework/ROADMAP.md` does not exist in the current project, acknowledge
  that the project has not been initialized. You can still audit raw source files —
  just note that SDLC state context is unavailable.
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review both agent files together. Confirm:
  - Tone is consistent between the two (professional, directive)
  - Read-only contract in `zie-audit-mode.md` has no ambiguity
  - No overlap between "apply changes" language in `zie-implement-mode.md` and prohibitions in `zie-audit-mode.md`

  Run: `make test-unit` — still PASS

---

## Task 3: Add `agentsDir` to `plugin.json` + create `settings.json`

<!-- depends_on: Task 1, Task 2 -->

**Acceptance Criteria:**
- `.claude-plugin/plugin.json` contains `"agentsDir": "agents"` key
- `.claude-plugin/plugin.json` version bumped to `1.6.0`
- `VERSION` file updated to `1.6.0` (keeps version sync test green)
- `settings.json` exists at plugin root with `"defaultAgent"` and `"invocation"` keys
- Existing `TestPluginJsonVersion` test continues to pass (version sync)
- New structural test asserts `agentsDir` key present in `plugin.json`

**Files:**
- Modify: `.claude-plugin/plugin.json`
- Modify: `VERSION`
- Create: `settings.json`
- Modify: `tests/unit/test_agents.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agents.py — add after TestAuditModeAgent

  class TestPluginJsonAgentsDir:
      def test_agents_dir_key_present(self):
          import json
          plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
          assert "agentsDir" in plugin, \
              "plugin.json must contain 'agentsDir' key"

      def test_agents_dir_value(self):
          import json
          plugin = json.loads((REPO_ROOT / ".claude-plugin" / "plugin.json").read_text())
          assert plugin["agentsDir"] == "agents", \
              f"Expected agentsDir: 'agents', got: {plugin.get('agentsDir')}"


  class TestSettingsJson:
      def test_settings_json_exists(self):
          assert (REPO_ROOT / "settings.json").exists(), \
              "settings.json not found at plugin root"

      def test_settings_json_has_default_agent(self):
          import json
          settings = json.loads((REPO_ROOT / "settings.json").read_text())
          assert "defaultAgent" in settings, \
              "settings.json must contain 'defaultAgent' key"

      def test_settings_json_default_agent_is_implement_mode(self):
          import json
          settings = json.loads((REPO_ROOT / "settings.json").read_text())
          assert settings["defaultAgent"] == "zie-implement-mode", \
              f"Expected defaultAgent: 'zie-implement-mode', got: {settings.get('defaultAgent')}"

      def test_settings_json_has_invocation_key(self):
          import json
          settings = json.loads((REPO_ROOT / "settings.json").read_text())
          assert "invocation" in settings, \
              "settings.json must contain 'invocation' key documenting usage examples"

      def test_settings_json_is_valid_json(self):
          import json
          content = (REPO_ROOT / "settings.json").read_text()
          try:
              json.loads(content)
          except json.JSONDecodeError as e:
              pytest.fail(f"settings.json is not valid JSON: {e}")
  ```

  Run: `make test-unit` — must FAIL (`agentsDir` key absent and `settings.json` absent)

- [ ] **Step 2: Implement (GREEN)**

  Updated `.claude-plugin/plugin.json`:

  ```json
  {
    "name": "zie-framework",
    "description": "Solo developer SDLC framework for Claude Code — spec-first, TDD, automated testing, brain-integrated",
    "version": "1.6.0",
    "author": {
      "name": "zie"
    },
    "agentsDir": "agents"
  }
  ```

  Updated `VERSION`:

  ```
  1.6.0
  ```

  New `settings.json` at plugin root:

  ```json
  {
    "defaultAgent": "zie-implement-mode",
    "note": "This file is a reference document, not machine-read by Claude Code for session config. It records the recommended agent for active development sessions.",
    "invocation": {
      "implement_mode": "claude --plugin-dir . --agent zie-framework:zie-implement-mode",
      "audit_mode": "claude --plugin-dir . --agent zie-framework:zie-audit-mode",
      "description": "Run from any host project directory. --plugin-dir must point to the zie-framework plugin root."
    }
  }
  ```

  Run: `make test-unit` — must PASS (including existing `TestPluginJsonVersion` which now checks `1.6.0` against `VERSION`)

- [ ] **Step 3: Refactor**

  Confirm `settings.json` `note` field accurately describes the file's role (documentation only, not machine-read). Confirm `plugin.json` has no trailing whitespace or formatting issues.

  Run: `make test-unit` — still PASS

---

## Task 4: Update `README.md` and `CLAUDE.md` with `--agent` usage docs

<!-- depends_on: Task 3 -->

**Acceptance Criteria:**
- `README.md` contains a new "Agent Modes" section with a table listing both agents, their permission modes, and invocation commands
- `CLAUDE.md` Development Commands section includes `--agent` invocation examples
- `zie-framework/project/components.md` has a new Agents section listing both agent files with their permission modes
- New test asserts "Agent Modes" section present in `README.md`
- All existing `TestReadmeReferences` tests continue to pass

**Files:**
- Modify: `README.md`
- Modify: `CLAUDE.md`
- Modify: `zie-framework/project/components.md`
- Modify: `tests/unit/test_agents.py`

- [ ] **Step 1: Write failing tests (RED)**

  ```python
  # tests/unit/test_agents.py — add after TestSettingsJson

  class TestReadmeAgentDocs:
      def test_agent_modes_section_present(self):
          readme = (REPO_ROOT / "README.md").read_text()
          assert "Agent Modes" in readme, \
              "README.md must contain an 'Agent Modes' section"

      def test_implement_mode_in_readme(self):
          readme = (REPO_ROOT / "README.md").read_text()
          assert "zie-implement-mode" in readme, \
              "README.md must document zie-implement-mode agent"

      def test_audit_mode_in_readme(self):
          readme = (REPO_ROOT / "README.md").read_text()
          assert "zie-audit-mode" in readme, \
              "README.md must document zie-audit-mode agent"

      def test_agent_invocation_command_in_readme(self):
          readme = (REPO_ROOT / "README.md").read_text()
          assert "--agent" in readme, \
              "README.md must show --agent flag in invocation example"


  class TestClaudeMdAgentDocs:
      def test_agent_invocation_in_claude_md(self):
          claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
          assert "--agent" in claude_md, \
              "CLAUDE.md must include --agent invocation example"

      def test_implement_mode_in_claude_md(self):
          claude_md = (REPO_ROOT / "CLAUDE.md").read_text()
          assert "zie-implement-mode" in claude_md, \
              "CLAUDE.md must reference zie-implement-mode"


  class TestComponentsRegistryAgents:
      def test_agents_section_present(self):
          components = (REPO_ROOT / "zie-framework" / "project" / "components.md").read_text()
          assert "## Agents" in components, \
              "components.md must have an '## Agents' section"

      def test_implement_mode_in_components(self):
          components = (REPO_ROOT / "zie-framework" / "project" / "components.md").read_text()
          assert "zie-implement-mode" in components, \
              "components.md Agents section must list zie-implement-mode"

      def test_audit_mode_in_components(self):
          components = (REPO_ROOT / "zie-framework" / "project" / "components.md").read_text()
          assert "zie-audit-mode" in components, \
              "components.md Agents section must list zie-audit-mode"
  ```

  Run: `make test-unit` — must FAIL (sections not yet present)

- [ ] **Step 2: Implement (GREEN)**

  Add to `README.md` after the `## Dependencies` section:

  ```markdown
  ## Agent Modes

  Start a fully configured session without per-operation approval prompts:

  | Agent | Mode | Tools | Invocation |
  | --- | --- | --- | --- |
  | `zie-implement-mode` | TDD-focused, full access | all | `claude --plugin-dir <path> --agent zie-framework:zie-implement-mode` |
  | `zie-audit-mode` | Read-only analysis | Read, Grep, Glob, WebSearch | `claude --plugin-dir <path> --agent zie-framework:zie-audit-mode` |

  **`zie-implement-mode`** — `permissionMode: acceptEdits`. File writes and shell
  commands run without confirmation. Session system prompt injects SDLC pipeline
  context, WIP=1 rule, and skill preload hints for `tdd-loop` and `test-pyramid`.

  **`zie-audit-mode`** — `permissionMode: plan`. Tool restriction hard-blocks any
  write or shell mutation at the Claude Code runtime layer. Findings are surfaced
  as backlog candidates; no changes are applied.

  Run from any host project directory where the plugin is available:

  ```bash
  # Active development session — TDD mode, no confirmation prompts
  claude --plugin-dir /path/to/zie-framework --agent zie-framework:zie-implement-mode

  # Codebase audit — read-only, analysis focused
  claude --plugin-dir /path/to/zie-framework --agent zie-framework:zie-audit-mode
  ```
  ```

  Add to `CLAUDE.md` under `## Development Commands`:

  ```markdown
  ## Agent Mode Sessions

  ```bash
  # TDD-focused session — permissionMode: acceptEdits, all tools
  claude --plugin-dir . --agent zie-framework:zie-implement-mode

  # Read-only audit session — permissionMode: plan, restricted tools
  claude --plugin-dir . --agent zie-framework:zie-audit-mode
  ```
  ```

  Add to `zie-framework/project/components.md` after the Hooks table:

  ```markdown
  ## Agents

  | Agent | permissionMode | Tools | System Prompt Focus |
  | --- | --- | --- | --- |
  | zie-implement-mode | acceptEdits | all | SDLC pipeline, TDD, tdd-loop + test-pyramid skill preload |
  | zie-audit-mode | plan | Read, Grep, Glob, WebSearch | Read-only analysis, backlog candidate surfacing |
  ```

  Run: `make test-unit` — must PASS

- [ ] **Step 3: Refactor**

  Review all four modified files together:
  - Confirm `README.md` Agent Modes table aligns with actual frontmatter values in the agent files
  - Confirm `CLAUDE.md` invocation examples use `--plugin-dir .` (relative, suitable for self-hosted dev)
  - Confirm `components.md` last updated date is accurate
  - Confirm no duplicate "Agent Modes" or "Agents" headings in any file

  Run: `make test-unit` — still PASS

---

## Commit

```
git add agents/zie-implement-mode.md agents/zie-audit-mode.md \
        .claude-plugin/plugin.json VERSION settings.json \
        README.md CLAUDE.md zie-framework/project/components.md \
        tests/unit/test_agents.py && \
git commit -m "feat: session-wide agent mode — zie-implement-mode + zie-audit-mode agents"
```
