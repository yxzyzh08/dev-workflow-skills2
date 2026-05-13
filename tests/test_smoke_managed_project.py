"""End-to-end smoke for a managed project (Phase 7 Item 2).

Each testcase below drives a real ``progress.py`` + ``validate.py``
chain against a temp-directory project root. Fixtures construct
doc-guardian-compliant frontmatter (incremental docs carry empty
``## Pending Changes`` + ``## Change Log`` sections) so that
``update --advance`` runs the live A/B/E P6 preflight without any
``validate_doc`` mocking. ``progress_lock`` is also un-mocked.

Three required scenarios per Phase 7 spec:

  1. ``S1MainHappyPathSmoke`` — init S1 release=0.1 through stages 1-7,
     including a single development task and a passing test/delivery
     run, ending in ``release-close``.
  2. ``BugFlowDevRollbackSmoke`` — same baseline up to testing with a
     failing test-report, then ``bug-start --root-cause development``,
     fix-and-pass cycle, ``bug-close``, advance to delivery + retro +
     release-close.
  3. ``IncidentContinueSmoke`` — PRD-exception incident from testing,
     ``incident-start`` opens both ``bug_flow`` and
     ``workflow_incident_active``; ``incident-resolve --action continue``
     returns to testing for retest pass, then continues to delivery
     and retro.

The shared ``_S1HappyDriver`` exposes per-stage helpers so each test
re-uses one definition of "what does a clean stage transition look
like in practice." Bug / incident tests branch off after fastening
testing artifacts.
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
_WORKFLOW_SCRIPTS = _REPO_ROOT / "skills" / "workflow-protocol" / "scripts"
_DOC_GUARDIAN_SCRIPTS = _REPO_ROOT / "skills" / "doc-guardian" / "scripts"
for _path in (_WORKFLOW_SCRIPTS, _DOC_GUARDIAN_SCRIPTS, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

progress = importlib.import_module("progress")
validate = importlib.import_module("validate")

from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    parse_frontmatter,
)


# ---------- low-level fixture helpers ----------


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_doc(root: Path, rel: str, fm: dict, body: str = "") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{_emit_yaml(fm)}\n---\n{body}", encoding="utf-8")
    return p


_INCREMENTAL_BODY = "\n## Pending Changes\n\n## Change Log\n"


def _basic_fm(
    *,
    title: str,
    doc_type: str,
    status: str = "review-passed",
    owner: str = "claude-opus-4-7/test-fixture",
    created: str = "2026-05-07T08:00:00Z",
    updated: str = "2026-05-07T08:00:00Z",
) -> dict:
    return {
        "title": title,
        "type": doc_type,
        "status": status,
        "created": created,
        "updated": updated,
        "owner": owner,
    }


# ---------- per-doc-type builders ----------


def _make_prd(root: Path, *, status: str = "review-passed") -> Path:
    fm = _basic_fm(title="MyApp Product Requirements", doc_type="prd", status=status)
    return _write_doc(root, "docs/prd/prd.md", fm, _INCREMENTAL_BODY)


def _make_srs(
    root: Path, *, release: str, status: str = "review-passed",
    is_multi_module: bool = False, architecture_change: bool = False,
) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} SRS", doc_type="srs", status=status,
        owner="claude-opus-4-7/srs-write",
    )
    fm["release"] = release
    fm["is_multi_module"] = is_multi_module
    fm["architecture_change"] = architecture_change
    return _write_doc(
        root, f"docs/release{release}/srs/srs.md", fm, _INCREMENTAL_BODY,
    )


def _make_acceptance_plan(
    root: Path, *, release: str, status: str = "review-passed",
) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Acceptance Plan",
        doc_type="acceptance-plan", status=status,
        owner="claude-opus-4-7/srs-write",
    )
    fm["release"] = release
    fm["related_srs"] = f"docs/release{release}/srs/srs.md"
    return _write_doc(
        root, f"docs/release{release}/srs/acceptance_plan.md", fm,
        _INCREMENTAL_BODY,
    )


def _make_architecture(root: Path, *, status: str = "review-passed") -> Path:
    fm = _basic_fm(
        title="MyApp Architecture", doc_type="architecture", status=status,
        owner="claude-opus-4-7/architecture-write",
    )
    return _write_doc(root, "docs/architecture/architecture.md", fm, _INCREMENTAL_BODY)


def _make_dev_plan(root: Path, *, release: str) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Development Plan",
        doc_type="development-plan",
        owner="claude-opus-4-7/development-planning-write",
    )
    fm["release"] = release
    return _write_doc(
        root, f"docs/release{release}/development/plan.md", fm, _INCREMENTAL_BODY,
    )


def _make_task_breakdown(
    root: Path, *, release: str, total_tasks: int,
    task_ids: tuple[str, ...] = ("T1",),
) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Task Breakdown",
        doc_type="task-breakdown",
        owner="claude-opus-4-7/development-planning-write",
    )
    fm["release"] = release
    fm["total_tasks"] = total_tasks
    # progress_artifacts.load_breakdown_with_tasks scans the body for
    # \bTn\b tokens; the smoke needs each declared task id named.
    task_section = "\n## Tasks\n\n" + "\n".join(
        f"- {tid}: smoke task {tid}" for tid in task_ids
    ) + "\n"
    body = _INCREMENTAL_BODY + task_section
    return _write_doc(
        root, f"docs/release{release}/development/breakdown.md", fm, body,
    )


def _make_detailed_design(
    root: Path, *, release: str, task_id: str,
) -> Path:
    fm = _basic_fm(
        title=f"{task_id} Detailed Design",
        doc_type="detailed-design",
        owner="claude-opus-4-7/development-planning-write",
    )
    fm["release"] = release
    fm["task_id"] = task_id
    return _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/detailed_design.md",
        fm, _INCREMENTAL_BODY,
    )


def _make_test_review_report(
    root: Path, *, release: str, task_id: str,
    review_status: str = "pass",
) -> Path:
    if review_status == "pass":
        doc_status, blocking, max_sev, findings = "review-passed", 0, "low", 0
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    elif review_status == "pending":
        doc_status, blocking, max_sev, findings = "draft", 0, "low", 0
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    elif review_status == "fail":
        doc_status, blocking, max_sev, findings = "in-review", 1, "high", 1
        sev = {"critical": 0, "high": 1, "medium": 0, "low": 0}
    else:
        raise ValueError(f"unknown review_status {review_status!r}")
    fm = _basic_fm(
        title=f"{task_id} Test Review Report",
        doc_type="test-review-report", status=doc_status,
        owner="claude-opus-4-7/development-test-review",
    )
    fm["release"] = release
    fm["task_id"] = task_id
    fm["findings_count"] = findings
    fm["severity_distribution"] = sev
    fm["review_status"] = review_status
    fm["blocking_findings_count"] = blocking
    fm["max_severity"] = max_sev
    return _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/test_review_report.md",
        fm,
    )


def _make_code_review_report(
    root: Path, *, release: str, task_id: str,
    review_status: str = "pass",
) -> Path:
    if review_status == "pass":
        doc_status, blocking, max_sev, findings = "review-passed", 0, "low", 0
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    elif review_status == "pending":
        doc_status, blocking, max_sev, findings = "draft", 0, "low", 0
        sev = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    elif review_status == "fail":
        doc_status, blocking, max_sev, findings = "in-review", 1, "high", 1
        sev = {"critical": 0, "high": 1, "medium": 0, "low": 0}
    else:
        raise ValueError(f"unknown review_status {review_status!r}")
    fm = _basic_fm(
        title=f"{task_id} Code Review Report",
        doc_type="code-review-report", status=doc_status,
        owner="claude-opus-4-7/development-code-review",
    )
    fm["release"] = release
    fm["task_id"] = task_id
    fm["findings_count"] = findings
    fm["severity_distribution"] = sev
    fm["review_status"] = review_status
    fm["blocking_findings_count"] = blocking
    fm["max_severity"] = max_sev
    return _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/code_review_report.md",
        fm,
    )


def _make_verification_result(
    root: Path, *, release: str, task_id: str,
    verification_status: str = "pass",
) -> Path:
    fm = _basic_fm(
        title=f"{task_id} Verification Result",
        doc_type="verification-result",
        owner="claude-opus-4-7/development-verifying",
    )
    fm["release"] = release
    fm["task_id"] = task_id
    fm["verification_status"] = verification_status
    return _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/verification_result.md",
        fm,
    )


def _make_test_preparation(root: Path, *, release: str) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Test Preparation",
        doc_type="test-preparation",
        owner="claude-opus-4-7/testing-write",
    )
    fm["release"] = release
    return _write_doc(
        root, f"docs/release{release}/testing/preparation.md", fm,
    )


def _make_test_procedure(root: Path, *, release: str) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Test Procedure",
        doc_type="test-procedure",
        owner="claude-opus-4-7/testing-write",
    )
    fm["release"] = release
    return _write_doc(
        root, f"docs/release{release}/testing/procedure.md", fm,
    )


def _make_test_report(
    root: Path, *, release: str, verification_status: str = "pass",
    total: int = 5, passed: int | None = None, failed: int | None = None,
) -> Path:
    if verification_status == "pass":
        passed_n = total if passed is None else passed
        failed_n = 0 if failed is None else failed
    elif verification_status == "fail":
        passed_n = (total - 1) if passed is None else passed
        failed_n = 1 if failed is None else failed
    else:  # partial
        passed_n = (total - 1) if passed is None else passed
        failed_n = 1 if failed is None else failed
    fm = _basic_fm(
        title=f"MyApp v{release} Test Report",
        doc_type="test-report",
        owner="claude-opus-4-7/testing-write",
    )
    fm["release"] = release
    fm["verification_status"] = verification_status
    fm["total_test_cases"] = total
    fm["passed"] = passed_n
    fm["failed"] = failed_n
    return _write_doc(
        root, f"docs/release{release}/testing/report.md", fm,
    )


def _make_deployment_doc(root: Path, *, release: str) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Deployment",
        doc_type="deployment-doc",
        owner="claude-opus-4-7/delivery-write",
    )
    fm["release"] = release
    return _write_doc(
        root, f"docs/release{release}/delivery/deployment.md", fm,
    )


def _make_operation_manual(root: Path, *, release: str) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Operation Manual",
        doc_type="operation-manual",
        owner="claude-opus-4-7/delivery-write",
    )
    fm["release"] = release
    return _write_doc(
        root, f"docs/release{release}/delivery/operation_manual.md", fm,
    )


def _make_installation_result(
    root: Path, *, release: str, verification_status: str = "pass",
) -> Path:
    fm = _basic_fm(
        title=f"MyApp v{release} Installation Result",
        doc_type="installation-result",
        owner="claude-opus-4-7/delivery-write",
    )
    fm["release"] = release
    fm["verification_status"] = verification_status
    return _write_doc(
        root, f"docs/release{release}/delivery/installation_result.md", fm,
    )


def _make_retrospective(root: Path) -> Path:
    fm = _basic_fm(
        title="MyApp Retrospective",
        doc_type="retrospective",
        owner="claude-opus-4-7/project-retrospective-write",
    )
    return _write_doc(root, "docs/retrospective/retrospective.md", fm, _INCREMENTAL_BODY)


# Bug / Incident reports.


def _make_bug_report(
    root: Path, *, bug_id: str, found_in_release: str,
    target_release: str | None, root_cause: str | None,
    consumed_in_release: str | None = None,
    triage_section: str | None = None,
) -> Path:
    fm = _basic_fm(
        title=f"{bug_id} Bug Report",
        doc_type="bug-report",
        owner="claude-opus-4-7/bug-triage",
    )
    fm["bug_id"] = bug_id
    fm["found_in_release"] = found_in_release
    fm["target_release"] = target_release
    fm["root_cause"] = root_cause
    fm["consumed_in_release"] = consumed_in_release
    body = _INCREMENTAL_BODY
    if triage_section is not None:
        body = body + "\n## Triage Analysis\n\n" + triage_section + "\n"
    return _write_doc(root, f"docs/bug/{bug_id}.md", fm, body)


def _make_incident_report(
    root: Path, *, incident_id: str, triggered_by_bug: str,
    triggered_in_release: str, resolution_action: str | None = None,
    status: str = "draft",
) -> Path:
    fm = _basic_fm(
        title=f"{incident_id} Workflow Incident",
        doc_type="workflow-incident",
        owner="claude-opus-4-7/workflow-evolution",
        status=status,
    )
    fm["incident_id"] = incident_id
    fm["triggered_by_bug"] = triggered_by_bug
    fm["triggered_in_release"] = triggered_in_release
    fm["resolution_action"] = resolution_action
    return _write_doc(
        root, f"docs/incident/{incident_id}.md", fm, _INCREMENTAL_BODY,
    )


# ---------- _FakeClock + CLI runner ----------


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(
            2026, 5, 7, 9, 0, 0, tzinfo=timezone.utc,
        )

    def __call__(self) -> str:
        ts = self._cursor.strftime("%Y-%m-%dT%H:%M:%SZ")
        self._cursor += timedelta(seconds=1)
        return ts


@contextlib.contextmanager
def _capture_io():
    """Capture stdout/stderr around a CLI invocation."""

    out, err = io.StringIO(), io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        yield out, err
    finally:
        sys.stdout, sys.stderr = old_out, old_err


class _SmokeBase(unittest.TestCase):
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
        # repo root must stay clean — the smoke test runs in a temp dir
        # but defensively check that nothing leaked into the cwd.
        assert not (Path.cwd() / "progress.md").exists(), \
            "smoke leaked progress.md into cwd"
        assert not (Path.cwd() / "progress-history.md").exists(), \
            "smoke leaked progress-history.md into cwd"

    # ----- thin wrappers on top of progress.main / validate.main -----

    def _run_progress(self, argv: list[str]) -> tuple[int, str, str]:
        with _capture_io() as (out, err):
            try:
                code = progress.main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        return code, out.getvalue(), err.getvalue()

    def _expect_progress_ok(self, argv: list[str], *, hint: str = "") -> str:
        code, out, err = self._run_progress(argv)
        if code != 0:
            self.fail(
                f"{hint or 'progress'} {argv} failed with exit {code}\n"
                f"STDERR:\n{err}\n"
                f"STDOUT:\n{out}\n"
                f"PROGRESS:\n{self._read_progress_text()}\n"
            )
        return out

    def _expect_progress_err(
        self, argv: list[str], *, expected_exit: int = 1,
    ) -> str:
        code, _out, err = self._run_progress(argv)
        self.assertEqual(
            code, expected_exit,
            f"expected exit {expected_exit}, got {code}; STDERR:\n{err}",
        )
        return err

    def _read_progress_fm(self) -> dict:
        return parse_frontmatter(
            (self.root / "progress.md").read_text(encoding="utf-8")
        ).frontmatter

    def _read_progress_text(self) -> str:
        path = self.root / "progress.md"
        if not path.exists():
            return "<no progress.md yet>"
        return path.read_text(encoding="utf-8")

    # ----- live validate.py file dispatch (no mocking) -----

    def _validate_file_ok(self, rel: str) -> None:
        with _capture_io() as (_out, err):
            issues = validate.validate_file(rel, self.root)
        if issues:
            self.fail(
                f"validate.py file {rel} unexpectedly produced issues:\n"
                + "\n".join(f"- {i}" for i in issues)
                + (f"\nSTDERR:\n{err.getvalue()}" if err.getvalue() else "")
            )


# ---------- shared driver: walk a clean S1 happy path stage by stage ----------


class _S1HappyDriver:
    """Lightweight wrapper that scripts each S1 happy-path stage.

    The driver is stateful — call methods in order. Each method
    constructs the docs the next ``update --advance`` will validate,
    drives the sub_state machine to ``approved`` (gated) or
    ``review-passed`` (non-gated), then advances. This keeps individual
    testcases readable: ``driver.do_prd_stage(); driver.do_srs_stage();``
    et cetera.
    """

    def __init__(self, base: _SmokeBase, *, release: str = "0.1") -> None:
        self.base = base
        self.root = base.root
        self.release = release

    # --- scenario lifecycle ---

    def init(self, *, project: str = "MyApp", scenario: str = "S1") -> None:
        self.base._expect_progress_ok(
            [
                "--root", str(self.root),
                "init", "--project", project, "--scenario", scenario,
                "--release", self.release,
            ],
            hint="init",
        )

    # --- gated stage helper ---

    def _drive_gated_stage(self, *, expected_stage: str) -> None:
        """Walk a gated stage write→in-review→review-passed→approved."""

        fm = self.base._read_progress_fm()
        self.base.assertEqual(fm["current_stage"], expected_stage)
        self.base.assertEqual(fm["sub_state"], "write")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "write-complete"],
            hint=f"{expected_stage} write-complete",
        )
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "review-passed"],
            hint=f"{expected_stage} review-passed",
        )
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "human-confirmed"],
            hint=f"{expected_stage} human-confirmed",
        )

    def _drive_review_passed_stage(self, *, expected_stage: str) -> None:
        """Walk a non-gated stage write→in-review→review-passed."""

        fm = self.base._read_progress_fm()
        self.base.assertEqual(fm["current_stage"], expected_stage)
        self.base.assertEqual(fm["sub_state"], "write")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "write-complete"],
            hint=f"{expected_stage} write-complete",
        )
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "review-passed"],
            hint=f"{expected_stage} review-passed",
        )

    # --- stage 1 PRD ---

    def do_prd_stage(self) -> None:
        # Doc must be present and valid before the stage's --advance.
        # Use status=approved so validate.py file passes through; the
        # Phase 6.4 P6 D dim is enforced by progress.py sub_state, not
        # by re-reading doc status here.
        _make_prd(self.root, status="approved")
        self.base._validate_file_ok("docs/prd/prd.md")
        self._drive_gated_stage(expected_stage="prd-inception")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="prd-inception advance",
        )

    # --- stage 2 SRS ---

    def do_srs_stage(self) -> None:
        _make_srs(self.root, release=self.release, status="approved")
        _make_acceptance_plan(
            self.root, release=self.release, status="review-passed",
        )
        self.base._validate_file_ok(f"docs/release{self.release}/srs/srs.md")
        self.base._validate_file_ok(
            f"docs/release{self.release}/srs/acceptance_plan.md",
        )
        self._drive_gated_stage(expected_stage="srs-specification")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="srs-specification advance",
        )

    # --- stage 3 Architecture ---

    def do_architecture_stage(self) -> None:
        _make_architecture(self.root, status="approved")
        self.base._validate_file_ok("docs/architecture/architecture.md")
        self._drive_gated_stage(expected_stage="architecture-design")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="architecture-design advance",
        )

    # --- stage 4 Development (single task) ---

    def do_development_stage(self, *, task_id: str = "T1") -> None:
        # Stage-level artifacts.
        _make_dev_plan(self.root, release=self.release)
        _make_task_breakdown(
            self.root, release=self.release, total_tasks=1,
        )
        # Per-task artifacts. detailed_design first; reviews + verification
        # finish each task transition. Stage-4 surrogate ("all task_states
        # verified") is enforced by apply_update_advance, but the per-task
        # transitions still run through the state machine.
        _make_detailed_design(
            self.root, release=self.release, task_id=task_id,
        )
        # Skeleton review reports in 'pending' so update --task can walk
        # to test-review without forcing through the test-done gate
        # prematurely.
        _make_test_review_report(
            self.root, release=self.release, task_id=task_id,
            review_status="pending",
        )
        _make_code_review_report(
            self.root, release=self.release, task_id=task_id,
            review_status="pending",
        )
        # Walk task state machine: planning-done → test-writing → test-review
        # → test-done → code-writing → code-review → code-review-passed
        # → verifying → verified.
        for status in ("planning-done", "test-writing", "test-review"):
            self.base._expect_progress_ok(
                [
                    "--root", str(self.root),
                    "update", "--task", task_id, "--status", status,
                ],
                hint=f"task {task_id} {status}",
            )
        # Promote test review skeleton to pass before transitioning test-done.
        _make_test_review_report(
            self.root, release=self.release, task_id=task_id,
            review_status="pass",
        )
        for status in ("test-done", "code-writing", "code-review"):
            self.base._expect_progress_ok(
                [
                    "--root", str(self.root),
                    "update", "--task", task_id, "--status", status,
                ],
                hint=f"task {task_id} {status}",
            )
        # Promote code review skeleton to pass before code-review-passed.
        _make_code_review_report(
            self.root, release=self.release, task_id=task_id,
            review_status="pass",
        )
        for status in ("code-review-passed", "verifying"):
            self.base._expect_progress_ok(
                [
                    "--root", str(self.root),
                    "update", "--task", task_id, "--status", status,
                ],
                hint=f"task {task_id} {status}",
            )
        # verifying → verified requires verification_result.md.
        _make_verification_result(
            self.root, release=self.release, task_id=task_id,
            verification_status="pass",
        )
        self.base._expect_progress_ok(
            [
                "--root", str(self.root),
                "update", "--task", task_id, "--status", "verified",
            ],
            hint=f"task {task_id} verified",
        )
        # Live validate.py file on every per-task artifact.
        for fname in (
            "detailed_design.md", "test_review_report.md",
            "code_review_report.md", "verification_result.md",
        ):
            self.base._validate_file_ok(
                f"docs/release{self.release}/development/tasks/"
                f"{task_id}/{fname}",
            )
        self.base._validate_file_ok(
            f"docs/release{self.release}/development/plan.md",
        )
        self.base._validate_file_ok(
            f"docs/release{self.release}/development/breakdown.md",
        )
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="development advance",
        )

    # --- stage 5 Testing ---

    def do_testing_stage(self) -> None:
        _make_test_preparation(self.root, release=self.release)
        _make_test_procedure(self.root, release=self.release)
        _make_test_report(
            self.root, release=self.release, verification_status="pass",
        )
        self.base._validate_file_ok(
            f"docs/release{self.release}/testing/preparation.md",
        )
        self.base._validate_file_ok(
            f"docs/release{self.release}/testing/procedure.md",
        )
        self.base._validate_file_ok(
            f"docs/release{self.release}/testing/report.md",
        )
        self._drive_review_passed_stage(expected_stage="testing")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="testing advance",
        )

    # --- stage 6 Delivery ---

    def do_delivery_stage(self) -> None:
        _make_deployment_doc(self.root, release=self.release)
        _make_operation_manual(self.root, release=self.release)
        _make_installation_result(
            self.root, release=self.release, verification_status="pass",
        )
        for rel in (
            f"docs/release{self.release}/delivery/deployment.md",
            f"docs/release{self.release}/delivery/operation_manual.md",
            f"docs/release{self.release}/delivery/installation_result.md",
        ):
            self.base._validate_file_ok(rel)
        self._drive_review_passed_stage(expected_stage="delivery")
        self.base._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="delivery advance",
        )

    # --- stage 7 Retrospective ---

    def do_retrospective_stage(self) -> None:
        _make_retrospective(self.root)
        self.base._validate_file_ok("docs/retrospective/retrospective.md")
        self._drive_review_passed_stage(expected_stage="project-retrospective")
        # No --advance from project-retrospective; release-close instead.
        self.base._expect_progress_ok(
            ["--root", str(self.root), "release-close"],
            hint="release-close",
        )


# ---------- 1. S1 main happy path ----------


class S1MainHappyPathSmoke(_SmokeBase):
    def test_full_s1_release_0_1_through_release_close(self) -> None:
        driver = _S1HappyDriver(self, release="0.1")
        driver.init()

        fm0 = self._read_progress_fm()
        self.assertEqual(fm0["current_stage"], "prd-inception")
        self.assertEqual(fm0["sub_state"], "write")
        self.assertEqual(fm0["scenario"], "S1")
        self.assertEqual(fm0["release"], "0.1")
        self.assertEqual(fm0["release_state"], "active")

        driver.do_prd_stage()
        self.assertEqual(self._read_progress_fm()["current_stage"], "srs-specification")

        driver.do_srs_stage()
        self.assertEqual(
            self._read_progress_fm()["current_stage"], "architecture-design",
        )

        driver.do_architecture_stage()
        self.assertEqual(self._read_progress_fm()["current_stage"], "development")

        driver.do_development_stage(task_id="T1")
        fm_after_dev = self._read_progress_fm()
        self.assertEqual(fm_after_dev["current_stage"], "testing")
        self.assertEqual(
            fm_after_dev["development_state"]["task_states"]["T1"], "verified",
        )

        driver.do_testing_stage()
        self.assertEqual(self._read_progress_fm()["current_stage"], "delivery")

        driver.do_delivery_stage()
        self.assertEqual(
            self._read_progress_fm()["current_stage"], "project-retrospective",
        )

        driver.do_retrospective_stage()
        fm_final = self._read_progress_fm()
        self.assertEqual(fm_final["release_state"], "closed")
        self.assertEqual(fm_final["release_close_reason"], "stage-7-completed")
        self.assertEqual(fm_final["previous_releases"], ["0.1"])
        self.assertEqual(
            fm_final["current_stage"], "project-retrospective",
        )

        # validate.py consistency may trip on the closed-release state
        # (consistency derives from current_stage which is still
        # project-retrospective and no retro doc exists for the closed
        # release). We only assert the four artifact types we relied on
        # pass validate.py file individually — the per-file assertions
        # already ran through the driver.
        history_text = (self.root / "progress-history.md").read_text(
            encoding="utf-8",
        )
        # Each entry header is ``## <ts> — <event> — <summary>``. The
        # chain should include exactly one release-close entry and one
        # entry for each of the six stage advances.
        self.assertEqual(history_text.count(" — update-advance — "), 6)
        self.assertEqual(history_text.count(" — release-close — "), 1)


# ---------- 2. Bug Flow with Gap-4 dev rollback ----------


class BugFlowDevRollbackSmoke(_SmokeBase):
    def test_dev_root_cause_bug_flow_through_close(self) -> None:
        driver = _S1HappyDriver(self, release="0.1")
        driver.init()
        driver.do_prd_stage()
        driver.do_srs_stage()
        driver.do_architecture_stage()
        driver.do_development_stage(task_id="T1")

        # Now in testing/write. Build testing artifacts EXCEPT the test
        # report shows fail — driver doesn't create the artifacts in
        # this branch, we do it inline.
        _make_test_preparation(self.root, release="0.1")
        _make_test_procedure(self.root, release="0.1")
        _make_test_report(
            self.root, release="0.1", verification_status="fail",
        )
        self._validate_file_ok("docs/release0.1/testing/report.md")

        # Drive testing through write-complete + review-passed so
        # bug_flow can be opened from sub_state=review-passed.
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "write-complete"],
            hint="testing write-complete (fail)",
        )
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "review-passed"],
            hint="testing review-passed (fail)",
        )
        # advance must REJECT because verification_status==fail.
        err = self._expect_progress_err(
            ["--root", str(self.root), "update", "--advance"],
        )
        self.assertIn("dimension E", err)

        # Open Bug Flow with root_cause=development; triage section
        # picks T1 so Gap-4 rollback fires (verified → test-revising
        # for test-only fix). The fix-style classifier is keyword-based
        # — "test-only" lands in _TEST_FIX_KEYWORDS so the rollback
        # picks the test-revising target instead of code-revising.
        triage = (
            "**Affected Task(s)**: T1\n\n"
            "Classification: test-only fix; missing regression coverage.\n"
        )
        _make_bug_report(
            self.root,
            bug_id="BUG-001",
            found_in_release="0.1",
            target_release="0.1",
            root_cause="development",
            triage_section=triage,
        )
        self._validate_file_ok("docs/bug/BUG-001.md")
        self._expect_progress_ok(
            [
                "--root", str(self.root), "bug-start",
                "--bug", "docs/bug/BUG-001.md",
                "--root-cause", "development",
            ],
            hint="bug-start dev",
        )
        fm_in_bug = self._read_progress_fm()
        self.assertTrue(fm_in_bug["bug_flow"]["active"])
        self.assertEqual(fm_in_bug["bug_flow"]["root_cause"], "development")
        self.assertEqual(fm_in_bug["current_stage"], "development")
        # Gap-4 dev rollback should have moved T1 back from verified.
        self.assertNotEqual(
            fm_in_bug["development_state"]["task_states"]["T1"], "verified",
        )

        # Walk T1 back through the state machine to verified again, then
        # bug-close on a passing retest.
        # The rollback put T1 into test-revising; from there the legal
        # forward path is test-revising → test-review → test-done →
        # code-writing → code-review → code-review-passed → verifying
        # → verified. We need fresh review reports in 'pass' to
        # transition test-done / code-review-passed.
        self.assertEqual(
            fm_in_bug["development_state"]["task_states"]["T1"], "test-revising",
        )
        # Set both review reports back to pending while we re-walk; the
        # transitions re-promote them to pass at the right gates.
        _make_test_review_report(
            self.root, release="0.1", task_id="T1", review_status="pending",
        )
        _make_code_review_report(
            self.root, release="0.1", task_id="T1", review_status="pending",
        )
        self._expect_progress_ok(
            [
                "--root", str(self.root),
                "update", "--task", "T1", "--status", "test-review",
            ],
            hint="T1 retry test-review",
        )
        _make_test_review_report(
            self.root, release="0.1", task_id="T1", review_status="pass",
        )
        for status in ("test-done", "code-writing", "code-review"):
            self._expect_progress_ok(
                [
                    "--root", str(self.root),
                    "update", "--task", "T1", "--status", status,
                ],
                hint=f"T1 retry {status}",
            )
        _make_code_review_report(
            self.root, release="0.1", task_id="T1", review_status="pass",
        )
        for status in ("code-review-passed", "verifying"):
            self._expect_progress_ok(
                [
                    "--root", str(self.root),
                    "update", "--task", "T1", "--status", status,
                ],
                hint=f"T1 retry {status}",
            )
        _make_verification_result(
            self.root, release="0.1", task_id="T1",
            verification_status="pass",
        )
        self._expect_progress_ok(
            [
                "--root", str(self.root),
                "update", "--task", "T1", "--status", "verified",
            ],
            hint="T1 retry verified",
        )

        # T1 is verified again. Per bug-flow choreography (command-
        # reference §10), bug-close requires current_stage=testing
        # AND verification_status=pass on the latest test-report. So
        # we first advance back from development to testing (P6 dim A
        # passes — all dev artifacts exist; B passes — they validate;
        # development has no E dim), refresh the test-report to pass,
        # walk testing through review-passed, then close the bug.
        fm_dev_done = self._read_progress_fm()
        self.assertEqual(fm_dev_done["current_stage"], "development")
        self.assertEqual(
            fm_dev_done["development_state"]["task_states"]["T1"], "verified",
        )
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="advance dev→testing after bug fix",
        )
        self.assertEqual(self._read_progress_fm()["current_stage"], "testing")
        # Flip the test-report to pass and walk testing's review again.
        _make_test_report(
            self.root, release="0.1", verification_status="pass",
        )
        self._validate_file_ok("docs/release0.1/testing/report.md")
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "write-complete"],
            hint="testing write-complete after retest",
        )
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "review-passed"],
            hint="testing review-passed after retest",
        )
        self._expect_progress_ok(
            ["--root", str(self.root), "bug-close"],
            hint="bug-close",
        )
        fm_after_close = self._read_progress_fm()
        self.assertFalse(fm_after_close["bug_flow"]["active"])
        self.assertEqual(fm_after_close["current_stage"], "testing")
        # bug-close leaves sub_state at review-passed, so advance can
        # proceed straight to delivery.
        self.assertEqual(fm_after_close["sub_state"], "review-passed")
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="testing advance after bug-close",
        )
        self.assertEqual(self._read_progress_fm()["current_stage"], "delivery")

        # Finish the release through retro + close so we get a clean
        # end-state assertion.
        driver.do_delivery_stage()
        driver.do_retrospective_stage()
        fm_final = self._read_progress_fm()
        self.assertEqual(fm_final["release_state"], "closed")
        self.assertEqual(fm_final["previous_releases"], ["0.1"])


# ---------- 3. Incident continue ----------


class IncidentContinueSmoke(_SmokeBase):
    def test_prd_exception_incident_continue_returns_to_testing(self) -> None:
        driver = _S1HappyDriver(self, release="0.1")
        driver.init()
        driver.do_prd_stage()
        driver.do_srs_stage()
        driver.do_architecture_stage()
        driver.do_development_stage(task_id="T1")

        # Build testing artifacts with a failing test-report (the issue
        # is later attributed to a PRD exception, not the dev work).
        _make_test_preparation(self.root, release="0.1")
        _make_test_procedure(self.root, release="0.1")
        _make_test_report(
            self.root, release="0.1", verification_status="fail",
        )
        self._validate_file_ok("docs/release0.1/testing/report.md")
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "write-complete"],
            hint="testing write-complete (incident)",
        )
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--event", "review-passed"],
            hint="testing review-passed (incident)",
        )

        # Construct BUG with root_cause=prd-exception + INCIDENT skeleton.
        _make_bug_report(
            self.root,
            bug_id="BUG-002",
            found_in_release="0.1",
            target_release="0.1",
            root_cause="prd-exception",
        )
        # INCIDENT skeleton goes through workflow-evolution; for the
        # smoke we go straight to a fully-promoted INCIDENT (the
        # incident-resolve gate requires status=review-passed +
        # resolution_action=continue).
        # incident-start requires an INCIDENT doc that already passes
        # validate.py file; doc-guardian permits any status, but
        # triggered_by_bug must equal the BUG bug_id.
        _make_incident_report(
            self.root,
            incident_id="INCIDENT-001",
            triggered_by_bug="BUG-002",
            triggered_in_release="0.1",
            resolution_action=None,
            status="draft",
        )
        self._validate_file_ok("docs/bug/BUG-002.md")
        self._validate_file_ok("docs/incident/INCIDENT-001.md")

        self._expect_progress_ok(
            [
                "--root", str(self.root), "incident-start",
                "--bug", "docs/bug/BUG-002.md",
                "--report", "docs/incident/INCIDENT-001.md",
            ],
            hint="incident-start",
        )
        fm_in_incident = self._read_progress_fm()
        self.assertTrue(fm_in_incident["bug_flow"]["active"])
        self.assertTrue(fm_in_incident["workflow_incident_active"])
        self.assertEqual(
            fm_in_incident["bug_flow"]["root_cause"], "prd-exception",
        )
        self.assertEqual(
            fm_in_incident["current_stage"], "workflow-incident-analysis",
        )

        # Workflow-evolution finalizes the incident: the smoke skips the
        # actual finalization steps and just promotes the INCIDENT doc
        # with action=continue + status=review-passed, which is the
        # contract incident-resolve enforces.
        _make_incident_report(
            self.root,
            incident_id="INCIDENT-001",
            triggered_by_bug="BUG-002",
            triggered_in_release="0.1",
            resolution_action="continue",
            status="review-passed",
        )
        self._validate_file_ok("docs/incident/INCIDENT-001.md")
        self._expect_progress_ok(
            [
                "--root", str(self.root), "incident-resolve",
                "--action", "continue",
            ],
            hint="incident-resolve continue",
        )
        fm_after = self._read_progress_fm()
        self.assertFalse(fm_after["workflow_incident_active"])
        self.assertFalse(fm_after["bug_flow"]["active"])
        # 'continue' returns to testing, not a terminal state.
        self.assertEqual(fm_after["current_stage"], "testing")
        self.assertEqual(fm_after["project_state"], "active")

        # incident-resolve --action continue per apply_incident_resolve
        # restores current_stage=testing AND sub_state=review-passed
        # (command-reference §12.1). So the caller can flip the test-
        # report to pass and advance straight to delivery without
        # rewalking write-complete/review-passed.
        self.assertEqual(fm_after["sub_state"], "review-passed")
        _make_test_report(
            self.root, release="0.1", verification_status="pass",
        )
        self._validate_file_ok("docs/release0.1/testing/report.md")
        self._expect_progress_ok(
            ["--root", str(self.root), "update", "--advance"],
            hint="testing advance (post-incident)",
        )
        self.assertEqual(self._read_progress_fm()["current_stage"], "delivery")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
