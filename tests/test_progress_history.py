"""Tests for skills/_shared/dev_workflow/progress_history.py."""

from __future__ import annotations

import unittest

from skills._shared.dev_workflow.progress_history import (
    HISTORY_TITLE_LINE,
    HistoryEntry,
    HistoryError,
    append_history_text,
    initial_history_text,
    iter_entries_chronological,
    parse_history_text,
    render_history_entry,
)


def _entry(
    *,
    timestamp: str = "2026-05-15T10:00:00Z",
    event: str = "init",
    summary: str = "project created",
    agent: str | None = "claude-opus-4-7/workflow-init",
    result: str | None = "scenario=S1, release=0.1",
    next_: str | None = "prd-write",
) -> HistoryEntry:
    return HistoryEntry(
        timestamp=timestamp,
        event=event,
        summary=summary,
        agent=agent,
        result=result,
        next=next_,
        raw="",
    )


class ParseHistoryTextTests(unittest.TestCase):
    def test_empty_text_returns_empty_list(self):
        self.assertEqual(parse_history_text(""), [])
        self.assertEqual(parse_history_text("\n\n\n"), [])

    def test_single_entry_parsed(self):
        text = (
            "# Project History\n\n"
            "## 2026-05-15T10:00:00Z — init — project created\n"
            "- agent: claude-opus-4-7/workflow-init\n"
            "- result: scenario=S1, release=0.1\n"
            "- next: prd-write\n"
        )
        [entry] = parse_history_text(text)
        self.assertEqual(entry.timestamp, "2026-05-15T10:00:00Z")
        self.assertEqual(entry.event, "init")
        self.assertEqual(entry.summary, "project created")
        self.assertEqual(entry.agent, "claude-opus-4-7/workflow-init")
        self.assertEqual(entry.result, "scenario=S1, release=0.1")
        self.assertEqual(entry.next, "prd-write")

    def test_multi_entry_in_document_order(self):
        text = (
            "# Project History\n\n"
            "## 2026-05-15T10:00:00Z — init — project created\n"
            "- agent: a/b\n"
            "\n"
            "## 2026-05-16T11:00:00Z — release-close — release 0.1 closed\n"
            "- agent: a/b\n"
            "- result: previous_releases now [\"0.1\"]\n"
        )
        entries = parse_history_text(text)
        self.assertEqual([e.event for e in entries], ["init", "release-close"])

    def test_optional_fields_default_to_none(self):
        text = (
            "## 2026-05-15T10:00:00Z — init — project created\n"
            "- agent: a/b\n"
        )
        [entry] = parse_history_text(text)
        self.assertIsNone(entry.result)
        self.assertIsNone(entry.next)

    def test_invalid_header_rejected(self):
        with self.assertRaises(HistoryError):
            parse_history_text(
                "## 2026-05-15 — init — project created\n"  # missing time portion
                "- agent: a/b\n"
            )

    def test_field_outside_entry_rejected(self):
        with self.assertRaises(HistoryError):
            parse_history_text("- agent: a/b\n")

    def test_unknown_field_rejected(self):
        with self.assertRaises(HistoryError):
            parse_history_text(
                "## 2026-05-15T10:00:00Z — init — project created\n"
                "- bogus: x\n"
            )

    def test_duplicate_field_rejected(self):
        with self.assertRaises(HistoryError):
            parse_history_text(
                "## 2026-05-15T10:00:00Z — init — project created\n"
                "- agent: a/b\n"
                "- agent: c/d\n"
            )

    def test_event_token_must_match_regex(self):
        # Event tokens are letters/digits/_/- only.
        with self.assertRaises(HistoryError):
            parse_history_text(
                "## 2026-05-15T10:00:00Z — bad event — project created\n"
            )

    def test_unknown_top_level_line_rejected(self):
        with self.assertRaises(HistoryError):
            parse_history_text(
                "## 2026-05-15T10:00:00Z — init — project created\n"
                "stray text\n"
            )


class RenderHistoryEntryTests(unittest.TestCase):
    def test_render_full_entry(self):
        rendered = render_history_entry(_entry())
        self.assertIn("## 2026-05-15T10:00:00Z — init — project created\n", rendered)
        self.assertIn("- agent: claude-opus-4-7/workflow-init\n", rendered)
        self.assertIn("- result: scenario=S1, release=0.1\n", rendered)
        self.assertIn("- next: prd-write\n", rendered)
        self.assertTrue(rendered.endswith("\n"))

    def test_render_omits_optional_fields_when_none(self):
        entry = _entry(result=None, next_=None)
        rendered = render_history_entry(entry)
        self.assertNotIn("result:", rendered)
        self.assertNotIn("next:", rendered)
        self.assertIn("- agent: ", rendered)

    def test_render_round_trip_through_parse(self):
        original = _entry()
        rendered = render_history_entry(original)
        [parsed] = parse_history_text(rendered)
        self.assertEqual(parsed.timestamp, original.timestamp)
        self.assertEqual(parsed.event, original.event)
        self.assertEqual(parsed.summary, original.summary)
        self.assertEqual(parsed.agent, original.agent)
        self.assertEqual(parsed.result, original.result)
        self.assertEqual(parsed.next, original.next)


class AppendHistoryTextTests(unittest.TestCase):
    def test_append_to_empty_returns_just_entry(self):
        out = append_history_text("", _entry())
        entries = parse_history_text(out)
        self.assertEqual(len(entries), 1)

    def test_append_keeps_prior_title_line(self):
        existing = HISTORY_TITLE_LINE + render_history_entry(_entry())
        out = append_history_text(
            existing,
            _entry(
                timestamp="2026-05-16T11:00:00Z",
                event="release-close",
                summary="release 0.1 closed",
            ),
        )
        entries = parse_history_text(out)
        self.assertEqual([e.event for e in entries], ["init", "release-close"])

    def test_append_adds_blank_line_separator(self):
        first = render_history_entry(_entry())
        out = append_history_text(
            first,
            _entry(
                timestamp="2026-05-16T11:00:00Z",
                event="release-close",
                summary="release 0.1 closed",
            ),
        )
        self.assertIn("\n\n## 2026-05-16T11:00:00Z", out)


class InitialHistoryTextTests(unittest.TestCase):
    def test_includes_title_and_entry(self):
        out = initial_history_text(_entry())
        self.assertTrue(out.startswith(HISTORY_TITLE_LINE))
        entries = parse_history_text(out)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].event, "init")


class IterChronologicalTests(unittest.TestCase):
    def test_sort_ascending_by_timestamp(self):
        a = _entry(timestamp="2026-05-15T10:00:00Z")
        b = _entry(timestamp="2026-05-14T09:00:00Z", event="release-close", summary="x")
        c = _entry(timestamp="2026-05-16T11:00:00Z", event="bug-intake", summary="y")
        out = iter_entries_chronological([a, b, c])
        self.assertEqual(
            [e.timestamp for e in out],
            ["2026-05-14T09:00:00Z", "2026-05-15T10:00:00Z", "2026-05-16T11:00:00Z"],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
