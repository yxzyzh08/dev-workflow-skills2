"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_bug_intake."""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    BugIntakeOutcome,
    ProgressStateError,
    apply_bug_intake,
)


_NOW = "2026-09-15T14:00:00Z"


def _closed_state(
    *,
    unresolved_bugs=None,
    project_state: str = "active",
    release_state: str = "closed",
    review_iteration: int = 0,
) -> dict:
    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": "0.1",
        "release_state": release_state,
        "release_close_reason": "stage-7-completed",
        "previous_releases": ["0.1"],
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": "project-retrospective",
        "sub_state": "review-passed",
        "review_iteration": review_iteration,
        "artifacts": {
            "prd": "docs/prd/prd.md",
            "architecture": "docs/architecture/architecture.md",
            "srs": "docs/release0.1/srs/srs.md",
            "acceptance_plan": "docs/release0.1/srs/acceptance_plan.md",
            "integration_plan": None,
            "architecture_delta": None,
        },
        "bug_flow": {"active": False, "bug_report_path": None, "root_cause": None},
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": list(unresolved_bugs or []),
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-09-14T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_first_intake_appends_to_unresolved_bugs(self):
        outcome = apply_bug_intake(
            _closed_state(), "docs/bug/BUG-001.md", now=_NOW,
        )
        self.assertIsInstance(outcome, BugIntakeOutcome)
        self.assertEqual(
            outcome.new_state["unresolved_bugs"], ["docs/bug/BUG-001.md"]
        )
        self.assertEqual(outcome.new_state["updated"], _NOW)
        self.assertIn("bug=docs/bug/BUG-001.md", outcome.history_summary)

    def test_subsequent_intake_appends_in_order(self):
        outcome = apply_bug_intake(
            _closed_state(unresolved_bugs=["docs/bug/BUG-001.md"]),
            "docs/bug/BUG-002.md",
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["unresolved_bugs"],
            ["docs/bug/BUG-001.md", "docs/bug/BUG-002.md"],
        )
        self.assertIn("count = 2", outcome.history_result)

    def test_other_fields_preserved(self):
        outcome = apply_bug_intake(
            _closed_state(), "docs/bug/BUG-001.md", now=_NOW,
        )
        self.assertEqual(outcome.new_state["release"], "0.1")
        self.assertEqual(outcome.new_state["release_state"], "closed")
        self.assertEqual(
            outcome.new_state["previous_releases"], ["0.1"],
        )

    def test_history_summary_canonical_for_replay(self):
        outcome = apply_bug_intake(
            _closed_state(), "docs/bug/BUG-042.md", now=_NOW,
        )
        # Replay extracts bug=<path> token from summary or result.
        joined = outcome.history_summary + " " + (outcome.history_result or "")
        self.assertIn("bug=docs/bug/BUG-042.md", joined)


class RejectionTests(unittest.TestCase):
    def test_release_state_active_rejected(self):
        # bug-intake is post-close only.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(release_state="active"),
                "docs/bug/BUG-001.md",
                now=_NOW,
            )
        self.assertIn("release_state", str(cm.exception))
        self.assertIn("closed", str(cm.exception))

    def test_aborted_project_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(project_state="aborted"),
                "docs/bug/BUG-001.md",
                now=_NOW,
            )

    def test_duplicate_path_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(unresolved_bugs=["docs/bug/BUG-001.md"]),
                "docs/bug/BUG-001.md",
                now=_NOW,
            )
        self.assertIn("duplicate", str(cm.exception))
        self.assertIn("BUG-001", str(cm.exception))

    def test_empty_path_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(_closed_state(), "", now=_NOW)

    def test_non_string_path_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(_closed_state(), None, now=_NOW)  # type: ignore[arg-type]

    def test_iter_over_limit_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(review_iteration=8),
                "docs/bug/BUG-001.md",
                now=_NOW,
            )

    def test_invalid_now_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(),
                "docs/bug/BUG-001.md",
                now="2026-09-15",
            )


class BugPathShapeTests(unittest.TestCase):
    """Phase 5.4 round 2 review M1: BUG paths in unresolved_bugs must be
    canonical project-relative ``docs/bug/BUG-NNN.md`` strings. Forward
    AND replay paths must reject malformed values so a corrupted
    progress.md / progress-history.md cannot feed release-start fan-out
    a path that escapes --root or points at a non-BUG file."""

    def test_absolute_path_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "/etc/passwd", now=_NOW,
            )
        self.assertIn("absolute", str(cm.exception))

    def test_windows_drive_path_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "C:/secret/BUG-001.md", now=_NOW,
            )
        self.assertIn("absolute", str(cm.exception))

    def test_traversal_dotdot_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "../etc/BUG-001.md", now=_NOW,
            )
        self.assertIn("'.' or '..'", str(cm.exception))

    def test_dot_segment_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(), "./docs/bug/BUG-001.md", now=_NOW,
            )

    def test_backslash_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "docs\\bug\\BUG-001.md", now=_NOW,
            )
        self.assertIn("forward slashes", str(cm.exception))

    def test_wrong_filename_pattern_rejected(self):
        # Not BUG-NNN.md
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "docs/bug/INCIDENT-001.md", now=_NOW,
            )
        self.assertIn("BUG-NNN.md", str(cm.exception))

    def test_BUG_id_with_4_digits_rejected(self):
        # Schema mandates 3-digit zero-pad until a future review.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_intake(
                _closed_state(), "docs/bug/BUG-1000.md", now=_NOW,
            )
        self.assertIn("BUG-NNN.md", str(cm.exception))

    def test_BUG_id_with_2_digits_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(), "docs/bug/BUG-01.md", now=_NOW,
            )

    def test_wrong_parent_directory_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_intake(
                _closed_state(), "docs/incident/BUG-001.md", now=_NOW,
            )

    def test_canonical_path_accepted(self):
        outcome = apply_bug_intake(
            _closed_state(), "docs/bug/BUG-007.md", now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["unresolved_bugs"], ["docs/bug/BUG-007.md"]
        )


class ContractTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_bug_intake(
            _closed_state(), "docs/bug/BUG-001.md", now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
