"""Tests for skills/workflow-protocol/scripts/progress.py update --event."""

from __future__ import annotations

import importlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "skills" / "workflow-protocol" / "scripts"
for _path in (_SCRIPTS_DIR, _REPO_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

progress = importlib.import_module("progress")

from skills._shared.dev_workflow.frontmatter import parse_frontmatter, render_markdown  # noqa: E402
from skills._shared.dev_workflow.progress_history import parse_history_text  # noqa: E402


def _seed(root: Path) -> None:
    out = io.StringIO()
    err = io.StringIO()
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = out, err
    try:
        code = progress.main(
            [
                "--root", str(root),
                "init", "--project", "MyApp",
                "--scenario", "S1",
                "--release", "0.1",
            ]
        )
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
    if code != 0:
        raise RuntimeError(f"seed init failed: {err.getvalue()}")


class _CliRunner(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name).resolve()

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out = io.StringIO()
        err = io.StringIO()
        old_stdout, old_stderr = sys.stdout, sys.stderr
        sys.stdout, sys.stderr = out, err
        try:
            try:
                code = progress.main(argv)
            except SystemExit as exc:
                code = exc.code if isinstance(exc.code, int) else 2
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
        return code, out.getvalue(), err.getvalue()

    def _read_progress_fm(self) -> dict:
        return parse_frontmatter(
            (self.root / "progress.md").read_text(encoding="utf-8")
        ).frontmatter

    def _update(self, event: str) -> tuple[int, str, str]:
        return self._run(
            ["--root", str(self.root), "update", "--event", event]
        )

    def _rewrite_progress(self, mutator) -> None:
        """Mutate progress.md frontmatter (test-only: bypasses lock).

        The helper reads progress.md, applies ``mutator(state)`` to the
        frontmatter dict, and writes it back. Used to set up scenarios
        the public CLI cannot reach in Phase 5.2 (e.g. project_state=
        aborted, current_stage=development).
        """

        path = self.root / "progress.md"
        doc = parse_frontmatter(path.read_text(encoding="utf-8"))
        new_fm = dict(doc.frontmatter)
        mutator(new_fm)
        path.write_text(render_markdown(new_fm, doc.body), encoding="utf-8")


class UpdateEventHappyCycleTests(_CliRunner):
    def test_full_review_cycle_for_gated_stage(self):
        _seed(self.root)

        code, out, err = self._update("write-complete")
        self.assertEqual(code, 0, err)
        self.assertIn("write-complete", out)
        self.assertEqual(self._read_progress_fm()["sub_state"], "in-review")
        self.assertEqual(self._read_progress_fm()["review_iteration"], 0)

        code, out, err = self._update("review-issues")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._read_progress_fm()["sub_state"], "revising")
        self.assertEqual(self._read_progress_fm()["review_iteration"], 1)

        code, out, err = self._update("write-complete")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._read_progress_fm()["sub_state"], "in-review")
        self.assertEqual(self._read_progress_fm()["review_iteration"], 1)

        code, out, err = self._update("review-passed")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._read_progress_fm()["sub_state"], "review-passed")
        self.assertEqual(self._read_progress_fm()["review_iteration"], 0)

        code, out, err = self._update("human-confirmed")
        self.assertEqual(code, 0, err)
        self.assertEqual(self._read_progress_fm()["sub_state"], "approved")
        self.assertEqual(self._read_progress_fm()["review_iteration"], 0)

    def test_history_is_appended_with_each_event(self):
        _seed(self.root)
        self._update("write-complete")
        self._update("review-passed")
        history = parse_history_text(
            (self.root / "progress-history.md").read_text(encoding="utf-8")
        )
        events = [e.event for e in history]
        self.assertEqual(events, ["init", "write-complete", "review-passed"])

    def test_progress_md_updated_field_matches_history_timestamp(self):
        _seed(self.root)
        self._update("write-complete")
        history = parse_history_text(
            (self.root / "progress-history.md").read_text(encoding="utf-8")
        )
        latest_ts = history[-1].timestamp
        self.assertEqual(self._read_progress_fm()["updated"], latest_ts)


