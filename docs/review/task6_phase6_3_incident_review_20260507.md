# Task 6 Phase 6.3 `incident-start` / `incident-resolve` Review — 2026-05-07

## 1. Executive Summary

**Overall judgment**: Phase 6.3 is largely implemented correctly: the incident state-machine functions, replay handlers, action-aware terminal gate, CLI integration, doc-guardian double-safety hook, and tests are all present and the full suite is green. I found one medium issue in `incident-resolve` preflight path safety/ordering and three low issues in exit-code and documentation alignment.

**Findings**: 0 High / 1 Medium / 3 Low.

**Phase 6.4 readiness**: **Blocked until the Medium finding is fixed.** The fix is small and localized: validate/contain `progress.md.incident_report_path` before `validate_doc()` or `read_markdown()` in `cmd_incident_resolve`. I also recommend fixing the invalid-action exit code before Phase 6.4 because it is a one-line contract mismatch plus test update.

**Validation run during review**:

```bash
python3 -m unittest tests.test_apply_incident_start tests.test_apply_incident_resolve tests.test_progress_incident tests.test_progress_replay tests.test_progress_recover
# Ran 131 tests in 0.939s — OK

python3 -m unittest discover -s tests
# Ran 713 tests in 5.970s — OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 12 subcommands, including incident-start / incident-resolve
```

I also checked that no repo-root `progress.md` / `progress-history.md` exists after the test run.

## 2. Findings

### Medium

#### M1 — `incident-resolve` reads/validates `incident_report_path` before applying the incident path-shape and containment guard

**Location**: `skills/workflow-protocol/scripts/progress.py:1392`

**Issue**: `cmd_incident_resolve` pulls `incident_report_path` from `progress.md` and immediately calls `validate_doc(incident_path, root)` (`progress.py:1402`) and then `read_markdown(root / incident_path)` (`progress.py:1415`). The canonical `_validate_incident_path_shape` guard is only reached later inside `apply_incident_resolve` during `_run_update_pipeline` (`skills/_shared/dev_workflow/progress_state.py:1892`), after those file reads have already happened. A corrupted or hand-edited `progress.md` can therefore make `incident-resolve` attempt to read an absolute path or traversal path before the state-machine rejects it.

**Impact**: This violates the Phase 6.3 precondition that `incident_path` be shape-valid before doc validation, weakens the repo-root containment defense, and creates a preflight read outside the intended project boundary for out-of-band edited `progress.md`. It is especially relevant because earlier phases intentionally hardened BUG path handling against exactly this class of corrupted-state input.

**Recommendation**: After `incident_path` is read from `progress.md` and before `validate_doc()` or `read_markdown()`, run `_validate_incident_path_shape(incident_path)` and an explicit containment check:

```python
try:
    _validate_incident_path_shape(incident_path)
    (root / incident_path).resolve().relative_to(root.resolve())
except (ProgressStateError, ValueError) as exc:
    ... return 1
```

Add CLI tests for absolute, traversal, and non-canonical `progress.md.incident_report_path` values that assert `validate_doc` is not called and `progress.md` remains byte-identical. For consistency, consider applying the explicit shape guard to `incident-start` resolved paths before `validate_doc()` too, although `incident-start` already resolves user-supplied paths under `--root`.

### Low

#### L1 — Invalid `incident-resolve --action` uses exit 2 instead of the documented workflow-validation exit 1

**Location**: `skills/workflow-protocol/scripts/progress.py:1358`; test currently pins the opposite at `tests/test_progress_incident.py:351`

**Issue**: The Phase 6.3 prompt and the argparse comment say missing required arguments should exit 2, while an unsupported action value should be a workflow validation error (exit 1). The implementation returns 2 for `--action retry`.

**Impact**: Runtime state is safe, but callers cannot distinguish a missing CLI argument from a supplied-but-invalid workflow value according to the documented exit-code contract.

**Recommendation**: Change the invalid-action branch to `return 1` and update `IncidentArgparseTests.test_incident_resolve_invalid_action_returns_2` to expect 1. Keep missing `--action` at exit 2.

#### L2 — Incident history templates in `command-reference.md` omit required canonical replay tokens

**Location**: `skills/workflow-protocol/references/command-reference.md:512` and `skills/workflow-protocol/references/command-reference.md:607`

