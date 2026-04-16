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

- **Agent mode**: `claude --agent zie-framework:builder` (TDD) · `auditor` (read-only)
- **Never commit secrets** — hooks, templates, commands are all public
- **Idempotent commands** — all commands must be safe to re-run
- **Graceful degradation** — every feature must work without optional
  dependencies (zie-memory, playwright)
- **Hook safety** — hooks must NEVER crash or block Claude when optional tools
  are missing
- **Test runner**: pytest
- **Non-Claude models**: `model:`/`effort:` frontmatter ignored; `--agent` unavailable → use `/implement` directly (ADR-066)

## Non-Claude Model Compatibility

Running on `glm-5.1:cloud`, Ollama, or other non-Claude providers:

| Feature | Claude Code | Non-Claude |
|---------|-------------|------------|
| `model:` frontmatter | Used for model routing (ADR-022/ADR-063) | Ignored — runs on provider's default model |
| `effort:` frontmatter | Routes to haiku/sonnet/opus | Ignored — no effect |
| `--agent` flag | Available (`claude --agent`) | Unavailable — use Skill() directly |
| Safety hooks | Claude models | Regex fallback when Claude unavailable (ADR-066) |

**Fallback pattern:**
```bash
# Claude Code: use agent mode
claude --agent zie-framework:builder

# Non-Claude: run /implement directly in current session
/implement
```

See ADR-066 for full details.

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
| `/spike` | Time-boxed exploration in an isolated sandbox |
| `/fix` | Debug and fix failing tests or broken features (`--hotfix` for emergencies, `--chore` for maintenance) |
| `/status` | Show current SDLC state (`--guide` for walkthrough, `--health` for hook check, `--brief` for design brief) |
| `/audit` | Project audit across 9 dimensions |
| `/resync` | Rescan codebase + update knowledge docs |
| `/next` | Rank backlog items (`--rescue` for pipeline diagnosis) |

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
- **Optional**: `playwright`/`zie-memory` (gated by config flags)

