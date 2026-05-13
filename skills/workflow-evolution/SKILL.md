---
name: workflow-evolution
description: dev-workflow-skills2 工作流演进 meta skill (Layer 4)。双模式：(a) Incident analysis mode（强制）：progress.md workflow_incident_active==true 时由 AGENTS.md Bootstrap 调用，读 INCIDENT-NNN.md skeleton + 关联 BUG report，分析 PRD 异常根因与工作流缺陷，3 action（continue/abort/reconstruct）评估并与用户决策，填 INCIDENT body §3-§7 + frontmatter resolution_action，调 progress.py incident-resolve；(b) Retrospective consumption mode（advisory）：Stage 7 retrospective review-passed 后由用户主动触发，分析 retrospective.md 跨 release patterns 输出工作流改进建议（conversation 输出，不强制持久化）。本 skill 不修 PRD/SRS/Architecture/Development 内容（无写权），不修 dev-workflow-skills2 自身 skill 文件（递归悖论），不直接 mutation progress.md（mutation 走 progress.py）。
authority: 4
references:
  - references/incident-analysis-template.md
---

# workflow-evolution

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径** `skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（Meta layer，与 stage skill / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（5 项）**：

1. **Incident analysis mode**：在 `workflow_incident_active==true` 期间，分析触发 incident 的 PRD 异常根因 + 工作流缺陷
2. **Incident analysis mode**：填 INCIDENT-NNN.md body（§3 Root Cause / §4 Workflow Improvement Suggestions / §5 3 Action Evaluation / §6 Recommendation / §7 Resolution）
3. **Incident analysis mode**：与用户决策 3 个 action（continue / abort / reconstruct），写 INCIDENT frontmatter `resolution_action`，调 `progress.py incident-resolve`
4. **Retrospective consumption mode**：在 Stage 7 retrospective 完成后由用户主动触发，分析跨 release patterns，输出工作流 / skill / template 改进建议（conversation 输出）
5. 维护 INCIDENT report ID 唯一性（依赖 doc-guardian validate.py ids）

**不属于本 skill**：

- 创建 INCIDENT skeleton（仅 frontmatter）→ `bug-triage`
- 写 BUG report → `testing-write` / `bug-triage`
- 修 PRD / SRS / Architecture / Development / Testing / Delivery / Retrospective 内容 → 对应 stage skill
- 修改 `dev-workflow-skills2` 自身的 skill 文件 / workflow spec / design proposal（**递归悖论**，见 §8）
- 直接 mutation `progress.md` → `workflow-protocol` 的 `progress.py`
- 评审 / approve INCIDENT report 内容（INCIDENT 是非 gated doc 类型，自评后直接 review-passed）
- 决定 scenario / scenario_subtype → `scenario-dispatcher`
- 分类 bug 根因 → `bug-triage`

## 2. When to Invoke

### 2.1 Incident Analysis Mode 触发

| 时机 | 由谁调用 | 输入 |
|------|---------|------|
| `progress.md workflow_incident_active==true` | AGENTS.md Bootstrap 第 5 步 | `incident_report_path` 指向的 INCIDENT-NNN.md skeleton + `bug_flow.bug_report_path` 指向的 BUG-NNN.md |
| `incident-start` 刚成功（bug-triage 调完）| `bug-triage` 退出后由 AGENTS.md Bootstrap 重新进入 | 同上 |

**前置条件**（incident analysis mode）：

- `workflow_incident_active == true`
- `incident_report_path` 指向合法 `workflow-incident` type 的 doc（skeleton 已由 bug-triage 创建）
- `bug_flow.active == true` AND `bug_flow.root_cause == prd-exception`
- INCIDENT-NNN.md frontmatter `triggered_by_bug` 等于 BUG-NNN.md frontmatter `bug_id`

### 2.2 Retrospective Consumption Mode 触发

| 时机 | 由谁调用 | 输入 |
|------|---------|------|
| Stage 7 retrospective 完成（review-passed）| **用户主动**调用（不强制） | retrospective.md 全文 + 跨 release 历史 progress-history.md |

**前置条件**（retrospective consumption mode）：

- `workflow_incident_active == false`
- 当前 release 已在 Stage 7（`current_stage == project-retrospective`）且 retrospective.md `status: review-passed`
- 或 release 已 closed，用户主动启动跨 release 复盘

**关键差异**：retrospective consumption 是 advisory，**用户不调用就不触发**。不会被 AGENTS.md Bootstrap 自动 invoke。

### 2.3 不会被 invoke 的时机

- `workflow_incident_active == false` 且非用户主动触发：本 skill 不主动接管
- `project_state ∈ {aborted, reconstructing}`：终态；终态进入前可能由 incident-resolve 调用本 skill 完成最后一次 incident 分析，但终态后不再触发
- `bug_flow.active == true` 且 `root_cause != prd-exception`：那是 `bug-triage` / 对应 stage skill 的事；本 skill 不介入

## 3. Mode A: Incident Analysis

### 3.1 7 步流程

```
1. 读 progress.py query 确认 workflow_incident_active==true 与 incident_report_path
2. 读 INCIDENT-NNN.md（skeleton 由 bug-triage 创建，body §3-§7 待填）
3. 读关联 BUG-NNN.md（path 来自 bug_flow.bug_report_path）
4. 读 PRD + SRS + Architecture + 相关 Detailed Design / Test Report 作为分析上下文
5. 与用户协作填 INCIDENT body §3-§6（不含 §7）：
   - §3 Root Cause Analysis
   - §4 Workflow Improvement Suggestions（含 advisory 建议 + Action Item 标注）
   - §5 Three Action Evaluation（3 个 action 全填）
   - §6 Recommendation（含 D1-D6 维度评估）
   - 每次编辑追加一条 ## Pending Changes entry
