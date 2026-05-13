# Reviewer Feedback Response — Batch 1 Round 2 SKILL.md Review

**Source Review**: `docs/review/skill_set_batch1_round2_review.md`
**Adopted In**: `skills/workflow-protocol/*` + `skills/doc-guardian/*` (round 2 修订到位)
**Workflow Spec Update**: `docs/workflow/workflow_specification_claude.md` (v0.6 正文 Technical Debt 修正)
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 1 第 2 轮

---

## Findings 处置一览（9 项新 finding）

| # | Severity | Finding 摘要 | 处置 | 关键决策 |
|---|----------|---------------|------|---------|
| H1 | High | required-artifacts DSL 引用未定义 SRS 字段 | **采纳** | srs frontmatter 加 `is_multi_module: bool` + `architecture_change: bool`；DSL 加 condition 规范（白名单 parser，禁止裸 eval）|
| H2 | High | workflow-protocol SKILL.md 仍含旧 incident 命令签名 | **采纳** | 主 SKILL.md 表格全部更新为 `incident-start --bug <bug-path> --report <incident-path>`；Forbidden 加旧签名禁用项 |
| H3 | High | `incident-resolve --bug-flow keep\|clear` 引入未定义字段 | **采纳 Option B（简化）** | 删 `--bug-flow` 子参数；continue **只允许一种 mutation**——清空 bug_flow + 回 testing；reclassification 由用户创建新 BUG 触发 |
| H4 | High | workflow spec v0.6 正文 Technical Debt 仍标 S3 必备 | **采纳** | 改 spec line 144 为"S3 推荐"，与 7 份目标文件对齐 |
| M5 | Medium | terminal state schema/cleanup/recover 不一致 | **采纳** | sub_state enum 加 null；workflow_version v0.5→v0.6；recover 改"terminal state 唯一允许 repair mutation，不得改变 project_state 终态语义" |
| M6 | Medium | Stage 4 substate_matches 模糊 | **采纳简化** | 删 `task_substate_required` 字段；Stage 4 advance **无条件校验全部 4 个 per-task artifacts**；task 子状态合法性由 `update --task` 状态机保证 |
| M7 | Medium | test-review-report owner 模糊 | **采纳** | frontmatter-schema 明示生命周期表：`development-test-write` 创建 skeleton（counts=0、review_status=pass），`development-test-review` 填 findings + review_status |
| M8 | Medium | ID/path/zero-padding 不一致 | **采纳** | ID regex 强制 `^(CR\|BUG\|INCIDENT)-\d{3}$`（3 位 zero-padded）；directory-layout 模板改 `{cr_id}`/`{bug_id}`/`{incident_id}`；frontmatter-schema 加 ID References 小节，triggered_by_bug 移出 Path References |
| L9 | Low | SKILL.md shorthand 残留 | **采纳** | 两个 SKILL.md 顶部加 Path Convention Note；display-only 简写明示 |

9 项全采纳，无反驳。

## 关键决策详解

### H3：选 Option B（简化）—— continue 单一行为

reviewer 给了两个选项：
- **A**：扩展 schema，加 `workflow-incident.resolution_detail: keep|clear`、BUG `resolved_by_workflow_change` / `final_status` 字段
- **B**：简化 continue，只允许一个确定路径（清空 bug_flow），reclassification 由新 BUG 触发

选 B 理由：

1. **少加 schema 字段**：避免引入跨 skill 一致性维护负担
2. **职责清晰**：incident-resolve continue 的语义是"workflow 改了，回到正常流程"；如果原 bug 仍需修复，那是新一轮 bug-triage 的事，不是 incident-resolve 的事
3. **可观察性**：新 BUG 触发新 BUG-MMM.md + 新 bug-triage event，比"原 BUG 加 status 字段隐式重启"更易 debug
4. **Bypass 风险低**：只一个 mutation 路径，无歧义

代价：用户在罕见的"workflow 修了 + 原 bug 仍需修"场景下要多创建一个 BUG 文件。可接受。

### H1：DSL Condition 规范（白名单）

为防止 `eval()` 暴露任意代码执行风险（Python script 直接读 user-provided string 危险），condition DSL 用受限白名单：

| 元素 | 允许 |
|------|------|
| 变量 | `scenario` / `scenario_subtype` / `current_stage` / `release` / `srs.is_multi_module` / `srs.architecture_change` |
| 运算符 | `==` / `!=` / `&&` / `\|\|` / `()` |
| 字面量 | enum / bool / 引号字符串 |
| 函数调用 | ❌ |
| 属性链长度 > 2 | ❌ |
| 其他 | ❌ |

