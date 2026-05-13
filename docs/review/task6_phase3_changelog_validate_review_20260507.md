# Task 6 Phase 3 Review — changelog.py + validate.py file/ids

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Phase 3 only — `skills/_shared/dev_workflow/changelog.py`, `skills/doc-guardian/scripts/changelog.py`, `skills/doc-guardian/scripts/validate.py`, `tests/test_changelog.py`, `tests/test_validate_file.py`  
**Recommendation**: **(B) fix before Phase 4** — implementation is close, but Class 5 cross-reference enforcement and several Change Log strictness checks still allow spec-bypassing documents to validate.

---

## 1. Executive Summary

Phase 3 is structurally sound: the shared Change Log helper is in-memory, both CLIs bootstrap correctly, `--root` behavior is clear, `validate.py all` / `consistency` are properly deferred with exit 2, and the test suite is isolated in temp dirs.

Validation performed during review:

```bash
python3 -m unittest discover -s tests
# Ran 91 tests in 0.092s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK

python3 skills/doc-guardian/scripts/validate.py --help
python3 skills/doc-guardian/scripts/changelog.py --help
# both OK
```

Findings distribution:

| Severity | Count | Blocks Phase 4? | Summary |
|----------|-------|-----------------|---------|
| High | 1 | Yes | Required path references can be null or point outside the project and still pass Class 5. |
| Medium | 3 | Yes | CR `target_release` is unvalidated; Change Log strictness can be bypassed; Pending Changes comment filtering can hide content. |
| Low | 2 | No | `title` non-empty string is not enforced; `ids` filename checks are not directory-prefix-specific. |

Overall judgment: **do not proceed to Phase 4 until H1 + M1-M3 are fixed**. These are local Phase 3 fixes, not design rework; expected repair size is modest.

---

## 2. Findings

### High

#### H1 — Class 5 path references accept null values and absolute/out-of-root paths

- **Location**: `skills/doc-guardian/scripts/validate.py:419`, `skills/doc-guardian/scripts/validate.py:423`, `skills/doc-guardian/scripts/validate.py:430`
- **Issue**: `check_class_5_cross_reference()` skips `None` for `affected_doc` / `parent_architecture` / `related_srs`, and resolves arbitrary strings with `(root / value).resolve()` without requiring a relative project-root path. As a result, required path-reference fields can be `null`, absolute paths such as `/etc/passwd`, or traversal paths that escape `--root`, and they pass if the resolved file exists.
- **Impact**: This violates `frontmatter-schema.md` §4.5 and the prompt Class 5 requirement that `affected_doc` / `parent_architecture` / `related_srs` are real project-relative file references. It lets `validate.py file` certify CRs, architecture deltas, or acceptance plans whose required references are absent or outside the managed project.
- **Evidence**: Focused spot checks showed both of these return `[]` from `validate_file(...)`: `acceptance-plan` with `related_srs: null`, and `cr` with `affected_doc: /etc/passwd`.
- **Recommendation**: For these path-reference fields, reject `None`, non-string, empty string, absolute paths, backslashes, `.` / `..` segments, and any resolved target not under `root`. Then require the target to exist. Add tests for `related_srs: null`, `affected_doc: /etc/passwd`, and `parent_architecture: ../...`.

### Medium

#### M1 — CR `target_release` is present-only, not format-validated

- **Location**: `skills/doc-guardian/scripts/validate.py:201`, `skills/doc-guardian/scripts/validate.py:368`
- **Issue**: Class 4 validates a field literally named `release`, and has special release checks for bug-report fields, but it never validates `cr.target_release`. Class 3 only checks that the key exists. A CR with `target_release: null`, `target_release: 0.2` (YAML float), or `target_release: abc` can pass if the rest of the document is valid.
- **Impact**: This breaks `frontmatter-schema.md` §3.4 / §4.2, which requires CR `target_release` to be a non-null quoted release string. It also leaves a release-string bypass that Phase 3 explicitly defends for other release fields.
- **Evidence**: Focused spot checks showed `validate_file('docs/cr/CR-001.md', root)` returns `[]` for `target_release` values `None`, `0.2`, and `abc` when `affected_doc` exists.
- **Recommendation**: Add a CR-specific Class 4 branch requiring `target_release` to be `str` and match `^\d+\.\d+$`; reject `None` and non-strings with the same quoted-YAML guidance used for `release`. Add tests for null, float, malformed string, and happy path.

