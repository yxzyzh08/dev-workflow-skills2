# Task 6 Phase 4 Review — status_transition.py

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Phase 4 only — `skills/doc-guardian/scripts/status_transition.py` + `tests/test_status_transition.py`  
**Recommendation**: **(B) fix before Phase 5/6** — implementation is close and tests pass, but two status-transition guard gaps can silently accept invalid doc types or apply stale plans.

---

## 1. Executive Summary

Phase 4 implements the intended CLI/API shape: `plan` is dry-run, `apply` mutates frontmatter status with multi-doc transaction semantics, incremental docs use Phase 3 in-memory `promote_text()`, snapshot docs avoid Change Log sections, and post-write self-validation calls `validate.validate_file()` in-process.

Validation performed during review:

```bash
python3 -m unittest discover -s tests
# Ran 153 tests in 0.395s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK

python3 skills/doc-guardian/scripts/status_transition.py --help
python3 skills/doc-guardian/scripts/status_transition.py plan --help
python3 skills/doc-guardian/scripts/status_transition.py apply --help
# all OK
```

Findings distribution:

| Severity | Count | Blocks Phase 5/6? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No data-loss or rollback-breaking issue found. |
| Medium | 2 | Yes | Unknown doc types can plan/apply as success; stale plans can apply illegal status transitions. |
| Low | 0 | No | No standalone Low findings beyond optional test polish noted in assumptions. |

Overall judgment: **fix M1 and M2 before Phase 5/6**. Both are localized correctness fixes in `status_transition.py` plus focused regression tests; no design revisit is needed.

---

## 2. Findings

### Medium

#### M1 — Unknown `type` strings are not rejected and can succeed as no-op

- **Location**: `skills/doc-guardian/scripts/status_transition.py:219`, `skills/doc-guardian/scripts/status_transition.py:226`, `skills/doc-guardian/scripts/status_transition.py:257`
- **Issue**: `compute_plan()` only rejects a missing/non-string `type`; it does not verify that a string `type` belongs to the doc-guardian schema. A document with `type: not-a-real-type` and `status: in-review` produces `op="no-op"` for `write-complete` and `apply_plan()` returns success without touching or validating the file. A mutating unknown type is only caught later by post-write `validate_file()` after a rollback, not at planning time.
- **Impact**: Violates the prompt requirement that `doc_type / current_status 缺失或非法 → op="reject"`. It also weakens idempotent retry safety: an invalid doc can be accepted as already transitioned, giving Phase 5 callers a false success signal.
- **Evidence**: A focused probe returned `PlanItem(... doc_type='not-a-real-type', current_status='in-review', target_status='in-review', op='no-op')` and `ApplyResult(mutated=(), no_ops=(...))`.
- **Recommendation**: Import `DOC_TYPES` from `skills._shared.dev_workflow.schema` and reject `doc_type not in DOC_TYPES` before gated/no-op/status checks. Add tests for unknown type already-at-target and unknown type in mutating status; both should produce `op="reject"` and `apply_plan()` should not write.

#### M2 — `apply_plan()` trusts stale `PlanItem` status/type and can apply an illegal transition after file changes

- **Location**: `skills/doc-guardian/scripts/status_transition.py:373`, `skills/doc-guardian/scripts/status_transition.py:381`, `skills/doc-guardian/scripts/status_transition.py:307`
- **Issue**: `apply_plan()` re-reads file content before building final content, but `_build_new_content()` does not verify that the current on-disk `type` and `status` still match the `PlanItem` produced by `compute_plan()`. If a file changes between `compute_plan()` and `apply_plan()`, the stale plan can overwrite the new status with the old target even when that transition is now illegal.
- **Impact**: This can regress doc status without being caught by `validate_file()`, because `validate_file()` validates enum/schema/path, not transition legality. Example: compute `write-complete` on `draft` snapshot doc, externally change it to `review-passed`, then apply the stale plan; final status becomes `in-review`, an illegal backward transition for `write-complete`.
- **Evidence**: A focused probe changed a planned `test-report` from `draft` to `review-passed` before `apply_plan()`; after apply, final frontmatter status was `in-review` and validation succeeded.
- **Recommendation**: During apply preflight, re-parse each mutating/no-op doc and verify `type`, `status`, and `is_incremental` still match the plan, or recompute the plan inside `apply_plan()` from `item.doc_path` and reject if the operation is no longer identical. Add a regression test that mutates a doc between `compute_plan()` and `apply_plan()` and asserts `StatusTransitionError` with unchanged bytes.

---

## 3. Cross-Doc Consistency Check

