# Task 6 Phase 6.2 `bug-rework` Review — 2026-05-07

## 1. Executive Summary

**Overall judgment**: Phase 6.2 is implemented correctly for the requested scope. The active Bug Flow retest fail/partial route (`bug-rework`) is wired through shared state-machine code, replay, CLI dispatch, and tests; the Gap-4 development rollback refactor to `compute_dev_bug_rollback` is behavior-preserving and reused by both `bug-start` and `bug-rework`.

**Findings**: 0 High / 0 Medium / 3 Low.

**Phase 6.3 readiness**: No blocking implementation issues found. The low-severity items are documentation/comment/diagnostic polish and do not block proceeding to Phase 6.3 (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS`).

**Validation run during review**:

```bash
python3 -m unittest tests.test_apply_bug_rework tests.test_progress_bug_rework tests.test_progress_replay tests.test_progress_recover
# Ran 112 tests in 0.937s — OK

python3 -m unittest discover -s tests
# Ran 637 tests in 5.121s — OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 10 subcommands, including bug-rework
```

I also checked that no repo-root `progress.md` / `progress-history.md` exists after the test run.

## 2. Findings

### Low

#### L1 — Reference history template for `bug-rework` is stale relative to the implemented canonical replay tokens

**Location**: `skills/workflow-protocol/references/command-reference.md:425`; related older planning text at `docs/implementation/task6_plan_20260507.md:239` and `docs/handoff/task6_progress_py_prerequisites_20260506.md:88`

**Issue**: The implementation writes the replay-canonical summary in `apply_bug_rework` as `bug=<path> root_cause=<root_cause> Bug Flow rerouted [rollback=...]` (`skills/_shared/dev_workflow/progress_state.py:1588`), and the replay handler requires both `bug=` and `root_cause=` tokens (`skills/_shared/dev_workflow/progress_replay.py:423`). However, `command-reference.md` §9 still shows the append-history template as `active Bug Flow retest failed` with `bug=` only in the `result` line and no `root_cause=` token. The older plan/prereq docs also say to include a test-report path in history, while the implementation records the deterministic state transition and not `test_report=`.

**Impact**: Runtime behavior is correct and covered by tests, but future maintainers or agents using the reference as an exact history template could produce a `bug-rework` history entry that replay rejects for missing `root_cause=`. It also obscures the Phase 6.2 canonical-token contract that recover depends on.

**Recommendation**: When the docs write set opens, update `command-reference.md` §9 append-history block to match the implemented canonical form: summary contains `bug=<path> root_cause=<srs|architecture|development> Bug Flow rerouted [rollback=...]`, result contains `current_stage=<stage>` plus rollback/planning-route prose, and `test_report` is a forward CLI precondition rather than a replay token. Optionally annotate the older plan/prereq docs as superseded by the Phase 6.2 handoff canonical-token contract.

#### L2 — `bug-rework` replay comment overstates root-cause token validation

**Location**: `skills/_shared/dev_workflow/progress_replay.py:446`

**Issue**: `_apply_bug_rework_handler` parses `root_cause` and checks that the token exists, but it intentionally does not pass that value into `apply_bug_rework`. The transition uses `state['bug_flow']['root_cause']`. The comment says `apply_bug_rework` will reject if state disagrees with what came in via the token, but no such comparison happens.

**Impact**: No runtime bug under the stated Phase 6.2 contract: the prompt explicitly treats the `root_cause=` token as a required canonical/readability token while the state remains the source of truth. The risk is maintainability: a future reviewer could assume summary root-cause tampering is detected when it is only presence-checked.

**Recommendation**: Either update the comment to say the `root_cause` token is currently required for canonical form/readability only, or add an explicit replay check that `root_cause == state['bug_flow']['root_cause']` if the project wants stricter history-token integrity.

#### L3 — `load_bug_report(..., expect_root_cause=...)` emits a bug-start-specific diagnostic when used by `bug-rework`

**Location**: `skills/_shared/dev_workflow/progress_artifacts.py:405`

**Issue**: `cmd_bug_rework` correctly calls `load_bug_report(root, rel_bug, expect_root_cause=active_root_cause)` (`skills/workflow-protocol/scripts/progress.py:1048`) to reject BUG frontmatter drift. If the check fails, the helper error says the BUG root cause must match the `bug-start --root-cause` argument, but `bug-rework` has no `--root-cause` argument; it compares against `bug_flow.root_cause` from `progress.md`.

**Impact**: Validation behavior is correct, but the operator-facing error message is misleading for the new Phase 6.2 caller.

**Recommendation**: Generalize the helper message to say `expected root_cause` / `caller-supplied expected root_cause`, or let callers pass a context label such as `expect_root_cause_source='bug_flow.root_cause'`. This is cosmetic and can be bundled with future doc/diagnostic polish.

## 3. Cross-Doc Consistency Check

- **`command-reference.md` §9 preconditions/mutation**: Matches implementation. `cmd_bug_rework` enforces active bug flow, BUG path equality, root-cause membership, latest test report fail/partial, and BUG frontmatter root-cause equality before entering `_run_update_pipeline`; `apply_bug_rework` enforces state-machine gates and mutation.
- **`command-reference.md` §9 development rollback**: Matches implementation. Development root cause reuses the same Gap-4 rollback helper and applies protected transitions only through `apply_bug_rework`.
- **`command-reference.md` §9 append-history template**: ⚠️ Drift noted in L1. The implementation follows the Phase 6.2 handoff canonical-token contract, but the reference template does not show the required `root_cause=` summary token or optional `rollback=` token.
- **`command-reference.md` protected-transition table**: Matches Phase 6.2; Stage 4 Gap-4 rows now name owner `bug-start` or `bug-rework` (`skills/workflow-protocol/references/command-reference.md:646`).
- **`task6_plan_20260507.md` §6.3**: Mutation steps align. Step 6's wording says history includes test-report path; implementation instead records canonical replay tokens and state/result text, so this is an older-plan wording drift rather than a code gap.
- **`task6_progress_py_prerequisites_20260506.md` §6**: Preconditions and mutation align; same minor history wording drift as above.
- **`skills/workflow-protocol/SKILL.md` command matrix**: The `bug-rework` row and active retest fail/partial flow match the script behavior. The SKILL file is forward-looking and lists `incident-start` / `incident-resolve` plus “12 subcommands”; the actual Phase 6.2 CLI has 10 subcommands. Per review scope, missing incident commands are Phase 6.3 and not a finding.

## 4. Checklist Results

### A. `compute_dev_bug_rollback` shared helper

- ✓ Moved to `skills/_shared/dev_workflow/progress_state.py:1148` as a public helper with a clear Phase 6.1/6.2 Gap-4 docstring.
- ✓ Signature is simplified to `(state, triage)`; `bug_info` was not needed by the previous algorithm. `rg _compute_bug_start_rollback` finds no remaining references.
- ✓ Duck-typed triage access via `getattr` is safe for the real `TriageAnalysis` object and covered by `_FakeTriage` tests.
- ✓ Classification behavior matches Phase 6.1: `test` only rolls `verified -> test-revising`; `source` rolls `verified` and `code-review-passed` to `code-revising`; `ambiguous` / `unable_to_localize` return empty; unregistered/ineligible tasks are skipped.
- ✓ Six helper tests cover the expected cases, and the full baseline still passes after `cmd_bug_start` switched to the shared helper.

### B. `apply_bug_rework` state machine

- ✓ Enforces active project, review-iteration guard, canonical bug path shape, `current_stage == testing`, `sub_state == review-passed`, active bug flow, BUG path equality, and root-cause membership (`skills/_shared/dev_workflow/progress_state.py:1501`).
- ✓ Leaves `bug_flow.active`, `bug_flow.bug_report_path`, and `bug_flow.root_cause` unchanged while routing `current_stage` through the root-cause map, resetting `sub_state` to `write`, `review_iteration` to `0`, and `updated` to `now`.
- ✓ Development rollback semantics match `apply_bug_start`: non-development rollback is rejected; malformed decisions are rejected; stale old status trips the out-of-band guard; only `PROTECTED_TASK_TRANSITIONS` are accepted.
- ✓ History summary has canonical `bug=`, `root_cause=`, `Bug Flow rerouted`, and optional `rollback=` tokens.
- ✓ Development empty-rollback path persists the planning-route note in `history_result` / `history_next`, symmetrical with the Phase 6.1 round 2 bug-start behavior.
- ✓ 36 unit tests cover happy paths, rollback application/rejection, precondition rejection, planning-route notes, frozen outcome, constants, and helper behavior.

### C. `progress_replay._apply_bug_rework_handler`

- ✓ Registered in `_HANDLERS`, bringing `supported_events()` to 12.
- ✓ Requires `bug=` and `root_cause=` tokens and parses optional `rollback=` using the same helper as `bug-start`.
- ✓ Calls `apply_bug_rework(state, bug_path, now=entry.timestamp, rollback_decisions=...)` and does not read BUG files or test reports during replay.
- ✓ Unsupported-event messaging is updated to Phase 6.2 and names `bug-rework` as supported.
- ⚠️ Comment at `progress_replay.py:446` overstates root-cause-token validation; see L2.

### D. `cmd_bug_rework` CLI

- ✓ Argparse exposes `bug-rework --bug --agent`; missing `--bug` exits 2.
- ✓ Path resolution/containment runs first; outside-root paths are rejected before file reads.
- ✓ Progress preflight validates active bug flow, path equality, root-cause membership, release availability, latest test-report `fail|partial`, BUG frontmatter root-cause equality, and development triage parsing before `_run_update_pipeline`.
- ✓ `bug-rework` has no `--root-cause`; root cause is sourced from `progress.md bug_flow.root_cause` and cross-checked against the BUG file.
- ✓ Development root cause uses shared `compute_dev_bug_rollback`; empty rollback emits stderr warning and persists planning-route history through `apply_bug_rework`.
- ✓ Dispatcher branch and help entry are present; `bug-close` stderr now says `use bug-rework for fail/partial` without the stale Phase 6.2 note.

### E. Tests design

- ✓ New tests use `tempfile.TemporaryDirectory` and do not touch repo-root workflow files.
- ✓ CLI integration mirrors the Phase 6.1 fixture style with `_install_test_stage_advance_handler`, `_FakeClock`, and `_bring_active_bug_flow_to_retest_failed`.
- ✓ CLI coverage includes three root causes, fail/partial verification statuses, development classifications, expected rejects, recover round-trips, M1 inheritance, lock blocking, and argparse behavior.
- ✓ Replay coverage includes happy path, rollback token, missing token, malformed rollback, and no BUG/test-report reads.
- ✓ Unsupported-event samples moved to `incident-start` in replay/recover tests.

### F. Existing invariants

- ✓ Full suite passes: 637 tests OK; compileall is clean.
- ✓ `bug-rework` uses `_run_update_pipeline`, so history parse, composed-history replay, state diff, lock/atomic write, and M1 consistency remain inherited.
- ✓ `apply_bug_rework` calls `_validate_review_iteration_value`, preserving the M2 guard.
- ✓ `progress_lock.py`, `progress_history.py`, `progress_artifacts.py`, `validate.py`, `changelog.py`, and `status_transition.py` were not expanded for Phase 6.2 behavior.
- ✓ Existing command paths remain covered by the full suite; `cmd_bug_start` reuses the shared helper without regressing the Phase 6.1 dev rollback/planning-route tests.
- ✓ `_run_update_pipeline` and `extra_writes_factory` behavior are unchanged.

### G. Design / maintainability

- ✓ `bug-rework` mirrors `bug-start` where helpful but keeps distinct intent: existing active bug flow, no root-cause argument, unchanged bug-flow fields, and retest fail/partial preflight.
- ✓ Sharing `compute_dev_bug_rollback` is the right abstraction boundary; the apply functions still own state mutation and protected-transition validation.
- ✓ The replay token shape mirrors `bug-start` and avoids new parser helpers.
- ✓ Current duplication between `apply_bug_start` and `apply_bug_rework` is acceptable at this stage; premature abstraction would blur materially different preconditions.
- ✓ Public helper naming is appropriate now that the CLI and state/replay tests share it.
- ⚠️ Minor diagnostic/comment polish remains (L2/L3).

### H. Cross-doc consistency

- ✓ State mutation table and protected transition table align with implementation.
- ✓ Rejected alternatives are enforced indirectly: active flow/path mismatch blocks second BUG rework; `bug-close` requires pass; `bug-rework` rejects pass and requires fail/partial; `_run_update_pipeline` plus M1 discourages hand-edited progress.
- ✓ Gap-5 plan/precondition/mutation work is implemented.
- ⚠️ Append-history exact wording/token placement is stale in the reference/planning docs; see L1.
- ✓ Phase 6.3/6.4 work is correctly not implemented and not treated as a blocker.

## 5. Open Questions / Assumptions

- **Assumption**: The Phase 6.2 handoff canonical-token contract (`bug=<path> root_cause=<r> Bug Flow rerouted [rollback=...]`) supersedes the older `command-reference.md` §9 append-history prose for exact summary formatting. The implementation follows that newer contract.
- **Open question**: Should replay harden `bug-rework` by comparing the parsed `root_cause=` token to `state['bug_flow']['root_cause']`? The current prompt only requires token presence/readability, but a comparison would catch a narrow class of manual history-summary tampering.
- **Open question**: Should `load_bug_report` accept a caller-context label for `expect_root_cause` errors now that both `bug-start` and `bug-rework` use it?
- **Assumption**: SKILL.md's incident command rows are forward-looking Phase 6.3 documentation and are intentionally ahead of the Phase 6.2 CLI implementation.

## 6. Recommendation

**(A) accept and proceed to Phase 6.3 (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS`)**

The implementation satisfies the Phase 6.2 state-machine, replay, CLI, and test requirements. The three low-severity findings can be handled as non-blocking documentation/comment/diagnostic polish; they do not require code rework before Phase 6.3.
