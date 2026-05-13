# Task 6 Phase 5.1 Review — progress.py Core (init / query / recover)

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Phase 5.1 implementation for `progress.py` foundation (`progress_lock.py`, `progress_history.py`, `progress_replay.py`, `progress_state.py` extension, `progress.py` CLI, and six new test files).  
**Recommendation**: **(B) fix before Phase 5.2** — the implementation is largely solid, but replay timestamp-order validation is currently ineffective and should be corrected before Phase 5.2 builds more mutating handlers on top of replay.

---

## 1. Executive Summary

Phase 5.1 covers the intended surface area: lock/history/replay modules exist, `init` / `query` / `recover` are wired, state construction matches the init schema, and tests use temporary project roots rather than creating repo-root `progress.md` / `progress-history.md`.

Findings distribution:

| Severity | Count | Blocks Phase 5.2? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss or direct repo-mutation defect found in the implemented Phase 5.1 paths. |
| Medium | 2 | Yes | Replay sorts before checking timestamp monotonicity; invalid init scenario exits as CLI usage code 2 instead of validation failure code 1. |
| Low | 0 | No | No additional low-severity implementation defect recorded. |

Overall judgment: **close, but not ready to proceed to Phase 5.2 until the two Medium findings are fixed**. The first finding is foundational because Phase 5.2+ will depend on replay for consistency and recovery across multiple state-changing events.

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 227 tests in 1.640s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# exit 0

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py init --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py query --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py recover --help
# all OK
```

Additional checks:

- Symlink invocation of `progress.py --help` worked with the `parents[3]` bootstrap.
- `find . -maxdepth 3 \( -name 'progress.md' -o -name 'progress-history.md' \)` returned no repo-root managed workflow files.
- `git status --short` still shows the expected broad untracked project content; no clean/reset/delete action was taken.

---

## 2. Findings

### High

No High findings.

### Medium

#### M1 — Replay sorts history before checking whether timestamps go backwards

- **Location**: `skills/_shared/dev_workflow/progress_replay.py:131`
- **Related test gap**: `tests/test_progress_replay.py:121`
- **Issue**: `replay_history()` first calls `iter_entries_chronological(history)`, which sorts entries by timestamp, and only then checks `if entry.timestamp < prev_ts`. After sorting ascending, that condition is effectively unreachable for a physically out-of-order history file. The current regression test only asserts that *some* `ReplayError` is raised for two decreasing `init` entries; it passes because the second `init` is rejected as duplicate, not because timestamp monotonicity was detected.
- **Impact**: A corrupted or clock-skewed append order can be silently reordered before validation. In Phase 5.1 this is mostly masked by the single `init` handler, but Phase 5.2+ will add legal multi-event histories where replaying sorted order instead of document append order can hide history corruption or validate a different transition sequence than what was actually written. This conflicts with the prompt requirement that a second timestamp earlier than the first must produce `ReplayError`, and it weakens future consistency replay.
- **Recommendation**: Validate monotonicity in the original parsed/document order before sorting or applying handlers. If replay must still apply chronological order, compare adjacent entries in original order first and raise `ReplayError("timestamp goes backwards ...")` before handler dispatch. Add a regression test that asserts the exact backwards-timestamp error for decreasing timestamps, not merely any `ReplayError`.

#### M2 — Invalid `init --scenario` is classified as usage error instead of validation failure

- **Location**: `skills/workflow-protocol/scripts/progress.py:346`
- **Related test gap**: `tests/test_progress_init.py:190`
- **Issue**: `argparse` uses `choices=sorted(SCENARIOS_INIT)` for `--scenario`, so `progress.py init --scenario S2` exits with code 2 before reaching `cmd_init()`. The Phase 5.1 prompt explicitly lists `scenario / release / project_name` validation failures under `init` as exit code 1, with no `progress.md` / `progress-history.md` creation.
- **Impact**: Automation can distinguish usage errors (code 2) from workflow precondition/validation failures (code 1). Returning code 2 for a bad workflow value makes invalid scenario handling inconsistent with invalid release/project handling and with the stated CLI contract.
- **Recommendation**: Remove the `choices=` guard from argparse and let `build_initial_state()` / `_validate_scenario_init()` produce the same code-1 path used by release and project name validation. Update the test to expect exit 1 and verify no `progress.md` / `progress-history.md` is created.

### Low

No Low findings.

---

## 3. Cross-Doc Consistency Check

| Source | Result | Notes |
|--------|--------|-------|
| `skills/workflow-protocol/references/command-reference.md` §1 (`init`) | ✓ / ⚠️ | The generated state fields match the init mutation table, including initial artifacts, bug flow, timestamps, and active release fields. The first history entry includes an extra `project=<name>` token, which is necessary for recover replay and is compatible with the header summary format. The scenario validation exit code mismatch is tracked as M2. |
| `skills/workflow-protocol/references/command-reference.md` §3 (`query`) | ✓ | `query` is read-only, takes no lock, supports full YAML, full JSON, field output, and errors for missing/corrupt `progress.md` or unknown fields. |
| `skills/workflow-protocol/references/command-reference.md` §4 (`recover`) | ⚠️ | `recover` uses strict history parsing, replay, lock, and atomic rewrite, and leaves history unchanged. The terminal-state scaffold exists with empty Phase 5.1 sets. The replay timestamp-order check is ineffective because of pre-validation sorting (M1). |
| `docs/implementation/task6_plan_20260507.md` §5 | ✓ / ⚠️ | Implemented only the Phase 5.1 subset (`init`, `query`, `recover`) and did not implement deferred commands. The replay ordering issue affects the recovery contract that later update/release/bug/incident commands will rely on. |
| `docs/implementation/task6_plan_20260507.md` §11.1 | ✓ / ⚠️ | Mutating implemented commands use `.progress.lock` and `atomic.transaction()`; `query` does not lock. The future consistency replay path should not proceed until M1 is fixed. |
| `docs/implementation/task6_plan_20260507.md` §13 / §15 | ✓ | Phase boundaries are respected; no Phase 5.2/5.3/5.4/6 commands are implemented or judged missing. Full tests pass locally. |
| `skills/workflow-protocol/SKILL.md` command matrix | ✓ | The script exposes only `init`, `query`, and `recover` for Phase 5.1; all other listed commands remain deferred. The SKILL history schema mentions future `task` fields, but the Phase 5.1 prompt intentionally restricts the parser to `agent` / `result` / `next`. |

---

## 4. Checklist Results

### A. `progress_lock.py`

| Check | Result | Notes |
|-------|--------|-------|
| Uses `fcntl.flock` rather than stale lock-file semantics | ✓ | `fcntl.flock(fd, LOCK_EX | LOCK_NB)` is used; the lock file can persist safely. |
| Timeout implemented by non-blocking poll | ✓ | Poll loop raises `ProgressLockError` with clear timeout text. |
| Context exit releases lock even on body exception | ✓ | Unlock is in the inner `finally`; fd close is in the outer `finally`. |
| File descriptor closed in `finally` | ✓ | `os.close(fd)` is best-effort guarded. |
| Missing root directory created | ✓ | `root_path.mkdir(parents=True, exist_ok=True)`. |
| Tests cover primitive behavior | ✓ | Acquire/release, missing root, fork contention, timeout, and sequential reentry are covered. |

### B. `progress_history.py`

| Check | Result | Notes |
|-------|--------|-------|
| Header regex matches strict Phase 5.1 format | ✓ | Timestamp, event token, em dash separators, and non-empty summary are anchored. |
| Body field whitelist is enforced | ✓ | Only `agent`, `result`, and `next` parse; unknown/duplicate/outside-entry fields raise. |
| Rendering omits absent optional fields | ✓ | `None` fields are skipped. |
| Append preserves title and spacing | ✓ | `# Project History` is compatible; entries are separated by one blank line. |
| Chronological helper stable-sorts | ✓ | Implemented, but replay's use of sorting before monotonicity validation is tracked separately as M1. |
| Tests cover parser/renderer basics | ✓ | Empty/single/multi/round-trip/header/field/duplicate/unknown-line cases are present. |

