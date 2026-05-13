"""Shared progress.md constants and lightweight loaders."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

from .frontmatter import read_markdown, render_markdown
from .progress_artifacts import (
    ProgressArtifactError,
    load_artifact_frontmatter,
    load_breakdown_with_tasks,
)


WORKFLOW_VERSION = "v0.6"

STAGES = (
    "prd-inception",
    "srs-specification",
    "architecture-design",
    "development",
    "testing",
    "delivery",
    "project-retrospective",
)

SPECIAL_STAGES = ("workflow-incident-analysis",)
ALL_STAGES = STAGES + SPECIAL_STAGES
GATED_STAGES = {"prd-inception", "srs-specification", "architecture-design"}

EVENTS = {"write-complete", "review-issues", "review-passed", "human-confirmed"}
SUB_STATES = {"write", "in-review", "revising", "review-passed", "approved"}

NEXT_STAGE = {
    "prd-inception": "srs-specification",
    "srs-specification": "architecture-design",
    "architecture-design": "development",
    "development": "testing",
    "testing": "delivery",
    "delivery": "project-retrospective",
}

ROOT_CAUSE_TO_STAGE = {
    "srs": "srs-specification",
    "architecture": "architecture-design",
    "development": "development",
}

TASK_STATES = {
    "planning-done",
    "test-writing",
    "test-review",
    "test-revising",
    "test-done",
    "code-writing",
    "code-review",
    "code-revising",
    "code-review-passed",
    "verifying",
    "verified",
}

# Normal Stage 4 task transitions. These may be triggered by the standard
# `progress.py update --task Tn --status <new>` path with only state-machine
# legality checks. They do not require active Bug Flow context.
NORMAL_TASK_TRANSITIONS = {
    (None, "planning-done"),
    ("planning-done", "planning-done"),
    ("planning-done", "test-writing"),
    ("test-writing", "test-review"),
    ("test-review", "test-revising"),
    ("test-review", "test-done"),
    ("test-revising", "test-review"),
    ("test-done", "code-writing"),
    ("code-writing", "code-review"),
    ("code-review", "code-revising"),
    ("code-review", "code-review-passed"),
    ("code-revising", "code-review"),
    ("code-review-passed", "verifying"),
    ("verifying", "verified"),
}

# Protected Stage 4 task transitions. Each requires extra caller-side
# preconditions that are enforced by `progress.py update --task` /
# `bug-start` / `bug-rework`. See command-reference.md state-machine table
# (lines 645-648) and task6_plan §6.1 / §6.2:
#   - verifying  -> code-revising  (Gap-3): development-code-write retry,
#       guarded by `verification_result.md verification_status in {fail, partial}`.
#   - verified   -> test-revising  (Gap-4): active Bug Flow with
#       root_cause==development, BUG body Affected Task(s) includes Tn,
#       fix is test-only/test-first; owner=`bug-start --root-cause development`
#       or `bug-rework`.
#   - verified   -> code-revising  (Gap-4): same as above, source-code fix.
#   - code-review-passed -> code-revising (Gap-4): same as above, source fix
#       needed before verification.
PROTECTED_TASK_TRANSITIONS = {
    ("verifying", "code-revising"),
    ("verified", "test-revising"),
    ("verified", "code-revising"),
    ("code-review-passed", "code-revising"),
}

# Backwards-compatible union for callers that legitimately need to enumerate
# every legal transition (state-machine documentation, validation tooling).
TASK_TRANSITIONS = NORMAL_TASK_TRANSITIONS | PROTECTED_TASK_TRANSITIONS


@dataclass(frozen=True)
class ProgressDocument:
    state: dict[str, Any]
    body: str
    path: Path

    @property
    def release(self) -> str:
        return str(self.state["release"])

    @property
    def current_stage(self) -> str | None:
        value = self.state.get("current_stage")
        return None if value is None else str(value)

    @property
    def scenario(self) -> str:
        return str(self.state["scenario"])

    @property
    def scenario_subtype(self) -> str | None:
        value = self.state.get("scenario_subtype")
        return None if value is None else str(value)

    @property
    def task_states(self) -> dict[str, str]:
        dev = self.state.get("development_state") or {}
        states = dev.get("task_states") or {}
        return {str(key): str(value) for key, value in states.items()}


def load_progress(root: str | Path = ".") -> ProgressDocument:
    path = Path(root) / "progress.md"
    doc = read_markdown(path)
    return ProgressDocument(doc.frontmatter, doc.body, path)


def render_progress(state: Mapping[str, Any], body: str = "\n# Current Stage Summary\n\n# Recent Activity\n") -> str:
    return render_markdown(state, body)


def is_valid_task_transition(
    old: str | None,
    new: str,
    *,
    allow_protected: bool = False,
) -> bool:
    """Check whether ``(old, new)`` is a legal Stage 4 task transition.

    By default only NORMAL_TASK_TRANSITIONS are accepted. Pass
    ``allow_protected=True`` from a caller that has already verified the
    Gap-3 / Gap-4 preconditions (verification_result status, active Bug Flow,
    BUG body Affected Task(s) match, owner in {bug-start, bug-rework}).
    """

    if (old, new) in NORMAL_TASK_TRANSITIONS:
        return True
    if allow_protected and (old, new) in PROTECTED_TASK_TRANSITIONS:
        return True
    return False


def next_stage(stage: str) -> str | None:
    return NEXT_STAGE.get(stage)


# ---------- Phase 5.1: init / recover state construction ----------


SCENARIOS_INIT = {"S1", "S3"}
SCENARIO_SUBTYPES = {"S2-1", "S2-2", "S2-3", "S2-4"}
PROJECT_STATES = {"active", "aborted", "reconstructing"}
RELEASE_STATES = {"active", "closed"}

_PROJECT_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,63}$")
_RELEASE_RE = re.compile(r"^\d+\.\d+$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class ProgressStateError(ValueError):
    """Raised for invalid arguments when constructing or rendering progress state."""


def _validate_project_name(name: str) -> None:
    if not isinstance(name, str) or not _PROJECT_NAME_RE.match(name):
        raise ProgressStateError(
            "project name must match ^[A-Za-z][A-Za-z0-9_.-]{0,63}$, "
            f"got {name!r}"
        )


def _validate_release(release: str) -> None:
    if not isinstance(release, str) or not _RELEASE_RE.match(release):
        raise ProgressStateError(
            f"release must be a quoted YAML string matching ^\\d+\\.\\d+$, got {release!r}"
        )


def _validate_scenario_init(scenario: str) -> None:
    if scenario not in SCENARIOS_INIT:
        raise ProgressStateError(
            f"init scenario must be one of {sorted(SCENARIOS_INIT)}, got {scenario!r}"
        )


def _validate_timestamp(value: str, *, field: str) -> None:
    if not isinstance(value, str) or not _TIMESTAMP_RE.match(value):
        raise ProgressStateError(
            f"{field} must be ISO8601 UTC second-precision with 'Z', got {value!r}"
        )


def _initial_artifacts(release: str) -> dict[str, Any]:
    """Per command-reference.md §1, artifacts at init time."""

    return {
        "prd": "docs/prd/prd.md",
        "architecture": "docs/architecture/architecture.md",
        "srs": f"docs/release{release}/srs/srs.md",
        "acceptance_plan": f"docs/release{release}/srs/acceptance_plan.md",
        "integration_plan": None,
        "architecture_delta": None,
    }


def build_initial_state(
    *,
    project: str,
    scenario: str,
    release: str,
    now: str,
) -> dict[str, Any]:
    """Compose the canonical ``progress.md`` frontmatter for ``init``.

    All fields the v0.6 schema declares mandatory at first creation are
    present, with their initial values per ``command-reference.md §1``.

    Caller (``progress.py init``) renders this through
    :func:`render_progress_text` and writes the resulting Markdown
    atomically alongside the first ``progress-history.md`` entry.
    """

    _validate_project_name(project)
    _validate_scenario_init(scenario)
    _validate_release(release)
    _validate_timestamp(now, field="now")

    return {
        "project_name": project,
        "workflow_version": WORKFLOW_VERSION,
        "project_state": "active",
        "release": release,
        "release_state": "active",
        "release_close_reason": None,
        "previous_releases": [],
        "scenario": scenario,
        "scenario_subtype": None,
        "current_stage": "prd-inception",
        "sub_state": "write",
        "review_iteration": 0,
        "artifacts": _initial_artifacts(release),
        "bug_flow": {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        },
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "created": now,
        "updated": now,
    }


PROGRESS_BODY_TEMPLATE = (
    "\n# Current Stage Summary\n\n"
    "Workflow has just been initialised. The orchestrator is at "
    "`prd-inception` / `write`; the next action is to invoke the PRD write skill.\n"
    "\n# Recent Activity\n\n"
    "See `progress-history.md` for the full event log.\n"
)


def render_progress_text(
    state: Mapping[str, Any],
    body: str = PROGRESS_BODY_TEMPLATE,
) -> str:
    """Render the progress state mapping back to Markdown text.

    The body argument lets the recovery path preserve a previously written
    summary; the default is the canonical Phase 5.1 template.
    """

    return render_markdown(state, body)


# ---------- Phase 5.2: update --event state machine ----------


REVIEW_ITERATION_LIMIT = 7


@dataclass(frozen=True)
class EventOutcome:
    """Result of applying a state-machine event.

    Phase 5.2 callers:
      * ``progress.py update --event``: writes ``new_state`` back to
        ``progress.md`` and appends a history entry rendered from
        ``history_summary`` / ``history_result`` / ``history_next``.
      * ``progress_replay.py``: applies ``new_state`` during recover; the
        history fields are unused there because the entry is being read,
        not written.
    """

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def _validate_active_project(state: Mapping[str, Any], event: str) -> None:
    project_state = state.get("project_state")
    if project_state != "active":
        raise ProgressStateError(
            f"refusing event {event!r}: project_state is {project_state!r}, "
            "expected 'active'; terminal projects only accept recover"
        )


def _validate_sub_state_value(value: Any) -> str:
    if not isinstance(value, str) or value not in SUB_STATES:
        raise ProgressStateError(
            f"sub_state must be one of {sorted(SUB_STATES)}, got {value!r}"
        )
    return value


def _validate_review_iteration_value(value: Any) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ProgressStateError(
            f"review_iteration must be a non-negative int, got {value!r}"
        )
    if value > REVIEW_ITERATION_LIMIT:
        # Existing review_iteration is already over the spec cap (0-7). Any
        # mutating event must reject so a tampered or migrated progress.md
        # cannot bypass the human-escalation invariant. The post-increment
        # check inside review-issues still keeps 7 -> 8 rejected; this entry
        # check additionally blocks write-complete / review-passed /
        # human-confirmed from preserving or resetting an over-limit value.
        # (Phase 5.2 round 2 review M2.)
        raise ProgressStateError(
            f"review_iteration is {value}, exceeding the limit of "
            f"{REVIEW_ITERATION_LIMIT}; escalate to a human and reset history"
        )
    return value


def apply_update_event(
    state: Mapping[str, Any],
    event: str,
    *,
    now: str,
) -> EventOutcome:
    """Apply a generic ``update --event`` transition to a progress state.

    Pure: no file I/O, no logging, no clock access. The caller (``progress.py``
    forward path or ``progress_replay.py`` replay path) provides ``now``.

    Validates against ``command-reference.md §2.1`` and raises
    :class:`ProgressStateError` with an actionable message on any rule
    violation. The ``new_state`` returned mutates exactly three fields
    (``sub_state``, ``review_iteration``, ``updated``); every other field is
    copied verbatim so the caller can render with full state preserved.
    """

    if event not in EVENTS:
        raise ProgressStateError(
            f"event must be one of {sorted(EVENTS)}, got {event!r}"
        )
    _validate_timestamp(now, field="now")
    _validate_active_project(state, event)
    sub_state = _validate_sub_state_value(state.get("sub_state"))
    review_iteration = _validate_review_iteration_value(
        state.get("review_iteration", 0)
    )
    raw_stage = state.get("current_stage")

    if event == "write-complete":
        if sub_state not in {"write", "revising"}:
            raise ProgressStateError(
                f"event 'write-complete' requires sub_state in {{write, revising}}, "
                f"got {sub_state!r}"
            )
        new_sub = "in-review"
        new_iter = review_iteration
        summary = f"sub_state {sub_state} -> in-review"
        next_text = "review skill"
    elif event == "review-issues":
        if sub_state != "in-review":
            raise ProgressStateError(
                f"event 'review-issues' requires sub_state 'in-review', got {sub_state!r}"
            )
        new_iter = review_iteration + 1
        if new_iter > REVIEW_ITERATION_LIMIT:
            raise ProgressStateError(
                f"event 'review-issues' would push review_iteration to {new_iter}, "
                f"exceeding the limit of {REVIEW_ITERATION_LIMIT}; escalate to a human"
            )
        new_sub = "revising"
        summary = "sub_state in-review -> revising"
        next_text = "write Change Mode"
    elif event == "review-passed":
        if sub_state != "in-review":
            raise ProgressStateError(
                f"event 'review-passed' requires sub_state 'in-review', got {sub_state!r}"
            )
        new_sub = "review-passed"
        new_iter = 0
        summary = "sub_state in-review -> review-passed"
        next_text = (
            "human-confirmed"
            if raw_stage in GATED_STAGES
            else "advance"
        )
    else:  # event == "human-confirmed"
        if sub_state != "review-passed":
            raise ProgressStateError(
                f"event 'human-confirmed' requires sub_state 'review-passed', "
                f"got {sub_state!r}"
            )
        if raw_stage not in GATED_STAGES:
            raise ProgressStateError(
                f"event 'human-confirmed' is only valid for gated stages "
                f"{sorted(GATED_STAGES)}; current_stage={raw_stage!r}"
            )
        new_sub = "approved"
        new_iter = 0
        summary = "sub_state review-passed -> approved (gated stage human-confirmed)"
        next_text = "advance"

    new_state = dict(state)
    new_state["sub_state"] = new_sub
    new_state["review_iteration"] = new_iter
    new_state["updated"] = now

    result = (
        f"current_stage={raw_stage}, review_iteration={new_iter}"
        if raw_stage is not None
        else f"review_iteration={new_iter}"
    )

    return EventOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=result,
        history_next=next_text,
    )


# ---------- Phase 5.3: update --task state machine ----------


_TASK_ID_RE = re.compile(r"^T\d+$")


@dataclass(frozen=True)
class TaskOutcome:
    """Result of applying a Stage 4 task transition."""

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def _check_planning_done_artifacts(
    root: Path, *, release: str, task_id: str
) -> None:
    """planning-done precondition: breakdown declares Tn AND detailed_design exists."""

    info = load_breakdown_with_tasks(root, release=release)
    if task_id not in info.declared_tasks:
        raise ProgressArtifactError(
            f"breakdown.md does not declare {task_id} (declared: "
            f"{list(info.declared_tasks)}); planning-done requires the task "
            "to appear in the breakdown body"
        )
    load_artifact_frontmatter(
        root,
        doc_type="detailed-design",
        release=release,
        task_id=task_id,
    )


def _require_review_skeleton(
    root: Path,
    *,
    doc_type: str,
    release: str,
    task_id: str,
) -> None:
    """test-review / code-review precondition: report frontmatter is in skeleton state.

    The doc-guardian schema documents the skeleton as
    ``review_status: pending`` plus zero counts. Phase 5.3 enforces only
    the ``review_status`` field; broader structural validation remains
    the doc-guardian binary's job.
    """

    info = load_artifact_frontmatter(
        root,
        doc_type=doc_type,
        release=release,
        task_id=task_id,
    )
    raw_status = info.fields.get("review_status")
    if raw_status != "pending":
        raise ProgressArtifactError(
            f"{info.rel_path}: review_status must be 'pending' for skeleton "
            f"transition, got {raw_status!r}"
        )


def _require_review_pass(
    root: Path,
    *,
    doc_type: str,
    release: str,
    task_id: str,
) -> None:
    """test-done / code-review-passed precondition: review pass + zero blocking."""

    info = load_artifact_frontmatter(
        root,
        doc_type=doc_type,
        release=release,
        task_id=task_id,
    )
    raw_status = info.fields.get("review_status")
    if raw_status != "pass":
        raise ProgressArtifactError(
            f"{info.rel_path}: review_status must be 'pass' (got {raw_status!r}); "
            "transitions to test-done / code-review-passed require pass"
        )
    raw_blocking = info.fields.get("blocking_findings_count")
    if not isinstance(raw_blocking, int) or isinstance(raw_blocking, bool) or raw_blocking != 0:
        raise ProgressArtifactError(
            f"{info.rel_path}: blocking_findings_count must be 0 for review_status=pass, "
            f"got {raw_blocking!r}"
        )


def _require_verification_pass(
    root: Path, *, release: str, task_id: str
) -> None:
    """verified precondition: verification_result.md verification_status==pass."""

    info = load_artifact_frontmatter(
        root,
        doc_type="verification-result",
        release=release,
        task_id=task_id,
    )
    raw_status = info.fields.get("verification_status")
    if raw_status != "pass":
        raise ProgressArtifactError(
            f"{info.rel_path}: verification_status must be 'pass' for transition "
            f"to verified, got {raw_status!r}"
        )


def _check_gap_3_verification_fail(
    *, root: Path, release: str, task_id: str
) -> None:
    """Phase 6.1 Gap-3 precondition: ``verifying -> code-revising`` is
    only legal when ``verification_result.md`` exists with
    ``verification_status ∈ {fail, partial}``.

    Owner: ``development-code-write`` verification retry. This path is
    self-contained and does NOT require an active Bug Flow (that's
    Gap-4 / Phase 6.2 ``bug-rework``).
    """

    info = load_artifact_frontmatter(
        root,
        doc_type="verification-result",
        release=release,
        task_id=task_id,
    )
    raw_status = info.fields.get("verification_status")
    if raw_status not in {"fail", "partial"}:
        raise ProgressArtifactError(
            f"{info.rel_path}: Gap-3 transition (verifying -> code-revising) "
            f"requires verification_status in {{fail, partial}}, got {raw_status!r}"
        )


def _check_artifact_preconditions(
    new_status: str, *, root: Path, release: str, task_id: str
) -> None:
    """Dispatch per-status artifact validation. No-op for transitional states."""

    if new_status == "planning-done":
        _check_planning_done_artifacts(root, release=release, task_id=task_id)
    elif new_status == "test-review":
        _require_review_skeleton(
            root, doc_type="test-review-report",
            release=release, task_id=task_id,
        )
    elif new_status == "test-done":
        _require_review_pass(
            root, doc_type="test-review-report",
            release=release, task_id=task_id,
        )
    elif new_status == "code-review":
        _require_review_skeleton(
            root, doc_type="code-review-report",
            release=release, task_id=task_id,
        )
    elif new_status == "code-review-passed":
        _require_review_pass(
            root, doc_type="code-review-report",
            release=release, task_id=task_id,
        )
    elif new_status == "verified":
        _require_verification_pass(
            root, release=release, task_id=task_id,
        )
    # test-writing / test-revising / code-writing / code-revising / verifying:
    # transitional states with no artifact precondition (caller signals intent).


def _next_skill_for_status(new_status: str) -> str:
    """Suggested next skill / command name for the history entry's `next` field."""

    return {
        "planning-done": "development-test-write",
        "test-writing": "development-test-write",
        "test-review": "development-test-review",
        "test-revising": "development-test-write Change Mode",
        "test-done": "development-code-write",
        "code-writing": "development-code-write",
        "code-review": "development-code-review",
        "code-revising": "development-code-write Change Mode",
        "code-review-passed": "development-code-write verification",
        "verifying": "development-code-write run-tests",
        "verified": "next task or progress.py update --advance",
    }.get(new_status, "next-step")


