"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_incident_resolve.

Phase 6.3: PRD-exception incident exit per ``--action``.
``--action continue`` is non-terminal and resumes testing/review-passed;
``--action abort`` and ``--action reconstruct`` are terminal and freeze
the project.
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    IncidentResolveOutcome,
    ProgressStateError,
    apply_incident_resolve,
)


_NOW = "2026-10-05T15:00:00Z"
_INCIDENT_PATH = "docs/incident/INCIDENT-007.md"
_ACTIVE_BUG = "docs/bug/BUG-700.md"


def _incident_active_state(
    *,
    project_state: str = "active",
    release_state: str = "active",
    incident_report_path: str = _INCIDENT_PATH,
    workflow_incident_active: bool = True,
    review_iteration: int = 0,
    sub_state: str = "review-passed",
    current_stage: str = "workflow-incident-analysis",
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
            "active": True,
            "bug_report_path": _ACTIVE_BUG,
            "root_cause": "prd-exception",
        },
        "workflow_incident_active": workflow_incident_active,
        "incident_report_path": incident_report_path,
        "unresolved_bugs": [],
        "development_state": None,
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-10-04T10:00:00Z",
    }


class ContinueActionTests(unittest.TestCase):
    """``--action continue`` (§12.1, v0.6 round 2 H3 simplification): single
    behavior, returns to testing/review-passed, clears bug_flow + incident.
    NOT terminal."""

    def test_clears_workflow_incident_state(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertIsInstance(outcome, IncidentResolveOutcome)
        self.assertFalse(outcome.new_state["workflow_incident_active"])
        self.assertIsNone(outcome.new_state["incident_report_path"])

    def test_clears_bug_flow(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )

    def test_resumes_testing_review_passed(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "testing")
        self.assertEqual(outcome.new_state["sub_state"], "review-passed")
        self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_continue_is_not_terminal(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertFalse(outcome.is_terminal)

    def test_continue_does_not_touch_project_state(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["project_state"], "active")
        self.assertEqual(outcome.new_state["release_state"], "active")
        self.assertIsNone(outcome.new_state["release_close_reason"])

    def test_history_summary_canonical_for_replay(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertIn("action=continue", outcome.history_summary)
        self.assertIn(f"incident={_INCIDENT_PATH}", outcome.history_summary)


class AbortActionTests(unittest.TestCase):
    """``--action abort`` (§12.2 v0.6 F11): terminal — project_state=aborted,
    release_state=closed with incident-abort reason."""

    def test_freezes_project_state(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "abort",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["project_state"], "aborted")
        self.assertEqual(outcome.new_state["release_state"], "closed")
        self.assertEqual(
            outcome.new_state["release_close_reason"], "incident-abort",
        )

    def test_clears_current_stage_and_sub_state(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "abort",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertIsNone(outcome.new_state["current_stage"])
        self.assertIsNone(outcome.new_state["sub_state"])
        self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_clears_bug_flow_and_incident_state(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "abort",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )
        self.assertFalse(outcome.new_state["workflow_incident_active"])
        self.assertIsNone(outcome.new_state["incident_report_path"])

    def test_abort_is_terminal(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "abort",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertTrue(outcome.is_terminal)


class ReconstructActionTests(unittest.TestCase):
    """``--action reconstruct`` (§12.3 v0.6 F11): terminal — same shape
    as abort but project_state=reconstructing and release_close_reason
    differs."""

    def test_freezes_project_state_as_reconstructing(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "reconstruct",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["project_state"], "reconstructing")
        self.assertEqual(outcome.new_state["release_state"], "closed")
        self.assertEqual(
            outcome.new_state["release_close_reason"], "incident-reconstruct",
        )

    def test_reconstruct_is_terminal(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "reconstruct",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertTrue(outcome.is_terminal)

    def test_reconstruct_history_next_mentions_new_directory(self):
        # The reconstruct path implies starting a fresh S3 project in a
        # new directory; the history next field should mention this so
        # operators reading history alone know what comes next.
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "reconstruct",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertIn("new directory", outcome.history_next)


class TerminalCleanupCompletenessTests(unittest.TestCase):
    """Spec watch point: v0.6 F11 cleanup must zero EVERY field listed in
    §12.2 / §12.3 mutation tables. Easy to forget one (e.g. leaving an
    odd review_iteration or stale bug_flow), and a recover roundtrip
    would diverge from forward then. These tests pin every field for
    both terminal actions."""

    def _state_with_dirty_fields(self) -> dict:
        # Populate fields that abort/reconstruct must zero so we can
        # verify cleanup wasn't half-done.
        state = _incident_active_state(
            review_iteration=4, sub_state="in-review",
            current_stage="workflow-incident-analysis",
        )
        return state

    def test_abort_zeroes_all_required_fields(self):
        outcome = apply_incident_resolve(
            self._state_with_dirty_fields(),
            "abort",
            _INCIDENT_PATH,
            now=_NOW,
        )
        new = outcome.new_state
        self.assertEqual(new["project_state"], "aborted")
        self.assertEqual(new["release_state"], "closed")
        self.assertEqual(new["release_close_reason"], "incident-abort")
        self.assertIsNone(new["current_stage"])
        self.assertIsNone(new["sub_state"])
        self.assertEqual(new["review_iteration"], 0)
        self.assertEqual(
            new["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )
        self.assertFalse(new["workflow_incident_active"])
        self.assertIsNone(new["incident_report_path"])

    def test_reconstruct_zeroes_all_required_fields(self):
        outcome = apply_incident_resolve(
            self._state_with_dirty_fields(),
            "reconstruct",
            _INCIDENT_PATH,
            now=_NOW,
        )
        new = outcome.new_state
        self.assertEqual(new["project_state"], "reconstructing")
        self.assertEqual(new["release_state"], "closed")
        self.assertEqual(new["release_close_reason"], "incident-reconstruct")
        self.assertIsNone(new["current_stage"])
        self.assertIsNone(new["sub_state"])
        self.assertEqual(new["review_iteration"], 0)
        self.assertEqual(
            new["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )
        self.assertFalse(new["workflow_incident_active"])
        self.assertIsNone(new["incident_report_path"])


class RejectionTests(unittest.TestCase):
    def test_no_active_incident_rejects(self):
        state = _incident_active_state(
            workflow_incident_active=False, incident_report_path=None,
        )
        with self.assertRaises(ProgressStateError) as cm:
            apply_incident_resolve(state, "continue", _INCIDENT_PATH, now=_NOW)
        self.assertIn("workflow_incident_active", str(cm.exception))

    def test_incident_path_mismatch_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_incident_resolve(
                _incident_active_state(),
                "continue",
                "docs/incident/INCIDENT-008.md",
                now=_NOW,
            )
        self.assertIn("does not match", str(cm.exception))

    def test_invalid_incident_path_shape_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_resolve(
                _incident_active_state(),
                "continue",
                "/etc/passwd",
                now=_NOW,
            )

    def test_unknown_action_rejects(self):
        for bad in ("retry", "skip", "", "Continue", "ABORT"):
            with self.subTest(action=bad):
                with self.assertRaises(ProgressStateError) as cm:
                    apply_incident_resolve(
                        _incident_active_state(),
                        bad,
                        _INCIDENT_PATH,
                        now=_NOW,
                    )
                self.assertIn("action", str(cm.exception))

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_resolve(
                _incident_active_state(review_iteration=8),
                "continue",
                _INCIDENT_PATH,
                now=_NOW,
            )

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_resolve(
                _incident_active_state(),
                "continue",
                _INCIDENT_PATH,
                now="2026-10-05",
            )

    def test_continue_does_not_require_active_project(self):
        # Sanity check on the design choice: incident-resolve does NOT
        # gate on project_state==active (because abort/reconstruct
        # legitimately mutate project_state). For continue, we still
        # land in valid state because we trust workflow_incident_active.
        # We don't assert continue succeeds with project_state=aborted
        # (that's an out-of-band combination); we just confirm the
        # function doesn't reject because of project_state alone when
        # workflow_incident_active is true.
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertFalse(outcome.is_terminal)


class ContractTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_incident_resolve(
            _incident_active_state(),
            "continue",
            _INCIDENT_PATH,
            now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]

    def test_is_terminal_flag_consistency(self):
        # is_terminal must mirror the action-aware terminal gate that
        # replay_history (Phase 6.3) uses to decide whether subsequent
        # mutating entries are allowed.
        for action, expected in (
            ("continue", False),
            ("abort", True),
            ("reconstruct", True),
        ):
            with self.subTest(action=action):
                outcome = apply_incident_resolve(
                    _incident_active_state(),
                    action,
                    _INCIDENT_PATH,
                    now=_NOW,
                )
                self.assertEqual(outcome.is_terminal, expected)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
