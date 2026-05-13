# Session Handoff — Task 6 Phase 4 Start (`status_transition.py`)

**Handoff Date**: 2026-05-07  
**Handoff By**: Claude (claude-opus-4-7[1m])  
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`  
**Current Task**: Task 6 implementation — `progress.py` + doc-guardian scripts  
**Current Phase**: **Phase 3 closed (round 1 + round 2 + sweep all accepted by Codex). Next session should start Phase 4 (`status_transition.py`).**  
**Important Status**: Phase 3 round 2 review accepted (A); Round 2 follow-up sweep applied. Tests pass: `Ran 117 tests ... OK`.

---

## 0. New Session Read Order

Read these in order before coding:

1. `docs/handoff/session_handoff_task6_phase4_20260507.md` (this handoff)
2. `docs/implementation/task6_plan_20260507.md` §9 + §11.3 + §12 (status_transition.py plan, atomicity, tests)
3. `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md` (Phase 3 closure context)
4. `docs/review/task6_phase3_changelog_validate_review_20260507.md` (Phase 3 round 1 — explains why current strictness exists)
5. `skills/doc-guardian/SKILL.md` §6.7 (status_transition.py interface and call sequencing)
6. `skills/doc-guardian/references/change-log-format.md` §7.1 (`[frontmatter]` Change Log entry rules)
7. `skills/doc-guardian/references/frontmatter-schema.md` §1-§2 (universal fields, status state machine, gated types)
8. `skills/_shared/dev_workflow/changelog.py` (Phase 3 in-memory promote/validate API — Phase 4 reuses)
9. `skills/_shared/dev_workflow/atomic.py` (`transaction()` context manager — Phase 4 reuses for multi-doc all-or-nothing)
10. `skills/_shared/dev_workflow/frontmatter.py` (`parse_frontmatter`, `render_markdown`)
11. `skills/_shared/dev_workflow/schema.py` (`INCREMENTAL_DOC_TYPES`, `GATED_APPROVED_TYPES`, `STATUSES`)
12. `skills/doc-guardian/scripts/validate.py` (`validate_file(doc_path, root)` — Phase 4 reuses for post-write self-validate)
13. `skills/doc-guardian/scripts/changelog.py` (CLI shape reference; Phase 4 follows same pattern)

Optional background:

- `docs/handoff/session_handoff_task6_phase3_20260507.md`
- `docs/handoff/task6_progress_py_prerequisites_20260506.md`
- `docs/design/skill_set_design_proposal_v0.5.md` §15.2

---

## 1. Critical Constraints

- Do **not** treat `dev-workflow-skills2` itself as a managed workflow project. This repo is the skill/script implementation repo.
- Do **not** create or mutate repo-root `progress.md` / `progress-history.md` for this repo.
- Tests must use temp directories / fixtures and must not mutate the repo's real `docs/` or `skills/` as a managed project.
- The current git worktree is largely untracked (`docs/`, `skills/`, `tests/`, helper start scripts). Do not delete, clean, reset, or revert these files.
- Keep Task 6 phase boundaries:
  - **Phase 4** (this session): `status_transition.py` + tests.
  - **Phase 5/6**: `progress.py` core, Bug Flow, incident, `update --advance`. Do not implement.
  - **Phase 7**: full smoke + docs polish.
- `progress.py update --event` event whitelist is exactly:
  - `write-complete`
  - `review-issues`
  - `review-passed`
  - `human-confirmed`
- `issues-found` is business wording, not an event name.
- `bug-rework` is the dedicated active Bug Flow retest fail/partial command (Phase 6 territory). Do not anticipate it here.
- Phase 4 must **not** write to `progress.md` / `progress-history.md` — that is `progress.py`'s exclusive ownership. Phase 4 only owns frontmatter `status` mutation per change-log-format.md §7.1 + SKILL.md §6.7.

---

## 2. Current Repository State

Project root:

```bash
/home/cgs/github_projects/dev-workflow-skills2
```

Relevant runtime layout:

- `skills/_shared/dev_workflow/` — Phase 2 + 3 shared modules (PyYAML-backed frontmatter, atomic transactions, change-log helper, schema constants, etc.)
- `skills/doc-guardian/scripts/changelog.py` — Phase 3 CLI (validate + promote)
- `skills/doc-guardian/scripts/validate.py` — Phase 3 CLI (file + ids; all/consistency stub exit 2)
- `skills/workflow-protocol/scripts/` — empty (Phase 5/6 territory)
- `tests/` — 117 tests across 5 files (`test_frontmatter_markdown_atomic.py` / `test_conditions_artifacts.py` / `test_progress_schema.py` / `test_changelog.py` / `test_validate_file.py`)

Runtime checks at handoff:

```bash
python3 -m unittest discover -s tests
# Ran 117 tests in 0.128s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK
```

No repo-root `progress.md` or `progress-history.md` exists (intentional — this repo is not workflow-managed).

---

## 3. Completed Work Before This Handoff

### Phase 1 — Docs Alignment

References, SKILL.md, and command-reference aligned for Task 6 (12 commands, `bug-rework`, Gap-3/4/5, status_transition.py interface, scenario-dispatcher count). Review accepted; Lows fixed.

### Phase 2 — Shared Foundation

Implemented `_shared/dev_workflow/{frontmatter,markdown,atomic,conditions,artifacts,progress_state,schema}.py` + 34 unit tests. Round 1 + Round 2 review accepted with all findings closed (M1 normal/protected task transitions split + keyword-only flag, M2 atomic rollback per-target error aggregation + parent fsync, etc.).

### Phase 3 — `changelog.py` + `validate.py file/ids`

Implemented:

- `skills/_shared/dev_workflow/changelog.py` — pure in-memory `parse_pending_section` / `parse_changelog_section` / `merge_groups` / `render_changelog_body` / `promote_text` / `validate_text` + `_classify_comment_line` strict comment handling.
- `skills/doc-guardian/scripts/changelog.py` — CLI wrapper for `promote` / `validate` with `--root`, atomic write + post-validate.
- `skills/doc-guardian/scripts/validate.py` — CLI for `file` (classes 1-7) / `ids` (per-directory regex). `all` / `consistency` stubbed exit 2 + deferred message.
- `tests/test_changelog.py` — 29 tests (including 7 round 2 regression + 3 round 2 sweep tests for unclosed comment / inline trailing / blank line after heading).
- `tests/test_validate_file.py` — 53 tests (including 14 round 2 regression + 2 round 2 sweep tests for non-string / empty path-ref).

Phase 3 review history:

- Round 1 review: `docs/review/task6_phase3_changelog_validate_review_20260507.md` — recommendation **(B) fix before Phase 4** (1H + 3M + 2L).
- Round 2 review: `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md` — recommendation **(A) accept regression and proceed to Phase 4** (0H/0M/1L). The new Low (blank line after `### YYYY-MM-DD` heading before first entry) plus 4 optional polish tests have been applied as a pre-Phase-4 sweep.

