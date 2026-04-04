# Merge safety_check_agent.py into safety-check.py — Design Spec

**Problem:** Every Bash invocation fires two PreToolUse hooks: `safety-check.py` (Write|Edit|Bash) and `safety_check_agent.py` (Bash only). In the default "regex" mode, `safety_check_agent.py` performs a Python startup + config read + early-exit on every single Bash call, producing zero output. This is pure overhead with no user-visible benefit.

**Approach:** Inline the `safety_check_agent.evaluate()` dispatch into `safety-check.py`'s existing Bash branch. `safety_check_agent.py` stays on disk as an importable module (used by tests and by `safety-check.py` via `import`). Remove the `safety_check_agent.py` entry from `hooks.json` so only one PreToolUse process runs per Bash event. Mirrors the ADR-043 consolidation of `input-sanitizer.py`.

**Components:**
- `hooks/safety-check.py` — add inline dispatch: call `safety_check_agent.evaluate()` when mode is "agent" or "both"; remove the `if mode == "agent": sys.exit(0)` early-exit (now handled internally)
- `hooks/safety_check_agent.py` — retained as importable module; `__main__` block kept for standalone testing; no logic changes
- `hooks/hooks.json` — remove the second PreToolUse matcher entry for `safety_check_agent.py`
- `tests/test_safety_check_agent.py` — verify mode dispatch still works via direct import
- `tests/test_safety_check.py` — add integration cases: mode="agent" calls agent evaluate; mode="both" calls both; mode="regex" skips agent

**Data Flow:**

1. Bash event arrives → Claude Code fires `safety-check.py` (only)
2. `safety-check.py` reads event, detects `tool_name == "Bash"`
3. Loads config → reads `safety_check_mode`
4. **mode="regex" (default):** runs `evaluate(command)` regex check → confirm-wrap → exit
5. **mode="agent":** calls `safety_check_agent.evaluate(command, mode, timeout)` → exit with result (skip regex block + confirm-wrap when agent blocks)
6. **mode="both":** runs regex `evaluate(command)` first; if blocked → exit 2; if allowed → calls `safety_check_agent.evaluate()` → A/B log → exit with agent result
7. `safety_check_agent.py` is never spawned as a subprocess by Claude Code; only imported

**Edge Cases:**
- `safety_check_agent.py` `__main__` block: must remain functional for `python3 safety_check_agent.py` standalone invocation (manual testing)
- mode="both" ordering: regex runs first — if regex blocks, agent is skipped (same behaviour as today; agent is additive)
- Agent timeout: `config["safety_agent_timeout_s"]` already threaded through; no change needed
- Import failure: if `safety_check_agent` import fails (e.g. missing util), wrap in try/except per ADR-003 hook safety convention — fall back to regex

**Out of Scope:**
- Changing `safety_check_agent.py` logic, prompts, or patterns
- Removing `safety_check_agent.py` from disk
- Adding new safety modes beyond "regex", "agent", "both"
- Changing the A/B log format or location
- Moving BLOCKS/WARNS pattern lists
