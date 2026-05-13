# Codex Review Prompt — Task 5 Batch 1 (Round 5, Final)

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节）整段发给 codex。
> **本轮定位为评审循环的终轮**。如果通过，进 batch 2；如果未通过但 finding 不致命，强行进 Task 6 实现获取真实信号。

---

## Prompt Body

请第 5 轮评审 dev-workflow-skills2 项目的 Task 5 批 1 产出。第 4 轮评审（`docs/review/skill_set_batch1_round4_review.md`）发现 5 项 finding（1 High + 3 Medium + 1 Low），claude 已声称全部采纳并落地修复（见 `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md`）。

**本轮是 batch 1 评审的最后一轮**——4 轮评审已使 finding 数从 16 收敛到 5，High 从 8 收敛到 1。如果 round 5 通过，进 batch 2 batch；如果未通过，需要在"再 round"和"暂停评审进 Task 6 实际实现获信号"之间做权衡。

### 评审目标文件（与 round 4 相同 7 份）

主要审查：

- `skills/workflow-protocol/SKILL.md`
- `skills/workflow-protocol/references/command-reference.md`
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`
- `skills/doc-guardian/references/directory-layout.md`
- `skills/doc-guardian/references/required-artifacts.md`
- `skills/doc-guardian/references/change-log-format.md`

### 必读参考材料

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`
- `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md`（claude 对 5 项 round 4 finding 的处置说明）

历史评审（一致性参考）：

- `docs/review/skill_set_batch1_round4_review.md`
- `docs/review/skill_set_batch1_round3_review.md`
- `docs/review/skill_set_batch1_round2_review.md`
- `docs/review/skill_set_batch1_review.md`

### Round 5 评审重点

**优先级 1：Round 4 5 项 finding 验证**

按编号（H1 / M2 / M3 / M4 / L5）逐条验证修复是否到位、是否引入回归。每条 finding 报告：
- ✅ Resolved
- 🟡 Partially Resolved（说明残留）
- ❌ Not Resolved（说明原 finding 仍存在）
- ⚠ Resolved but introduced new issue（说明新引入的问题）

**优先级 2：Round 4 关键结构性改动验证**

claude 在 round 4 做了 3 个结构性改动，请重点验证：

1. **H1 三态不变量重写**（frontmatter-schema.md + SKILL.md）：
   - "三态约束块" 是否清晰？skeleton 状态（pending + 0 + low）是否真的合法？
   - SKILL.md §4.3 的 quick row 是否同步加 pending？
   - 关键不变量段是否替换原 "pass iff blocking=0" 全局规则？
   - 与 Stage 4 task `test-done` / `code-review-passed` 转移条件是否一致（pending/fail 都 reject，仅 pass 通过）？
   - validate.py 类 3/类 4 是否能按三态分支实现？

2. **M2 完整 DSL grammar**（required-artifacts.md）：
   - 6 个产生式（expr / or-expr / and-expr / primary / comparison / variable / literal 等）是否完整无歧义？
   - Enum literal 白名单 16 个值是否覆盖现有 conditions？
   - hyphenated literal 仅 RHS 接受的规则是否清晰？
   - 6 个 parser test cases 是否能驱动单元测试？

3. **M3 recover replay validator**（command-reference.md §4）：
   - terminal event 后任何 mutating entry → fatal 的算法是否可直接实现？
   - terminal event 定义是否清晰（仅 `incident-resolve --action abort/reconstruct`，还是含其他）？
   - "禁止 silent truncate" 是否在 SKILL.md 与 command-reference 一致？

**优先级 3：跨文件残余 inconsistency**

经过 4 轮迭代，主要风险是文档间残留不一致。重点排查：

- review_status 三态在所有文件（frontmatter-schema 详细 + SKILL summary + command-reference Stage 4 表 + workflow-protocol SKILL Stage 4 表）是否完全对齐
- DSL 字段（`srs.is_multi_module` / `srs.architecture_change`）在 srs schema、cheat sheet、SKILL summary、required-artifacts.md condition 4 处是否一致
- terminal recover 描述在 SKILL.md §9 和 command-reference §4 是否一致
- Stage 4 unconditional per-task validation 在 SKILL.md §7.1 和 required-artifacts.md §5 是否一致

