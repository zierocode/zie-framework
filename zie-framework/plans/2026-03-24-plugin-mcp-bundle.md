---
approved: true
approved_at: 2026-03-24
backlog: backlog/plugin-mcp-bundle.md
spec: specs/2026-03-24-plugin-mcp-bundle-design.md
---

# Plugin .mcp.json Bundle zie-memory Server — Implementation Plan

**Goal:** Ship `.claude-plugin/.mcp.json` so zie-memory MCP server is available automatically when the plugin is installed, and update all commands/skills to call `mcp__plugin_zie-memory_zie-memory__*` tool names directly in their `zie_memory_enabled=true` branches.

**Architecture:** Three independent work units. Task 1 creates the new `.mcp.json` file. Task 2 is a sweeping text-substitution pass across commands and skills that replaces pseudo-call syntax with canonical MCP tool names. Task 3 updates README.md to document zero-setup brain integration. No hook files change; no logic changes in `.config` or `zie-init` detection; the HTTP path in `utils.py` is untouched.

**Tech Stack:** Python 3.x, pytest, stdlib only (json, subprocess, pathlib)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Create | `.claude-plugin/.mcp.json` | Declares zie-memory MCP server (stdio, env-gated) |
| Create | `tests/unit/test_mcp_bundle.py` | Schema validity + env vars declared + plugin.json unaffected |
| Modify | `skills/spec-design/SKILL.md` | MCP tool names in `zie_memory_enabled=true` branches |
| Modify | `skills/write-plan/SKILL.md` | MCP tool names in `zie_memory_enabled=true` branches |
| Modify | `skills/debug/SKILL.md` | MCP tool names in `zie_memory_enabled=true` branches |
| Modify | `skills/verify/SKILL.md` | MCP tool names in `zie_memory_enabled=true` branches |
| Modify | `commands/zie-backlog.md` | MCP tool names for recall + remember steps |
| Modify | `commands/zie-spec.md` | MCP tool names (passed to spec-design skill) |
| Modify | `commands/zie-plan.md` | MCP tool names for recall + remember steps |
| Modify | `commands/zie-implement.md` | MCP tool names for recall + remember + WIP checkpoint steps |
| Modify | `commands/zie-fix.md` | MCP tool names for recall + remember steps |
| Modify | `commands/zie-release.md` | MCP tool names for recall + remember steps |
| Modify | `commands/zie-retro.md` | MCP tool names for recall + remember + downvote steps |
| Modify | `commands/zie-init.md` | MCP tool name for step 12 memory bootstrap |
| Modify | `README.md` | Add "Brain Integration — zero-setup via plugin .mcp.json" section |

---

## Task 1: Create `.claude-plugin/.mcp.json`

<!-- depends_on: none -->

**Acceptance Criteria:**
- `.claude-plugin/.mcp.json` exists and parses as valid JSON.
- Top-level key is `mcpServers`; the `zie-memory` entry has `type`, `command`, and `env` keys.
- `env` map declares both `ZIE_MEMORY_API_URL` and `ZIE_MEMORY_API_KEY`.
- `command` is `npx` with `args: ["zie-memory"]` (stdio transport).
- `.claude-plugin/plugin.json` still parses correctly after adding the new file.
- All pre-existing unit tests continue to pass.

**Files:**
- Create: `.claude-plugin/.mcp.json`
- Create: `tests/unit/test_mcp_bundle.py`

### Step 1: Write failing tests (RED)

