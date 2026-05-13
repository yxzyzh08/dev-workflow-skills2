"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_bug_rework.

Phase 6.2 / Gap-5: re-route an active Bug Flow whose retest came back
fail/partial. The CLI computes ``rollback_decisions`` by reading the
BUG body; these unit tests pass the tuple directly to
``apply_bug_rework`` so they remain pure (no file I/O).
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    BugReworkOutcome,
    ProgressStateError,
    ROOT_CAUSES_FOR_BUG_START,
    apply_bug_rework,
    compute_dev_bug_rollback,
)


_NOW = "2026-09-15T15:00:00Z"
_ACTIVE_BUG = "docs/bug/BUG-050.md"


def _active_bug_flow_state(
    *,
    sub_state: str = "review-passed",
    current_stage: str = "testing",
    bug_path: str = _ACTIVE_BUG,
    root_cause: str = "srs",
    project_state: str = "active",
    release_state: str = "active",
    review_iteration: int = 0,
    task_states: dict | None = None,
) -> dict:
    """Build a state with active Bug Flow at testing/review-passed.

    This is the canonical pre-bug-rework starting state. ``bug-start``
    has already fired previously, the project routed to root-cause
    stage, the fix landed, retest ran, and the agent now wants to
    re-route after retest fail/partial.
    """

    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": "0.1",
        "release_state": release_state,
        "release_close_reason": None,
        "previous_releases": [],
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": current_stage,
        "sub_state": sub_state,
        "review_iteration": review_iteration,
        "artifacts": {
            "prd": "docs/prd/prd.md",
            "architecture": "docs/architecture/architecture.md",
            "srs": "docs/release0.1/srs/srs.md",
            "acceptance_plan": "docs/release0.1/srs/acceptance_plan.md",
            "integration_plan": None,
            "architecture_delta": None,
        },
        "bug_flow": {
            "active": True,
            "bug_report_path": bug_path,
            "root_cause": root_cause,
        },
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "development_state": (
            {"task_states": dict(task_states)} if task_states is not None else None
        ),
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-09-14T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_root_cause_srs_routes_back_to_srs_specification(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="srs"),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertIsInstance(outcome, BugReworkOutcome)
        self.assertEqual(outcome.new_state["current_stage"], "srs-specification")
        self.assertEqual(outcome.new_state["sub_state"], "write")
        self.assertEqual(outcome.new_state["review_iteration"], 0)
        # bug_flow stays active and unchanged.
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {
                "active": True,
                "bug_report_path": _ACTIVE_BUG,
                "root_cause": "srs",
            },
        )
        self.assertEqual(outcome.rollback_decisions, ())

    def test_root_cause_architecture_routes_back_to_architecture_design(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="architecture"),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "architecture-design")
        self.assertEqual(outcome.new_state["bug_flow"]["root_cause"], "architecture")

    def test_root_cause_development_without_rollback(self):
        # development root cause but caller passed empty rollback list
        # (ambiguous classification or no affected tasks). Mutation
        # still applies for current_stage / bug_flow stays unchanged.
        outcome = apply_bug_rework(
            _active_bug_flow_state(
                root_cause="development", task_states={"T1": "verified"},
            ),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "development")
        # T1 still verified — no rollback was supplied.
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"], {"T1": "verified"}
        )

    def test_history_summary_canonical_for_replay(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="srs"),
            _ACTIVE_BUG,
            now=_NOW,
        )
        # Replay handler reverses bug=, root_cause= tokens via _kv_tokens.
        self.assertIn(f"bug={_ACTIVE_BUG}", outcome.history_summary)
        self.assertIn("root_cause=srs", outcome.history_summary)
        # Distinct verb from bug-start so log inspection can grep events.
        self.assertIn("rerouted", outcome.history_summary)

    def test_review_iteration_resets_even_from_high_value(self):
        # An active retest re-route resets the review counter so the
        # caller's next review cycle starts fresh; if it inherited the
        # previous iteration it could trigger the M2 escalation guard
        # spuriously.
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="srs", review_iteration=5),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_bug_flow_path_and_root_cause_preserved(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(
                root_cause="architecture", bug_path="docs/bug/BUG-077.md",
            ),
            "docs/bug/BUG-077.md",
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["bug_flow"]["bug_report_path"],
            "docs/bug/BUG-077.md",
        )
        self.assertEqual(
            outcome.new_state["bug_flow"]["root_cause"], "architecture",
        )
        self.assertTrue(outcome.new_state["bug_flow"]["active"])