6. 与用户决策 3 个 action（continue / abort / reconstruct），按以下**严格序列**执行（v0.6 round 2 batch2-F5；缺一则 incident-resolve 失败或 doc-guardian validate 拒绝）：
   a. 填 INCIDENT body §7 Resolution（含用户最终 action / timestamp / rationale / Resolution Command 行 / Post-Resolution Path）
   b. 改 INCIDENT frontmatter `resolution_action: null → <continue|abort|reconstruct>`
   c. 改 INCIDENT frontmatter `status: draft → review-passed`
   d. 改 INCIDENT frontmatter `updated: <now>`
   e. 追加一条 ## Pending Changes entry "incident analysis 完成 + resolution_action=<enum>"
   f. 调 skills/doc-guardian/scripts/changelog.py promote <incident-path>
      → 把 §5/§6/§7 阶段所有 Pending entries 移入 Change Log（按日期分组）
   g. 调 skills/doc-guardian/scripts/validate.py file <incident-path>
      → 必须 exit 0；类 6 (Change Log Discipline) 要求 Pending 已空、Change Log 格式合法
      → 类 3/4 校验 frontmatter `resolution_action` ∈ enum、`status` 合法
      → 失败则修后重 promote / validate；不允许跳过 validate 直接进 7
7. validate pass 后才允许调 progress.py incident-resolve --action <enum>
   → progress.py 自身会再次 validate INCIDENT 文件，二次校验前 6 步顺序正确
