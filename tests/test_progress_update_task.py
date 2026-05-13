"""CLI integration tests for progress.py update --task.

Phase 5.3 cannot legitimately bring ``current_stage`` to ``development``
through the public CLI alone (no ``update --advance`` until Phase 6).
Tests therefore use a temporary replay handler injection
(``_install_test_stage_advance_handler``) that registers a synthetic
``test-stage-advance`` history event for the duration of a test. The
production replay validator is unaffected outside the patched window.

This test file focuses on:
  * argparse / dispatch for ``update --task`` (mutex group + --status)
  * full Stage 4 task happy path through the CLI
  * M1 inheritance: ``update --task`` rejects malformed history /
    out-of-band progress.md tampering exactly like ``update --event``.
  * recover roundtrip after a multi-task Stage 4 cycle.
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


# ---------- test-only stage-advance handler ----------


_TEST_ADVANCE_EVENT = "test-stage-advance"


def _test_stage_advance_handler(state, entry, root):
    """Synthetic replay handler that mutates ``current_stage`` /
    ``sub_state`` / ``review_iteration`` according to tokens in the
    summary. Used by Phase 5.3 tests so that forging progress.md to
    ``current_stage=development`` can be paired with a corresponding
    history entry that the replay validator accepts.

    Recognised summary format::

        test-stage-advance current_stage=<stage> sub_state=<state>

    Plus, when ``current_stage=development``, automatically initialises
    ``development_state.task_states`` to an empty dict if missing, so
    update-task transitions can build on it.
    """

    if not state:
        raise progress_replay.ReplayError(
            f"history at {entry.timestamp}: '{_TEST_ADVANCE_EVENT}' "
            "requires prior init"
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
    new_state["review_iteration"] = 0
    if new_state.get("current_stage") == "development":
        dev = dict(new_state.get("development_state") or {})
        dev.setdefault("task_states", {})
        new_state["development_state"] = dev
    new_state["updated"] = entry.timestamp
    return new_state


@contextlib.contextmanager
def _install_test_stage_advance_handler():
    handlers = dict(progress_replay._HANDLERS)
    handlers[_TEST_ADVANCE_EVENT] = _test_stage_advance_handler
    with patch.object(progress_replay, "_HANDLERS", handlers):
        yield


# ---------- fixture builders ----------


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_doc(root: Path, rel: str, fm: dict, body: str = "Body.\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(f"---\n{_emit_yaml(fm)}\n---\n{body}", encoding="utf-8")
    return p


def _base_fm(doc_type: str, **extra) -> dict:
    fm = {
        "title": f"{doc_type} doc",
        "type": doc_type,
        "status": "draft",
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-05-15T10:00:00Z",
        "owner": "claude-opus-4-7/development-write",
    }
    fm.update(extra)
    return fm


def _make_breakdown(root: Path, *, release: str = "0.1", tasks=("T1",)) -> None:
    body = "# Tasks\n\n" + "\n".join(f"- {t} — task" for t in tasks) + "\n"
    _write_doc(
        root,
        f"docs/release{release}/development/breakdown.md",
        _base_fm("task-breakdown", release=release, total_tasks=len(tasks)),
        body=body,
    )


def _make_detailed_design(
    root: Path, *, release: str = "0.1", task_id: str = "T1"
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/detailed_design.md",
        _base_fm("detailed-design", release=release, task_id=task_id),
    )


def _make_test_review_report(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    review_status: str = "pending",
    blocking: int = 0,
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/test_review_report.md",
        _base_fm(
            "test-review-report",
            release=release,
            task_id=task_id,
            findings_count=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            review_status=review_status,
            blocking_findings_count=blocking,
            max_severity="low",
        ),
    )


def _make_code_review_report(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    review_status: str = "pending",
    blocking: int = 0,
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/code_review_report.md",
        _base_fm(
            "code-review-report",
            release=release,
            task_id=task_id,
            findings_count=0,
            severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
            review_status=review_status,
            blocking_findings_count=blocking,
            max_severity="low",
        ),
    )


def _make_verification_result(
    root: Path,
    *,
    release: str = "0.1",
    task_id: str = "T1",
    verification_status: str = "pass",
) -> None:
    _write_doc(
        root,
        f"docs/release{release}/development/tasks/{task_id}/verification_result.md",
        _base_fm(
            "verification-result",
            release=release,
            task_id=task_id,
            verification_status=verification_status,
        ),
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


def _seed_development(root: Path, *, advance_ts: str | None = None) -> None:
    """Seed init + forge progress.md to development + append a synthetic
    stage-advance history entry so the replay validator (with the test
    handler installed) reproduces the same state.

    The advance timestamp must lie strictly between the init timestamp
    and the system clock now (so subsequent ``update --task`` entries
    are monotonically later). Tests using this helper should also be
    running with ``_FakeClock`` patched so the wall clock is mocked.
    Caller MUST run the test inside ``_install_test_stage_advance_handler``
    or the synthetic event will fail replay.
    """

    _seed(root)
    progress_path = root / "progress.md"
    history_path = root / "progress-history.md"

    if advance_ts is None:
        # Pull a timestamp from the patched _utc_now_iso so it is
        # monotonically after init and before subsequent update entries.
        advance_ts = progress._utc_now_iso()

    doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
    new_fm = dict(doc.frontmatter)
    new_fm["current_stage"] = "development"
    new_fm["sub_state"] = "write"
    new_fm["review_iteration"] = 0
    new_fm["development_state"] = {"task_states": {}}
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )

    advance_entry = HistoryEntry(
        timestamp=advance_ts,
        event=_TEST_ADVANCE_EVENT,
        summary="test-stage-advance current_stage=development sub_state=write",
        agent="test/forge",
        result="forged Stage 4 development entry for Phase 5.3 testing",
        next="update-task",
        raw="",
    )
    new_history = append_history_text(
        history_path.read_text(encoding="utf-8"), advance_entry
    )
    history_path.write_text(new_history, encoding="utf-8")


class _FakeClock:
    """Monotonic synthetic clock for deterministic timestamps in CLI tests.

    Each ``next()`` returns the next second-precision UTC ISO timestamp.
    Used as a side_effect for ``unittest.mock.patch.object(progress,
    '_utc_now_iso', ...)`` so init / update --task / recover all consume
    timestamps from the same monotonically-increasing source.
    """

    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 5, 15, 11, 0, 0, tzinfo=timezone.utc)

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

    def _update_task(self, task_id: str, status: str) -> tuple[int, str, str]:
        return self._run(
            [
                "--root", str(self.root),
                "update", "--task", task_id, "--status", status,
            ]
        )


# ---------- argparse / dispatch ----------


class UpdateTaskArgparseTests(_CliRunner):
    def test_help_runs(self):
        code, out, _ = self._run(["update", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--task", out)
        self.assertIn("--status", out)

    def test_event_and_task_are_mutually_exclusive(self):
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "update", "--event", "write-complete",
                "--task", "T1", "--status", "planning-done",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("not allowed", err)

    def test_task_without_status_returns_2(self):
        _seed(self.root)
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "update", "--task", "T1",
            ]
        )
        self.assertEqual(code, 2)
        self.assertIn("--status is required", err)

    def test_invalid_task_id_format_returns_1(self):
        _seed(self.root)
        # Invalid task_id (lowercase t) is a workflow validation failure,
        # not an argparse failure.
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "update", "--task", "task1", "--status", "planning-done",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("task_id", err)


class UpdateTaskNonDevelopmentTests(_CliRunner):
    def test_update_task_on_prd_inception_rejects(self):
        # Init leaves current_stage=prd-inception. update --task must
        # reject with the development-stage requirement.
        _seed(self.root)
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update_task("T1", "planning-done")
        self.assertEqual(code, 1)
        self.assertIn("current_stage", err)
        self.assertIn("development", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )


# ---------- M1 inheritance ----------


class UpdateTaskM1ConsistencyTests(_CliRunner):
    def test_update_task_inherits_replay_consistency_on_tampered_progress(self):
        # Forge progress.md to development WITHOUT a matching history
        # entry. The M1 replay-consistency check must reject because the
        # forward outcome (built from forged state) diverges from the
        # canonical replay (which produces prd-inception).
        _seed(self.root)
        progress_path = self.root / "progress.md"
        doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
        new_fm = dict(doc.frontmatter)
        new_fm.update({
            "current_stage": "development",
            "development_state": {"task_states": {}},
        })
        progress_path.write_text(
            render_markdown(new_fm, doc.body), encoding="utf-8"
        )
        _make_breakdown(self.root, tasks=("T1",))
        _make_detailed_design(self.root, task_id="T1")

        progress_before = progress_path.read_text(encoding="utf-8")
        history_before = (self.root / "progress-history.md").read_text(encoding="utf-8")

        code, _, err = self._update_task("T1", "planning-done")
        self.assertEqual(code, 1)
        # Either replay rejects update-task because history-derived state
        # has current_stage=prd-inception, or the consistency diff fires.
        self.assertTrue(
            "replay" in err or "consistency" in err,
            f"expected M1-style rejection, got: {err}",
        )
        self.assertEqual(
            progress_path.read_text(encoding="utf-8"), progress_before
        )
        self.assertEqual(
            (self.root / "progress-history.md").read_text(encoding="utf-8"),
            history_before,
        )

    def test_update_task_inherits_malformed_history_rejection(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            history_path = self.root / "progress-history.md"
            history_path.write_text(
                history_path.read_text(encoding="utf-8") + "- bogus: x\n",
                encoding="utf-8",
            )
            history_before = history_path.read_text(encoding="utf-8")
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._update_task("T1", "planning-done")
            self.assertEqual(code, 1)
            self.assertIn("malformed", err)
            self.assertEqual(
                history_path.read_text(encoding="utf-8"), history_before
            )
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


# ---------- happy path with synthetic stage-advance ----------


class UpdateTaskHappyPathTests(_CliRunner):
    def test_planning_done_round_trip(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")

            code, out, err = self._update_task("T1", "planning-done")
            self.assertEqual(code, 0, err)
            self.assertIn("update-task T1=planning-done", out)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "planning-done"},
            )

    def test_full_stage_4_cycle_for_T1(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")

            # 1. planning-done
            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            # 2. test-writing
            self.assertEqual(self._update_task("T1", "test-writing")[0], 0)
            # 3. test-review (skeleton needed)
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            # 4. test-done (pass)
            _make_test_review_report(self.root, review_status="pass", blocking=0)
            self.assertEqual(self._update_task("T1", "test-done")[0], 0)
            # 5. code-writing
            self.assertEqual(self._update_task("T1", "code-writing")[0], 0)
            # 6. code-review (skeleton)
            _make_code_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "code-review")[0], 0)
            # 7. code-review-passed
            _make_code_review_report(self.root, review_status="pass", blocking=0)
            self.assertEqual(self._update_task("T1", "code-review-passed")[0], 0)
            # 8. verifying
            self.assertEqual(self._update_task("T1", "verifying")[0], 0)
            # 9. verified
            _make_verification_result(self.root, verification_status="pass")
            self.assertEqual(self._update_task("T1", "verified")[0], 0)

            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "verified"},
            )

    def test_idempotent_planning_done_does_not_double_register(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")

            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            code, out, err = self._update_task("T1", "planning-done")
            self.assertEqual(code, 0, err)
            self.assertIn("idempotent retry", out)
            # Task state still planning-done; sibling task entries unaffected.
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "planning-done"},
            )

    def test_two_tasks_progress_independently(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1", "T2"))
            _make_detailed_design(self.root, task_id="T1")
            _make_detailed_design(self.root, task_id="T2")

            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            self.assertEqual(self._update_task("T2", "planning-done")[0], 0)
            self.assertEqual(self._update_task("T1", "test-writing")[0], 0)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "test-writing", "T2": "planning-done"},
            )

    def test_history_entry_is_canonical_update_task(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)

            entries = parse_history_text(
                (self.root / "progress-history.md").read_text(encoding="utf-8")
            )
            update_task_entries = [e for e in entries if e.event == "update-task"]
            self.assertEqual(len(update_task_entries), 1)
            entry = update_task_entries[0]
            self.assertIn("task=T1", entry.summary)
            self.assertIn("status=planning-done", entry.summary)


class UpdateTaskRecoverRoundtripTests(_CliRunner):
    def test_recover_rebuilds_dev_state_after_full_cycle(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            self.assertEqual(self._update_task("T1", "test-writing")[0], 0)
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            _make_test_review_report(self.root, review_status="pass", blocking=0)
            self.assertEqual(self._update_task("T1", "test-done")[0], 0)

            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
            self.assertEqual(code, 0, err)
            after_fm = self._read_progress_fm()
            self.assertEqual(
                after_fm["development_state"]["task_states"],
                before_fm["development_state"]["task_states"],
            )
            self.assertEqual(after_fm["current_stage"], "development")


class UpdateTaskArtifactRejectionTests(_CliRunner):
    def test_planning_done_missing_breakdown_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_detailed_design(self.root, task_id="T1")
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            history_before = (self.root / "progress-history.md").read_text(encoding="utf-8")
            code, _, err = self._update_task("T1", "planning-done")
            self.assertEqual(code, 1)
            self.assertIn("task-breakdown", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )
            self.assertEqual(
                (self.root / "progress-history.md").read_text(encoding="utf-8"),
                history_before,
            )

    def test_verified_with_partial_verification_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            self.assertEqual(self._update_task("T1", "test-writing")[0], 0)
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            _make_test_review_report(self.root, review_status="pass")
            self.assertEqual(self._update_task("T1", "test-done")[0], 0)
            self.assertEqual(self._update_task("T1", "code-writing")[0], 0)
            _make_code_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "code-review")[0], 0)
            _make_code_review_report(self.root, review_status="pass")
            self.assertEqual(self._update_task("T1", "code-review-passed")[0], 0)
            self.assertEqual(self._update_task("T1", "verifying")[0], 0)

            _make_verification_result(self.root, verification_status="partial")
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._update_task("T1", "verified")
            self.assertEqual(code, 1)
            self.assertIn("verification_status", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


class UpdateTaskIterationOverLimitTests(_CliRunner):
    """Phase 5.3 round 2 review M1: progress.md whose review_iteration
    is already over the spec cap (0-7) cannot be a base for update --task,
    matching the Phase 5.2 round 2 M2 behavior on update --event."""

    def test_update_task_with_iter_eight_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            # Forge review_iteration to 8 in progress.md only. The
            # synthetic stage-advance entry's replay handler resets
            # review_iteration to 0, so M1 (round 2) replay diff would
            # also catch the divergence — but we want apply_update_task
            # itself to reject at the entry guard, before replay runs.
            progress_path = self.root / "progress.md"
            doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
            new_fm = dict(doc.frontmatter)
            new_fm["review_iteration"] = 8
            progress_path.write_text(
                render_markdown(new_fm, doc.body), encoding="utf-8"
            )

            progress_before = progress_path.read_text(encoding="utf-8")
            history_before = (
                self.root / "progress-history.md"
            ).read_text(encoding="utf-8")

            code, _, err = self._update_task("T1", "planning-done")
            self.assertEqual(code, 1)
            self.assertIn("review_iteration", err)
            self.assertIn("8", err)
            self.assertIn("escalate", err)
            self.assertEqual(
                progress_path.read_text(encoding="utf-8"), progress_before
            )
            self.assertEqual(
                (self.root / "progress-history.md").read_text(encoding="utf-8"),
                history_before,
            )


class UpdateTaskRevisionLoopTests(_CliRunner):
    """Phase 5.3 round 2 review L2: end-to-end CLI smoke for the
    revision-loop branches that the original happy cycle skipped."""

    def test_test_review_test_revising_loop_via_cli(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            self.assertEqual(self._update_task("T1", "planning-done")[0], 0)
            self.assertEqual(self._update_task("T1", "test-writing")[0], 0)
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            # Reviewer flagged issues — revising path.
            self.assertEqual(self._update_task("T1", "test-revising")[0], 0)
            # Caller refreshes skeleton to pending after revising.
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "test-review"},
            )

    def test_code_review_code_revising_loop_via_cli(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")
            for status in (
                "planning-done",
                "test-writing",
            ):
                self.assertEqual(self._update_task("T1", status)[0], 0)
            _make_test_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "test-review")[0], 0)
            _make_test_review_report(self.root, review_status="pass", blocking=0)
            self.assertEqual(self._update_task("T1", "test-done")[0], 0)
            self.assertEqual(self._update_task("T1", "code-writing")[0], 0)
            _make_code_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "code-review")[0], 0)
            # Code reviewer flagged issues.
            self.assertEqual(self._update_task("T1", "code-revising")[0], 0)
            _make_code_review_report(self.root, review_status="pending")
            self.assertEqual(self._update_task("T1", "code-review")[0], 0)
            self.assertEqual(
                self._read_progress_fm()["development_state"]["task_states"],
                {"T1": "code-review"},
            )


class UpdateTaskLockTests(_CliRunner):
    def test_lock_held_blocks_update_task(self):
        with _install_test_stage_advance_handler():
            _seed_development(self.root)
            _make_breakdown(self.root, tasks=("T1",))
            _make_detailed_design(self.root, task_id="T1")

            from skills._shared.dev_workflow.progress_lock import progress_lock

            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            with progress_lock(self.root, timeout=1.0):
                code, _, err = self._run(
                    [
                        "--root", str(self.root),
                        "--lock-timeout", "0.1",
                        "update", "--task", "T1", "--status", "planning-done",
                    ]
                )
            self.assertEqual(code, 1)
            self.assertIn("held by another process", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
