# Task 6 Phase 3 Round 2 Review — changelog.py + validate.py Regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Round 2 fixes for Phase 3 `changelog.py` + `validate.py file/ids` only  
**Baseline**: `docs/review/task6_phase3_changelog_validate_review_20260507.md`  
**Recommendation**: **(A) accept regression and proceed to Phase 4 (`status_transition.py`)** — Round 1 blocking findings are fixed; new residual finding is Low and non-blocking.

Validation performed:

```bash
python3 -m unittest discover -s tests
# Ran 112 tests in 0.120s
# OK

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK
```

---

## 1. Round 1 Findings 回归状态

| Round 1 Finding | Status | Regression Review Notes |
|-----------------|--------|-------------------------|
| **H1 — Class 5 path references accept null / absolute / out-of-root paths** | ✅ Fixed | `validate.py` now routes only required path-reference fields (`acceptance-plan.related_srs`, `architecture-delta.parent_architecture`, `cr.affected_doc`) through `_validate_path_reference()`. It rejects null, non-string, empty string, backslash paths, POSIX/Windows absolutes, `.` / `..` / empty segments, symlink/root escapes, and missing files. It does not false-trigger on unrelated doc types. BUG ID lookup remains separate and correct. |
| **M1 — CR `target_release` is present-only, not format-validated** | ✅ Fixed | `check_class_4_format()` now has a CR-specific branch requiring `target_release` to be non-null, a YAML string, and `^\d+\.\d+$`. This stays distinct from `bug-report.target_release`, which remains nullable per schema. Null, float, malformed string, and quoted happy path are covered. |
| **M2 — Change Log raw-line strictness + empty-pending malformed log bypass** | ✅ Fixed for blocking scope | `parse_changelog_section()` no longer strips before validation, rejects indented headings/entries, rejects missing blank line between date groups, handles comments with strict trailing-content checks, and `promote_text()` now parses existing Change Log even when Pending Changes is empty. See New Low L1 for one non-blocking canonical-layout nuance around blank lines after headings. |
| **M3 — Pending Changes inline comment trailing text hidden** | ✅ Fixed | `parse_pending_section()` no longer uses the permissive `markdown.non_comment_lines()` helper. `_classify_comment_line()` rejects inline comment tails and multi-line close tails, and unclosed blocks raise `ChangelogError`. Regression tests cover inline tail, hidden entry after comment, and multi-line close tail. |
| **L1 — `title` must be non-empty string** | ✅ Fixed | Class 4 checks present `title` values for `str` and non-empty after `.strip()`. Missing title still only reports Class 3 missing, avoiding double-report noise. |
| **L2 — `validate.py ids` accepts wrong prefix in ID dirs** | ✅ Fixed | `check_ids_uniqueness()` now uses per-directory prefixes (`CR`, `BUG`, `INCIDENT`) and skips malformed/misplaced files from `seen`, so wrong-prefix files do not distort uniqueness tracking. Tests cover CR-in-bug, BUG-in-cr, and INCIDENT-in-bug. |

**Regression conclusion**: 6/6 Round 1 findings are closed for Phase 4 readiness. Blocking count is now **0 High / 0 Medium**.

---

## 2. New Findings (Round 2)

### Low

#### L1 — Change Log validation still accepts a date heading immediately followed by an entry

- **Location**: `skills/_shared/dev_workflow/changelog.py:168`, `skills/_shared/dev_workflow/changelog.py:188`
- **Issue**: The Round 2 state machine enforces a blank line before a subsequent date heading, but it does not enforce the canonical `### YYYY-MM-DD` + blank line + entries layout rendered by `render_changelog_body()`. A hand-edited Change Log like `### 2026-05-15\n- 2026-05-15T10:00:00Z [Section 1]: ok` currently validates.
- **Impact**: Low. The explicit strictness bullet in `change-log-format.md` §3.3 requires blank lines between date blocks, which is now enforced; Phase 4-generated entries will use `render_changelog_body()` and therefore remain canonical. This is only a residual direct-edit layout permissiveness if §3.1 is interpreted literally as requiring a blank line after each date heading.
- **Recommendation**: Optional before or during Phase 4: when the previous non-comment line is a heading, require a blank line before the first entry of that group, and add one regression test. If the intended policy is only “blank line between date groups,” add a one-sentence clarification to `change-log-format.md` later.

No new High or Medium findings were found.

---

