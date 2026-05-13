# Codex Review Prompt — Task 5 Batch 2

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请评审 dev-workflow-skills2 项目的 Task 5 批 2 产出（scenario-dispatcher / bug-triage / workflow-evolution 三个 skill 的完整 SKILL.md + 关键 references），按之前 batch 1 review 的格式输出评审报告。

### 评审目标文件（7 份）

主要审查：

- `skills/scenario-dispatcher/SKILL.md`
- `skills/scenario-dispatcher/references/scenario-decision-tree.md`
- `skills/bug-triage/SKILL.md`
- `skills/bug-triage/references/root-cause-rubric.md`
- `skills/bug-triage/references/triage-decision-tree.md`
- `skills/workflow-evolution/SKILL.md`
- `skills/workflow-evolution/references/incident-analysis-template.md`

### 必读参考材料

判断"是否符合 spec / design / batch 1"时必读：

- `docs/workflow/workflow_specification_claude.md`（v0.6）
- `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计）
- `skills/workflow-protocol/SKILL.md`（已闭环 batch 1 round 5）
- `skills/workflow-protocol/references/command-reference.md`（progress.py 11 个子命令 mutation 权威源）
- `skills/doc-guardian/SKILL.md`（已闭环 batch 1 round 5）
- `skills/doc-guardian/references/frontmatter-schema.md`（doc type schema 权威）
- `skills/doc-guardian/references/required-artifacts.md`（scenario-aware required artifacts）
- `docs/handoff/session_handoff_20260506.md`（项目状态快照）
- `docs/review/skill_set_batch1_round5_review.md`（batch 1 终轮 review，了解收敛风格）

可选参考（理解评审风格）：

- `docs/review/skill_set_batch1_review.md`（batch 1 round 1，作为评审风格底）
- `docs/review/skill_set_batch1_round4_review.md`（batch 1 round 4）
- `docs/review/skill_set_batch1_round5_review.md`（batch 1 round 5）

### 评审维度（10 个）

请覆盖以下维度，每条 finding 必须明确归属于其中一个或多个：

1. **Spec / Design 一致性**
   - SKILL.md 描述与 workflow spec v0.6 + design proposal v0.5 是否一致？
   - 引用的 progress.py 命令签名是否与 batch 1 `command-reference.md` 完全一致？特别是 `init`（参数 `--project / --scenario S1|S3 / --release`）、`release-start`（`--version / --scenario S2-1|S2-2|S2-3`）、`bug-start --bug --root-cause`、`incident-start --bug --report`、`incident-resolve --action continue|abort|reconstruct`
   - 引用的 frontmatter schema 字段是否与 batch 1 `frontmatter-schema.md` 完全一致？特别是 `bug-report`（`bug_id / found_in_release / target_release / root_cause / consumed_in_release`）与 `workflow-incident`（`incident_id / triggered_by_bug / triggered_in_release / resolution_action`）
   - workflow-protocol authority 1 / AGENTS.md 2 / doc-guardian authority 3 / 这 3 个 skill authority 4 标注是否一致？
   - S2 4 子场景定义、4 类 bug 根因、3 个 incident action 与 design proposal 是否一致？

2. **跨 skill 协作一致性**（**重点**）
   - scenario-dispatcher 路由到 bug-triage / workflow-evolution 的入口条件，是否与那两个 skill 的 "When to Invoke" 一致？
   - bug-triage active mode 调 progress.py `bug-start` / `incident-start` 的前置条件，是否与 `command-reference.md` §8 / §10 完全一致？
   - workflow-evolution 调 `incident-resolve` 3 action mutation，是否与 `command-reference.md` §11 完全一致？特别是 `continue` 不再支持 `--bug-flow keep|clear` 子参数（v0.6 round 2 H3 决议）
   - INCIDENT body 章节责任分工（bug-triage 写 §1-§2 skeleton，workflow-evolution 写 §3-§7 body）在三处描述（bug-triage SKILL §5 / triage-decision-tree §4 / workflow-evolution §3.2 + incident-analysis-template §1）是否完全对齐、无矛盾？
   - INCIDENT.frontmatter `triggered_by_bug` 在 bug-triage / workflow-evolution / doc-guardian 三处描述是否一致（必须是 BUG ID 字符串而非路径）？

3. **决策树完整性**
   - scenario-dispatcher 决策树是否覆盖所有 (project_state, release_state, bug_flow.active, workflow_incident_active) 组合？
   - bug-triage 双模式入口（active vs post-close）+ 4 类根因路由 + INCIDENT skeleton 创建是否覆盖完整？
   - workflow-evolution 7 步流程 + retrospective consumption 触发条件是否完整？
   - 各 skill 的 "When NOT to Invoke" 是否互斥且覆盖全集？

4. **Output Contract 严格性**
   - 三个 skill 是否都明确"不直接 mutation progress.md"？
   - 各自的 Type A/B/C 输出分类是否清晰、不重叠？
   - bug-triage 写 BUG.frontmatter `root_cause` 是否唯一渠道？
   - workflow-evolution 写 INCIDENT.frontmatter `resolution_action` 是否唯一渠道？

5. **Forbidden Actions 完整性**
   - 每份 SKILL.md 都有 Forbidden Actions 清单。是否有明显的 bypass 路径未被列入？例如：
     - scenario-dispatcher 在 active release 期间重新 dispatch 已锁定 scenario
     - bug-triage active mode 在 closed release 触发 / post-close mode 在 active release 触发
     - workflow-evolution 修改 dev-workflow-skills2 自身文件（递归悖论）
     - bug-triage 自创 BUG-NNN.md ID 与 doc-guardian validate ids 冲突
     - workflow-evolution 跳过 self-evaluation 直接 incident-resolve
     - bug-triage 修 BUG.root_cause 但 BUG report 已被 progress.py bug-start 引用（破坏一致性）

6. **递归悖论严格性**（仅 workflow-evolution）
   - §8 Recursion Constraint 是否覆盖所有可能的"修自身"路径？
   - retrospective consumption 输出建议是否清楚区分"本 skill 集改进"vs"用户项目改进"？
   - 是否存在用户绕过 §8 直接让 workflow-evolution 修自身文件的路径？

7. **可实现性**
   - Python / TypeScript 实现者读这 7 份文件能否直接动手实现 dispatcher / triage / evolution 逻辑？
   - 哪些地方语义模糊导致实现者会做不一致选择？
   - bug-triage 的 root-cause-rubric heuristic（§5 信号强度评分）是否过模糊以致无法确定性判定？
   - workflow-evolution 的 3 action decision matrix 6 维度（D1-D6）是否可程序化判定（哪怕需要用户输入）？
   - 决策树伪代码（scenario-decision-tree §1 / triage-decision-tree §1 / incident analysis 7 步）是否可直接转 Python？

8. **简洁度**（避开 foreman 690 行反模式）
   - 7 份文件是否过长？bug-triage SKILL.md 425 行 / workflow-evolution SKILL.md 422 行（与 batch 1 doc-guardian 365 / workflow-protocol 329 比较）
   - 哪些章节冗余、可合并？哪些应拆 reference？
   - End-to-end examples 数量（scenario-decision-tree §8 有 8 个，triage-decision-tree §7 有 7 个，incident-analysis-template §4 有 3 个）是否过多？

9. **边界状态处理**
   - bug-triage active mode 在 `current_stage != testing` 时的 fallback 路径是否清晰（参 triage-decision-tree §7.2 Example B：用户在 development stage 主动报 bug）？
   - workflow-evolution 在用户拒绝 3 action 选择（持续不决策）时的处理是否清晰？
   - scenario-dispatcher 在 `project_state ∈ {aborted, reconstructing}` 时是否完全 reject（不路由到任何下游 skill）？
   - bug-triage 重 invoke 幂等性约束（SKILL.md §8.1）：三种状态（root_cause==null / root_cause set + active==false / root_cause set + active==true）的处理是否完整？
   - workflow-evolution 重 invoke 幂等性（SKILL.md §7.2）：四种状态分布是否覆盖？
   - bug-triage 同一 bug 经多轮 Bug Flow（修 SRS 后 retest fail 又判 architecture）的 reclassification 路径（root-cause-rubric §4.7）是否一致？

10. **术语一致性**（v0.4 F4 决议）
    - `review-passed` / `issues-found` 一律使用，绝不用 `approved`（除非指 PRD/SRS/Architecture/CR 人 gate 后的 doc status）
    - `S4` / `Bug Fix` / `active release` / `post-close` / `Bug Flow` / `Change Mode` / `Full Mode` 等术语是否与 design proposal v0.5 一致？
    - `prd-exception` / `incident` / `workflow_incident_active` 在三个 skill 中是否使用一致 enum？
    - `bug-start` / `bug-close` / `bug-intake` / `incident-start` / `incident-resolve` 调用时机描述是否一致？

### 输出要求

保存到：`docs/review/skill_set_batch2_review.md`

格式（参考 batch 1 review 历史）：

```markdown
# Skill Set Batch 2 Review (scenario-dispatcher + bug-triage + workflow-evolution)

