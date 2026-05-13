#!/usr/bin/env python3
"""doc-guardian Change Log helper.

Subcommands
-----------
- ``promote <doc>``  : merge ``## Pending Changes`` into ``## Change Log``
- ``validate <doc>`` : check Change Log discipline (no mutation)

The pure parsing/promotion logic lives in
``skills/_shared/dev_workflow/changelog.py`` so other helpers (status_transition
in Phase 4) can reuse it inside multi-doc transactions.

Exit codes: ``0`` success, ``1`` validation/promote failure, ``2`` CLI usage
error.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from skills._shared.dev_workflow.atomic import atomic_write_text  # noqa: E402
from skills._shared.dev_workflow.changelog import (  # noqa: E402
    ChangelogError,
    promote_text,
    validate_text,
)


def _resolve_doc(doc: str, root: Path) -> Path:
    path = Path(doc)
    return path if path.is_absolute() else root / path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def cmd_validate(doc: str, root: Path) -> int:
    target = _resolve_doc(doc, root)
    if not target.exists():
        print(f"changelog.py validate: file not found: {target}", file=sys.stderr)
        return 1
    issues = validate_text(_read(target))
    if issues:
        print(f"changelog.py validate failed for {target}:", file=sys.stderr)
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    return 0


def cmd_promote(doc: str, root: Path) -> int:
    target = _resolve_doc(doc, root)
    if not target.exists():
        print(f"changelog.py promote: file not found: {target}", file=sys.stderr)
        return 1
    content = _read(target)
    try:
        new_content, entries = promote_text(content)
    except ChangelogError as exc:
        print(f"changelog.py promote failed for {target}: {exc}", file=sys.stderr)
        return 1
    if not entries:
        return 0
    try:
        atomic_write_text(target, new_content)
    except OSError as exc:
        print(f"changelog.py promote: atomic write failed for {target}: {exc}", file=sys.stderr)
        return 1
    issues = validate_text(new_content)
    if issues:
        print(
            f"changelog.py promote wrote {target} but post-validate failed:",
            file=sys.stderr,
        )
        for issue in issues:
            print(f"- {issue}", file=sys.stderr)
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="changelog.py",
        description=(
            "Validate or promote Change Log sections per "
            "skills/doc-guardian/references/change-log-format.md."
        ),
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root used to resolve relative doc paths (default: cwd)",
    )
    sub = parser.add_subparsers(dest="cmd")
    p_validate = sub.add_parser(
        "validate", help="Validate Pending Changes / Change Log discipline (no mutation)"
    )
    p_validate.add_argument("doc", help="Doc path (relative to --root or absolute)")
    p_promote = sub.add_parser(
        "promote", help="Move Pending Changes entries into Change Log atomically"
    )
    p_promote.add_argument("doc", help="Doc path (relative to --root or absolute)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.cmd is None:
        parser.print_help(sys.stderr)
        return 2
    root = Path(args.root).resolve()
    if args.cmd == "validate":
        return cmd_validate(args.doc, root)
    if args.cmd == "promote":
        return cmd_promote(args.doc, root)
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
