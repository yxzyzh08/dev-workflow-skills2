# Codex Review Prompt — Task 5 Batch 2 Round 3

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请对 dev-workflow-skills2 项目 Task 5 批 2 第 3 轮评审。本轮目标是**回归 round 2 的 7 项修复**（0 High + 6 Medium + 1 Low），并扫描修复引入的新一致性风险。本轮如全部 ✅ 已修 + 0 New High 即可进 batch 3（17 个 vertical skill 起骨架）。

### Round 1/2 Review 与采纳记录（必读）

- `docs/review/skill_set_batch2_review.md`（round 1 review）
- `docs/review/reviewer_feedback_response_v0.9_batch2.md`（round 1 采纳）
- `docs/review/skill_set_batch2_round2_review.md`（round 2 review）
- `docs/review/reviewer_feedback_response_v0.10_batch2_round2.md`（round 2 采纳记录）

### 评审目标文件（同 round 1/2，加 1 份 batch 1 reference）

- `skills/scenario-dispatcher/SKILL.md`
- `skills/scenario-dispatcher/references/scenario-decision-tree.md`
- `skills/bug-triage/SKILL.md`
- `skills/bug-triage/references/root-cause-rubric.md`
- `skills/bug-triage/references/triage-decision-tree.md`
- `skills/workflow-evolution/SKILL.md`
- `skills/workflow-evolution/references/incident-analysis-template.md`
- **`skills/workflow-protocol/references/command-reference.md`**（**新增**：M6 修改了 §10 + §11 前置）

### 必读参考材料

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`
- `skills/workflow-protocol/SKILL.md`
- `skills/doc-guardian/SKILL.md` + `skills/doc-guardian/references/frontmatter-schema.md` + `skills/doc-guardian/references/change-log-format.md` + `skills/doc-guardian/references/required-artifacts.md`

### 本轮评审重点（针对 7 项修复的回归点）

#### 回归 M1：bug-triage active mode 三层 gate 一致

**修复定位**：
- bug-triage SKILL.md frontmatter description（行 3）
- triage-decision-tree.md §1 顶层决策树（active 分支拆 testing-pass / non-testing-reject）
- triage-decision-tree.md §2.1 active_mode_triage() Step 0 early gate

**回归审查**：

- description 是否完全删除了"active release 其他 stage 主动报"措辞？（M1 主问题）
- §1 顶层决策树 active 分支两路是否清晰：testing-pass → 走 Active Mode；non-testing → reject early？
- §2.1 active_mode_triage() Step 0 early gate 的伪代码是否清楚地在读 BUG / 写 frontmatter / 调 progress.py 之前执行？
- dispatcher（scenario-dispatcher SKILL §3 / scenario-decision-tree §4.2 / §5）+ bug-triage（SKILL §2.1 / triage-decision-tree §1 / §2.1）+ progress.py（command-reference §8 bug-start）三层 gate 前置是否完全一致？
- Forbidden Actions 与 early gate 是否冗余但互补（前者兜底，后者主动）？

#### 回归 M2：PRD-exception Example E + §4.3 validate checklist

**修复定位**：
- root-cause-rubric.md §7.5 Example E 加 promote/validate 步
- triage-decision-tree.md §4.3 改为完整 1-7 类清单 + 引用 doc-guardian §5.1

**回归审查**：

- Example E 是否完整列出：写 BUG frontmatter → promote BUG → validate BUG → 创建 INCIDENT skeleton → **promote INCIDENT → validate INCIDENT** → incident-start？
- §4.3 7 类清单是否与 doc-guardian SKILL §5.1 完全对应？class 8 (Consistency) 不在本时点的解释是否清楚？
- 是否还有任何引用"validate.py 8 类校验" 但只列 4 类的残留？

#### 回归 M3：post-close BUG 模板 Pending 改空

**修复定位**：
- triage-decision-tree.md §3.2 post-close BUG 完整模板

**回归审查**：

- 模板的 `## Pending Changes` 是否真正为空（仅 HTML comment）？
- 注释 `<!-- empty after changelog.py promote -->` 是否符合 change-log-format §2.3 规范？
- 7 个端到端 examples 中是否还有其他 BUG/INCIDENT 模板残留 "- (空，已 promote)" 这类反模式？

