# Backlog: Drop write-plan skill effort medium → low

**Problem:**
write-plan uses `model: sonnet` + `effort: medium`. write-plan produces structured
implementation plans: task list with file assignments, depends_on, test coverage per
task. The output format is well-defined and the skill has detailed instructions.
Structured plan generation follows a fixed schema — it's templated output, not
open-ended reasoning.

**Motivation:**
sonnet+low produces the same structured plan output as medium for well-specified
inputs. The quality of a plan depends more on the spec quality (upstream) and the
plan format instructions (in the skill) than on extended thinking time.

**Rough scope:**
- Change `effort: medium` → `effort: low` in skills/write-plan/SKILL.md frontmatter
- Tests: write-plan produces valid plan with correct task structure at low effort
