# Skill Set Design Proposal v0.3 Re-review

**Review Target**: `docs/design/skill_set_design_proposal_v0.3.md`  
**Previous Review**: `docs/review/skill_set_design_proposal_v0.2_rereview.md`  
**Feedback Response**: `docs/review/reviewer_feedback_response_v0.2.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md`  
**Review Date**: 2026-05-05  
**Reviewer**: Codex  
**Status**: v0.2 findings are largely resolved; remaining issues are mainly spec/design synchronization and bug/release edge cases

## Previous Findings Verification

| Finding | Status | Notes |
|---|---|---|
| F1 logical vs physical skill conflict | Resolved | v0.3 adds logical vs physical reconciliation and workflow spec now reflects it. |
| F2 S4 vs closed-release conflict | Partially resolved | Design now chooses active-release-only S4, but workflow spec and post-close intake are still inconsistent; see Findings 1-2. |
| F3 S3 artifact types missing | Resolved | v0.3 adds `source-system-analysis` with `analysis_kind` enum and required S3 mapping. |
| F4 review-passed vs approved terminology | Mostly resolved | Main design now uses `review-passed`; minor wording remains acceptable, except workflow implementation should keep this strict. |
| F5 progress.md sample invalid | Resolved | Sample now uses active `0.3`, previous `0.1/0.2`, and `sub_state: in-review`. |
| F6 missing release-start | Mostly resolved | `release-start` exists, but release-close/release-start state mutation details need one more rule; see Finding 5. |
| F7 code-review pass/fail contract | Resolved | `code-review-report` now has `review_status`, `blocking_findings_count`, and `max_severity`. |
| F8 script path shorthand | Mostly resolved | Executable examples use full paths, but a few shorthand references remain; see Finding 6. |

## Findings

### High: Workflow spec still describes S4 as post-delivery bugfix, conflicting with v0.3 active-release-only policy

- **Location**: `docs/workflow/workflow_specification_claude.md:31`, `docs/workflow/workflow_specification_claude.md:336`, `docs/workflow/workflow_specification_claude.md:588`, `docs/workflow/workflow_specification_claude.md:593`, `docs/design/skill_set_design_proposal_v0.3.md:36`, `docs/design/skill_set_design_proposal_v0.3.md:102`, `docs/design/skill_set_design_proposal_v0.3.md:340`, `docs/design/skill_set_design_proposal_v0.3.md:425`
- **Issue**: Design v0.3 says S4 is only allowed during an active release, specifically when Stage 5 testing finds a bug. The workflow spec still says S4 is for Bug Fix generally and that Bug Rollback can be triggered by post-delivery defect input.
- **Impact**: The workflow spec remains the declared baseline, so future agents may follow spec and allow post-delivery S4 even though the design forbids it. This reintroduces the release/S4 ambiguity v0.3 intended to remove.
- **Recommendation**: Update workflow spec §2, §6, and §9.4 to match v0.3: S4 is active-release-only; post-close bug reports are intake records, not S4 execution. If S4 should remain broader in the workflow spec, then the design's active-only rule should be marked as an implementation constraint rather than a workflow rule.

### High: Post-close bug intake has no owning skill or deterministic state transition

- **Location**: `docs/design/skill_set_design_proposal_v0.3.md:247`, `docs/design/skill_set_design_proposal_v0.3.md:330`, `docs/design/skill_set_design_proposal_v0.3.md:343`, `docs/design/skill_set_design_proposal_v0.3.md:348`, `docs/design/skill_set_design_proposal_v0.3.md:426`, `docs/design/skill_set_design_proposal_v0.3.md:769`
- **Issue**: v0.3 says post-close bugs are written to `docs/bug/BUG-NNN.md`, added to `unresolved_bugs`, and later merged into the next S2 SRS. But S4 is forbidden when release is closed, and no skill/command owns this post-close bug intake or the update to `unresolved_bugs`.
- **Impact**: A user can report a bug after release close, but the system has no legal workflow action to create the bug report, validate it, append it to `progress.md`, or later clear it after S2 consumes it. Agents may either incorrectly invoke S4 or hand-edit `progress.md`, both of which violate v0.3 rules.
- **Recommendation**: Add an explicit `bug-intake` path. Options: add a small physical skill, make `bug-triage` own post-close intake, or add `progress.py bug-intake --bug <path>`. Define who creates `BUG-NNN.md`, when `target_release: null` is allowed, how `unresolved_bugs` is appended, and how S2 marks bugs as consumed.

### High: PRD root-cause exception cannot be represented in progress state

