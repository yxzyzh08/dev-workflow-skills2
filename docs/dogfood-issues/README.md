# Dogfood Issues

This directory tracks issues discovered while using the `dev-workflow-skills` plugin against real downstream projects ("dogfooding"). Each issue gets a numbered file; `INDEX.md` keeps the live list with status. Once an issue is fixed, the file stays here as a permanent record (status updated to `fixed`, with the fixing commit / PR linked).

## Why a dedicated directory

Issues found while dogfooding don't belong to any in-workflow `BUG-*.md` (that's for the *downstream project's own* bugs, tracked by `bug-triage` and consumed by `progress.py` state machine). Dogfood issues are about the **plugin and spec themselves** — the upstream artifacts maintainers fix here in `dev-workflow-skills2`, not via the workflow's Bug Flow.

Examples of issues that belong here:

- The `using-dev-workflow` bootstrap skill failed to auto-route in Codex 0.128.0.
- `progress.py update --advance` rejected a legitimate state because of a missing dimension-A artifact that was actually unnecessary for that scenario.
- The `prd-template.md` reference said one thing but `prd-write/SKILL.md` said another.
- Installing via `codex plugin marketplace add` succeeded but `/plugins` didn't show the entry until restart.
- The hook `session-start` script printed wrong JSON shape for harness X.

Examples of issues that do **not** belong here (use the in-workflow Bug Flow instead):

- A bug in the user's own application code under `src/` of the managed project.
- A failing acceptance criterion in the user's own SRS.

## File layout

```
docs/dogfood-issues/
├── README.md          # this file
├── INDEX.md           # live list of open + recently-fixed issues
├── _template.md       # copy this when filing a new issue
└── NNN-<slug>.md      # one file per issue (e.g. 001-codex-hook-not-firing.md)
```

`NNN` is a zero-padded 3-digit serial (001, 002, …, 042, …). Pick the next unused number from `INDEX.md`. The slug is a short kebab-case description.

## Filing a new issue

1. Copy `_template.md` to `NNN-<slug>.md` (next unused N).
2. Fill in every field; leave fields you don't know yet as `<unknown>` rather than deleting them.
3. Add a row to `INDEX.md` under "Open" with the same metadata.
4. Commit; reference the issue file in any related commit or PR description.

## Lifecycle

| Status | Meaning |
|--------|---------|
| `open` | Reproduced, root cause not yet fixed |
| `investigating` | Someone is actively triaging; expect a status update within a session or two |
| `fix-pending` | Fix proposed (PR / commit drafted) but not yet landed |
| `fixed` | Fix landed; `Fixed in` field has the commit / PR reference; row moved to "Fixed" section in `INDEX.md` |
| `wontfix` | Decided not to fix (with reason); kept for posterity |
| `duplicate` | Subsumed by another issue (with cross-link) |

`fixed` and `wontfix` issues stay on disk forever — they're the dogfood history.

## Severity

| Severity | Meaning |
|----------|---------|
| `blocking` | Real downstream projects cannot proceed without a workaround |
| `high` | Workaround exists but is awkward / error-prone |
| `medium` | Cosmetic or wording drift; doesn't block usage |
| `low` | Minor polish; nice-to-have |

Severity is set by the filer; the maintainer can adjust during triage.
