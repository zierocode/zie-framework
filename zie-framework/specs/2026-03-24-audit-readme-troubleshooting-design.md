---
approved: true
approved_at: 2026-03-24
backlog: backlog/audit-readme-troubleshooting.md
---

# README Troubleshooting Section — Design Spec

**Problem:** `README.md` has no troubleshooting section and no direct links
to `SECURITY.md` or `CHANGELOG.md`, leaving users without a self-service path
when setup fails.

**Approach:** Add a `## Troubleshooting` section to `README.md` covering the
three most-reported failure modes (hook not firing, zie-memory not connecting,
tests not auto-running). Add a `## More` section with links to `SECURITY.md`
and `CHANGELOG.md`.

**Components:**

- `README.md` — add two new sections at the end of the file

**Data Flow:**

1. Append `## Troubleshooting` section after the existing `## Plugin
   Coexistence` section with three FAQ entries:

   | Symptom | Fix |
   |---|---|
   | Hook not firing | Run `make setup` to activate `.githooks/`; verify Python 3 is on `PATH` |
   | zie-memory not connecting | Check `ZIE_MEMORY_API_KEY` env var; `zie_memory_enabled` must be `true` in `.config` |
   | Tests not auto-running | Verify `test_runner` is set in `.config`; run `make test-unit` manually to confirm runner works |

2. Append `## More` section with direct Markdown links:

   ```markdown
   - [CHANGELOG](CHANGELOG.md) — release history
   - [SECURITY](SECURITY.md) — vulnerability reporting policy
   ```

**Edge Cases:**

- README currently ends at line 102 (no trailing newline issues expected)
- Troubleshooting entries must stay short — this is a README, not a wiki

**Out of Scope:**

- Full wiki or docs site
- Troubleshooting for non-core dependencies (playwright, vitest)
- Auto-generating the FAQ from hook source comments
