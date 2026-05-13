#!/usr/bin/env python3
"""workflow-protocol progress.py — workflow state machine binary.

Phase 5.1 owns these subcommands:

- ``init --project <name> --scenario <S1|S3> --release <x.y>``
  Create ``progress.md`` + ``progress-history.md`` for a brand-new
  project. Refuses to overwrite any existing file. Locks
  ``.progress.lock``.

- ``query [--field <name>] [--json]``
  Read-only inspection. No lock; safe for concurrent callers.

- ``recover --confirm``
  Replay ``progress-history.md`` through the shared replay validator and
  rewrite ``progress.md`` from the resulting state. Phase 5.1's replay
  validator only knows about ``init``; later phases extend the validator
  rather than this CLI.

Phase 5.2 / 5.3 / 5.4 / Phase 6 will add ``update --event``,
``update --task``, ``release-*``, ``bug-*``, ``incident-*``, and
``update --advance``.

Spec sources:
  - ``skills/workflow-protocol/references/command-reference.md`` §1, §3, §4
  - ``docs/implementation/task6_plan_20260507.md`` §5

Exit codes:
  - ``0`` — success
  - ``1`` — precondition / state-machine / replay / I/O failure
  - ``2`` — CLI usage error
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import sys

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Phase 6.3: incident-start / incident-resolve invoke
# ``doc-guardian/scripts/validate.py`` for round 2 M6 double-safety
# re-validation of BUG / INCIDENT documents. We import the script as a
# Python module rather than spawning a subprocess so error capture and
# test mocking are straightforward, and the same Python interpreter
# (and venv) is used. ``validate_doc`` below is the single CLI-side
# entry point; tests can patch it.
_DOC_GUARDIAN_SCRIPTS = _REPO_ROOT / "skills" / "doc-guardian" / "scripts"
if str(_DOC_GUARDIAN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_DOC_GUARDIAN_SCRIPTS))

import yaml  # noqa: E402

from skills._shared.dev_workflow.atomic import (  # noqa: E402
    AtomicWriteError,
    transaction,
)
from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    FrontmatterError,
    read_markdown,
)
from skills._shared.dev_workflow.progress_history import (  # noqa: E402
    HISTORY_TITLE_LINE,
    HistoryEntry,
    HistoryError,
    append_history_text,
    initial_history_text,
    parse_history_text,
)
from skills._shared.dev_workflow.progress_lock import (  # noqa: E402
    ProgressLockError,
    progress_lock,
)
from skills._shared.dev_workflow.progress_replay import (  # noqa: E402
    ReplayError,
    replay_history,
)
from skills._shared.dev_workflow.progress_artifacts import (  # noqa: E402
    ProgressArtifactError,
)
from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    render_markdown as _render_markdown,
)
from skills._shared.dev_workflow.progress_state import (  # noqa: E402
    EVENTS as UPDATE_EVENT_NAMES,
    GATED_STAGES,
    NEXT_STAGE,
    PROGRESS_BODY_TEMPLATE,
    ProgressStateError,
    RELEASE_START_SUBTYPES,
    ROOT_CAUSES_FOR_BUG_START,
    SCENARIOS_INIT,
    TASK_STATES,
    _validate_bug_path_shape,
    _validate_incident_path_shape,
    apply_bug_close,
    apply_bug_intake,
    apply_bug_rework,
    apply_bug_start,
    apply_incident_resolve,
    apply_incident_start,
    apply_release_close,
    apply_release_start,
    apply_update_advance,
    apply_update_event,
    apply_update_task,
    build_initial_state,
    compute_dev_bug_rollback,
    render_progress_text,
)


PROGRESS_FILENAME = "progress.md"
HISTORY_FILENAME = "progress-history.md"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- init ----------


def _build_init_history_entry(
    *,
    project: str,
    scenario: str,
    release: str,
    now: str,
    agent: str,
) -> HistoryEntry:
    return HistoryEntry(
        timestamp=now,
        event="init",
        summary=(
            "project created — "
            f"project={project}, scenario={scenario}, release={release}"
        ),
        agent=agent,
        result=f"workflow_version=v0.6, current_stage=prd-inception/write",
        next="prd-write",
        raw="",
    )


def cmd_init(args: argparse.Namespace, root: Path) -> int:
    project = args.project
    scenario = args.scenario
    release = args.release
    agent = args.agent

    progress_path = root / PROGRESS_FILENAME
    history_path = root / HISTORY_FILENAME

    try:
        with progress_lock(root, timeout=args.lock_timeout):
            if progress_path.exists():
                print(
                    f"progress.py init: refusing to overwrite existing {progress_path}",
                    file=sys.stderr,
                )
                return 1
            if history_path.exists():
                print(
                    f"progress.py init: refusing to overwrite existing {history_path}",
                    file=sys.stderr,
                )
                return 1

            now = _utc_now_iso()
            try:
                state = build_initial_state(
                    project=project,
                    scenario=scenario,
                    release=release,
                    now=now,
                )
            except ProgressStateError as exc:
                print(f"progress.py init: {exc}", file=sys.stderr)
                return 1

            entry = _build_init_history_entry(
                project=project,
                scenario=scenario,
                release=release,
                now=now,
                agent=agent,
            )
            progress_text = render_progress_text(state, PROGRESS_BODY_TEMPLATE)
            history_text = initial_history_text(entry)

            try:
                with transaction() as tx:
                    tx.write_text(progress_path, progress_text)
                    tx.write_text(history_path, history_text)
            except (AtomicWriteError, OSError) as exc:
                print(
                    f"progress.py init: atomic write failed: {exc}",
                    file=sys.stderr,
                )
                return 1
    except ProgressLockError as exc:
        print(f"progress.py init: {exc}", file=sys.stderr)
        return 1

    print(
        f"progress.py init: created {progress_path.name} and {history_path.name} "
        f"(project={project}, scenario={scenario}, release={release})"
    )
    return 0


# ---------- query ----------


def cmd_query(args: argparse.Namespace, root: Path) -> int:
    progress_path = root / PROGRESS_FILENAME
    if not progress_path.exists():
        print(
            f"progress.py query: {progress_path} not found; run 'progress.py init' first",
            file=sys.stderr,
        )
        return 1
    try:
        doc = read_markdown(progress_path)
    except FrontmatterError as exc:
        print(f"progress.py query: cannot parse frontmatter: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"progress.py query: cannot read {progress_path}: {exc}", file=sys.stderr)
        return 1

    state = doc.frontmatter
    if args.field is not None:
        if args.field not in state:
            print(
                f"progress.py query: field {args.field!r} not present",
                file=sys.stderr,
            )
            return 1
        value = state[args.field]
        if args.json_output:
            print(json.dumps(value, ensure_ascii=False, sort_keys=False))
        else:
            print(_format_scalar(value))
        return 0

    if args.json_output:
        print(json.dumps(state, ensure_ascii=False, sort_keys=False, default=str))
    else:
        sys.stdout.write(
            yaml.safe_dump(
                dict(state),
                allow_unicode=True,
                default_flow_style=False,
                sort_keys=False,
            )
        )
    return 0


def _format_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value)
    return yaml.safe_dump(
        value, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


# ---------- recover ----------


def cmd_recover(args: argparse.Namespace, root: Path) -> int:
    if not args.confirm:
        print(
            "progress.py recover: refusing to rebuild without --confirm",
            file=sys.stderr,
        )
        return 1

    history_path = root / HISTORY_FILENAME
    progress_path = root / PROGRESS_FILENAME
    if not history_path.exists():
        print(
            f"progress.py recover: {history_path} not found; cannot replay",
            file=sys.stderr,
        )
        return 1

    try:
        with progress_lock(root, timeout=args.lock_timeout):
            try:
                history_text = history_path.read_text(encoding="utf-8")
            except OSError as exc:
                print(
                    f"progress.py recover: cannot read history: {exc}",
                    file=sys.stderr,
                )
                return 1
            try:
                history_entries = parse_history_text(history_text)
            except HistoryError as exc:
                print(
                    f"progress.py recover: cannot parse history: {exc}",
                    file=sys.stderr,
                )
                return 1
            if not history_entries:
                print(
                    "progress.py recover: history is empty; nothing to replay",
                    file=sys.stderr,
                )
                return 1

            try:
                state = replay_history(history_entries, root=root)
            except ReplayError as exc:
                print(f"progress.py recover: {exc}", file=sys.stderr)
                return 1

            # Bump `updated` to the time of recovery so consumers can see
            # the rebuild happened. `created` still reflects history.
            state = dict(state)
            state["updated"] = _utc_now_iso()

            progress_text = render_progress_text(state, PROGRESS_BODY_TEMPLATE)
            try:
                with transaction() as tx:
                    tx.write_text(progress_path, progress_text)
            except (AtomicWriteError, OSError) as exc:
                print(
                    f"progress.py recover: atomic write failed: {exc}",
                    file=sys.stderr,
                )
                return 1
    except ProgressLockError as exc:
        print(f"progress.py recover: {exc}", file=sys.stderr)
        return 1

    print(
        f"progress.py recover: rebuilt {progress_path.name} from "
        f"{len(history_entries)} history entr{'y' if len(history_entries) == 1 else 'ies'}"
    )
    return 0


# ---------- update ----------


def cmd_update(args: argparse.Namespace, root: Path) -> int:
    """Dispatch ``progress.py update`` by mutex-group mode.

    Phase 5.2 implemented ``--event``. Phase 5.3 adds ``--task``. Phase
    6.4 adds ``--advance`` (P6 matrix). Each mode computes a per-event
    outcome (``EventOutcome`` / ``TaskOutcome`` / ``AdvanceOutcome``)
    but shares the lock + history parse + replay-consistency +
    atomic-write pipeline below.
    """

    if args.event is not None:
        return _do_update_event(args, root)
    if args.task is not None:
        return _do_update_task(args, root)
    if getattr(args, "advance", False):
        return _do_update_advance(args, root)
    # The argparse mutually-exclusive group enforces required-one-of with
    # SystemExit(2). This branch is defensive for direct API callers.
    print(
        "progress.py update: one of --event / --task / --advance is required",
        file=sys.stderr,
    )
    return 2


def _do_update_event(args: argparse.Namespace, root: Path) -> int:
    return _run_update_pipeline(
        args=args,
        root=root,
        event_name=args.event,
        compute_outcome=lambda state, now: apply_update_event(
            state, args.event, now=now,
        ),
        success_label=f"event {args.event}",
    )


def _do_update_task(args: argparse.Namespace, root: Path) -> int:
    if args.status is None:
        print(
            "progress.py update --task: --status is required",
            file=sys.stderr,
        )
        return 2
    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="update-task",
        compute_outcome=lambda state, now: apply_update_task(
            state, args.task, args.status,
            now=now, root=root,
        ),
        success_label=f"update-task {args.task}={args.status}",
    )


def _do_update_advance(args: argparse.Namespace, root: Path) -> int:
    """Phase 6.4 P6 matrix forward path.

    Per ``command-reference.md §2.2``: advance preconditions are five
    dimensions (A artifacts exist, B doc-guardian validate, C review
    approved, D human gate, E verification status). C/D collapse into
    the sub_state precondition that ``apply_update_advance`` enforces;
    A/B/E run inside the locked critical section against the freshly
    re-read progress.md (round 2 M1 contract — see
    :func:`_run_p6_advance_preflight`).

    Round 2 M1 fix: A/B/E moved INTO the ``compute_outcome`` lambda,
    which ``_run_update_pipeline`` calls with the locked state. Before
    the round 2 fix these checks ran against an unlocked pre-read, so
    a parallel mutating command between read and lock could let the
    advance bypass P6 for the new stage.
    """

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="update-advance",
        compute_outcome=lambda state, now: _advance_compute_outcome(
            state, now, root,
        ),
        success_label="update-advance",
    )


def _advance_compute_outcome(state: dict, now: str, root: Path):
    """Locked-state preflight + apply for ``update --advance``.

    Runs inside ``_run_update_pipeline`` after the lock is held and
    progress.md has been re-read (the ``state`` argument IS the locked
    frontmatter). Order:

      1. Validate progress.md.current_stage shape.
      2. If current_stage has no next stage, skip P6 and let
         apply_update_advance produce the canonical "no next stage"
         error message.
      3. Otherwise run P6 A (existence) + B (validate.py file) + E
         (stage-specific verification status). Any failure raises
         :class:`ProgressStateError` whose message the pipeline prints
         as ``progress.py update: <msg>``; progress.md is not mutated.
      4. Call :func:`apply_update_advance` for the actual state-machine
         transition.
    """

    current_stage = state.get("current_stage")
    if not isinstance(current_stage, str):
        raise ProgressStateError(
            f"progress.md.current_stage must be a string, got "
            f"{type(current_stage).__name__}"
        )

    if current_stage in NEXT_STAGE:
        _run_p6_advance_preflight(state, current_stage, root)

    return apply_update_advance(state, now=now)


def _run_p6_advance_preflight(
    state: dict, current_stage: str, root: Path,
) -> None:
    """P6 A/B/E checks against the supplied (locked) frontmatter.

    Raises :class:`ProgressStateError` whose message is a multi-line
    block describing every dimension-A missing path, every dimension-B
    per-file issue, or the dimension-E verification problem. The
    pipeline catches the error and prints it to stderr without mutating
    progress.md.

    Aggregation behavior (so an operator can fix in one round):
      * Dimension A collects ALL missing required artifacts.
      * Dimension B runs validate_doc on every existing required artifact
        and lists every per-file issue.
      * Dimension E reports the first stage-specific failure (testing
        and delivery only — development surrogate is enforced by
        apply_update_advance, other stages have no E dimension).
    """

    try:
        from skills._shared.dev_workflow.artifacts import (
            ArtifactError,
            get_required_artifacts,
        )

        specs = get_required_artifacts(state, root=root)
    except ArtifactError as exc:
        raise ProgressStateError(
            f"required-artifact derivation failed: {exc}"
        )
    except (KeyError, TypeError, AttributeError) as exc:
        # Round 2 M2: progress.md may parse as YAML yet still lack
        # resolver-required fields (scenario / release / current_stage).
        # Convert any structural lookup failure into a clean error.
        raise ProgressStateError(
            f"progress.md is structurally incomplete; required-artifact "
            f"resolver inputs are missing or wrong type: {exc!r}"
        )

    seen_paths: set[str] = set()
    missing: list[str] = []
    present_paths: list[str] = []
    for spec in specs:
        if spec.path in seen_paths:
            continue
        seen_paths.add(spec.path)
        if not (root / spec.path).exists():
            missing.append(spec.path)
        else:
            present_paths.append(spec.path)
    if missing:
        lines = ["P6 dimension A failed; required artifacts missing:"]
        for path in missing:
            lines.append(f"- {path}")
        raise ProgressStateError("\n".join(lines))

    b_issues: list[tuple[str, str]] = []
    for path in present_paths:
        for issue in validate_doc(path, root):
            b_issues.append((path, issue))
    if b_issues:
        lines = ["P6 dimension B failed; doc-guardian rejected required artifacts:"]
        for path, issue in b_issues:
            lines.append(f"- {path}: {issue}")
        raise ProgressStateError("\n".join(lines))

    e_issue = _check_p6_dim_e(current_stage, state, root)
    if e_issue is not None:
        raise ProgressStateError(
            f"P6 dimension E failed; {e_issue}"
        )


def _check_p6_dim_e(current_stage: str, fm: dict, root: Path) -> str | None:
    """P6 E dimension: verification_status==pass for stages 4/5/6.

    Returns the failing-message string if the check fails, else None.
    Stage 4 surrogate (all task_states verified) is enforced by
    apply_update_advance; this function only handles per-stage
    verification artifacts (Stage 4 per-task verification_result.md is
    not re-read here because apply already trusts the registered
    task_states).
    """

    from skills._shared.dev_workflow.progress_artifacts import (
        load_artifact_frontmatter,
        load_test_report,
    )

    release = fm.get("release")
    if not isinstance(release, str) or not release:
        return (
            "progress.md.release is missing or non-string; cannot read "
            "stage verification artifact"
        )

    if current_stage == "testing":
        try:
            info = load_test_report(root, release=release)
        except ProgressArtifactError as exc:
            return f"cannot load test-report: {exc}"
        if info.verification_status != "pass":
            return (
                f"latest test-report at {info.rel_path} has "
                f"verification_status={info.verification_status!r}; "
                "advance from testing requires 'pass' "
                "(use bug-start / bug-rework for fail/partial)"
            )
        return None

    if current_stage == "delivery":
        try:
            info = load_artifact_frontmatter(
                root, doc_type="installation-result", release=release,
            )
        except ProgressArtifactError as exc:
            return f"cannot load installation-result: {exc}"
        raw_status = info.fields.get("verification_status")
        if raw_status != "pass":
            return (
                f"installation-result at {info.rel_path} has "
                f"verification_status={raw_status!r}; advance from "
                "delivery requires 'pass'"
            )
        return None

    # Stage 4 (development): apply_update_advance enforces "all
    # task_states verified" — no per-task verification_result.md re-read
    # here (each verifying→verified transition already passed).
    # Other stages (PRD/SRS/Architecture/retrospective): no E dimension.
    return None


def _run_update_pipeline(
    *,
    args: argparse.Namespace,
    root: Path,
    event_name: str,
    compute_outcome,
    success_label: str,
    extra_writes_factory=None,
) -> int:
    """Shared lock + parse + apply + replay + atomic-write pipeline.

    ``compute_outcome(progress_state, now)`` returns an outcome with
    ``new_state`` / ``history_summary`` / ``history_result`` /
    ``history_next``. The pipeline duck-types the outcome; any of the
    Phase 5.2/5.3/5.4 outcome dataclasses are accepted.

    ``extra_writes_factory(outcome, root) -> Iterable[(Path, str)]``
    (optional) lets a command queue additional file writes inside the
    same atomic transaction as ``progress.md`` + ``progress-history.md``.
    Phase 5.4 ``release-start`` uses it to fan out BUG frontmatter
    mutations (``target_release`` / ``consumed_in_release``).
    """

    progress_path = root / PROGRESS_FILENAME
    history_path = root / HISTORY_FILENAME

    try:
        with progress_lock(root, timeout=args.lock_timeout):
            if not progress_path.exists():
                print(
                    f"progress.py update: {progress_path} not found; "
                    "run 'progress.py init' first",
                    file=sys.stderr,
                )
                return 1
            if not history_path.exists():
                print(
                    f"progress.py update: {history_path} not found; cannot append entry",
                    file=sys.stderr,
                )
                return 1

            try:
                progress_doc = read_markdown(progress_path)
            except FrontmatterError as exc:
                print(
                    f"progress.py update: cannot parse {progress_path}: {exc}",
                    file=sys.stderr,
                )
                return 1
            except OSError as exc:
                print(
                    f"progress.py update: cannot read {progress_path}: {exc}",
                    file=sys.stderr,
                )
                return 1

            try:
                history_text = history_path.read_text(encoding="utf-8")
            except OSError as exc:
                print(
                    f"progress.py update: cannot read history: {exc}",
                    file=sys.stderr,
                )
                return 1

            # Round 2 M1: refuse to append to a malformed history. Without
            # this guard, a corrupt history would silently grow, and a
            # later 'recover --confirm' would then be unable to replay.
            try:
                parse_history_text(history_text)
            except HistoryError as exc:
                print(
                    f"progress.py update: existing progress-history.md is malformed: {exc}",
                    file=sys.stderr,
                )
                return 1

            now = _utc_now_iso()
            try:
                outcome = compute_outcome(progress_doc.frontmatter, now)
            except ProgressStateError as exc:
                print(f"progress.py update: {exc}", file=sys.stderr)
                return 1
            except ProgressArtifactError as exc:
                print(f"progress.py update: {exc}", file=sys.stderr)
                return 1

            entry = HistoryEntry(
                timestamp=now,
                event=event_name,
                summary=outcome.history_summary,
                agent=args.agent,
                result=outcome.history_result,
                next=outcome.history_next,
                raw="",
            )
            new_history_text = append_history_text(history_text, entry)
            new_progress_text = render_progress_text(
                outcome.new_state, PROGRESS_BODY_TEMPLATE
            )

            # Phase 5.2 round 2 M1: replay the composed history end-to-end
            # before writing. The replay re-derives state from ``init`` plus
            # every prior event entry; if the forward outcome computed from
            # progress.md diverges from the canonical history replay (e.g.
            # progress.md was edited out-of-band), the diff catches it and
            # we refuse to commit.
            #
            # ``root`` is forwarded because the ``update-task`` replay
            # handler defensively requires it. Phase 5.3 design choice:
            # replay does NOT re-evaluate Stage 4 artifact preconditions
            # (reports mutate from skeleton to pass/fail across
            # transitions, so re-checking against "current" artifacts
            # would false-fail historical entries). Forward path is the
            # gatekeeper for artifact state at write time.
            try:
                replayed_entries = parse_history_text(new_history_text)
                replayed_state = replay_history(
                    replayed_entries, root=root,
                )
            except HistoryError as exc:
                print(
                    f"progress.py update: composed history is malformed: {exc}",
                    file=sys.stderr,
                )
                return 1
            except ReplayError as exc:
                print(
                    f"progress.py update: composed history fails replay: {exc}",
                    file=sys.stderr,
                )
                return 1

            if replayed_state != outcome.new_state:
                diff_keys = sorted(
                    key
                    for key in set(outcome.new_state) | set(replayed_state)
                    if outcome.new_state.get(key) != replayed_state.get(key)
                )
                print(
                    "progress.py update: replay consistency check failed; "
                    f"forward outcome diverges from history replay on fields {diff_keys}; "
                    "progress.md may have been edited out-of-band — "
                    "run 'progress.py recover --confirm' to rebuild from history",
                    file=sys.stderr,
                )
                return 1

            extra_writes: list[tuple[Path, str]] = []
            if extra_writes_factory is not None:
                try:
                    extra_writes = list(extra_writes_factory(outcome, root))
                except (
                    ProgressStateError,
                    ProgressArtifactError,
                    FrontmatterError,
                ) as exc:
                    print(
                        f"progress.py update: extra-write factory failed: {exc}",
                        file=sys.stderr,
                    )
                    return 1
                except OSError as exc:
                    print(
                        f"progress.py update: extra-write factory I/O failed: {exc}",
                        file=sys.stderr,
                    )
                    return 1

            try:
                with transaction() as tx:
                    tx.write_text(progress_path, new_progress_text)
                    tx.write_text(history_path, new_history_text)
                    for extra_path, extra_text in extra_writes:
                        tx.write_text(extra_path, extra_text)
            except (AtomicWriteError, OSError) as exc:
                print(
                    f"progress.py update: atomic write failed: {exc}",
                    file=sys.stderr,
                )
                return 1
    except ProgressLockError as exc:
        print(f"progress.py update: {exc}", file=sys.stderr)
        return 1

    print(
        f"progress.py update: applied {success_label} -> {outcome.history_summary}"
    )
    return 0


# ---------- release-close ----------


def cmd_release_close(args: argparse.Namespace, root: Path) -> int:
    """End-of-Stage-7 release close. Mutates progress.md only."""

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="release-close",
        compute_outcome=lambda state, now: apply_release_close(state, now=now),
        success_label="release-close",
    )


# ---------- bug-intake ----------


def _validate_bug_for_intake(
    abs_bug: Path, rel_bug: str, current_unresolved: list,
) -> tuple[int, str | None]:
    """Thin frontmatter check for bug-intake.

    Returns ``(exit_code, error_message)``. ``exit_code == 0`` means the
    BUG is acceptable for intake; otherwise the message has already
    been formatted with ``progress.py bug-intake:`` prefix and should
    be printed to stderr verbatim.
    """

    if not abs_bug.exists():
        return 1, f"BUG file not found: {abs_bug}"
    try:
        bug_doc = read_markdown(abs_bug)
    except FrontmatterError as exc:
        return 1, f"cannot parse BUG frontmatter: {exc}"
    except OSError as exc:
        return 1, f"cannot read BUG: {exc}"

    fm = bug_doc.frontmatter
    if fm.get("type") != "bug-report":
        return 1, (
            f"BUG file type must be 'bug-report', got {fm.get('type')!r}"
        )
    if fm.get("target_release") is not None:
        return 1, (
            "BUG target_release must be null at intake, got "
            f"{fm.get('target_release')!r}"
        )
    if fm.get("consumed_in_release") is not None:
        return 1, (
            "BUG consumed_in_release must be null at intake, got "
            f"{fm.get('consumed_in_release')!r}"
        )
    if rel_bug in current_unresolved:
        return 1, (
            f"BUG path {rel_bug!r} already in unresolved_bugs (duplicate intake)"
        )
    return 0, None


def cmd_bug_intake(args: argparse.Namespace, root: Path) -> int:
    """Append a post-close BUG path to unresolved_bugs."""

    raw_bug = Path(args.bug)
    abs_bug = raw_bug if raw_bug.is_absolute() else (root / raw_bug)
    abs_bug = abs_bug.resolve()
    try:
        rel_bug = str(abs_bug.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        print(
            f"progress.py bug-intake: BUG path must lie under --root, got {abs_bug}",
            file=sys.stderr,
        )
        return 1

    # Read progress unresolved_bugs first (independent of pipeline lock,
    # since the pipeline acquires its own lock; we re-validate after lock
    # acquisition via apply_bug_intake's duplicate check, so this is just
    # the eager guard).
    progress_path = root / PROGRESS_FILENAME
    current_unresolved: list = []
    if progress_path.exists():
        try:
            current_unresolved = list(
                read_markdown(progress_path).frontmatter.get("unresolved_bugs") or []
            )
        except (FrontmatterError, OSError):
            # Defer to the pipeline; it will surface a clearer error.
            current_unresolved = []

    code, msg = _validate_bug_for_intake(abs_bug, rel_bug, current_unresolved)
    if code != 0:
        print(f"progress.py bug-intake: {msg}", file=sys.stderr)
        return code

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="bug-intake",
        compute_outcome=lambda state, now: apply_bug_intake(
            state, rel_bug, now=now,
        ),
        success_label=f"bug-intake {rel_bug}",
    )


# ---------- release-start ----------


def _read_bug_for_release_start(
    bug_rel: str, root: Path
) -> tuple[Path, dict, str]:
    """Load and minimally validate one BUG file for release-start.

    Returns ``(abs_path, frontmatter_dict, body)``. Raises
    :class:`ProgressArtifactError` if the BUG is missing, has the wrong
    type, or already has a non-null ``target_release`` /
    ``consumed_in_release`` (which would mean it was consumed by an
    earlier release and should not be re-consumed).

    Phase 5.4 round 2 M1: BUG paths in ``unresolved_bugs`` must be
    canonical project-relative ``docs/bug/BUG-NNN.md`` strings AND must
    resolve under ``--root`` after symlinks. The shape check is shared
    with ``apply_bug_intake`` (state-machine layer); the containment
    check is forward-only because replay does not read BUG files.
    """

    try:
        _validate_bug_path_shape(bug_rel)
    except ProgressStateError as exc:
        raise ProgressArtifactError(str(exc)) from exc

    abs_bug = (root / bug_rel).resolve()
    root_resolved = root.resolve()
    try:
        abs_bug.relative_to(root_resolved)
    except ValueError:
        raise ProgressArtifactError(
            f"BUG path {bug_rel!r} resolves outside --root "
            f"({abs_bug}); refusing to fan out release-start writes"
        )

    if not abs_bug.exists():
        raise ProgressArtifactError(
            f"unresolved BUG file missing: {bug_rel}"
        )
    try:
        bug_doc = read_markdown(abs_bug)
    except FrontmatterError as exc:
        raise ProgressArtifactError(
            f"{bug_rel}: cannot parse BUG frontmatter: {exc}"
        ) from exc
    fm = bug_doc.frontmatter
    if fm.get("type") != "bug-report":
        raise ProgressArtifactError(
            f"{bug_rel}: BUG type must be 'bug-report', got {fm.get('type')!r}"
        )
    if fm.get("target_release") is not None:
        raise ProgressArtifactError(
            f"{bug_rel}: BUG target_release must be null at release-start, "
            f"got {fm.get('target_release')!r} (already consumed?)"
        )
    if fm.get("consumed_in_release") is not None:
        raise ProgressArtifactError(
            f"{bug_rel}: BUG consumed_in_release must be null at release-start, "
            f"got {fm.get('consumed_in_release')!r}"
        )
    return abs_bug, dict(fm), bug_doc.body


def _release_start_extra_writes(outcome, root: Path):
    """Build (path, content) writes for each consumed BUG.

    The forward path mutates ``target_release`` and ``consumed_in_release``
    in-place inside the same atomic transaction as ``progress.md`` /
    ``progress-history.md``. Replay does NOT re-write BUG files; the
    write happened once at forward time and the on-disk frontmatter is
    the source of truth thereafter.
    """

    new_release = outcome.new_state["release"]
    writes: list[tuple[Path, str]] = []
    for bug_rel in outcome.consumed_bugs:
        abs_bug, fm, body = _read_bug_for_release_start(bug_rel, root)
        fm["target_release"] = new_release
        fm["consumed_in_release"] = new_release
        # Bump the BUG's `updated` so doc-guardian downstream tools can see
        # the consumption. `created` is preserved.
        fm["updated"] = outcome.new_state["updated"]
        rendered = _render_markdown(fm, body)
        writes.append((abs_bug, rendered))
    return writes


def cmd_release_start(args: argparse.Namespace, root: Path) -> int:
    """Start a new active release; consume unresolved BUGs into target_release."""

    if args.version is None:
        print(
            "progress.py release-start: --version is required",
            file=sys.stderr,
        )
        return 2
    if args.scenario is None:
        print(
            "progress.py release-start: --scenario is required",
            file=sys.stderr,
        )
        return 2

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="release-start",
        compute_outcome=lambda state, now: apply_release_start(
            state,
            new_version=args.version,
            scenario_subtype=args.scenario,
            now=now,
        ),
        success_label=f"release-start version={args.version} scenario={args.scenario}",
        extra_writes_factory=_release_start_extra_writes,
    )


# ---------- bug-start / bug-close ----------


def cmd_bug_start(args: argparse.Namespace, root: Path) -> int:
    """Enter active Bug Flow for the given BUG-NNN.md."""

    if args.bug is None:
        print(
            "progress.py bug-start: --bug is required", file=sys.stderr,
        )
        return 2
    if args.root_cause is None:
        print(
            "progress.py bug-start: --root-cause is required",
            file=sys.stderr,
        )
        return 2

    raw_bug = Path(args.bug)
    abs_bug = raw_bug if raw_bug.is_absolute() else (root / raw_bug)
    abs_bug = abs_bug.resolve()
    try:
        rel_bug = str(abs_bug.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        print(
            f"progress.py bug-start: BUG path must lie under --root, got {abs_bug}",
            file=sys.stderr,
        )
        return 1

    # Read BUG to validate type/root_cause + grab body for Triage Analysis.
    try:
        from skills._shared.dev_workflow.progress_artifacts import (
            load_bug_report,
            parse_bug_triage_analysis,
        )

        bug_info = load_bug_report(
            root, rel_bug, expect_root_cause=args.root_cause,
        )
    except ProgressArtifactError as exc:
        print(f"progress.py bug-start: {exc}", file=sys.stderr)
        return 1

    triage = None
    if args.root_cause == "development":
        try:
            triage = parse_bug_triage_analysis(
                bug_info.body, rel_path=rel_bug,
            )
        except ProgressArtifactError as exc:
            print(f"progress.py bug-start: {exc}", file=sys.stderr)
            return 1

    # Read current progress state to compute Gap-4 rollback (dev only).
    progress_path = root / PROGRESS_FILENAME
    rollback_decisions: tuple[tuple[str, str, str, str], ...] = ()
    if args.root_cause == "development" and progress_path.exists() and triage is not None:
        try:
            doc = read_markdown(progress_path)
        except FrontmatterError:
            # Defer to the pipeline; it will surface the parse error.
            doc = None
        if doc is not None:
            rollback_decisions = compute_dev_bug_rollback(
                dict(doc.frontmatter), triage,
            )

    # Phase 6.1 round 2 L1: dev root cause without auto-rollback must
    # surface a stderr warning so the operator notices the planning
    # route requirement. The persistent record lives in
    # apply_bug_start's history_result / history_next (replay-safe).
    if (
        args.root_cause == "development"
        and triage is not None
        and not rollback_decisions
    ):
        if triage.unable_to_localize:
            reason = "marks 'unable to localize'"
        elif triage.classification == "ambiguous":
            reason = "classification is ambiguous"
        elif triage.affected_tasks:
            reason = (
                "affected task(s) "
                f"{list(triage.affected_tasks)} not in a state eligible for "
                "Gap-4 rollback"
            )
        else:
            reason = "yields no rollback decisions"
        print(
            f"progress.py bug-start: BUG '## Triage Analysis' {reason}; "
            "no auto-rollback applied. Caller must invoke "
            "development-planning-write to replan/route the fix.",
            file=sys.stderr,
        )

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="bug-start",
        compute_outcome=lambda state, now: apply_bug_start(
            state,
            rel_bug,
            args.root_cause,
            now=now,
            rollback_decisions=rollback_decisions,
        ),
        success_label=(
            f"bug-start bug={rel_bug} root_cause={args.root_cause}"
        ),
    )


def cmd_bug_rework(args: argparse.Namespace, root: Path) -> int:
    """Re-route an active Bug Flow whose retest came back fail/partial.

    Per ``command-reference.md §9`` (Phase 6.2 / Gap-5): the active
    BUG already routed once via ``bug-start``, the fix landed, retest
    ran, and the latest test-report now shows ``fail`` or ``partial``.
    ``bug-rework`` returns ``current_stage`` to the same root-cause
    stage with ``sub_state=write`` and ``review_iteration=0``, so the
    relevant Change Mode write skill can iterate again.

    Pre-flight gates (state-machine legality lives in
    :func:`apply_bug_rework`; the CLI checks artifact preconditions
    here so error messages stay specific):
      * ``progress.md`` exists and parses;
      * ``bug_flow.active == true`` (otherwise no rework target);
      * ``bug_flow.bug_report_path`` is recorded as a string;
      * the supplied ``--bug`` resolves to the same path;
      * the BUG file's frontmatter ``root_cause`` matches
        ``bug_flow.root_cause``;
      * the latest ``docs/release<release>/testing/report.md`` shows
        ``verification_status in {fail, partial}`` (not ``pass`` —
        that case is ``bug-close``).
    """

    if args.bug is None:
        print(
            "progress.py bug-rework: --bug is required", file=sys.stderr,
        )
        return 2

    raw_bug = Path(args.bug)
    abs_bug = raw_bug if raw_bug.is_absolute() else (root / raw_bug)
    abs_bug = abs_bug.resolve()
    try:
        rel_bug = str(abs_bug.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        print(
            f"progress.py bug-rework: BUG path must lie under --root, got {abs_bug}",
            file=sys.stderr,
        )
        return 1

    progress_path = root / PROGRESS_FILENAME
    if not progress_path.exists():
        print(
            f"progress.py bug-rework: {progress_path} not found; "
            "run 'progress.py init' first",
            file=sys.stderr,
        )
        return 1
    try:
        progress_doc = read_markdown(progress_path)
    except FrontmatterError as exc:
        print(
            f"progress.py bug-rework: cannot parse {progress_path}: {exc}",
            file=sys.stderr,
        )
        return 1
    fm = progress_doc.frontmatter

    bug_flow = fm.get("bug_flow") or {}
    if not bug_flow.get("active"):
        print(
            "progress.py bug-rework: bug_flow is not active; "
            "use 'bug-start' to enter Bug Flow first",
            file=sys.stderr,
        )
        return 1
    active_path = bug_flow.get("bug_report_path")
    if active_path != rel_bug:
        print(
            f"progress.py bug-rework: --bug {rel_bug!r} does not match "
            f"active bug_flow.bug_report_path {active_path!r}; refuse "
            "to rework a different BUG (use bug-close + bug-start for a "
            "new issue)",
            file=sys.stderr,
        )
        return 1
    active_root_cause = bug_flow.get("root_cause")
    if active_root_cause not in ROOT_CAUSES_FOR_BUG_START:
        print(
            f"progress.py bug-rework: bug_flow.root_cause must be one of "
            f"{sorted(ROOT_CAUSES_FOR_BUG_START)}, got {active_root_cause!r} "
            "(prd-exception is owned by incident-resolve in Phase 6.3)",
            file=sys.stderr,
        )
        return 1

    release = fm.get("release")
    if not isinstance(release, str):
        print(
            "progress.py bug-rework: cannot determine release from progress.md; "
            "ensure progress.md is well-formed",
            file=sys.stderr,
        )
        return 1

    # Latest test-report must be fail/partial. bug-close is the
    # complementary command for retest pass.
    try:
        from skills._shared.dev_workflow.progress_artifacts import (
            load_bug_report,
            load_test_report,
            parse_bug_triage_analysis,
        )

        test_info = load_test_report(root, release=release)
    except ProgressArtifactError as exc:
        print(f"progress.py bug-rework: {exc}", file=sys.stderr)
        return 1
    if test_info.verification_status not in {"fail", "partial"}:
        print(
            f"progress.py bug-rework: latest test-report at "
            f"{test_info.rel_path} has verification_status="
            f"{test_info.verification_status!r}; "
            "bug-rework requires 'fail' or 'partial' "
            "(use bug-close for 'pass')",
            file=sys.stderr,
        )
        return 1

    # BUG frontmatter root_cause must match bug_flow.root_cause; this
    # also validates path shape, type, bug_id, etc. via load_bug_report.
    try:
        bug_info = load_bug_report(
            root, rel_bug, expect_root_cause=active_root_cause,
        )
    except ProgressArtifactError as exc:
        print(f"progress.py bug-rework: {exc}", file=sys.stderr)
        return 1

    triage = None
    rollback_decisions: tuple[tuple[str, str, str, str], ...] = ()
    if active_root_cause == "development":
        try:
            triage = parse_bug_triage_analysis(
                bug_info.body, rel_path=rel_bug,
            )
        except ProgressArtifactError as exc:
            print(f"progress.py bug-rework: {exc}", file=sys.stderr)
            return 1
        rollback_decisions = compute_dev_bug_rollback(dict(fm), triage)

    # Phase 6.1 round 2 L1 mirror: dev root cause without auto-rollback
    # must surface a stderr warning so the operator notices the
    # planning route requirement. The persistent record lives in
    # apply_bug_rework's history_result / history_next (replay-safe).
    if (
        active_root_cause == "development"
        and triage is not None
        and not rollback_decisions
    ):
        if triage.unable_to_localize:
            reason = "marks 'unable to localize'"
        elif triage.classification == "ambiguous":
            reason = "classification is ambiguous"
        elif triage.affected_tasks:
            reason = (
                "affected task(s) "
                f"{list(triage.affected_tasks)} not in a state eligible for "
                "Gap-4 rollback"
            )
        else:
            reason = "yields no rollback decisions"
        print(
            f"progress.py bug-rework: BUG '## Triage Analysis' {reason}; "
            "no auto-rollback applied. Caller must invoke "
            "development-planning-write to replan/route the fix.",
            file=sys.stderr,
        )

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="bug-rework",
        compute_outcome=lambda state, now: apply_bug_rework(
            state,
            rel_bug,
            now=now,
            rollback_decisions=rollback_decisions,
        ),
        success_label=(
            f"bug-rework bug={rel_bug} root_cause={active_root_cause}"
        ),
    )


def cmd_bug_close(args: argparse.Namespace, root: Path) -> int:
    """Exit active Bug Flow after the latest test-report shows pass."""

    progress_path = root / PROGRESS_FILENAME

    # Pre-flight: latest test-report.verification_status must be 'pass'
    # before we enter the pipeline. The pipeline's apply_bug_close does
    # not do file I/O, so we read here while still outside the lock; the
    # lock+pipeline re-reads progress to detect any race.
    release: str | None = None
    if progress_path.exists():
        try:
            release = read_markdown(progress_path).frontmatter.get("release")
        except (FrontmatterError, OSError):
            release = None

    if not isinstance(release, str):
        print(
            "progress.py bug-close: cannot determine release from progress.md; "
            "ensure progress.md exists and is well-formed",
            file=sys.stderr,
        )
        return 1
    try:
        from skills._shared.dev_workflow.progress_artifacts import (
            load_test_report,
        )

        info = load_test_report(root, release=release)
    except ProgressArtifactError as exc:
        print(f"progress.py bug-close: {exc}", file=sys.stderr)
        return 1
    if info.verification_status != "pass":
        print(
            f"progress.py bug-close: latest test-report at "
            f"{info.rel_path} has verification_status={info.verification_status!r}; "
            "bug-close requires 'pass' (use bug-rework for fail/partial)",
            file=sys.stderr,
        )
        return 1

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="bug-close",
        compute_outcome=lambda state, now: apply_bug_close(state, now=now),
        success_label="bug-close",
    )


# ---------- Phase 6.3: PRD-exception incident lifecycle ----------


def validate_doc(doc_path: str, root: Path) -> list[str]:
    """Invoke ``doc-guardian/scripts/validate.py file <doc>`` in-process.

    Phase 6.3 round 2 M6 double-safety contract: incident-start and
    incident-resolve re-validate caller-supplied BUG / INCIDENT
    documents before allowing the state-machine transition. Even though
    the caller (bug-triage / workflow-evolution) already promote+
    validates the same docs, this re-check guarantees that no silent
    Step 6.f/g skip slipped through.

    Returns the list of issues reported by ``validate.validate_file``.
    Empty list ⇔ exit-0-equivalent. Tests mock this single entry point
    rather than the underlying validate_file to keep monkey-patching
    straightforward.
    """

    import validate as _doc_guardian_validate  # type: ignore  # noqa: PLC0415

    return list(_doc_guardian_validate.validate_file(doc_path, root))


def cmd_incident_start(args: argparse.Namespace, root: Path) -> int:
    """Open a PRD-exception incident — atomically opens bug_flow +
    workflow-incident state.

    Per ``command-reference.md §11`` (v0.6 F2): caller (typically
    ``bug-triage``) creates BUG-NNN.md (root_cause=prd-exception) and
    INCIDENT-NNN.md skeleton, runs doc-guardian promote+validate on
    both, and invokes this command. Pre-flight gates here (M6
    double-safety = re-validate BOTH docs):

      * ``progress.md`` exists, is parseable, ``project_state==active``;
      * ``bug_flow.active==false`` and ``workflow_incident_active==false``;
      * BUG path shape + containment + ``validate.py file`` exit 0;
      * INCIDENT path shape + containment + ``validate.py file`` exit 0;
      * BUG frontmatter ``root_cause==prd-exception``;
      * INCIDENT frontmatter ``triggered_by_bug == BUG bug_id``.
    """

    if args.bug is None:
        print(
            "progress.py incident-start: --bug is required", file=sys.stderr,
        )
        return 2
    if args.report is None:
        print(
            "progress.py incident-start: --report is required",
            file=sys.stderr,
        )
        return 2

    # Resolve and contain BOTH paths under root.
    def _resolve_under_root(arg_value: str, label: str) -> str | None:
        raw = Path(arg_value)
        absolute = raw if raw.is_absolute() else (root / raw)
        absolute = absolute.resolve()
        try:
            return str(absolute.relative_to(root.resolve())).replace("\\", "/")
        except ValueError:
            print(
                f"progress.py incident-start: {label} path must lie under "
                f"--root, got {absolute}",
                file=sys.stderr,
            )
            return None

    rel_bug = _resolve_under_root(args.bug, "BUG")
    if rel_bug is None:
        return 1
    rel_incident = _resolve_under_root(args.report, "INCIDENT")
    if rel_incident is None:
        return 1

    # M1 (round 2): apply explicit canonical-shape guards BEFORE
    # validate_doc reads the files. ``_resolve_under_root`` already
    # bounds paths under --root, but a user-supplied ``--bug other.md``
    # or ``--report docs/foo/notes.md`` would otherwise reach
    # ``validate_doc`` first; defending in depth keeps the contract
    # symmetric with incident-resolve and the bug-* CLI commands.
    try:
        _validate_bug_path_shape(rel_bug)
        _validate_incident_path_shape(rel_incident)
    except ProgressStateError as exc:
        print(f"progress.py incident-start: {exc}", file=sys.stderr)
        return 1

    progress_path = root / PROGRESS_FILENAME
    if not progress_path.exists():
        print(
            f"progress.py incident-start: {progress_path} not found; "
            "run 'progress.py init' first",
            file=sys.stderr,
        )
        return 1

    # M6 double-safety: validate.py file BOTH docs before opening
    # incident state. Either failure leaves progress.md byte-identical.
    bug_issues = validate_doc(rel_bug, root)
    if bug_issues:
        print(
            f"progress.py incident-start: doc-guardian rejected BUG "
            f"{rel_bug} — fix and retry:",
            file=sys.stderr,
        )
        for issue in bug_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    incident_issues = validate_doc(rel_incident, root)
    if incident_issues:
        print(
            f"progress.py incident-start: doc-guardian rejected INCIDENT "
            f"{rel_incident} — fix and retry:",
            file=sys.stderr,
        )
        for issue in incident_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    # Cross-check BUG.root_cause==prd-exception + INCIDENT.triggered_by_bug.
    try:
        from skills._shared.dev_workflow.progress_artifacts import (
            load_artifact_frontmatter,
            load_bug_report,
        )

        bug_info = load_bug_report(
            root, rel_bug, expect_root_cause="prd-exception",
        )
    except ProgressArtifactError as exc:
        print(f"progress.py incident-start: {exc}", file=sys.stderr)
        return 1

    # Read INCIDENT frontmatter directly (no dedicated loader yet);
    # we already ran validate.py file on it above so frontmatter shape
    # is sound — only the cross-ref to BUG bug_id remains.
    try:
        incident_doc = read_markdown(root / rel_incident)
    except FrontmatterError as exc:
        print(
            f"progress.py incident-start: cannot parse INCIDENT "
            f"frontmatter at {rel_incident}: {exc}",
            file=sys.stderr,
        )
        return 1
    incident_fm = incident_doc.frontmatter
    triggered = incident_fm.get("triggered_by_bug")
    if triggered != bug_info.bug_id:
        print(
            f"progress.py incident-start: INCIDENT frontmatter "
            f"triggered_by_bug={triggered!r} must equal the BUG "
            f"bug_id={bug_info.bug_id!r}",
            file=sys.stderr,
        )
        return 1

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="incident-start",
        compute_outcome=lambda state, now: apply_incident_start(
            state, rel_bug, rel_incident, now=now,
        ),
        success_label=(
            f"incident-start bug={rel_bug} incident={rel_incident}"
        ),
    )


def cmd_incident_resolve(args: argparse.Namespace, root: Path) -> int:
    """Exit incident state per ``--action``.

    Per ``command-reference.md §12.{1,2,3}``: caller (typically
    ``workflow-evolution`` after Step 6.e-g finalization) sets
    INCIDENT.frontmatter ``resolution_action`` + ``status=review-passed``,
    then invokes this command. Pre-flight gates:

      * ``progress.md`` exists, parseable, ``workflow_incident_active==true``;
      * INCIDENT path shape (re-derived from progress.md) + ``validate.py file`` exit 0
        (M6 double-safety);
      * INCIDENT frontmatter ``resolution_action == --action`` AND ``status == review-passed``.

    Note: progress_state already prevents ``--action continue`` from
    being misclassified as terminal in replay (Option B action-aware
    gate). This CLI does not need to special-case continue here.
    """

    if args.action is None:
        # Missing required CLI argument → exit 2 (CLI usage error),
        # matching how bug-start / bug-rework treat their required flags.
        print(
            "progress.py incident-resolve: --action is required",
            file=sys.stderr,
        )
        return 2
    if args.action not in {"continue", "abort", "reconstruct"}:
        # Supplied-but-invalid value → exit 1 (workflow validation),
        # consistent with release-start --scenario, init --scenario,
        # and the Phase 5.1 round 2 M2 contract: shape errors get exit 2,
        # workflow-meaning errors get exit 1.
        print(
            f"progress.py incident-resolve: --action must be one of "
            f"continue / abort / reconstruct, got {args.action!r}",
            file=sys.stderr,
        )
        return 1

    progress_path = root / PROGRESS_FILENAME
    if not progress_path.exists():
        print(
            f"progress.py incident-resolve: {progress_path} not found; "
            "run 'progress.py init' first",
            file=sys.stderr,
        )
        return 1
    try:
        progress_doc = read_markdown(progress_path)
    except FrontmatterError as exc:
        print(
            f"progress.py incident-resolve: cannot parse {progress_path}: "
            f"{exc}",
            file=sys.stderr,
        )
        return 1
    fm = progress_doc.frontmatter

    if not fm.get("workflow_incident_active"):
        print(
            "progress.py incident-resolve: workflow_incident_active is not "
            "true; no incident is currently open",
            file=sys.stderr,
        )
        return 1
    incident_path = fm.get("incident_report_path")
    if not isinstance(incident_path, str) or not incident_path:
        print(
            "progress.py incident-resolve: progress.md.incident_report_path "
            "is missing or non-string; cannot resolve",
            file=sys.stderr,
        )
        return 1

    # M1 (round 2): apply path-shape and containment guards BEFORE any
    # disk read. If progress.md was hand-edited or replayed from a
    # corrupt history, incident_report_path could be absolute, contain
    # ``..``, or otherwise escape the project tree; we must reject
    # before validate_doc / read_markdown can touch the filesystem.
    try:
        _validate_incident_path_shape(incident_path)
    except ProgressStateError as exc:
        print(
            f"progress.py incident-resolve: {exc}",
            file=sys.stderr,
        )
        return 1
    try:
        (root / incident_path).resolve().relative_to(root.resolve())
    except ValueError:
        print(
            f"progress.py incident-resolve: progress.md.incident_report_path "
            f"{incident_path!r} resolves outside --root; refuse to read",
            file=sys.stderr,
        )
        return 1

    # M6 double-safety: re-validate INCIDENT doc.
    incident_issues = validate_doc(incident_path, root)
    if incident_issues:
        print(
            f"progress.py incident-resolve: doc-guardian rejected INCIDENT "
            f"{incident_path} — fix workflow-evolution Step 6.e-g and retry:",
            file=sys.stderr,
        )
        for issue in incident_issues:
            print(f"- {issue}", file=sys.stderr)
        return 1

    # Cross-check INCIDENT.resolution_action == --action AND status == review-passed.
    try:
        incident_doc = read_markdown(root / incident_path)
    except FrontmatterError as exc:
        print(
            f"progress.py incident-resolve: cannot parse INCIDENT "
            f"frontmatter at {incident_path}: {exc}",
            file=sys.stderr,
        )
        return 1
    incident_fm = incident_doc.frontmatter
    declared_action = incident_fm.get("resolution_action")
    if declared_action != args.action:
        print(
            f"progress.py incident-resolve: INCIDENT frontmatter "
            f"resolution_action={declared_action!r} does not match "
            f"--action={args.action!r}; workflow-evolution must update the "
            "INCIDENT doc before re-running",
            file=sys.stderr,
        )
        return 1
    declared_status = incident_fm.get("status")
    if declared_status != "review-passed":
        print(
            f"progress.py incident-resolve: INCIDENT frontmatter "
            f"status={declared_status!r} must be 'review-passed' "
            "(workflow-evolution Step 6.f promote)",
            file=sys.stderr,
        )
        return 1

    return _run_update_pipeline(
        args=args,
        root=root,
        event_name="incident-resolve",
        compute_outcome=lambda state, now: apply_incident_resolve(
            state, args.action, incident_path, now=now,
        ),
        success_label=f"incident-resolve action={args.action}",
    )


# ---------- argparse ----------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="progress.py",
        description=(
            "workflow-protocol progress.py — Phase 5.1 implements init / query / recover. "
            "Phase 5.2 / 5.3 / 5.4 / Phase 6 add update --event / update --task / "
            "release-* / bug-* / incident-* / update --advance."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root containing progress.md / progress-history.md (default: cwd)",
    )
    parser.add_argument(
        "--lock-timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for the .progress.lock advisory lock (default: 5.0)",
    )

    sub = parser.add_subparsers(dest="cmd")

    p_init = sub.add_parser("init", help="Initialise progress.md + progress-history.md")
    p_init.add_argument("--project", required=True)
    # We intentionally do NOT use ``choices=`` here. The scenario value is a
    # workflow precondition, not a CLI shape error: invalid scenarios must
    # exit with code 1 (validation failure) like ``--release`` and
    # ``--project`` do, not code 2 (CLI usage error). Validation flows
    # through ``_validate_scenario_init`` inside ``build_initial_state``.
    p_init.add_argument(
        "--scenario",
        required=True,
        help=f"Init scenario; must be one of {sorted(SCENARIOS_INIT)} "
        "(S2-1/-2/-3 enter via release-start once Phase 5.4 lands)",
    )
    p_init.add_argument("--release", required=True, help="Release version e.g. 0.1")
    p_init.add_argument(
        "--agent",
        default="claude-opus-4-7/workflow-init",
        help="Agent identifier recorded in the init history entry",
    )

    p_query = sub.add_parser("query", help="Read progress.md state without locking")
    p_query.add_argument("--field", default=None, help="Print only the named frontmatter field")
    p_query.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit JSON instead of YAML",
    )

    p_recover = sub.add_parser(
        "recover",
        help="Replay progress-history.md and rewrite progress.md (terminal-state aware)",
    )
    p_recover.add_argument(
        "--confirm",
        action="store_true",
        help="Required acknowledgement that recover overwrites progress.md",
    )

    p_update = sub.add_parser(
        "update",
        help="Apply a state-machine event (Phase 5.3: --event / --task)",
    )
    # Mutually-exclusive group structured for forward compatibility:
    # Phase 5.3 adds --task; Phase 6 will add --advance.
    p_update_mode = p_update.add_mutually_exclusive_group(required=True)
    p_update_mode.add_argument(
        "--event",
        default=None,
        help=(
            f"State-machine event to apply; one of {sorted(UPDATE_EVENT_NAMES)}. "
            "Validation runs through apply_update_event so unknown values "
            "exit 1 with the same path as illegal sub_state transitions."
        ),
    )
    p_update_mode.add_argument(
        "--task",
        default=None,
        help=(
            "Stage 4 task ID (e.g. T1) to mutate. Must be combined with "
            "--status. Validation runs through apply_update_task; protected "
            "rollback transitions (Gap-3/4) require Phase 6 bug-start / "
            "bug-rework."
        ),
    )
    p_update_mode.add_argument(
        "--advance",
        action="store_true",
        help=(
            "Phase 6.4: explicit stage advance after the current stage's "
            "P6 matrix passes. CLI runs A (artifact existence), B "
            "(doc-guardian validate.py file), and E (verification status). "
            "C/D collapse into apply_update_advance's sub_state preconditions "
            "(approved for gated stages; review-passed for non-gated stages; "
            "all task_states verified for development)."
        ),
    )
    p_update.add_argument(
        "--status",
        default=None,
        help=(
            f"Target task state when --task is given; one of {sorted(TASK_STATES)}. "
            "Ignored unless --task is also supplied."
        ),
    )
    p_update.add_argument(
        "--agent",
        default="claude-opus-4-7/workflow-update",
        help="Agent identifier recorded in the history entry",
    )

    p_release_close = sub.add_parser(
        "release-close",
        help="Mark the current release closed at the end of Stage 7",
    )
    p_release_close.add_argument(
        "--agent",
        default="claude-opus-4-7/workflow-release",
        help="Agent identifier recorded in the history entry",
    )

    p_release_start = sub.add_parser(
        "release-start",
        help="Start a new active release (S2-1/-2/-3) after release-close",
    )
    p_release_start.add_argument(
        "--version",
        default=None,
        help="New release version, e.g. '0.2'. Must be strictly greater "
        "than every prior release.",
    )
    p_release_start.add_argument(
        "--scenario",
        default=None,
        help=(
            f"Scenario subtype; one of {sorted(RELEASE_START_SUBTYPES)}. "
            "S2-4 is forbidden — promote to a fresh S3 project instead."
        ),
    )
    p_release_start.add_argument(
        "--agent",
        default="claude-opus-4-7/workflow-release",
        help="Agent identifier recorded in the history entry",
    )

    p_bug_intake = sub.add_parser(
        "bug-intake",
        help="Append a post-close BUG path to unresolved_bugs (release_state must be 'closed')",
    )
    p_bug_intake.add_argument(
        "--bug",
        required=True,
        help="Path to the BUG-NNN.md report (relative to --root or absolute)",
    )
    p_bug_intake.add_argument(
        "--agent",
        default="claude-opus-4-7/bug-intake",
        help="Agent identifier recorded in the history entry",
    )

    p_bug_start = sub.add_parser(
        "bug-start",
        help="Enter active Bug Flow (Phase 6.1; Stage 5 testing review-passed)",
    )
    p_bug_start.add_argument(
        "--bug",
        default=None,
        help="Path to BUG-NNN.md (relative to --root or absolute)",
    )
    p_bug_start.add_argument(
        "--root-cause",
        dest="root_cause",
        default=None,
        help=(
            "BUG root cause classification; one of "
            f"{sorted(ROOT_CAUSES_FOR_BUG_START)}. "
            "prd-exception goes through incident-start (Phase 6.3)."
        ),
    )
    p_bug_start.add_argument(
        "--agent",
        default="claude-opus-4-7/bug-triage",
        help="Agent identifier recorded in the history entry",
    )

    p_bug_close = sub.add_parser(
        "bug-close",
        help="Exit active Bug Flow after a passing retest (Phase 6.1)",
    )
    p_bug_close.add_argument(
        "--agent",
        default="claude-opus-4-7/testing-write",
        help="Agent identifier recorded in the history entry",
    )

    p_bug_rework = sub.add_parser(
        "bug-rework",
        help=(
            "Re-route an active Bug Flow whose retest came back "
            "fail/partial (Phase 6.2; Gap-5)"
        ),
    )
    p_bug_rework.add_argument(
        "--bug",
        default=None,
        help="Path to BUG-NNN.md (relative to --root or absolute)",
    )
    p_bug_rework.add_argument(
        "--agent",
        default="claude-opus-4-7/testing-write",
        help="Agent identifier recorded in the history entry",
    )

    p_incident_start = sub.add_parser(
        "incident-start",
        help=(
            "Open a PRD-exception incident (Phase 6.3; sets bug_flow + "
            "workflow-incident-analysis state in one atomic step)"
        ),
    )
    p_incident_start.add_argument(
        "--bug",
        default=None,
        help="Path to BUG-NNN.md (must have root_cause: prd-exception)",
    )
    p_incident_start.add_argument(
        "--report",
        default=None,
        help="Path to INCIDENT-NNN.md skeleton",
    )
    p_incident_start.add_argument(
        "--agent",
        default="claude-opus-4-7/bug-triage",
        help="Agent identifier recorded in the history entry",
    )

    p_incident_resolve = sub.add_parser(
        "incident-resolve",
        help=(
            "Exit incident state (Phase 6.3; abort/reconstruct are "
            "terminal — no further mutating commands accepted)"
        ),
    )
    p_incident_resolve.add_argument(
        "--action",
        default=None,
        # No choices= so an invalid value lands in the workflow-validation
        # exit-1 path rather than argparse's exit-2 path, matching how
        # release-start handles --scenario.
        help="One of continue / abort / reconstruct",
    )
    p_incident_resolve.add_argument(
        "--agent",
        default="claude-opus-4-7/workflow-evolution",
        help="Agent identifier recorded in the history entry",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help(sys.stderr)
        return 2
    root = Path(args.root).resolve()
    if args.cmd == "init":
        return cmd_init(args, root)
    if args.cmd == "query":
        return cmd_query(args, root)
    if args.cmd == "recover":
        return cmd_recover(args, root)
    if args.cmd == "update":
        return cmd_update(args, root)
    if args.cmd == "release-close":
        return cmd_release_close(args, root)
    if args.cmd == "release-start":
        return cmd_release_start(args, root)
    if args.cmd == "bug-intake":
        return cmd_bug_intake(args, root)
    if args.cmd == "bug-start":
        return cmd_bug_start(args, root)
    if args.cmd == "bug-close":
        return cmd_bug_close(args, root)
    if args.cmd == "bug-rework":
        return cmd_bug_rework(args, root)
    if args.cmd == "incident-start":
        return cmd_incident_start(args, root)
    if args.cmd == "incident-resolve":
        return cmd_incident_resolve(args, root)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
