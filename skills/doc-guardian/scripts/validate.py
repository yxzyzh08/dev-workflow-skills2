#!/usr/bin/env python3
"""doc-guardian validate.py — single-file binary checks + cross-progress consistency.

Subcommands
-----------
- ``file <doc>``      : run checks 1-7 on a single doc and exit 0/1
- ``ids``             : enforce ID uniqueness across docs/cr, docs/bug, docs/incident
- ``consistency``     : Class 8 cross-progress check — derive required artifacts
                        for ``progress.md.current_stage`` via
                        ``required-artifacts.md`` resolver, assert each exists
                        and passes ``file <doc>``. Exit 0 OK / 1 inconsistent /
                        2 only on usage error.
- ``all``             : full-project sweep over every doc type (deferred to Phase 7)

Class index (per docs/implementation/task6_plan_20260507.md §7 + SKILL.md §5):
  1 Path                 — type → directory mapping
  2 Naming               — filename convention
  3 Frontmatter Schema   — universal + per-type required fields, enums
  4 Frontmatter Format   — timestamps / release / owner / IDs / counts / bools
  5 Cross-Reference      — path refs exist; ID refs resolve under docs/bug/
  6 Change Log Discipline — delegate to changelog.validate_text
  7 ID Uniqueness        — single-file format match; multi-file via ``ids``
  8 Consistency          — required-artifact existence + per-file validity
                           (Phase 6.4: ``consistency`` subcommand)
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.dev_workflow.changelog import validate_text as validate_changelog_text  # noqa: E402
from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    FrontmatterError,
    parse_frontmatter,
)
from skills._shared.dev_workflow.schema import (  # noqa: E402
    DOC_TYPES,
    GATED_APPROVED_TYPES,
    INCREMENTAL_DOC_TYPES,
    PER_TYPE_REQUIRED_FIELDS,
    REVIEW_STATUSES,
    SOURCE_ANALYSIS_PATHS,
    STATUSES,
    TYPE_PATHS,
    UNIVERSAL_FIELDS,
    VERIFICATION_STATUSES,
)


# ---------- regexes ----------

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_RELEASE_RE = re.compile(r"^\d+\.\d+$")
_OWNER_RE = re.compile(r"^[^/]+/[^/]+$")
_CR_ID_RE = re.compile(r"^CR-\d{3}$")
_BUG_ID_RE = re.compile(r"^BUG-\d{3}$")
_INCIDENT_ID_RE = re.compile(r"^INCIDENT-\d{3}$")
_TASK_ID_RE = re.compile(r"^T\d+$")
_NORMAL_FILENAME_RE = re.compile(r"^[a-z][a-z0-9_]*\.md$")
_ID_FILENAME_RE = re.compile(r"^(CR|BUG|INCIDENT)-\d{3}\.md$")

_ANALYSIS_KINDS = set(SOURCE_ANALYSIS_PATHS.keys())
_ANALYSIS_KINDS_RELEASE_OPTIONAL = {"prd-level", "feature-matrix"}
_MAX_SEVERITIES = {"low", "medium", "high", "critical"}
_RESOLUTION_ACTIONS = {"continue", "abort", "reconstruct"}
_ROOT_CAUSES = {"srs", "architecture", "development", "prd-exception"}


# ---------- helpers ----------


def _normalize_relpath(path: Path, root: Path) -> str:
    abs_path = path if path.is_absolute() else (root / path)
    resolved = abs_path.resolve()
    try:
        return str(resolved.relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(resolved).replace("\\", "/")


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _expected_path(fm: dict) -> str | None:
    """Return the canonical relative path for a doc based on its frontmatter, or None."""

    doc_type = fm.get("type")
    if doc_type == "source-system-analysis":
        kind = fm.get("analysis_kind")
        template = SOURCE_ANALYSIS_PATHS.get(kind) if isinstance(kind, str) else None
        if template is None:
            return None
        if "{release}" not in template:
            return template
        release = fm.get("release")
        if not isinstance(release, str):
            return None
        return template.format(release=release)
    template = TYPE_PATHS.get(doc_type) if isinstance(doc_type, str) else None
    if template is None:
        return None
    needed = re.findall(r"\{(\w+)\}", template)
    values: dict[str, str] = {}
    for key in needed:
        value = fm.get(key)
        if not isinstance(value, str) or value == "":
            return None
        values[key] = value
    return template.format(**values)


# ---------- check classes ----------


def check_class_1_path(fm: dict, abs_path: Path, root: Path) -> list[str]:
    expected = _expected_path(fm)
    actual = _normalize_relpath(abs_path, root)
    if expected is None:
        return [
            f"Class 1 (Path): cannot derive expected path for type={fm.get('type')!r}; "
            "fix Class 3/4 frontmatter errors first"
        ]
    if actual != expected:
        return [
            f"Class 1 (Path): {actual} should be {expected} based on type={fm.get('type')}"
        ]
    return []


def check_class_2_naming(abs_path: Path) -> list[str]:
    name = abs_path.name
    if _ID_FILENAME_RE.match(name):
        return []
    if not _NORMAL_FILENAME_RE.match(name):
        return [
            f"Class 2 (Naming): filename {name!r} must match ^[a-z][a-z0-9_]*\\.md$ "
            "or ^(CR|BUG|INCIDENT)-\\d{3}\\.md$"
        ]
    return []


def check_class_3_schema(fm: dict) -> list[str]:
    issues: list[str] = []

    for key in UNIVERSAL_FIELDS:
        if key not in fm:
            issues.append(f"Class 3 (Schema): missing universal field: {key}")

    doc_type = fm.get("type")
    if doc_type not in DOC_TYPES:
        issues.append(f"Class 3 (Schema): unknown or missing type: {doc_type!r}")
        return issues

    for key in PER_TYPE_REQUIRED_FIELDS.get(doc_type, ()):
        if key not in fm:
            issues.append(f"Class 3 (Schema): {doc_type} missing required field: {key}")

    status = fm.get("status")
    if status not in STATUSES:
        issues.append(
            f"Class 3 (Schema): status must be one of {sorted(STATUSES)}, got {status!r}"
        )
    if status == "approved" and doc_type not in GATED_APPROVED_TYPES:
        issues.append(
            f"Class 3 (Schema): status=approved is only valid for gated types "
            f"{sorted(GATED_APPROVED_TYPES)}, not {doc_type}"
        )

    if doc_type == "source-system-analysis":
        kind = fm.get("analysis_kind")
        if kind not in _ANALYSIS_KINDS:
            issues.append(
                f"Class 3 (Schema): analysis_kind must be one of {sorted(_ANALYSIS_KINDS)}, "
                f"got {kind!r}"
            )

    return issues


def check_class_4_format(fm: dict) -> list[str]:
    issues: list[str] = []
    doc_type = fm.get("type")

    if "title" in fm:
        value = fm["title"]
        if not isinstance(value, str) or not value.strip():
            issues.append(
                f"Class 4 (Format): title must be a non-empty string, "
                f"got {type(value).__name__} ({value!r})"
            )

    for key in ("created", "updated"):
        if key not in fm:
            continue
        value = fm[key]
        if not isinstance(value, str):
            issues.append(
                f"Class 4 (Format): {key} must be an ISO8601 UTC string, "
                f"got {type(value).__name__} ({value!r})"
            )
        elif not _TIMESTAMP_RE.match(value):
            issues.append(
                f"Class 4 (Format): {key} must match ^\\d{{4}}-\\d{{2}}-\\d{{2}}T\\d{{2}}:\\d{{2}}:\\d{{2}}Z$, "
                f"got {value!r}"
            )

    if "release" in fm:
        release = fm["release"]
        if release is None:
            allow_null = (
                doc_type == "source-system-analysis"
                and fm.get("analysis_kind") in _ANALYSIS_KINDS_RELEASE_OPTIONAL
            )
            if not allow_null:
                issues.append(
                    "Class 4 (Format): release must not be null for this doc type"
                )
        elif not isinstance(release, str):
            issues.append(
                "Class 4 (Format): release must be a quoted YAML string (e.g. \"0.1\"); "
                f"YAML parsed it as {type(release).__name__} ({release!r})"
            )
        elif not _RELEASE_RE.match(release):
            issues.append(
                f"Class 4 (Format): release must match ^\\d+\\.\\d+$, got {release!r}"
            )

    if "owner" in fm:
        owner = fm["owner"]
        if not isinstance(owner, str) or not _OWNER_RE.match(owner):
            issues.append(
                "Class 4 (Format): owner must be 'agent_id/skill_name' with non-empty halves, "
                f"got {owner!r}"
            )

    for key, regex in (
        ("cr_id", _CR_ID_RE),
        ("bug_id", _BUG_ID_RE),
        ("incident_id", _INCIDENT_ID_RE),
    ):
        if key not in fm:
            continue
        value = fm[key]
        if value is None:
            issues.append(f"Class 4 (Format): {key} must not be null")
        elif not isinstance(value, str) or not regex.match(value):
            issues.append(
                f"Class 4 (Format): {key} must match {regex.pattern}, got {value!r}"
            )

    if "task_id" in fm:
        value = fm["task_id"]
        if value is None:
            issues.append("Class 4 (Format): task_id must not be null")
        elif not isinstance(value, str) or not _TASK_ID_RE.match(value):
            issues.append(
                f"Class 4 (Format): task_id must match ^T\\d+$, got {value!r}"
            )

    if doc_type == "srs":
        for key in ("is_multi_module", "architecture_change"):
            if key not in fm:
                continue
            value = fm[key]
            if not isinstance(value, bool):
                issues.append(
                    f"Class 4 (Format): srs.{key} must be a YAML bool, "
                    f"got {type(value).__name__} ({value!r})"
                )

    if "verification_status" in fm:
        value = fm["verification_status"]
        if value not in VERIFICATION_STATUSES:
            issues.append(
                f"Class 4 (Format): verification_status must be in "
                f"{sorted(VERIFICATION_STATUSES)}, got {value!r}"
            )

    if doc_type in {"code-review-report", "test-review-report"}:
        review_status = fm.get("review_status")
        if review_status not in REVIEW_STATUSES:
            issues.append(
                f"Class 4 (Format): review_status must be in {sorted(REVIEW_STATUSES)}, "
                f"got {review_status!r}"
            )
        for key in ("findings_count", "blocking_findings_count"):
            value = fm.get(key)
            if not _is_non_negative_int(value):
                issues.append(
                    f"Class 4 (Format): {key} must be a non-negative int, got {value!r}"
                )
        max_severity = fm.get("max_severity")
        if max_severity not in _MAX_SEVERITIES:
            issues.append(
                f"Class 4 (Format): max_severity must be in {sorted(_MAX_SEVERITIES)}, "
                f"got {max_severity!r}"
            )
        sev_dist = fm.get("severity_distribution")
        if not isinstance(sev_dist, dict):
            issues.append(
                "Class 4 (Format): severity_distribution must be a mapping with "
                "critical/high/medium/low integer counts"
            )
        else:
            for level in ("critical", "high", "medium", "low"):
                value = sev_dist.get(level)
                if not _is_non_negative_int(value):
                    issues.append(
                        f"Class 4 (Format): severity_distribution.{level} must be "
                        f"a non-negative int, got {value!r}"
                    )
        if review_status == "pass":
            blocking = fm.get("blocking_findings_count")
            if isinstance(blocking, int) and not isinstance(blocking, bool) and blocking != 0:
                issues.append(
                    f"Class 4 (Format): review_status=pass requires "
                    f"blocking_findings_count==0, got {blocking}"
                )

    if doc_type == "test-report":
        ints_ok = True
        for key in ("total_test_cases", "passed", "failed"):
            value = fm.get(key)
            if not _is_non_negative_int(value):
                issues.append(
                    f"Class 4 (Format): {key} must be a non-negative int, got {value!r}"
                )
                ints_ok = False
        skipped = fm.get("skipped")
        if skipped is not None and not _is_non_negative_int(skipped):
            issues.append(
                f"Class 4 (Format): skipped must be a non-negative int when present, "
                f"got {skipped!r}"
            )
            ints_ok = False
        if ints_ok:
            sk = int(skipped) if skipped is not None else 0
            total = int(fm["total_test_cases"])
            expected_total = int(fm["passed"]) + int(fm["failed"]) + sk
            if total != expected_total:
                issues.append(
                    "Class 4 (Format): total_test_cases must equal passed + failed "
                    f"+ skipped; total={total}, passed={fm['passed']}, "
                    f"failed={fm['failed']}, skipped={sk}"
                )

    if doc_type == "workflow-incident":
        triggered = fm.get("triggered_by_bug")
        if "triggered_by_bug" in fm:
            if triggered is None:
                issues.append("Class 4 (Format): triggered_by_bug must not be null")
            elif not isinstance(triggered, str) or not _BUG_ID_RE.match(triggered):
                issues.append(
                    "Class 4 (Format): triggered_by_bug must be a BUG-NNN ID "
                    f"(e.g. BUG-007), not a path or other value; got {triggered!r}"
                )
        triggered_release = fm.get("triggered_in_release")
        if "triggered_in_release" in fm:
            if triggered_release is None:
                issues.append("Class 4 (Format): triggered_in_release must not be null")
            elif not isinstance(triggered_release, str) or not _RELEASE_RE.match(triggered_release):
                issues.append(
                    "Class 4 (Format): triggered_in_release must be a quoted release "
                    f"string, got {triggered_release!r}"
                )
        if "resolution_action" in fm:
            value = fm["resolution_action"]
            if value is not None and value not in _RESOLUTION_ACTIONS:
                issues.append(
                    f"Class 4 (Format): resolution_action must be in "
                    f"{sorted(_RESOLUTION_ACTIONS)} or null, got {value!r}"
                )

    if doc_type == "bug-report":
        for key in ("target_release", "consumed_in_release"):
            if key not in fm:
                continue
            value = fm[key]
            if value is None:
                continue
            if not isinstance(value, str) or not _RELEASE_RE.match(value):
                issues.append(
                    f"Class 4 (Format): {key} must be a quoted release string or null, "
                    f"got {value!r}"
                )
        if "found_in_release" in fm:
            value = fm["found_in_release"]
            if value is None:
                issues.append("Class 4 (Format): found_in_release must not be null")
            elif not isinstance(value, str) or not _RELEASE_RE.match(value):
                issues.append(
                    "Class 4 (Format): found_in_release must be a quoted release "
                    f"string, got {value!r}"
                )
        if "root_cause" in fm:
            value = fm["root_cause"]
            if value is not None and value not in _ROOT_CAUSES:
                issues.append(
                    f"Class 4 (Format): root_cause must be in {sorted(_ROOT_CAUSES)} "
                    f"or null, got {value!r}"
                )

    if doc_type == "cr":
        # CR target_release is required and must be a non-null quoted release
        # string (frontmatter-schema.md §3.4 / §4.2). Class 3 only checks key
        # presence; we own the format check here.
        if "target_release" in fm:
            value = fm["target_release"]
            if value is None:
                issues.append("Class 4 (Format): cr.target_release must not be null")
            elif not isinstance(value, str):
                issues.append(
                    "Class 4 (Format): cr.target_release must be a quoted YAML string "
                    f"(e.g. \"0.1\"); YAML parsed it as {type(value).__name__} ({value!r})"
                )
            elif not _RELEASE_RE.match(value):
                issues.append(
                    "Class 4 (Format): cr.target_release must match ^\\d+\\.\\d+$, "
                    f"got {value!r}"
                )

    if doc_type == "task-breakdown":
        if "total_tasks" in fm and not _is_non_negative_int(fm.get("total_tasks")):
            issues.append(
                f"Class 4 (Format): total_tasks must be a non-negative int, "
                f"got {fm.get('total_tasks')!r}"
            )

    if doc_type == "source-system-analysis":
        if "source_system_name" in fm:
            value = fm["source_system_name"]
            if not isinstance(value, str) or not value.strip():
                issues.append(
                    "Class 4 (Format): source_system_name must be a non-empty string, "
                    f"got {value!r}"
                )

    return issues


def _validate_path_reference(key: str, value: object, root: Path) -> list[str]:
    """Strict validation for required path-reference frontmatter fields.

    Per ``frontmatter-schema.md §4.5`` and ``directory-layout.md §3.3``:
      - value must be a non-empty string
      - value must use forward slashes (no backslashes)
      - value must be project-root relative (not absolute)
      - value must not contain ``.`` / ``..`` segments
      - resolved target must remain under ``root``
      - resolved target must exist
    """

    if value is None:
        return [f"Class 5 (Cross-Ref): {key} must not be null"]
    if not isinstance(value, str):
        return [
            f"Class 5 (Cross-Ref): {key} must be a string path, "
            f"got {type(value).__name__} ({value!r})"
        ]
    if not value:
        return [f"Class 5 (Cross-Ref): {key} must not be empty"]
    if "\\" in value:
        return [
            f"Class 5 (Cross-Ref): {key} must use forward slashes, got {value!r}"
        ]
    if value.startswith("/") or (len(value) >= 2 and value[1] == ":"):
        return [
            f"Class 5 (Cross-Ref): {key} must be project-root relative, "
            f"not absolute: {value!r}"
        ]
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return [
            f"Class 5 (Cross-Ref): {key} must not contain '.' or '..' segments "
            f"(or empty segments): {value!r}"
        ]
    root_resolved = root.resolve()
    target = (root_resolved / value).resolve()
    try:
        target.relative_to(root_resolved)
    except ValueError:
        return [
            f"Class 5 (Cross-Ref): {key}={value!r} resolves outside the "
            "project root"
        ]
    if not target.exists():
        return [
            f"Class 5 (Cross-Ref): {key} references {value} which does not exist"
        ]
    return []


def check_class_5_cross_reference(fm: dict, root: Path) -> list[str]:
    issues: list[str] = []
    doc_type = fm.get("type")

    # All three of these path references are non-null required fields per
    # frontmatter-schema.md §3.2 / §3.4. Only run the strict check when the
    # field is part of the doc type's required schema; for unrelated types
    # the field would not appear at all.
    required_path_refs = {
        "acceptance-plan": ("related_srs",),
        "architecture-delta": ("parent_architecture",),
        "cr": ("affected_doc",),
    }
    for key in required_path_refs.get(doc_type, ()):
        if key not in fm:
            continue
        issues.extend(_validate_path_reference(key, fm[key], root))

    triggered = fm.get("triggered_by_bug")
    if isinstance(triggered, str) and _BUG_ID_RE.match(triggered):
        target = (root / "docs" / "bug" / f"{triggered}.md").resolve()
        if not target.exists():
            try:
                rel = target.relative_to(root.resolve())
                rel_text = str(rel).replace("\\", "/")
            except ValueError:
                rel_text = str(target)
            issues.append(
                f"Class 5 (Cross-Ref): triggered_by_bug={triggered} resolves to "
                f"{rel_text} which does not exist"
            )

    return issues


def check_class_6_changelog(fm: dict, content: str) -> list[str]:
    doc_type = fm.get("type")
    raw_issues = validate_changelog_text(content)
    if doc_type not in INCREMENTAL_DOC_TYPES:
        # snapshot doc: missing sections are fine; only carry forward any
        # malformed-section issues if the author chose to include them.
        raw_issues = [i for i in raw_issues if not i.startswith("Missing '##")]
    return [f"Class 6 (Change Log): {issue}" for issue in raw_issues]


def check_class_7_id_uniqueness_single(fm: dict, abs_path: Path) -> list[str]:
    issues: list[str] = []
    name = abs_path.name
    for key in ("cr_id", "bug_id", "incident_id"):
        value = fm.get(key)
        if not isinstance(value, str):
            continue
        expected = f"{value}.md"
        if name != expected:
            issues.append(
                f"Class 7 (ID): filename {name!r} should equal {expected} based on {key}"
            )
    return issues


_DIRECTORY_PREFIXES = (
    ("cr", "CR"),
    ("bug", "BUG"),
    ("incident", "INCIDENT"),
)


def check_ids_uniqueness(root: Path) -> list[str]:
    """Walk docs/cr, docs/bug, docs/incident and report bad-prefix or duplicate IDs.

    Per ``directory-layout.md §2.6 / §3.1``, each directory carries exactly
    one ID prefix: ``docs/cr/`` holds ``CR-NNN.md`` only, ``docs/bug/`` holds
    ``BUG-NNN.md`` only, and ``docs/incident/`` holds ``INCIDENT-NNN.md`` only.
    A misplaced ID file (e.g. ``docs/bug/CR-001.md``) is rejected here even
    though Class 1 path validation would also catch it for a single file.
    """

    issues: list[str] = []
    for sub, prefix in _DIRECTORY_PREFIXES:
        dir_path = root / "docs" / sub
        if not dir_path.is_dir():
            continue
        pattern = re.compile(rf"^{prefix}-\d{{3}}\.md$")
        seen: dict[str, Path] = {}
        for entry in sorted(dir_path.iterdir()):
            if not entry.is_file() or entry.suffix != ".md":
                continue
            if not pattern.match(entry.name):
                rel = entry.relative_to(root)
                issues.append(
                    f"Class 7 (IDs): {rel} filename must match "
                    rf"^{prefix}-\d{{3}}\.md$ in docs/{sub}/"
                )
                continue
            stem = entry.stem
            if stem in seen:
                rel_a = seen[stem].relative_to(root)
                rel_b = entry.relative_to(root)
                issues.append(
                    f"Class 7 (IDs): duplicate ID {stem} at {rel_a} and {rel_b}"
                )
            else:
                seen[stem] = entry
    return issues


# ---------- top-level entry points ----------


def validate_file(doc_path: Path | str, root: Path | str = ".") -> list[str]:
    """Run classes 1-7 on a single doc; return list of issues (empty == valid)."""

    root_path = Path(root).resolve()
    raw_doc = Path(doc_path)
    abs_path = raw_doc if raw_doc.is_absolute() else (root_path / raw_doc)
    if not abs_path.exists():
        return [f"File not found: {abs_path}"]

    try:
        content = abs_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Cannot read {abs_path}: {exc}"]

    try:
        doc = parse_frontmatter(content)
    except FrontmatterError as exc:
        return [f"Class 3 (Schema): cannot parse frontmatter: {exc}"]

    fm = doc.frontmatter
    issues: list[str] = []
    issues += check_class_3_schema(fm)
    issues += check_class_4_format(fm)
    issues += check_class_1_path(fm, abs_path, root_path)
    issues += check_class_2_naming(abs_path)
    issues += check_class_5_cross_reference(fm, root_path)
    issues += check_class_6_changelog(fm, content)
    issues += check_class_7_id_uniqueness_single(fm, abs_path)
    return issues


def check_consistency(root: Path | str = ".") -> list[str]:
    """Class 8 cross-progress consistency check (Phase 6.4).

    Reads ``progress.md`` from ``root``, derives the required-artifact
    list for the current stage via
    :func:`skills._shared.dev_workflow.artifacts.get_required_artifacts`,
    and asserts that:

      * each derived artifact path exists on disk;
      * each existing artifact passes :func:`validate_file` (classes 1-7);
      * (light Class 8 checks) progress.md ``current_stage`` /
        ``sub_state`` are well-formed enums.

    Returns the list of issue strings; empty list ⇔ consistent. The CLI
    entry point converts an empty list to exit 0 and a non-empty list
    to exit 1.

    The function does not mutate any file. It is safe to call from
    ``progress.py update --advance`` post-checks or from a stand-alone
    ``validate.py consistency`` invocation. ``workflow-incident-analysis``
    pseudo-stage is intentionally skipped: Phase 6.3's incident-resolve
    is the gatekeeper for that state, not the P6 matrix.

    Spec sources:
      * ``docs/implementation/task6_plan_20260507.md`` §7 (Class 8
        consistency definition);
      * ``skills/doc-guardian/references/required-artifacts.md`` §12
        (consistency algorithm sketch).
    """

    root_path = Path(root)
    issues: list[str] = []

    progress_path = root_path / "progress.md"
    if not progress_path.exists():
        return [f"progress.md not found at {progress_path}"]

    try:
        content = progress_path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"cannot read progress.md: {exc}"]
    try:
        doc = parse_frontmatter(content)
    except FrontmatterError as exc:
        return [f"progress.md frontmatter is malformed: {exc}"]
    fm = doc.frontmatter

    # Light Class 8 checks before delegating to artifacts derivation.
    current_stage = fm.get("current_stage")
    if current_stage is None:
        return ["progress.md.current_stage is required"]
    if current_stage == "workflow-incident-analysis":
        # Spec: this pseudo-stage bypasses P6; consistency check has no
        # required artifact list to enforce here.
        return []
    sub_state = fm.get("sub_state")
    if sub_state is not None and not isinstance(sub_state, str):
        issues.append(
            f"progress.md.sub_state must be a string or null, got "
            f"{type(sub_state).__name__}"
        )

    # Derive required artifacts for the current stage. ArtifactError
    # at this layer means the progress.md state itself is internally
    # malformed (e.g. unknown current_stage), so report and short-circuit.
    try:
        from skills._shared.dev_workflow.artifacts import (  # type: ignore
            ArtifactError,
            get_required_artifacts,
        )
    except ImportError as exc:  # pragma: no cover - defensive
        return [f"cannot import artifacts module: {exc}"]
    try:
        required = get_required_artifacts(fm, root=root_path)
    except ArtifactError as exc:
        return [f"required-artifact derivation failed: {exc}"]
    except (KeyError, TypeError, AttributeError) as exc:
        # Round 2 M2: progress.md may parse as YAML but still be
        # missing resolver-required fields (scenario / release /
        # current_stage) or have wrong types. progress_from_mapping
        # indexes those keys directly, raising KeyError / TypeError /
        # AttributeError before ArtifactError can fire. Convert into a
        # clean exit-1 diagnostic.
        return [
            "progress.md is structurally incomplete; required-artifact "
            f"resolver inputs are missing or wrong type: {exc!r}"
        ]

    seen: set[str] = set()
    for spec in required:
        if spec.path in seen:
            continue
        seen.add(spec.path)
        artifact_abs = root_path / spec.path
        if not artifact_abs.exists():
            issues.append(
                f"required artifact missing: {spec.path} "
                f"(type={spec.type})"
            )
            continue
        per_file_issues = validate_file(spec.path, root_path)
        for issue in per_file_issues:
            issues.append(f"{spec.path}: {issue}")

    return issues


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate.py",
        description=(
            "doc-guardian validate.py — single-file binary checks (classes 1-7) + ID uniqueness. "
            "Reuses change-log validation from skills/_shared/dev_workflow/changelog.py."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root used to resolve relative doc paths and ID references (default: cwd)",
    )
    sub = parser.add_subparsers(dest="cmd")
    p_file = sub.add_parser("file", help="Validate a single doc (classes 1-7)")
    p_file.add_argument("doc")
    sub.add_parser(
        "ids", help="Check ID uniqueness across docs/cr, docs/bug, docs/incident"
    )
    sub.add_parser(
        "all",
        help="Validate every doc in docs/ (deferred to Phase 7)",
    )
    sub.add_parser(
        "consistency",
        help=(
            "Class 8 cross-progress consistency check — required-artifact "
            "existence + per-file validity for the current stage"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help(sys.stderr)
        return 2
    root = Path(args.root).resolve()

    if args.cmd == "file":
        issues = validate_file(args.doc, root)
        if issues:
            print(f"validate.py file failed for {args.doc}:", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "ids":
        issues = check_ids_uniqueness(root)
        if issues:
            print("validate.py ids failed:", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "consistency":
        issues = check_consistency(root)
        if issues:
            print("validate.py consistency failed:", file=sys.stderr)
            for issue in issues:
                print(f"- {issue}", file=sys.stderr)
            return 1
        return 0

    if args.cmd == "all":
        print(
            "validate.py all is deferred to Phase 7 (full-project sweep "
            "across every doc type). Use 'file <doc>', 'ids', or "
            "'consistency' for now.",
            file=sys.stderr,
        )
        return 2

    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
