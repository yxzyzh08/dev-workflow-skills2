"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_update_task.

These tests are pure (no CLI invocation, no progress_lock). They forge
the in-memory progress state directly and write artifact fixtures into a
temporary directory. The CLI-side M1 replay-consistency check is exercised
in test_progress_update_task.py; here we focus on the state machine plus
per-status artifact preconditions.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from skills._shared.dev_workflow.progress_artifacts import ProgressArtifactError
from skills._shared.dev_workflow.progress_state import (
    ProgressStateError,
    TASK_STATES,
    TaskOutcome,
    apply_update_task,
)


_NOW = "2026-05-15T12:00:00Z"


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_doc(root: Path, rel: str, fm: dict, body: str = "Body.\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{_emit_yaml(fm)}\n---\n{body}", encoding="utf-8")
    return p


def _base_fm(doc_type: str, **extra) -> dict:
    fm = {
        "title": f"{doc_type} doc",
        "type": doc_type,
        "status": "draft",
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-05-15T10:00:00Z",
        "owner": "claude-opus-4-7/development-write",
    }
    fm.update(extra)
    return fm


def _make_breakdown(root: Path, *, release: str = "0.1", tasks=("T1",)) -> None:
    body = "# Tasks\n\n" + "\n".join(f"- {t} — task" for t in tasks) + "\n"
    _write_doc(
        root,
        f"docs/release{release}/development/breakdown.md",
        _base_fm("task-breakdown", release=release, total_tasks=len(tasks)),
        body=body,
    )


def _make_detailed_design(
    root: Path, *, release: str = "0.1", task_id: str = "T1"
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/detailed_design.md",
        _base_fm("detailed-design", release=release, task_id=task_id),
    )


def _make_test_review_report(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    review_status: str = "pending",
    blocking: int = 0,
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/test_review_report.md",
        _base_fm(
            "test-review-report",
            release=release,
            task_id=task_id,
            findings_count=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            review_status=review_status,
            blocking_findings_count=blocking,
            max_severity="low",
        ),
    )


def _make_code_review_report(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    review_status: str = "pending",
    blocking: int = 0,
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/code_review_report.md",
        _base_fm(
            "code-review-report",
            release=release,
            task_id=task_id,
            findings_count=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            review_status=review_status,
            blocking_findings_count=blocking,
            max_severity="low",
        ),
    )


def _make_verification_result(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    verification_status: str = "pass",
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/verification_result.md",
        _base_fm(
            "verification-result",
            release=release,
            task_id=task_id,
            verification_status=verification_status,
        ),
    )


def _dev_state(
    *,
    release: str = "0.1",
    task_states: dict | None = None,
    project_state: str = "active",
    current_stage: str = "development",
) -> dict:
    """Forge an in-memory progress state at Stage 4 development."""

    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": release,
        "release_state": "active",
        "release_close_reason": None,
        "previous_releases": [],
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": current_stage,
        "sub_state": "write",
        "review_iteration": 0,
        "artifacts": {
            "prd": "docs/prd/prd.md",
            "architecture": "docs/architecture/architecture.md",
            "srs": f"docs/release{release}/srs/srs.md",
            "acceptance_plan": f"docs/release{release}/srs/acceptance_plan.md",
            "integration_plan": None,
            "architecture_delta": None,
        },
        "bug_flow": {"active": False, "bug_report_path": None, "root_cause": None},
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "development_state": {"task_states": dict(task_states or {})},
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-05-15T10:00:00Z",
    }


class _BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()


# ---------- planning-done ----------


