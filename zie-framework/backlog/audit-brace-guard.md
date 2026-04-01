# Brace characters not blocked by _DANGEROUS_COMPOUND_RE in input-sanitizer

**Severity**: Low | **Source**: audit-2026-04-01

## Problem

`input-sanitizer.py:106–115` embeds the raw user command into a
`{ command; }` shell wrapper: `f'... && {{ {command}; }}'`. The compound
operator guard `_DANGEROUS_COMPOUND_RE` blocks `;`, `&&`, `||`, `` ` ``,
`$()` but does not block bare `}` or `{` characters in the command string.

A command literal containing a bare `}` could structurally break the shell
wrapper and cause unexpected execution. This is a narrow edge case since most
real commands don't contain bare braces, but the guard is incomplete relative
to the embedding context.

## Motivation

Add `{` and `}` to the set of blocked characters in
`_is_safe_for_confirmation_wrapper`, or escape them before embedding.
