# Codex Review Prompt — Task 5 Batch 1

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请评审 dev-workflow-skills2 项目的 Task 5 批 1 产出（workflow-protocol 和 doc-guardian 两个 skill 的完整 SKILL.md + 关键 references），按之前 v0.x review 的格式输出评审报告。

### 评审目标文件

主要审查（4 份）：

- `skills/workflow-protocol/SKILL.md`
- `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`

### 必读参考材料

判断"是否符合 spec / design"时必读：

- `docs/workflow/workflow_specification_claude.md` (v0.5)
- `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计方案）
- `docs/review/reviewer_feedback_response_v0.4.md`（上一轮采纳记录，了解最近决策）

可选参考（理解评审风格）：

- `docs/review/skill_set_design_proposal_v0.4_rereview.md`
- `docs/review/skill_set_design_proposal_v0.3_rereview.md`

### 评审维度

请覆盖以下 8 个维度，每条 finding 必须明确归属于其中一个或多个：

1. **Spec/Design 一致性**：SKILL.md 描述是否与 workflow spec v0.5 + design proposal v0.5 一致？特别检查：
   - 11 个 progress.py 子命令的 mutation 是否完全匹配 design proposal Section 4.4
   - frontmatter schema 的 per-type 字段是否完全匹配 design proposal Section 5.3
   - P6 stage done 矩阵 5 维度（A/B/C/D/E）是否一致
   - S3 必备 source-system-analysis artifacts 列表是否一致

2. **内部一致性**：4 份文件之间、单文件内部是否有矛盾？例如：
   - SKILL.md 主文档与 references 是否对得上
   - 状态机转移表与 mutation 描述是否一致
   - validate.py 8 类 check 在 SKILL.md 与 frontmatter-schema 之间描述是否一致

3. **完整性**：SKILL.md 是否覆盖了所有契约细节，使 Task 6 实现者能基于此规范落地？特别检查：
   - 11 个子命令的前置条件是否全部明确
   - 错误处理路径是否清晰
   - 边界 case 是否覆盖（如 init 时 workflow_version 默认值、recover 在 history 不完整时的行为、bug-start 时已有未解决 incident 的冲突）

4. **可实现性**：Python 实现者读这份 SKILL.md / references 能否直接动手写 progress.py 和 validate.py？哪些地方语义模糊导致实现者会做不一致选择？

5. **简洁度（避开 foreman 690 行 SKILL.md 反模式）**：4 份文件是否过长？哪些章节可拆到 references？哪些信息冗余？

6. **跨 skill 引用一致性**：workflow-protocol 引用 doc-guardian 的 validate.py，doc-guardian 引用 workflow-protocol 的 progress.py，这些 cross-reference 是否准确？路径、命令、子命令名称是否完全对得上？

7. **Forbidden Actions 完整性**：每份 SKILL.md 都有 Forbidden Actions 清单。是否有明显的 bypass 路径未被列入？例如 agent 能否通过：
   - 不调 progress.py 直接写 progress-history.md
   - 跳过 changelog.py promote 直接编辑 Change Log 章节
   - 不通过 bug-start 直接修改 bug_flow.active

8. **边界状态处理**：以下边界 case 是否有清晰处理路径？
   - PRD root-cause exception → workflow-incident-analysis 流程
   - project_state ∈ {aborted, reconstructing} 终态
   - post-close 期间的 bug intake
   - Stage 4 多 task 并发时的 progress.md 更新冲突
   - review_iteration 超过 7 时的升级路径
   - release-start 时 unresolved_bugs 自动 consume + BUG-NNN.md 加 consumed_in_release 字段

### 输出要求

保存到：`docs/review/skill_set_batch1_review.md`

格式（参考之前 v0.x review）：

```markdown
# Skill Set Batch 1 Review (workflow-protocol + doc-guardian)

**Review Target**: 4 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "blocking issues: <count>; needs fix before Task 5 batch 2">

## Findings

### High/Medium/Low: <一句话标题>

- **Location**: <file>:<line>, ...
- **Baseline Reference**: <相关 spec/design 行号>，如有
- **Issue**: <具体描述>
- **Impact**: <实现时会导致什么问题>
- **Recommendation**: <具体修复建议；2 选项时列出取舍>

[每条 finding 一节]

## Cross-Skill Consistency Check

[专门一节列举 workflow-protocol 与 doc-guardian 之间的 cross-reference 是否对齐]

## Implementability Assessment

[评估 Python 实现者能否直接基于此规范实现，列出语义模糊点]

## Positive Notes

[列出做得好的设计决策；不强制]

## Suggested Next Revision Order

[按优先级排序的 fix 顺序]
```

### 评审风格约束

- **High** = blocker，会导致 Task 6 实现错误或实现者无法决策；不修不能进 batch 2
- **Medium** = 设计问题但有 workaround；可在批 2 设计期间补
- **Low** = 文档清理 / 风格问题；不阻塞
- Finding 数量不限，但每条必须有具体 location 和可执行 recommendation
- 不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义"
- 已经在 v0.5 design 闭环过的决策（如 11 个子命令的存在、Foreman 拆分等）不需要 revisit

请直接产出报告，不需要先和我对齐范围。
