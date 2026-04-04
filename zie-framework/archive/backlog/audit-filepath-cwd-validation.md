# file_path from hook event not validated within cwd

**Severity**: High | **Source**: audit-2026-03-24

## Problem

`auto-test.py` does `changed = Path(file_path)` where `file_path` comes directly
from the Claude hook event with no boundary validation. Passing `/etc/passwd`
results in `changed.stem = 'passwd'`, which gets logged and searched. Subprocess
args are safe (list-form), but unbounded paths leak to output.

## Motivation

Defense in depth: hook inputs should be validated against the project root before
use. A simple `changed.is_relative_to(cwd)` check prevents path confusion and
protects log output from leaking arbitrary system paths.
