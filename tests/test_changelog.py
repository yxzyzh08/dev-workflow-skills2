"""Tests for shared changelog helpers and the doc-guardian changelog.py CLI."""

from __future__ import annotations

from pathlib import Path
import io
import sys
import tempfile
import unittest

import yaml

from skills._shared.dev_workflow.changelog import (
    ChangelogError,
    promote_text,
    validate_text,
)


def make_doc(
    *,
    type_: str = "srs",
    title: str = "Example Doc",
    status: str = "draft",
    created: str = "2026-05-15T10:00:00Z",
    updated: str = "2026-05-15T10:00:00Z",
    owner: str = "claude-opus-4-7/srs-write",
    extra_fm: dict | None = None,
    body: str = "# Document Title\n\nMain content.\n",
    pending: str | None = "",
    change_log: str | None = "",
) -> str:
    fm: dict = {
        "title": title,
        "type": type_,
        "status": status,
        "created": created,
        "updated": updated,
        "owner": owner,
    }
    if extra_fm:
        fm.update(extra_fm)
    fm_text = yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()
    text = f"---\n{fm_text}\n---\n{body}"
    if pending is not None:
        text += f"\n## Pending Changes\n{pending}\n" if pending else "\n## Pending Changes\n\n"
    if change_log is not None:
        text += f"\n## Change Log\n{change_log}\n" if change_log else "\n## Change Log\n\n"
    return text


SRS_FRONTMATTER_EXTRA = {
    "release": "0.1",
    "is_multi_module": False,
    "architecture_change": False,
}