#### M2 — Change Log parser weakens strict line-level format and promote can no-op over malformed existing logs

- **Location**: `skills/_shared/dev_workflow/changelog.py:83`, `skills/_shared/dev_workflow/changelog.py:88`, `skills/_shared/dev_workflow/changelog.py:98`, `skills/_shared/dev_workflow/changelog.py:169`
- **Issue**: `parse_changelog_section()` applies `raw_line.strip()` before matching headings and entries, so an indented `  ### 2026-05-15` or `  - 2026-05-15T...` passes despite the spec's anchored regexes. It also ignores blank-line structure, so headings and entries without the required blank line pass. Separately, `promote_text()` returns immediately when Pending Changes is empty, before parsing the existing Change Log; this contradicts its own docstring and the review prompt requirement that malformed Change Log entries/headings raise `ChangelogError`.
- **Impact**: `validate_text()` and `validate.py` Class 6 do not strictly enforce `change-log-format.md` §3.1 / §3.3. Directly edited Change Log content can be outside the literal format and still validate, weakening the main Phase 3 anti-bypass gate.
- **Evidence**: Focused spot checks showed `validate_text(...) == []` for both an indented date heading and an indented entry. A document with empty Pending Changes and malformed existing Change Log also returns success from `promote_text()` as a no-op.
- **Recommendation**: Match headings and entries against raw lines, not stripped lines; only allow blank lines where the spec requires them. Parse/validate the existing Change Log whenever both sections are present, even when Pending Changes is empty. Add tests for indented headings, indented entries, missing blank-line spacing, and empty-pending/malformed-changelog `promote_text()`.

#### M3 — Pending Changes treats lines starting with an HTML comment as fully ignorable even when trailing content exists

- **Location**: `skills/_shared/dev_workflow/changelog.py:68`, `skills/_shared/dev_workflow/changelog.py:72`
- **Issue**: `parse_pending_section()` delegates to `markdown.non_comment_lines()`. That helper skips any line starting with `<!--`; if the same line contains closing `-->` plus trailing text, the trailing text is also skipped. Therefore `<!-- c --> - 2026-05-15T10:00:00Z [Section 1]: hidden` is considered comment-only instead of non-comment content.
- **Impact**: `validate_text()` can report an incremental doc as clean even though `## Pending Changes` contains non-comment text. This violates `change-log-format.md` §2.3 and the prompt's Class 6 rule that Pending Changes is valid only when it has no non-comment entries.
- **Evidence**: Focused spot checks showed `validate_text(...) == []` for pending bodies `<!-- c --> trailing text` and `<!-- c --> - 2026-05-15T10:00:00Z [Section 1]: hidden`.
- **Recommendation**: Add pending-specific strict comment handling in `changelog.py` or tighten `non_comment_lines()` so content after a comment close on the same line is preserved/rejected. Add tests for single-line comment with trailing text and multi-line close with trailing text.

### Low

#### L1 — Universal `title` is not checked as a non-empty string

- **Location**: `skills/doc-guardian/scripts/validate.py:147`, `skills/doc-guardian/scripts/validate.py:182`
- **Issue**: Class 3 confirms `title` exists, but Class 4 never checks type or non-emptiness. `title: ""` and `title: 123` can pass.
- **Impact**: This is a schema strictness gap against `frontmatter-schema.md` §1. It is not likely to break Phase 4 mechanics, but it means `validate.py file` is not fully enforcing universal fields.
- **Recommendation**: Add a simple Class 4 universal check: `title` must be `str` and `title.strip()` non-empty. Add two negative tests.

#### L2 — `validate.py ids` does not enforce directory-specific ID prefixes