**Review Target**: 7 份目标文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Batch 1 Reference**: skills/workflow-protocol/SKILL.md + skills/doc-guardian/SKILL.md (round 5 闭环)
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "blocking issues: <count>; recommendation: (A) 进 batch 3 / (B) fix / (C) revisit design">

## Findings

### High/Medium/Low: <一句话标题>

- **Location**: `<file>:<line>` (如 multi-line `<line-start>-<line-end>`)
- **Baseline Reference**: <相关 spec/design/batch1 file:line>（如有）
- **Issue**: <具体描述>
- **Impact**: <实现 / 协作时会导致什么问题>
- **Recommendation**: <具体修复建议；2 选项时列出取舍>

[每条 finding 一节，按 High → Medium → Low 排]

## Cross-Skill Consistency Check

[专门一节列举 batch 2 三个 skill + 与 batch 1 workflow-protocol / doc-guardian 之间的 cross-reference 是否对齐；按 (caller skill → callee skill) 列表]

## Implementability Assessment

[评估实现者能否直接基于此规范实现 dispatcher 路由 / triage 分类 / evolution 决策逻辑；列出每个 skill 的"语义模糊点"清单]

## Recursion Paradox Compliance

[workflow-evolution §8 是否严格防止修改 dev-workflow-skills2 自身；列举所有潜在 bypass 路径]