## 3. Cross-Finding Consistency Check

| Area | Status | Notes |
|------|--------|-------|
| **Class 1 Path** | ✅ | Still uses `TYPE_PATHS` / `SOURCE_ANALYSIS_PATHS`; Round 2 did not regress path derivation. Missing render fields still produce “cannot derive expected path”. |
| **Class 2 Naming** | ✅ | Filename shape check remains unchanged and consistent with directory-layout. `./` / `..` in `doc_path` are still normalized by path resolution as previously accepted. |
| **Class 3 Frontmatter Schema** | ✅ | Universal + per-type required field presence and enum checks remain intact. Missing `title` is Class 3 only; present bad `title` is Class 4. |
| **Class 4 Frontmatter Format** | ✅ | `title`, timestamps, release, owner, ID fields, task IDs, SRS bools, report counts, review/report enums, bug-report nullable release fields, workflow-incident fields, and CR `target_release` now align with `frontmatter-schema.md`. |
| **Class 5 Cross-Reference** | ✅ | Required path refs are now strict project-root-relative forward-slash paths, must resolve under `root`, and must exist. `triggered_by_bug` remains a BUG ID lookup, not a path. |
| **Class 6 Change Log Discipline** | ✅⚠️ | Blocking bypasses are fixed: raw-line indentation, malformed existing Change Log on empty pending, comment trailing content, unclosed comments, date order, and timestamp order are handled. Residual Low L1 is only about optional enforcement of blank line after a date heading. |
| **Class 7 ID Uniqueness** | ✅ | Directory-specific ID prefixes align with `directory-layout.md` §2.6 / §3.1; wrong-prefix files are rejected and not counted as valid stems. |
| **Deferred Class 8 / all / consistency** | ✅ | Still correctly deferred to Phase 5/6 with exit 2; no accidental Phase 4+ implementation introduced. |

Cross-doc reference check:

| Reference | Status | Notes |
|-----------|--------|-------|
| `change-log-format.md` §2.3 | ✅ | Pending Changes comment-only semantics are now strict; trailing content after `-->` is rejected. |
| `change-log-format.md` §3.1 / §3.3 | ✅⚠️ | Date heading regex, entry regex, group separation, and render layout are aligned. Optional nuance: validation does not require a blank line after each date heading (L1). |
| `frontmatter-schema.md` §1 | ✅ | `title` non-empty string is enforced when present; missing title remains Class 3. |
| `frontmatter-schema.md` §3.4 / §4.2 | ✅ | CR `target_release` is non-null quoted release string; bug-report nullable release fields remain nullable. |
| `frontmatter-schema.md` §4.5 | ✅ | Path refs are forward-slash, project-root-relative, non-null, existing files. Implementation also rejects `.` / `..`, backslashes, absolutes, empty segments, and root escapes. |
| `directory-layout.md` §2.6 / §3.1 | ✅ | `ids` now enforces CR only in `docs/cr`, BUG only in `docs/bug`, INCIDENT only in `docs/incident`. |
| `doc-guardian/SKILL.md` §5 | ✅ | The 8-class description remains aligned. No SKILL.md patch is required for the Round 2 fixes; its Class 7 wording is already per-directory rather than cross-directory global uniqueness. |

---

## 4. Round 2 Implementation Quality Spot-checks

### `_classify_comment_line()`

- ✅ Correctly distinguishes normal non-comment lines from single-line comments and multi-line comment blocks.
- ✅ Rejects `<!-- a --> b` and `--> b` with actionable context-specific errors.
- ✅ Accepts pure comments (`<!-- a -->`, multi-line blocks) and reports unclosed comment blocks through callers.
- ⚠️ Minor polish: `residual_kind` is mostly documentary; callers ignore all values except the conceptual `non_comment` branch. This is harmless, but could be simplified if touched later.

### `parse_changelog_section()` / `last_kind` state machine

- ✅ First non-comment line as entry raises “entry before heading”.
- ✅ First non-comment line as heading is accepted.
- ✅ Comments before a heading or between groups are accepted; comment then heading works because `last_kind=comment`.
- ✅ Indented headings and entries are rejected before regex matching.
- ✅ Missing blank line between groups (`entry` immediately followed by `### date`) is rejected.
- ⚠️ Low L1: heading immediately followed by first entry is accepted; decide whether §3.1 requires rejecting it.

### `_validate_path_reference()`

