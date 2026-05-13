# Skill Set Design Proposal v0.2 Re-review

**Review Target**: `docs/design/skill_set_design_proposal_v0.2.md`  
**Previous Review**: `docs/review/skill_set_design_proposal_v0.1_review.md`  
**Feedback Response**: `docs/review/reviewer_feedback_response_v0.1.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md`  
**Review Date**: 2026-05-05  
**Reviewer**: Codex  
**Status**: v0.1 findings are mostly resolved; several v0.2 consistency issues should be fixed before Task 5 / Task 6

## Previous Findings Verification

| Finding | Status | Notes |
|---|---|---|
| F1 skill count 22 vs 23 | Resolved | v0.2 consistently uses 23 skills after adding `development-code-review`. |
| F2 S3 artifacts skipped by gate | Mostly resolved | Gate is now scenario-aware, but S3 artifact types/schema are still underspecified; see Finding 3. |
| F3 script path conflict | Mostly resolved | Main command paths now use `skills/.../scripts/...`; minor shorthand remains in AGENTS catalog descriptions. |
| F4 CR approved status conflict | Resolved | `approved` now applies to PRD / SRS / Architecture / CR. |
| F5 S2 routing oversimplified | Resolved | v0.2 adds S2-1 / S2-2 / S2-3 / S2-4 routing and `scenario_subtype`. |
| F6 no code review | Resolved | v0.2 adds `development-code-review`. |
| F7 revise owner unclear | Resolved | v0.2 defines revise as `*-write` Change Mode. |
| F8 release lifecycle undefined | Partially resolved | v0.2 adds release rules, but S4 / closed-release behavior is inconsistent; see Finding 2. |
| F9 Claude-local memory path | Resolved | Claude-local memory reference was removed. |

## Findings

### High: 23-skill implementation conflicts with the workflow spec's “One Stage Skill” principle

- **Location**: `docs/workflow/workflow_specification_claude.md:45`, `docs/workflow/workflow_specification_claude.md:307`, `docs/design/skill_set_design_proposal_v0.2.md:109`, `docs/design/skill_set_design_proposal_v0.2.md:115`, `docs/design/skill_set_design_proposal_v0.2.md:119`, `docs/design/skill_set_design_proposal_v0.2.md:127`
- **Issue**: The workflow baseline says each main Stage corresponds to one Skill with Full Mode and Change Mode. The v0.2 design implements each Stage as write/review pairs, and Stage 4 as six skills, for a total of 23 skills.
- **Impact**: Future agents may treat the workflow spec and design doc as conflicting sources of truth. This is especially risky for `workflow-protocol`, which must know whether it routes to one logical stage skill or many physical implementation skills.
- **Recommendation**: Keep the 23-skill Foreman design if desired, but update the workflow spec or add a reconciliation rule: “one logical Stage Skill” is implemented as one or more physical skills (`*-write`, `*-review`, etc.), all sharing the same Stage and Mode contract.

### High: S4 bugfix conflicts with strict closed-release rules

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:307`, `docs/design/skill_set_design_proposal_v0.2.md:308`, `docs/design/skill_set_design_proposal_v0.2.md:384`, `docs/design/skill_set_design_proposal_v0.2.md:387`, `docs/design/skill_set_design_proposal_v0.2.md:388`, `docs/design/skill_set_design_proposal_v0.2.md:389`, `docs/design/skill_set_design_proposal_v0.2.md:750`
- **Issue**: The decision tree says when the current release is closed, the user may choose S2 or S4. But Release Lifecycle says bug fixes must target the current active release, closed releases are read-only, and old releases do not accept patches. After Stage 7 closes a release, there may be no active release that represents the bug's shipped version.
- **Impact**: Post-release bugfix is underspecified or impossible: S4 can be selected after release close, but cannot legally modify the closed release; it also cannot target a new release unless a release-start rule exists.
- **Recommendation**: Define one explicit S4 policy: either (A) S4 always creates a new maintenance release targeting the latest closed release, (B) S4 is only allowed before Stage 7 closes the active release, or (C) closed releases are read-only but bugfix creates a new active release with `bugfix_of_release`. Add the required progress fields and command flow.

### High: S3 mandatory artifacts are listed in the tree but not formalized as document types

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:343`, `docs/design/skill_set_design_proposal_v0.2.md:344`, `docs/design/skill_set_design_proposal_v0.2.md:442`, `docs/design/skill_set_design_proposal_v0.2.md:455`, `docs/design/skill_set_design_proposal_v0.2.md:530`, `docs/design/skill_set_design_proposal_v0.2.md:553`, `docs/design/skill_set_design_proposal_v0.2.md:563`, `docs/design/skill_set_design_proposal_v0.2.md:565`
- **Issue**: S3 artifacts such as `source_product_prd_analysis.md`, `source_product_srs_analysis.md`, `source_module_analysis.md`, and `reuse_replace_capability.md` are required in the directory tree and gate matrix, but the per-type schema does not define their `type` values, required fields, or path rules. It only says they reuse “similar” types and add `s3_mandatory: true`.
- **Impact**: `validate.py` cannot deterministically enforce Path / Frontmatter Schema / type enum checks for these mandatory S3 artifacts. Implementers may choose different types, causing false failures or missed required artifacts.
- **Recommendation**: Add explicit doc types for each S3 mandatory artifact, or define a formal shared type such as `source-system-analysis` with `analysis_kind` enum. Include required fields and exact path rules in `frontmatter-schema.md` and `required-artifacts.md`.

