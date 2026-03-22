# zie-framework

Solo developer SDLC framework for Claude Code. Spec-first, TDD, automated testing, brain-integrated.

## Install

```bash
claude plugin install zierocode/zie-framework
```

## Commands

| Command | Phase | Description |
|---------|-------|-------------|
| `/zie-init` | Bootstrap | Initialize framework in a project |
| `/zie-status` | Anytime | Show current SDLC state |
| `/zie-idea` | Ideation | Brainstorm → spec → implementation plan |
| `/zie-build` | Build | TDD feature loop |
| `/zie-fix` | Debug | Bug path — skip ideation, go to fix |
| `/zie-ship` | Release | Full test gate → merge dev→main → tag |
| `/zie-retro` | Learn | Retrospective + ADRs + brain storage |

## How It Works

1. **Ambient intent detection** — type anything, hooks detect your SDLC phase and suggest the right command
2. **Auto-test on save** — PostToolUse hook runs unit tests after every file edit
3. **Session resume** — SessionStart hook injects current SDLC state at every session start
4. **Brain integration** — works with zie-memory for cross-session context (optional)

## Dependencies

| Dependency | Required | Graceful degradation |
|-----------|----------|---------------------|
| Claude Code | Yes | — |
| Python 3.x | Yes | Hooks need Python |
| superpowers plugin | No | Inline Q&A mode |
| zie-memory plugin | No | Local-only, no brain |
| playwright | No | `/zie-ship` skips e2e gate |
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
│   │   └── decisions.md     # ADR log (append-only)
│   ├── specs/               # design specs (output of /zie-idea)
│   ├── plans/               # implementation plans (output of /zie-plan)
│   ├── decisions/           # ADR files (output of /zie-retro)
│   └── evidence/            # milestone screenshots (gitignored by default)
├── tests/                   # test code (part of project, not framework)
├── Makefile                 # standard targets: test, push, ship
├── VERSION                  # semver
└── CHANGELOG.md             # auto-generated
```

## Plugin Coexistence

Works alongside zie-memory plugin. Both install hooks independently — no conflicts.