class UpdateEventRejectionTests(_CliRunner):
    def test_unknown_event_returns_1(self):
        _seed(self.root)
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("issues-found")  # business wording
        self.assertEqual(code, 1)
        self.assertIn("event must be one of", err)
        # No mutation on rejection.
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )

    def test_illegal_transition_returns_1(self):
        # init leaves sub_state=write; review-passed requires in-review.
        _seed(self.root)
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("review-passed")
        self.assertEqual(code, 1)
        self.assertIn("review-passed", err)
        self.assertIn("in-review", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )

    def test_human_confirmed_on_non_gated_stage_returns_1(self):
        # In real workflow execution, sub_state=review-passed on a
        # non-gated stage is only reachable via Phase 6 --advance. For
        # Phase 5.2 testing we forge the terminal state in a single
        # rewrite. The forward apply_update_event() gated-only check
        # rejects this human-confirmed call before the round 2 M1
        # replay-consistency step ever runs, so we get the expected
        # gated-stage error rather than a replay-divergence error.
        _seed(self.root)
        self._rewrite_progress(
            lambda fm: fm.update(
                {
                    "current_stage": "development",
                    "sub_state": "review-passed",
                }
            )
        )
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("human-confirmed")
        self.assertEqual(code, 1)
        self.assertIn("gated stages", err)
        self.assertIn("development", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )

    def test_iteration_limit_rejected_at_eight(self):
        _seed(self.root)
        # Drive to in-review then review-issues 7 times; the 8th attempt
        # should reject because it would push review_iteration to 8.
        self._update("write-complete")
        for i in range(7):
            code, _, err = self._update("review-issues")
            self.assertEqual(code, 0, err)
            code, _, err = self._update("write-complete")
            self.assertEqual(code, 0, err)
        # Now sub_state=in-review, review_iteration=7. One more
        # review-issues would move to 8 → reject.
        self.assertEqual(self._read_progress_fm()["review_iteration"], 7)
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("review-issues")
        self.assertEqual(code, 1)
        self.assertIn("escalate", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )

    def test_aborted_project_rejects_event(self):
        _seed(self.root)
        self._rewrite_progress(
            lambda fm: fm.update({"project_state": "aborted"})
        )
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("project_state", err)
        self.assertIn("aborted", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )


class UpdateEventArgparseTests(_CliRunner):
    def test_missing_event_returns_2(self):
        _seed(self.root)
        # Mutually-exclusive group with required=True triggers argparse
        # usage error → SystemExit(2).
        code, _, _ = self._run(["--root", str(self.root), "update"])
        self.assertEqual(code, 2)

    def test_update_help_runs(self):
        code, out, _ = self._run(["update", "--help"])
        self.assertEqual(code, 0)
        self.assertIn("--event", out)


class UpdateEventFileGuardTests(_CliRunner):
    def test_missing_progress_returns_1(self):
        # No init; only history exists (or neither).
        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("progress.md", err)

    def test_missing_history_returns_1(self):
        _seed(self.root)
        (self.root / "progress-history.md").unlink()
        before = (self.root / "progress.md").read_text(encoding="utf-8")
        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("progress-history.md", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )

    def test_corrupt_progress_returns_1(self):
        _seed(self.root)
        (self.root / "progress.md").write_text(
            "no frontmatter", encoding="utf-8"
        )
        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("frontmatter", err)


class UpdateEventLockTests(_CliRunner):
    def test_lock_held_blocks_update(self):
        _seed(self.root)
        from skills._shared.dev_workflow.progress_lock import progress_lock

        before = (self.root / "progress.md").read_text(encoding="utf-8")
        with progress_lock(self.root, timeout=1.0):
            code, _, err = self._run(
                [
                    "--root", str(self.root),
                    "--lock-timeout", "0.1",
                    "update", "--event", "write-complete",
                ]
            )
        self.assertEqual(code, 1)
        self.assertIn("held by another process", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"), before
        )


class UpdateEventRecoverRoundtripTests(_CliRunner):
    def test_recover_rebuilds_state_after_full_cycle(self):
        # init → write-complete → review-issues → write-complete →
        # review-passed → human-confirmed; after that, deleting
        # progress.md and running recover must reproduce the same state.
        _seed(self.root)
        self._update("write-complete")
        self._update("review-issues")
        self._update("write-complete")
        self._update("review-passed")
        self._update("human-confirmed")
        before_fm = self._read_progress_fm()

        (self.root / "progress.md").unlink()
        code, _, err = self._run(
            ["--root", str(self.root), "recover", "--confirm"]
        )
        self.assertEqual(code, 0, err)
        after_fm = self._read_progress_fm()
        # Recover rebuilds the state machine result; only `updated` is
        # bumped to recovery time. Everything else must match.
        self.assertEqual(after_fm["sub_state"], before_fm["sub_state"])
        self.assertEqual(after_fm["review_iteration"], before_fm["review_iteration"])
        self.assertEqual(after_fm["current_stage"], before_fm["current_stage"])
        self.assertEqual(after_fm["created"], before_fm["created"])
        self.assertEqual(after_fm["project_name"], before_fm["project_name"])


# ---------- Phase 5.2 round 2: M1 (history parse + replay consistency) ----------


