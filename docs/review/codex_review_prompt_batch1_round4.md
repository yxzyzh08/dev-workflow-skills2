# Codex Review Prompt — Task 5 Batch 1 (Round 4)

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节）整段发给 codex。

---

## Prompt Body

请第 4 轮评审 dev-workflow-skills2 项目的 Task 5 批 1 产出。第 3 轮评审（`docs/review/skill_set_batch1_round3_review.md`）发现 5 项 finding（2 High + 2 Medium + 1 Low），claude 已声称全部采纳并落地修复（见 `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md`）。本轮目标：**验证 5 项 round 3 finding 是否真修复 + 检查 round 3 结构性改动是否引入新连带问题 + 评估当前是否可进 batch 2**。

### 评审目标文件（与 round 3 相同 7 份）

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
- `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md`（claude 对 5 项 round 3 finding 的处置说明）

历史评审（参考一致性）：

- `docs/review/skill_set_batch1_round3_review.md`
- `docs/review/skill_set_batch1_round2_review.md`
- `docs/review/skill_set_batch1_review.md`

### Round 4 评审重点

**优先级 1：Round 3 5 项 finding 验证**

按编号（H1/H2/M3/M4/L5）逐条验证修复是否到位、是否引入回归。每条 finding 报告：
- ✅ Resolved
- 🟡 Partially Resolved（说明残留）
- ❌ Not Resolved（说明原 finding 仍存在）
- ⚠ Resolved but introduced new issue（说明新引入的问题）

输出表格放在报告 "Previous Findings Verification" 节。

**优先级 2：Round 3 关键结构性改动验证**

claude 在 round 3 做了 3 个有结构性影响的决策，请重点验证连带正确性：

1. **H1 White-list parser 重写**（required-artifacts.md §12）：
   - 新 grammar 是否完整覆盖现有 conditions（`scenario == S3`、`srs.is_multi_module == true` 等）？
   - tokenize / parse / evaluate 三函数职责划分是否清晰、Python 实现者按伪码能写出 unit-testable 的 parser？
   - 6 个白名单变量、5 个运算符、3 类 literal 是否完整？是否有 condition 用了白名单外语法？
   - 旧 `substate_matches` / `task_substate_required` 字段是否在所有文件中彻底清除（含 SKILL.md / command-reference / frontmatter-schema / directory-layout）？
   - Stage 4 unconditional validation 在 command-reference 状态机和 SKILL.md 中是否一致表达？

2. **H2 review_status enum 加 pending**（frontmatter-schema.md + 引用处）：
   - `code-review-report` 与 `test-review-report` 是否都改为 `pending | pass | fail`？
   - skeleton 默认 `pending` 是否在两份 schema、SKILL summary、command-reference Stage 4 状态表 4 处一致？
   - Stage 4 task `test-done` / `code-review-passed` 转移条件是否严格要求 `review_status: pass`（明确 reject pending 和 fail）？
   - Forbidden Actions 是否覆盖"不得在 review skill 未填 review_status 前推进 task state"？
   - validate.py 类 3 / 类 4 是否需要校验 enum 新增 pending 值（即接受 pending 为合法 status）？
   - 是否有遗留的 "review_status: pass" 默认值文档（如 SKILL.md 旧 summary）？

3. **M3 recover terminal 语义**（command-reference §4）：
   - terminal state 下 recover 必须保持 `project_state` 终态的规则是否清晰？
   - SKILL.md §9 Project Terminal State 与 command-reference §4 表述是否一致（无矛盾）？
   - replay history 算法是否能保证 `project_state: aborted` 的 history 重建后仍是 aborted？

**优先级 3：新连带问题排查**

