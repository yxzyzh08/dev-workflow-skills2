# Task 6 Phase 5.3 Round 2 Review — update --task Regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Regression review for Round 2 fixes to `progress_artifacts.py`, `progress_state.py`, `progress_replay.py`, `progress.py` comments, and the new regression tests for Phase 5.3 `update --task`.  
**Recommendation**: **(A) accept regression and proceed to Phase 5.4 (`release-*` + `bug-intake`)** — all Round 1 findings are fixed, the new regression coverage is materially stronger, and no new blocking issue was found.

---

## 1. Executive Summary

Round 2 closes the two functional Phase 5.3 blockers and the two Low review items without expanding into Phase 5.4 / Phase 6 scope. `apply_update_task()` now inherits the Phase 5.2 over-limit `review_iteration` guard, `load_breakdown_with_tasks()` now rejects malformed `total_tasks`, replay/update comments now match the `validate_artifacts=False` design, and revision-loop transitions have focused unit and CLI coverage.

Findings distribution for this review:

| Severity | Count | Blocks Phase 5.4? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss, atomicity, or replay-regression issue found. |
| Medium | 0 | No | Round 1 M1/M2 are fixed. |
| Low | 0 | No | Round 1 L1/L2 are fixed; no new Low finding raised. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 383 tests in 3.232s
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

No repo-root `progress.md` / `progress-history.md` files were created.

---

## 2. Round 1 Findings 回归状态

| Round 1 Finding | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| M1 — `apply_update_task` 未继承 `review_iteration > 7` entry guard | ✅ Fixed | `skills/_shared/dev_workflow/progress_state.py:695` calls `_validate_review_iteration_value(state.get("review_iteration", 0))` after current-stage validation and before release validation. Regression tests are at `tests/test_apply_update_task.py:695` and `tests/test_progress_update_task.py:654`. | Behavior now matches `apply_update_event`: iteration 7 is allowed and preserved; iteration 8 rejects with the shared escalation message. |
| M2 — `load_breakdown_with_tasks` accepted invalid/missing `total_tasks` | ✅ Fixed | `skills/_shared/dev_workflow/progress_artifacts.py:77` narrows `BreakdownInfo.total_tasks` to `int`; `skills/_shared/dev_workflow/progress_artifacts.py:196` rejects missing values; `skills/_shared/dev_workflow/progress_artifacts.py:202` rejects non-int, bool, and negative values. Tests are at `tests/test_progress_artifacts.py:232`. | Count-vs-declared consistency remains deferred to Phase 6, as intended. |
| L1 — replay/update comments contradicted `validate_artifacts=False` | ✅ Fixed | `_apply_update_task()` docstring at `skills/_shared/dev_workflow/progress_replay.py:157` now says replay validates state-machine legality only; `_run_update_pipeline` comments at `skills/workflow-protocol/scripts/progress.py:477` now say forward path is the artifact gatekeeper. | `rg` found no stale positive claim that replay re-evaluates artifact preconditions. |
| L2 — tests did not cover revision-loop transitions | ✅ Fixed | Unit coverage at `tests/test_apply_update_task.py:762`; CLI coverage at `tests/test_progress_update_task.py:696`. | Covers test and code review revising loops, including code-review re-entry rejection when the report is already pass. |

---

## 3. New Findings (Round 2)

No new findings.

I did not identify any new High, Medium, or Low defects introduced by the Round 2 changes. Minor observations are listed under implementation quality, but none block Phase 5.4.

---

## 4. Cross-Finding Consistency Check

| Area | Status | Notes |
|------|--------|-------|
| M1 + Phase 5.2 M2 invariant | ✅ | Both `apply_update_event()` and `apply_update_task()` now reject existing `review_iteration > 7` through the same helper. |
| M2 + frontmatter schema | ✅ | `task-breakdown.total_tasks` is now required and must be a non-bool non-negative int, matching `frontmatter-schema.md` and `validate.py` format logic. |
| L1 + replay artifact design | ✅ | Runtime already used `validate_artifacts=False`; docs/comments now match that design. |
| L2 + command-reference Stage 4 table | ✅ | Revision-loop normal transitions now have direct test coverage without implementing deferred protected rollback paths. |
| Phase boundary | ✅ | No `release-*`, `bug-*`, `incident-*`, `update --advance`, or Gap-3/4/5 implementation is required or expected in this round. |

