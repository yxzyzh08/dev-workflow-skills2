# Task 6 Phase 5.4 Review — release lifecycle + bug-intake

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Code review for Phase 5.4 `release-close`, `release-start`, and `bug-intake`, including state-machine functions, replay handlers, CLI integration, BUG fan-out atomic writes, and new regression tests.  
**Recommendation**: **(B) fix before Phase 6** — the main release lifecycle implementation is solid and the test suite is green, but `release-start` can fan out writes to BUG paths outside `--root` if `unresolved_bugs` is corrupted through history/progress, and the `release-start` history summary does not include the required canonical `version=` token.

---

## 1. Executive Summary

Phase 5.4 adds the expected release lifecycle commands and reuses the existing lock/history/replay/transaction pipeline. The core state-machine transitions for `release-close`, `release-start`, and `bug-intake` are broadly aligned with `command-reference.md`; `release-start` correctly queues BUG frontmatter mutations in the same `atomic.transaction()` as `progress.md` and `progress-history.md`; replay intentionally does not read or rewrite BUG files; and the new test coverage exercises the key happy/reject paths.

I found one Medium issue and one Low issue:

| Severity | Count | Blocks Phase 6? | Summary |
|----------|-------|-----------------|---------|
| High | 0 | No | No immediate data-loss or transaction rollback defect found on the normal CLI path. |
| Medium | 1 | Yes | `release-start` trusts `unresolved_bugs` paths during BUG fan-out and can write outside `--root` if history/progress contains an absolute or `..` path. |
| Low | 1 | No | `release-start` puts `version=` only in `history_result`, not the summary header required by the Phase 5.4 canonical-history contract. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 454 tests in 3.733s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py --help
# OK; subcommands: init / query / recover / update / release-close / release-start / bug-intake

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py release-start --help
# OK; --version / --scenario / --agent are shown

