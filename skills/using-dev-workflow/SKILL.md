---
name: using-dev-workflow
description: Use at the start of every session in a project where the dev-workflow-skills plugin is active. Establishes how to detect project state from progress.md and route to the right skill (project-init / scenario-dispatcher / stage skill / bug-triage / workflow-evolution). Loaded automatically by the SessionStart hook.
---

<SUBAGENT-STOP>
If you were dispatched as a subagent to execute a specific task, skip this skill.
</SUBAGENT-STOP>

<EXTREMELY-IMPORTANT>
This plugin manages a project's full lifecycle through `progress.md` (workflow state) and `validate.py` (doc validation). State mutation MUST go through `progress.py`; doc validation MUST go through `validate.py`. Bypassing breaks replay-consistency, the advisory lock, and the doc schema contract.

If you are in a project that has `progress.md` at the root, you are operating under this workflow until told otherwise — do NOT freelance edits to `progress.md` / `progress-history.md`, do NOT skip `validate.py` before treating a managed doc as final, and do NOT advance stages by editing `current_stage` directly.
</EXTREMELY-IMPORTANT>

## Instruction priority

User instructions always win. If `<target>/AGENTS.md` (the project's own governance layer, generated from `templates/managed-project/AGENTS.md`) says something specific to the project, that overrides plugin defaults. The plugin's mandatory contracts are stable across all projects this workflow manages — see them under §Mandatory contracts below.

## Step 1 — Detect project state

Run this first, before any clarifying question or action:

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-<plugin-root>}/skills/workflow-protocol/scripts/progress.py --root . query
```

Read what comes back and pick a branch:

| Detected state | Route to |
|----------------|----------|
| `progress.py query` errors with "progress.md not found" → target is **not yet managed** | **Ask the user**: do they want this directory managed by the dev-workflow plugin? If yes → invoke `Skill` tool on `project-init`. If no → skip the plugin's routing and answer the user's actual question normally. |
| `progress.py query` errors with frontmatter parse / schema errors | invoke `Skill` tool on `workflow-protocol` and propose `progress.py recover --confirm` |
| `project_state ∈ {aborted, reconstructing}` | terminal — refuse mutation; suggest the user start a fresh project in a separate directory |
| `workflow_incident_active == true` | invoke `Skill` tool on `workflow-evolution` |
| `bug_flow.active == true` | invoke `Skill` tool on `bug-triage` (active mode) **or** the stage skill matching `bug_flow.root_cause` |
| `release_state == active` and the user input matches the current stage's normal work | invoke `Skill` tool on the `*-write` or `*-review` skill for `current_stage` × `sub_state` |
| `release_state == active` and the user input does NOT match the current stage (new request, scope change, scenario change) | invoke `Skill` tool on `scenario-dispatcher` |
| `release_state == closed` and the user wants to start the next release / new feature | invoke `Skill` tool on `scenario-dispatcher` |
| `release_state == closed` and the user reports a new bug | invoke `Skill` tool on `bug-triage` (post-close mode) |

Plugin root resolution: prefer the environment variable `CLAUDE_PLUGIN_ROOT` (set by Claude Code when the plugin is loaded). Fall back to whatever path the user / install instructions told you. Never hardcode `/home/...` paths in artifacts you write into the user's project.

## Step 2 — Skill before answer

Once routing is decided, **invoke the chosen skill via the `Skill` tool before responding to the user**, even if the user's question seems trivial. The chosen skill defines the procedure for the rest of this turn.

If multiple skills could apply, prefer in this order:

1. **Terminal / blocking states** — `workflow-evolution` (incident active) > `bug-triage` (bug active) > stage skills.
2. **State machine over content** — `scenario-dispatcher` runs before any stage skill when scenario is undecided or being re-decided.
3. **Stage write before stage review** — never invoke `*-review` while `sub_state == write/revising`; the state machine forbids it.

## Mandatory contracts

These hold for every session in every project under this plugin. Do not negotiate them with the user; if they ask you to bypass, decline and explain.

- **State mutation**: every change to `progress.md` / `progress-history.md` MUST go through `${CLAUDE_PLUGIN_ROOT}/skills/workflow-protocol/scripts/progress.py` (12 subcommands: `init`, `query`, `recover`, `update --event/--task/--advance`, `release-close`, `release-start`, `bug-intake`, `bug-start`, `bug-close`, `bug-rework`, `incident-start`, `incident-resolve`). Hand-editing breaks replay-consistency and the advisory lock.
- **Doc validation**: before treating any managed doc (PRD, SRS, architecture, dev plan, test report, etc.) as final, run `${CLAUDE_PLUGIN_ROOT}/skills/doc-guardian/scripts/validate.py file <doc-path>`. P6 dimension B re-runs validate as double-safety inside `update --advance`.
- **Doc status sync**: after every `progress.py update --event <name>`, the caller MUST run `${CLAUDE_PLUGIN_ROOT}/skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path>` (repeat `--doc` for multi-doc) to keep frontmatter `status` aligned with `progress.md.sub_state`.
- **Stage advance**: only `progress.py update --advance` may move `current_stage`. The advance command runs the P6 matrix (A/B/C/D/E) live; a failure means a real precondition is missing — fix it, do not bypass.
- **Bug Flow choreography**: the canonical sequence is `bug-start` → modify root-cause stage → `update --advance` back to testing → `write-complete` + `review-passed` → `bug-close` → `update --advance` to delivery. See `${CLAUDE_PLUGIN_ROOT}/skills/workflow-protocol/references/command-reference.md §10.1`.
- **Spec is immutable from runtime**: do not edit anything under `${CLAUDE_PLUGIN_ROOT}/skills/`. Spec drift requires a design-proposal review cycle in the upstream repo.

## Red flags

These thoughts mean STOP — you are about to violate the contracts:

| Thought | Reality |
|---------|---------|
| "I'll just edit progress.md to fix the state" | Use `progress.py recover --confirm` if state is corrupt; never hand-edit. |
| "validate.py is being too strict, I'll skip it once" | The double-safety in `update --advance` will catch it; you only delay the failure. |
| "I'll advance the stage by editing `current_stage`" | Advance is `progress.py update --advance` — a 5-dimension precondition check, not a string assignment. |
| "Let me create a BUG report in active mode but skip bug-triage" | The skill state machine rejects orphan BUG reports without `root_cause`. |
| "The user is in a hurry, I'll skip the review" | Each `*-review` skill is the C-dimension owner; bypassing leaves P6 unsatisfied and the advance will fail anyway. |
| "I know what scenario this is, I'll skip scenario-dispatcher" | Scenario routing has subtle S2 sub-scenarios (S2-1/-2/-3/-4) and S2-4 → S3 transitions; let the dispatcher handle them. |
| "The skill seems overkill for this small task" | If a skill exists for the situation, invoke it. Small tasks become big when state is mismanaged. |
| "I'll just answer the user's clarifying question first, then check skills" | Skills come before answers. The skill might tell you the question itself is wrong. |

## Skill catalog (this plugin)

Use the `Skill` tool with one of these names. The list is stable across versions; new skills appear here when added.

**Orchestration**

- `using-dev-workflow` — this skill (loaded automatically; you are reading it now)
- `project-init` — bootstrap a fresh directory into a managed project (templates + `progress.py init`)
- `scenario-dispatcher` — pick S1 / S2-x / S3 / S4 and route
- `bug-triage` — classify bugs (active / post-close mode)
- `workflow-evolution` — incident analysis and resolution
- `brainstorming` — pre-skill brainstorming when scope is unclear

**Workflow binaries (skills wrapping the Python scripts)**

- `workflow-protocol` — the `progress.py` state machine
- `doc-guardian` — `validate.py` + `changelog.py` + `status_transition.py`

**Stage 1–3 (gated)**

- `prd-write`, `prd-review`
- `srs-write`, `srs-review`
- `architecture-write`, `architecture-review`

**Stage 4 (development)**

- `development-planning-write`, `development-planning-review`
- `development-test-write`, `development-test-review`
- `development-code-write`, `development-code-review`

**Stage 5–7**

- `testing-write`, `testing-review`
- `delivery-write`, `delivery-review`
- `retrospective-write`, `retrospective-review`

If the user asks for something outside this list, the plugin does not cover it — answer normally, no skill required.
