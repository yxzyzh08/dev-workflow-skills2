import unittest

from skills._shared.dev_workflow.progress_state import (
    EVENTS,
    NORMAL_TASK_TRANSITIONS,
    PROTECTED_TASK_TRANSITIONS,
    ROOT_CAUSE_TO_STAGE,
    TASK_TRANSITIONS,
    is_valid_task_transition,
    next_stage,
)
from skills._shared.dev_workflow.schema import INCREMENTAL_DOC_TYPES, PER_TYPE_REQUIRED_FIELDS, SNAPSHOT_DOC_TYPES


class ProgressStateTests(unittest.TestCase):
    def test_event_whitelist(self):
        self.assertEqual(EVENTS, {"write-complete", "review-issues", "review-passed", "human-confirmed"})
        self.assertNotIn("issues-found", EVENTS)

    def test_normal_transitions_allowed_by_default(self):
        self.assertTrue(is_valid_task_transition(None, "planning-done"))
        self.assertTrue(is_valid_task_transition("planning-done", "test-writing"))
        self.assertTrue(is_valid_task_transition("verifying", "verified"))

    def test_protected_transitions_require_flag(self):
        # Gap-3 + Gap-4 protected transitions must be rejected unless the
        # caller explicitly opts in after verifying ownership preconditions.
        for old, new in PROTECTED_TASK_TRANSITIONS:
            self.assertFalse(
                is_valid_task_transition(old, new),
                msg=f"protected transition {old}->{new} must be rejected by default",
            )
            self.assertTrue(
                is_valid_task_transition(old, new, allow_protected=True),
                msg=f"protected transition {old}->{new} must succeed with allow_protected=True",
            )

    def test_protected_set_matches_command_reference_gaps(self):
        # Spec source: command-reference.md state-machine table lines 645-648.
        self.assertEqual(
            PROTECTED_TASK_TRANSITIONS,
            {
                ("verifying", "code-revising"),
                ("verified", "test-revising"),
                ("verified", "code-revising"),
                ("code-review-passed", "code-revising"),
            },
        )

    def test_normal_and_protected_are_disjoint_and_union_is_full_table(self):
        self.assertFalse(NORMAL_TASK_TRANSITIONS & PROTECTED_TASK_TRANSITIONS)
        self.assertEqual(TASK_TRANSITIONS, NORMAL_TASK_TRANSITIONS | PROTECTED_TASK_TRANSITIONS)

    def test_illegal_transition_rejected_even_with_flag(self):
        self.assertFalse(is_valid_task_transition("verifying", "test-revising"))
        self.assertFalse(is_valid_task_transition("verifying", "test-revising", allow_protected=True))

    def test_stage_helpers(self):
        self.assertEqual(next_stage("testing"), "delivery")
        self.assertEqual(ROOT_CAUSE_TO_STAGE["development"], "development")


class SchemaTests(unittest.TestCase):
    def test_change_log_classification(self):
        self.assertIn("srs", INCREMENTAL_DOC_TYPES)
        self.assertIn("bug-report", INCREMENTAL_DOC_TYPES)
        self.assertIn("verification-result", SNAPSHOT_DOC_TYPES)
        self.assertNotIn("verification-result", INCREMENTAL_DOC_TYPES)

    def test_required_fields_capture_key_task6_schema(self):
        self.assertIn("is_multi_module", PER_TYPE_REQUIRED_FIELDS["srs"])
        self.assertIn("architecture_change", PER_TYPE_REQUIRED_FIELDS["srs"])
        self.assertIn("consumed_in_release", PER_TYPE_REQUIRED_FIELDS["bug-report"])
        self.assertIn("review_status", PER_TYPE_REQUIRED_FIELDS["test-review-report"])


if __name__ == "__main__":
    unittest.main()
