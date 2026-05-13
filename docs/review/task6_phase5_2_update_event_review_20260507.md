# Task 6 Phase 5.2 Review — progress.py update --event

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Phase 5.2 implementation for `progress.py update --event`, including `progress_state.apply_update_event`, `progress_replay` update-event handlers, `progress.py cmd_update`, and the new/extended update-event tests.  
**Recommendation**: **(B) fix before Phase 5.3 (`update --task`)** — the main event state machine is mostly aligned, but two validation gaps remain in the mutation/replay foundation that Phase 5.3 would otherwise inherit.

---

## 1. Executive Summary

Phase 5.2 implements the intended command surface and keeps the phase boundary clean: only `update --event` is added; `update --task`, `update --advance`, release, bug, and incident commands remain deferred. The forward path and replay path both delegate to `apply_update_event`, which is the right single-source-of-truth shape. The test suite passes locally.

Findings distribution:

| Severity | Count | Blocks Phase 5.3? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No direct data-loss or lock/transaction bypass issue found on valid histories. |
| Medium | 2 | Yes | `cmd_update` appends to malformed history without parsing/replay consistency; `apply_update_event` can bypass the review-iteration cap when the existing state already exceeds 7. |
| Low | 0 | No | No additional low-severity defect recorded. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 279 tests in 2.220s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# compileall_exit=0

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py update --help
# OK
```

Additional checks:

- No repo-root `progress.md` / `progress-history.md` files were created.
- Manual smoke showed malformed `progress-history.md` is currently accepted by `update --event` and appended to, confirming M1.
- Manual smoke showed `review_iteration=8` can be reset by `review-passed`, confirming M2.

---

## 2. Findings

### High

No High findings.

### Medium

#### M1 — `update --event` appends to malformed history and skips the feasible replay consistency check

- **Location**: `skills/workflow-protocol/scripts/progress.py:376`
- **Issue**: `cmd_update()` reads `progress-history.md` as text, but does not parse it with `parse_history_text()` before appending and does not replay the newly composed history before committing. As a result, a malformed existing history still gets a new canonical entry appended and `progress.md` is advanced.
- **Impact**: A corrupt `progress-history.md` remains corrupt but now has additional state-changing entries after it; `recover --confirm` will later fail to replay the history. This contradicts the prompt's `cmd_update` review item requiring read + parse before mutation, and it diverges from `command-reference.md` §2 / SKILL.md §4.1 / task6_plan §11.1, which describe update as append + progress overwrite followed by consistency replay where feasible. Phase 5.2 makes replay feasible for `init` plus the four update events, so this is the right time to close the gap before Phase 5.3 adds more update modes.
- **Recommendation**: In `cmd_update()`, after reading `history_text`, call `parse_history_text(history_text)` and fail with exit 1 on `HistoryError` before applying the event. After composing `new_history_text`, parse/replay it with `replay_history(parse_history_text(new_history_text))` and compare the replayed state to `outcome.new_state` before entering `atomic.transaction()`; any mismatch should exit 1 without writing. Add tests for corrupt history rejection and for byte-for-byte unchanged `progress.md` / `progress-history.md` on replay/parse failure.

#### M2 — Existing `review_iteration > 7` can be preserved or reset instead of rejected

- **Location**: `skills/_shared/dev_workflow/progress_state.py:344`
- **Issue**: `_validate_review_iteration_value()` only rejects non-int, bool, and negative values. It does not reject integers above `REVIEW_ITERATION_LIMIT`. Therefore, a malformed state with `review_iteration=8` can pass `write-complete` unchanged, or pass `review-passed` and reset the counter to `0`.
- **Impact**: The state-machine guard for the review loop cap can be bypassed if `progress.md` is already malformed or manually edited. `command-reference.md` §2.1 states that `review_iteration > 7` should reject and escalate, and the `progress.md` schema documents the field as `0-7`. Letting `review-passed` clear an over-limit value undermines the human-escalation invariant.
- **Recommendation**: Extend `_validate_review_iteration_value()` to reject `value > REVIEW_ITERATION_LIMIT` with an error message that includes the value, limit, and `escalate`. Keep the existing `review-issues` post-increment check so `6 -> 7` remains allowed and `7 -> 8` remains rejected. Add tests for `review_iteration=8` with at least `write-complete` and `review-passed`, plus a bool regression if desired.

### Low

No Low findings.

---

## 3. Cross-Doc Consistency Check

| Source | Result | Notes |
|--------|--------|-------|
| `command-reference.md` §2 update common flow | ⚠️ | Locking and dual writes are present, but history parse/replay consistency is missing in `cmd_update()` (M1). |
| `command-reference.md` §2.1 review-loop transitions | ⚠️ | Four event transitions are implemented, but existing `review_iteration > 7` is not rejected for all events (M2). |
| `docs/implementation/task6_plan_20260507.md` §5.3 | ✓ / ⚠️ | The four event mutations match the matrix for valid states; the iteration cap issue is tracked as M2. |
| `docs/implementation/task6_plan_20260507.md` §11.1 | ⚠️ | `.progress.lock` and `atomic.transaction()` are used, but the feasible consistency replay step is absent (M1). |
| `docs/implementation/task6_plan_20260507.md` §13 | ✓ | Phase slicing is respected; deferred Phase 5.3/5.4/6 commands are not implemented or judged missing. |
| `skills/workflow-protocol/SKILL.md` command matrix | ✓ / ⚠️ | `update --event` command surface and event names align; the SKILL update atomic flow includes consistency replay, which is not yet implemented (M1). |
| Phase 5.1 Round 2 closure | ✓ | Timestamp document-order replay remains intact, and `init --scenario` validation behavior is unchanged. |

---

## 4. Checklist Results

### A. `apply_update_event` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| `write-complete` from `write` / `revising` to `in-review` | ✓ | Implemented and preserves `review_iteration`. |
| `review-issues` from `in-review` to `revising`, incrementing iteration | ✓ | `6 -> 7` allowed and `7 -> 8` rejected. |
| `review-passed` from `in-review` to `review-passed`, resetting iteration | ✓ / ⚠️ | Valid-state behavior is correct; malformed existing `review_iteration > 7` can be reset (M2). |
| `human-confirmed` from `review-passed` to `approved`, gated only | ✓ | Non-gated stages reject with stage details. |
| Active-project precondition | ✓ | Non-`active` `project_state` rejects. |
| `sub_state` and `review_iteration` type validation | ✓ / ⚠️ | Invalid sub_state and bool/negative iteration are handled; over-limit existing iteration is not (M2). |
| `EventOutcome` frozen and useful | ✓ | Dataclass is frozen and exposes state plus history text fields. |
| Only `sub_state` / `review_iteration` / `updated` frontmatter fields changed | ✓ | `new_state = dict(state)` then sets those three keys. |
| `now` timestamp validation reused | ✓ | `_validate_timestamp(now, field="now")` is used. |
| Event whitelist remains exactly four events | ✓ | `EVENTS` set matches the whitelist. |

### B. `progress_replay.py` 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `_apply_update_event_factory(event_name)` delegates to `apply_update_event` | ✓ | Forward and replay paths share the same state-machine helper. |
| Four handlers registered through `_HANDLERS` | ✓ | Dict comprehension registers sorted `UPDATE_EVENT_NAMES` plus `init`. |
| Replay uses entry timestamp for `updated` | ✓ | Handler passes `now=entry.timestamp`. |
| `ProgressStateError` wraps as `ReplayError` with timestamp | ✓ | Error context includes `history at <timestamp>`. |
| `supported_events()` returns five items | ✓ | Tests assert `init` plus four update events. |
| Phase 5.1 document-order monotonicity check preserved | ✓ | Replay still loops in document order and checks timestamps before handler dispatch. |

### C. `progress.py update` CLI

| Check | Result | Notes |
|-------|--------|-------|
| Lock is acquired for mutation | ✓ | `with progress_lock(root, timeout=args.lock_timeout)` wraps update. |
| `progress.md` / `progress-history.md` existence checks | ✓ | Missing file guards return exit 1. |
| `progress.md` frontmatter parse failure returns 1 | ✓ | `FrontmatterError` is caught. |
| `progress-history.md` strict parse before append | ❌ | History text is read but not parsed before append (M1). |
| `apply_update_event` handles unknown/illegal/terminal cases | ✓ | `ProgressStateError` is caught and returned as exit 1. |
| Canonical history entry uses event literal and allowed fields | ✓ | `HistoryEntry` uses `event`, `agent`, `result`, and `next`. |
| Dual write uses `atomic.transaction()` | ✓ | `progress.md` and `progress-history.md` writes share one transaction. |
| Feasible replay consistency check before/within transaction | ❌ | No parse/replay check of the composed history is performed (M1). |
| Argparse mutually exclusive group is required | ✓ | Missing mode exits 2; `--event` itself has no `choices=`. |
| Success/error output style | ✓ | Success prints one stdout line; failures use stderr. |

### D. Tests

| Check | Result | Notes |
|-------|--------|-------|
| `test_apply_update_event.py` covers happy and illegal branches | ✓ | Coverage is broad for valid states and event-specific illegal transitions. |
| Iteration boundary `6 -> 7` / `7 -> 8` | ✓ | Covered for `review-issues`. |
| Human-confirmed gated/non-gated coverage | ✓ | Gated stages pass and four non-gated stages reject. |
| Terminal project, unknown event, invalid now/sub_state, negative iteration | ✓ | Covered. |
| Existing over-limit `review_iteration > 7` for non-`review-issues` events | ❌ | Missing; this gap allows M2. |
| `ReplayUpdateEventTests` cover full cycle and iteration behavior | ✓ | Full cycle, review-issues accumulation, reset, illegal transition, and timestamp updated are covered. |
| `test_progress_update_event.py` covers CLI happy cycle and rejections | ✓ | Unknown event, illegal transition, non-gated human-confirmed, iteration limit, aborted project, file guards, lock, and recover roundtrip are covered. |
| Corrupt existing `progress-history.md` update path | ❌ | Missing; this gap allows M1. |
| Temp-dir isolation and silent `_seed` | ✓ | Tests use `TemporaryDirectory`; seed output is suppressed. |
| Test-only frontmatter rewrite is marked | ✓ | `_rewrite_progress()` is clearly documented as test-only. |

### E. 与既有 invariant 的一致性

| Check | Result | Notes |
|-------|--------|-------|
| Phase 5.1 Round 2 tests still pass | ✓ | Full 279-test suite passes, including timestamp-order replay tests. |
| `progress_lock.py` / `progress_history.py` not expanded for Phase 5.2 | ✓ | No new dependencies or modules were introduced. |
| `init` / `query` / `recover` behavior preserved | ✓ | Existing tests pass; recover can replay valid update-event histories. |
| `atomic.transaction()` remains dual-write mechanism | ✓ | Used by `init`, `recover`, and `update`. |
| History title and canonical append spacing | ✓ | `append_history_text()` remains the shared append path. |
| Existing corrupt-history handling before update | ⚠️ | Update does not reject malformed existing history (M1). |

### F. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| `apply_update_event` single-source design | ✓ | Good separation: pure state transition shared by CLI and replay. |
| Error messages are actionable | ✓ / ⚠️ | Most include event/value; over-limit existing iteration has no guard yet (M2). |
| `EventOutcome` fields fit CLI/history needs | ✓ | Caller can use summary/result/next directly. |
| Mutex group design leaves room for `--task` / `--advance` | ✓ | Required mutually-exclusive group is correctly structured. |
| Import order and `noqa: E402` pattern | ✓ | Consistent with prior scripts. |
| Replay documentation freshness | ⚠️ | The top-level replay docstring still says Phase 5.1 only registers `init`; harmless but worth refreshing when fixing M1/M2. |

---

## 5. Open Questions / Assumptions

- I assume Phase 5.2 should enforce the update common-flow consistency check now that replay supports `init` plus all four `update --event` entries; if maintainers intentionally deferred this, that deferral should be documented explicitly because it diverges from `command-reference.md` §2 and SKILL.md §4.1.
- I assume `review_iteration > 7` in an existing `progress.md` should be treated as state corruption and rejected for every mutating event, matching `command-reference.md` §2.1 and the schema range `0-7`.
- I did not treat missing `update --task`, `update --advance`, release, bug, incident, protected rollback, or `validate.py consistency` as findings; those remain later phases.

---

## 6. Recommendation

**(B) fix before Phase 5.3 (`update --task`)**.

Required before Phase 5.3:

1. **Fix M1**: parse existing history before append and perform a replay consistency check on the newly composed history before committing. Add corrupt-history and replay-mismatch/unchanged-files tests. Estimated scope: ~20-45 implementation LOC plus ~20-40 test LOC.
2. **Fix M2**: reject existing `review_iteration > REVIEW_ITERATION_LIMIT` in `_validate_review_iteration_value()` and add over-limit tests for non-`review-issues` events. Estimated scope: ~5-10 implementation LOC plus ~10-20 test LOC.

Can be deferred:

- Updating `progress_replay.py`'s top-level docstring to remove the stale "Phase 5.1 only registers init" wording is optional and can be done alongside the required fixes.
- `progress_history.py` support for future `- task:` fields should wait until Phase 5.3 defines the `update --task` history shape.

Why Phase 5.3 should not proceed first:

- Phase 5.3 will add another update mutation mode on top of the same history append and replay foundation. If M1 remains, `update --task` can inherit the ability to append to unreplayable history.
- Phase 5.3 will also rely on the same progress state validation discipline. If M2 remains, a malformed `review_iteration` can bypass the review escalation invariant before task-state work begins.
