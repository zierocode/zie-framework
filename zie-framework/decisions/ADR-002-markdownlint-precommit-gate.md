# ADR-002: markdownlint Pre-commit Gate

Date: 2026-03-23
Status: Accepted

## Context

The zie-framework codebase is almost entirely Markdown (commands, skills,
docs). During the SDLC pipeline redesign, inconsistent line lengths, table
formatting, and inline HTML slipped into files across multiple commits. Issues
were only caught during the T12 final pass, requiring a retroactive fix sweep.

Pre-existing `.md` files in `backlog/` and `plans/` had accumulated violations
(MD041, MD040, MD029, MD033) that blocked `git add -A` when the hook was
introduced.

## Decision

Add a `.githooks/pre-commit` hook that runs `npx markdownlint-cli` on all
staged `.md` files before every commit. Configuration in `.markdownlint.json`
with MD013 line length = 120 (relaxed from default 80).

`/zie-init` template installs the hook automatically (`chmod +x` + git config
`core.hooksPath`). Legacy files with pre-existing violations are excluded via
`.markdownlintignore` until they can be cleaned up separately.

## Consequences

- New `.md` files are linted at commit time — violations caught immediately
- Commits with staged lint violations are blocked (exit non-zero)
- `git add -A` on mixed repos requires selective staging to avoid legacy files
- `make lint-md` target added for manual full-repo lint runs
- Teams adopting zie-framework get the hook automatically via `/zie-init`