Important Phase 3 implementation invariants (Phase 4 must respect):

- `changelog.promote_text(content) -> (new_content, [Entry])` is pure in-memory. No file I/O. No Change Log entry written when pending is empty (returns content unchanged + empty list), but **does** parse and validate the existing Change Log even on no-op so malformed pre-existing content surfaces.
- `changelog.validate_text(content) -> [issues]` is the discipline gate. Phase 4 should **not** bypass it.
- `non_comment_lines` (in `markdown.py`) is intentionally kept lenient on multi-line comment closer trailing for backward compatibility; **changelog.py** does its own strict parsing via `_classify_comment_line`. Phase 4 status helper, when generating Pending entries, must produce single canonical lines that go through the same strict parser, so do not embed inline comments alongside content.
- `atomic.py` exposes `transaction()` context manager with all-or-nothing rollback (`AtomicTransaction.write_text` / `backup` / `rollback` with per-target OSError aggregation + parent dir fsync). Phase 4 multi-doc apply uses this.
- `validate_file(doc_path, root)` is importable directly from `scripts/validate.py` (no need to shell out). Phase 4 self-validate after write should call this in-process.

---

## 4. Next Phase Scope — Phase 4

Implement:

1. `skills/doc-guardian/scripts/status_transition.py`
   - `plan` dry-run subcommand
   - `apply` mutation subcommand
   - 4 events × event-to-status mapping
   - Multi-doc all-or-nothing transaction
   - Idempotent retry (already-at-target → exit 0 without writing)
   - Change Log atomicity for incremental docs (frontmatter Pending entry → in-memory promote → write)
   - Self-validate after write (calls `validate.validate_file`)
   - Optional `--root` global flag matching changelog.py / validate.py
