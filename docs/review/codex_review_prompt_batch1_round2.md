# Codex Review Prompt — Task 5 Batch 1 (Round 2)

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节）整段发给 codex。

---

## Prompt Body

请第 2 轮评审 dev-workflow-skills2 项目的 Task 5 批 1 产出。第 1 轮评审（`docs/review/skill_set_batch1_review.md`）发现 16 项 finding（8 High + 5 Medium + 3 Low），claude 已声称全部采纳并落地修复（见 `docs/review/reviewer_feedback_response_v0.5_batch1.md`）。本轮目标：**验证 16 项 finding 是否真修复 + 检查修复是否引入新连带问题 + 评估当前是否可进 batch 2**。

### 评审目标文件

主要审查（**7 份**，比第 1 轮新增 3 份 reference）：

- `skills/workflow-protocol/SKILL.md`
- `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`
- `skills/doc-guardian/references/directory-layout.md`（**新增**，承担 F1）
- `skills/doc-guardian/references/required-artifacts.md`（**新增**，承担 F1 + F4 artifact map 角色）
- `skills/doc-guardian/references/change-log-format.md`（**新增**，承担 F1）

### 必读参考材料

判断"是否符合 spec / design"时必读：

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`（design 仍是 v0.5；本轮 batch 1 修复未升级 design proposal）
- `docs/review/reviewer_feedback_response_v0.5_batch1.md`（claude 对 16 项 finding 的处置说明）

历史评审（参考风格 + 验证修复一致性）：

- `docs/review/skill_set_batch1_review.md`（第 1 轮发现的 16 项，本轮逐条验证）

### Round 2 评审重点

**优先级 1：第 1 轮 16 项 finding 验证**

按 finding 编号逐条验证修复是否到位、是否引入回归。每条 finding 报告：
- ✅ Resolved
- 🟡 Partially Resolved（说明残留）
- ❌ Not Resolved（说明原 finding 仍存在）
- ⚠ Resolved but introduced new issue（说明新引入的问题）

输出表格放在报告 "Previous Findings Verification" 节。

**优先级 2：新连带问题**

修复 16 项可能引入的新问题，重点排查：

1. **3 个新 reference 文件的内部一致性**：directory-layout.md / required-artifacts.md / change-log-format.md 之间、与 SKILL.md / frontmatter-schema.md 之间是否一致
2. **F8 `--event` 白名单的完整性**：4 个事件（write-complete / review-issues / review-passed / human-confirmed）是否覆盖所有合法 sub_state 转换；状态机转移表 §状态机转移合法性表 是否能用纯 `--event` 完成全部转换
3. **F2 incident-start 自闭路径**：新前置（`bug_flow.active==false` + BUG frontmatter `root_cause==prd-exception` + INCIDENT skeleton 存在）能否真的从 testing 状态走通；bug-triage 创建 INCIDENT skeleton 的责任是否清晰
4. **F4 artifact 来源 map**：required-artifacts.md 的 condition DSL（`scenario == S3` / `srs.is_multi_module == true` 等）实现者能否解析；condition 求值需要的字段（如 `srs.is_multi_module`）是否在对应 frontmatter schema 中定义
5. **F7 test-review-report**：与 code-review-report 完全对称，但 `development-test-write` 写测试代码 + 写 test_review_report skeleton 的双重职责是否清晰；测试代码 quality 评审标准（覆盖度 / 边界 / mock 合理性等）由谁定义
6. **F11 terminal state cleanup**：abort/reconstruct 后 progress.md 是否真的所有受影响字段都清理；recover 命令在 terminal state 下的行为是否定义

**优先级 3：可实现性总检**

Python 实现者读完 7 份文件后，能否直接实现 `progress.py`（含 11 个子命令完整 mutation）和 `validate.py`（含 8 类 check + ID reference lookup）？哪些地方仍语义模糊？

### 评审维度（沿用 round 1）

1. Spec/Design 一致性
2. 内部一致性
3. 完整性
4. 可实现性
5. 简洁度
6. 跨 skill 引用一致性
7. Forbidden Actions 完整性
8. 边界状态处理

### 输出要求

保存到：`docs/review/skill_set_batch1_round2_review.md`

格式：

```markdown
# Skill Set Batch 1 Round 2 Review

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch1_review.md
**Round 1 Response**: docs/review/reviewer_feedback_response_v0.5_batch1.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "16 项 round 1 findings: <verified count> resolved, <count> partially, <count> not resolved; <new count> new findings; recommendation: <proceed to batch 2 / fix and re-review>">

## Previous Findings Verification

按编号逐条验证。

| Finding | Severity | Round 1 Status | Round 2 Status | Notes |
|---------|----------|----------------|----------------|-------|
| F1 | High | 3 ref missing | ✅ Resolved | 3 文件创建并相互一致 |
| F2 | High | PRD exception 不可达 | ✅/🟡/❌ | <说明> |
| ... |

## New Findings (round 2 引入)

### High/Medium/Low: <一句话标题>

- **Location**: <file>:<line>
- **Baseline Reference**: <相关 spec/design 行号>
- **Issue**: <具体描述>
- **Impact**: <实现时会导致什么问题>
- **Recommendation**: <具体修复建议>

[每条新 finding 一节]

## Cross-File Consistency Check (新增)

7 份文件之间的引用、术语、字段、命令是否一致？特别检查：
- 4 个原文件 vs 3 个新 reference 之间
- required-artifacts.md DSL 与 frontmatter-schema.md condition 字段（`srs.is_multi_module` 等）

## Implementability Assessment (Round 2 更新)

整体能否进入 Task 6 实现？哪些剩余语义模糊点需要进一步澄清？

## Recommendation

明确建议下一步：
- (A) 通过，可进 batch 2
- (B) 修复 N 项后再 round 3
- (C) 设计层面有问题，需要回 design proposal 评审

## Suggested Next Revision Order

按优先级排序的 fix 顺序（如有）。

## Positive Notes

[列出 round 1 → round 2 的实质性改进，作为正向反馈]
```

### 评审风格约束

- High = blocker（阻塞 batch 2 推进）
- Medium = 设计问题但有 workaround（可在 batch 2 期间补）
- Low = 文档清理 / 风格问题（不阻塞）
- 每条 finding 必须有具体 location 和可执行 recommendation
- **不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义"**
- 已经在 round 1 闭环过的决策（如 11 个子命令存在、test-review-report 加入等）不需要再质疑结构合理性，只需验证落地一致性
- 如果 round 2 的 finding 数量明显少于 round 1（如 < 4 项 High + < 3 Medium），建议结论为 "可进 batch 2"

请直接产出报告，不需要先和我对齐范围。
