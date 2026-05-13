# Task 6 Phase 4 Round 2 Review — status_transition.py Regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Round 2 fixes for `skills/doc-guardian/scripts/status_transition.py` and `tests/test_status_transition.py`, with Round 1 findings from `docs/review/task6_phase4_status_transition_review_20260507.md` as baseline.  
**Recommendation**: **(A) accept regression and proceed to Phase 5/6** — Round 1 M1/M2 are fixed, regression coverage is present, and no new blocking findings were found.

---

## 1. Executive Summary

Round 2 correctly tightens the Phase 4 status-transition helper without changing the intended MVP surface area. `compute_plan()` now rejects unknown `type` enum strings before gated/no-op handling, and `apply_plan()` now performs a freshness preflight that re-reads every non-rejected plan item before building or writing content.

Findings distribution for this review:

| Severity | Count | Blocks Phase 5/6? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss, rollback, or transition-regression issue found. |
| Medium | 0 | No | Round 1 M1/M2 are closed. |
| Low | 0 | No | No new non-blocking implementation defect found. |

Validation performed during review:

```bash
python3 -m unittest discover -s tests
# Ran 160 tests in 0.368s
# OK

python3 -m unittest tests.test_status_transition.Round2RegressionTests -v
# Ran 7 tests in 0.012s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK

python3 skills/doc-guardian/scripts/status_transition.py --help
python3 skills/doc-guardian/scripts/status_transition.py plan --help
python3 skills/doc-guardian/scripts/status_transition.py apply --help
# all OK
```

Overall judgment: **Round 2 is acceptable**. The changes are localized, match the prompt's required repair path, preserve Phase 4 invariants, and do not introduce a need to revisit the Phase 4 design.

---

## 2. Round 1 Findings 回归状态

| Round 1 Finding | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| M1 — Unknown `type` strings are not rejected and can succeed as no-op | ✅ Fixed | `skills/doc-guardian/scripts/status_transition.py:68` imports `DOC_TYPES`; `skills/doc-guardian/scripts/status_transition.py:226`-`skills/doc-guardian/scripts/status_transition.py:251` rejects `doc_type not in DOC_TYPES` before the no-op branch at `skills/doc-guardian/scripts/status_transition.py:266`. | Unknown type now always yields `op="reject"`, including the prior false-success case where `current_status == target_status`. |
| M2 — `apply_plan()` trusts stale `PlanItem` status/type and can apply an illegal transition after file changes | ✅ Fixed | `_verify_plan_freshness()` at `skills/doc-guardian/scripts/status_transition.py:313`-`skills/doc-guardian/scripts/status_transition.py:351` re-reads every non-reject item and compares on-disk `type`/`status`; `apply_plan()` calls it at `skills/doc-guardian/scripts/status_transition.py:410`-`skills/doc-guardian/scripts/status_transition.py:415` before timestamp creation, content build, and transaction. | Stale mutate and stale no-op plans now reject before any write, avoiding both illegal backward transitions and false no-op success. |

---

## 3. New Findings (Round 2)

No new findings.

I did not identify any new High, Medium, or Low defects in the Round 2 implementation or tests. The remaining concurrency caveat is the expected Phase 4 design assumption: there is still no filesystem lock preventing an edit after the freshness gate but before the transaction write. That is not a Round 2 regression because the prompt required a pre-apply stale-plan gate, not lock-based compare-and-swap semantics.

---

## 4. Cross-Finding Consistency Check

| Reference / Plan | Status | Notes |
|------------------|--------|-------|
| Round 1 review M1/M2 | ✅ | Both previously blocking Medium findings have direct code fixes and regression tests. |
| `docs/implementation/task6_plan_20260507.md` §9 | ✅ | `plan` remains dry-run, four event mappings remain unchanged, no-op still does not duplicate Change Log entries, and multi-doc mutation still uses all-or-nothing behavior. |
| `skills/doc-guardian/SKILL.md` §6.7 | ✅ | CLI shape, progress-first sequencing, event table, Change Log atomicity, snapshot behavior, multi-doc restore, and idempotent no-op semantics remain aligned. |
| `skills/doc-guardian/references/change-log-format.md` §2.2 / §3.1 | ✅ | Incremental status changes still produce `- <now> [frontmatter]: 更新 status 至 <new-status>` via Pending Changes and in-memory promotion before writing. |
| `skills/doc-guardian/references/frontmatter-schema.md` §1-§2 | ✅ | The M1 fix now enforces the schema requirement that `type` belongs to the doc type enum instead of allowing arbitrary strings through no-op planning. |
| Phase 5/6 deferred items | ✅ | No `progress.py`, `validate.py consistency`, Bug Flow, `update --advance`, Gap-3/4/5, or extra status events are treated as Round 2 blockers. |

