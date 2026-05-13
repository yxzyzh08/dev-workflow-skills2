# `<PROJECT_NAME>`

Managed by the [`dev-workflow-skills2`](<DEV_WORKFLOW_SKILLS_URL_OR_PATH>) workflow.

## Quick start (for human readers)

- **Project state**: see `progress.md` (workflow frontmatter) and `progress-history.md` (event log). Both files are maintained by `progress.py`; do not hand-edit.
- **Active deliverables**: under `docs/`. Project-level docs (PRD, architecture, retrospective) live in their own directories; per-release docs (SRS, development, testing, delivery) live under `docs/release<x.y>/`.
- **Source code**: under `src/` (or wherever your project conventionally puts it).
- **Tests**: under `tests/` (or wherever your project conventionally puts it).

## For agent sessions

Read [`AGENTS.md`](AGENTS.md). It encodes the workflow contracts and the per-project overrides.

## Workflow source of truth

`<DEV_WORKFLOW_SKILLS_PATH>/skills/` (set during `project-init` bootstrap). Do not edit it from this project.
