# Session Handoff — Task 6 Phase 6.2 Start (`bug-rework` + Gap-4/5)

**Handoff Date**: 2026-05-07  
**Handoff By**: Claude (claude-opus-4-7[1m])  
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`  
**Current Task**: Task 6 implementation — Phase 6 Bug Flow / Incident / Advance  
**Current Phase**: **Phase 6.1 Round 2 fixes complete; awaiting reviewer (B-fix → expected A). Next session should pick up Phase 6.2 (`bug-rework`).**  
**Important Status**: 575 tests pass; compileall clean; 9 progress.py subcommands shipped (`init / query / recover / update / release-close / release-start / bug-intake / bug-start / bug-close`).

---

## 0. New Session Read Order

Read these in order before coding:

1. `docs/handoff/session_handoff_task6_phase6_2_20260507.md` (this handoff)
2. `docs/review/task6_phase6_1_bug_flow_entry_round2_review_20260507.md` (when reviewer writes it; expected (A))
3. `docs/implementation/task6_plan_20260507.md` §6 (Gap-3/4/5 plan) + §13 (phase boundaries)
4. `skills/workflow-protocol/references/command-reference.md` §9 (bug-rework) — primary spec source
5. `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 (Gap-5 detailed)
6. `skills/_shared/dev_workflow/progress_state.py` (apply_bug_start at the bottom — bug-rework reuses Gap-4 logic)
7. `skills/workflow-protocol/scripts/progress.py` (`_compute_bug_start_rollback` — 6.2 should refactor to shared helper)
8. `tests/test_apply_bug_start.py` + `tests/test_progress_bug_flow.py` (template for 6.2 tests)
9. Phase 5 / 6.1 review prompts under `docs/review/claude_review_prompt_task6_phase*` (style reference for 6.2 review prompt)

Optional background:

- `docs/review/task6_phase5_4_release_lifecycle_round2_review_20260507.md` — last Phase 5 closure
- `skills/_shared/dev_workflow/progress_replay.py` — replay handler dispatch + handler signatures

---

## 1. Critical Constraints

- This repo is the skill-implementation repo, **not** a workflow-managed project. Never create / mutate repo-root `progress.md` / `progress-history.md`. They MUST not exist after any test run.
- The current git working tree is largely untracked (`docs/`, `skills/`, `tests/`, helper start scripts). Never delete / clean / reset / revert these.
- All tests use `tempfile.TemporaryDirectory()` fixtures. Never touch the real `docs/` / `skills/` as a managed project.
- Phase 6 sub-phase boundaries (user-confirmed 4-split):
  - **Phase 6.1** ✅ closed (round 2 expected A): bug-start + bug-close + Gap-3 update --task
  - **Phase 6.2** (this session): `bug-rework` + Gap-4/5 reuse
  - **Phase 6.3**: `incident-start` + `incident-resolve` + `TERMINAL_EVENTS` first activation
  - **Phase 6.4**: `update --advance` (P6 matrix) + `validate.py consistency`
- The 11 supported replay events (Phase 6.1 final state) are: `init / write-complete / review-issues / review-passed / human-confirmed / update-task / release-close / release-start / bug-intake / bug-start / bug-close`. Phase 6.2 adds `bug-rework`.
- Event whitelist for `update --event` is exactly `{write-complete, review-issues, review-passed, human-confirmed}`. `issues-found` is business wording, NOT an event. `bug-rework` is a TOP-LEVEL command (not an `update --event`).
- Replay design contract: replay validates state-machine legality only; it does NOT re-read BUG / test-report / verification artifact files. All mutation info travels in canonical history summary tokens (`bug=` / `root_cause=` / `rollback=Tn:old->new;...` etc.).

---

## 2. Current Repository State

Project root: `/home/cgs/github_projects/dev-workflow-skills2`

Key files (after Phase 6.1 round 2):

