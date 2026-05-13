# Codex Review Prompt — Task 5 Batch 1 (Round 3)

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节）整段发给 codex。

---

## Prompt Body

请第 3 轮评审 dev-workflow-skills2 项目的 Task 5 批 1 产出。第 2 轮评审（`docs/review/skill_set_batch1_round2_review.md`）发现 9 项新 finding（4 High + 4 Medium + 1 Low），claude 已声称全部采纳并落地修复（见 `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md`）。本轮目标：**验证 9 项 round 2 finding 是否真修复 + 检查修复是否引入新连带问题 + 评估当前是否可进 batch 2**。

### 评审目标文件（与 round 2 相同 7 份）

主要审查：

- `skills/workflow-protocol/SKILL.md`
- `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`
- `skills/doc-guardian/references/directory-layout.md`
- `skills/doc-guardian/references/required-artifacts.md`
- `skills/doc-guardian/references/change-log-format.md`

### 必读参考材料

判断"是否符合 spec / design"时必读：

- `docs/workflow/workflow_specification_claude.md` (v0.6，含 round 2 H4 修正)
- `docs/design/skill_set_design_proposal_v0.5.md`（design 仍 v0.5；本轮 batch 1 修复未升级 design proposal）
- `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md`（claude 对 9 项 round 2 finding 的处置说明）

历史评审（参考一致性）：

- `docs/review/skill_set_batch1_round2_review.md`（round 2 发现的 9 项，本轮逐条验证）
- `docs/review/skill_set_batch1_review.md`（round 1 历史记录）
- `docs/review/reviewer_feedback_response_v0.5_batch1.md`（round 1 的处置）

### Round 3 评审重点

**优先级 1：Round 2 9 项 finding 验证**

按 finding 编号（H1/H2/H3/H4/M5/M6/M7/M8/L9）逐条验证修复是否到位、是否引入回归。每条 finding 报告：
- ✅ Resolved
- 🟡 Partially Resolved（说明残留）
- ❌ Not Resolved（说明原 finding 仍存在）
- ⚠ Resolved but introduced new issue（说明新引入的问题）

输出表格放在报告 "Previous Findings Verification" 节。

**优先级 2：Round 2 关键决策的可实现性验证**

claude 在 round 2 做了几个关键设计决策，请重点验证它们是否真的让实现确定性：

1. **H1 Condition DSL**（required-artifacts.md 新增）：
   - 6 个白名单变量、5 个运算符、3 类字面量是否完整覆盖现有 condition（如 `scenario == S3`、`srs.is_multi_module == true`）？
   - 是否有现存 condition 用了白名单外的语法？
   - DSL parser 实现者是否能直接按规范写 simple parser（无歧义）？

2. **H2 incident-start 双参数签名**：
   - SKILL.md / command-reference / Forbidden Actions 三处的命令签名是否完全一致？
   - 旧 `--report <path>` 单参数版本是否已彻底清除？

3. **H3 incident-resolve continue 简化**：
   - command-reference 是否真的删了 `--bug-flow keep|clear`？
   - SKILL.md 任何遗留的 keep/clear 提及是否已清理？
   - `resolution_action: continue` 是否仍为 enum 中合法值（无新增 `continue-keep` / `continue-clear`）？

4. **H4 Workflow spec S3 Technical Debt**：
   - workflow spec line 144 是否改为"S3 推荐"？
   - workflow spec 其他位置（§4.9 P6 矩阵 / Possible Supporting Artifacts 表）是否同步？

5. **M5 sub_state nullable + workflow_version v0.6 + recover 语义**：
   - SKILL.md schema 是否真的允许 `sub_state: null`？
   - `workflow_version: v0.6` 是否所有引用处一致？
   - Forbidden Actions 是否明确"recover 在 terminal state 是唯一允许 repair mutation 但不得改 project_state 终态"？

6. **M6 Stage 4 unconditional validation**：
   - required-artifacts.md 是否真的删了 `task_substate_required` 字段？
   - command-reference Stage 4 advance 描述是否同步为"无条件全校验"？
   - 是否有遗留 `substate_matches` 函数引用？

7. **M7 test-review-report 生命周期**：
   - frontmatter-schema.md 的"生命周期 owner"表是否清晰说明 write/review skill 各自字段填充责任？
   - skeleton 默认值是否合理（counts=0、review_status=pass 待覆盖）？

8. **M8 ID 标准化**：
   - regex 是否真的强制 `^(CR|BUG|INCIDENT)-\d{3}$` 3 位 zero-padded？
   - directory-layout 路径模板是否改为 `{cr_id}` / `{bug_id}` / `{incident_id}` 形式？
   - frontmatter-schema 的 ID References 小节（区别于 Path References）是否清晰？