- **Location**: `skills/doc-guardian/scripts/validate.py:478`, `skills/doc-guardian/scripts/validate.py:488`
- **Issue**: `check_ids_uniqueness()` accepts any `^(CR|BUG|INCIDENT)-\d{3}\.md$` filename in all three directories. For example, `docs/bug/CR-001.md` is accepted by `ids`, even though `directory-layout.md` says `docs/bug/` contains `BUG-NNN.md` files.
- **Impact**: `validate.py file` would catch a correctly-frontmattered misplaced bug via Class 1, so this is not a primary bypass when all files are validated. However, the standalone `ids` subcommand is weaker than its directory-specific contract.
- **Recommendation**: Use per-directory regexes (`CR-` only under `docs/cr`, `BUG-` only under `docs/bug`, `INCIDENT-` only under `docs/incident`). Add tests for wrong-prefix-in-directory and keep the cross-directory non-interference test.

---

## 3. Cross-Doc Consistency Check

| Reference | Status | Notes |
|-----------|--------|-------|
| `change-log-format.md` §1 | ✓ | Incremental vs snapshot type classification matches `schema.py` and Phase 3 behavior. Snapshot docs without sections pass; snapshot docs with both sections can promote. |
| `change-log-format.md` §2.2 | ⚠️ | Entry regex itself is correct, but Change Log validation applies it after stripping whitespace; Pending comment handling can hide trailing content (M2, M3). |
| `change-log-format.md` §3 | ⚠️ | Date heading regex is correct, merge/render sorting is correct, but validation does not enforce raw line anchoring or blank-line layout (M2). |
| `change-log-format.md` §4 | ⚠️ | Promote merge/sort/clear behavior is correct when pending entries exist; empty-pending no-op skips malformed existing Change Log despite docstring/prompt expectations (M2). |
| `change-log-format.md` §5 / §8 | ⚠️ | Class 6 catches many malformed entries, date ordering, and timestamp ordering; strictness gaps remain for whitespace/comment bypasses. |
| `frontmatter-schema.md` §1 | ⚠️ | Universal field presence is checked, but `title` non-empty string is not enforced (L1). |
| `frontmatter-schema.md` §3-§4 | ⚠️ | Most enum/format rules are implemented; CR `target_release` is missing validation (M1). |
| `frontmatter-schema.md` §4.5 | ❌ | Path reference fields do not enforce non-null project-relative paths and can escape `--root` (H1). |
| `frontmatter-schema.md` §4.6 | ✓ | `workflow-incident.triggered_by_bug` is treated as a BUG ID and resolved to `docs/bug/{value}.md`. |
| `directory-layout.md` §2 | ✓ | Type-to-path templates, source-system-analysis path selection, ID path rendering, and project-level hard-coded paths are aligned. |
| `directory-layout.md` §3 | ⚠️ | Class 2 filename shape is implemented; `./` / `..` in doc paths are intentionally normalized as noted in the prompt. `ids` lacks directory-specific ID prefixes (L2). |
| `doc-guardian/SKILL.md` §5 | ⚠️ | Classes 1-7 exist and report actionable messages. Class 5 and parts of Class 6 are not strict enough (H1, M2, M3). |
| `doc-guardian/SKILL.md` §6 | ⚠️ | CLI surface and promote/validate flow exist. Promote's no-op path should still reject malformed existing Change Log if sections are present (M2). |
| `task6_plan_20260507.md` §7 | ⚠️ | `validate.py file` and `ids` are implemented; Class 5 and CR release validation need fixes. `all` / `consistency` deferral is acceptable for Phase 3. |
| `task6_plan_20260507.md` §8 | ⚠️ | Promote/validate core algorithm is mostly implemented; strict line-level validation and empty-pending malformed-log behavior need fixes. |

---

## 4. Checklist Results

### A. Shared `changelog.py`

