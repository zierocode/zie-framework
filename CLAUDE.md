# zie-framework

Solo developer SDLC framework plugin for Claude Code.

## What This Is

A Claude Code plugin that installs a structured development workflow into any
project:

- **Ambient intent detection** via hooks
- **Spec-first TDD** via `/zie-*` commands
- **Brain integration** with zie-memory
- **Safety guardrails** via PreToolUse hooks

## Tech Stack

- **Runtime**: Python 3.x (all hooks)
- **Plugin format**: Claude Code plugin (`.claude-plugin/plugin.json` +
  `hooks/hooks.json`)
- **Commands**: Markdown files in `commands/` (slash commands)
- **Skills**: Markdown files in `skills/` (invoked via Skill tool)
- **Templates**: Reusable file templates in `templates/`

### Optional Dependencies

| Dependency | Purpose | Required? |
| --- | --- | --- |
| `pytest` + `pytest-cov` | Unit + integration test runner | For `make test` |
| `coverage` | Subprocess coverage measurement | For `make test-unit` |
| `playwright` | Browser automation for frontend hooks | Only if `playwright_enabled: true` |
| zie-memory API | Cross-session memory persistence | Only if `zie_memory_enabled: true` |

## Project Structure

```text
.claude-plugin/plugin.json  # plugin metadata
hooks/hooks.json            # hook event → script mapping
hooks/*.py                  # hook implementations (Python)
commands/zie-*.md           # slash command definitions
skills/*/SKILL.md           # skill definitions
templates/                  # templates for /zie-init
zie-framework/              # self-managed SDLC state (this repo uses itself)
  ├── PROJECT.md            # hub: project overview + knowledge links
  ├── project/              # spokes: architecture, components, decisions
  ├── ROADMAP.md            # backlog + active work
  ├── specs/                # feature design docs
  ├── plans/                # implementation plans
  └── decisions/            # ADR log
```

## Development Commands

```bash
make test-fast        # fast TDD feedback — changed files + last-failed (use during RED/GREEN)
make test-ci          # full suite with coverage gate — use before commit and in CI
make test-unit        # run unit tests with subprocess coverage measurement
make test-int         # run integration tests (require live Claude session — not in CI)
make test             # full test suite (unit + integration + md lint)
make bump NEW=x.y.z   # bump VERSION + plugin.json + PROJECT.md
make sync-version     # re-sync all version files to current VERSION
make push m="msg"     # commit + push to dev
make start            # open Claude with local plugin (ENV=dev)
make setup            # install git hooks + python deps (run once)
make archive-prune    # Prune archive/ files older than 90 days (guard: ≥20 files)
```

## Agent Mode Sessions

Plugin loads from marketplace cache (`github:zierocode/zie-framework`).
After `make release`, restart Claude to pick up the new version.

```bash
# TDD-focused session — permissionMode: acceptEdits, all tools
claude --agent zie-framework:zie-implement-mode

# Read-only audit session — permissionMode: plan, restricted tools
claude --agent zie-framework:zie-audit-mode
```

## Key Rules

- **Never commit secrets** — hooks, templates, commands are all public
- **Idempotent commands** — all `/zie-*` commands must be safe to re-run
- **Graceful degradation** — every feature must work without optional
  dependencies (zie-memory, playwright)
- **Hook safety** — hooks must NEVER crash or block Claude when optional tools
  are missing
- **Test runner**: pytest

## Hook Configuration

Optional keys in `zie-framework/.config` (JSON):

| Key | Default | Values | Description |
| --- | --- | --- | --- |
| `safety_check_mode` | `"regex"` | `"regex"`, `"agent"`, `"both"` | Controls `safety_check_agent.py`. `"regex"` — fast pattern matching only, no subprocess spawned. `"agent"` — spawns a Claude subagent on every Bash call to evaluate safety. `"both"` — runs regex first, then agent. Use `"regex"` unless you need AI-level judgment on commands. |
| `subprocess_timeout_s` | `5` | `int` | Timeout (s) for `git` subprocess calls in `failure-context.py` and `stop-guard.py`. |
| `safety_agent_timeout_s` | `30` | `int` | Timeout (s) for the Claude subagent subprocess in `safety_check_agent.py`. |
| `auto_test_max_wait_s` | `15` | `int` | Wall-clock kill limit (s) for `auto-test.py`. Set to `0` to disable (falls back to `auto_test_timeout_ms`). |
| `auto_test_timeout_ms` | `30000` | `int` | Fallback subprocess timeout (ms) for `auto-test.py` when `auto_test_max_wait_s` is `0`. |

## Hook Error Handling Convention

All hooks follow a two-tier pattern:

1. **Outer guard** — event parse + early-exit checks. Use bare `except Exception`
   → `sys.exit(0)`. This tier must _never_ block Claude regardless of input.
2. **Inner operations** — file I/O, API calls, subprocess. Use
   `except Exception as e: print(f"[zie-framework] <hook-name>: {e}", file=sys.stderr)`.
   Hook still exits 0 after logging; Claude is never blocked.

Never raise an unhandled exception from a hook. Never use a non-zero exit code.

## SDLC State

Managed by zie-framework itself — see `zie-framework/ROADMAP.md` for current
backlog.
