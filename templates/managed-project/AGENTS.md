# AGENTS.md

Entry doc for any agent (Claude Code, Codex, others) opening a session in this project.

> **This file is the per-project governance layer.** It is generated from the
> `dev-workflow-skills2` template `templates/managed-project/AGENTS.md` and
> tailored at project bootstrap by the `project-init` skill. Update only the
> placeholder lines below; the contracts are stable across all projects this
> workflow manages.

## What this project is

`<PROJECT_NAME>` is managed by the `dev-workflow-skills2` workflow specification: 7-stage pipeline (PRD → SRS → Architecture → Development → Testing → Delivery → Retrospective) across 4 scenarios (S1 / S2 / S3 / S4) with Bug Flow and Incident Flow.

- **Workflow source**: `<DEV_WORKFLOW_SKILLS_PATH>` (replace with the absolute path to the cloned `dev-workflow-skills2` repo, or with the plugin / package reference once distribution is decided).
- **Project state**: read live from `progress.md` at the project root. **Never** edit it by hand — every mutation goes through `progress.py`.

## When you start a session

1. Run `python3 <DEV_WORKFLOW_SKILLS_PATH>/skills/workflow-protocol/scripts/progress.py --root . query` to inspect current state.
2. From the returned frontmatter:
   - **`progress.md` does not exist** → bootstrap was not run; ask the user to confirm the project intent and re-invoke the `project-init` skill.
   - **`project_state ∈ {aborted, reconstructing}`** → terminal; do not mutate.
   - **`workflow_incident_active == true`** → invoke `workflow-evolution` skill.
   - **`bug_flow.active == true`** → invoke `bug-triage` (active mode) or the stage skill for `bug_flow.root_cause`.
   - **`release_state == active`** and you have user input not matching the current stage → invoke `scenario-dispatcher`.
   - **`release_state == active`** and the user asks to keep going on the current stage → invoke the stage skill for `current_stage`.
   - **`release_state == closed`** → invoke `scenario-dispatcher` to decide S2 sub-scenario or post-close bug intake.
3. Before doing **any** doc edit, run `python3 <DEV_WORKFLOW_SKILLS_PATH>/skills/doc-guardian/scripts/validate.py file <doc-path>` and only mutate if it passes (or accept the issues as the work to fix).

## Mandatory contracts

These hold for **every** session in this project:

- **State mutation**: every `progress.md` / `progress-history.md` change MUST go through `<DEV_WORKFLOW_SKILLS_PATH>/skills/workflow-protocol/scripts/progress.py` subcommands. Hand-editing these files breaks replay-consistency and the advisory lock; corruption requires `progress.py recover --confirm`.
- **Doc validation**: every doc managed by `doc-guardian` MUST pass `<DEV_WORKFLOW_SKILLS_PATH>/skills/doc-guardian/scripts/validate.py file <path>` before the consumer (review skill / `update --advance`) treats it as final. P6 dimension B re-runs validate as a double-safety check.
- **Doc status sync**: after every successful `progress.py update --event <name>`, the caller MUST run `<DEV_WORKFLOW_SKILLS_PATH>/skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path>` (repeat `--doc` for multi-doc changes) so frontmatter `status` stays aligned with `progress.md.sub_state`.
- **Stage advance**: only `progress.py update --advance` may move `current_stage`. Do not bypass with `update --event` or by editing `progress.md`.
- **Bug Flow choreography**: `bug-start` → modify root-cause stage → `update --advance` back to testing → `write-complete` + `review-passed` → `bug-close` → `update --advance` to delivery (see `<DEV_WORKFLOW_SKILLS_PATH>/skills/workflow-protocol/references/command-reference.md` §10.1).
- **Spec sources are read-only here**: do not edit anything under `<DEV_WORKFLOW_SKILLS_PATH>/skills/`. Spec drift goes back through the workflow's design proposal review cycle.

## Project-specific overrides

> Add only what differs from the workflow defaults. Examples:
> - "Owner format is `<team>/<skill>` instead of `<agent_id>/<skill>`."
> - "All PRs must reference a Linear ticket in the title."
> - "Stage 6 deployment uses internal `deploy-prod.sh` instead of generic instructions."
>
> **Do not** restate or contradict the mandatory contracts above; if you need to
> change a contract, that's a workflow-spec change, not a project override.

<PROJECT_OVERRIDES_HERE>

## Key file locations (in this project)

- `progress.md` / `progress-history.md` — workflow state (managed by `progress.py`)
- `docs/prd/prd.md` — Stage 1 deliverable (project-level, single file)
- `docs/architecture/architecture.md` — Stage 3 deliverable (project-level, single file)
- `docs/retrospective/retrospective.md` — Stage 7 deliverable (project-level, incremental)
- `docs/release<x.y>/srs/srs.md` — Stage 2 deliverable (per release)
- `docs/release<x.y>/development/{plan,breakdown,tasks/T*}` — Stage 4 deliverables
- `docs/release<x.y>/testing/{preparation,procedure,report}.md` — Stage 5
- `docs/release<x.y>/delivery/{deployment,operation_manual,installation_result}.md` — Stage 6
- `docs/cr/CR-NNN.md` — change requests (cross-release)
- `docs/bug/BUG-NNN.md` — bug reports (cross-release)
- `docs/incident/INCIDENT-NNN.md` — workflow incidents (cross-release)

The complete directory contract is `<DEV_WORKFLOW_SKILLS_PATH>/skills/doc-guardian/references/directory-layout.md`.

## What lives outside the workflow

- `src/`, `tests/` — source code and test code; not validated by `doc-guardian`. Internal review of these is the responsibility of `development-code-review` / `development-test-review`.
- Anything else you put at the project root that is not in the file list above.
