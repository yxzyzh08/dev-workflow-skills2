# Task 6 Phase 6.1 Review — Bug Flow entry/exit + Gap-3

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Code review for Task 6 Phase 6.1 implementation: `bug-start`, `bug-close`, Gap-3 `update --task`, and Phase 6.1 Gap-4 dev rollback helper.  
**Recommendation**: **(B) fix before Phase 6.2** — core state-machine behavior is strong and tests pass, but `bug-start` currently accepts malformed BUG frontmatter that the schema says must be rejected before an active Bug Flow is opened.

---

## 1. Executive Summary

Phase 6.1 is largely implemented correctly:

- `bug-start` / `bug-close` are wired into the shared progress pipeline and replay validator.
- Gap-3 (`verifying -> code-revising`) is accepted only when `verification_result.md verification_status in {fail, partial}` on the forward path, while replay correctly skips current artifact reads.
- Gap-4 rollback decisions for development root cause are encoded into `bug-start` history via `rollback=Tn:old->new;...`, so replay does not need to re-read BUG files.
- The full test suite and compile checks pass.

Findings distribution:

| Severity | Count | Blocks Phase 6.2? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No root escape, data loss, replay divergence, or broken atomic pipeline found. |
| Medium | 1 | Yes | `load_bug_report()` does not enforce required BUG frontmatter shape enough before `bug-start`. |
| Low | 1 | No | Development BUGs with ambiguous/no-localized rollback do not leave the documented planning-route note in history / next text. |

Validation performed:

```bash
TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m unittest discover -s tests
# Ran 553 tests in 4.240s
# OK
rm -rf "$TMPPYCACHE"

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
rm -rf "$TMPPYCACHE"

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py --help
# OK; 9 subcommands: init / query / recover / update / release-close /
# release-start / bug-intake / bug-start / bug-close

find . -maxdepth 3 \( -name 'progress.md' -o -name 'progress-history.md' \) -print
# no output
```

---

## 2. Findings

### Medium

#### M1 — `bug-start` can open Bug Flow on a malformed BUG frontmatter identity

**Location**: `skills/_shared/dev_workflow/progress_artifacts.py:341`

**Issue**: `load_bug_report()` checks that `bug_id` is a string and `found_in_release` is a string, but it does not enforce the BUG ID regex, does not verify that `bug_id` matches the canonical path filename, and treats absent `target_release` / `consumed_in_release` fields as acceptable `None` via `fm.get()` at `skills/_shared/dev_workflow/progress_artifacts.py:362` and `skills/_shared/dev_workflow/progress_artifacts.py:363`.

This means a file at `docs/bug/BUG-001.md` with frontmatter such as `bug_id: NOTBUG` and missing `target_release` / `consumed_in_release` can pass `load_bug_report(..., expect_root_cause="development")`. I confirmed this with a local spot check: the loader returned `BugReportInfo(bug_id='NOTBUG', target_release=None, consumed_in_release=None, ...)` instead of rejecting.

**Impact**: `progress.py bug-start` can create an active `bug_flow` for a BUG document that violates `frontmatter-schema.md`'s required BUG identity contract. That weakens traceability before Phase 6.2 reuses the same BUG-loading path for `bug-rework`, and it lets malformed BUG reports enter the state machine even though Phase 6.1's prompt and cross-doc checklist expect thin schema validation for all five bug-report fields.

Relevant schema refs:

- `skills/doc-guardian/references/frontmatter-schema.md:296` requires `bug_id: BUG-<NNN>`.
- `skills/doc-guardian/references/frontmatter-schema.md:417` says bug-report requires `bug_id`, `found_in_release`, `target_release`, `root_cause`, and `consumed_in_release` keys, with nullable values only where documented.

**Recommendation**: Before Phase 6.2, strengthen `load_bug_report()` and add regression tests:

- Reject missing required keys separately from nullable values.
- Require `bug_id` to match `^BUG-\d{3}$`.
- Require `bug_id` to match `Path(bug_path).stem`.
- Require `target_release` and `consumed_in_release` to be either `None` or strings, but not silently absent.
- Require `root_cause` to be in `{srs, architecture, development, prd-exception}` or `None`; when `expect_root_cause` is supplied, keep the existing exact-match check.

### Low

#### L1 — Ambiguous / non-localized dev rollback paths do not record the documented planning-route note

