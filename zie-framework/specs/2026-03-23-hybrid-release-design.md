---
approved: true
approved_at: 2026-03-23
backlog: backlog/hybrid-release.md
---

# Hybrid Release — Design Spec

**Problem:** `/zie-release` handles project-specific git ops and publish steps
itself, making the SDLC layer non-generic and fragile across project types.

**Approach:** Split release into two layers — SDLC layer (`/zie-release`: gates,
versioning, changelog, ROADMAP update) delegates to Publishing layer
(`make release NEW=<version>`: project-defined git ops + publish). `zie-init`
negotiates a typed skeleton for `make release` with the user at init time.
`/zie-release` checks Makefile readiness before delegating.

**Components:**

- `commands/zie-release.md` — remove git ops from final step; add readiness
  gate + `make release NEW=<version>` call
- `commands/zie-init.md` — add step to draft, present, and write `make release`
  skeleton into Makefile (after Makefile creation step)
- `templates/Makefile.python.template` — add `release` skeleton with
  `ZIE-NOT-READY` marker
- `templates/Makefile.typescript.template` — add `release` skeleton with
  `ZIE-NOT-READY` marker

**Data Flow:**

```
/zie-release
  1. Run test gates (test-unit, test-int, test-e2e)
  2. Determine version bump (patch / minor / major)
  3. Update ROADMAP Now → Done
  4. Draft + approve CHANGELOG entry
  5. Readiness gate: scan Makefile for ZIE-NOT-READY in release target
       → found    : STOP — print "Implement make release NEW=<v> first"
       → not found: proceed
  6. Call: make release NEW=<version>
  7. Trigger /zie-retro

/zie-init (after Makefile creation, existing + greenfield paths)
  1. Skip if Makefile already has a `release` target (idempotent)
  2. Draft skeleton based on project_type:
       python-api     : sed VERSION + pyproject.toml skeleton + comment
       python-plugin  : sed VERSION + plugin.json skeleton + comment
       typescript-cli : npm version + npm publish skeleton + comment
       typescript-full: npm version + vercel deploy skeleton + comment
       (unknown)      : generic skeleton with detailed TODO comment
  3. Present to user:
       "Here's the make release target I'll add to your Makefile.
        Does this look right? (yes / no / edit)"
  4. Iterate until approved, then write to Makefile
```

**Skeleton marker:**

```makefile
release:
	@echo "ZIE-NOT-READY: implement make release NEW=$(NEW) for this project"
	@exit 1
```

User removes `ZIE-NOT-READY` lines and replaces with real publish steps.
`/zie-release` scans for the literal string `ZIE-NOT-READY` — if absent,
the target is considered ready.

**Edge Cases:**

- `release` target already exists → `zie-init` skips (idempotent, no overwrite)
- User removes `ZIE-NOT-READY` but target still broken → `make` fails with
  native error; user asks AI to fix (intentional — we don't over-validate)
- `$(NEW)` not passed → skeleton's `@exit 1` fires; real targets should
  guard: `ifndef NEW $(error NEW is required) endif`
- Makefile does not exist → `zie-init` creates it first (existing behavior),
  then adds skeleton
- `make release` exits non-zero → `/zie-release` surfaces error and stops;
  no rollback (out of scope)

**Out of Scope:**

- Auto-implementing publish steps (user writes project-specific logic)
- Dry-run validation of `make release`
- Rollback on publish failure
- Multi-project monorepo release coordination
- CI/CD pipeline integration (separate backlog item)
