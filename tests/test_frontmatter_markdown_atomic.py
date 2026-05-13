from pathlib import Path
import tempfile
import unittest

from skills._shared.dev_workflow.atomic import (
    AtomicWriteError,
    atomic_write_text,
    transaction,
)
from skills._shared.dev_workflow.frontmatter import FrontmatterError, parse_frontmatter, render_markdown
from skills._shared.dev_workflow.markdown import find_section, non_comment_lines, replace_section_body


class FrontmatterTests(unittest.TestCase):
    def test_parse_keeps_timestamp_as_string(self):
        doc = parse_frontmatter(
            "---\n"
            "title: Example\n"
            "type: prd\n"
            "release: \"0.1\"\n"
            "created: 2026-05-15T10:00:00Z\n"
            "updated: 2026-05-15T10:00:00Z\n"
            "owner: tester/unit\n"
            "---\n"
            "# Body\n"
        )
        self.assertEqual(doc.frontmatter["release"], "0.1")
        self.assertIsInstance(doc.frontmatter["created"], str)
        self.assertEqual(doc.body, "# Body\n")

    def test_rejects_missing_frontmatter(self):
        with self.assertRaises(FrontmatterError):
            parse_frontmatter("# Body only\n")

    def test_render_round_trip(self):
        text = render_markdown({"title": "Example", "count": 2}, "\n# Body\n")
        doc = parse_frontmatter(text)
        self.assertEqual(doc.frontmatter["count"], 2)
        self.assertEqual(doc.body, "# Body\n")


class MarkdownTests(unittest.TestCase):
    def test_find_and_replace_section_body(self):
        text = "# T\n\n## Pending Changes\nold\n\n## Change Log\nlog\n"
        section = find_section(text, "## Pending Changes")
        self.assertIsNotNone(section)
        self.assertEqual(section.body, "old\n\n")
        updated = replace_section_body(text, "## Pending Changes", "new")
        self.assertIn("## Pending Changes\n\nnew\n", updated)
        self.assertIn("## Change Log\nlog", updated)

    def test_non_comment_lines_ignores_blank_and_html_comments(self):
        lines = non_comment_lines("\n<!-- ok -->\n- entry\n  \n")
        self.assertEqual(lines, ["- entry"])

    def test_non_comment_lines_handles_multi_line_html_comment(self):
        body = "<!--\nfirst\nsecond\n-->\n- entry\n"
        self.assertEqual(non_comment_lines(body), ["- entry"])

    def test_non_comment_lines_treats_only_comments_as_empty(self):
        body = "<!-- one -->\n<!--\nblock\n-->\n  \n"
        self.assertEqual(non_comment_lines(body), [])

    def test_find_section_cuts_at_same_or_higher_level_heading(self):
        text = "## A\n### A1\nx\n### A2\ny\n## B\nz\n"
        section_a = find_section(text, "## A")
        self.assertIsNotNone(section_a)
        self.assertEqual(section_a.body, "### A1\nx\n### A2\ny\n")
        section_a1 = find_section(text, "### A1")
        self.assertIsNotNone(section_a1)
        # Same-level "### A2" terminates A1; "## B" not reached.
        self.assertEqual(section_a1.body, "x\n")


class AtomicTests(unittest.TestCase):
    def test_atomic_write_text(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "doc.md"
            atomic_write_text(path, "hello")
            self.assertEqual(path.read_text(), "hello")

    def test_transaction_rolls_back_existing_and_new_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "existing.txt"
            new_file = root / "new.txt"
            existing.write_text("old")
            with self.assertRaises(RuntimeError):
                with transaction() as tx:
                    tx.write_text(existing, "new")
                    tx.write_text(new_file, "created")
                    raise RuntimeError("boom")
            self.assertEqual(existing.read_text(), "old")
            self.assertFalse(new_file.exists())

    def test_transaction_rolls_back_when_a_later_write_fails(self):
        # Regression for the M2 scenario: a later atomic_write_text raises an
        # OSError (here NotADirectoryError because the third target's parent is
        # a regular file). Earlier writes must still be undone, and the new
        # file from the second write must be deleted.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            existing = root / "a.txt"
            existing.write_text("A0")
            new_file = root / "b.txt"
            blocked = root / "a.txt" / "subfile"  # parent is a regular file
            with self.assertRaises(OSError):
                with transaction() as tx:
                    tx.write_text(existing, "A1")
                    tx.write_text(new_file, "B1")
                    tx.write_text(blocked, "X")
            self.assertEqual(existing.read_text(), "A0")
            self.assertFalse(new_file.exists())


if __name__ == "__main__":
    unittest.main()
