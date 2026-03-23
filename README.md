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
| zie-memory plugin | No | Local-only, no brain |
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
