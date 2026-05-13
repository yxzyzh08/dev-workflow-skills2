"""Tests for skills/workflow-protocol/scripts/progress.py init."""

from __future__ import annotations

import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "skills" / "workflow-protocol" / "scripts"
for _path in (_SCRIPTS_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

progress = importlib.import_module("progress")

from skills._shared.dev_workflow.frontmatter import parse_frontmatter  # noqa: E402
from skills._shared.dev_workflow.progress_history import parse_history_text  # noqa: E402


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

    def _read_progress(self) -> dict:
        return parse_frontmatter(
            (self.root / "progress.md").read_text(encoding="utf-8")
        ).frontmatter


class InitHappyPathTests(_CliRunner):
    def test_init_s1_creates_both_files(self):
        code, out, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("created progress.md and progress-history.md", out)
        self.assertTrue((self.root / "progress.md").exists())
        self.assertTrue((self.root / "progress-history.md").exists())

    def test_init_s3_supported(self):
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "LegacyMig",
                "--scenario", "S3",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 0, err)

    def test_init_progress_frontmatter_has_all_required_fields(self):
        self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        fm = self._read_progress()
        for key in (
            "project_name",
            "workflow_version",
            "project_state",
            "release",
            "release_state",
            "release_close_reason",
            "previous_releases",
            "scenario",
            "scenario_subtype",
            "current_stage",
            "sub_state",
            "review_iteration",
            "artifacts",
            "bug_flow",
            "workflow_incident_active",
            "incident_report_path",
            "unresolved_bugs",
            "created",
            "updated",
        ):
            self.assertIn(key, fm, f"missing field: {key}")
        self.assertEqual(fm["project_name"], "MyApp")
        self.assertEqual(fm["workflow_version"], "v0.6")
        self.assertEqual(fm["project_state"], "active")
        self.assertEqual(fm["release"], "0.1")
        self.assertEqual(fm["release_state"], "active")
        self.assertEqual(fm["scenario"], "S1")
        self.assertIsNone(fm["scenario_subtype"])
        self.assertEqual(fm["current_stage"], "prd-inception")
        self.assertEqual(fm["sub_state"], "write")
        self.assertEqual(fm["review_iteration"], 0)
        self.assertEqual(fm["previous_releases"], [])
        self.assertEqual(fm["unresolved_bugs"], [])
        self.assertFalse(fm["workflow_incident_active"])
        self.assertIsNone(fm["incident_report_path"])
        self.assertEqual(
            fm["bug_flow"],
            {"active": False, "bug_report_path": None, "root_cause": None},
        )
        self.assertEqual(
            fm["artifacts"]["prd"], "docs/prd/prd.md"
        )
        self.assertEqual(
            fm["artifacts"]["srs"], "docs/release0.1/srs/srs.md"
        )
        self.assertIsNone(fm["artifacts"]["integration_plan"])
        self.assertEqual(fm["created"], fm["updated"])

    def test_init_history_first_entry_is_init(self):
        self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        history_text = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )
        entries = parse_history_text(history_text)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry.event, "init")
        self.assertIn("project=MyApp", entry.summary)
        self.assertIn("scenario=S1", entry.summary)
        self.assertIn("release=0.1", entry.summary)


class InitRejectionTests(_CliRunner):
    def test_init_refuses_to_overwrite_existing_progress(self):
        (self.root / "progress.md").write_text("placeholder", encoding="utf-8")
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to overwrite", err)

    def test_init_refuses_to_overwrite_existing_history(self):
        (self.root / "progress-history.md").write_text(
            "placeholder", encoding="utf-8"
        )
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to overwrite", err)

    def test_init_invalid_scenario_returns_1(self):
        # Phase 5.1 round 2 (M2): scenario validation is a workflow
        # precondition error, not a CLI usage error. It must exit with
        # code 1, the same path as --release / --project, and must not
        # leave a half-written progress.md / progress-history.md behind.
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S2",  # init scenario whitelist is {S1, S3}
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("scenario", err)
        # No file should be created when validation fails.
        self.assertFalse((self.root / "progress.md").exists())
        self.assertFalse((self.root / "progress-history.md").exists())

    def test_init_invalid_scenario_subtype_also_returns_1(self):
        # Reject S2-1 / S2-2 / S2-3 / S2-4 via the same path: they belong
        # to release-start (Phase 5.4), not init. The choices= guard
        # previously routed these as code 2 too; the round 2 fix keeps
        # them on the code 1 validation path.
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S2-1",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("scenario", err)
        self.assertFalse((self.root / "progress.md").exists())
        self.assertFalse((self.root / "progress-history.md").exists())

    def test_init_invalid_release_returns_1(self):
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1.1",  # patch level not allowed
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("release", err)

    def test_init_invalid_project_name_returns_1(self):
        code, _, err = self._run(
            [
                "--root", str(self.root),
                "init", "--project", "1bad/name",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("project name", err)

    def test_init_no_subcommand_returns_2(self):
        code, _, err = self._run(["--root", str(self.root)])
        self.assertEqual(code, 2)


class InitAtomicityTests(_CliRunner):
    def test_init_creates_both_files_or_neither_if_lock_busy(self):
        # Acquire the lock so init's lock acquire fails fast.
        from skills._shared.dev_workflow.progress_lock import progress_lock

        with progress_lock(self.root, timeout=1.0):
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "--lock-timeout", "0.1",
                    "init", "--project", "MyApp",
                    "--scenario", "S1",
                    "--release", "0.1",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)
        self.assertFalse((self.root / "progress.md").exists())
        self.assertFalse((self.root / "progress-history.md").exists())


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