---

## 5. Round 2 Implementation Quality Spot-checks

### 5.1 `compute_plan()` unknown-type path

- `DOC_TYPES` is imported from the shared schema next to `STATUSES`, `GATED_APPROVED_TYPES`, and `INCREMENTAL_DOC_TYPES` at `skills/doc-guardian/scripts/status_transition.py:68`-`skills/doc-guardian/scripts/status_transition.py:73`.
- The unknown-type check is in the existing errors collection block at `skills/doc-guardian/scripts/status_transition.py:226`-`skills/doc-guardian/scripts/status_transition.py:237`.
- The check runs before gated-only validation and before the `current_status == target` no-op branch at `skills/doc-guardian/scripts/status_transition.py:245` and `skills/doc-guardian/scripts/status_transition.py:266`.
- The error includes the actual type value (`{doc_type!r}`), which is sufficient for CLI/API diagnostics.
- Existing no-op behavior for legal doc types is preserved: the no-op path is unchanged and still only reached after all type/status/gated errors are absent.

### 5.2 `_verify_plan_freshness()` implementation

- `_verify_plan_freshness()` is module-level and private, which keeps `apply_plan()` readable without prematurely moving the helper to shared code.
- It iterates all plan items and skips only `op == "reject"`, so both `mutate` and `no-op` items are covered at `skills/doc-guardian/scripts/status_transition.py:325`-`skills/doc-guardian/scripts/status_transition.py:328`.
- It re-reads and parses each file, collecting `OSError` / `FrontmatterError` into discrepancies rather than aborting at the first bad file (`skills/doc-guardian/scripts/status_transition.py:329`-`skills/doc-guardian/scripts/status_transition.py:334`).
- It compares only `type` and `status`, which is the right minimal freshness contract because `is_incremental` is derived from `type` and remaining schema/path issues are still caught by post-write validation.
- The error message begins with `stale plan detected; refusing to apply` and includes per-doc `rel_path` plus `plan=...` / `on-disk=...` details for both type and status drift.
- `apply_plan()` calls the freshness gate after reject preflight and before `now`, `_build_new_content()`, and `transaction()`, so stale plans fail before in-memory promotion or any write attempt.

### 5.3 New regression tests

- M1 coverage is present in `tests/test_status_transition.py:727`, `tests/test_status_transition.py:745`, and `tests/test_status_transition.py:757`: target-status unknown type, mutating-status unknown type, and mixed-batch blocking.
- M1 tests assert `op="reject"`, verify error text contains `unknown doc type`, exercise `apply_plan()` rejection, and check files remain byte-for-byte unchanged.
- M2 coverage is present in `tests/test_status_transition.py:776`, `tests/test_status_transition.py:807`, `tests/test_status_transition.py:833`, and `tests/test_status_transition.py:859`: stale mutate status, stale no-op status, stale type, and stale multi-doc batch.
- M2 tests use the correct `compute_plan()` → external file rewrite → `apply_plan()` timing and verify rejection before stale writes are applied.
- All new tests use the existing `TemporaryDirectory`-based `_BaseTest` fixture and do not touch real repo-managed docs.

---

## 6. Checklist Results

### A. M1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| `compute_plan()` rejects unknown type during errors collection | ✓ | Implemented at `skills/doc-guardian/scripts/status_transition.py:226`-`skills/doc-guardian/scripts/status_transition.py:237`. |
| Unknown-type check is before gated/no-op short-circuit | ✓ | Gated check follows at `skills/doc-guardian/scripts/status_transition.py:245`; no-op follows at `skills/doc-guardian/scripts/status_transition.py:266`. |
| Error message includes actual type value | ✓ | Uses `doc_type!r` in the message. |
| No extra Phase 5/6 enum/event behavior introduced | ✓ | Event table remains the four allowed events only. |
| Legal no-op behavior preserved | ✓ | Existing no-op tests and CLI no-op test pass; no-op branch unchanged except for stronger preconditions. |
| `_build_new_content()` / `apply_plan()` not affected by M1 beyond reject input | ✓ | M1 is localized to `compute_plan()` and shared import. |