- ✅ Null, non-string, empty, backslash, POSIX absolute, Windows-drive absolute, `.` / `..` / empty segments, missing files, and symlink/root escape paths are rejected.
- ✅ Uses `root.resolve()` and compares resolved targets via `relative_to(root_resolved)`, so a symlink inside the project pointing outside is rejected.
- ✅ The strict path-ref check is scoped to doc types where the field is required, avoiding false positives on unrelated/extra fields.
- ✅ Error messages include field names and rejected values or remediation hints.

### Per-directory IDs regex

- ✅ Uses `(cr, CR)`, `(bug, BUG)`, `(incident, INCIDENT)` mapping and builds per-directory regexes.
- ✅ Wrong-prefix files produce `Class 7 (IDs)` and are skipped from `seen`, preventing malformed files from perturbing uniqueness checks.
- ✅ Existing happy path for clean BUG files still passes.
- ℹ️ True duplicate stems within a single POSIX directory cannot be created as two separate files; keeping duplicate-stem logic is harmless defensive code.

---

## 5. Checklist Results

| Module / Area | Status | Notes |
|---------------|--------|-------|
| `skills/_shared/dev_workflow/changelog.py` | ✅⚠️ | M2/M3 blockers fixed; helper remains pure in-memory and suitable for Phase 4 `status_transition.py`. Low L1 is optional layout strictness. |
| `skills/doc-guardian/scripts/changelog.py` | ✅ | CLI behavior unchanged and still correct: `validate` read-only, `promote` writes atomically only after in-memory promote, post-validates, 0/1/2 contract intact. |
| `skills/doc-guardian/scripts/validate.py` | ✅ | H1/M1/L1/L2 fixes are localized, actionable, and preserve deferred `all` / `consistency` behavior. |
| `tests/test_changelog.py` | ✅ | New M2/M3 regression tests are readable and isolated. They cover indented heading/entry, missing blank line between groups, empty-pending malformed Change Log, inline comment tail, hidden entry tail, and multi-line close tail. Optional gap: add explicit unclosed-comment test. |
| `tests/test_validate_file.py` | ✅ | New H1/M1/L1/L2 tests use temp dirs, assert specific error fragments, and do not mutate real repo docs/skills. Optional gap: add non-string/empty path-ref tests if desired; code paths were spot-checked manually. |
| CLI help / exit codes | ✅ | `validate.py all` / `consistency` still exit 2 with deferred message; validation failures are exit 1; successful paths are exit 0. |
| Phase boundaries | ✅ | No `status_transition.py`, `progress.py`, `validate.py all`, or `validate.py consistency` implementation slipped into Phase 3. |

---

## 6. Open Questions / Assumptions

1. **Blank line after date heading**: I treat this as a Low optional strictness issue because `change-log-format.md` §3.3 explicitly requires blank lines between date blocks, while §3.1 shows (but does not separately bullet) a blank line after each heading. If the intended policy is exact §3.1 rendering, add the small validation check before Phase 4; otherwise clarify the reference later.
2. **Comment lines in Change Log**: Round 2 implementation allows pure comments in Change Log, not just Pending Changes. This is stricter than before for trailing content and appears harmless; if comments in Change Log are not desired, add a future spec clarification and reject them.
3. **`ids` scope**: I assume Class 7 standalone `ids` is per-directory only, consistent with SKILL.md (“`docs/cr/` 下 CR-NNN 不重复…”). Cross-directory ID uniqueness is not required and should not be added without a spec change.

---

## 7. Recommendation

**(A) accept regression and proceed to Phase 4 (`status_transition.py`)**.

Reasons:

- All Round 1 blocking findings are fixed: **H1/M1/M2/M3 = closed**.
- The two Round 1 Low findings are also fixed: **L1/L2 = closed**.
- Full tests and compile checks pass: **112 tests OK**, compileall OK.
- No new High or Medium issues were found.
- The only new/residual issue is Low and does not undermine Phase 4 transactions because Phase 4 will generate Change Log bodies through the canonical renderer.

Optional cleanup before or during Phase 4:

1. Enforce or explicitly document whether a blank line is required between `### YYYY-MM-DD` and the first entry in that date group.
2. Add tests for path-reference non-string / empty values and unclosed Pending/Change Log HTML comment blocks, even though code already handles them.
3. Simplify `_classify_comment_line()` return shape if future edits touch it; current behavior is correct.
