# ROADMAP.md Section-Aware Reads

## Problem

Every command that needs ROADMAP.md reads the entire file — including Done
history, Later/Icebox sections, and all backlog items — even when only one
section is relevant. `/zie-implement` only needs the Now lane.
`/zie-status` needs Now + summary counts. `/zie-backlog` only needs the
Next section. As ROADMAP.md grows, this wasted read compounds with every
command invocation.

## Motivation

ROADMAP.md is read by nearly every command. Reading the full file when only
Now lane is needed wastes tokens proportional to backlog size — which grows
continuously. Section-aware reads cap the cost at the size of the relevant
section regardless of total file length.

## Rough Scope

- Map each command to the minimum sections it requires:
  - `/zie-implement` → Now only
  - `/zie-status` → Now + line counts for Next/Done
  - `/zie-plan` → Now (WIP check) + Next (item selection)
  - `/zie-spec` → Now (WIP check) only
  - `/zie-retro` → Now + Done (recent)
  - `/zie-release` → Now only
- Read only those sections via targeted grep/parse rather than full file read
- Complementary to `md-file-bloat` (which reduces file size); this reduces
  read scope regardless of file size
- Out of scope: changing ROADMAP.md format