def apply_update_task(
    state: Mapping[str, Any],
    task_id: str,
    new_status: str,
    *,
    now: str,
    root: str | Path,
    validate_artifacts: bool = True,
) -> TaskOutcome:
    """Apply a Stage 4 task transition to the progress state.

    Phase 5.3 implements the **normal** transitions per
    ``command-reference.md §2.1`` Stage 4 task table. Protected
    transitions (Gap-3 ``verifying -> code-revising`` and Gap-4
    ``verified|code-review-passed -> code-revising`` /
    ``verified -> test-revising``) require active Bug Flow context and
    are deferred to Phase 6 (``bug-start`` / ``bug-rework``).

    The function reads only the artifacts needed for the requested
    transition (a thin frontmatter check; full Class 1-7 validation
    remains the doc-guardian binary's job). It does not run the wider
    cross-progress consistency check covered by Phase 6
    ``validate.py consistency`` / ``progress.py update --advance``.

    ``validate_artifacts`` controls whether the per-status
    artifact precondition is enforced. The forward CLI path
    (``progress.py update --task``) keeps it ``True`` so callers cannot
    record a transition before the supporting artifact is in the right
    state. The replay path (``progress_replay._apply_update_task``)
    sets it ``False`` because replay walks the full history and the
    same artifact file evolves across transitions (skeleton → pass);
    re-reading "current" artifacts during replay would falsely fail an
    early transition that was perfectly valid when it was recorded.
    M1 still catches forward-vs-replay state divergence on
    ``progress.md``.

    Raises :class:`ProgressStateError` on state-machine violations and
    :class:`ProgressArtifactError` on missing or non-conforming
    artifacts. Both are caught at the CLI / replay boundaries.
    """

    if not isinstance(task_id, str) or not _TASK_ID_RE.match(task_id):
        raise ProgressStateError(
            f"task_id must match ^T\\d+$, got {task_id!r}"
        )
    if new_status not in TASK_STATES:
        raise ProgressStateError(
            f"task status must be one of {sorted(TASK_STATES)}, got {new_status!r}"
        )
    _validate_timestamp(now, field="now")
    _validate_active_project(state, f"update-task {task_id}")

    current_stage = state.get("current_stage")
    if current_stage != "development":
        raise ProgressStateError(
            f"update --task requires current_stage='development', got {current_stage!r}"
        )

    # Phase 5.3 round 2 M1: inherit the Phase 5.2 round 2 M2 invariant
    # that a tampered/migrated progress.md whose review_iteration is
    # already over the spec cap (0-7) cannot be a base for any mutating
    # event. update --task does not directly mutate review_iteration,
    # but reading and preserving an out-of-limit value would leave the
    # door open for later commands to inherit it.
    _validate_review_iteration_value(state.get("review_iteration", 0))

    release = state.get("release")
    if not isinstance(release, str):
        raise ProgressStateError(
            f"progress.md release must be a string, got {release!r}"
        )

    raw_dev = state.get("development_state")
    dev_state = dict(raw_dev) if isinstance(raw_dev, dict) else {}
    raw_task_states = dev_state.get("task_states")
    task_states = dict(raw_task_states) if isinstance(raw_task_states, dict) else {}
    old_status = task_states.get(task_id)

    is_gap_3 = (old_status, new_status) == ("verifying", "code-revising")
    if not is_valid_task_transition(old_status, new_status, allow_protected=False):
        protected = (old_status, new_status) in PROTECTED_TASK_TRANSITIONS
        if protected and not is_gap_3:
            # Gap-4 transitions (verified->test-revising / verified->code-revising /
            # code-review-passed->code-revising) require active dev Bug Flow
            # context; only ``bug-start`` / ``bug-rework`` may apply them.
            raise ProgressStateError(
                f"task {task_id} transition {old_status!r} -> {new_status!r} is a "
                "protected Gap-4 rollback; use Phase 6 bug-start / bug-rework"
            )
        if not is_gap_3:
            raise ProgressStateError(
                f"task {task_id} transition {old_status!r} -> {new_status!r} is not a "
                "legal normal transition"
            )
        # Gap-3 (verifying -> code-revising): caller is
        # development-code-write retrying after a failed verification.
        # No active Bug Flow needed; precondition is verification_result
        # in {fail, partial}.

    if validate_artifacts:
        if is_gap_3:
            _check_gap_3_verification_fail(
                root=Path(root), release=release, task_id=task_id,
            )
        else:
            _check_artifact_preconditions(
                new_status, root=Path(root), release=release, task_id=task_id,
            )

    task_states[task_id] = new_status
    dev_state["task_states"] = task_states

    new_state = dict(state)
    new_state["development_state"] = dev_state
    new_state["updated"] = now

    if old_status == new_status:
        # planning-done idempotent retry: spec allows it as a no-op-shaped
        # transition. We still record a history entry so the replay path
        # remains lossless, but mark it as idempotent in the summary.
        summary = (
            f"task={task_id} status={new_status} (idempotent retry)"
        )
        result = f"task={task_id} unchanged at {new_status}"
    else:
        summary = f"task={task_id} status={new_status}"
        if old_status is None:
            result = f"task={task_id} registered (was unset)"
        else:
            result = f"task={task_id} from {old_status}"

    return TaskOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=result,
        history_next=_next_skill_for_status(new_status),
    )


