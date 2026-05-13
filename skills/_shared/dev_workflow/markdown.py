"""Small Markdown section helpers used by doc-guardian scripts."""

from __future__ import annotations

from dataclasses import dataclass
import re


class MarkdownSectionError(ValueError):
    """Raised when a required Markdown section cannot be found."""


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Section:
    heading: str
    title: str
    level: int
    start: int
    heading_end: int
    end: int
    body: str


def _normalize_heading(heading: str) -> tuple[int, str]:
    match = re.match(r"^(#{1,6})\s+(.+?)\s*$", heading.strip())
    if not match:
        raise MarkdownSectionError(f"Invalid heading selector: {heading!r}")
    return len(match.group(1)), match.group(2).strip()


def find_section(text: str, heading: str) -> Section | None:
    """Find a section by exact heading, ending at next same/higher heading."""

    normalized = text.replace("\r\n", "\n")
    target_level, target_title = _normalize_heading(heading)
    headings = list(_HEADING_RE.finditer(normalized))
    for index, match in enumerate(headings):
        level = len(match.group(1))
        title = match.group(2).strip()
        if level != target_level or title != target_title:
            continue
        end = len(normalized)
        for next_match in headings[index + 1 :]:
            if len(next_match.group(1)) <= level:
                end = next_match.start()
                break
        body = normalized[match.end() : end]
        if body.startswith("\n"):
            body = body[1:]
        return Section(
            heading=match.group(0),
            title=title,
            level=level,
            start=match.start(),
            heading_end=match.end(),
            end=end,
            body=body,
        )
    return None


def require_section(text: str, heading: str) -> Section:
    section = find_section(text, heading)
    if section is None:
        raise MarkdownSectionError(f"Missing required section: {heading}")
    return section


def replace_section_body(text: str, heading: str, new_body: str) -> str:
    """Replace a section body while preserving its heading and surrounding text."""

    section = require_section(text, heading)
    body = new_body.rstrip("\n")
    replacement = section.heading
    replacement += "\n"
    if body:
        replacement += "\n" + body + "\n"
    else:
        replacement += "\n"
    return text[: section.start] + replacement + text[section.end :]


def non_comment_lines(section_body: str) -> list[str]:
    """Return non-blank, non-HTML-comment lines from a Markdown section body.

    Both single-line ``<!-- ... -->`` and multi-line HTML comment blocks are
    skipped, matching the change-log-format §2.3 intent of treating
    "Pending Changes" sections that contain only whitespace and comments as
    empty.

    Limitation: in a multi-line comment block, the closing line is dropped
    in its entirety, so any inline content that follows ``-->`` on that same
    line (e.g. ``--> trailing note``) is also skipped. This is acceptable
    because change-log-format.md §2.3 does not allow content sharing a line
    with a comment closing tag; legal Pending Changes entries always sit on
    their own line.
    """

    lines: list[str] = []
    in_block_comment = False
    for line in section_body.splitlines():
        stripped = line.strip()
        if in_block_comment:
            if "-->" in stripped:
                in_block_comment = False
            continue
        if not stripped:
            continue
        if stripped.startswith("<!--") and stripped.endswith("-->"):
            continue
        if stripped.startswith("<!--"):
            # Multi-line comment block: skip until we see the closing tag.
            if "-->" not in stripped:
                in_block_comment = True
            continue
        lines.append(line)
    return lines
