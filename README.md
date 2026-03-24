# zie-framework

Solo developer SDLC framework for Claude Code. Spec-first, TDD, automated
testing, brain-integrated.

## Install

```bash
claude plugin install zierocode/zie-framework
```

## Commands

| Command | Stage | Description |
| --- | --- | --- |
| `/zie-init` | Bootstrap | Initialize framework in a project |
| `/zie-status` | Anytime | Show current SDLC state |
| `/zie-resync` | Anytime | Rescan codebase + update knowledge docs |
| `/zie-backlog` | 1 — Capture | Capture a new backlog item |
| `/zie-spec` | 2 — Design | Write a design spec with reviewer loop |
| `/zie-plan` | 3 — Plan | Draft implementation plan + approval |
| `/zie-implement` | 4 — Build | TDD feature loop with impl-reviewer |
| `/zie-release` | 5 — Release | Test gates → readiness → `make release` |
| `/zie-retro` | 6 — Learn | Retrospective + ADRs + brain storage |
| `/zie-fix` | Debug | Bug path — skip to systematic fix |
| `/zie-audit` | Health | 9-dimension audit + external research → backlog |

## Skills

Skills are invoked automatically by commands as subagents — not called directly.

| Skill | Purpose |
| --- | --- |
| `spec-design` | Draft design spec from backlog item |
| `spec-reviewer` | Review spec for completeness and correctness |
| `write-plan` | Convert approved spec into implementation plan |
| `plan-reviewer` | Review plan for feasibility and test coverage |
| `tdd-loop` | RED/GREEN/REFACTOR loop for a single task |
| `impl-reviewer` | Review implementation against spec and plan |
| `verify` | Post-implementation verification gate |
| `test-pyramid` | Test strategy advisor |
| `retro-format` | Format retrospective findings as ADRs |
| `debug` | Systematic bug diagnosis and fix path |
| `zie-audit` | 9-dimension audit analysis (invoked by /zie-audit) |

## Pipeline

```text
/zie-backlog → /zie-spec ──[spec-reviewer]──► /zie-plan ──[plan-reviewer]──►
/zie-implement ──[impl-reviewer per task]──► /zie-release ──[test gates]──► /zie-retro
```

Each stage has a single responsibility. Quality gates run automatically as
subagents at every handoff — max 3 iterations before surfacing to human.

| Stage | Command | Gate |
| --- | --- | --- |
| 1 — Capture | `/zie-backlog` | — |
| 2 — Design | `/zie-spec` | spec-reviewer loop |
| 3 — Plan | `/zie-plan` | plan-reviewer loop |
| 4 — Build | `/zie-implement` | impl-reviewer after each task |
| 5 — Release | `/zie-release` | unit → integration → e2e → verify |
| 6 — Learn | `/zie-retro` | — |

**WIP=1** — one `[ ]` item in the Now lane at a time. Finish or fix before
starting the next feature.

**Batch release** — completed `[x]` items accumulate in Now until
`/zie-release` moves them all to Done with a version tag.

## How It Works

1. **Ambient intent detection** — type anything, hooks detect your SDLC phase
   and suggest the right command
2. **Auto-test on save** — PostToolUse hook runs unit tests after every file
   edit
3. **Session resume** — SessionStart hook injects current SDLC state at every
   session start
4. **Brain integration** — works with zie-memory for cross-session context
   (optional)

## Dependencies

| Dependency | Required | Graceful degradation |
| --- | --- | --- |
| Claude Code | Yes | — |
| Python 3.x | Yes | Hooks need Python |
| zie-memory plugin | No | Auto-bundled via .mcp.json; local-only if absent |
| playwright | No | `/zie-release` skips e2e gate |
| pytest / vitest | No | auto-test hook disabled |

## Directory Structure (in your project)

After `/zie-init`, a `zie-framework/` folder is created in your project root:

```text
your-project/
├── zie-framework/
│   ├── .config              # project type, thresholds, feature flags
│   ├── ROADMAP.md           # single source of truth for backlog
│   ├── PROJECT.md           # hub: project overview + knowledge links
│   ├── project/
│   │   ├── architecture.md  # system design, component relationships
│   │   ├── components.md    # component registry
│   │   └── project/context.md  # ADR log (append-only)
│   ├── specs/               # design specs (output of /zie-spec)
│   ├── plans/               # implementation plans (output of /zie-plan)
│   ├── decisions/           # ADR files (output of /zie-retro)
│   └── evidence/            # milestone screenshots (gitignored by default)
├── tests/                   # test code (part of project, not framework)
├── Makefile                 # standard targets: test, push
├── VERSION                  # semver
└── CHANGELOG.md             # auto-generated
```

## Plugin Coexistence

Works alongside zie-memory plugin. Both install hooks independently — no
conflicts.

## Brain Integration

zie-memory is bundled in the plugin — zero-setup, no per-project configuration needed.

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

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Hook not firing | Run `make setup` to activate `.githooks/`; verify Python 3 is on `PATH` |
| zie-memory not connecting | Check `ZIE_MEMORY_API_KEY` env var; `zie_memory_enabled` must be `true` in `.config` |
| Tests not auto-running | Verify `test_runner` is set in `.config`; run `make test-unit` manually to confirm runner works |

## More

- [CHANGELOG](CHANGELOG.md) — release history
- [SECURITY](SECURITY.md) — vulnerability reporting policy
