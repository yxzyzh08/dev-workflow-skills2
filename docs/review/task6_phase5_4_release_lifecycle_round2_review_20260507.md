# Task 6 Phase 5.4 Round 2 Review — release lifecycle regression

**Review Date**: 2026-05-07  
**Reviewer**: Codex (GPT-5)  
**Scope**: Regression review for Round 2 fixes to Phase 5.4 `release-close` / `release-start` / `bug-intake`, focused on Round 1 M1 BUG path safety and L1 release-start canonical summary tokens.  
**Recommendation**: **(A) accept regression and proceed to Phase 6** — both Round 1 findings are fixed, the new regression coverage is strong, and no new blocking issue was found.

---

## 1. Executive Summary

Round 2 closes the Phase 5.4 blockers without expanding into Phase 6 implementation. BUG paths are now validated at the state-machine/replay layer and again at release-start fan-out time, and `release-start` history summaries now include summary-local `version=` and `scenario=` tokens.

Findings distribution for this review:

| Severity | Count | Blocks Phase 6? | Summary |
|----------|-------|-----------------|---------|
| High | 0 | No | No data-loss, root-escape, or transaction regression found. |
| Medium | 0 | No | Round 1 M1 is fixed. |
| Low | 0 | No | Round 1 L1 is fixed; no new Low finding raised. |

Validation performed during review:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests
# Ran 468 tests in 3.759s
# OK

TMPPYCACHE=$(mktemp -d)
PYTHONPYCACHEPREFIX="$TMPPYCACHE" python3 -m compileall -q \
  skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

PYTHONDONTWRITEBYTECODE=1 python3 skills/workflow-protocol/scripts/progress.py --help
# OK; subcommands remain init / query / recover / update / release-close / release-start / bug-intake