**Location**: `skills/_shared/dev_workflow/progress_state.py:1322`

**Issue**: When `bug-start --root-cause development` produces no rollback decisions, `apply_bug_start()` always emits only:

```text
summary = bug=<path> root_cause=development Bug Flow entered
result = current_stage=development
next = development-write Change Mode
```

The CLI warns on stderr only for `unable_to_localize` at `skills/workflow-protocol/scripts/progress.py:933`; it does not warn for `classification == "ambiguous"`, and neither case leaves a persistent history/result/next note that `development-planning-write` must replan or route the fix.

This diverges from the planning docs:

- `skills/workflow-protocol/references/command-reference.md:375` says `unable to localize` or missing affected-task data must reject or enter a development planning route and record a history requirement for `development-planning-write`.
- `skills/workflow-protocol/references/command-reference.md:380` says ambiguous classification must keep task state unchanged and write that a planning route is needed.
- `docs/implementation/task6_plan_20260507.md:208` says ambiguous classification should append a history entry stating that `development-planning-write` must replan/route.

**Impact**: State remains replay-safe, but the durable audit trail loses the reason why no task rollback occurred. A future agent reading only `progress-history.md` / `progress.md` may see `current_stage=development` and unchanged verified tasks without the documented instruction to route via planning.

**Recommendation**: Add a small, replay-neutral planning note when `root_cause == "development"` and the computed rollback list is empty due to ambiguous classification, `unable to localize`, or skipped affected tasks. For example, include `route=development-planning-write` or prose in `history_result` / `history_next`; add CLI/test coverage for both ambiguous and unable-to-localize cases. This can be fixed with M1 or deferred if Phase 6.2 will refactor the shared rollback helper immediately.

---

## 3. Cross-Doc Consistency Check

| Source / Contract | Status | Notes |
|-------------------|--------|-------|
| Phase 5.4 closure | ✓ | `_validate_bug_path_shape` is reused by `apply_bug_start`; prior BUG path safety and canonical summary-token invariants are preserved. |
| `command-reference.md §8 bug-start` | ⚠ | Main preconditions and mutations are implemented; planning-route history note for ambiguous / unable-to-localize dev rollback is missing (L1). |
| `command-reference.md §10 bug-close` | ✓ | Active bug flow + `current_stage=testing` are enforced by `apply_bug_close`; latest test-report pass is enforced by CLI preflight. |
| Stage 4 task table Gap-3 | ✓ | `verifying -> code-revising` is accepted only with `verification_status in {fail, partial}` on forward path. |
| Stage 4 task table Gap-4 | ✓ | `update --task` still rejects Gap-4 transitions; `apply_bug_start` applies only supplied protected rollback tuples for development root cause. |
| `task6_progress_py_prerequisites.md §1-§5` | ⚠ | Gap-3 and Gap-4 mechanics align; ambiguous/no-localize planning-route note is incomplete (L1). |
| `frontmatter-schema.md §3.4 / required fields table` | ⚠ | BUG path shape and type/root_cause checks exist, but BUG ID regex/path matching and required nullable-field presence are not enforced (M1). |
| `workflow-protocol/SKILL.md` command matrix | ✓ / scoped | The skill describes the final 12-command matrix; Phase 6.1 intentionally exposes 9 commands and leaves `bug-rework`, incident commands, and `update --advance` to later sub-phases. |
| Phase 6.2+ boundaries | ✓ | No `bug-rework`, `incident-*`, `update --advance`, terminal-event, or consistency implementation is required or treated as a finding here. |

---

## 4. Checklist Results

### A. `progress_artifacts.py` 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `_BUG_PATH_RE` matches progress_state policy | ✓ | Both use `^docs/bug/BUG-\d{3}\.md$`; dedupe can be optional cleanup. |
| `test-report` path template uses existing loader path | ✓ | `load_test_report()` delegates to `load_artifact_frontmatter()`. |
| `load_test_report` rejects missing / wrong type / wrong release / bad status | ✓ | Covered by tests and loader behavior. |
| `load_bug_report` canonical path / type / expected root cause | ✓ | Implemented. |
| `load_bug_report` required BUG field validation | ⚠ | M1: required key presence and `bug_id` regex/path match are incomplete. |
| `parse_bug_triage_analysis` required section / affected line / token validation | ✓ | Missing section, missing line, bad task token, dedupe, and unable-to-localize are covered. |
| Classification test/source/ambiguous logic | ✓ | Keyword family intersection maps to ambiguous as expected. |
| Test coverage | ⚠ | Current tests cover many loader cases but do not cover malformed `bug_id`, missing nullable keys, or root_cause enum without `expect_root_cause`. |