| Reference / Plan | Status | Notes |
|------------------|--------|-------|
| `change-log-format.md` §7.1 | ✅ | Incremental mutation updates frontmatter, appends `- <now> [frontmatter]: 更新 status 至 <target>`, calls `promote_text()` in memory, clears Pending Changes, and writes inside the transaction. |
| `change-log-format.md` §2.2 | ✅ | Generated frontmatter entry is a single canonical line matching the strict entry regex: timestamp with `Z`, `[frontmatter]`, non-empty summary. |
| `frontmatter-schema.md` §1-§2 | ⚠️ | Status event mapping and gated set match the schema, but unknown doc type strings are not rejected (M1), which is inconsistent with the schema enum requirement. |
| `doc-guardian/SKILL.md` §6.7 | ✅⚠️ | CLI shape, four event mappings, progress-first sequencing, incremental Change Log atomicity, snapshot behavior, and idempotent no-op are implemented. Stale plan trust (M2) is an API robustness gap for future in-process callers. |
| `task6_plan_20260507.md` §9 | ✅⚠️ | Plan/apply, event table, idempotent no-op, and status mutation behavior are present. Apply should re-check current status/type or rebuild the plan to fully satisfy the preflight intent (M2). |
| `task6_plan_20260507.md` §11.3 | ✅ | Mutating writes use `atomic.transaction()`; post-write validation failure rolls back all staged docs in tests. |
| `task6_plan_20260507.md` §12 | ✅ | Test suite uses `unittest` and temp dirs; Phase 4 adds comprehensive tests for event mapping, gated docs, idempotency, rollback, pending entry format, and CLI integration. |
| Phase 3 invariants | ✅ | Phase 4 reuses `promote_text()`, `validate_file()`, and `transaction()` instead of duplicating Change Log, validation, or atomicity logic. No subprocess self-validation is used. |

---

## 4. Checklist Results

### A. `compute_plan(event, docs, root)` Pure Logic

| Check | Result | Notes |
|-------|--------|-------|
| Unknown event raises | ✓ | Direct API raises `StatusTransitionError`; CLI uses argparse `choices` and exits 2 for invalid events. |
| File missing/read/frontmatter parse errors | ✓ | Returned as `op="reject"` with readable errors, not raised. |
| Missing/invalid status | ✓ | Missing/non-string/non-enum status rejects with allowed status list. |
| Missing/invalid doc type | ❌ | Missing/non-string rejects, but unknown string doc type does not reject (M1). |
| `human-confirmed` gated check before no-op | ✓ | Non-gated docs reject even if current status coincidentally equals `approved`. |
| Current already target -> no-op | ✓ | No-op items do not write or bump `updated`. M1 is the unknown-type exception. |
| Current not allowed old -> reject | ✓ | Error includes event, allowed-old list, and current status. |
| Incremental classification | ✓ | Uses `INCREMENTAL_DOC_TYPES`; snapshots are not forced to contain Change Log sections. |
| Read-only behavior | ✓ | Only reads files and parses frontmatter; no writes or transactions. |

### B. `apply_plan(plan, root, *, now=None)` Write Flow

| Check | Result | Notes |
|-------|--------|-------|
| Reject preflight before writes | ✓ | Any `op="reject"` raises before content build/transaction. |
| All no-op returns without transaction | ✓ | Returns `ApplyResult(mutated=(), no_ops=...)` and leaves bytes unchanged. |
| Stale plan validation | ❌ | Re-reads file but does not confirm on-disk type/status still match the plan (M2). |
| `_build_new_content` frontmatter mutation | ✓ | Parses frontmatter, updates copied dict, renders Markdown. |
| Incremental Pending entry | ✓ | Appends canonical `[frontmatter]` entry, then calls `promote_text()` before writing. |
| Snapshot handling | ✓ | Only renders updated frontmatter/body; no Pending/Change Log sections are added. |
| In-memory errors before write | ✓ | Frontmatter/changelog/markdown errors raise before transaction writes; missing Pending raises `StatusTransitionError`. |
| Transaction write + self-validate | ✓ | Writes all mutating docs via `tx.write_text()`, then calls `validate_module.validate_file(abs_path, root)`. Any issue raises and triggers rollback. |
| `now` default/test injection | ✓ | Defaults to UTC second-precision `Z`; tests inject deterministic timestamp. |

### C. CLI (`plan` / `apply` + `--root`)

| Check | Result | Notes |
|-------|--------|-------|
| `--root` and path resolution | ✓ | Defaults to cwd; relative docs are rooted; absolute docs are used directly, matching Phase 3 scripts. |
| Argparse event/doc validation | ✓ | Invalid events and missing `--doc` are usage errors (exit 2). |
| `plan` behavior | ✓ | Rejects exit 1 to stderr; clean plans exit 0 to stdout and do not write. |
| `apply` reject behavior | ✓ | Prints full plan and “refusing to mutate”; file bytes remain unchanged. |
| `apply` success/no-op output | ✓ | Mutations go to stdout; no-op diagnostic goes to stderr; exit 0. |
| No subcommand | ✓ | Help to stderr and exit 2. |
| Import bootstrap | ✓ | Adds repo root and scripts dir; `import validate as validate_module` remains stable in tests. |