- `skills/_shared/dev_workflow/`
  - `atomic.py` (Phase 2; `transaction()` context manager)
  - `frontmatter.py` (Phase 2; `parse_frontmatter`, `render_markdown`)
  - `markdown.py` (Phase 2)
  - `changelog.py` (Phase 3)
  - `schema.py` (Phase 2)
  - `progress_lock.py` (Phase 5.1)
  - `progress_history.py` (Phase 5.1; `agent / result / next` field whitelist)
  - `progress_replay.py` (Phase 5.1+; 11 handlers; `_kv_tokens` summary parser)
  - `progress_artifacts.py` (Phase 5.3+; loaders + BUG triage parser; **load_bug_report** strict in 6.1 round 2)
  - `progress_state.py` (Phase 5.1+; all `apply_*` state-machine functions)
- `skills/doc-guardian/scripts/`
  - `validate.py` (Phase 3; classes 1-7 + `ids`; `consistency` is Phase 6.4)
  - `changelog.py` (Phase 3)
  - `status_transition.py` (Phase 4)
- `skills/workflow-protocol/scripts/`
  - `progress.py` (Phase 5.1+; 9 subcommands as of 6.1)

Current test runtime baseline:

```bash
python3 -m unittest discover -s tests
# Ran 575 tests in 4.577s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

No repo-root `progress.md` / `progress-history.md` exists (intentional).

---

## 3. Completed Work Before This Handoff

### Phases 1-4 (closed)

- Phase 1: docs alignment
- Phase 2: shared foundation (frontmatter / markdown / atomic / conditions / artifacts / progress_state base / schema)
- Phase 3: `changelog.py` + `validate.py file/ids`
- Phase 4: `status_transition.py`

### Phase 5 (closed; 4 sub-phases)

- 5.1: progress.py foundation (`init / query / recover` + lock / history / replay)
- 5.2: `update --event` (4 events with M1 history-parse-and-replay-consistency + M2 review_iteration ≤ 7 entry guard)
- 5.3: `update --task` (Stage 4 task state machine; `validate_artifacts=True` forward / `False` replay design choice)
- 5.4: `release-close` + `release-start` (BUG fan-out via `extra_writes_factory`) + `bug-intake`

### Phase 6.1 (round 2 expected A; awaiting reviewer)

- `bug-start --bug --root-cause`: 3 root-cause routing + Gap-4 dev auto-rollback (parses BUG `## Triage Analysis`, classifies test/source/ambiguous + handles `unable to localize`)
- `bug-close`: clears bug_flow when latest test-report `verification_status==pass`
- `update --task` Gap-3: `verifying → code-revising` accepted when `verification_result.md verification_status ∈ {fail, partial}`
- Round 2 fixes: M1 strict BUG frontmatter validation; L1 dev empty-rollback persists `route=development-planning-write` token in history_result/next + CLI stderr warning for ambiguous classification

### Round 2 deliverables (this session)

- `progress_artifacts.py` `load_bug_report`: bug_id regex + path-stem match + nullable-field key presence + root_cause enum
- `progress_state.py` `apply_bug_start`: dev empty-rollback emits planning-route history note; CLI prints stderr reason
- 22 new tests (artifacts 10 + apply 4 + bug-flow CLI 8)
- Round 2 review prompt: `docs/review/claude_review_prompt_task6_phase6_1_round2_20260507.md`

---

## 4. Phase 6.2 Scope — `bug-rework` + Gap-4/5

### 4.1 Spec source of truth

- `skills/workflow-protocol/references/command-reference.md §9 bug-rework`
- `docs/handoff/task6_progress_py_prerequisites_20260506.md §6 (Gap-5)`
- `docs/implementation/task6_plan_20260507.md §6.3 (Gap-5 detailed plan)`

### 4.2 Command shape

```bash
progress.py bug-rework --bug <docs/bug/BUG-NNN.md> [--agent <agent>]
```

### 4.3 Preconditions (per command-reference.md §9)

