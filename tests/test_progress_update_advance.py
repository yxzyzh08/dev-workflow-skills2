"""CLI integration tests for progress.py update --advance.

Phase 6.4 P6 matrix forward path. The CLI runs three live filesystem
checks (A: existence, B: validate.py file, E: verification_status==pass
for stages 4/5/6) before delegating to ``apply_update_advance`` via
``_run_update_pipeline``. These tests focus on the P6 forward-path
contract; real doc-guardian validation is exercised end-to-end by
``test_validate_consistency.py``. Where helpful we patch
``progress.validate_doc`` to short-circuit doc-guardian and isolate
the P6 forward path's branches.
"""

from __future__ import annotations

import contextlib
import importlib
import io
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "skills" / "workflow-protocol" / "scripts"
for _path in (_SCRIPTS_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

progress = importlib.import_module("progress")

from skills._shared.dev_workflow import progress_replay  # noqa: E402
from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    parse_frontmatter,
    render_markdown,
)
from skills._shared.dev_workflow.progress_history import (  # noqa: E402
    HistoryEntry,
    append_history_text,
    parse_history_text,
)


# ---------- test-only handler / fixtures ----------


_TEST_ADVANCE_EVENT = "test-stage-advance"


def _test_stage_advance_handler(state, entry, root):
    if not state:
        raise progress_replay.ReplayError(
            f"history at {entry.timestamp}: '{_TEST_ADVANCE_EVENT}' requires prior init"
        )
    tokens: dict[str, str] = {}
    for token in entry.summary.split():
        if "=" in token:
            key, _, value = token.partition("=")
            tokens[key] = value
    new_state = dict(state)
    if "current_stage" in tokens:
        new_state["current_stage"] = tokens["current_stage"]
    if "sub_state" in tokens:
        new_state["sub_state"] = tokens["sub_state"]
    if "review_iteration" in tokens:
        new_state["review_iteration"] = int(tokens["review_iteration"])
    if "task_states" in tokens:
        kv: dict[str, str] = {}
        for piece in tokens["task_states"].split(";"):
            if not piece:
                continue
            tid, _, status = piece.partition(":")
            kv[tid] = status
        new_state["development_state"] = {"task_states": kv}
    if "bug_flow_active" in tokens:
        new_state["bug_flow"] = {
            "active": tokens["bug_flow_active"] == "true",
            "bug_report_path": (
                "docs/bug/BUG-099.md" if tokens["bug_flow_active"] == "true" else None
            ),
            "root_cause": "srs" if tokens["bug_flow_active"] == "true" else None,
        }
    new_state["updated"] = entry.timestamp
    return new_state


@contextlib.contextmanager
def _install_test_stage_advance_handler():
    handlers = dict(progress_replay._HANDLERS)
    handlers[_TEST_ADVANCE_EVENT] = _test_stage_advance_handler
    with patch.object(progress_replay, "_HANDLERS", handlers):
        yield


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_doc(root: Path, rel: str, fm: dict, body: str = "Body.\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{_emit_yaml(fm)}\n---\n{body}", encoding="utf-8")
    return p


