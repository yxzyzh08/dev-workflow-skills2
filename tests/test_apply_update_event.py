"""Unit tests for skills/_shared/dev_workflow/progress_state.apply_update_event.

These tests are pure: no file I/O, no clock access, no CLI invocation. They
exercise every branch of the state machine (4 events × legal/illegal
sub_state) plus iteration limit, gated check, project_state precondition,
and field-preservation invariants.
"""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_state import (
    EVENTS,
    GATED_STAGES,
    REVIEW_ITERATION_LIMIT,
    EventOutcome,
    ProgressStateError,
    apply_update_event,
    build_initial_state,
)


_NOW = "2026-05-15T11:00:00Z"


def _initial_state(*, scenario: str = "S1", release: str = "0.1") -> dict:
    return build_initial_state(
        project="MyApp",
        scenario=scenario,
        release=release,
        now="2026-05-15T10:00:00Z",
    )


def _state_at(*, sub_state: str, current_stage: str = "prd-inception",
              review_iteration: int = 0, project_state: str = "active") -> dict:
    state = _initial_state()
    state["sub_state"] = sub_state
    state["current_stage"] = current_stage
    state["review_iteration"] = review_iteration
    state["project_state"] = project_state
    return state


# ---------- write-complete ----------


class WriteCompleteTests(unittest.TestCase):
    def test_write_complete_from_write_to_in_review(self):
        outcome = apply_update_event(
            _state_at(sub_state="write"),
            "write-complete",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["sub_state"], "in-review")
        self.assertEqual(outcome.new_state["review_iteration"], 0)
        self.assertEqual(outcome.new_state["updated"], _NOW)
        self.assertIn("write -> in-review", outcome.history_summary)

    def test_write_complete_from_revising_preserves_iteration(self):
        outcome = apply_update_event(
            _state_at(sub_state="revising", review_iteration=3),
            "write-complete",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["sub_state"], "in-review")
        self.assertEqual(outcome.new_state["review_iteration"], 3)
        self.assertIn("revising -> in-review", outcome.history_summary)

    def test_write_complete_from_in_review_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(
                _state_at(sub_state="in-review"),
                "write-complete",
                now=_NOW,
            )
        self.assertIn("write-complete", str(cm.exception))
        self.assertIn("in-review", str(cm.exception))

    def test_write_complete_from_review_passed_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="review-passed"),
                "write-complete",
                now=_NOW,
            )

    def test_write_complete_from_approved_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="approved"),
                "write-complete",
                now=_NOW,
            )


# ---------- review-issues ----------


class ReviewIssuesTests(unittest.TestCase):
    def test_review_issues_increments_iteration(self):
        outcome = apply_update_event(
            _state_at(sub_state="in-review", review_iteration=0),
            "review-issues",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["sub_state"], "revising")
        self.assertEqual(outcome.new_state["review_iteration"], 1)

    def test_review_issues_iteration_six_to_seven_allowed(self):
        outcome = apply_update_event(
            _state_at(sub_state="in-review", review_iteration=6),
            "review-issues",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["review_iteration"], 7)

    def test_review_issues_iteration_seven_to_eight_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(
                _state_at(sub_state="in-review", review_iteration=7),
                "review-issues",
                now=_NOW,
            )
        self.assertIn(str(REVIEW_ITERATION_LIMIT), str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_review_issues_from_write_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="write"),
                "review-issues",
                now=_NOW,
            )

    def test_review_issues_from_revising_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="revising"),
                "review-issues",
                now=_NOW,
            )


# ---------- review-passed ----------


class ReviewPassedTests(unittest.TestCase):
    def test_review_passed_resets_iteration(self):
        outcome = apply_update_event(
            _state_at(sub_state="in-review", review_iteration=4),
            "review-passed",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["sub_state"], "review-passed")
        self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_review_passed_history_next_for_gated_stage(self):
        outcome = apply_update_event(
            _state_at(sub_state="in-review", current_stage="srs-specification"),
            "review-passed",
            now=_NOW,
        )
        self.assertEqual(outcome.history_next, "human-confirmed")

    def test_review_passed_history_next_for_non_gated_stage(self):
        outcome = apply_update_event(
            _state_at(sub_state="in-review", current_stage="development"),
            "review-passed",
            now=_NOW,
        )
        self.assertEqual(outcome.history_next, "advance")

    def test_review_passed_from_write_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="write"),
                "review-passed",
                now=_NOW,
            )

    def test_review_passed_from_revising_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="revising"),
                "review-passed",
                now=_NOW,
            )


# ---------- human-confirmed ----------


class HumanConfirmedTests(unittest.TestCase):
    def test_human_confirmed_on_gated_stage(self):
        for stage in sorted(GATED_STAGES):
            with self.subTest(stage=stage):
                outcome = apply_update_event(
                    _state_at(sub_state="review-passed", current_stage=stage),
                    "human-confirmed",
                    now=_NOW,
                )
                self.assertEqual(outcome.new_state["sub_state"], "approved")
                self.assertEqual(outcome.new_state["review_iteration"], 0)

    def test_human_confirmed_on_non_gated_stage_rejected(self):
        for stage in ("development", "testing", "delivery", "project-retrospective"):
            with self.subTest(stage=stage):
                with self.assertRaises(ProgressStateError) as cm:
                    apply_update_event(
                        _state_at(sub_state="review-passed", current_stage=stage),
                        "human-confirmed",
                        now=_NOW,
                    )
                self.assertIn("gated stages", str(cm.exception))
                self.assertIn(stage, str(cm.exception))

    def test_human_confirmed_from_in_review_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="in-review"),
                "human-confirmed",
                now=_NOW,
            )

    def test_human_confirmed_from_write_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="write"),
                "human-confirmed",
                now=_NOW,
            )