```

### 3.2 Incident Body 章节责任（详见 references/incident-analysis-template.md）

| 章节 | 内容 | 责任方 |
|------|------|--------|
| §1 Triggering Bug | 引用 BUG-NNN.md（链接 / ID）| bug-triage 已填 skeleton |
| §2 Workflow State at Trigger | release / stage / scenario / project_state（客观信息）| bug-triage 已填 skeleton |
| §3 Root Cause Analysis | PRD 哪部分错 / 工作流哪段没拦住 / 是否 known-issue | **workflow-evolution 填** |
| §4 Workflow Improvement Suggestions | workflow spec / skill / template / 评审 rubric 改进建议 | **workflow-evolution 填** |
| §5 Three Action Evaluation | 3 action 各自的适用条件 / 风险 / 后续工作 | **workflow-evolution 填** |
| §6 Recommendation | 基于分析推荐 action + rationale | **workflow-evolution 填** |
| §7 Resolution | 用户决策记录 + incident-resolve 命令 | **workflow-evolution 填**（用户决策后）|

### 3.3 与用户协作的边界

workflow-evolution 在 §3-§6 章节完成后**与用户对话**：

- 展示分析结果与 recommendation
- 接受用户的 review / 反驳 / 补充
- 让用户做最终决策（3 个 action 选 1）

**关键原则**：用户决策权重 > workflow-evolution recommendation。如果用户与 recommendation 不一致，按用户选择，不要拗。

### 3.4 INCIDENT report 不走独立 review skill

INCIDENT report 是 non-gated doc 类型，**没有**对应的 `incident-review` skill：

- workflow-evolution 自评（按下面 3.5 自评清单）
- 在 §3.1 Step 6 中按严格序列改 frontmatter（`resolution_action` + `status: review-passed`）→ 加 Pending entry → promote → validate
- validate pass 后才能调 incident-resolve

frontmatter 状态变化（**单次原子序列**，禁止 validate 后再改 frontmatter）：

```
status: draft (skeleton)
  → status: review-passed (workflow-evolution 完成 §3-§7 body + 设 resolution_action + Pending → promote → validate pass 后)
```

不进 `in-review` / `revising` / `approved` 状态。

### 3.5 自评清单（workflow-evolution 写完 body 后）

| # | 自评项 | 通过标准 |
|---|--------|---------|
| 1 | §3 Root Cause Analysis 是否引用具体 PRD 章节 / 工作流 stage？ | 至少 1 处具体引用，非泛泛而谈 |
| 2 | §4 Workflow Improvement Suggestions 是否针对 dev-workflow-skills2 工作流而非用户项目代码？ | 是 |
| 3 | §5 Three Action Evaluation 是否覆盖 3 个 action（continue / abort / reconstruct）？ | 3 个都有 |
| 4 | §5 每个 action 是否含适用条件 + 风险 + 后续工作？ | 都有 |
| 5 | §6 Recommendation 是否给出明确选择 + rationale？ | 是 |
| 6 | §6 Recommendation 是否与 §3 根因分析一致？ | 一致 |
| 7 | §7 Resolution 是否记录用户最终决策（含 timestamp 与 action）？ | 用户决策后填，决策前留待写状态 |
| 8 | INCIDENT frontmatter resolution_action 是否与 §7 Resolution 一致？ | 一致 |
| 9 | INCIDENT frontmatter triggered_by_bug 是否指向真实 BUG-NNN.md？ | doc-guardian validate cross-ref 校验 |
| 10 | §4 改进建议是否含具体 skill / 章节引用（advisory 仍要精确）？ | 是 |
| 11 | §4 每条改进建议是否标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle"？ | 是 |
| 12 | 是否输出可直接应用的 patch / diff / unified diff 给 dev-workflow-skills2 自身文件？（v0.6 round 2 batch2-F4 严格区分 advisory vs patch）| **否**（advisory 自然语言建议允许；patch/diff 严禁）|

任一未通过 → 修复后重跑 validate.py。

### 3.6 调 progress.py incident-resolve

INCIDENT body + frontmatter 全部完成后调：

```
skills/workflow-protocol/scripts/progress.py incident-resolve --action <enum>
```

3 个 action 的 mutation 详见 `skills/workflow-protocol/references/command-reference.md` §11。本 skill 概要：

| Action | progress.md 后续状态 |
|--------|---------------------|
| `continue` | `workflow_incident_active=false`、`bug_flow.*=null`、`current_stage=testing`、`sub_state=review-passed`、`review_iteration=0` |
| `abort` | `project_state=aborted`、`release_state=closed`、`release_close_reason="incident-abort"`、`current_stage=null`、其余字段 cleanup |
| `reconstruct` | `project_state=reconstructing`、`release_state=closed`、`release_close_reason="incident-reconstruct"`、`current_stage=null`、其余字段 cleanup |

**continue 后续行为**：

- 用户若希望修原 bug → 创建**新 BUG-MMM.md**（new ID）触发新一轮 bug-triage active mode
- 不复用原 BUG（避免 reclassification 状态污染）；原 BUG 保留 `root_cause: prd-exception` 作历史记录

**abort 后续行为**：本 project 进终态；用户起新 project（独立目录）。

**reconstruct 后续行为**：本 project 进终态；用户起新 S3 project（独立目录），可在新 PRD 引用本 project 作 source system。

## 4. Mode B: Retrospective Consumption

### 4.1 用户主动触发场景

- Stage 7 retrospective 完成后用户问："这次 release 暴露的 patterns 对 workflow 有什么改进建议？"
- 用户做跨多个 closed release 复盘，希望找出反复出现的工作流薄弱点
- 用户想总结某 incident 的长期教训（incident-resolve 后 archives 复盘）

### 4.2 输入

| 输入 | 用途 |
|------|------|
| `docs/retrospective/retrospective.md`（项目级单文件，每 release 增量加节）| 主输入；含本 release / 历史 release 的 issue analysis 与 improvement proposals |
| `progress-history.md` | 历史动作 / event timeline；可挖掘 review iteration 高 / 反复 revising 的 patterns |
| `docs/incident/INCIDENT-*.md`（如有）| 历史 incident；workflow 异常路径数据 |
| `docs/bug/BUG-*.md`（如有）| 历史 bug；root_cause 分布数据 |

### 4.3 输出形式

**纯 conversation 输出**，不强制持久化为新 doc。模板（v0.6 round 3 M4：与 incident mode advisory/patch 边界一致，每条建议必须标注 Action Item）：

```
"# Workflow Evolution Analysis (Release X.Y / Cross-Release)

