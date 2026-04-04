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
