# Task 6 Phase 6.4 Round 2 Review - `update --advance` + `validate.py consistency`

Review date: 2026-05-07
Reviewer: Codex
Scope: Round 2 fixes for `docs/review/task6_phase6_4_advance_consistency_review_20260507.md` findings H1 / M1 / M2 / L1 / L2 only.

## 1. Executive Summary

Recommendation: **(A) round 2 fixes complete; Task 6 implementation closes; ready for Phase 7 / next-task scope**.

Round 2 addresses all five round 1 findings. I found no remaining blocking or non-blocking findings in the reviewed scope.

Remaining findings distribution:

- High: 0
- Medium: 0
- Low: 0

Validation run locally:

```bash
python3 -m unittest discover -s tests
# Ran 781 tests in 6.512s - OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/doc-guardian/scripts/validate.py --help
# Shows file / ids / all (deferred to Phase 7) / consistency (Class 8)

python3 skills/workflow-protocol/scripts/progress.py --help
# Shows 12 top-level subcommands; update still owns --event / --task / --advance
```

I also spot-checked the prior H1 and M2 failure modes directly:

- `_check_p6_dim_e("delivery", ...)` with a valid `installation_result.md` now returns `None` instead of `unknown doc_type`.
- `validate.check_consistency(root)` with parseable but missing `scenario` returns a clean issue string containing `progress.md is structurally incomplete` instead of raising `KeyError`.

## 2. Findings

No findings.

## 3. Round 1 Findings Status Table

| Round 1 ID | Status | Evidence | Grade |
|------------|--------|----------|-------|
| H1 delivery E-dim `installation-result` loader missing | Fixed | `skills/_shared/dev_workflow/progress_artifacts.py:67` registers `installation-result`; `skills/workflow-protocol/scripts/progress.py:589` loads it; `tests/test_progress_update_advance.py:370` covers delivery happy path and `tests/test_progress_update_advance.py:522` covers fail rejection. | Complete |
| M1 P6 A/B/E ran before lock / stale-state race | Fixed | `_do_update_advance` is now a thin wrapper at `skills/workflow-protocol/scripts/progress.py:433`; `_advance_compute_outcome` runs inside locked pipeline at `skills/workflow-protocol/scripts/progress.py:444`; `_run_p6_advance_preflight` owns P6 at `skills/workflow-protocol/scripts/progress.py:476`; locked-state regressions are in `tests/test_progress_update_advance.py:674` and `tests/test_progress_update_advance.py:706`. | Complete |
| M2 structurally incomplete progress could raise `KeyError` | Fixed | progress.py catches structural resolver failures at `skills/workflow-protocol/scripts/progress.py:507`; validate.py catches the same class at `skills/doc-guardian/scripts/validate.py:717`; regressions are in `tests/test_progress_update_advance.py:772`, `tests/test_validate_consistency.py:261`, `tests/test_validate_consistency.py:271`, and `tests/test_validate_consistency.py:285`. | Complete |
| L1 stale `validate.py` docstring/help text | Fixed | module docstring now documents `consistency` as Class 8 at `skills/doc-guardian/scripts/validate.py:8` and `all` as Phase 7 at `skills/doc-guardian/scripts/validate.py:13`; subparser help is updated at `skills/doc-guardian/scripts/validate.py:767` and `skills/doc-guardian/scripts/validate.py:771`. | Complete |
| L2 SKILL P6 matrix pointed A at `progress.md artifacts:` | Fixed | Dimension A now names required-artifacts.md + `get_required_artifacts(...)` and explicitly says not `progress.md artifacts:` at `skills/workflow-protocol/SKILL.md:160`; B/C/D/E rows are aligned at `skills/workflow-protocol/SKILL.md:161`, `skills/workflow-protocol/SKILL.md:162`, `skills/workflow-protocol/SKILL.md:163`, and `skills/workflow-protocol/SKILL.md:164`. | Complete |

## 4. Cross-Doc Consistency Check

- `command-reference.md` section 2.2 vs implementation: The `update --advance` flow remains resolver-driven and validates A/B/E before state mutation. Round 2 moves those checks inside the locked pipeline, which strengthens the command-reference atomicity intent without changing user-visible semantics. Delivery E now checks `installation-result.verification_status == pass` as specified.
- `skills/workflow-protocol/SKILL.md` P6 matrix vs implementation: The matrix now matches the actual implementation: A derives paths from `required-artifacts.md` via `get_required_artifacts`, B runs `validate.py file` on those paths, C/D are indirectly enforced by `apply_update_advance` sub_state gates, and E maps to the Stage 4 task surrogate / Stage 5 test-report / Stage 6 installation-result split.
- `validate.py` docstring/help vs behavior: The module docstring and subcommand help now describe `consistency` as implemented Class 8 and `all` as explicitly deferred to Phase 7. CLI behavior matches: `consistency` returns 0/1 based on issues; `all` returns 2 with Phase 7 wording.
- `required-artifacts.md` vs implementation: The shared resolver remains the P6 fact source for both `update --advance` and `validate.py consistency`; no new hardcoded artifact list was introduced in workflow-protocol except the existing thin E-dimension loaders.
- Phase boundaries: Round 2 does not implement `validate.py all`, managed-project smoke, `artifacts:` reinitialization, or per-task verification_result re-read on Stage 4 advance. These remain outside Phase 6.4 per the prompt.

