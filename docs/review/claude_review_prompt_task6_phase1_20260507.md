# Claude Review Prompt — Task 6 Phase 1 Docs Alignment

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成审查，并把评审报告保存到 `docs/review/task6_phase1_docs_alignment_review_20260507.md`。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 1 Docs Alignment** 做一次严格 review。目标是先评审 Codex 刚完成的文档对齐工作，只有评审通过后才继续实现 Phase 2 shared Python foundation。

本轮不是实现轮：不要因为 `skills/workflow-protocol/scripts/progress.py`、`skills/doc-guardian/scripts/validate.py`、`skills/doc-guardian/scripts/changelog.py`、`skills/doc-guardian/scripts/status_transition.py` 尚未存在而报 finding。请只评审 Task 6 implementation plan 与 references / SKILL.md 文档是否足以指导后续脚本实现，是否与已闭环设计一致，是否引入新的自相矛盾或 bypass。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 5 已闭环：23 个 physical skill 的 SKILL.md 与核心 references 经 Batch 1 / 2 / 3a / 3b / 3c review accept。Task 6 进入脚本实现前，Codex 先做了两件事：

1. 新增 Task 6 implementation plan。
2. 做 Phase 1 docs alignment：把 Task 6 Gap-3 / Gap-4 / Gap-5、`bug-rework`、`status_transition.py` helper 接口写入 workflow-protocol / doc-guardian references 与相关 SKILL.md。

请注意：当前 repo 里 `docs/` 与 `skills/` 很可能是 untracked 状态，不要把 untracked 视为可删除或异常；这些就是当前设计产物。

## 本轮 Codex 改动摘要

### 新增计划文档

- `docs/implementation/task6_plan_20260507.md`
  - 覆盖 `progress.py` command matrix
  - 覆盖 `validate.py` 8 类 checker
  - 覆盖 `changelog.py` promote / validate
  - 覆盖 `status_transition.py` helper API
  - 覆盖 Gap-3 / Gap-4 / Gap-5、文件写集、测试策略、分阶段顺序

### 主要 reference / SKILL.md 对齐

- `skills/workflow-protocol/references/command-reference.md`
  - command count 从 11 改为 12
  - 新增 `bug-rework --bug <bug-report-path>`
  - 新增 Gap-3：`verifying -> code-revising`
  - 新增 Gap-4 protected rollback：`verified -> test-revising` / `verified -> code-revising` / `code-review-passed -> code-revising`
  - 新增 Gap-5 protected transition：active Bug Flow retest fail/partial → `bug-rework`

- `skills/workflow-protocol/SKILL.md`
  - command count 从 11 改为 12
  - invocation matrix、command list、Bug Flow path、terminal-state protected command list、Forbidden Actions 均加入 `bug-rework`

- `skills/doc-guardian/SKILL.md`
  - 新增 `skills/doc-guardian/scripts/status_transition.py`
  - 定义 `plan` / `apply`
  - 定义 event → status mapping
  - 定义调用顺序：`progress.py update --event <event>` 成功后 caller 调 helper
  - 定义增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败 rollback、幂等 retry

- `skills/doc-guardian/references/change-log-format.md`
  - 新增 `status_transition.py` helper 调用模式
  - 要求 helper 对增量类 doc 在同一 transaction 内更新 frontmatter、追加 `[frontmatter]` pending entry、promote、校验、rollback

### 相关 SKILL.md 清理

- `skills/scenario-dispatcher/SKILL.md`
  - command-reference 引用从 11 个 progress.py 子命令改为 12 个

- `skills/testing-write/SKILL.md`
  - Stage 5 active Bug Flow retest fail/partial 从“Gap-5 escalation / 等待命令”改为调用 `progress.py bug-rework`
  - 保留禁止二次 triage / 禁止创建第二个 BUG / 禁止手工回 root-cause stage

- `skills/testing-review/SKILL.md`
  - active retest fail/partial 后续路径改为 testing-write / Bootstrap 调 `bug-rework`
  - review skill 自身仍不调 `bug-start` / `bug-rework` / `bug-close`

- 多个 stage SKILL.md 中 Gap-2 helper 文案已从“接口 TBD / batch upgrade”更新为明确的 `skills/doc-guardian/scripts/status_transition.py apply --event <event> --doc <path> ...`。

## 必读材料

请按以下顺序阅读，避免遗漏上下文：