# ---------- Phase 5.4: release lifecycle + bug intake ----------


_RELEASE_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")
_RELEASE_START_STAGE_MAP: dict[str, str] = {
    "S2-1": "prd-inception",
    "S2-2": "srs-specification",
    "S2-3": "srs-specification",
}
RELEASE_START_SUBTYPES = frozenset(_RELEASE_START_STAGE_MAP)


# Phase 5.4 round 2 review M1: BUG paths in ``unresolved_bugs`` must be
# canonical project-relative paths under ``docs/bug/``. Enforced at the
# state-machine layer so both forward (bug-intake) and replay (recover)
# reject corrupted history before release-start fans out to anything
# outside ``--root``.
_BUG_PATH_RE = re.compile(r"^docs/bug/BUG-\d{3}\.md$")
_INCIDENT_PATH_RE = re.compile(r"^docs/incident/INCIDENT-\d{3}\.md$")


def _validate_doc_path_shape(
    path: str, *, label: str, regex: re.Pattern[str], expected_pattern: str,
) -> None:
    """Generic shape validator shared by BUG / INCIDENT path checks.

    Rejects:
      - non-string / empty values
      - backslash separators
      - POSIX absolute (``/``) or Windows-drive absolute (``C:/...``) paths
      - any segment that is empty / ``.`` / ``..``
      - filenames not matching ``regex``

    Each caller-facing error message uses ``label`` (e.g. ``"BUG"`` or
    ``"INCIDENT"``) and ``expected_pattern`` (the human-readable form
    such as ``docs/bug/BUG-NNN.md``) so operators see a consistent
    diagnosis pattern across both validators.
    """

    if not isinstance(path, str) or not path:
        raise ProgressStateError(
            f"{label} path must be a non-empty string, got {path!r}"
        )
    if "\\" in path:
        raise ProgressStateError(
            f"{label} path must use forward slashes, got {path!r}"
        )
    if path.startswith("/") or (len(path) >= 2 and path[1] == ":"):
        raise ProgressStateError(
            f"{label} path must be project-root relative, not absolute: {path!r}"
        )
    parts = path.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ProgressStateError(
            f"{label} path must not contain '.' or '..' segments (or empty segments): "
            f"{path!r}"
        )
    if not regex.match(path):
        raise ProgressStateError(
            f"{label} path must match {expected_pattern!r} "
            f"(3-digit zero-padded ID), got {path!r}"
        )