- `bug_flow.active == true`
- `current_stage == testing`
- `sub_state == review-passed`
- Latest `docs/release<release>/testing/report.md` `verification_status ∈ {fail, partial}`
- `<bug-report-path>` equals `bug_flow.bug_report_path` (exact match)
- BUG frontmatter `root_cause == bug_flow.root_cause`
- `bug_flow.root_cause ∈ {srs, architecture, development}`

Use `progress_artifacts.load_test_report` + `load_bug_report` for these checks. The BUG path must use the canonical `_validate_bug_path_shape` (already imported into `progress.py`).

### 4.4 Mutation (per command-reference.md §9)

```yaml
bug_flow.active: true → true                # unchanged
bug_flow.bug_report_path: <path> → <same>   # unchanged
bug_flow.root_cause: <enum> → <same>        # unchanged
current_stage: testing → <root_cause stage> # srs→spec / architecture→design / development→development
sub_state: review-passed → write
review_iteration: <N> → 0
```

### 4.5 Gap-4 dev rollback (reuse from 6.1)

When `bug_flow.root_cause == development`, `bug-rework` must apply the SAME Gap-4 logic 6.1 `bug-start` already does:

- Parse BUG body `## Triage Analysis` (use `parse_bug_triage_analysis`)
- Read current `task_states` from progress.md
- Classify per task → roll back (`verified→test-revising` / `verified→code-revising` / `code-review-passed→code-revising`)
- Empty rollback list → emit planning-route note (matching 6.1 round 2 L1 fix)

**Refactor recommendation**: 6.1's `_compute_bug_start_rollback` lives in `skills/workflow-protocol/scripts/progress.py`. Phase 6.2 should move it to `skills/_shared/dev_workflow/progress_state.py` (or a new shared helper) so `cmd_bug_rework` reuses without duplication. Spec docstring should clarify that the helper is shared by bug-start AND bug-rework.

### 4.6 Apply function shape

Suggested signature mirroring `apply_bug_start`:

```python
@dataclass(frozen=True)
class BugReworkOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None
    rollback_decisions: tuple[tuple[str, str, str, str], ...]


def apply_bug_rework(
    state: Mapping[str, Any],
    bug_path: str,
    *,
    now: str,
    rollback_decisions: tuple[tuple[str, str, str, str], ...] = (),
) -> BugReworkOutcome:
    """Active Bug Flow retest re-route (Phase 6.2 / Gap-5)."""
```

Note: bug-rework does NOT take `--root-cause` (root cause is fixed by the existing `bug_flow.root_cause`). The CLI reads it from progress.md and confirms BUG file matches.

### 4.7 History summary canonical tokens

Mirror bug-start: `bug=<path> root_cause=<r> Bug Flow rerouted [rollback=...]`

This lets replay reuse `_kv_tokens` + `_parse_rollback_token` without new helpers.

### 4.8 Replay handler

```python
def _apply_bug_rework_handler(state, entry, root):
    del root  # bug-rework replay does not read BUG / test-report.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    if bug_path is None:
        raise ReplayError(...)
    rollback_token = tokens.get("rollback") or ""
    rollback_decisions = _parse_rollback_token(rollback_token) if rollback_token else ()
    try:
        outcome = apply_bug_rework(
            state, bug_path,
            now=entry.timestamp,
            rollback_decisions=rollback_decisions,
        )
    except ProgressStateError as exc:
        raise ReplayError(...)
    return outcome.new_state
```

Then register in `_HANDLERS`. `supported_events()` becomes 12.

### 4.9 CLI flow