> **Advisory Notice**：本输出仅产出 advisory 自然语言建议；**禁止**输出 patch / diff / unified diff
> 或直接编辑 dev-workflow-skills2 自身文件（v0.6 round 2 batch2-F4：递归悖论防的是 patch，不是建议）。
> 每条建议必须标注 Action Item，让用户清楚不会自动落地。
>
> **No-Suggestion Legitimacy**（v0.6 round 3 L2）：如某类（spec / skill / template / rubric）
> 经分析后**无 actionable 建议**，对应 table 必须填一行 `None — no actionable suggestion found`，
> **不要为了凑表格而编造低价值或假阳性建议**。质量 > 数量。

## 1. Patterns Observed
- ...

## 2. Workflow Spec Suggestions

| 改进点 | 目标章节 | 建议改动 | 优先级 | Action Item |
|--------|---------|---------|--------|-------------|
| <例：review iteration 接近上限时自动升级提醒> | workflow-protocol §8 Review Loop | 加 review_iteration ≥ 6 时 progress.py 输出升级 hint | High | 提交 dev-workflow-skills2 design proposal review cycle |

## 3. Skill Suggestions

| 改进点 | 目标 skill | 建议改动 | 优先级 | Action Item |
|--------|-----------|---------|--------|-------------|
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 4. Template Suggestions

| 改进点 | 目标 doc type | 建议改动 | 优先级 | Action Item |
|--------|-------------|---------|--------|-------------|
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 5. Review Rubric Suggestions

| 改进点 | 目标 review skill | 加 / 改 rubric | 优先级 | Action Item |
|--------|----------------|---------------|--------|-------------|
| ... | ... | ... | ... | 提交 dev-workflow-skills2 design proposal review cycle |

## 6. Caveat

- 本输出仅 advisory；不会自动改 workflow / skill / template
- 改进建议落地路径：
  (a) 在下次 retrospective.md 加 'Workflow Improvements' 章节（由 retrospective-write 在 Stage 7 Change Mode 处理）
  (b) 跨 project 复盘后，去 dev-workflow-skills2 仓库走 **独立 design proposal review cycle**
