# SECURITY.md hardcodes 'zierocode' GitHub username

**Severity**: Low | **Source**: audit-2026-03-24

## Problem

`SECURITY.md:17` contains a GitHub security advisory URL with the hardcoded
username 'zierocode'. If the repository moves or is forked, this URL points
to the wrong place. Security researchers following the link would end up at the
wrong advisory page.

## Motivation

Replace with the actual repository slug or use a relative path. Cheap fix that
keeps security reporting accurate.
