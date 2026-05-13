"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_release_start."""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    ProgressStateError,
    RELEASE_START_SUBTYPES,
    ReleaseStartOutcome,
    apply_release_start,
)


_NOW = "2026-10-01T09:00:00Z"


def _closed_state(
    *,
    release: str = "0.1",
    previous_releases=None,
    unresolved_bugs=None,
    project_state: str = "active",
    review_iteration: int = 0,
) -> dict:
    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": project_state,
        "release": release,
        "release_state": "closed",
        "release_close_reason": "stage-7-completed",
        "previous_releases": list(previous_releases or [release]),
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": "project-retrospective",
        "sub_state": "review-passed",
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
        "unresolved_bugs": list(unresolved_bugs or []),
        "development_state": {"task_states": {"T1": "verified"}},
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-09-30T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_release_start_S2_1_to_prd_inception(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        self.assertIsInstance(outcome, ReleaseStartOutcome)
        self.assertEqual(outcome.new_state["release"], "0.2")
        self.assertEqual(outcome.new_state["release_state"], "active")
        self.assertIsNone(outcome.new_state["release_close_reason"])
        self.assertEqual(outcome.new_state["scenario"], "S2")
        self.assertEqual(outcome.new_state["scenario_subtype"], "S2-1")
        self.assertEqual(outcome.new_state["current_stage"], "prd-inception")
        self.assertEqual(outcome.new_state["sub_state"], "write")
        self.assertEqual(outcome.new_state["review_iteration"], 0)
        self.assertEqual(outcome.new_state["unresolved_bugs"], [])
        self.assertEqual(outcome.consumed_bugs, ())
        self.assertEqual(outcome.new_state["updated"], _NOW)

    def test_release_start_S2_2_to_srs_specification(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-2",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "srs-specification")
        self.assertEqual(outcome.new_state["scenario_subtype"], "S2-2")
        self.assertIn("Full Mode", outcome.history_next)

    def test_release_start_S2_3_to_srs_specification_change_mode(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-3",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "srs-specification")
        self.assertEqual(outcome.new_state["scenario_subtype"], "S2-3")
        self.assertIn("Change Mode", outcome.history_next)

    def test_artifacts_paths_reset_to_new_release(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        artifacts = outcome.new_state["artifacts"]
        self.assertEqual(artifacts["srs"], "docs/release0.2/srs/srs.md")
        self.assertEqual(
            artifacts["acceptance_plan"], "docs/release0.2/srs/acceptance_plan.md"
        )
        self.assertIsNone(artifacts["integration_plan"])
        self.assertIsNone(artifacts["architecture_delta"])
        # Project-level artifacts unchanged.
        self.assertEqual(artifacts["prd"], "docs/prd/prd.md")
        self.assertEqual(artifacts["architecture"], "docs/architecture/architecture.md")

    def test_development_state_cleared(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        self.assertNotIn("development_state", outcome.new_state)

    def test_unresolved_bugs_consumed(self):
        outcome = apply_release_start(
            _closed_state(
                unresolved_bugs=["docs/bug/BUG-001.md", "docs/bug/BUG-002.md"]
            ),
            new_version="0.2",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        self.assertEqual(
            outcome.consumed_bugs,
            ("docs/bug/BUG-001.md", "docs/bug/BUG-002.md"),
        )
        self.assertEqual(outcome.new_state["unresolved_bugs"], [])
        self.assertIn("consumed 2", outcome.history_summary)

    def test_history_summary_canonical_tokens_in_summary_only(self):
        # Phase 5.4 round 2 L1: replay must be able to reverse
        # version + scenario from the summary alone (independent of
        # result), so a summary-only consumer cannot miss them.
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.5",
            scenario_subtype="S2-2",
            now=_NOW,
        )
        self.assertIn("version=0.5", outcome.history_summary)
        self.assertIn("scenario=S2-2", outcome.history_summary)


class RejectionTests(unittest.TestCase):
    def test_release_state_not_closed_rejected(self):
        state = _closed_state()
        state["release_state"] = "active"
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_start(
                state, new_version="0.2", scenario_subtype="S2-1", now=_NOW,
            )
        self.assertIn("release_state", str(cm.exception))

    def test_aborted_project_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_start(
                _closed_state(project_state="aborted"),
                new_version="0.2",
                scenario_subtype="S2-1",
                now=_NOW,
            )

    def test_invalid_scenario_subtype_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_start(
                _closed_state(),
                new_version="0.2",
                scenario_subtype="S2-4",  # forbidden by spec
                now=_NOW,
            )
        self.assertIn("scenario_subtype", str(cm.exception))
        self.assertIn("S2-4", str(cm.exception))

    def test_S1_or_S3_scenario_rejected(self):
        # S1 / S3 belong to init / new project, not release-start.
        for bad in ("S1", "S3", "S2", "S2-7", ""):
            with self.subTest(scenario=bad):
                with self.assertRaises(ProgressStateError):
                    apply_release_start(
                        _closed_state(),
                        new_version="0.2",
                        scenario_subtype=bad,
                        now=_NOW,
                    )

    def test_invalid_version_format_rejected(self):
        for bad in ("0.1.1", "0", "v0.2", "0.2.3-alpha"):
            with self.subTest(version=bad):
                with self.assertRaises(ProgressStateError):
                    apply_release_start(
                        _closed_state(),
                        new_version=bad,
                        scenario_subtype="S2-1",
                        now=_NOW,
                    )

    def test_version_must_be_strictly_greater(self):
        # Equal to current
        with self.assertRaises(ProgressStateError) as cm:
            apply_release_start(
                _closed_state(release="0.2", previous_releases=["0.1", "0.2"]),
                new_version="0.2",
                scenario_subtype="S2-1",
                now=_NOW,
            )
        self.assertIn("strictly greater", str(cm.exception))

    def test_version_smaller_than_current_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_start(
                _closed_state(release="0.5", previous_releases=["0.1", "0.2", "0.5"]),
                new_version="0.3",  # smaller than 0.5
                scenario_subtype="S2-1",
                now=_NOW,
            )

    def test_version_greater_than_max_prior_allowed(self):
        # Strictly greater than max(previous_releases ∪ {current})
        outcome = apply_release_start(
            _closed_state(release="0.5", previous_releases=["0.1", "0.2", "0.5"]),
            new_version="0.6",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["release"], "0.6")

    def test_iter_over_limit_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_start(
                _closed_state(review_iteration=8),
                new_version="0.2",
                scenario_subtype="S2-1",
                now=_NOW,
            )

    def test_invalid_now_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_release_start(
                _closed_state(),
                new_version="0.2",
                scenario_subtype="S2-1",
                now="2026-10-01",
            )


class ContractTests(unittest.TestCase):
    def test_release_start_subtypes_constant_matches_implementation(self):
        self.assertEqual(
            RELEASE_START_SUBTYPES, frozenset({"S2-1", "S2-2", "S2-3"})
        )

    def test_outcome_is_frozen(self):
        outcome = apply_release_start(
            _closed_state(),
            new_version="0.2",
            scenario_subtype="S2-1",
            now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.consumed_bugs = ()  # type: ignore[misc]


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