实现者用 simple parser（如 `pyparsing` 或手写 recursive descent），不用 `eval`/`exec`/`ast.literal_eval`。

### M6：Stage 4 unconditional validation

reviewer 给了两个选项：
- 定义严格 `rank()` 函数 + `rank(current) >= rank(required)`
- Stage 4 advance 无条件校验全部 4 个 per-task artifacts

选第 2 个简化方案：

1. **实现简单**：避免 rank 顺序定义错误
2. **语义明确**：Stage 4 done 必须所有 task `verified`，每个 task `verified` 必然产出全部 4 个 artifacts
3. **代价小**：advance 时多跑几次 validate.py file，但这是最终 advance check，性能可接受

task 子状态推进的中间合法性由 `update --task` 状态机转移表保证（命令拒绝非法 task state 跳跃），不需要 advance 时再次校验子状态匹配。

### M5：recover 在 terminal state 的语义

明确：terminal state（`project_state ∈ {aborted, reconstructing}`）下：

- `query` 允许（只读）
- `recover` 允许（**唯一 repair mutation**：从 history 重建 progress.md，但**不得改 `project_state` 终态**——重建后必须保持 `aborted` 或 `reconstructing`）
- 其他 update 类命令全部拒绝

这样 terminal state 不是"完全只读"，而是"只允许从 history 修复"。recover 不能"复活"已 abort 的 project（避免误用）。

## v0.5 batch 1 → v0.6 batch 1 round 2 主要修改清单

| 文件 | 变化 |
|------|------|
| `docs/workflow/workflow_specification_claude.md` | H4：line 144 Technical Debt 必备→推荐 |
| `skills/workflow-protocol/SKILL.md` | H2: incident command 签名同步；M5: sub_state enum 加 null + workflow_version v0.6 + recover 语义；H3: continue 简化说明；L9: Path Convention Note |
| `skills/workflow-protocol/references/command-reference.md` | H3: continue mutation 简化（删 keep/clear） |
| `skills/doc-guardian/SKILL.md` | L9: Path Convention Note |
| `skills/doc-guardian/references/frontmatter-schema.md` | H1: srs 加 is_multi_module + architecture_change；M7: test-review-report 生命周期表；M8: ID regex 强制 3 位 + ID References 小节 |
| `skills/doc-guardian/references/required-artifacts.md` | H1: 加 condition DSL 规范；M6: Stage 4 删 task_substate_required，无条件全校验 |
| `skills/doc-guardian/references/directory-layout.md` | M8: ID 路径模板改 `{cr_id}`/`{bug_id}`/`{incident_id}`；强制 3 位 zero-padded |
| `skills/doc-guardian/references/change-log-format.md` | 无修改 |

## 没有采纳/弱采纳的项

- F16（doc-guardian SKILL.md 内联 changelog 细节）：仍延迟。`change-log-format.md` 已创建，但 SKILL.md 内联描述未精简——不阻塞，待 batch 2/3 视情况优化。

## 评审循环统计

| 版本 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|----------------|
| v0.1 评审 | 9 | 5 | 4 | 0 | fix |
| v0.2 评审 | 8 | 5 | 3 | 0 | fix |
| v0.3 评审 | 6 | 3 | 2 | 1 | fix |
| v0.4 评审 | 4 | 0 | 2 | 2 | fix |
| batch 1 round 1 | 16 | 8 | 5 | 3 | fix |
| **batch 1 round 2** | **9 new** | **4** | **4** | **1** | fix |

收敛趋势：从 round 1 的 16 项降到 round 2 的 9 项，High 从 8 降到 4。如果 round 3 能降到 ≤ 4 finding 且 0-1 High，可进 batch 2。

## 验证 Round 1 partial-resolved 是否在 Round 2 全部覆盖

Round 1 中 10 项 partial-resolved finding，对照 Round 2 处置：

| Round 1 残留 | Round 2 覆盖 |
|-------------|--------------|
| F2 partial（incident command 签名）| ✅ H2 |
| F3 partial（continue mutation）| ✅ H3 |
| F4 partial（DSL 字段）| ✅ H1 + M6 |
| F5 partial（spec body S3）| ✅ H4 |
| F7 partial（test-review owner）| ✅ M7 |
| F9 partial（is_multi_module 缺 schema）| ✅ H1 |
| F11 partial（terminal cleanup + schema）| ✅ M5 |
| F12 partial（ID/path/triggered_by_bug）| ✅ M8 |
| F13 partial（shorthand）| ✅ L9 |
| F16 partial（doc-guardian SKILL 内联）| ⏸ 仍延迟 |

10 项中 9 项被本轮 9 项新 finding 覆盖；F16 仍延迟（不阻塞）。