- workflow-evolution **不**直接修改 dev-workflow-skills2 自身文件（递归悖论）
- 不输出 patch / diff / unified diff；只输出自然语言 advisory 建议"
```

### 4.4 不强制持久化的理由

- 设计哲学：retrospective 改进建议会**落到用户实际项目**而非本 skill 集（dev-workflow-skills2 的递归悖论）
- 改进 dev-workflow-skills2 自身需要走**独立的 design proposal review cycle**（参见 docs/design/skill_set_design_proposal_v0.5.md 模式）
- meta layer 不应擅自创建新 doc type / 新 frontmatter 字段
- conversation 输出可让用户灵活决定哪些采纳

### 4.5 用户主动持久化的可选路径

如果用户决定持久化（仅作为参考路径，本 skill 不强制）：

| 持久化路径 | 操作方 |
|----------|-------|
| 加到 `docs/retrospective/retrospective.md` 作"Workflow Improvements"章节 | `retrospective-write` skill（Change Mode）|
| 提交到 dev-workflow-skills2 上游做 spec 改进 | 用户离开本 project，到 dev-workflow-skills2 仓库走 design proposal |

workflow-evolution 在 conversation 输出末尾**主动告知**这两条路径，但不替用户决定。

### 4.6 Retrospective Mode 不调 progress.py

retrospective consumption mode 是**纯只读 + 输出**，不修改任何 state。完成后用户继续后续工作（推进 Stage 7 → release-close → 下个 release-start，由 dispatcher / retrospective-write 接管）。

## 5. Three Action Decision Framework

仅适用 incident analysis mode。完整 framework 见 `references/incident-analysis-template.md` §3 Three Action Decision Matrix。本节为概要。

### 5.1 Continue 适用条件

满足**任一**：

- INCIDENT 分析后发现原 bug 实际可在某 stage（srs/architecture/development）合理修复（即 bug-triage 误判 prd-exception）
- workflow 微调（如评审 rubric 改进、template 加 check）即可避免再发生，PRD 与 release 内容仍有效
- 用户判定 incident 属于"特殊单点"，不影响整体方向

**风险**：

- 若 PRD 实际有问题但选 continue，bug 可能在后续 release 反复出现
- workflow 修订建议如未跟进，下次还会卡在同一类异常

### 5.2 Abort 适用条件

满足**任一**：

- INCIDENT 分析揭示 PRD 描述的产品**根本不可行**（任何技术栈都达不到 / 用户群完全错配）
- 投资回报率分析后用户决定不继续投入
- 项目方向与组织战略变化（外部因素）

**风险**：

- 已投入的 release 1...N 沉没成本
- project terminal state 不可逆（除非起新 project）

### 5.3 Reconstruct 适用条件

满足**全部**：

- PRD 描述的产品方向有效（用户群 / 核心价值不变）
- 但当前实现路径（架构 / 技术栈 / 数据模型）已根本走错
- 需要**从外部源系统重建**：本 project 作 source system，新 S3 project 用新方案重做

**风险**：

- 新 S3 project 需要重新走完整 7 阶段
- 旧 project 的代码 / 测试基本不可复用

### 5.4 Recommendation 决策原则

workflow-evolution 给出 recommendation 时应：

- 列每个 action 的**客观证据**（从 PRD / SRS / 测试数据 / incident 现象）
- 优先 continue（最低破坏性），仅在 continue 风险显著大于成本时升级到 reconstruct / abort
- 不要因为"看起来更彻底"推荐 reconstruct / abort（这两个不可逆）
- recommendation 必须能基于 §3 Root Cause Analysis 推出（不是直觉）

### 5.5 用户最终决定

用户可能与 recommendation 不一致。处理：

- 尊重用户决定，不要反复劝
- 在 §7 Resolution 记录用户决定 + 用户给出的 rationale
- 不要在 frontmatter / body 暗中"留 escape hatch"标记用户错（中立记录即可）

## 6. Output Contract

### 6.1 Incident Analysis Mode 输出

| Type | 输出 |
|------|------|
| A | 写 INCIDENT-NNN.md body §3-§7 |
| A | 改 INCIDENT frontmatter `status: draft → review-passed` |
| A | 改 INCIDENT frontmatter `resolution_action: null → <continue\|abort\|reconstruct>` |
| B | 调 `skills/workflow-protocol/scripts/progress.py incident-resolve --action <enum>` |
| B | 退出本 skill；后续由 progress.py mutation 后的 state 决定路由 |

### 6.2 Retrospective Consumption Mode 输出

| Type | 输出 |
|------|------|
| C | conversation 文本（按 §4.3 模板） |
| C | （可选）告知用户持久化路径（retrospective-write Change Mode 或 dev-workflow-skills2 design proposal） |

### 6.3 不输出

- ❌ 不创建 / 修改任何 stage doc（PRD / SRS / Architecture / Development / Testing / Delivery / Retrospective）
- ❌ 不修改 `dev-workflow-skills2` 自身的 skill 文件 / spec / design
- ❌ 不直接 mutation `progress.md`（mutation 走 progress.py）
- ❌ 不创建新 doc type（如 "improvement-proposal"）—— 这种扩展需 design review

## 7. Concurrency & Idempotency

### 7.1 Incident Analysis Mode

- 同一 INCIDENT-NNN.md 不允许两个 workflow-evolution 实例并发编辑（doc 编辑层无锁）
- progress.py incident-resolve 内部 flock 保证 progress.md 原子
- **重复 invoke 严格规则（v0.6 round 3 M5）**：仅当下列**全部**为真才允许"直接重试 incident-resolve"，否则必须重走 §3.1 Step 6.e-g：
  1. INCIDENT body §3-§7 已填
  2. frontmatter resolution_action ∈ {continue, abort, reconstruct}
  3. frontmatter status == review-passed
  4. **`## Pending Changes` 章节为空（仅空白行 / HTML comment）**
  5. **最近一次 `validate.py file <incident-path>` exit 0**（重 invoke 时必须再跑一次 validate 确认）
  6. workflow_incident_active == true（progress.md 还未被 incident-resolve 改）

  缺任一项 → 不允许直接重试；必须按 §3.1 Step 6.e-g 重做（必要时补 Pending entry → promote → validate → 再 incident-resolve）。