def _validate_bug_path_shape(bug_path: str) -> None:
    """Reject malformed BUG paths before they reach ``unresolved_bugs``.

    Phase 5.4 round 2 review M1; Phase 6.3 refactored to share the
    generic shape validator with ``_validate_incident_path_shape``.
    Rejection rules and call-site contracts are unchanged.

    The ``release-start`` fan-out additionally re-resolves the path under
    ``--root`` and verifies it stays inside the project tree (defense in
    depth against symlink/race tampering between intake and release-start).
    """

    _validate_doc_path_shape(
        bug_path,
        label="BUG",
        regex=_BUG_PATH_RE,
        expected_pattern="docs/bug/BUG-NNN.md",
    )


def _validate_incident_path_shape(incident_path: str) -> None:
    """Reject malformed INCIDENT paths.

    Phase 6.3: parallel to ``_validate_bug_path_shape`` for the
    ``incident-start`` / ``incident-resolve`` commands.
    ``incident_report_path`` carried in ``progress.md`` and INCIDENT
    history tokens must satisfy this shape so replay can never feed
    ``apply_incident_*`` an absolute, traversal, or non-INCIDENT path.

    Like BUG, callers should additionally re-resolve the path under
    ``--root`` and verify it stays inside the project tree as defense
    in depth.
    """

    _validate_doc_path_shape(
        incident_path,
        label="INCIDENT",
        regex=_INCIDENT_PATH_RE,
        expected_pattern="docs/incident/INCIDENT-NNN.md",
    )


def _parse_release_tuple(release: str) -> tuple[int, int]:
    match = _RELEASE_VERSION_RE.match(release)
    if not match:
        raise ProgressStateError(
            f"release version must match ^\\d+\\.\\d+$, got {release!r}"
        )
    return (int(match.group(1)), int(match.group(2)))


@dataclass(frozen=True)
class ReleaseCloseOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def apply_release_close(
    state: Mapping[str, Any], *, now: str
) -> ReleaseCloseOutcome:
    """Mark the current release closed at the end of Stage 7.

    Per ``command-reference.md §5``: requires ``release_state==active``,
    ``current_stage==project-retrospective``, ``sub_state==review-passed``.
    The current release is appended to ``previous_releases``;
    ``release_close_reason`` is set to ``"stage-7-completed"``.

    Phase 5.2 round 2 M2 / Phase 5.3 round 2 M1 invariant inherited:
    refuses to mutate when ``review_iteration > REVIEW_ITERATION_LIMIT``.
    """

    _validate_timestamp(now, field="now")
    _validate_active_project(state, "release-close")
    _validate_review_iteration_value(state.get("review_iteration", 0))

    if state.get("release_state") != "active":
        raise ProgressStateError(
            f"release-close requires release_state='active', got {state.get('release_state')!r}"
        )
    if state.get("current_stage") != "project-retrospective":
        raise ProgressStateError(
            "release-close requires current_stage='project-retrospective', got "
            f"{state.get('current_stage')!r}"
        )
    if state.get("sub_state") != "review-passed":
        raise ProgressStateError(
            f"release-close requires sub_state='review-passed', got {state.get('sub_state')!r}"
        )

    release = state.get("release")
    if not isinstance(release, str) or not _RELEASE_VERSION_RE.match(release):
        raise ProgressStateError(
            f"progress.md release must be a quoted release string, got {release!r}"
        )

    previous = list(state.get("previous_releases") or [])
    if release in previous:
        raise ProgressStateError(
            f"release {release!r} already appears in previous_releases; "
            "progress.md may have been edited out-of-band"
        )
    previous.append(release)

    new_state = dict(state)
    new_state["release_state"] = "closed"
    new_state["release_close_reason"] = "stage-7-completed"
    new_state["previous_releases"] = previous
    new_state["updated"] = now

    return ReleaseCloseOutcome(
        new_state=new_state,
        history_summary=f"release {release} closed",
        history_result=f"previous_releases={previous}",
        history_next="release-start or bug-intake",
    )


@dataclass(frozen=True)
class ReleaseStartOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None
    consumed_bugs: tuple[str, ...]


def _initial_artifacts_for_release(release: str) -> dict[str, Any]:
    return {
        "prd": "docs/prd/prd.md",
        "architecture": "docs/architecture/architecture.md",
        "srs": f"docs/release{release}/srs/srs.md",
        "acceptance_plan": f"docs/release{release}/srs/acceptance_plan.md",
        "integration_plan": None,
        "architecture_delta": None,
    }


def apply_release_start(
    state: Mapping[str, Any],
    *,
    new_version: str,
    scenario_subtype: str,
    now: str,
) -> ReleaseStartOutcome:
    """Start a new active release after the previous one was closed.

    Per ``command-reference.md §6``: requires ``release_state==closed``,
    a strictly-greater ``new_version`` than every ``previous_releases``
    entry, and a ``scenario_subtype`` in
    ``{S2-1, S2-2, S2-3}`` (S2-4 is forbidden — it must be promoted to a
    fresh S3 project per spec).

    The function clears ``unresolved_bugs`` and returns the consumed
    list as :attr:`ReleaseStartOutcome.consumed_bugs` so the CLI can
    fan-out frontmatter mutations to each ``BUG-NNN.md``
    (``target_release`` / ``consumed_in_release``) inside the same
    atomic transaction. Replay does NOT re-write BUG files (consistent
    with the Phase 5.3 ``validate_artifacts=False`` design choice).
    """

    _validate_timestamp(now, field="now")
    _validate_review_iteration_value(state.get("review_iteration", 0))

    project_state = state.get("project_state")
    if project_state != "active":
        raise ProgressStateError(
            f"release-start requires project_state='active', got {project_state!r}"
        )
    if state.get("release_state") != "closed":
        raise ProgressStateError(
            f"release-start requires release_state='closed', got {state.get('release_state')!r}"
        )
    if scenario_subtype not in _RELEASE_START_STAGE_MAP:
        raise ProgressStateError(
            f"release-start scenario_subtype must be one of "
            f"{sorted(RELEASE_START_SUBTYPES)}, got {scenario_subtype!r}"
        )
    if not isinstance(new_version, str):
        raise ProgressStateError(
            f"release-start new_version must be a string, got {type(new_version).__name__}"
        )
    new_tuple = _parse_release_tuple(new_version)

    # Strictly greater than every previously-known release. Both the just-
    # closed release and the historical ``previous_releases`` list contribute.
    candidates: list[str] = []
    current = state.get("release")
    if isinstance(current, str):
        candidates.append(current)
    for prior in state.get("previous_releases") or []:
        if isinstance(prior, str):
            candidates.append(prior)
    for prior in candidates:
        if not _RELEASE_VERSION_RE.match(prior):
            raise ProgressStateError(
                f"progress.md contains invalid release {prior!r}; recover required"
            )
        if _parse_release_tuple(prior) >= new_tuple:
            raise ProgressStateError(
                f"release-start new_version {new_version!r} must be strictly greater "
                f"than every prior release; found {prior!r}"
            )

    consumed_bugs = tuple(
        path
        for path in state.get("unresolved_bugs") or []
        if isinstance(path, str)
    )
    raw_unresolved = state.get("unresolved_bugs") or []
    if any(not isinstance(p, str) for p in raw_unresolved):
        raise ProgressStateError(
            f"unresolved_bugs must be a list of string paths, got {raw_unresolved!r}"
        )

    new_state = dict(state)
    new_state["release"] = new_version
    new_state["release_state"] = "active"
    new_state["release_close_reason"] = None
    new_state["scenario"] = "S2"
    new_state["scenario_subtype"] = scenario_subtype
    new_state["current_stage"] = _RELEASE_START_STAGE_MAP[scenario_subtype]
    new_state["sub_state"] = "write"
    new_state["review_iteration"] = 0
    new_state["unresolved_bugs"] = []
    new_state["artifacts"] = _initial_artifacts_for_release(new_version)
    # Clear any leftover Stage 4 task state from the previous release;
    # the next Stage 4 cycle will rebuild it.
    new_state.pop("development_state", None)
    new_state["updated"] = now

    # Phase 5.4 round 2 L1: keep canonical ``version=`` and ``scenario=``
    # tokens in the summary itself so replay's ``_kv_tokens`` can reverse
    # them without falling back to the result field. Result still echoes
    # the same tokens for human readability.
    return ReleaseStartOutcome(
        new_state=new_state,
        history_summary=(
            f"version={new_version} scenario={scenario_subtype} new release started, "
            f"consumed {len(consumed_bugs)} unresolved bugs"
        ),
        history_result=(
            f"version={new_version} scenario_subtype={scenario_subtype} "
            f"consumed={len(consumed_bugs)}"
        ),
        history_next=(
            f"{_RELEASE_START_STAGE_MAP[scenario_subtype]}-write "
            f"({'Full Mode' if scenario_subtype != 'S2-3' else 'Change Mode'})"
        ),
        consumed_bugs=consumed_bugs,
    )


