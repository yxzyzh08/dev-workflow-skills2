"""Tests for skills/doc-guardian/scripts/status_transition.py."""

from __future__ import annotations

from pathlib import Path
import importlib
import io
import sys
import tempfile
import unittest
from unittest.mock import patch

import yaml


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "skills" / "doc-guardian" / "scripts"
for _path in (_SCRIPTS_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

status_transition = importlib.import_module("status_transition")
validate_module = importlib.import_module("validate")

from skills._shared.dev_workflow.changelog import validate_text  # noqa: E402
from skills._shared.dev_workflow.frontmatter import parse_frontmatter  # noqa: E402


# ---------- fixture builders (temp-dir only) ----------


def _emit_yaml(fm: dict) -> str:
    return yaml.safe_dump(
        fm, allow_unicode=True, default_flow_style=False, sort_keys=False
    ).rstrip()


_DEFAULT_BODY = "# Title\n\nContent.\n"
_DEFAULT_CHANGELOG = "### 2026-05-15\n\n- 2026-05-15T09:00:00Z [Section 1]: 初始版本"


def _build_doc(
    fm: dict,
    body: str = _DEFAULT_BODY,
    *,
    pending: str | None = "",
    change_log: str | None = _DEFAULT_CHANGELOG,
) -> str:
    text = f"---\n{_emit_yaml(fm)}\n---\n{body}"
    if pending is not None:
        text += (
            f"\n## Pending Changes\n\n{pending}\n"
            if pending
            else "\n## Pending Changes\n\n"
        )
    if change_log is not None:
        text += (
            f"\n## Change Log\n\n{change_log}\n"
            if change_log
            else "\n## Change Log\n\n"
        )
    return text


def _write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def _base_universal(
    *,
    type_: str,
    status: str,
    owner: str,
    title: str | None = None,
    created: str = "2026-05-15T10:00:00Z",
    updated: str = "2026-05-15T10:00:00Z",
) -> dict:
    return {
        "title": title or f"{type_} doc",
        "type": type_,
        "status": status,
        "created": created,
        "updated": updated,
        "owner": owner,
    }


def _make_srs(root: Path, *, status: str = "draft") -> Path:
    fm = _base_universal(
        type_="srs",
        status=status,
        owner="claude-opus-4-7/srs-write",
        title="App v0.1 SRS",
    )
    fm.update({"release": "0.1", "is_multi_module": False, "architecture_change": False})
    return _write(root, "docs/release0.1/srs/srs.md", _build_doc(fm))


def _make_prd(root: Path, *, status: str = "draft") -> Path:
    fm = _base_universal(
        type_="prd",
        status=status,
        owner="claude-opus-4-7/prd-write",
        title="App PRD",
    )
    return _write(root, "docs/prd/prd.md", _build_doc(fm))


def _make_architecture(root: Path, *, status: str = "draft") -> Path:
    fm = _base_universal(
        type_="architecture",
        status=status,
        owner="claude-opus-4-7/architecture-write",
        title="App Architecture",
    )
    return _write(root, "docs/architecture/architecture.md", _build_doc(fm))


def _make_cr(root: Path, *, status: str = "draft") -> Path:
    # CR's affected_doc is required by Class 5 to point at an existing file.
    target_fm = _base_universal(
        type_="srs",
        status="approved",
        owner="claude-opus-4-7/srs-write",
        title="App v0.2 SRS",
    )
    target_fm.update(
        {"release": "0.2", "is_multi_module": False, "architecture_change": False}
    )
    target_path = root / "docs/release0.2/srs/srs.md"
    if not target_path.exists():
        _write(root, "docs/release0.2/srs/srs.md", _build_doc(target_fm))

    fm = _base_universal(
        type_="cr",
        status=status,
        owner="claude-opus-4-7/srs-write",
        title="CR-001 Add 2FA",
    )
    fm.update(
        {
            "cr_id": "CR-001",
            "target_release": "0.2",
            "affected_doc": "docs/release0.2/srs/srs.md",
        }
    )
    return _write(root, "docs/cr/CR-001.md", _build_doc(fm))


def _make_development_plan(root: Path, *, status: str = "draft") -> Path:
    """Incremental, non-gated."""

    fm = _base_universal(
        type_="development-plan",
        status=status,
        owner="claude-opus-4-7/development-write",
        title="App v0.1 Development Plan",
    )
    fm.update({"release": "0.1"})
    return _write(root, "docs/release0.1/development/plan.md", _build_doc(fm))


def _make_acceptance_plan(root: Path, *, status: str = "draft") -> Path:
    """Incremental, non-gated. Requires SRS to satisfy Class 5 related_srs."""

    srs_path = root / "docs/release0.1/srs/srs.md"
    if not srs_path.exists():
        _make_srs(root)
    fm = _base_universal(
        type_="acceptance-plan",
        status=status,
        owner="claude-opus-4-7/srs-write",
        title="App v0.1 Acceptance Plan",
    )
    fm.update({"release": "0.1", "related_srs": "docs/release0.1/srs/srs.md"})
    return _write(root, "docs/release0.1/srs/acceptance_plan.md", _build_doc(fm))


def _make_test_report(root: Path, *, status: str = "draft") -> Path:
    """Snapshot, non-gated; no Pending/Change Log sections."""

    fm = _base_universal(
        type_="test-report",
        status=status,
        owner="claude-opus-4-7/testing-write",
        title="App v0.1 Test Report",
    )
    fm.update(
        {
            "release": "0.1",
            "verification_status": "pass",
            "total_test_cases": 5,
            "passed": 5,
            "failed": 0,
        }
    )
    return _write(
        root,
        "docs/release0.1/testing/report.md",
        _build_doc(fm, pending=None, change_log=None),
    )


_FIXED_NOW = "2026-05-20T14:00:00Z"


# ---------- base TestCase ----------


class _BaseTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _read(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def _frontmatter(self, path: Path) -> dict:
        return parse_frontmatter(self._read(path)).frontmatter


# ---------- 1. EventMappingTests ----------


class EventMappingTests(_BaseTest):
    """4 events × incremental + snapshot."""

    def test_write_complete_draft_to_in_review_incremental(self):
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        [item] = plan
        self.assertEqual(item.op, "mutate")
        self.assertEqual(item.current_status, "draft")
        self.assertEqual(item.target_status, "in-review")
        self.assertTrue(item.is_incremental)
        result = status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(len(result.mutated), 1)
        self.assertEqual(result.no_ops, ())
        fm = self._frontmatter(srs)
        self.assertEqual(fm["status"], "in-review")
        self.assertEqual(fm["updated"], _FIXED_NOW)
        body = self._read(srs)
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 in-review", body
        )
        self.assertIn("### 2026-05-20", body)

    def test_write_complete_revising_to_in_review_incremental(self):
        srs = _make_srs(self.root, status="revising")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(srs)["status"], "in-review")

    def test_review_issues_in_review_to_revising_incremental(self):
        srs = _make_srs(self.root, status="in-review")
        plan = status_transition.compute_plan("review-issues", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(srs)["status"], "revising")
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 revising",
            self._read(srs),
        )

    def test_review_passed_in_review_to_review_passed_incremental(self):
        srs = _make_srs(self.root, status="in-review")
        plan = status_transition.compute_plan("review-passed", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(srs)["status"], "review-passed")

    def test_human_confirmed_review_passed_to_approved_for_srs(self):
        srs = _make_srs(self.root, status="review-passed")
        plan = status_transition.compute_plan("human-confirmed", [srs], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(srs)["status"], "approved")
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 approved",
            self._read(srs),
        )

    def test_write_complete_on_snapshot_doc_no_changelog_section(self):
        report = _make_test_report(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [report], self.root)
        [item] = plan
        self.assertEqual(item.op, "mutate")
        self.assertFalse(item.is_incremental)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        fm = self._frontmatter(report)
        self.assertEqual(fm["status"], "in-review")
        self.assertEqual(fm["updated"], _FIXED_NOW)
        text = self._read(report)
        # Snapshot doc must not gain Pending Changes / Change Log sections.
        self.assertNotIn("## Pending Changes", text)
        self.assertNotIn("## Change Log", text)
        self.assertNotIn("[frontmatter]:", text)

    def test_review_issues_on_snapshot_doc(self):
        report = _make_test_report(self.root, status="in-review")
        plan = status_transition.compute_plan("review-issues", [report], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(report)["status"], "revising")

    def test_review_passed_on_snapshot_doc(self):
        report = _make_test_report(self.root, status="in-review")
        plan = status_transition.compute_plan("review-passed", [report], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(report)["status"], "review-passed")


