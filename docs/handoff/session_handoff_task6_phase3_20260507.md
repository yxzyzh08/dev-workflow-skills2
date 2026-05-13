# Session Handoff — Task 6 Phase 3 Start

**Handoff Date**: 2026-05-07  
**Handoff By**: Codex (GPT-5)  
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`  
**Current Task**: Task 6 implementation — `progress.py` + doc-guardian scripts  
**Current Phase**: **Phase 2 shared foundation accepted; next session should start Phase 3 (`changelog.py` + `validate.py file`)**  
**Important Status**: Claude Phase 2 review and regression review are accepted. Shared foundation tests pass: `Ran 34 tests ... OK`.

---

## 0. New Session Read Order

Read these files before coding:

1. `docs/handoff/session_handoff_task6_phase3_20260507.md` (this handoff)
2. `docs/implementation/task6_plan_20260507.md`
3. `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md`
4. `docs/review/task6_phase2_shared_foundation_review_20260507.md`
5. `docs/review/task6_phase1_docs_alignment_review_20260507.md`
6. `docs/handoff/task6_progress_py_prerequisites_20260506.md`
7. `skills/doc-guardian/references/frontmatter-schema.md`
8. `skills/doc-guardian/references/directory-layout.md`
9. `skills/doc-guardian/references/change-log-format.md`
10. `skills/doc-guardian/references/required-artifacts.md`
11. `skills/doc-guardian/SKILL.md`
12. `skills/workflow-protocol/references/command-reference.md`
13. `skills/workflow-protocol/SKILL.md`

Optional background:

- `docs/handoff/session_handoff_20260506_v4.md`
- `docs/design/skill_set_design_proposal_v0.5.md`

---

## 1. Critical Constraints

- Do **not** treat `dev-workflow-skills2` itself as a managed workflow project. This repo is the skill/script implementation repo.
- Do **not** create or mutate repo-root `progress.md` / `progress-history.md` for this repo.
- Tests must use temp directories / fixtures and must not mutate the repo's real `docs/` or `skills/` as a managed project.
- The current git worktree is largely untracked (`docs/`, `skills/`, `tests/`, helper start scripts). Do not delete, clean, reset, or revert these files.
- Keep Task 6 phase boundaries:
  - Phase 3: `changelog.py`, `validate.py file`, `validate.py ids`, and tests.
  - Phase 4: `status_transition.py`.
  - Phase 5/6: `progress.py` core, Bug Flow, incident, `update --advance`.
- Do not implement missing `progress.py` / `status_transition.py` behavior during Phase 3 unless a small shared utility is required and isolated.
- `progress.py update --event` event whitelist is exactly:
  - `write-complete`
  - `review-issues`
  - `review-passed`
  - `human-confirmed`
- `issues-found` is business wording, not an event.
- `bug-rework` is the dedicated active Bug Flow retest fail/partial command. Do not overload `bug-start`.

---

## 2. Current Repository State

Project root:

```bash
/home/cgs/github_projects/dev-workflow-skills2
```

Relevant write state:

- Runtime script directories exist but are currently empty:
  - `skills/doc-guardian/scripts/`
  - `skills/workflow-protocol/scripts/`
- Shared foundation package exists:
  - `skills/_shared/dev_workflow/`
- Current tests:
  - `tests/test_frontmatter_markdown_atomic.py`
  - `tests/test_conditions_artifacts.py`
  - `tests/test_progress_schema.py`
- No repo-root `progress.md` or `progress-history.md` exists.

Last validation run in this handoff session:

```bash
python3 -m unittest discover -s tests
# Ran 34 tests in 0.031s
# OK

