"""CLI integration tests for progress.py incident-start / incident-resolve.

Phase 6.3 / PRD-exception incident lifecycle. The tests mirror the
Phase 6.1 / 6.2 forge style: ``_install_test_stage_advance_handler``
+ ``_FakeClock`` patch lets us reach an arbitrary state before
exercising the new commands. doc-guardian's ``validate.py file`` is
imported in-process by progress.py; tests construct genuinely valid
BUG / INCIDENT documents (so happy paths are real end-to-end) and
patch ``progress.validate_doc`` only when forcing the M6 double-safety
reject path.
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


# ---------- test-only handler / fixtures (mirror Phase 6.2) ----------


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


# ---------- valid BUG / INCIDENT fixtures ----------


def _bug_fm_prd_exception(bug_id: str = "BUG-700") -> dict:
    """A frontmatter dict that passes doc-guardian validate.py file
    for a PRD-exception BUG report."""

    return {
        "title": f"BUG report {bug_id}",
        "type": "bug-report",
        "status": "review-passed",
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-09-01T10:00:00Z",
        "owner": "claude-opus-4-7/bug-triage",
        "bug_id": bug_id,
        "found_in_release": "0.1",
        "target_release": None,
        "root_cause": "prd-exception",
        "consumed_in_release": None,
    }


def _incident_fm(
    incident_id: str = "INCIDENT-007",
    *,
    triggered_by_bug: str = "BUG-700",
    resolution_action: str | None = None,
    status: str = "draft",
) -> dict:
    return {
        "title": f"Incident {incident_id}",
        "type": "workflow-incident",
        "status": status,
        "created": "2026-09-01T10:00:00Z",
        "updated": "2026-09-01T10:00:00Z",
        "owner": "claude-opus-4-7/workflow-evolution",
        "incident_id": incident_id,
        "triggered_by_bug": triggered_by_bug,
        "triggered_in_release": "0.1",
        "resolution_action": resolution_action,
    }


# Doc body: validate.py requires Change Log section for incremental docs;
# bug-report and workflow-incident are listed as INCREMENTAL_DOC_TYPES.
_VALID_BODY_WITH_CHANGE_LOG = (
    "# Description\n\nFreshly-promoted doc body.\n\n"
    "## Pending Changes\n\n"
    "## Change Log\n\n"
    "### 2026-05-15\n\n"
    "- 2026-05-15T10:00:00Z [Section 1]: 初始版本\n"
)


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
        result="forged for Phase 6.3 testing",
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
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


def _seed_at_testing_review_passed(root: Path) -> None:
    _seed(root)
    _append_synthetic_advance(
        root,
        summary="test-stage-advance current_stage=testing sub_state=review-passed",
    )


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 10, 1, 12, 0, 0, tzinfo=timezone.utc)

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

    def _seed_pending_incident(
        self,
        *,
        bug_id: str = "BUG-700",
        incident_id: str = "INCIDENT-007",
    ) -> tuple[str, str]:
        """Drop a valid BUG and INCIDENT skeleton onto disk; caller
        invokes incident-start. Returns (bug_rel, incident_rel)."""

        bug_rel = f"docs/bug/{bug_id}.md"
        incident_rel = f"docs/incident/{incident_id}.md"
        _write_doc(
            self.root, bug_rel,
            _bug_fm_prd_exception(bug_id),
            body=_VALID_BODY_WITH_CHANGE_LOG,
        )
        _write_doc(
            self.root, incident_rel,
            _incident_fm(incident_id, triggered_by_bug=bug_id),
            body=_VALID_BODY_WITH_CHANGE_LOG,
        )
        return bug_rel, incident_rel

    def _open_incident(self, bug_id: str = "BUG-700",
                       incident_id: str = "INCIDENT-007") -> tuple[str, str]:
        bug_rel, incident_rel = self._seed_pending_incident(
            bug_id=bug_id, incident_id=incident_id,
        )
        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-start",
                    "--bug", bug_rel,
                    "--report", incident_rel,
                ]
            )
            self.assertEqual(code, 0, err)
        return bug_rel, incident_rel

    def _finalize_incident(
        self, incident_rel: str, *, action: str,
        incident_id: str = "INCIDENT-007", bug_id: str = "BUG-700",
    ) -> None:
        # workflow-evolution Step 6.e/f: write resolution_action +
        # advance status to review-passed.
        fm = _incident_fm(
            incident_id, triggered_by_bug=bug_id,
            resolution_action=action, status="review-passed",
        )
        _write_doc(self.root, incident_rel, fm, body=_VALID_BODY_WITH_CHANGE_LOG)


# ---------- argparse ----------


class IncidentArgparseTests(_CliRunner):
    def test_incident_start_help_runs(self):
        code, out, _ = self._run(["incident-start", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--bug", out)
        self.assertIn("--report", out)

    def test_incident_resolve_help_runs(self):
        code, out, _ = self._run(["incident-resolve", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--action", out)

    def test_incident_start_missing_bug_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, _, err = self._run(
                ["--root", str(self.root), "incident-start",
                 "--report", "docs/incident/INCIDENT-007.md"]
            )
            self.assertEqual(code, 2)
            self.assertIn("--bug", err)

    def test_incident_start_missing_report_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, _, err = self._run(
                ["--root", str(self.root), "incident-start",
                 "--bug", "docs/bug/BUG-700.md"]
            )
            self.assertEqual(code, 2)
            self.assertIn("--report", err)

    def test_incident_resolve_missing_action_returns_2(self):
        code, _, err = self._run(["incident-resolve"])
        self.assertEqual(code, 2)
        self.assertIn("--action", err)

    def test_incident_resolve_invalid_action_returns_1(self):
        # Round 2 L1: supplied-but-invalid --action is a workflow
        # validation error (exit 1), not a CLI usage error (exit 2).
        # This matches release-start --scenario / init --scenario
        # contracts (Phase 5.1 round 2 M2).
        code, _, err = self._run(
            ["incident-resolve", "--action", "retry"]
        )
        self.assertEqual(code, 1)
        self.assertIn("continue / abort / reconstruct", err)


# ---------- incident-start happy paths + rejections ----------


class IncidentStartHappyTests(_CliRunner):
    def test_incident_start_opens_bug_flow_and_incident_state(self):
        bug_rel, incident_rel = self._seed_pending_incident()
        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-start",
                    "--bug", bug_rel,
                    "--report", incident_rel,
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "workflow-incident-analysis")
            self.assertTrue(fm["workflow_incident_active"])
            self.assertEqual(fm["incident_report_path"], incident_rel)
            self.assertEqual(
                fm["bug_flow"],
                {
                    "active": True,
                    "bug_report_path": bug_rel,
                    "root_cause": "prd-exception",
                },
            )


class IncidentStartRejectionTests(_CliRunner):
    def test_active_bug_flow_rejects(self):
        # Open one incident, then try a second one — workflow_incident_active
        # already true must reject.
        self._open_incident()
        with _install_test_stage_advance_handler():
            bug_rel2, incident_rel2 = self._seed_pending_incident(
                bug_id="BUG-701", incident_id="INCIDENT-008",
            )
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-start",
                    "--bug", bug_rel2,
                    "--report", incident_rel2,
                ]
            )
            self.assertEqual(code, 1)
            # Either bug_flow.active=true OR workflow_incident_active=true
            # path triggers; both are valid reject reasons.
            self.assertTrue(
                "already active" in err or "already True" in err,
                f"unexpected stderr: {err!r}",
            )
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_doc_guardian_rejected_BUG_blocks_incident_start(self):
        bug_rel, incident_rel = self._seed_pending_incident()
        # Mock validate_doc to return non-empty for BUG path, empty for
        # INCIDENT (so the BUG reject is the trigger).
        def fake_validate(path: str, root: Path) -> list[str]:
            if path == bug_rel:
                return ["Class 4 (Format): forged failure"]
            return []

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            with patch.object(progress, "validate_doc", side_effect=fake_validate):
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "incident-start",
                        "--bug", bug_rel,
                        "--report", incident_rel,
                    ]
                )
                self.assertEqual(code, 1)
                self.assertIn("doc-guardian rejected BUG", err)
                self.assertEqual(
                    (self.root / "progress.md").read_text(encoding="utf-8"),
                    progress_before,
                )

    def test_doc_guardian_rejected_INCIDENT_blocks_incident_start(self):
        bug_rel, incident_rel = self._seed_pending_incident()
        def fake_validate(path: str, root: Path) -> list[str]:
            if path == incident_rel:
                return ["Class 4 (Format): forged failure"]
            return []

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            with patch.object(progress, "validate_doc", side_effect=fake_validate):
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "incident-start",
                        "--bug", bug_rel,
                        "--report", incident_rel,
                    ]
                )
                self.assertEqual(code, 1)
                self.assertIn("doc-guardian rejected INCIDENT", err)

    def test_bug_root_cause_must_be_prd_exception(self):
        bug_rel = "docs/bug/BUG-702.md"
        incident_rel = "docs/incident/INCIDENT-010.md"
        # BUG with root_cause=srs (not prd-exception) — load_bug_report
        # rejects via expect_root_cause.
        bug_fm = _bug_fm_prd_exception("BUG-702")
        bug_fm["root_cause"] = "srs"
        _write_doc(
            self.root, bug_rel, bug_fm, body=_VALID_BODY_WITH_CHANGE_LOG,
        )
        _write_doc(
            self.root, incident_rel,
            _incident_fm("INCIDENT-010", triggered_by_bug="BUG-702"),
            body=_VALID_BODY_WITH_CHANGE_LOG,
        )

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-start",
                    "--bug", bug_rel,
                    "--report", incident_rel,
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("prd-exception", err)

    def test_triggered_by_bug_mismatch_rejects(self):
        bug_rel = "docs/bug/BUG-703.md"
        incident_rel = "docs/incident/INCIDENT-011.md"
        _write_doc(
            self.root, bug_rel,
            _bug_fm_prd_exception("BUG-703"),
            body=_VALID_BODY_WITH_CHANGE_LOG,
        )
        # INCIDENT.triggered_by_bug points at a different BUG ID.
        _write_doc(
            self.root, incident_rel,
            _incident_fm("INCIDENT-011", triggered_by_bug="BUG-999"),
            body=_VALID_BODY_WITH_CHANGE_LOG,
        )

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-start",
                    "--bug", bug_rel,
                    "--report", incident_rel,
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("triggered_by_bug", err)


# ---------- incident-resolve happy paths ----------


class IncidentResolveHappyTests(_CliRunner):
    def test_continue_clears_incident_and_resumes_testing(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="continue")
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-resolve",
                    "--action", "continue",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["current_stage"], "testing")
            self.assertEqual(fm["sub_state"], "review-passed")
            self.assertEqual(fm["review_iteration"], 0)
            self.assertFalse(fm["workflow_incident_active"])
            self.assertIsNone(fm["incident_report_path"])
            self.assertEqual(
                fm["bug_flow"],
                {"active": False, "bug_report_path": None, "root_cause": None},
            )
            # project_state untouched.
            self.assertEqual(fm["project_state"], "active")
            self.assertEqual(fm["release_state"], "active")
            self.assertIsNone(fm["release_close_reason"])

    def test_abort_freezes_project(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="abort")
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-resolve",
                    "--action", "abort",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["project_state"], "aborted")
            self.assertEqual(fm["release_state"], "closed")
            self.assertEqual(fm["release_close_reason"], "incident-abort")
            self.assertIsNone(fm["current_stage"])
            self.assertIsNone(fm["sub_state"])
            self.assertEqual(fm["review_iteration"], 0)

    def test_reconstruct_freezes_project_with_distinct_reason(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="reconstruct")
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-resolve",
                    "--action", "reconstruct",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["project_state"], "reconstructing")
            self.assertEqual(fm["release_close_reason"], "incident-reconstruct")


class IncidentResolveRejectionTests(_CliRunner):
    def test_no_active_incident_rejects(self):
        # Plain init only; no incident open.
        _seed(self.root)
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "incident-resolve", "--action", "continue",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("workflow_incident_active", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )

    def test_action_mismatch_with_incident_resolution_action_rejects(self):
        _, incident_rel = self._open_incident()
        # workflow-evolution writes resolution_action=continue, but caller
        # invokes --action abort.
        self._finalize_incident(incident_rel, action="continue")
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-resolve", "--action", "abort",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("resolution_action", err)

    def test_incident_status_must_be_review_passed(self):
        _, incident_rel = self._open_incident()
        # workflow-evolution forgot Step 6.f promote — status still draft.
        fm = _incident_fm(
            "INCIDENT-007", triggered_by_bug="BUG-700",
            resolution_action="continue", status="draft",
        )
        _write_doc(self.root, incident_rel, fm, body=_VALID_BODY_WITH_CHANGE_LOG)
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "incident-resolve", "--action", "continue",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("review-passed", err)

    def test_validate_doc_rejection_blocks_resolve(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="continue")

        def fake_validate(path: str, root: Path) -> list[str]:
            return ["Class 4 (Format): forged failure"]

        with _install_test_stage_advance_handler():
            with patch.object(progress, "validate_doc", side_effect=fake_validate):
                progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "continue",
                    ]
                )
                self.assertEqual(code, 1)
                self.assertIn("doc-guardian rejected INCIDENT", err)
                self.assertEqual(
                    (self.root / "progress.md").read_text(encoding="utf-8"),
                    progress_before,
                )


# ---------- M1 round 2: incident-resolve corrupt-path preflight ----------


class IncidentResolveCorruptIncidentPathTests(_CliRunner):
    """Round 2 M1 regression suite. Re-tests below cover corrupted /
    hand-edited progress.md.incident_report_path values:
      * absolute path
      * traversal segments (``..``)
      * non-canonical (wrong directory or 4-digit ID)

    Each must reject with exit 1 BEFORE validate_doc / read_markdown
    touch the filesystem. We assert (a) progress.md is byte-identical
    after the failed attempt, AND (b) validate_doc was never called by
    using a side-effect that would let the test fail loudly if it had
    been invoked.
    """

    def _open_incident_then_corrupt(self, *, corrupted_path: str) -> str:
        """Drive the project to active incident, then mutate
        progress.md.incident_report_path on disk to ``corrupted_path``.
        Returns the corrupted progress.md text so callers can compare."""

        self._open_incident()
        progress_path = self.root / "progress.md"
        text = progress_path.read_text(encoding="utf-8")
        # Replace the persisted incident_report_path. The original is
        # 'docs/incident/INCIDENT-007.md'; YAML emits it as a quoted or
        # bare scalar — try both forms safely.
        marker = "incident_report_path:"
        lines = text.splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.lstrip().startswith(marker):
                # Preserve indentation; replace the value with corrupted_path.
                indent = line[: len(line) - len(line.lstrip())]
                lines[i] = (
                    f"{indent}incident_report_path: {corrupted_path!r}\n"
                )
                break
        progress_path.write_text("".join(lines), encoding="utf-8")
        return progress_path.read_text(encoding="utf-8")

    def _run_resolve_with_validate_spy(self) -> tuple[int, str, str, list[str]]:
        """Run incident-resolve and assert validate_doc is never called.
        Returns (code, stdout, stderr, validate_doc_calls)."""

        calls: list[str] = []

        def spy_validate(path: str, root: Path) -> list[str]:
            calls.append(path)
            return []

        with _install_test_stage_advance_handler():
            with patch.object(progress, "validate_doc", side_effect=spy_validate):
                code, out, err = self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "continue",
                    ]
                )
        return code, out, err, calls

    def test_absolute_incident_path_rejected_before_validate_doc(self):
        progress_after_corruption = self._open_incident_then_corrupt(
            corrupted_path="/etc/passwd",
        )
        code, _, err, validate_calls = self._run_resolve_with_validate_spy()
        self.assertEqual(code, 1)
        # Specifically rejected by the path-shape guard, not by
        # validate_doc (which we asserted was never called).
        self.assertEqual(validate_calls, [])
        self.assertTrue(
            "INCIDENT path" in err or "absolute" in err,
            f"unexpected stderr: {err!r}",
        )
        # progress.md is byte-identical to the corrupted-but-unprocessed
        # state; we did NOT mutate it further.
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_after_corruption,
        )

    def test_traversal_incident_path_rejected_before_validate_doc(self):
        progress_after_corruption = self._open_incident_then_corrupt(
            corrupted_path="docs/../../etc/passwd",
        )
        code, _, err, validate_calls = self._run_resolve_with_validate_spy()
        self.assertEqual(code, 1)
        self.assertEqual(validate_calls, [])
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_after_corruption,
        )

    def test_non_canonical_incident_path_rejected_before_validate_doc(self):
        # Wrong directory (docs/bug instead of docs/incident).
        progress_after_corruption = self._open_incident_then_corrupt(
            corrupted_path="docs/bug/INCIDENT-007.md",
        )
        code, _, err, validate_calls = self._run_resolve_with_validate_spy()
        self.assertEqual(code, 1)
        self.assertEqual(validate_calls, [])
        self.assertIn("INCIDENT path", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_after_corruption,
        )

    def test_four_digit_incident_id_rejected_before_validate_doc(self):
        progress_after_corruption = self._open_incident_then_corrupt(
            corrupted_path="docs/incident/INCIDENT-1000.md",
        )
        code, _, err, validate_calls = self._run_resolve_with_validate_spy()
        self.assertEqual(code, 1)
        self.assertEqual(validate_calls, [])
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_after_corruption,
        )


class IncidentStartCorruptPathPreflightTests(_CliRunner):
    """Round 2 M1 hardening: cmd_incident_start now applies explicit
    canonical-shape checks on resolved BUG / INCIDENT paths BEFORE
    validate_doc reads the files. _resolve_under_root already bounds
    paths under --root, so user-supplied paths can't escape the tree;
    these tests cover the in-tree-but-non-canonical case."""

    def _run_start_with_validate_spy(
        self, *, bug_arg: str, report_arg: str,
    ) -> tuple[int, str, str, list[str]]:
        calls: list[str] = []

        def spy_validate(path: str, root: Path) -> list[str]:
            calls.append(path)
            return []

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            with patch.object(progress, "validate_doc", side_effect=spy_validate):
                code, out, err = self._run(
                    [
                        "--root", str(self.root),
                        "incident-start",
                        "--bug", bug_arg,
                        "--report", report_arg,
                    ]
                )
        return code, out, err, calls

    def test_non_canonical_bug_path_rejected_before_validate_doc(self):
        # In-tree but wrong directory (docs/foo instead of docs/bug).
        # File doesn't need to exist — the shape guard fires first.
        code, _, err, validate_calls = self._run_start_with_validate_spy(
            bug_arg="docs/foo/BUG-700.md",
            report_arg="docs/incident/INCIDENT-007.md",
        )
        self.assertEqual(code, 1)
        self.assertEqual(validate_calls, [])
        self.assertIn("BUG path", err)

    def test_non_canonical_incident_path_rejected_before_validate_doc(self):
        code, _, err, validate_calls = self._run_start_with_validate_spy(
            bug_arg="docs/bug/BUG-700.md",
            report_arg="docs/notes/INCIDENT-007.md",
        )
        self.assertEqual(code, 1)
        self.assertEqual(validate_calls, [])
        self.assertIn("INCIDENT path", err)


# ---------- terminal-state semantics ----------


class TerminalStateSemanticsTests(_CliRunner):
    """After incident-resolve abort/reconstruct, no further mutating
    progress.py command should succeed. query/recover continue to work."""

    def _drive_to_aborted(self) -> str:
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="abort")
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "abort",
                    ]
                )[0], 0,
            )
        return incident_rel

    def test_after_abort_query_still_works(self):
        self._drive_to_aborted()
        code, out, err = self._run(["--root", str(self.root), "query"])
        self.assertEqual(code, 0, err)
        self.assertIn("project_state", out)

    def test_after_abort_recover_still_works(self):
        self._drive_to_aborted()
        # Delete progress.md — recover replays from history. Keep the
        # synthetic test-stage-advance handler installed because the
        # forged advance entries are still in progress-history.md.
        (self.root / "progress.md").unlink()
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
        self.assertEqual(code, 0, err)
        fm = self._read_progress_fm()
        self.assertEqual(fm["project_state"], "aborted")

    def test_after_abort_update_event_rejects(self):
        # apply_update_event has _validate_active_project gate; once
        # project_state=aborted it must refuse.
        self._drive_to_aborted()
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        with _install_test_stage_advance_handler():
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "update", "--event", "write-complete",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("project_state", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_after_reconstruct_bug_intake_rejects(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="reconstruct")
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "reconstruct",
                    ]
                )[0], 0,
            )
            # bug-intake requires project_state==active; reconstructing → reject.
            _write_doc(
                self.root, "docs/bug/BUG-900.md",
                {
                    "title": "BUG-900",
                    "type": "bug-report",
                    "status": "draft",
                    "created": "2026-10-05T10:00:00Z",
                    "updated": "2026-10-05T10:00:00Z",
                    "owner": "claude-opus-4-7/bug-triage",
                    "bug_id": "BUG-900",
                    "found_in_release": "0.1",
                    "target_release": None,
                    "root_cause": None,
                    "consumed_in_release": None,
                },
            )
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "bug-intake", "--bug", "docs/bug/BUG-900.md",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("project_state", err)


# ---------- recover roundtrip ----------


class IncidentRecoverRoundtripTests(_CliRunner):
    def test_recover_after_continue_preserves_state(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="continue")
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "continue",
                    ]
                )[0], 0,
            )
            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            # Keep handler installed: history still has forged advances.
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
        self.assertEqual(code, 0, err)
        after_fm = self._read_progress_fm()
        self.assertEqual(after_fm["bug_flow"], before_fm["bug_flow"])
        self.assertEqual(after_fm["current_stage"], "testing")
        self.assertEqual(after_fm["sub_state"], "review-passed")
        self.assertFalse(after_fm["workflow_incident_active"])

    def test_recover_after_abort_preserves_terminal_fields(self):
        _, incident_rel = self._open_incident()
        self._finalize_incident(incident_rel, action="abort")
        with _install_test_stage_advance_handler():
            self.assertEqual(
                self._run(
                    [
                        "--root", str(self.root),
                        "incident-resolve", "--action", "abort",
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
        self.assertEqual(after_fm["project_state"], "aborted")
        self.assertEqual(
            after_fm["release_close_reason"], "incident-abort",
        )
        self.assertIsNone(after_fm["current_stage"])
        self.assertIsNone(after_fm["sub_state"])
        self.assertEqual(after_fm["release_state"], "closed")
        self.assertEqual(after_fm["review_iteration"], 0)
        self.assertEqual(
            after_fm["bug_flow"],
            before_fm["bug_flow"],
        )
        self.assertFalse(after_fm["workflow_incident_active"])
        self.assertIsNone(after_fm["incident_report_path"])


# ---------- lock blocking ----------


class IncidentLockTests(_CliRunner):
    def test_lock_blocks_incident_start(self):
        bug_rel, incident_rel = self._seed_pending_incident()
        from skills._shared.dev_workflow.progress_lock import progress_lock

        with _install_test_stage_advance_handler():
            _seed_at_testing_review_passed(self.root)
            with progress_lock(self.root, timeout=1.0):
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "--lock-timeout", "0.1",
                        "incident-start",
                        "--bug", bug_rel,
                        "--report", incident_rel,
                    ]
                )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
