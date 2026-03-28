---
approved: true
approved_at: 2026-03-24
backlog: backlog/security-shell-injection.md
---

# Security: Shell Injection Fix in input-sanitizer.py — Design Spec

**Problem:** `hooks/input-sanitizer.py` constructs a bash confirmation wrapper by directly interpolating `{command}` into an f-string at lines 91–94, allowing shell metacharacters in the command to break the `echo` display string and potentially cause unintended execution in the compound command block.

**Approach:** Add `import shlex` to the stdlib import block (lines 12–15) and replace the `echo "Would run: {command}"` display sub-expression with `printf "Would run: %s\n" {shlex.quote(command)}`. Using `printf` with `%s` separates the static format string from the argument, so shlex.quote's output (which may contain single quotes and `'"'"'` sequences) composes safely without interacting with any outer quoting. The inner execution block `{ {command}; }` remains unquoted — this is intentional, the command must run verbatim. Add a unit test with concrete assertions.

**Components:**
- `hooks/input-sanitizer.py`
  - Line 12–15 area: add `import shlex` to the stdlib import block (after `import re`, before `import sys`)
  - Lines 91–94: replace the `echo "Would run: {command}"` sub-expression within the `rewritten` f-string with `printf "Would run: %s\\n" {shlex.quote(command)}`
- `tests/unit/test_input_sanitizer.py`
  - Add one parametrized test method covering commands with `"`, `'`, `;`, `&&`, `|` metacharacters

**Data Flow:**
1. PreToolUse Bash event arrives with `tool_input.command`
2. Existing normalization: `normalized = re.sub(r"\s+", " ", command.strip())`
3. Pattern matched against CONFIRM_PATTERNS — on match:
4. **BEFORE (injection point):**
   ```python
   rewritten = (
       f'echo "Would run: {command}" '          # ← vulnerable
       f'&& read -p "Confirm? [y/N] " _y '
       f'&& [ "$_y" = "y" ] && {{ {command}; }}'
   )
   ```
5. **AFTER (safe):**
   ```python
   rewritten = (
       f'printf "Would run: %s\\n" {shlex.quote(command)} '  # ← safe
       f'&& read -p "Confirm? [y/N] " _y '
       f'&& [ "$_y" = "y" ] && {{ {command}; }}'             # ← intentional
   )
   ```
6. `updatedInput` returned to Claude with `permissionDecision: "allow"`

**Why `printf` instead of `echo "...{shlex.quote(command)}"`:**
`shlex.quote()` wraps strings in single quotes and escapes embedded single quotes as `'"'"'`. If this output is embedded inside double-quoted `echo "..."`, the `'"'"'` sequence interacts with the outer double-quote context and produces malformed shell. Using `printf "%s\n" <shlex_output>` avoids this: the format string is static double-quoted; the argument is the shlex-quoted word, parsed independently by the shell.

Example: `command = "it's rm -rf ./"`:
- `shlex.quote(command)` → `'it'"'"'s rm -rf ./'`
- `printf "Would run: %s\n" 'it'"'"'s rm -rf ./'` → prints `Would run: it's rm -rf ./` ✓
- `echo "Would run: 'it'"'"'s rm -rf ./"` → broken quoting, shell error ✗

**Edge Cases:**
- Command with `"` → shlex.quote wraps in single quotes → safe in printf arg ✓
- Command with `'` → shlex.quote uses `'"'"'` escape → safe in printf arg (not in double-quoted echo) ✓
- Command with `;` or `&&` → shlex.quote single-quotes the whole string → display only, does not affect exec block ✓
- Command with `|` or backticks → same: shlex.quote prevents interpretation in display ✓
- Command is empty → existing early-exit at line 78 handles before reaching rewrite ✓
- Double-wrapping guard (`"Would run:"` check line 82) still works — `printf` does not add "Would run:" to the command string ✓
- Very long commands → `printf %s` and shlex.quote both handle arbitrary length ✓

**Test assertions required (test_input_sanitizer.py):**

Test name: `test_confirm_rewrite_metacharacters_safe`

For each of these commands that match CONFIRM_PATTERNS:
- `rm -rf ./dist "quoted dir"`
- `rm -rf ./it's-mine`
- `rm -rf ./foo; evil`
- `rm -rf ./a && evil`

Assert all of:
1. Hook exits 0 (hook never blocks — outer guard)
2. Hook stdout is valid JSON with keys `updatedInput` and `permissionDecision`
3. `rewritten_command` (from `updatedInput.command`) contains the substring `printf "Would run: %s\n"`
4. `rewritten_command` does NOT contain the bare `{command}` value embedded in a double-quoted echo (i.e., `'echo "Would run: rm'` or similar)
5. `rewritten_command` ends with `{ rm -rf ...; }` — inner exec block contains original unquoted command

**Out of Scope:**
- Changing the inner execution block `{ {command}; }` — intentionally unquoted
- Adding sanitization of the command itself (handled by safety-check.py BLOCKS)
- Migrating to heredoc, process substitution, or Option B/C approaches (YAGNI)
- Fixing other hooks — this is the only hook with this display-wrapping pattern
- Escaping `read -p` prompt string — static string, no injection vector