@dataclass(frozen=True)
class BugIntakeOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def apply_bug_intake(
    state: Mapping[str, Any], bug_path: str, *, now: str
) -> BugIntakeOutcome:
    """Append a post-close BUG path to ``unresolved_bugs``.

    Per ``command-reference.md §7``: only valid while
    ``release_state==closed`` (the post-close window between
    ``release-close`` and ``release-start``). Duplicate paths are
    rejected; the BUG frontmatter ``target_release`` /
    ``consumed_in_release`` validation is the CLI's responsibility
    (this function only owns the progress-state mutation).
    """

    _validate_timestamp(now, field="now")
    _validate_review_iteration_value(state.get("review_iteration", 0))

    project_state = state.get("project_state")
    if project_state != "active":
        raise ProgressStateError(
            f"bug-intake requires project_state='active', got {project_state!r}"
        )
    if state.get("release_state") != "closed":
        raise ProgressStateError(
            f"bug-intake requires release_state='closed' (post-close window), "
            f"got {state.get('release_state')!r}"
        )
    if not isinstance(bug_path, str) or not bug_path:
        raise ProgressStateError(
            f"bug-intake bug_path must be a non-empty string, got {bug_path!r}"
        )
    # Phase 5.4 round 2 M1: enforce path shape on both forward and replay
    # paths so a corrupted progress.md / progress-history.md cannot feed
    # release-start fan-out an absolute, traversal, or non-BUG path.
    _validate_bug_path_shape(bug_path)

    raw_unresolved = list(state.get("unresolved_bugs") or [])
    if bug_path in raw_unresolved:
        raise ProgressStateError(
            f"bug-intake refuses duplicate: {bug_path!r} is already in unresolved_bugs"
        )
    new_unresolved = raw_unresolved + [bug_path]

    new_state = dict(state)
    new_state["unresolved_bugs"] = new_unresolved
    new_state["updated"] = now

    return BugIntakeOutcome(
        new_state=new_state,
        history_summary=f"bug={bug_path} registered (post-close)",
        history_result=f"unresolved_bugs count = {len(new_unresolved)}",
        history_next="wait for next release-start",
    )


# ---------- Phase 6.1: Bug Flow entry / exit ----------


_ROOT_CAUSE_TO_STAGE: dict[str, str] = {
    "srs": "srs-specification",
    "architecture": "architecture-design",
    "development": "development",
}
ROOT_CAUSES_FOR_BUG_START = frozenset(_ROOT_CAUSE_TO_STAGE)


def compute_dev_bug_rollback(
    state: Mapping[str, Any], triage: Any,
) -> tuple[tuple[str, str, str, str], ...]:
    """Phase 6.1/6.2 Gap-4 helper — derive per-task rollback decisions.

    Given the current ``progress.md`` state and the parsed
    ``## Triage Analysis`` block of the active BUG, decide per-task
    rollbacks per Gap-4:

    * ``classification == "test"``: ``verified -> test-revising`` for
      affected tasks currently in ``verified``.
    * ``classification == "source"``: ``verified -> code-revising`` for
      ``verified`` tasks AND ``code-review-passed -> code-revising`` for
      ``code-review-passed`` tasks.
    * ``classification == "ambiguous"``: no auto-rollback; spec mandates
      planning route. Returns an empty tuple.
    * ``unable_to_localize == True``: also no auto-rollback.

    Affected tasks not registered in ``progress.md`` and tasks whose
    current state is not eligible for any Gap-4 transition are silently
    skipped — caller is responsible for routing them through
    ``development-planning-write``.

    Returns a tuple of ``(task_id, old_status, new_status, reason)``
    that ``apply_bug_start`` / ``apply_bug_rework`` consume.

    This helper lives in ``progress_state.py`` rather than the CLI so
    both ``cmd_bug_start`` and ``cmd_bug_rework`` (Phase 6.2) reuse the
    same logic without code duplication. The function is read-only on
    ``state`` and does no I/O.
    """

    if getattr(triage, "unable_to_localize", False):
        return ()
    classification = getattr(triage, "classification", None)
    if classification == "ambiguous":
        return ()
    raw_dev = state.get("development_state") or {}
    task_states = raw_dev.get("task_states") or {}

    decisions: list[tuple[str, str, str, str]] = []
    for task_id in getattr(triage, "affected_tasks", ()):
        old_status = task_states.get(task_id)
        if old_status is None:
            # Task not registered in progress.md; spec says skip and let
            # planning route handle.
            continue
        if classification == "test":
            if old_status == "verified":
                decisions.append(
                    (task_id, "verified", "test-revising", "test-only fix"),
                )
        elif classification == "source":
            if old_status == "verified":
                decisions.append(
                    (task_id, "verified", "code-revising", "source fix"),
                )
            elif old_status == "code-review-passed":
                decisions.append(
                    (
                        task_id,
                        "code-review-passed",
                        "code-revising",
                        "source fix",
                    ),
                )
    return tuple(decisions)


@dataclass(frozen=True)
class BugStartOutcome:
    """Outcome of ``progress.py bug-start --bug --root-cause``.

    ``rollback_decisions`` is the (possibly empty) tuple of per-task
    Gap-4 rollbacks that the forward CLI computed by parsing the BUG's
    ``## Triage Analysis`` section. Each entry is
    ``(task_id, old_status, new_status, reason)``. The replay handler
    re-derives the same tuple from the canonical history summary tokens
    so forward and replay end at identical state without re-reading the
    BUG body. Phase 6.1 covers ``verified -> test-revising`` /
    ``verified -> code-revising`` / ``code-review-passed -> code-revising``;
    Phase 6.2 ``bug-rework`` reuses this same shape.
    """

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None
    rollback_decisions: tuple[tuple[str, str, str, str], ...]


@dataclass(frozen=True)
class BugCloseOutcome:
    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def _validate_bug_flow_inactive(state: Mapping[str, Any]) -> None:
    bug_flow = state.get("bug_flow") or {}
    if bug_flow.get("active"):
        raise ProgressStateError(
            f"bug_flow is already active (root_cause={bug_flow.get('root_cause')!r}, "
            f"bug={bug_flow.get('bug_report_path')!r}); refuse to start another"
        )


def _validate_bug_flow_active(state: Mapping[str, Any]) -> dict:
    bug_flow = state.get("bug_flow") or {}
    if not bug_flow.get("active"):
        raise ProgressStateError(
            "bug_flow is not active; refuse to apply Bug Flow command"
        )
    return dict(bug_flow)


