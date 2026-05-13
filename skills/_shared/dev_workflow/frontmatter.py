"""Markdown frontmatter parsing and rendering helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import copy

import yaml


class FrontmatterError(ValueError):
    """Raised when a Markdown file has invalid YAML frontmatter."""


class _NoTimestampSafeLoader(yaml.SafeLoader):
    pass


_NoTimestampSafeLoader.yaml_implicit_resolvers = copy.deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)

# PyYAML otherwise converts ISO8601 timestamps to datetime objects. The workflow
# schema validates timestamps as strings, so keep scalar values unchanged.
for first, resolvers in list(_NoTimestampSafeLoader.yaml_implicit_resolvers.items()):
    _NoTimestampSafeLoader.yaml_implicit_resolvers[first] = [
        (tag, regexp)
        for tag, regexp in resolvers
        if tag != "tag:yaml.org,2002:timestamp"
    ]


@dataclass(frozen=True)
class FrontmatterDocument:
    frontmatter: dict[str, Any]
    body: str
    raw_frontmatter: str


def split_frontmatter(text: str) -> tuple[str, str]:
    """Return the raw YAML frontmatter and Markdown body.

    The opening delimiter must be ``---\\n`` and the closing delimiter must be
    a ``---`` line that is preceded by ``\\n`` (i.e. on its own line). A
    "truly empty" frontmatter that collapses to ``---\\n---\\n`` (no content
    line in between) is rejected as missing the closing delimiter; this is
    acceptable in practice because every doc-guardian-managed type requires
    the universal frontmatter fields, so a completely empty mapping would be
    rejected by validate.py class 3 anyway. To carry an empty mapping use
    ``---\\n\\n---\\n``.
    """

    normalized = text.replace("\r\n", "\n")
    if not normalized.startswith("---\n"):
        raise FrontmatterError("Markdown document must start with YAML frontmatter delimiter")

    end_marker = normalized.find("\n---", 4)
    if end_marker == -1:
        raise FrontmatterError("Markdown document is missing closing frontmatter delimiter")

    marker_end = end_marker + len("\n---")
    if marker_end < len(normalized) and normalized[marker_end] not in "\n":
        raise FrontmatterError("Closing frontmatter delimiter must be on its own line")

    yaml_text = normalized[4:end_marker]
    body_start = marker_end + 1 if marker_end < len(normalized) else marker_end
    return yaml_text, normalized[body_start:]


def parse_frontmatter(text: str) -> FrontmatterDocument:
    yaml_text, body = split_frontmatter(text)
    try:
        loaded = yaml.load(yaml_text, Loader=_NoTimestampSafeLoader)
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"Invalid YAML frontmatter: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise FrontmatterError("YAML frontmatter must be a mapping")
    return FrontmatterDocument(dict(loaded), body, yaml_text)


def read_markdown(path: str | Path) -> FrontmatterDocument:
    return parse_frontmatter(Path(path).read_text(encoding="utf-8"))


def dump_frontmatter(frontmatter: Mapping[str, Any]) -> str:
    return yaml.safe_dump(
        dict(frontmatter),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
    ).rstrip()


def render_markdown(frontmatter: Mapping[str, Any], body: str) -> str:
    rendered = dump_frontmatter(frontmatter)
    if body and not body.startswith("\n"):
        body = "\n" + body
    return f"---\n{rendered}\n---{body}"
