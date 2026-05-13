"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_release_close."""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    ProgressStateError,
    ReleaseCloseOutcome,
    apply_release_close,
)


_NOW = "2026-09-01T18:00:00Z"


def _stage_7_state(
    *,
    release: str = "0.1",
    sub_state: str = "review-passed",
    current_stage: str = "project-retrospective",
    release_state: str = "active",
    project_state: str = "active",
    review_iteration: int = 0,
    previous_releases=None,
) -> dict:
    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": release,
        "release_state": release_state,
        "release_close_reason": None,
        "previous_releases": list(previous_releases or []),
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": current_stage,
        "sub_state": sub_state,
        "review_iteration": review_iteration,
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
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-08-31T17:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_release_close_marks_closed_with_reason(self):
        outcome = apply_release_close(_stage_7_state(), now=_NOW)
        self.assertIsInstance(outcome, ReleaseCloseOutcome)
        self.assertEqual(outcome.new_state["release_state"], "closed")
        self.assertEqual(
            outcome.new_state["release_close_reason"], "stage-7-completed"
        )
        self.assertEqual(outcome.new_state["previous_releases"], ["0.1"])
        self.assertEqual(outcome.new_state["updated"], _NOW)
        self.assertIn("release 0.1 closed", outcome.history_summary)

    def test_release_close_appends_to_existing_previous_releases(self):
        outcome = apply_release_close(
            _stage_7_state(release="0.4", previous_releases=["0.1", "0.2", "0.3"]),
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["previous_releases"], ["0.1", "0.2", "0.3", "0.4"]
        )

    def test_release_close_preserves_other_fields(self):
        state = _stage_7_state()
        state["unresolved_bugs"] = []  # explicitly empty
        state["scenario"] = "S3"  # not modified by release-close
        outcome = apply_release_close(state, now=_NOW)
        self.assertEqual(outcome.new_state["scenario"], "S3")
        self.assertEqual(
            outcome.new_state["release"], "0.1",
        )
        self.assertEqual(
            outcome.new_state["current_stage"], "project-retrospective",
        )
        self.assertEqual(outcome.new_state["sub_state"], "review-passed")


class RejectionTests(unittest.TestCase):
    def test_release_state_not_active_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_close(
                _stage_7_state(release_state="closed"), now=_NOW,
            )
        self.assertIn("release_state", str(cm.exception))

    def test_current_stage_not_retrospective_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_close(
                _stage_7_state(current_stage="delivery"), now=_NOW,
            )
        self.assertIn("project-retrospective", str(cm.exception))

    def test_sub_state_not_review_passed_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_close(
                _stage_7_state(sub_state="in-review"), now=_NOW,
            )
        self.assertIn("review-passed", str(cm.exception))

    def test_aborted_project_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_close(
                _stage_7_state(project_state="aborted"), now=_NOW,
            )

    def test_iter_over_limit_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_close(
                _stage_7_state(review_iteration=8), now=_NOW,
            )
        self.assertIn("review_iteration", str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_release_already_in_previous_releases_rejected(self):
        # Out-of-band tampering: someone forged previous_releases to
        # already contain the current release.
        state = _stage_7_state(release="0.1", previous_releases=["0.1"])
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_close(state, now=_NOW)
        self.assertIn("already appears in previous_releases", str(cm.exception))

    def test_invalid_release_format_rejected(self):
        state = _stage_7_state()
        state["release"] = "not-a-version"
        with self.assertRaises(ProgressStateError):
            apply_release_close(state, now=_NOW)

    def test_invalid_now_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_close(_stage_7_state(), now="2026-09-01")


class FieldShapeTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_release_close(_stage_7_state(), now=_NOW)
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]

    def test_history_fields_populated(self):
        outcome = apply_release_close(
            _stage_7_state(release="0.2", previous_releases=["0.1"]), now=_NOW,
        )
        self.assertIsNotNone(outcome.history_result)
        self.assertIn("0.1", outcome.history_result)
        self.assertIn("0.2", outcome.history_result)
        self.assertIsNotNone(outcome.history_next)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
