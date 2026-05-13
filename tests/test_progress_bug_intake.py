"""CLI integration tests for progress.py bug-intake."""

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


# ---------- test-only stage-advance handler (mirrors release-lifecycle tests) ----------


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
    if "release_state" in tokens:
        new_state["release_state"] = tokens["release_state"]
    if "release_close_reason" in tokens:
        v = tokens["release_close_reason"]
        new_state["release_close_reason"] = None if v == "null" else v
    if "previous_releases" in tokens:
        v = tokens["previous_releases"]
        new_state["previous_releases"] = [] if v == "" else v.split(":")
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


def _bug_fm(bug_id: str, **extra) -> dict:
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
        "root_cause": None,
        "consumed_in_release": None,
    }
    fm.update(extra)
    return fm


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


def _seed_post_close(root: Path) -> None:
    _seed(root)
    advance_ts = progress._utc_now_iso()
    history_path = root / "progress-history.md"
    progress_path = root / "progress.md"

    entry = HistoryEntry(
        timestamp=advance_ts,
        event=_TEST_ADVANCE_EVENT,
        summary=(
            "test-stage-advance current_stage=project-retrospective "
            "sub_state=review-passed release_state=closed "
            "release_close_reason=stage-7-completed previous_releases=0.1"
        ),
        agent="test/forge",
        result="forged for Phase 5.4 testing",
        next=None,
        raw="",
    )
    history_path.write_text(
        append_history_text(history_path.read_text(encoding="utf-8"), entry),
        encoding="utf-8",
    )

    doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
    new_fm = dict(doc.frontmatter)
    new_fm["current_stage"] = "project-retrospective"
    new_fm["sub_state"] = "review-passed"
    new_fm["release_state"] = "closed"
    new_fm["release_close_reason"] = "stage-7-completed"
    new_fm["previous_releases"] = ["0.1"]
    new_fm["updated"] = advance_ts
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


class _FakeClock:
    def __init__(self, *, start: datetime | None = None) -> None:
        self._cursor = start or datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)

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

    def _intake(self, bug_path: str) -> tuple[int, str, str]:
        return self._run(
            ["--root", str(self.root), "bug-intake", "--bug", bug_path]
        )


class BugIntakeHappyTests(_CliRunner):
    def test_first_intake_appends_relative_path(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            code, out, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 0, err)
            self.assertEqual(
                self._read_progress_fm()["unresolved_bugs"],
                ["docs/bug/BUG-001.md"],
            )
            self.assertIn("bug-intake docs/bug/BUG-001.md", out)

    def test_history_entry_has_canonical_token(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            _write_doc(self.root, "docs/bug/BUG-007.md", _bug_fm("BUG-007"))
            self._intake("docs/bug/BUG-007.md")
            entries = parse_history_text(
                (self.root / "progress-history.md").read_text(encoding="utf-8")
            )
            intake_entries = [e for e in entries if e.event == "bug-intake"]
            self.assertEqual(len(intake_entries), 1)
            self.assertIn("bug=docs/bug/BUG-007.md", intake_entries[0].summary)

    def test_multiple_intakes_accumulate(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            _write_doc(self.root, "docs/bug/BUG-002.md", _bug_fm("BUG-002"))
            self._intake("docs/bug/BUG-001.md")
            self._intake("docs/bug/BUG-002.md")
            self.assertEqual(
                self._read_progress_fm()["unresolved_bugs"],
                ["docs/bug/BUG-001.md", "docs/bug/BUG-002.md"],
            )

    def test_recover_roundtrip_preserves_unresolved_bugs(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            self._intake("docs/bug/BUG-001.md")
            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
            self.assertEqual(code, 0, err)
            after_fm = self._read_progress_fm()
            self.assertEqual(
                after_fm["unresolved_bugs"], before_fm["unresolved_bugs"],
            )


class BugIntakeRejectionTests(_CliRunner):
    def test_intake_during_active_release_returns_1(self):
        # No release-close yet → release_state=active → bug-intake illegal.
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            # Re-forge to active.
            progress_path = self.root / "progress.md"
            doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
            new_fm = dict(doc.frontmatter)
            new_fm["release_state"] = "active"
            progress_path.write_text(
                render_markdown(new_fm, doc.body), encoding="utf-8"
            )
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            progress_before = progress_path.read_text(encoding="utf-8")
            code, _, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 1)
            # Progress.md may have its release_state forged, but no append happened.
            after_fm = parse_frontmatter(
                progress_path.read_text(encoding="utf-8")
            ).frontmatter
            self.assertEqual(after_fm.get("unresolved_bugs"), [])

    def test_missing_BUG_file_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            code, _, err = self._intake("docs/bug/BUG-404.md")
            self.assertEqual(code, 1)
            self.assertIn("not found", err)

    def test_BUG_wrong_type_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            # Write a doc that has bug-report path but wrong type.
            fm = _bug_fm("BUG-001")
            fm["type"] = "test-report"
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 1)
            self.assertIn("'bug-report'", err)

    def test_BUG_with_target_release_set_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            fm = _bug_fm("BUG-001", target_release="0.1")
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 1)
            self.assertIn("target_release", err)

    def test_BUG_with_consumed_in_release_set_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            fm = _bug_fm("BUG-001", consumed_in_release="0.1")
            _write_doc(self.root, "docs/bug/BUG-001.md", fm)
            code, _, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 1)
            self.assertIn("consumed_in_release", err)

    def test_duplicate_intake_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            _write_doc(self.root, "docs/bug/BUG-001.md", _bug_fm("BUG-001"))
            self.assertEqual(self._intake("docs/bug/BUG-001.md")[0], 0)
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._intake("docs/bug/BUG-001.md")
            self.assertEqual(code, 1)
            self.assertIn("duplicate", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
