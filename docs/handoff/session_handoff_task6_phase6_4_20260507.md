# Session Handoff — Task 6 Phase 6.4 Start (`update --advance` + `validate.py consistency`)

**Handoff Date**: 2026-05-07
**Handoff By**: Claude (claude-opus-4-7[1m])
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Current Task**: Task 6 implementation — Phase 6 Bug Flow / Incident / Advance
**Current Phase**: **Phase 6.3 closed (A) round 2 + 1 non-blocking Low (already fixed); ready to start Phase 6.4 (final phase 6 sub-batch).**
**Important Status**: 719 tests pass; compileall clean; 12 progress.py subcommands. Phase 6 sub-phases 1-3 all (A). Phase 6.4 is the FINAL Phase 6 sub-batch and closes Task 6 implementation.

---

## 0. New Session Read Order

Read these in order before coding:

1. `docs/handoff/session_handoff_task6_phase6_4_20260507.md` (this handoff)
2. `docs/review/task6_phase6_3_incident_round2_review_20260507.md` — Phase 6.3 closure (A) + 1 non-blocking Low (already fixed; do NOT re-open)
3. `docs/implementation/task6_plan_20260507.md` §6 (Gap-3/4/5 — Phase 6.1/6.2 reference) + §7 (validate.py plan, Class 8 = consistency) + §10 (Required Artifacts and Condition DSL) + §13 (phase boundaries)
4. `skills/workflow-protocol/references/command-reference.md` §2.2 (`--advance` 子选项 — primary spec source) + 状态机表 通用 sub_state 转换 (line ~615)
5. `skills/doc-guardian/references/required-artifacts.md` §1-§12 (P6 fact source; condition DSL; consistency algorithm at line ~393)
6. `skills/_shared/dev_workflow/conditions.py` (Phase 2 — whitelist DSL parser, NO `eval`)
7. `skills/_shared/dev_workflow/artifacts.py` (Phase 2 — `get_required_artifacts(progress, root)` + `ArtifactSpec` + `progress_from_mapping`)
8. `skills/doc-guardian/scripts/validate.py` `consistency` subcommand (line ~691, currently returns 2 with deferred-explanation; Phase 6.4 to fully implement)
9. `skills/_shared/dev_workflow/progress_state.py` `apply_update_event` / `apply_update_task` (Phase 5.2/5.3 — `--advance` is structurally similar but P6-driven)
10. `skills/workflow-protocol/scripts/progress.py` `cmd_update` mutex group (`--event` / `--task`; Phase 6.4 adds `--advance`)
11. Phase 6.3 review prompts under `docs/review/claude_review_prompt_task6_phase6_3_*.md` (style reference for 6.4 review prompt)

Optional background:

