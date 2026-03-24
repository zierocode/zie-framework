---
approved: true
approved_at: 2026-03-24
backlog: backlog/subagentstart-sdlc-context.md
---

# SubagentStart SDLC Context Injection — Design Spec

**Problem:** Subagents spawned by `/zie-implement` and `/zie-plan` have no SDLC context, so they research generically rather than purposefully against the active feature and its constraints.

**Approach:** A new `SubagentStart` hook (`hooks/subagent-context.py`) fires whenever Claude spawns a subagent. It reads only `ROADMAP.md`, the most recent plan file, and `project/context.md` (for ADR count) — all pure file I/O with no subprocesses. When the spawned agent type matches `Explore|Plan`, it emits a JSON `additionalContext` payload that names the active feature slug, the first incomplete task from the plan, and the total ADR count as a constraint signal.

**Components:**
- `hooks/subagent-context.py` — new hook (SubagentStart event)
- `hooks/hooks.json` — add SubagentStart entry with `matcher: "Explore|Plan"`
- `hooks/utils.py` — reuse `read_event()`, `get_cwd()`, `parse_roadmap_now()`, `parse_roadmap_section()` (no new utils needed)
- `tests/test_subagent_context.py` — new unit test file
- `zie-framework/project/components.md` — add hook row to Hooks table

---

## Data Flow

1. Claude spawns a subagent; Claude Code fires `SubagentStart` with a JSON event on stdin. The event contains at minimum an `agentType` field (e.g. `"Explore"`, `"Plan"`, `"Task"`).
2. **Outer guard:** `read_event()` parses stdin. On any failure → `sys.exit(0)`. Extract `agent_type = event.get("agentType", "")`.
3. **Agent-type filter:** If `agent_type` does not match `re.search(r'Explore|Plan', agent_type, re.IGNORECASE)` → `sys.exit(0)` silently. Non-matching agents (e.g. `Task`, `Build`) receive no injection.
4. **Framework presence check:** `cwd = get_cwd()`. If `(cwd / "zie-framework")` does not exist → `sys.exit(0)`.
5. **Read ROADMAP Now lane:** `now_items = parse_roadmap_now(cwd / "zie-framework" / "ROADMAP.md")`. If empty → `feature_slug = "none"`, skip plan lookup.
6. **Derive feature slug:** Strip markdown link syntax and checkbox prefix from `now_items[0]`. Convert to lowercase slug form (spaces → hyphens, strip non-alphanumeric except hyphens) for the context label.
7. **Find active plan file:** Glob `zie-framework/plans/*.md`, sort by `mtime` descending, take `plans[0]`. If none → `active_task = "unknown"`.
8. **Extract first incomplete task:** Read the plan file lines. Find the first line matching `re.search(r'- \[ \]', line)`. Strip `- [ ]`, `**`, and leading/trailing whitespace. Result → `active_task`. If no incomplete task found → `active_task = "all tasks complete"`.
9. **Count ADRs:** Read `zie-framework/project/context.md`. Count lines matching `r'^## ADR-\d+'` → `adr_count`. If file missing → `adr_count = "unknown"`.
10. **Emit `additionalContext`:** Print JSON to stdout:
    ```json
    {"additionalContext": "[zie-framework] Active: <feature_slug> | Task: <active_task> | ADRs: <adr_count> (see zie-framework/project/context.md)"}
    ```
11. **Inner error handling:** Each file read is wrapped in `try/except Exception as e` → `print(f"[zie-framework] subagent-context: {e}", file=sys.stderr)`, then continue with safe fallback values. Hook always exits 0.

---

## Edge Cases

- **No active feature (empty Now lane):** Emit context with `Active: none | Task: none | ADRs: <n>`. Still useful — subagent knows nothing is in progress.
- **No plan files exist:** `active_task = "unknown"`. Hook continues and emits partial context rather than skipping.
- **All plan tasks are complete (`[x]`):** `active_task = "all tasks complete"`. Subagent is informed no new work is outstanding.
- **`project/context.md` missing:** `adr_count = "unknown"`. Not a blocking condition.
- **ROADMAP.md missing:** `parse_roadmap_now()` returns `[]` — handled by step 5 fallback.
- **`agentType` field absent from event:** `event.get("agentType", "")` returns empty string → regex match fails → `sys.exit(0)`. No injection, no crash.
- **Non-research agent type (e.g. `"Task"`):** Filtered out in step 3. Zero overhead for the common case.
- **Symlinked plan files:** `mtime`-based sort works on symlinks; the hook reads content only, no write. No special handling needed.
- **Very long plan files:** Only reading until the first `- [ ]` line, so performance is bounded by task position, not file size.
- **`additionalContext` already injected by another hook:** The `SubagentStart` event supports multiple hooks; each emits its own `additionalContext` JSON. Claude Code merges them. No conflict.

---

## Out of Scope

- Injecting context into non-research agents (`Task`, `Build`, `Coding`).
- Reading full plan task descriptions beyond the first incomplete task title.
- Fetching ADR body text — only the count is injected as a constraint signal.
- Writing or modifying any files — hook is read-only.
- zie-memory integration — this feature deliberately uses file I/O only per the backlog's "Fast: file reads only" constraint.
- Injecting spec file content — plan file provides sufficient task-level focus.
- Updating `_hook_output_protocol` in `hooks.json` for `SubagentStart` — the existing comment block is informational only and does not gate hook registration.
