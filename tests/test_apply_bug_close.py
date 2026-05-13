"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_bug_close."""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    BugCloseOutcome,
    ProgressStateError,
    apply_bug_close,
)


_NOW = "2026-09-02T16:00:00Z"


def _bug_active_state(
    *,
    current_stage: str = "testing",
    sub_state: str = "review-passed",
    project_state: str = "active",
    review_iteration: int = 0,
    bug_flow_active: bool = True,
    root_cause: str | None = "development",
) -> dict:
    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": "0.1",
        "release_state": "active",
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
            "root_cause": root_cause if bug_flow_active else None,
        },
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "created": "2026-08-01T10:00:00Z",
        "updated": "2026-09-01T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_bug_close_clears_bug_flow(self):
        outcome = apply_bug_close(_bug_active_state(), now=_NOW)
        self.assertIsInstance(outcome, BugCloseOutcome)
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )

    def test_current_stage_stays_testing(self):
        outcome = apply_bug_close(_bug_active_state(), now=_NOW)
        self.assertEqual(outcome.new_state["current_stage"], "testing")

    def test_sub_state_unchanged(self):
        # Phase 6.1: bug-close does NOT touch sub_state; the caller
        # subsequently invokes update --advance to step out of Stage 5.
        outcome = apply_bug_close(
            _bug_active_state(sub_state="review-passed"), now=_NOW,
        )
        self.assertEqual(outcome.new_state["sub_state"], "review-passed")

    def test_history_records_closed_bug_path(self):
        outcome = apply_bug_close(_bug_active_state(), now=_NOW)
        self.assertIn("docs/bug/BUG-099.md", outcome.history_result)
        self.assertIn("development", outcome.history_result)
        self.assertEqual(
            outcome.history_summary, "Bug Flow exited (retest passed)"
        )

    def test_updated_field_set_to_now(self):
        outcome = apply_bug_close(_bug_active_state(), now=_NOW)
        self.assertEqual(outcome.new_state["updated"], _NOW)


class RejectionTests(unittest.TestCase):
    def test_no_active_bug_flow_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_close(
                _bug_active_state(bug_flow_active=False), now=_NOW,
            )
        self.assertIn("not active", str(cm.exception))

    def test_non_testing_stage_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_close(
                _bug_active_state(current_stage="development"), now=_NOW,
            )
        self.assertIn("testing", str(cm.exception))

    def test_aborted_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_close(
                _bug_active_state(project_state="aborted"), now=_NOW,
            )

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_close(
                _bug_active_state(review_iteration=8), now=_NOW,
            )

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_close(_bug_active_state(), now="2026-09-02")


class ContractTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_bug_close(_bug_active_state(), now=_NOW)
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