- `skills/doc-guardian/scripts/changelog.py` (Phase 3 — change log validation; not directly used by 6.4 but consistency check might compose with it)
- `skills/_shared/dev_workflow/progress_artifacts.py` `load_test_report` / `load_artifact_frontmatter` (Phase 5.3+ — loaders that 6.4's `--advance` E-dimension check can reuse)
- `docs/handoff/session_handoff_task6_phase6_3_20260507.md` (recent reference for handoff format / watch-points style)

---

## 1. Critical Constraints

- This repo is the skill-implementation repo, **not** a workflow-managed project. Never create / mutate repo-root `progress.md` / `progress-history.md`. They MUST not exist after any test run.
- The current git working tree is largely untracked (`docs/`, `skills/`, `tests/`, helper start scripts). Never delete / clean / reset / revert these.
- All tests use `tempfile.TemporaryDirectory()` fixtures.
- Phase 6 sub-phase boundaries (user-confirmed 4-split):
  - Phase 6.1 ✅ closed (A): bug-start + bug-close + Gap-3 update --task
  - Phase 6.2 ✅ closed (A) + 3 Low polish landed: bug-rework + Gap-4/5 reuse
  - Phase 6.3 ✅ closed (A) round 2 + 1 non-blocking Low fixed: incident-start + incident-resolve + TERMINAL_EVENTS + action-aware terminal gate
  - **Phase 6.4 (this session)**: `update --advance` (P6 matrix) + `validate.py consistency`
- The 14 supported replay events (Phase 6.3 final state) are: `init / write-complete / review-issues / review-passed / human-confirmed / update-task / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework / incident-start / incident-resolve`. Phase 6.4 adds `update-advance` (the canonical replay event name TBD; suggest `update-advance` since `update --event` already uses an event-name-keyed handler factory). After 6.4, total = 15.
- `TERMINAL_EVENTS = {"incident-resolve"}` with action-aware gate (continue non-terminal; abort/reconstruct terminal). Phase 6.4 does NOT touch this.
- Replay design contract: replay validates state-machine legality only; it does NOT re-read artifact files / required-artifacts derivation. The forward path is the gatekeeper for artifact state at write time (replay-skips-artifacts invariant). `--advance` should follow the same pattern: forward path runs P6 matrix; replay re-derives the post-advance state purely from canonical history tokens.
- Phase 6.4 is the **last** Phase 6 sub-batch. After (A), Task 6 implementation closes and a Task 6 closure handoff should follow (or the user decides next-task scope).

---

## 2. Current Repository State

Project root: `/home/cgs/github_projects/dev-workflow-skills2`

Key files (after Phase 6.3 round 2 + non-blocking Low fix):

- `skills/_shared/dev_workflow/`
  - `atomic.py` (Phase 2)
  - `frontmatter.py` (Phase 2)
  - `markdown.py` (Phase 2)
  - `changelog.py` (Phase 3)
  - `schema.py` (Phase 2)
  - `progress_lock.py` (Phase 5.1)
  - `progress_history.py` (Phase 5.1; field whitelist `agent / result / next`)
  - `progress_replay.py` (Phase 6.3; **14 handlers**; `TERMINAL_EVENTS = {"incident-resolve"}` with action-aware gate)
  - `progress_artifacts.py` (Phase 5.3+; loaders + BUG triage parser; expect_root_cause error message lists 3 callers)
  - `progress_state.py` (Phase 6.3+; all `apply_*` state-machine functions including 2 incident apply functions; `compute_dev_bug_rollback` + `_validate_doc_path_shape` shared helpers)
  - **`conditions.py`** (Phase 2 — whitelist DSL parser; no eval; lookup via `evaluate(ast, progress)` against 6 allowed variables)
  - **`artifacts.py`** (Phase 2 — `get_required_artifacts(progress, root) -> list[ArtifactSpec]` + `progress_from_mapping(progress) -> ProgressLike` + `condition_variables(progress, root)`)
- `skills/doc-guardian/scripts/`
  - `validate.py` (Phase 3 — classes 1-7 + `ids` + `file`; `consistency` subcommand currently returns exit 2 with deferred-explanation message; **Phase 6.4 to implement**)
  - `changelog.py` (Phase 3)
  - `status_transition.py` (Phase 4)
- `skills/workflow-protocol/scripts/`
  - `progress.py` (Phase 6.3+; **12 subcommands**; `_DOC_GUARDIAN_SCRIPTS` sys.path bootstrap + `validate_doc(path, root)` direct-import helper for M6 double-safety)

Current test runtime baseline:

```bash
python3 -m unittest discover -s tests
# Ran 719 tests in 6.5s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

No repo-root `progress.md` / `progress-history.md` exists (intentional).

---

## 3. Completed Work Before This Handoff

### Phases 1-4 (closed)

- Phase 1: docs alignment
- Phase 2: shared foundation (frontmatter / markdown / atomic / **conditions / artifacts** / progress_state base / schema)
- Phase 3: `changelog.py` + `validate.py file/ids` (consistency deferred to 6.4)
- Phase 4: `status_transition.py`

### Phase 5 (closed; 4 sub-phases)

- 5.1: progress.py foundation (`init / query / recover` + lock / history / replay)
- 5.2: `update --event` (4 events with M1 history-parse-and-replay-consistency + M2 review_iteration ≤ 7 entry guard)
- 5.3: `update --task` (Stage 4 task state machine; `validate_artifacts=True` forward / `False` replay)
- 5.4: `release-close` + `release-start` (BUG fan-out via `extra_writes_factory`) + `bug-intake`

### Phase 6.1 (closed; A)

- `bug-start` (3 root_cause routing + Gap-4 dev auto-rollback) + `bug-close` + `update --task` Gap-3 + Phase 6.1 round 2 fixes

### Phase 6.2 (closed; A + 3 Low polish landed)

- `bug-rework` (Gap-5) + `compute_dev_bug_rollback` shared helper + 3 Low fixes (canonical token doc / replay handler comment / load_bug_report message generalization)

### Phase 6.3 (closed; A round 2 + 1 non-blocking Low fixed)

- `incident-start` (PRD-exception entry; opens bug_flow + workflow-incident state atomically) + `incident-resolve` (3 actions: continue / abort / reconstruct) + `TERMINAL_EVENTS` first activation with **Option B action-aware terminal gate**
- Round 2 fixes: M1 path-shape preflight on incident-resolve + incident-start; L1 invalid --action exit 2→1; L2 canonical token doc; L3 SKILL/table stage applicability fix; cosmetic load_bug_report 3rd caller; round 2 L1 doc wording (root_cause= replay enforcement clarification)
- progress.py first time imports doc-guardian validate.py (`validate_doc(path, root)` direct-import; tests mock via `patch.object(progress, "validate_doc", ...)`)

---

## 4. Phase 6.4 Scope — `update --advance` + `validate.py consistency`

### 4.1 Spec source of truth

- `skills/workflow-protocol/references/command-reference.md` §2.2 (`--advance` 子选项)
- `docs/implementation/task6_plan_20260507.md` §10 (Condition DSL + required-artifacts resolver — Phase 2 already implemented this; 6.4 only wires it) + §7 (validate.py consistency = Class 8) + §13 phase boundary
- `skills/doc-guardian/references/required-artifacts.md` §1-§12 (P6 fact source; YAML map; condition DSL; consistency algorithm sketch)

### 4.2 `update --advance` command shape

```bash
progress.py update --advance [--agent <agent>]
```

`--advance` joins the existing `--event` / `--task` mutually-exclusive group on `update`.

### 4.3 P6 matrix (per command-reference.md §2.2)

5 dimensions per stage:

| Dim | Check | How |
|-----|-------|-----|
| **A** Required artifacts exist | Each derived ArtifactSpec.path file exists | `os.path.exists(root / spec.path)` |
| **B** doc-guardian validate | Each artifact passes `validate.py file` | Reuse `validate_doc(path, root)` (already imported in progress.py for Phase 6.3) |
| **C** Review approved | `*-review` skill returned `review-passed` for current stage | Read most recent matching `review-passed` event in progress-history.md (or rely on current `sub_state==review-passed`) |
| **D** Human gate (PRD/SRS/Arch only) | history has `human-confirmed` after the latest `review-passed`; doc frontmatter `status==approved` | Already enforced by `apply_update_event(human-confirmed)` Phase 5.2 — gate just needs to confirm sub_state==`approved` for gated stages |
| **E** Internal verification (Stage 4/5/6) | verification artifact frontmatter `verification_status: pass` | Stage 4: per-task `verification_result.md`; Stage 5: `test-report`; Stage 6: `installation_result` |

`--advance` runs forward path through ALL 5 dimensions in order, returning exit 1 on any failure with a specific stderr listing the failing dimension + path.

### 4.4 `update --advance` mutation

```yaml
current_stage: <stage> → <NEXT_STAGE[stage]>
sub_state: <whatever> → write
review_iteration: <N> → 0
artifacts: <re-init for new stage as needed>  # consult required-artifacts.md to derive new mutable entries
updated: now
```

Special cases:
- Stage 4 (development) → Stage 5 (testing): all `task_states[Tn] == "verified"` precondition (Stage 4 D dimension surrogate)
- Stage 7 (project-retrospective) → next: NOT supported by `--advance`; user must call `release-close` instead. `--advance` rejects with "use release-close to end Stage 7".
- gated stages (PRD / SRS / Architecture): require `sub_state==approved` (i.e. human-confirmed already fired). non-gated stages (Stage 4-7): require `sub_state==review-passed` (review-pass already fired).

### 4.5 `validate.py consistency` subcommand

Per command-reference and required-artifacts §12:

```python
def check_consistency(progress, doc_guardian_required):
    required_artifacts = get_required_artifacts(progress, root)
    for spec in required_artifacts:
        path = root / spec.path
        if not path.exists():
            issues.append(f"Required artifact missing: {spec.path}")
            continue
        per_file_issues = validate_file(spec.path, root)
        issues.extend(f"{spec.path}: {issue}" for issue in per_file_issues)
    # Additional Class 8 checks (per task6_plan §7):
    #   - progress.md current_stage / sub_state matches doc statuses
    #   - Stage 4 task counts match breakdown.total_tasks
    return issues
```

Exit codes:
- exit 0 if `issues == []`
- exit 1 if any inconsistency
- exit 2 only on usage error (e.g. progress.md missing)

CLI shape:
```bash
validate.py consistency [--root <path>]
```

### 4.6 Apply function shape

```python
@dataclass(frozen=True)
class AdvanceOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def apply_update_advance(
    state: Mapping[str, Any],
    *,
    now: str,
) -> AdvanceOutcome:
    """Advance current_stage to NEXT_STAGE[current_stage].

    Replay-side: state-machine legality check only. The CLI is the gate
    for P6 A/B/E dimensions (artifact existence + validate.py +
    verification status) — replay does NOT re-read artifacts because
    artifact state legitimately mutates over time.

    Preconditions enforced here (state-machine legal):
      * project_state == "active"
      * current_stage in {prd-inception, srs-specification,
        architecture-design, development, testing, delivery}
      * For gated stages: sub_state == "approved"
      * For non-gated stages: sub_state == "review-passed"
      * For Stage 4: all task_states[Tn] == "verified"
      * iter ≤ 7 (M2)

    Mutation: current_stage → next, sub_state=write, iter=0, updated=now.
    """
```

### 4.7 History summary canonical tokens

```
update-advance summary:  from=<old_stage> to=<new_stage> Stage advance
```

Replay handler reverses `from=` / `to=` and uses the same `apply_update_advance` function. Optionally encode a `task_count=<N>` token if Stage 4 → 5 needs replay-side verification of `verified` count, but probably unnecessary since replay can read `task_states` from state.

### 4.8 Replay handler

```python
def _apply_update_advance_handler(state, entry, root):
    del root  # advance replay does not read artifacts.
    tokens = _kv_tokens(entry)
    from_stage = tokens.get("from")
    to_stage = tokens.get("to")
    if from_stage is None or to_stage is None:
        raise ReplayError(...)
    try:
        outcome = apply_update_advance(state, now=entry.timestamp)
    except ProgressStateError as exc:
        raise ReplayError(...)
    if outcome.new_state["current_stage"] != to_stage:
        raise ReplayError(
            f"history at {entry.timestamp}: 'update-advance' summary says "
            f"to={to_stage} but state machine derived "
            f"{outcome.new_state['current_stage']!r}; history corruption?"
        )
    return outcome.new_state
```

Register in `_HANDLERS` (now 15) and update `supported_events()` test + module docstring + unsupported-event error text.

### 4.9 CLI flow

```python
def _do_update_advance(args, root):
    # 1. argparse: --advance is a flag (no value)
    # 2. Pre-flight inside _run_update_pipeline OR before, depending on
    #    where artifact derivation feels cleaner. Recommend:
    #    BEFORE _run_update_pipeline so we can use clear error messages
    #    per dimension.
    # 3. Read progress.md (M2 entry guard via apply_update_advance later)
    # 4. P6 matrix:
    #    A. derive get_required_artifacts(progress, root) → list[ArtifactSpec]
    #       For each spec, assert (root / spec.path).exists() else reject
    #       with "A failed: missing <path>"
    #    B. for each spec, validate_doc(spec.path, root) → must be empty
    #       else reject with "B failed: <path>: <issues>"
    #    C. covered by Stage's sub_state check inside apply_update_advance
    #       (review-passed for non-gated, approved for gated)
    #    D. ditto (sub_state==approved == human-confirmed already fired)
    #    E. for stages 4/5/6: read verification artifact and check status
    #       Stage 4: per-task verification_result.md (loop task_states)
    #       Stage 5: load_test_report → verification_status==pass
    #       Stage 6: load_artifact_frontmatter("installation_result", ...) → verification_status==pass
    # 5. _run_update_pipeline(event_name="update-advance",
    #                         compute_outcome=apply_update_advance(...))
    # 6. If success: history records from=<old> to=<new> Stage advance
```

### 4.10 Tests scope

- `tests/test_apply_update_advance.py` — pure state-machine unit tests
  - 6 happy stage advances (prd→srs / srs→arch / arch→dev / dev→testing / testing→delivery / delivery→retro)
  - reject from project-retrospective (use release-close)
  - reject when sub_state wrong (gated requires approved; non-gated requires review-passed)
  - Stage 4: reject if any task != verified; happy when all verified
  - reject aborted/reconstructing project
  - reject iter > 7
  - outcome frozen
- `tests/test_progress_update_advance.py` — CLI integration
  - happy 6 advances with full P6 satisfaction (write real artifacts; skip if heavy)
  - A reject (missing artifact)
  - B reject (validate.py issues; mock validate_doc)
  - E reject for stages 4/5/6 (verification fail/partial)
  - argparse: --advance with --event or --task → mutex error (exit 2)
  - lock blocking
  - M1 inheritance (out-of-band edit + advance)
  - recover roundtrip: advance + delete progress.md + recover → state preserved
- `tests/test_validate_consistency.py` — direct unit tests for `validate.py consistency` CLI
  - happy when progress + all required artifacts on disk + validate
  - reject missing artifact
  - reject malformed artifact
  - reject Class 8 inconsistency (e.g. progress current_stage doesn't match doc statuses; if scope includes that)
- `tests/test_progress_replay.py` — extend ReplayUpdateAdvanceTests
  - happy advance replay
  - missing tokens reject
  - to= mismatch detected (M1-style guard)
  - Update `supported_events_in_phase_6_3` → `_in_phase_6_4`, expected set 15 items
  - Move "unsupported event" sample from `update-advance` (Phase 6.3 placeholder) to a NEW Phase 7+ candidate (e.g. `task-spawn` or just a definitively-unsupported synthetic name like `definitely-not-an-event`)

### 4.11 Phase 6.4 NOT in scope

- Phase 7 (full smoke test of an end-to-end managed-project happy path) — separate handoff
- Anything not listed in command-reference §2.2 or task6_plan §13 Phase 6 scope
- Reworking Phase 5/6.x apply functions

---

## 5. Code Patterns to Follow (Established Conventions)

(Same as Phase 6.2/6.3 §5 with one new pattern — see 5.6.)

### 5.1 New `apply_*` function

(Same shape as Phase 6.1/6.2/6.3.)

### 5.2 New replay handler

(Same shape; for `update-advance` add a state-diff guard since the canonical token includes `to=` which we can verify against the state-machine result.)

### 5.3 New CLI subcommand

(For `--advance`: it joins existing `update` mutex group; not a brand-new subcommand. Follow `_do_update_event` / `_do_update_task` shape.)

### 5.4 Test patterns

(Same. For P6 advance tests: writing all required artifacts on disk is the heaviest setup since required-artifacts.md spans all 7 stages; lean on `tempfile.TemporaryDirectory` + helper functions to construct the per-stage skeletons.)

### 5.5 Critical invariants

(Same M1 / M2 / canonical token / replay-skips-artifacts invariants.)

### 5.6 NEW pattern: P6 matrix forward path

The CLI runs A/B/E dimensions per ordered stage; C/D are subsumed into apply's sub_state preconditions. Each dimension that fails should produce a stderr line naming the dimension + the specific path/file. **Don't** short-circuit on the first dimension — collect all A failures before failing (helps users fix in one round) — but DO short-circuit between dimensions (e.g. don't run B if A failed for the same path, since validate.py file would also fail). Recommended order:

1. A: existence check on EVERY required artifact
2. B: validate.py file on EVERY existing artifact
3. E: verification artifact status check (Stage 4/5/6 only)
4. apply_update_advance: handles C/D via sub_state precondition + state-machine legality

If A fails for any path → reject with all missing paths listed; do NOT run B.
If B fails for any path → reject with all validation issues listed; do NOT run E or apply.
If E fails → reject with verification_status detail; do NOT run apply.
Only when A/B/E all pass → invoke apply via `_run_update_pipeline`.

---

## 6. Recommended Phase 6.4 Work Order

1. **Re-confirm baseline** (`unittest discover` + `compileall`).
2. **Re-confirm Phase 6.3 round 2 closure**: read `task6_phase6_3_incident_round2_review_20260507.md` (already (A); just confirm 1 doc-wording fix landed in §11 wording).
3. **Implement `apply_update_advance`** in `progress_state.py` + `AdvanceOutcome` dataclass + `NEXT_STAGE_FOR_ADVANCE` constant (or reuse existing `NEXT_STAGE` map). Add `tests/test_apply_update_advance.py` first (TDD-style if helpful).
4. **Register `update-advance` replay handler** in `progress_replay.py`. Update `_HANDLERS` to 15, supported_events test, module docstring, unsupported-event error text. Use `_apply_update_event_factory` shape OR a dedicated handler — recommend dedicated handler for the from=/to= state-diff guard.
5. **Implement `validate.py consistency`** in `skills/doc-guardian/scripts/validate.py` (replace the current "deferred" stub). Reuse `get_required_artifacts` from `skills/_shared/dev_workflow/artifacts.py`. Add `tests/test_validate_consistency.py`.
6. **Add P6 forward path (`_do_update_advance`)** in `progress.py`. Wire A/B/E checks per §5.6 above; delegate to `_run_update_pipeline` only after they all pass.
7. **Add argparse `--advance`** to the existing `update` mutex group. Update `cmd_update` dispatcher.
8. **Write `tests/test_progress_update_advance.py`** (CLI integration; 6 stage advances + each P6 dim reject + M1 + recover + lock + argparse).
9. **Extend `tests/test_progress_replay.py`** with `ReplayUpdateAdvanceTests`. Update `supported_events_in_phase_6_3` → `_in_phase_6_4` (15 events). Move "unsupported event" sample to a synthetic placeholder (e.g. `task-spawn` — use whatever string is clearly not a future Phase 7+ event).
10. **Update test_progress_recover.py** "unsupported event" sample synchronously.
11. **Run full suite + compileall + smoke** (`update --advance --help`; manual happy path on a tempdir if useful).
12. **Write Phase 6.4 review prompt** under `docs/review/claude_review_prompt_task6_phase6_4_advance_consistency_20260507.md` (template: Phase 6.3 prompt).

Phase 6.4 acceptance target:
- `progress.py update --advance --help` works
- 6 stage advances all pass (prd→srs→arch→dev→testing→delivery→retro) with realistic per-stage P6 fixtures
- A/B/E reject paths each have a CLI test demonstrating exit 1 + specific stderr + progress.md byte-identical
- `validate.py consistency` works on tempdir-managed projects (happy + reject)
- Replay handler registered; supported_events() returns 15
- Recover roundtrip preserves state after advance
- All previous 719 tests still green; total ≈ 800+
- compileall clean

---

## 7. Watch Points / Common Pitfalls

- **Stage 4 (development) → Stage 5 (testing) E-dim**: Stage 4 has NO single per-stage verification artifact; instead, Stage 4 is "done" when every task in `task_states` == `verified`. The E check for Stage 4 is therefore "all tasks verified" (already in apply preconditions), NOT a per-task `verification_result.md` re-read. (Per-task verification was checked at the `verifying → verified` transition in Phase 5.3.)
- **Gated vs non-gated sub_state at advance time**:
  - PRD / SRS / Architecture: advance preconditions sub_state==`approved` (human-confirmed already happened);
  - Stage 4 / 5 / 6 / 7: advance preconditions sub_state==`review-passed`.
  - Stage 4 special case: review-passed is task-level, not stage-level; advance gate is `all task_states verified`.
- **Stage 7 → ?**: there's no next stage. `apply_update_advance` rejects from project-retrospective with "use release-close to end Stage 7". DO NOT try to map retrospective to anything in `NEXT_STAGE`.
- **Stage 5 (testing) E-dim during active Bug Flow**: if `bug_flow.active==true`, advance must reject — bug must be closed first via `bug-close`. (Stage 5 advance to delivery requires testing's verification_status pass AND no active bug flow.)
- **`get_required_artifacts(progress, root)` already exists** (Phase 2). Call it directly from `_do_update_advance`. The function returns `list[ArtifactSpec]` with rendered paths — A check is `(root / spec.path).exists()`.
- **`condition_variables(progress, root)` reads SRS frontmatter** (`is_multi_module` / `architecture_change`) lazily. If SRS doesn't exist yet (e.g. advancing INTO srs-specification), `read_srs_condition_fields` should return defaults (or the resolver should skip those conditions). Verify Phase 2's behavior; don't re-implement.
- **`validate.py consistency` exit codes**: 0 OK / 1 inconsistent / 2 only on usage error (matches `validate.py file`). The current "deferred" stub returns 2; switch to the real implementation that returns 0 / 1 based on issues.
- **`update --advance` is the FINAL canonical event** in Task 6. After 6.4, supported_events() = 15. No more events expected for now. The "unsupported event" sample test will be tricky to keep meaningful — pick a string that's genuinely not on any roadmap (e.g. `task-spawn` or `synthetic-test-event`).
- **`_run_update_pipeline` already replays-and-diffs** (M1) — `--advance`'s replay must therefore reproduce the exact same outcome. The state-diff guard in `_apply_update_advance_handler` (verifying `outcome.new_state["current_stage"] == to=` token) is defense-in-depth on top of M1.
- **artifacts: dict mutation on advance**: per command-reference, `artifacts:` re-initializes for the new stage. Phase 5.4's `release-start` already has logic for new release; `--advance` may need similar logic to add new artifact slots (e.g. when entering development, add `breakdown / detailed_design / source_code` slots; when entering testing, add `test_report / acceptance_criteria_check` slots). Consult `_initial_artifacts_for_release` shape from Phase 5.4 as reference. **DECIDE THIS EARLY** — could grow scope materially. Recommend: 6.4 keeps artifacts: dict structure unchanged across advance (only `release-start` mutates it); P6 derivation is via `get_required_artifacts(...)` which doesn't read `artifacts:` keys. If user/reviewer wants per-stage artifacts: dict updates, defer to Phase 7.
- **`update --event` doesn't run validate.py** (v0.6 F14 explicitly removed the auto-validate). `--advance` is the dedicated validate point. Don't accidentally start running validate.py for `update --event`.
- **TERMINAL_EVENTS still `{"incident-resolve"}`** — Phase 6.4 does not add to it. `update-advance` is non-terminal.
- **`progress_history.py` field whitelist still `agent / result / next`** — do not add fields. All new info goes into summary tokens or result text.

---

## 8. Reference Anchors

### 8.1 Existing `apply_*` functions in progress_state.py

- `build_initial_state` — Phase 5.1 init
- `apply_update_event` — Phase 5.2
- `apply_update_task` — Phase 5.3 (Phase 6.1 added Gap-3)
- `apply_release_close` / `apply_release_start` / `apply_bug_intake` — Phase 5.4
- `apply_bug_start` / `apply_bug_close` — Phase 6.1
- `compute_dev_bug_rollback` — Phase 6.2 shared Gap-4 helper
- `apply_bug_rework` — Phase 6.2
- `apply_incident_start` / `apply_incident_resolve` — Phase 6.3
- `_validate_doc_path_shape` (Phase 6.3 refactor of bug + incident shape checks)

Phase 6.4 adds: `apply_update_advance` + `AdvanceOutcome`.

### 8.2 Existing replay handlers (14 in progress_replay._HANDLERS)

- `init` — `_apply_init`
- 4 events — `_apply_update_event_factory`
- `update-task` — `_apply_update_task`
- `release-close` / `release-start` / `bug-intake` — Phase 5.4
- `bug-start` / `bug-close` — Phase 6.1
- `bug-rework` — Phase 6.2
- `incident-start` / `incident-resolve` — Phase 6.3

Phase 6.4 adds 15th: `update-advance`.

### 8.3 progress.py CLI subcommands (12)

`init / query / recover / update (--event / --task) / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework / incident-start / incident-resolve`

Phase 6.4 adds `update --advance` (under existing `update` subparser via mutex group). After 6.4 the count stays 12 (it's a new flag on existing `update`, not a new subcommand).

### 8.4 doc-guardian validate.py subcommands

- `file <doc>` — Phase 3 (classes 1-7)
- `ids` — Phase 3 (ID uniqueness)
- `all` — deferred (Phase 7+; not in 6.4 scope)
- `consistency` — Phase 6.4 (Class 8 cross-progress)

### 8.5 Phase 6.3 deliverables

- `docs/review/claude_review_prompt_task6_phase6_3_incident_20260507.md` — round 1 prompt
- `docs/review/task6_phase6_3_incident_review_20260507.md` — round 1 review (B)
- `docs/review/claude_review_prompt_task6_phase6_3_round2_20260507.md` — round 2 prompt
- `docs/review/task6_phase6_3_incident_round2_review_20260507.md` — round 2 review (A)

### 8.6 Phase 6.3 polish (post-(A) Low fixes, landed before this handoff)

- `skills/workflow-protocol/references/command-reference.md §11/§12` — canonical token templates with full result/next prose (L2)
- `skills/workflow-protocol/references/command-reference.md §11` Append history intro — `root_cause=prd-exception` clarified as canonical-form-only token (round 2 L1 wording)
- `skills/workflow-protocol/references/command-reference.md` 受保护字段表 incident-start row — Phase 6.3 stage applicability (L3)
- `skills/workflow-protocol/SKILL.md` command matrix incident-start row — same (L3)
- `skills/_shared/dev_workflow/progress_artifacts.py` `load_bug_report` `expect_root_cause` mismatch error — 3 caller list (cosmetic)

---

## 9. Final Checklist Before New Session Codes

The new session should:

- [ ] Read items 1-11 of §0 in order.
- [ ] Run `python3 -m unittest discover -s tests` and confirm 719 OK + compileall clean.
- [ ] Confirm Phase 6.3 round 2 closure (review (A) verdict + 1 non-blocking Low fixed; do NOT re-open those decisions).
- [ ] Decide canonical event-name for advance replay (recommend `update-advance` to mirror `update-task`).
- [ ] Decide unsupported-event sample for round 6.4 tests (recommend a synthetic non-roadmap string like `task-spawn` since 6.4 closes Phase 6 and there's no obvious next-event placeholder).
- [ ] Confirm Watch Point §7 "artifacts: dict mutation on advance" stays out of scope (recommend yes — defer to Phase 7).
- [ ] Use the test patterns in §5.4 — synthetic stage-advance forge handlers + `_FakeClock` + real artifact files for happy P6 paths.
- [ ] Generate Phase 6.4 review prompt at the end and ask reviewer for (A); follow round-1 → round-2 → (A) cycle as in earlier phases.

When Phase 6.4 closes, write a **Task 6 closure** handoff (mirror this doc but cover the full Task 6 deliverables for the user — what shipped, what was deferred to Phase 7+, what next-task scope looks like).