#### 回归 M4：retrospective Action Item + advisory notice

**修复定位**：
- workflow-evolution SKILL.md §4.3 retrospective output 模板（5 个 suggestion table 加 Action Item 列）
- incident-analysis-template.md §5 retrospective output 模板 + 顶部 Advisory Notice
- incident-analysis-template.md examples §4.1/§4.2/§4.3 的 §4 加 per-item Action Item

**回归审查**：

- SKILL §4.3 与 incident-analysis-template §5 retrospective 模板是否完全一致？两份模板的 5 个 suggestion 表格列是否对齐？
- §5 顶部的 Advisory Notice 是否与 §1.2 (incident mode §4 Scope Notice) 同等强度（含"禁止 patch/diff/直接编辑文件"+"必须含 Action Item"）？
- 3 个 examples 的 §4 是否都改为 per-item Action Item 表（不再是 paragraph 风格）？
- Caveat 段是否提到 "(b) 跨 project 复盘后，去 dev-workflow-skills2 仓库走 **独立 design proposal review cycle**"（不再笼统说 "提交去向：dev-workflow-skills2 仓库"）？

#### 回归 M5：workflow-evolution 重 invoke 幂等性二次确认

**修复定位**：
- workflow-evolution SKILL.md §7.1 严格 6 条规则
- workflow-evolution SKILL.md §7.2 idempotency 表拆两态
- workflow-evolution SKILL.md §10 Recovery on Failure 改写
- incident-analysis-template.md §1.6.1 reentrant_finalization_check 伪代码

**回归审查**：

- §7.1 6 条规则是否可程序化判定（特别是 "Pending 为空" + "validate 重新 pass" 两条新加）？
- §7.2 表是否清晰拆 `finalization complete` 与 `body/frontmatter complete but finalization unknown` 两态？
- §1.6.1 伪代码是否完整覆盖：(a) workflow_incident_active=false 提前退出；(b) finalization complete → 直接重试；(c) body 完成但 finalization 未完成 → 重走 6.e-g；(d) frontmatter 漏 → 重走 6.b-g？
- §10 Recovery 表"重 invoke 时检测到 status=review-passed 但 incident-resolve 未调用"行是否正确指向 §7.1 / §7.2 严格规则？
- 修复后是否还存在任何 "silent skip 到 incident-resolve" 路径？

#### 回归 M6：command-reference 加 incident validate 前置

**修复定位**：
- workflow-protocol/references/command-reference.md §10 incident-start 前置（加 validate.py file <incident-path> exit 0）
- workflow-protocol/references/command-reference.md §11 incident-resolve 前置（加 validate.py file <incident-path> exit 0 + status==review-passed + resolution_action ∈ enum）

**回归审查**：

- §10 / §11 前置改写是否与 batch 2 文档的 "double-safety" 表述一致？特别是 bug-triage SKILL §5.2 / workflow-evolution SKILL §3.1 Step 7 是否仍能解释为"caller validate 一次 + progress.py 二次"？
- §11 incident-resolve 前置加的 "status==review-passed + resolution_action ∈ enum + validate exit 0" 是否会与 §11.1/§11.2/§11.3 的 mutation 描述冲突？
- command-reference §1 init 与 §6 release-start 是否需要类似的 validate 前置补全？（**专项**：本轮只补 §10/§11，是否漏了其他子命令？）
- progress.py 实现这些前置的复杂度评估：是否引入 progress.py → doc-guardian validate.py 的 cross-skill 调用？是否有 cycle 风险？

#### 回归 L1：examples Finalization sequence 展示

**修复定位**：
- incident-analysis-template.md Example A/B/C 各加 Finalization sequence 段

**回归审查**：

- 3 个 examples 的 Finalization sequence 段是否完全一致（仅 action enum / timestamp / incident path 不同）？
- 每个 example 的 6.b-g 步骤是否与 §1.6 主序列字母编号完全对应？
- "仅在 6.g pass 后调 progress.py incident-resolve" 是否在每个 example 都明确？

### 横向一致性检查（跨 finding）

