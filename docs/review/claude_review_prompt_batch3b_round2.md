# Claude Review Prompt — Task 5 Batch 3b Round 2

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成回归审查，并把复评报告保存到 `docs/review/skill_set_batch3b_round2_review.md`。

---

## Prompt Body

请对 dev-workflow-skills2 项目的 Task 5 Batch 3b（Stage 4 Development planning/test/code write+review × 3，共 6 份 SKILL.md）做 **Round 2 post-fix regression review**。

Round 1 报告是：`docs/review/skill_set_batch3b_review.md`。本轮目标是确认 Round 1 的 2 High / 6 Medium / 9 Low 是否已修复，是否引入新的 High/Medium，是否可进入 batch 3c。

本批仍是**骨架轮**：只评审 6 个 `SKILL.md`，不要求新增 references，不要求实现 scripts。不要因为 `skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` 尚未存在而报 finding；只评审 SKILL.md 对这些脚本行为的描述是否与 references 一致。

### 评审目标文件（6 份）

- `skills/development-planning-write/SKILL.md` (240 行)
- `skills/development-planning-review/SKILL.md` (195 行)
- `skills/development-test-write/SKILL.md` (206 行)
- `skills/development-test-review/SKILL.md` (210 行)
- `skills/development-code-write/SKILL.md` (252 行)
- `skills/development-code-review/SKILL.md` (215 行)

总计 1318 行。

### 必读参考材料