2. Tests:
   - `tests/test_status_transition.py` — covers all 4 events, gated vs non-gated, incremental vs snapshot, idempotency, multi-doc rollback
   - Reuse fixture builders from `tests/test_validate_file.py` style if convenient (or extract a small `tests/_fixtures.py` helper if it reduces duplication; keep tests in temp dirs)
3. **Do not** implement in Phase 4:
   - `progress.py` workflow state machine (Phase 5/6)
   - `validate.py consistency` deep cross-progress checks (Phase 5/6)
   - `progress.py update --advance` artifact scanning (Phase 6)
   - Any new event names beyond the four above
   - Any cross-doc referential integrity beyond what `validate_file` already enforces

---

## 5. Phase 4 Detailed Requirements

### 5.1 CLI Shape

```bash
python3 skills/doc-guardian/scripts/status_transition.py [--root <root>] \
    plan --event <event> --doc <path> [--doc <path> ...]

python3 skills/doc-guardian/scripts/status_transition.py [--root <root>] \
    apply --event <event> --doc <path> [--doc <path> ...]
```

Exit code contract (matches Phase 3 conventions):

- `0` — success (including idempotent no-op)
- `1` — pre-validate / mutate / self-validate failure (after rollback if any writes had succeeded)
- `2` — CLI usage error

### 5.2 Event → Status Mapping

Source of truth: `skills/doc-guardian/SKILL.md` §6.7 + change-log-format.md §7.1. Apply per-doc:

| Event | Allowed old status | New status | Doc type scope |
|-------|--------------------|------------|----------------|
| `write-complete` | `draft` / `revising` | `in-review` | All doc types |
| `review-issues` | `in-review` | `revising` | All doc types |
| `review-passed` | `in-review` | `review-passed` | All doc types |
| `human-confirmed` | `review-passed` | `approved` | **Only** `prd` / `srs` / `architecture` / `cr` (`schema.GATED_APPROVED_TYPES`) |

If a doc's current status does not match the allowed-old set:

- If current already equals the new status (e.g. `apply --event write-complete` on a doc already at `in-review`) → idempotent no-op for that doc (success). Do not append a Change Log entry on idempotent retry.
- Otherwise → reject with actionable stderr citing event + doc + current status.

If `human-confirmed` is requested for a non-gated type → reject with `human-confirmed only valid for {prd, srs, architecture, cr}` + doc type info.

### 5.3 Mutation Per Doc

For each doc that is **not** already at the target status:

1. Load file → `parse_frontmatter`.
2. Validate the doc's current status is in the allowed-old set (or already-target → no-op branch above).
3. Compute new frontmatter `status` (per mapping) and new `updated` (current ISO8601 UTC with `Z` suffix; second precision).
4. **If incremental doc type** (`schema.INCREMENTAL_DOC_TYPES`):
   - Append entry to `## Pending Changes` body: `- <new updated> [frontmatter]: 更新 status 至 <new-status>`.
   - Re-render the file content with the new frontmatter + new body containing the appended pending entry.
   - Run `changelog.promote_text(new_content)` in memory → produces final content with the entry merged into Change Log + Pending Changes cleared.
5. **If snapshot doc type**:
   - Just re-render with new frontmatter `status` + `updated`. No Change Log entries.
6. Validate the final in-memory content with `changelog.validate_text` (incremental docs) — must return empty list.
7. Stage the write to the multi-doc transaction.

### 5.4 Multi-Doc Transaction (all-or-nothing)

Use `with atomic.transaction() as tx:`:

1. **Pre-flight**: for each doc, do steps 1-3 of §5.3 (load, check current status, compute new). Do not write yet. Collect (doc_path, final_content) for each non-no-op doc, plus a list of no-op docs.
2. If any pre-flight check fails → return error list, exit 1, **no writes** issued.
3. For each non-no-op doc, call `tx.write_text(doc_path, final_content)`. The transaction backs up existing file, writes atomically.
4. **After** all writes succeed, call `validate.validate_file(doc_path, root)` for each written doc as post-write self-validate. If any returns non-empty issues → raise to trigger transaction rollback.
5. On any failure, the transaction context manager rolls back all writes (per the Phase 2 round 2 atomic.py contract).
6. On success, exit 0 with summary of mutated and no-op docs.