python3 -m compileall -q skills/_shared tests
# OK
```

---

## 3. Completed Work Before This Handoff

### Phase 1 — Docs Alignment

Phase 1 aligned references and SKILL docs for Task 6:

- `skills/workflow-protocol/references/command-reference.md`
  - Command count aligned to 12.
  - `bug-rework` added.
  - Gap-3 / Gap-4 / Gap-5 transitions specified.
- `skills/workflow-protocol/SKILL.md`
  - `bug-rework` added to invocation matrix / Bug Flow / forbidden actions.
- `skills/doc-guardian/SKILL.md`
  - `status_transition.py` plan/apply interface documented.
  - Status helper ownership and Change Log behavior documented.
- `skills/doc-guardian/references/change-log-format.md`
  - Status helper frontmatter Change Log transaction behavior documented.
- `skills/scenario-dispatcher/SKILL.md`
  - Command count updated from 11 to 12.
- `skills/testing-write/SKILL.md` / `skills/testing-review/SKILL.md`
  - Active Bug Flow retest fail/partial uses `bug-rework`.
- `skills/bug-triage/SKILL.md`
  - Active retest fail/partial boundary clarified: no re-triage, no second BUG, no manual state edit.

Review:

- `docs/review/task6_phase1_docs_alignment_review_20260507.md`
- Result: accepted. Low findings adopted.

### Phase 2 — Shared Foundation

Implemented shared modules:

- `skills/_shared/dev_workflow/__init__.py`
- `skills/_shared/dev_workflow/frontmatter.py`
- `skills/_shared/dev_workflow/markdown.py`
- `skills/_shared/dev_workflow/atomic.py`
- `skills/_shared/dev_workflow/conditions.py`
- `skills/_shared/dev_workflow/artifacts.py`
- `skills/_shared/dev_workflow/progress_state.py`
- `skills/_shared/dev_workflow/schema.py`

Implemented focused unit tests:

- `tests/test_frontmatter_markdown_atomic.py`
- `tests/test_conditions_artifacts.py`
- `tests/test_progress_schema.py`

Important implementation details:

- `frontmatter.py`
  - Parses/renders Markdown YAML frontmatter.
  - Uses a PyYAML loader copy that disables timestamp auto-conversion so ISO8601 timestamps remain strings.
  - Preserves `release: "0.1"` as a string.
- `markdown.py`
  - Finds/replaces Markdown sections by exact heading.
  - Section ends at the next same-or-higher heading.
  - `non_comment_lines` supports single-line and multi-line HTML comments.
- `atomic.py`
  - Uses temp file + fsync + `os.replace` + parent dir fsync.
  - Provides `AtomicTransaction` rollback with per-target error aggregation.
  - Provides `atomic_replace_from` for atomic restore/copy from backups.
- `conditions.py`
  - Strict whitelist DSL parser/evaluator.
  - No `eval`, `exec`, or `ast.literal_eval`.
  - Supports `==`, `!=`, `&&`, `||`, parentheses.
  - `&&` has higher precedence than `||`.
  - Rejects unknown variables, function calls, quoted enum literals, assignment, unknown enum literals, property chains longer than two, and type mismatches.
- `artifacts.py`
  - Required artifact resolver aligned with `required-artifacts.md`.
  - SRS condition fields default to false when SRS is missing or fields are missing.
  - `workflow-incident-analysis` explicitly raises `ArtifactError` because incident state bypasses P6 matrix.
- `progress_state.py`
  - Event whitelist is exactly four events.
  - Stage order and root-cause mappings are encoded.
  - Normal task transitions are split from protected Gap-3/Gap-4 transitions.
  - `is_valid_task_transition(..., allow_protected=False)` rejects protected transitions unless caller explicitly opts in after checking preconditions.
- `schema.py`
  - Encodes doc type constants, required fields, incremental vs snapshot classification, and path templates.

Review:

- Round 1: `docs/review/task6_phase2_shared_foundation_review_20260507.md`
  - 0 High / 2 Medium / 6 Low.
  - Recommendation: accept Phase 3, with fixes before later phases.
- Round 2: `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md`
  - Round 1 findings fully fixed.
  - New findings: 0 High / 0 Medium / 2 Low.
  - Recommendation: accept regression and proceed to Phase 3.
- Post-Round-2 trivial fixes already present:
  - Precedence regression test now includes a discriminating case.
  - `atomic.py` cleanup catches `OSError` only and documents why.
  - `markdown.py` documents the intentional limitation for inline content after a multi-line comment closing tag.

---

## 4. Next Phase Scope — Phase 3

Phase 3 should implement:

1. `skills/doc-guardian/scripts/changelog.py`
   - `promote`
   - `validate`
   - optional `--root`
   - actionable non-zero errors
2. `skills/doc-guardian/scripts/validate.py`
   - `file <doc-path>` checks classes 1-7
   - `ids`
   - help output
   - optional `--root`
3. Tests:
   - `tests/test_changelog.py`
   - `tests/test_validate_file.py`
   - add fixtures only under `tests/fixtures/` if useful

Do not implement in Phase 3:

- `status_transition.py` mutation behavior (Phase 4)
- `progress.py` workflow state machine (Phase 5/6)
- `validate.py consistency` full P6/progress cross-checks (Phase 5/6 support; can be stubbed or deferred if help documents it)
- full project smoke path (Phase 7)

---

## 5. Phase 3 Detailed Requirements

### 5.1 `changelog.py validate`

Source of truth:

- `skills/doc-guardian/references/change-log-format.md`
- `skills/_shared/dev_workflow/schema.py`
- `skills/_shared/dev_workflow/markdown.py`
- `skills/_shared/dev_workflow/frontmatter.py`

Required behavior:

- Determine doc type from frontmatter.
- Incremental doc types require:
  - `## Pending Changes`
  - `## Change Log`
