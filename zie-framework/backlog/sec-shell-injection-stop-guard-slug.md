# Backlog: Add shlex.quote(slug) in stop-guard.py subprocess call

**Problem:**
stop-guard.py lines 63–71 interpolates a ROADMAP-derived `slug` directly into a
`shell=True` subprocess:
```python
result = subprocess.run(
    f"git log --all -p -- zie-framework/ROADMAP.md | grep -B5 '+- \\[ \\] {slug}'",
    shell=True,  # nosec B602
)
```
A slug containing shell metacharacters (e.g. `$(malicious)`, backtick, `|`) from
a tampered ROADMAP would execute arbitrary shell code. The `# nosec` annotation
acknowledges the risk but does not mitigate it.

**Motivation:**
ROADMAP is version-controlled but could be tampered with in a compromised workspace
or via a malicious PR. Fix is one line: `shlex.quote(slug)` in the grep argument.
Can be bundled with lean-stop-guard-nudge-per-stop since both touch the same function.

**Rough scope:**
- Wrap `slug` with `shlex.quote()` in the subprocess call
- Consider removing `shell=True` entirely by using `subprocess.run(["git", "log", ...],
  stdin=subprocess.PIPE)` piped via Python instead of shell
- Update or remove `# nosec` annotation after fix
- Tests: slug with shell metacharacters does not execute
