# zie-framework

Solo developer SDLC framework plugin for Claude Code.

<!-- STABLE: do not move below dynamic section -->

## Project Structure

```text
.claude-plugin/plugin.json  # plugin metadata
hooks/hooks.json            # hook event → script mapping
hooks/*.py / commands/*.md / skills/*/SKILL.md / templates/
zie-framework/              # SDLC state (this repo uses itself)
  ├── PROJECT.md + project/  # knowledge hub + spokes
  └── ROADMAP.md + specs/ + plans/ + decisions/
```

## Key Rules

- **Agent mode**: `claude --agent zie-framework:zie-implement-mode` (TDD) · `zie-audit-mode` (read-only)
- **Never commit secrets** — hooks, templates, commands are all public
- **Idempotent commands** — all commands must be safe to re-run
- **Graceful degradation** — every feature must work without optional
  dependencies (zie-memory, playwright)
- **Hook safety** — hooks must NEVER crash or block Claude when optional tools
  are missing
- **Test runner**: pytest

## Hook Reference Docs
- Hook Output Convention · Hook Error Handling Convention · Hook Context Hints → `zie-framework/project/hook-conventions.md`
- Hook Configuration Keys → `zie-framework/project/config-reference.md`

## SDLC Commands

| Command | Purpose |
| --- | --- |
| `/init` | Bootstrap: initialize framework in a new project |
| `/backlog` | Capture a new idea as a backlog item |
| `/spec` | Write design spec for a backlog item |
| `/plan` | Draft implementation plan from spec |
| `/implement` | TDD implementation loop (WIP=1) |
| `/release` | Release gate — merge dev→main, version bump |
| `/retro` | Post-release retrospective + ADRs |
| `/sprint` | Sprint clear — batch all items: spec + plan + implement + release + retro |
| `/chore` | Maintenance task track — no spec required |
| `/hotfix` | Emergency fix track — describe → fix → ship without full pipeline |
| `/spike` | Time-boxed exploration in an isolated sandbox |
| `/fix` | Debug and fix failing tests or broken features |
| `/status` | Show current SDLC state |
| `/audit` | Project audit across 9 dimensions |
| `/resync` | Rescan codebase + update knowledge docs |
| `/next` | Rank backlog items by impact, age, and dependencies — recommend top 3 |
| `/rescue` | Pipeline diagnosis — show stuck items + recovery actions |
| `/health` | Hook health + config validation check |
| `/guide` | On-demand framework walkthrough + pipeline position |
| `/brief` | Display `.zie/handoff.md` session brief |

## Development Commands

```bash
make test-fast        # fast TDD feedback — changed files + last-failed (use during RED/GREEN)
make lint             # run ruff lint check (fast, no I/O)
make lint-fix         # auto-fix safe ruff violations
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

<!-- DYNAMIC: version-specific, ok to change -->

## Tech Stack

- **Runtime**: Python 3.x (all hooks)
- **Plugin format**: Claude Code plugin (`.claude-plugin/plugin.json` +
  `hooks/hooks.json`)
- **Commands**: Markdown files in `commands/` (slash commands)
- **Skills**: Markdown files in `skills/` (invoked via Skill tool)
- **Templates**: Reusable file templates in `templates/`
- **Optional**: `playwright` (if `playwright_enabled: true`),
  `zie-memory` API (if `zie_memory_enabled: true`)

## Non-Claude Model Compatibility

- `model:` frontmatter in commands/agents is a Claude Code hint — non-Claude providers ignore it
- `--agent` flag requires Claude Code CLI — use `/implement` directly on non-Claude providers
- `effort:` frontmatter has no effect on non-Claude models
- Safety hooks fall back to regex when Claude models are unavailable (ADR-066)
- `make implement-local` runs `/implement` in current session without agent mode