```python
def cmd_bug_rework(args, root):
    # 1. argparse: --bug required; --agent default
    # 2. resolve abs_bug + relative_to(root) containment check
    # 3. read progress.md to get release, bug_flow, task_states
    # 4. Pre-flight gates (NOT inside pipeline; want clear error messages):
    #    - bug_flow.active = true
    #    - bug_path matches bug_flow.bug_report_path
    #    - root_cause is dev/srs/architecture (not prd-exception)
    # 5. load_test_report(release) → verification_status in {fail, partial}
    # 6. load_bug_report(bug_path, expect_root_cause=bug_flow.root_cause)
    # 7. If root_cause == "development": parse_bug_triage_analysis +
    #    _compute_rollback_for_dev (refactored shared helper)
    # 8. _run_update_pipeline(event_name="bug-rework",
    #                         compute_outcome=apply_bug_rework(...))
```

### 4.10 Tests scope

- `tests/test_apply_bug_rework.py` — pure state-machine unit tests (3 root_cause × happy / Gap-4 dev rollback × test-only/source/ambiguous/unable / each precondition reject / outcome frozen / planning-route note for empty dev rollback)
- `tests/test_progress_bug_rework.py` — CLI integration:
  - happy 3 root_cause + dev × 4 classification
  - reject when bug_flow.active=false / current_stage != testing / latest test-report=pass / BUG path != bug_flow.path / BUG root_cause != bug_flow.root_cause
  - recover roundtrip preserves bug_flow + current_stage + dev rollback
  - lock blocking
  - M1 inheritance (forge progress.md → replay diff)
- `tests/test_progress_replay.py` — extend `ReplayBugFlowTests` with bug-rework happy + missing tokens reject + replay-skips-files
- Update `supported_events_in_phase_6_1` → `supported_events_in_phase_6_2`, expected set 12 items
- Update "unsupported event" sample in `test_progress_replay.py:ReplayUnsupportedEventTests` and `test_progress_recover.py` from `bug-rework` to `incident-start` (Phase 6.3 territory)

### 4.11 Phase 6.2 NOT in scope

- `incident-start` / `incident-resolve` (Phase 6.3)
- `TERMINAL_EVENTS` first activation (Phase 6.3)
- `update --advance` / `validate.py consistency` (Phase 6.4)

---

## 5. Code Patterns to Follow (Established Conventions)

### 5.1 New apply_* function

1. Follow `apply_bug_start` shape: dataclass `<Cmd>Outcome` (frozen) with `new_state / history_summary / history_result / history_next` + command-specific fields.
2. Always inherit invariants:
   - `_validate_timestamp(now, field="now")`
   - `_validate_active_project(state, "<cmd-name>")`
   - `_validate_review_iteration_value(state.get("review_iteration", 0))` (M2 from 5.2 round 2)
3. Mutate via `new_state = dict(state); new_state[k] = v` to preserve unrelated fields.
4. Emit canonical history summary tokens (`key=value` parseable by `_kv_tokens`) when replay needs to reproduce.

### 5.2 New replay handler

1. Add `_apply_<cmd>_handler(state, entry, root)` in `progress_replay.py`.
2. Use `_kv_tokens(entry)` to extract summary tokens.
3. Validate required tokens; raise `ReplayError` with "missing" message.
4. Call same `apply_<cmd>` function the forward path uses (single source of truth).
5. `del root` if your handler doesn't need artifact reads.
6. Register in `_HANDLERS` dict + update `supported_events()` test + module docstring.

### 5.3 New CLI subcommand

1. Add `cmd_<name>` after the existing `cmd_*` functions in `progress.py`.
2. Read progress state OUTSIDE `_run_update_pipeline` for pre-flight checks (cleaner error messages).
3. Pass `compute_outcome=lambda state, now: apply_<name>(...)` to the pipeline.
4. For multi-file atomic writes, use `extra_writes_factory` (see `release-start` for reference).
5. Add subparser in `build_parser` + dispatcher branch in `main`.
6. Use argparse `required=True` for genuinely-required flags → caller gets exit 2; workflow validation failures → exit 1 (see Phase 5.1 round 2 M2 contract).

### 5.4 Test patterns