find . -maxdepth 3 \( -name 'progress.md' -o -name 'progress-history.md' \) -print
# no output
```

No repo-root `progress.md` / `progress-history.md` files were created.

---

## 2. Findings

### High

No High findings.

### Medium

#### M1 — `release-start` BUG fan-out can write outside `--root` when `unresolved_bugs` is corrupted

- **Location**: `skills/workflow-protocol/scripts/progress.py:702`; related replay intake path at `skills/_shared/dev_workflow/progress_replay.py:281`; related state guard at `skills/_shared/dev_workflow/progress_state.py:990`
- **Issue**: The normal `bug-intake` CLI path rejects BUG paths outside `--root`, but replay and the pure state function accept any non-empty `bug=` token/string. Later, `_read_bug_for_release_start()` resolves `bug_rel` with `(root / bug_rel).resolve()` and does not verify that the resolved path is still under `root` or under `docs/bug/BUG-NNN.md`. If `progress.md`/`progress-history.md` is corrupted but replay-consistent, `release-start` can queue an extra write to an absolute path or path containing `..`.
- **Evidence**: A spot check calling `_read_bug_for_release_start(<absolute temp BUG path>, root)` accepted the outside path and returned that absolute path for the fan-out write target. The full CLI suite still passes because all normal `bug-intake` tests use relative in-root paths.
- **Impact**: The multi-file transaction boundary can escape the managed project root and mutate arbitrary files that happen to have BUG-like frontmatter. This weakens the Phase 5.4 guarantee that fan-out applies only to project BUG reports and makes malformed history more dangerous than a replay error.
- **Recommendation**: Add a shared BUG path validator used by `apply_bug_intake()` / `_apply_bug_intake_handler()` and `_read_bug_for_release_start()`: reject absolute paths, `..` traversal, paths outside `root`, and preferably anything not matching `docs/bug/BUG-\d{3}.md`. Add regression tests for replay rejecting an outside `bug=` token and for release-start refusing unresolved BUG paths that resolve outside `--root`, with progress/history unchanged.

### Low

#### L1 — `release-start` history summary lacks the canonical `version=` token

- **Location**: `skills/_shared/dev_workflow/progress_state.py:966`
- **Issue**: The Phase 5.4 prompt requires version/scenario/bug information to use canonical summary tokens (`version=`, `scenario=`, `bug=`) so replay can reverse them through `_kv_tokens`. Current `release-start` writes `history_summary` as `new release 0.2 started, scenario=S2-1, ...`; `version=0.2` appears only in `history_result` at `skills/_shared/dev_workflow/progress_state.py:970`.
- **Impact**: Runtime replay currently succeeds because `_kv_tokens()` reads summary plus result, but the history header is not canonical and any summary-only consumer or future parser would miss the version. This also leaves tests weaker: `tests/test_apply_release_start.py:143` joins summary and result instead of asserting summary-only canonical tokens.
- **Recommendation**: Change the summary to include `version=<x.y>` and `scenario=<S2-x>` (for example `version=0.2 scenario=S2-1 started; consumed=0 unresolved bugs`) and update tests to assert summary-only tokens.

---

## 3. Cross-Doc Consistency Check

| Reference / Contract | Status | Notes |
|----------------------|--------|-------|
| `command-reference.md` §5 `release-close` | ✓ | State preconditions and mutation match: active release, Stage 7 review-passed, close reason set, previous release appended. |
| `command-reference.md` §6 `release-start` | ⚠️ | Main state mutation and BUG target/consumed fan-out match. Path trust in fan-out needs hardening so only managed BUG files are mutated (M1). |
| `command-reference.md` §7 `bug-intake` | ✓ / ⚠️ | CLI preflight checks BUG type and null fields and rejects duplicate in normal use. Replay/state paths should share path-policy validation to prevent malformed history from feeding unsafe fan-out (M1). |
| `frontmatter-schema.md` §3.4 `bug-report` | ✓ | Phase 5.4 thin checks cover `type`, `target_release`, and `consumed_in_release`; full Class 1-7 validation remains deferred. |
| `task6_plan_20260507.md` §5.2 / §5.5 | ✓ | Release lifecycle and post-close intake semantics are implemented without Phase 6 commands. |
| `task6_plan_20260507.md` §11.1 / §11.2 | ✓ / ⚠️ | Atomic transaction placement for `release-start` is correct; path scope for extra writes should be explicitly enforced before Phase 6 (M1). |
| `skills/workflow-protocol/SKILL.md` command matrix | ✓ | Implemented command set is consistent with Phase 5.4 scope; Phase 6 commands remain unsupported. |
| Phase 5.3 replay-skips-artifacts design | ✓ | Release-start replay does not read BUG files, matching the forward-only fan-out design. |
| Phase 5.4 canonical history token contract | ⚠️ | `bug-intake` uses `bug=` and release-start has `scenario=`, but `version=` is in result only, not summary (L1). |

---

## 4. Checklist Results

### A. `apply_release_close` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| Active project + `review_iteration <= 7` | ✓ | Uses `_validate_active_project()` and `_validate_review_iteration_value()`. |
| `release_state=active` | ✓ | Rejects non-active release state. |
| `current_stage=project-retrospective` | ✓ | Rejects other stages. |
| `sub_state=review-passed` | ✓ | Rejects other sub-states. |
| Release format and duplicate prior release guard | ✓ | Validates current release string and rejects if already in `previous_releases`. |
| Mutation scope | ✓ | Only release close fields, `previous_releases`, and `updated` change. |
| Outcome/history fields | ✓ | Frozen dataclass with summary/result/next. |
| Tests | ✓ | 13 tests cover happy paths, rejects, field preservation, and frozen outcome. |

### B. `apply_release_start` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| Active project + iter guard | ✓ | Calls `_validate_review_iteration_value()` and rejects inactive projects. |
| `release_state=closed` | ✓ | Enforced. |
| Scenario subtype only `S2-1` / `S2-2` / `S2-3` | ✓ | `S2-4`, `S1`, `S3`, `S2`, and malformed values reject in tests. |
| Version format and strict greater-than prior releases | ✓ | Compares numeric `(major, minor)` tuples against current + previous release strings. |
| State reset | ✓ | New release/scenario/stage/sub_state/iteration/artifacts set; unresolved bugs cleared; development state removed. |
| Consumed bugs returned | ✓ | `ReleaseStartOutcome.consumed_bugs` feeds CLI fan-out. |
| `RELEASE_START_SUBTYPES` exposed | ✓ | Imported by CLI help. |
| History summary canonical tokens | ⚠️ | `scenario=` is in summary, but `version=` is only in result (L1). |
| Tests | ✓ / ⚠️ | Unit tests cover main state and rejects; summary-token test joins summary+result, missing the summary-only contract. |

### C. `apply_bug_intake` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| Active project + iter guard | ✓ | Enforced. |
| `release_state=closed` | ✓ | Enforced. |
| Non-empty string bug path | ✓ | Enforced. |
| Duplicate guard | ✓ | Rejects duplicate path in `unresolved_bugs`. |
| Mutation scope | ✓ | Appends to `unresolved_bugs` and updates timestamp. |
| Canonical `bug=` summary token | ✓ | Present. |
| Path safety for replay/direct state path | ⚠️ | Pure/replay path accepts absolute/traversal strings; CLI normalizes in-root paths (M1). |
| Tests | ✓ | 12 unit tests cover happy/reject/contract cases. |

### D. `progress_replay.py` 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `_kv_tokens()` parses summary + result | ✓ | Handles comma/space separated key-value tokens. |
| Release lifecycle handlers ignore root | ✓ | `del root` used. |
| Missing release-start tokens reject | ✓ | Error names expected `version=<x.y> scenario=<S2-x>`. |
| Missing bug token rejects | ✓ | Error mentions `bug=<path>`. |
| Handler set has 9 events | ✓ | `supported_events()` tests assert exact set. |
| Module docstring / unsupported-event message updated | ✓ | Phase 5.4 wording present. |
| Replay does not touch BUG files | ✓ | Explicit test uses empty tempdir. |
| Path policy for replayed `bug=` token | ⚠️ | Replay accepts any non-empty path via `apply_bug_intake()` (M1). |

### E. `progress.py` CLI

| Check | Result | Notes |
|-------|--------|-------|
| `extra_writes_factory` placement | ✓ | Runs after replay state equality and before `atomic.transaction()`. |
| Factory failures return 1 before writes | ✓ | Catches state/artifact/frontmatter/I/O failures before transaction. |
| `release-close` dispatch | ✓ | Uses `_run_update_pipeline(event_name="release-close")`. |
| `bug-intake` thin preflight | ✓ | Checks file exists, parse, type, null target/consumed, and duplicate in normal CLI path. |
| `bug-intake` path normalization | ✓ | CLI rejects paths outside `--root` before pipeline. |
| `release-start` CLI required args | ✓ | Missing `--version` / `--scenario` returns 2. |
| BUG fan-out in transaction | ✓ | Extra writes are queued and written within the same transaction as progress/history. |
| `_read_bug_for_release_start` path containment | ❌ | It accepts absolute/outside paths from `outcome.consumed_bugs` (M1). |
| Argparse layout + dispatcher | ✓ | Seven subcommands are present and routed. |

### F. Unit tests for apply functions

| Check | Result | Notes |
|-------|--------|-------|
| Pure state-machine unit tests | ✓ | The apply tests are pure and use in-memory state. |
| Happy / rejection / contract organization | ✓ | Consistent style across three files. |
| Reject paths assert exception type and key tokens | ✓ / ⚠️ | Most important rejects assert key tokens; a few only assert type, acceptable but less diagnostic. |
| Field preservation/reset coverage | ✓ | Covered for release-close, release-start, and bug-intake. |

### G. CLI tests

| Check | Result | Notes |
|-------|--------|-------|
| Temp-dir isolation | ✓ | CLI test classes use `TemporaryDirectory`. |
| Synthetic advance handler scoped | ✓ | Patch is context-scoped. |
| Progress/history synchronized in fixtures | ✓ | Helpers update both files for M1 consistency. |
| BUG fan-out happy path | ✓ | Two BUGs are consumed and frontmatter fields set. |
| Stale BUG reject | ✓ | `target_release` already set rejects before writes. |
| Recover roundtrip | ✓ | Release-start and bug-intake roundtrips covered. |
| Bug-intake reject matrix | ✓ | Active release, missing BUG, wrong type, target/consumed set, duplicate covered. |
| Timestamp monotonicity | ✓ | `_FakeClock` is used. |
| Outside/traversal path fan-out regression | ❌ | No test currently covers corrupted unresolved BUG paths (M1). |

### H. `tests/test_progress_replay.py` 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `ReplayReleaseLifecycleTests` coverage | ✓ | Six tests cover close/start/intake/missing-token/no-BUG-file replay. |
| `supported_events` exact 9 | ✓ | Covered. |
| Unsupported event switched to Phase 6 sample | ✓ | Uses `bug-start`. |
| `test_progress_recover` unsupported event updated | ✓ | Uses `bug-start`. |
| Path policy for replayed `bug=` | ⚠️ | Missing negative coverage for absolute or traversal paths (M1). |

### I. Existing invariants

| Check | Result | Notes |
|-------|--------|-------|
| Prior 383 tests still pass | ✓ | Full suite now 454 tests OK. |
| `compileall` passes | ✓ | Shared modules, scripts, and tests compile. |
| `progress_lock.py` / `progress_history.py` behavior preserved | ✓ | No regressions detected. |
| init/query/recover/update event/task preserved | ✓ | Existing tests pass. |
| M1 history parse + replay + diff inherited | ✓ | New commands share `_run_update_pipeline()`. |
| M2 review iteration guard inherited | ✓ | All three new apply functions call `_validate_review_iteration_value()`. |
| Replay skips BUG files by design | ✓ | Implemented and tested. |

### J. Design / maintainability

| Check | Result | Notes |
|-------|--------|-------|
| Outcome dataclass duck type | ✓ | All new outcomes expose the expected pipeline fields; release-start adds `consumed_bugs`. |
| `extra_writes_factory` extensibility | ✓ | The hook is a clean path for future multi-file writes. |
| BUG fan-out error messages | ✓ / ⚠️ | Field/type errors name BUG rel path and field; path containment error is missing because containment is not enforced (M1). |
| Helper responsibility split | ✓ | Intake preflight vs release-start fan-out helpers are conceptually clear. |
| Import layout | ✓ | Existing `noqa: E402` style is maintained. |

---

## 5. Open Questions / Assumptions

- I agree with the design choice that replay must not rewrite BUG files. `release-start` BUG consumption is a forward-time side effect, and replay should validate progress state from history rather than mutate current artifacts.
- I assume `unresolved_bugs` should contain only managed-project BUG paths such as `docs/bug/BUG-001.md`. The CLI normal path enforces this for `bug-intake`; the issue is that replay/direct state paths do not enforce the same policy before `release-start` fan-out.
- I assume `release-start` need not run full doc-guardian Class 1-7 validation on BUG files in Phase 5.4; the findings above concern only path scope and canonical history tokens, not deferred schema consistency.

---

## 6. Recommendation

**(B) fix before Phase 6**.

Must fix before entering Phase 6:

1. **M1**: Enforce BUG path containment/canonical shape for replay/direct state paths and release-start fan-out. At minimum, `_read_bug_for_release_start()` must reject resolved paths outside `root`; preferably `apply_bug_intake()` / replay should also reject absolute paths, `..`, and non-`docs/bug/BUG-\d{3}.md` paths.

Can be deferred to Phase 7 polish if necessary, but cheap to fix now:

- **L1**: Put `version=<x.y>` in the `release-start` history summary and strengthen tests to assert summary-only canonical tokens.

Estimated fix path:

- M1: add a small path-normalization helper plus 2-3 tests; no state-machine redesign needed.
- L1: one summary string change plus 1-2 assertion updates.
