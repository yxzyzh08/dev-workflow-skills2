"""Replay validator for ``progress-history.md``.

``progress.py recover --confirm`` reconstructs ``progress.md`` by replaying
``progress-history.md`` entries through this validator. The replay is the
single source of truth for "given this history, what should the live state
be" and is shared with the ``progress.py update --event`` /
``update --task`` forward paths so the two cannot drift.

Phase 6.4 registers handlers for ``init``, the four ``update --event``
events (``write-complete`` / ``review-issues`` / ``review-passed`` /
``human-confirmed``), ``update-task``, the release lifecycle trio
(``release-close`` / ``release-start`` / ``bug-intake``), the Bug
Flow entry/exit pair (``bug-start`` / ``bug-close``), the active
Bug Flow re-route command ``bug-rework``, the PRD-exception incident
lifecycle pair (``incident-start`` / ``incident-resolve``), and the
explicit stage-advance command ``update-advance``.
:data:`TERMINAL_EVENTS` is event-name-keyed for ``incident-resolve``,
but the dispatch loop reads the canonical ``action=`` summary token
and only flips ``seen_terminal`` when ``action`` is ``abort`` or
``reconstruct``. ``--action continue`` is non-terminal and may
legitimately be followed by additional mutating entries (resume
testing). ``update --advance`` is non-terminal. Any event not
registered raises :class:`ReplayError` — better to refuse to recover
than to silently drop a state-machine step we do not yet know how to
validate.

Spec: ``skills/workflow-protocol/references/command-reference.md`` §4
(``recover`` algorithm + terminal-state semantics).
"""

from __future__ import annotations

from pathlib import Path
import re
from typing import Callable, Iterable

from .progress_artifacts import ProgressArtifactError
from .progress_history import HistoryEntry
from .progress_state import (
    EVENTS as UPDATE_EVENT_NAMES,
    ProgressStateError,
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
)


class ReplayError(ValueError):
    """Raised when history cannot be replayed into a valid state."""


# Apply functions take ``(state, entry, root)`` and return a new state dict.
# ``root`` is the project root directory and is required by the
# ``update-task`` handler so it can read Stage 4 task artifacts. Handlers
# that do not need root (init / update --event) ignore the parameter.
ApplyFn = Callable[[dict, HistoryEntry, "Path | None"], dict]

# Events that *can* put the project into a terminal state. Phase 6.3
# populates this with ``incident-resolve``, but the dispatch loop is
# action-aware: only ``--action abort`` and ``--action reconstruct``
# actually flip ``seen_terminal``; ``--action continue`` resumes
# testing/review-passed and is non-terminal. The action is encoded in
# the canonical history summary token ``action=<continue|abort|reconstruct>``.
TERMINAL_EVENTS: set[str] = {"incident-resolve"}

# Subset of action values within ``TERMINAL_EVENTS`` that are actually
# terminal. Kept as a frozenset so callers cannot mutate the policy.
TERMINAL_INCIDENT_ACTIONS: frozenset[str] = frozenset({"abort", "reconstruct"})

# Read-only entries do not mutate state and are allowed after a terminal
# event. ``recover`` itself is a read-write rebuild but does not append to
# history, so it never appears here. Phase 5.1 keeps this empty as well —
# we only have ``init`` so far.
READ_ONLY_EVENTS: set[str] = set()


def _apply_init(state: dict, entry: HistoryEntry, root: "Path | None") -> dict:
    """Handler for the ``init`` history event.

    Validation rules:
      * ``init`` must be the first entry overall (i.e. state is empty).
      * Summary must contain ``scenario=<S1|S3>, release=<x.y>, project=<name>``
        in any order so build_initial_state can recover the parameters.
    """

    del root  # init does not read artifacts.
    if state:
        raise ReplayError(
            f"history at {entry.timestamp}: 'init' is only legal as the first entry"
        )
    args = _parse_init_summary(entry)
    try:
        new_state = build_initial_state(
            project=args["project"],
            scenario=args["scenario"],
            release=args["release"],
            now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: 'init' summary fields are invalid: {exc}"
        ) from exc
    return new_state