- `docs/review/skill_set_batch3b_review.md`（Round 1 findings，必须逐项回归）
- `docs/handoff/session_handoff_20260506_v3.md`（batch 3b 起手指南 §7 / §8）
- `docs/workflow/workflow_specification_claude.md`（v0.6）
- `docs/design/skill_set_design_proposal_v0.5.md`
- `docs/review/skill_set_batch3a_round3_review.md`（Gap-1 / Gap-2 状态 + batch 3a 闭环）
- `skills/workflow-protocol/SKILL.md`（§5.2 Stage 4 task-level 判定 + §10 concurrency）
- `skills/workflow-protocol/references/command-reference.md`（§2 event 白名单；§2.1 global sub_state；§2.2 advance；§8 bug-start；Stage 4 task transition table）
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`（development-plan / task-breakdown / detailed-design / test-review-report / code-review-report / verification-result schema）
- `skills/doc-guardian/references/required-artifacts.md`（Stage 4 required artifacts）
- `skills/doc-guardian/references/change-log-format.md`（增量类 vs 一次性 doc 分类）
- `skills/doc-guardian/references/directory-layout.md`
- `skills/bug-triage/SKILL.md`
- `skills/bug-triage/references/root-cause-rubric.md`
- `skills/bug-triage/references/triage-decision-tree.md`

### Round 1 Findings 回归检查清单

请逐项判断：✅ 已修 / ⚠️ 部分残留 / ❌ 未修，并给具体评论。

#### H1: Bug Flow Direct Route 未提供 verified task 回退 transition（新 Gap-4）

修复定位：

- `development-planning-write` §3 Bug Flow Direct Route、§7 Bug Flow Re-entry、§10 Design Gaps
- `development-test-write` §2 Bug Flow 入口、§10 Design Gaps
- `development-code-write` §2 Bug Flow 入口、§10 Design Gaps

回归审查：

- 是否明确声明 **Gap-4**：current command-reference 缺 `verified -> test-revising` / `verified -> code-revising` / `code-review-passed -> code-revising` rollback transition？
- planning-write §3 Direct Route 是否不再声称 verified task 可直接用 existing state 进入 revise？
- test-write / code-write 是否明确：affected task 已 `verified` 时，在 workflow-protocol/progress.py 补 rollback 前不能被直接 invoke，也不能手工改 progress.md？
- Gap-4 推荐方案是否清楚：`progress.py bug-start --root-cause development` 解析 BUG body `Affected Task(s)` 并自动回退相关 task？
- 是否仍与 bug-triage 的 BUG body `Affected Task(s)` 事实源一致？

#### H2: Verification Fail 回退 transition 缺失（Gap-3）

修复定位：

- `development-code-write` §10 Gap-3
- `development-code-review` §10 Gap-3 awareness

回归审查：

- 是否明确推荐 transition：`verifying -> code-revising`？
- 是否明确前置：`verification_result.md verification_status: fail|partial`？
- 是否仍禁止 verification fail 后手工改 progress.md / 绕过 code review？
- code-write §5.2 Verification Procedure 是否仍清楚 pass 才能 `verified`，fail/partial 不得 call `verified`？

#### M1: planning review pass 后 partial task registration recovery 不充分

修复定位：

- `development-planning-review` §2 When to Invoke
- `development-planning-review` §4.1 review-passed output
- `development-planning-review` §5 Step 5
- `development-planning-review` §9 Recovery

回归审查：

- 是否新增 `sub_state==review-passed` + task registration incomplete 的 reentry 入口？
- 是否明确重 invoke 时跳过业务评审 / 不重发 `review-passed` event，只 retry 未 `planning-done` task？
- 已经 `planning-done` 的 task 是否视为幂等成功 / 跳过？
- recovery 是否避免手工补 progress.md？
- 是否仍保持顺序：先 global `review-passed`，再 task `planning-done`？

#### M2: validate.py file 与 task registration 的 chicken-and-egg 误导

修复定位：

- `development-planning-write` §5 Step 4 + 关键约束
- `development-planning-write` §10 Task registration note
- `development-planning-review` §10 Task registration note

回归审查：

- 是否删除/修正“validate.py file 会因 task_id 不在 progress.md task_states 而拒绝”的暗示？
- 是否明确 `validate.py file` 只跑 file-level class 1-7，不做 progress consistency？
- 是否明确 class 8 consistency / `validate.py consistency` / advance 在 task 注册后兜底？
- 是否把 task_id/path/breakdown/progress 原子一致性责任放到 `progress.py update --task Tn --status planning-done` 实现，而不是 validate.py file？

#### M3: Stage 4 advance 的 C 维度复合判定未明确

修复定位：

- `development-planning-review` §6
- `development-test-review` §6
- `development-code-review` §6

回归审查：

- 是否明确 Stage 4 C 维度 = planning review-passed + every task test_review_report pass + every task code_review_report pass？
- 是否清楚每个 review skill 只贡献自己的子层？
- 是否与 workflow-protocol §5.2 task 子状态序列一致？

#### M4: test-review / code-review 没声明 review_iteration 不适用 task-level review

修复定位：

- `development-test-review` §2
- `development-code-review` §2
- `development-planning-review` §9

回归审查：

- test-review / code-review 是否明确不使用 global `review_iteration`？
- 是否明确 task-level 三态 report 循环不计入 workflow-protocol §8 cap 7？
- planning-review 是否说明 review_iteration cap 仅适用 planning global review loop？
- 是否避免把 task-level fail/revise 误接到 global `review-issues`？

#### M5: 三态 report / verification-result 不需 Pending Changes 章节边界不明确

修复定位：

- `development-test-write` §4 / §5
- `development-code-write` §4.2 / §4.3 / §5
- `development-test-review` §5
- `development-code-review` §5

回归审查：

- 是否明确 test-review-report / code-review-report / verification-result 是一次性 doc，不需要 Pending Changes / Change Log？
- write skill 创建 skeleton / verification_result 时是否禁止添加 Pending/Change Log？
- review skill 填 report 时是否说明不操作 Pending/Change Log？
- 是否与 `change-log-format.md` §1 分类一致？

#### M6: code-write 职责混合 code write 与 verification submode

修复定位：

- `development-code-write` §1 Authority & Scope

回归审查：

- §1 是否把职责拆为 `Code Write Submode` 与 `Verification Submode` 两组？
- 拆分后是否与 §3 mode table / §5 procedure 对齐？
- 是否仍清楚 `development-code-write` 是 verification owner？

#### L1-L9 文档清理回归

请抽查以下低优先项是否已修或仍可接受：

- L1：planning-write §5 标题是否不再写 4-Step 但实际 5 步？（也可检查 test-write 是否顺手修）
- L2：planning-review §9 partial registration recovery 是否回指 §5 Step 5 / 幂等 retry？
- L3：test/code skeleton 是否明确 `status: draft` 与 `review_status: pending` 是独立字段？
- L4：code-write 是否说明 `src/` 不在 doc-guardian 管辖，source quality gate 由 code review + verification 承担？
- L5：claim task 是否定义为 progress.py task state transition，不是锁？
- L6：test-review/code-review Bug Flow rubric 是否 cross-link 到 corresponding write §7？
- L7：test/code review 的 diff/file scope convention 是否给出（detailed_design Files/Modules + breakdown ownership + git diff evidence）？
- L8：planning-write §3 是否说明 Bug Flow Replan 与 Direct Route 是平行二选一？
- L9：6 个 SKILL.md 的 Stage 4 特例 / no auto advance note 是否统一？

### 横向一致性重点

1. **Event whitelist**：所有 `--event <name>` 必须 ∈ {`write-complete`, `review-issues`, `review-passed`, `human-confirmed`}。Stage 4 test/code task review 不得用 global event 推 task 状态。
2. **Task transition calls**：test/code flow 必须使用 `progress.py update --task Tn --status <new>`。
3. **Gap-3 / Gap-4 status**：本轮仍不修改 `workflow-protocol` references；只要求 6 SKILL.md 正确声明 Task 6 前置。请不要把“command-reference 尚未补 transition”重复报为新的 High，除非 SKILL.md 声明仍不充分或自相矛盾。
4. **No manual progress.md**：所有 Gap-3 / Gap-4 / partial registration recovery 都必须禁止手工编辑 progress.md。
5. **Three-state report**：pending skeleton owner / pass-fail owner / blocking count / no Change Log / per-task path 是否全程一致。
6. **Global sub_state vs task_state**：planning 用 global review loop；planning pass 后 test/code/verification owner 判定看 `development_state.task_states[Tn]`；no auto advance note 是否一致。
7. **Bug Flow development re-entry**：BUG body `Affected Task(s)` 仍是当前事实源；无法定位 task → planning rebreakdown；测试遗漏 → test-write；source bug → code-write；verification fail 不走 bug-triage。

### 输出要求

保存到：`docs/review/skill_set_batch3b_round2_review.md`

格式：

```markdown
# Skill Set Batch 3b Round 2 Review (post-fix regression)