### B. `apply_bug_start` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| Active project / review iteration guard | ✓ | Inherits `_validate_review_iteration_value` and project-state checks. |
| Release/stage/sub_state/bug_flow gates | ✓ | Requires `release_state=active`, `current_stage=testing`, `sub_state=review-passed`, and inactive bug flow. |
| Canonical BUG path and root cause map | ✓ | `_validate_bug_path_shape` plus `{srs, architecture, development}` map are enforced. |
| Mutation scope | ✓ | Mutates bug_flow, current_stage, sub_state, review_iteration, updated; preserves unrelated fields. |
| Gap-4 rollback tuple validation | ✓ | Non-dev rollback rejects, stale old status rejects, non-protected transition rejects, task IDs are checked. |
| History canonical tokens | ✓ | `bug=` and `root_cause=` are in summary; rollback token is replay-friendly when present. |
| Ambiguous/no-localize planning instruction | ⚠ | L1: no persistent history/result/next note when no rollback is applied. |

### C. `apply_bug_close` 状态机

| Check | Result | Notes |
|-------|--------|-------|
| Active project / review iteration guard | ✓ | Implemented. |
| Active bug_flow and testing stage gates | ✓ | Implemented. |
| Retest-pass responsibility split | ✓ | CLI checks latest test-report pass; apply function remains pure state machine. |
| Mutation scope | ✓ | Clears bug_flow and updates `updated`; current_stage and sub_state are preserved. |
| History result diagnostic | ✓ | Result includes closed bug path and root cause. |

### D. `apply_update_task` Gap-3 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `verifying -> code-revising` recognized as Gap-3 | ✓ | Accepted outside normal transitions. |
| Gap-4 still rejected via `update --task` | ✓ | Error directs caller to Phase 6 `bug-start` / `bug-rework`. |
| Forward artifact check | ✓ | `verification_status in {fail, partial}` required when `validate_artifacts=True`. |
| Replay bypass | ✓ | `validate_artifacts=False` still applies state-machine transition without reading current artifacts. |
| Test coverage | ✓ | Unit and CLI tests cover fail/partial/pass/missing and replay bypass. |

### E. `progress_replay.py` 扩展

| Check | Result | Notes |
|-------|--------|-------|
| `bug-start` / `bug-close` handlers registered | ✓ | `supported_events()` returns 11 events. |
| `bug-start` token requirements | ✓ | Missing `bug` or `root_cause` rejects. |
| Rollback token parse | ✓ | Parses semicolon list; malformed token rejects before mutation. |
| Replay does not read BUG / test-report | ✓ | Tests confirm empty tempdir replay succeeds for bug-start. |
| Unsupported-event message updated | ✓ | Message states Phase 6.1 support and later `bug-rework` / incident / advance phases. |

### F. `progress.py` CLI

| Check | Result | Notes |
|-------|--------|-------|
| `bug-start` root containment | ✓ | Resolves user path and rejects outside `--root`; loader then enforces canonical shape. |
| BUG load + root_cause match | ⚠ | Root cause match exists, but M1 shows BUG identity/required nullable fields are under-validated. |
| Dev triage and rollback computation | ✓ | Test/source/ambiguous/unable branches route to rollback tuple or empty tuple. |
| Unable-to-localize warning | ✓ | Stderr warning is present. |
| Ambiguous planning warning/history | ⚠ | No stderr warning and no durable history note (L1). |
| `bug-close` latest test-report pass | ✓ | CLI requires pass before applying state-machine close. |
| argparse / dispatcher | ✓ | `bug-start` and `bug-close` are present; missing required bug-start args return 2. |

### G. Tests 设计