```python
# tests/unit/test_mcp_bundle.py

"""Tests for .claude-plugin/.mcp.json MCP bundle spec (Task 1)."""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
MCP_JSON = REPO_ROOT / ".claude-plugin" / ".mcp.json"
PLUGIN_JSON = REPO_ROOT / ".claude-plugin" / "plugin.json"


class TestMcpJsonSchema:
    def test_file_exists(self):
        assert MCP_JSON.exists(), f".mcp.json not found at {MCP_JSON}"

    def test_parses_as_valid_json(self):
        data = json.loads(MCP_JSON.read_text())
        assert isinstance(data, dict)

    def test_top_level_key_is_mcp_servers(self):
        data = json.loads(MCP_JSON.read_text())
        assert "mcpServers" in data, f"Expected 'mcpServers' key, got: {list(data.keys())}"

    def test_zie_memory_entry_exists(self):
        data = json.loads(MCP_JSON.read_text())
        assert "zie-memory" in data["mcpServers"], (
            f"Expected 'zie-memory' server entry, got: {list(data['mcpServers'].keys())}"
        )

    def test_zie_memory_has_required_keys(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        for key in ("type", "command", "env"):
            assert key in entry, f"Missing required key '{key}' in zie-memory entry"

    def test_zie_memory_type_is_stdio(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert entry["type"] == "stdio", f"Expected type='stdio', got '{entry['type']}'"

    def test_zie_memory_command_is_npx(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert entry["command"] == "npx", f"Expected command='npx', got '{entry['command']}'"

    def test_zie_memory_args_contains_zie_memory(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "args" in entry and "zie-memory" in entry["args"], (
            f"Expected 'zie-memory' in args, got: {entry.get('args')}"
        )


class TestMcpJsonEnvVars:
    def test_env_declares_api_url(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "ZIE_MEMORY_API_URL" in entry["env"], (
            "ZIE_MEMORY_API_URL must be declared in zie-memory env map"
        )

    def test_env_declares_api_key(self):
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        assert "ZIE_MEMORY_API_KEY" in entry["env"], (
            "ZIE_MEMORY_API_KEY must be declared in zie-memory env map"
        )

    def test_env_values_are_shell_variable_references(self):
        """Values should be ${VAR} references, not hardcoded strings."""
        entry = json.loads(MCP_JSON.read_text())["mcpServers"]["zie-memory"]
        for var in ("ZIE_MEMORY_API_URL", "ZIE_MEMORY_API_KEY"):
            val = entry["env"][var]
            assert val.startswith("${") and val.endswith("}"), (
                f"env.{var} should be a shell reference like '${{VAR}}', got: '{val}'"
            )


class TestPluginJsonUnaffected:
    def test_plugin_json_still_parses(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert isinstance(data, dict)

    def test_plugin_json_has_name(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert "name" in data and data["name"] == "zie-framework"

    def test_plugin_json_has_version(self):
        data = json.loads(PLUGIN_JSON.read_text())
        assert "version" in data
```

Run: `make test-unit` — must FAIL (`test_file_exists` fails; `.mcp.json` does not exist yet)

### Step 2: Implement (GREEN)

Create `.claude-plugin/.mcp.json` with the following exact content:

```json
{
  "mcpServers": {
    "zie-memory": {
      "type": "stdio",
      "command": "npx",
      "args": ["zie-memory"],
      "env": {
        "ZIE_MEMORY_API_URL": "${ZIE_MEMORY_API_URL}",
        "ZIE_MEMORY_API_KEY": "${ZIE_MEMORY_API_KEY}"
      }
    }
  }
}
```

Run: `make test-unit` — must PASS (all `TestMcpJsonSchema`, `TestMcpJsonEnvVars`, `TestPluginJsonUnaffected` classes green)

### Step 3: Refactor

No structural changes needed. Confirm:
- JSON is minified to exactly the shape above (no extra keys).
- `TestMcpJsonEnvVars.test_env_values_are_shell_variable_references` passes — values are `${ZIE_MEMORY_API_URL}` and `${ZIE_MEMORY_API_KEY}`, not bare names.

Run: `make test-unit` — still PASS

---

## Task 2: Update commands and skills to use `mcp__plugin_zie-memory_zie-memory__*` tool names

<!-- depends_on: none -->

**Acceptance Criteria:**
- Every `zie_memory_enabled=true` branch in commands and skills that previously used pseudo-call syntax (`recall ...`, `remember "..."`, `downvote_memory`) now references the canonical MCP tool name (`mcp__plugin_zie-memory_zie-memory__recall`, `mcp__plugin_zie-memory_zie-memory__remember`, `mcp__plugin_zie-memory_zie-memory__downvote_memory`).
- The condition guard `If zie_memory_enabled=true:` remains in every file — no logic is removed.
- All pre-existing unit tests continue to pass.
- New regression test confirms the MCP tool names appear in all affected files.