| Check | Result | Notes |
|-------|--------|-------|
| Pure in-memory APIs | ✓ | `parse_*`, `merge_groups`, `render_changelog_body`, `promote_text`, and `validate_text` perform no file I/O. |
| Entry regex literal | ✓ | `_ENTRY_RE` matches the required timestamp / section_ref / non-empty summary pattern. |
| Date heading regex | ✓ | `_DATE_HEADING_RE` is anchored to `### YYYY-MM-DD`. |
| Raw strictness | ⚠️ | Change Log matching happens after `strip()`, so line anchors are weakened (M2). |
| Unknown type / missing incremental sections | ✓ | `promote_text()` rejects unknown doc type and missing sections for incremental docs. |
| Invalid pending entry | ✓ | Invalid Pending Changes entries raise `ChangelogError`. |
| Invalid existing Change Log | ⚠️ | Raises when pending entries exist; skipped when pending is empty (M2). |
| Snapshot behavior | ✓ | Snapshot without sections no-ops; snapshot with both sections promotes. One-section snapshot cases no-op rather than strict-validate. |
| Merge/sort/render | ✓ | Same-date merge, date-desc group sort, timestamp-asc entry sort, and renderer layout are correct. |
| `validate_text` standalone | ✓ | Works independently of promote; snapshot missing sections pass; incremental missing sections report clear issues. |
| Monotonicity checks | ✓ | Date groups reject equal/ascending dates; entries are compared pairwise for ascending timestamp order. |
| Bypass defense | ⚠️ | Whitespace-stripped Change Log lines and comment-with-trailing-text Pending lines can pass (M2, M3). |

### B. CLI `skills/doc-guardian/scripts/changelog.py`

| Check | Result | Notes |
|-------|--------|-------|
| `--root` default and path resolution | ✓ | Defaults to cwd; relative docs resolve under root; absolute docs are used directly. |
| `validate` no mutation | ✓ | Reads and reports issues without writing. |
| `promote` atomic write | ✓ | Uses in-memory `promote_text()` and `atomic_write_text()`, then post-validates written content. |
| Pending empty no-op | ✓/⚠️ | Correctly does not write, but also skips malformed existing Change Log detection (M2). |
| Failure exit codes | ✓ | Validation/promote failures return 1; usage/deferred paths return 2. |
| Help/import bootstrap | ✓ | `parents[3]` works for current layout; `__file__.resolve()` is symlink-friendly. |

### C. CLI `skills/doc-guardian/scripts/validate.py`

| Class | Result | Notes |
|-------|--------|-------|
| 1 Path | ✓ | Uses `TYPE_PATHS` / `SOURCE_ANALYSIS_PATHS`; missing render fields produce “cannot derive expected path”. |
| 2 Naming | ✓ | Filename shape checks align with prompt; path-style normalization is as expected. |
| 3 Frontmatter Schema | ✓/⚠️ | Required field presence and enums are mostly correct; `title` value is not checked (L1). |
| 4 Frontmatter Format | ⚠️ | Timestamp, release, owner, IDs, bools, review/test report invariants, workflow incident, bug-report fields mostly pass; CR `target_release` is missing (M1). |
| 5 Cross-Reference | ❌ | Path references accept null/out-of-root absolute paths (H1). BUG ID lookup is correct. |
| 6 Change Log Discipline | ⚠️ | Delegates correctly, but inherits M2/M3 strictness gaps. Snapshot missing sections pass. |
| 7 ID Uniqueness | ✓/⚠️ | Single-file filename-vs-ID check works; `ids` bad-filename check is not directory-prefix-specific (L2). |
| Deferred subcommands | ✓ | `all` and `consistency` return exit 2 with Phase 5/6 deferred message. |

### D. Tests

| Area | Result | Notes |
|------|--------|-------|
| Isolation | ✓ | Tests use `tempfile.TemporaryDirectory()` and do not mutate real repo `docs/` / `skills/`. |
| Changelog coverage | ✓/⚠️ | Happy paths, sort/merge, invalid timestamp/section_ref, missing sections, unknown type, comments, CLI integration are covered. Missing cases for M2/M3. |
| Validate happy paths | ✓ | PRD, SRS, code-review pass/pending, test-report skipped, workflow-incident, bug-report null fields, source-system-analysis prd/srs, snapshot test-preparation covered. |
| Class reject cases | ✓/⚠️ | Classes 1-7 have representative rejects, but not H1/M1/L1/L2 edge cases. |
| IDs tests | ⚠️ | Unique/bad filename/cross-dir non-interference covered; wrong-prefix-in-directory not covered. |
| CLI integration | ✓ | file pass/fail, ids pass, all-deferred, changelog promote/validate pass/fail covered. |

