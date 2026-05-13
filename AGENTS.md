# AGENTS.md

Entry doc for any agent (Claude Code, Codex, others) opening a session in this repo.

## What this repo is

`dev-workflow-skills2` is the **spec + binary-script source** for the dev-workflow skill set (workflow-protocol, doc-guardian, plus 22 vertical skills). It defines:

- The 7-stage / 4-scenario workflow specification (PRD → SRS → Architecture → Development → Testing → Delivery → Retrospective; S1/S2/S3/S4 + Bug Flow + Incident Flow).
- The `progress.py` state machine and `validate.py` doc checks under `skills/workflow-protocol/scripts/` and `skills/doc-guardian/scripts/`.
- The reference docs that consumers (vertical write/review skills, downstream managed projects) treat as authoritative.

## What this repo is NOT

- **Not a project managed by this workflow.** Do not run `progress.py init` here. Do not create `progress.md` / `progress-history.md` at the repo root. Smoke and integration tests use `tempfile.TemporaryDirectory` for isolation; that pattern must continue. To bootstrap a downstream managed project, use `skills/project-init/SKILL.md` against a separate target directory; the template lives at `templates/managed-project/` and is never installed into this repo's root.
- Not a Codex plugin distribution (yet). `.codex-plugin/plugin.json` and marketplace metadata are deferred until an explicit decision lands.

## Current state (as of Task 6 closure)

- **Task 6 implementation closed (A)** across Phase 1–6.4: 13 shared modules + `progress.py` (12 subcommands) + `validate.py` (4 subcommands; `all` deferred) + 28 test files = 784 tests pass; `compileall` clean.
- **Phase 7**: managed-project happy-path smoke + reference wording polish + entry docs (this file). After Phase 7 closure: Task 7-A (SKILL.md drift audit) + Task 7-B (PRD/SRS/Architecture references拆出) + Task 7-C (project-init + templates/managed-project/) + plugin packaging (`.claude-plugin/`, `.codex-plugin/`, `hooks/`, `using-dev-workflow` bootstrap skill) all landed.

## Plugin runtime entry point (vs. this contributor entry)

This file (`AGENTS.md` at the repo root) is the **contributor entry** — for an agent or human working ON this spec repo. When this repo is loaded as a **plugin** in some downstream project (via `.claude-plugin/plugin.json` or `.codex-plugin/plugin.json`), the runtime entry is different:

- The harness fires the `SessionStart` hook registered in `hooks/hooks.json`.
- The hook runs `hooks/session-start` (via the `hooks/run-hook.cmd` polyglot wrapper), which injects `skills/using-dev-workflow/SKILL.md` into the new session as `additionalContext`.
- That bootstrap skill tells the agent to detect the target project's `progress.md` state and route to `project-init` / `scenario-dispatcher` / a stage skill / `bug-triage` / `workflow-evolution`.
- The downstream project's own `AGENTS.md` (generated from `templates/managed-project/AGENTS.md`) is the project-specific governance layer; this repo's `AGENTS.md` is **never** loaded into a downstream session.

So: editing this file affects contributors only. To affect plugin runtime behavior, edit `skills/using-dev-workflow/SKILL.md` (the bootstrap skill content) or `templates/managed-project/AGENTS.md` (the per-project governance template).

## New session read order

When you start a session, read these in order:

1. The most recent `docs/handoff/session_handoff_*.md` (start with the latest `session_handoff_task6_phase7_*.md` until the closure handoff lands).
2. `docs/implementation/task6_plan_20260507.md` — the implementation plan; §13/§14/§15 cover Phase 7 + acceptance + rejected alternatives.
3. `docs/workflow/workflow_specification_claude.md` — top-level workflow spec (v0.2 merged) for stage / scenario / Bug Flow / Incident Flow semantics.
4. `skills/workflow-protocol/references/command-reference.md` — every `progress.py` subcommand's exact pre-conditions and field mutations (Phase 7 polish landed here).
5. `skills/doc-guardian/references/` — `frontmatter-schema.md`, `directory-layout.md`, `required-artifacts.md`, `change-log-format.md`.

## Mandatory contracts

- **State mutation**: every `progress.md` / `progress-history.md` change MUST go through a `progress.py` subcommand. Hand-editing is forbidden — replay-consistency, advisory locking, and history append are coupled.
- **Doc validation**: every doc-guardian-managed doc MUST pass `python3 skills/doc-guardian/scripts/validate.py file <path>` before any consumer treats it as final. `progress.py update --advance` re-runs validate as P6 dimension B.
- **Spec changes**: do not edit `skills/{workflow-protocol,doc-guardian}/references/` to win arguments — they are derived from `docs/workflow/workflow_specification_claude.md`. Spec drift goes through a design-proposal review cycle (see `docs/review/`).
- **No bypassing**: no skipping hooks, no `--no-verify`, no editing `progress.md` to "fix a bug." Use `progress.py recover --confirm` for genuine corruption.

## Development protocol

After any code change touching `skills/` or `tests/`:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
test ! -e progress.md && test ! -e progress-history.md && echo "ROOT CLEAN"
```

All three must pass. The 784-test number is the floor — new work adds tests, never trims them.

## Where new artifacts belong

- Spec deltas / design proposals → `docs/design/`
- Implementation plans → `docs/implementation/`
- Review reports → `docs/review/`
- Session handoffs → `docs/handoff/`
- Research notes → `docs/research/`
- Dogfood issues (problems found while *using* the plugin against real downstream projects, batched for fixing in this upstream repo) → `docs/dogfood-issues/` (see `docs/dogfood-issues/README.md` for the filing template and lifecycle)
- Test files → `tests/test_*.py`
- Shared workflow modules → `skills/_shared/dev_workflow/`
- Workflow-protocol scripts → `skills/workflow-protocol/scripts/`
- Doc-guardian scripts → `skills/doc-guardian/scripts/`
- Vertical skill implementations (Task 7+) → `skills/<skill-name>/`
- **Bootstrap templates for downstream managed projects** → `templates/managed-project/` (consumed by the `project-init` skill; do not copy from this directory by hand — invoke `skills/project-init/SKILL.md` to bootstrap a new managed project)

## Repository conventions

- Python target: 3.10+ (uses `from __future__ import annotations` and PEP-604 unions in tests).
- No external package manager assumed; standard library + `pyyaml` only.
- Atomic file writes go through `skills/_shared/dev_workflow/atomic.py` `transaction()`; never use raw `open(path, "w")` for `progress.md` / history / validated docs.
- Frontmatter parsing / rendering goes through `skills/_shared/dev_workflow/frontmatter.py`; never hand-write YAML headers.
- All file paths in code use `pathlib.Path` and forward-slash representation when serialised.
