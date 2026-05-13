# Task 6 Phase 6.4 Review — `update --advance` + `validate.py consistency`

Review date: 2026-05-07
Reviewer: Codex
Scope: Phase 6.4 implementation only, per `docs/review/claude_review_prompt_task6_phase6_4_advance_consistency_20260507.md`.

## 1. Executive Summary

Recommendation: **(B) fix before Task 6 closure**.

Phase 6.4 is broadly implemented in the intended shape: `apply_update_advance` is a state-machine-only layer, replay registers `update-advance` as the 15th event, `validate.py consistency` now performs required-artifact existence + `validate_file` checks, and the CLI wires `update --advance` into the existing update mutex group. The full suite and compile checks pass locally:

```bash
python3 -m unittest discover -s tests
# Ran 773 tests in 6.412s — OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

However, I found one blocking functional bug: the delivery-stage E-dimension path calls `load_artifact_frontmatter(doc_type="installation-result")`, but the loader cannot resolve that doc type, so a valid delivery stage cannot advance to retrospective. I also found two robustness/invariant issues and two documentation/help consistency issues.

Findings distribution:

- High: 1
- Medium: 2
- Low: 2

Task 6 should not close until at least H1 is fixed and covered by a delivery-stage CLI test. I also recommend fixing M1 before closure because it weakens the lock invariant for the new `--advance` path.

## 2. Findings

### H1 — Delivery `update --advance` is blocked because `installation-result` is not a supported loader type

- Location: `skills/workflow-protocol/scripts/progress.py:584`
- Location: `skills/_shared/dev_workflow/progress_artifacts.py:52`
- Issue: `_check_p6_dim_e()` checks Stage 6 by calling `load_artifact_frontmatter(root, doc_type="installation-result", release=release)`, but `progress_artifacts._PATH_TEMPLATES` only includes `task-breakdown`, Stage 4 per-task artifacts, and `test-report`. It does not include `installation-result`, so `_format_path()` raises `ProgressArtifactError("unknown doc_type: 'installation-result'")` before it can read the valid file.
- Evidence: a direct call with a valid `docs/release0.1/delivery/installation_result.md` returns `cannot load installation-result: unknown doc_type: 'installation-result'`.
- Impact: delivery -> project-retrospective cannot succeed through the Phase 6.4 CLI forward path. This violates the explicit Phase 6.4 requirement that delivery checks `installation-result.verification_status == pass` and then advances.
- Recommendation: add `"installation-result": "docs/release{release}/delivery/installation_result.md"` to `progress_artifacts._PATH_TEMPLATES` or refactor `load_artifact_frontmatter()` to use the canonical `schema.TYPE_PATHS`. Add at least one delivery happy-path CLI test and one delivery E reject test so this path cannot regress.

### M1 — P6 A/B/E checks run before acquiring `.progress.lock`, so they can validate stale state

- Location: `skills/workflow-protocol/scripts/progress.py:443`
- Location: `skills/workflow-protocol/scripts/progress.py:470`
- Location: `skills/workflow-protocol/scripts/progress.py:631`
- Issue: `_do_update_advance()` reads `progress.md` and runs required-artifact derivation, missing-file checks, `validate_doc()`, and `_check_p6_dim_e()` before `_run_update_pipeline()` acquires `.progress.lock` and re-reads the current state. The locked pipeline then applies `apply_update_advance()` to the later state, not necessarily the state that A/B/E validated.
- Impact: in concurrent agent usage, process A can validate P6 for stage X, process B can legally mutate the project to stage Y before process A enters `_run_update_pipeline()`, and process A can then advance stage Y without having run P6 for stage Y. M1 replay consistency will not catch this if process B's history is valid, because replay will match the final history/state. This weakens the lock/atomicity invariant specifically for the new `--advance` path.
- Recommendation: execute P6 A/B/E inside the same locked critical section and against the re-read `progress_doc.frontmatter`. One low-impact design is to extend `_run_update_pipeline()` with an optional locked preflight callback that receives the locked frontmatter and can return/raise before `compute_outcome`; another is to move the P6 checks into the `compute_outcome` lambda for `update-advance`, before calling `apply_update_advance()`. Add a regression test that proves `validate_doc`/P6 preflight runs under the lock against the re-read state, or, more importantly, that a state change between initial read and lock acquisition cannot bypass P6 for the later stage.

### M2 — `validate.py consistency` can raise an uncaught exception for structurally incomplete `progress.md`

- Location: `skills/doc-guardian/scripts/validate.py:700`
- Location: `skills/_shared/dev_workflow/artifacts.py:147`
- Issue: `check_consistency()` catches `ArtifactError` from `get_required_artifacts()`, but `progress_from_mapping()` directly indexes required keys such as `scenario`, `current_stage`, and `release`. If `progress.md` parses as YAML but is missing `scenario` or `release`, `check_consistency()` raises `KeyError` instead of returning a consistency issue and causing CLI exit 1.
- Evidence: a `progress.md` containing only `current_stage: prd-inception` and `release: "0.1"` raises `KeyError: 'scenario'` from `validate.check_consistency(root)`.
- Impact: corrupted or manually truncated progress frontmatter can produce a Python traceback rather than the specified `validate.py consistency` behavior of reporting inconsistency with exit 1. This also leaves similar risk in `_do_update_advance()` because it catches only `ArtifactError` around resolver derivation.
- Recommendation: either validate the minimal resolver inputs before calling `get_required_artifacts()` or catch `KeyError`, `TypeError`, and `AttributeError` around resolver derivation and convert them to a single issue/error message. Mirror the same defensive handling in `_do_update_advance()` so malformed-but-parseable progress cannot crash the CLI.

### L1 — `validate.py` help/docstrings still describe implemented/deferred subcommands inaccurately

- Location: `skills/doc-guardian/scripts/validate.py:8`
- Location: `skills/doc-guardian/scripts/validate.py:9`
- Location: `skills/doc-guardian/scripts/validate.py:750`
- Location: `skills/doc-guardian/scripts/validate.py:755`
- Issue: the module docstring still says both `all` and `consistency` are deferred to Phase 5/6, and argparse help says `all` / `consistency` are "deferred to Phase 5/6" even though `consistency` is now implemented and `all` is explicitly Phase 7.
- Impact: user-facing help contradicts current script behavior and Phase 6.4 scope. This is not a runtime blocker, but it weakens the handoff/CLI contract.
- Recommendation: update the docstring and subparser help to say `consistency` is Class 8 cross-progress validation and `all` is deferred to Phase 7.

### L2 — workflow-protocol SKILL P6 matrix still points Dimension A at `progress.md artifacts:`

- Location: `skills/workflow-protocol/SKILL.md:160`
- Issue: the P6 matrix says Dimension A checks all paths in `artifacts:`, while the Phase 6.4 implementation and `command-reference.md` use `required-artifacts.md` + `get_required_artifacts(...)` as the fact source. `skills/workflow-protocol/SKILL.md:170` partially corrects this by naming `required-artifacts.md`, but the matrix row itself remains contradictory.
- Impact: agents reading the SKILL matrix can conclude that `progress.md.artifacts` is authoritative, which conflicts with the Phase 6.4 decision to leave the `artifacts:` dict unchanged on advance.
- Recommendation: update the matrix row to say Dimension A derives required paths from `skills/doc-guardian/references/required-artifacts.md` via the shared resolver. This can be folded into Phase 7 documentation polish if H1/M1 are fixed first, but it should be tracked because the review explicitly asks for SKILL matrix consistency.

## 3. Cross-Doc Consistency Check

- `skills/workflow-protocol/references/command-reference.md` §2.2 vs implementation: mostly aligned on explicit `--advance`, required-artifact resolver, A/B/E before apply, next-stage mutation, and `update --event` not auto-validating. The delivery E implementation currently fails because the shared loader lacks `installation-result` support (H1). The Stage 4 per-task `verification_result.md` re-read described in the reference is intentionally out of Phase 6.4 per the review prompt, so I did not count it as a finding.
- `docs/implementation/task6_plan_20260507.md` §7 / §10 vs implementation: §10 resolver inputs and no-`eval` Condition DSL are consumed as intended. `validate.py consistency` implements the Phase 6.4 artifact existence/validity subset; broader Class 8 status compatibility and task-count checks appear in planning prose but are treated here as deferred/assumed out of current scope per the prompt.
- `skills/doc-guardian/references/required-artifacts.md` §12 vs implementation: `get_required_artifacts()` is the actual fact source for both `update --advance` and `validate.py consistency`; `workflow-incident-analysis` is skipped by `check_consistency()` as requested. The core algorithm matches, with the robustness caveat in M2.
- `skills/workflow-protocol/SKILL.md` command/P6 matrix vs implementation: command list includes `update --advance`; terminal event policy remains unchanged. The P6 Dimension A row still mentions `artifacts:` as the source, which conflicts with the resolver-based implementation and should be corrected (L2).
- `skills/doc-guardian/SKILL.md` vs implementation: command matrix lists `validate.py consistency`, `file`, `ids`, and `all`; the implemented `all` remains deferred to Phase 7, which matches the prompt but should ideally be called out in CLI help and future docs polish.

## 4. Checklist Results

### A. `apply_update_advance` State Machine

Status: ✓

- ✓ Enforces active project, review_iteration cap, no active workflow incident, next-stage existence, gated approved sub_state, development all-verified surrogate, non-gated review-passed, and testing active bug-flow rejection.
- ✓ Mutates only `current_stage`, `sub_state`, `review_iteration`, and `updated`; nested fields such as `artifacts`, `bug_flow`, `development_state`, and release/project fields are preserved.
- ✓ Development branch rejects empty task map and lists non-verified task IDs sorted.
- ✓ Retrospective rejection points to `release-close`.
- ✓ History summary includes canonical `from=` / `to=` tokens plus `Stage advance`; result/next match the requested contract.

### B. `_apply_update_advance_handler` Replay Handler

Status: ✓

- ✓ Registers `update-advance` as the 15th supported replay event and ignores `root` without artifact reads.
- ✓ Requires `from=` and `to=` token presence.
- ✓ Calls `apply_update_advance(state, now=entry.timestamp)` and compares derived `current_stage` to the `to=` token with a "history may be corrupt" error.
- ✓ Replay tests cover happy path, missing token, `to=` mismatch, and replay-skips-artifacts.
- Note: `from=` is presence-checked but not compared to the pre-advance state. That matches the prompt's explicit guard requirement (`to=`), but it is a possible future hardening option.

### C. `validate.py consistency`

Status: ⚠️

- ✓ Reads `progress.md`, reports missing file / malformed frontmatter, requires `current_stage`, skips `workflow-incident-analysis`, derives required artifacts, de-duplicates paths, checks existence, and prefixes `validate_file()` issues.
- ✓ CLI returns 0 for no issues and 1 for inconsistencies; `all` returns 2 with Phase 7 wording.
- ⚠️ Structurally incomplete but parseable `progress.md` can still raise uncaught exceptions through `get_required_artifacts()` (M2).
- ⚠️ Help/docstrings still say `consistency` is deferred (L1).

### D. `_do_update_advance` CLI

Status: ❌

- ✓ Adds `--advance` as a flag in the existing `update` mutex group and dispatches after `--event` / `--task`.
- ✓ Runs A missing-path aggregation, B per-file issue aggregation, E stage-specific helper, and then `_run_update_pipeline(event_name="update-advance")`.
- ✓ Testing E checks latest test-report `verification_status == pass`; development E is intentionally delegated to the apply surrogate.
- ❌ Delivery E cannot pass because `installation-result` is not supported by `load_artifact_frontmatter()` (H1).
- ⚠️ A/B/E run before the lock and before the pipeline re-read, so they can validate stale state under concurrency (M1).

### E. Tests Design

Status: ⚠️

- ✓ New tests are isolated with `tempfile.TemporaryDirectory()` and use established `_FakeClock` / synthetic replay-handler patterns.
- ✓ Full suite reports 773 tests passing.
- ✓ Replay event count and synthetic unsupported event sample are updated.
- ⚠️ CLI tests cover representative happy paths but miss delivery -> retrospective with a passing `installation-result`, which would have caught H1.
- ⚠️ Lock test verifies the lock eventually blocks, but not that P6 preflight is performed under the lock or against the locked/re-read state (M1).

### F. Existing Invariants

Status: ⚠️

- ✓ Full test suite and compileall pass.
- ✓ Existing `init`, `query`, `recover`, `update --event`, `update --task`, release, bug, and incident tests remain green.
- ✓ `TERMINAL_EVENTS` remains `{"incident-resolve"}`; `update-advance` is non-terminal.
- ⚠️ `_run_update_pipeline` invariants are inherited only after A/B/E preflight; the new preflight itself is outside the lock/re-read critical section (M1).

### G. Design / Maintainability

Status: ⚠️

- ✓ `AdvanceOutcome` + `apply_update_advance` match the shape of existing state-machine outcomes.
- ✓ `_check_p6_dim_e` is a reasonable helper boundary for testing/delivery/development branching.
- ⚠️ Reusing `progress_artifacts.load_artifact_frontmatter()` is maintainable, but the shared loader currently has a Stage-4/Stage-5-only path table, causing H1. Either expand the table or centralize path rendering on `schema.TYPE_PATHS`.
- ✓ Lazy imports in `validate.py` and `progress.py` follow existing style.

### H. Cross-Doc Consistency

Status: ⚠️

- ✓ Primary behavior aligns with command-reference and required-artifacts for resolver-driven P6 checks.
- ✓ Phase 6.4 deferrals named in the prompt were not treated as blockers.
- ⚠️ workflow-protocol SKILL Dimension A still references `artifacts:` instead of the required-artifacts resolver (L2).
- ⚠️ `validate.py` help/docstrings are stale for `consistency` and Phase 7 `all` (L1).

### I. Phase 6.4 Acceptance

Status: ❌

- ✓ `progress.py update --help` exposes `--advance`.
- ✓ `validate.py consistency --help` works.
- ✓ `supported_events()` returns 15 and recover roundtrip is tested.
- ✓ Full suite and compileall pass.
- ❌ Stage 6 delivery -> project-retrospective cannot currently pass E-dimension because of H1, so Phase 6.4 acceptance is not complete.

## 5. Open Questions / Assumptions

- I accepted the prompt's decision that `progress.md artifacts:` is not reinitialized on advance in Phase 6.4. L2 is only about stale SKILL wording, not a request to implement artifacts mutation.
- I accepted the prompt's decision that Stage 4 -> Stage 5 does not re-read each `verification_result.md` in `_check_p6_dim_e`; the apply surrogate and prior task transitions are the Phase 6.4 gate.
- `from=` token validation is presence-only in replay. This is consistent with the prompt, but a future hardening pass could compare it to the pre-advance `state["current_stage"]` for stronger audit integrity.
- The broader Class 8 consistency concept in `task6_plan`/`doc-guardian SKILL` mentions doc status compatibility and task-count checks. I treated those as out of Phase 6.4 unless the owner wants `validate.py consistency` to grow beyond the required-artifact algorithm now.

## 6. Recommendation

**(B) fix before Task 6 closure**.

Must fix before Task 6 closure:

1. H1: make delivery E-dimension load `installation-result` correctly and add delivery CLI tests.
2. M1: move P6 A/B/E checks under the lock/re-read path, or otherwise prove stale-state validation cannot advance a later stage.

Strongly recommended before closure:

1. M2: convert structurally incomplete `progress.md` inputs into clean exit-1 diagnostics in both `validate.py consistency` and `progress.py update --advance`.

Can defer to Phase 7 documentation polish if time-boxed:

1. L1: refresh `validate.py` help/docstrings.
2. L2: refresh SKILL P6 matrix wording from `artifacts:` to required-artifacts resolver.

Estimated fix path:

- H1: small code change plus 2 tests, likely <1 hour.
- M1: moderate refactor of `_run_update_pipeline` or `update-advance` preflight placement plus concurrency/stale-state regression test, likely 1-2 hours.
- M2: small defensive handling plus 2 tests, likely <1 hour.