### C. `progress_replay.py`

| Check | Result | Notes |
|-------|--------|-------|
| Only `init` handler registered in Phase 5.1 | ✓ | `supported_events()` returns `{'init'}`. |
| Unsupported events reject clearly | ✓ | Error names the event and states Phase 5.1 only implements `init`. |
| `_apply_init` rejects non-first init | ✓ | State non-empty path raises `ReplayError`. |
| `_apply_init` extracts project/scenario/release | ✓ | Summary and `result` are both searched for key-value tokens. |
| `build_initial_state` validation reused | ✓ | Invalid project/scenario/release/timestamp flow through `ProgressStateError` to `ReplayError`. |
| Timestamp backwards detection | ❌ | M1: sorting before the monotonicity check prevents detection in document order. |
| Terminal-state framework present | ✓ | `TERMINAL_EVENTS` and `READ_ONLY_EVENTS` are empty Phase 5.1 sets with hook points. |
| Tests cover replay framework | ⚠️ | Coverage is broad, but the backwards timestamp test does not assert the intended failure mode and currently passes for the wrong reason. |

### D. `progress_state.py` extension

| Check | Result | Notes |
|-------|--------|-------|
| Init fields match command-reference §1 | ✓ | Required top-level fields, nested `artifacts`, nested `bug_flow`, incident fields, and timestamps are present. |
| Validators match Phase 5.1 scope | ✓ | Project name, release, init scenarios `{S1, S3}`, and second-precision UTC timestamp regex are implemented. |
| No Phase 5.2/5.3 state machine added | ✓ | Existing NORMAL/PROTECTED task transition split remains intact; no event handlers were added here. |
| Body template is reusable/readable | ✓ | `PROGRESS_BODY_TEMPLATE` is module-level and referenced by init/recover. |

