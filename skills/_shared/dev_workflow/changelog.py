"""In-memory Change Log parsing, promotion, and validation helpers.

Spec source: ``skills/doc-guardian/references/change-log-format.md``.

The doc-guardian ``scripts/changelog.py`` CLI wraps these helpers with atomic
file I/O and exit codes. The Phase 4 ``scripts/status_transition.py`` helper is
expected to reuse :func:`promote_text` inside its own multi-doc transaction so
that frontmatter-driven Change Log entries land atomically alongside the
status mutation (see change-log-format.md §7.1).
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable

from .frontmatter import parse_frontmatter
from .markdown import find_section, replace_section_body
from .schema import DOC_TYPES, INCREMENTAL_DOC_TYPES


class ChangelogError(ValueError):
    """Raised when Change Log content cannot be parsed or promoted."""


PENDING_HEADING = "## Pending Changes"
CHANGELOG_HEADING = "## Change Log"

# Strict entry regex per change-log-format.md §2.2.
_ENTRY_RE = re.compile(
    r"^- (?P<timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z) "
    r"\[(?P<section_ref>Section \d+(?:\.\d+)?|frontmatter|全文)\]: "
    r"(?P<summary>\S.*)$"
)

_DATE_HEADING_RE = re.compile(r"^### (\d{4}-\d{2}-\d{2})$")


@dataclass(frozen=True)
class Entry:
    timestamp: str
    section_ref: str
    summary: str
    raw: str

    @property
    def date(self) -> str:
        return self.timestamp[:10]


def is_incremental_type(doc_type: str | None) -> bool:
    return doc_type in INCREMENTAL_DOC_TYPES


def parse_entry_line(line: str) -> Entry:
    match = _ENTRY_RE.match(line)
    if not match:
        raise ChangelogError(f"Invalid entry: {line!r}")
    return Entry(
        timestamp=match.group("timestamp"),
        section_ref=match.group("section_ref"),
        summary=match.group("summary"),
        raw=line,
    )


def _classify_comment_line(raw_line: str, *, in_block: bool, context: str) -> tuple[bool, str | None]:
    """Strict per-line HTML-comment handling.

    Returns ``(new_in_block, residual_kind)`` where ``residual_kind`` is one of
    ``None`` (line was fully consumed by comment handling) or ``"open_block"``
    (caller should treat the line as a block-comment opener and continue).

    Raises :class:`ChangelogError` when a line carries non-blank content after
    a comment closer (single-line or multi-line block close); spec
    ``change-log-format.md §2.3`` only allows blank lines and HTML comments,
    so trailing content beside ``-->`` is rejected.
    """

    if in_block:
        if "-->" in raw_line:
            tail = raw_line.split("-->", 1)[1].strip()
            if tail:
                raise ChangelogError(
                    f"{context}: unexpected content after multi-line comment closer: {raw_line!r}"
                )
            return False, None
        return True, None
    stripped = raw_line.strip()
    if not stripped.startswith("<!--"):
        # Caller must handle as a non-comment line.
        return False, "non_comment"
    close_idx = stripped.find("-->")
    if close_idx >= 0:
        tail = stripped[close_idx + 3 :].strip()
        if tail:
            raise ChangelogError(
                f"{context}: unexpected content after inline comment: {raw_line!r}"
            )
        return False, None
    return True, "open_block"


def parse_pending_section(body: str) -> list[Entry]:
    """Parse Pending Changes body into entries.

    Strictness (per ``change-log-format.md §2.2 / §2.3``):
      - blank lines and pure HTML comments are skipped;
      - non-blank lines must not be indented;
      - inline comment closures (``<!-- ... -->``) cannot carry trailing text;
      - multi-line comment closers cannot carry trailing text;
      - any other line must match the strict entry regex.
    """

    entries: list[Entry] = []
    in_block = False
    for raw_line in body.splitlines():
        if in_block:
            in_block, _ = _classify_comment_line(raw_line, in_block=True, context="Pending Changes")
            continue
        stripped = raw_line.strip()
        if not stripped:
            continue
        if raw_line[0].isspace():
            raise ChangelogError(
                f"Pending Changes line must not be indented: {raw_line!r}"
            )
        if stripped.startswith("<!--"):
            in_block, _ = _classify_comment_line(raw_line, in_block=False, context="Pending Changes")
            continue
        entries.append(parse_entry_line(raw_line))
    if in_block:
        raise ChangelogError("Pending Changes: unclosed HTML comment block")
    return entries


def parse_changelog_section(body: str) -> list[tuple[str, list[Entry]]]:
    """Parse Change Log body into ``[(date, [Entry])]`` in document order.

    Strictness (per ``change-log-format.md §3.1 / §3.3``):
      - non-blank lines must not be indented;
      - date headings must be preceded by a blank line, a comment, or the
        start of the section (groups are separated by at least one blank line);
      - the first entry of a date group must be separated from the heading
        by a blank line (or a comment), matching the canonical layout in
        §3.1 and the output of :func:`render_changelog_body`;
      - inline / block comment closures cannot carry trailing text;
      - any other line must be a valid entry whose date matches the enclosing
        group heading.
    """

    groups: list[tuple[str, list[Entry]]] = []
    current_date: str | None = None
    current_entries: list[Entry] = []
    in_block = False
    last_kind: str | None = None  # "blank" / "heading" / "entry" / "comment" / None
    for raw_line in body.splitlines():
        if in_block:
            in_block, _ = _classify_comment_line(raw_line, in_block=True, context="Change Log")
            if not in_block:
                last_kind = "comment"
            continue
        if raw_line.strip() == "":
            last_kind = "blank"
            continue
        if raw_line[0].isspace():
            raise ChangelogError(
                f"Change Log line must not be indented: {raw_line!r}"
            )
        if raw_line.startswith("###"):
            heading_match = _DATE_HEADING_RE.match(raw_line)
            if not heading_match:
                raise ChangelogError(f"Invalid Change Log group heading: {raw_line!r}")
            if last_kind in {"heading", "entry"}:
                raise ChangelogError(
                    "Change Log groups must be separated by a blank line; "
                    f"missing blank line before {raw_line!r}"
                )
            if current_date is not None:
                groups.append((current_date, current_entries))
            current_date = heading_match.group(1)
            current_entries = []
            last_kind = "heading"
            continue
        if raw_line.startswith("<!--"):
            in_block, _ = _classify_comment_line(raw_line, in_block=False, context="Change Log")
            if not in_block:
                last_kind = "comment"
            continue
        if not raw_line.startswith("- "):
            raise ChangelogError(f"Unexpected Change Log line: {raw_line!r}")
        if last_kind == "heading":
            raise ChangelogError(
                "Change Log: a date heading must be followed by a blank line "
                f"before the first entry: {raw_line!r}"
            )
        entry = parse_entry_line(raw_line)
        if current_date is None:
            raise ChangelogError(
                f"Change Log entry before any '### YYYY-MM-DD' heading: {raw_line!r}"
            )
        if entry.date != current_date:
            raise ChangelogError(
                f"Change Log entry date {entry.date} does not match group heading {current_date}"
            )
        current_entries.append(entry)
        last_kind = "entry"
    if in_block:
        raise ChangelogError("Change Log: unclosed HTML comment block")
    if current_date is not None:
        groups.append((current_date, current_entries))
    return groups


def merge_groups(
    existing: Iterable[tuple[str, list[Entry]]],
    pending: Iterable[Entry],
) -> list[tuple[str, list[Entry]]]:
    by_date: dict[str, list[Entry]] = {}
    for date, entries in existing:
        by_date.setdefault(date, []).extend(entries)
    for entry in pending:
        by_date.setdefault(entry.date, []).append(entry)
    for date in by_date:
        by_date[date].sort(key=lambda e: e.timestamp)
    return [(date, by_date[date]) for date in sorted(by_date.keys(), reverse=True)]


def render_changelog_body(groups: list[tuple[str, list[Entry]]]) -> str:
    if not groups:
        return ""
    parts: list[str] = []
    for index, (date, entries) in enumerate(groups):
        if index:
            parts.append("")
        parts.append(f"### {date}")
        parts.append("")
        for entry in entries:
            parts.append(entry.raw)
    return "\n".join(parts) + "\n"


def promote_text(content: str) -> tuple[str, list[Entry]]:
    """Promote Pending Changes into Change Log.

    Returns ``(new_content, promoted_entries)``. If pending is empty (or both
    sections are absent for a snapshot doc), returns the input unchanged with
    an empty list.

    Raises :class:`ChangelogError` on:
      - unknown doc type;
      - incremental doc missing either section;
      - malformed pending or change log entries / headings.
    """

    doc = parse_frontmatter(content)
    doc_type = doc.frontmatter.get("type")
    if doc_type not in DOC_TYPES:
        raise ChangelogError(f"Unknown doc type: {doc_type!r}")

    pending = find_section(content, PENDING_HEADING)
    changelog = find_section(content, CHANGELOG_HEADING)

    if is_incremental_type(doc_type):
        if pending is None or changelog is None:
            raise ChangelogError(
                "Incremental doc requires both '## Pending Changes' and '## Change Log' sections"
            )
    else:
        if pending is None or changelog is None:
            return content, []

    pending_entries = parse_pending_section(pending.body)
    # Always parse the existing Change Log so that malformed entries / headings
    # surface even when there is nothing to promote. This guards against the
    # bypass where a hand-edited Change Log slips through because Pending
    # Changes happens to be empty.
    existing_groups = parse_changelog_section(changelog.body)
    if not pending_entries:
        return content, []

    merged = merge_groups(existing_groups, pending_entries)
    new_changelog_body = render_changelog_body(merged)

    updated = replace_section_body(content, CHANGELOG_HEADING, new_changelog_body)
    updated = replace_section_body(updated, PENDING_HEADING, "")
    return updated, pending_entries


def validate_text(content: str) -> list[str]:
    """Validate Change Log discipline. Returns list of issues (empty == valid).

    Issue messages do not carry a class prefix; callers (``validate.py`` Class
    6 wrapper, ``changelog.py validate``) prepend their own context.
    """

    issues: list[str] = []
    try:
        doc = parse_frontmatter(content)
    except Exception as exc:  # pragma: no cover - frontmatter errors surface elsewhere
        return [f"Cannot parse frontmatter: {exc}"]
    doc_type = doc.frontmatter.get("type")

    pending = find_section(content, PENDING_HEADING)
    changelog = find_section(content, CHANGELOG_HEADING)

    if is_incremental_type(doc_type):
        if pending is None:
            issues.append("Missing '## Pending Changes' section")
        if changelog is None:
            issues.append("Missing '## Change Log' section")

    if pending is not None:
        try:
            pending_entries = parse_pending_section(pending.body)
        except ChangelogError as exc:
            issues.append(f"Pending Changes: {exc}")
            pending_entries = []
        if pending_entries:
            issues.append(
                f"Pending Changes has {len(pending_entries)} unpromoted entries; "
                "run changelog.py promote"
            )

    if changelog is not None:
        try:
            groups = parse_changelog_section(changelog.body)
        except ChangelogError as exc:
            issues.append(f"Change Log: {exc}")
            return issues
        prev_date: str | None = None
        for date, entries in groups:
            if prev_date is not None and date >= prev_date:
                issues.append(
                    "Change Log date groups must be sorted descending; "
                    f"{date} is not strictly older than {prev_date}"
                )
            prev_date = date
            prev_ts: str | None = None
            for entry in entries:
                if prev_ts is not None and entry.timestamp < prev_ts:
                    issues.append(
                        f"Change Log entries within {date} must be ascending; "
                        f"{entry.timestamp} appears after {prev_ts}"
                    )
                prev_ts = entry.timestamp

    return issues