## Positive Notes

[列出做得好的设计决策；不强制]

## Suggested Next Revision Order

[按优先级排序的 fix 顺序：High first, Medium second, Low last，给出每条估计的 patch 体量]

## Recommendation

- **(A)**: 进 batch 3（17 个 vertical skill 起骨架）—— 当前批 finding 全部 Medium/Low 且数量 ≤ 3
- **(B)**: 修后再评（再评 1 轮）—— 有 High finding 或 Medium ≥ 5
- **(C)**: 重设计（design level 问题）—— 触及架构层决策
```

### 评审风格约束

- **High** = blocker，会导致 Task 6 实现错误、路由 / 分类 / 决策歧义、跨 skill 协作崩盘；不修不能进 batch 3
- **Medium** = 设计问题但有 workaround；可在 batch 3 设计期间补
- **Low** = 文档清理 / 风格问题；不阻塞
- Finding 数量不限，但每条必须有具体 location 和可执行 recommendation
- 不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义 / 是否能让其他 skill 调用本 skill 不出错"
- 已经在 v0.5 design / batch 1 round 5 闭环过的决策（如 11 个 progress.py 子命令的存在、双 symlink、Foreman 拆分、INCIDENT type 字段、3 位 zero-padded ID 等）不需要 revisit
- handoff §11 提示：建议 batch 2/3 评审循环放宽到 2-3 轮；本轮发现**质量比数量**重要——优先抓跨 skill 协作错位、决策树漏洞、Forbidden Actions 缺口、递归悖论 bypass 这类"会真正破事"的问题
- 评审完毕后给出明确的 (A) / (B) / (C) recommendation

请直接产出报告，不需要先和我对齐范围。
