# Codex Review Prompt — Task 5 Batch 2 Round 2

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请对 dev-workflow-skills2 项目 Task 5 批 2 第 2 轮评审。本轮目标是**回归 round 1 的 5 项修复**（3 High + 2 Medium，全部采纳为 Option A，无 design 层扩展），并扫描修复引入的新一致性风险。

### Round 1 Review 与采纳记录（必读）

- `docs/review/skill_set_batch2_review.md`（round 1 review）
- `docs/review/reviewer_feedback_response_v0.9_batch2.md`（采纳记录 + 影响文件清单）

### 评审目标文件（同 round 1，7 份）

- `skills/scenario-dispatcher/SKILL.md`
- `skills/scenario-dispatcher/references/scenario-decision-tree.md`
- `skills/bug-triage/SKILL.md`
- `skills/bug-triage/references/root-cause-rubric.md`
- `skills/bug-triage/references/triage-decision-tree.md`
- `skills/workflow-evolution/SKILL.md`
- `skills/workflow-evolution/references/incident-analysis-template.md`

### 必读参考材料

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`
- `skills/workflow-protocol/SKILL.md` + `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md` + `skills/doc-guardian/references/frontmatter-schema.md` + `skills/doc-guardian/references/change-log-format.md` + `skills/doc-guardian/references/required-artifacts.md`
- `docs/handoff/session_handoff_20260506.md`

### 本轮评审重点（针对 5 项修复的 5 大回归点）

#### 回归 1：F1 PRD-exception INCIDENT skeleton 必经 changelog promote

**修复定位**：
- bug-triage SKILL.md §3.1 Step 7d / §5.1 Step 1-4 / §5.2 末段
- triage-decision-tree.md §2.1 Step 7 / §4.1 (promote 前后两态) / §4.3 (3 步必跑流程) / §7.4 Example D Step 11

**回归审查**：

- bug-triage 创建 INCIDENT skeleton 后是否**严格按序** `changelog.py promote → validate.py file → progress.py incident-start`？
- §4.1 模板的 "promote 前" 与 "promote 后" 两种状态展示是否清晰、不会让实现者混淆？
- §4.3 是否完整覆盖 validate 8 类 check 中适用 single-file 的 1-7 类？
- progress.py incident-start 内部是否会再次 validate INCIDENT 文件（双重保险）？这一点 SKILL.md 与 command-reference.md 是否一致？
- 7 个 examples 的 prd-exception 路径（Example D 在 root-cause-rubric.md / Example E in root-cause-rubric.md / Example A in incident-analysis-template.md / Example B in incident-analysis-template.md / Example C in incident-analysis-template.md）是否都体现了"先 promote 再 validate" 序列？

#### 回归 2：F2 active 非 testing 阶段报 bug 收敛 reject

**修复定位**：
- scenario-dispatcher SKILL.md §3 (decision flow 2d 子分支)、§5.1 (3 种情况)、§6.2 (Type B 路由表) / §6.3 (Type C 拒绝表新增一行)、§9 Forbidden Actions 末
- scenario-decision-tree.md §4.2 (S4 入口路径表 4 行)、§5 (dispatch_active_release report_bug 子分支扩 if/else)、§8.9 Example I 新增
- bug-triage SKILL.md §2.1 触发表第 2 行重写、§2.1 前置条件强化、§9 Forbidden Actions 末加 2 条
- triage-decision-tree.md §7.2 Example B 完全重写

**回归审查**：

- scenario-dispatcher 在 (current_stage, sub_state) ≠ (testing, review-passed) 时是否**所有路径**都 reject？特别检查 §3 decision flow / §5 sub-tree / §6 Output Contract / Examples 是否一致
- bug-triage active mode 入口前置是否与 progress.py bug-start 前置完全对齐？三层（dispatcher → bug-triage → progress.py）的前置 gate 是否一致？
- 是否还有任何残留路径建议"创建 known-issue BUG (target_release/root_cause null) 不调 progress.py"？这是 round 1 标记的 orphan doc 反模式
- "把现象记入当前 stage doc 的 known-issue 段" 提示对哪些 stage doc 适用？是否引用了 detailed_design / plan / breakdown 等具体 doc 类型？是否与 doc-guardian frontmatter-schema 的 doc 类型清单一致？
- §5 dispatch_active_release 伪代码是否能直接转 Python 实现？是否有未覆盖的 intent classification 边界？

#### 回归 3：F3 active mode 强制 4 类输出（删除 out-of-scope 第五路径）

**修复定位**：
- root-cause-rubric.md §4.4a 新增（强制 4 类规则 + 升级用户决策的 3 选项）、§7.4 Example D 完全重写

**回归审查**：

- bug-triage active mode 是否在所有相关章节明确"必须从 {srs, architecture, development, prd-exception} 选 1"？
- 是否完整列出"留 null / 写第五种值 / silent close" 三个反模式 + 各自被哪个 enforcement 拒绝（progress.py 参数一致校验 / doc-guardian validate / bug-triage 无子命令）？
- "用户判定 BUG 应撤销" 路径是否清晰？bug-triage 是否明确"无权撤销 BUG report"，用户必须**手动删除文件**？
- testing-write 是否被告知 post-deletion 责任（在 testing report 注明 out-of-scope）？此处与 testing-write skill 的协作是否需要同步标注？（注：testing-write 在 batch 3 才设计；本轮可标 advisory）
- §7.4 Example D 是否给实现者足够指引避免重蹈"out-of-scope 第五路径"覆辙？

#### 回归 4：F4 区分 advisory（允许）vs patch（禁止）

**修复定位**：
- workflow-evolution SKILL.md §8.2 重写（新增 allow/forbid 表）、§3.5 自评清单加 #10/#11/#12
- incident-analysis-template.md §1.2 §4 模板加 Action Item 提示、§3 自评清单加 #13/#14

**回归审查**：

- §8.2 的"允许 advisory"与"禁止 patch"边界是否表述清楚？是否有歧义路径让实现者再次混淆？
- §4 模板每条改进是否都需要标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle"？这与自评 #11 / #13 一致吗？
- retrospective consumption mode 的 output 模板（incident-analysis-template.md §5）是否同样应用 advisory vs patch 边界？是否需要也加 Action Item 标注？（**专项检查**）
- 自评清单 #12（SKILL.md）+ #14（incident-analysis-template.md）是否完全对齐？两份文件的清单顺序是否一致？
- workflow-evolution 用户对话中是否会被引诱进入 patch 模式（如用户说"帮我直接改 SKILL.md"）？§8.3 拒绝模板是否覆盖该场景？

#### 回归 5：F5 INCIDENT Finalization 单一原子序列

**修复定位**：
- workflow-evolution SKILL.md §3.1 Step 5/6/7 改写、§3.4 frontmatter 状态变化注解、§9 Forbidden Actions 末加 2 条
- incident-analysis-template.md §1.6 新增、§3 自评清单加 #15/#16

**回归审查**：

- Step 6.a-g 7 个子步骤序列是否完全一致地在 SKILL.md §3.1 + incident-analysis-template.md §1.6 描述？两份的字母编号 a-g 是否完全对应？
- "validate 后到 incident-resolve 之间禁止 doc 编辑" 是否在所有相关章节强调？是否有遗漏路径？
- 多次 promote / validate 重试场景是否覆盖（如 6.g validate fail → 修 → 6.f promote → 6.g validate）？
- progress.py incident-resolve 内部是否会再次 validate INCIDENT 文件？SKILL.md / incident-analysis-template.md / command-reference.md 三处描述是否一致？
- §9 Forbidden Actions 新增 2 条与 §3.1 Step 6 序列描述是否冗余？Forbidden 是否能独立读懂还是必须配 §3.1 才理解？

### 横向一致性检查（跨 finding）

1. **三层前置 gate 一致**：dispatcher → bug-triage active mode → progress.py bug-start 前置 (current_stage==testing AND sub_state==review-passed) 在所有相关章节是否一致？
2. **changelog promote / validate 顺序**：bug-triage 创建 BUG report（§4.1 / §4.2 of triage-decision-tree.md）+ 创建 INCIDENT skeleton（§4.3）+ workflow-evolution finalize INCIDENT（§3.1 Step 6）三处的 promote / validate 顺序是否一致？
3. **Action Item 标注**：incident-analysis-template.md §1.2 §4 模板 + §5 retrospective output 模板是否都覆盖 Action Item 提示？
4. **Forbidden Actions 数量**：scenario-dispatcher / bug-triage / workflow-evolution 三个 SKILL.md 的 Forbidden 各新增条数：1 / 2 / 2；是否完整覆盖修复点？

### 重点排查"修复引入的新风险"

- bug-triage 在 dispatcher 层 reject 后，是否还可能从其他入口被错误 invoke？（如 Bootstrap 检测 bug_flow.active=true 但 BUG.root_cause=null 的 retry 路径——见 SKILL.md §2.1 第 3 行）
- workflow-evolution finalization 序列改写后，**重 invoke 幂等性**（SKILL.md §7.2）是否仍正确？特别是 "INCIDENT body §3-§7 已填, resolution_action ∈ enum, status=review-passed, workflow_incident_active=true" 状态下重试 incident-resolve 是否安全？
- F4 修复后，retrospective consumption mode 输出建议时是否被同样的 advisory vs patch 约束覆盖？（incident-analysis-template.md §5 模板）
- F1 / F5 共享 `changelog.py promote` 调用模式：bug-triage 与 workflow-evolution 调 promote 时如果 doc 损坏（如 Pending entry 格式非法）的失败处理是否一致？

### 评审格式

保存到：`docs/review/skill_set_batch2_round2_review.md`

格式（沿用 round 1）：

```markdown
# Skill Set Batch 2 Round 2 Review (post-fix regression)

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch2_review.md
**Round 1 Response**: docs/review/reviewer_feedback_response_v0.9_batch2.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "regression: <count> remaining; recommendation: (A)/(B)/(C)">

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| F1 PRD-exception INCIDENT changelog | ✅ 已修 / ⚠️ 部分残留 / ❌ 未修 | <具体描述> |
| F2 active 非 testing reject | ... | ... |
| F3 4 类强制 | ... | ... |
| F4 advisory vs patch | ... | ... |
| F5 finalization 序列 | ... | ... |

## New Findings (Round 2)

### High/Medium/Low: <一句话标题>
- **Location**: ...
- **Issue**: ...
- **Impact**: ...
- **Recommendation**: ...

[每条 finding 一节]

## Cross-Finding Consistency Check

[5 项修复之间是否引入新的协作不一致]

## Recommendation

- **(A)**: 进 batch 3（17 个 vertical skill）—— 0 New High，且 Round 1 Findings 全部 ✅ 已修
- **(B)**: 修后再评（再评 1 轮）—— 有 New High 或 Round 1 残留
- **(C)**: 重设计（design level 问题）—— 触及架构层决策
```

### 评审风格约束

- 优先做**回归测试**：5 项修复是否完整落地到所有相关文件
- 重点抓"修复引入的新一致性风险"，不重复 Round 1 已闭环的 8 个评审维度（如 spec/design 一致性、authority 标注等）
- 已经在 Round 1 闭环的决策（如 4 类强制、advisory 边界、reject 路径）不需要重新质疑结构合理性，只检查文档落实是否完整
- handoff §11：批 2 计划评审 2-3 轮；本轮如全部 ✅ 已修 + 0 High new finding，建议 (A) 进 batch 3

请直接产出报告，不需要先和我对齐范围。
