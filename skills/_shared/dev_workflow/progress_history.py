"""Strict parser/renderer for ``progress-history.md`` entries.

Spec source: ``skills/workflow-protocol/references/command-reference.md``.
Each history entry is a Markdown ``##`` section of the canonical form::

    ## <ISO8601 UTC> — <event-name> — <free-text summary>
    - agent: <agent-id>
    - result: <result-text>
    - next: <next-text>

Phase 5.1 owns this module so that ``progress.py init`` / ``recover`` and
the later Phase 5.2/5.3/5.4 commands all share the exact same on-disk
format. The parser is intentionally strict: tolerating malformed entries
during replay would silently let a corrupted history fabricate state.

The module is pure in-memory (no file I/O). ``progress.py`` adds the
atomic-append wrapper.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable


class HistoryError(ValueError):
    """Raised when ``progress-history.md`` cannot be parsed."""


# ``## <timestamp> — <event> — <summary>``. The spec uses the en dash
# ``—`` (U+2014). We anchor the line so anything else is rejected up
# front.
_HEADER_RE = re.compile(
    r"^## (?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) — "
    r"(?P<event>[A-Za-z][A-Za-z0-9_-]*) — "
    r"(?P<summary>\S.*)$"
)
_FIELD_RE = re.compile(r"^- (?P<key>agent|result|next): (?P<value>.+)$")


@dataclass(frozen=True)
class HistoryEntry:
    timestamp: str
    event: str
    summary: str
    agent: str | None
    result: str | None
    next: str | None
    raw: str


def parse_history_text(text: str) -> list[HistoryEntry]:
    """Parse the body of ``progress-history.md`` into entries.

    The expected layout interleaves entries with one blank line. The first
    non-blank line must be a header; entries are read until EOF. Every
    field that appears must be ``- agent: ...``, ``- result: ...``, or
    ``- next: ...``; unknown fields, missing header before fields, or
    duplicate keys raise :class:`HistoryError`.
    """

    entries: list[HistoryEntry] = []
    lines = text.replace("\r\n", "\n").splitlines()

    current_header: re.Match[str] | None = None
    current_fields: dict[str, str] = {}
    raw_lines: list[str] = []

    def _flush() -> None:
        nonlocal current_header, current_fields, raw_lines
        if current_header is None:
            return
        entries.append(
            HistoryEntry(
                timestamp=current_header.group("ts"),
                event=current_header.group("event"),
                summary=current_header.group("summary"),
                agent=current_fields.get("agent"),
                result=current_fields.get("result"),
                next=current_fields.get("next"),
                raw="\n".join(raw_lines),
            )
        )
        current_header = None
        current_fields = {}
        raw_lines = []

    for raw_line in lines:
        if raw_line.startswith("## "):
            _flush()
            match = _HEADER_RE.match(raw_line)
            if match is None:
                raise HistoryError(f"invalid history header: {raw_line!r}")
            current_header = match
            current_fields = {}
            raw_lines = [raw_line]
            continue
        if not raw_line.strip():
            if current_header is not None:
                raw_lines.append(raw_line)
            continue
        if raw_line.startswith("# "):
            # A top-level Markdown heading (e.g. file title) is allowed
            # only before the first entry. Inside an entry it is illegal.
            if current_header is not None:
                raise HistoryError(
                    f"top-level heading inside history entry: {raw_line!r}"
                )
            continue
        if raw_line.startswith("- "):
            if current_header is None:
                raise HistoryError(
                    f"history field outside any entry: {raw_line!r}"
                )
            field_match = _FIELD_RE.match(raw_line)
            if field_match is None:
                raise HistoryError(f"invalid history field: {raw_line!r}")
            key = field_match.group("key")
            if key in current_fields:
                raise HistoryError(f"duplicate '- {key}:' in history entry")
            current_fields[key] = field_match.group("value")
            raw_lines.append(raw_line)
            continue
        raise HistoryError(f"unexpected history line: {raw_line!r}")

    _flush()
    return entries


def render_history_entry(entry: HistoryEntry) -> str:
    """Render a :class:`HistoryEntry` to canonical Markdown text.

    The result includes the trailing blank line so callers can append
    successive entries with simple string concatenation.
    """

    lines = [f"## {entry.timestamp} — {entry.event} — {entry.summary}"]
    if entry.agent is not None:
        lines.append(f"- agent: {entry.agent}")
    if entry.result is not None:
        lines.append(f"- result: {entry.result}")
    if entry.next is not None:
        lines.append(f"- next: {entry.next}")
    return "\n".join(lines) + "\n"


def append_history_text(existing: str, entry: HistoryEntry) -> str:
    """Append a rendered entry to existing history text, normalising spacing.

    The contract: each entry is separated from the previous one by exactly
    one blank line. The function does not enforce timestamp monotonicity;
    that is the replay validator's job.
    """

    rendered = render_history_entry(entry)
    if not existing or existing.strip() == "":
        # An empty (or whitespace-only) file: keep an optional ``# Project
        # History`` title that callers may have prepended.
        prefix = existing.rstrip()
        if prefix:
            return prefix + "\n\n" + rendered
        return rendered
    if not existing.endswith("\n"):
        existing = existing + "\n"
    if not existing.endswith("\n\n"):
        existing = existing + "\n"
    return existing + rendered


HISTORY_TITLE_LINE = "# Project History\n\n"


def initial_history_text(entry: HistoryEntry) -> str:
    """Compose the very first ``progress-history.md`` content.

    Files start with ``# Project History`` followed by a blank line, then
    the ``init`` entry. Phase 5.2/5.3/5.4 reuse :func:`append_history_text`
    for subsequent entries.
    """

    return HISTORY_TITLE_LINE + render_history_entry(entry)


def iter_entries_chronological(entries: Iterable[HistoryEntry]) -> list[HistoryEntry]:
    """Return entries sorted ascending by timestamp.

    Stable sort over the input list — duplicate timestamps preserve input
    order, so callers can detect monotonicity violations after the sort.
    """

    return sorted(entries, key=lambda e: e.timestamp)