### E. `progress.py` CLI

| Check | Result | Notes |
|-------|--------|-------|
| Subcommands are limited to `init` / `query` / `recover` | ✓ | Deferred commands are not implemented. |
| `--root` and `--lock-timeout` are global | ✓ | Both are parsed before subcommands; root defaults to cwd. |
| Bootstrap uses `parents[3]` and works via symlink | ✓ | Manual symlink `--help` smoke passed. |
| `init` lock + overwrite + atomic two-file write | ✓ | Existing `progress.md` or `progress-history.md` rejects; successful writes use one `transaction()`. |
| `init` field validation exit code | ⚠️ | Release/project errors return 1; invalid scenario returns 2 due argparse choices (M2). |
| `query` is read-only and unlocked | ✓ | Lock-held query test passes; missing/corrupt/unknown field paths return 1. |
| `query` output formatting | ✓ | Scalars, `null`, bools, dict YAML, and JSON are covered. |
| `recover` confirmation, lock, parse/replay, and atomic write | ✓ | `--confirm` required; history failure paths do not write; success rewrites progress only. |
| Exit code contract | ⚠️ | No subcommand returns 2 as expected; M2 is the scenario-value exception. |

### F. Tests

| Check | Result | Notes |
|-------|--------|-------|
| Six new test files cover lock/history/replay/init/query/recover | ✓ | 67 new Phase 5.1 tests are present. |
| CLI runner isolates stdout/stderr and catches `SystemExit` | ✓ | `_run` helpers do this across CLI test files. |
| Tests use temp roots, not real repo state | ✓ | Temp directories are used for managed-project fixtures. |
| Seed helpers suppress output | ✓ | Query/recover seeds redirect stdout/stderr. |
| Atomicity and unchanged-history assertions | ✓ | Lock-busy init/recover and recover history byte equality are covered. |
| Lock-blocked init/recover paths | ✓ | Both paths have tests. |
| Unsupported future event during recover | ✓ | `release-close` history rejects in Phase 5.1. |
| Regression precision for found issues | ⚠️ | M1 is masked by a broad `assertRaises`; M2 is codified by a test expecting exit 2. |

### G. Existing invariant consistency

| Check | Result | Notes |
|-------|--------|-------|
| Multi-file atomicity uses `atomic.transaction()` | ✓ | `init` writes both files in one transaction; `recover` writes progress via transaction. |
| Progress parsing/rendering uses frontmatter helpers | ✓ | `read_markdown` and `render_markdown` are reused. |
| Phase 4 scripts not touched by Phase 5.1 review scope | ✓ | No behavioral changes found in `status_transition.py`, `validate.py`, or `changelog.py` during this review. |
| Full suite and compile check pass | ✓ | 227 unittest tests pass; `compileall` passes with pycache redirected outside the repo. |
| Repo root remains unmanaged | ✓ | No `progress.md` / `progress-history.md` exists under the implementation repo root. |

---

## 5. Open Questions / Assumptions

- **History field scope**: I assume Phase 5.1 intentionally rejects `- task:` even though the SKILL-level schema documents it for future Stage 4 history entries. Phase 5.3 should revisit the parser whitelist when `update --task` lands.
- **Timestamp validation depth**: I treated second-precision `YYYY-MM-DDTHH:MM:SSZ` regex validation as acceptable for Phase 5.1 because existing docs specify ISO8601 UTC but do not define calendar-date parsing requirements. If strict real-date validation is desired, add it as a future hardening task.
- **Recover body template**: I assume recover is allowed to regenerate the canonical Phase 5.1 progress body instead of trying to reconstruct a prior manual body; `progress.md` is script-owned and body text is derived/readable summary only.

---

## 6. Recommendation

**(B) fix before Phase 5.2**.

Required before Phase 5.2:

1. **Fix M1**: validate timestamp monotonicity in document order before sorting/handler replay, and update the regression test to assert the backwards-timestamp error. Estimated scope: ~10-25 implementation LOC plus ~5-15 test LOC.
2. **Fix M2**: remove argparse `choices=` for `init --scenario`, route scenario validation through the same code-1 validation path as release/project, and update the test expectation. Estimated scope: ~5-10 implementation LOC plus ~2-5 test LOC.

Can be deferred:

- Adding `task` field support to `progress_history.py` should wait until Phase 5.3 `update --task` defines the exact rendering/replay contract.
- Strict calendar-date parsing for timestamps can be deferred unless the project decides regex-only ISO8601 checks are insufficient.

Why Phase 5.2 should not proceed first:

- Phase 5.2 adds `update --event` and will start depending on replay as a real multi-event consistency validator. If M1 remains, recovery and future consistency checks can validate a timestamp-sorted sequence rather than the append-only history sequence that was actually written.
- M2 is small but should be fixed now so future CLI validation paths do not copy the same `argparse choices -> exit 2` pattern for workflow values that should be state/precondition failures.
