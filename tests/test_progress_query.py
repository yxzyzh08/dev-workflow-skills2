"""Tests for skills/workflow-protocol/scripts/progress.py query."""

from __future__ import annotations

import importlib
import io
import json
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


def _seed(root: Path) -> None:
    """Run init to drop a known progress.md / progress-history.md pair.

    Suppresses init's stdout/stderr to keep test output tidy when many
    tests share this fixture.
    """

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
        raise RuntimeError(f"init failed during seed: code={code}, err={err.getvalue()}")


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


class QueryYamlOutputTests(_CliRunner):
    def test_query_full_state_yaml(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query"]
        )
        self.assertEqual(code, 0, err)
        loaded = yaml.safe_load(out)
        self.assertEqual(loaded["project_name"], "MyApp")
        self.assertEqual(loaded["scenario"], "S1")
        self.assertEqual(loaded["current_stage"], "prd-inception")

    def test_query_full_state_json(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--json"]
        )
        self.assertEqual(code, 0, err)
        loaded = json.loads(out)
        self.assertEqual(loaded["project_name"], "MyApp")
        self.assertFalse(loaded["bug_flow"]["active"])


class QueryFieldTests(_CliRunner):
    def test_query_scalar_field(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--field", "current_stage"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "prd-inception")

    def test_query_int_field(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--field", "review_iteration"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "0")

    def test_query_null_field(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--field", "incident_report_path"]
        )
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "null")

    def test_query_dict_field_yaml(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--field", "bug_flow"]
        )
        self.assertEqual(code, 0, err)
        loaded = yaml.safe_load(out)
        self.assertEqual(
            loaded,
            {"active": False, "bug_report_path": None, "root_cause": None},
        )

    def test_query_dict_field_json(self):
        _seed(self.root)
        code, out, err = self._run(
            ["--root", str(self.root), "query", "--field", "bug_flow", "--json"]
        )
        self.assertEqual(code, 0, err)
        loaded = json.loads(out)
        self.assertEqual(
            loaded,
            {"active": False, "bug_report_path": None, "root_cause": None},
        )

    def test_query_unknown_field_returns_1(self):
        _seed(self.root)
        code, _, err = self._run(
            ["--root", str(self.root), "query", "--field", "nonexistent"]
        )
        self.assertEqual(code, 1)
        self.assertIn("not present", err)


class QueryMissingFileTests(_CliRunner):
    def test_query_without_progress_file_returns_1(self):
        code, _, err = self._run(["--root", str(self.root), "query"])
        self.assertEqual(code, 1)
        self.assertIn("not found", err)

    def test_query_with_corrupt_progress_returns_1(self):
        (self.root / "progress.md").write_text(
            "no frontmatter here", encoding="utf-8"
        )
        code, _, err = self._run(["--root", str(self.root), "query"])
        self.assertEqual(code, 1)
        self.assertIn("frontmatter", err)


class QueryConcurrentReadTests(_CliRunner):
    def test_query_does_not_acquire_lock(self):
        # Hold the .progress.lock and verify query can still read.
        _seed(self.root)
        from skills._shared.dev_workflow.progress_lock import progress_lock

        with progress_lock(self.root, timeout=1.0):
            code, out, err = self._run(
                ["--root", str(self.root),
                 "--lock-timeout", "0.1",
                 "query", "--field", "scenario"]
            )
        self.assertEqual(code, 0, err)
        self.assertEqual(out.strip(), "S1")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