def _parse_init_summary(entry: HistoryEntry) -> dict[str, str]:
    """Extract ``project=...``, ``scenario=...`` and ``release=...`` tokens.

    The ``init`` history summary is rendered by ``progress.py init`` as::

        project created — project=<name>, scenario=<S1|S3>, release=<x.y>

    Replay does not require the canonical wording; it only requires the
    three ``key=value`` tokens to be discoverable in the summary OR the
    ``result`` field. This keeps the parser tolerant to phrasing tweaks
    while still rejecting missing values.
    """

    haystack = entry.summary
    if entry.result:
        haystack = haystack + " " + entry.result
    out: dict[str, str] = {}
    for token in haystack.replace(",", " ").split():
        if "=" in token:
            key, _, value = token.partition("=")
            if key in {"project", "scenario", "release"}:
                out[key] = value
    missing = {"project", "scenario", "release"} - out.keys()
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'init' entry is missing fields {sorted(missing)}; "
            "expected project=<name>, scenario=<S1|S3>, release=<x.y> tokens "
            "in summary or result"
        )
    return out


def _apply_update_event_factory(event_name: str) -> ApplyFn:
    """Build a replay handler that delegates to :func:`apply_update_event`.

    Phase 5.2 wires the four ``update --event`` events through the same
    state-machine implementation used by ``progress.py update --event``,
    so a divergence between forward path and replay path is impossible
    by construction. The handler uses each entry's recorded timestamp as
    the new ``state['updated']`` value, which keeps replay deterministic.
    """

    def _handler(state: dict, entry: HistoryEntry, root: "Path | None") -> dict:
        del root  # update --event handlers do not read artifacts.
        try:
            outcome = apply_update_event(state, event_name, now=entry.timestamp)
        except ProgressStateError as exc:
            raise ReplayError(
                f"history at {entry.timestamp}: {exc}"
            ) from exc
        return outcome.new_state

    return _handler


_UPDATE_TASK_SUMMARY_RE = re.compile(
    r"^task=(?P<task>T\d+) status=(?P<status>[a-z][a-z0-9-]*)\b"
)