class Gap4DevRollbackTests(unittest.TestCase):
    def _dev_state(self, *, task_states):
        return _active_bug_flow_state(
            root_cause="development", task_states=task_states,
        )

    def test_verified_to_test_revising_for_test_classification(self):
        rollback = (
            ("T1", "verified", "test-revising", "test-only fix"),
        )
        outcome = apply_bug_rework(
            self._dev_state(task_states={"T1": "verified"}),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-revising",
        )
        self.assertEqual(outcome.rollback_decisions, rollback)

    def test_verified_to_code_revising_for_source_classification(self):
        rollback = (
            ("T1", "verified", "code-revising", "source fix"),
        )
        outcome = apply_bug_rework(
            self._dev_state(task_states={"T1": "verified"}),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-revising",
        )

    def test_code_review_passed_to_code_revising_for_source(self):
        rollback = (
            ("T2", "code-review-passed", "code-revising", "source fix"),
        )
        outcome = apply_bug_rework(
            self._dev_state(task_states={"T2": "code-review-passed"}),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T2"],
            "code-revising",
        )

    def test_multiple_rollbacks_applied_atomically(self):
        rollback = (
            ("T1", "verified", "code-revising", "source fix"),
            ("T3", "code-review-passed", "code-revising", "source fix"),
        )
        outcome = apply_bug_rework(
            self._dev_state(
                task_states={"T1": "verified", "T3": "code-review-passed"},
            ),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        new_task_states = outcome.new_state["development_state"]["task_states"]
        self.assertEqual(new_task_states["T1"], "code-revising")
        self.assertEqual(new_task_states["T3"], "code-revising")

    def test_rollback_summary_token_in_history(self):
        rollback = (
            ("T1", "verified", "code-revising", "source fix"),
        )
        outcome = apply_bug_rework(
            self._dev_state(task_states={"T1": "verified"}),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertIn("rollback=T1:verified->code-revising", outcome.history_summary)

    def test_rollback_with_non_dev_root_cause_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                _active_bug_flow_state(
                    root_cause="srs", task_states={"T1": "verified"},
                ),
                _ACTIVE_BUG,
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "test-revising", "test-only fix"),
                ),
            )
        self.assertIn("development", str(cm.exception))

    def test_rollback_with_non_protected_transition_rejected(self):
        # ``verified -> verifying`` is not in PROTECTED_TASK_TRANSITIONS.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                self._dev_state(task_states={"T1": "verified"}),
                _ACTIVE_BUG,
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "verifying", "weird"),
                ),
            )
        self.assertIn("Gap-4", str(cm.exception))

    def test_rollback_with_stale_old_status_rejected(self):
        # Caller said T1 was 'verified' but progress.md has 'code-writing'.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                self._dev_state(task_states={"T1": "code-writing"}),
                _ACTIVE_BUG,
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "code-revising", "source fix"),
                ),
            )
        self.assertIn("out-of-band", str(cm.exception))

    def test_rollback_with_malformed_task_id_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                self._dev_state(task_states={"T1": "verified"}),
                _ACTIVE_BUG,
                now=_NOW,
                rollback_decisions=(
                    ("not-a-task", "verified", "test-revising", "x"),
                ),
            )
        self.assertIn("T", str(cm.exception))


class RejectionTests(unittest.TestCase):
    def test_inactive_bug_flow_rejects(self):
        state = _active_bug_flow_state()
        state["bug_flow"] = {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        }
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(state, _ACTIVE_BUG, now=_NOW)
        self.assertIn("not active", str(cm.exception))

    def test_non_testing_stage_rejects(self):
        state = _active_bug_flow_state(current_stage="development")
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(state, _ACTIVE_BUG, now=_NOW)
        self.assertIn("testing", str(cm.exception))

    def test_non_review_passed_substate_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                _active_bug_flow_state(sub_state="in-review"),
                _ACTIVE_BUG,
                now=_NOW,
            )
        self.assertIn("review-passed", str(cm.exception))

    def test_bug_path_mismatch_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(
                _active_bug_flow_state(bug_path="docs/bug/BUG-050.md"),
                "docs/bug/BUG-051.md",
                now=_NOW,
            )
        self.assertIn("does not match", str(cm.exception))

    def test_aborted_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_rework(
                _active_bug_flow_state(project_state="aborted"),
                _ACTIVE_BUG,
                now=_NOW,
            )

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_rework(
                _active_bug_flow_state(review_iteration=8),
                _ACTIVE_BUG,
                now=_NOW,
            )

    def test_invalid_bug_path_shape_rejects(self):
        # bug_path arg must satisfy canonical shape regardless of what
        # bug_flow stores.
        state = _active_bug_flow_state(bug_path="/etc/passwd")
        with self.assertRaises(ProgressStateError):
            apply_bug_rework(state, "/etc/passwd", now=_NOW)

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_rework(
                _active_bug_flow_state(),
                _ACTIVE_BUG,
                now="2026-09-15",
            )

    def test_prd_exception_root_cause_in_bug_flow_rejects(self):
        # An out-of-band edit could leave bug_flow.root_cause at
        # 'prd-exception' (which incident-resolve owns). bug-rework must
        # refuse rather than try to map it through _ROOT_CAUSE_TO_STAGE.
        state = _active_bug_flow_state()
        state["bug_flow"]["root_cause"] = "prd-exception"
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_rework(state, _ACTIVE_BUG, now=_NOW)
        self.assertIn("prd-exception", str(cm.exception))


