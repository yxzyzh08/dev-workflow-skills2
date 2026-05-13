"""CLI integration tests for progress.py release-close + release-start.

Phase 5.4 has no public way to walk current_stage from prd-inception
all the way to project-retrospective via the CLI alone (advance is
Phase 6). Tests therefore install a temporary ``test-stage-advance``
replay handler — same pattern as Phase 5.3 — that lets
``_seed_stage_7`` forge progress.md to ``project-retrospective /
review-passed`` while keeping replay consistent.
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


_TEST_ADVANCE_EVENT = "test-stage-advance"


def _test_stage_advance_handler(state, entry, root):
    """Synthetic replay handler that mutates state per summary tokens.

    Recognised tokens (key=value):
      * ``current_stage`` — set new current_stage
      * ``sub_state`` — set new sub_state
      * ``release_state`` — set new release_state
      * ``release_close_reason`` — set or clear (token "null" → None)
      * ``previous_releases`` — colon-separated list, e.g. "0.1:0.2"
        (use empty string for [])
    """

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


# ---------- fixture helpers ----------


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


def _append_synthetic_advance(
    root: Path,
    *,
    timestamp: str,
    summary: str,
) -> None:
    """Append a synthetic test-stage-advance entry to history + sync progress.md."""

    history_path = root / "progress-history.md"
    progress_path = root / "progress.md"

    entry = HistoryEntry(
        timestamp=timestamp,
        event=_TEST_ADVANCE_EVENT,
        summary=summary,
        agent="test/forge",
        result="forged for Phase 5.4 testing",
        next=None,
        raw="",
    )
    history_path.write_text(
        append_history_text(
            history_path.read_text(encoding="utf-8"), entry
        ),
        encoding="utf-8",
    )

    # Mirror the mutation onto progress.md so apply_* sees consistent state.
    doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
    new_fm = dict(doc.frontmatter)
    for token in summary.split():
        if "=" in token:
            key, _, value = token.partition("=")
            if key in {"current_stage", "sub_state", "release_state"}:
                new_fm[key] = value
            elif key == "review_iteration":
                new_fm[key] = int(value)
            elif key == "release_close_reason":
                new_fm[key] = None if value == "null" else value
            elif key == "previous_releases":
                new_fm[key] = [] if value == "" else value.split(":")
    new_fm["updated"] = timestamp
    progress_path.write_text(
        render_markdown(new_fm, doc.body), encoding="utf-8"
    )


def _seed_stage_7(root: Path) -> None:
    """Seed init + forge state to project-retrospective / review-passed.

    Caller MUST be inside ``_install_test_stage_advance_handler``.
    """

    _seed(root)
    advance_ts = progress._utc_now_iso()
    _append_synthetic_advance(
        root,
        timestamp=advance_ts,
        summary="test-stage-advance current_stage=project-retrospective sub_state=review-passed",
    )


def _seed_post_close(root: Path) -> None:
    """Seed init + forge state to closed (post-release-close window)."""

    _seed(root)
    advance_ts = progress._utc_now_iso()
    _append_synthetic_advance(
        root,
        timestamp=advance_ts,
        summary=(
            "test-stage-advance current_stage=project-retrospective "
            "sub_state=review-passed release_state=closed "
            "release_close_reason=stage-7-completed previous_releases=0.1"
        ),
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


# ---------- release-close ----------


class ReleaseCloseHappyTests(_CliRunner):
    def test_release_close_marks_closed(self):
        with _install_test_stage_advance_handler():
            _seed_stage_7(self.root)
            code, out, err = self._run(
                ["--root", str(self.root), "release-close"]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["release_state"], "closed")
            self.assertEqual(fm["release_close_reason"], "stage-7-completed")
            self.assertEqual(fm["previous_releases"], ["0.1"])
            self.assertIn("release-close", out)

    def test_release_close_history_entry_recorded(self):
        with _install_test_stage_advance_handler():
            _seed_stage_7(self.root)
            self._run(["--root", str(self.root), "release-close"])
            entries = parse_history_text(
                (self.root / "progress-history.md").read_text(encoding="utf-8")
            )
            close_entries = [e for e in entries if e.event == "release-close"]
            self.assertEqual(len(close_entries), 1)
            self.assertIn("release 0.1 closed", close_entries[0].summary)


class ReleaseCloseRejectionTests(_CliRunner):
    def test_release_close_on_non_retrospective_stage_returns_1(self):
        _seed(self.root)
        # Forge state to delivery (not project-retrospective).
        progress_path = self.root / "progress.md"
        doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
        new_fm = dict(doc.frontmatter)
        new_fm["current_stage"] = "delivery"
        new_fm["sub_state"] = "review-passed"
        progress_path.write_text(
            render_markdown(new_fm, doc.body), encoding="utf-8"
        )
        before = progress_path.read_text(encoding="utf-8")
        code, _, err = self._run(
            ["--root", str(self.root), "release-close"]
        )
        self.assertEqual(code, 1)
        self.assertIn("project-retrospective", err)
        self.assertEqual(
            progress_path.read_text(encoding="utf-8"), before,
        )


# ---------- release-start ----------


class ReleaseStartHappyTests(_CliRunner):
    def test_release_start_S2_1_full_cycle(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 0, err)
            fm = self._read_progress_fm()
            self.assertEqual(fm["release"], "0.2")
            self.assertEqual(fm["release_state"], "active")
            self.assertIsNone(fm["release_close_reason"])
            self.assertEqual(fm["scenario"], "S2")
            self.assertEqual(fm["scenario_subtype"], "S2-1")
            self.assertEqual(fm["current_stage"], "prd-inception")
            self.assertEqual(fm["sub_state"], "write")
            self.assertEqual(fm["unresolved_bugs"], [])

    def test_release_start_with_unresolved_bugs_fans_out_to_BUG_files(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            # Add 2 BUG files and bug-intake them.
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001"),
            )
            _write_doc(
                self.root, "docs/bug/BUG-002.md",
                _bug_fm("BUG-002"),
            )
            self.assertEqual(
                self._run(
                    ["--root", str(self.root), "bug-intake",
                     "--bug", "docs/bug/BUG-001.md"]
                )[0], 0,
            )
            self.assertEqual(
                self._run(
                    ["--root", str(self.root), "bug-intake",
                     "--bug", "docs/bug/BUG-002.md"]
                )[0], 0,
            )

            code, out, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 0, err)
            self.assertIn("consumed 2", out)

            # Both BUG frontmatters now have target_release / consumed_in_release set.
            for bug_id in ("BUG-001", "BUG-002"):
                bug_fm = parse_frontmatter(
                    (self.root / f"docs/bug/{bug_id}.md").read_text(encoding="utf-8")
                ).frontmatter
                self.assertEqual(bug_fm["target_release"], "0.2")
                self.assertEqual(bug_fm["consumed_in_release"], "0.2")

            # progress.md unresolved_bugs is now empty.
            self.assertEqual(self._read_progress_fm()["unresolved_bugs"], [])

    def test_release_start_recover_roundtrip_preserves_state(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            before_fm = self._read_progress_fm()
            (self.root / "progress.md").unlink()
            code, _, err = self._run(
                ["--root", str(self.root), "recover", "--confirm"]
            )
            self.assertEqual(code, 0, err)
            after_fm = self._read_progress_fm()
            self.assertEqual(after_fm["release"], before_fm["release"])
            self.assertEqual(after_fm["scenario_subtype"], before_fm["scenario_subtype"])
            self.assertEqual(
                after_fm["current_stage"], before_fm["current_stage"],
            )
            self.assertEqual(
                after_fm["unresolved_bugs"], before_fm["unresolved_bugs"],
            )


class ReleaseStartRejectionTests(_CliRunner):
    def test_version_not_strictly_greater_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.1",  # equal to existing
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("strictly greater", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )

    def test_invalid_scenario_returns_1(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-4",  # forbidden
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("scenario_subtype", err)

    def test_missing_version_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 2)

    def test_missing_scenario_returns_2(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                ]
            )
            self.assertEqual(code, 2)

    def test_release_start_rejects_outside_root_unresolved_bug_path(self):
        # Phase 5.4 round 2 review M1: even if progress.md's
        # unresolved_bugs list somehow contains an outside-root path
        # (corrupted history, hand-edit), release-start must refuse to
        # fan out writes there. Forward path's _read_bug_for_release_start
        # rejects with ProgressArtifactError before the transaction.
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            # Forge progress.md unresolved_bugs to contain a bad path.
            progress_path = self.root / "progress.md"
            doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
            new_fm = dict(doc.frontmatter)
            new_fm["unresolved_bugs"] = ["../etc/BUG-001.md"]
            progress_path.write_text(
                render_markdown(new_fm, doc.body), encoding="utf-8"
            )
            progress_before = progress_path.read_text(encoding="utf-8")
            history_before = (self.root / "progress-history.md").read_text(encoding="utf-8")

            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 1)
            # Forward path catches the bad path either via apply_bug_intake's
            # share validator (already in unresolved_bugs at apply time
            # would not be re-validated, so the rejection actually happens
            # in _read_bug_for_release_start). Either error message is
            # acceptable as long as it's exit 1 with no fan-out.
            self.assertTrue(
                "'.' or '..'" in err or "outside" in err or "BUG-NNN.md" in err,
                f"expected path-shape rejection, got: {err}",
            )
            # No file should have been touched by the fan-out.
            self.assertEqual(
                progress_path.read_text(encoding="utf-8"), progress_before,
            )
            self.assertEqual(
                (self.root / "progress-history.md").read_text(encoding="utf-8"),
                history_before,
            )

    def test_release_start_rejects_absolute_unresolved_bug_path(self):
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            progress_path = self.root / "progress.md"
            doc = parse_frontmatter(progress_path.read_text(encoding="utf-8"))
            new_fm = dict(doc.frontmatter)
            new_fm["unresolved_bugs"] = ["/etc/BUG-001.md"]
            progress_path.write_text(
                render_markdown(new_fm, doc.body), encoding="utf-8"
            )
            progress_before = progress_path.read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("absolute", err)
            self.assertEqual(
                progress_path.read_text(encoding="utf-8"), progress_before,
            )

    def test_BUG_with_target_release_set_rejects_release_start(self):
        # If a BUG was already consumed by a prior release (target_release
        # non-null), release-start must reject and not write any file.
        with _install_test_stage_advance_handler():
            _seed_post_close(self.root)
            # bug-intake first.
            _write_doc(
                self.root, "docs/bug/BUG-001.md",
                _bug_fm("BUG-001"),
            )
            self._run(
                ["--root", str(self.root), "bug-intake",
                 "--bug", "docs/bug/BUG-001.md"]
            )
            # Forge BUG to already have target_release set (out-of-band).
            bug_path = self.root / "docs/bug/BUG-001.md"
            bug_doc = parse_frontmatter(bug_path.read_text(encoding="utf-8"))
            new_bug_fm = dict(bug_doc.frontmatter)
            new_bug_fm["target_release"] = "0.2"
            bug_path.write_text(
                render_markdown(new_bug_fm, bug_doc.body), encoding="utf-8"
            )

            progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
            history_before = (self.root / "progress-history.md").read_text(encoding="utf-8")
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "release-start",
                    "--version", "0.2",
                    "--scenario", "S2-1",
                ]
            )
            self.assertEqual(code, 1)
            self.assertIn("target_release", err)
            self.assertEqual(
                (self.root / "progress.md").read_text(encoding="utf-8"),
                progress_before,
            )
            self.assertEqual(
                (self.root / "progress-history.md").read_text(encoding="utf-8"),
                history_before,
            )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
