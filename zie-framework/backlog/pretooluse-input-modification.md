# Backlog: PreToolUse updatedInput — Path Sanitization and Input Rewriting

**Problem:**
`safety-check.py` only blocks dangerous commands — it can't fix them. When
Claude uses a relative file path in Write/Edit that could escape the project
root, or when a command needs minor sanitization, the only option is block+retry.

**Motivation:**
PreToolUse supports `updatedInput`: the hook can rewrite the tool's input before
execution. This enables: (1) resolving relative paths to absolute against CWD,
(2) adding `--dry-run` to destructive commands for confirmation, (3) rewriting
ambiguous paths inside the project boundary.

**Rough scope:**
- Update `hooks/auto-test.py` or create `hooks/input-sanitizer.py`
  (PreToolUse: Write|Edit|Bash)
- For Write/Edit: if `file_path` is relative → resolve to `cwd/file_path`,
  output `updatedInput` with absolute path
- For Bash: if command matches a "confirm before run" pattern (e.g. `rm -rf ./`)
  → rewrite to `echo "Would run: rm -rf ./" && read -p "Confirm? " y && $cmd`
- Output `permissionDecision: "allow"` for the modified input (skip re-prompt)
- Tests: relative path resolution, non-relative paths unchanged, bash rewrite