# ---------- 2. GatedRejectionTests ----------


class GatedRejectionTests(_BaseTest):
    def test_human_confirmed_on_prd_allowed(self):
        prd = _make_prd(self.root, status="review-passed")
        plan = status_transition.compute_plan("human-confirmed", [prd], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(prd)["status"], "approved")

    def test_human_confirmed_on_architecture_allowed(self):
        arch = _make_architecture(self.root, status="review-passed")
        plan = status_transition.compute_plan("human-confirmed", [arch], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(arch)["status"], "approved")

    def test_human_confirmed_on_srs_allowed(self):
        srs = _make_srs(self.root, status="review-passed")
        plan = status_transition.compute_plan("human-confirmed", [srs], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(srs)["status"], "approved")

    def test_human_confirmed_on_cr_allowed(self):
        cr = _make_cr(self.root, status="review-passed")
        plan = status_transition.compute_plan("human-confirmed", [cr], self.root)
        self.assertEqual(plan[0].op, "mutate")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._frontmatter(cr)["status"], "approved")

    def test_human_confirmed_on_development_plan_rejected(self):
        plan_path = _make_development_plan(self.root, status="review-passed")
        before = self._read(plan_path)
        plan = status_transition.compute_plan("human-confirmed", [plan_path], self.root)
        [item] = plan
        self.assertEqual(item.op, "reject")
        joined = "; ".join(item.errors)
        self.assertIn("only valid for", joined)
        self.assertIn("development-plan", joined)
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        # File unchanged byte-for-byte.
        self.assertEqual(self._read(plan_path), before)

    def test_human_confirmed_on_test_report_rejected(self):
        report = _make_test_report(self.root, status="review-passed")
        before = self._read(report)
        plan = status_transition.compute_plan("human-confirmed", [report], self.root)
        self.assertEqual(plan[0].op, "reject")
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._read(report), before)