- Snapshot doc types do not require these sections, but if sections exist they should still be validated reasonably.
- Pending Changes is valid only if it contains no non-comment entries.
  - Blank lines and HTML comments are allowed.
  - Use `markdown.non_comment_lines`.
- Change Log must use:
  - date headings like `### YYYY-MM-DD`
  - strict entries like `- YYYY-MM-DDTHH:MM:SSZ [Section X[.Y]|frontmatter|全文]: summary`
- Timestamps inside each date group should be monotonic ascending.
- Reject malformed entries with actionable stderr.

### 5.2 `changelog.py promote`

Required behavior:

- Read doc frontmatter + body.
- If doc is snapshot and has no Change Log sections, succeed as no-op.
- If doc is incremental, require Pending Changes and Change Log sections.
- Parse Pending Changes entries using strict regex.
- Merge pending entries into Change Log grouped by `### YYYY-MM-DD`.
- Sort date groups descending.
- Sort entries inside a date group ascending by timestamp.
- Clear Pending Changes body.
- Write atomically using `atomic_write_text`.
- Validate result after promotion.

Recommended CLI shape:

```bash
python3 skills/doc-guardian/scripts/changelog.py validate <doc-path> [--root <root>]
python3 skills/doc-guardian/scripts/changelog.py promote <doc-path> [--root <root>]
```

### 5.3 `validate.py file`

Source of truth:

- `skills/doc-guardian/references/frontmatter-schema.md`
- `skills/doc-guardian/references/directory-layout.md`
- `skills/doc-guardian/references/change-log-format.md`
- `skills/_shared/dev_workflow/schema.py`
- `skills/_shared/dev_workflow/frontmatter.py`

Implement classes 1-7 from `docs/implementation/task6_plan_20260507.md`:

| Class | Name | Phase 3 expectation |
|-------|------|---------------------|
| 1 | Path | Use schema path templates and source-analysis mappings. |
| 2 | Naming | Enforce lowercase underscore normal docs and `CR-NNN.md` / `BUG-NNN.md` / `INCIDENT-NNN.md`. |
| 3 | Frontmatter Schema | Universal fields plus per-type required fields; nullable fields must exist when required. |
| 4 | Frontmatter Format | Timestamps, release string, owner format, IDs, enums, bools, counts. |
| 5 | Cross-Reference | Validate path refs and ID refs that can be checked locally. |
| 6 | Change Log Discipline | Delegate to `changelog.py validate` logic for incremental docs. |
| 7 | ID Uniqueness | Implement `validate.py ids` and reuse for single-file where practical. |

