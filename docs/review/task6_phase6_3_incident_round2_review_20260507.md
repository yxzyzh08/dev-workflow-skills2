# Task 6 Phase 6.3 Round 2 Review - Incident Lifecycle Fixes

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Regression review of the Task 6 Phase 6.3 round 2 fixes, focused on the five Round 1 findings in `docs/review/task6_phase6_3_incident_review_20260507.md`.

---

## 1. Executive Summary

Round 2 fixes the Round 1 blocking issue and the requested Low/cosmetic items. The important safety ordering now holds: both `incident-resolve` and the hardened `incident-start` path-shape guards run before doc-guardian validation can read the target BUG/INCIDENT files, and invalid `incident-resolve --action <bad>` now exits as workflow validation (`1`) rather than argparse usage (`2`).

Findings distribution for this round:

| Severity | Count | Blocks Phase 6.4? | Summary |
|----------|-------|-------------------|---------|
| High | 0 | No | No root-escape, data-loss, replay divergence, or terminal-state regression found. |
| Medium | 0 | No | Round 1 M1 is fixed. |
| Low | 1 | No | One command-reference sentence overstates current replay enforcement of `root_cause=prd-exception`; this is the inherited open question, not a Phase 6.4 blocker. |

Recommendation: **(A) round 2 fixes complete; accept and proceed to Phase 6.4 (`update --advance` + `validate.py consistency`)**.

Validation performed during review:

```bash
python3 -m unittest tests.test_apply_incident_start tests.test_apply_incident_resolve tests.test_progress_incident tests.test_progress_replay tests.test_progress_recover
# Ran 137 tests in 1.067s - OK

python3 -m unittest discover -s tests
# Ran 719 tests in 6.039s - OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py incident-resolve --action retry
# exit 1; stderr contains "continue / abort / reconstruct"

test ! -e progress.md && test ! -e progress-history.md
# no repo-root progress artifacts
```

---

## 2. Findings

### Low

#### L1 - `command-reference.md` says replay requires `root_cause=prd-exception`, but replay currently does not enforce that token

**Location**: `skills/workflow-protocol/references/command-reference.md:512`; implementation reference at `skills/_shared/dev_workflow/progress_replay.py:500`

**Issue**: The new §11 append-history intro says `root_cause=prd-exception` is a readability token and that replay does not strongly validate the value but still requires the token to be present. The actual replay handler only treats missing `bug=` and `incident=` as errors; it never reads or checks `tokens.get("root_cause")` before calling `apply_incident_start()`.

**Impact**: Runtime is safe because forward `apply_incident_start()` always emits `root_cause=prd-exception`, and replay mutates `bug_flow.root_cause` to the literal `prd-exception` regardless of the summary text. The risk is documentation/maintenance drift: a future maintainer or hand-written history fixture may assume replay rejects an `incident-start` entry that has `bug=` and `incident=` but lacks `root_cause=prd-exception`, when it is currently accepted. This is the same inherited open question from Round 1, so I do not treat it as a Phase 6.4 blocker.

**Recommendation**: Either adjust the §11 sentence to say `root_cause=prd-exception` is part of the canonical forward summary but is not currently replay-required, or close the inherited open question by adding an explicit replay check for `root_cause == "prd-exception"` plus a regression test. The one-line doc wording fix is enough if strict replay enforcement is intentionally deferred.

---

## 3. Round 1 Findings Status

| Round 1 Finding | Status | Evidence | Grade |
|-----------------|--------|----------|-------|
| M1 - `cmd_incident_resolve` read/validated `incident_report_path` before path-shape + containment checks | Fixed | `cmd_incident_resolve` now validates `_validate_incident_path_shape(incident_path)` at `skills/workflow-protocol/scripts/progress.py:1420` before `validate_doc()` at `skills/workflow-protocol/scripts/progress.py:1443` and `read_markdown(root / incident_path)` at `skills/workflow-protocol/scripts/progress.py:1455`; containment uses `relative_to(root.resolve())` at `skills/workflow-protocol/scripts/progress.py:1433`. | Complete |
| L1 - invalid `incident-resolve --action retry` returned exit 2 | Fixed | Invalid supplied values now return `1` at `skills/workflow-protocol/scripts/progress.py:1373`, while missing `--action` still returns `2` at `skills/workflow-protocol/scripts/progress.py:1365`; `tests/test_progress_incident.py:351` pins the new exit code. | Complete |
| L2 - command-reference incident history snippets omitted canonical replay tokens | Fixed with one wording note | §11 now shows `bug=... incident=... root_cause=prd-exception PRD exception triggered` at `skills/workflow-protocol/references/command-reference.md:515`; §12 now shows `action=... incident=... Incident resolved` at `skills/workflow-protocol/references/command-reference.md:617`. The remaining wording note is L1 in this review. | Functionally complete |
| L3 - SKILL/protected transition docs described `incident-start` as testing-only | Fixed | SKILL.md now states `project_state==active AND bug_flow.active==false AND workflow_incident_active==false AND BUG.root_cause==prd-exception` with no `current_stage` gate at `skills/workflow-protocol/SKILL.md:132`; the protected-field table says Phase 6.3 no longer gates `current_stage` at `skills/workflow-protocol/references/command-reference.md:684`. | Complete |
| Cosmetic - `load_bug_report(expect_root_cause=...)` diagnostic omitted `incident-start` | Fixed | The mismatch message now lists bug-start, bug-rework, and incident-start callers at `skills/_shared/dev_workflow/progress_artifacts.py:405`. | Complete |