**Issue**: The implementation emits replay-canonical summaries:

- `incident-start`: `bug=<path> incident=<path> root_cause=prd-exception PRD exception triggered` (`skills/_shared/dev_workflow/progress_state.py:1830`)
- `incident-resolve`: `action=<action> incident=<path> Incident resolved` (`skills/_shared/dev_workflow/progress_state.py:1966`)

But the reference templates still show `incident-start` as only `PRD exception triggered`, and `incident-resolve` as only `action=<...>` without the `incident=` token. Replay requires `bug=` / `incident=` for start and `action=` / `incident=` for resolve.

**Impact**: The implementation is correct, but the primary command reference can mislead future maintainers or hand-authored history fixtures into producing entries that replay rejects.

**Recommendation**: Update §11/§12 append-history blocks to show the exact canonical summary tokens used by `apply_incident_start` and `apply_incident_resolve`, plus the current result/next prose shape.

#### L3 — Cross-doc state applicability for `incident-start` is inconsistent with the implementation and tests

**Location**: `skills/workflow-protocol/SKILL.md:132`; related table row at `skills/workflow-protocol/references/command-reference.md:667`

**Issue**: `apply_incident_start` intentionally does not gate on `current_stage`, and the Phase 6.3 unit tests assert it can trigger from `testing`, `development`, or `delivery` (`tests/test_apply_incident_start.py:136`). However, the SKILL command matrix and protected-field table still describe `incident-start` as a `current_stage==testing` transition.

**Impact**: Runtime follows the Phase 6.3 prompt, but routing documentation points agents toward a narrower precondition than the script enforces. That can cause inconsistent operator behavior around PRD-exception escalation outside Stage 5.

**Recommendation**: Pick one source of truth. If Phase 6.3's broader behavior is intended, update SKILL.md and the command-reference protected-field row to say `project_state=active`, no active bug flow/incident, valid PRD-exception BUG, valid incident report. If testing-only is intended instead, add a `current_stage=='testing'` gate to `apply_incident_start` and adjust the “3 stage” unit test; based on the prompt, the doc update is the expected path.

## 3. Cross-Doc Consistency Check

- **`command-reference.md` §11 incident-start**: Mutation aligns with implementation for opening `bug_flow`, setting `workflow_incident_active`, storing `incident_report_path`, and routing to `workflow-incident-analysis`. The append-history template is stale (L2), and the protected transition table still implies testing-only (L3).
- **`command-reference.md` §12 incident-resolve**: The three action mutation tables align with `apply_incident_resolve`: continue clears incident/bug flow and resumes testing; abort/reconstruct close the release, clear protected fields, and set terminal project states. The history template omits the `incident=` token (L2).
- **`frontmatter-schema.md` §3.4 / §4.4 / §4.6**: The implementation matches the workflow-incident schema. `validate_doc` enforces `incident_id`, `triggered_by_bug`, `triggered_in_release`, and `resolution_action`; `cmd_incident_start` cross-checks `triggered_by_bug == BUG bug_id`; `cmd_incident_resolve` cross-checks `resolution_action == --action` and `status == review-passed`.
- **`directory-layout.md`**: `docs/incident/{incident_id}.md` matches `_INCIDENT_PATH_RE = ^docs/incident/INCIDENT-\d{3}\.md$` and doc-guardian's `^INCIDENT-\d{3}$` ID policy.
- **`task6_plan_20260507.md` §13**: Phase split is respected. Phase 6.3 implements incident lifecycle only; `update --advance` and `validate.py consistency` remain Phase 6.4.
- **`skills/workflow-protocol/SKILL.md` command matrix**: 12-command count and incident command names match the CLI. The `incident-start` applicable-state row is narrower than implementation/tests (L3).

## 4. Checklist Results

### A. `_validate_doc_path_shape` refactor + `_validate_incident_path_shape`

- ✓ Shared helper preserves the five BUG rules: non-empty string, no backslashes, not absolute, no `.` / `..` / empty segments, regex match.
- ✓ Error messages include the caller label (`BUG` / `INCIDENT`) and expected pattern.
- ✓ `_INCIDENT_PATH_RE` matches the doc-guardian/directory-layout 3-digit zero-padded INCIDENT policy.
- ✓ Existing BUG path callers still pass the full suite, indicating the `_validate_bug_path_shape` refactor is transparent.
- ⚠️ CLI `incident-resolve` imports `_validate_incident_path_shape` but does not apply it before reading the path from `progress.md` (M1).