1. **三层 gate 一致**（M1）：dispatcher / bug-triage / progress.py 前置全文一致；frontmatter description / 顶层决策树 / Step 0 / Forbidden Actions 全部对齐
2. **changelog promote / validate 顺序**（M2 + L1）：BUG / INCIDENT / workflow-evolution finalization 三处的 promote → validate → progress.py 顺序在主流程 + examples + checklist 全部一致
3. **空 Pending Changes 章节**（M3）：所有 doc 模板均无 "- (空，已 promote)" 残留；统一用 HTML comment 或纯空
4. **Action Item 标注**（M4）：incident mode + retrospective mode + examples 三处的 advisory 都含 per-item Action Item；advisory/patch 边界全文一致
5. **重 invoke 幂等性**（M5）：SKILL §7.1 / §7.2 / §10 + incident-analysis-template §1.6.1 描述一致；不留任何 silent skip 路径
6. **double-safety validate**（M6）：caller (bug-triage / workflow-evolution) 第一次 validate + progress.py 第二次 validate；command-reference §10/§11 与 batch 2 SKILL 描述对齐

### 重点排查"修复引入的新风险"

- **M6 引入 progress.py → doc-guardian validate 调用**：是否产生循环依赖？workflow-protocol 依赖 doc-guardian 还是相反？authority 1 vs 3 的层级关系是否被破坏？
- **M5 reentrant 检查的复杂度**：每次 workflow-evolution 重 invoke 都要跑一次 validate.py（可能很贵），是否有性能 / UX 顾虑？是否有简化路径（如只检查 Pending 章节内容是否为空）？
- **M4 retrospective 模板**：是否会让用户误以为 retrospective consumption 必须输出 5 个 suggestion table（即使没有发现）？是否需要"无 suggestion 时也合法"的明示？
- **M2 §4.3 引用 doc-guardian §5.1**：如果 doc-guardian §5.1 后续调整 (e.g. 8 类改 9 类)，本 reference 是否会自动失效？是否需要 stable cross-reference 锚点？
- **M1 description 收紧**：是否会与 v0.6 round 1 batch2-F2 的 reject 路径产生表述冗余？

### 评审格式

保存到：`docs/review/skill_set_batch2_round3_review.md`

格式（沿用 round 2）：

```markdown
# Skill Set Batch 2 Round 3 Review

**Review Target**: 8 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review/Response**: docs/review/skill_set_batch2_review.md / reviewer_feedback_response_v0.9_batch2.md
**Round 2 Review/Response**: docs/review/skill_set_batch2_round2_review.md / reviewer_feedback_response_v0.10_batch2_round2.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "regression: 0 remain; recommendation: (A) 进 batch 3">

## Round 2 Findings 回归状态

| Round 2 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| M1 三层 gate | ✅ / ⚠️ / ❌ | <具体描述> |
| M2 Example E + §4.3 | ... | ... |
| M3 post-close 模板 | ... | ... |
| M4 retrospective Action Item | ... | ... |
| M5 reentrant idempotency | ... | ... |
| M6 progress.py validate 前置 | ... | ... |
| L1 examples finalization | ... | ... |

## New Findings (Round 3)

[每条 finding 一节；按 High / Medium / Low 排]

## Cross-Finding Consistency Check

[7 项修复之间的协作一致性]

## Recommendation

- **(A)**: 进 batch 3 —— 0 New High，且 Round 2 Findings 全部 ✅
- **(B)**: 修后再评（再评 1 轮）—— 有 New High 或 Round 2 残留
- **(C)**: 重设计（design level 问题）
```

### 评审风格约束

- 优先做**回归审查**：7 项修复是否完整落地
- 抓**修复引入的新风险**（特别是 M6 cycle dependency / M5 性能 / M4 retrospective 假阳性）
- 已经在 Round 1/2 闭环的决策（如 advisory vs patch / 4 类强制 / reject 路径）不再重新质疑
- handoff §11：批 2 计划 2-3 轮；本轮是第 3 轮，建议（A）/（B）二选一，避免再延迟到 round 4
- 本轮如全部 ✅ 已修 + 0 New High，强烈推荐 (A) 进 batch 3

请直接产出报告，不需要先和我对齐范围。