9. **L9 Path Convention Note**：
   - 两个 SKILL.md 顶部是否都加了 Path Convention Note？

**优先级 3：新连带问题**

修复 9 项可能引入的新问题，重点排查：

- **DSL 与 frontmatter schema 字段一致性**：condition DSL 引用 `srs.is_multi_module` / `srs.architecture_change` 这两个新加 SRS 字段，validate.py 类 5 是否需要校验这两个字段存在且 bool 合法？
- **continue 简化后的 PRD exception 退出路径**：用户场景"workflow 改了但原 bug 仍需修"是否真的可以通过"创建新 BUG"处理，还是有边界 case 漏掉？
- **Stage 4 unconditional validation 与 task 中间状态的关系**：如果某 task 还在 `code-writing`，advance 时校验 code_review_report.md 不存在 → 失败。这是预期的（task 必须 verified 才允许 advance），但 error message 是否对实现者友好？
- **ID 3 位 zero-pad 强制后**：如果未来 BUG 数量超 999 怎么办？规范是否说了 4 位扩展规则？

**优先级 4：可实现性总检**

Python 实现者读完 7 份文件 + workflow spec v0.6 后，能否直接实现 `progress.py`（含 11 个子命令完整 mutation）和 `validate.py`（含 8 类 check + ID lookup）+ `changelog.py`（promote）？哪些地方仍语义模糊？

### 评审维度（沿用前几轮）

1. Spec/Design 一致性
2. 内部一致性
3. 完整性
4. 可实现性
5. 简洁度
6. 跨 skill 引用一致性
7. Forbidden Actions 完整性
8. 边界状态处理

### 输出要求

保存到：`docs/review/skill_set_batch1_round3_review.md`

格式：

```markdown
# Skill Set Batch 1 Round 3 Review

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch1_review.md
**Round 1 Response**: docs/review/reviewer_feedback_response_v0.5_batch1.md
**Round 2 Review**: docs/review/skill_set_batch1_round2_review.md
**Round 2 Response**: docs/review/reviewer_feedback_response_v0.6_batch1_round2.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结：例如 "9 项 round 2 findings: <verified count> resolved, <count> partially, <count> not resolved; <new count> new findings; recommendation: <proceed to batch 2 / fix and re-review>">

## Previous Findings Verification

按编号（H1-H4 / M5-M8 / L9）逐条验证。

| Finding | Severity | Round 2 Status | Round 3 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | DSL 字段未定义 | ✅/🟡/❌ | <说明> |
| H2 | High | 旧 incident 签名残留 | ✅/🟡/❌ | <说明> |
| H3 | High | --bug-flow 引入未定义字段 | ✅/🟡/❌ | <说明> |
| H4 | High | spec body Technical Debt | ✅/🟡/❌ | <说明> |
| M5 | Medium | terminal state 不一致 | ✅/🟡/❌ | <说明> |
| M6 | Medium | substate_matches 模糊 | ✅/🟡/❌ | <说明> |
| M7 | Medium | test-review owner 模糊 | ✅/🟡/❌ | <说明> |
| M8 | Medium | ID/path 不一致 | ✅/🟡/❌ | <说明> |
| L9 | Low | shorthand 残留 | ✅/🟡/❌ | <说明> |

## New Findings (round 3 引入)

[每条新 finding 按 round 1/2 格式]

## Cross-File Consistency Check

7 份文件之间的引用、术语、字段、命令一致性 check（特别检查 DSL 字段、incident 签名、ID 格式三个 round 2 重点修改区域）。

## Implementability Assessment (Round 3 更新)

整体能否进入 Task 6 实现？哪些剩余语义模糊点需要进一步澄清？

## Recommendation

明确建议下一步：
- (A) 通过，可进 batch 2
- (B) 修复 N 项后再 round 4
- (C) 设计层面有问题，需要回 design proposal 评审

## Suggested Next Revision Order

按优先级排序的 fix 顺序（如有）。

## Positive Notes

[列出 round 2 → round 3 的实质性改进]
```

### 评审风格约束

- High = blocker（阻塞 batch 2 推进）
- Medium = 设计问题但有 workaround
- Low = 文档清理 / 风格问题
- 每条 finding 必须有具体 location 和可执行 recommendation
- **不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义"**
- 已经在 round 1/2 闭环过的决策（如 11 个子命令、test-review-report、Foreman 拆分）不再质疑结构合理性，只验证落地一致性
- **判定门槛**：如果 round 3 finding 数 ≤ 4 且 High ≤ 1，建议 (A) 通过进 batch 2；如果 High ≥ 2，建议 (B) 再 round 4

请直接产出报告，不需要先和我对齐范围。