`plan` subcommand: stops after step 1 and prints the planned (doc, old_status → new_status, op_kind ∈ {mutate, no-op}) table without invoking the transaction.

### 5.5 Frontmatter Pending Entry Format

Per change-log-format.md §7.1:

```
- <ISO8601 UTC timestamp> [frontmatter]: 更新 status 至 <new-status>
```

Constraints:

- `<timestamp>` matches `^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$` and equals the new `updated` value
- `<new-status>` is the literal new status string (e.g. `in-review`)
- The line is single-line; never include comments or other content

The entry must round-trip through `changelog.parse_pending_section` → `merge_groups` → `render_changelog_body` cleanly. It will land in the date group matching the timestamp's date.

### 5.6 Idempotent Retry

If `apply --event <event> --doc <path>` is invoked on a doc whose current status already equals the event's target status:

- Do not append a Pending Changes entry
- Do not bump `updated`
- Do not write the file
- Print one stderr line summary (for diagnostic only) and exit 0

This matches SKILL.md §6.7 ("doc 已在目标 status 时 exit 0，不重复写 Change Log entry") and supports retries by callers that do not know whether the helper already ran.

If multiple docs are passed and some are no-op while others mutate, the apply still proceeds; all-or-nothing guarantees apply only to the mutating subset.

### 5.7 Self-Validate Reuse

`validate.validate_file(doc_path, root) -> list[str]` is importable. Phase 4 imports it from `skills/doc-guardian/scripts/validate.py` via the same `parents[3]` bootstrap used in changelog.py. Do not re-run subprocess; use in-process Python call.

If the post-validate path diverges between Phase 4 helper and Phase 3 validate.py over time, the helper must keep using `validate_file` so the contract stays single-sourced.

---

## 6. Shared Modules To Reuse

Use existing helpers; do not duplicate behavior:

- `skills._shared.dev_workflow.frontmatter`: `parse_frontmatter`, `render_markdown`
- `skills._shared.dev_workflow.markdown`: `find_section`, `replace_section_body` (for inserting Pending entry)
- `skills._shared.dev_workflow.atomic`: `transaction` (context manager); do not call `atomic_write_text` directly when multi-doc transaction is needed
- `skills._shared.dev_workflow.changelog`: `promote_text`, `validate_text`, `Entry` dataclass if needed
- `skills._shared.dev_workflow.schema`: `INCREMENTAL_DOC_TYPES`, `GATED_APPROVED_TYPES`, `STATUSES`, `UNIVERSAL_FIELDS`
- `skills.doc_guardian.scripts.validate.validate_file` — import via `sys.path.insert(0, _REPO_ROOT)` bootstrap then `import validate` (same pattern Phase 3 tests use)

If a shared helper is missing (e.g. a "compose Pending entry line" helper that multiple sites might want), add it to `skills/_shared/dev_workflow/` instead of inlining. Keep `status_transition.py` thin.

---

## 7. Testing Strategy

