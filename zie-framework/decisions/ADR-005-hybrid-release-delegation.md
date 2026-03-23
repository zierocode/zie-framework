# ADR-005: Hybrid Release — SDLC Gates + Project-Defined Publish

Date: 2026-03-23
Status: Accepted

## Context

`/zie-release` originally handled both quality gates AND the git ops
(merge dev→main, tag, push). This made it impossible for projects with
non-standard publish steps (pip publish, gh release, vercel deploy) to
integrate release publishing into the SDLC flow. Every project needed to
manually implement its own publish step after `/zie-release`, outside the
gate sequence.

## Decision

Split the release responsibility into two layers:

1. **SDLC layer** (`/zie-release`) — runs quality gates (unit tests,
   integration tests, e2e, verify, docs sync), bumps VERSION, updates
   ROADMAP, writes CHANGELOG, commits release files. Then checks for a
   `ZIE-NOT-READY` marker in the project Makefile (readiness gate), and
   if clear, delegates to `make release NEW=<version>`.

2. **Project layer** (`make release`) — project-specific publish steps:
   git merge dev→main, tag, push, and any project-specific publishing
   (pip publish, gh release, npm publish, vercel deploy --prod, etc.).
   Projects get a `ZIE-NOT-READY` skeleton on first `/zie-init`; replace
   the skeleton with real steps before first release.

`/zie-init` negotiates the release skeleton with the user based on
`project_type`, so projects aren't left with a blank Makefile target.

## Consequences

- Projects must implement `make release` before first release (gate
  prevents accidental skeleton execution).
- `/zie-release` no longer does git ops directly — all git ops live in
  `make release` where the project author controls them.
- The SDLC layer is portable across project types; only the publish
  layer is project-specific.
- Easier to customize release steps (bump multiple version files, run
  post-publish tasks) without touching zie-framework internals.
