# Claude Review Prompt — Task 5 Batch 3c Round 2

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成回归审查，并把复评报告保存到 `docs/review/skill_set_batch3c_round2_review.md`。

---

## Prompt Body

请对 dev-workflow-skills2 项目的 Task 5 Batch 3c（Testing / Delivery / Retrospective write+review × 3，共 6 份 SKILL.md）做 **Round 2 post-fix regression review**。

Round 1 报告是：`docs/review/skill_set_batch3c_review.md`。本轮目标是确认 Round 1 的 0 High / 1 Medium / 5 Low 是否已修复，是否引入新的 High/Medium，是否可接受进入 Task 6 实现准备。

本批仍是**骨架轮**：只评审 6 个 `SKILL.md` 与 Task 6 prerequisite 文档的 Gap-5 补充；不要求新增 references，不要求实现 scripts。不要因为 `progress.py` / `validate.py` / `changelog.py` 尚未存在而报 finding；只评审这些文档对脚本行为的描述是否与现有 references 一致。

### 评审目标文件

主要审查（Batch 3c SKILL.md × 6）：

- `skills/testing-write/SKILL.md` (217 行)
- `skills/testing-review/SKILL.md` (162 行)
- `skills/delivery-write/SKILL.md` (164 行)
- `skills/delivery-review/SKILL.md` (143 行)
- `skills/retrospective-write/SKILL.md` (171 行)
- `skills/retrospective-review/SKILL.md` (148 行)

Task 6 prerequisite 补充：

- `docs/handoff/task6_progress_py_prerequisites_20260506.md` (100 行)

### 必读参考材料

- `docs/review/skill_set_batch3c_review.md`（Round 1 findings，必须逐项回归）
- `docs/review/claude_review_prompt_batch3c.md`（Round 1 prompt / review scope）
- `docs/handoff/session_handoff_20260506_v3.md`
- `docs/handoff/task6_progress_py_prerequisites_20260506.md`
- `docs/workflow/workflow_specification_claude.md`
- `docs/design/skill_set_design_proposal_v0.5.md`
- `docs/review/skill_set_batch3a_round3_review.md`
- `docs/review/skill_set_batch3b_round2_review.md`
- `skills/workflow-protocol/SKILL.md`
- `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`
- `skills/doc-guardian/references/required-artifacts.md`
- `skills/doc-guardian/references/change-log-format.md`
- `skills/bug-triage/SKILL.md`
- `skills/workflow-evolution/SKILL.md`

### Round 1 Findings 回归检查清单

请逐项判断：✅ 已修 / ⚠️ 部分残留 / ❌ 未修，并给具体评论。

#### M1: Gap-5 推荐 transition 缺具体 command name 候选 + mutation 描述

修复定位：

