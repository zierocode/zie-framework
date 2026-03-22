# zie-framework

Solo developer SDLC framework plugin for Claude Code.

## What This Is

A Claude Code plugin that installs a structured development workflow into any project:
- **Ambient intent detection** via hooks
- **Spec-first TDD** via `/zie-*` commands
- **Brain integration** with zie-memory
- **Safety guardrails** via PreToolUse hooks

## Tech Stack

- **Runtime**: Python 3.x (all hooks)
- **Plugin format**: Claude Code plugin (`.claude-plugin/plugin.json` + `hooks/hooks.json`)
- **Commands**: Markdown files in `commands/` (slash commands)
- **Skills**: Markdown files in `skills/` (invoked via Skill tool)
- **Templates**: Reusable file templates in `templates/`

## Project Structure

```
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
make test-unit   # run unit tests (pytest)
make test        # full test suite
make push m="msg"  # commit + push to dev
```

## Key Rules

- **Never commit secrets** — hooks, templates, commands are all public
- **Idempotent commands** — all `/zie-*` commands must be safe to re-run
- **Graceful degradation** — every feature must work without optional dependencies (zie-memory, superpowers, playwright)
- **Hook safety** — hooks must NEVER crash or block Claude when optional tools are missing
- **Test runner**: pytest

## SDLC State

Managed by zie-framework itself — see `zie-framework/ROADMAP.md` for current backlog.