- Pure unit tests: `tests/test_apply_<cmd>.py` — no CLI / file I/O except temp dirs for artifact loaders.
- CLI integration: `tests/test_progress_<cmd>.py` — use `_install_test_stage_advance_handler` context manager + `_FakeClock` patch to forge state. Pattern: `_seed_*` helpers first call init then append synthetic `test-stage-advance` history entries that the patched handler converts.
- Always assert (a) exit code, (b) stderr contains specific token, (c) progress.md / progress-history.md byte-for-byte unchanged on reject paths.
- Replay tests: `tests/test_progress_replay.py` extends per phase. Patch `_HANDLERS` for synthetic events.

### 5.5 Critical invariants

- M1: `_run_update_pipeline` does (1) parse existing history before apply, (2) replay composed history, (3) state diff against forward outcome. ALL forward commands must use this pipeline.
- M2: every `apply_*` function calls `_validate_review_iteration_value` even if it doesn't directly mutate `review_iteration`.
- L1 (canonical token): summary holds `key=value` tokens that replay can reverse without consulting `result` field.
- replay-skips-artifacts: replay handlers `del root` and don't read BUG / test-report / verification artifacts. The forward path is the gatekeeper; replay validates state-machine legality only.

---

## 6. Recommended Phase 6.2 Work Order

1. **Re-confirm baseline** (`unittest discover` + `compileall`).
2. **Verify Phase 6.1 round 2 review verdict** (read `task6_phase6_1_bug_flow_entry_round2_review_20260507.md`); if (B), fix before starting 6.2.
3. **Refactor Phase 6.1 helper**: move `_compute_bug_start_rollback` from `progress.py` to `progress_state.py` (or new `_compute_dev_bug_rollback`). Update `cmd_bug_start` to import. Run baseline.
4. **Implement `apply_bug_rework`** in `progress_state.py` + `BugReworkOutcome` dataclass. Mirror `apply_bug_start` (no `--root-cause` argument; reads from `bug_flow`). Add `tests/test_apply_bug_rework.py` first (TDD-style if helpful).
5. **Register `bug-rework` replay handler** in `progress_replay.py`. Update docstring + supported_events count to 12. Update tests/test_progress_replay.py supported_events test.
6. **Add `cmd_bug_rework`** to `progress.py` + argparse subparser + dispatcher. Use `_run_update_pipeline`.
7. **Write `tests/test_progress_bug_rework.py`** (CLI integration; mirror `test_progress_bug_flow.py` style).
8. **Extend `tests/test_progress_replay.py`** ReplayBugFlowTests with bug-rework cases.
9. **Update test_progress_replay.py + test_progress_recover.py** "unsupported event" sample from `bug-rework` → `incident-start`.
10. **Run full suite + compileall + smoke** (`bug-rework --help`).
11. **Write Phase 6.2 review prompt** under `docs/review/claude_review_prompt_task6_phase6_2_bug_rework_20260507.md` (template: `docs/review/claude_review_prompt_task6_phase6_1_*.md`).

Phase 6.2 acceptance target:
- `progress.py bug-rework --help` works
- bug-rework happy paths for srs/arch/dev × dev-with-Gap-4 rollback all pass
- Replay handler registered; supported_events() returns 12
- Recover roundtrip preserves state after a bug-rework
- All previous 575 tests still green; total ≈ 620+
- compileall clean

---

## 7. Watch Points / Common Pitfalls