# ---------- generic preconditions ----------


class TerminalProjectStateTests(unittest.TestCase):
    def test_aborted_project_rejects_event(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(
                _state_at(sub_state="write", project_state="aborted"),
                "write-complete",
                now=_NOW,
            )
        self.assertIn("project_state", str(cm.exception))
        self.assertIn("aborted", str(cm.exception))

    def test_reconstructing_project_rejects_event(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="write", project_state="reconstructing"),
                "write-complete",
                now=_NOW,
            )


class UnknownInputTests(unittest.TestCase):
    def test_unknown_event_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(
                _state_at(sub_state="write"),
                "issues-found",  # business wording, not whitelisted
                now=_NOW,
            )
        self.assertIn("event must be one of", str(cm.exception))

    def test_invalid_now_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_event(
                _state_at(sub_state="write"),
                "write-complete",
                now="2026-05-15",  # missing time portion
            )

    def test_invalid_sub_state_value_rejected(self):
        state = _state_at(sub_state="write")
        state["sub_state"] = "no-such-state"
        with self.assertRaises(ProgressStateError):
            apply_update_event(state, "write-complete", now=_NOW)

    def test_negative_iteration_rejected(self):
        state = _state_at(sub_state="in-review")
        state["review_iteration"] = -1
        with self.assertRaises(ProgressStateError):
            apply_update_event(state, "review-issues", now=_NOW)


class IterationOverLimitTests(unittest.TestCase):
    """Phase 5.2 round 2 review M2: existing review_iteration > 7 must be
    rejected at the entry of every mutating event so a tampered or migrated
    progress.md cannot bypass the human-escalation invariant. The post-
    increment check inside review-issues already covered 7 -> 8; this entry
    check additionally blocks write-complete / review-passed /
    human-confirmed from preserving or resetting an over-limit value."""

    def test_write_complete_rejects_existing_iteration_eight(self):
        state = _state_at(sub_state="write", review_iteration=8)
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(state, "write-complete", now=_NOW)
        self.assertIn("review_iteration", str(cm.exception))
        self.assertIn("8", str(cm.exception))
        self.assertIn(str(REVIEW_ITERATION_LIMIT), str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_review_issues_rejects_existing_iteration_eight(self):
        # The entry check fires before the post-increment check, so the
        # error mentions the over-limit value as found, not 9.
        state = _state_at(sub_state="in-review", review_iteration=8)
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(state, "review-issues", now=_NOW)
        self.assertIn("review_iteration is 8", str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_review_passed_rejects_existing_iteration_eight(self):
        # Without the round 2 fix, review-passed would silently reset
        # iteration from 8 to 0, hiding the corruption.
        state = _state_at(sub_state="in-review", review_iteration=8)
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(state, "review-passed", now=_NOW)
        self.assertIn("8", str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_human_confirmed_rejects_existing_iteration_eight(self):
        state = _state_at(
            sub_state="review-passed",
            current_stage="prd-inception",
            review_iteration=8,
        )
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(state, "human-confirmed", now=_NOW)
        self.assertIn("8", str(cm.exception))
        self.assertIn("escalate", str(cm.exception))

    def test_iteration_seven_still_allowed_at_entry(self):
        # The cap is inclusive; iteration=7 must still pass the entry
        # check. write-complete preserves the value.
        outcome = apply_update_event(
            _state_at(sub_state="write", review_iteration=7),
            "write-complete",
            now=_NOW,
        )
        self.assertEqual(outcome.new_state["review_iteration"], 7)

    def test_iteration_far_above_limit_rejected(self):
        state = _state_at(sub_state="write", review_iteration=42)
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_event(state, "write-complete", now=_NOW)
        self.assertIn("42", str(cm.exception))


class FieldPreservationTests(unittest.TestCase):
    def test_other_fields_are_copied_verbatim(self):
        state = _state_at(sub_state="write")
        state["unresolved_bugs"] = ["docs/bug/BUG-001.md"]
        state["bug_flow"] = {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        }
        outcome = apply_update_event(state, "write-complete", now=_NOW)
        self.assertEqual(
            outcome.new_state["unresolved_bugs"], ["docs/bug/BUG-001.md"]
        )
        self.assertEqual(outcome.new_state["bug_flow"], state["bug_flow"])
        self.assertEqual(outcome.new_state["release"], state["release"])
        self.assertEqual(outcome.new_state["project_name"], state["project_name"])
        self.assertEqual(outcome.new_state["created"], state["created"])

    def test_outcome_is_frozen(self):
        outcome = apply_update_event(
            _state_at(sub_state="write"),
            "write-complete",
            now=_NOW,
        )
        self.assertIsInstance(outcome, EventOutcome)
        with self.assertRaises(Exception):
            outcome.new_state = {}  # type: ignore[misc]

    def test_events_set_matches_white_list(self):
        # Defends against accidental drift between EVENTS set and the
        # branches inside apply_update_event.
        self.assertEqual(
            EVENTS,
            {"write-complete", "review-issues", "review-passed", "human-confirmed"},
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