# ---------- 3. IdempotencyTests ----------


class IdempotencyTests(_BaseTest):
    def test_already_at_target_no_op_for_incremental_unchanged_bytes(self):
        srs = _make_srs(self.root, status="in-review")
        before = self._read(srs)
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        [item] = plan
        self.assertEqual(item.op, "no-op")
        result = status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(result.mutated, ())
        self.assertEqual(len(result.no_ops), 1)
        # Byte-for-byte unchanged: no Pending entry appended, no updated bump.
        self.assertEqual(self._read(srs), before)

    def test_already_at_target_no_op_for_snapshot_unchanged_bytes(self):
        report = _make_test_report(self.root, status="in-review")
        before = self._read(report)
        plan = status_transition.compute_plan("write-complete", [report], self.root)
        self.assertEqual(plan[0].op, "no-op")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._read(report), before)

    def test_already_at_approved_for_gated_doc_no_op(self):
        prd = _make_prd(self.root, status="approved")
        before = self._read(prd)
        plan = status_transition.compute_plan("human-confirmed", [prd], self.root)
        self.assertEqual(plan[0].op, "no-op")
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._read(prd), before)

    def test_no_op_alongside_mutate_partial_writes(self):
        # SRS already at target → no-op. Test report draft → mutate.
        srs = _make_srs(self.root, status="in-review")
        report = _make_test_report(self.root, status="draft")
        srs_before = self._read(srs)
        plan = status_transition.compute_plan(
            "write-complete", [srs, report], self.root
        )
        ops = [item.op for item in plan]
        self.assertEqual(ops, ["no-op", "mutate"])
        result = status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(len(result.mutated), 1)
        self.assertEqual(len(result.no_ops), 1)
        # SRS untouched, test report mutated.
        self.assertEqual(self._read(srs), srs_before)
        self.assertEqual(self._frontmatter(report)["status"], "in-review")


