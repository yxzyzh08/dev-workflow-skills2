"""Tests for skills/_shared/dev_workflow/progress_replay.py."""

from __future__ import annotations

import tempfile
import unittest
from unittest.mock import patch

from skills._shared.dev_workflow.progress_history import (
    HistoryEntry,
    parse_history_text,
)
from skills._shared.dev_workflow.progress_replay import (
    READ_ONLY_EVENTS,
    ReplayError,
    TERMINAL_EVENTS,
    replay_history,
    supported_events,
)


def _init_entry(
    *,
    timestamp: str = "2026-05-15T10:00:00Z",
    project: str = "MyApp",
    scenario: str = "S1",
    release: str = "0.1",
    summary_extra: str = "",
) -> HistoryEntry:
    summary = f"project created — project={project}, scenario={scenario}, release={release}"
    if summary_extra:
        summary += f" {summary_extra}"
    return HistoryEntry(
        timestamp=timestamp,
        event="init",
        summary=summary,
        agent="claude-opus-4-7/workflow-init",
        result=None,
        next="prd-write",
        raw="",
    )


class ReplayInitTests(unittest.TestCase):
    def test_empty_history_returns_empty_state(self):
        self.assertEqual(replay_history([]), {})

    def test_init_only_history_yields_initial_state(self):
        state = replay_history([_init_entry()])
        self.assertEqual(state["project_name"], "MyApp")
        self.assertEqual(state["scenario"], "S1")
        self.assertEqual(state["release"], "0.1")
        self.assertEqual(state["project_state"], "active")
        self.assertEqual(state["current_stage"], "prd-inception")
        self.assertEqual(state["sub_state"], "write")
        self.assertEqual(state["review_iteration"], 0)
        self.assertEqual(state["created"], "2026-05-15T10:00:00Z")
        self.assertEqual(state["updated"], "2026-05-15T10:00:00Z")

    def test_init_can_read_fields_from_result(self):
        entry = HistoryEntry(
            timestamp="2026-05-15T10:00:00Z",
            event="init",
            summary="project created",
            agent="a/b",
            result="project=MyApp scenario=S3 release=0.1",
            next=None,
            raw="",
        )
        state = replay_history([entry])
        self.assertEqual(state["scenario"], "S3")

    def test_init_missing_fields_raises(self):
        entry = HistoryEntry(
            timestamp="2026-05-15T10:00:00Z",
            event="init",
            summary="project created",  # no key=value tokens
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        with self.assertRaises(ReplayError) as cm:
            replay_history([entry])
        self.assertIn("missing fields", str(cm.exception))

    def test_init_invalid_scenario_rejected(self):
        with self.assertRaises(ReplayError):
            replay_history([_init_entry(scenario="S9")])

    def test_init_invalid_release_rejected(self):
        with self.assertRaises(ReplayError):
            replay_history([_init_entry(release="0.1.1")])

    def test_init_must_be_first_entry(self):
        first = _init_entry(timestamp="2026-05-15T10:00:00Z")
        second = _init_entry(timestamp="2026-05-16T11:00:00Z")  # second init
        with self.assertRaises(ReplayError) as cm:
            replay_history([first, second])
        self.assertIn("only legal as the first entry", str(cm.exception))


class ReplayUnsupportedEventTests(unittest.TestCase):
    def test_unknown_event_rejected(self):
        # Phase 6.4 closes Phase 6 with 15 supported events. Anything
        # else is either a future-phase entry or a corrupt history. We
        # use a clearly-not-on-roadmap synthetic name so the test stays
        # meaningful even if Phase 7+ adds more events.
        entry = HistoryEntry(
            timestamp="2026-05-15T10:00:00Z",
            event="synthetic-test-event",
            summary="should never be supported",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        with self.assertRaises(ReplayError) as cm:
            replay_history([entry])
        self.assertIn("not supported", str(cm.exception))
        self.assertIn("synthetic-test-event", str(cm.exception))

    def test_supported_events_in_phase_6_4(self):
        # Phase 6.4 closes Phase 6 by adding update-advance on top of
        # Phase 6.3's fourteen handlers. Total = 15.
        self.assertEqual(
            supported_events(),
            {
                "init",
                "write-complete",
                "review-issues",
                "review-passed",
                "human-confirmed",
                "update-task",
                "release-close",
                "release-start",
                "bug-intake",
                "bug-start",
                "bug-close",
                "bug-rework",
                "incident-start",
                "incident-resolve",
                "update-advance",
            },
        )


class ReplayMonotonicityTests(unittest.TestCase):
    def test_timestamp_going_backwards_rejected_with_specific_message(self):
        # Document order is what the replay validator must check (history
        # is append-only). The second entry's timestamp is earlier than the
        # first; the replay must reject with a message that names the
        # backwards-timestamp condition specifically — not the duplicate-
        # init condition (which masked M1 in round 1).
        a = _init_entry(timestamp="2026-05-15T10:00:00Z")
        b = _init_entry(timestamp="2026-05-15T09:59:59Z")
        with self.assertRaises(ReplayError) as cm:
            replay_history([a, b])
        self.assertIn("timestamp goes backwards", str(cm.exception))
        # Specifically: the previous-timestamp pin is included for diagnosis.
        self.assertIn("2026-05-15T10:00:00Z", str(cm.exception))

    def test_timestamp_check_fires_before_handler_dispatch(self):
        # Even when the second entry's event is unsupported by the
        # current handler set, the backwards-timestamp check must fire
        # first. This nails the ordering: monotonicity validation runs
        # before handler-based validation, so a corrupted append-order
        # is rejected regardless of what the offending entry's event
        # happens to be.
        a = _init_entry(timestamp="2026-05-15T10:00:00Z")
        b = HistoryEntry(
            timestamp="2026-05-15T09:59:59Z",
            event="synthetic-test-event",  # Definitively unsupported.
            summary="should never be supported",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        with self.assertRaises(ReplayError) as cm:
            replay_history([a, b])
        self.assertIn("timestamp goes backwards", str(cm.exception))
        self.assertNotIn("not supported", str(cm.exception))

    def test_replay_uses_document_order_not_sorted_order(self):
        # If replay still pre-sorted the input ascending, a [later, earlier]
        # input would be reordered and the second pass would never trip the
        # backwards-timestamp rule. Asserting the specific monotonicity
        # error confirms document-order replay.
        a = _init_entry(timestamp="2026-05-16T10:00:00Z")
        b = _init_entry(timestamp="2026-05-15T10:00:00Z")  # earlier
        with self.assertRaises(ReplayError) as cm:
            replay_history([a, b])
        self.assertIn("timestamp goes backwards", str(cm.exception))


class ReplayTerminalSemanticsTests(unittest.TestCase):
    def test_terminal_set_is_incident_resolve_in_phase_6_3(self):
        # Phase 6.3 activates the terminal-event framework for the
        # first time. ``incident-resolve`` is event-name-keyed terminal,
        # but the dispatch loop is action-aware (Option B): only abort
        # / reconstruct flip seen_terminal. ``--action continue`` is
        # non-terminal and may be followed by further legal mutations.
        self.assertEqual(TERMINAL_EVENTS, {"incident-resolve"})
        # READ_ONLY_EVENTS stays empty in 6.3 — replay handlers all
        # mutate state, and recover does not append history.
        self.assertEqual(READ_ONLY_EVENTS, set())

    def test_terminal_incident_actions_are_abort_and_reconstruct(self):
        # Phase 6.3 exposes the policy enum so callers / tests can
        # introspect the action-aware terminal gate without grepping.
        from skills._shared.dev_workflow.progress_replay import (
            TERMINAL_INCIDENT_ACTIONS,
        )
        self.assertEqual(
            TERMINAL_INCIDENT_ACTIONS, frozenset({"abort", "reconstruct"}),
        )


class ReplayParseRoundTripTests(unittest.TestCase):
    def test_replay_after_parse_history_text(self):
        text = (
            "# Project History\n\n"
            "## 2026-05-15T10:00:00Z — init — project created — "
            "project=MyApp, scenario=S1, release=0.1\n"
            "- agent: claude-opus-4-7/workflow-init\n"
            "- next: prd-write\n"
        )
        state = replay_history(parse_history_text(text))
        self.assertEqual(state["project_name"], "MyApp")


def _update_event_entry(
    *,
    timestamp: str,
    event: str,
    summary: str = "x",
    agent: str = "claude-opus-4-7/workflow-update",
) -> HistoryEntry:
    return HistoryEntry(
        timestamp=timestamp,
        event=event,
        summary=summary,
        agent=agent,
        result=None,
        next=None,
        raw="",
    )


# ---------- Phase 5.2: update --event replay handlers ----------


class ReplayUpdateEventTests(unittest.TestCase):
    """Verify the four update --event handlers integrate cleanly with replay."""

    def _init(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-05-15T10:00:00Z")

    def test_replay_full_review_cycle(self):
        # init -> write-complete -> review-passed -> human-confirmed
        # leaves prd-inception in the gated 'approved' sub_state.
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:00:00Z",
                event="write-complete",
                summary="sub_state write -> in-review",
            ),
            _update_event_entry(
                timestamp="2026-05-15T12:00:00Z",
                event="review-passed",
                summary="sub_state in-review -> review-passed",
            ),
            _update_event_entry(
                timestamp="2026-05-15T13:00:00Z",
                event="human-confirmed",
                summary="sub_state review-passed -> approved",
            ),
        ]
        state = replay_history(entries)
        self.assertEqual(state["sub_state"], "approved")
        self.assertEqual(state["review_iteration"], 0)
        self.assertEqual(state["current_stage"], "prd-inception")
        self.assertEqual(state["updated"], "2026-05-15T13:00:00Z")

    def test_replay_review_issues_accumulates_iteration(self):
        # init -> write-complete -> review-issues -> write-complete -> review-issues
        # iteration goes 0 -> 0 -> 1 -> 1 -> 2.
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:00:00Z",
                event="write-complete",
                summary="sub_state write -> in-review",
            ),
            _update_event_entry(
                timestamp="2026-05-15T12:00:00Z",
                event="review-issues",
                summary="sub_state in-review -> revising",
            ),
            _update_event_entry(
                timestamp="2026-05-15T13:00:00Z",
                event="write-complete",
                summary="sub_state revising -> in-review",
            ),
            _update_event_entry(
                timestamp="2026-05-15T14:00:00Z",
                event="review-issues",
                summary="sub_state in-review -> revising",
            ),
        ]
        state = replay_history(entries)
        self.assertEqual(state["sub_state"], "revising")
        self.assertEqual(state["review_iteration"], 2)

    def test_replay_review_passed_resets_iteration_to_zero(self):
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:00:00Z",
                event="write-complete",
                summary="x",
            ),
            _update_event_entry(
                timestamp="2026-05-15T12:00:00Z",
                event="review-issues",
                summary="x",
            ),
            _update_event_entry(
                timestamp="2026-05-15T13:00:00Z",
                event="write-complete",
                summary="x",
            ),
            _update_event_entry(
                timestamp="2026-05-15T14:00:00Z",
                event="review-passed",
                summary="x",
            ),
        ]
        state = replay_history(entries)
        self.assertEqual(state["sub_state"], "review-passed")
        self.assertEqual(state["review_iteration"], 0)

    def test_replay_rejects_illegal_transition(self):
        # write-complete is illegal from sub_state=write's preceding state
        # only when sub_state is wrong; here we drive the engine through an
        # illegal sequence: init -> review-passed (illegal: sub_state=write).
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:00:00Z",
                event="review-passed",
                summary="x",
            ),
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        msg = str(cm.exception)
        self.assertIn("review-passed", msg)
        self.assertIn("in-review", msg)

    def test_replay_rejects_human_confirmed_on_non_gated_stage(self):
        # We can only reach a non-gated current_stage in Phase 5.2 by
        # forging the state, but we can still drive a small forced sequence
        # by manually constructing a state through replay handlers — the
        # only legal way to be at sub_state=review-passed without being on
        # a gated stage is impossible until --advance lands. So instead we
        # rely on the apply_update_event tests to cover the non-gated case
        # and document here that, in Phase 5.2 history alone, every legal
        # human-confirmed entry is on prd-inception (gated).
        # This test asserts the gated-only constraint holds when we splice
        # an init that would put us on a fictitious non-gated start by
        # forging a current_stage in the replay. Such forgery requires
        # touching state mid-replay, which the public API forbids; the
        # cleanest demonstration is the unit-level test in
        # test_apply_update_event.HumanConfirmedTests.
        # Here we still verify replay surfaces the same ReplayError when
        # human-confirmed is requested on a non-review-passed sub_state.
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:00:00Z",
                event="human-confirmed",
                summary="x",
            ),
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        self.assertIn("human-confirmed", str(cm.exception))
        self.assertIn("review-passed", str(cm.exception))

    def test_replay_uses_entry_timestamp_for_updated_field(self):
        entries = [
            self._init(),
            _update_event_entry(
                timestamp="2026-05-15T11:30:45Z",
                event="write-complete",
                summary="x",
            ),
        ]
        state = replay_history(entries)
        self.assertEqual(state["updated"], "2026-05-15T11:30:45Z")


