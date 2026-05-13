"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_bug_start.

Phase 6.1: Bug Flow entry. The CLI computes ``rollback_decisions`` by
reading the BUG body; these unit tests pass the tuple directly to
``apply_bug_start`` so they remain pure (no file I/O).
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    BugStartOutcome,
    ProgressStateError,
    ROOT_CAUSES_FOR_BUG_START,
    apply_bug_start,
)


_NOW = "2026-09-01T15:00:00Z"


def _testing_state(
    *,
    sub_state: str = "review-passed",
    bug_flow_active: bool = False,
    project_state: str = "active",
    release_state: str = "active",
    review_iteration: int = 0,
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
        "current_stage": "testing",
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
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "development_state": (
            {"task_states": dict(task_states)} if task_states is not None else None
        ),
        "created": "2026-08-01T10:00:00Z",
        "updated": "2026-08-31T10:00:00Z",
    }


class HappyPathTests(unittest.TestCase):
    def test_root_cause_srs_routes_to_srs_specification(self):
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-001.md",
            "srs",
            now=_NOW,
        )
        self.assertIsInstance(outcome, BugStartOutcome)
        self.assertEqual(outcome.new_state["current_stage"], "srs-specification")
        self.assertEqual(outcome.new_state["sub_state"], "write")
        self.assertEqual(outcome.new_state["review_iteration"], 0)
        self.assertEqual(
            outcome.new_state["bug_flow"],
            {
                "active": True,
                "bug_report_path": "docs/bug/BUG-001.md",
                "root_cause": "srs",
            },
        )
        self.assertEqual(outcome.rollback_decisions, ())

    def test_root_cause_architecture_routes_to_architecture_design(self):
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-002.md",
            "architecture",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "architecture-design")

    def test_root_cause_development_without_rollback(self):
        # development root cause but caller passed empty rollback list
        # (ambiguous classification or no affected tasks). Mutation
        # still applies for current_stage / bug_flow.
        outcome = apply_bug_start(
            _testing_state(task_states={"T1": "verified"}),
            "docs/bug/BUG-003.md",
            "development",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["current_stage"], "development")
        # T1 still verified — no rollback was supplied.
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"], {"T1": "verified"}
        )

    def test_history_summary_canonical_for_replay(self):
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-007.md",
            "srs",
            now=_NOW,
        )
        self.assertIn("bug=docs/bug/BUG-007.md", outcome.history_summary)
        self.assertIn("root_cause=srs", outcome.history_summary)


class Gap4DevRollbackTests(unittest.TestCase):
    def test_verified_to_test_revising_for_test_classification(self):
        rollback = (
            ("T1", "verified", "test-revising", "test-only fix"),
        )
        outcome = apply_bug_start(
            _testing_state(task_states={"T1": "verified"}),
            "docs/bug/BUG-004.md",
            "development",
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "test-revising",
        )
        self.assertEqual(outcome.rollback_decisions, rollback)

    def test_multiple_rollbacks_applied_atomically(self):
        rollback = (
            ("T1", "verified", "code-revising", "source fix"),
            ("T3", "code-review-passed", "code-revising", "source fix"),
        )
        outcome = apply_bug_start(
            _testing_state(task_states={"T1": "verified", "T3": "code-review-passed"}),
            "docs/bug/BUG-005.md",
            "development",
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
        outcome = apply_bug_start(
            _testing_state(task_states={"T1": "verified"}),
            "docs/bug/BUG-006.md",
            "development",
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertIn("rollback=T1:verified->code-revising", outcome.history_summary)

    def test_rollback_with_non_dev_root_cause_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_start(
                _testing_state(task_states={"T1": "verified"}),
                "docs/bug/BUG-007.md",
                "srs",
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "test-revising", "test-only fix"),
                ),
            )
        self.assertIn("development", str(cm.exception))

    def test_rollback_with_non_protected_transition_rejected(self):
        # ``verified -> verifying`` is not in PROTECTED_TASK_TRANSITIONS.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_start(
                _testing_state(task_states={"T1": "verified"}),
                "docs/bug/BUG-008.md",
                "development",
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "verifying", "weird"),
                ),
            )
        self.assertIn("Gap-4", str(cm.exception))

    def test_rollback_with_stale_old_status_rejected(self):
        # Caller said T1 was 'verified' but progress.md has 'code-writing'.
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_start(
                _testing_state(task_states={"T1": "code-writing"}),
                "docs/bug/BUG-009.md",
                "development",
                now=_NOW,
                rollback_decisions=(
                    ("T1", "verified", "code-revising", "source fix"),
                ),
            )
        self.assertIn("out-of-band", str(cm.exception))