### E. Cross-Doc Consistency

- ⚠️ Mostly aligned, with explicit deviations listed in section 3.
- ❌ Class 5 path reference behavior is the largest reference mismatch.
- ⚠️ Change Log strictness is close but too permissive at raw-line/comment boundaries.

### F. Design / Maintainability

| Check | Result | Notes |
|-------|--------|-------|
| Shared API for Phase 4 | ✓ | `promote_text(content) -> (new_content, promoted_entries)` is a good fit for status-transition multi-doc transactions. |
| CLI `--root` design | ✓ | Simple and test-friendly. |
| Symlink-safe repo bootstrap | ✓ | `Path(__file__).resolve().parents[3]` should resolve back to the original skill repo under `.claude/skills` / `.agents/skills` symlinks. |
| Exit code contract | ✓ | 0/1/2 contract is clear. |
| Import ordering / `noqa: E402` | ✓ | Reasonable for script bootstrap. |

### G. Phase Boundary Compliance

| Check | Result | Notes |
|-------|--------|-------|
| No repo-root `progress.md` mutation | ✓ | No scripts/tests create or edit root progress files. |
| No Phase 4/5/6 implementation | ✓ | `status_transition.py` / `progress.py` not implemented; `all` / `consistency` deferred. |
| Event whitelist unaffected | ✓ | No `progress.py update --event` work in Phase 3. |
| `bug-rework` unaffected | ✓ | Not implemented in Phase 3, correctly out of scope. |

---

## 5. Open Questions / Assumptions

1. **Source-system-analysis `feature-matrix` release null**: `frontmatter-schema.md` has one sentence saying `release: null` is PRD-level only, but the table lists `feature-matrix` as project-level with `release: null`. The implementation allows null for both `prd-level` and `feature-matrix`. I treated the table + directory layout as authoritative and did not count this as a finding.
2. **HTML comment trailing content**: I treated content after `-->` on the same line as non-comment content that must be rejected, because `change-log-format.md` §2.3 only allows blank lines and HTML comments. If the intended behavior is to ignore same-line trailing text, the reference should explicitly say so; otherwise M3 should be fixed.
3. **`ids` uniqueness semantics**: A true duplicate filename stem cannot exist twice in the same POSIX directory, so `ids` is necessarily more useful as a naming/prefix scan unless it parses frontmatter. I did not require frontmatter parsing for `ids` because the Phase 3 prompt frames single-file filename-vs-ID checks separately.

---

## 6. Recommendation

**(B) fix before Phase 4**.

Must fix before Phase 4:

1. **H1** — tighten Class 5 path references so required path refs are non-null, project-relative, in-root, and existing. Estimated fix: 25-40 LOC + 3-5 tests.
2. **M1** — validate CR `target_release` as a non-null quoted release string. Estimated fix: 10-15 LOC + 3-4 tests.
3. **M2** — make Change Log validation raw-line strict and parse existing Change Log even when Pending Changes is empty. Estimated fix: 30-60 LOC + 4-6 tests.
4. **M3** — reject Pending Changes lines where an HTML comment shares a line with trailing non-comment content. Estimated fix: 15-30 LOC + 2-3 tests.

Can defer to Phase 5/6/7 or fold into the above cleanup:

1. **L1** — enforce `title` as non-empty string. Estimated fix: 5-10 LOC + 2 tests.
2. **L2** — make `ids` directory-prefix checks specific to `cr` / `bug` / `incident`. Estimated fix: 10-20 LOC + 2 tests.

Why Phase 4 should wait: Phase 4 `status_transition.py` will rely on the Phase 3 Change Log in-memory API and `validate.py file` as its post-mutation gate. Proceeding while Class 5 and Class 6 can certify spec-bypassing documents would make Phase 4's all-or-nothing transaction appear valid even when referenced artifacts or Change Log discipline are not actually compliant.

No architecture revisit is needed. These are localized validation strictness fixes within the existing Phase 3 design.