# ---------- 4. MultiDocTransactionTests ----------


class MultiDocTransactionTests(_BaseTest):
    def test_two_doc_happy_path_both_mutated(self):
        srs = _make_srs(self.root, status="draft")
        ap = _make_acceptance_plan(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs, ap], self.root)
        self.assertTrue(all(item.op == "mutate" for item in plan))
        result = status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(len(result.mutated), 2)
        self.assertEqual(self._frontmatter(srs)["status"], "in-review")
        self.assertEqual(self._frontmatter(ap)["status"], "in-review")

    def test_one_doc_invalid_status_blocks_all_writes(self):
        srs = _make_srs(self.root, status="draft")
        # Acceptance plan at review-passed → not in allowed_old for write-complete.
        ap = _make_acceptance_plan(self.root, status="review-passed")
        srs_before = self._read(srs)
        ap_before = self._read(ap)
        plan = status_transition.compute_plan("write-complete", [srs, ap], self.root)
        ops = [item.op for item in plan]
        self.assertIn("reject", ops)
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        # No doc mutated.
        self.assertEqual(self._read(srs), srs_before)
        self.assertEqual(self._read(ap), ap_before)

    def test_post_write_validate_failure_rolls_back_all_docs(self):
        srs = _make_srs(self.root, status="draft")
        ap = _make_acceptance_plan(self.root, status="draft")
        srs_before = self._read(srs)
        ap_before = self._read(ap)
        plan = status_transition.compute_plan("write-complete", [srs, ap], self.root)
        self.assertTrue(all(item.op == "mutate" for item in plan))

        with patch.object(
            status_transition.validate_module,
            "validate_file",
            return_value=["forced post-write failure"],
        ):
            with self.assertRaises(status_transition.StatusTransitionError):
                status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)

        # Both docs rolled back to pre-transition bytes.
        self.assertEqual(self._read(srs), srs_before)
        self.assertEqual(self._read(ap), ap_before)

    def test_compute_plan_unknown_event_raises(self):
        srs = _make_srs(self.root, status="draft")
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.compute_plan("not-an-event", [srs], self.root)

    def test_missing_file_rejected_no_writes(self):
        plan = status_transition.compute_plan(
            "write-complete",
            [self.root / "docs/release0.1/srs/srs.md"],
            self.root,
        )
        self.assertEqual(plan[0].op, "reject")
        self.assertTrue(any("file not found" in e for e in plan[0].errors))
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)


# ---------- 5. PendingEntryFormatTests ----------