---

## 4. Cross-Doc Consistency Check

| Area | Status | Notes |
|------|--------|-------|
| `command-reference.md` §11 append-history template | OK / WARN | The emitted template matches `apply_incident_start()` summary/result/next at `skills/_shared/dev_workflow/progress_state.py:1830`; L1 notes only the sentence that overstates root-cause replay enforcement. |
| `command-reference.md` §12 append-history template | OK | The template includes `action=` and `incident=`, and the three result/next prose variants match `apply_incident_resolve()` at `skills/_shared/dev_workflow/progress_state.py:1927` and `skills/_shared/dev_workflow/progress_state.py:1953`. |
| `command-reference.md` protected-field table | OK | `incident-start` no longer claims `current_stage=testing`; it lists active project, inactive bug flow, inactive incident, and BUG `root_cause=prd-exception`. |
| `workflow-protocol/SKILL.md` command matrix | OK | The `incident-start` row is aligned with implementation/tests: no `current_stage` gate, active project, inactive bug flow, inactive incident, PRD-exception BUG. |
| `progress.py` CLI behavior | OK | `incident-start` and `incident-resolve` preflight docs align with the code: path shape, containment, doc-guardian, frontmatter cross-check, then `_run_update_pipeline()`. |
| Replay docs and handlers | OK / inherited open | `incident-start` and `incident-resolve` replay do not read BUG/INCIDENT files and require the critical state tokens. Whether `root_cause=prd-exception` should also be replay-required remains inherited open question H2. |

---

## 5. Checklist Results

### A. M1 Fix Completeness

| Check | Result | Notes |
|-------|--------|-------|
| `incident-resolve` parses `progress.md`, checks active incident, then validates `incident_report_path` shape before target reads | OK | Shape guard is at `progress.py:1420`; `validate_doc()` and INCIDENT `read_markdown()` are later. |
| Containment check happens before `validate_doc()` | OK | `(root / incident_path).resolve().relative_to(root.resolve())` runs at `progress.py:1433` before doc-guardian. |
| Corrupt-path regression coverage: absolute / traversal / wrong directory / 4-digit ID | OK | `IncidentResolveCorruptIncidentPathTests` covers all four at `tests/test_progress_incident.py:677`. |
| Corrupt-path tests spy on `validate_doc` and assert no calls | OK | `_run_resolve_with_validate_spy()` records calls at `tests/test_progress_incident.py:715`; each corrupt-path test asserts `[]`. |
| Corrupt-path tests assert `progress.md` byte-identical after reject | OK | Each case compares against the corrupted pre-run text. |
| `incident-start` runs shape guards on both resolved paths before `validate_doc()` | OK | `_validate_bug_path_shape(rel_bug)` and `_validate_incident_path_shape(rel_incident)` run at `progress.py:1258`; doc validation starts at `progress.py:1274`. |
| `incident-start` in-tree non-canonical path tests avoid `validate_doc` | OK | `IncidentStartCorruptPathPreflightTests` covers non-canonical BUG and INCIDENT paths at `tests/test_progress_incident.py:794`. |

### B. L1 Exit Code Contract

| Check | Result | Notes |
|-------|--------|-------|
| Missing `--action` exits 2 | OK | `cmd_incident_resolve()` returns `2` for missing required CLI argument at `progress.py:1365`. |
| Supplied invalid `--action retry` exits 1 | OK | Invalid supplied value returns `1` at `progress.py:1373`; local spot check confirmed exit 1. |
| Comment explains usage vs workflow validation boundary | OK | The comment cites the Phase 5.1 round 2 M2 contract and release-start/init scenario behavior. |
| Regression test pins exit 1 and enum text | OK | `tests/test_progress_incident.py:351` asserts exit 1 and `continue / abort / reconstruct`. |

### C. L2 Canonical Token Documentation

