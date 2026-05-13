# Task 6 Progress.py Prerequisites — Batch 3b/3c Follow-up

**Date**: 2026-05-06
**Source**: `docs/review/skill_set_batch3b_review.md` + `docs/review/skill_set_batch3b_round2_review.md` + `docs/review/skill_set_batch3c_review.md`
**Scope**: Implementation prerequisites for `skills/workflow-protocol/scripts/progress.py` before Stage 4 Development and Stage 5 active Bug Flow can be executed end-to-end.

This checklist records the Batch 3b/3c gaps that are intentionally left as Task 6 implementation prerequisites. It does **not** reopen the Stage 4 or Stage 5 skill design; Batch 3b Round 2 accepted the development SKILL.md skeletons, and Batch 3c review accepted the Stage 5/6/7 SKILL.md skeletons with Gap-5 staged here.

## 1. Required Task-State Transitions

Add the following transitions to the Stage 4 task transition table in `skills/workflow-protocol/references/command-reference.md` and implement them in `progress.py update --task` / `bug-start` as noted.

| Gap | From | To | Required precondition | Owner / trigger |
|-----|------|----|-----------------------|-----------------|
| Gap-3 | `verifying` | `code-revising` | `verification_result.md` exists and frontmatter `verification_status` is fail/partial | `development-code-write` verification retry |
| Gap-4 | `verified` | `test-revising` | active Bug Flow, `root_cause==development`, BUG body `Affected Task(s)` includes `Tn`, fix requires test change | `progress.py bug-start --root-cause development` or `bug-rework` auto-rollback |
| Gap-4 | `verified` | `code-revising` | active Bug Flow, `root_cause==development`, BUG body `Affected Task(s)` includes `Tn`, fix requires source change | `progress.py bug-start --root-cause development` or `bug-rework` auto-rollback |
| Gap-4 | `code-review-passed` | `code-revising` | active Bug Flow, `root_cause==development`, BUG body `Affected Task(s)` includes `Tn`, source fix needed before verification | `progress.py bug-start --root-cause development` or `bug-rework` auto-rollback |

## 2. Bug-Start Development Auto-Rollback

When `progress.py bug-start --root-cause development --bug <BUG-NNN.md>` succeeds:

1. Keep the existing Batch 2 mutation: `current_stage: testing -> development`, `sub_state: review-passed -> write`, `bug_flow.active: true`.
2. Parse the BUG body `## Triage Analysis` section for `Affected Task(s)` values (`T<n>` list). Current schema does not store task IDs in frontmatter.
3. For each affected task:
   - If task is `verified` and the fix is test-only/test-first, set task state to `test-revising`.
   - If task is `verified` and the fix is source-code, set task state to `code-revising`.
   - If task is `code-review-passed` and source-code fix is needed, set task state to `code-revising`.
   - If task cannot be classified, leave task state unchanged and require `development-planning-write` replan/route decision; do not guess.
4. Append a progress-history entry that lists affected tasks and rollback targets.
5. Reject or require human escalation if BUG body lacks `Affected Task(s)` and no planning rebreakdown path is selected.

## 3. Idempotent Planning Task Registration

`development-planning-review` may be re-invoked after global planning `review-passed` if only part of the task registration succeeded.

Implementation requirements:

- `progress.py update --task Tn --status planning-done` should be safe to retry when `Tn` is already `planning-done`.
- Repeated registration of an already `planning-done` task should be a no-op or append an idempotent history entry, not fail fatally.
- The command must still reject incompatible states such as a task already in `test-writing` unless the operation is a pure idempotent retry for `planning-done`.

## 4. Planning-Done Atomic Consistency

When implementing `progress.py update --task Tn --status planning-done`, validate atomically that:

- `docs/release{release}/development/breakdown.md` exists and declares `Tn`.
- `docs/release{release}/development/tasks/Tn/detailed_design.md` exists.
- `detailed_design.md` frontmatter `task_id` equals `Tn`.
- Path `tasks/Tn/`, breakdown task table, and progress task key agree.

Important boundary from Batch 3b Round 2:

- `validate.py file` does **not** check whether `task_id` already exists in `progress.md development_state.task_states`.
- Cross-file/progress consistency is enforced by `progress.py update --task` and by `validate.py consistency` / `progress.py update --advance` after task registration.

## 5. Non-Bypass Rule

Until Gap-3, Gap-4, and Gap-5 transitions are implemented:

- Do not hand-edit `progress.md` / `progress-history.md` to move tasks backward.
- Do not let `development-code-write` mark `verified` after a failed/partial `verification_result.md`.
- Do not let `development-test-write` or `development-code-write` accept `verified` as an entry state during Bug Flow.
- Do not close Bug Flow until Stage 5 retest passes and `progress.py bug-close` runs.
- Do not re-run `bug-start`, create a new BUG, or hand-edit `current_stage` when active Bug Flow retest fails; use the Gap-5 command once implemented.

## 6. Gap-5 — Active Bug Flow Retest Re-routing

When active Bug Flow has already routed a BUG to its root-cause stage, the fix may return to Stage 5 Testing and still fail. Current `command-reference.md` defines `bug-start` only for initial Bug Flow entry (`bug_flow.active==false`) and `bug-close` only for retest pass. It does not define a legal path for retest fail/partial to return to the existing `bug_flow.root_cause` stage.

Recommended implementation:

| Gap | Command / transition | Required precondition | Mutation owner / trigger |
|-----|----------------------|-----------------------|--------------------------|
| Gap-5 | `progress.py bug-rework --bug <BUG-NNN.md>` | `bug_flow.active==true`, `current_stage==testing`, `sub_state==review-passed`, latest `test-report.verification_status` is fail/partial, `<BUG>` equals `bug_flow.bug_report_path`, BUG frontmatter `root_cause == bug_flow.root_cause ∈ {srs, architecture, development}` | `testing-write` post-review Case C / Bootstrap |

Mutation:

1. Keep `bug_flow.active: true`.
2. Keep `bug_flow.bug_report_path` and `bug_flow.root_cause` unchanged.
3. Set `current_stage: testing -> <root_cause stage>`:
   - `srs -> srs-specification`
   - `architecture -> architecture-design`
   - `development -> development`
4. Set `sub_state: review-passed -> write`.
5. Set `review_iteration: <N> -> 0`.
6. Append a progress-history entry. **Phase 6.2 implementation note (supersedes this prereq's original wording)**: the canonical replay-token contract requires the summary to carry `bug=<path> root_cause=<srs|architecture|development> Bug Flow rerouted [rollback=Tn:old->new;...]`; the test-report path is a forward CLI precondition rather than a history token (replay never re-reads the test-report). See `skills/workflow-protocol/references/command-reference.md` §9 Append history for the exact template.
7. If `root_cause==development`, reuse Gap-4 logic: parse BUG body `Affected Task(s)` and rollback affected task states to `test-revising` / `code-revising` as needed. If affected task classification is missing, require `development-planning-write` replan/route decision; do not guess.

Rejected alternative:

- Do not overload initial `bug-start` for retest fail. Keeping a dedicated `bug-rework` command preserves the meaning of `bug-start` as first Bug Flow entry and avoids accidentally clearing or replacing active `bug_flow` fields.

Non-bypass rule:

- Until the `bug-rework` script lands in Phase 5/6, active Bug Flow retest fail/partial must stop and escalate to user/Bootstrap. The command is now fully specified in `skills/workflow-protocol/references/command-reference.md` §9; testing-write/-review must escalate when the command is unavailable or rejects, but must not create a second BUG, call `bug-start` again, call `bug-close`, or hand-edit `progress.md`.
