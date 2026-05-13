"""CLI integration tests for progress.py bug-start / bug-close + Gap-3.

Phase 6.1 has no public CLI to drive ``current_stage`` from
``prd-inception`` to ``testing/review-passed`` (advance is Phase 6.4),
so tests forge state via a synthetic ``test-stage-advance`` replay
handler — same pattern as Phase 5.3 / 5.4. The forge keeps progress.md
and progress-history.md aligned so the M1 replay-consistency check
(introduced in Phase 5.2 round 2) does not false-fail.
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
        # task_states=T1:verified;T2:code-review-passed
        kv: dict[str, str] = {}
        for piece in tokens["task_states"].split(";"):
            if not piece:
                continue
            tid, _, status = piece.partition(":")
            kv[tid] = status
        new_state["development_state"] = {"task_states": kv}
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


def _bug_fm(bug_id: str, *, root_cause: str = "srs", **extra) -> dict:
    fm = {
        "title": f"BUG report {bug_id}",
        "type": "bug-report",
        "status": "draft",
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-09-01T10:00:00Z",
        "owner": "claude-opus-4-7/testing-write",
        "bug_id": bug_id,
        "found_in_release": "0.1",
        "target_release": None,
        "root_cause": root_cause,
        "consumed_in_release": None,
    }
    fm.update(extra)
    return fm


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


def _verification_result_fm(
    *, task_id: str, verification_status: str = "fail"
) -> dict:
    return {
        "title": f"{task_id} Verification Result",
        "type": "verification-result",
        "status": "draft",
        "created": "2026-09-01T11:00:00Z",
        "updated": "2026-09-01T11:00:00Z",
        "owner": "claude-opus-4-7/development-code-write",
        "release": "0.1",
        "task_id": task_id,
        "verification_status": verification_status,
    }


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
        result="forged for Phase 6.1 testing",
        next=None,
        raw="",
    )
    history_path.write_text(
        append_history_text(
            history_path.read_text(encoding="utf-8"), entry,
        ),
        encoding="utf-8",
    )
    # Mirror summary mutations into progress.md.
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
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


def _seed_testing_review_passed(root: Path) -> None:
    """Seed init + forge state to ``testing / review-passed`` (Stage 5
    just completed, ready for bug-start)."""

    _seed(root)
    _append_synthetic_advance(
        root,
        summary="test-stage-advance current_stage=testing sub_state=review-passed",
    )


def _seed_testing_review_passed_with_dev_tasks(
    root: Path, task_states: dict[str, str],
) -> None:
    """Seed + forge testing/review-passed AND populate development_state.task_states.

    The forged advance encodes both stage/sub_state and the per-task map
    so replay reconstructs the same state.
    """

    _seed(root)
    task_token = ";".join(f"{tid}:{s}" for tid, s in sorted(task_states.items()))
    _append_synthetic_advance(
        root,
        summary=(
            "test-stage-advance current_stage=testing sub_state=review-passed "
            f"task_states={task_token}"
        ),
    )


def _seed_development_with_task(
    root: Path, *, task_id: str, status: str,
) -> None:
    """Seed + forge state to development with one task in the given status."""

    _seed(root)
    _append_synthetic_advance(
        root,
        summary=(
            "test-stage-advance current_stage=development sub_state=write "
            f"task_states={task_id}:{status}"
        ),
    )


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 9, 1, 12, 0, 0, tzinfo=timezone.utc)

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


# ---------- bug-start ----------


class BugStartArgparseTests(_CliRunner):
    def test_help_runs(self):
        code, out, _ = self._run(["bug-start", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--bug", out)
        self.assertIn("--root-cause", out)

    def test_missing_bug_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            code, _, err = self._run(
                ["--root", str(self.root), "bug-start", "--root-cause", "srs"]
            )
            self.assertEqual(code, 2)
            self.assertIn("--bug", err)

    def test_missing_root_cause_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start", "--bug", "docs/bug/BUG-001.md",
                ]
            )
            self.assertEqual(code, 2)
            self.assertIn("--root-cause", err)


class BugStartHappyTests(_CliRunner):
    def test_srs_root_cause_routes_to_srs_specification(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001", root_cause="srs"))
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "srs-specification")
            self.assertEqual(fm["sub_state"], "write")
            self.assertEqual(fm["review_iteration"], 0)
            self.assertEqual(
                fm["bug_flow"],
                {
                    "active": True,
                    "bug_report_path": "docs/bug/BUG-001.md",
                    "root_cause": "srs",
                },
            )

    def test_architecture_root_cause_routes_to_architecture_design(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root,
                "docs/bug/BUG-002.md",
                _bug_fm("BUG-002", root_cause="architecture"),
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-002.md",
                    "--root-cause", "architecture",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                self._read_progress_fm()["current_stage"], "architecture-design",
            )

    def test_development_with_test_only_classification_rolls_back_T1(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified", "T2": "test-done"},
            )
            body = (
                "# BUG-003\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: T1\n\n"
                "Root cause: missing test coverage; this is test-only.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-003.md",
                _bug_fm("BUG-003", root_cause="development"),
                body=body,
            )
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-003.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "development")
            self.assertEqual(
                fm["development_state"]["task_states"],
                {"T1": "test-revising", "T2": "test-done"},
            )

    def test_development_source_classification_rolls_back_to_code_revising(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified", "T3": "code-review-passed"},
            )
            body = (
                "# BUG-004\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: T1, T3\n\n"
                "Root cause: source-code logic error in the implementation.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-004.md",
                _bug_fm("BUG-004", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-004.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(
                fm["development_state"]["task_states"],
                {"T1": "code-revising", "T3": "code-revising"},
            )

    def test_development_ambiguous_classification_skips_rollback(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified"},
            )
            body = (
                "# BUG-005\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: T1\n\n"
                "We are not sure where the issue lies; needs deeper analysis.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-005.md",
                _bug_fm("BUG-005", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-005.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            # T1 still verified — ambiguous classification means no
            # auto-rollback per spec.
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "verified"},
            )

    def test_development_unable_to_localize_warns(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified"},
            )
            body = (
                "# BUG-006\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: unable to localize\n\n"
                "Will require planning re-route.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-006.md",
                _bug_fm("BUG-006", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-006.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("unable to localize", err)
            self.assertIn("development-planning-write", err)
            # No rollback applied.
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "verified"},
            )


class PlanningRoutePersistenceTests(_CliRunner):
    """Phase 6.1 round 2 review L1: dev root cause with empty rollback
    must:
      * print stderr warning naming the reason; AND
      * persist a planning-route token in progress-history so a future
        agent reading only the history can see the routing requirement.
    """

    def _read_latest_bug_start_entry(self):
        history_text = (self.root / "progress-history.md").read_text(
            encoding="utf-8",
        )
        entries = parse_history_text(history_text)
        bug_start_entries = [e for e in entries if e.event == "bug-start"]
        return bug_start_entries[-1] if bug_start_entries else None

    def test_unable_to_localize_persists_planning_route_in_history(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified"},
            )
            body = (
                "# BUG-100\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: unable to localize\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-100.md",
                _bug_fm("BUG-100", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-100.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("unable to localize", err)
            entry = self._read_latest_bug_start_entry()
            self.assertIsNotNone(entry)
            self.assertIn("development-planning-write", entry.result)
            self.assertIn("route=", entry.result)
            self.assertIn("development-planning-write", entry.next)

    def test_ambiguous_classification_warns_and_persists_planning_route(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified"},
            )
            body = (
                "# BUG-101\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: T1\n\n"
                "We are not sure where the issue lies; needs deeper analysis.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-101.md",
                _bug_fm("BUG-101", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-101.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("ambiguous", err)
            self.assertIn("development-planning-write", err)
            entry = self._read_latest_bug_start_entry()
            self.assertIn("development-planning-write", entry.result)
            self.assertIn("development-planning-write", entry.next)

    def test_dev_with_no_matching_task_state_persists_planning_route(self):
        # BUG body classifies clearly (test-only) AND names T1, but T1
        # is in test-done (not verified) so no Gap-4 rollback fires.
        # Forward path must still record planning-route persistence.
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "test-done"},
            )
            body = (
                "# BUG-102\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: T1\n\n"
                "Root cause: missing test coverage; test-only fix.\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-102.md",
                _bug_fm("BUG-102", root_cause="development"),
                body=body,
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-102.md",
                    "--root-cause", "development",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("not in a state eligible", err)
            entry = self._read_latest_bug_start_entry()
            self.assertIn("development-planning-write", entry.result)

    def test_recover_replay_preserves_planning_route_token(self):
        # Replay must produce identical history_result (via apply_bug_start)
        # even though it doesn't have triage context. The trigger is
        # purely "dev root cause AND empty rollback".
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed_with_dev_tasks(
                self.root, {"T1": "verified"},
            )
            body = (
                "# BUG-103\n\n"
                "## Triage Analysis\n\n"
                "**Affected Task(s)**: unable to localize\n"
            )
            _write_doc(
                self.root, "docs/bug/BUG-103.md",
                _bug_fm("BUG-103", root_cause="development"),
                body=body,
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start",
                        "--bug", "docs/bug/BUG-103.md",
                        "--root-cause", "development",
                    ]
                )[0], 0,
            )
            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
            self.assertEqual(code, 0, err)
            after_fm = self._read_progress_fm()
            # State machine deterministic — bug_flow active, current_stage
            # back to development.
            self.assertEqual(
                after_fm["bug_flow"], before_fm["bug_flow"]
            )
            self.assertEqual(
                after_fm["current_stage"], "development"
            )


class BugStartMalformedFrontmatterTests(_CliRunner):
    """Phase 6.1 round 2 review M1: bug-start CLI must reject malformed
    BUG frontmatter before opening Bug Flow."""

    def test_bug_id_regex_mismatch_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            fm = _bug_fm("BUG-001", root_cause="srs")
            fm["bug_id"] = "NOTBUG"
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            progress_before = (self.root / "progress.md").read_text(
                encoding="utf-8",
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("BUG-\\d{3}", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_bug_id_stem_mismatch_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            fm = _bug_fm("BUG-001", root_cause="srs")
            fm["bug_id"] = "BUG-999"
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("path stem", err)

    def test_missing_target_release_field_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            fm = _bug_fm("BUG-001", root_cause="srs")
            del fm["target_release"]
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("target_release", err)

    def test_missing_consumed_in_release_field_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            fm = _bug_fm("BUG-001", root_cause="srs")
            del fm["consumed_in_release"]
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("consumed_in_release", err)


class BugStartRejectionTests(_CliRunner):
    def test_active_release_required(self):
        # Plain init: state is prd-inception/write (active release), but
        # current_stage != testing → reject.
        _seed(self.root)
        _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "bug-start",
                "--bug", "docs/bug/BUG-001.md",
                "--root-cause", "srs",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("testing", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )

    def test_bug_root_cause_must_match_arg(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001", root_cause="development"),
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-001.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("root_cause", err)

    def test_missing_bug_file_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "docs/bug/BUG-404.md",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("missing", err)

    def test_invalid_bug_path_shape_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-start",
                    "--bug", "/etc/passwd",
                    "--root-cause", "srs",
                ]
            )
            self.assertEqual(code, 1)


# ---------- bug-close ----------


class BugCloseHappyTests(_CliRunner):
    def _seed_active_bug_flow_with_passing_test_report(self, root_cause: str) -> None:
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001", root_cause=root_cause),
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start",
                        "--bug", "docs/bug/BUG-001.md",
                        "--root-cause", root_cause,
                    ]
                )[0], 0,
            )
            # Forge state back to testing/review-passed (simulating
            # post-fix retest pass — Phase 6.4 advance would do this in
            # production).
            _append_synthetic_advance(
                self.root,
                summary=(
                    "test-stage-advance current_stage=testing "
                    "sub_state=review-passed"
                ),
            )
            # Latest test-report shows pass.
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="pass"),
            )

    def test_bug_close_clears_bug_flow_and_keeps_testing(self):
        self._seed_active_bug_flow_with_passing_test_report("srs")
        with _install_test_stage_advance_handler():
            code, out, err = self._run(
                ["--root", str(self.root), "bug-close"]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(
                fm["bug_flow"],
                {"active": False, "bug_report_path": None, "root_cause": None},
            )
            self.assertEqual(fm["current_stage"], "testing")


class BugCloseRejectionTests(_CliRunner):
    def test_bug_close_without_active_flow_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="pass"),
            )
            code, _, err = self._run(
                ["--root", str(self.root), "bug-close"]
            )
            self.assertEqual(code, 1)
            self.assertIn("not active", err)

    def test_bug_close_with_failing_test_report_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001", root_cause="srs"),
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start", "--bug", "docs/bug/BUG-001.md",
                        "--root-cause", "srs",
                    ]
                )[0], 0,
            )
            _append_synthetic_advance(
                self.root,
                summary=(
                    "test-stage-advance current_stage=testing "
                    "sub_state=review-passed"
                ),
            )
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="fail"),
            )
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                ["--root", str(self.root), "bug-close"]
            )
            self.assertEqual(code, 1)
            self.assertIn("verification_status", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_bug_close_without_test_report_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001", root_cause="srs"),
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start", "--bug", "docs/bug/BUG-001.md",
                        "--root-cause", "srs",
                    ]
                )[0], 0,
            )
            _append_synthetic_advance(
                self.root,
                summary=(
                    "test-stage-advance current_stage=testing "
                    "sub_state=review-passed"
                ),
            )
            # No test-report on disk.
            code, _, err = self._run(
                ["--root", str(self.root), "bug-close"]
            )
            self.assertEqual(code, 1)
            self.assertIn("test-report", err)


# ---------- Gap-3 update --task verifying -> code-revising ----------


class Gap3UpdateTaskTests(_CliRunner):
    def test_gap3_with_failing_verification_succeeds(self):
        with _install_test_stage_advance_handler():
            _seed_development_with_task(
                self.root, task_id="T1", status="verifying",
            )
            _write_doc(
                self.root,
                "docs/release0.1/development/tasks/T1/verification_result.md",
                _verification_result_fm(task_id="T1", verification_status="fail"),
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "update", "--task", "T1", "--status", "code-revising",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"]["T1"],
                "code-revising",
            )

    def test_gap3_with_partial_verification_succeeds(self):
        with _install_test_stage_advance_handler():
            _seed_development_with_task(
                self.root, task_id="T1", status="verifying",
            )
            _write_doc(
                self.root,
                "docs/release0.1/development/tasks/T1/verification_result.md",
                _verification_result_fm(task_id="T1", verification_status="partial"),
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "update", "--task", "T1", "--status", "code-revising",
                ]
            )
            self.assertEqual(code, 0, err)

    def test_gap3_with_passing_verification_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_development_with_task(
                self.root, task_id="T1", status="verifying",
            )
            _write_doc(
                self.root,
                "docs/release0.1/development/tasks/T1/verification_result.md",
                _verification_result_fm(task_id="T1", verification_status="pass"),
            )
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "update", "--task", "T1", "--status", "code-revising",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("Gap-3", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