def apply_bug_start(
    state: Mapping[str, Any],
    bug_path: str,
    root_cause: str,
    *,
    now: str,
    rollback_decisions: tuple[tuple[str, str, str, str], ...] = (),
) -> BugStartOutcome:
    """Enter active Bug Flow.

    Per ``command-reference.md §8``: requires no active Bug Flow,
    ``release_state==active``, ``current_stage==testing``,
    ``sub_state==review-passed``, a canonical
    ``docs/bug/BUG-NNN.md`` ``bug_path``, and a ``root_cause`` in
    ``{srs, architecture, development}``.

    Mutation:
      * ``bug_flow`` switches to ``active=true`` with ``bug_report_path``
        and ``root_cause`` fields set;
      * ``current_stage`` reroutes to the root-cause stage (per
        :data:`_ROOT_CAUSE_TO_STAGE`);
      * ``sub_state`` resets to ``write``;
      * ``review_iteration`` resets to ``0``;
      * For ``root_cause==development`` AND non-empty
        ``rollback_decisions``, ``development_state.task_states`` is
        updated per the supplied Gap-4 rollback list. Each tuple is
        ``(task_id, old_status, new_status, reason)`` and must match a
        :data:`PROTECTED_TASK_TRANSITIONS` entry.

    The CLI computes ``rollback_decisions`` by parsing the BUG body
    ``## Triage Analysis`` (see ``progress_artifacts.parse_bug_triage_analysis``);
    replay re-derives the same tuple from canonical history summary
    tokens so forward and replay converge.
    """

    _validate_timestamp(now, field="now")
    _validate_review_iteration_value(state.get("review_iteration", 0))
    _validate_bug_path_shape(bug_path)

    if state.get("project_state") != "active":
        raise ProgressStateError(
            f"bug-start requires project_state='active', "
            f"got {state.get('project_state')!r}"
        )
    if state.get("release_state") != "active":
        raise ProgressStateError(
            f"bug-start requires release_state='active', "
            f"got {state.get('release_state')!r}"
        )
    if state.get("current_stage") != "testing":
        raise ProgressStateError(
            f"bug-start requires current_stage='testing', "
            f"got {state.get('current_stage')!r}"
        )
    if state.get("sub_state") != "review-passed":
        raise ProgressStateError(
            f"bug-start requires sub_state='review-passed', "
            f"got {state.get('sub_state')!r}"
        )
    _validate_bug_flow_inactive(state)
    if root_cause not in _ROOT_CAUSE_TO_STAGE:
        raise ProgressStateError(
            f"bug-start root_cause must be one of "
            f"{sorted(ROOT_CAUSES_FOR_BUG_START)}, got {root_cause!r} "
            "(prd-exception goes through incident-start in Phase 6.3)"
        )

    new_state = dict(state)
    new_state["bug_flow"] = {
        "active": True,
        "bug_report_path": bug_path,
        "root_cause": root_cause,
    }
    new_state["current_stage"] = _ROOT_CAUSE_TO_STAGE[root_cause]
    new_state["sub_state"] = "write"
    new_state["review_iteration"] = 0
    new_state["updated"] = now

    # Gap-4 dev rollback: only legitimate when root_cause=='development'.
    applied_rollbacks: list[tuple[str, str, str, str]] = []
    if rollback_decisions:
        if root_cause != "development":
            raise ProgressStateError(
                f"bug-start rollback_decisions are only valid for "
                f"root_cause='development', got {root_cause!r}"
            )
        raw_dev = state.get("development_state")
        dev_state = dict(raw_dev) if isinstance(raw_dev, dict) else {}
        raw_task_states = dev_state.get("task_states")
        task_states = dict(raw_task_states) if isinstance(raw_task_states, dict) else {}
        for decision in rollback_decisions:
            if not isinstance(decision, tuple) or len(decision) != 4:
                raise ProgressStateError(
                    f"rollback decision must be a 4-tuple "
                    f"(task_id, old_status, new_status, reason), got {decision!r}"
                )
            task_id, decided_old, new_status, reason = decision
            if not isinstance(task_id, str) or not _TASK_ID_RE.match(task_id):
                raise ProgressStateError(
                    f"rollback task_id must match ^T\\d+$, got {task_id!r}"
                )
            actual_old = task_states.get(task_id)
            if actual_old != decided_old:
                raise ProgressStateError(
                    f"rollback for {task_id}: caller said old status was "
                    f"{decided_old!r} but progress.md has {actual_old!r}; "
                    "out-of-band edit detected"
                )
            if (decided_old, new_status) not in PROTECTED_TASK_TRANSITIONS:
                raise ProgressStateError(
                    f"rollback for {task_id}: ({decided_old!r} -> {new_status!r}) "
                    "is not a Gap-4 protected transition"
                )
            task_states[task_id] = new_status
            applied_rollbacks.append((task_id, decided_old, new_status, reason))
        if applied_rollbacks:
            dev_state["task_states"] = task_states
            new_state["development_state"] = dev_state

    # History summary: canonical tokens for replay.
    rollback_token = ""
    if applied_rollbacks:
        rollback_pieces = ";".join(
            f"{tid}:{old}->{new}" for tid, old, new, _reason in applied_rollbacks
        )
        rollback_token = f" rollback={rollback_pieces}"
    summary = (
        f"bug={bug_path} root_cause={root_cause} Bug Flow entered"
        f"{rollback_token}"
    )
    target_stage = _ROOT_CAUSE_TO_STAGE[root_cause]
    if applied_rollbacks:
        rollback_reasons = "; ".join(
            f"{tid}: {reason}" for tid, _o, _n, reason in applied_rollbacks
        )
        result = f"current_stage={target_stage} ({rollback_reasons})"
        next_text = f"{target_stage}-write Change Mode"
    elif root_cause == "development":
        # Phase 6.1 round 2 L1: dev root cause with empty rollback list
        # means BUG body either marked 'unable to localize', had
        # ambiguous classification, or no affected task matched the
        # required prior state. Spec (command-reference.md §8 +
        # task6_plan §6.2) mandates a persistent history note that
        # development-planning-write must replan/route. The note lives
        # in result/next so replay reproduces it deterministically
        # (forward and replay both apply this branch when applied_rollbacks
        # is empty for dev root cause).
        result = (
            f"current_stage={target_stage}; "
            "route=development-planning-write (no auto-rollback applied)"
        )
        next_text = "development-planning-write replan/route"
    else:
        # SRS / Architecture root cause routes to its respective stage's
        # write skill; no planning-route note required because rollback
        # decisions are dev-only.
        result = f"current_stage={target_stage}"
        next_text = f"{target_stage}-write Change Mode"

    return BugStartOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=result,
        history_next=next_text,
        rollback_decisions=tuple(applied_rollbacks),
    )


# ---------- Phase 6.2: Bug Flow retest re-route (Gap-5) ----------


@dataclass(frozen=True)
class BugReworkOutcome:
    """Outcome of ``progress.py bug-rework --bug``.

    Mirrors :class:`BugStartOutcome` but for the active retest re-route
    case (Phase 6.2 / Gap-5). ``rollback_decisions`` is the (possibly
    empty) tuple of per-task Gap-4 rollbacks that the forward CLI
    computed by parsing the BUG's ``## Triage Analysis`` section. The
    replay handler re-derives the same tuple from canonical history
    summary tokens so forward and replay end at identical state without
    re-reading the BUG body.
    """

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
    """Re-route an active Bug Flow whose retest came back fail/partial.

    Per ``command-reference.md §9`` (Gap-5): requires an active Bug
    Flow, ``current_stage==testing``, ``sub_state==review-passed``, and
    the supplied ``bug_path`` must equal ``bug_flow.bug_report_path``.
    The current ``bug_flow.root_cause`` must be in
    ``{srs, architecture, development}`` (a stale ``prd-exception`` here
    indicates an out-of-band edit and is rejected).

    Mutation:
      * ``bug_flow`` is unchanged (active stays true; path/root_cause
        stay set);
      * ``current_stage`` reroutes to the root-cause stage (per
        :data:`_ROOT_CAUSE_TO_STAGE`);
      * ``sub_state`` resets to ``write``;
      * ``review_iteration`` resets to ``0``;
      * For ``root_cause==development`` AND non-empty
        ``rollback_decisions``, ``development_state.task_states`` is
        updated per the supplied Gap-4 rollback list. Each tuple is
        ``(task_id, old_status, new_status, reason)`` and must match a
        :data:`PROTECTED_TASK_TRANSITIONS` entry — same shape and
        validation as :func:`apply_bug_start`.

    The CLI verifies the latest ``test-report`` shows
    ``verification_status in {fail, partial}`` and computes
    ``rollback_decisions`` by parsing the BUG body
    ``## Triage Analysis`` (see
    ``progress_artifacts.parse_bug_triage_analysis``); replay
    re-derives the same tuple from canonical history summary tokens so
    forward and replay converge.

    Note: ``bug-rework`` does NOT take a ``--root-cause`` argument; the
    root cause is fixed by the existing ``bug_flow.root_cause``. The CLI
    confirms the BUG file's frontmatter ``root_cause`` matches before
    invoking this function (preventing caller from swapping BUG
    documents mid-flow).
    """

    _validate_timestamp(now, field="now")
    _validate_active_project(state, "bug-rework")
    _validate_review_iteration_value(state.get("review_iteration", 0))
    _validate_bug_path_shape(bug_path)

    if state.get("current_stage") != "testing":
        raise ProgressStateError(
            f"bug-rework requires current_stage='testing', "
            f"got {state.get('current_stage')!r}"
        )
    if state.get("sub_state") != "review-passed":
        raise ProgressStateError(
            f"bug-rework requires sub_state='review-passed', "
            f"got {state.get('sub_state')!r}"
        )
    bug_flow = _validate_bug_flow_active(state)

    active_path = bug_flow.get("bug_report_path")
    if active_path != bug_path:
        raise ProgressStateError(
            f"bug-rework bug path {bug_path!r} does not match active "
            f"bug_flow.bug_report_path {active_path!r}; refuse to rework "
            "a different BUG (use bug-close + bug-start for a new issue)"
        )

    root_cause = bug_flow.get("root_cause")
    if root_cause not in _ROOT_CAUSE_TO_STAGE:
        raise ProgressStateError(
            f"bug-rework requires bug_flow.root_cause in "
            f"{sorted(ROOT_CAUSES_FOR_BUG_START)}, got {root_cause!r} "
            "(prd-exception goes through incident-resolve in Phase 6.3)"
        )

    new_state = dict(state)
    new_state["current_stage"] = _ROOT_CAUSE_TO_STAGE[root_cause]
    new_state["sub_state"] = "write"
    new_state["review_iteration"] = 0
    new_state["updated"] = now

    # Gap-4 dev rollback: only legitimate when root_cause=='development'.
    applied_rollbacks: list[tuple[str, str, str, str]] = []
    if rollback_decisions:
        if root_cause != "development":
            raise ProgressStateError(
                f"bug-rework rollback_decisions are only valid for "
                f"root_cause='development', got {root_cause!r}"
            )
        raw_dev = state.get("development_state")
        dev_state = dict(raw_dev) if isinstance(raw_dev, dict) else {}
        raw_task_states = dev_state.get("task_states")
        task_states = dict(raw_task_states) if isinstance(raw_task_states, dict) else {}
        for decision in rollback_decisions:
            if not isinstance(decision, tuple) or len(decision) != 4:
                raise ProgressStateError(
                    f"rollback decision must be a 4-tuple "
                    f"(task_id, old_status, new_status, reason), got {decision!r}"
                )
            task_id, decided_old, new_status, reason = decision
            if not isinstance(task_id, str) or not _TASK_ID_RE.match(task_id):
                raise ProgressStateError(
                    f"rollback task_id must match ^T\\d+$, got {task_id!r}"
                )
            actual_old = task_states.get(task_id)
            if actual_old != decided_old:
                raise ProgressStateError(
                    f"rollback for {task_id}: caller said old status was "
                    f"{decided_old!r} but progress.md has {actual_old!r}; "
                    "out-of-band edit detected"
                )
            if (decided_old, new_status) not in PROTECTED_TASK_TRANSITIONS:
                raise ProgressStateError(
                    f"rollback for {task_id}: ({decided_old!r} -> {new_status!r}) "
                    "is not a Gap-4 protected transition"
                )
            task_states[task_id] = new_status
            applied_rollbacks.append((task_id, decided_old, new_status, reason))
        if applied_rollbacks:
            dev_state["task_states"] = task_states
            new_state["development_state"] = dev_state

    # History summary: canonical tokens for replay (mirrors bug-start).
    rollback_token = ""
    if applied_rollbacks:
        rollback_pieces = ";".join(
            f"{tid}:{old}->{new}" for tid, old, new, _reason in applied_rollbacks
        )
        rollback_token = f" rollback={rollback_pieces}"
    summary = (
        f"bug={bug_path} root_cause={root_cause} Bug Flow rerouted"
        f"{rollback_token}"
    )
    target_stage = _ROOT_CAUSE_TO_STAGE[root_cause]
    if applied_rollbacks:
        rollback_reasons = "; ".join(
            f"{tid}: {reason}" for tid, _o, _n, reason in applied_rollbacks
        )
        result = f"current_stage={target_stage} ({rollback_reasons})"
        next_text = f"{target_stage}-write Change Mode"
    elif root_cause == "development":
        # Mirrors bug-start Phase 6.1 round 2 L1: dev root cause with
        # empty rollback list means BUG body either marked 'unable to
        # localize', had ambiguous classification, or no affected task
        # matched the required prior state. Persist a planning-route
        # note so replay (which has no triage context) reproduces the
        # same history_result / history_next.
        result = (
            f"current_stage={target_stage}; "
            "route=development-planning-write (no auto-rollback applied)"
        )
        next_text = "development-planning-write replan/route"
    else:
        result = f"current_stage={target_stage}"
        next_text = f"{target_stage}-write Change Mode"

    return BugReworkOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=result,
        history_next=next_text,
        rollback_decisions=tuple(applied_rollbacks),
    )