### B. `apply_incident_start` state machine

- ✓ Enforces active project, review-iteration guard, canonical BUG path, canonical INCIDENT path, inactive bug flow, and no existing workflow incident.
- ✓ Mutation opens `bug_flow` with literal `root_cause='prd-exception'`, sets incident fields, routes to `workflow-incident-analysis`, and updates `updated`.
- ✓ Preserves `sub_state`, `review_iteration`, `unresolved_bugs`, artifacts, and other unrelated fields.
- ✓ History summary includes `bug=`, `incident=`, and `root_cause=prd-exception` canonical tokens.
- ✓ Tests cover happy path, preserved substate/iteration, multiple starting stages, rejects, frozen outcome, and the “prd-exception not in bug-start root-cause map” contract.

### C. `apply_incident_resolve` state machine

- ✓ Enforces review-iteration guard, canonical incident path shape, active workflow incident, incident path equality, and action enum membership.
- ✓ Correctly does not gate on `project_state == active`, matching the Phase 6.3 design note.
- ✓ `continue` clears incident and bug flow, resumes `testing/review-passed`, resets iteration, and leaves project/release state active.
- ✓ `abort` closes the release, sets `project_state=aborted`, `release_close_reason=incident-abort`, clears current/substate/bug/incident fields, and is terminal.
- ✓ `reconstruct` uses the same cleanup shape with `project_state=reconstructing` and `release_close_reason=incident-reconstruct`, and history next mentions a new directory.
- ✓ `is_terminal` maps correctly: continue false, abort/reconstruct true.
- ✓ Tests cover action branches, cleanup completeness, rejects, frozen outcome, and terminal-flag mapping.

### D. `progress_replay` Option B action-aware terminal gate

- ✓ `TERMINAL_EVENTS = {'incident-resolve'}` and `TERMINAL_INCIDENT_ACTIONS = frozenset({'abort', 'reconstruct'})` are present.
- ✓ Dispatch loop runs the handler first, then reparses `action=` and only flips `seen_terminal` for terminal actions.
- ✓ `READ_ONLY_EVENTS` remains empty.
- ✓ Incident handlers do not read BUG/INCIDENT files and require the state-changing tokens needed by replay.
- ✓ `_HANDLERS` has 14 events and unsupported-event messaging is updated to Phase 6.3.
- ⚠️ `incident-start` does not require the `root_cause=prd-exception` token during replay; this is harmless because the state mutation is literal, but it is worth noting if the canonical-token contract is later tightened.

### E. `cmd_incident_start` / `cmd_incident_resolve` CLI

- ✓ `validate_doc(path, root) -> list[str]` is a single in-process import wrapper around `validate.validate_file`, making tests easy to mock.
- ✓ Argparse exposes `incident-start --bug --report --agent` and `incident-resolve --action --agent`.
- ✓ `incident-start` resolves and contains both paths under `--root`, double-validates BUG and INCIDENT docs, checks BUG root cause, checks INCIDENT `triggered_by_bug`, and writes via `_run_update_pipeline`.
- ✓ `incident-resolve` checks active incident, validates INCIDENT doc, checks `resolution_action` and `status`, and writes via `_run_update_pipeline`.
- ❌ `incident-resolve` validates/reads the incident path from `progress.md` before path-shape/containment checks (M1).
- ⚠️ Invalid `--action` returns exit 2 instead of exit 1 (L1).

### F. Tests design

- ✓ Unit tests are pure state-machine tests; CLI tests use `TemporaryDirectory`, `_FakeClock`, and synthetic replay handlers consistent with Phase 6.1/6.2 patterns.
- ✓ Happy CLI paths use real valid BUG/INCIDENT docs so `validate.py file` runs for real.
- ✓ M6 double-safety reject paths patch `progress.validate_doc` at the intended single seam.
- ✓ CLI coverage includes argparse, start happy/rejects, three resolve actions, resolve rejects, terminal semantics, recover roundtrips, and lock blocking.
- ✓ Replay coverage includes incident start, missing tokens, continue non-terminal, abort/reconstruct terminal behavior, action rejects, and no artifact reads.
- ⚠️ Missing focused CLI coverage for corrupted `progress.md.incident_report_path` shape/containment before `validate_doc` (M1), and invalid action currently asserts the wrong exit code (L1).

