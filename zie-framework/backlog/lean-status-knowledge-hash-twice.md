# Backlog: Deduplicate knowledge-hash computation in /status

**Problem:**
status.md line 21 has a live bang injection `!python3 hooks/knowledge-hash.py` at
command load time. Step 4 then runs `python3 hooks/knowledge-hash.py` again as an
explicit Bash call to compare against the stored hash. This runs the rglob + hash
computation twice per /status invocation — same file, same result, twice.

**Motivation:**
knowledge-hash.py does a full `rglob("*")` across the project to compute a hash.
Running it twice per /status is pure waste (~100 tokens + double the I/O). The
bang-injected result should be captured and reused in step 4 instead of re-running.

**Rough scope:**
- Capture the bang-injected hash output in a named variable in the command flow
- Remove the duplicate Bash call in step 4; reference the captured output instead
- Tests: /status flow runs knowledge-hash exactly once (verify Bash call count in test)