def apply_bug_close(
    state: Mapping[str, Any], *, now: str
) -> BugCloseOutcome:
    """Exit active Bug Flow after a passing retest.

    Per ``command-reference.md §10``: requires active Bug Flow and
    ``current_stage==testing``. The CLI is responsible for verifying the
    latest test-report ``verification_status==pass`` (via
    ``progress_artifacts.load_test_report``); this state-machine
    function does not do file I/O.

    Mutation:
      * ``bug_flow`` clears (active=false, path/root_cause=null);
      * ``current_stage`` stays at ``testing``;
      * ``sub_state`` is left unchanged so the caller can subsequently
        invoke ``progress.py update --advance`` (Phase 6.4) to step out
        of Stage 5.
    """

    _validate_timestamp(now, field="now")
    _validate_active_project(state, "bug-close")
    _validate_review_iteration_value(state.get("review_iteration", 0))

    bug_flow = _validate_bug_flow_active(state)
    if state.get("current_stage") != "testing":
        raise ProgressStateError(
            f"bug-close requires current_stage='testing', "
            f"got {state.get('current_stage')!r}"
        )

    closed_path = bug_flow.get("bug_report_path")
    closed_root_cause = bug_flow.get("root_cause")

    new_state = dict(state)
    new_state["bug_flow"] = {
        "active": False,
        "bug_report_path": None,
        "root_cause": None,
    }
    new_state["updated"] = now

    return BugCloseOutcome(
        new_state=new_state,
        history_summary="Bug Flow exited (retest passed)",
        history_result=(
            f"closed bug={closed_path} root_cause={closed_root_cause}"
        ),
        history_next="progress.py update --advance to delivery",
    )


# ---------- Phase 6.3: PRD-exception incident lifecycle ----------


_INCIDENT_RESOLVE_ACTIONS = frozenset({"continue", "abort", "reconstruct"})
_INCIDENT_TERMINAL_ACTIONS = frozenset({"abort", "reconstruct"})


@dataclass(frozen=True)
class IncidentStartOutcome:
    """Outcome of ``progress.py incident-start --bug --report``.

    Mutation atomically opens both the Bug Flow (with
    ``root_cause=prd-exception``) and the workflow-incident state.
    The CLI is responsible for double-validating BOTH the BUG and
    INCIDENT documents via ``doc-guardian/scripts/validate.py file``
    before this function runs (round 2 M6 contract); this state-machine
    function does no I/O.
    """

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


@dataclass(frozen=True)
class IncidentResolveOutcome:
    """Outcome of ``progress.py incident-resolve --action``.

    ``is_terminal`` is ``True`` for ``abort`` / ``reconstruct`` and
    ``False`` for ``continue``. Replay uses the same boolean (re-derived
    from the ``action=`` summary token) to flip ``seen_terminal`` only
    when appropriate, preserving the rule that ``--action continue``
    can be followed by further legal mutations (the project resumes at
    ``testing / review-passed``).
    """

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None
    is_terminal: bool


def apply_incident_start(
    state: Mapping[str, Any],
    bug_path: str,
    incident_path: str,
    *,
    now: str,
) -> IncidentStartOutcome:
    """Open a PRD-exception incident.

    Per ``command-reference.md §11`` (v0.6 F2): ``incident-start``
    atomically sets both ``bug_flow`` and the workflow-incident state.

    Preconditions:
      * ``project_state == "active"``;
      * ``review_iteration <= 7`` (M2 entry guard);
      * ``bug_flow.active == false`` (caller must close any active flow first);
      * ``workflow_incident_active == false`` (caller can't be already inside
        another incident);
      * ``bug_path`` matches ``docs/bug/BUG-NNN.md`` shape;
      * ``incident_path`` matches ``docs/incident/INCIDENT-NNN.md`` shape.

    Mutation:
      * ``bug_flow.active`` → ``true``;
      * ``bug_flow.bug_report_path`` → ``bug_path``;
      * ``bug_flow.root_cause`` → ``"prd-exception"`` (literal; not in
        ``_ROOT_CAUSE_TO_STAGE`` because incident routes to a special
        pseudo-stage rather than a normal write skill);
      * ``workflow_incident_active`` → ``true``;
      * ``incident_report_path`` → ``incident_path``;
      * ``current_stage`` → ``"workflow-incident-analysis"``;
      * ``sub_state`` is preserved (incident analysis does not consume
        review-passed; on resolve continue, sub_state is reset there);
      * ``review_iteration`` is preserved.

    The CLI enforces BUG ``root_cause == "prd-exception"`` and INCIDENT
    ``triggered_by_bug == BUG bug_id`` via :func:`load_bug_report` /
    :func:`load_artifact_frontmatter` plus a double validate-py invocation
    (round 2 M6); this state-machine function relies on those checks
    having already passed.
    """

    _validate_timestamp(now, field="now")
    _validate_active_project(state, "incident-start")
    _validate_review_iteration_value(state.get("review_iteration", 0))
    _validate_bug_path_shape(bug_path)
    _validate_incident_path_shape(incident_path)

    _validate_bug_flow_inactive(state)
    if state.get("workflow_incident_active"):
        raise ProgressStateError(
            "incident-start refuses to open a second incident: "
            f"workflow_incident_active is already True "
            f"(incident_report_path={state.get('incident_report_path')!r})"
        )

    new_state = dict(state)
    new_state["bug_flow"] = {
        "active": True,
        "bug_report_path": bug_path,
        "root_cause": "prd-exception",
    }
    new_state["workflow_incident_active"] = True
    new_state["incident_report_path"] = incident_path
    new_state["current_stage"] = "workflow-incident-analysis"
    new_state["updated"] = now

    summary = (
        f"bug={bug_path} incident={incident_path} "
        "root_cause=prd-exception PRD exception triggered"
    )
    return IncidentStartOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=(
            "current_stage=workflow-incident-analysis; "
            "bug_flow.active=true root_cause=prd-exception"
        ),
        history_next="workflow-evolution fills INCIDENT body",
    )


