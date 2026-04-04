---
approved: false
approved_at:
backlog: backlog/audit-mcp-check.md
---

# Audit MCP Server Usage Check — Implementation Plan

**Goal:** Add an inline MCP server usage check to Agent 2 of `/zie-audit` that warns on configured-but-unreferenced MCP servers.
**Architecture:** Pure command-file edit — no new hooks or Python files. The check is appended to Agent 2's instruction block inside `commands/zie-audit.md`. It reads `~/.claude/settings.json` and `.claude/settings.json`, extracts `mcpServers` key names, greps `commands/*.md` and `skills/*/SKILL.md` for `mcp__<name>__` patterns, and emits LOW findings for any server with zero matches.
**Tech Stack:** Markdown (command definition), Python pseudocode (inline detection algorithm)

---

## File Map

| Action | File | Responsibility |
| --- | --- | --- |
| Modify | `commands/zie-audit.md` | Add MCP check sub-block inside Agent 2 section |

## Task Sizing

This is a **S plan** — single file, 3 tasks.

---

## Task 1: Read zie-audit.md and identify insertion point

**Acceptance Criteria:**
- Agent 2's instruction block in `commands/zie-audit.md` is identified.
- The correct insertion location (end of Agent 2 performance focus, before "Output:") is confirmed.
- No content is modified yet.

**Files:**
- Read: `commands/zie-audit.md`

- [ ] **Step 1: Read and annotate (RED)**
  Read `commands/zie-audit.md`. Confirm that Agent 2 ends its instruction block with:
  ```
  Output: findings list with severity.
  ```
  and that the MCP check block is absent. This task has no test — it is a read/confirm step.

- [ ] **Step 2: Confirm insertion point (GREEN)**
  Target insertion: immediately before `Output: findings list with severity.` inside the Agent 2 block (after the Performance focus paragraph).

- [ ] **Step 3: Refactor**
  No code changes yet — proceed to Task 2.

---

## Task 2: Add MCP check block to Agent 2

<!-- depends_on: Task 1 -->

**Acceptance Criteria:**
- AC1: Agent 2 contains a "MCP Server Usage" sub-check with the detection algorithm described in the spec.
- AC2: Graceful skip conditions are present (no settings file, no `mcpServers` key, empty object).
- AC3: LOW finding message matches spec exactly: `MCP server '<name>' configured but never referenced in commands or skills — consider removing to reduce context overhead`.
- AC4: Both settings file paths are checked (`~/.claude/settings.json` and `.claude/settings.json`).
- AC5: Grep scope covers `commands/*.md` and `skills/*/SKILL.md`.
- AC6: Multiple unused servers each produce a separate finding.

**Files:**
- Modify: `commands/zie-audit.md`

- [ ] **Step 1: Write failing tests (RED)**
  No unit tests apply (pure markdown command). Verify AC by inspection:
  ```bash
  grep -c "mcp__<name>__" commands/zie-audit.md
  # Expected: 0  (check not yet present)
  ```
  Run: not applicable — command file only.

- [ ] **Step 2: Implement (GREEN)**
  Insert the following block inside Agent 2, immediately before the existing `Output: findings list with severity.` line:

  ```markdown
  **MCP Server Usage check** (context efficiency):

  Read settings files to build the configured server list:
  1. Expand `~/.claude/settings.json` to absolute path. Read if it exists.
  2. Read `.claude/settings.json` (repo-root-relative) if it exists.
  3. From each file that exists, extract keys of the `mcpServers` object.
     Union all keys across both files into `configured_servers`.
  4. If no settings file exists, or `mcpServers` is absent or `{}` in all found
     files → skip this check entirely (no output).

  For each name in `configured_servers`:
  - Grep `commands/*.md` and `skills/*/SKILL.md` for the literal prefix `mcp__<name>__`.
  - If zero matches found across both scopes → emit LOW finding:
    ```
    MCP server '<name>' configured but never referenced in commands or skills
    — consider removing to reduce context overhead
    ```
  - If at least one match found → no finding for this server (clean pass).
  ```

- [ ] **Step 3: Refactor**
  Review the inserted block for clarity and consistency with surrounding Agent 2 language (imperative tone, same bullet style).
  Run: `make lint` — must PASS.

---

## Task 3: Verify insertion by grep

<!-- depends_on: Task 2 -->

**Acceptance Criteria:**
- AC1–AC6 verified by grep evidence.
- `make lint` passes.

**Files:**
- Read: `commands/zie-audit.md` (verify only)

- [ ] **Step 1: Grep verification (RED → GREEN confirm)**
  ```bash
  grep -n "MCP Server Usage" commands/zie-audit.md
  # Expected: line number present inside Agent 2 block

  grep -n "mcp__<name>__" commands/zie-audit.md
  # Expected: at least 2 occurrences (grep step + finding message)

  grep -n "consider removing to reduce context overhead" commands/zie-audit.md
  # Expected: 1 occurrence

  grep -n "skip this check entirely" commands/zie-audit.md
  # Expected: 1 occurrence
  ```

- [ ] **Step 2: Lint (GREEN)**
  ```bash
  make lint
  # Expected: no errors
  ```

- [ ] **Step 3: Refactor**
  No changes needed. Task complete.

---

## Completion Checklist

- [ ] Task 1 complete (insertion point identified)
- [ ] Task 2 complete (MCP check block inserted)
- [ ] Task 3 complete (grep verification + lint pass)
- [ ] `commands/zie-audit.md` is the only file modified
- [ ] All 6 ACs verifiable by reading the updated command