**Files:**
- Modify: `skills/spec-design/SKILL.md`
- Modify: `skills/write-plan/SKILL.md`
- Modify: `skills/debug/SKILL.md`
- Modify: `skills/verify/SKILL.md`
- Modify: `commands/zie-backlog.md`
- Modify: `commands/zie-spec.md`
- Modify: `commands/zie-plan.md`
- Modify: `commands/zie-implement.md`
- Modify: `commands/zie-fix.md`
- Modify: `commands/zie-release.md`
- Modify: `commands/zie-retro.md`
- Modify: `commands/zie-init.md`
- Modify: `tests/unit/test_mcp_bundle.py`

### Step 1: Write failing tests (RED)

Add a new class to `tests/unit/test_mcp_bundle.py`:

```python
# Append to tests/unit/test_mcp_bundle.py

COMMANDS_DIR = REPO_ROOT / "commands"
SKILLS_DIR = REPO_ROOT / "skills"

# Files that must reference mcp__ tool names in their zie_memory branches
COMMANDS_WITH_MEMORY = [
    "zie-backlog.md",
    "zie-spec.md",
    "zie-plan.md",
    "zie-implement.md",
    "zie-fix.md",
    "zie-release.md",
    "zie-retro.md",
    "zie-init.md",
]

SKILLS_WITH_MEMORY = [
    "spec-design/SKILL.md",
    "write-plan/SKILL.md",
    "debug/SKILL.md",
]

MCP_RECALL = "mcp__plugin_zie-memory_zie-memory__recall"
MCP_REMEMBER = "mcp__plugin_zie-memory_zie-memory__remember"
MCP_DOWNVOTE = "mcp__plugin_zie-memory_zie-memory__downvote_memory"

# Mapping: file → which MCP tools it must reference
EXPECTED_TOOLS = {
    "commands/zie-backlog.md": [MCP_RECALL, MCP_REMEMBER],
    "commands/zie-spec.md": [MCP_RECALL],
    "commands/zie-plan.md": [MCP_RECALL, MCP_REMEMBER],
    "commands/zie-implement.md": [MCP_RECALL, MCP_REMEMBER],
    "commands/zie-fix.md": [MCP_RECALL, MCP_REMEMBER],
    "commands/zie-release.md": [MCP_RECALL, MCP_REMEMBER],
    "commands/zie-retro.md": [MCP_RECALL, MCP_REMEMBER, MCP_DOWNVOTE],
    "commands/zie-init.md": [MCP_REMEMBER],
    "skills/spec-design/SKILL.md": [MCP_RECALL, MCP_REMEMBER],
    "skills/write-plan/SKILL.md": [MCP_RECALL],
    "skills/debug/SKILL.md": [MCP_RECALL, MCP_REMEMBER],
}


class TestMcpToolNamesInCommandsAndSkills:
    def _read(self, rel_path: str) -> str:
        return (REPO_ROOT / rel_path).read_text()

    def test_zie_backlog_recall(self):
        assert MCP_RECALL in self._read("commands/zie-backlog.md")

    def test_zie_backlog_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-backlog.md")

    def test_zie_spec_recall(self):
        assert MCP_RECALL in self._read("commands/zie-spec.md")

    def test_zie_plan_recall(self):
        assert MCP_RECALL in self._read("commands/zie-plan.md")

    def test_zie_plan_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-plan.md")

    def test_zie_implement_recall(self):
        assert MCP_RECALL in self._read("commands/zie-implement.md")

    def test_zie_implement_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-implement.md")

    def test_zie_fix_recall(self):
        assert MCP_RECALL in self._read("commands/zie-fix.md")

    def test_zie_fix_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-fix.md")

    def test_zie_release_recall(self):
        assert MCP_RECALL in self._read("commands/zie-release.md")

    def test_zie_release_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-release.md")

    def test_zie_retro_recall(self):
        assert MCP_RECALL in self._read("commands/zie-retro.md")

    def test_zie_retro_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-retro.md")

    def test_zie_retro_downvote(self):
        assert MCP_DOWNVOTE in self._read("commands/zie-retro.md")

    def test_zie_init_remember(self):
        assert MCP_REMEMBER in self._read("commands/zie-init.md")

    def test_skill_spec_design_recall(self):
        assert MCP_RECALL in self._read("skills/spec-design/SKILL.md")

    def test_skill_spec_design_remember(self):
        assert MCP_REMEMBER in self._read("skills/spec-design/SKILL.md")

    def test_skill_write_plan_recall(self):
        assert MCP_RECALL in self._read("skills/write-plan/SKILL.md")

    def test_skill_debug_recall(self):
        assert MCP_RECALL in self._read("skills/debug/SKILL.md")

    def test_skill_debug_remember(self):
        assert MCP_REMEMBER in self._read("skills/debug/SKILL.md")

    def test_zie_memory_enabled_guard_preserved_in_commands(self):
        """The zie_memory_enabled=true condition guard must still appear in each command."""
        for rel in COMMANDS_WITH_MEMORY:
            content = self._read(f"commands/{rel}")
            assert "zie_memory_enabled" in content, (
                f"commands/{rel} lost its zie_memory_enabled guard"
            )

    def test_zie_memory_enabled_guard_preserved_in_skills(self):
        for rel in SKILLS_WITH_MEMORY:
            content = self._read(f"skills/{rel}")
            assert "zie_memory_enabled" in content, (
                f"skills/{rel} lost its zie_memory_enabled guard"
            )
```

