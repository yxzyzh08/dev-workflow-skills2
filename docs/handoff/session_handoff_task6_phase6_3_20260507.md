# Session Handoff — Task 6 Phase 6.3 Start (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS`)

**Handoff Date**: 2026-05-07
**Handoff By**: Claude (claude-opus-4-7[1m])
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Current Task**: Task 6 implementation — Phase 6 Bug Flow / Incident / Advance
**Current Phase**: **Phase 6.2 closed (A) + 3 Low polish landed; ready to start Phase 6.3 (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS` first activation).**
**Important Status**: 637 tests pass; compileall clean; 10 progress.py subcommands (`init / query / recover / update / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework`).

---

## 0. New Session Read Order

Read these in order before coding:

1. `docs/handoff/session_handoff_task6_phase6_3_20260507.md` (this handoff)
2. `docs/review/task6_phase6_2_bug_rework_review_20260507.md` — Phase 6.2 closure (A) + 3 Low (already fixed; do NOT re-open)
3. `docs/implementation/task6_plan_20260507.md` §13 (phase boundaries) — Phase 6 sub-phase split confirmation
4. `skills/workflow-protocol/references/command-reference.md` §11 (incident-start) + §12 (incident-resolve) — primary spec source for both new commands
5. `skills/_shared/dev_workflow/progress_replay.py` (`TERMINAL_EVENTS` placeholder + dispatch loop at line ~545) — first time we'll populate this set
6. `skills/_shared/dev_workflow/progress_state.py` (`apply_bug_start` / `apply_bug_close` / `apply_bug_rework` + `_validate_bug_path_shape` + `_ROOT_CAUSE_TO_STAGE`) — Phase 6.1/6.2 patterns to mirror
7. `skills/workflow-protocol/scripts/progress.py` (`cmd_bug_start` / `cmd_bug_rework`) — preflight + double-validate pattern (round 2 M6)
8. `skills/doc-guardian/scripts/validate.py` — `validate.py file <path>` exit-0/exit-1 contract; Phase 6.3 will invoke this twice per command (incident-start: BUG + INCIDENT both pre-flight; incident-resolve: INCIDENT pre-flight)
9. `tests/test_apply_bug_rework.py` + `tests/test_progress_bug_rework.py` — template for Phase 6.3 tests
10. Phase 5 / 6.1 / 6.2 review prompts under `docs/review/claude_review_prompt_task6_phase*` (style reference for 6.3 review prompt)

Optional background:

- `skills/workflow-evolution/SKILL.md` — owner of INCIDENT-NNN.md body; Phase 6.3 only validates schema, does not write the body
- `skills/bug-triage/SKILL.md` — caller of `incident-start` (post-classification PRD-exception path)
- `docs/review/claude_review_prompt_batch2_round2.md` (or similar batch-2 reviews) — context on `validate.py file` double-safety design (M6)

---

## 1. Critical Constraints

- This repo is the skill-implementation repo, **not** a workflow-managed project. Never create / mutate repo-root `progress.md` / `progress-history.md`. They MUST not exist after any test run.
- The current git working tree is largely untracked (`docs/`, `skills/`, `tests/`, helper start scripts). Never delete / clean / reset / revert these.
- All tests use `tempfile.TemporaryDirectory()` fixtures. Never touch the real `docs/` / `skills/` as a managed project.
- Phase 6 sub-phase boundaries (user-confirmed 4-split):
  - Phase 6.1 ✅ closed (A): bug-start + bug-close + Gap-3 update --task
  - Phase 6.2 ✅ closed (A) + 3 Low polish landed: bug-rework + Gap-4/5 reuse
  - **Phase 6.3 (this session)**: incident-start + incident-resolve + `TERMINAL_EVENTS` first activation
  - Phase 6.4: update --advance (P6 matrix) + validate.py consistency
- The 12 supported replay events (Phase 6.2 final state) are: `init / write-complete / review-issues / review-passed / human-confirmed / update-task / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework`. Phase 6.3 adds `incident-start / incident-resolve`.
- Event whitelist for `update --event` is exactly `{write-complete, review-issues, review-passed, human-confirmed}`. Incident commands are NOT `update --event` events; they are dedicated TOP-LEVEL subcommands (`incident-start` / `incident-resolve`).
- **`TERMINAL_EVENTS` semantics (new in Phase 6.3)**: Once `incident-resolve --action abort` or `--action reconstruct` fires, the project enters a terminal state. Replay must reject every subsequent **mutating** entry. `incident-resolve --action continue` is NOT terminal. Read-only entries (none currently in `READ_ONLY_EVENTS`) are still allowed; `recover` itself is r/w but does not append to history.
- Replay design contract (still): replay validates state-machine legality only; it does NOT re-read BUG / test-report / verification / **INCIDENT** artifact files. All mutation info travels in canonical history summary tokens.

---

## 2. Current Repository State

Project root: `/home/cgs/github_projects/dev-workflow-skills2`

Key files (after Phase 6.2 + L1/L2/L3 polish):

- `skills/_shared/dev_workflow/`
  - `atomic.py` (Phase 2; `transaction()` context manager)
  - `frontmatter.py` (Phase 2; `parse_frontmatter`, `render_markdown`)
  - `markdown.py` (Phase 2)
  - `changelog.py` (Phase 3)
  - `schema.py` (Phase 2)
  - `progress_lock.py` (Phase 5.1)
  - `progress_history.py` (Phase 5.1; `agent / result / next` field whitelist)
  - `progress_replay.py` (Phase 5.1+; **12 handlers**; `_kv_tokens` summary parser; `TERMINAL_EVENTS` still `set()`)
  - `progress_artifacts.py` (Phase 5.3+; loaders + BUG triage parser; `load_bug_report` strict in 6.1 round 2; L3 polish: generic `expect_root_cause` error message)
  - `progress_state.py` (Phase 5.1+; all `apply_*` state-machine functions; `compute_dev_bug_rollback` shared Gap-4 helper added in 6.2)
- `skills/doc-guardian/scripts/`
  - `validate.py` (Phase 3; classes 1-7 + `ids`; `consistency` is Phase 6.4)
  - `changelog.py` (Phase 3)
  - `status_transition.py` (Phase 4)
- `skills/workflow-protocol/scripts/`
  - `progress.py` (Phase 5.1+; **10 subcommands** as of 6.2)

Current test runtime baseline:

```bash
python3 -m unittest discover -s tests
# Ran 637 tests in 5.455s
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

### Phase 6.1 (closed; round 2 expected (A))

- `bug-start --bug --root-cause`: 3 root-cause routing + Gap-4 dev auto-rollback (parses BUG `## Triage Analysis`, classifies test/source/ambiguous + handles `unable to localize`)
- `bug-close`: clears bug_flow when latest test-report `verification_status==pass`
- `update --task` Gap-3: `verifying → code-revising` accepted when `verification_result.md verification_status ∈ {fail, partial}`
- Round 2 fixes: M1 strict BUG frontmatter validation; L1 dev empty-rollback persists `route=development-planning-write` token in history_result/next + CLI stderr warning for ambiguous classification

### Phase 6.2 (closed (A) + 3 Low polish landed)

- `bug-rework --bug` (Gap-5): 3 root-cause re-route + Gap-4 dev auto-rollback (reuses 6.1 helper); requires latest test-report `verification_status ∈ {fail, partial}` and BUG frontmatter `root_cause == bug_flow.root_cause`; bug_flow stays active and unchanged across re-route
- `compute_dev_bug_rollback` refactor: moved from `progress.py._compute_bug_start_rollback` to `progress_state.py` shared helper; `cmd_bug_start` switched to import from shared layer
- 12 replay handlers; `_apply_bug_rework_handler` registered; canonical token contract `bug=<path> root_cause=<r> Bug Flow rerouted [rollback=...]`
- 62 new tests (apply 36 + CLI 21 + replay 5)
- Phase 6.2 review verdict (A): 0 H / 0 M / 3 L all non-blocking; Low items L1/L2/L3 fixed in same session before this handoff:
  - L1: `command-reference.md §9` Append history block updated to canonical-token form; `task6_plan §6.3` step 6 + `progress_py_prerequisites §6` step 6 annotated as superseded by Phase 6.2 contract.
  - L2: `_apply_bug_rework_handler` comment in `progress_replay.py` rewritten to accurately state token is presence-checked only; future hardening hook noted.
  - L3: `load_bug_report` `expect_root_cause` mismatch error generalized — no longer says "match the bug-start --root-cause argument"; now mentions both bug-start and bug-rework callers.

---

## 4. Phase 6.3 Scope — `incident-start` / `incident-resolve` + `TERMINAL_EVENTS`

### 4.1 Spec source of truth

- `skills/workflow-protocol/references/command-reference.md §11` (incident-start) + `§12` (incident-resolve, includes 12.1 continue / 12.2 abort / 12.3 reconstruct)
- `docs/implementation/task6_plan_20260507.md` §13 (phase split confirmation)
- `command-reference.md` 状态机转移合法性表 (line ~611) for terminal-state mutation rows

### 4.2 Command shapes

```bash
progress.py incident-start --bug <docs/bug/BUG-NNN.md> --report <docs/incident/INCIDENT-NNN.md> [--agent <agent>]
progress.py incident-resolve --action <continue|abort|reconstruct> [--agent <agent>]
```

### 4.3 `incident-start` preconditions (per command-reference.md §11)

- `bug_flow.active == false` (force caller to bug-close first if there's an active flow; spec v0.6 F2)
- `<bug-path>` shape matches `docs/bug/BUG-NNN.md` AND `validate.py file <bug-path>` exit 0
- `<bug-path>` BUG-NNN.md frontmatter `root_cause == prd-exception`
- `<incident-path>` shape (TBD: confirm `docs/incident/INCIDENT-NNN.md` regex against `frontmatter-schema.md`)
- `<incident-path>` is a legal `workflow-incident` skeleton AND `validate.py file <incident-path>` exit 0 (round 2 M6 double-safety)
- INCIDENT-NNN.md frontmatter `triggered_by_bug` ID equals `<bug-path>` `bug_id`
- Project not in terminal state (`project_state == "active"`)

### 4.4 `incident-start` mutation (per command-reference.md §11)

```yaml
bug_flow.active: false → true                # incident-start atomically opens bug_flow
bug_flow.bug_report_path: null → <bug-path>
bug_flow.root_cause: null → prd-exception
workflow_incident_active: false → true
incident_report_path: null → <incident-path>
current_stage: <previous, usually testing> → workflow-incident-analysis
# sub_state preserved across incident analysis
# review_iteration NOT touched
```

Note: `prd-exception` is a 4th `bug_flow.root_cause` value; `_ROOT_CAUSE_TO_STAGE` MUST NOT contain it (the 3-key set drives `bug-rework`/`bug-start` legality). Add a separate constant or inline check for `incident-start`.

### 4.5 `incident-resolve` preconditions (per command-reference.md §12)

- `workflow_incident_active == true`
- INCIDENT-NNN.md frontmatter `resolution_action ∈ {continue, abort, reconstruct}` AND equals CLI `--action`
- INCIDENT-NNN.md frontmatter `status == review-passed` (workflow-evolution finalization done)
- `validate.py file <incident-report-path>` exit 0 (round 2 M6 double-safety)

### 4.6 `incident-resolve` mutation by action

**`--action continue`** (§12.1, v0.6 round 2 H3 simplification — single behavior, no sub-flag):
```yaml
workflow_incident_active: true → false
incident_report_path: <path> → null
current_stage: workflow-incident-analysis → testing
sub_state: → review-passed
review_iteration: <N> → 0
bug_flow.active: true → false
bug_flow.bug_report_path: <path> → null
bug_flow.root_cause: prd-exception → null
```
- BUG-NNN.md frontmatter `root_cause: prd-exception` is left intact (historical record).
- INCIDENT-NNN.md `resolution_action: continue` was already written by workflow-evolution before this command runs.

**`--action abort`** (§12.2, v0.6 F11 cleanup):
```yaml
workflow_incident_active: true → false
incident_report_path: <path> → null
project_state: active → aborted
release_state: active → closed
release_close_reason: null → "incident-abort"
current_stage: workflow-incident-analysis → null     # terminal
sub_state: <any> → null                              # F11 allows null
review_iteration: <N> → 0
bug_flow.active: <any> → false
bug_flow.bug_report_path: <any> → null
bug_flow.root_cause: <any> → null
```

**`--action reconstruct`** (§12.3, v0.6 F11 cleanup) — same as abort except:
```yaml
project_state: active → reconstructing               # not aborted
release_close_reason: null → "incident-reconstruct"  # not "incident-abort"
```

`abort` and `reconstruct` are **terminal**: after them, every `update` / `release-*` / `bug-*` / `incident-*` command must reject. `query` / `recover` still work.

### 4.7 `TERMINAL_EVENTS` activation

```python
TERMINAL_EVENTS: set[str] = {"incident-resolve"}    # consider per-action; see open question below
```

Open design question: should `TERMINAL_EVENTS` be event-name-only (i.e. ALL `incident-resolve` entries are terminal, including `continue`) or include action-aware filtering? Spec semantics dictate that `continue` is **not** terminal. Two viable shapes:

- **Option A**: keep `TERMINAL_EVENTS = {"incident-resolve"}` and let the handler detect `--action continue` from summary tokens; but the dispatch loop currently flips `seen_terminal=True` based purely on event name, so this would mis-flag `continue`.
- **Option B (recommended)**: `TERMINAL_EVENTS` stays event-name-keyed, but the dispatch loop checks the entry summary for an `action=` token before flipping the terminal flag. Encode `action` as a canonical replay token in the summary (`action=continue|abort|reconstruct`) and gate `seen_terminal = (entry.event in TERMINAL_EVENTS) and (action != "continue")`.

Pick **B** unless the user prefers a cleaner schema (e.g. introduce two distinct event names `incident-resolve-continue` / `incident-resolve-terminal`). Reviewer should resolve this in round 1.

### 4.8 History summary canonical tokens

```
incident-start summary:    bug=<path> incident=<path> root_cause=prd-exception PRD exception triggered
incident-resolve summary:  action=<continue|abort|reconstruct> incident=<path> Incident resolved
```

Replay handlers parse these via the existing `_kv_tokens` helper. No new token parser needed.

### 4.9 Apply function shapes

```python
@dataclass(frozen=True)
class IncidentStartOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def apply_incident_start(
    state: Mapping[str, Any],
    bug_path: str,
    incident_path: str,
    *,
    now: str,
) -> IncidentStartOutcome:
    """PRD exception entry. CLI is responsible for double-validating
    BOTH bug_path and incident_path via validate.py file before this
    function runs; this state-machine function does no I/O."""
    ...


@dataclass(frozen=True)
class IncidentResolveOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None
    is_terminal: bool         # True for abort/reconstruct, False for continue


def apply_incident_resolve(
    state: Mapping[str, Any],
    action: str,
    incident_path: str,
    *,
    now: str,
) -> IncidentResolveOutcome:
    """Exit incident state per --action. Handles 3 mutation tables
    (continue/abort/reconstruct). Terminal action sets project_state
    + release_state + release_close_reason."""
    ...
```

### 4.10 Replay handlers

```python
def _apply_incident_start_handler(state, entry, root):
    del root  # replay does not read BUG / INCIDENT artifact files.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    incident_path = tokens.get("incident")
    if bug_path is None or incident_path is None:
        raise ReplayError(f"missing bug=/incident= tokens at {entry.timestamp}")
    try:
        outcome = apply_incident_start(
            state, bug_path, incident_path, now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(f"history at {entry.timestamp}: {exc}") from exc
    return outcome.new_state


def _apply_incident_resolve_handler(state, entry, root):
    del root
    tokens = _kv_tokens(entry)
    action = tokens.get("action")
    incident_path = tokens.get("incident")
    if action is None or incident_path is None:
        raise ReplayError(...)
    if action not in {"continue", "abort", "reconstruct"}:
        raise ReplayError(...)
    try:
        outcome = apply_incident_resolve(
            state, action, incident_path, now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(...)
    return outcome.new_state
```

Then update `_HANDLERS` (now 14) and `replay_history` to use the action-token-aware terminal gate (Option B from §4.7).

### 4.11 CLI flow

```python
def cmd_incident_start(args, root):
    # 1. argparse: --bug + --report required; --agent default
    # 2. resolve abs paths + relative_to(root) containment
    # 3. read progress.md to confirm project_state == active and bug_flow.active == false
    # 4. shape validate both paths (use _validate_bug_path_shape for BUG;
    #    add _validate_incident_path_shape for INCIDENT-NNN.md if not already)
    # 5. validate.py file <bug-path>  → exit 0 OR reject (subprocess; capture exit code)
    # 6. validate.py file <incident-path> → exit 0 OR reject (round 2 M6 double-safety)
    # 7. load BUG-NNN.md → root_cause must equal "prd-exception"
    # 8. load INCIDENT-NNN.md → triggered_by_bug must equal BUG bug_id
    # 9. _run_update_pipeline(event_name="incident-start",
    #                         compute_outcome=apply_incident_start(...))


def cmd_incident_resolve(args, root):
    # 1. argparse: --action required (choices=continue|abort|reconstruct); --agent default
    # 2. read progress.md to confirm workflow_incident_active == true and pull incident_report_path
    # 3. validate.py file <incident-path> → exit 0 OR reject
    # 4. load INCIDENT-NNN.md → resolution_action must equal --action AND status == review-passed
    # 5. _run_update_pipeline(event_name="incident-resolve",
    #                         compute_outcome=apply_incident_resolve(...))
    # NB: terminal actions still write progress.md + history; the
    # terminal flag activates ON THE NEXT replay, not the resolve write
    # itself.
```

### 4.12 Tests scope

- `tests/test_apply_incident_start.py` — pure state-machine unit tests (happy + each precondition reject + outcome frozen + bug_flow + incident state mutations + sub_state preserved + non-active bug-flow reject)
- `tests/test_apply_incident_resolve.py` — pure unit tests for 3 actions (continue/abort/reconstruct) × happy + each precondition reject + `is_terminal` flag set correctly + bug_flow cleanup + project_state / release_state mutations
- `tests/test_progress_incident.py` — CLI integration:
  - happy 3 actions × all-fields-mutated check
  - reject when bug already active (incident-start) / no incident active (incident-resolve)
  - validate.py double-safety reject (mock `validate.py` to return 1; assert no progress.md mutation)
  - terminal state semantics: after abort/reconstruct, any subsequent `update` / `release-*` / `bug-*` / `incident-*` rejects; `query` and `recover` still work
  - recover roundtrip preserves state for all 3 actions
  - lock blocking
  - M1 inheritance
- `tests/test_progress_replay.py` — extend `ReplayTerminalSemanticsTests` (currently asserts empty TERMINAL_EVENTS — flip it to assert {"incident-resolve"} + action-aware gate); new `ReplayIncidentTests` with happy / missing tokens / malformed action / continue NOT terminal / abort + reconstruct ARE terminal / mutating entry after abort REJECTED
- Update `supported_events_in_phase_6_2` → `supported_events_in_phase_6_3`, expected set 14 items
- Update "unsupported event" sample in `test_progress_replay.py:ReplayUnsupportedEventTests` and `test_progress_recover.py` from `incident-start` (Phase 6.2 placeholder) to a Phase 6.4 placeholder. Possible candidates: `update-advance` (the canonical replay token shape for the Phase 6.4 advance event TBD; pick a string that won't be in `_HANDLERS` — e.g. `advance` or `update-advance`).
- Update `progress_replay.py` module docstring + unsupported-event error message text to mention 6.3 supported set.

### 4.13 Phase 6.3 NOT in scope

- `update --advance` / P6 matrix evaluation (Phase 6.4)
- `validate.py consistency` Class 8 cross-progress check (Phase 6.4)
- `INCIDENT-NNN.md` body content / `Pending Changes` validation — owned by `workflow-evolution` skill (validate.py shape check is enough here)
- Action-detail post-resolve workflow routing (e.g. who picks up after abort/reconstruct) — that's user/workflow-evolution territory, not progress.py
- Migrating Phase 6.1 / 6.2 helpers — they stay as-is unless an obvious overlap appears

---

## 5. Code Patterns to Follow (Established Conventions)

(Same as Phase 6.2 §5; summarized highlights below.)

### 5.1 New `apply_*` function

1. Frozen `<Cmd>Outcome` dataclass with `new_state / history_summary / history_result / history_next` + command-specific fields.
2. Always inherit invariants:
   - `_validate_timestamp(now, field="now")`
   - `_validate_active_project(state, "<cmd-name>")` — but watch out: `incident-resolve --action abort/reconstruct` flips `project_state` itself, so you can't gate on "project_state must be active"; gate instead on `workflow_incident_active`.
   - `_validate_review_iteration_value(state.get("review_iteration", 0))` (M2)
3. Mutate via `new_state = dict(state); new_state[k] = v`.
4. Emit canonical history summary tokens (`key=value` parseable by `_kv_tokens`).

### 5.2 New replay handler

1. Add `_apply_<cmd>_handler(state, entry, root)` in `progress_replay.py`.
2. Use `_kv_tokens(entry)` to extract summary tokens.
3. Validate required tokens; raise `ReplayError` with "missing" message.
4. Call same `apply_<cmd>` function the forward path uses.
5. `del root`.
6. Register in `_HANDLERS` dict + update `supported_events()` test + module docstring + unsupported-event error text.

### 5.3 New CLI subcommand

1. Add `cmd_<name>` after the existing `cmd_*` functions in `progress.py`.
2. **Round 2 M6 double-safety**: when the command consumes a doc that the caller has already promote+validated (e.g. `incident-start` consumes a workflow-evolution-owned INCIDENT skeleton), re-invoke `validate.py file <path>` inside the CLI before `_run_update_pipeline`. Reject with exit 1 if the second validate fails.
3. Read progress state OUTSIDE `_run_update_pipeline` for pre-flight checks (cleaner error messages).
4. Pass `compute_outcome=lambda state, now: apply_<name>(...)` to the pipeline.
5. Use argparse `required=True` for genuinely-required flags → exit 2; workflow validation failures → exit 1.

### 5.4 Test patterns

- Pure unit tests: `tests/test_apply_<cmd>.py` — no CLI / file I/O except temp dirs for artifact loaders.
- CLI integration: `tests/test_progress_<cmd>.py` — `_install_test_stage_advance_handler` + `_FakeClock` patch.
- For `validate.py file` subprocess calls: consider mocking via `unittest.mock.patch` on the subprocess invoker (or factor it through a tiny helper that tests can monkey-patch). Look at how `cmd_release_start` calls validate.py for a reference (or, if it doesn't, accept this as Phase 6.3's first introduction of the subprocess pattern and document it clearly).
- Replay tests: extend `ReplayTerminalSemanticsTests` for the first time + new `ReplayIncidentTests`.

### 5.5 Critical invariants (recap)

- M1 (replay vs forward state diff)
- M2 (review_iteration ≤ 7)
- L1 canonical history token contract
- replay-skips-artifacts (replay handlers `del root`, never re-read BUG / test-report / verification / **INCIDENT** files)

---

## 6. Recommended Phase 6.3 Work Order

1. **Re-confirm baseline** (`unittest discover` + `compileall`).
2. **Re-confirm Phase 6.2 closure**: read `task6_phase6_2_bug_rework_review_20260507.md` (it's already (A); just confirm the 3 Low fixes from L1/L2/L3 are present in the diff).
3. **Decide Option A vs B for `TERMINAL_EVENTS`** (§4.7). Recommend Option B (action-aware gate). Document the choice in apply_incident_resolve docstring + replay_history dispatch comment so future maintainers see the rationale.
4. **Add `_validate_incident_path_shape`** in `progress_state.py` (mirror `_validate_bug_path_shape` for `docs/incident/INCIDENT-\d{3}\.md`).
5. **Add `IncidentStartOutcome` + `apply_incident_start`** in `progress_state.py`. Add `tests/test_apply_incident_start.py`.
6. **Add `IncidentResolveOutcome` + `apply_incident_resolve`** in `progress_state.py` (3 action branches, each with a clear mutation block). Add `tests/test_apply_incident_resolve.py`.
7. **Register two replay handlers** in `progress_replay.py`. Update `_HANDLERS` to 14, `TERMINAL_EVENTS` populate, `replay_history` action-aware terminal gate, module docstring, unsupported-event error text.
8. **Add `cmd_incident_start` + `cmd_incident_resolve`** to `progress.py` + argparse subparsers + dispatcher. Use `_run_update_pipeline`. Wire double-validate via subprocess to `validate.py file`.
9. **Write `tests/test_progress_incident.py`** (CLI integration; mirror `test_progress_bug_rework.py` style; use mocked validate.py subprocess for the failure paths; cover terminal-state semantics end-to-end).
10. **Extend `tests/test_progress_replay.py`**: flip `ReplayTerminalSemanticsTests` to assert populated set + new `ReplayIncidentTests` (happy / missing tokens / continue not terminal / abort+reconstruct terminal / mutating after terminal rejected).
11. **Update test_progress_replay.py + test_progress_recover.py** "unsupported event" sample from `incident-start` → Phase 6.4 placeholder.
12. **Run full suite + compileall + smoke** (`incident-start --help`, `incident-resolve --help`).
13. **Write Phase 6.3 review prompt** under `docs/review/claude_review_prompt_task6_phase6_3_incident_20260507.md` (template: `docs/review/claude_review_prompt_task6_phase6_2_bug_rework_20260507.md`).

Phase 6.3 acceptance target:

- `progress.py incident-start --help` and `progress.py incident-resolve --help` work
- Happy paths for incident-start + 3 resolve actions all pass
- Replay handlers registered; `supported_events()` returns 14
- `TERMINAL_EVENTS == {"incident-resolve"}` with action-aware terminal gate
- After abort/reconstruct, no further mutating commands accepted
- Recover roundtrip preserves state for all 3 actions
- All previous 637 tests still green; total ≈ 700+
- compileall clean

---

## 7. Watch Points / Common Pitfalls

- **`_validate_active_project` doesn't apply to terminal-actions of `incident-resolve`**: `--action abort` / `reconstruct` mutates `project_state` from `active` to `aborted` / `reconstructing`. Don't gate `apply_incident_resolve` on `project_state == active`; gate on `workflow_incident_active == true`.
- **`prd-exception` is the 4th `bug_flow.root_cause` value but NOT in `_ROOT_CAUSE_TO_STAGE`**: don't add it there (it would break `bug-start` / `bug-rework` legality checks). The `incident-start` mutation writes the literal string `"prd-exception"` directly. `apply_bug_rework` already rejects `prd-exception` (Phase 6.2 added that explicit check); confirm the same is true after Phase 6.3 lands.
- **Action-aware terminal gate**: `seen_terminal = entry.event in TERMINAL_EVENTS` flips ALL `incident-resolve` entries to terminal under naive Option A. Use Option B (parse `action=` token, only flip when `action != "continue"`). Add a dedicated test for "history with `incident-resolve --action continue` followed by another mutating command must NOT reject".
- **`validate.py file` subprocess invocation**: this is the first time progress.py shells out to a sibling script. Pick a clear contract: capture exit code only (don't parse stdout/stderr). Document the contract in the CLI docstring so Phase 7 can audit. Consider a small helper `_validate_doc_via_external(path) -> int` so tests can patch one entry point.
- **Round 2 M6 double-safety**: incident-start validates BOTH `<bug-path>` AND `<incident-path>`; incident-resolve validates `<incident-path>` (already on disk and pointed to by `incident_report_path`). Don't validate the BUG again on resolve — the BUG is by then reference-only.
- **`v0.6 F11` cleanup completeness for abort/reconstruct**: the mutation table includes `sub_state`, `review_iteration`, AND all three `bug_flow` fields being cleared. Easy to forget cleanup of one — write tests that pin every field.
- **`incident-resolve --action continue` reuses retest-passed semantics WITHOUT requiring a passing test report**: spec deliberately resets to `testing/review-passed` so the project can re-run testing. Don't pre-flight a `verification_status==pass` check.
- **`bug_flow.root_cause: prd-exception` after `incident-resolve --action continue`**: cleared to `null` in progress.md, but the BUG-NNN.md file's frontmatter `root_cause: prd-exception` is **not** mutated (historical record). Tests should pin the BUG file unchanged.
- **TERMINAL_EVENTS still empty in current code**: review the `replay_history` dispatch loop carefully before flipping the set — current code sets `seen_terminal = entry.event in TERMINAL_EVENTS` and the only other use of this state is the rejection branch. Add the action-aware gate inline rather than introducing a separate `_is_terminal_entry(entry)` helper unless complexity grows.
- **`progress_history.py` field whitelist still `agent / result / next`** — do not add fields. All new info goes into summary tokens or result text.

---

## 8. Reference Anchors

### 8.1 Existing `apply_*` functions in progress_state.py (line numbers approximate after Phase 6.2 + L3 polish)

- `build_initial_state` — Phase 5.1 init
- `apply_update_event` — Phase 5.2 (sub_state state machine)
- `apply_update_task` — Phase 5.3 (Stage 4 task; Phase 6.1 added Gap-3 branch)
- `apply_release_close` / `apply_release_start` / `apply_bug_intake` — Phase 5.4
- `apply_bug_start` / `apply_bug_close` — Phase 6.1
- `compute_dev_bug_rollback` — Phase 6.2 shared Gap-4 helper
- `apply_bug_rework` — Phase 6.2
- `_validate_bug_path_shape` (Phase 5.4 round 2)
- Phase 6.3 adds: `_validate_incident_path_shape` + `apply_incident_start` + `apply_incident_resolve`

### 8.2 Existing replay handlers (12 in progress_replay._HANDLERS)

- `init` — `_apply_init`
- 4 events (`write-complete` / `review-issues` / `review-passed` / `human-confirmed`) — `_apply_update_event_factory`
- `update-task` — `_apply_update_task`
- `release-close` / `release-start` / `bug-intake` — Phase 5.4 handlers
- `bug-start` / `bug-close` — Phase 6.1 handlers
- `bug-rework` — Phase 6.2 handler

Phase 6.3 adds 13th + 14th: `incident-start` / `incident-resolve`.

### 8.3 progress.py CLI subcommands (10)

`init / query / recover / update (--event / --task) / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework`

Phase 6.3 adds `incident-start / incident-resolve`. Phase 6.4 may add `update --advance` (under existing `update` subparser via mutex group).

### 8.4 Phase 6.2 deliverables

- `docs/review/claude_review_prompt_task6_phase6_2_bug_rework_20260507.md` — review prompt
- `docs/review/task6_phase6_2_bug_rework_review_20260507.md` — review report (A)

### 8.5 Phase 6.2 polish (post-(A) Low fixes, landed before this handoff)

- `skills/workflow-protocol/references/command-reference.md §9` — Append history block updated to canonical-token form (L1)
- `docs/implementation/task6_plan_20260507.md §6.3` step 6 — superseded note (L1)
- `docs/handoff/task6_progress_py_prerequisites_20260506.md §6` step 6 — superseded note (L1)
- `skills/_shared/dev_workflow/progress_replay.py` `_apply_bug_rework_handler` comment — clarified token validation scope (L2)
- `skills/_shared/dev_workflow/progress_artifacts.py` `load_bug_report` `expect_root_cause` mismatch error — generalized for both bug-start and bug-rework callers (L3)

---

## 9. Final Checklist Before New Session Codes

The new session should:

- [ ] Read items 1-10 of §0 in order.
- [ ] Run `python3 -m unittest discover -s tests` and confirm 637 OK + compileall clean.
- [ ] Confirm Phase 6.2 closure (review (A) verdict + 3 Low polish landed; do NOT re-open those decisions).
- [ ] Pick `TERMINAL_EVENTS` design (§4.7 Option A vs B) — recommend B (action-aware gate via summary token) — and record the choice in apply_incident_resolve docstring + replay_history comment.
- [ ] Decide `update-advance` placeholder string for unsupported-event sample (§4.12 last bullet).
- [ ] Use the test patterns in §5.4 — synthetic stage-advance handlers + `_FakeClock` + mocked validate.py subprocess for double-safety reject tests.
- [ ] Generate Phase 6.3 review prompt at the end and ask reviewer for (A); follow round-1 → round-2 → (A) cycle as in earlier phases.

When Phase 6.3 closes, write a Phase 6.4 handoff (mirror this doc) and continue with `update --advance` + `validate.py consistency`.
