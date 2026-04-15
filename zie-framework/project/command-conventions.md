# Command Conventions

Shared protocol definitions referenced by all zie-framework commands.

---

## Pre-flight

Every command that operates on an existing project runs these 3 steps before anything else:

1. Check `zie-framework/` exists → if not, tell user to run `/init` first.
2. Read `zie-framework/.config` → load project settings (project_type, zie_memory_enabled, etc.).
3. Read `zie-framework/ROADMAP.md` → check Now lane.
   - If a `[ ]` item exists in Now → warn: "WIP active: `<feature>`. Starting a new task
     splits focus. Continue? (yes/no)"
   - If ROADMAP.md not found → STOP: "ROADMAP.md not found — run /init first."

### Pre-flight levels

- **`preflight: full`** — all 3 steps. Default for commands that modify state (backlog, spec, plan, implement, sprint, etc.).
- **`preflight: minimal`** — existence check only (step 1). For read-only or self-contained commands: `/health`, `/brief`, `/guide`.

Commands declare their level in the frontmatter or first line: `preflight: minimal` or `preflight: full`.

---

## Error format

All error/warning messages in commands follow these formats:

- **Blocker**: `STOP: <action-oriented message>` — user must act before proceeding. No emoji.
- **Warning**: `⚠ <message>` — non-blocking issue the user should know about.
- **Tip/Info**: `ℹ️ <advice>` — helpful suggestion, not an error.

Examples:

```
STOP: Run /init first.                          # zie-framework/ not found
STOP: ROADMAP.md not found — run /init first.    # missing roadmap
⚠ WIP active: feature-x. Starting a new task splits focus.
ℹ️ Run /spec next to write a design spec.
```

Do NOT use: `❌`, `Error:`, `Failed to`, bare `STOP` without colon, or emoji in `STOP:`/`⚠` lines.

---

## Output format

Every command produces output in this structure:

1. **Header line**: `/command — <one-line description>` (e.g., `/backlog — capture a new idea`)
2. **Body**: structured content (tables, lists, code blocks)
3. **Footer**: `→ /next-command` suggestion (e.g., `→ /spec my-feature`)

The header line tells the user what's happening. The footer tells them what to do next. Remove trailing summaries — the footer replaces them.