### D. Phase 3 Invariant Consistency

| Check | Result | Notes |
|-------|--------|-------|
| No write-before-promote intermediate state | ✓ | Pending entry is appended in memory, promoted in memory, then final content is written. |
| Reuses Phase 3 Change Log discipline | ✓ | Does not reimplement parsing; relies on `promote_text()` and `validate_file()`. |
| Canonical generated Pending entry | ✓ | Single-line, no comments/trailing content, strict timestamp. |
| Reuses atomic transaction | ✓ | No custom atomic/rollback logic added. |
| In-process `validate_file` | ✓ | Uses direct `validate_module.validate_file`, not subprocess. |

### E. Tests

| Test Area | Result | Notes |
|-----------|--------|-------|
| Event mappings | ✓ | Covers write/review/human-confirmed paths for incremental and snapshot docs. |
| Gated rejection | ✓ | PRD/SRS/Architecture/CR pass; development-plan/test-report reject and remain byte-identical. |
| Idempotency | ✓ | Incremental, snapshot, approved gated no-op, and mixed no-op/mutate are covered. |
| Multi-doc transaction | ✓ | Happy path, preflight reject, post-write validate mock rollback, unknown event, and missing file covered. |
| Pending entry format | ✓ | Exact entry text, timestamp=updated, date-desc ordering, `validate_text`, `validate_file`, and Pending comment compatibility covered. |
| CLI integration | ✓ | Help/no-subcommand/invalid event, dry-run, apply, no-op, reject, and multi-doc happy path covered. |
| Missing regression tests | ⚠️ | Add focused tests for unknown doc type (M1) and stale plan/file changed after `compute_plan()` (M2). |
| Isolation | ✓ | Uses `tempfile.TemporaryDirectory()`; no real repo `docs/` / `skills/` mutation. |

### F. Cross-Doc Consistency

- ✓ Event table matches `frontmatter-schema.md` and `doc-guardian/SKILL.md`.
- ✓ Change Log entry format matches `change-log-format.md` §7.1 / §2.2.
- ✓ Atomicity and tests match `task6_plan_20260507.md` §11.3 / §12.
- ⚠️ `doc_type` enum validity is the main schema consistency miss (M1).

### G. Design / Maintainability

| Check | Result | Notes |
|-------|--------|-------|
| API reuse by Phase 5 | ⚠️ | Dataclasses and functions are reusable, but `apply_plan()` needs freshness validation before Phase 5 imports it directly (M2). |
| Dataclass shape | ✓ | `PlanItem` and `ApplyResult` are clear and frozen. |
| Single event table | ✓ | `EVENTS` is centralized and easy to extend with future spec changes. |
| Error messages | ✓ | Mostly actionable, include relative paths and status facts; M2 fix should add stale-plan detail. |
| Import order / `noqa: E402` | ✓ | Reasonable script bootstrap with repo root + scripts dir. |
| No unnecessary shared helper | ✓ | Phase 4 stays in the script and reuses existing shared modules. |

---

## 5. Open Questions / Assumptions

1. **Existing non-empty Pending Changes**: `status_transition.py` appends its `[frontmatter]` entry and `promote_text()` promotes all pending entries. I did not count this as a finding because the documented call sequence requires callers to run `changelog.py promote` / `validate.py file` before progress and status transition, and the Phase 4 prompt explicitly says to append then promote in memory.
2. **Concurrent modifications**: There is no file lock in Phase 4, but `apply_plan()` can still cheaply reject stale plans by rechecking on-disk type/status before building content. I treat this as a required robustness fix (M2), not a request for new locking or Phase 5 design.
3. **No-op validation scope**: The idempotent no-op branch intentionally avoids writing and does not run `validate_file()`. This is acceptable for byte-for-byte retry semantics, but it makes M1 more important: unknown doc types must be rejected before no-op.

---

## 6. Recommendation

**(B) fix before Phase 5/6**.

Must fix before Phase 5:

1. **M1** — reject unknown string doc types in `compute_plan()` before gated/no-op checks. Estimated fix: 5-10 LOC + 2 tests.
2. **M2** — make `apply_plan()` re-validate plan freshness (type/status/is_incremental still match; or recompute and compare operations) before writing/no-op return. Estimated fix: 20-35 LOC + 2-3 tests.

Why Phase 5 should wait: Phase 5 `progress.py update --event` is expected to call or coordinate with this helper after progress transitions. If the helper can return success for invalid doc types or apply a stale illegal status transition, Phase 5 would inherit a false-success path and could advance workflow state while document state is wrong.

No architecture revisit is needed. The implementation model is sound; the fixes are localized guard checks and tests.