Recommended CLI shape:

```bash
python3 skills/doc-guardian/scripts/validate.py file <doc-path> [--root <root>]
python3 skills/doc-guardian/scripts/validate.py ids [--root <root>]
python3 skills/doc-guardian/scripts/validate.py --help
```

If `validate.py all` or `validate.py consistency` is exposed in help, it may be marked as deferred or return a clear non-zero "not implemented in Phase 3" unless implemented safely.

---

## 6. Shared Modules To Reuse

Use these instead of duplicating logic:

- `skills._shared.dev_workflow.frontmatter`
  - `read_markdown`
  - `render_markdown`
  - `parse_frontmatter`
  - `split_frontmatter`
- `skills._shared.dev_workflow.markdown`
  - `find_section`
  - `require_section`
  - `replace_section_body`
  - `non_comment_lines`
- `skills._shared.dev_workflow.atomic`
  - `atomic_write_text`
  - `transaction`
- `skills._shared.dev_workflow.schema`
  - incremental/snapshot doc type sets
  - required fields
  - path templates
  - status and enum constants

If a shared helper is missing, add it in the shared package with tests instead of embedding duplicate behavior inside scripts.

---

## 7. Testing Strategy For Phase 3

Use `unittest`:

```bash
python3 -m unittest discover -s tests
python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
```

Add tests that cover:

- `changelog.py promote` happy path for an incremental doc.
- `changelog.py promote` no-op or safe behavior for a snapshot doc.
- `changelog.py validate` rejects non-empty Pending Changes after promote is expected.
- malformed timestamp / malformed section ref / malformed Change Log heading.
- Change Log date group descending sort and per-date timestamp ascending sort.
- `validate.py file` accepts a representative valid incremental doc.
- `validate.py file` accepts a representative valid snapshot doc without Change Log sections.
- path mismatch rejects.
- missing universal field rejects.
- missing per-type required field rejects.
- `release: 0.1` parsed as float rejects; `release: "0.1"` accepts.
- bad owner format rejects.
- bad BUG / CR / INCIDENT ID rejects.
- `triggered_by_bug` as path rejects; `BUG-007` style accepts when present.
- `test-report.total_test_cases` must equal `passed + failed + skipped` (if `skipped` present) or `passed + failed`.
- `test-review-report` / `code-review-report` pending is allowed but does not imply pass.

Keep tests in temporary directories. Do not validate this repo's historical design/handoff docs as managed-project docs.

---

## 8. Known Watch Points

- `schema.py` has `SOURCE_ANALYSIS_PATHS` separate from `TYPE_PATHS`. `validate.py file` must explicitly handle `type: source-system-analysis` via `analysis_kind`.
- Optional PRD supporting docs such as competitor / market / non-goals have only universal required fields unless references say otherwise.
- Gated `approved` status is valid only for PRD / SRS / Architecture / CR.
- `status_transition.py` will later own frontmatter status mutation. Phase 3 validation should enforce status validity but should not mutate statuses.
- `AtomicTransaction` backup cleanup deletes temp backups even if rollback partially fails. This was accepted for personal single-process use.
- Protected task transitions in `progress_state.py` require caller-side preconditions before `allow_protected=True`; this is Phase 5/6 work.

---

## 9. Recommended Phase 3 Work Order

1. Re-run existing tests and compileall to confirm baseline.
2. Read `change-log-format.md` and implement pure in-memory Change Log parse/promote helpers.
3. Add `skills/doc-guardian/scripts/changelog.py` CLI wrapper.
4. Add `tests/test_changelog.py`.
5. Read `frontmatter-schema.md` and `directory-layout.md` deeply.
6. Implement `validate.py file` checks classes 1-6.
7. Implement `validate.py ids` / Class 7.
8. Add `tests/test_validate_file.py`.
9. Run full tests + compileall.
10. Create a Claude review prompt for Phase 3 and ask Claude to save the review report before Phase 4.

---

