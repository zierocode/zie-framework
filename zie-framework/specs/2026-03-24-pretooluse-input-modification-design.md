---
approved: true
approved_at: 2026-03-24
backlog: backlog/pretooluse-input-modification.md
---

# PreToolUse updatedInput Path Sanitization + Rewriting — Design Spec

**Problem:** `safety-check.py` can only block dangerous tool calls — it cannot fix them — so a Write/Edit with a relative `file_path` or a risky Bash command forces a costly block-then-retry cycle instead of a silent in-place correction.

**Approach:** Create a new dedicated hook `hooks/input-sanitizer.py` that fires on `PreToolUse` for `Write`, `Edit`, and `Bash` tools. For Write and Edit it resolves any relative `file_path` to an absolute path anchored at `get_cwd()` and emits an `updatedInput` JSON response; for Bash it rewrites commands matching a "confirm before run" pattern into an interactive confirmation wrapper. The hook always outputs `permissionDecision: "allow"` alongside any `updatedInput` so Claude proceeds immediately without a re-prompt.

**Components:**
- `hooks/input-sanitizer.py` — new PreToolUse hook (primary deliverable)
- `hooks/hooks.json` — add `input-sanitizer.py` to the `PreToolUse` hook list alongside `safety-check.py` and `intent-detect.py`
- `hooks/utils.py` — `read_event()` and `get_cwd()` already exist; no changes needed
- `tests/test_input_sanitizer.py` — new unit test file

**Data Flow:**

1. Claude Code fires `PreToolUse`; `input-sanitizer.py` reads the event via `read_event()` (stdin JSON).
2. **Outer guard:** Extract `tool_name` and `tool_input`. If `tool_name` not in `{"Write", "Edit", "Bash"}`, print nothing and `sys.exit(0)`.
3. **Write / Edit path — relative path resolution:**
   a. Extract `tool_input["file_path"]` (string). If absent or empty, `sys.exit(0)`.
   b. Construct `p = Path(file_path)`.
   c. If `p.is_absolute()`, no change needed — `sys.exit(0)`.
   d. Resolve: `abs_path = (get_cwd() / p).resolve()`.
   e. Safety boundary check: confirm `abs_path` starts with `get_cwd().resolve()`. If it escapes (e.g. `../../etc/passwd`), print a warning to stderr and `sys.exit(0)` — let `safety-check.py` or Claude handle it (do not silently redirect outside project root).
   f. Build `updated = dict(tool_input); updated["file_path"] = str(abs_path)`.
   g. Print `json.dumps({"updatedInput": updated, "permissionDecision": "allow"})` to stdout.
   h. `sys.exit(0)`.
4. **Bash path — confirm-before-run rewrite:**
   a. Extract `tool_input["command"]` (string). If absent or empty, `sys.exit(0)`.
   b. Normalize: `cmd = re.sub(r'\s+', ' ', command.strip())` (preserve original case unlike safety-check).
   c. Match against `CONFIRM_PATTERNS` list (see Edge Cases for entries).
   d. On first match: rewrite command to `echo "Would run: <original_command>" && read -p "Confirm? [y/N] " _y && [ "$_y" = "y" ] && { <original_command>; }`.
   e. Build `updated = dict(tool_input); updated["command"] = rewritten`.
   f. Print `json.dumps({"updatedInput": updated, "permissionDecision": "allow"})` to stdout.
   g. `sys.exit(0)`.
5. If no condition matched, exit 0 silently — no output (Claude proceeds unchanged).

**CONFIRM_PATTERNS (Bash rewrite triggers):**

```python
CONFIRM_PATTERNS = [
    r"rm\s+-rf\s+\./",          # rm -rf ./<path> (project-relative recursive delete)
    r"rm\s+-f\s+\./",           # rm -f ./<path>  (project-relative force delete)
    r"git\s+clean\s+-fd",       # git clean -fd   (removes untracked files)
    r"make\s+clean",            # make clean      (may delete build artifacts)
    r"truncate\s+--size\s+0",   # truncate --size 0 (zeroing a file)
]
```

Note: patterns that are already in `safety-check.py`'s `BLOCKS` list (e.g. `rm -rf /`, `rm -rf ~`, `rm -rf .` bare) must NOT be duplicated here — they belong to the blocking layer, not the rewrite layer. `input-sanitizer.py` targets commands that are legitimate but warrant confirmation.

**Hook registration in `hooks/hooks.json`:**

`input-sanitizer.py` is added as a second entry in the `PreToolUse` hook array. Execution order: `safety-check.py` runs first (it may exit 2 and abort), then `input-sanitizer.py` runs if safety-check exits 0.

**Output protocol:**

- When a rewrite is needed: `print(json.dumps({"updatedInput": {...}, "permissionDecision": "allow"}))` to stdout, then `sys.exit(0)`.
- When no rewrite is needed: no stdout output, `sys.exit(0)`.
- All unexpected errors: `sys.exit(0)` — never block Claude.

**Edge Cases:**
- Relative path that traverses above `cwd` (e.g. `../sibling-project/secret.py`): boundary check fails → no rewrite, silent exit 0. `safety-check.py` does not cover Write/Edit paths, so this is a soft miss — future scope for a separate boundary-enforcement item.
- `file_path` is already absolute: no output, exit 0. Idempotent.
- `file_path` contains a symlink component: `Path.resolve()` follows symlinks. The resolved absolute path is used as-is; symlink traversal outside cwd is caught by the boundary check.
- Bash command matches multiple `CONFIRM_PATTERNS`: first match wins; only one rewrite applied.
- Bash command already contains the confirmation wrapper (re-entrant call): the `read -p` substring will not match any `CONFIRM_PATTERNS`, so no double-wrapping.
- `CLAUDE_CWD` env var missing: `get_cwd()` falls back to `os.getcwd()` (existing utils behaviour).
- `tool_input` is `None` or not a dict: `(event.get("tool_input") or {})` guard prevents `KeyError`; exit 0.
- stdin parse failure: `read_event()` calls `sys.exit(0)` internally — outer guard never reached.

**Test Cases (`tests/test_input_sanitizer.py`):**
- Relative path `"src/main.py"` with `cwd="/project"` → `file_path` becomes `/project/src/main.py`.
- Absolute path `/project/src/main.py` → unchanged, no updatedInput emitted.
- Traversal path `"../../etc/passwd"` → no updatedInput emitted, exits 0.
- Bash `rm -rf ./dist/` → command rewritten with confirmation wrapper.
- Bash `echo hello` (no match) → no output, exits 0.
- Non-targeted tool (e.g. `Read`) → exits 0 with no output.
- `tool_input` missing `file_path` key → exits 0 without error.

**Out of Scope:**
- Blocking dangerous paths in Write/Edit (boundary enforcement beyond silent no-op) — separate hardening item.
- Rewriting Bash commands that are already in `safety-check.py` BLOCKS — those are hard blocks, not rewrites.
- Windows path separators — this framework targets macOS/Linux (POSIX `Path` behaviour assumed).
- UI-level confirmation dialog — the confirmation wrapper uses shell `read`, which is sufficient for terminal-based Claude Code sessions.
- Modifying `safety-check.py` or `auto-test.py` — input-sanitizer is a standalone new hook.
