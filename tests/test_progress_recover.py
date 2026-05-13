"""Tests for skills/workflow-protocol/scripts/progress.py recover."""

from __future__ import annotations

import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "skills" / "workflow-protocol" / "scripts"
for _path in (_SCRIPTS_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

progress = importlib.import_module("progress")

from skills._shared.dev_workflow.frontmatter import parse_frontmatter  # noqa: E402
from skills._shared.dev_workflow.progress_history import (  # noqa: E402
    HISTORY_TITLE_LINE,
    HistoryEntry,
    append_history_text,
    initial_history_text,
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


class _CliRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
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


class RecoverConfirmGuardTests(_CliRunner):
    def test_recover_without_confirm_rejects(self):
        _seed(self.root)
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._run(
            ["--root", str(self.root), "recover"]
        )
        self.assertEqual(code, 1)
        self.assertIn("--confirm", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )


class RecoverHappyPathTests(_CliRunner):
    def test_recover_rebuilds_progress_from_history(self):
        _seed(self.root)
        # Corrupt progress.md but leave history intact.
        (self.root / "progress.md").write_text(
            "garbage frontmatter", encoding="utf-8"
        )
        code, out, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("rebuilt progress.md", out)
        fm = self._read_progress_fm()
        self.assertEqual(fm["project_name"], "MyApp")
        self.assertEqual(fm["current_stage"], "prd-inception")
        self.assertEqual(fm["sub_state"], "write")

    def test_recover_works_when_progress_missing(self):
        _seed(self.root)
        (self.root / "progress.md").unlink()
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 0, err)
        self.assertTrue((self.root / "progress.md").exists())

    def test_recover_does_not_modify_history(self):
        _seed(self.root)
        history_before = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )
        (self.root / "progress.md").write_text("garbage", encoding="utf-8")
        self._run(["--root", str(self.root), "recover", "--confirm"])
        history_after = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(history_before, history_after)

    def test_recover_updates_updated_field(self):
        _seed(self.root)
        original_fm = self._read_progress_fm()
        (self.root / "progress.md").write_text("garbage", encoding="utf-8")
        # Sleep is unnecessary because _utc_now_iso is second precision —
        # the test instead asserts that updated is a valid timestamp string
        # without enforcing strict greater-than ordering against the seed.
        self._run(["--root", str(self.root), "recover", "--confirm"])
        new_fm = self._read_progress_fm()
        self.assertEqual(new_fm["created"], original_fm["created"])
        self.assertRegex(
            new_fm["updated"],
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )


class RecoverHistoryGuardTests(_CliRunner):
    def test_recover_rejects_missing_history(self):
        # No init; no history file.
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_recover_rejects_empty_history(self):
        (self.root / "progress-history.md").write_text(
            HISTORY_TITLE_LINE, encoding="utf-8"
        )
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 1)
        self.assertIn("empty", err)

    def test_recover_rejects_history_with_unsupported_event(self):
        # Phase 6.4 closes Phase 6 with 15 supported events. Any
        # synthetic / future / corrupt event name must reject during
        # replay rather than silently truncate.
        init_entry = HistoryEntry(
            timestamp="2026-05-15T10:00:00Z",
            event="init",
            summary="project created — project=MyApp, scenario=S1, release=0.1",
            agent="claude-opus-4-7/workflow-init",
            result=None,
            next="prd-write",
            raw="",
        )
        future_entry = HistoryEntry(
            timestamp="2026-05-16T11:00:00Z",
            event="synthetic-test-event",
            summary="should never be supported",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        text = initial_history_text(init_entry)
        text = append_history_text(text, future_entry)
        (self.root / "progress-history.md").write_text(text, encoding="utf-8")
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 1)
        self.assertIn("not supported", err)
        self.assertIn("synthetic-test-event", err)
        # progress.md must not have been written.
        self.assertFalse((self.root / "progress.md").exists())

    def test_recover_rejects_corrupt_history_format(self):
        (self.root / "progress-history.md").write_text(
            "## not a valid header\n", encoding="utf-8"
        )
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 1)
        self.assertIn("history", err.lower())


class RecoverLockingTests(_CliRunner):
    def test_recover_acquires_lock(self):
        _seed(self.root)
        from skills._shared.dev_workflow.progress_lock import progress_lock

        with progress_lock(self.root, timeout=1.0):
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "--lock-timeout", "0.1",
                    "recover", "--confirm",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
