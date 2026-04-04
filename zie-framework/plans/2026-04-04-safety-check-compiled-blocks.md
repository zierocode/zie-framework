# Plan: safety-check-compiled-blocks

**Date:** 2026-04-04
**Spec:** `specs/2026-04-04-safety-check-compiled-blocks-design.md`
**File:** `hooks/safety_check_agent.py`

## Steps

### 1. RED — confirm test coverage exists
- Run `make test-fast` targeting `test_safety_check_agent_injection.py`.
- Verify tests cover both BLOCK and ALLOW paths for `_regex_evaluate`.

### 2. GREEN — apply fix

**`hooks/safety_check_agent.py`**

a. Update import line 14:
```python
# before
from utils_safety import BLOCKS, normalize_command
# after
from utils_safety import BLOCKS, COMPILED_BLOCKS, normalize_command
```

b. After `_AGENT_BLOCKS` definition, add compiled version at module level:
```python
_COMPILED_AGENT_BLOCKS = COMPILED_BLOCKS + [
    (re.compile(p, re.IGNORECASE), msg)
    for p, msg in _AGENT_BLOCKS[len(BLOCKS):]  # agent-only additions
]
```

c. Update `_regex_evaluate` loop (line 43-44):
```python
# before
for pattern, message in _AGENT_BLOCKS:
    if re.search(pattern, cmd):
# after
for p, message in _COMPILED_AGENT_BLOCKS:
    if p.search(cmd):
```

d. Remove `import re` if it is no longer referenced elsewhere in the file (check first).

### 3. REFACTOR — clean up
- If `_AGENT_BLOCKS` string list is no longer needed after step 2b, simplify: define the agent-only extra patterns as compiled directly, remove the intermediate string list.
- Keep `_AGENT_BLOCKS` only if tests import it directly (check grep first).

### 4. VERIFY
```bash
make test-fast   # must be green
make lint        # must be clean
```

## Risk

Low. Pure optimisation — no logic change, no interface change. Existing tests provide full regression coverage.
