#!/usr/bin/env python3
"""doc-guardian status_transition.py — frontmatter ``status`` transition helper.

Subcommands
-----------
- ``plan --event <event> --doc <path> ...``  : dry-run; print the planned
  per-doc transitions without writing.
- ``apply --event <event> --doc <path> ...`` : apply the transition with
  multi-doc all-or-nothing semantics. Mutates frontmatter ``status`` /
  ``updated`` and (for incremental docs) records a ``[frontmatter]`` Pending
  Changes entry that is promoted into the Change Log inside the same
  in-memory transaction. After every write succeeds, each mutated doc is
  re-validated through ``validate.validate_file``; any failure rolls every
  written doc back to its pre-transition contents.

Spec sources:
  - ``skills/doc-guardian/SKILL.md`` §6.7 (event mapping, sequencing).
  - ``skills/doc-guardian/references/change-log-format.md`` §7.1
    (``[frontmatter]`` Pending entry format).
  - ``skills/doc-guardian/references/frontmatter-schema.md`` §1-§2
    (universal fields, status state machine, gated types).

Exit codes (matches Phase 3 conventions):
  - ``0`` — success, including idempotent no-op.
  - ``1`` — pre-validate, mutate, write, or post-validate failure
            (after rollback when any writes had been issued).
  - ``2`` — CLI usage error (handled by ``argparse``).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Iterable

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Cross-script import: validate.py lives in the same scripts/ directory and is
# loaded via sys.path so we can call validate_file in-process (single source of
# truth for the post-write self-validate gate).
_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from skills._shared.dev_workflow.atomic import (  # noqa: E402
    AtomicWriteError,
    transaction,
)
from skills._shared.dev_workflow.changelog import (  # noqa: E402
    ChangelogError,
    promote_text,
)
from skills._shared.dev_workflow.frontmatter import (  # noqa: E402
    FrontmatterError,
    parse_frontmatter,
    render_markdown,
)
from skills._shared.dev_workflow.markdown import (  # noqa: E402
    MarkdownSectionError,
    find_section,
    replace_section_body,
)
from skills._shared.dev_workflow.schema import (  # noqa: E402
    DOC_TYPES,
    GATED_APPROVED_TYPES,
    INCREMENTAL_DOC_TYPES,
    STATUSES,
)

import validate as validate_module  # noqa: E402


PENDING_HEADING = "## Pending Changes"


EVENTS: dict[str, dict] = {
    "write-complete": {
        "allowed_old": ("draft", "revising"),
        "new_status": "in-review",
        "gated_only": False,
    },
    "review-issues": {
        "allowed_old": ("in-review",),
        "new_status": "revising",
        "gated_only": False,
    },
    "review-passed": {
        "allowed_old": ("in-review",),
        "new_status": "review-passed",
        "gated_only": False,
    },
    "human-confirmed": {
        "allowed_old": ("review-passed",),
        "new_status": "approved",
        "gated_only": True,
    },
}


class StatusTransitionError(RuntimeError):
    """Raised when a planned or applied transition cannot complete."""


@dataclass(frozen=True)
class PlanItem:
    doc_path: Path  # absolute, resolved
    rel_path: str
    doc_type: str | None
    is_incremental: bool
    current_status: str | None
    target_status: str
    op: str  # "mutate" | "no-op" | "reject"
    errors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ApplyResult:
    mutated: tuple[Path, ...]
    no_ops: tuple[Path, ...]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _resolve_doc(doc: str | Path, root: Path) -> Path:
    p = Path(doc)
    return p if p.is_absolute() else root / p


def _rel_for_display(abs_path: Path, root: Path) -> str:
    try:
        return str(abs_path.resolve().relative_to(root.resolve())).replace("\\", "/")
    except ValueError:
        return str(abs_path).replace("\\", "/")


def compute_plan(
    event: str, docs: Iterable[str | Path], root: Path
) -> list[PlanItem]:
    """Build a plan of per-doc transitions without touching the filesystem.

    The returned list mirrors the input ``docs`` order. Each item has
    ``op == "reject"`` carrying ``errors`` when the doc cannot transition,
    ``"no-op"`` when it is already at the target status, or ``"mutate"`` when
    the helper should rewrite the file.
    """

    if event not in EVENTS:
        raise StatusTransitionError(
            f"unknown event {event!r}; allowed: {sorted(EVENTS)}"
        )
    spec = EVENTS[event]
    target = spec["new_status"]

    plan: list[PlanItem] = []
    for doc in docs:
        abs_raw = _resolve_doc(doc, root)
        try:
            abs_path = abs_raw.resolve()
        except OSError:
            abs_path = abs_raw
        rel = _rel_for_display(abs_path, root)

        if not abs_path.exists():
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=None,
                    is_incremental=False,
                    current_status=None,
                    target_status=target,
                    op="reject",
                    errors=(f"file not found: {abs_path}",),
                )
            )
            continue

        try:
            content = abs_path.read_text(encoding="utf-8")
        except OSError as exc:
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=None,
                    is_incremental=False,
                    current_status=None,
                    target_status=target,
                    op="reject",
                    errors=(f"cannot read file: {exc}",),
                )
            )
            continue

        try:
            doc_obj = parse_frontmatter(content)
        except FrontmatterError as exc:
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=None,
                    is_incremental=False,
                    current_status=None,
                    target_status=target,
                    op="reject",
                    errors=(f"cannot parse frontmatter: {exc}",),
                )
            )
            continue

        fm = doc_obj.frontmatter
        raw_type = fm.get("type")
        doc_type = raw_type if isinstance(raw_type, str) else None
        raw_status = fm.get("status")
        current_status = raw_status if isinstance(raw_status, str) else None
        is_incremental = doc_type in INCREMENTAL_DOC_TYPES

        errors: list[str] = []
        if doc_type is None:
            errors.append("frontmatter missing required 'type'")
        elif doc_type not in DOC_TYPES:
            # Unknown type strings must reject up front. Without this, a doc
            # whose status coincidentally equals the event target would slip
            # through as no-op, returning a false-success signal to the
            # caller (Phase 4 round 2 review M1).
            errors.append(
                f"unknown doc type {doc_type!r}: not registered in schema DOC_TYPES"
            )
        if current_status is None or current_status not in STATUSES:
            errors.append(
                f"frontmatter 'status' must be one of {sorted(STATUSES)}, "
                f"got {raw_status!r}"
            )
        # Doc-type compatibility comes before any status-vs-target reasoning so
        # that human-confirmed on a non-gated type is rejected even when the
        # current status happens to coincidentally equal the target.
        if spec["gated_only"] and doc_type is not None and doc_type not in GATED_APPROVED_TYPES:
            errors.append(
                f"event 'human-confirmed' is only valid for {sorted(GATED_APPROVED_TYPES)}, "
                f"got type={doc_type}"
            )

        if errors:
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=doc_type,
                    is_incremental=is_incremental,
                    current_status=current_status,
                    target_status=target,
                    op="reject",
                    errors=tuple(errors),
                )
            )
            continue

        if current_status == target:
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=doc_type,
                    is_incremental=is_incremental,
                    current_status=current_status,
                    target_status=target,
                    op="no-op",
                )
            )
            continue

        if current_status not in spec["allowed_old"]:
            plan.append(
                PlanItem(
                    doc_path=abs_path,
                    rel_path=rel,
                    doc_type=doc_type,
                    is_incremental=is_incremental,
                    current_status=current_status,
                    target_status=target,
                    op="reject",
                    errors=(
                        f"event {event!r} requires current status in "
                        f"{list(spec['allowed_old'])}, got {current_status!r}",
                    ),
                )
            )
            continue

        plan.append(
            PlanItem(
                doc_path=abs_path,
                rel_path=rel,
                doc_type=doc_type,
                is_incremental=is_incremental,
                current_status=current_status,
                target_status=target,
                op="mutate",
            )
        )

    return plan


def _verify_plan_freshness(plan: list[PlanItem]) -> None:
    """Reject the plan if any non-rejected doc has drifted on disk.

    Phase 4 has no file lock between :func:`compute_plan` and
    :func:`apply_plan`. If a doc was edited by another caller in that window,
    the plan's recorded ``current_status`` / ``doc_type`` may no longer
    reflect the on-disk state, and writing the staged ``target_status`` could
    silently regress the doc to an older status. This preflight re-reads
    each non-reject item and aborts before any writes when on-disk values
    diverge from the plan (Phase 4 round 2 review M2).
    """

    discrepancies: list[str] = []
    for item in plan:
        if item.op == "reject":
            continue
        try:
            content = item.doc_path.read_text(encoding="utf-8")
            doc = parse_frontmatter(content)
        except (OSError, FrontmatterError) as exc:
            discrepancies.append(f"{item.rel_path}: re-read failed: {exc}")
            continue
        live_type = doc.frontmatter.get("type")
        live_status = doc.frontmatter.get("status")
        if live_type != item.doc_type:
            discrepancies.append(
                f"{item.rel_path}: type changed since plan was built "
                f"(plan={item.doc_type!r}, on-disk={live_type!r})"
            )
        if live_status != item.current_status:
            discrepancies.append(
                f"{item.rel_path}: status changed since plan was built "
                f"(plan={item.current_status!r}, on-disk={live_status!r})"
            )
    if discrepancies:
        raise StatusTransitionError(
            "stale plan detected; refusing to apply: "
            + "; ".join(discrepancies)
        )


def _build_new_content(content: str, item: PlanItem, now: str) -> str:
    """Compute the post-transition file content for a single mutating doc."""

    doc = parse_frontmatter(content)
    new_fm = dict(doc.frontmatter)
    new_fm["status"] = item.target_status
    new_fm["updated"] = now
    new_text = render_markdown(new_fm, doc.body)

    if not item.is_incremental:
        return new_text

    pending = find_section(new_text, PENDING_HEADING)
    if pending is None:
        raise StatusTransitionError(
            f"{item.rel_path}: incremental doc missing required '{PENDING_HEADING}' section"
        )

    new_entry = f"- {now} [frontmatter]: 更新 status 至 {item.target_status}"
    body_existing = pending.body.rstrip()
    new_pending_body = f"{body_existing}\n{new_entry}" if body_existing else new_entry

    new_text = replace_section_body(new_text, PENDING_HEADING, new_pending_body)

    # Promote in memory: this also re-parses the existing Change Log so a
    # previously hand-edited malformed log surfaces here rather than hitting
    # disk. The promote helper merges the new entry into the canonical
    # Change Log layout and clears Pending Changes.
    promoted_text, _entries = promote_text(new_text)
    return promoted_text


def apply_plan(
    plan: list[PlanItem], root: Path, *, now: str | None = None
) -> ApplyResult:
    """Apply a plan returned by :func:`compute_plan`.

    Multi-doc all-or-nothing: any failure during pre-flight content build, the
    transactional write, or the post-write self-validate raises
    :class:`StatusTransitionError`; the underlying ``transaction()`` context
    manager rolls every staged write back to its pre-transition bytes.

    Idempotent retry: docs whose ``op`` is ``no-op`` are returned without
    being touched; they never enter the transaction and never produce a
    Pending Changes ``[frontmatter]`` entry.
    """

    rejects = [item for item in plan if item.op == "reject"]
    if rejects:
        details = "; ".join(
            f"{item.rel_path}: {'; '.join(item.errors) or 'rejected'}" for item in rejects
        )
        raise StatusTransitionError(
            f"plan has {len(rejects)} rejected doc(s): {details}"
        )

    # Freshness gate: re-read each non-reject doc and abort the apply if any
    # doc's on-disk type/status no longer matches the plan recorded by
    # compute_plan(). This covers both the mutating subset (where a stale
    # write would regress doc state) and the no-op subset (where a stale
    # success signal would mislead the caller).
    _verify_plan_freshness(plan)

    if now is None:
        now = _utc_now_iso()

    mutate_items = [item for item in plan if item.op == "mutate"]
    no_op_items = [item for item in plan if item.op == "no-op"]

    if not mutate_items:
        return ApplyResult(
            mutated=tuple(),
            no_ops=tuple(item.doc_path for item in no_op_items),
        )

    finals: list[tuple[Path, str, PlanItem]] = []
    for item in mutate_items:
        try:
            content = item.doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StatusTransitionError(
                f"{item.rel_path}: cannot read file: {exc}"
            ) from exc
        try:
            new_content = _build_new_content(content, item, now)
        except (
            FrontmatterError,
            ChangelogError,
            MarkdownSectionError,
        ) as exc:
            raise StatusTransitionError(f"{item.rel_path}: {exc}") from exc
        finals.append((item.doc_path, new_content, item))

    with transaction() as tx:
        for abs_path, new_content, _item in finals:
            tx.write_text(abs_path, new_content)
        for abs_path, _content, item in finals:
            issues = validate_module.validate_file(abs_path, root)
            if issues:
                raise StatusTransitionError(
                    f"{item.rel_path}: post-write validate failed: "
                    + "; ".join(issues)
                )

    return ApplyResult(
        mutated=tuple(item.doc_path for _, _, item in finals),
        no_ops=tuple(item.doc_path for item in no_op_items),
    )


# ---------- CLI ----------


def _format_plan_line(item: PlanItem) -> str:
    if item.op == "reject":
        err_text = "; ".join(item.errors) or "rejected"
        return f"  REJECT  {item.rel_path}: {err_text}"
    return (
        f"  {item.op.upper():<7} {item.rel_path}: "
        f"{item.current_status} -> {item.target_status} "
        f"(type={item.doc_type})"
    )


def _print_plan(event: str, plan: list[PlanItem], stream) -> None:
    print(f"status_transition.py plan event={event}", file=stream)
    for item in plan:
        print(_format_plan_line(item), file=stream)


def cmd_plan(event: str, docs: list[str], root: Path) -> int:
    try:
        plan = compute_plan(event, docs, root)
    except StatusTransitionError as exc:
        print(f"status_transition.py plan: {exc}", file=sys.stderr)
        return 1
    has_reject = any(item.op == "reject" for item in plan)
    stream = sys.stderr if has_reject else sys.stdout
    _print_plan(event, plan, stream)
    return 1 if has_reject else 0


def cmd_apply(event: str, docs: list[str], root: Path) -> int:
    try:
        plan = compute_plan(event, docs, root)
    except StatusTransitionError as exc:
        print(f"status_transition.py apply: {exc}", file=sys.stderr)
        return 1
    if any(item.op == "reject" for item in plan):
        print(
            "status_transition.py apply: refusing to mutate; planning rejected:",
            file=sys.stderr,
        )
        for item in plan:
            print(_format_plan_line(item), file=sys.stderr)
        return 1
    try:
        result = apply_plan(plan, root)
    except StatusTransitionError as exc:
        print(f"status_transition.py apply: {exc}", file=sys.stderr)
        return 1
    except (AtomicWriteError, OSError) as exc:
        print(
            f"status_transition.py apply: write/rollback I/O failure: {exc}",
            file=sys.stderr,
        )
        return 1
    if result.mutated:
        rels = ", ".join(_rel_for_display(p, root) for p in result.mutated)
        print(f"status_transition.py apply mutated event={event}: {rels}")
    if result.no_ops:
        rels = ", ".join(_rel_for_display(p, root) for p in result.no_ops)
        print(
            f"status_transition.py apply no-op (already at target) event={event}: {rels}",
            file=sys.stderr,
        )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="status_transition.py",
        description=(
            "doc-guardian status_transition.py — apply doc frontmatter status "
            "transitions atomically, with Change Log discipline for incremental "
            "docs. Sequenced after a successful 'progress.py update --event'."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root used to resolve relative doc paths (default: cwd)",
    )
    sub = parser.add_subparsers(dest="cmd")

    p_plan = sub.add_parser(
        "plan",
        help="Dry-run: print planned per-doc transitions without writing",
    )
    p_plan.add_argument(
        "--event",
        required=True,
        choices=sorted(EVENTS.keys()),
        help="Transition event",
    )
    p_plan.add_argument(
        "--doc",
        action="append",
        dest="docs",
        required=True,
        metavar="PATH",
        help="Doc path (relative to --root or absolute). Repeat for multi-doc.",
    )

    p_apply = sub.add_parser(
        "apply",
        help="Apply transition; multi-doc all-or-nothing rollback on failure",
    )
    p_apply.add_argument(
        "--event",
        required=True,
        choices=sorted(EVENTS.keys()),
        help="Transition event",
    )
    p_apply.add_argument(
        "--doc",
        action="append",
        dest="docs",
        required=True,
        metavar="PATH",
        help="Doc path (relative to --root or absolute). Repeat for multi-doc.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help(sys.stderr)
        return 2
    root = Path(args.root).resolve()
    if args.cmd == "plan":
        return cmd_plan(args.event, args.docs, root)
    if args.cmd == "apply":
        return cmd_apply(args.event, args.docs, root)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