class RejectionTests(unittest.TestCase):
    def test_active_bug_flow_rejects(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_start(
                _testing_state(bug_flow_active=True),
                "docs/bug/BUG-010.md",
                "srs",
                now=_NOW,
            )
        self.assertIn("already active", str(cm.exception))

    def test_non_testing_stage_rejects(self):
        state = _testing_state()
        state["current_stage"] = "development"
        with self.assertRaises(ProgressStateError) as cm:
            apply_bug_start(state, "docs/bug/BUG-001.md", "srs", now=_NOW)
        self.assertIn("testing", str(cm.exception))

    def test_non_review_passed_substate_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(sub_state="in-review"),
                "docs/bug/BUG-001.md",
                "srs",
                now=_NOW,
            )

    def test_non_active_release_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(release_state="closed"),
                "docs/bug/BUG-001.md",
                "srs",
                now=_NOW,
            )

    def test_aborted_project_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(project_state="aborted"),
                "docs/bug/BUG-001.md",
                "srs",
                now=_NOW,
            )

    def test_iter_over_limit_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(review_iteration=8),
                "docs/bug/BUG-001.md",
                "srs",
                now=_NOW,
            )

    def test_unknown_root_cause_rejects(self):
        for bad in ("prd-exception", "infra", "foo", ""):
            with self.subTest(root_cause=bad):
                with self.assertRaises(ProgressStateError):
                    apply_bug_start(
                        _testing_state(),
                        "docs/bug/BUG-001.md",
                        bad,
                        now=_NOW,
                    )

    def test_invalid_bug_path_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(),
                "/etc/passwd",
                "srs",
                now=_NOW,
            )
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(),
                "docs/bug/BUG-1000.md",
                "srs",
                now=_NOW,
            )

    def test_invalid_now_rejects(self):
        with self.assertRaises(ProgressStateError):
            apply_bug_start(
                _testing_state(),
                "docs/bug/BUG-001.md",
                "srs",
                now="2026-09-01",
            )


class ContractTests(unittest.TestCase):
    def test_root_causes_constant_matches_implementation(self):
        self.assertEqual(
            ROOT_CAUSES_FOR_BUG_START,
            frozenset({"srs", "architecture", "development"}),
        )

    def test_outcome_is_frozen(self):
        outcome = apply_bug_start(
            _testing_state(), "docs/bug/BUG-001.md", "srs", now=_NOW,
        )
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]


# ---------- Phase 6.1 round 2 review L1: planning-route note ----------


class PlanningRouteNoteTests(unittest.TestCase):
    """Phase 6.1 round 2 review L1: when ``root_cause == 'development'``
    and the rollback list is empty, ``apply_bug_start`` records a
    persistent planning-route note in ``history_result`` /
    ``history_next`` so a future agent reading only progress-history.md
    can see the documented requirement to invoke
    ``development-planning-write``."""

    def test_dev_root_cause_with_empty_rollback_records_planning_route(self):
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-001.md",
            "development",
            now=_NOW,
            rollback_decisions=(),
        )
        self.assertIn("development-planning-write", outcome.history_result)
        self.assertIn("route=", outcome.history_result)
        self.assertIn("development-planning-write", outcome.history_next)

    def test_dev_root_cause_with_rollback_does_not_append_planning_route(self):
        rollback = (("T1", "verified", "test-revising", "test-only fix"),)
        outcome = apply_bug_start(
            _testing_state(task_states={"T1": "verified"}),
            "docs/bug/BUG-002.md",
            "development",
            now=_NOW,
            rollback_decisions=rollback,
        )
        self.assertNotIn("development-planning-write", outcome.history_result)
        self.assertNotIn("development-planning-write", outcome.history_next)

    def test_srs_root_cause_does_not_get_planning_route(self):
        # Non-dev root causes use their stage's standard write skill;
        # planning-route note is dev-specific.
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-003.md",
            "srs",
            now=_NOW,
        )
        self.assertNotIn("planning-write", outcome.history_next)
        self.assertIn("srs-specification-write", outcome.history_next)

    def test_architecture_root_cause_does_not_get_planning_route(self):
        outcome = apply_bug_start(
            _testing_state(),
            "docs/bug/BUG-004.md",
            "architecture",
            now=_NOW,
        )
        self.assertIn("architecture-design-write", outcome.history_next)
        self.assertNotIn("planning-write", outcome.history_next)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