find . -maxdepth 3 \( -name 'progress.md' -o -name 'progress-history.md' \) -print
# no output
```

Additional spot checks:

- `_read_bug_for_release_start()` now rejects `/tmp/BUG-001.md`, `../etc/BUG-001.md`, and `docs/bug/BUG-1000.md` before reading or writing any BUG file.
- `apply_release_start(...).history_summary` now emits `version=0.2 scenario=S2-1 ...` directly in the summary.

---

## 2. Round 1 Findings 回归状态

| Round 1 Finding | Status | Evidence | Notes |
|-----------------|--------|----------|-------|
| M1 — `release-start` BUG fan-out trusted corrupted `unresolved_bugs` paths and could write outside `--root` | ✅ Fixed | `_BUG_PATH_RE` and `_validate_bug_path_shape()` were added at `skills/_shared/dev_workflow/progress_state.py:779`; `apply_bug_intake()` calls it at `skills/_shared/dev_workflow/progress_state.py:1076`; `_read_bug_for_release_start()` calls it and then enforces `relative_to(root.resolve())` at `skills/workflow-protocol/scripts/progress.py:709`-`skills/workflow-protocol/scripts/progress.py:722`. | This gives shared shape validation for forward/replay intake plus runtime containment defense for release-start fan-out. |
| L1 — `release-start` summary lacked canonical `version=` token | ✅ Fixed | `apply_release_start()` now builds summary as `version=<x.y> scenario=<S2-x> ...` at `skills/_shared/dev_workflow/progress_state.py:1019`; `tests/test_apply_release_start.py:143` asserts summary-only tokens. | Result still echoes version/scenario_subtype for readability and replay remains backward-compatible because `_kv_tokens()` reads summary + result. |

---

## 3. New Findings (Round 2)

No new findings.

I did not identify any new High, Medium, or Low defects introduced by the Round 2 changes. Optional naming/API polish is listed under Open Questions, but it does not block Phase 6.

---

## 4. Cross-Finding Consistency Check

| Area | Status | Notes |
|------|--------|-------|
| M1 path shape validation | ✅ | Empty/non-string, backslash, POSIX absolute, Windows drive, dot/dotdot/empty segments, wrong directory, and non-3-digit BUG IDs reject. |
| M1 release-start containment | ✅ | Fan-out re-resolves under `--root` and rejects paths that escape after symlink/race resolution. |
| M1 replay safety | ✅ | `bug-intake` replay delegates to `apply_bug_intake()`, so malformed `bug=` tokens reject before reaching `unresolved_bugs`. |
| L1 canonical summary | ✅ | `version=` and `scenario=` are now in `history_summary`, not only `history_result`. |
| Existing Phase 5.4 behavior | ✅ | Full suite passes; `_run_update_pipeline`, extra writes, update-event/task, recover, and progress history behavior remain intact. |
| Phase 6 boundary | ✅ | No Phase 6 `bug-*`, `incident-*`, `update --advance`, terminal-event, or consistency behavior is required or implemented in this round. |

---

## 5. Round 2 Implementation Quality Spot-checks

### 5.1 `_validate_bug_path_shape`

- Centralized shape check is intentionally strict: only `docs/bug/BUG-NNN.md` with a 3-digit zero-padded ID is accepted.
- Error messages distinguish absolute paths, backslash separators, dot/traversal segments, and pattern mismatches.
- The helper is called from `apply_bug_intake()`, so normal CLI intake and replayed `bug-intake` entries share the same state-machine guard.
- Unit tests cover the expected malformed path matrix and a canonical happy path.

### 5.2 `_read_bug_for_release_start` double defense

- Shape validation runs before filesystem resolution, so obviously malformed `unresolved_bugs` entries fail fast.
- Runtime containment uses `abs_bug.relative_to(root.resolve())`, so symlink/race-induced root escapes reject before BUG frontmatter reads or transaction writes.
- Shape errors are converted to `ProgressArtifactError`, which the existing extra-write factory path already maps to exit 1.
- CLI regression tests forge bad `unresolved_bugs` values and assert `progress.md` / `progress-history.md` are unchanged.

### 5.3 `release-start` summary

- Summary now includes `version=<x.y>` and `scenario=<S2-x>` in the header text itself.
- `history_result` retains `version=` / `scenario_subtype=` as a human-readable echo and backward-compatible replay source.
- Existing replay tests using the old prose summary plus result still pass, confirming `_kv_tokens()` compatibility.

### 5.4 Regression tests

- Round 2 adds 14 tests and the full suite now runs 468 tests OK.
- New unit tests cover 10 BUG path-shape cases.
- New replay tests cover absolute and traversal `bug=` tokens independently from CLI preflight.
- New CLI tests cover forged `progress.md unresolved_bugs` paths for traversal and absolute variants, with unchanged-file assertions.

---

## 6. Checklist Results

### A. M1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| Empty / non-string path rejected | ✓ | Existing and new `apply_bug_intake` tests cover this. |
| Backslash rejected | ✓ | Error mentions forward slashes. |
| POSIX absolute rejected | ✓ | Error mentions absolute path. |
| Windows drive rejected | ✓ | `C:/...` rejects as absolute. |
| `.` / `..` / empty segments rejected | ✓ | Dot and traversal tests are present; empty segments are covered by the same segment guard. |
| Wrong filename / ID width / parent dir rejected | ✓ | INCIDENT, 4-digit, 2-digit, and `docs/incident` cases covered. |
| Canonical path accepted | ✓ | `docs/bug/BUG-007.md` accepted. |
| `apply_bug_intake` calls shared shape guard | ✓ | Guard call is at `progress_state.py:1076`. |
| `_read_bug_for_release_start` shape + containment layers | ✓ | Shape guard plus `relative_to(root.resolve())` are present. |
| Error messages clear enough | ✓ | Messages include expected shape or specific cause plus actual value. |
| `_`-prefixed helper imported by CLI | ✓ / ⚠️ | Acceptable for shared internal package use; public naming could be considered later. |

### B. L1 fix 是否到位

| Check | Result | Notes |
|-------|--------|-------|
| `version=` in `history_summary` | ✓ | Summary begins with `version=<new_version>`. |
| `scenario=` in `history_summary` | ✓ | Summary includes `scenario=<scenario_subtype>`. |
| Summary-only test | ✓ | `tests/test_apply_release_start.py:143` inspects `outcome.history_summary` only. |
| Replay compatibility retained | ✓ | Existing replay tests still pass because `_kv_tokens()` reads summary + result. |

### C. 既有 invariant 是否保持

| Check | Result | Notes |
|-------|--------|-------|
| Prior Phase 5.4 Round 1 tests remain green | ✓ | Full suite now 468 tests OK. |
| Review-iteration guard and replay consistency inherited | ✓ | Round 2 did not alter `_run_update_pipeline` or the apply-function iter guards. |
| Untouched shared modules stay stable | ✓ | `progress_lock.py`, `progress_history.py`, and `progress_artifacts.py` were not part of the Round 2 fix. |
| Existing commands preserved | ✓ | Init/query/recover/update event/update task paths still pass existing tests. |
| Extra writes hook unchanged | ✓ | No regression observed in release-start fan-out or atomic path. |

### D. 测试质量

| Check | Result | Notes |
|-------|--------|-------|
| M1 unit tests cover malformed matrix | ✓ | 10 path-shape tests are present. |
| M1 replay tests cover non-CLI path | ✓ | Absolute and traversal `bug=` tokens reject in replay. |
| M1 CLI tests cover forged progress path | ✓ | Absolute and traversal `unresolved_bugs` reject in release-start. |
| Reject tests assert message tokens | ✓ | Assertions include `absolute`, `forward slashes`, `'.' or '..'`, `BUG-NNN.md`, or equivalent. |
| File unchanged assertions | ✓ | CLI forged-path tests assert progress/history unchanged; absolute variant asserts progress unchanged. |
| L1 summary-only assertion | ✓ | No result concatenation remains in the canonical-token test. |
| Temp-dir isolation | ✓ | New CLI/replay tests use temp-dir fixtures and scoped handler patches. |

### E. Cross-doc 一致性

| Check | Result | Notes |
|-------|--------|-------|
| `frontmatter-schema.md` BUG ID 3-digit rule | ✓ | `_BUG_PATH_RE` enforces `BUG-\d{3}.md`. |
| Release-start fan-out limited to managed BUG paths | ✓ | Shape + containment defenses ensure fan-out stays under `--root` and under `docs/bug`. |
| Bug-intake remains Phase 5.4 thin check | ✓ | Path shape/type/null fields are checked; full Class 1-7 remains deferred. |
| Canonical history token contract | ✓ | `release-start` has `version=` and `scenario=` in summary; `bug-intake` has `bug=` in summary. |

### F. 设计 / 可维护性

| Check | Result | Notes |
|-------|--------|-------|
| Shared helper reusable for Phase 6 | ✓ | Phase 6 `bug-start` / `bug-rework` can reuse the same BUG path policy. |
| Double defense cost acceptable | ✓ | String validation plus one resolve/relative check per consumed BUG is negligible. |
| Error class layering reasonable | ✓ | Shape violations are `ProgressStateError`; fan-out containment is surfaced as `ProgressArtifactError`; both map to exit 1. |
| Cross-module `_` import acceptable | ✓ / ⚠️ | Works cleanly; consider public naming only if more scripts import it in Phase 6. |

---

## 7. Open Questions / Assumptions

- I assume the strict `docs/bug/BUG-NNN.md` path policy is intended for all progress commands that accept BUG paths. This aligns with `frontmatter-schema.md` and makes Phase 6 reuse straightforward.
- I assume `_validate_bug_path_shape` remaining underscore-prefixed is acceptable while it is shared only inside `skills._shared.dev_workflow` and `progress.py`. If Phase 6 imports it from multiple scripts, renaming to `validate_bug_path_shape` could improve API clarity.
- I did not require full doc-guardian Class 1-7 validation or Phase 6 consistency checks for BUG files; Phase 5.4 still correctly performs only thin checks.

---

## 8. Recommendation

**(A) accept regression and proceed to Phase 6**.

Required before Phase 6: none from this review.

Optional non-blocking polish:

- Consider renaming `_validate_bug_path_shape` to `validate_bug_path_shape` if Phase 6 makes it a broadly imported helper.
- Add an explicit empty-segment test such as `docs//bug/BUG-001.md` if you want exact one-test-per-reject-branch coverage; the guard is already implemented.
