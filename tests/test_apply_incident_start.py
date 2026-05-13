"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_incident_start.

Phase 6.3: PRD-exception incident entry. The CLI is responsible for
double-validating the BUG and INCIDENT documents via
``doc-guardian/scripts/validate.py file`` and confirming the BUG's
``root_cause == prd-exception`` plus the INCIDENT's
``triggered_by_bug == BUG bug_id``; these unit tests skip those file
checks (they're CLI concerns) and exercise the state-machine
mutation directly.
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    IncidentStartOutcome,
    ProgressStateError,
    apply_incident_start,
)


_NOW = "2026-10-01T15:00:00Z"
_BUG_PATH = "docs/bug/BUG-700.md"
_INCIDENT_PATH = "docs/incident/INCIDENT-007.md"


def _testing_state(
    *,
    sub_state: str = "review-passed",
    current_stage: str = "testing",
    bug_flow_active: bool = False,
    workflow_incident_active: bool = False,
    project_state: str = "active",
    release_state: str = "active",
    review_iteration: int = 0,
    incident_report_path: str | None = None,
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
        "incident_report_path": incident_report_path,
        "unresolved_bugs": [],
        "development_state": None,
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-09-30T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_incident_start_opens_bug_flow_and_incident_state(self):
        outcome = apply_incident_start(
            _testing_state(),
            _BUG_PATH,
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertIsInstance(outcome, IncidentStartOutcome)
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {
                "active": True,
                "bug_report_path": _BUG_PATH,
                "root_cause": "prd-exception",
            },
        )
        self.assertTrue(outcome.new_state["workflow_incident_active"])
        self.assertEqual(
            outcome.new_state["incident_report_path"], _INCIDENT_PATH,
        )
        self.assertEqual(
            outcome.new_state["current_stage"], "workflow-incident-analysis",
        )

    def test_sub_state_is_preserved(self):
        # incident-start does NOT touch sub_state — incident analysis
        # runs alongside whatever sub_state existed at trigger time.
        # (The continue resolve later resets it.)
        for sub_state in ("review-passed", "in-review", "write"):
            with self.subTest(sub_state=sub_state):
                outcome = apply_incident_start(
                    _testing_state(sub_state=sub_state),
                    _BUG_PATH,
                    _INCIDENT_PATH,
                    now=_NOW,
                )
                self.assertEqual(outcome.new_state["sub_state"], sub_state)

    def test_review_iteration_is_preserved(self):
        # Likewise review_iteration is not reset on incident-start —
        # only resolve continue (= resume testing fresh) clears it.
        outcome = apply_incident_start(
            _testing_state(review_iteration=3),
            _BUG_PATH,
            _INCIDENT_PATH,
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["review_iteration"], 3)

    def test_history_summary_canonical_for_replay(self):
        outcome = apply_incident_start(
            _testing_state(),
            _BUG_PATH,
            _INCIDENT_PATH,
            now=_NOW,
        )
        # Replay handler reverses bug=, incident=, root_cause= tokens.
        self.assertIn(f"bug={_BUG_PATH}", outcome.history_summary)
        self.assertIn(f"incident={_INCIDENT_PATH}", outcome.history_summary)
        self.assertIn("root_cause=prd-exception", outcome.history_summary)

    def test_can_trigger_from_any_stage_and_substate(self):
        # incident-start does not gate on current_stage; bug-triage may
        # invoke it from any stage where it judges PRD exception. The
        # only state requirement is: no active bug flow / incident.
        for stage in ("testing", "development", "delivery"):
            with self.subTest(stage=stage):
                outcome = apply_incident_start(
                    _testing_state(current_stage=stage),
                    _BUG_PATH,
                    _INCIDENT_PATH,
                    now=_NOW,
                )
                self.assertEqual(
                    outcome.new_state["current_stage"],
                    "workflow-incident-analysis",
                )


class RejectionTests(unittest.TestCase):
    def test_active_bug_flow_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_incident_start(
                _testing_state(bug_flow_active=True),
                _BUG_PATH,
                _INCIDENT_PATH,
                now=_NOW,
            )
        self.assertIn("already active", str(cm.exception))

    def test_workflow_incident_already_active_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_incident_start(
                _testing_state(
                    workflow_incident_active=True,
                    incident_report_path="docs/incident/INCIDENT-001.md",
                ),
                _BUG_PATH,
                _INCIDENT_PATH,
                now=_NOW,
            )
        self.assertIn("already True", str(cm.exception))

    def test_aborted_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(project_state="aborted"),
                _BUG_PATH,
                _INCIDENT_PATH,
                now=_NOW,
            )

    def test_reconstructing_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(project_state="reconstructing"),
                _BUG_PATH,
                _INCIDENT_PATH,
                now=_NOW,
            )

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(review_iteration=8),
                _BUG_PATH,
                _INCIDENT_PATH,
                now=_NOW,
            )

    def test_invalid_bug_path_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(),
                "/etc/passwd",
                _INCIDENT_PATH,
                now=_NOW,
            )

    def test_invalid_incident_path_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(),
                _BUG_PATH,
                "/etc/passwd",
                now=_NOW,
            )

    def test_non_canonical_incident_path_rejects(self):
        # 4-digit ID and non-INCIDENT directory both rejected.
        for bad in (
            "docs/incident/INCIDENT-1000.md",
            "docs/bug/INCIDENT-007.md",
            "incident/INCIDENT-007.md",
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ProgressStateError):
                    apply_incident_start(
                        _testing_state(),
                        _BUG_PATH,
                        bad,
                        now=_NOW,
                    )

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_incident_start(
                _testing_state(),
                _BUG_PATH,
                _INCIDENT_PATH,
                now="2026-10-01",
            )


class ContractTests(unittest.TestCase):
    def test_outcome_is_frozen(self):
        outcome = apply_incident_start(
            _testing_state(),
            _BUG_PATH,
            _INCIDENT_PATH,
            now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]

    def test_root_cause_literal_not_in_root_cause_to_stage(self):
        # Phase 6.3 watch point: 'prd-exception' is a 4th
        # bug_flow.root_cause value but must NOT be in the bug-start /
        # bug-rework root-cause map (would route to a normal write
        # stage, breaking incident semantics).
        from skills._shared.dev_workflow.progress_state import (
            ROOT_CAUSES_FOR_BUG_START,
        )
        self.assertNotIn("prd-exception", ROOT_CAUSES_FOR_BUG_START)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