- **`pending` 状态的 doc lifecycle**：skeleton 创建后 doc 自身的 `status` 字段是 `draft` 还是 `in-review`？`development-test-write` 完成 skeleton 时是否触发任何 `progress.py update --event` 事件？如果是 `write-complete` 事件，对应 task state 应转 `test-review`，但此时 review skill 还没运行——这个时序如何处理？
- **DSL grammar 的 enum 字面量**：grammar 写"S1/S3 等 enum 不带引号"，但实际 condition 写 `scenario == S3`（裸 S3 token）。tokenizer 如何区分 enum 字面量 vs identifier？是否需要预定义 enum literal 集合？
- **Stage 4 unconditional validation 的副作用**：当某 task 还在 `code-writing`，`progress.py update --advance` 会校验 code_review_report.md 不存在 → fail。但用户实际意图可能是查询其他 task 是否 done（误用 advance）。错误信息是否对实现者友好？是否要在 `update --advance` 之前加 dry-run 模式？
- **terminal recover 的 history 完整性**：如果 history 在 abort 后还有手工 entry（误编辑），recover 重建会 replay 那些 entry 吗？规范是否说了 "recover 只 replay 到第一个 terminal event"？

**优先级 4：可实现性总检**

Python 实现者读完 7 份文件 + workflow spec v0.6 + reviewer feedback v0.5/v0.6/v0.7 后，能否直接实现 `progress.py`、`validate.py`、`changelog.py` 三个脚本？哪些地方仍语义模糊？

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

保存到：`docs/review/skill_set_batch1_round4_review.md`

格式：

```markdown
# Skill Set Batch 1 Round 4 Review

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1-3 History**: docs/review/skill_set_batch1_review.md / skill_set_batch1_round2_review.md / skill_set_batch1_round3_review.md
**Round 1-3 Responses**: docs/review/reviewer_feedback_response_v0.5_batch1.md / v0.6_batch1_round2.md / v0.7_batch1_round3.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结：例如 "5 项 round 3 findings: <verified count> resolved, <count> partially; <new count> new findings; recommendation: <proceed to batch 2 / fix and re-review>">

## Previous Findings Verification

按编号（H1 / H2 / M3 / M4 / L5）逐条验证。

| Finding | Severity | Round 3 Status | Round 4 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | DSL Hint + substate_matches 残留 | ✅/🟡/❌ | <说明> |
| H2 | High | skeleton 默认 pass 可绕过 | ✅/🟡/❌ | <说明> |
| M3 | Medium | command-reference v0.6 未同步 | ✅/🟡/❌ | <说明> |
| M4 | Medium | SRS bool 字段未同步 cheat sheet | ✅/🟡/❌ | <说明> |
| L5 | Low | ID 文案 + >999 模糊 | ✅/🟡/❌ | <说明> |

## New Findings (round 4 引入)

[每条新 finding 按统一格式]

## Cross-File Consistency Check

7 份文件之间的引用、术语、字段、命令一致性 check（特别检查 round 3 改动密集区：DSL grammar 一致性、pending enum 各处对齐、terminal recover 跨文件描述）。

## Implementability Assessment

整体能否进入 Task 6 实现？哪些剩余语义模糊点需要进一步澄清？

## Recommendation

明确建议下一步：
- (A) 通过，可进 batch 2
- (B) 修复 N 项后再 round 5
- (C) 设计层面有问题，需要回 design proposal 评审

## Suggested Next Revision Order

按优先级排序的 fix 顺序（如有）。

## Positive Notes

[列出 round 3 → round 4 的实质性改进]
```

### 评审风格约束

- High = blocker（阻塞 batch 2 推进）
- Medium = 设计问题但有 workaround
- Low = 文档清理 / 风格问题
- 每条 finding 必须有具体 location 和可执行 recommendation
- **不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义"**
- 已在前几轮闭环过的决策（11 个子命令、test-review-report、Foreman 拆分、active-only S4、incident 路径、release version grammar）不再质疑结构合理性，只验证落地一致性
- **判定门槛（本轮收紧）**：
  - 如果 round 4 finding 数 ≤ 3 且 **High = 0** → 建议 (A) 通过进 batch 2
  - 如果 High ≥ 1 或 finding > 3 → 建议 (B) 再 round 5
  - 如果发现结构性 design 问题（不只是 SKILL.md 文档问题）→ (C)

请直接产出报告，不需要先和我对齐范围。