Use `unittest` and temporary directories:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
```

### 7.1 Required Test Cases

Cover at least:

- 4 event mappings, each on at least one incremental doc and one snapshot doc
- gated `human-confirmed` allowed on PRD / SRS / Architecture / CR
- `human-confirmed` rejected on non-gated type (e.g. development-plan)
- Idempotent retry: doc already at target status → exit 0, no Pending entry, file unchanged byte-for-byte
- Multi-doc happy path: e.g. SRS + Acceptance Plan both move write-complete → in-review in same transaction
- Multi-doc rollback: one doc fails (e.g. malformed or status not in allowed-old) → no doc is mutated
- Pending entry format: exactly `- <ISO8601> [frontmatter]: 更新 status 至 <new>` and round-trips through validate_text
- Snapshot doc: status update only, no Change Log entries even if doc had no Change Log section
- `plan` dry-run does not mutate and prints expected summary
- CLI exit codes (0 / 1 / 2) at each branch
- Post-write validate catches a malformed result (mock or simulate by passing a doc whose Pending entry would create a stale state)

### 7.2 Test File Structure

Recommended: `tests/test_status_transition.py` with classes:

- `EventMappingTests` — 4 events × incremental+snapshot
- `GatedRejectionTests` — `human-confirmed` on PRD/SRS/Architecture/CR allowed; on others rejected
- `IdempotencyTests` — already-at-target no-op
- `MultiDocTransactionTests` — all-or-nothing rollback
- `PendingEntryFormatTests` — entry shape + round-trip through validate
- `CliIntegrationTests` — `plan` / `apply` with `--root`, exit codes

Reuse fixture style from `tests/test_validate_file.py` (e.g. `_base_universal`, `_build_doc`, `_write` helpers). Optional: extract these to `tests/_fixtures.py` if duplication grows; small duplication (one helper per test file) is also fine and matches Phase 3's current pattern.

---

## 8. Known Watch Points

- **Idempotency vs append**: idempotent retry must NOT add a Pending entry. The check is "current status == target status", not "did caller call us already". Keep the gate before any mutation.
- **Pending entry timestamp matches updated**: the new `updated` and the Pending entry timestamp must be identical (single-source-of-truth) so round-trip through promote → validate is consistent.
- **In-memory promote, then atomic write**: do the entire compute in memory before staging the write. Do not write a Pending entry first and promote later — that would expose intermediate state to crashes.
- **Self-validate uses canonical content**: call `validate_file` after `tx.write_text`, not on the in-memory string. The post-validate gate ensures the on-disk file is also healthy. If validate fails after write, raise → transaction rollback restores backup.
- **Non-gated docs and `human-confirmed`**: SKILL.md / schema explicitly restrict `approved` to `prd / srs / architecture / cr`. Reject with a clear message; do not silently downgrade to `review-passed`.
- **Multi-doc atomicity**: caller may pass docs of different types. They share a single transaction. If even one rolls back, all roll back. Reuse Phase 2 round 2's `transaction()` — do not roll your own.
- **No `progress.py` interaction in Phase 4**: SKILL.md §6.7 specifies the call sequence `progress.py update --event` runs **first**, then `status_transition.py apply` runs. Phase 4 only owns step 5; step 4 (progress event) is Phase 5/6. Tests should not assume `progress.py` exists.
- **Bootstrap path**: same as Phase 3 (`Path(__file__).resolve().parents[3]`). Verify with a quick `--help` smoke test before writing tests.
- **Round 2 sweep state**: Phase 3 round 2 + sweep added strict comment / blank-line rules in `changelog.py`. Phase 4 generated Pending entries are simple single lines and won't trigger the strict rules, but if you ever need to insert HTML comments alongside entries, don't — the strict parser will reject.

---

## 9. Recommended Phase 4 Work Order

1. Re-run existing tests + compileall to confirm baseline (117 tests, OK).
2. Re-read change-log-format.md §7.1 and SKILL.md §6.7 in detail.
3. Sketch internal API:
   - `compute_plan(event, docs, root)` → `[(doc_path, current_status, new_status, kind ∈ {mutate, no-op, reject})]`
   - `apply_plan(plan, root)` → uses `transaction()` + `validate_file`
   - CLI is a thin wrapper.
4. Implement `compute_plan` (no I/O during compute besides reading docs); add `EventMappingTests` + `GatedRejectionTests` + `IdempotencyTests` first.
5. Implement `apply_plan` with multi-doc transaction; add `MultiDocTransactionTests` and `PendingEntryFormatTests`.
6. Implement CLI (`plan` + `apply`); add `CliIntegrationTests`.
7. Run full suite + compileall.
8. Generate Phase 4 review prompt and ask Codex (or Claude) to save the review report at `docs/review/task6_phase4_status_transition_review_20260507.md`. Recommendation chain: round 1 → round 2 if needed → accept (A) → handoff to Phase 5/6.

Phase 4 acceptance target:

- `python3 skills/doc-guardian/scripts/status_transition.py --help` works
- `plan` and `apply` work for all 4 events on incremental + snapshot docs
- Idempotent retries do not double-write Change Log entries
- Multi-doc rollback verified by tests
- New tests pass; full suite green; compileall clean
- No mutation to repo-root `progress.md` (none exists; ensure tests don't introduce it)

---