def _apply_update_task(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Handler for ``update-task`` history events.

    Replay validates state-machine legality only; it does **not**
    re-evaluate Stage 4 artifact preconditions. Review report files
    legitimately mutate from skeleton (``review_status==pending``) to
    final (``pass`` / ``fail``) across transitions, so re-reading
    "current" artifacts during replay would falsely fail an early
    transition that was perfectly valid when it was recorded. The
    forward CLI path is the gatekeeper for artifact state at write
    time. M1 still catches forward-vs-replay state divergence on
    ``progress.md``.

    ``root`` is required defensively because Phase 5.4+ may extend
    artifact-aware replay; current callers must pass it (recover and
    cmd_update do).
    """

    if root is None:
        raise ReplayError(
            f"history at {entry.timestamp}: 'update-task' replay requires a "
            "project root (artifact reads are skipped, but the parameter is "
            "required for forward compatibility)"
        )
    match = _UPDATE_TASK_SUMMARY_RE.match(entry.summary)
    if match is None:
        raise ReplayError(
            f"history at {entry.timestamp}: cannot parse 'update-task' summary "
            f"{entry.summary!r}; expected 'task=Tn status=<state>' prefix"
        )
    task_id = match.group("task")
    new_status = match.group("status")
    try:
        # Replay does not re-evaluate artifact preconditions: Stage 4
        # report files mutate across transitions (skeleton → pass), so
        # re-reading "current" artifacts during replay would falsely
        # fail historically-valid transitions. The forward path is the
        # gatekeeper for artifact state at write time; replay only
        # validates that the recorded transition is state-machine legal.
        outcome = apply_update_task(
            state,
            task_id,
            new_status,
            now=entry.timestamp,
            root=root,
            validate_artifacts=False,
        )
    except (ProgressStateError, ProgressArtifactError) as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _kv_tokens(entry: HistoryEntry) -> dict[str, str]:
    """Extract ``key=value`` tokens from summary + result fields."""

    haystack = entry.summary
    if entry.result:
        haystack = haystack + " " + entry.result
    out: dict[str, str] = {}
    for token in haystack.replace(",", " ").split():
        if "=" in token:
            key, _, value = token.partition("=")
            if key not in out:
                out[key] = value
    return out


def _apply_release_close_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    del root  # release-close does not read artifacts.
    try:
        outcome = apply_release_close(state, now=entry.timestamp)
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_release_start_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``release-start``.

    Re-derives the new release version + scenario_subtype from the
    summary's ``version=...`` / ``scenario=...`` (or
    ``scenario_subtype=...``) tokens and applies the progress-state
    mutation. Replay does NOT re-read or re-write BUG files; the
    forward CLI path owns BUG ``target_release`` /
    ``consumed_in_release`` mutations at write time, exactly like
    update-task replay leaves Stage 4 review reports alone.
    """

    del root  # BUG file fan-out is forward-only.
    tokens = _kv_tokens(entry)
    version = tokens.get("version")
    scenario_subtype = tokens.get("scenario") or tokens.get("scenario_subtype")
    missing = [
        name
        for name, value in (("version", version), ("scenario_subtype", scenario_subtype))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'release-start' summary is missing "
            f"{missing}; expected version=<x.y> scenario=<S2-x> tokens"
        )
    try:
        outcome = apply_release_start(
            state,
            new_version=version,
            scenario_subtype=scenario_subtype,
            now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_bug_intake_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    del root  # bug-intake does not read artifacts during replay.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    if bug_path is None:
        raise ReplayError(
            f"history at {entry.timestamp}: 'bug-intake' summary is missing "
            "bug=<path> token"
        )
    try:
        outcome = apply_bug_intake(state, bug_path, now=entry.timestamp)
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _parse_rollback_token(value: str) -> tuple[tuple[str, str, str, str], ...]:
    """Reverse the canonical ``rollback=Tn:old->new;...`` summary token.

    Returns the same tuple shape as ``apply_bug_start`` /
    ``apply_bug_rework`` consume: ``(task_id, old, new, reason)``. The
    reason field is filled with ``"replay"`` because BUG body language
    is forward-only.
    """

    out: list[tuple[str, str, str, str]] = []
    for piece in value.split(";"):
        piece = piece.strip()
        if not piece:
            continue
        if ":" not in piece or "->" not in piece:
            raise ValueError(
                f"rollback token piece must be 'Tn:old->new', got {piece!r}"
            )
        task_id, _, transition = piece.partition(":")
        old_status, _, new_status = transition.partition("->")
        if not (task_id and old_status and new_status):
            raise ValueError(
                f"rollback token piece is malformed: {piece!r}"
            )
        out.append((task_id, old_status, new_status, "replay"))
    return tuple(out)


def _apply_bug_start_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``bug-start``.

    Reverses the canonical summary tokens (``bug=`` / ``root_cause=`` /
    optional ``rollback=Tn:old->new;...``) and replays the same
    state-machine transition the forward CLI applied. Replay does NOT
    read the BUG body — the rollback decisions are already encoded in
    the history entry.
    """

    del root  # bug-start replay does not read BUG / artifact files.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    root_cause = tokens.get("root_cause")
    missing = [
        name
        for name, value in (("bug", bug_path), ("root_cause", root_cause))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'bug-start' summary is missing "
            f"{missing}; expected bug=<path> root_cause=<srs|architecture|development>"
        )
    rollback_token = tokens.get("rollback") or ""
    try:
        rollback_decisions = (
            _parse_rollback_token(rollback_token) if rollback_token else ()
        )
    except ValueError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: 'bug-start' rollback token is "
            f"malformed: {exc}"
        )
    try:
        outcome = apply_bug_start(
            state,
            bug_path,
            root_cause,
            now=entry.timestamp,
            rollback_decisions=rollback_decisions,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_bug_close_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``bug-close``.

    Forward CLI confirms the latest test-report shows
    ``verification_status==pass`` before allowing close; replay trusts
    that the entry was recorded only after that check passed and does
    not re-read the test-report (consistent with the
    ``validate_artifacts=False`` design used since Phase 5.3).
    """

    del root
    try:
        outcome = apply_bug_close(state, now=entry.timestamp)
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_bug_rework_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``bug-rework`` (Phase 6.2 / Gap-5).

    Reverses the canonical summary tokens (``bug=`` / ``root_cause=`` /
    optional ``rollback=Tn:old->new;...``) — same shape as
    ``bug-start`` — and replays the same state-machine transition the
    forward CLI applied. Replay does NOT read the BUG body or the
    test-report: rollback decisions are already encoded in the history
    entry, and the test-report fail/partial precondition is the
    forward CLI's responsibility (consistent with bug-start, bug-close,
    update-task, release-start replay design).
    """

    del root  # bug-rework replay does not read BUG / artifact files.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    root_cause = tokens.get("root_cause")
    missing = [
        name
        for name, value in (("bug", bug_path), ("root_cause", root_cause))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'bug-rework' summary is missing "
            f"{missing}; expected bug=<path> root_cause=<srs|architecture|development>"
        )
    rollback_token = tokens.get("rollback") or ""
    try:
        rollback_decisions = (
            _parse_rollback_token(rollback_token) if rollback_token else ()
        )
    except ValueError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: 'bug-rework' rollback token is "
            f"malformed: {exc}"
        )
    # apply_bug_rework reads bug_flow.root_cause from state, which the
    # earlier bug-start handler put there during replay; we don't pass
    # root_cause as an argument here. The state's bug_flow.root_cause
    # is the source of truth for the transition. The root_cause= token
    # required above is presence-checked for canonical-form/readability
    # only (parity with bug-start summary so log inspection has a
    # consistent token shape) — replay does NOT compare it against
    # state['bug_flow']['root_cause']. If a future tightening pass
    # wants to detect manual history-summary tampering, add an explicit
    # equality check here; until then the token is informational.
    try:
        outcome = apply_bug_rework(
            state,
            bug_path,
            now=entry.timestamp,
            rollback_decisions=rollback_decisions,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_incident_start_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``incident-start`` (Phase 6.3).

    Reverses the canonical summary tokens
    (``bug=<path>`` / ``incident=<path>`` / ``root_cause=prd-exception``).
    Replay does NOT read the BUG or INCIDENT files: shape and frontmatter
    legality are forward CLI gates (the ``validate.py file`` double-check
    runs there per round 2 M6), and only the state-machine transition
    itself is reproduced here.
    """

    del root  # incident-start replay does not read artifact files.
    tokens = _kv_tokens(entry)
    bug_path = tokens.get("bug")
    incident_path = tokens.get("incident")
    missing = [
        name
        for name, value in (("bug", bug_path), ("incident", incident_path))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'incident-start' summary is missing "
            f"{missing}; expected bug=<path> incident=<path> root_cause=prd-exception"
        )
    try:
        outcome = apply_incident_start(
            state, bug_path, incident_path, now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_incident_resolve_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``incident-resolve`` (Phase 6.3).

    Reverses the canonical summary tokens
    (``action=<continue|abort|reconstruct>`` / ``incident=<path>``).
    Replay does NOT read the INCIDENT file: ``resolution_action`` and
    ``status==review-passed`` are forward CLI gates (with the round 2
    M6 double-validate), and the state-machine transition is reproduced
    here purely from the canonical action token.

    The dispatch loop in :func:`replay_history` consults the same
    ``action=`` token after this handler runs to decide whether the
    entry is terminal (``abort`` / ``reconstruct``) or non-terminal
    (``continue``).
    """

    del root  # incident-resolve replay does not read artifact files.
    tokens = _kv_tokens(entry)
    action = tokens.get("action")
    incident_path = tokens.get("incident")
    missing = [
        name
        for name, value in (("action", action), ("incident", incident_path))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'incident-resolve' summary is missing "
            f"{missing}; expected action=<continue|abort|reconstruct> incident=<path>"
        )
    try:
        outcome = apply_incident_resolve(
            state, action, incident_path, now=entry.timestamp,
        )
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    return outcome.new_state


def _apply_update_advance_handler(
    state: dict, entry: HistoryEntry, root: "Path | None"
) -> dict:
    """Replay handler for ``update-advance`` (Phase 6.4).

    Reverses the canonical summary tokens (``from=<old_stage>`` /
    ``to=<new_stage>``) and replays the same state-machine transition
    the forward CLI applied. Replay does NOT re-evaluate the P6 matrix
    (artifact existence / validate.py / verification status); the
    forward CLI is the gatekeeper for those dimensions, consistent
    with the replay-skips-artifacts invariant inherited from Phase 5.3.

    Adds an extra defense-in-depth check on top of M1: after running
    :func:`apply_update_advance`, verify the recomputed
    ``current_stage`` matches the recorded ``to=`` token. If they
    diverge, the history is corrupt or the state-machine has changed
    incompatibly; reject with a specific message.
    """

    del root  # update-advance replay does not read artifact files.
    tokens = _kv_tokens(entry)
    from_stage = tokens.get("from")
    to_stage = tokens.get("to")
    missing = [
        name
        for name, value in (("from", from_stage), ("to", to_stage))
        if value is None
    ]
    if missing:
        raise ReplayError(
            f"history at {entry.timestamp}: 'update-advance' summary is "
            f"missing {missing}; expected from=<stage> to=<stage>"
        )
    try:
        outcome = apply_update_advance(state, now=entry.timestamp)
    except ProgressStateError as exc:
        raise ReplayError(
            f"history at {entry.timestamp}: {exc}"
        ) from exc
    derived_to = outcome.new_state.get("current_stage")
    if derived_to != to_stage:
        raise ReplayError(
            f"history at {entry.timestamp}: 'update-advance' summary "
            f"recorded to={to_stage!r} but state machine derived "
            f"current_stage={derived_to!r}; history may be corrupt or "
            "out-of-sync with the implementation"
        )
    return outcome.new_state


_HANDLERS: dict[str, ApplyFn] = {
    "init": _apply_init,
    **{
        event_name: _apply_update_event_factory(event_name)
        for event_name in sorted(UPDATE_EVENT_NAMES)
    },
    "update-task": _apply_update_task,
    "release-close": _apply_release_close_handler,
    "release-start": _apply_release_start_handler,
    "bug-intake": _apply_bug_intake_handler,
    "bug-start": _apply_bug_start_handler,
    "bug-close": _apply_bug_close_handler,
    "bug-rework": _apply_bug_rework_handler,
    "incident-start": _apply_incident_start_handler,
    "incident-resolve": _apply_incident_resolve_handler,
    "update-advance": _apply_update_advance_handler,
}


def supported_events() -> set[str]:
    """Return the event names this replay validator currently handles."""

    return set(_HANDLERS)


def replay_history(
    history: Iterable[HistoryEntry],
    *,
    root: str | Path | None = None,
) -> dict:
    """Replay history entries in document/append order and return final state.

    The caller is expected to pass entries in the order they appear in
    ``progress-history.md`` — this is what :func:`parse_history_text`
    already returns. ``progress-history.md`` is append-only by design, so
    timestamps must be monotonically ascending in document order; any
    backwards timestamp aborts replay before any handler runs (avoids
    silently re-ordering a corrupted history).

    ``root`` is forwarded to handlers that read artifacts (currently
    only ``update-task``). Callers that know they will not exercise such
    handlers (e.g. unit tests for ``init`` / ``update --event``) may
    omit it; if an artifact-reading handler fires without a root, replay
    raises :class:`ReplayError` rather than silently skipping the check.

    Raises :class:`ReplayError` on:
      * timestamp going backwards (checked first, in document order);
      * mutating entries after a terminal event;
      * unknown / unsupported event names;
      * any per-handler validation failure (including artifact failures).
    """

    root_path: Path | None = Path(root) if root is not None else None

    state: dict = {}
    seen_terminal = False
    prev_ts: str | None = None
    for entry in history:
        # Monotonicity check fires before handler dispatch so a corrupted
        # backwards-timestamp history is rejected even if the offending
        # entry's event name is also unsupported / terminal-violating.
        if prev_ts is not None and entry.timestamp < prev_ts:
            raise ReplayError(
                f"history at {entry.timestamp}: timestamp goes backwards "
                f"(previous {prev_ts})"
            )
        prev_ts = entry.timestamp

        if seen_terminal and entry.event not in READ_ONLY_EVENTS:
            raise ReplayError(
                f"history at {entry.timestamp}: mutating event {entry.event!r} "
                "after terminal incident-resolve; refusing to silently truncate"
            )

        handler = _HANDLERS.get(entry.event)
        if handler is None:
            raise ReplayError(
                f"history at {entry.timestamp}: event {entry.event!r} is not "
                "supported by the current replay validator (phase 6.4 closes "
                "Phase 6 with: 'init', the four update --event handlers, "
                "'update-task', 'release-close', 'release-start', "
                "'bug-intake', 'bug-start', 'bug-close', 'bug-rework', "
                "'incident-start', 'incident-resolve', and 'update-advance' "
                "— 15 events total; any other event indicates either a "
                "future-phase entry or a corrupt history)"
            )
        state = handler(state, entry, root_path)
        # Action-aware terminal gate (Phase 6.3): event-name membership in
        # TERMINAL_EVENTS is necessary but not sufficient. For
        # incident-resolve, only --action abort / reconstruct are
        # terminal; --action continue resumes testing/review-passed and
        # is followed by legal mutations. We re-derive the action from
        # the canonical summary token rather than passing extra state
        # through the handler return — the handler already ran above
        # and validated the token's presence, so this re-parse is safe.
        if entry.event in TERMINAL_EVENTS:
            action = _kv_tokens(entry).get("action")
            if action in TERMINAL_INCIDENT_ACTIONS:
                seen_terminal = True
    return state
