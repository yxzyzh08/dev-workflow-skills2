# Task 6 Phase 5.1 Round 2 Review — progress.py Core Regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Regression review for the Round 2 fixes to `skills/_shared/dev_workflow/progress_replay.py`, `skills/workflow-protocol/scripts/progress.py`, `tests/test_progress_replay.py`, and `tests/test_progress_init.py`, using `docs/review/task6_phase5_1_progress_core_review_20260507.md` as the Round 1 baseline.  
**Recommendation**: **(A) accept regression and proceed to Phase 5.2 (`update --event`)** — both Round 1 Medium findings are fixed, regression coverage is specific enough to prevent the same failures, and no new blocking issue was found.

---

## 1. Executive Summary

Round 2 correctly addresses the two Round 1 blockers without expanding Phase 5.1 scope. `replay_history()` now validates append/document order directly instead of sorting first, and `init --scenario` now flows through the normal workflow validation path with exit code 1 rather than argparse usage code 2.

Findings distribution for this review:

| Severity | Count | Blocks Phase 5.2? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss, atomicity, or replay-regression issue found. |
| Medium | 0 | No | Round 1 M1/M2 are fixed. |
| Low | 0 | No | No new non-blocking implementation defect found. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 230 tests in 1.646s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# compileall_exit=0

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py init --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py query --help
PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py recover --help
# all OK
```

Additional spot checks:

- `init --scenario S2`, `S2-1`, `S2-2`, `S2-3`, and `S2-4` each returned exit code 1, emitted a scenario validation error, and created no progress files in temp roots.
- Manual `replay_history([later, earlier])` checks now raise `timestamp goes backwards (previous ...)` before duplicate-init or unsupported-event validation.
- Symlink invocation of `progress.py --help` still works with the `parents[3]` bootstrap.
- No repo-root `progress.md` / `progress-history.md` files were created.

---

## 2. Round 1 Findings 回归状态

| Round 1 Finding | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| M1 — `replay_history()` sorted entries before timestamp monotonicity validation | ✅ Fixed | `progress_replay.py` imports only `HistoryEntry` at `skills/_shared/dev_workflow/progress_replay.py:23`; `replay_history()` iterates `for entry in history` at `skills/_shared/dev_workflow/progress_replay.py:141`; the backwards timestamp check runs immediately at `skills/_shared/dev_workflow/progress_replay.py:145` before terminal or handler dispatch. | The previous `iter_entries_chronological()` helper remains available in `progress_history.py`, but replay no longer uses it. |
| M2 — invalid `init --scenario` returned argparse usage code 2 instead of validation code 1 | ✅ Fixed | `--scenario` no longer uses `choices=`; the parser comment and help live at `skills/workflow-protocol/scripts/progress.py:346`-`skills/workflow-protocol/scripts/progress.py:356`. Invalid values now reach `build_initial_state()` and `cmd_init()`'s `ProgressStateError` handler. | Tests now assert code 1 and no output files for both `S2` and `S2-1`. Manual checks also covered all S2 subtypes. |

---

## 3. New Findings (Round 2)

No new findings.

I did not identify any new High, Medium, or Low defects introduced by the Round 2 changes. The modifications are limited to the intended files, preserve Phase 5.1 boundaries, and do not require design changes before Phase 5.2.

---

## 4. Cross-Finding Consistency Check

| Reference / Plan | Status | Notes |
|------------------|--------|-------|
| Round 1 review M1/M2 | ✅ | Both prior Medium findings have direct implementation fixes and targeted regression tests. |
| `skills/workflow-protocol/references/command-reference.md` §1 (`init`) | ✅ | Init state mutation remains aligned. Invalid init scenarios now behave as workflow validation failures, consistent with invalid project/release handling. |
| `skills/workflow-protocol/references/command-reference.md` §4 (`recover`) | ✅ | Replay now validates history in append/document order, which better matches append-only history semantics and avoids silently reordering corrupt history. |
| `docs/implementation/task6_plan_20260507.md` §11.1 | ✅ | Locking, atomic write paths, `--root`, and `--lock-timeout` behavior remain unchanged for implemented mutating commands. |
| `docs/implementation/task6_plan_20260507.md` §13 / §15 | ✅ | Phase boundaries are preserved; no Phase 5.2+ command is treated as missing or required in this review. |
| `skills/workflow-protocol/SKILL.md` command matrix | ✅ | The command surface remains Phase 5.1-only: `init`, `query`, and `recover`. Deferred `update`, release, bug, and incident commands remain future scope. |
| `skills/doc-guardian/SKILL.md` | ✅ | No doc-guardian command behavior is touched by this fix set. |

---

## 5. Round 2 Implementation Quality Spot-checks

### 5.1 `replay_history` document-order traversal

- `progress_replay.py` no longer imports or calls `iter_entries_chronological`; replay consumes the caller-provided iterable directly.
- The docstring at `skills/_shared/dev_workflow/progress_replay.py:121`-`skills/_shared/dev_workflow/progress_replay.py:136` clearly states the append/document-order contract.
- The loop at `skills/_shared/dev_workflow/progress_replay.py:141` preserves parse order from `parse_history_text()`.
- The monotonicity check at `skills/_shared/dev_workflow/progress_replay.py:145`-`skills/_shared/dev_workflow/progress_replay.py:150` fires before terminal handling and before `_HANDLERS.get(entry.event)`.
- The error message includes both `timestamp goes backwards` and the previous timestamp, which is actionable for history repair.
- Existing replay behavior for empty history, init-only history, missing init fields, invalid scenario/release, duplicate init, unsupported event, supported-events set, and terminal empty-set tests remains passing.

### 5.2 `init --scenario` validation path

- `skills/workflow-protocol/scripts/progress.py:346`-`skills/workflow-protocol/scripts/progress.py:356` intentionally removes `choices=` and documents why invalid workflow values are not CLI usage errors.
- Help text still lists legal init scenarios and notes S2 subtype routing through future `release-start`, so UX remains clear despite removing argparse enforcement.
- Invalid scenarios now pass parser validation, enter `cmd_init()`, call `build_initial_state()`, raise `ProgressStateError`, print a `scenario` error, and return exit code 1.
- Since validation occurs before transaction writes, no `progress.md` or `progress-history.md` is created on invalid scenario input.
- Manual temp-root checks confirmed `S2`, `S2-1`, `S2-2`, `S2-3`, and `S2-4` all follow the code-1/no-file path.

### 5.3 Regression test coverage

- `tests/test_progress_replay.py:122` asserts `timestamp goes backwards` and the previous timestamp, closing the weak Round 1 `assertRaises` gap.
- `tests/test_progress_replay.py:136` verifies monotonicity fires before unsupported-event handler dispatch by asserting the error does not contain `not supported`.
- `tests/test_progress_replay.py:157` is the detective test for the original bug: `[later, earlier]` must not be sorted into a valid or different failure path.
- `tests/test_progress_init.py:190` verifies invalid `S2` returns 1, emits `scenario`, and creates neither managed file.
- `tests/test_progress_init.py:209` verifies an S2 subtype (`S2-1`) takes the same validation path, covering release-start-only scenario values at init time.
- All new tests use the existing temp-dir CLI fixture and do not touch the implementation repo as a managed workflow project.

---

## 6. Checklist Results

### A. M1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| `replay_history` removed `iter_entries_chronological` sorting | ✓ | Replay imports only `HistoryEntry` and loops over `history` directly. |
| Loop input is caller-provided document order | ✓ | `for entry in history` preserves `parse_history_text()` order. |
| Timestamp check runs at loop entry before terminal/handler dispatch | ✓ | The check precedes `seen_terminal` and `_HANDLERS.get(...)`. |
| Error message includes `timestamp goes backwards` and previous timestamp | ✓ | Message includes both current and previous timestamps. |
| `iter_entries_chronological` helper remains available elsewhere | ✓ | It remains in `progress_history.py` and is simply not used by replay. |
| Existing replay tests still pass | ✓ | Full suite passed: 230 tests OK. |
| New monotonicity tests cover specificity, ordering, and no-sort regression | ✓ | Three targeted tests are present and assert the concrete message. |

### B. M2 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| argparse removed `choices=` for `--scenario` | ✓ | The argument has `required=True` and descriptive help only. |
| Help text still explains legal values | ✓ | Help shows `['S1', 'S3']` and mentions S2 subtype entry via future `release-start`. |
| Invalid scenario reaches `ProgressStateError` path | ✓ | Manual and unit tests return code 1 with `scenario` in stderr. |
| Tests assert exit code, stderr, and no files | ✓ | Both invalid scenario tests assert code 1, `scenario`, and missing `progress.md` / `progress-history.md`. |
| S2 subtype handling uses code 1, not code 2 | ✓ | `S2-1` is covered by unit test; manual checks covered `S2-1` through `S2-4`. |

### C. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| Phase 1-4 + Phase 5.1 tests all pass | ✓ | `Ran 230 tests ... OK`. |
| `progress_lock.py` / `progress_history.py` / `progress_state.py` untouched by Round 2 intent | ✓ | The reviewed fix set does not alter lock/history/state behavior; only replay imports changed relative to M1. |
| `init` / `query` / `recover` high-level behavior remains consistent | ✓ | Locking, atomic transaction use, root handling, and exit-code contract are preserved. |
| `query` remains unlocked | ✓ | No code path added lock acquisition to `query`; existing lock-held query tests pass. |
| `recover` confirmation and failure behavior remain intact | ✓ | `--confirm`, missing/empty/parse-fail/unsupported-event handling remains unchanged; tests pass. |
| Repo root remains unmanaged | ✓ | No `progress.md` / `progress-history.md` exists under the implementation repo root. |

### D. 测试质量

| Check | Result | Notes |
|-------|--------|-------|
| M1 tests use concrete message assertions | ✓ | All three monotonicity tests assert `timestamp goes backwards`; the first also asserts previous timestamp. |
| M1 tests cover document-order reversal | ✓ | `[later, earlier]` is covered explicitly. |
| M1 tests cover check ordering before handler dispatch | ✓ | Unsupported `release-close` with backwards timestamp produces monotonicity error first. |
| M1 tests protect against pre-sort regression | ✓ | The detective test would fail or take a different error path if replay sorted first. |
| M2 tests check code/stderr/no files | ✓ | Both invalid scenario tests assert all three. |
| M2 tests cover S2 subtype class | ✓ | `S2-1` is covered; manual review confirmed remaining S2 subtypes behave the same. |
| Tests use temporary roots | ✓ | Existing `_CliRunner` fixture uses `TemporaryDirectory`. |
| Round 1 tests not regressed | ✓ | Full test suite passes. |

### E. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| `command-reference.md` §1 init fields still align | ✓ | No state construction change was made. |
| `command-reference.md` §4 recover replay semantics improved | ✓ | Replay now respects append order and rejects backwards timestamps before applying handlers. |
| `task6_plan` §11.1 atomicity/locking remains aligned | ✓ | Round 2 does not change transaction or lock structure. |
| `workflow-protocol/SKILL.md` command matrix unaffected | ✓ | No additional subcommands or event names were added. |
| `doc-guardian/SKILL.md` unaffected | ✓ | No doc-guardian script or helper behavior changed. |

### F. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| Replay contract is clearer | ✓ | Docstring now states caller supplies append/document order. |
| Scenario help remains future-friendly | ✓ | It distinguishes init scenarios from S2 release-start scenarios. |
| No new dependencies or shared helpers | ✓ | Only stdlib/existing imports remain. |
| Error messages are caller-friendly | ✓ | Scenario errors include the bad value; replay errors include current and previous timestamps. |
| Phase 5.2+ concerns kept out of implementation | ✓ | No deferred commands were implemented in Round 2. |

---

## 7. Open Questions / Assumptions

- I continue to assume Phase 5.1 intentionally keeps `progress_history.py` field parsing limited to `agent` / `result` / `next`; future `task` field support can be added when Phase 5.3 defines the `update --task` history contract.
- I assume regex-level timestamp validity remains acceptable for Phase 5.1; this review only verifies monotonic ordering semantics, not full calendar-date validation.
- I assume preserving `iter_entries_chronological()` as an unused helper is acceptable because the prompt explicitly called out keeping it available for other callers.

---

## 8. Recommendation

**(A) accept regression and proceed to Phase 5.2 (`update --event`)**.

Required before Phase 5.2: none from this review.

Optional cleanup, not blocking:

- When Phase 5.2 adds the first multi-event replay handlers, add at least one parse-and-replay test whose event order is valid only in append order to keep the replay contract visible.
- When Phase 5.3 adds task history entries, revisit whether `progress_history.py` should admit `- task:` and how replay should consume it.
