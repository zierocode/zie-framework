# Backlog: Deduplicate 4 git log reads in retro.md

**Problem:**
retro.md reads git log 4 times per invocation:
1. `!git log --oneline` bang injection at command load
2. `!git log -20 --oneline` bang injection at command load
3. `git log --oneline -50` Bash call in self-tuning proposals (step 5)
4. `git log -1 --format="%s"` Bash call in docs-sync guard (step 8)

**Motivation:**
The bang-injected git log is already in context — step 3 explicitly says "git context
already injected above, no Bash needed" but then step 5 spawns a new subprocess anyway.
~200–500 tokens of redundant content plus extra subprocess latency. The injected
context should be reused directly.

**Rough scope:**
- Remove the `git log --oneline -50` Bash call in self-tuning step — reference the
  already-injected bang output instead
- Consolidate the two bang injections into one (one is enough for both purposes)
- For docs-sync guard: the last commit subject can be extracted from the injected
  log without a separate Bash call
- Tests: verify retro only runs git log once (count Bash calls in test if possible)