### 7.2 Idempotency 边界（v0.6 round 3 M5 拆 finalization-complete vs body-only）

| 状态 | 重复 invoke 行为 |
|------|----------------|
| `INCIDENT.body §3-§7 空, frontmatter resolution_action=null` | 正常 incident analysis 流程 |
| `INCIDENT.body §3-§6 已填, §7 空, resolution_action=null` | 跳过 §3-§6，与用户决策填 §7 → 走完整 §3.1 Step 6.a-g |
| **`body §3-§7 已填 + resolution_action 已设 + status=review-passed`，但 Pending 非空 / validate 未跑或 fail / promote 未做**（**finalization 未完成**）| **必须重走 Step 6.e-g**：补 Pending entry（如改动还没记） → `changelog.py promote` → `validate.py file` → 全 pass 后才能 incident-resolve；不允许"直接重试"|
| **`body §3-§7 已填 + resolution_action 已设 + status=review-passed + Pending 已空 + validate.py file 重新 exit 0`**（**finalization complete**）| 仅重试 `progress.py incident-resolve --action <enum>`（progress.py 调用失败重试场景）|
| `workflow_incident_active=false` | 已经 resolved；本 skill 退出（不应被 invoke）|

**关键约束**：从"body/frontmatter 已写"到"finalization complete"之间的状态对外**不可观测**——session 中断后重 invoke 时**不能信任** "status=review-passed" 单独表示 finalization 已 done。必须重跑 validate.py 确认 Pending 为空才能进 progress.py incident-resolve。

### 7.3 Retrospective Consumption Mode

- 完全无副作用 → 可任意并发调用
- 每次重新分析（结果可能因 input doc 变化而不同）