- **Location**: `docs/design/skill_set_design_proposal_v0.3.md:241`, `docs/design/skill_set_design_proposal_v0.3.md:245`, `docs/design/skill_set_design_proposal_v0.3.md:408`, `docs/design/skill_set_design_proposal_v0.3.md:409`, `docs/workflow/workflow_specification_claude.md:401`, `docs/workflow/workflow_specification_claude.md:406`, `docs/workflow/workflow_specification_claude.md:417`
- **Issue**: `bug_flow.root_cause` only lists SRS / Architecture / Development, and Bug Flow handling switches `current_stage` to the root-cause stage Change Mode. The workflow spec has a fourth PRD root cause exception that must stop normal development and enter Workflow Incident Analysis.
- **Impact**: If `bug-triage` determines PRD root cause, progress state cannot record it cleanly and the generic Bug Flow transition is wrong because PRD root cause must not route to PRD Change Mode.
- **Recommendation**: Extend `bug_flow.root_cause` to include `PRD_EXCEPTION` or `WorkflowIncident`, and add state fields such as `workflow_incident_active`, `incident_report_path`, or a dedicated `current_stage: workflow-incident-analysis`. Also define that this branch bypasses normal stage Change Mode.

### Medium: release-close / release-start mutation semantics are incomplete

- **Location**: `docs/design/skill_set_design_proposal_v0.3.md:209`, `docs/design/skill_set_design_proposal_v0.3.md:211`, `docs/design/skill_set_design_proposal_v0.3.md:295`, `docs/design/skill_set_design_proposal_v0.3.md:296`, `docs/design/skill_set_design_proposal_v0.3.md:308`, `docs/design/skill_set_design_proposal_v0.3.md:313`, `docs/design/skill_set_design_proposal_v0.3.md:421`, `docs/design/skill_set_design_proposal_v0.3.md:422`
- **Issue**: `release-start` requires the new version to be greater than `previous_releases`, but the design does not explicitly say `release-close` appends the current `release` to `previous_releases`. It also does not specify what happens to `scenario`, `scenario_subtype`, artifact paths, and `unresolved_bugs` during `release-start`.
- **Impact**: Implementers can produce incompatible progress states. For example, after closing `0.3`, if `previous_releases` is not updated, the next start validation may not know `0.3` is closed. If S2 consumes unresolved bugs but the list is not cleared or annotated, bugs can be duplicated into later releases.
- **Recommendation**: Add exact state mutations: `release-close` appends current release to `previous_releases` and sets `release_state: closed`; `release-start` sets `release`, `release_state: active`, `scenario`, `scenario_subtype`, `current_stage`, release-scoped artifact paths, and handles `unresolved_bugs` by either copying to a consumed list or marking each bug with `consumed_in_release`.

### Medium: Version ordering is underspecified for release strings

- **Location**: `docs/design/skill_set_design_proposal_v0.3.md:211`, `docs/design/skill_set_design_proposal_v0.3.md:296`, `docs/design/skill_set_design_proposal_v0.3.md:311`, `docs/design/skill_set_design_proposal_v0.3.md:422`
- **Issue**: The design requires a new release version to be “strictly greater” than previous releases, but release values are strings like `"0.3"` and the comparison algorithm is not defined.
- **Impact**: Lexicographic comparison will order `0.10` before `0.2`; ad-hoc numeric parsing may mishandle `1.0.1` if later allowed. This can break serial release enforcement.
- **Recommendation**: Define the accepted version grammar and comparison. For v1, use either strict `MAJOR.MINOR` integer pairs or full SemVer. If only `x.y` is allowed, say so and make `progress.py release-start` parse two integers.

### Low: Script path normalization still has shorthand references

- **Location**: `docs/design/skill_set_design_proposal_v0.3.md:155`, `docs/design/skill_set_design_proposal_v0.3.md:652`, `docs/design/skill_set_design_proposal_v0.3.md:654`, `docs/design/skill_set_design_proposal_v0.3.md:718`, `docs/design/skill_set_design_proposal_v0.3.md:719`
- **Issue**: v0.3 claims all script paths were normalized, but some references still use `scripts/validate.py`, `scripts/changelog.py`, or `scripts/progress.py` shorthand.
- **Impact**: Low because executable instructions mostly use full paths, but shorthand can leak into generated SKILL.md files.
- **Recommendation**: Replace remaining shorthand with full paths or explicitly label shorthand as display-only names.

## Positive Notes

- The logical vs physical skill reconciliation is clear and resolves the largest architecture/spec tension.
- `source-system-analysis` is now a usable doc type with scenario-aware required artifacts.
- `review-passed` vs `approved` is much clearer than v0.2.
- `code-review-report` now has enough fields to support deterministic gate checks.
- The active-release-only S4 policy is simple and coherent as a user preference; it just needs spec sync and intake mechanics.

## Suggested Next Revision Order

1. Sync workflow spec S4 sections with the v0.3 active-release-only policy.
2. Add a deterministic post-close bug intake owner and progress update path.
3. Add PRD root-cause / Workflow Incident state representation.
4. Specify `release-close` and `release-start` state mutations, including unresolved bug consumption.
5. Define release version grammar/comparison.
6. Clean remaining script path shorthand.