def _seed(root: Path) -> None:
    out = io.StringIO()
    err = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = progress.main(
            [
                "--root", str(root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    if code != 0:
        raise RuntimeError(f"seed init failed: {err.getvalue()}")


def _append_synthetic_advance(root: Path, *, summary: str) -> None:
    history_path = root / "progress-history.md"
    progress_path = root / "progress.md"

    advance_ts = progress._utc_now_iso()
    entry = HistoryEntry(
        timestamp=advance_ts,
        event=_TEST_ADVANCE_EVENT,
        summary=summary,
        agent="test/forge",
        result="forged for Phase 6.4 testing",
        next=None,
        raw="",
    )
    history_path.write_text(
        append_history_text(
            history_path.read_text(encoding="utf-8"), entry,
        ),
        encoding="utf-8",
    )
    doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
    new_fm = dict(doc.frontmatter)
    for token in summary.split():
        if "=" not in token:
            continue
        key, _, value = token.partition("=")
        if key in {"current_stage", "sub_state"}:
            new_fm[key] = value
        elif key == "review_iteration":
            new_fm[key] = int(value)
        elif key == "task_states":
            kv: dict[str, str] = {}
            for piece in value.split(";"):
                if not piece:
                    continue
                tid, _, status = piece.partition(":")
                kv[tid] = status
            new_fm["development_state"] = {"task_states": kv}
        elif key == "bug_flow_active":
            new_fm["bug_flow"] = {
                "active": value == "true",
                "bug_report_path": (
                    "docs/bug/BUG-099.md" if value == "true" else None
                ),
                "root_cause": "srs" if value == "true" else None,
            }
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


def _seed_at(
    root: Path,
    *,
    current_stage: str,
    sub_state: str,
    task_states: dict[str, str] | None = None,
    bug_flow_active: bool = False,
) -> None:
    _seed(root)
    summary = (
        f"test-stage-advance current_stage={current_stage} sub_state={sub_state}"
    )
    if task_states is not None:
        token = ";".join(f"{tid}:{s}" for tid, s in sorted(task_states.items()))
        summary += f" task_states={token}"
    if bug_flow_active:
        summary += " bug_flow_active=true"
    _append_synthetic_advance(root, summary=summary)


def _test_report_fm(verification_status: str = "pass") -> dict:
    return {
        "title": "Test Report 0.1",
        "type": "test-report",
        "status": "review-passed",
        "created": "2026-09-01T09:00:00Z",
        "updated": "2026-09-01T09:00:00Z",
        "owner": "claude-opus-4-7/testing-write",
        "release": "0.1",
        "verification_status": verification_status,
        "total_test_cases": 5,
        "passed": 5 if verification_status == "pass" else 3,
        "failed": 0 if verification_status == "pass" else 2,
    }


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 11, 1, 12, 0, 0, tzinfo=timezone.utc)

    def __call__(self) -> str:
        ts = self._cursor.strftime("%Y-%m-%dT%H:%M:%SZ")
        self._cursor += timedelta(seconds=1)
        return ts


class _CliRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()
        self._clock = _FakeClock()
        self._clock_patch = patch.object(
            progress, "_utc_now_iso", side_effect=self._clock,
        )
        self._clock_patch.start()

    def tearDown(self) -> None:
        self._clock_patch.stop()
        self._tmp.cleanup()

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            try:
                code = progress.main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def _read_progress_fm(self) -> dict:
        return parse_frontmatter(
            (self.root / "progress.md").read_text(encoding="utf-8")
        ).frontmatter


# ---------- argparse / mutex group ----------


class AdvanceArgparseTests(_CliRunner):
    def test_help_runs(self):
        code, out, _ = self._run(["update", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--advance", out)

    def test_advance_with_event_mutex_returns_2(self):
        code, _, err = self._run(
            ["update", "--advance", "--event", "write-complete"]
        )
        self.assertEqual(code, 2)
        self.assertIn("not allowed with", err.lower())

    def test_advance_with_task_mutex_returns_2(self):
        code, _, err = self._run(
            ["update", "--advance", "--task", "T1"]
        )
        self.assertEqual(code, 2)
        self.assertIn("not allowed with", err.lower())


# ---------- happy paths (validate_doc mocked to short-circuit doc-guardian) ----------


class AdvanceHappyTests(_CliRunner):
    """Happy-path advances. We patch ``progress.validate_doc`` to a
    no-op (returns []) so we can test the P6 forward-path control flow
    without building every doc-guardian-compliant frontmatter. Real
    doc-guardian integration is covered by test_validate_consistency.py.
    """

    def _stub_validate(self):
        return patch.object(progress, "validate_doc", return_value=[])

    def test_advance_prd_to_srs(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            # PRD required artifact must exist for A dim.
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "srs-specification")
            self.assertEqual(fm["sub_state"], "write")
            self.assertEqual(fm["review_iteration"], 0)

    def test_advance_development_to_testing_with_all_tasks_verified(self):
        with _install_test_stage_advance_handler():
            _seed_at(
                self.root,
                current_stage="development",
                sub_state="write",
                task_states={"T1": "verified", "T2": "verified"},
            )
            # Stage 4 development_stage_level required artifacts +
            # per-task artifacts must exist (4 per task).
            for rel in (
                "docs/release0.1/development/plan.md",
                "docs/release0.1/development/breakdown.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            for tid in ("T1", "T2"):
                for f in (
                    "detailed_design.md", "test_review_report.md",
                    "code_review_report.md", "verification_result.md",
                ):
                    _write_doc(
                        self.root,
                        f"docs/release0.1/development/tasks/{tid}/{f}",
                        {"placeholder": True},
                    )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 0, err)
            self.assertEqual(self._read_progress_fm()["current_stage"], "testing")

    def test_advance_testing_to_delivery_with_passing_test_report(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="testing", sub_state="review-passed")
            for rel in (
                "docs/release0.1/testing/preparation.md",
                "docs/release0.1/testing/procedure.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="pass"),
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 0, err)
            self.assertEqual(self._read_progress_fm()["current_stage"], "delivery")

    def test_advance_delivery_to_retrospective_with_passing_installation_result(self):
        # Round 2 H1 regression: delivery -> project-retrospective
        # requires installation-result.verification_status==pass. Before
        # the H1 fix, _check_p6_dim_e raised "unknown doc_type:
        # 'installation-result'" because _PATH_TEMPLATES didn't list it.
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="delivery", sub_state="review-passed")
            for rel in (
                "docs/release0.1/delivery/deployment.md",
                "docs/release0.1/delivery/operation_manual.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/delivery/installation_result.md",
                {
                    "title": "Installation Result 0.1",
                    "type": "installation-result",
                    "status": "review-passed",
                    "created": "2026-09-01T09:00:00Z",
                    "updated": "2026-09-01T09:00:00Z",
                    "owner": "claude-opus-4-7/delivery-write",
                    "release": "0.1",
                    "verification_status": "pass",
                },
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                self._read_progress_fm()["current_stage"],
                "project-retrospective",
            )


# ---------- A reject (artifact missing) ----------


class AdvanceDimensionATests(_CliRunner):
    def test_missing_required_artifact_rejects_with_path_listed(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            # No PRD on disk — A dim must reject before B/E.
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                ["--root", str(self.root), "update", "--advance"]
            )
            self.assertEqual(code, 1)
            self.assertIn("dimension A", err)
            self.assertIn("docs/prd/prd.md", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_missing_artifact_lists_all_misses(self):
        with _install_test_stage_advance_handler():
            _seed_at(
                self.root, current_stage="testing", sub_state="review-passed",
            )
            # No testing artifacts at all.
            code, _, err = self._run(
                ["--root", str(self.root), "update", "--advance"]
            )
            self.assertEqual(code, 1)
            self.assertIn("preparation.md", err)
            self.assertIn("procedure.md", err)
            self.assertIn("report.md", err)


# ---------- B reject (validate_doc returns issues) ----------


class AdvanceDimensionBTests(_CliRunner):
    def test_doc_guardian_rejection_blocks_advance(self):
        def fake_validate(path: str, root: Path) -> list[str]:
            if path.endswith("prd.md"):
                return ["Class 4 (Format): forged failure"]
            return []

        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            with patch.object(progress, "validate_doc", side_effect=fake_validate):
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("dimension B", err)
            self.assertIn("forged failure", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


# ---------- E reject (verification_status != pass) ----------


class AdvanceDimensionETests(_CliRunner):
    def _stub_validate(self):
        return patch.object(progress, "validate_doc", return_value=[])

    def test_testing_advance_rejects_with_failing_test_report(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="testing", sub_state="review-passed")
            for rel in (
                "docs/release0.1/testing/preparation.md",
                "docs/release0.1/testing/procedure.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="fail"),
            )
            with self._stub_validate():
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("dimension E", err)
            self.assertIn("verification_status", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_testing_advance_rejects_with_partial_test_report(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="testing", sub_state="review-passed")
            for rel in (
                "docs/release0.1/testing/preparation.md",
                "docs/release0.1/testing/procedure.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="partial"),
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("dimension E", err)

    def test_delivery_advance_rejects_with_failing_installation_result(self):
        # Round 2 H1 regression: delivery E dim must catch a non-pass
        # installation-result and reject before mutation.
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="delivery", sub_state="review-passed")
            for rel in (
                "docs/release0.1/delivery/deployment.md",
                "docs/release0.1/delivery/operation_manual.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/delivery/installation_result.md",
                {
                    "title": "Installation Result 0.1",
                    "type": "installation-result",
                    "status": "review-passed",
                    "created": "2026-09-01T09:00:00Z",
                    "updated": "2026-09-01T09:00:00Z",
                    "owner": "claude-opus-4-7/delivery-write",
                    "release": "0.1",
                    "verification_status": "fail",
                },
            )
            with self._stub_validate():
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("dimension E", err)
            self.assertIn("verification_status", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


# ---------- state-machine rejects (apply layer) ----------


class AdvanceStateMachineRejectionTests(_CliRunner):
    def _stub_validate(self):
        return patch.object(progress, "validate_doc", return_value=[])

    def test_testing_with_active_bug_flow_blocks_advance(self):
        with _install_test_stage_advance_handler():
            _seed_at(
                self.root,
                current_stage="testing",
                sub_state="review-passed",
                bug_flow_active=True,
            )
            for rel in (
                "docs/release0.1/testing/preparation.md",
                "docs/release0.1/testing/procedure.md",
            ):
                _write_doc(self.root, rel, {"placeholder": True})
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="pass"),
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("bug_flow.active=true", err)

    def test_advance_from_retrospective_rejects_with_release_close_hint(self):
        with _install_test_stage_advance_handler():
            _seed_at(
                self.root,
                current_stage="project-retrospective",
                sub_state="review-passed",
            )
            # Even with retro doc on disk, advance should not work from
            # the terminal stage — caller must use release-close.
            _write_doc(
                self.root, "docs/retrospective/retrospective.md",
                {"placeholder": True},
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("release-close", err)

    def test_gated_stage_rejects_with_review_passed_substate(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="review-passed")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            with self._stub_validate():
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("approved", err)


# ---------- recover roundtrip ----------


class AdvanceRecoverRoundtripTests(_CliRunner):
    def test_recover_after_advance_preserves_state(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            with patch.object(progress, "validate_doc", return_value=[]):
                self.assertEqual(
                    self._run(
                        ["--root", str(self.root), "update", "--advance"]
                    )[0], 0,
                )
            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
        self.assertEqual(code, 0, err)
        after_fm = self._read_progress_fm()
        self.assertEqual(after_fm["current_stage"], "srs-specification")
        self.assertEqual(after_fm["sub_state"], "write")
        self.assertEqual(after_fm["review_iteration"], 0)
        self.assertEqual(
            after_fm["current_stage"], before_fm["current_stage"],
        )


# ---------- lock blocking ----------


class AdvanceLockedStatePreflightTests(_CliRunner):
    """Round 2 M1 regression: P6 A/B/E must run against the LOCKED
    re-read of progress.md, not a pre-lock unlocked read. Before the
    round 2 refactor, _do_update_advance read progress.md outside the
    lock, ran A/B/E against that snapshot, then entered
    _run_update_pipeline which re-acquired the lock and re-read
    progress.md. A parallel agent mutating progress.md between the two
    reads could make the advance bypass P6 for the new stage.

    These tests exercise the new compute_outcome lambda's
    _run_p6_advance_preflight call to prove P6 runs against the locked
    state.
    """

    def test_p6_dim_a_runs_against_locked_state(self):
        # State setup: development with all tasks verified, but NO
        # development required artifacts on disk. apply_update_advance
        # alone would succeed (T1 verified satisfies surrogate); only
        # the locked-state P6 dim A catches the missing artifacts.
        with _install_test_stage_advance_handler():
            _seed_at(
                self.root,
                current_stage="development",
                sub_state="write",
                task_states={"T1": "verified"},
            )
            # Intentionally no docs/release0.1/development/plan.md etc.
            with patch.object(progress, "validate_doc", return_value=[]):
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            # P6 dim A should fire and reject; if P6 didn't run, apply
            # would let the advance proceed (T1 verified).
            self.assertEqual(code, 1)
            self.assertIn("dimension A", err)
            # All 6 expected missing dev artifacts listed (2 stage-level
            # + 4 per-task for T1).
            self.assertIn("plan.md", err)
            self.assertIn("breakdown.md", err)
            self.assertIn("detailed_design.md", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_p6_uses_locked_progress_md_not_stale_snapshot(self):
        # Round 2 M1 regression: drive home the locked-state contract.
        # We patch progress_lock to mutate progress.md when it acquires
        # the lock — simulating a parallel mutation between any
        # hypothetical pre-lock read and the lock entry. If P6 had
        # been reading the unlocked state, it would still see the old
        # state X. Now P6 must observe the post-mutation state Y and
        # reject because state Y has no required artifacts on disk.
        from skills._shared.dev_workflow import progress_lock as lock_module

        with _install_test_stage_advance_handler():
            # State X: prd-inception/approved with PRD on disk → P6 would
            # have passed for X.
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )

            # State Y: forge progress.md to development/write with
            # T1 verified BUT no development artifacts on disk. P6
            # against Y must fail (dev artifacts missing); apply
            # against Y would otherwise succeed.
            def _mutate_progress_md_to_state_y(self_root: Path = self.root):
                doc = parse_frontmatter(
                    (self_root / "progress.md").read_text(encoding="utf-8")
                )
                fm = dict(doc.frontmatter)
                fm["current_stage"] = "development"
                fm["sub_state"] = "write"
                fm["development_state"] = {"task_states": {"T1": "verified"}}
                (self_root / "progress.md").write_text(
                    render_markdown(fm, doc.body), encoding="utf-8",
                )

            real_lock = lock_module.progress_lock

            @contextlib.contextmanager
            def _spy_lock(lock_root, *, timeout):
                # Mutate progress.md AFTER lock acquisition, so any
                # post-lock re-read sees state Y.
                with real_lock(lock_root, timeout=timeout) as held:
                    _mutate_progress_md_to_state_y()
                    yield held

            with patch.object(progress, "progress_lock", _spy_lock):
                with patch.object(progress, "validate_doc", return_value=[]):
                    code, _, err = self._run(
                        ["--root", str(self.root), "update", "--advance"]
                    )
            # P6 sees state Y (development, no artifacts) → reject.
            # If P6 had run against state X (prd-inception with PRD), it
            # would have passed and the apply layer would then have
            # advanced based on state X — the bug.
            self.assertEqual(code, 1)
            self.assertIn("dimension A", err)
            self.assertIn("plan.md", err)


class AdvanceMalformedProgressTests(_CliRunner):
    """Round 2 M2 regression: malformed-but-parseable progress.md must
    convert resolver KeyError/TypeError/AttributeError into a clean
    exit-1 diagnostic rather than a Python traceback. The mirror of
    test_validate_consistency.StructurallyIncompleteProgressTests on
    the progress.py side."""

    def test_missing_scenario_field_returns_exit_1_with_clean_message(self):
        # Init normally then strip the scenario field from progress.md.
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            doc = parse_frontmatter(
                (self.root / "progress.md").read_text(encoding="utf-8")
            )
            fm = dict(doc.frontmatter)
            del fm["scenario"]
            (self.root / "progress.md").write_text(
                render_markdown(fm, doc.body), encoding="utf-8",
            )
            with patch.object(progress, "validate_doc", return_value=[]):
                code, _, err = self._run(
                    ["--root", str(self.root), "update", "--advance"]
                )
            self.assertEqual(code, 1)
            self.assertIn("structurally incomplete", err)


class AdvanceLockTests(_CliRunner):
    def test_lock_blocks_advance(self):
        with _install_test_stage_advance_handler():
            _seed_at(self.root, current_stage="prd-inception", sub_state="approved")
            _write_doc(
                self.root, "docs/prd/prd.md",
                {"title": "PRD", "type": "prd"},
            )
            from skills._shared.dev_workflow.progress_lock import progress_lock

            with progress_lock(self.root, timeout=1.0):
                with patch.object(progress, "validate_doc", return_value=[]):
                    code, _, err = self._run(
                        [
                            "--root", str(self.root),
                            "--lock-timeout", "0.1",
                            "update", "--advance",
                        ]
                    )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