| Check | Result | Notes |
|-------|--------|-------|
| Pure state-machine unit tests | ✓ | `apply_bug_start`, `apply_bug_close`, and Gap-3 unit tests avoid CLI where appropriate. |
| CLI temp-dir isolation | ✓ | `test_progress_bug_flow.py` uses `TemporaryDirectory` and fake clock patching. |
| Synthetic replay handlers keep progress/history aligned | ✓ | Test-only handler pattern matches Phase 5.3/5.4 style and avoids false M1 failures. |
| Bug-start happy paths | ✓ | SRS, architecture, development test/source/ambiguous/unable cases covered. |
| Bug-start rejection paths | ⚠ | Good coverage for state/path/root-cause mismatch; add malformed BUG frontmatter cases from M1. |
| Bug-close rejection paths | ✓ | No active flow, failing report, and missing report covered. |
| Gap-3 CLI tests | ✓ | fail/partial/pass and unchanged-file rejection covered. |
| Replay tests | ✓ | Supported events exact-set and bug-flow replay cases covered. |

### H. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| Existing Phase 1-5 tests | ✓ | Full suite now 553 tests OK. |
| M1 replay consistency pipeline | ✓ | `bug-start`, `bug-close`, and Gap-3 update paths use `_run_update_pipeline`. |
| M2 review_iteration entry guard | ✓ | New apply functions and Gap-3 path enforce the cap. |
| `progress_lock.py` / `progress_history.py` | ✓ | Not touched in this phase. |
| Existing commands preserved | ✓ | init/query/recover/update/release/bug-intake behavior remains covered. |
| `_validate_bug_path_shape` inherited | ✓ | Used by `apply_bug_start` and existing bug-intake/release-start path. |

### I. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| `_compute_bug_start_rollback` future reuse | ⚠ | It is currently CLI-local; Phase 6.2 may want to move it to a shared helper to avoid duplicate `bug-rework` logic. |
| Keyword lists | ✓ | MVP lists are simple and testable; extensibility is acceptable. |
| `_check_gap_3_verification_fail` naming | ✓ | Clear counterpart to `_require_verification_pass`. |
| Rollback token format | ✓ | `Tn:old->new` is grep-friendly and replayable. |
| Public/private helper boundaries | ⚠ | `_BUG_PATH_RE` duplicated across modules; optional cleanup only. |

### J. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| `command-reference.md §8` mutation table | ✓ | Main bug-start mutation aligns. |
| `command-reference.md §8` dev planning-route notes | ⚠ | L1. |
| `command-reference.md §10` bug-close | ✓ | Aligns. |
| Stage 4 Gap-3 artifact condition | ✓ | Aligns. |
| Prerequisites Gap-3/4 | ⚠ | Mechanics align; history note for ambiguous/no-localize is incomplete. |
| `frontmatter-schema.md §3.4` bug-report fields | ⚠ | M1. |

---

## 5. Open Questions / Assumptions

- I assume Phase 6.1 intentionally does not require `bug-start` to validate latest `test-report verification_status in {fail, partial}`; testing-write / bug-triage caller flow owns that decision, while `bug-start` owns stage/sub_state/root_cause gates.
- I assume `load_test_report()` and `load_bug_report()` are intentionally thin and do not need full doc-guardian Class 1-7 validation. M1 only asks for required identity/schema-shape checks needed before state-machine mutation.
- I assume the final 12-command matrix in `workflow-protocol/SKILL.md` is aspirational across Phase 6.1-6.4; the current 9-command CLI is acceptable for this sub-phase.
- I recommend moving `_compute_bug_start_rollback()` to shared code only when Phase 6.2 starts implementing `bug-rework`, not as a prerequisite by itself.

---

## 6. Recommendation

**(B) fix before Phase 6.2**.

Required before Phase 6.2:

1. Fix **M1** in `load_bug_report()` and add tests for malformed/mismatched `bug_id`, missing `target_release`, missing `consumed_in_release`, and invalid nullable field types.
2. Re-run full tests and compile checks.

Can be fixed with M1 or deferred to early Phase 6.2 if the rollback helper is being refactored anyway:

- **L1**: persist the planning-route note for ambiguous / unable-to-localize / skipped dev rollback cases, ideally in `history_result` or `history_next` so replay remains unaffected.

Estimated repair path:

- M1 is a small loader/test patch in `skills/_shared/dev_workflow/progress_artifacts.py` and `tests/test_progress_artifacts.py` / `tests/test_progress_bug_flow.py`.
- L1 is a small CLI/state outcome messaging patch plus two assertions in the ambiguous and unable-to-localize CLI tests.