class PromoteTests(unittest.TestCase):
    def test_promote_happy_path_merges_into_top(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending=(
                "- 2026-05-15T10:00:00Z [Section 1.3]: 精简产品边界描述\n"
                "- 2026-05-15T11:00:00Z [frontmatter]: 更新 status 至 review-passed"
            ),
            change_log=(
                "### 2026-05-10\n"
                "\n"
                "- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建"
            ),
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(len(entries), 2)
        self.assertIn("### 2026-05-15", new_text)
        self.assertIn("### 2026-05-10", new_text)
        # 2026-05-15 group must come before 2026-05-10
        self.assertLess(
            new_text.index("### 2026-05-15"),
            new_text.index("### 2026-05-10"),
        )
        # Pending Changes body emptied
        self.assertIn("## Pending Changes\n\n## Change Log", new_text)
        # Re-validate should succeed
        self.assertEqual(validate_text(new_text), [])

    def test_promote_no_op_when_pending_empty(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026-05-10\n\n- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建",
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(entries, [])
        self.assertEqual(new_text, doc)

    def test_promote_rejects_invalid_timestamp(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="- 2026-05-15 [Section 1]: missing time-of-day",
            change_log="",
        )
        with self.assertRaises(ChangelogError):
            promote_text(doc)

    def test_promote_rejects_invalid_section_ref(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="- 2026-05-15T10:00:00Z [3.2]: missing 'Section' prefix",
            change_log="",
        )
        with self.assertRaises(ChangelogError):
            promote_text(doc)

    def test_promote_requires_both_sections_for_incremental(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="- 2026-05-15T10:00:00Z [Section 1]: foo",
            change_log=None,
        )
        with self.assertRaises(ChangelogError):
            promote_text(doc)

    def test_promote_no_op_for_snapshot_without_sections(self):
        doc = make_doc(
            type_="test-report",
            title="Test Report 0.1",
            status="review-passed",
            owner="claude-opus-4-7/testing-write",
            extra_fm={
                "release": "0.1",
                "verification_status": "pass",
                "total_test_cases": 10,
                "passed": 10,
                "failed": 0,
            },
            pending=None,
            change_log=None,
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(new_text, doc)
        self.assertEqual(entries, [])

    def test_promote_works_for_snapshot_with_both_sections(self):
        doc = make_doc(
            type_="test-report",
            title="Test Report 0.1",
            status="review-passed",
            owner="claude-opus-4-7/testing-write",
            extra_fm={
                "release": "0.1",
                "verification_status": "pass",
                "total_test_cases": 1,
                "passed": 1,
                "failed": 0,
            },
            pending="- 2026-05-15T10:00:00Z [Section 1]: 补充测试说明",
            change_log="",
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(len(entries), 1)
        self.assertIn("### 2026-05-15", new_text)

    def test_promote_sorts_dates_and_timestamps(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending=(
                "- 2026-05-15T11:00:00Z [Section 1]: later same day\n"
                "- 2026-05-15T09:00:00Z [Section 2]: earlier same day\n"
                "- 2026-05-12T08:00:00Z [Section 3]: older day"
            ),
            change_log="",
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(len(entries), 3)
        idx_15 = new_text.index("### 2026-05-15")
        idx_12 = new_text.index("### 2026-05-12")
        self.assertLess(idx_15, idx_12)
        # within 2026-05-15 group, T09 before T11
        idx_t09 = new_text.index("2026-05-15T09:00:00Z")
        idx_t11 = new_text.index("2026-05-15T11:00:00Z")
        self.assertLess(idx_t09, idx_t11)

    def test_promote_merges_into_existing_date_group(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="- 2026-05-10T12:00:00Z [Section 5]: late same-day add",
            change_log=(
                "### 2026-05-10\n"
                "\n"
                "- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建"
            ),
        )
        new_text, entries = promote_text(doc)
        self.assertEqual(len(entries), 1)
        # only one '### 2026-05-10' group should exist
        self.assertEqual(new_text.count("### 2026-05-10"), 1)
        idx_t08 = new_text.index("2026-05-10T08:00:00Z")
        idx_t12 = new_text.index("2026-05-10T12:00:00Z")
        self.assertLess(idx_t08, idx_t12)

    def test_promote_unknown_doc_type_rejected(self):
        doc = make_doc(
            type_="not-a-real-type",
            extra_fm={},
            pending="",
            change_log=None,
        )
        with self.assertRaises(ChangelogError):
            promote_text(doc)

    def test_promote_with_empty_pending_still_validates_existing_changelog(self):
        # Round 2 M2: even when there is nothing to promote, malformed existing
        # Change Log entries / headings must surface as ChangelogError. Otherwise
        # a hand-edited Change Log slips through whenever Pending Changes is empty.
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026/05/15\n\n- 2026-05-15T10:00:00Z [Section 1]: bad heading",
        )
        with self.assertRaises(ChangelogError):
            promote_text(doc)


class ValidateTests(unittest.TestCase):
    def test_validate_clean_incremental_doc_passes(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: foo",
        )
        self.assertEqual(validate_text(doc), [])

    def test_validate_rejects_unpromoted_pending(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="- 2026-05-15T10:00:00Z [Section 1]: still pending",
            change_log="",
        )
        issues = validate_text(doc)
        self.assertTrue(any("unpromoted entries" in i for i in issues), issues)

    def test_validate_rejects_invalid_changelog_heading(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026/05/15\n\n- 2026-05-15T10:00:00Z [Section 1]: bad date heading",
        )
        issues = validate_text(doc)
        self.assertTrue(any("Invalid Change Log group heading" in i for i in issues), issues)

    def test_validate_rejects_invalid_changelog_entry(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026-05-15\n\n- nope this is not an entry",
        )
        issues = validate_text(doc)
        self.assertTrue(any("Invalid entry" in i for i in issues), issues)

    def test_validate_rejects_dates_not_descending(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log=(
                "### 2026-05-10\n"
                "\n"
                "- 2026-05-10T08:00:00Z [Section 1]: old\n"
                "\n"
                "### 2026-05-15\n"
                "\n"
                "- 2026-05-15T08:00:00Z [Section 2]: new"
            ),
        )
        issues = validate_text(doc)
        self.assertTrue(any("must be sorted descending" in i for i in issues), issues)

    def test_validate_rejects_timestamps_not_ascending_within_date(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log=(
                "### 2026-05-15\n"
                "\n"
                "- 2026-05-15T11:00:00Z [Section 1]: later first\n"
                "- 2026-05-15T09:00:00Z [Section 2]: earlier last"
            ),
        )
        issues = validate_text(doc)
        self.assertTrue(any("must be ascending" in i for i in issues), issues)

    def test_validate_skips_missing_sections_for_snapshot(self):
        doc = make_doc(
            type_="test-report",
            owner="claude-opus-4-7/testing-write",
            extra_fm={
                "release": "0.1",
                "verification_status": "pass",
                "total_test_cases": 1,
                "passed": 1,
                "failed": 0,
            },
            pending=None,
            change_log=None,
        )
        self.assertEqual(validate_text(doc), [])

    def test_validate_reports_missing_sections_for_incremental(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending=None,
            change_log=None,
        )
        issues = validate_text(doc)
        self.assertTrue(any("Missing '## Pending Changes'" in i for i in issues), issues)
        self.assertTrue(any("Missing '## Change Log'" in i for i in issues), issues)

    def test_validate_allows_html_comments_in_pending(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="<!-- placeholder -->\n<!--\nmulti\nline\n-->",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        self.assertEqual(validate_text(doc), [])

    # ----- Round 2 M2 raw-line / blank-line strictness -----

    def test_validate_rejects_indented_changelog_heading(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="  ### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("must not be indented" in i for i in issues), issues
        )

    def test_validate_rejects_indented_changelog_entry(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026-05-15\n\n  - 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("must not be indented" in i for i in issues), issues
        )

    def test_validate_rejects_missing_blank_line_between_groups(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log=(
                "### 2026-05-15\n"
                "\n"
                "- 2026-05-15T10:00:00Z [Section 1]: new\n"
                "### 2026-05-10\n"
                "\n"
                "- 2026-05-10T08:00:00Z [Section 2]: old"
            ),
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("must be separated by a blank line" in i for i in issues), issues
        )

    # ----- Round 2 M3 inline-trailing strictness -----

    def test_validate_rejects_inline_trailing_after_comment_close(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="<!-- comment --> trailing text",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("after inline comment" in i for i in issues), issues
        )

    def test_validate_rejects_hidden_entry_after_inline_comment(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="<!-- c --> - 2026-05-15T10:00:00Z [Section 1]: hidden entry",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("after inline comment" in i for i in issues), issues
        )

    def test_validate_rejects_multi_line_comment_close_with_trailing(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="<!--\nfirst\nsecond\n--> trailing\n",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("after multi-line comment closer" in i for i in issues), issues
        )

    # ----- Round 2 follow-up Low: blank line after date heading -----

    def test_validate_rejects_heading_immediately_followed_by_entry(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log="### 2026-05-15\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("date heading must be followed by a blank line" in i for i in issues),
            issues,
        )

    # ----- Round 2 polish: unclosed comment blocks -----

    def test_validate_rejects_unclosed_pending_comment(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="<!-- never closed",
            change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("unclosed HTML comment" in i for i in issues), issues
        )

    def test_validate_rejects_unclosed_changelog_comment(self):
        doc = make_doc(
            extra_fm=SRS_FRONTMATTER_EXTRA,
            pending="",
            change_log=(
                "### 2026-05-15\n"
                "\n"
                "- 2026-05-15T10:00:00Z [Section 1]: ok\n"
                "<!-- never closed"
            ),
        )
        issues = validate_text(doc)
        self.assertTrue(
            any("unclosed HTML comment" in i for i in issues), issues
        )


class CliIntegrationTests(unittest.TestCase):
    """Run the changelog.py module entry point against temp files."""

    def setUp(self) -> None:
        scripts_root = Path(__file__).resolve().parents[1] / "skills" / "doc-guardian" / "scripts"
        if str(scripts_root) not in sys.path:
            sys.path.insert(0, str(scripts_root))
        # Re-import each test to pick up a fresh argparse parser if needed
        import importlib

        self._cli = importlib.import_module("changelog")
        importlib.reload(self._cli)

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            code = self._cli.main(argv)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def test_cli_promote_writes_back_atomically(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_rel = "docs/release0.1/srs/srs.md"
            doc_path = root / doc_rel
            doc_path.parent.mkdir(parents=True)
            content = make_doc(
                extra_fm=SRS_FRONTMATTER_EXTRA,
                pending="- 2026-05-15T10:00:00Z [Section 1]: 新增需求",
                change_log="",
            )
            doc_path.write_text(content, encoding="utf-8")
            code, _, err = self._run(["--root", str(root), "promote", doc_rel])
            self.assertEqual(code, 0, err)
            new_text = doc_path.read_text(encoding="utf-8")
            self.assertIn("### 2026-05-15", new_text)
            self.assertIn("## Pending Changes\n\n## Change Log", new_text)

    def test_cli_validate_rejects_unpromoted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_rel = "docs/release0.1/srs/srs.md"
            doc_path = root / doc_rel
            doc_path.parent.mkdir(parents=True)
            content = make_doc(
                extra_fm=SRS_FRONTMATTER_EXTRA,
                pending="- 2026-05-15T10:00:00Z [Section 1]: still pending",
                change_log="",
            )
            doc_path.write_text(content, encoding="utf-8")
            code, _, err = self._run(["--root", str(root), "validate", doc_rel])
            self.assertEqual(code, 1)
            self.assertIn("unpromoted entries", err)

    def test_cli_validate_passes_clean_doc(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            doc_rel = "docs/release0.1/srs/srs.md"
            doc_path = root / doc_rel
            doc_path.parent.mkdir(parents=True)
            content = make_doc(
                extra_fm=SRS_FRONTMATTER_EXTRA,
                pending="",
                change_log="### 2026-05-15\n\n- 2026-05-15T10:00:00Z [Section 1]: ok",
            )
            doc_path.write_text(content, encoding="utf-8")
            code, _, err = self._run(["--root", str(root), "validate", doc_rel])
            self.assertEqual(code, 0, err)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