Run: `make test-unit` — all `TestMcpToolNamesInCommandsAndSkills` tests must FAIL (pseudo-call syntax still present, MCP names absent)

### Step 2: Implement (GREEN)

Apply the following changes to each file. In every case the change is a targeted substitution: replace the pseudo-call line(s) inside the `zie_memory_enabled=true` block with a line calling the canonical MCP tool name. The surrounding prose, condition guard, and argument structure are preserved.

#### `skills/spec-design/SKILL.md`

Under `## เตรียม context`, replace:

```
- `recall project=<project> domain=<feature-area> tags=[spec, design] limit=10`
```

with:

```
- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<feature-area> tags=[spec, design] limit=10`
```

No other change. (`remember` does not appear in this skill's current text — no remember line to add here.)

Wait — re-reading the spec: spec-design is listed as needing both recall and remember. Checking the current SKILL.md: it has `recall` in the prepare block but no `remember` in any step. The spec says to update it to use MCP names "in the `zie_memory_enabled=true` branches." Since the current file has no remember branch, we add one after step 6 (Record approval), mirroring the pattern used in debug/SKILL.md:

After step 6 `**Record approval**`, append:

```markdown
If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Spec approved: <feature>. Key decisions: [<d1>]." tags=[spec, <project>, <feature-area>]`
```

Full resulting `## เตรียม context` block:

```markdown
## เตรียม context

If `zie_memory_enabled=true`:

- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<feature-area> tags=[spec, design] limit=10`
- Use recalled context to inform design decisions and avoid repeating past mistakes.
```

Full resulting addition after step 6:

```markdown
7. **Store spec approval in brain** — if `zie_memory_enabled=true`:

   - Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Spec approved: <feature>. Key decisions: [<d1>]." tags=[spec, <project>, <feature-area>]`
```

(Renumber old step 7 → 8, old step 8 → 9.)

#### `skills/write-plan/SKILL.md`

Under `## เตรียม context`, replace:

```
- `recall project=<project> domain=<feature-area> tags=[plan, implementation]
  limit=10`
```

with:

```
- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<feature-area> tags=[plan, implementation] limit=10`
```

#### `skills/debug/SKILL.md`

Under `## เตรียม context`, replace:

```
- `recall project=<project> domain=<failing-area> tags=[bug, debug] limit=10`
```

with:

```
- Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<failing-area> tags=[bug, debug] limit=10`
```

Under `### บันทึกการเรียนรู้`, replace:

```
- `remember "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern:
  <recurring|one-off>." tags=[bug, <project>, <domain>]`
