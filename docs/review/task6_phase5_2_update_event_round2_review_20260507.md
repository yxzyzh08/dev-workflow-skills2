# Task 6 Phase 5.2 Round 2 Review — update --event Regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Regression review for the Round 2 fixes to `progress_state.py`, `progress_replay.py`, `progress.py`, `tests/test_apply_update_event.py`, and `tests/test_progress_update_event.py`, using `docs/review/task6_phase5_2_update_event_review_20260507.md` as the Round 1 baseline.  
**Recommendation**: **(A) accept regression and proceed to Phase 5.3 (`update --task`)** — both Round 1 Medium findings are fixed, regression coverage is strong, and no new blocking issue was found.

---

## 1. Executive Summary

Round 2 closes the two Phase 5.2 blockers without expanding the implementation beyond `update --event`. `cmd_update()` now validates existing history and replays the composed history before writing, and `_validate_review_iteration_value()` now enforces the inclusive `0-7` cap at entry for every mutating event.

Findings distribution for this review:

| Severity | Count | Blocks Phase 5.3? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss, rollback, or replay-regression issue found. |
| Medium | 0 | No | Round 1 M1/M2 are fixed. |
| Low | 0 | No | No new non-blocking implementation defect found. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 293 tests in 2.343s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# compileall_exit=0

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py update --help
# OK
```

Additional spot checks:

- Malformed `progress-history.md` now returns exit 1 with `existing progress-history.md is malformed`, and both `progress.md` and `progress-history.md` remain byte-for-byte unchanged.
- `apply_update_event()` now rejects `review_iteration=8` with an error containing the value, limit, and `escalate`.
- No repo-root `progress.md` / `progress-history.md` files were created.

---

## 2. Round 1 Findings 回归状态

| Round 1 Finding | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| M1 — `cmd_update` appended to malformed history and skipped feasible replay consistency | ✅ Fixed | Existing history parse guard is at `skills/workflow-protocol/scripts/progress.py:385`-`skills/workflow-protocol/scripts/progress.py:395`; composed history parse + replay is at `skills/workflow-protocol/scripts/progress.py:420`-`skills/workflow-protocol/scripts/progress.py:439`; full-state diff check is at `skills/workflow-protocol/scripts/progress.py:441`-`skills/workflow-protocol/scripts/progress.py:454`, before `transaction()` starts at `skills/workflow-protocol/scripts/progress.py:457`. | Reject paths return 1 before writes. Error text includes malformed/composed/replay-consistency context and, on mismatch, suggests `progress.py recover --confirm`. |
| M2 — `_validate_review_iteration_value` allowed existing `review_iteration > 7` | ✅ Fixed | Over-limit entry guard is at `skills/_shared/dev_workflow/progress_state.py:344`-`skills/_shared/dev_workflow/progress_state.py:361`; existing `review-issues` post-increment guard remains at `skills/_shared/dev_workflow/progress_state.py:409`-`skills/_shared/dev_workflow/progress_state.py:414`. | `iteration=7` remains allowed at entry; `7 -> 8`, `8`, and `42` reject with escalation wording. |

---

## 3. New Findings (Round 2)

No new findings.

I did not identify any new High, Medium, or Low defects introduced by the Round 2 changes. The new checks are inside the existing lock, execute before transaction writes, preserve the single-source `apply_update_event()` design, and keep Phase 5.3/5.4/Phase 6 work out of scope.

---

## 4. Cross-Finding Consistency Check

| Reference / Plan | Status | Notes |
|------------------|--------|-------|
| Round 1 review M1/M2 | ✅ | Both Medium findings have direct code fixes and targeted regression tests. |
| `command-reference.md` §2 update common flow | ✅ | Update now locks, validates state, appends canonical history, overwrites progress, and performs feasible replay consistency before writing. |
| `command-reference.md` §2.1 review loop | ✅ | `review_iteration > 7` now rejects for all mutating event paths, while `6 -> 7` remains allowed and `7 -> 8` remains rejected. |
| `docs/implementation/task6_plan_20260507.md` §11.1 | ✅ | The lock/parse/apply/verify/write order matches the atomicity and consistency intent; failures before transaction do not mutate files. |
| `docs/implementation/task6_plan_20260507.md` §13 | ✅ | Phase boundaries remain clean; `update --task`, release, bug, incident, and advance commands are still deferred. |
| `skills/workflow-protocol/SKILL.md` command matrix / update atomic flow | ✅ | `update --event` remains the only new implemented command mode, and its history/progress mutation is replay-checked. |
| `progress_replay.py` docs/error messages | ✅ | Module docstring and unsupported-event error now accurately describe Phase 5.2: `init` plus the four update-event handlers. |

---

## 5. Round 2 Implementation Quality Spot-checks

### 5.1 `cmd_update` history parse + replay

- Existing `progress-history.md` is parsed immediately after read and before `apply_update_event()`, so malformed history cannot grow new entries.
- `new_history_text` is parsed and replayed before entering `atomic.transaction()`, so the write path only runs after the composed history is replayable.
- Full-state equality compares `replayed_state` to `outcome.new_state`; mismatches report deterministic `sorted(...)` `diff_keys`.
- All new rejection points are inside `progress_lock` and before `transaction()`, preserving serialization while avoiding partial writes.
- Error messages distinguish existing malformed history, composed malformed history, replay failure, and replay consistency mismatch; mismatch guidance points callers to `progress.py recover --confirm`.
- The consistency check is O(N) per update over history length. This is acceptable for Phase 5.2; if history grows to thousands of entries, future phases can consider incremental validation without changing the correctness contract.

### 5.2 Review iteration cap hardening

- `_validate_review_iteration_value()` still rejects non-int, bool, and negative values.
- It now rejects values above `REVIEW_ITERATION_LIMIT` with a message containing the current value, limit, and `escalate`.
- The guard sits at the shared input-validation point, so `write-complete`, `review-issues`, `review-passed`, and `human-confirmed` all inherit it.
- The existing `review-issues` post-increment guard remains, preserving the inclusive cap semantics: entry `7` is valid, but `review-issues` from `7` rejects because it would produce `8`.

### 5.3 `progress_replay.py` polish

- The module docstring now states Phase 5.2 handles `init` plus the four `update --event` handlers and lists future handler phases.
- The unsupported-event message now says Phase 5.2 implements `init` plus four update handlers, rather than the stale Phase 5.1 wording.
- Replay still uses document/append order and keeps the Round 5.1 timestamp monotonicity fix intact.

### 5.4 Regression tests

- M1 parse guard tests cover bad header and unknown field corruption; bad-header coverage asserts both files unchanged, and unknown-field coverage asserts history remains unchanged on the pre-apply path.
- M1 replay consistency tests cover tampered `release`, tampered `project_name`, and a clean five-event cycle that must not false-positive.
- M2 unit tests cover all four events with existing iteration `8`, entry `7` still allowed, and far-over-limit `42` rejected.
- M2 CLI tests cover `write-complete`, `review-passed`, and `human-confirmed` with iteration `8`, with progress unchanged on reject.
- The updated non-gated `human-confirmed` test clearly documents why it forges the final frontmatter state in one step: it isolates the forward gated-stage check from the new replay-consistency mismatch check.

---

## 6. Checklist Results

### A. M1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Existing history parsed inside lock before `apply_update_event` | ✓ | Implemented at `progress.py:385`-`progress.py:395`. |
| Composed history parse + replay + equality compare | ✓ | Implemented at `progress.py:420`-`progress.py:454`. |
| Reject paths return 1 and write to stderr | ✓ | Each parse/replay/mismatch branch prints to stderr and returns 1. |
| Reject paths are before transaction writes | ✓ | `transaction()` starts only after all checks pass. |
| `diff_keys` output is deterministic | ✓ | Uses `sorted(...)`. |
| Mismatch message suggests `recover --confirm` | ✓ | Message includes `run 'progress.py recover --confirm'`. |
| Lock still covers read/parse/apply/compose/verify/write | ✓ | Entire sequence remains inside `with progress_lock(...)`. |
| Transaction wraps only writes | ✓ | `with transaction()` encloses only `tx.write_text(...)` calls. |

### B. M2 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| `_validate_review_iteration_value` rejects `> REVIEW_ITERATION_LIMIT` | ✓ | Over-limit branch added at `progress_state.py:349`-`progress_state.py:360`. |
| `review-issues` post-increment check retained | ✓ | Still rejects `new_iter > REVIEW_ITERATION_LIMIT`. |
| `iter=7` entry remains allowed | ✓ | Unit test confirms `write-complete` preserves 7. |
| `iter=8` and `iter=42` messages include escalation | ✓ | Tests assert `8`/`42` and `escalate`. |
| Round 1 iteration boundary tests still pass | ✓ | Full suite passes; `6 -> 7` and `7 -> 8` behavior preserved. |

### C. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| Prior 279 tests still pass with new regressions | ✓ | Full suite now runs 293 tests OK. |
| `progress_lock.py` / `progress_history.py` / init/query/recover untouched in behavior | ✓ | Existing tests pass; no new module or dependency introduced. |
| `apply_update_event` remains the forward/replay single source | ✓ | Replay handler still delegates to `apply_update_event`. |
| `EventOutcome` shape unchanged | ✓ | Fields remain `new_state`, `history_summary`, `history_result`, `history_next`. |
| Argparse mutex group remains required and extensible | ✓ | `update` still has required mutually exclusive group with `--event` only in Phase 5.2. |
| Repo root remains unmanaged | ✓ | No repo-root `progress.md` / `progress-history.md` exists. |

### D. 测试质量

| Check | Result | Notes |
|-------|--------|-------|
| M1 covers bad header and unknown field | ✓ | `UpdateEventHistoryParseGuardTests` covers both parser failures. |
| M1 covers tampered non-state-machine fields | ✓ | `release` and `project_name` replay mismatch tests are present. |
| M1 covers clean cycle no false-positive | ✓ | Five-event clean cycle passes the new consistency check. |
| M1 tests assert specific error fragments | ✓ | Assertions include `malformed`, `replay consistency check failed`, field names, and `recover --confirm`. |
| M1 tests assert unchanged files | ✓ / ⚠️ | Critical mismatch tests assert both files; bad-header asserts both files; unknown-field asserts history unchanged. Progress is also pre-write by code path, but the test could optionally assert it too. |
| M2 unit tests cover four events, 7, and 42 | ✓ | `IterationOverLimitTests` covers all requested cases. |
| M2 CLI tests cover representative events and unchanged progress | ✓ | `write-complete`, `review-passed`, and `human-confirmed` are covered. |
| M2 CLI tests assert full byte-for-byte two-file unchanged | ✓ / ⚠️ | They assert `progress.md` unchanged; the code path returns before history composition, but adding history assertions would make coverage stricter. Not blocking. |
| Updated non-gated test explains single-step forge | ✓ | Comment clearly documents interaction with M1 consistency. |
| Temp-dir isolation preserved | ✓ | `_CliRunner` still uses `TemporaryDirectory`; `_seed` output remains suppressed. |

### E. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| `command-reference.md` §2 seven-step update flow covered | ✓ | Feasible replay consistency is now implemented before transaction writes. |
| `command-reference.md` §2.1 `review_iteration > 7` reject/escalate | ✓ | Shared entry guard applies to all update events. |
| Progress schema `review_iteration: 0-7` enforced | ✓ | Over-limit values now reject before transition-specific branches. |
| `task6_plan` §11.1 failure/rollback behavior | ✓ | Pre-write failures return without mutation; transaction remains rollback mechanism for write failures. |
| `progress_replay.py` wording reflects Phase 5.2 | ✓ | Top docstring and unsupported-event message are updated. |

### F. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| Parse + replay consistency cost is acceptable | ✓ | O(N) per update is fine at current phase scale; can be optimized later if needed. |
| `diff_keys` deterministic | ✓ | Uses sorted field list. |
| `recover --confirm` guidance is caller-friendly | ✓ | Gives a concrete repair command when progress/history drift is detected. |
| Review-iteration guard location is shared | ✓ | Central helper protects all current and future event branches that call it. |
| No unnecessary dependencies or modules | ✓ | Fix stays within existing modules and stdlib. |

---

## 7. Open Questions / Assumptions

- I assume O(N) parse/replay on each update is acceptable through Phase 5.3. If long-lived projects accumulate thousands of history entries, a future optimization can add incremental validation while keeping the full replay check as a periodic or debug assertion.
- I assume update should compare complete frontmatter dicts for Phase 5.2. Future phases that intentionally allow fields only some handlers know how to derive should extend replay handlers first, not loosen this equality prematurely.
- I assume stricter byte-for-byte assertions for `progress-history.md` in the new M2 CLI tests are optional polish, not a blocker, because the implementation returns before any history composition or transaction write.

---

## 8. Recommendation

**(A) accept regression and proceed to Phase 5.3 (`update --task`)**.

Required before Phase 5.3: none from this review.

Optional cleanup, not blocking:

- Add `progress-history.md` unchanged assertions to the three M2 CLI over-limit tests and `progress.md` unchanged assertion to the unknown-field malformed-history test for perfectly symmetric test coverage.
- Update the `READ_ONLY_EVENTS` comment in `progress_replay.py` at a convenient time; it still references the Phase 5.1-era "we only have init" wording, though the executable docstring and errors are now correct.