- `skills/testing-write/SKILL.md` §10 Gap-5
- `skills/testing-review/SKILL.md` §10 Gap-5
- `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 Gap-5

回归审查：

- 是否明确推荐 dedicated `progress.py bug-rework --bug <BUG-NNN.md>`，且优先于放宽 `bug-start`？
- 前置是否完整：`bug_flow.active==true`、`current_stage==testing`、`sub_state==review-passed`、最新 test-report fail/partial、BUG path 等于 `bug_flow.bug_report_path`、BUG.root_cause 与 `bug_flow.root_cause` 一致且属于 `{srs, architecture, development}`？
- mutation 是否完整：保持 active bug_flow 不变，`current_stage` 切回 root_cause stage，`sub_state -> write`，`review_iteration -> 0`，append `bug-rework` history？
- `root_cause==development` 时是否复用 Gap-4 affected-task rollback？
- prerequisites 文档是否把 Gap-5 加入 non-bypass rule？
- 是否仍禁止 retest fail 时重新 `bug-start`、创建新 BUG、`bug-close`、手工编辑 progress.md？

#### L1: testing-write §2 sub_state 字段值 narrative

修复定位：`skills/testing-write/SKILL.md` §2

回归审查：

- `sub_state` 表格是否改为 enum：`write` / `revising` / `review-passed`？
- 是否新增 Reentry 说明，限定 `review-passed` 只能走 §5.2 Case A/B/C？

#### L2: delivery-write §7 暗示 delivery → testing transition

修复定位：`skills/delivery-write/SKILL.md` §3 / §7

回归审查：

- 是否删除“按项目策略回 testing 阶段重测/创建 BUG”的暗示？
- 是否明确当前 spec 不提供 delivery → testing rollback transition？
- 是否只允许升级用户/Bootstrap：release close 后 post-close `bug-intake`，或经 design cycle 增加 dedicated rollback？
- `delivery-review` recovery 是否也避免暗示 Bootstrap 可手工回 testing？

#### L3: testing-write §3 Bug Close mode 前置比 spec 严

修复定位：`skills/testing-write/SKILL.md` §3

回归审查：

- 是否新增 footnote：`sub_state==review-passed` 是 caller-side safety net？
- 是否明确 `progress.py bug-close` 自身前置仍以 command-reference 为准（bug_flow.active + current_stage==testing + latest test-report pass）？

#### L4: retrospective-write 首次创建 owner 不明确

修复定位：`skills/retrospective-write/SKILL.md` §3 / §4

回归审查：

- 是否明确首个 release 进入 Stage 7 时由 retrospective-write 创建 `retrospective.md`？
- 是否说明首次创建包含 universal frontmatter、首个 release section、Pending Changes、Change Log skeleton？
- 后续 release 是否仍是在同一文件追加/修订当前 release section？

#### L5: testing-write description 行长度

修复定位：`skills/testing-write/SKILL.md` frontmatter description

回归审查：

- description 是否已适度精简且仍保留 trigger / core responsibilities / forbidden owner boundary？
- 是否仍足以触发 testing-write skill？

### 横向一致性重点

1. Event whitelist：所有 `--event <name>` 必须属于 `{write-complete, review-issues, review-passed, human-confirmed}`；不得出现 `--event issues-found`。
2. Gap-5 与 existing Bug Flow：`bug-rework` 不应替代 initial `bug-start`，也不应替代 `bug-close`；只用于 active Bug Flow retest fail/partial。
3. Stage 6 delivery：仍不启动 Bug Flow，不创建 active BUG，不提供 delivery → testing rollback。
4. Stage 7 retrospective：仍不调 release-close，不自动调 workflow-evolution，不 patch dev-workflow-skills2。
5. Gap-1 / Gap-2：本轮不解决，只确认声明仍保守且未引入 bypass。
6. No manual progress.md：所有 Gap-5 / delivery upstream mismatch / review-passed reentry 场景都不得手工编辑 progress.md。

### 输出要求

保存到：`docs/review/skill_set_batch3c_round2_review.md`

格式：

```markdown
# Skill Set Batch 3c Round 2 Review (post-fix regression)

**Review Target**: 6 份 Stage 5/6/7 SKILL.md + Task 6 prerequisites Gap-5 section
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch3c_review.md
**Round 1 Prompt**: docs/review/claude_review_prompt_batch3c.md
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: regression: <count> remaining; new findings: <H/M/L>; recommendation: (A) accept / (B) fix remaining / (C) revisit design

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|----------|------|
| M1 Gap-5 command/mutation/prerequisites | ✅/⚠️/❌ | ... |
| L1 testing-write sub_state narrative | ✅/⚠️/❌ | ... |
| L2 delivery-write rollback wording | ✅/⚠️/❌ | ... |
| L3 bug-close caller-side safety note | ✅/⚠️/❌ | ... |
| L4 retrospective first-create owner | ✅/⚠️/❌ | ... |
| L5 testing-write description length | ✅/⚠️/❌ | ... |

## New Findings

[仅列 regression 后仍存在或新增的问题，按 High → Medium → Low 排。]

## Gap-5 Assessment

[确认 `bug-rework` 方案是否清晰、可实现、与 bug-start/bug-close 不冲突，是否足以进入 Task 6。]

## Cross-Skill Consistency Check

[简要验证 testing/delivery/retrospective 之间与 workflow-protocol/bug-triage/workflow-evolution 的边界。]

## Recommendation

[明确是否 accept；若 accept，说明可进入 Task 6 prerequisites / implementation planning。]
```