# ---------- Phase 5.3: update-task replay handler ----------


class ReplayUpdateTaskTests(unittest.TestCase):
    """update-task replay should:
      * parse 'task=Tn status=<state>' tokens from the entry summary,
      * reject summaries that don't match the canonical shape,
      * require a project root (artifact reads),
      * NOT re-evaluate artifact preconditions (Phase 5.3 design call —
        Stage 4 reports mutate across transitions, so historical
        replays use validate_artifacts=False), and
      * apply the same state-machine transition as the forward path.
    """

    def _init(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-05-15T10:00:00Z")

    def _stage_advance(self, *, ts: str = "2026-05-15T10:30:00Z") -> HistoryEntry:
        return HistoryEntry(
            timestamp=ts,
            event="test-stage-advance",
            summary="test-stage-advance current_stage=development sub_state=write",
            agent="test/forge",
            result="forged for test",
            next=None,
            raw="",
        )

    def _update_task_entry(
        self,
        *,
        ts: str,
        task: str,
        status: str,
        suffix: str = "",
    ) -> HistoryEntry:
        return HistoryEntry(
            timestamp=ts,
            event="update-task",
            summary=f"task={task} status={status}{suffix}",
            agent="claude-opus-4-7/development-write",
            result=f"task={task} from None" if not suffix else None,
            next="next",
            raw="",
        )

    def test_supported_events_include_update_task(self):
        self.assertIn("update-task", supported_events())

    def test_replay_update_task_requires_root(self):
        entries = [
            self._init(),
        ]
        # Without a stage-advance handler installed, the test fixture
        # cannot reach development; we still verify that update-task
        # rejection without root happens before state-machine checks.
        bare_update_task = self._update_task_entry(
            ts="2026-05-15T10:01:00Z", task="T1", status="planning-done",
        )
        with self.assertRaises(ReplayError) as cm:
            replay_history([self._init(), bare_update_task])
        # Either "requires a project root" or the state-machine error
        # (current_stage prd-inception). The handler raises the root
        # error first when root is None.
        self.assertIn("project root", str(cm.exception))

    def test_replay_update_task_unparseable_summary_rejected(self):
        bad = HistoryEntry(
            timestamp="2026-05-15T10:01:00Z",
            event="update-task",
            summary="totally garbled summary no kv pairs",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ReplayError) as cm:
                replay_history([self._init(), bad], root=tmp)
            self.assertIn("cannot parse", str(cm.exception))
            self.assertIn("update-task", str(cm.exception))

    def test_replay_update_task_skips_artifact_validation(self):
        # The replay handler intentionally passes validate_artifacts=False,
        # so even a brand-new tempdir with NO artifact files at all should
        # be sufficient for replay to succeed. We need the test
        # stage-advance handler to bring state to development first.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)

        def _stage_advance_handler(state, entry, root):
            new_state = dict(state)
            new_state["current_stage"] = "development"
            new_state["sub_state"] = "write"
            new_state["review_iteration"] = 0
            new_state["development_state"] = {"task_states": {}}
            new_state["updated"] = entry.timestamp
            return new_state

        handlers["test-stage-advance"] = _stage_advance_handler

        from unittest.mock import patch

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                state = replay_history(
                    [
                        self._init(),
                        self._stage_advance(),
                        self._update_task_entry(
                            ts="2026-05-15T11:00:00Z",
                            task="T1",
                            status="planning-done",
                        ),
                        self._update_task_entry(
                            ts="2026-05-15T11:01:00Z",
                            task="T1",
                            status="test-writing",
                        ),
                    ],
                    root=tmp,
                )
            # No artifact files exist under tmp, but replay still succeeded.
            self.assertEqual(
                state["development_state"]["task_states"], {"T1": "test-writing"}
            )
            self.assertEqual(state["updated"], "2026-05-15T11:01:00Z")

    def test_replay_update_task_still_validates_state_machine(self):
        # Even with validate_artifacts=False, the state-machine guard
        # rejects illegal transitions like None -> test-writing.
        from skills._shared.dev_workflow import progress_replay as pr
        from unittest.mock import patch

        handlers = dict(pr._HANDLERS)

        def _stage_advance_handler(state, entry, root):
            new_state = dict(state)
            new_state["current_stage"] = "development"
            new_state["sub_state"] = "write"
            new_state["review_iteration"] = 0
            new_state["development_state"] = {"task_states": {}}
            new_state["updated"] = entry.timestamp
            return new_state

        handlers["test-stage-advance"] = _stage_advance_handler

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                with self.assertRaises(ReplayError) as cm:
                    replay_history(
                        [
                            self._init(),
                            self._stage_advance(),
                            self._update_task_entry(
                                ts="2026-05-15T11:00:00Z",
                                task="T1",
                                status="test-writing",  # illegal first-time
                            ),
                        ],
                        root=tmp,
                    )
                self.assertIn("not a", str(cm.exception))
                self.assertIn("legal normal transition", str(cm.exception))

    def test_replay_update_task_idempotent_summary_handled(self):
        # Replay must accept summaries with the (idempotent retry) suffix.
        from skills._shared.dev_workflow import progress_replay as pr
        from unittest.mock import patch

        handlers = dict(pr._HANDLERS)

        def _stage_advance_handler(state, entry, root):
            new_state = dict(state)
            new_state["current_stage"] = "development"
            new_state["sub_state"] = "write"
            new_state["review_iteration"] = 0
            new_state["development_state"] = {"task_states": {}}
            new_state["updated"] = entry.timestamp
            return new_state

        handlers["test-stage-advance"] = _stage_advance_handler

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                state = replay_history(
                    [
                        self._init(),
                        self._stage_advance(),
                        self._update_task_entry(
                            ts="2026-05-15T11:00:00Z",
                            task="T1",
                            status="planning-done",
                        ),
                        self._update_task_entry(
                            ts="2026-05-15T11:01:00Z",
                            task="T1",
                            status="planning-done",
                            suffix=" (idempotent retry)",
                        ),
                    ],
                    root=tmp,
                )
            self.assertEqual(
                state["development_state"]["task_states"], {"T1": "planning-done"}
            )


# ---------- Phase 5.4: release lifecycle + bug-intake replay ----------


def _stage_advance_to_close_handler(state, entry, root):
    """Forge replay-side state to project-retrospective / closed so that
    release-start replay can run on top. Same shape as the CLI test
    fixture but isolated here for the unit-only replay tests."""

    new_state = dict(state)
    tokens = {}
    for token in entry.summary.split():
        if "=" in token:
            k, _, v = token.partition("=")
            tokens[k] = v
    if "current_stage" in tokens:
        new_state["current_stage"] = tokens["current_stage"]
    if "sub_state" in tokens:
        new_state["sub_state"] = tokens["sub_state"]
    if "release_state" in tokens:
        new_state["release_state"] = tokens["release_state"]
    if "release_close_reason" in tokens:
        v = tokens["release_close_reason"]
        new_state["release_close_reason"] = None if v == "null" else v
    if "previous_releases" in tokens:
        v = tokens["previous_releases"]
        new_state["previous_releases"] = [] if v == "" else v.split(":")
    new_state["updated"] = entry.timestamp
    return new_state


class ReplayReleaseLifecycleTests(unittest.TestCase):
    """Phase 5.4: replay handlers for release-close / release-start /
    bug-intake. Replay does NOT touch BUG files — those mutations were
    forward-only at write time."""

    def _init_entry(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-05-15T10:00:00Z")

    def _ts(self, hours: int) -> str:
        return f"2026-09-15T{hours:02d}:00:00Z"

    def test_release_close_replay(self):
        # init → S1 prd-inception/write. Forge to project-retrospective /
        # review-passed. Replay release-close: state moves to closed.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary="test-stage-advance current_stage=project-retrospective sub_state=review-passed",
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="release-close",
                    summary="release 0.1 closed",
                    agent="claude-opus-4-7/workflow-release",
                    result="previous_releases=['0.1']",
                    next="release-start or bug-intake",
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(state["release_state"], "closed")
            self.assertEqual(
                state["release_close_reason"], "stage-7-completed"
            )
            self.assertEqual(state["previous_releases"], ["0.1"])

    def test_release_start_replay_extracts_version_and_scenario(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="release-start",
                    summary=(
                        "new release 0.2 started, scenario=S2-1, "
                        "consumed 0 unresolved bugs"
                    ),
                    agent="claude-opus-4-7/workflow-release",
                    result="version=0.2 scenario_subtype=S2-1 consumed=0",
                    next="prd-inception-write (Full Mode)",
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(state["release"], "0.2")
            self.assertEqual(state["release_state"], "active")
            self.assertEqual(state["scenario"], "S2")
            self.assertEqual(state["scenario_subtype"], "S2-1")
            self.assertEqual(state["current_stage"], "prd-inception")
            self.assertEqual(state["sub_state"], "write")
            self.assertEqual(state["unresolved_bugs"], [])

    def test_release_start_replay_missing_tokens_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="release-start",
                    summary="new release started without tokens",  # missing version + scenario
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("missing", str(cm.exception))
            self.assertIn("version", str(cm.exception))

    def test_bug_intake_replay(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="bug-intake",
                    summary="bug=docs/bug/BUG-001.md registered (post-close)",
                    agent="claude-opus-4-7/bug-intake",
                    result="unresolved_bugs count = 1",
                    next="wait for next release-start",
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(
                state["unresolved_bugs"], ["docs/bug/BUG-001.md"]
            )

    def test_bug_intake_replay_rejects_absolute_path(self):
        # Phase 5.4 round 2 review M1: replay must enforce the same
        # path-shape policy as the forward CLI so a corrupted
        # progress-history.md cannot smuggle an outside-root BUG path
        # into unresolved_bugs.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="bug-intake",
                    summary="bug=/etc/passwd registered (post-close)",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("absolute", str(cm.exception))

    def test_bug_intake_replay_rejects_traversal(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="bug-intake",
                    summary="bug=../etc/BUG-001.md registered (post-close)",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("'.' or '..'", str(cm.exception))

    def test_bug_intake_replay_missing_bug_token_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(8),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=project-retrospective "
                        "sub_state=review-passed release_state=closed "
                        "release_close_reason=stage-7-completed previous_releases=0.1"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(9),
                    event="bug-intake",
                    summary="registered some bug",  # no bug=path token
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("bug=", str(cm.exception))

    def test_release_start_replay_does_not_touch_bug_files(self):
        # Pass an empty tempdir as root; if replay tried to read BUG files,
        # it would fail. But Phase 5.4 design is forward-only for BUG
        # mutation, so replay should succeed without artifact reads.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_close_handler

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                entries = [
                    self._init_entry(),
                    HistoryEntry(
                        timestamp=self._ts(8),
                        event="test-stage-advance",
                        summary=(
                            "test-stage-advance current_stage=project-retrospective "
                            "sub_state=review-passed release_state=closed "
                            "release_close_reason=stage-7-completed previous_releases=0.1"
                        ),
                        agent="test/forge",
                        result=None,
                        next=None,
                        raw="",
                    ),
                    HistoryEntry(
                        timestamp=self._ts(8) + ".forge",  # bogus, but unused
                        event="bug-intake",
                        summary="bug=docs/bug/BUG-001.md registered (post-close)",
                        agent="a/b",
                        result=None,
                        next=None,
                        raw="",
                    ),
                ]
                # Replace bogus timestamp with valid one to avoid format error.
                entries[2] = HistoryEntry(
                    timestamp=self._ts(9),
                    event="bug-intake",
                    summary="bug=docs/bug/BUG-001.md registered (post-close)",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                )
                entries.append(
                    HistoryEntry(
                        timestamp=self._ts(10),
                        event="release-start",
                        summary=(
                            "new release 0.2 started, scenario=S2-1, "
                            "consumed 1 unresolved bugs"
                        ),
                        agent="a/b",
                        result="version=0.2 scenario_subtype=S2-1 consumed=1",
                        next="prd-inception-write",
                        raw="",
                    )
                )
                # No BUG file under tmp; replay still must succeed.
                state = replay_history(entries, root=tmp)
                self.assertEqual(state["release"], "0.2")
                self.assertEqual(state["unresolved_bugs"], [])


# ---------- Phase 6.1: bug-start / bug-close replay ----------


def _stage_advance_to_testing_review_passed(state, entry, root):
    """Synthetic handler for the test-stage-advance event used in
    Phase 6.1 replay tests. Mirrors the helper in
    test_progress_bug_flow.py but isolated here for the unit replay
    tests so we don't cross-import."""

    new_state = dict(state)
    tokens = {}
    for token in entry.summary.split():
        if "=" in token:
            k, _, v = token.partition("=")
            tokens[k] = v
    if "current_stage" in tokens:
        new_state["current_stage"] = tokens["current_stage"]
    if "sub_state" in tokens:
        new_state["sub_state"] = tokens["sub_state"]
    if "task_states" in tokens:
        kv: dict[str, str] = {}
        for piece in tokens["task_states"].split(";"):
            if not piece:
                continue
            tid, _, status = piece.partition(":")
            kv[tid] = status
        new_state["development_state"] = {"task_states": kv}
    new_state["updated"] = entry.timestamp
    return new_state


class ReplayBugFlowTests(unittest.TestCase):
    """Phase 6.1: bug-start + bug-close replay handlers must reproduce
    the exact same state-machine mutation the forward CLI applied,
    including Gap-4 dev rollback decisions encoded in the summary
    rollback= token."""

    def _init_entry(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-09-01T10:00:00Z")

    def _ts(self, hours: int) -> str:
        return f"2026-09-01T{hours:02d}:00:00Z"

    def test_bug_start_replay_routes_by_root_cause(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="bug-start",
                    summary=(
                        "bug=docs/bug/BUG-001.md root_cause=architecture "
                        "Bug Flow entered"
                    ),
                    agent="claude-opus-4-7/bug-triage",
                    result="current_stage=architecture-design",
                    next="architecture-design-write Change Mode",
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(state["current_stage"], "architecture-design")
            self.assertEqual(state["sub_state"], "write")
            self.assertEqual(
                state["bug_flow"],
                {
                    "active": True,
                    "bug_report_path": "docs/bug/BUG-001.md",
                    "root_cause": "architecture",
                },
            )

    def test_bug_start_replay_with_rollback_token(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed task_states=T1:verified;T3:code-review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="bug-start",
                    summary=(
                        "bug=docs/bug/BUG-002.md root_cause=development "
                        "Bug Flow entered "
                        "rollback=T1:verified->code-revising;T3:code-review-passed->code-revising"
                    ),
                    agent="claude-opus-4-7/bug-triage",
                    result="rollback applied",
                    next="development-write Change Mode",
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(
                state["development_state"]["task_states"],
                {"T1": "code-revising", "T3": "code-revising"},
            )

    def test_bug_start_replay_missing_tokens_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="bug-start",
                    summary="active Bug Flow entered without tokens",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("missing", str(cm.exception))

    def test_bug_start_replay_malformed_rollback_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed task_states=T1:verified"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="bug-start",
                    summary=(
                        "bug=docs/bug/BUG-003.md root_cause=development "
                        "rollback=garbage-no-arrow"
                    ),
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("rollback", str(cm.exception))

    def test_bug_close_replay(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="bug-start",
                    summary=(
                        "bug=docs/bug/BUG-001.md root_cause=srs Bug Flow entered"
                    ),
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
                # After fix, advance back to testing/review-passed.
                HistoryEntry(
                    timestamp=self._ts(13),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(14),
                    event="bug-close",
                    summary="Bug Flow exited (retest passed)",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(
                state["bug_flow"],
                {"active": False, "bug_report_path": None, "root_cause": None},
            )
            self.assertEqual(state["current_stage"], "testing")

    def test_bug_start_replay_does_not_read_BUG_file(self):
        # Pass an empty tempdir as root; bug-start replay reads only
        # history tokens, so missing BUG file on disk must NOT fail
        # replay.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                entries = [
                    self._init_entry(),
                    HistoryEntry(
                        timestamp=self._ts(11),
                        event="test-stage-advance",
                        summary=(
                            "test-stage-advance current_stage=testing "
                            "sub_state=review-passed"
                        ),
                        agent="test/forge",
                        result=None,
                        next=None,
                        raw="",
                    ),
                    HistoryEntry(
                        timestamp=self._ts(12),
                        event="bug-start",
                        summary=(
                            "bug=docs/bug/BUG-007.md root_cause=srs "
                            "Bug Flow entered"
                        ),
                        agent="a/b",
                        result=None,
                        next=None,
                        raw="",
                    ),
                ]
                # No BUG file under tmp; replay still succeeds.
                state = replay_history(entries, root=tmp)
                self.assertEqual(state["current_stage"], "srs-specification")


# ---------- Phase 6.2: bug-rework replay ----------


class ReplayBugReworkTests(unittest.TestCase):
    """Phase 6.2: bug-rework replay handler must reproduce the active
    re-route mutation the forward CLI applied, including Gap-4 dev
    rollback decisions encoded in the summary rollback= token. Replay
    relies entirely on the history canonical tokens — neither the BUG
    file nor the test-report needs to exist on disk."""

    def _init_entry(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-09-15T10:00:00Z")

    def _ts(self, hours: int) -> str:
        return f"2026-09-15T{hours:02d}:00:00Z"

    def _bug_start_then_advance(
        self,
        *,
        bug_path: str,
        root_cause: str,
        bug_start_rollback: str = "",
        task_states_token: str = "",
    ) -> list[HistoryEntry]:
        """Build init + advance + bug-start + advance-back entries
        common to every bug-rework replay test."""

        # The forward path: init → forge to testing/review-passed
        # (with optional task_states) → bug-start → forge back to
        # testing/review-passed (simulating retest run).
        advance_summary = (
            "test-stage-advance current_stage=testing "
            "sub_state=review-passed"
        )
        if task_states_token:
            advance_summary += f" task_states={task_states_token}"
        rollback_token_full = (
            f" rollback={bug_start_rollback}" if bug_start_rollback else ""
        )
        return [
            self._init_entry(),
            HistoryEntry(
                timestamp=self._ts(11),
                event="test-stage-advance",
                summary=advance_summary,
                agent="test/forge",
                result=None,
                next=None,
                raw="",
            ),
            HistoryEntry(
                timestamp=self._ts(12),
                event="bug-start",
                summary=(
                    f"bug={bug_path} root_cause={root_cause} "
                    "Bug Flow entered" + rollback_token_full
                ),
                agent="claude-opus-4-7/bug-triage",
                result=None,
                next=None,
                raw="",
            ),
            HistoryEntry(
                timestamp=self._ts(13),
                event="test-stage-advance",
                summary=advance_summary,
                agent="test/forge",
                result=None,
                next=None,
                raw="",
            ),
        ]

    def test_bug_rework_replay_routes_by_root_cause(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = self._bug_start_then_advance(
                bug_path="docs/bug/BUG-101.md", root_cause="architecture",
            )
            entries.append(
                HistoryEntry(
                    timestamp=self._ts(14),
                    event="bug-rework",
                    summary=(
                        "bug=docs/bug/BUG-101.md root_cause=architecture "
                        "Bug Flow rerouted"
                    ),
                    agent="claude-opus-4-7/testing-write",
                    result="current_stage=architecture-design",
                    next="architecture-design-write Change Mode",
                    raw="",
                ),
            )
            state = replay_history(entries)
            self.assertEqual(state["current_stage"], "architecture-design")
            self.assertEqual(state["sub_state"], "write")
            # bug_flow stays active and unchanged across rework.
            self.assertEqual(
                state["bug_flow"],
                {
                    "active": True,
                    "bug_report_path": "docs/bug/BUG-101.md",
                    "root_cause": "architecture",
                },
            )

    def test_bug_rework_replay_with_rollback_token(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = self._bug_start_then_advance(
                bug_path="docs/bug/BUG-102.md",
                root_cause="development",
                # bug-start already rolled T1 to code-revising.
                bug_start_rollback="T1:verified->code-revising",
                task_states_token="T1:verified",
            )
            # Forward forge: bug-start put T1 at code-revising; the
            # synthetic test-stage-advance back to testing leaves T1
            # untouched in our handler. For the bug-rework rollback to
            # be re-applicable we need T1 to be in code-review-passed
            # again (e.g. fix landed). Inject another forge entry to
            # set the task state freshly.
            entries.append(
                HistoryEntry(
                    timestamp=self._ts(14),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=testing "
                        "sub_state=review-passed task_states=T1:code-review-passed"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
            )
            entries.append(
                HistoryEntry(
                    timestamp=self._ts(15),
                    event="bug-rework",
                    summary=(
                        "bug=docs/bug/BUG-102.md root_cause=development "
                        "Bug Flow rerouted "
                        "rollback=T1:code-review-passed->code-revising"
                    ),
                    agent="claude-opus-4-7/testing-write",
                    result=None,
                    next=None,
                    raw="",
                ),
            )
            state = replay_history(entries)
            self.assertEqual(
                state["development_state"]["task_states"],
                {"T1": "code-revising"},
            )

    def test_bug_rework_replay_missing_tokens_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = self._bug_start_then_advance(
                bug_path="docs/bug/BUG-103.md", root_cause="srs",
            )
            entries.append(
                HistoryEntry(
                    timestamp=self._ts(14),
                    event="bug-rework",
                    summary="active Bug Flow rerouted without tokens",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            )
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("missing", str(cm.exception))

    def test_bug_rework_replay_malformed_rollback_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = self._bug_start_then_advance(
                bug_path="docs/bug/BUG-104.md",
                root_cause="development",
                task_states_token="T1:verified",
            )
            entries.append(
                HistoryEntry(
                    timestamp=self._ts(14),
                    event="bug-rework",
                    summary=(
                        "bug=docs/bug/BUG-104.md root_cause=development "
                        "rollback=garbage-no-arrow"
                    ),
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            )
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("rollback", str(cm.exception))

    def test_bug_rework_replay_does_not_read_BUG_or_test_report(self):
        # Pass an empty tempdir as root; bug-rework replay reads only
        # history tokens, so missing BUG file AND missing test-report
        # on disk must NOT fail replay (consistent with bug-start /
        # bug-close / update-task replay design).
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                entries = self._bug_start_then_advance(
                    bug_path="docs/bug/BUG-105.md", root_cause="srs",
                )
                entries.append(
                    HistoryEntry(
                        timestamp=self._ts(14),
                        event="bug-rework",
                        summary=(
                            "bug=docs/bug/BUG-105.md root_cause=srs "
                            "Bug Flow rerouted"
                        ),
                        agent="a/b",
                        result=None,
                        next=None,
                        raw="",
                    ),
                )
                state = replay_history(entries, root=tmp)
                self.assertEqual(state["current_stage"], "srs-specification")
                self.assertEqual(state["bug_flow"]["active"], True)


# ---------- Phase 6.3: incident-start / incident-resolve replay ----------


class ReplayIncidentTests(unittest.TestCase):
    """Phase 6.3: incident-start + incident-resolve replay handlers must
    reproduce the PRD-exception lifecycle entirely from canonical
    history tokens. Replay does NOT read BUG / INCIDENT artifact files;
    the forward CLI is the validate.py double-safety gatekeeper.

    Also exercises the Option B action-aware terminal gate: --action
    abort and --action reconstruct flip seen_terminal; --action continue
    does not."""

    def _init_entry(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-10-01T10:00:00Z")

    def _ts(self, hours: int) -> str:
        return f"2026-10-01T{hours:02d}:00:00Z"

    def _incident_start_entry(
        self,
        *,
        ts_hours: int,
        bug_path: str = "docs/bug/BUG-700.md",
        incident_path: str = "docs/incident/INCIDENT-007.md",
    ) -> HistoryEntry:
        return HistoryEntry(
            timestamp=self._ts(ts_hours),
            event="incident-start",
            summary=(
                f"bug={bug_path} incident={incident_path} "
                "root_cause=prd-exception PRD exception triggered"
            ),
            agent="claude-opus-4-7/bug-triage",
            result=None,
            next=None,
            raw="",
        )

    def _incident_resolve_entry(
        self,
        *,
        ts_hours: int,
        action: str,
        incident_path: str = "docs/incident/INCIDENT-007.md",
    ) -> HistoryEntry:
        return HistoryEntry(
            timestamp=self._ts(ts_hours),
            event="incident-resolve",
            summary=(
                f"action={action} incident={incident_path} Incident resolved"
            ),
            agent="claude-opus-4-7/workflow-evolution",
            result=None,
            next=None,
            raw="",
        )

    def test_incident_start_replay_opens_bug_flow_and_incident_state(self):
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
        ]
        state = replay_history(entries)
        self.assertEqual(state["current_stage"], "workflow-incident-analysis")
        self.assertTrue(state["workflow_incident_active"])
        self.assertEqual(
            state["incident_report_path"], "docs/incident/INCIDENT-007.md",
        )
        self.assertEqual(
            state["bug_flow"],
            {
                "active": True,
                "bug_report_path": "docs/bug/BUG-700.md",
                "root_cause": "prd-exception",
            },
        )

    def test_incident_start_replay_missing_tokens_rejected(self):
        bad_entry = HistoryEntry(
            timestamp=self._ts(11),
            event="incident-start",
            summary="PRD exception triggered (no tokens)",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        with self.assertRaises(ReplayError) as cm:
            replay_history([self._init_entry(), bad_entry])
        self.assertIn("missing", str(cm.exception))

    def test_incident_resolve_continue_is_not_terminal(self):
        # incident-start → incident-resolve continue → another mutating
        # entry must succeed. This is the central Option B test.
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            self._incident_resolve_entry(ts_hours=12, action="continue"),
            # A subsequent legitimate command (e.g. a fictitious
            # write-complete to test that mutation is still allowed).
            HistoryEntry(
                timestamp=self._ts(13),
                event="write-complete",
                summary="sub_state review-passed -> in-review",
                agent="a/b",
                result=None,
                next=None,
                raw="",
            ),
        ]
        # write-complete from sub_state=review-passed is illegal in the
        # standard sub_state machine — but the test target here is
        # *terminal gate*, not sub_state legality. We catch ReplayError
        # only if the error actually mentions "after terminal"; any other
        # error proves the terminal gate didn't fire.
        try:
            replay_history(entries)
        except ReplayError as exc:
            self.assertNotIn("after terminal", str(exc))
        else:
            # If replay succeeded, that's also fine — terminal gate
            # didn't reject the third entry.
            pass

    def test_incident_resolve_abort_is_terminal(self):
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            self._incident_resolve_entry(ts_hours=12, action="abort"),
        ]
        # abort itself replays fine; project_state freezes to aborted.
        state = replay_history(entries)
        self.assertEqual(state["project_state"], "aborted")
        self.assertEqual(state["release_close_reason"], "incident-abort")

    def test_mutating_entry_after_abort_rejected(self):
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            self._incident_resolve_entry(ts_hours=12, action="abort"),
            # Any mutating event after terminal is fatal.
            HistoryEntry(
                timestamp=self._ts(13),
                event="bug-intake",
                summary="bug=docs/bug/BUG-099.md registered (post-close)",
                agent="a/b",
                result=None,
                next=None,
                raw="",
            ),
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        self.assertIn("after terminal incident-resolve", str(cm.exception))

    def test_mutating_entry_after_reconstruct_rejected(self):
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            self._incident_resolve_entry(ts_hours=12, action="reconstruct"),
            HistoryEntry(
                timestamp=self._ts(13),
                event="bug-intake",
                summary="bug=docs/bug/BUG-099.md registered (post-close)",
                agent="a/b",
                result=None,
                next=None,
                raw="",
            ),
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        self.assertIn("after terminal incident-resolve", str(cm.exception))

    def test_incident_resolve_missing_action_token_rejected(self):
        bad_entry = HistoryEntry(
            timestamp=self._ts(12),
            event="incident-resolve",
            summary="incident=docs/incident/INCIDENT-007.md Incident resolved",
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            bad_entry,
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        self.assertIn("missing", str(cm.exception))

    def test_incident_resolve_unknown_action_rejected(self):
        bad_entry = HistoryEntry(
            timestamp=self._ts(12),
            event="incident-resolve",
            summary=(
                "action=retry incident=docs/incident/INCIDENT-007.md "
                "Incident resolved"
            ),
            agent="a/b",
            result=None,
            next=None,
            raw="",
        )
        entries = [
            self._init_entry(),
            self._incident_start_entry(ts_hours=11),
            bad_entry,
        ]
        with self.assertRaises(ReplayError) as cm:
            replay_history(entries)
        # apply_incident_resolve raises with the action enum.
        self.assertIn("action", str(cm.exception))

    def test_incident_replay_does_not_read_artifact_files(self):
        # Same property as bug-start / bug-rework: replay reads only
        # canonical history tokens. Even with empty tempdir and no
        # BUG / INCIDENT files on disk, replay must succeed.
        with tempfile.TemporaryDirectory() as tmp:
            entries = [
                self._init_entry(),
                self._incident_start_entry(ts_hours=11),
                self._incident_resolve_entry(ts_hours=12, action="continue"),
            ]
            state = replay_history(entries, root=tmp)
            # continue resumed testing.
            self.assertEqual(state["current_stage"], "testing")
            self.assertEqual(state["sub_state"], "review-passed")
            self.assertFalse(state["workflow_incident_active"])


# ---------- Phase 6.4: update-advance replay ----------


class ReplayUpdateAdvanceTests(unittest.TestCase):
    """Phase 6.4: update-advance replay handler reproduces stage advance
    purely from canonical from=/to= summary tokens, with an extra M1-
    style state-diff guard that catches summary/state divergence (e.g.
    a hand-authored history entry whose to= disagrees with the
    state-machine result)."""

    def _init_entry(self) -> HistoryEntry:
        return _init_entry(timestamp="2026-11-01T10:00:00Z")

    def _ts(self, hours: int) -> str:
        return f"2026-11-01T{hours:02d}:00:00Z"

    def test_advance_replay_routes_through_next_stage(self):
        # init lands at prd-inception/write. To replay an advance we
        # need to forge a transition to (prd-inception, approved) first,
        # then the advance entry can fire.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=prd-inception "
                        "sub_state=approved"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="update-advance",
                    summary=(
                        "from=prd-inception to=srs-specification Stage advance"
                    ),
                    agent="claude-opus-4-7/workflow-update",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            state = replay_history(entries)
            self.assertEqual(state["current_stage"], "srs-specification")
            self.assertEqual(state["sub_state"], "write")
            self.assertEqual(state["review_iteration"], 0)

    def test_advance_replay_missing_tokens_rejected(self):
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=prd-inception "
                        "sub_state=approved"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="update-advance",
                    summary="advanced (no canonical tokens)",
                    agent="a/b",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("missing", str(cm.exception))

    def test_advance_replay_to_token_mismatch_detected(self):
        # Hand-authored history claims the advance led to architecture-design,
        # but starting from prd-inception/approved the state machine
        # derives srs-specification. The handler's diff guard must catch
        # this on top of M1.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with patch.object(pr, "_HANDLERS", handlers):
            entries = [
                self._init_entry(),
                HistoryEntry(
                    timestamp=self._ts(11),
                    event="test-stage-advance",
                    summary=(
                        "test-stage-advance current_stage=prd-inception "
                        "sub_state=approved"
                    ),
                    agent="test/forge",
                    result=None,
                    next=None,
                    raw="",
                ),
                HistoryEntry(
                    timestamp=self._ts(12),
                    event="update-advance",
                    summary=(
                        "from=prd-inception to=architecture-design Stage advance"
                    ),
                    agent="claude-opus-4-7/workflow-update",
                    result=None,
                    next=None,
                    raw="",
                ),
            ]
            with self.assertRaises(ReplayError) as cm:
                replay_history(entries)
            self.assertIn("history may be corrupt", str(cm.exception))

    def test_advance_replay_does_not_read_artifact_files(self):
        # Replay-skips-artifacts: with empty tempdir as root, advance
        # replay still succeeds because the canonical from=/to= tokens
        # carry everything the state machine needs.
        from skills._shared.dev_workflow import progress_replay as pr

        handlers = dict(pr._HANDLERS)
        handlers["test-stage-advance"] = _stage_advance_to_testing_review_passed

        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(pr, "_HANDLERS", handlers):
                entries = [
                    self._init_entry(),
                    HistoryEntry(
                        timestamp=self._ts(11),
                        event="test-stage-advance",
                        summary=(
                            "test-stage-advance current_stage=prd-inception "
                            "sub_state=approved"
                        ),
                        agent="test/forge",
                        result=None,
                        next=None,
                        raw="",
                    ),
                    HistoryEntry(
                        timestamp=self._ts(12),
                        event="update-advance",
                        summary=(
                            "from=prd-inception to=srs-specification Stage advance"
                        ),
                        agent="a/b",
                        result=None,
                        next=None,
                        raw="",
                    ),
                ]
                state = replay_history(entries, root=tmp)
                self.assertEqual(state["current_stage"], "srs-specification")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