class PlanningDoneTests(_BaseTest):
    def test_first_time_planning_done_succeeds(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        outcome = apply_update_task(
            _dev_state(),
            "T1",
            "planning-done",
            now=_NOW,
            root=self.root,
        )
        self.assertIsInstance(outcome, TaskOutcome)
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "planning-done",
        )
        self.assertEqual(outcome.new_state["updated"], _NOW)
        self.assertIn("task=T1", outcome.history_summary)
        self.assertIn("planning-done", outcome.history_summary)

    def test_idempotent_planning_done_retry_marks_summary(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "planning-done"}),
            "T1",
            "planning-done",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "planning-done",
        )
        self.assertIn("idempotent retry", outcome.history_summary)

    def test_planning_done_rejected_when_breakdown_missing(self):
        _make_detailed_design(self.root, task_id="T1")
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("missing required task-breakdown", str(cm.exception))

    def test_planning_done_rejected_when_breakdown_does_not_declare_task(self):
        _make_breakdown(self.root, tasks=("T2",))
        _make_detailed_design(self.root, task_id="T1")
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("does not declare", str(cm.exception))
        self.assertIn("T1", str(cm.exception))

    def test_planning_done_rejected_when_detailed_design_missing(self):
        _make_breakdown(self.root, tasks=("T1",))
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("missing required detailed-design", str(cm.exception))

    def test_planning_done_rejected_when_detailed_design_task_id_mismatches(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T2")
        # detailed_design path is per-task, so we need to write under T1 with
        # a wrong task_id to trip the cross-check.
        _write_doc(
            self.root,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
            _base_fm("detailed-design", release="0.1", task_id="T9"),
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("task_id", str(cm.exception))


# ---------- transitional states (no artifact precondition) ----------


class TransitionalStatesTests(_BaseTest):
    def test_planning_done_to_test_writing(self):
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "planning-done"}),
            "T1",
            "test-writing",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-writing",
        )

    def test_test_revising_to_test_review_requires_skeleton(self):
        # The transition itself is allowed, but Phase 5.3 enforces the
        # skeleton precondition (review_status=pending) on test-review.
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "test-revising"}),
                "T1",
                "test-review",
                now=_NOW,
                root=self.root,
            )

    def test_test_done_to_code_writing(self):
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "test-done"}),
            "T1",
            "code-writing",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-writing",
        )

    def test_code_review_passed_to_verifying(self):
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "code-review-passed"}),
            "T1",
            "verifying",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "verifying",
        )


# ---------- review-bearing states ----------


class TestReviewSkeletonTests(_BaseTest):
    def test_test_writing_to_test_review_requires_pending_skeleton(self):
        _make_test_review_report(self.root, review_status="pending")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "test-writing"}),
            "T1",
            "test-review",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-review",
        )

    def test_test_review_rejected_when_review_status_not_pending(self):
        _make_test_review_report(self.root, review_status="pass")
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "test-writing"}),
                "T1",
                "test-review",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("review_status must be 'pending'", str(cm.exception))


class TestDoneTests(_BaseTest):
    def test_test_review_to_test_done_requires_pass_and_zero_blocking(self):
        _make_test_review_report(
            self.root, review_status="pass", blocking=0,
        )
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "test-review"}),
            "T1",
            "test-done",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-done",
        )

    def test_test_done_rejected_when_review_status_pending(self):
        _make_test_review_report(self.root, review_status="pending")
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "test-review"}),
                "T1",
                "test-done",
                now=_NOW,
                root=self.root,
            )

    def test_test_done_rejected_when_review_status_fail(self):
        _make_test_review_report(self.root, review_status="fail")
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "test-review"}),
                "T1",
                "test-done",
                now=_NOW,
                root=self.root,
            )

    def test_test_done_rejected_when_blocking_nonzero(self):
        # Construct a doc-guardian-illegal-but-frontmatter-present case:
        # review_status=pass with blocking=1. doc-guardian would reject
        # this earlier (Class 4 invariant); progress.py should also reject
        # the transition because the invariant holds.
        _make_test_review_report(
            self.root, review_status="pass", blocking=1,
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "test-review"}),
                "T1",
                "test-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("blocking_findings_count", str(cm.exception))