**Review Target**: 6 份 development-* SKILL.md
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch3b_review.md
**Round 1 Prompt**: docs/review/claude_review_prompt_batch3b.md
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: regression: <count> remaining; new findings: <H/M/L>; recommendation: (A)/(B)/(C)

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|----------|------|
| H1 Gap-4 verified task rollback | ✅/⚠️/❌ | ... |
| H2 Gap-3 verification fail rollback | ✅/⚠️/❌ | ... |
| M1 partial task registration recovery | ✅/⚠️/❌ | ... |
| M2 validate.py file/task registration boundary | ✅/⚠️/❌ | ... |
| M3 Stage 4 C composite | ✅/⚠️/❌ | ... |
| M4 review_iteration not task-level | ✅/⚠️/❌ | ... |
| M5 one-shot doc no Change Log | ✅/⚠️/❌ | ... |
| M6 code-write submodes | ✅/⚠️/❌ | ... |
| L1-L9 cleanup | ✅/⚠️/❌ | ... |

## New Findings (Round 2)

### High/Medium/Low: <title>

- **Location**: `<file>:<line>`
- **Baseline Reference**: <reference>
- **Dimension**: <dimension>
- **Issue**: <issue>
- **Impact**: <impact>
- **Recommendation**: <fix>

## Cross-Finding Consistency Check

[验证 H1-H2-M1-M2-M3-M4-M5-M6 修复之间没有互相打架；尤其 Gap-3/4 与 workflow-protocol references 的 staging 是否清楚。]

## Task State Machine Verification

[逐条验证 current command-reference transitions + declared Gap-3/4 staging；确认 SKILL.md 没有新增非法 transition call。]

## Three-State Review Report Verification

[验证 pending/pass/fail lifecycle + one-shot doc no Change Log + owner boundaries。]

## Bug Flow Development Re-entry Assessment

[验证 Gap-4 声明后 root_cause==development 仍可理解，且不会误导 implementer 手工回退 task。]

## Design Gap Status Update

[Gap-1 / Gap-2 / Gap-3 / Gap-4 状态表；明确哪些不阻塞 batch 3c，哪些是 Task 6 前置。]

## Recommendation

- **(A)**: 进 batch 3c（testing + delivery + retrospective write/review × 3）—— 0 High / 0 Medium，或仅余 Low / 已声明 Task 6 前置 gap
- **(B)**: 修后再评（再评 1 轮）—— 仍有 High 或 Medium ≥ 3
- **(C)**: 重设计 —— 触及已闭环架构层决策或 Stage 4 状态机需要大改
```

### 评审风格约束

- High = blocker，会导致 Task 6 实现错误、状态机不可达、三态 report bypass、Bug Flow development re-entry 崩盘。
- Medium = 设计/可实现性问题但有 workaround。
- Low = 文档清理 / 术语 / cross-reference / 可读性问题。
- Round 2 重点是回归和新引入风险，不要重复完整 Round 1。
- 已声明且本批不修的 Gap-3 / Gap-4 不应重复作为 High，除非 SKILL.md 声明缺失、推荐路径不清或出现绕过 progress.py 的描述。
- 评审完毕后给出明确 (A)/(B)/(C) recommendation。

请直接产出报告，不需要先和我对齐范围。