1. `docs/handoff/session_handoff_20260506_v4.md`
2. `docs/handoff/task6_progress_py_prerequisites_20260506.md`
3. `docs/implementation/task6_plan_20260507.md`
4. `skills/workflow-protocol/references/command-reference.md`
5. `skills/workflow-protocol/SKILL.md`
6. `skills/doc-guardian/SKILL.md`
7. `skills/doc-guardian/references/change-log-format.md`
8. `skills/doc-guardian/references/frontmatter-schema.md`
9. `skills/doc-guardian/references/required-artifacts.md`
10. `skills/doc-guardian/references/directory-layout.md`
11. `skills/testing-write/SKILL.md`
12. `skills/testing-review/SKILL.md`
13. `skills/scenario-dispatcher/SKILL.md`
14. `docs/review/skill_set_batch3c_round2_review.md`
15. `docs/review/skill_set_batch3b_round2_review.md`
16. `docs/review/skill_set_batch3a_round3_review.md`
17. `docs/design/skill_set_design_proposal_v0.5.md`
18. `docs/workflow/workflow_specification_claude.md`

可选抽查（用于 Gap-2 helper 文案是否全局一致）：

- `skills/prd-write/SKILL.md`
- `skills/prd-review/SKILL.md`
- `skills/srs-write/SKILL.md`
- `skills/srs-review/SKILL.md`
- `skills/architecture-write/SKILL.md`
- `skills/architecture-review/SKILL.md`
- `skills/development-planning-write/SKILL.md`
- `skills/development-planning-review/SKILL.md`
- `skills/development-test-write/SKILL.md`
- `skills/development-test-review/SKILL.md`
- `skills/development-code-write/SKILL.md`
- `skills/development-code-review/SKILL.md`
- `skills/delivery-write/SKILL.md`
- `skills/delivery-review/SKILL.md`
- `skills/retrospective-write/SKILL.md`
- `skills/retrospective-review/SKILL.md`

## Review Scope

### A. Task 6 Plan Review

检查 `docs/implementation/task6_plan_20260507.md`：

- 是否覆盖 `progress.py` / `validate.py` / `changelog.py` / `status_transition.py` 四大实现目标？
- 文件写集是否合理，是否遗漏必须脚本或共享模块？
- 测试策略是否覆盖 happy path、Gap-3、Gap-4、Gap-5、status helper、Change Log、required-artifacts DSL？
- 分阶段顺序是否安全：先 references alignment，再 shared foundation，再 changelog/validate，再 helper，再 progress core，再 Bug Flow/advance？
- 是否明确哪些内容暂不做（AGENTS/CLAUDE/plugin metadata、Gap-1 reopen event 等）？
- 是否存在过度实现、与设计冲突、或隐藏 bypass？

### B. progress.py Reference Alignment

检查 `skills/workflow-protocol/references/command-reference.md` 与 `skills/workflow-protocol/SKILL.md`：

- command count 是否全局一致为 12？是否仍有 stale “11 个子命令”？
- `bug-rework` 是否只用于 active Bug Flow retest fail/partial？
- `bug-start` 是否仍只表示 initial Bug Flow entry，且不得被 retest fail/partial overload？
- `bug-close` 是否仍只用于 retest pass？
- Gap-3 `verifying -> code-revising` 是否前置为 `verification_result.md verification_status in {fail, partial}`，且不走 bug-triage？
- Gap-4 rollback 是否只由 `bug-start` / `bug-rework` protected path 触发，且依赖 BUG body `Affected Task(s)`？
- Gap-4 是否禁止猜测：affected task 缺失或分类不明确时 route to `development-planning-write` replan/route？
- Gap-5 `bug-rework` 前置是否完整：active bug_flow、current stage testing、sub_state review-passed、latest test-report fail/partial、BUG path matches `bug_flow.bug_report_path`、BUG root_cause matches active root cause and in `{srs, architecture, development}`？
- protected fields / terminal-state / Forbidden Actions 是否覆盖 `bug-rework`？

### C. doc-guardian status_transition.py Helper Review

检查 `skills/doc-guardian/SKILL.md` 与 `skills/doc-guardian/references/change-log-format.md`：

- helper owner 是否明确为 `skills/doc-guardian/scripts/status_transition.py`？
- `plan` / `apply` interface 是否足够明确？
- event mapping 是否完整且与 frontmatter-schema status machine 一致：
  - `write-complete`: `draft|revising -> in-review`
  - `review-issues`: `in-review -> revising`
  - `review-passed`: `in-review -> review-passed`
  - `human-confirmed`: `review-passed -> approved` only for PRD/SRS/Architecture/CR