class CodeReviewTests(_BaseTest):
    def test_code_writing_to_code_review_requires_pending(self):
        _make_code_review_report(self.root, review_status="pending")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "code-writing"}),
            "T1",
            "code-review",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-review",
        )

    def test_code_review_passed_requires_pass_and_zero_blocking(self):
        _make_code_review_report(self.root, review_status="pass", blocking=0)
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "code-review"}),
            "T1",
            "code-review-passed",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-review-passed",
        )

    def test_code_review_passed_rejected_when_blocking_nonzero(self):
        _make_code_review_report(self.root, review_status="pass", blocking=2)
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "code-review"}),
                "T1",
                "code-review-passed",
                now=_NOW,
                root=self.root,
            )


class VerifiedTests(_BaseTest):
    def test_verifying_to_verified_requires_verification_pass(self):
        _make_verification_result(self.root, verification_status="pass")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "verifying"}),
            "T1",
            "verified",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "verified",
        )

    def test_verified_rejected_when_verification_fail(self):
        _make_verification_result(self.root, verification_status="fail")
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "verifying"}),
                "T1",
                "verified",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("verification_status must be 'pass'", str(cm.exception))

    def test_verified_rejected_when_verification_partial(self):
        _make_verification_result(self.root, verification_status="partial")
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "verifying"}),
                "T1",
                "verified",
                now=_NOW,
                root=self.root,
            )


# ---------- protected transitions (deferred to Phase 6) ----------


class ProtectedTransitionsRejectedTests(_BaseTest):
    """Gap-4 protected transitions (active dev Bug Flow context required)
    must remain rejected through ``apply_update_task`` even after Phase
    6.1 accepts Gap-3. The Gap-3 path itself moved to
    ``tests/test_apply_update_task_gap3.py``.
    """

    def test_verified_to_code_revising_rejected_in_phase_5_3(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "verified"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("protected", str(cm.exception))

    def test_verified_to_test_revising_rejected_in_phase_5_3(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(task_states={"T1": "verified"}),
                "T1",
                "test-revising",
                now=_NOW,
                root=self.root,
            )

    def test_code_review_passed_to_code_revising_rejected_in_phase_5_3(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(task_states={"T1": "code-review-passed"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )


# ---------- generic preconditions ----------


class GenericPreconditionTests(_BaseTest):
    def test_invalid_task_id_format_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(),
                "task1",  # lowercase t — illegal
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("task_id", str(cm.exception))

    def test_invalid_status_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(),
                "T1",
                "no-such-state",
                now=_NOW,
                root=self.root,
            )

    def test_non_development_stage_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(current_stage="testing"),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("current_stage", str(cm.exception))
        self.assertIn("development", str(cm.exception))

    def test_aborted_project_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(project_state="aborted"),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )

    def test_invalid_now_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(),
                "T1",
                "planning-done",
                now="2026-05-15",
                root=self.root,
            )

    def test_illegal_normal_transition_rejected(self):
        # planning-done -> test-review is not a normal transition.
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "planning-done"}),
                "T1",
                "test-review",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("not a", str(cm.exception))
        self.assertIn("legal normal transition", str(cm.exception))

    def test_first_time_test_writing_rejected(self):
        # None -> test-writing is illegal (only None -> planning-done is the
        # registration transition).
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(),
                "T1",
                "test-writing",
                now=_NOW,
                root=self.root,
            )

    def test_other_task_states_preserved(self):
        # Mutating T1 must not touch task_states for sibling tasks.
        _make_breakdown(self.root, tasks=("T1", "T2"))
        _make_detailed_design(self.root, task_id="T1")
        outcome = apply_update_task(
            _dev_state(task_states={"T2": "verified"}),
            "T1",
            "planning-done",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"],
            {"T1": "planning-done", "T2": "verified"},
        )