## 8. Recursion Constraint（递归悖论）

### 8.1 严格禁止

workflow-evolution **绝不**修改 `dev-workflow-skills2` 自身的：

- skill 文件（`skills/*/SKILL.md`、`references/*.md`、`scripts/*.py`）
- workflow spec（`docs/workflow/workflow_specification_claude.md`）
- design proposal（`docs/design/skill_set_design_proposal_v*.md`）
- AGENTS.md template / CLAUDE.md template
- 任何 doc-guardian 配置

理由：本 skill 集作用于**用户的项目**，不应作用于自身（recursive paradox，参见 dev_workflow_skills v1 D-003/D-006）。任何对 dev-workflow-skills2 自身的修改必须走独立 project 的设计流程。

### 8.2 区分"禁止 patch"与"允许 advisory 建议"（v0.6 round 2 batch2-F4）

workflow-evolution **绝对禁止**：

- 直接编辑 `dev-workflow-skills2` 自身任何文件（skill / spec / design / template / scripts）
- 输出可直接应用的 **patch / diff / unified diff** 文本针对本 skill 集
- 自动 commit / PR / 任何 mutation 类操作影响 dev-workflow-skills2 仓库

workflow-evolution **允许并鼓励**：

- 在 INCIDENT body §4 Workflow Improvement Suggestions 输出**具体的 advisory 改进建议**，例如"prd-review skill §X.Y 加 NFR feasibility rubric 项"、"workflow_specification §Z 增加用户访谈必备 artifact"
- 在 retrospective consumption 输出 advisory 建议针对本 skill 集（明确标注"提交到 dev-workflow-skills2 design proposal review cycle"）
- 引用具体的 skill / 章节 / rubric 项位置（精确化建议有助于 design proposal 落地，不会让 advisory 价值被稀释为空泛建议）

**关键区分**：

| 行为 | 允许 | 例子 |
|------|------|------|
| 输出 advisory **改进建议**（自然语言描述）| ✓ | "建议 prd-review SKILL.md §6.3 评审 rubric 加'NFR feasibility check'子项" |
| 输出 patch / diff / 直接可应用的代码改动 | ✗ | `--- a/skills/prd-review/SKILL.md\n+++ b/skills/prd-review/SKILL.md\n@@ ...` |
| 引用具体 skill / 章节做精确建议 | ✓ | "建议在 workflow-protocol §5.1 P6 矩阵 D 维度加…" |
| 直接 patch 本仓库文件 | ✗ | Edit / Write 任何 dev-workflow-skills2 文件 |
| advisory 标注 "提交 design proposal cycle" | ✓ | "Action Item: 提交到 dev-workflow-skills2 仓库走独立 design proposal review cycle" |
| 自行声明 "本建议已采纳"或"本 incident 自动改 spec" | ✗ | 任何 patch 类语义 |

如果分析揭示 dev-workflow-skills2 工作流本身有缺陷，应在 §4 输出**精确 advisory 建议**（自然语言 + 引用位置），并在每条建议尾部标注 "Action Item: 提交 dev-workflow-skills2 design proposal review cycle"。

### 8.3 例外（无）

无例外。哪怕用户明确要求"帮我改 skills/workflow-protocol/SKILL.md 加新 hook"，workflow-evolution 也应拒绝并提示：

```
"修改 dev-workflow-skills2 自身的 skill / spec / design 不属于本 skill 职责。
 这类修改应在 dev-workflow-skills2 仓库走 design proposal review cycle，
 不能从本 project 的 incident analysis 或 retrospective consumption 直接 patch。"
```

## 9. Forbidden Actions

