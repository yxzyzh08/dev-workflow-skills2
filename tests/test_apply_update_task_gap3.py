"""Phase 6.1: ``apply_update_task`` Gap-3 transition tests.

Gap-3 (``verifying -> code-revising``) is the verification-retry path
owned by ``development-code-write``. It is NOT a Bug Flow transition
(that's Gap-4 / Phase 6.2 ``bug-rework``). Phase 6.1 enables Gap-3 by
adding an artifact precondition: ``verification_result.md
verification_status ∈ {fail, partial}``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from skills._shared.dev_workflow.progress_artifacts import ProgressArtifactError
from skills._shared.dev_workflow.progress_state import (
    ProgressStateError,
    apply_update_task,
)


_NOW = "2026-09-15T12:00:00Z"


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_doc(root: Path, rel: str, fm: dict, body: str = "Body.\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{_emit_yaml(fm)}\n---\n{body}", encoding="utf-8")
    return p


def _make_verification_result(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    verification_status: str = "fail",
) -> None:
    fm = {
        "title": "verification-result doc",
        "type": "verification-result",
        "status": "draft",
        "created": "2026-09-15T10:00:00Z",
        "updated": "2026-09-15T10:00:00Z",
        "owner": "claude-opus-4-7/development-code-write",
        "release": release,
        "task_id": task_id,
        "verification_status": verification_status,
    }
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/verification_result.md",
        fm,
    )


def _dev_state(*, task_states=None) -> dict:
    return {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": "active",
        "release": "0.1",
        "release_state": "active",
        "release_close_reason": None,
        "previous_releases": [],
        "scenario": "S1",
        "scenario_subtype": None,
        "current_stage": "development",
        "sub_state": "write",
        "review_iteration": 0,
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
        "unresolved_bugs": [],
        "development_state": {"task_states": dict(task_states or {})},
        "created": "2026-08-01T10:00:00Z",
        "updated": "2026-09-14T10:00:00Z",
    }


class _BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()


class Gap3HappyPathTests(_BaseTest):
    def test_verifying_to_code_revising_with_fail_status(self):
        _make_verification_result(self.root, verification_status="fail")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "verifying"}),
            "T1",
            "code-revising",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-revising",
        )

    def test_verifying_to_code_revising_with_partial_status(self):
        _make_verification_result(self.root, verification_status="partial")
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "verifying"}),
            "T1",
            "code-revising",
            now=_NOW,
            root=self.root,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-revising",
        )


class Gap3RejectionTests(_BaseTest):
    def test_verifying_to_code_revising_with_pass_rejects(self):
        # If verification passed, the caller should be moving the task
        # to ``verified``, not back to ``code-revising``.
        _make_verification_result(self.root, verification_status="pass")
        with self.assertRaises(ProgressArtifactError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "verifying"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("Gap-3", str(cm.exception))
        self.assertIn("fail, partial", str(cm.exception))

    def test_verifying_to_code_revising_without_verification_result_rejects(self):
        with self.assertRaises(ProgressArtifactError):
            apply_update_task(
                _dev_state(task_states={"T1": "verifying"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )


class Gap4StillRejectedThroughUpdateTask(_BaseTest):
    """Phase 6.1 still rejects Gap-4 transitions through ``update --task``;
    only ``bug-start`` (Phase 6.1) / ``bug-rework`` (Phase 6.2) may apply
    them. This guards against accidental bypass."""

    def test_verified_to_test_revising_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "verified"}),
                "T1",
                "test-revising",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("Gap-4", str(cm.exception))
        self.assertIn("bug-start", str(cm.exception))

    def test_verified_to_code_revising_rejected(self):
        with self.assertRaises(ProgressStateError) as cm:
            apply_update_task(
                _dev_state(task_states={"T1": "verified"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )
        self.assertIn("Gap-4", str(cm.exception))

    def test_code_review_passed_to_code_revising_rejected(self):
        with self.assertRaises(ProgressStateError):
            apply_update_task(
                _dev_state(task_states={"T1": "code-review-passed"}),
                "T1",
                "code-revising",
                now=_NOW,
                root=self.root,
            )


class Gap3ReplayBypassesArtifactCheckTests(_BaseTest):
    """Replay sets validate_artifacts=False (consistent with Phase 5.3
    design); a Gap-3 transition with no verification_result on disk
    must still apply during replay."""

    def test_replay_path_skips_verification_check(self):
        outcome = apply_update_task(
            _dev_state(task_states={"T1": "verifying"}),
            "T1",
            "code-revising",
            now=_NOW,
            root=self.root,
            validate_artifacts=False,
        )
        self.assertEqual(
            outcome.new_state["development_state"]["task_states"]["T1"],
            "code-revising",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