| Check | Result | Notes |
|-------|--------|-------|
| §11 summary contains `bug=`, `incident=`, `root_cause=prd-exception`, and `PRD exception triggered` | OK | Present at `command-reference.md:515`. |
| §11 result/next match implementation | OK | `current_stage=workflow-incident-analysis; bug_flow.active=true root_cause=prd-exception` and `workflow-evolution fills INCIDENT body` match `progress_state.py:1837`. |
| §11 explains BUG/INCIDENT files are forward-validated and replay does not re-read them | OK | Present at `command-reference.md:526`. |
| §12 summary contains `action=`, `incident=`, and `Incident resolved` | OK | Present at `command-reference.md:617`. |
| §12 explains continue/abort/reconstruct result and next prose | OK | Present at `command-reference.md:627` and matches `apply_incident_resolve()`. |
| Replay-token wording is exact | WARN | §11 overstates `root_cause=prd-exception` replay enforcement; see L1. |

### D. L3 SKILL.md / Protected-Field Table Alignment

| Check | Result | Notes |
|-------|--------|-------|
| SKILL.md command matrix removes `current_stage==testing` from `incident-start` | OK | `skills/workflow-protocol/SKILL.md:132`. |
| SKILL.md lists active project, inactive bug flow, inactive incident, and PRD-exception BUG | OK | Same row. |
| Protected-field table says Phase 6.3 does not gate `current_stage` | OK | `skills/workflow-protocol/references/command-reference.md:684`. |
| Docs align with `apply_incident_start()` preconditions | OK | `apply_incident_start()` validates active project, inactive bug flow, inactive incident, BUG path, and INCIDENT path without a stage gate. |
| Unit tests close the doc/implementation loop | OK | `test_can_trigger_from_any_stage_and_substate` in `tests/test_apply_incident_start.py` remains green. |

### E. Cosmetic Diagnostic

| Check | Result | Notes |
|-------|--------|-------|
| `load_bug_report` mismatch message lists bug-start | OK | `progress_artifacts.py:409`. |
| Message lists bug-rework | OK | `progress_artifacts.py:409`. |
| Message lists incident-start and literal `prd-exception` | OK | `progress_artifacts.py:410`. |
| Existing tests are not coupled to old wording | OK | `tests/test_progress_artifacts.py:429` asserts only durable fragments (`root_cause`, actual value), not the caller prose. |

### F. Existing Invariants

| Check | Result | Notes |
|-------|--------|-------|
| Focused incident/apply/replay/recover tests pass | OK | 137 tests OK. |
| Full test suite passes | OK | 719 tests OK. |
| Compileall is clean | OK | `python3 -m compileall -q ...` completed successfully. |
| No repo-root workflow artifacts leaked | OK | No `progress.md` or `progress-history.md` exists at repo root after validation. |
| Round 1 state-machine/replay invariants remain intact | OK | `progress_state.py` incident apply logic and `progress_replay.py` terminal handling remain behaviorally consistent and covered by full tests. |
| M6 double-safety still composes with M1 preflight | OK | New order is shape -> containment -> doc-guardian -> frontmatter cross-check -> `_run_update_pipeline()`. |

### G. Round 2 Scope Control

| Check | Result | Notes |
|-------|--------|-------|
| No Phase 6.4 design work introduced | OK | No `update --advance` or `validate.py consistency` behavior is added here. |
| Incident apply state machine not reworked | OK | The review found no behavioral expansion beyond the requested CLI/doc/test hardening. |
| Replay terminal gate not reworked | OK | `TERMINAL_EVENTS` / action-aware dispatch remain the Round 1 accepted design. |
| Docs changes stay in incident-start / incident-resolve rows/templates | OK | The reviewed doc edits target the Round 1 L2/L3 areas. |

---

## 6. Open Questions / Assumptions

These carry forward from Round 1; I am not adding new design questions.

- **Resolved by round 2**: The broader Phase 6.3 `incident-start` state-machine behavior is now the documented source of truth. Docs and tests agree that `current_stage` is not a gate.
- **Still open, non-blocking**: Should replay require and validate the `root_cause=prd-exception` token for `incident-start` summaries? Current replay only requires `bug=` and `incident=`; L1 notes a doc sentence that should either be softened or backed by an implementation check.
- **Still open, non-blocking**: Should `_INCIDENT_RESOLVE_ACTIONS` become public if Phase 6.4 or docs tooling needs to share the enum?
- **Still open, non-blocking**: Should `validate_doc` catch unexpected `ImportError` or doc-guardian exceptions and convert them to exit-1 issue strings, or should those remain hard failures as installation/programmer errors?

---

## 7. Recommendation

**(A) round 2 fixes complete; accept and proceed to Phase 6.4 (`update --advance` + `validate.py consistency`)**.

Required before Phase 6.4: none from this review.

Optional cleanup, not blocking Phase 6.4:

1. Update `skills/workflow-protocol/references/command-reference.md:512` to avoid saying replay requires `root_cause=prd-exception`, unless the team chooses to close the inherited open question by enforcing that token in replay.