class UpdateEventHistoryParseGuardTests(_CliRunner):
    """M1: cmd_update must reject when the existing progress-history.md is
    not parseable, so a corrupt history cannot grow new entries that a
    later 'recover --confirm' would refuse to replay."""

    def test_corrupt_history_with_bad_header_returns_1(self):
        _seed(self.root)
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        # Replace history with garbage that fails the strict header regex.
        (self.root / "progress-history.md").write_text(
            "## not a real header\n", encoding="utf-8"
        )
        history_before = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )

        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("malformed", err)
        # Both files unchanged byte-for-byte.
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )
        self.assertEqual(
            (self.root / "progress-history.md").read_text(encoding="utf-8"),
            history_before,
        )

    def test_corrupt_history_with_unknown_field_returns_1(self):
        _seed(self.root)
        # Inject an unknown bullet field; parse_history_text rejects it.
        history_path = self.root / "progress-history.md"
        existing = history_path.read_text(encoding="utf-8")
        history_path.write_text(existing + "- bogus: x\n", encoding="utf-8")
        before = history_path.read_text(encoding="utf-8")

        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("malformed", err)
        self.assertEqual(
            history_path.read_text(encoding="utf-8"), before
        )


class UpdateEventReplayConsistencyTests(_CliRunner):
    """M1: cmd_update must replay the composed history end-to-end and
    reject when the forward-path outcome diverges from the canonical
    history replay (e.g. progress.md was edited out-of-band)."""

    def test_tampered_release_field_triggers_replay_mismatch(self):
        # Init writes release='0.1' to progress.md. Forge release='0.2'
        # in progress.md only — history is untouched. The forward path
        # produces outcome.new_state.release='0.2'; replay produces
        # release='0.1' (from clean init replay). Comparison must fail
        # and refuse to write either file.
        _seed(self.root)
        self._rewrite_progress(lambda fm: fm.update({"release": "0.2"}))
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        history_before = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )

        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("replay consistency check failed", err)
        self.assertIn("release", err)
        self.assertIn("recover --confirm", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )
        self.assertEqual(
            (self.root / "progress-history.md").read_text(encoding="utf-8"),
            history_before,
        )

    def test_tampered_project_name_triggers_replay_mismatch(self):
        _seed(self.root)
        self._rewrite_progress(lambda fm: fm.update({"project_name": "Hijacked"}))
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")
        history_before = (self.root / "progress-history.md").read_text(
            encoding="utf-8"
        )
        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("replay consistency check failed", err)
        self.assertIn("project_name", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )
        self.assertEqual(
            (self.root / "progress-history.md").read_text(encoding="utf-8"),
            history_before,
        )

    def test_clean_state_passes_replay_consistency(self):
        # Sanity: the consistency check must not false-positive on a
        # state that has only been mutated through the public CLI.
        _seed(self.root)
        for event in (
            "write-complete",
            "review-issues",
            "write-complete",
            "review-passed",
            "human-confirmed",
        ):
            code, _, err = self._update(event)
            self.assertEqual(code, 0, f"{event}: {err}")


# ---------- Phase 5.2 round 2: M2 (review_iteration > 7 entry check) ----------


class UpdateEventIterationOverLimitTests(_CliRunner):
    """M2: a tampered or migrated progress.md whose review_iteration is
    already over the spec cap (0-7) must not be allowed to apply any
    mutating event. The original review-issues +1 check still covers
    7 -> 8; this entry-time check additionally blocks write-complete /
    review-passed / human-confirmed from preserving or resetting an
    over-limit value."""

    def test_write_complete_with_iter_eight_returns_1(self):
        _seed(self.root)
        self._rewrite_progress(lambda fm: fm.update({"review_iteration": 8}))
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")

        code, _, err = self._update("write-complete")
        self.assertEqual(code, 1)
        self.assertIn("review_iteration", err)
        self.assertIn("8", err)
        self.assertIn("escalate", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )

    def test_review_passed_with_iter_eight_does_not_silently_reset(self):
        _seed(self.root)
        self._rewrite_progress(
            lambda fm: fm.update(
                {"sub_state": "in-review", "review_iteration": 8}
            )
        )
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")

        code, _, err = self._update("review-passed")
        self.assertEqual(code, 1)
        self.assertIn("review_iteration", err)
        self.assertIn("8", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )

    def test_human_confirmed_with_iter_eight_returns_1(self):
        _seed(self.root)
        self._rewrite_progress(
            lambda fm: fm.update(
                {"sub_state": "review-passed", "review_iteration": 8}
            )
        )
        progress_before = (self.root / "progress.md").read_text(encoding="utf-8")

        code, _, err = self._update("human-confirmed")
        self.assertEqual(code, 1)
        self.assertIn("review_iteration", err)
        self.assertIn("8", err)
        self.assertEqual(
            (self.root / "progress.md").read_text(encoding="utf-8"),
            progress_before,
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