---

## 5. Round 2 Implementation Quality Spot-checks

### 5.1 `apply_update_task` review-iteration guard

- The guard is placed after the general task/status/timestamp/project/current-stage checks and before release validation, matching the Round 2 prompt.
- It reuses `_validate_review_iteration_value()` directly; no duplicate cap logic was introduced.
- The returned state still preserves `review_iteration` for valid values, so `update --task` does not accidentally mutate review-loop state.
- Unit tests cover `planning-done`, `test-writing`, `verified`, and `iter=7` allowed behavior.
- CLI coverage verifies exit 1 and byte-for-byte unchanged `progress.md` / `progress-history.md` when `review_iteration=8` is forged.

### 5.2 `load_breakdown_with_tasks` total-tasks validation

- `BreakdownInfo.total_tasks` is now typed as `int`, which simplifies Phase 6 count-consistency work.
- Missing `total_tasks` raises `ProgressArtifactError` with the relative breakdown path and field name.
- String, bool, and negative values raise `ProgressArtifactError`; invalid-value messages include relative path, field name, actual type, and actual value.
- `total_tasks=0` is accepted, and declared-task extraction still uses the same word-boundary `Tn` token scan.
- The implementation does not prematurely enforce `total_tasks == len(declared_tasks)`, preserving the Phase 6 boundary.

### 5.3 Replay / update comments

- `_apply_update_task()` now explicitly states replay validates state-machine legality only.
- The `root` requirement is described as defensive/forward-compatible rather than as current artifact-read behavior.
- `_run_update_pipeline()` no longer implies replay catches artifact drift; it accurately says the forward path gates artifact state at write time.

### 5.4 Regression tests

- Round 2 adds 16 tests and the full suite now runs 383 tests OK.
- The M1 CLI test asserts both files remain unchanged on rejection.
- The M2 tests cover string, missing, bool, negative, and zero values.
- The L2 tests assert the concrete `development_state.task_states[Tn]` value after revision-loop transitions.
- All new CLI/state tests continue using temp directories and scoped test-only handler patches.

---

## 6. Checklist Results

### A. M1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Guard location in `apply_update_task` | ✓ | `_validate_review_iteration_value` is called at `progress_state.py:701`, after current-stage validation and before release validation. |
| Shared error wording reused | ✓ | Uses the Phase 5.2 helper, so messages retain `review_iteration is N`, limit `7`, and `escalate`. |
| `iter=7` allowed, `iter=8` rejected | ✓ | Unit tests cover both; valid `iter=7` is preserved. |
| Multiple task paths covered | ✓ | Planning registration, transitional `test-writing`, and final `verified` paths are covered. |
| CLI integration covered | ✓ | `UpdateTaskIterationOverLimitTests` checks exit 1 and unchanged files. |
| Existing apply-update-task suite remains green | ✓ | Full 383-test suite passes. |

### B. M2 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Missing `total_tasks` rejected | ✓ | `ProgressArtifactError` at `progress_artifacts.py:196`. |
| Non-int / bool / negative rejected | ✓ | Type/value guard at `progress_artifacts.py:202`. |
| Error messages actionable | ✓ | Invalid-value errors include rel path, field, type, and value; missing-field error includes rel path and field. |
| `BreakdownInfo.total_tasks` narrowed to `int` | ✓ | Dataclass field at `progress_artifacts.py:88`. |
| Planning-done path still works | ✓ | Existing and new tests pass with valid breakdown fixtures. |
| Tests cover string/missing/bool/negative/zero | ✓ | Covered in `tests/test_progress_artifacts.py:232`-`tests/test_progress_artifacts.py:296`. |
| Count-vs-declared remains deferred | ✓ | Comments and behavior keep this for Phase 6. |

### C. L1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Replay docstring says state-machine legality only | ✓ | `progress_replay.py:157` states this directly. |
| Root described as defensive | ✓ | `progress_replay.py:167` describes forward-compatible root requirement. |
| Update-pipeline comment no longer promises artifact replay | ✓ | `progress.py:484`-`progress.py:490` says replay does not re-evaluate artifacts. |
| Stale wording removed | ✓ | Spot grep found no old positive wording. |

