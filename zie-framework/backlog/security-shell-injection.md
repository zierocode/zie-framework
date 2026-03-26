# Security: Shell Injection in input-sanitizer.py

**Source**: audit-2026-03-24b C1 (Critical — Agent A)
**Effort**: XS
**Score impact**: +15 (Critical eliminated → Security +15)

## Problem

`hooks/input-sanitizer.py:91-94` wraps dangerous commands in a confirmation prompt
using direct f-string interpolation of `{command}`:

```python
rewritten = (
    f'echo "Would run: {command}" '
    f'&& read -p "Confirm? [y/N] " _y '
    f'&& [ "$_y" = "y" ] && {{ {command}; }}'
)
```

If `command` contains `"` or shell metacharacters (`; && |`), the echo string
breaks and the bash compound command can execute injected code. Example:
`rm -rf ./foo" && malicious_cmd #` → breaks out of echo + runs malicious_cmd.

## Motivation

This is the only Critical security finding. Fix is one line (`shlex.quote`).
High confidence the blast radius is limited (Claude controls the command, BLOCKS
run first) but the injection is technically real and must be closed.

## Scope

- `hooks/input-sanitizer.py:91` — wrap `{command}` in `shlex.quote()` for the
  echo display portion
- The inner `{ {command}; }` block is intentional (run as-is) but should be
  documented as safe-by-design
- Add test verifying commands with shell metacharacters are echoed safely

## Acceptance Criteria

- [ ] `shlex.quote(command)` used in echo display string
- [ ] Command with `"`, `;`, `&&` doesn't break echo output
- [ ] Dedicated unit test for metacharacter handling
- [ ] No functional regression on normal CONFIRM_PATTERNS commands