- ❌ 修 PRD / SRS / Architecture / Development / Testing / Delivery / Retrospective 内容（无写权；改建议交对应 stage skill 在 Change Mode 处理）
- ❌ 修 `dev-workflow-skills2` 自身的 skill / spec / design / template 文件（递归悖论）
- ❌ 创建新 doc type（如 "improvement-proposal" / "evolution-report"）—— 需 design review
- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 在 `workflow_incident_active==false` 时进入 incident analysis mode（应退出）
- ❌ 在 retrospective consumption mode 中持久化输出为新 doc（仅 conversation）
- ❌ 写 INCIDENT body 时省略 §3-§7 任一章节
- ❌ 调 `progress.py incident-resolve` 时未先写 INCIDENT frontmatter resolution_action
- ❌ INCIDENT frontmatter resolution_action 与 body §7 Resolution 不一致
- ❌ 创建 INCIDENT skeleton（这是 `bug-triage` 责任；本 skill 仅填 body）
- ❌ 推荐用户做未经 design review 的 dev-workflow-skills2 自身修改
- ❌ 在 incident analysis 中替用户做 3 action 决策（必须用户最终选择）
- ❌ 跳过 `validate.py file <INCIDENT path>` 校验直接调 incident-resolve
- ❌ **在 `validate.py file` pass 之后再改 INCIDENT frontmatter / body**（v0.6 round 2 batch2-F5）：所有 frontmatter / body 改动必须在 §3.1 Step 6 严格序列内完成（先全部 mutation → Pending → promote → validate）；validate 后到 incident-resolve 之间**禁止**任何 doc 编辑；如确实发现需要补充，必须重走 Step 6.a-g（含再 promote + 再 validate），不得 silent 改后调 incident-resolve
- ❌ **跳过 `changelog.py promote` 直接 validate**（v0.6 round 2 batch2-F5）：每次 INCIDENT 编辑（Step 5 §3-§6 + Step 6 §7 + frontmatter mutation）都必须有对应 ## Pending Changes entry，promote 是 validate 前置；不允许 manual 编辑 Change Log 章节

## 10. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| INCIDENT-NNN.md skeleton 不存在或 frontmatter 损坏 | 不修复 skeleton（那是 bug-triage 责任）；提示用户调 `progress.py recover --confirm` 或重新触发 bug-triage 创建新 INCIDENT |
| Body §3-§7 写完后 validate.py file fail | 按 validate 错误修 body / frontmatter；不要 bypass validate 直接 incident-resolve |
| 用户拒绝 3 个 action 都不选 | 与用户继续对话；本 skill 不退出（不允许 incident state 长期挂着，但也不能强迫用户选）；提示用户：incident state 期间项目无法推进，必须选 1 |
| `progress.py incident-resolve` 拒绝（resolution_action enum 非法 / INCIDENT frontmatter validate fail）| 修 frontmatter 后重试 |
| 重 invoke 时检测到 status=review-passed 但 incident-resolve 未调用（v0.6 round 3 M5）| **不直接重试**：先跑 `skills/doc-guardian/scripts/validate.py file <incident-path>` 确认 Pending 已空、frontmatter 全合法；若 Pending 非空 / validate fail，重走 §3.1 Step 6.e-g（补 Pending entry → promote → validate）后才能调 incident-resolve；详见 §7.1 / §7.2 严格规则 |
| Retrospective consumption 输入数据不足（retrospective.md 太短）| 与用户对话补充上下文；不要凭模糊数据生成低质量建议 |
| 用户问"能不能直接改 dev-workflow-skills2 改进工作流"| 拒绝 + 解释（§8.3 模板）|

## 11. References

- `references/incident-analysis-template.md` — INCIDENT body §3-§7 详细模板 + 3 action decision matrix + 自评清单 + 端到端 examples
- `skills/workflow-protocol/SKILL.md` — workflow-protocol 主协议
- `skills/workflow-protocol/references/command-reference.md` — `incident-resolve` 3 action 完整 mutation
- `skills/doc-guardian/references/frontmatter-schema.md` — `workflow-incident` doc type schema
- `skills/bug-triage/SKILL.md` — INCIDENT skeleton 创建（前置）
- `docs/workflow/workflow_specification_claude.md`（项目级）— Workflow spec PRD 异常路径
- `docs/design/skill_set_design_proposal_v0.5.md`（项目级）— 完整设计方案（含递归悖论决策）