### D. L2 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| `test-review -> test-revising` unit coverage | ✓ | Covered at `tests/test_apply_update_task.py:767`. |
| `test-revising -> test-review` skeleton coverage | ✓ | Covered at `tests/test_apply_update_task.py:781`. |
| `code-review -> code-revising` unit coverage | ✓ | Covered at `tests/test_apply_update_task.py:797`. |
| `code-revising -> code-review` skeleton coverage | ✓ | Covered at `tests/test_apply_update_task.py:810`. |
| `code-revising -> code-review` pass-report reject | ✓ | Covered at `tests/test_apply_update_task.py:824`. |
| CLI revision-loop smoke | ✓ | Test and code loops covered at `tests/test_progress_update_task.py:700` and `tests/test_progress_update_task.py:719`. |

### E. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| Phase 5.1 + 5.2 + 5.3 Round 1 tests remain green | ✓ | Full suite: 383 tests OK. |
| `compileall` remains clean | ✓ | Shared modules, scripts, and tests compile. |
| `progress_lock.py` / `progress_history.py` behavior unchanged | ✓ | No regression detected; tests still pass. |
| `init` / `query` / `recover` behavior preserved | ✓ | Existing tests pass; no repo-root progress files created. |
| `apply_update_event` not altered by M1 fix | ✓ | Round 2 guard change is localized to `apply_update_task`. |
| Argparse / dispatcher / shared pipeline intact | ✓ | `update --help` remains correct; shared pipeline still owns lock/history/replay/transaction. |

### F. 测试质量

| Check | Result | Notes |
|-------|--------|-------|
| M1 unit tests assert exception type | ✓ | `assertRaises(ProgressStateError)` is used. |
| M1 message token assertions | ✓ | The planning-done unit test and CLI test assert `review_iteration`, `8`, and `escalate`; other unit paths prove guard placement by using otherwise-legal transitions. |
| M1 CLI unchanged files | ✓ | Both `progress.md` and `progress-history.md` are byte-for-byte checked. |
| M2 edge values covered | ✓ | Missing, string, bool, negative, and zero are covered. |
| L2 state assertions | ✓ | Tests assert concrete task-state values after each loop. |
| Temp-dir isolation | ✓ | New tests use the existing `TemporaryDirectory`-based fixtures. |

### G. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| `command-reference.md` §2.1 Stage 4 table | ✓ | Normal/protected transition implementation remains aligned. |
| `frontmatter-schema.md` §3.2 `total_tasks` required int | ✓ | Loader now enforces required non-bool non-negative int. |
| Phase 5.2 M2 invariant covers event and task paths | ✓ | Shared helper is now called from both update modes. |
| Replay docstring reflects 5.3 design | ✓ | State-machine-only replay semantics are documented. |

### H. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| Shared helper reuse | ✓ | `_validate_review_iteration_value` remains the single implementation of the cap. |
| Future Phase 5.4/6 extensibility | ✓ | The pattern is easy for later mutating commands to reuse. |
| `BreakdownInfo.total_tasks: int` helps Phase 6 | ✓ | Phase 6 can compare `info.total_tasks` directly with declared count. |
| Stale artifact-replay wording removed | ✓ | No old wording found in the relevant scripts. |
| No premature Phase 6 behavior | ✓ | Breakdown count consistency and protected rollback commands remain deferred. |

---

## 7. Open Questions / Assumptions

- I assume missing `total_tasks` does not need a synthetic "actual type/value" token in the error; the message clearly identifies the rel path and missing field. Invalid present values do include type and value.
- I assume future Phase 5.4 / Phase 6 mutating commands should reuse `_validate_review_iteration_value` where they preserve or depend on existing `review_iteration`, but that implementation work is outside this Round 2 review.
- I assume no CLI reject smoke is required for the revision-loop pass-report case because the unit test covers the state/artifact precondition and existing CLI artifact-reject tests already prove unchanged-file behavior on `ProgressArtifactError`.

---

## 8. Recommendation

**(A) accept regression and proceed to Phase 5.4 (`release-*` + `bug-intake`)**.

Required before Phase 5.4: none from this review.

Optional non-blocking polish:

- Add message-token assertions to the two additional M1 unit tests (`test-writing` and `verified`) for perfect symmetry with the planning-done and CLI tests.
- Add a CLI reject smoke for `code-revising -> code-review` with a pass report if future maintainers want end-to-end coverage of that exact L2 negative path.
