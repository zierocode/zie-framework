---
slug: audit-brace-guard
status: approved
date: 2026-04-01
---
# Spec: Brace Character Guard in `_is_safe_for_confirmation_wrapper`

## Problem

`hooks/input-sanitizer.py` embeds the raw user command into a shell wrapper at line 115:

```python
f'... && {{ {command}; }}'
```

The compound operator guard `_DANGEROUS_COMPOUND_RE` (line 34) blocks `;`, `&&`, `||`, `` ` ``, and `$()` — but does **not** block bare `{` or `}` characters in the command string.

A command containing a bare `}` would prematurely close the outer `{ ... ; }` block, breaking shell structure and potentially causing unintended execution. Example: `rm -rf ./foo }; malicious_cmd #` would corrupt the wrapper into:

```sh
... && { rm -rf ./foo }; malicious_cmd #; }
```

The inner `}` closes the group early; everything after it runs outside the confirmation guard.

## Proposed Solution

Add `{` and `}` to the blocked-character check inside `_is_safe_for_confirmation_wrapper`. This is the narrowest safe fix: it targets exactly the characters that can structurally corrupt the embedding context without touching `_DANGEROUS_COMPOUND_RE` (which serves a different, broader purpose).

Implementation: extend the function body with an explicit character check before the regex search:

```python
def _is_safe_for_confirmation_wrapper(command: str) -> bool:
    if '{' in command or '}' in command:
        return False
    return not _DANGEROUS_COMPOUND_RE.search(command)
```

No changes to `_DANGEROUS_COMPOUND_RE`, `CONFIRM_PATTERNS`, or any other function.

## Acceptance Criteria

- [ ] AC1: `_is_safe_for_confirmation_wrapper("rm -rf ./foo }")` returns `False`
- [ ] AC2: `_is_safe_for_confirmation_wrapper("rm -rf ./foo {bar}")` returns `False`
- [ ] AC3: `_is_safe_for_confirmation_wrapper("rm -rf ./foo")` still returns `True` (no regression)
- [ ] AC4: `_is_safe_for_confirmation_wrapper("rm -rf ./foo | grep bar")` still returns `True` (pipe allowed)
- [ ] AC5: A command matching `CONFIRM_PATTERNS` that also contains `}` logs the "compound command skipped" message and exits without rewriting
- [ ] AC6: `_DANGEROUS_COMPOUND_RE` is unchanged
- [ ] AC7: All existing `input-sanitizer` unit tests continue to pass

## Out of Scope

- Escaping or sanitizing brace characters rather than blocking (adds complexity, not needed)
- Changing `_DANGEROUS_COMPOUND_RE` to include brace characters
- Any change to `CONFIRM_PATTERNS`
- Handling other shell metacharacters not specifically related to the `{ cmd; }` embedding context (e.g., `>`, `<`, `!`)
