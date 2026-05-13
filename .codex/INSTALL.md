# Installing dev-workflow-skills for Codex

This plugin includes a Codex-native local marketplace at `.agents/plugins/marketplace.json`. Claude Code still uses `.claude-plugin/marketplace.json`. Two install paths are documented here; pick one.

## Prerequisites

- **Path A (recommended)**: Codex CLI **≥ 0.128.0** (run `codex --version` to check). This release added native local-marketplace support — you can register the plugin from a local directory in one command.
- **Path B (fallback / older Codex)**: Git + symlink permissions (Windows requires Developer Mode or `mklink /J` junction).

## Path A — Marketplace install (recommended)

### 1. Register the local marketplace

From any shell:

```bash
codex plugin marketplace add /home/cgs/github_projects/dev-workflow-skills2
```

You should see:

```
Added marketplace `dev-workflow-skills-dev` from /home/cgs/github_projects/dev-workflow-skills2.
```

Codex writes a `[marketplaces.dev-workflow-skills-dev]` section to `~/.codex/config.toml` with `source_type = "local"` and the absolute path. The marketplace name (`dev-workflow-skills-dev`) comes from `.agents/plugins/marketplace.json` in this repo.

### 2. Install the plugin

Start a Codex CLI session:

```bash
codex
```

Inside the session run the plugin browser:

```
/plugins
```

Search for `dev-workflow-skills`, select it, choose **Install**. Codex copies the plugin's metadata, skills, and hooks into its runtime. You may need to restart the Codex session for the SessionStart hook (defined in `hooks/hooks.json`) to fire.

### 3. Verify

Start a **fresh** Codex session in a directory you want to manage (e.g. `cd /tmp && mkdir testproj && cd testproj && codex`). Tell the agent:

> I want to manage this directory with the dev-workflow plugin.

A working install should:

- Auto-invoke the `using-dev-workflow` skill (via `SessionStart` hook → bootstrap context injection).
- Route you through `project-init` to copy `templates/managed-project/` into the directory and run `progress.py init`.
- After bootstrap, route to `prd-write` (Stage 1).

If the agent does not auto-invoke `using-dev-workflow` (Codex hook compatibility varies), you can manually invoke it the first time:

```
Use the using-dev-workflow skill to detect this project's state and route me.
```

### 4. Update

Re-pull the plugin source (this repo) and ask Codex to refresh the marketplace:

```bash
codex plugin marketplace upgrade dev-workflow-skills-dev
```

### 5. Uninstall

```bash
codex plugin marketplace remove dev-workflow-skills-dev
```

This removes the marketplace registration; the plugin source on disk is untouched.

## Path B — Native symlink (older Codex / no marketplace command)

For Codex versions before native skill discovery added the `plugin marketplace` subcommand, expose the skills via the same `~/.agents/skills/` mechanism that superpowers uses.

### Linux / macOS

```bash
mkdir -p ~/.agents/skills
ln -s /home/cgs/github_projects/dev-workflow-skills2/skills ~/.agents/skills/dev-workflow-skills
```

### Windows (PowerShell)

```powershell
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
cmd /c mklink /J "$env:USERPROFILE\.agents\skills\dev-workflow-skills" "<absolute path to>\dev-workflow-skills2\skills"
```

Restart Codex. Skills are now discoverable as `dev-workflow-skills:<skill-name>` (e.g. `dev-workflow-skills:using-dev-workflow`).

**Caveat**: symlink mode does **not** load the `hooks/hooks.json` SessionStart hook. The agent will not be auto-bootstrapped with `using-dev-workflow`. You must invoke it manually each session:

```
Use the dev-workflow-skills:using-dev-workflow skill to start.
```

### Update (Path B)

Whatever updates the source repo (e.g. `git pull` if you cloned it) updates the live skills instantly through the symlink.

### Uninstall (Path B)

```bash
rm ~/.agents/skills/dev-workflow-skills
```

(Windows: `Remove-Item "$env:USERPROFILE\.agents\skills\dev-workflow-skills"`.)

## Troubleshooting

### `codex plugin marketplace add` fails

- Ensure Codex CLI ≥ 0.128.0 (`codex --version`). Older versions don't support local-path marketplaces — fall back to Path B.
- Pass an absolute path; relative paths may be resolved against the wrong cwd.
- Make sure the path contains `.agents/plugins/marketplace.json`. Codex 0.129 also recognizes `.claude-plugin/marketplace.json`, but a plugin source of `"./"` is rejected as an empty path, so this repo uses the `.agents/` shim.

### `/plugins` doesn't show dev-workflow-skills

- Restart the Codex session — marketplaces registered mid-session may not reflect.
- Check the marketplace entry is in `~/.codex/config.toml` under `[marketplaces.dev-workflow-skills-dev]`.
- Re-add the marketplace: `codex plugin marketplace remove dev-workflow-skills-dev` then `codex plugin marketplace add /path/to/repo`.

### Hook doesn't fire automatically (no auto-bootstrap)

- Codex hook compatibility for `SessionStart` is harness-version dependent. The fallback is to manually invoke `using-dev-workflow` per session (see verify step above).
- If you find a stable way to make the hook fire on Codex, please file an issue or PR with the exact Codex version and the env var the hook script should branch on (current branches: `CURSOR_PLUGIN_ROOT`, `CLAUDE_PLUGIN_ROOT`, `COPILOT_CLI`).

### `progress.py` errors with import or path issues when invoked from inside Codex

- The plugin's binaries (`progress.py`, `validate.py`) need their own `skills/_shared/dev_workflow/` modules on `sys.path`. They handle that via `_REPO_ROOT = Path(__file__).resolve().parents[3]`. As long as the symlink / install copy preserves the `skills/<name>/scripts/<file>.py` layout (4 levels deep), imports work.
- If you copy individual scripts out of the layout, imports will break. Don't reorganize the tree.

## Reference

- Plugin metadata: `.agents/plugins/marketplace.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`.
- Bootstrap skill: `skills/using-dev-workflow/SKILL.md`.
- SessionStart hook: `hooks/hooks.json` + `hooks/run-hook.cmd` (polyglot wrapper) + `hooks/session-start` (bash injection).
- Top-level docs: `README.md`, `AGENTS.md`, `CLAUDE.md`.
