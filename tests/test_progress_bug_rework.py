"""CLI integration tests for progress.py bug-rework (Phase 6.2 / Gap-5).

These tests exercise the same forge pattern used by Phase 6.1
``test_progress_bug_flow.py``: ``_install_test_stage_advance_handler``
+ ``_FakeClock`` patch lets us drive the project from a fresh init
through ``bug-start`` → simulated retest fail/partial →
``bug-rework`` without depending on Phase 6.4's ``update --advance``.
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


# ---------- test-only handler / fixtures (mirror Phase 6.1) ----------


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


def _test_report_fm(verification_status: str = "fail") -> dict:
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
        result="forged for Phase 6.2 testing",
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
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


def _seed_testing_review_passed(root: Path) -> None:
    _seed(root)
    _append_synthetic_advance(
        root,
        summary="test-stage-advance current_stage=testing sub_state=review-passed",
    )


def _seed_testing_review_passed_with_dev_tasks(
    root: Path, task_states: dict[str, str],
) -> None:
    _seed(root)
    task_token = ";".join(f"{tid}:{s}" for tid, s in sorted(task_states.items()))
    _append_synthetic_advance(
        root,
        summary=(
            "test-stage-advance current_stage=testing sub_state=review-passed "
            f"task_states={task_token}"
        ),
    )


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 9, 15, 12, 0, 0, tzinfo=timezone.utc)

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

    # Helper: drive bug-start, then forge state back to testing/review-passed
    # (simulating retest having run) and write a failing test report.
    def _bring_active_bug_flow_to_retest_failed(
        self,
        *,
        root_cause: str,
        bug_id: str = "BUG-200",
        verification_status: str = "fail",
        bug_body: str | None = None,
        task_states: dict[str, str] | None = None,
    ) -> str:
        bug_rel = f"docs/bug/{bug_id}.md"
        with _install_test_stage_advance_handler():
            if task_states is not None:
                _seed_testing_review_passed_with_dev_tasks(self.root, task_states)
            else:
                _seed_testing_review_passed(self.root)
            body = bug_body or "Body.\n"
            _write_doc(
                self.root, bug_rel,
                _bug_fm(bug_id, root_cause=root_cause),
                body=body,
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start",
                        "--bug", bug_rel,
                        "--root-cause", root_cause,
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
                _test_report_fm(verification_status=verification_status),
            )
        return bug_rel


# ---------- argparse / smoke ----------


class BugReworkArgparseTests(_CliRunner):
    def test_help_runs(self):
        code, out, _ = self._run(["bug-rework", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--bug", out)

    def test_missing_bug_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            code, _, err = self._run(
                ["--root", str(self.root), "bug-rework"]
            )
            self.assertEqual(code, 2)
            self.assertIn("--bug", err)


# ---------- Happy paths ----------


class BugReworkHappyTests(_CliRunner):
    def test_srs_root_cause_reroutes_back_to_srs_specification(self):
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-201",
        )
        with _install_test_stage_advance_handler():
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "srs-specification")
            self.assertEqual(fm["sub_state"], "write")
            self.assertEqual(fm["review_iteration"], 0)
            # bug_flow stays active and unchanged.
            self.assertEqual(
                fm["bug_flow"],
                {
                    "active": True,
                    "bug_report_path": bug_rel,
                    "root_cause": "srs",
                },
            )

    def test_architecture_root_cause_reroutes_back_to_architecture_design(self):
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="architecture", bug_id="BUG-202",
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "architecture-design")
            self.assertEqual(fm["bug_flow"]["root_cause"], "architecture")

    def test_partial_verification_status_also_accepted(self):
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-203",
            verification_status="partial",
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertEqual(
                self._read_progress_fm()["current_stage"], "srs-specification",
            )

    def test_development_with_test_only_classification_rolls_back_T1(self):
        body = (
            "# BUG-204\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: T1\n\n"
            "Root cause: missing test coverage; this is test-only.\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-204",
            bug_body=body,
            task_states={"T1": "verified", "T2": "test-done"},
        )
        with _install_test_stage_advance_handler():
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
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
        body = (
            "# BUG-205\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: T1, T3\n\n"
            "Root cause: source-code logic error in the implementation.\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-205",
            bug_body=body,
            task_states={"T1": "verified", "T3": "code-review-passed"},
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(
                fm["development_state"]["task_states"],
                {"T1": "code-revising", "T3": "code-revising"},
            )

    def test_development_ambiguous_classification_skips_rollback(self):
        body = (
            "# BUG-206\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: T1\n\n"
            "We are not sure where the issue lies; needs deeper analysis.\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-206",
            bug_body=body,
            task_states={"T1": "verified"},
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("ambiguous", err)
            # T1 still verified — ambiguous classification means no
            # auto-rollback per spec.
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "verified"},
            )

    def test_development_unable_to_localize_warns(self):
        body = (
            "# BUG-207\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: unable to localize\n\n"
            "Will require planning re-route.\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-207",
            bug_body=body,
            task_states={"T1": "verified"},
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("unable to localize", err)
            self.assertIn("development-planning-write", err)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "verified"},
            )


class PlanningRoutePersistenceTests(_CliRunner):
    """Mirror Phase 6.1 round 2 review L1: dev root cause with empty
    rollback must persist a planning-route token in
    progress-history (history_result + history_next) so a future agent
    reading only the history can see the routing requirement."""

    def _read_latest_bug_rework_entry(self):
        history_text = (self.root / "progress-history.md").read_text(
            encoding="utf-8",
        )
        entries = parse_history_text(history_text)
        events = [e for e in entries if e.event == "bug-rework"]
        return events[-1] if events else None

    def test_unable_to_localize_persists_planning_route_in_history(self):
        body = (
            "# BUG-300\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: unable to localize\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-300",
            bug_body=body,
            task_states={"T1": "verified"},
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            entry = self._read_latest_bug_rework_entry()
            self.assertIsNotNone(entry)
            self.assertIn("development-planning-write", entry.result)
            self.assertIn("route=", entry.result)
            self.assertIn("development-planning-write", entry.next)


# ---------- Rejections ----------


class BugReworkRejectionTests(_CliRunner):
    def test_no_active_bug_flow_rejects(self):
        # Plain init + forge to testing/review-passed, but no bug-start.
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-301.md",
                _bug_fm("BUG-301", root_cause="srs"),
            )
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="fail"),
            )
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", "docs/bug/BUG-301.md",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("not active", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_bug_path_must_match_active_bug_flow(self):
        bug_rel_active = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-302",
        )
        # Try to rework a different BUG.
        _write_doc(
            self.root, "docs/bug/BUG-303.md",
            _bug_fm("BUG-303", root_cause="srs"),
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", "docs/bug/BUG-303.md",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("does not match", err)

    def test_passing_test_report_rejects(self):
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-304",
            verification_status="pass",
        )
        with _install_test_stage_advance_handler():
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("verification_status", err)
            self.assertIn("bug-close", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_missing_test_report_rejects(self):
        # Active bug flow at testing/review-passed, but no test-report
        # written (e.g. retest never ran).
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-305.md",
                _bug_fm("BUG-305", root_cause="srs"),
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start", "--bug", "docs/bug/BUG-305.md",
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
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", "docs/bug/BUG-305.md",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("test-report", err)

    def test_bug_root_cause_mismatch_rejects(self):
        # Active bug_flow has root_cause=srs, but the BUG file's
        # frontmatter root_cause was edited out-of-band to architecture.
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-306",
        )
        # Mutate the on-disk BUG to have a different root_cause; we
        # must reject before opening the pipeline.
        bug_path = self.root / bug_rel
        existing_text = bug_path.read_text(encoding="utf-8")
        bug_path.write_text(
            existing_text.replace("root_cause: srs", "root_cause: architecture"),
            encoding="utf-8",
        )
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("root_cause", err)

    def test_invalid_bug_path_shape_rejects(self):
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", "/etc/passwd",
                ]
            )
            self.assertEqual(code, 1)

    def test_non_testing_stage_rejects(self):
        # bug-start sets current_stage to root_cause stage; without
        # forging back to testing, bug-rework must reject.
        with _install_test_stage_advance_handler():
            _seed_testing_review_passed(self.root)
            _write_doc(
                self.root, "docs/bug/BUG-307.md",
                _bug_fm("BUG-307", root_cause="srs"),
            )
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-start", "--bug", "docs/bug/BUG-307.md",
                        "--root-cause", "srs",
                    ]
                )[0], 0,
            )
            # State is now srs-specification/write — write a failing
            # report and try bug-rework. bug-rework requires testing.
            _write_doc(
                self.root, "docs/release0.1/testing/report.md",
                _test_report_fm(verification_status="fail"),
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", "docs/bug/BUG-307.md",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("testing", err)


# ---------- M1 / replay roundtrip ----------


class BugReworkRecoverRoundtripTests(_CliRunner):
    def test_recover_after_bug_rework_preserves_state(self):
        # Active bug_flow + bug-rework + recover: replay must reproduce
        # the same bug_flow + current_stage + dev rollback state.
        body = (
            "# BUG-400\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: T1\n\n"
            "Root cause: source-code logic error.\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-400",
            bug_body=body,
            task_states={"T1": "verified"},
        )
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-rework", "--bug", bug_rel,
                    ]
                )[0], 0,
            )
            before_fm = self._read_progress_fm()

            # Delete progress.md and recover from history alone.
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
            self.assertEqual(code, 0, err)
            after_fm = self._read_progress_fm()

        self.assertEqual(after_fm["bug_flow"], before_fm["bug_flow"])
        self.assertEqual(after_fm["current_stage"], "development")
        self.assertEqual(after_fm["sub_state"], "write")
        self.assertEqual(
            after_fm["development_state"]["task_states"],
            before_fm["development_state"]["task_states"],
        )

    def test_recover_with_dev_planning_route_token(self):
        # Empty rollback dev case must replay identical history_result
        # / history_next via apply_bug_rework's deterministic branch.
        body = (
            "# BUG-401\n\n"
            "## Triage Analysis\n\n"
            "**Affected Task(s)**: unable to localize\n"
        )
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="development", bug_id="BUG-401",
            bug_body=body,
            task_states={"T1": "verified"},
        )
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "bug-rework", "--bug", bug_rel,
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

        self.assertEqual(after_fm["current_stage"], "development")
        self.assertEqual(after_fm["bug_flow"], before_fm["bug_flow"])


class BugReworkM1Tests(_CliRunner):
    def test_out_of_band_progress_edit_rejected_by_pipeline(self):
        # Forge state to retest fail/partial, then hand-edit
        # progress.md to flip current_stage. M1 (replay vs forward
        # diff) must reject the bug-rework atomically.
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-500",
        )
        progress_path = self.root / "progress.md"
        text = progress_path.read_text(encoding="utf-8")
        progress_path.write_text(
            text.replace("current_stage: testing", "current_stage: development"),
            encoding="utf-8",
        )

        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-rework", "--bug", bug_rel,
                ]
            )
            # Either pipeline pre-flight catches "non-testing" via the
            # bug_flow.active check + current_stage gate, OR M1 replay
            # diff catches it. Either way the command must fail and not
            # mutate progress.md.
            self.assertEqual(code, 1)


# ---------- Lock blocking ----------


class BugReworkLockTests(_CliRunner):
    def test_lock_blocks_bug_rework(self):
        bug_rel = self._bring_active_bug_flow_to_retest_failed(
            root_cause="srs", bug_id="BUG-600",
        )
        from skills._shared.dev_workflow.progress_lock import progress_lock

        with _install_test_stage_advance_handler():
            with progress_lock(self.root, timeout=1.0):
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "--lock-timeout", "0.1",
                        "bug-rework", "--bug", bug_rel,
                    ]
                )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
