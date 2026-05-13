"""Tests for skills/doc-guardian/scripts/validate.py consistency.

Phase 6.4 / Class 8: cross-progress consistency check. Builds a real
progress.md + the per-stage required artifacts in a tempdir, then
asserts that ``check_consistency`` returns an empty issue list (happy)
or specific issue strings (reject).
"""

from __future__ import annotations

import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "skills" / "doc-guardian" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

validate_module = importlib.import_module("validate")
check_consistency = validate_module.check_consistency
validate_main = validate_module.main


# ---------- helpers ----------


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _build_doc(
    fm: dict,
    body: str = "# Title\n\nContent.\n",
    pending: str | None = None,
    change_log: str | None = None,
) -> str:
    text = f"---\n{_emit_yaml(fm)}\n---\n{body}"
    if pending is not None:
        text += f"\n## Pending Changes\n{pending}\n" if pending else "\n## Pending Changes\n\n"
    if change_log is not None:
        text += f"\n## Change Log\n{change_log}\n" if change_log else "\n## Change Log\n\n"
    return text


def _empty_changelog() -> str:
    return "### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: 初始版本"


def _base_universal(
    *,
    title: str,
    type_: str,
    status: str = "draft",
    owner: str = "claude-opus-4-7/srs-write",
    created: str = "2026-05-15T10:00:00Z",
    updated: str = "2026-05-15T10:00:00Z",
) -> dict:
    return {
        "title": title,
        "type": type_,
        "status": status,
        "created": created,
        "updated": updated,
        "owner": owner,
    }


def _progress_fm(
    *,
    current_stage: str,
    scenario: str = "S1",
    sub_state: str = "review-passed",
    release: str = "0.1",
    task_states: dict | None = None,
) -> dict:
    fm = {
        "project_name": "MyApp",
        "workflow_version": "v0.6",
        "project_state": "active",
        "release": release,
        "release_state": "active",
        "release_close_reason": None,
        "previous_releases": [],
        "scenario": scenario,
        "scenario_subtype": None,
        "current_stage": current_stage,
        "sub_state": sub_state,
        "review_iteration": 0,
        "artifacts": {
            "prd": "docs/prd/prd.md",
        },
        "bug_flow": {
            "active": False,
            "bug_report_path": None,
            "root_cause": None,
        },
        "workflow_incident_active": False,
        "incident_report_path": None,
        "unresolved_bugs": [],
        "development_state": (
            {"task_states": dict(task_states)} if task_states is not None else None
        ),
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-05-15T10:00:00Z",
    }
    return fm


def _write_progress(root: Path, fm: dict) -> None:
    text = f"---\n{_emit_yaml(fm)}\n---\n# Current Stage Summary\n\n# Recent Activity\n"
    (root / "progress.md").write_text(text, encoding="utf-8")


# ---------- happy paths ----------