### G. Existing invariants

- ✓ Full suite passes: 713 tests OK; compileall is clean.
- ✓ Both incident commands use `_run_update_pipeline`, preserving M1 replay consistency, lock/atomic writes, and history append semantics.
- ✓ Both apply functions preserve the review-iteration entry guard where required.
- ✓ Existing `init`, `query`, `recover`, `update`, release, and bug-flow behavior remains covered by the full test suite.
- ✓ No repo-root workflow files are created by the tests.
- ⚠️ Preflight path handling for `incident-resolve` should be moved before doc reads to fully preserve the prior path-hardening invariant (M1).

### H. Design / maintainability

- ✓ Direct in-process `validate_doc` import is reasonable for Phase 6.3: no subprocess/PATH handling, same interpreter, simple mock seam.
- ✓ Lazy import inside `validate_doc` is acceptable and keeps startup cheap.
- ✓ Keeping incident start/resolve logic explicit rather than abstracting with bug-start is readable; the fields and semantics differ enough to justify separate functions.
- ✓ `apply_incident_resolve` if/elif action branches are clear and easy to compare with §12 mutation tables.
- ✓ Private `_INCIDENT_RESOLVE_ACTIONS` is acceptable because the CLI intentionally avoids argparse `choices=`; if more modules need it later, public export can be added then.
- ⚠️ Consider documenting the doc-guardian direct-import dependency in SKILL/handoff prose when docs are open.

### I. Cross-doc consistency

- ✓ Frontmatter schema and directory-layout path rules align with the validators and CLI cross-checks.
- ✓ Phase 6.3 / 6.4 boundary is respected.
- ⚠️ Command-reference history snippets omit canonical replay tokens (L2).
- ⚠️ SKILL.md / protected transition table testing-only wording conflicts with implementation/tests allowing incident-start from multiple stages (L3).
- ⚠️ `load_bug_report(..., expect_root_cause=...)` diagnostic now mentions bug-start/bug-rework but not incident-start; cosmetic only, but worth folding into future diagnostics polish.

## 5. Open Questions / Assumptions

- **Assumption**: The Phase 6.3 prompt's broader `incident-start` state-machine behavior (no `current_stage` gate; tests for multiple stages) is the intended source of truth, despite older SKILL/table wording that says testing-only.
- **Open question**: Should replay require and validate `root_cause=prd-exception` for `incident-start` summaries, or is that token purely documentary because the mutation always writes the literal value?
- **Open question**: Should `_INCIDENT_RESOLVE_ACTIONS` become public if Phase 6.4 or docs tooling needs to share the enum, or is the current private constant sufficient until a second runtime caller appears?
- **Open question**: Should `validate_doc` catch unexpected `ImportError` / exceptions from doc-guardian and turn them into exit-1 issue strings, or should such failures remain hard crashes because they indicate an installation/programmer error?

## 6. Recommendation

**(B) fix before Phase 6.4**

Must fix before Phase 6.4:

1. **M1**: In `cmd_incident_resolve`, validate `_validate_incident_path_shape` and root containment before `validate_doc()` or `read_markdown()`. Add regression tests proving invalid/corrupt `incident_report_path` does not trigger doc reads and leaves `progress.md` unchanged.
2. **L1**: Change invalid `incident-resolve --action <bad>` from exit 2 to exit 1 and update the pinned test.

Can be deferred to Phase 7/documentation polish if necessary:

- **L2**: Update command-reference history snippets to include canonical replay tokens.
- **L3**: Align SKILL.md / protected transition wording with the chosen `incident-start` stage applicability.
- Cosmetic diagnostic: include `incident-start` in the `load_bug_report(expect_root_cause=...)` error text.

Estimated fix path: small, localized patch in `skills/workflow-protocol/scripts/progress.py` plus 2-4 CLI tests; documentation-only updates for L2/L3 when the docs write set is open.