def apply_incident_resolve(
    state: Mapping[str, Any],
    action: str,
    incident_path: str,
    *,
    now: str,
) -> IncidentResolveOutcome:
    """Exit the workflow-incident state per ``--action``.

    Per ``command-reference.md §12.1`` (continue), ``§12.2`` (abort),
    ``§12.3`` (reconstruct):

    Preconditions:
      * ``review_iteration <= 7`` (M2 entry guard);
      * ``workflow_incident_active == true``;
      * ``incident_path`` matches ``docs/incident/INCIDENT-NNN.md`` shape;
      * ``incident_path`` equals ``state['incident_report_path']`` (refuse
        to close the wrong incident);
      * ``action`` is one of ``{continue, abort, reconstruct}``.

    Note: this function does **not** require ``project_state == "active"``
    because abort/reconstruct legitimately mutates ``project_state`` from
    ``active`` to a terminal value; gating on workflow_incident_active is
    sufficient and matches the §12.2 / §12.3 spec.

    Mutation by action:
      * **continue** (§12.1 v0.6 round 2 H3): clears workflow-incident
        state, clears bug_flow, resets ``current_stage`` to ``testing``
        with ``sub_state="review-passed"`` and ``review_iteration=0``.
        BUG-NNN.md frontmatter (`root_cause: prd-exception`) is left
        intact for historical record; the CLI does not mutate the BUG
        file. New BUGs (if any) follow normal bug-triage flow.
      * **abort** (§12.2 v0.6 F11): terminal — sets ``project_state=aborted``,
        ``release_state=closed``, ``release_close_reason="incident-abort"``,
        ``current_stage=null``, ``sub_state=null``, ``review_iteration=0``,
        clears all bug_flow fields and workflow-incident state.
      * **reconstruct** (§12.3 v0.6 F11): terminal — same shape as abort
        but ``project_state=reconstructing`` and
        ``release_close_reason="incident-reconstruct"``.

    The CLI enforces INCIDENT ``resolution_action == action`` and
    INCIDENT ``status == "review-passed"`` plus the M6 double-safety
    ``validate.py file`` re-check before invoking this function.
    """

    _validate_timestamp(now, field="now")
    _validate_review_iteration_value(state.get("review_iteration", 0))
    _validate_incident_path_shape(incident_path)
    if action not in _INCIDENT_RESOLVE_ACTIONS:
        raise ProgressStateError(
            f"incident-resolve action must be one of "
            f"{sorted(_INCIDENT_RESOLVE_ACTIONS)}, got {action!r}"
        )

    if not state.get("workflow_incident_active"):
        raise ProgressStateError(
            "incident-resolve requires workflow_incident_active=true; "
            "no incident is currently open"
        )

    active_incident = state.get("incident_report_path")
    if active_incident != incident_path:
        raise ProgressStateError(
            f"incident-resolve incident path {incident_path!r} does not "
            f"match active incident_report_path {active_incident!r}; "
            "refuse to resolve a different incident"
        )

    new_state = dict(state)
    new_state["workflow_incident_active"] = False
    new_state["incident_report_path"] = None
    new_state["updated"] = now

    if action == "continue":
        new_state["bug_flow"] = {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        }
        new_state["current_stage"] = "testing"
        new_state["sub_state"] = "review-passed"
        new_state["review_iteration"] = 0
        history_result = (
            "current_stage=testing sub_state=review-passed; "
            "bug_flow cleared (BUG report root_cause=prd-exception preserved on disk)"
        )
        history_next = "testing-write retest (or new BUG via bug-triage)"
        is_terminal = False
    else:
        # abort / reconstruct share the same cleanup shape; only the
        # project_state value and release_close_reason differ.
        if action == "abort":
            terminal_project_state = "aborted"
            terminal_close_reason = "incident-abort"
        else:  # reconstruct
            terminal_project_state = "reconstructing"
            terminal_close_reason = "incident-reconstruct"
        new_state["project_state"] = terminal_project_state
        new_state["release_state"] = "closed"
        new_state["release_close_reason"] = terminal_close_reason
        new_state["current_stage"] = None
        new_state["sub_state"] = None
        new_state["review_iteration"] = 0
        new_state["bug_flow"] = {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        }
        history_result = (
            f"project_state={terminal_project_state} "
            f"release_state=closed close_reason={terminal_close_reason}; "
            "current_stage cleared (terminal)"
        )
        history_next = (
            "no further progress.py mutation accepted; "
            "start fresh project / release in a new directory"
            if action == "reconstruct"
            else "no further progress.py mutation accepted"
        )
        is_terminal = True

    summary = (
        f"action={action} incident={incident_path} Incident resolved"
    )
    return IncidentResolveOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=history_result,
        history_next=history_next,
        is_terminal=is_terminal,
    )


# ---------- Phase 6.4: stage advance (P6 matrix forward path) ----------


@dataclass(frozen=True)
class AdvanceOutcome:
    """Outcome of ``progress.py update --advance``.

    The CLI is the gatekeeper for P6 dimensions A (artifact existence),
    B (validate.py file), and E (verification artifact status). This
    state-machine function only enforces dimensions C / D (review or
    human gate via sub_state) plus structural state-machine legality:
    next_stage exists, project active, M2 review-iteration cap, and
    Stage 4 surrogate (all task_states verified).

    Replay re-derives the post-advance state from canonical history
    summary tokens (``from=<old> to=<new> Stage advance``) and uses the
    same function on the forward path, so forward and replay converge
    without re-reading artifact files (replay-skips-artifacts invariant
    inherited from Phase 5.3).
    """

    new_state: dict
    history_summary: str
    history_result: str | None
    history_next: str | None


def apply_update_advance(
    state: Mapping[str, Any],
    *,
    now: str,
) -> AdvanceOutcome:
    """Advance ``current_stage`` to ``NEXT_STAGE[current_stage]``.

    Per ``command-reference.md §2.2``: explicit stage advance after the
    current stage's P6 matrix passes. Stage 4 special case: instead of
    ``sub_state==review-passed``, the precondition is "all task states
    are ``verified``" (per-task review/verify already gated each
    Stage-4 transition).

    Preconditions enforced here (state-machine legal; CLI runs A/B/E):
      * ``project_state == "active"`` (terminal projects can't advance);
      * ``review_iteration <= 7`` (M2 entry guard);
      * no active workflow incident (must resolve before advancing);
      * ``current_stage`` is in :data:`NEXT_STAGE` (refuses advance from
        ``project-retrospective``: callers must use ``release-close``);
      * for gated stages (PRD / SRS / Architecture):
        ``sub_state == "approved"`` (i.e. ``human-confirmed`` already
        fired);
      * for ``development``: every value of
        ``development_state.task_states`` is ``"verified"``;
      * for non-gated stages other than ``development``:
        ``sub_state == "review-passed"``.

    Mutation:
      * ``current_stage`` → ``NEXT_STAGE[current_stage]``;
      * ``sub_state`` → ``"write"``;
      * ``review_iteration`` → ``0``;
      * ``updated`` → ``now``.

    Phase 6.4 deliberately does NOT mutate the ``artifacts:`` dict on
    advance. Per-stage mutable artifact entries remain entirely the
    responsibility of stage write skills (and ``release-start``);
    P6 derivation goes through
    :func:`skills._shared.dev_workflow.artifacts.get_required_artifacts`
    which does not depend on ``progress.md.artifacts``.
    """

    _validate_timestamp(now, field="now")
    _validate_active_project(state, "update --advance")
    _validate_review_iteration_value(state.get("review_iteration", 0))

    if state.get("workflow_incident_active"):
        raise ProgressStateError(
            "update --advance refuses while workflow_incident_active=true; "
            "resolve the incident first via incident-resolve"
        )

    current_stage = state.get("current_stage")
    if current_stage not in NEXT_STAGE:
        raise ProgressStateError(
            f"update --advance: current_stage={current_stage!r} has no next "
            f"stage. Stage 7 (project-retrospective) ends a release via "
            "release-close, not --advance"
        )
    next_stage = NEXT_STAGE[current_stage]

    sub_state = state.get("sub_state")
    if current_stage in GATED_STAGES:
        # PRD / SRS / Architecture must have human-confirmed already fired
        # (apply_update_event flips sub_state from review-passed to approved).
        if sub_state != "approved":
            raise ProgressStateError(
                f"update --advance from gated stage {current_stage!r} requires "
                f"sub_state='approved' (after human-confirmed), got {sub_state!r}"
            )
    elif current_stage == "development":
        # Stage 4 surrogate: review-pass / verify gates ran per-task; the
        # stage is "done" when every task_state is verified. apply does
        # not enforce that breakdown.total_tasks matches len(task_states)
        # — that's the CLI's E-dimension responsibility (or Phase 6.4
        # validate.py consistency).
        raw_dev = state.get("development_state") or {}
        task_states = raw_dev.get("task_states") or {}
        if not task_states:
            raise ProgressStateError(
                "update --advance from development requires at least one "
                "registered task; development_state.task_states is empty"
            )
        non_verified = sorted(
            tid for tid, status in task_states.items() if status != "verified"
        )
        if non_verified:
            raise ProgressStateError(
                "update --advance from development requires every task "
                f"verified; not yet verified: {non_verified}"
            )
    else:
        # testing / delivery — sub_state==review-passed (review pass
        # already fired). For testing, also forbid advance while a Bug
        # Flow is active (must close via bug-close first).
        if sub_state != "review-passed":
            raise ProgressStateError(
                f"update --advance from {current_stage!r} requires "
                f"sub_state='review-passed', got {sub_state!r}"
            )
        if current_stage == "testing":
            bug_flow = state.get("bug_flow") or {}
            if bug_flow.get("active"):
                raise ProgressStateError(
                    "update --advance from testing refuses while "
                    "bug_flow.active=true; close the active Bug Flow via "
                    "bug-close (after retest pass) first"
                )

    new_state = dict(state)
    new_state["current_stage"] = next_stage
    new_state["sub_state"] = "write"
    new_state["review_iteration"] = 0
    new_state["updated"] = now

    summary = f"from={current_stage} to={next_stage} Stage advance"
    return AdvanceOutcome(
        new_state=new_state,
        history_summary=summary,
        history_result=f"current_stage={next_stage} sub_state=write iteration=0",
        history_next=f"{next_stage}-write",
    )