### Medium: AI review status is still conflated with human approval

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:335`, `docs/design/skill_set_design_proposal_v0.2.md:361`, `docs/design/skill_set_design_proposal_v0.2.md:362`, `docs/design/skill_set_design_proposal_v0.2.md:523`, `docs/design/skill_set_design_proposal_v0.2.md:525`, `docs/design/skill_set_design_proposal_v0.2.md:526`
- **Issue**: The status schema distinguishes `review-passed` for AI review and `approved` for human confirmation, but the P6 matrix says review passes when the `*-review` skill returns `approved`, and Stage 4 task states say review is `approved`.
- **Impact**: A workflow implementation may confuse AI review approval with human approval. This can cause gated documents to advance without a human-confirmed `approved` state, or non-gated documents to wait for human approval unnecessarily.
- **Recommendation**: Use `review-passed` consistently for AI review output. Reserve `approved` only for human-gated artifacts and CR. Rename review-skill result from `approved` to `review-passed` or `no-blocking-findings`.

### Medium: progress.md sample contains invalid release and sub_state examples

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:188`, `docs/design/skill_set_design_proposal_v0.2.md:194`, `docs/design/skill_set_design_proposal_v0.2.md:223`, `docs/design/skill_set_design_proposal_v0.2.md:226`, `docs/design/skill_set_design_proposal_v0.2.md:235`
- **Issue**: The sample has active `release: "0.1"` while `previous_releases` includes `"0.1"` and `"0.2"`. It also uses `sub_state: review`, while the stated enum uses `in-review`.
- **Impact**: Since this schema will likely seed `progress.py init` and tests, invalid examples can become invalid fixtures or misleading implementation guidance.
- **Recommendation**: Make the sample internally valid. For example: `release: "0.3"`, `previous_releases: ["0.1", "0.2"]`, and `sub_state: in-review`.

### Medium: New-release creation command is missing

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:263`, `docs/design/skill_set_design_proposal_v0.2.md:271`, `docs/design/skill_set_design_proposal_v0.2.md:385`, `docs/design/skill_set_design_proposal_v0.2.md:750`
- **Issue**: `progress.py` adds `release-close`, and the lifecycle says scenario-dispatcher starts a new release after Stage 7, but there is no `release-start` / `release-init` command or state transition definition.
- **Impact**: After a release closes, the workflow has no deterministic way to create the next active release, update `previous_releases`, set `scenario_subtype`, initialize release-scoped artifact paths, and reset stage state.
- **Recommendation**: Add a `release-start` command, or define that `progress.py init --release <version>` handles both first project init and new release init. Include validation for serial release constraints.

### Medium: Code review report lacks a machine-readable pass/fail contract

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:124`, `docs/design/skill_set_design_proposal_v0.2.md:363`, `docs/design/skill_set_design_proposal_v0.2.md:542`
- **Issue**: `development-code-review` is added, but `code-review-report` only requires `findings_count` and `severity_distribution`. The Stage 4 state says Source Code passes review, but there is no required `review_status`, `blocking_findings_count`, or severity threshold.
- **Impact**: `progress.py` cannot reliably decide whether `code-review-passed` is valid. A report with 5 critical findings could still have a schema-valid `findings_count` unless another rule exists.
- **Recommendation**: Add fields such as `review_status: pass | fail`, `blocking_findings_count`, and `max_severity`; define that `code-review-passed` requires `review_status: pass` and `blocking_findings_count: 0`.

### Low: Some script-path wording still uses shorthand after the full-path decision

- **Location**: `docs/design/skill_set_design_proposal_v0.2.md:37`, `docs/design/skill_set_design_proposal_v0.2.md:137`, `docs/design/skill_set_design_proposal_v0.2.md:703`, `docs/design/skill_set_design_proposal_v0.2.md:704`, `docs/design/skill_set_design_proposal_v0.2.md:857`
- **Issue**: Most executable command examples use `skills/.../scripts/...`, but several summary lines still say `scripts/validate.py`, `scripts/progress.py`, or `scripts/changelog.py`.
- **Impact**: Low, but it weakens the F3 resolution and may reintroduce path ambiguity when snippets are copied into SKILL.md.
- **Recommendation**: Normalize all command references to full skill paths, or explicitly label shorthand as display-only.

## Summary

v0.2 successfully addresses the original review's main blockers: skill count, S2 routing, CR status, code review, revise ownership, and vendor-neutral memory cleanup are materially improved. The remaining blockers are mostly second-order consistency issues introduced by the fixes: release/S4 semantics, formal S3 artifact schemas, and status terminology.

## Suggested Next Revision Order

1. Reconcile workflow spec “One Stage Skill” with the 23 physical skill Foreman implementation.
2. Decide and document S4 behavior under strict serial releases.
3. Formalize S3 mandatory artifact types and schemas.
4. Normalize `review-passed` vs `approved` terminology.
5. Add `release-start` semantics and fix the progress.md sample.
6. Add machine-readable code review pass/fail fields.