**优先级 4：可实现性总检（最终）**

Python 实现者读完 7 份文件 + workflow spec v0.6 + 4 份 reviewer feedback response 后，能否**直接**实现 `progress.py`、`validate.py`、`changelog.py` 三个脚本？

请给出明确判断："可以"或"不可以 + 列出阻碍点"。

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

保存到：`docs/review/skill_set_batch1_round5_review.md`

格式：

```markdown
# Skill Set Batch 1 Round 5 Review (Final)

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Review History**: round 1 / 2 / 3 / 4
**Round 4 Response**: docs/review/reviewer_feedback_response_v0.8_batch1_round4.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结：例如 "5 项 round 4 findings: <verified count> resolved, <count> partially; <new count> new findings; recommendation: <proceed to batch 2 / fix and re-review / pause review and start Task 6 implementation>">

## Previous Findings Verification

按编号（H1 / M2 / M3 / M4 / L5）逐条验证。

| Finding | Severity | Round 4 Status | Round 5 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | pending invariant 冲突 | ✅/🟡/❌ | <说明> |
| M2 | Medium | DSL grammar 不完整 | ✅/🟡/❌ | <说明> |
| M3 | Medium | recover post-terminal 模糊 | ✅/🟡/❌ | <说明> |
| M4 | Medium | doc-guardian §7 不一致 | ✅/🟡/❌ | <说明> |
| L5 | Low | SRS 示例缺字段 | ✅/🟡/❌ | <说明> |

## New Findings (round 5 引入)

[每条新 finding 按统一格式，如无可写 "无新 finding"]

## Cross-File Consistency Check

特别检查 round 4 改动密集区：
- review_status 三态各文件对齐
- DSL 字段四处对齐
- terminal recover 跨文件描述
- Stage 4 unconditional validation 跨文件描述

## Implementability Assessment (Final)

**明确判断**：Python 实现者能否直接实现三个脚本？
- 如可，列 1-2 个建议关注点
- 如不可，列具体阻碍点

## Recommendation (Final)

明确建议下一步（必选其一）：

- (A) **进 batch 2** —— 当前契约已可实现，剩余问题（如有）属 batch 2/Task 6 中可修补
- (B) **再 round 6** —— 仍有 blocker，需要再迭代
- (C) **暂停 review 循环，进 Task 6 实际实现** —— 即使有 1-2 项 finding 残留，也建议直接实现获取真实信号；纯 spec 推演已收益递减

## Suggested Next Revision Order

如选 (B)，按优先级排序的 fix 顺序。如选 (A) 或 (C)，列 batch 2/Task 6 期间应继续关注的 watch list。

## Positive Notes

[列出 round 4 → round 5 的实质性改进；如已成熟可作为 batch 2 设计的良好基础，明确说明]
```

### 评审风格约束

- High = blocker（阻塞 batch 2 推进）
- Medium = 设计问题但有 workaround
- Low = 文档清理 / 风格问题
- 每条 finding 必须有具体 location 和可执行 recommendation
- **不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义"**
- 已在前几轮闭环过的决策（11 个子命令、test-review-report、Foreman 拆分、active-only S4、incident 路径、release version grammar、三态 review_status、DSL grammar 等）不再质疑结构合理性

**判定门槛（Round 5 终轮）**：

- 如果 finding 数 ≤ 3 且 **High = 0** → 建议 **(A) 进 batch 2**
- 如果 High = 1 且其他都是 Low → 建议 **(C) 暂停 review，进 Task 6**（避免无限 review 循环；实现层会暴露真实问题）
- 如果 High ≥ 2 → 建议 (B) 再 round 6（但请在 recommendation 中说明为什么本轮没收敛）

请直接产出报告，不需要先和我对齐范围。
