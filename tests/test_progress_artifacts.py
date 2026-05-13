"""Tests for skills/_shared/dev_workflow/progress_artifacts.py."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from skills._shared.dev_workflow.progress_artifacts import (
    ArtifactFrontmatter,
    BreakdownInfo,
    BugReportInfo,
    ProgressArtifactError,
    TestReportInfo,
    TriageAnalysis,
    load_artifact_frontmatter,
    load_breakdown_with_tasks,
    load_bug_report,
    load_test_report,
    parse_bug_triage_analysis,
)


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


def _write_artifact(root: Path, rel: str, fm: dict, body: str = "Body.\n") -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    text = f"---\n{_emit_yaml(fm)}\n---\n{body}"
    p.write_text(text, encoding="utf-8")
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


class _BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()


# ---------- load_artifact_frontmatter ----------


class LoadArtifactBasicsTests(_BaseTest):
    def test_load_detailed_design_happy_path(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
            _base_fm("detailed-design", release="0.1", task_id="T1"),
        )
        info = load_artifact_frontmatter(
            self.root,
            doc_type="detailed-design",
            release="0.1",
            task_id="T1",
        )
        self.assertIsInstance(info, ArtifactFrontmatter)
        self.assertEqual(info.doc_type, "detailed-design")
        self.assertEqual(info.task_id, "T1")
        self.assertEqual(info.fields["task_id"], "T1")
        self.assertEqual(
            info.rel_path,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
        )

    def test_load_test_review_report_happy_path(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/tasks/T1/test_review_report.md",
            _base_fm(
                "test-review-report",
                release="0.1",
                task_id="T1",
                review_status="pending",
                blocking_findings_count=0,
                findings_count=0,
                severity_distribution={"critical": 0, "high": 0, "medium": 0, "low": 0},
                max_severity="low",
            ),
        )
        info = load_artifact_frontmatter(
            self.root,
            doc_type="test-review-report",
            release="0.1",
            task_id="T1",
        )
        self.assertEqual(info.fields["review_status"], "pending")
        self.assertEqual(info.fields["blocking_findings_count"], 0)


class LoadArtifactRejectionTests(_BaseTest):
    def test_missing_file_rejected(self):
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root,
                doc_type="detailed-design",
                release="0.1",
                task_id="T1",
            )
        self.assertIn("missing", str(cm.exception))
        self.assertIn("detailed-design", str(cm.exception))

    def test_corrupt_frontmatter_rejected(self):
        rel = "docs/release0.1/development/tasks/T1/detailed_design.md"
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("garbage no frontmatter", encoding="utf-8")
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1", task_id="T1",
            )
        self.assertIn("frontmatter", str(cm.exception))

    def test_wrong_type_rejected(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
            _base_fm("test-review-report", release="0.1", task_id="T1"),
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1", task_id="T1",
            )
        self.assertIn("does not match expected", str(cm.exception))
        self.assertIn("test-review-report", str(cm.exception))

    def test_wrong_release_rejected(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
            _base_fm("detailed-design", release="0.2", task_id="T1"),
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1", task_id="T1",
            )
        self.assertIn("release", str(cm.exception))

    def test_wrong_task_id_rejected(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/tasks/T1/detailed_design.md",
            _base_fm("detailed-design", release="0.1", task_id="T2"),
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1", task_id="T1",
            )
        self.assertIn("task_id", str(cm.exception))

    def test_unknown_doc_type_rejected(self):
        with self.assertRaises(ProgressArtifactError):
            load_artifact_frontmatter(
                self.root, doc_type="not-a-real-type",
                release="0.1", task_id="T1",
            )

    def test_invalid_task_id_format_rejected(self):
        with self.assertRaises(ProgressArtifactError):
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1", task_id="not-a-task",
            )

    def test_doc_type_requires_task_id(self):
        with self.assertRaises(ProgressArtifactError) as cm:
            load_artifact_frontmatter(
                self.root, doc_type="detailed-design",
                release="0.1",
            )
        self.assertIn("requires task_id", str(cm.exception))


# ---------- load_breakdown_with_tasks ----------


class LoadBreakdownTests(_BaseTest):
    def test_breakdown_extracts_task_tokens(self):
        body = (
            "# Stage 4 Tasks\n\n"
            "- T1 — implement schema\n"
            "- T2 — write parser\n"
            "- T3 — wire CLI\n"
            "\n"
            "Notes referencing T1 again are deduplicated.\n"
        )
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks=3),
            body=body,
        )
        info = load_breakdown_with_tasks(self.root, release="0.1")
        self.assertIsInstance(info, BreakdownInfo)
        self.assertEqual(info.declared_tasks, ("T1", "T2", "T3"))
        self.assertEqual(info.total_tasks, 3)
        self.assertEqual(info.release, "0.1")

    def test_breakdown_missing_rejected(self):
        with self.assertRaises(ProgressArtifactError):
            load_breakdown_with_tasks(self.root, release="0.1")

    def test_breakdown_wrong_type_rejected(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("development-plan", release="0.1"),
            body="No tasks declared\n",
        )
        with self.assertRaises(ProgressArtifactError):
            load_breakdown_with_tasks(self.root, release="0.1")

    def test_breakdown_total_tasks_string_rejected(self):
        # Phase 5.3 round 2 M2: total_tasks is a required non-bool int
        # per frontmatter-schema.md §3.2. A YAML string value must fail
        # the loader, not silently flatten to None.
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks="three"),
            body="- T1 — first\n- T2 — second\n",
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_breakdown_with_tasks(self.root, release="0.1")
        self.assertIn("total_tasks", str(cm.exception))
        self.assertIn("three", str(cm.exception))

    def test_breakdown_total_tasks_missing_rejected(self):
        # Required field; absence must reject.
        fm = _base_fm("task-breakdown", release="0.1")
        # Note: _base_fm does not include total_tasks; explicitly omit.
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            fm,
            body="- T1 — first\n",
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_breakdown_with_tasks(self.root, release="0.1")
        self.assertIn("missing required field", str(cm.exception))
        self.assertIn("total_tasks", str(cm.exception))

    def test_breakdown_total_tasks_bool_rejected(self):
        # Python int subclasses bool; the loader must reject true/false
        # since YAML 'true' / 'false' is not a valid task count.
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks=True),
            body="- T1 — first\n",
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_breakdown_with_tasks(self.root, release="0.1")
        self.assertIn("total_tasks", str(cm.exception))

    def test_breakdown_total_tasks_negative_rejected(self):
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks=-1),
            body="- T1 — first\n",
        )
        with self.assertRaises(ProgressArtifactError):
            load_breakdown_with_tasks(self.root, release="0.1")

    def test_breakdown_total_tasks_zero_allowed(self):
        # Zero declared tasks is a degenerate but legitimate case for
        # an empty Stage 4. Loader accepts it; Phase 6 advance can still
        # cross-check declared_tasks against total_tasks.
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks=0),
            body="No tasks yet.\n",
        )
        info = load_breakdown_with_tasks(self.root, release="0.1")
        self.assertEqual(info.total_tasks, 0)
        self.assertEqual(info.declared_tasks, ())

    def test_breakdown_word_boundary(self):
        # Tokens that look like task IDs but are part of larger words
        # must not be counted (e.g. "T10000" is a task; "TenThousand" is not).
        body = "- T10 — works\n- T11 — works\n- TenThousand — not a task\n"
        _write_artifact(
            self.root,
            "docs/release0.1/development/breakdown.md",
            _base_fm("task-breakdown", release="0.1", total_tasks=2),
            body=body,
        )
        info = load_breakdown_with_tasks(self.root, release="0.1")
        self.assertEqual(info.declared_tasks, ("T10", "T11"))


# ---------- Phase 6.1: load_test_report ----------


class LoadTestReportTests(_BaseTest):
    def test_happy_path_returns_status(self):
        _write_artifact(
            self.root,
            "docs/release0.1/testing/report.md",
            _base_fm(
                "test-report",
                release="0.1",
                verification_status="pass",
                total_test_cases=5,
                passed=5,
                failed=0,
            ),
        )
        info = load_test_report(self.root, release="0.1")
        self.assertIsInstance(info, TestReportInfo)
        self.assertEqual(info.verification_status, "pass")
        self.assertEqual(info.release, "0.1")

    def test_fail_status_returned_verbatim(self):
        _write_artifact(
            self.root,
            "docs/release0.1/testing/report.md",
            _base_fm(
                "test-report",
                release="0.1",
                verification_status="fail",
                total_test_cases=3,
                passed=2,
                failed=1,
            ),
        )
        info = load_test_report(self.root, release="0.1")
        self.assertEqual(info.verification_status, "fail")

    def test_missing_test_report_rejects(self):
        with self.assertRaises(ProgressArtifactError):
            load_test_report(self.root, release="0.1")

    def test_wrong_type_rejects(self):
        _write_artifact(
            self.root,
            "docs/release0.1/testing/report.md",
            _base_fm("test-preparation", release="0.1"),
        )
        with self.assertRaises(ProgressArtifactError):
            load_test_report(self.root, release="0.1")

    def test_invalid_verification_status_rejects(self):
        _write_artifact(
            self.root,
            "docs/release0.1/testing/report.md",
            _base_fm(
                "test-report",
                release="0.1",
                verification_status="not-a-status",
                total_test_cases=0,
                passed=0,
                failed=0,
            ),
        )
        with self.assertRaises(ProgressArtifactError):
            load_test_report(self.root, release="0.1")


# ---------- Phase 6.1: load_bug_report ----------


class LoadBugReportTests(_BaseTest):
    def _bug_fm(self, **overrides):
        fm = _base_fm("bug-report", status="draft")
        fm.update(
            {
                "bug_id": "BUG-001",
                "found_in_release": "0.1",
                "target_release": None,
                "root_cause": "development",
                "consumed_in_release": None,
            }
        )
        fm.update(overrides)
        return fm

    def test_happy_path_returns_full_info(self):
        _write_artifact(
            self.root,
            "docs/bug/BUG-001.md",
            self._bug_fm(),
            body="# BUG-001\n\nBody.\n",
        )
        info = load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIsInstance(info, BugReportInfo)
        self.assertEqual(info.bug_id, "BUG-001")
        self.assertEqual(info.found_in_release, "0.1")
        self.assertEqual(info.root_cause, "development")
        self.assertIn("Body.", info.body)

    def test_expect_root_cause_match_passes(self):
        _write_artifact(
            self.root, "docs/bug/BUG-001.md", self._bug_fm(),
        )
        info = load_bug_report(
            self.root, "docs/bug/BUG-001.md",
            expect_root_cause="development",
        )
        self.assertEqual(info.root_cause, "development")

    def test_expect_root_cause_mismatch_rejects(self):
        _write_artifact(
            self.root, "docs/bug/BUG-001.md", self._bug_fm(),
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(
                self.root, "docs/bug/BUG-001.md",
                expect_root_cause="srs",
            )
        self.assertIn("root_cause", str(cm.exception))
        self.assertIn("development", str(cm.exception))

    def test_non_canonical_path_rejects(self):
        with self.assertRaises(ProgressArtifactError):
            load_bug_report(self.root, "/etc/passwd")
        with self.assertRaises(ProgressArtifactError):
            load_bug_report(self.root, "docs/bug/BUG-1000.md")
        with self.assertRaises(ProgressArtifactError):
            load_bug_report(self.root, "docs/incident/BUG-001.md")

    def test_missing_file_rejects(self):
        with self.assertRaises(ProgressArtifactError):
            load_bug_report(self.root, "docs/bug/BUG-404.md")

    def test_wrong_type_rejects(self):
        fm = self._bug_fm()
        fm["type"] = "test-report"
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("'bug-report'", str(cm.exception))

    # ---------- Phase 6.1 round 2 review M1: stricter shape ----------

    def test_missing_bug_id_field_rejects(self):
        fm = self._bug_fm()
        del fm["bug_id"]
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("'bug_id'", str(cm.exception))
        self.assertIn("missing required", str(cm.exception))

    def test_invalid_bug_id_regex_rejects(self):
        fm = self._bug_fm(bug_id="NOTBUG")
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("BUG-\\d{3}", str(cm.exception))

    def test_bug_id_stem_mismatch_rejects(self):
        fm = self._bug_fm(bug_id="BUG-099")
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("BUG-099", str(cm.exception))
        self.assertIn("BUG-001", str(cm.exception))
        self.assertIn("path stem", str(cm.exception))

    def test_missing_target_release_field_rejects(self):
        # spec: value may be null but key MUST be present.
        fm = self._bug_fm()
        del fm["target_release"]
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("target_release", str(cm.exception))
        self.assertIn("missing required", str(cm.exception))

    def test_missing_consumed_in_release_field_rejects(self):
        fm = self._bug_fm()
        del fm["consumed_in_release"]
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("consumed_in_release", str(cm.exception))

    def test_target_release_non_string_non_null_rejects(self):
        fm = self._bug_fm(target_release=42)
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("target_release", str(cm.exception))
        self.assertIn("string or null", str(cm.exception))

    def test_missing_root_cause_field_rejects(self):
        fm = self._bug_fm()
        del fm["root_cause"]
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("root_cause", str(cm.exception))

    def test_unknown_root_cause_value_rejects(self):
        fm = self._bug_fm(root_cause="not-a-valid-cause")
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError) as cm:
            load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIn("not-a-valid-cause", str(cm.exception))
        self.assertIn("srs", str(cm.exception))

    def test_root_cause_null_accepted_without_expect(self):
        # null root_cause is legal pre-triage; load_bug_report doesn't
        # demand an answer unless expect_root_cause is supplied.
        fm = self._bug_fm(root_cause=None)
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        info = load_bug_report(self.root, "docs/bug/BUG-001.md")
        self.assertIsNone(info.root_cause)

    def test_empty_found_in_release_rejects(self):
        fm = self._bug_fm(found_in_release="")
        _write_artifact(self.root, "docs/bug/BUG-001.md", fm)
        with self.assertRaises(ProgressArtifactError):
            load_bug_report(self.root, "docs/bug/BUG-001.md")


# ---------- Phase 6.1: parse_bug_triage_analysis ----------


_TEST_BODY_HEADER = "# BUG-001\n\nDescription.\n\n"


class ParseBugTriageTests(unittest.TestCase):
    def test_test_only_classification(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T1, T3\n\n"
            + "Root cause: missing test coverage; this is test-only fix.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertEqual(info.affected_tasks, ("T1", "T3"))
        self.assertEqual(info.classification, "test")
        self.assertFalse(info.unable_to_localize)

    def test_source_classification(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T2\n\n"
            + "Root cause: source-code logic error in implementation.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-002.md")
        self.assertEqual(info.affected_tasks, ("T2",))
        self.assertEqual(info.classification, "source")

    def test_ambiguous_when_no_keywords(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T1\n\n"
            + "We are not yet sure where the issue lies; needs deeper analysis.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertEqual(info.classification, "ambiguous")

    def test_ambiguous_when_both_keyword_families_present(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T1\n\n"
            + "Maybe test-only or maybe source-code; unclear.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertEqual(info.classification, "ambiguous")

    def test_unable_to_localize(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: unable to localize\n\n"
            + "Will require planning re-route.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertTrue(info.unable_to_localize)
        self.assertEqual(info.affected_tasks, ())

    def test_missing_section_rejects(self):
        with self.assertRaises(ProgressArtifactError) as cm:
            parse_bug_triage_analysis(
                _TEST_BODY_HEADER, rel_path="docs/bug/BUG-001.md"
            )
        self.assertIn("Triage Analysis", str(cm.exception))

    def test_missing_affected_tasks_line_rejects(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "Root cause: source-code bug; needs code-revising.\n"
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertIn("Affected Task(s)", str(cm.exception))

    def test_invalid_token_rejects(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T1, NotATask\n"
        )
        with self.assertRaises(ProgressArtifactError) as cm:
            parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertIn("^T", str(cm.exception))

    def test_dedups_repeated_tokens(self):
        body = (
            _TEST_BODY_HEADER
            + "## Triage Analysis\n\n"
            + "**Affected Task(s)**: T1, T1, T2\n\n"
            + "test-only fix.\n"
        )
        info = parse_bug_triage_analysis(body, rel_path="docs/bug/BUG-001.md")
        self.assertEqual(info.affected_tasks, ("T1", "T2"))


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
