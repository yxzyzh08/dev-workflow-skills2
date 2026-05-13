"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_update_advance.

Phase 6.4: stage advance. CLI side runs P6 dimensions A (artifact
existence), B (validate.py file), and E (verification status). These
unit tests exercise the state-machine legality only — gated vs
non-gated sub_state preconditions, Stage 4 task surrogate, terminal /
incident / iteration guards, and the next-stage map.
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    AdvanceOutcome,
    NEXT_STAGE,
    ProgressStateError,
    apply_update_advance,
)


_NOW = "2026-11-01T15:00:00Z"


def _state(
    *,
    current_stage: str,
    sub_state: str = "review-passed",
    project_state: str = "active",
    release_state: str = "active",
    review_iteration: int = 0,
    bug_flow_active: bool = False,
    workflow_incident_active: bool = False,
    task_states: dict | None = None,
) -> dict:
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
            "active": bug_flow_active,
            "bug_report_path": "docs/bug/BUG-099.md" if bug_flow_active else None,
            "root_cause": "srs" if bug_flow_active else None,
        },
        "workflow_incident_active": workflow_incident_active,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "development_state": (
            {"task_states": dict(task_states)} if task_states is not None else None
        ),
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-10-31T10:00:00Z",
    }


class GatedStageHappyTests(unittest.TestCase):
    """PRD / SRS / Architecture: advance precondition is sub_state=='approved'
    (human-confirmed already fired), not review-passed."""

    def test_advance_prd_to_srs(self):
        outcome = apply_update_advance(
            _state(current_stage="prd-inception", sub_state="approved"),
            now=_NOW,
        )
        self.assertIsInstance(outcome, AdvanceOutcome)
        self.assertEqual(outcome.new_state["current_stage"], "srs-specification")
        self.assertEqual(outcome.new_state["sub_state"], "write")
        self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_advance_srs_to_architecture(self):
        outcome = apply_update_advance(
            _state(current_stage="srs-specification", sub_state="approved"),
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "architecture-design")

    def test_advance_architecture_to_development(self):
        outcome = apply_update_advance(
            _state(current_stage="architecture-design", sub_state="approved"),
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "development")

    def test_gated_stage_rejects_review_passed(self):
        # Non-gated event sub_state — rejects from gated stages.
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(current_stage="prd-inception", sub_state="review-passed"),
                now=_NOW,
            )
        self.assertIn("approved", str(cm.exception))


class DevelopmentStageHappyTests(unittest.TestCase):
    def test_advance_development_to_testing_with_all_tasks_verified(self):
        outcome = apply_update_advance(
            _state(
                current_stage="development",
                sub_state="write",  # ignored for development branch
                task_states={"T1": "verified", "T2": "verified", "T3": "verified"},
            ),
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "testing")

    def test_development_rejects_when_task_not_verified(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(
                    current_stage="development",
                    task_states={"T1": "verified", "T2": "code-revising"},
                ),
                now=_NOW,
            )
        self.assertIn("not yet verified", str(cm.exception))
        self.assertIn("T2", str(cm.exception))

    def test_development_rejects_with_no_tasks_registered(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(current_stage="development", task_states={}),
                now=_NOW,
            )
        self.assertIn("at least one", str(cm.exception))

    def test_development_rejects_with_missing_development_state(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(current_stage="development", task_states=None),
                now=_NOW,
            )


class NonGatedStageHappyTests(unittest.TestCase):
    """Stage 5 (testing) / Stage 6 (delivery): advance precondition is
    sub_state=='review-passed'."""

    def test_advance_testing_to_delivery(self):
        outcome = apply_update_advance(
            _state(current_stage="testing", sub_state="review-passed"),
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "delivery")

    def test_advance_delivery_to_retrospective(self):
        outcome = apply_update_advance(
            _state(current_stage="delivery", sub_state="review-passed"),
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["current_stage"], "project-retrospective",
        )

    def test_testing_rejects_with_active_bug_flow(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(
                    current_stage="testing",
                    sub_state="review-passed",
                    bug_flow_active=True,
                ),
                now=_NOW,
            )
        self.assertIn("bug_flow.active=true", str(cm.exception))
        self.assertIn("bug-close", str(cm.exception))

    def test_testing_rejects_wrong_substate(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(current_stage="testing", sub_state="in-review"),
                now=_NOW,
            )


class TerminalStageRejectionTests(unittest.TestCase):
    def test_advance_from_retrospective_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(current_stage="project-retrospective", sub_state="review-passed"),
                now=_NOW,
            )
        self.assertIn("release-close", str(cm.exception))


class GeneralRejectionTests(unittest.TestCase):
    def test_aborted_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(
                    current_stage="testing", project_state="aborted",
                    sub_state="review-passed",
                ),
                now=_NOW,
            )

    def test_reconstructing_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(
                    current_stage="testing", project_state="reconstructing",
                    sub_state="review-passed",
                ),
                now=_NOW,
            )

    def test_workflow_incident_active_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_advance(
                _state(
                    current_stage="testing",
                    sub_state="review-passed",
                    workflow_incident_active=True,
                ),
                now=_NOW,
            )
        self.assertIn("incident-resolve", str(cm.exception))

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(
                    current_stage="testing",
                    sub_state="review-passed",
                    review_iteration=8,
                ),
                now=_NOW,
            )

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_update_advance(
                _state(current_stage="testing", sub_state="review-passed"),
                now="2026-11-01",
            )


class HistoryTokenTests(unittest.TestCase):
    def test_summary_contains_from_and_to_tokens(self):
        outcome = apply_update_advance(
            _state(current_stage="srs-specification", sub_state="approved"),
            now=_NOW,
        )
        # _kv_tokens-parseable.
        self.assertIn("from=srs-specification", outcome.history_summary)
        self.assertIn("to=architecture-design", outcome.history_summary)
        self.assertIn("Stage advance", outcome.history_summary)

    def test_history_result_lists_post_advance_state(self):
        outcome = apply_update_advance(
            _state(current_stage="testing", sub_state="review-passed"),
            now=_NOW,
        )
        self.assertIn("current_stage=delivery", outcome.history_result)
        self.assertIn("sub_state=write", outcome.history_result)
        self.assertIn("iteration=0", outcome.history_result)


class ContractTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_update_advance(
            _state(current_stage="testing", sub_state="review-passed"),
            now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]

    def test_next_stage_map_completeness(self):
        # Sanity check: the 6 advancing stages all have a next stage,
        # and project-retrospective intentionally does not.
        self.assertEqual(
            set(NEXT_STAGE.keys()),
            {
                "prd-inception",
                "srs-specification",
                "architecture-design",
                "development",
                "testing",
                "delivery",
            },
        )
        self.assertNotIn("project-retrospective", NEXT_STAGE)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