class ContractTests(unittest.TestCase):
    def test_root_causes_constant_shared_with_bug_start(self):
        self.assertEqual(
            ROOT_CAUSES_FOR_BUG_START,
            frozenset({"srs", "architecture", "development"}),
        )

    def test_outcome_is_frozen(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(),
            _ACTIVE_BUG,
            now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]


# ---------- Phase 6.2 review L1 mirror: planning-route note ----------


class PlanningRouteNoteTests(unittest.TestCase):
    """Mirror Phase 6.1 round 2 review L1: when ``root_cause == 'development'``
    AND the rollback list is empty, ``apply_bug_rework`` records a
    persistent planning-route note in ``history_result`` /
    ``history_next`` so a future agent reading only progress-history.md
    can see the documented requirement to invoke
    ``development-planning-write``."""

    def test_dev_root_cause_with_empty_rollback_records_planning_route(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(
                root_cause="development", task_states={"T1": "verified"},
            ),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=(),
        )
        self.assertIn("development-planning-write", outcome.history_result)
        self.assertIn("route=", outcome.history_result)
        self.assertIn("development-planning-write", outcome.history_next)

    def test_dev_root_cause_with_rollback_does_not_append_planning_route(self):
        rollback = (("T1", "verified", "test-revising", "test-only fix"),)
        outcome = apply_bug_rework(
            _active_bug_flow_state(
                root_cause="development", task_states={"T1": "verified"},
            ),
            _ACTIVE_BUG,
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertNotIn("development-planning-write", outcome.history_result)
        self.assertNotIn("development-planning-write", outcome.history_next)

    def test_srs_root_cause_does_not_get_planning_route(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="srs"),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertNotIn("planning-write", outcome.history_next)
        self.assertIn("srs-specification-write", outcome.history_next)

    def test_architecture_root_cause_does_not_get_planning_route(self):
        outcome = apply_bug_rework(
            _active_bug_flow_state(root_cause="architecture"),
            _ACTIVE_BUG,
            now=_NOW,
        )
        self.assertIn("architecture-design-write", outcome.history_next)
        self.assertNotIn("planning-write", outcome.history_next)


# ---------- compute_dev_bug_rollback shared helper ----------


class _FakeTriage:
    """Test-only stand-in for progress_artifacts.TriageAnalysis.

    We don't need to touch the real parser here; the helper only reads
    ``classification`` / ``affected_tasks`` / ``unable_to_localize``.
    """

    def __init__(
        self,
        *,
        affected_tasks=(),
        classification="ambiguous",
        unable_to_localize=False,
    ):
        self.affected_tasks = tuple(affected_tasks)
        self.classification = classification
        self.unable_to_localize = unable_to_localize


class ComputeDevBugRollbackTests(unittest.TestCase):
    """Shared helper used by both bug-start and bug-rework. Phase 6.2
    refactor moved this from progress.py to progress_state.py so the
    Gap-4 logic has exactly one implementation."""

    def _state_with(self, task_states):
        return {"development_state": {"task_states": dict(task_states)}}

    def test_test_classification_rolls_verified_to_test_revising(self):
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "verified", "T2": "test-done"}),
            _FakeTriage(affected_tasks=("T1", "T2"), classification="test"),
        )
        self.assertEqual(
            decisions,
            (("T1", "verified", "test-revising", "test-only fix"),),
        )

    def test_source_classification_handles_both_origins(self):
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "verified", "T2": "code-review-passed"}),
            _FakeTriage(affected_tasks=("T1", "T2"), classification="source"),
        )
        self.assertEqual(
            decisions,
            (
                ("T1", "verified", "code-revising", "source fix"),
                ("T2", "code-review-passed", "code-revising", "source fix"),
            ),
        )

    def test_ambiguous_returns_empty(self):
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "verified"}),
            _FakeTriage(affected_tasks=("T1",), classification="ambiguous"),
        )
        self.assertEqual(decisions, ())

    def test_unable_to_localize_returns_empty(self):
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "verified"}),
            _FakeTriage(
                affected_tasks=(), classification="test", unable_to_localize=True,
            ),
        )
        self.assertEqual(decisions, ())

    def test_unregistered_task_skipped(self):
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "verified"}),
            _FakeTriage(affected_tasks=("T2",), classification="test"),
        )
        self.assertEqual(decisions, ())

    def test_ineligible_state_skipped(self):
        # T1 is in test-done — neither verified nor code-review-passed,
        # so neither test-only nor source classification can roll it
        # back. Skip silently and let the planning-route note (emitted
        # by apply_bug_rework / apply_bug_start) cover the empty case.
        decisions = compute_dev_bug_rollback(
            self._state_with({"T1": "test-done"}),
            _FakeTriage(affected_tasks=("T1",), classification="test"),
        )
        self.assertEqual(decisions, ())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
