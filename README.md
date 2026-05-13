# dev-workflow-skills

A 7-stage product workflow skill set for **Claude Code** and **Codex**: PRD → SRS → Architecture → Development → Testing → Delivery → Retrospective. Each stage has dedicated write/review skills; project state is tracked in `progress.md` via a Python state machine; docs are validated by a separate `doc-guardian` binary. Bug Flow and Incident Flow handle exceptional paths from testing failures back to the right stage.

## What this plugin manages

When installed and active in a downstream project, the plugin's skills:

- **Bootstrap a new project** (`project-init`) — copies the managed-project template (`AGENTS.md`, `CLAUDE.md`, `docs/` skeleton) into your project root and runs `progress.py init`.
- **Route by scenario** (`scenario-dispatcher`) — picks S1 (new product), S2-1/-2/-3 (feature evolution), S3 (reconstruction), or S4 (bug fix) based on `progress.md` state and your input.
- **Drive each stage** through write + review pairs (`prd-write` / `prd-review` / `srs-write` / `srs-review` / `architecture-write` / `architecture-review` / `development-{planning,test,code}-{write,review}` / `testing-{write,review}` / `delivery-{write,review}` / `retrospective-{write,review}`).
- **Triage bugs and incidents** (`bug-triage`, `workflow-evolution`).
- **Enforce contracts** through two binaries: `progress.py` (workflow state machine, 12 subcommands) and `validate.py` (doc-guardian, 4 subcommands).

## Install

### Claude Code

The plugin metadata lives in `.claude-plugin/plugin.json`. Install via your Claude Code marketplace UI by pointing it at this repository, or by adding the local marketplace:

```jsonc
// claude-code marketplace config
{
  "marketplaces": [
    {
      "name": "dev-workflow-skills-dev",
      "source": "/path/to/dev-workflow-skills2"
    }
  ]
}
```

### Codex

Two install paths are supported. Full instructions and verification steps are in [`.codex/INSTALL.md`](.codex/INSTALL.md).

**Path A — Marketplace install** (Codex CLI ≥ 0.128.0, recommended):

```bash
codex plugin marketplace add /absolute/path/to/dev-workflow-skills2
```

Then in a Codex session: `/plugins` → search `dev-workflow-skills` → Install.

Codex reads `.agents/plugins/marketplace.json` first, then falls back to `.claude-plugin/marketplace.json`. This repo includes the `.agents/` marketplace shim because Codex 0.129 rejects a marketplace plugin source of `"./"` as an empty path.

**Path B — Native symlink** (older Codex):

```bash
mkdir -p ~/.agents/skills
ln -s /absolute/path/to/dev-workflow-skills2/skills ~/.agents/skills/dev-workflow-skills
```

Restart Codex. Skills become discoverable as `dev-workflow-skills:<skill-name>`. The SessionStart hook does NOT fire on this path — invoke `using-dev-workflow` manually per session.

### Manual (development mode)

If you want to use the plugin without going through a marketplace, point your harness's plugin path at this directory. The `SessionStart` hook in `hooks/hooks.json` injects the bootstrap skill into every new session.

## Quick start (after install)

In a fresh project directory you want this workflow to manage:

1. Start a session in the target dir.
2. Tell the agent: *"I want to manage this directory with the dev-workflow plugin."*
3. The agent invokes `project-init`, which copies the template, asks you for project metadata (name, scenario, release version), and runs `progress.py init`.
4. The agent then routes you to the appropriate stage skill (typically `prd-write` for a fresh project).

In an already-managed project (one with `progress.md` at the root):

1. Start a session.
2. The bootstrap skill (auto-loaded by the `SessionStart` hook) tells the agent to read `progress.md` and route to the active stage skill, or to invoke `bug-triage` / `workflow-evolution` if those flags are set.

## Repository layout

```
.agents/plugins/        # Codex local marketplace metadata
.claude-plugin/         # Claude Code plugin metadata
.codex-plugin/          # Codex plugin metadata
hooks/                  # SessionStart hook + bootstrap script
skills/                 # 24 skills (vertical write/review pairs + orchestration + binaries)
├── _shared/dev_workflow/   # Shared Python helpers
├── workflow-protocol/scripts/progress.py
├── doc-guardian/scripts/{validate.py,changelog.py,status_transition.py}
├── project-init/SKILL.md
├── scenario-dispatcher/SKILL.md
├── using-dev-workflow/SKILL.md   # Bootstrap skill
└── ...
templates/managed-project/  # Bootstrap template copied into downstream projects
docs/                   # Spec, design proposals, implementation plan, review reports, handoffs
tests/                  # 784 unit + integration + smoke tests for the binaries
AGENTS.md               # Contributor guide for working ON this spec repo
CLAUDE.md               # @AGENTS.md
```

## Working ON this repo (vs. using the plugin)

This repo is **not** a project managed by the workflow itself — it is the spec source. Do not run `progress.py init` here. Smoke and integration tests use `tempfile.TemporaryDirectory` for isolation; that pattern must continue. To bootstrap a downstream managed project, use the `project-init` skill against a separate target directory.

For the contributor entry point, see [`AGENTS.md`](AGENTS.md).

## Testing

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
```

The full suite (784 tests) runs in under 10 seconds and includes a managed-project happy-path smoke (S1 main + Bug Flow + Incident continue) that drives `progress.py` and `validate.py` end-to-end without mocking.

## License

MIT — see [`LICENSE`](LICENSE).