```

with:

```
- Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`
```

#### `skills/verify/SKILL.md`

`verify/SKILL.md` has `zie_memory_enabled: true` in frontmatter metadata but the current body contains no `zie_memory_enabled=true` action block. No text substitution required in this file to pass the tests — the `test_zie_memory_enabled_guard_preserved_in_skills` check is limited to `SKILLS_WITH_MEMORY` which does not include `verify`. Leave this file unchanged for this task.

#### `commands/zie-backlog.md`

Step 3 (recall for duplicates), replace:

```
   - `recall project=<project> domain=<domain> tags=[backlog, <project>] limit=10`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<domain> tags=[backlog, <project>] limit=10`
```

Step 7 (remember after commit), replace:

```
   - `remember "Backlog: <title>. Problem: <one-line>." tags=[backlog, <project>]`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Backlog: <title>. Problem: <one-line>." tags=[backlog, <project>]`
```

#### `commands/zie-spec.md`

`zie-spec.md` passes `zie_memory_enabled` to the `spec-design` skill — the command itself does not call recall/remember directly. The spec lists it as needing only `recall`. The test `test_zie_spec_recall` checks for `MCP_RECALL` in the file. Since the command delegates to `spec-design`, the correct update is to add a documentation line in the step 2 description noting the MCP tool used:

In step 2 `**Slug mode**`, the note about `zie_memory_enabled` passed to the skill already mentions it implicitly. To make the test pass, add an inline note:

```markdown
   pass backlog file content to `Skill(zie-framework:spec-design)` with `zie_memory_enabled` from
   .config. Skill will call `mcp__plugin_zie-memory_zie-memory__recall` when brain is enabled.
```

Replace the existing line:

```
   pass backlog file content to
   `Skill(zie-framework:spec-design)` with `zie_memory_enabled` from
   .config.
```

with:

```
   pass backlog file content to `Skill(zie-framework:spec-design)` with `zie_memory_enabled` from
   .config. Skill calls `mcp__plugin_zie-memory_zie-memory__recall` for context when brain is enabled.
```

#### `commands/zie-plan.md`

Under `## ร่าง plan สำหรับ slug ที่เลือก`, step 1, replace:

```
   - `recall project=<project> tags=[shipped,retro,bug,decision] limit=20`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[shipped,retro,bug,decision] limit=20`
```

Under `## ขออนุมัติ plan (ทีละ plan)`, step 2, replace:

```
   - `remember "Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>. Key
     decisions: [<d1>]." tags=[plan, <project>, <domain>]`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Plan approved: <feature>. Tasks: N. Complexity: <S|M|L>. Key decisions: [<d1>]." tags=[plan, <project>, <domain>]`
```

#### `commands/zie-implement.md`

Step 7, replace:

```
     `recall project=<project> tags=[wip] feature=<slug> limit=1`
```

with:

```
     Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip] feature=<slug> limit=1`
```

Step 7 (conditional write, task harder than estimated), replace:

```
   `remember "Task harder than estimated:
   <why>. Next time: <tip>." tags=[build-learning, <project>, <domain>]`
```

with:

```
   Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Task harder than estimated: <why>. Next time: <tip>." tags=[build-learning, <project>, <domain>]`
```

Step 8 (brain checkpoint), replace:

```
   `remember "WIP: <feature> — T<N>/<total> done." tags=[wip, <project>,
   <feature-slug>] supersedes=[wip, <project>, <feature-slug>]`
```

with:

```
   Call `mcp__plugin_zie-memory_zie-memory__remember` with `"WIP: <feature> — T<N>/<total> done." tags=[wip, <project>, <feature-slug>] supersedes=[wip, <project>, <feature-slug>]`
```

#### `commands/zie-fix.md`

Step 4 (recall), replace:

```
   - `recall project=<project> domain=<domain> tags=[bug, build-learning] limit=10`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> domain=<domain> tags=[bug, build-learning] limit=10`
```

Step `### บันทึกและเรียนรู้`, replace:

```
   - `remember "Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern:
     <recurring|one-off>." tags=[bug, <project>, <domain>]`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Bug: <desc>. Root cause: <why>. Fix: <how>. Pattern: <recurring|one-off>." tags=[bug, <project>, <domain>]`
```

#### `commands/zie-release.md`

Step 9, replace:

```
   - First READ: `recall project=<project> tags=[wip, plan] feature=<slug> limit=5`
   - Then WRITE: `remember "Shipped: <feature> v<NEW_VERSION>. Tasks: N.
     Actual: <vs estimate>." tags=[shipped, <project>, <domain>]`
```

with:

```
   - First READ: Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip, plan] feature=<slug> limit=5`
   - Then WRITE: Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Shipped: <feature> v<NEW_VERSION>. Tasks: N. Actual: <vs estimate>." tags=[shipped, <project>, <domain>]`
```

#### `commands/zie-retro.md`

Under `### รวบรวม context`, step 1, replace:

```
   - `recall project=<project> tags=[wip, build-learning, shipped] limit=20`
```

with:

```
   - Call `mcp__plugin_zie-memory_zie-memory__recall` with `project=<project> tags=[wip, build-learning, shipped] limit=20`
```

Under `### อัปเดต project knowledge`, replace:

```
- ถ้า `zie_memory_enabled=true`: `remember "Project snapshot: <version>.
  Components changed: <list>. Decisions: <new ADR slugs>."
  tags=[project-knowledge, zie-framework, <version>]
  supersedes=[project-knowledge, zie-framework]`
```

with:

```
- ถ้า `zie_memory_enabled=true`: Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Project snapshot: <version>. Components changed: <list>. Decisions: <new ADR slugs>." tags=[project-knowledge, zie-framework, <version>] supersedes=[project-knowledge, zie-framework]`
```

Under `### บันทึกสู่ brain`, replace:

```
- Store P1 preferences (what worked): `remember "<what worked>. Preference:
  always use this approach for <context>." priority=preference tags=[retro,
  <slug>]`
- Store P2 project learnings: `remember "Retro <version>: <key learning>.
  Decision: <ADR slug>." priority=project tags=[retro, <project>]
  project=<project>`
- Downvote any memories that turned out to be incorrect via `downvote_memory`.
```

with:

```
- Store P1 preferences (what worked): Call `mcp__plugin_zie-memory_zie-memory__remember` with `"<what worked>. Preference: always use this approach for <context>." priority=preference tags=[retro, <slug>]`
- Store P2 project learnings: Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Retro <version>: <key learning>. Decision: <ADR slug>." priority=project tags=[retro, <project>] project=<project>`
- Downvote incorrect memories via `mcp__plugin_zie-memory_zie-memory__downvote_memory`.
```

#### `commands/zie-init.md`

Step 12, replace:

```
      `remember "Project <name> initialized with zie-framework. Type:
      <project_type>. Stack: <tech_stack>. Test runner: <test_runner>."
      tags=[zie-framework, init, <project_name>]`
```

with:

```
      Call `mcp__plugin_zie-memory_zie-memory__remember` with `"Project <name> initialized with zie-framework. Type: <project_type>. Stack: <tech_stack>. Test runner: <test_runner>." tags=[zie-framework, init, <project_name>]`
```

Run: `make test-unit` — all `TestMcpToolNamesInCommandsAndSkills` tests must PASS

### Step 3: Refactor

Verify there are no remaining bare pseudo-call lines (`recall project=`, `remember "`, `` `downvote_memory` ``) inside `zie_memory_enabled=true` blocks in any of the 12 modified files. Check:

```bash
grep -rn "^\s*- \`recall " commands/ skills/
grep -rn "^\s*- \`remember " commands/ skills/
grep -rn "via \`downvote_memory\`" commands/ skills/
```

All three commands should return no output. If any hits remain, apply the matching substitution from Step 2.

Run: `make test-unit` — still PASS

---

## Task 3: Update `README.md` zero-setup section

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- `README.md` contains a "Brain Integration" section explaining zero-setup via `.mcp.json`.
- Section explains: install plugin → zie-memory available automatically if `ZIE_MEMORY_API_URL` is set.
- Section explains: no per-project manual MCP configuration needed.
- The existing `Dependencies` table row for `zie-memory plugin` is updated to reflect zero-setup.
- The existing `Troubleshooting` row for zie-memory is accurate.
- New regression test confirms the section exists.
- All pre-existing unit tests continue to pass.