### B. M2 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Every non-reject item is freshness-checked | ✓ | The helper skips only `op == "reject"`; mutate and no-op are checked. |
| Compares `type` and `current_status` only | ✓ | No redundant `is_incremental` comparison introduced. |
| Re-read/parse errors are collected | ✓ | OSError and FrontmatterError append discrepancies and continue. |
| Error message distinguishes type vs status drift | ✓ | Separate `type changed since plan was built` and `status changed since plan was built` messages. |
| Called before timestamp/content/transaction | ✓ | Call site is before `now`, mutate item filtering, `_build_new_content()`, and `transaction()`. |
| Existing Phase 4 behavior still passes | ✓ | Full suite passes: 160 tests OK. |

### C. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| `compute_plan()` remains write-free | ✓ | Reads/parses only; no transaction or write path. |
| `_verify_plan_freshness()` is read-only | ✓ | Reads/parses only and raises on drift. |
| Apply order remains reject preflight → freshness gate → build finals → transaction → post-write validate | ✓ | Preserved in `apply_plan()`. |
| Post-write self-validation remains in-process | ✓ | Still calls `validate_module.validate_file(abs_path, root)` inside the transaction. |
| Multi-doc rollback still delegated to `atomic.transaction()` | ✓ | No custom rollback added. |
| Incremental docs still promote `[frontmatter]` entry in memory | ✓ | `_build_new_content()` appends Pending entry and calls `promote_text()`. |
| Snapshot docs still only update frontmatter | ✓ | Non-incremental path returns rendered frontmatter/body without Change Log mutation. |
| Idempotent no-op remains byte-for-byte | ✓ | No-op items are freshness-checked but never written. |

### D. 测试质量

| Check | Result | Notes |
|-------|--------|-------|
| M1 target / mutating / mixed-batch contexts covered | ✓ | Three dedicated tests cover all required contexts. |
| M1 tests assert reject, error text, apply failure, unchanged bytes | ✓ | Coverage is explicit enough for the prior false-success bug. |
| M2 mutate / no-op / type / multi-doc stale contexts covered | ✓ | Four dedicated tests cover all required contexts. |
| M2 tests use compute → external rewrite → apply timing | ✓ | Each stale test creates drift after planning and before apply. |
| M2 tests assert stale rejection and no stale write | ✓ | Message and unchanged-content assertions are present across the set. |
| Tests use temp fixtures only | ✓ | New tests inherit `_BaseTest` and write under temporary roots. |
| Round 1 tests still pass | ✓ | Full suite passes: 160 tests OK. |

### E. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| Task 6 plan §9 plan/apply/idempotency/atomicity | ✓ | Behavior remains aligned; Round 2 only adds stricter preflight checks. |
| `doc-guardian/SKILL.md` §6.7 events/call order/Change Log/idempotency | ✓ | Four-event CLI and helper semantics remain aligned. |
| `change-log-format.md` `[frontmatter]` Pending entry | ✓ | Entry format and in-memory promote remain unchanged. |
| `frontmatter-schema.md` `type` enum requirement | ✓ | M1 now enforces this earlier and more accurately. |

### F. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| M1 import diff is minimal | ✓ | Adds only `DOC_TYPES` to the existing schema import. |
| `_verify_plan_freshness()` as module-level private helper is reasonable | ✓ | Keeps the code reusable without forcing shared-module abstraction before Phase 5 needs it. |
| No need to move freshness helper to shared now | ✓ | Single caller in Phase 4; future `progress.py` can refactor if needed. |
| Error messages are actionable and rel-path based | ✓ | Messages include `rel_path` and plan/on-disk values. |
| Import order / `noqa: E402` remains coherent | ✓ | Existing sys.path bootstrap pattern is unchanged. |

---

## 7. Open Questions / Assumptions

- **Concurrency assumption**: Phase 4 still assumes no concurrent external writer modifies a document after `_verify_plan_freshness()` completes and before `transaction().write_text()` writes the staged content. This is acceptable for the requested Round 2 fix; lock/mtime compare-and-swap semantics can be revisited only if Phase 5/6 introduces true concurrent writers.
- **Scope assumption**: Missing `progress.py`, `validate.py consistency`, Bug Flow commands, `update --advance`, Gap-3/4/5, and any event outside the four-event whitelist remain intentionally deferred and are not evaluated as Round 2 findings.

---

## 8. Recommendation

**(A) accept regression and proceed to Phase 5/6**.

Required before Phase 5/6: none from this review.

Optional cleanup, not blocking:

- Consider adding a future compare-and-swap or mtime freshness check if later orchestration runs multiple status transitions concurrently against the same docs.
- If Phase 5 needs direct in-process reuse of freshness validation, consider moving `_verify_plan_freshness()` to a shared helper then; no shared extraction is needed for Round 2.