- 调用顺序是否与 Batch 3a/3b/3c 已声明序列一致：progress event 成功后 caller 调 helper？
- 增量类 doc 的 status 变更是否通过 `[frontmatter]` Pending Changes → Change Log 原子 promote？
- 一次性 doc 是否不被强制 Change Log？
- 多 doc all-or-nothing rollback 与幂等 retry 是否描述清楚？
- 是否仍有 stale “接口 TBD / batch upgrade / helper 接口待后续定义”？

### D. Stage 5 Testing / Bug Flow Consistency

检查 `skills/testing-write/SKILL.md` 与 `skills/testing-review/SKILL.md`：

- 初次 fail/partial 是否仍进入 bug-triage active mode，而不是 bug-rework？
- active retest fail/partial 是否明确不重新 triage、不新建 BUG、不 bug-close，而是调用 `bug-rework`？
- testing-review 是否仍只做 review，不调 `bug-start` / `bug-rework` / `bug-close`？
- Stage 5 advance 是否仍要求 `verification_status: pass`？fail/partial review-passed 只表示 artifacts 诚实，不表示 Stage done？
- 是否与 `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 Gap-5 一致？

### E. Cross-Skill Consistency / Regression Risks

请特别检查：

1. Event whitelist 是否仍只有 `{write-complete, review-issues, review-passed, human-confirmed}`；不得引入 `issues-found` event。
2. Stage 6 Delivery 是否仍不进入 active Bug Flow；本轮改动不得给 delivery → testing rollback 开口。
3. Stage 7 Retrospective 是否仍不自动 `release-close`，不自动 patch dev-workflow-skills2。
4. Gap-1 `review-passed -> revising` 是否仍明确 deferred，未被偷偷实现成新 event。
5. `status_transition.py` helper 是否不会使 progress.py 暗中 mutate docs；owner boundary 是否清晰。
6. `validate.py file` vs `validate.py consistency` / `progress.py update --task planning-done` 边界是否仍清楚。
7. Any stale text that still says “before bug-rework exists / escalate only / no legal command” in active Task 6 docs should be reported.

## Review Output Requirements

请把评审结论保存到：

`docs/review/task6_phase1_docs_alignment_review_20260507.md`

请使用以下格式：

```markdown
# Task 6 Phase 1 Docs Alignment Review

**Review Target**: Task 6 implementation plan + workflow/doc-guardian references + related SKILL.md alignment
**Review Date**: 2026-05-07
**Reviewer**: Claude
**Baseline**: Task 5 accepted state + Task 6 prerequisites
**Recommendation**: (A) accept and proceed to Phase 2 / (B) fix docs before Phase 2 / (C) revisit design
**Status**: findings: <H/M/L counts>; blockers: <yes/no>

## Executive Summary

[2-5 bullets. State clearly whether implementation may continue.]

## Findings

[Primary output. List findings ordered High → Medium → Low. For each finding include:]

### <Severity>: <Title>

- **Location**: `<file>:<line>`
- **Issue**: ...
- **Impact**: ...
- **Recommendation**: ...

If no findings, explicitly state: “No blocking or non-blocking findings discovered.”

## Checklist Results

| Area | Status | Notes |
|------|--------|-------|
| Task 6 implementation plan | ✅/⚠️/❌ | ... |
| progress.py command-reference alignment | ✅/⚠️/❌ | ... |
| bug-rework / Gap-5 | ✅/⚠️/❌ | ... |
| Gap-3 verification rollback | ✅/⚠️/❌ | ... |
| Gap-4 development task rollback | ✅/⚠️/❌ | ... |
| status_transition.py helper | ✅/⚠️/❌ | ... |
| Stage 5 testing flow | ✅/⚠️/❌ | ... |
| stale text / regression scan | ✅/⚠️/❌ | ... |

## Open Questions / Assumptions

[Only if needed.]

## Recommendation

[Choose A/B/C. If A, say: “Proceed to Phase 2 shared foundation implementation.” If B/C, list exact files that must be fixed first.]
```

## Important Constraints for Reviewer

- Do not implement code.
- Do not modify `progress.md` / `progress-history.md` if they exist.
- Do not delete untracked files.
- Do not treat missing runtime scripts as findings in this review; scripts are Phase 2+.
- Do save the review report to `docs/review/task6_phase1_docs_alignment_review_20260507.md`.
