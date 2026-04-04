You are scanning an existing software project to help initialize zie-framework.

Scan the project at the current working directory. Read existing documentation
first as primary sources (they encode deliberate intent, not just structure):
  README.md, CHANGELOG.md, ARCHITECTURE.md, AGENTS.md,
  docs/**, **/specs/*.md, **/plans/*.md, **/decisions/*.md
  (exclude anything inside zie-framework/)

Then scan the codebase structure to fill in any gaps.

Exclude from all scans:
  node_modules/, .git/, build/, dist/, .next/, __pycache__/, *.pyc,
  coverage/, zie-framework/

Return ONLY a JSON object with this exact structure (no markdown, no prose).
The parent parser will extract JSON from the first '{' to the last '}'.

{
  "architecture_pattern": "<string>",
  "components": [{ "name": "<string>", "purpose": "<one-line string>" }],
  "tech_stack": [{ "name": "<string>", "version": "<string | null>" }],
  "data_flow": "<string>",
  "key_constraints": ["<string>"],
  "test_strategy": { "runner": "<string | null>", "coverage_areas": ["<string>"] },
  "active_areas": ["<string>"],
  "existing_hooks": "<path to hooks/hooks.json if present, else null>",
  "existing_config": "<path to zie-framework/.config if present, else null>",
  "migration_candidates": {
    "specs":      ["<relative path>"],
    "plans":      ["<relative path>"],
    "decisions":  ["<relative path>"],
    "backlog":    ["<relative path>"]
  }
}

For migration_candidates: include files matching these patterns (excluding
anything already inside zie-framework/):
  specs:     **/specs/*.md, **/spec/*.md
  plans:     **/plans/*.md, **/plan/*.md
  decisions: **/decisions/*.md, **/adr/*.md, ADR-*.md (at project root)
  backlog:   **/backlog/*.md

For existing_hooks: check if hooks/hooks.json exists at project root.
For existing_config: check if zie-framework/.config exists.
If a field cannot be determined, use null for scalars or [] for arrays.
