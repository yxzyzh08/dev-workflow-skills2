"""Stage 4 task artifact loaders for ``progress.py update --task``.

Phase 5.3's ``apply_update_task`` validates per-status preconditions by
reading the relevant artifact file and inspecting a small set of
frontmatter fields:

- ``task-breakdown`` (``docs/release<x.y>/development/breakdown.md``)
  declares the task IDs participating in Stage 4.
- ``detailed-design`` (``docs/release<x.y>/development/tasks/T<n>/detailed_design.md``)
  is the per-task design doc whose ``task_id`` must equal ``T<n>``.
- ``test-review-report`` (``.../test_review_report.md``) tracks
  test-review skeleton vs. completed states via ``review_status`` and
  ``blocking_findings_count``.
- ``code-review-report`` (``.../code_review_report.md``) is the
  symmetric code-review counterpart.
- ``verification-result`` (``.../verification_result.md``) records the
  per-task verification outcome via ``verification_status``.

This module deliberately implements *thin* validation: it confirms
``type``, ``release``, and ``task_id`` agree with the caller's intent so
Phase 5.3 can short-circuit on misplaced docs, but it does not duplicate
``skills/doc-guardian/scripts/validate.py``. Full Class 1-7 doc
validation remains the doc-guardian binary's responsibility; the heavy
``validate.py consistency`` cross-progress check is Phase 6 territory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from .frontmatter import FrontmatterError, read_markdown


class ProgressArtifactError(ValueError):
    """Raised when a Stage 4 task artifact is missing or its frontmatter
    does not satisfy the precondition for the requested transition."""


# Task-ID regex: progress_state mirrors this; we keep a local copy so the
# loader does not depend on the state module (avoid import cycle).
_TASK_ID_RE = re.compile(r"^T\d+$")
_TASK_ID_BODY_RE = re.compile(r"\bT\d+\b")


_BUG_PATH_RE = re.compile(r"^docs/bug/BUG-\d{3}\.md$")


# Path templates per directory-layout.md / TYPE_PATHS.
_PATH_TEMPLATES: dict[str, str] = {
    "task-breakdown": "docs/release{release}/development/breakdown.md",
    "detailed-design": (
        "docs/release{release}/development/tasks/{task_id}/detailed_design.md"
    ),
    "test-review-report": (
        "docs/release{release}/development/tasks/{task_id}/test_review_report.md"
    ),
    "code-review-report": (
        "docs/release{release}/development/tasks/{task_id}/code_review_report.md"
    ),
    "verification-result": (
        "docs/release{release}/development/tasks/{task_id}/verification_result.md"
    ),
    "test-report": "docs/release{release}/testing/report.md",
    "installation-result": (
        "docs/release{release}/delivery/installation_result.md"
    ),
}


# Phase 6.1: BUG body keyword classification for Gap-4 dev rollback.
# Forward path runs `parse_bug_triage_analysis()` on the BUG body and decides
# per-task rollback (verified→test-revising / verified→code-revising /
# code-review-passed→code-revising). Replay does NOT re-read BUG bodies; it
# reads the rollback decisions from the canonical history summary token.
_TEST_FIX_KEYWORDS = (
    "test-only",
    "test-first",
    "regression test",
    "regression-test",
    "missing test",
)
_SOURCE_FIX_KEYWORDS = (
    "source-code",
    "source code",
    "implementation bug",
    "logic bug",
    "source fix",
)


_AFFECTED_TASKS_RE = re.compile(
    r"^\*\*Affected Task\(s\)\*\*\s*:\s*(?P<value>.+)$",
    re.MULTILINE,
)


@dataclass(frozen=True)
class ArtifactFrontmatter:
    """Minimal info returned by :func:`load_artifact_frontmatter`."""

    doc_type: str
    release: str
    task_id: str | None
    fields: dict[str, Any]
    rel_path: str


@dataclass(frozen=True)
class BreakdownInfo:
    """Result of :func:`load_breakdown_with_tasks`.

    ``total_tasks`` is the value read from the breakdown's frontmatter.
    Phase 5.3 round 2 M2 requires it to be a non-negative non-bool int;
    missing or invalid values are rejected by
    :func:`load_breakdown_with_tasks` before this dataclass is built.
    """

    release: str
    total_tasks: int
    declared_tasks: tuple[str, ...]
    rel_path: str


def _format_path(doc_type: str, *, release: str, task_id: str | None) -> str:
    template = _PATH_TEMPLATES.get(doc_type)
    if template is None:
        raise ProgressArtifactError(f"unknown doc_type: {doc_type!r}")
    if "{task_id}" in template and task_id is None:
        raise ProgressArtifactError(
            f"doc_type {doc_type!r} requires task_id but none was supplied"
        )
    if task_id is not None and not _TASK_ID_RE.match(task_id):
        raise ProgressArtifactError(
            f"task_id must match ^T\\d+$, got {task_id!r}"
        )
    return template.format(release=release, task_id=task_id or "")


def load_artifact_frontmatter(
    root: str | Path,
    *,
    doc_type: str,
    release: str,
    task_id: str | None = None,
) -> ArtifactFrontmatter:
    """Read an artifact's frontmatter and verify type/release/task_id.

    The loader does **not** evaluate per-transition predicates such as
    ``review_status==pending``; the caller (``apply_update_task``)
    interprets the returned :attr:`ArtifactFrontmatter.fields` map.

    Raises :class:`ProgressArtifactError` if:
      * the file does not exist,
      * the file cannot be parsed as Markdown with YAML frontmatter,
      * the frontmatter ``type`` field disagrees with ``doc_type``,
      * the frontmatter ``release`` disagrees with ``release``,
      * a ``task_id`` was supplied and the frontmatter ``task_id``
        disagrees.
    """

    root_path = Path(root)
    rel = _format_path(doc_type, release=release, task_id=task_id)
    abs_path = root_path / rel
    if not abs_path.exists():
        raise ProgressArtifactError(f"missing required {doc_type} at {rel}")
    try:
        doc = read_markdown(abs_path)
    except FrontmatterError as exc:
        raise ProgressArtifactError(
            f"cannot parse {rel} frontmatter: {exc}"
        ) from exc
    except OSError as exc:
        raise ProgressArtifactError(
            f"cannot read {rel}: {exc}"
        ) from exc

    fm = doc.frontmatter
    fm_type = fm.get("type")
    if fm_type != doc_type:
        raise ProgressArtifactError(
            f"{rel}: frontmatter type {fm_type!r} does not match expected {doc_type!r}"
        )
    fm_release = fm.get("release")
    if fm_release != release:
        raise ProgressArtifactError(
            f"{rel}: frontmatter release {fm_release!r} does not match expected {release!r}"
        )
    if task_id is not None:
        fm_task_id = fm.get("task_id")
        if fm_task_id != task_id:
            raise ProgressArtifactError(
                f"{rel}: frontmatter task_id {fm_task_id!r} does not match expected {task_id!r}"
            )
    return ArtifactFrontmatter(
        doc_type=doc_type,
        release=release,
        task_id=task_id,
        fields=dict(fm),
        rel_path=rel,
    )


def load_breakdown_with_tasks(
    root: str | Path, *, release: str
) -> BreakdownInfo:
    """Load ``breakdown.md`` and extract the set of declared task IDs.

    The "declared task" extraction is intentionally lightweight: any
    ``Tn`` token (whole-word) appearing in the body is considered a
    declaration. ``apply_update_task`` only requires a containment check
    (``task_id in info.declared_tasks``), and Phase 5.3 deliberately
    leaves the count-vs-declared consistency check (``total_tasks ==
    len(declared_tasks)``) to Phase 6 ``update --advance`` /
    ``validate.py consistency``.

    The frontmatter ``total_tasks`` field IS required and must be a
    non-bool int per ``frontmatter-schema.md §3.2`` (Phase 5.3 round 2
    review M2). Missing or non-int values raise
    :class:`ProgressArtifactError`; the count consistency check itself
    remains deferred.
    """

    info_fm = load_artifact_frontmatter(
        root, doc_type="task-breakdown", release=release
    )
    body = read_markdown(Path(root) / info_fm.rel_path).body
    if "total_tasks" not in info_fm.fields:
        raise ProgressArtifactError(
            f"{info_fm.rel_path}: task-breakdown is missing required field "
            "'total_tasks'"
        )
    raw_total = info_fm.fields["total_tasks"]
    if not isinstance(raw_total, int) or isinstance(raw_total, bool) or raw_total < 0:
        raise ProgressArtifactError(
            f"{info_fm.rel_path}: total_tasks must be a non-negative int, "
            f"got {type(raw_total).__name__} ({raw_total!r})"
        )
    declared = tuple(sorted(set(_TASK_ID_BODY_RE.findall(body))))
    return BreakdownInfo(
        release=release,
        total_tasks=raw_total,
        declared_tasks=declared,
        rel_path=info_fm.rel_path,
    )


# ---------- Phase 6.1: bug-start / bug-close helpers ----------


@dataclass(frozen=True)
class TestReportInfo:
    release: str
    verification_status: str  # "pass" / "fail" / "partial"
    rel_path: str


def load_test_report(root: str | Path, *, release: str) -> TestReportInfo:
    """Load the per-release Stage 5 test-report and return its
    ``verification_status``. Phase 6.1 bug-start / bug-close use this to
    short-circuit on the most recent test outcome before mutating
    ``progress.md``.

    Raises :class:`ProgressArtifactError` if the file is missing, has the
    wrong type/release, or its ``verification_status`` is not in the
    allowed enum {pass, fail, partial}.
    """

    info = load_artifact_frontmatter(
        root, doc_type="test-report", release=release
    )
    raw_status = info.fields.get("verification_status")
    if raw_status not in {"pass", "fail", "partial"}:
        raise ProgressArtifactError(
            f"{info.rel_path}: verification_status must be one of "
            f"{{pass, fail, partial}}, got {raw_status!r}"
        )
    return TestReportInfo(
        release=release,
        verification_status=raw_status,
        rel_path=info.rel_path,
    )


@dataclass(frozen=True)
class BugReportInfo:
    bug_id: str
    found_in_release: str
    target_release: str | None
    consumed_in_release: str | None
    root_cause: str | None
    rel_path: str
    body: str


_BUG_ID_RE = re.compile(r"^BUG-\d{3}$")
_BUG_ROOT_CAUSE_VALUES = frozenset({"srs", "architecture", "development", "prd-exception"})


def load_bug_report(
    root: str | Path,
    bug_path: str,
    *,
    expect_root_cause: str | None = None,
) -> BugReportInfo:
    """Load a BUG-NNN.md and validate its frontmatter.

    Validates (Phase 6.1 round 2 M1):
      * canonical path shape (``docs/bug/BUG-NNN.md`` with 3-digit ID);
      * ``type == bug-report``;
      * ``bug_id`` is present, matches ``^BUG-\\d{3}$``, and equals the
        path stem;
      * ``found_in_release`` is a non-empty string;
      * ``target_release`` and ``consumed_in_release`` keys exist (the
        spec's "value-may-be-null but key MUST be present" rule); their
        values are either ``None`` or strings;
      * ``root_cause`` value, when present, is in
        ``{srs, architecture, development, prd-exception}`` or ``None``;
        when ``expect_root_cause`` is given, the BUG ``root_cause`` must
        agree (used by ``bug-start`` to confirm the CLI ``--root-cause``
        argument matches the doc).

    Returns the BUG body as a string so callers can run
    :func:`parse_bug_triage_analysis` without re-reading the file.
    """

    if not isinstance(bug_path, str) or not _BUG_PATH_RE.match(bug_path):
        raise ProgressArtifactError(
            f"BUG path must match 'docs/bug/BUG-NNN.md' (3-digit zero-padded ID), "
            f"got {bug_path!r}"
        )

    abs_path = Path(root) / bug_path
    if not abs_path.exists():
        raise ProgressArtifactError(
            f"missing BUG file at {bug_path}"
        )
    try:
        doc = read_markdown(abs_path)
    except FrontmatterError as exc:
        raise ProgressArtifactError(
            f"{bug_path}: cannot parse BUG frontmatter: {exc}"
        ) from exc
    except OSError as exc:
        raise ProgressArtifactError(
            f"{bug_path}: cannot read BUG: {exc}"
        ) from exc

    fm = doc.frontmatter
    if fm.get("type") != "bug-report":
        raise ProgressArtifactError(
            f"{bug_path}: BUG type must be 'bug-report', got {fm.get('type')!r}"
        )

    if "bug_id" not in fm:
        raise ProgressArtifactError(
            f"{bug_path}: BUG frontmatter is missing required field 'bug_id'"
        )
    bug_id = fm["bug_id"]
    if not isinstance(bug_id, str) or not _BUG_ID_RE.match(bug_id):
        raise ProgressArtifactError(
            f"{bug_path}: bug_id must match ^BUG-\\d{{3}}$, got {bug_id!r}"
        )
    expected_stem = Path(bug_path).stem
    if bug_id != expected_stem:
        raise ProgressArtifactError(
            f"{bug_path}: bug_id={bug_id!r} does not match path stem "
            f"{expected_stem!r}; rename the file or fix the frontmatter"
        )

    if "found_in_release" not in fm:
        raise ProgressArtifactError(
            f"{bug_path}: BUG frontmatter is missing required field 'found_in_release'"
        )
    found = fm["found_in_release"]
    if not isinstance(found, str) or not found:
        raise ProgressArtifactError(
            f"{bug_path}: found_in_release must be a non-empty string, got {found!r}"
        )

    # spec: value may be null but key MUST be present.
    for nullable_key in ("target_release", "consumed_in_release"):
        if nullable_key not in fm:
            raise ProgressArtifactError(
                f"{bug_path}: BUG frontmatter is missing required field "
                f"{nullable_key!r} (value may be null, but the key must exist)"
            )
        value = fm[nullable_key]
        if value is not None and not isinstance(value, str):
            raise ProgressArtifactError(
                f"{bug_path}: {nullable_key} must be a string or null, "
                f"got {type(value).__name__} ({value!r})"
            )

    if "root_cause" not in fm:
        raise ProgressArtifactError(
            f"{bug_path}: BUG frontmatter is missing required field 'root_cause' "
            "(value may be null, but the key must exist)"
        )
    raw_root_cause = fm["root_cause"]
    if raw_root_cause is not None and raw_root_cause not in _BUG_ROOT_CAUSE_VALUES:
        raise ProgressArtifactError(
            f"{bug_path}: root_cause must be one of "
            f"{sorted(_BUG_ROOT_CAUSE_VALUES)} or null, got {raw_root_cause!r}"
        )
    if expect_root_cause is not None and raw_root_cause != expect_root_cause:
        raise ProgressArtifactError(
            f"{bug_path}: BUG root_cause must equal the caller-supplied "
            f"expected root_cause {expect_root_cause!r} "
            "(bug-start passes the --root-cause argument; bug-rework "
            "passes bug_flow.root_cause from progress.md; incident-start "
            "passes the literal 'prd-exception'), got "
            f"{raw_root_cause!r}"
        )

    return BugReportInfo(
        bug_id=bug_id,
        found_in_release=found,
        target_release=fm["target_release"],
        consumed_in_release=fm["consumed_in_release"],
        root_cause=raw_root_cause if isinstance(raw_root_cause, str) else None,
        rel_path=bug_path,
        body=doc.body,
    )


@dataclass(frozen=True)
class TriageAnalysis:
    """Result of parsing a BUG's ``## Triage Analysis`` section.

    ``unable_to_localize=True`` indicates the BUG body's
    ``Affected Task(s)`` line read ``unable to localize`` (or similar);
    callers must then escalate to ``development-planning-write`` instead
    of auto-rolling back tasks.

    ``classification`` is one of:
      * ``"test"`` — body language matches test-only / test-first /
        regression-test keywords; rollback target is ``test-revising``
        for ``verified``.
      * ``"source"`` — body language matches source-code / implementation
        keywords; rollback target is ``code-revising`` for
        ``verified`` / ``code-review-passed``.
      * ``"ambiguous"`` — neither keyword family was present; the spec
        says caller must NOT guess, leave task state unchanged, and add a
        history note requiring a planning-route decision.
    """

    affected_tasks: tuple[str, ...]
    classification: str  # "test" | "source" | "ambiguous"
    unable_to_localize: bool


def _classify_bug_body(body: str) -> str:
    lowered = body.lower()
    has_test = any(kw in lowered for kw in _TEST_FIX_KEYWORDS)
    has_source = any(kw in lowered for kw in _SOURCE_FIX_KEYWORDS)
    if has_test and not has_source:
        return "test"
    if has_source and not has_test:
        return "source"
    return "ambiguous"


def parse_bug_triage_analysis(body: str, *, rel_path: str) -> TriageAnalysis:
    """Parse a BUG's ``## Triage Analysis`` section.

    Looks for the canonical line ``**Affected Task(s)**: T1, T3`` (the
    spec wording); a value of ``unable to localize`` is treated as
    explicit non-localization, returning ``unable_to_localize=True`` with
    an empty task tuple.

    Raises :class:`ProgressArtifactError` if the section or the affected
    tasks line is missing, or if a listed task token does not match
    ``^T\\d+$``.
    """

    # Find the section header. We do a substring scan rather than full
    # markdown parsing to keep this dependency-free; the ``## Triage
    # Analysis`` heading is a fixed template per the spec.
    lower = body.lower()
    marker = "## triage analysis"
    idx = lower.find(marker)
    if idx < 0:
        raise ProgressArtifactError(
            f"{rel_path}: BUG body is missing required '## Triage Analysis' section"
        )
    section_text = body[idx:]
    # End at the next top-level ## heading (if any).
    next_heading_idx = -1
    for line_start in range(len(marker), len(section_text)):
        if section_text[line_start - 1] == "\n" and section_text[line_start:line_start + 3] == "## ":
            next_heading_idx = line_start
            break
    if next_heading_idx > 0:
        section_text = section_text[:next_heading_idx]

    match = _AFFECTED_TASKS_RE.search(section_text)
    if match is None:
        raise ProgressArtifactError(
            f"{rel_path}: BUG '## Triage Analysis' is missing required "
            "'**Affected Task(s)**: ...' line"
        )
    raw_value = match.group("value").strip()

    if raw_value.lower().startswith("unable to localize"):
        return TriageAnalysis(
            affected_tasks=(),
            classification=_classify_bug_body(section_text),
            unable_to_localize=True,
        )

    tokens: list[str] = []
    for piece in raw_value.replace(",", " ").split():
        token = piece.strip().rstrip(".")
        if not token:
            continue
        if not _TASK_ID_RE.match(token):
            raise ProgressArtifactError(
                f"{rel_path}: '**Affected Task(s)**' token must match "
                f"^T\\d+$, got {token!r}"
            )
        if token not in tokens:
            tokens.append(token)
    if not tokens:
        raise ProgressArtifactError(
            f"{rel_path}: '**Affected Task(s)**' line is empty (use 'unable to localize' "
            "to declare non-localizability)"
        )

    return TriageAnalysis(
        affected_tasks=tuple(tokens),
        classification=_classify_bug_body(section_text),
        unable_to_localize=False,
    )
