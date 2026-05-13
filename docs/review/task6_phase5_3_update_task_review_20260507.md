# Task 6 Phase 5.3 Review — progress.py update --task

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Code review for Phase 5.3 `progress.py update --task`, including `progress_artifacts.py`, `apply_update_task`, replay integration, CLI update pipeline, and new/extended tests.  
**Recommendation**: **(B) fix before Phase 5.4** — core task-state behavior and atomic pipeline are mostly sound, but two prompt-level invariants are not fully enforced: Phase 5.2 M2 `review_iteration > 7` is not inherited by `apply_update_task`, and malformed `task-breakdown.total_tasks` is accepted despite the Phase 5.3 artifact-test checklist and schema requiring an int.

---

## 1. Executive Summary

Phase 5.3 implements the main `update --task` path cleanly: the 14 Stage 4 normal/protected transition constants are aligned with `command-reference.md`, artifact preconditions are routed per target status, CLI updates share the Phase 5.2 lock/history/replay/transaction pipeline, and replay correctly uses `validate_artifacts=False` for mutable Stage 4 reports.

However, I found two Medium issues that should be fixed before Phase 5.4 builds more progress commands on this shared mutation path.

| Severity | Count | Blocks Phase 5.4? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss or atomic-write failure found. |
| Medium | 2 | Yes | `update --task` misses the Phase 5.2 M2 over-limit review-iteration entry guard; `task-breakdown.total_tasks` non-int/missing is accepted. |
| Low | 2 | No | Replay/update comments contradict the `validate_artifacts=False` design; tests do not explicitly enumerate all normal revision-loop transitions. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 367 tests in 3.013s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py update --help
# OK; usage shows (--event EVENT | --task TASK) plus --status and --agent