class FieldPreservationTests(_BaseTest):
    def test_other_top_level_fields_preserved(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        state = _dev_state()
        state["unresolved_bugs"] = ["docs/bug/BUG-001.md"]
        outcome = apply_update_task(
            state, "T1", "planning-done",
            now=_NOW, root=self.root,
        )
        self.assertEqual(
            outcome.new_state["unresolved_bugs"], ["docs/bug/BUG-001.md"]
        )
        self.assertEqual(
            outcome.new_state["release"], state["release"]
        )
        self.assertEqual(
            outcome.new_state["created"], state["created"]
        )
        self.assertEqual(outcome.new_state["sub_state"], state["sub_state"])

    def test_outcome_is_frozen(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        outcome = apply_update_task(
            _dev_state(), "T1", "planning-done",
            now=_NOW, root=self.root,
        )
        self.assertIsInstance(outcome, TaskOutcome)
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]


class IterationOverLimitTaskTests(_BaseTest):
    """Phase 5.3 round 2 review M1: apply_update_task must inherit the
    Phase 5.2 round 2 M2 invariant — a tampered/migrated progress.md
    whose review_iteration is already over the spec cap (0-7) cannot be
    a base for any task-state mutation, even though update --task does
    not directly mutate review_iteration."""

    def _state_with_iter(self, *, iteration: int, task_states=None) -> dict:
        s = _dev_state(task_states=task_states)
        s["review_iteration"] = iteration
        return s

    def test_planning_done_rejects_iter_eight(self):
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                self._state_with_iter(iteration=8),
                "T1",
                "planning-done",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("review_iteration", str(cm.exception))
        self.assertIn("8", str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_test_writing_rejects_iter_eight(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                self._state_with_iter(
                    iteration=8, task_states={"T1": "planning-done"},
                ),
                "T1",
                "test-writing",
                now=_NOW,
                root=self.root,
            )

    def test_verified_rejects_iter_eight(self):
        _make_verification_result(self.root, verification_status="pass")
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                self._state_with_iter(
                    iteration=8, task_states={"T1": "verifying"},
                ),
                "T1",
                "verified",
                now=_NOW,
                root=self.root,
            )

    def test_iter_seven_still_allowed(self):
        # Cap is inclusive; 7 must still pass.
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")
        outcome = apply_update_task(
            self._state_with_iter(iteration=7),
            "T1",
            "planning-done",
            now=_NOW,
            root=self.root,
        )
        # review_iteration is preserved (update --task does not touch it).
        self.assertEqual(outcome.new_state["review_iteration"], 7)


class RevisionLoopTransitionsTests(_BaseTest):
    """Phase 5.3 round 2 review L2: explicitly cover the revision-loop
    transitions that the original happy-path cycle did not exercise.
    Previously the suite only walked the pass branches."""

    def test_test_review_to_test_revising(self):
        # Revising path is transitional — no artifact precondition.
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "test-review"}),
            "T1",
            "test-revising",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-revising",
        )

    def test_test_revising_back_to_test_review_with_skeleton(self):
        # After test-revising, going back to test-review requires a
        # fresh pending skeleton.
        _make_test_review_report(self.root, review_status="pending")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "test-revising"}),
            "T1",
            "test-review",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-review",
        )

    def test_code_review_to_code_revising(self):
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "code-review"}),
            "T1",
            "code-revising",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-revising",
        )

    def test_code_revising_back_to_code_review_with_skeleton(self):
        _make_code_review_report(self.root, review_status="pending")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "code-revising"}),
            "T1",
            "code-review",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-review",
        )

    def test_code_revising_back_to_code_review_rejects_non_pending(self):
        # If the report has already been promoted to pass, transitioning
        # back to code-review must reject (the report should be reset
        # to pending after revising).
        _make_code_review_report(self.root, review_status="pass")
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "code-revising"}),
                "T1",
                "code-review",
                now=_NOW,
                root=self.root,
            )


class TaskStatesContractTests(_BaseTest):
    def test_task_states_set_matches_spec(self):
        # Defends against accidental drift; the schema cares about exactly
        # these 11 normal task states.
        self.assertEqual(
            TASK_STATES,
            {
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
            },
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
