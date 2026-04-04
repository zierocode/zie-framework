# Backlog: Fix shell injection in safety-check.py confirm wrapper

**Problem:**
In safety-check.py lines 138–142, raw `{command}` is interpolated unquoted into
a shell compound statement in the confirm wrapper:
```python
rewritten = f'... && {{ {command}; }}'  # raw interpolation
```
`_is_safe_for_confirmation_wrapper()` guards against `;`, `&&`, `||`, backticks,
`$()`, and `{}` — but NOT `>` (stdout redirect), `<` (stdin redirect), `|` (pipe),
or `\n` (newlines). A command like `rm -rf ./foo > /etc/passwd` passes the guard
and gets interpolated unescaped.

**Motivation:**
Security vulnerability. The `shlex.quote()` on the printf argument is correct but
the inline `{command}` in the `&&` tail is not quoted. Fix is one line.

**Rough scope:**
- Add `>`, `<`, `|`, `\n` to `_is_safe_for_confirmation_wrapper()` rejected chars
  OR use `shlex.quote(command)` in the compound statement tail
- Add test cases: commands with `>`, `|`, `\n` should not pass the wrapper check
- Run Bandit scan to confirm no remaining B602/B603 findings