- **Don't treat the dev_workflow_skills2 repo as workflow-managed** — never write to repo-root `progress.md` / `progress-history.md`. Tests must use `tempfile.TemporaryDirectory()`.
- **bug-rework root_cause comes from `bug_flow`, not CLI argument** — easy to confuse with bug-start. Validate the BUG file's `root_cause` matches `bug_flow.root_cause` to prevent caller swapping BUG documents mid-flow.
- **Gap-4 protected transitions** must only be applied via `apply_bug_start` / `apply_bug_rework`'s `rollback_decisions` argument. `apply_update_task` directly via `update --task` still rejects Gap-4 (correct behavior — gives a clear error pointing at the right command).
- **Path containment**: `_validate_bug_path_shape` only checks shape (`docs/bug/BUG-NNN.md`); always combine with `(root / path).resolve()` + `relative_to(root.resolve())` for symlink/race protection (see `_read_bug_for_release_start` / `cmd_bug_start` for reference).
- **History rollback token format**: canonical is `Tn:old->new;Tm:old->new` (no spaces). `_parse_rollback_token` is strict; tests should construct exactly this format.
- **Latest test-report semantics**: bug-close requires `verification_status==pass`; bug-rework requires `verification_status ∈ {fail, partial}`. Easy to flip; always reference `command-reference.md §9` and `§10` when implementing.
- **TERMINAL_EVENTS still empty in Phase 6.2** — `incident-resolve abort/reconstruct` is the only event that activates them and that's Phase 6.3. Don't pre-populate.
- **`progress_history.py` field whitelist still `agent / result / next`** — do not add fields. All new info goes into summary tokens or result text.

---

## 8. Reference Anchors

### 8.1 Existing apply_* functions in progress_state.py (line numbers approximate after Phase 6.1 round 2)

- `build_initial_state` — Phase 5.1 init
- `apply_update_event` — Phase 5.2 (sub_state state machine)
- `apply_update_task` — Phase 5.3 (Stage 4 task; Phase 6.1 added Gap-3 branch)
- `apply_release_close` / `apply_release_start` / `apply_bug_intake` — Phase 5.4
- `apply_bug_start` / `apply_bug_close` — Phase 6.1
- `_validate_bug_path_shape` (from Phase 5.4 round 2) — used by `apply_bug_intake` / `apply_bug_start`

### 8.2 Existing replay handlers (11 in progress_replay._HANDLERS)

- `init` — `_apply_init`
- 4 events (`write-complete` / `review-issues` / `review-passed` / `human-confirmed`) — `_apply_update_event_factory`
- `update-task` — `_apply_update_task`
- `release-close` / `release-start` / `bug-intake` — phase 5.4 handlers
- `bug-start` / `bug-close` — phase 6.1 handlers

Add 12th: `bug-rework` (phase 6.2).

### 8.3 progress.py CLI subcommands (9)

`init / query / recover / update (--event / --task) / release-close / release-start / bug-intake / bug-start / bug-close`

Phase 6.2 adds `bug-rework`. Phase 6.3 adds `incident-start / incident-resolve`. Phase 6.4 may add `update --advance` (under existing `update` subparser via mutex group).

### 8.4 Phase 6.1 round 2 deliverables

- `docs/review/claude_review_prompt_task6_phase6_1_round2_20260507.md` — review prompt
- `docs/review/task6_phase6_1_bug_flow_entry_round2_review_20260507.md` — review report (when reviewer writes it)

---

## 9. Final Checklist Before New Session Codes

The new session should:

- [ ] Read items 1-9 of §0 in order.
- [ ] Run `python3 -m unittest discover -s tests` and confirm 575 OK + compileall clean.
- [ ] Read `task6_phase6_1_bug_flow_entry_round2_review_20260507.md` (when reviewer publishes); apply any (B) round 3 fixes if needed.
- [ ] Confirm `bug-rework` is the right Phase 6.2 scope (not `incident-start`, which is 6.3).
- [ ] Refactor `_compute_bug_start_rollback` to shared helper before implementing `apply_bug_rework` to avoid duplicate Gap-4 logic.
- [ ] Use the test patterns in §5.4 — synthetic stage-advance handlers + FakeClock.
- [ ] Generate Phase 6.2 review prompt at the end and ask reviewer for (A); follow round-1 → round-2 → (A) cycle as in earlier phases.

When Phase 6.2 closes, write a Phase 6.3 handoff (mirror this doc) and continue with `incident-start` / `incident-resolve` + `TERMINAL_EVENTS`.