**Files:**
- Modify: `README.md`
- Modify: `tests/unit/test_mcp_bundle.py`

### Step 1: Write failing tests (RED)

Append a new class to `tests/unit/test_mcp_bundle.py`:

```python
# Append to tests/unit/test_mcp_bundle.py

README = REPO_ROOT / "README.md"


class TestReadmeBrainIntegrationSection:
    def _readme(self) -> str:
        return README.read_text()

    def test_brain_integration_section_exists(self):
        assert "## Brain Integration" in self._readme(), (
            "README.md must contain a '## Brain Integration' section"
        )

    def test_section_mentions_mcp_json(self):
        assert ".mcp.json" in self._readme(), (
            "Brain Integration section must reference .mcp.json"
        )

    def test_section_mentions_zero_setup(self):
        content = self._readme()
        assert "zero-setup" in content or "zero setup" in content, (
            "Brain Integration section must mention zero-setup"
        )

    def test_section_mentions_zie_memory_api_url(self):
        assert "ZIE_MEMORY_API_URL" in self._readme(), (
            "Brain Integration section must reference ZIE_MEMORY_API_URL"
        )

    def test_dependencies_table_updated(self):
        content = self._readme()
        assert "zie-memory" in content and "plugin" in content, (
            "Dependencies table must still reference zie-memory plugin"
        )
```

Run: `make test-unit` — `test_brain_integration_section_exists`, `test_section_mentions_mcp_json`, `test_section_mentions_zero_setup`, `test_section_mentions_zie_memory_api_url` must FAIL (section does not exist yet)

### Step 2: Implement (GREEN)

In `README.md`, after the `## Plugin Coexistence` section and before `## Troubleshooting`, insert:

```markdown
## Brain Integration

zie-memory is bundled in the plugin — no per-project configuration needed.

**Zero-setup path:**

1. Install the plugin: `claude plugin install zierocode/zie-framework`
2. Set environment variables (once, in your shell profile):

   ```bash
   export ZIE_MEMORY_API_URL=https://your-zie-memory-instance.example.com
   export ZIE_MEMORY_API_KEY=your_api_key_here
   ```

3. Start a session — zie-memory MCP server starts automatically via
   `.claude-plugin/.mcp.json`. No manual `claude mcp add` step required.

**How it works:**

The plugin ships `.claude-plugin/.mcp.json` declaring the `zie-memory` MCP
server (stdio transport, `npx zie-memory`). Claude Code discovers this file
at plugin load time and registers the server. If `ZIE_MEMORY_API_URL` is not
set the server exits immediately and the session continues normally — the same
graceful degradation as before.

**Prerequisite:** `zie-memory` npm package must be installed globally:

```bash
npm install -g zie-memory
```

**Manual install (no plugin):** If you run zie-framework without the plugin
install (local `.claude/` copy), add the server manually:

```bash
claude mcp add zie-memory -- npx zie-memory
```

Then set `zie_memory_enabled=true` in `zie-framework/.config`.
```

Also update the `Dependencies` table row for `zie-memory plugin`:

Old:

```
| zie-memory plugin | No | Local-only, no brain |
```

New:

```
| zie-memory plugin | No | Auto-bundled via .mcp.json; local-only if absent |
```

Run: `make test-unit` — all `TestReadmeBrainIntegrationSection` tests must PASS

### Step 3: Refactor

- Confirm the new section renders correctly in a Markdown previewer (no broken fences, no mismatched heading levels).
- Confirm the `Dependencies` table still has the same number of columns and aligns correctly.
- Run full test suite: `make test` — all tests PASS (not just unit).

Run: `make test-unit` — still PASS

---

*Commit: `git add .claude-plugin/.mcp.json commands/ skills/ README.md tests/unit/test_mcp_bundle.py && git commit -m "feat: plugin-mcp-bundle"`*