class HappyPathTests(unittest.TestCase):
    """A consistent project with all required artifacts on disk should
    return an empty issue list."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_prd_inception_with_prd_present(self):
        # required-artifacts S1 prd-inception → docs/prd/prd.md only
        # (no PRD supporting docs in MVP map).
        _write_progress(self.root, _progress_fm(current_stage="prd-inception"))
        prd_fm = _base_universal(
            title="MyApp PRD", type_="prd", status="draft",
            owner="claude-opus-4-7/prd-write",
        )
        _write(
            self.root, "docs/prd/prd.md",
            _build_doc(prd_fm, pending="", change_log=_empty_changelog()),
        )
        self.assertEqual(check_consistency(self.root), [])

    def test_workflow_incident_analysis_skipped(self):
        # Pseudo-stage: consistency returns [] without consulting the
        # P6 matrix (per required-artifacts.md §9).
        _write_progress(
            self.root,
            _progress_fm(current_stage="workflow-incident-analysis"),
        )
        # Even with no docs on disk, consistency is vacuously OK here.
        self.assertEqual(check_consistency(self.root), [])


# ---------- reject paths ----------


class RejectPathTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_progress_returns_issue(self):
        issues = check_consistency(self.root)
        self.assertEqual(len(issues), 1)
        self.assertIn("progress.md not found", issues[0])

    def test_malformed_progress_returns_issue(self):
        (self.root / "progress.md").write_text(
            "no yaml frontmatter here\n", encoding="utf-8"
        )
        issues = check_consistency(self.root)
        self.assertTrue(
            any("malformed" in i.lower() for i in issues)
            or any("frontmatter" in i.lower() for i in issues),
            f"unexpected issues: {issues}",
        )

    def test_missing_required_artifact(self):
        # progress claims prd-inception but docs/prd/prd.md doesn't exist.
        _write_progress(self.root, _progress_fm(current_stage="prd-inception"))
        issues = check_consistency(self.root)
        self.assertTrue(
            any("required artifact missing" in i and "docs/prd/prd.md" in i for i in issues),
            f"unexpected issues: {issues}",
        )

    def test_artifact_present_but_invalid(self):
        # progress claims prd-inception; PRD exists but has a broken
        # frontmatter (missing required field).
        _write_progress(self.root, _progress_fm(current_stage="prd-inception"))
        # Drop required field from PRD frontmatter.
        broken_fm = _base_universal(
            title="MyApp PRD", type_="prd", status="draft",
            owner="claude-opus-4-7/prd-write",
        )
        del broken_fm["status"]  # missing universal field → class 3 fail
        _write(
            self.root, "docs/prd/prd.md",
            _build_doc(broken_fm, pending="", change_log=_empty_changelog()),
        )
        issues = check_consistency(self.root)
        self.assertTrue(
            any("docs/prd/prd.md:" in i for i in issues),
            f"expected per-file issue prefixed with the artifact path: {issues}",
        )

    def test_unknown_current_stage_in_progress(self):
        # current_stage value not in STAGE_KEY_BY_STAGE → ArtifactError
        # surfaces as a single consistency issue.
        fm = _progress_fm(current_stage="testing")
        fm["current_stage"] = "made-up-stage"
        _write_progress(self.root, fm)
        issues = check_consistency(self.root)
        self.assertTrue(
            any("required-artifact derivation failed" in i for i in issues),
            f"unexpected issues: {issues}",
        )

    def test_missing_current_stage_field(self):
        fm = _progress_fm(current_stage="testing")
        del fm["current_stage"]
        _write_progress(self.root, fm)
        issues = check_consistency(self.root)
        self.assertTrue(
            any("current_stage is required" in i for i in issues),
            f"unexpected issues: {issues}",
        )


class StructurallyIncompleteProgressTests(unittest.TestCase):
    """Round 2 M2 regression: progress.md may parse as YAML but still
    be missing resolver-required fields (scenario / release / etc.) or
    have wrong types. ``check_consistency`` must convert any
    ``KeyError`` / ``TypeError`` / ``AttributeError`` from the artifacts
    resolver into a clean exit-1 issue rather than a Python traceback."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_missing_scenario_field_returns_clean_diagnostic(self):
        fm = _progress_fm(current_stage="prd-inception")
        del fm["scenario"]
        _write_progress(self.root, fm)
        issues = check_consistency(self.root)
        self.assertTrue(
            any("structurally incomplete" in i for i in issues),
            f"unexpected issues: {issues}",
        )

    def test_non_string_release_returns_clean_diagnostic(self):
        fm = _progress_fm(current_stage="prd-inception")
        # render_path(progress) reads progress.release as a str field;
        # a numeric release (YAML 0.1 instead of "0.1") trips
        # progress_from_mapping's str() coercion for some inputs but
        # cleaner to delete release entirely to force KeyError.
        del fm["release"]
        _write_progress(self.root, fm)
        issues = check_consistency(self.root)
        self.assertTrue(
            any("structurally incomplete" in i for i in issues),
            f"unexpected issues: {issues}",
        )

    def test_cli_returns_exit_1_for_structurally_incomplete(self):
        # End-to-end: malformed-but-parseable progress.md should never
        # surface a Python traceback to the operator; consistency CLI
        # must exit 1 with a one-line clean message.
        fm = _progress_fm(current_stage="testing")
        del fm["scenario"]
        _write_progress(self.root, fm)
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            try:
                code = validate_main(["--root", str(self.root), "consistency"])
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        self.assertEqual(code, 1)
        self.assertIn("structurally incomplete", err.getvalue())


# ---------- CLI integration ----------


class CliIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            try:
                code = validate_main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def test_consistency_happy_exits_0(self):
        _write_progress(
            self.root, _progress_fm(current_stage="workflow-incident-analysis"),
        )
        code, _, _ = self._run(["--root", str(self.root), "consistency"])
        self.assertEqual(code, 0)

    def test_consistency_missing_progress_exits_1(self):
        code, _, err = self._run(["--root", str(self.root), "consistency"])
        self.assertEqual(code, 1)
        self.assertIn("progress.md not found", err)

    def test_consistency_missing_artifact_exits_1(self):
        _write_progress(self.root, _progress_fm(current_stage="prd-inception"))
        # No PRD on disk.
        code, _, err = self._run(["--root", str(self.root), "consistency"])
        self.assertEqual(code, 1)
        self.assertIn("required artifact missing", err)
        self.assertIn("docs/prd/prd.md", err)

    def test_all_subcommand_still_deferred(self):
        # Phase 6.4 only implements consistency; `all` remains Phase 7.
        code, _, err = self._run(["--root", str(self.root), "all"])
        self.assertEqual(code, 2)
        self.assertIn("deferred to Phase 7", err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