class PendingEntryFormatTests(_BaseTest):
    def test_pending_entry_appears_in_change_log(self):
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        text = self._read(srs)
        # Exact spec wording from change-log-format.md §7.1.
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 in-review", text
        )
        # Date heading sorts descending: new (2026-05-20) appears before
        # the existing 2026-05-15 entry.
        idx_new = text.index("### 2026-05-20")
        idx_old = text.index("### 2026-05-15")
        self.assertLess(idx_new, idx_old)
        # Pending Changes section is empty after promote.
        # The old "初始版本" entry should now live under the existing date heading.
        self.assertIn("- 2026-05-15T09:00:00Z [Section 1]: 初始版本", text)

    def test_post_apply_doc_passes_validate_text(self):
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(validate_text(self._read(srs)), [])

    def test_post_apply_doc_passes_validate_file(self):
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        issues = validate_module.validate_file(srs, self.root)
        self.assertEqual(issues, [], issues)

    def test_pending_entry_timestamp_matches_updated(self):
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        fm = self._frontmatter(srs)
        self.assertEqual(fm["updated"], _FIXED_NOW)
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 in-review",
            self._read(srs),
        )

    def test_pending_section_with_existing_html_comment_still_validates(self):
        # Pending body carrying only an HTML comment must round-trip through
        # promote_text without raising. After promote, Pending Changes is
        # cleared and the new entry lives in Change Log.
        fm = _base_universal(
            type_="srs",
            status="draft",
            owner="claude-opus-4-7/srs-write",
            title="App v0.1 SRS",
        )
        fm.update(
            {"release": "0.1", "is_multi_module": False, "architecture_change": False}
        )
        text = _build_doc(
            fm,
            pending="<!-- placeholder -->",
            change_log=_DEFAULT_CHANGELOG,
        )
        srs = _write(self.root, "docs/release0.1/srs/srs.md", text)
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        out = self._read(srs)
        self.assertIn(
            f"- {_FIXED_NOW} [frontmatter]: 更新 status 至 in-review", out
        )
        self.assertEqual(validate_text(out), [])


# ---------- 6. CliIntegrationTests ----------