## 5. Checklist Results

### A. H1 Fix Completeness

Status: OK

- OK `installation-result` is registered in `_PATH_TEMPLATES` with `docs/release{release}/delivery/installation_result.md`.
- OK `_check_p6_dim_e("delivery", ...)` can load a valid installation-result and returns pass only for `verification_status == "pass"`.
- OK delivery -> project-retrospective happy path is covered by `test_advance_delivery_to_retrospective_with_passing_installation_result`.
- OK delivery E reject is covered by `test_delivery_advance_rejects_with_failing_installation_result`, including byte-identical `progress.md` preservation.
- OK existing advance CLI tests still pass.

### B. M1 Lock Contract

Status: OK

- OK `_do_update_advance` delegates to `_run_update_pipeline` without pre-reading `progress.md` or running P6 outside the lock.
- OK `_advance_compute_outcome` validates `current_stage`, runs P6 only for stages in `NEXT_STAGE`, then calls `apply_update_advance`.
- OK `_run_p6_advance_preflight` aggregates all A missing paths, all B per-file issues, and the E verification failure into `ProgressStateError` messages that the pipeline prints without mutation.
- OK P6 runs against the freshly locked frontmatter because `compute_outcome` is invoked inside `_run_update_pipeline` after acquiring `progress_lock` and re-reading `progress.md`.
- OK regressions cover the pure locked-state missing-artifact case and a spy-lock mutation that proves the post-lock state is used.

### C. M2 Defensive Handling

Status: OK

- OK progress.py catches `KeyError`, `TypeError`, and `AttributeError` around required-artifact derivation and converts them to `ProgressStateError("progress.md is structurally incomplete; ...")`.
- OK validate.py catches the same structural failures and returns a single issue string so the CLI exits 1 cleanly.
- OK both progress.py and validate.py have regression coverage for parseable but structurally incomplete progress frontmatter.
- OK the diagnostic includes the underlying exception repr, e.g. `KeyError('scenario')`, which is specific enough for operator repair.

### D. L1 Doc/Help Accuracy

Status: OK

- OK top module docstring lists `file`, `ids`, `consistency`, and `all` with current implementation status.
- OK Class index includes Class 8 consistency.
- OK `consistency` subparser help says Class 8 cross-progress check with required-artifact existence + per-file validity.
- OK `all` subparser help and runtime message both say deferred to Phase 7.
- OK `validate.py --help` output exposes the corrected subcommand help.

### E. L2 SKILL.md P6 Matrix Alignment

Status: OK

- OK Dimension A names `required-artifacts.md` + shared resolver as the fact source and explicitly excludes `progress.md artifacts:` as the P6 source.
- OK Dimension B scopes validation to paths derived by A.
- OK Dimensions C and D document the indirect `apply_update_advance` sub_state enforcement.
- OK Dimension E matches implementation: Stage 4 task-state surrogate, Stage 5 test-report, Stage 6 installation-result.
- OK The SKILL matrix now aligns with command-reference section 2.2 and the round 2 code.

### F. Round 1 Existing (A) Areas Preserved

Status: OK

- OK `apply_update_advance` state machine remains unchanged and its 22 unit tests pass.
- OK `_apply_update_advance_handler`, `_HANDLERS`, `supported_events()`, and `TERMINAL_EVENTS` remain unchanged from round 1 and pass replay tests.
- OK `cmd_update` dispatcher and argparse mutex group continue to support `--event`, `--task`, and `--advance`.
- OK Existing Phase 1-5 and Phase 6.1-6.3 test coverage remains green in the full 781-test suite.

### G. Round 2 Scope Control

Status: OK

- OK Round 2 stays focused on H1/M1/M2/L1/L2 fixes.
- OK It does not add Phase 7 features such as `validate.py all` or managed-project smoke.
- OK It does not reopen incident lifecycle, terminal semantics, replay event design, or the round 1 accepted state-machine/replay handler behavior.
- OK It does not mutate repo-root `progress.md` / `progress-history.md`; post-test root remains clean.

### H. Regression Coverage Completeness

Status: OK

- OK H1 has two regressions: delivery happy and delivery fail.
- OK M1 has two regressions: locked-state P6 A failure and spy-lock stale-snapshot guard.
- OK M2 has four regressions across progress.py and validate.py paths.
- OK L1 and L2 are document/help fixes verified by inspection and CLI help output.
- OK Full suite count increased to 781 and remains green.

## 6. Open Questions / Assumptions

- `from=` token strict comparison remains a possible future hardening option. Round 2 did not change replay handler behavior, and this is not blocking Task 6 closure.
- Broader Class 8 checks such as doc-status compatibility and task-count consistency remain Phase 7 territory unless the user expands scope. Round 2 correctly stays with required-artifact existence + per-file validity.

## 7. Recommendation

**(A) round 2 fixes complete; Task 6 implementation closes; ready for Phase 7 / next-task scope**.

No further Task 6 closure fixes are required from this review.
