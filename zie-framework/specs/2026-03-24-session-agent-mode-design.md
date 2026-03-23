---
approved: true
approved_at: 2026-03-24
backlog: backlog/session-agent-mode.md
---

# Session-Wide Agent Mode (--agent Flag Integration) — Design Spec

**Problem:** zie-framework sessions default to the standard Claude Code system prompt with no mechanism to pre-configure a session for a specific work mode (TDD-focused implementation or read-only analysis), requiring users to manually set context and approve permissions each time.

**Approach:** Add two agent definition files (`agents/zie-implement-mode.md` and `agents/zie-audit-mode.md`) to the plugin, each embedding a targeted system prompt, tool allowlist, and permission mode. Users invoke them via `claude --plugin-dir . --agent zie-framework:zie-implement-mode` (or `zie-audit-mode`); Claude Code applies the agent's system prompt and tool restrictions for the entire session without per-operation approval prompts. A `settings.json` at plugin root documents `zie-implement-mode` as the recommended default agent for active development sessions.

**Components:**
- Create: `agents/zie-implement-mode.md` — frontmatter: `model: sonnet`, `permissionMode: acceptEdits`, `tools: all`; system prompt: SDLC pipeline context, TDD discipline, skill preload hints for `tdd-loop` and `test-pyramid`, awareness of all `/zie-*` commands
- Create: `agents/zie-audit-mode.md` — frontmatter: `model: sonnet`, `permissionMode: plan`, `tools: [Read, Grep, Glob, WebSearch]`; system prompt: analysis-focused, read-only safety contract, instructions to surface findings as backlog candidates rather than applying changes
- Create: `settings.json` at plugin root (`/Users/zie/Code/zie-framework/settings.json`) — documents recommended invocation and sets `"defaultAgent": "zie-implement-mode"` for reference
- Modify: `.claude-plugin/plugin.json` — bump version, add `"agentsDir": "agents"` key to register the agents directory with the plugin loader
- Modify: `zie-framework/project/components.md` — add Agents section to component registry listing both agent files
- Modify: `CLAUDE.md` — add invocation examples under Development Commands

**Data Flow:**

1. User runs `claude --plugin-dir <path-to-plugin> --agent zie-framework:zie-implement-mode` (or `zie-audit-mode`) from any project directory.
2. Claude Code reads `.claude-plugin/plugin.json`, resolves `agentsDir: "agents"`, and loads `agents/zie-implement-mode.md`.
3. The agent frontmatter sets `permissionMode: acceptEdits` and `tools: all` for the session; the embedded system prompt is injected as the session-level system prompt, replacing the standard Claude Code default.
4. The system prompt instructs the agent to treat itself as operating inside the zie-framework SDLC pipeline: it is aware of the 6-stage flow (`/zie-backlog` → `/zie-spec` → `/zie-plan` → `/zie-implement` → `/zie-release` → `/zie-retro`), the WIP=1 rule (ADR-001), and the hook safety contract (ADR-003).
5. For `zie-implement-mode`: the system prompt includes a preamble to invoke `Skill(zie-framework:tdd-loop)` at the start of any implementation task and `Skill(zie-framework:test-pyramid)` before marking a task complete. `permissionMode: acceptEdits` means file writes and shell commands execute without per-operation confirmation.
6. For `zie-audit-mode`: the system prompt enforces read-only behavior — no writes, no shell mutations. Tool restriction to `[Read, Grep, Glob, WebSearch]` provides a hard enforcement layer. `permissionMode: plan` ensures any tool call outside the allowlist is flagged rather than executed.
7. The session runs normally; all `/zie-*` commands and skills remain available and operate under the agent's system prompt context.
8. Session ends; no persistent state is written by the agent itself (no `memory:` key — session scope only).

**Edge Cases:**
- **`agentsDir` key not yet supported by the installed Claude Code version** — plugin still loads without error (unknown keys in `plugin.json` are silently ignored per current plugin loader behavior); agents are simply not resolvable via `--agent zie-framework:` until the version supports it. Users can still manually point to the agent file.
- **`--agent` flag not available in installed Claude Code version** — entire feature is a no-op; no existing command, hook, or skill is modified, so backward compatibility is fully preserved.
- **User runs `zie-audit-mode` then attempts a write command** — tool restriction (`tools: [Read, Grep, Glob, WebSearch]`) hard-blocks the write at the Claude Code runtime layer regardless of system prompt; the agent surfaces a clear "audit mode is read-only" message from its system prompt.
- **User runs `zie-implement-mode` in a project that has not been initialized with `/zie-init`** — the system prompt's SDLC context references files that do not exist (e.g., `zie-framework/ROADMAP.md`). The system prompt must instruct the agent to gracefully degrade: acknowledge the missing state and prompt the user to run `/zie-init`.
- **`settings.json` conflicts with a project-level `settings.json`** — this `settings.json` lives at the plugin root (inside `zie-framework/`), not at the host project root, so there is no collision. It is documentation-oriented, not machine-read by Claude Code for session config.
- **Both agent files reference skills (`tdd-loop`, `test-pyramid`) that require the skill runner** — if `Skill()` invocation is unavailable (e.g., plugin not fully loaded), the system prompt must degrade gracefully: mention the skills by name as manual steps rather than hard-invoking them.
- **`model: sonnet` in agent frontmatter conflicts with org/project model policy** — Claude Code inherits the session model override if the frontmatter model is unavailable; no special handling needed in the agent file.

**Out of Scope:**
- Adding persistent cross-session memory to either agent (no `memory:` key — these are session-mode configurators, not accumulating reviewers like the reviewer agents in `ADR-009`).
- Creating a `zie-review-mode` agent or additional modes beyond implement and audit — the two modes cover the primary use cases identified in the backlog item.
- Modifying any existing `/zie-*` command to require or detect agent mode — commands remain mode-agnostic and function identically inside or outside an agent session.
- Changing default behavior for users who do not pass `--agent` — the standard Claude Code session prompt remains the default.
- CI/CD integration or non-interactive use of agent mode — the `--agent` flag targets interactive developer sessions only.
- Removing or replacing the skills (`tdd-loop`, `test-pyramid`) with agent equivalents — skills remain the primary execution unit; the agent mode system prompt references them, not replaces them.