class CliIntegrationTests(_BaseTest):
    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            try:
                code = status_transition.main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def test_no_subcommand_returns_2(self):
        code, _, err = self._run([])
        self.assertEqual(code, 2)
        self.assertIn("status_transition.py", err)

    def test_invalid_event_returns_2(self):
        code, _, err = self._run(
            ["plan", "--event", "no-such-event", "--doc", "x"]
        )
        self.assertEqual(code, 2)
        self.assertIn("invalid choice", err)

    def test_plan_dry_run_does_not_mutate(self):
        srs = _make_srs(self.root, status="draft")
        before = self._read(srs)
        code, out, _ = self._run(
            [
                "--root",
                str(self.root),
                "plan",
                "--event",
                "write-complete",
                "--doc",
                str(srs),
            ]
        )
        self.assertEqual(code, 0)
        self.assertIn("MUTATE", out)
        self.assertIn("draft -> in-review", out)
        self.assertEqual(self._read(srs), before)

    def test_apply_writes_and_returns_zero(self):
        srs = _make_srs(self.root, status="draft")
        code, out, err = self._run(
            [
                "--root",
                str(self.root),
                "apply",
                "--event",
                "write-complete",
                "--doc",
                str(srs),
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mutated", out)
        self.assertEqual(self._frontmatter(srs)["status"], "in-review")

    def test_apply_idempotent_no_op_returns_zero(self):
        srs = _make_srs(self.root, status="in-review")
        before = self._read(srs)
        code, _out, err = self._run(
            [
                "--root",
                str(self.root),
                "apply",
                "--event",
                "write-complete",
                "--doc",
                str(srs),
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(self._read(srs), before)
        self.assertIn("no-op", err)

    def test_plan_returns_one_when_reject(self):
        plan_path = _make_development_plan(self.root, status="review-passed")
        code, _, err = self._run(
            [
                "--root",
                str(self.root),
                "plan",
                "--event",
                "human-confirmed",
                "--doc",
                str(plan_path),
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("REJECT", err)

    def test_apply_returns_one_when_reject_no_mutation(self):
        plan_path = _make_development_plan(self.root, status="review-passed")
        before = self._read(plan_path)
        code, _, err = self._run(
            [
                "--root",
                str(self.root),
                "apply",
                "--event",
                "human-confirmed",
                "--doc",
                str(plan_path),
            ]
        )
        self.assertEqual(code, 1)
        self.assertIn("refusing to mutate", err)
        self.assertEqual(self._read(plan_path), before)

    def test_apply_multi_doc_atomic_via_cli(self):
        srs = _make_srs(self.root, status="draft")
        ap = _make_acceptance_plan(self.root, status="draft")
        code, out, err = self._run(
            [
                "--root",
                str(self.root),
                "apply",
                "--event",
                "write-complete",
                "--doc",
                str(srs),
                "--doc",
                str(ap),
            ]
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mutated", out)
        self.assertEqual(self._frontmatter(srs)["status"], "in-review")
        self.assertEqual(self._frontmatter(ap)["status"], "in-review")


# ---------- 7. Round2RegressionTests (M1 + M2) ----------


def _make_unknown_type_doc(root: Path, *, status: str) -> Path:
    """Doc whose ``type`` is a string but not in DOC_TYPES — used by M1 tests."""

    fm = {
        "title": "Phantom doc",
        "type": "not-a-real-type",
        "status": status,
        "created": "2026-05-15T10:00:00Z",
        "updated": "2026-05-15T10:00:00Z",
        "owner": "claude-opus-4-7/srs-write",
    }
    text = f"---\n{_emit_yaml(fm)}\n---\n# Title\n\nContent.\n"
    return _write(root, "docs/phantom/phantom.md", text)


class Round2RegressionTests(_BaseTest):
    """Regression coverage for Phase 4 round 2 review M1 (unknown type) and
    M2 (stale plan applied after on-disk drift)."""

    # ---------- M1: unknown doc type rejection ----------

    def test_m1_unknown_type_at_target_status_rejected(self):
        # Without the fix, type=not-a-real-type + status=in-review + event=
        # write-complete (target=in-review) would short-circuit as no-op and
        # apply_plan would return success without ever validating the doc.
        doc = _make_unknown_type_doc(self.root, status="in-review")
        before = self._read(doc)
        plan = status_transition.compute_plan("write-complete", [doc], self.root)
        [item] = plan
        self.assertEqual(item.op, "reject")
        joined = "; ".join(item.errors)
        self.assertIn("unknown doc type", joined)
        self.assertIn("not-a-real-type", joined)
        with self.assertRaises(status_transition.StatusTransitionError) as cm:
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertIn("unknown doc type", str(cm.exception))
        # File untouched.
        self.assertEqual(self._read(doc), before)

    def test_m1_unknown_type_in_mutating_status_rejected(self):
        doc = _make_unknown_type_doc(self.root, status="draft")
        before = self._read(doc)
        plan = status_transition.compute_plan("write-complete", [doc], self.root)
        [item] = plan
        self.assertEqual(item.op, "reject")
        joined = "; ".join(item.errors)
        self.assertIn("unknown doc type", joined)
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._read(doc), before)

    def test_m1_unknown_type_blocks_mixed_batch(self):
        # Even when sibling docs in the same batch are valid, an unknown type
        # in one doc causes plan-level reject which blocks all writes.
        srs = _make_srs(self.root, status="draft")
        bad = _make_unknown_type_doc(self.root, status="draft")
        srs_before = self._read(srs)
        bad_before = self._read(bad)
        plan = status_transition.compute_plan(
            "write-complete", [srs, bad], self.root
        )
        ops = [item.op for item in plan]
        self.assertIn("reject", ops)
        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertEqual(self._read(srs), srs_before)
        self.assertEqual(self._read(bad), bad_before)

    # ---------- M2: stale plan rejection ----------

    def test_m2_apply_rejects_stale_status_change_for_mutate(self):
        # Build the plan when SRS is draft, then externally change status to
        # review-passed. The stale plan would otherwise overwrite review-passed
        # back to in-review (an illegal write-complete transition).
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        self.assertEqual(plan[0].op, "mutate")

        # External rewrite: bump status to review-passed.
        external_fm = _base_universal(
            type_="srs",
            status="review-passed",
            owner="claude-opus-4-7/srs-write",
            title="App v0.1 SRS",
        )
        external_fm.update(
            {"release": "0.1", "is_multi_module": False, "architecture_change": False}
        )
        external_text = _build_doc(external_fm)
        srs.write_text(external_text, encoding="utf-8")
        external_bytes = self._read(srs)

        with self.assertRaises(status_transition.StatusTransitionError) as cm:
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        msg = str(cm.exception)
        self.assertIn("stale plan", msg)
        self.assertIn("status changed", msg)
        # Stale apply must not have overwritten the externally-modified file.
        self.assertEqual(self._read(srs), external_bytes)
        self.assertEqual(self._frontmatter(srs)["status"], "review-passed")

    def test_m2_apply_rejects_stale_status_change_for_no_op(self):
        # Plan says no-op (already at in-review). External rewrite to draft
        # should make the no-op plan stale; apply must reject so the caller
        # does not see a false success.
        srs = _make_srs(self.root, status="in-review")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        self.assertEqual(plan[0].op, "no-op")

        external_fm = _base_universal(
            type_="srs",
            status="draft",
            owner="claude-opus-4-7/srs-write",
            title="App v0.1 SRS",
        )
        external_fm.update(
            {"release": "0.1", "is_multi_module": False, "architecture_change": False}
        )
        external_text = _build_doc(external_fm)
        srs.write_text(external_text, encoding="utf-8")
        external_bytes = self._read(srs)

        with self.assertRaises(status_transition.StatusTransitionError) as cm:
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertIn("stale plan", str(cm.exception))
        self.assertEqual(self._read(srs), external_bytes)

    def test_m2_apply_rejects_stale_type_change(self):
        # Compute plan when doc is SRS. External rewrite changes type to
        # development-plan. Even though development-plan is also a valid type,
        # the recorded plan is no longer applicable and must reject.
        srs = _make_srs(self.root, status="draft")
        plan = status_transition.compute_plan("write-complete", [srs], self.root)
        self.assertEqual(plan[0].op, "mutate")
        self.assertEqual(plan[0].doc_type, "srs")

        external_fm = _base_universal(
            type_="development-plan",
            status="draft",
            owner="claude-opus-4-7/development-write",
            title="App v0.1 Dev Plan",
        )
        external_fm.update({"release": "0.1"})
        external_text = _build_doc(external_fm)
        srs.write_text(external_text, encoding="utf-8")
        external_bytes = self._read(srs)

        with self.assertRaises(status_transition.StatusTransitionError) as cm:
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        self.assertIn("stale plan", str(cm.exception))
        self.assertIn("type changed", str(cm.exception))
        self.assertEqual(self._read(srs), external_bytes)

    def test_m2_apply_rejects_stale_in_multi_doc_batch(self):
        # In a multi-doc apply, freshness drift on a single doc must abort the
        # whole batch before any write occurs (preflight gate).
        srs = _make_srs(self.root, status="draft")
        ap = _make_acceptance_plan(self.root, status="draft")
        plan = status_transition.compute_plan(
            "write-complete", [srs, ap], self.root
        )
        self.assertTrue(all(item.op == "mutate" for item in plan))

        # Drift: rewrite SRS as review-passed externally; leave acceptance
        # plan untouched.
        external_fm = _base_universal(
            type_="srs",
            status="review-passed",
            owner="claude-opus-4-7/srs-write",
            title="App v0.1 SRS",
        )
        external_fm.update(
            {"release": "0.1", "is_multi_module": False, "architecture_change": False}
        )
        srs_external = _build_doc(external_fm)
        srs.write_text(srs_external, encoding="utf-8")
        srs_bytes = self._read(srs)
        ap_bytes = self._read(ap)

        with self.assertRaises(status_transition.StatusTransitionError):
            status_transition.apply_plan(plan, self.root, now=_FIXED_NOW)
        # Neither doc was written by the apply step.
        self.assertEqual(self._read(srs), srs_bytes)
        self.assertEqual(self._read(ap), ap_bytes)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