find . -maxdepth 3 \( -name 'progress.md' -o -name 'progress-history.md' \) -print
# no output
```

Additional spot checks:

- `apply_update_task()` currently accepts a development state with `review_iteration: 8` for `planning-done -> test-writing`, confirming M1 below.
- `load_breakdown_with_tasks()` currently accepts `total_tasks: "three"` and returns `total_tasks=None`, confirming M2 below.
- No repo-root `progress.md` / `progress-history.md` was created during review.

---

## 2. Findings

### High

No High findings.

### Medium

#### M1 — `apply_update_task` does not inherit the Phase 5.2 M2 `review_iteration > 7` entry guard

- **Location**: `skills/_shared/dev_workflow/progress_state.py:637`; comparison point `skills/_shared/dev_workflow/progress_state.py:349`; existing event-path use at `skills/_shared/dev_workflow/progress_state.py:394`
- **Issue**: `apply_update_task()` validates `task_id`, `new_status`, timestamp, active project, current stage, release type, and task transition legality, but it never calls `_validate_review_iteration_value(state.get("review_iteration", 0))`. Phase 5.2 round 2 fixed this invariant for `apply_update_event()`, and the Phase 5.3 prompt explicitly requires M2 to be inherited even though task updates do not directly mutate `review_iteration`.
- **Impact**: The shared task mutation source can accept and preserve an already-invalid `review_iteration` value. In ordinary CLI tamper cases, the composed-history replay diff may catch some progress/history drift, but the state-machine function itself violates the invariant and future replay/Phase 5.4+ handlers can build on an over-limit state without the promised guard. Tests also do not cover `update --task` with `review_iteration=8`.
- **Recommendation**: Add `_validate_review_iteration_value(state.get("review_iteration", 0))` near the other entry validations in `apply_update_task()`. Add unit coverage in `tests/test_apply_update_task.py` for `review_iteration=8` rejection and a CLI/replay regression in `tests/test_progress_update_task.py` or `tests/test_progress_replay.py` to prove `update-task` inherits M2.

#### M2 — `load_breakdown_with_tasks` accepts malformed `task-breakdown.total_tasks`

- **Location**: `skills/_shared/dev_workflow/progress_artifacts.py:184`; current test expectation at `tests/test_progress_artifacts.py:232`; schema requirement at `skills/doc-guardian/references/frontmatter-schema.md:125`
- **Issue**: `load_breakdown_with_tasks()` reads `total_tasks` and silently converts any non-int or bool value to `None` instead of raising `ProgressArtifactError`. The current test is named `test_breakdown_total_tasks_optional` and asserts this behavior, but the Phase 5.3 review prompt asks for a `total_tasks 非 int` reject path, and the schema marks `total_tasks: <int>` as required for `task-breakdown`.
- **Impact**: `update --task Tn --status planning-done` can register a task against a malformed `breakdown.md` as long as the body contains `Tn` and `detailed_design.md` exists. This does not require the deferred Phase 6 count-vs-declared-task consistency check; it is only the frontmatter field type/presence check for a required schema field.
- **Recommendation**: In `load_breakdown_with_tasks()`, require `total_tasks` to be present and a non-bool int, raising `ProgressArtifactError` with `rel_path`, field name, expected type, and actual value otherwise. Keep the count-vs-`declared_tasks` consistency check deferred to Phase 6 as planned. Update `tests/test_progress_artifacts.py` to expect rejection for missing/non-int/bool `total_tasks` while retaining the word-boundary and wrong-type coverage.

### Low

#### L1 — Replay/update comments still claim artifacts are re-read during update-task replay

- **Location**: `skills/_shared/dev_workflow/progress_replay.py:157`; `skills/workflow-protocol/scripts/progress.py:477`
- **Issue**: The executable code correctly calls `apply_update_task(..., validate_artifacts=False)` during replay, and the inline comment at `progress_replay.py:180` explains why. But the `_apply_update_task()` docstring still says replay re-evaluates artifact preconditions and raises on out-of-band artifact changes; `_run_update_pipeline()` comments similarly say replay will reject if artifacts diverged.
- **Impact**: This contradicts the explicit Phase 5.3 design decision that replay validates state-machine legality, not current artifact compliance. It can mislead Phase 5.4/Phase 6 maintainers when adding more handlers or diagnosing recover behavior.
- **Recommendation**: Update these comments/docstrings to state that `root` is required defensively for `update-task`, but replay intentionally skips artifact preconditions because reports evolve from skeleton to pass/fail.

#### L2 — Tests do not explicitly enumerate every normal revision-loop transition

- **Location**: `tests/test_apply_update_task.py:293`; `tests/test_progress_update_task.py:496`
- **Issue**: Implementation constants include all normal transitions, but the tests do not directly exercise at least `test-review -> test-revising`, `code-review -> code-revising`, and `code-revising -> code-review`. The happy CLI cycle only takes the pass path.
- **Impact**: This is a coverage gap rather than an observed runtime defect. A future refactor could accidentally break revision-loop paths while the current suite remains green.
- **Recommendation**: Add focused unit tests for the missing normal transitions. These can be lightweight because the target revision states are transitional and do not require artifact preconditions; `code-revising -> code-review` should assert the pending code-review skeleton precondition.

---

## 3. Cross-Doc Consistency Check

| Reference | Status | Notes |
|-----------|--------|-------|
| `skills/workflow-protocol/references/command-reference.md` §2.1 Stage 4 table | PASS | `TASK_STATES`, `NORMAL_TASK_TRANSITIONS`, and `PROTECTED_TASK_TRANSITIONS` match the 11 states, 14 normal/idempotent rows, and 4 protected rollback rows. Protected transitions reject with Phase 6 wording. |
| `skills/doc-guardian/references/frontmatter-schema.md` §3.2 / §3.3 | WARN | Per-task artifact paths and `review_status` / `verification_status` checks align. `task-breakdown.total_tasks` required int is not enforced by `load_breakdown_with_tasks()` (M2). |
| `docs/handoff/task6_progress_py_prerequisites_20260506.md` | PASS | Idempotent planning registration, planning-done atomic artifact checks, and non-bypass protected rollback behavior are implemented in the intended Phase 5.3 scope. Gap-3/4/5 implementation remains correctly deferred. |
| `docs/implementation/task6_plan_20260507.md` §5.4 / §11.1 / §13 | WARN | Atomic update pipeline, Phase 5 split, and task-state core are aligned. The Phase 5.2 M2 inherited invariant is missing on the task path (M1). |
| `skills/workflow-protocol/SKILL.md` command matrix / Stage 4 matrix | PASS | Stage 4 per-task lifecycle is reflected in artifact preconditions; full doc-guardian and stage-advance checks remain appropriately deferred to later commands. |
| Phase 5.2 round 2 closure report | WARN | M1 history parse + composed replay + diff is inherited by `_run_update_pipeline`; M2 over-limit review-iteration entry check is not inherited by `apply_update_task()` (M1). |
| Replay design in this prompt | WARN | Runtime behavior matches `validate_artifacts=False`, but comments/docstrings still describe the opposite in two places (L1). |

---

## 4. Checklist Results

### A. `progress_artifacts.py`

| Check | Result | Notes |
|-------|--------|-------|
| `_PATH_TEMPLATES` matches `TYPE_PATHS` / directory layout | PASS | Paths match `task-breakdown`, `detailed-design`, `test-review-report`, `code-review-report`, and `verification-result`. |
| Missing file raises `ProgressArtifactError` | PASS | Missing artifacts include doc type and rel path in messages. |
| Frontmatter parse errors are wrapped | PASS | `FrontmatterError` is caught and re-raised as `ProgressArtifactError`. |
| Type / release / task_id mismatch checks | PASS | Expected/actual values are included in messages. |
| Unknown doc type and missing required task_id | PASS | `_format_path()` rejects both. |
| Task ID format `^T\d+$` | PASS | Local regex rejects invalid task IDs before path formatting. |
| `load_breakdown_with_tasks` body extraction uses word-boundary tokens | PASS | Uses `\bT\d+\b`; recognizes `T10` and ignores `TenThousand`. |
| `total_tasks` invalid type reject path | FAIL | Current implementation returns `None` for non-int/bool values instead of rejecting (M2). |
| Thin-validation boundary documented | PASS | Module docstring clearly says full Class 1-7 validation remains doc-guardian responsibility. |

### B. `apply_update_task` state machine

| Check | Result | Notes |
|-------|--------|-------|
| `_TASK_ID_RE` matches schema `^T\d+$` | PASS | Regex matches frontmatter-schema §4.4. |
| 14 normal transitions + planning-done idempotency | PASS | Constants match command-reference rows; idempotent planning-done is allowed. |
| 4 protected transitions rejected | PASS | Protected cases raise `ProgressStateError` and mention Gap/Phase 6 path. |
| Per-status precondition routing | PASS | Covers `planning-done`, `test-review`, `test-done`, `code-review`, `code-review-passed`, and `verified`; transitional states no-op. |
| Planning-done checks breakdown then detailed design | PASS | It checks breakdown declaration before loading the per-task detailed design. |
| Review skeleton checks `review_status == pending` | PASS | Both test and code review skeleton paths use `_require_review_skeleton()`. |
| Review pass checks `review_status == pass` + `blocking_findings_count == 0` | PASS | Non-int/bool/nonzero blocking counts reject. |
| Verification pass checks `verification_status == pass` | PASS | `fail` and `partial` reject. |
| Field preservation | PASS | `development_state.task_states[Tn]` and `updated` change; sibling and top-level fields are preserved. |
| History summary/result/next | PASS | Summary is canonical, idempotent suffix is present, and result distinguishes unset/from-old/unchanged. |
| `validate_artifacts=True` default and replay flag | PASS | Function docstring correctly explains forward vs replay artifact validation. |
| Phase 5.2 M2 inherited entry guard | FAIL | `review_iteration > 7` is not validated (M1). |

### C. `progress_replay.py` extension

| Check | Result | Notes |
|-------|--------|-------|
| `replay_history(history, *, root=None)` backward compatible | PASS | Existing init/update-event paths still omit root successfully. |
| Handler signature includes root | PASS | `ApplyFn` and handlers accept root; init/update-event delete it explicitly. |
| `update-task` requires root | PASS | Missing root raises `ReplayError` before state-machine work. |
| Summary parser handles idempotent suffix | PASS | Prefix regex with trailing word boundary accepts `(idempotent retry)`. |
| Replay uses `validate_artifacts=False` | PASS | Runtime behavior matches prompt design. |
| Progress/artifact errors wrapped as `ReplayError` | PASS | Both exception classes are caught. |
| `_HANDLERS` / `supported_events()` include six events | PASS | Tests assert `init` + four update events + `update-task`. |
| Replay docs/comments match design | WARN | Function docstring still says replay re-evaluates artifacts (L1). |

### D. `progress.py` CLI refactor

| Check | Result | Notes |
|-------|--------|-------|
| Dispatcher split into `_do_update_event` / `_do_update_task` / `_run_update_pipeline` | PASS | Shared pipeline avoids duplicate lock/history/transaction logic. |
| Mutex group contains `--event` and `--task` | PASS | `update --help` shows required one-of group. |
| `--task` requires `--status` with exit 2 | PASS | `_do_update_task()` returns 2 before entering the update pipeline. |
| Invalid status / task ID exits 1 | PASS | Validation flows through `apply_update_task()` and returns 1. |
| Shared update pipeline inherits M1 parse/replay/diff | PASS | Existing history parse, composed-history replay, and full-state diff run before transaction. |
| Atomic dual-write | PASS | `progress.md` and `progress-history.md` are written inside one `atomic.transaction()`. |
| `ProgressArtifactError` handled as exit 1 | PASS | Caught alongside `ProgressStateError` in the command path. |
| `cmd_recover` passes root to replay | PASS | Recover calls `replay_history(history_entries, root=root)`. |
| Pipeline comments match replay artifact behavior | WARN | Comments imply artifact divergence is caught by replay, which is no longer true by design (L1). |

### E. `tests/test_progress_artifacts.py`

| Check | Result | Notes |
|-------|--------|-------|
| Happy paths for detailed design and test review report | PASS | Covered. |
| Missing/corrupt/wrong type/wrong release/wrong task_id/unknown/invalid/missing task_id rejects | PASS | Covered. |
| Breakdown normal extraction | PASS | Covered. |
| Breakdown wrong type and word boundary | PASS | Covered. |
| Breakdown `total_tasks` non-int reject | FAIL | Test asserts optional/`None`; prompt expects reject (M2). |

### F. `tests/test_apply_update_task.py`

| Check | Result | Notes |
|-------|--------|-------|
| Planning-done first-time/idempotent/artifact reject paths | PASS | Covered. |
| Per-status review and verification preconditions | PASS | Pending/pass/blocking/fail/partial cases covered. |
| Protected transitions rejected | PASS | Four protected transitions are covered. |
| Generic preconditions | PASS | Invalid task_id/status/stage/project/now/illegal first transition/sibling preservation covered. |
| Field preservation and frozen outcome | PASS | Covered. |
| `TASK_STATES` exact set | PASS | Covered. |
| Phase 5.2 M2 inherited guard | FAIL | No unit test for `review_iteration > 7` on `apply_update_task()` (M1). |
| All normal revision-loop transitions explicitly tested | WARN | Missing direct tests for several revision branches (L2). |

### G. `tests/test_progress_update_task.py`

| Check | Result | Notes |
|-------|--------|-------|
| Argparse help/mutex/required status/invalid task ID | PASS | Covered. |
| Non-development rejection | PASS | Covered and asserts progress unchanged. |
| M1 malformed history and replay diff inheritance | PASS | Covered. |
| Happy planning and full pass-only Stage 4 cycle | PASS | Covered. |
| Idempotent planning and two-task parallel progression | PASS | Covered. |
| History canonical summary | PASS | Covered. |
| Recover roundtrip | PASS | Covered. |
| Artifact rejection and lock-held rejection | PASS | Covered. |
| Temp-dir isolation and test-only stage handler patching | PASS | Uses `TemporaryDirectory()` and scoped handler patching. |
| CLI M2 over-limit review iteration | WARN | No `update --task` CLI test for `review_iteration=8` rejection (M1). |
| Revision-loop CLI path | WARN | Full cycle uses pass branches only; no CLI revision loop smoke (L2). |

### H. `tests/test_progress_replay.py` extension

| Check | Result | Notes |
|-------|--------|-------|
| `supported_events` contains `update-task` and exact six-event set | PASS | Covered. |
| Missing root raises | PASS | Covered. |
| Unparseable summary rejects | PASS | Covered. |
| Artifact validation skipped | PASS | Covered with empty tempdir. |
| State-machine legality still enforced | PASS | `None -> test-writing` rejects. |
| Idempotent suffix parses | PASS | Covered. |
| M2 over-limit state during update-task replay | WARN | Not covered; would currently pass if a prior handler supplied `review_iteration=8` (M1). |

### I. Existing invariant consistency

| Check | Result | Notes |
|-------|--------|-------|
| Full suite passes | PASS | 367 tests OK. |
| `compileall` passes | PASS | Shared modules, scripts, and tests compile. |
| `progress_lock.py` / `progress_history.py` not part of Phase 5.3 write set | PASS | No behavior regression observed in tests. |
| Init/query/recover behavior preserved | PASS | Existing tests pass; recover now handles `update-task` histories with root. |
| `update --event` path preserved after refactor | PASS | Phase 5.2 tests still pass. |
| EventOutcome/TaskOutcome duck type for pipeline | PASS | Both expose `new_state`, `history_summary`, `history_result`, and `history_next`. |
| Phase 5.2 M2 inherited by update-task | FAIL | Missing in `apply_update_task()` (M1). |

### J. Design / Maintainability

| Check | Result | Notes |
|-------|--------|-------|
| Single source of truth for task transitions | PASS | CLI and replay both delegate to `apply_update_task()`. |
| `validate_artifacts` flag design is sound | PASS | Correctly avoids false replay failures after reports evolve from pending to pass/fail. |
| Artifact paths centralized | PASS | `_PATH_TEMPLATES` makes Phase 6 additions straightforward. |
| Error messages actionable | PASS | Most artifact/state errors include path/field/expected/actual context. |
| `_run_update_pipeline` extensible | PASS | Closure-based outcome computation should support later modes. |
| Documentation comments match implementation | WARN | Stale replay-artifact comments should be corrected (L1). |

---

## 5. Open Questions / Assumptions

- I agree with the `validate_artifacts=False` replay design. Stage 4 review report files legitimately evolve from `pending` skeletons to `pass`/`fail`, so replaying old transitions against current artifact frontmatter would create false negatives. The important boundary is that comments and docs should consistently say replay validates state-machine legality, not artifact compliance.
- I assume Phase 5.3 does not need to validate `total_tasks == len(declared_tasks)`; that count consistency remains Phase 6 `update --advance` / `validate.py consistency`. M2 is narrower: required field presence/type only.
- I assume the Phase 5.2 M2 invariant is intended to apply to every mutating progress command path, including future `release-*` and `bug-*` paths where appropriate. Fixing it in `apply_update_task()` now avoids a precedent of command-specific bypasses.
- I did not treat deferred `update --advance`, `release-*`, `bug-*`, `incident-*`, or Gap-3/4/5 rollback implementation as findings.

---

## 6. Recommendation

**(B) fix before Phase 5.4**.

Must fix before entering Phase 5.4:

1. **M1**: Add the `review_iteration > 7` entry guard to `apply_update_task()` and add targeted unit/CLI or replay tests.
2. **M2**: Reject missing/non-int/bool `task-breakdown.total_tasks` in `load_breakdown_with_tasks()` and update the artifact tests to match the prompt/schema.

Can be deferred to Phase 6 / Phase 7 polish if needed:

- **L1**: Correct stale comments/docstrings about replay artifact validation.
- **L2**: Add explicit tests for the normal revision-loop transitions not currently covered.

Estimated fix path:

- M1 is small: one helper call plus 2-3 tests.
- M2 is small-to-medium: enforce `total_tasks` presence/type in one loader and adjust/add artifact tests.
- L1/L2 are low-risk documentation/test-only cleanup.
