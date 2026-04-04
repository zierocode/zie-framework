# Hook Conventions

Reference for hook authoring. Loaded on demand — not included in every prompt turn.

## Hook Output Convention

All hooks emit INFO-level progress output using structured `[zie-framework] key: value`
pairs. This applies to **INFO-level output only** — error output uses free-form messages
(see Hook Error Handling Convention below).

**Format:** `[zie-framework] <noun>: <value>`
**Example:** `[zie-framework] wip: 1 task in progress`

Existing compliant hooks (no code changes needed):
- `wip-checkpoint` — already emits structured key: value for INFO output
- `task-completed-gate` — already emits structured key: value for INFO output

Future hooks must follow this convention for INFO-level output.

## Hook Error Handling Convention

All hooks follow a two-tier pattern:

1. **Outer guard** — event parse + early-exit checks. Use bare `except Exception`
   → `sys.exit(0)`. This tier must _never_ block Claude regardless of input.
2. **Inner operations** — file I/O, API calls, subprocess. Use
   `except Exception as e: print(f"[zie-framework] <hook-name>: {e}", file=sys.stderr)`.
   Hook still exits 0 after logging; Claude is never blocked.

Never raise an unhandled exception from a hook. Never use a non-zero exit code.

## Hook Context Hints

Static guidance strings removed from per-event `additionalContext` payloads (kept here for reference):

- **failure-context.py** — Quick fix: run `make test-unit` to reproduce; check output above for root cause.
- **sdlc-compact.py** — [zie-framework] SDLC state restored after context compaction.
- **subagent-context.py** — (see zie-framework/project/context.md)
