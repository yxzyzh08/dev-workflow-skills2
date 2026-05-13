# Skill Set Design Proposal (Skill 集合设计方案)

**Version**: v0.3
**Date**: 2026-05-05
**Status**: Draft — 架构层与详细设计层闭环；待 Task 5 (skill SKILL.md drafts) 与 Task 6 (implementation)
**Workflow Reference**: `docs/workflow/workflow_specification_claude.md` (v0.3)
**Predecessors**: `v0.1` / `v0.2`
**Review Responses**: `docs/review/reviewer_feedback_response_v0.1.md` / `docs/review/reviewer_feedback_response_v0.2.md`

---

## 0. v0.2 → v0.3 主要变化

| 变化点 | 原因 | 影响范围 |
|--------|------|---------|
| 加 Logical vs Physical Skill 调和说明 | F1 | Section 3.1, workflow spec v0.3 |
| S4 policy 改 active-release-only | F2 (B) | Section 4.5.2 决策树、Section 4.12 |
| 加 `source-system-analysis` doc type | F3 | Section 5.3 |
| review-passed vs approved 术语规范 | F4 | Section 4.8/4.10 |
| progress.md 示例修正 | F5 | Section 4.2 |
| 加 `release-start` 命令 | F6 | Section 4.4 |
| code-review-report 加 pass/fail contract | F7 | Section 5.3 |
| 全 script 路径 normalize | F8 | 全文 |

---

## 1. Executive Summary

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合。本方案汇总 Task 1-4 的所有架构层与详细设计层决策，作为 Task 5（23 个 skill 骨架设计）和 Task 6（实现）的依据。

### 1.1 架构概览

- **23 个 physical skill**（对应 7 个 logical Stage Skill + 5 个 Cross-cutting/Orchestration/Meta），分 4 层
- **7 阶段主流程** + Bug Flow + 4 场景（S1-S4，含 S2 4 个子场景）
- **Release 严格串行**：同时只 1 个 active release，0.1 → 0.2 → 0.3 顺序推进
- **S4 仅在 active release 期间允许**（v0.3）；post-close bug 留待下次 S2
- **Foreman binary 校验**：doc-guardian 配 `skills/doc-guardian/scripts/validate.py`，exit code 决定 block/pass
- **评审循环**：write → review → revise，cap = 7 次，超限升级人介入；revise 由 `*-write` 在 Change Mode 下完成
- **vendor-neutral**：`CLAUDE.md = @AGENTS.md`，AGENTS.md 治理层 + workflow-protocol 操作层；命令统一 `skills/<name>/scripts/...` 全路径

### 1.2 项目设计哲学

- 用户偏好：先框架后细节；记忆有限所以阶段名要少要清晰；避免文档漂移所以小需求也强制走全流程
- 工作流自身演进：Stage 7 复盘 + PRD 根因异常 两条路径汇入元改进
- 递归悖论意识：本 skill 集**不应作用于 dev-workflow-skills2 自身**，仅用于其他项目
- 代码质量双轨：代码同时由 review skill 评审 + 测试验证（v0.2 起）

### 1.3 Logical vs Physical Skill（v0.3 reconciliation）

Workflow spec 的 "One Stage Skill" 是 **logical concept**：每个 Stage 对应一个 logical Stage Skill，承载 Stage 与 Mode 契约。

具体物理实现使用 **Foreman 拆分**：每个 logical Stage Skill 由一个或多个 physical skill 组成（如 `*-write` / `*-review` 配对）；所有 physical skills 共享同一 Stage 与 Mode 契约。

| Logical Stage Skill | Physical Skills |
|---------------------|-----------------|
| Stage 1 PRD | `prd-write` + `prd-review` |
| Stage 2 SRS | `srs-write` + `srs-review` |
| Stage 3 Architecture | `architecture-write` + `architecture-review` |
| Stage 4 Development | `development-planning-write` + `development-planning-review` + `development-test-write` + `development-test-review` + `development-code-write` + `development-code-review` |
| Stage 5 Testing | `testing-write` + `testing-review` |
| Stage 6 Delivery | `delivery-write` + `delivery-review` |
| Stage 7 Retrospective | `retrospective-write` + `retrospective-review` |

总计 7 logical Stage Skill = 18 physical Vertical Skill；加 Cross-cutting/Orchestration/Meta 5 个 = **23 physical skill**。

### 1.4 当前进度

| Task | 状态 | 输出 |
|------|------|------|
| Task 1: 架构层决策 | ✅ Done（v0.3：F1/F2 落地）| D1-D5 / Q1-Q3 / Logical vs Physical 调和 |
| Task 2: workflow-protocol 设计 | ✅ Done（v0.3：F5/F6/F7 落地）| 5 项责任、progress 格式、scripts、并发模型、P6 矩阵、release lifecycle |
| Task 3: AGENTS.md template | 🟡 Draft v0.3（路径、术语调整）| 10-section template |
| Task 4: doc-guardian 设计 | ✅ Done（v0.3：F3/F4/F8 落地）| F1-F6 (F4 跳过)，含 source-system-analysis 类型 |
| Task 5: 23 个 skill 骨架 | ⏳ Pending | 按 3 批展开 |
| Task 6: 实现 | ⏳ Pending | 写实际 SKILL.md / scripts / AGENTS.md / CLAUDE.md |

---

## 2. Workflow Reference

完整 workflow spec 在 `docs/workflow/workflow_specification_claude.md` (v0.3)。

### 2.1 主流程 7 阶段

| # | Stage | Lead | Human Gate | 主要产出 |
|---|-------|------|------------|---------|
| 1 | PRD Inception | Human + AI | ✓ | PRD + Supporting Artifacts |
| 2 | SRS Specification | Human + AI | ✓ | SRS + Acceptance Plan + Integration Plan（多模块时）|
| 3 | Architecture Design | AI | ✓ | Architecture + (per-release) architecture_delta |
| 4 | Development | AI | × | Plan + Breakdown + Detailed Design + Tests + Source Code（含 code review）|
| 5 | Testing | AI | × | Test Preparation + Procedure + Report |
| 6 | Delivery | AI | × | Deployment Doc + Operation Manual + Installation Result |
| 7 | Project Retrospective | AI | × | Issue Report + Improvement Proposals（项目级，每 release 增量加节）|

### 2.2 4 场景

| Code | Name | 流程 | Input |
|------|------|------|-------|
| S1 | New Product | 主流程全程 | 无 |
| S2 | Feature Evolution | 主流程全程（含 4 子场景路由）| 当前项目的 PRD/SRS/Architecture |
| S3 | Product Reconstruction | 主流程全程 | 源系统 PRD + 源系统 SRS（**Stage 1/2 强制要求源系统分析**）|
| S4 | Bug Fix | Bug Flow | Bug Report；**仅在 active release 期间触发** |

### 2.3 Bug Flow 4 类根因路由

| 根因 | 路径 |
|------|------|
| SRS | CR Document → SRS Update → Architecture Update? → Development → Testing |
| Architecture | Architecture Update（仅版本历史）→ Development → Testing |
| Development | Development Update → Testing |
| PRD（异常逃生阀）| 项目暂停 → Workflow Incident Analysis |

### 2.4 关键规则

- **变更记录**：仅 SRS 变更需 CR Document；Architecture 仅版本历史；其他无需
- **Skill 复用**：同一 logical Skill 通过 Full Mode / Change Mode 应对 4 个场景
- **元演进**：Stage 7 + PRD 根因异常 都汇入 workflow-evolution

---

## 3. Skill Architecture (Task 1)

### 3.1 4 层架构

| Layer | 职责 | Physical Skill 数 |
|-------|------|---------|
| 1 Vertical | 主流程 7 logical Stage Skill 的 write/review skill 配对 | **18** |
| 2 Cross-cutting | workflow-protocol / doc-guardian | 2 |
| 3 Orchestration | scenario-dispatcher / bug-triage | 2 |
| 4 Meta | workflow-evolution | 1 |
| **总计** | | **23** |

### 3.2 Vertical Skill 完整清单（18 个 physical skill = 7 logical Stage Skill）

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + Supporting Artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 release 引发的 architecture_delta）|
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests（测试代码）|
| `development-code-write` / `development-code-review` | 4 | Source Code（关注架构一致性 / 安全 / 可维护性 / 边界覆盖）|
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective（项目级，每 release 增量加节）|

### 3.3 架构层决策（已闭环）

| ID | 决策点 | 选定 |
|----|--------|------|
| 评审结构 | Skill 拆分模式 | Foreman 模式（write/review 分开 physical skill）|
| 评审上限 | 评审循环最多次数 | 7 次 |
| Stage 4 拆分 | Development 内部分组 | Option I：规划设计 / 测试 / 代码 三组（含 code review）|
| 代码评审 (v0.2) | Source Code 是否走 review | 是（development-code-review）|
| D1 | doc 校验机制 | Foreman binary：doc-guardian 配 `scripts/validate.py`，exit 0/1 |
| D2 | CLAUDE.md 形态 | foreman 模式 |
| D3 | SessionStart Hook | 不要 |
| D4 | vendor-neutral skill 结构 | 要：双 symlink |
| D5 | Risk-based review | 不要 v1 |
| Q1 | 评审超 7 次 | 升级人介入 |
| Q2 | cr-guardian | 合并进 doc-guardian |
| Q3 | project-memory-manager | 不独立 |
| 脚本路径 (v0.2) | 命令路径 | 全 skill 路径 |
| Release 并发 (v0.2) | 是否可并发 | 严格串行 |
| **S4 policy (v0.3 F2)** | closed release 时 S4 如何 | **(B)** S4 仅 active release 期间允许；post-close bug 留待下次 S2 |
| **Logical vs Physical (v0.3 F1)** | Spec "One Stage Skill" 与 23 skill 关系 | "One Stage Skill" 是 logical；可对应多个 physical skill（write/review 配对）|

### 3.4 关键设计原则

设计任何 skill 时遵守：

- 检查它属于哪一层
- vertical skill 必须支持 Full Mode + Change Mode
- 任何 doc 类产物完成前必须调 `skills/doc-guardian/scripts/validate.py`（exit code 决定 block/pass）
- 任何阶段转换必须由 workflow-protocol 驱动，stage skill 不可自行决定下一步
- 评审是流程控制（write → review → revise → loop），不是 stage 内部 sub-process
- **Revise 由 `*-write` skill 在 Change Mode 下完成**——无独立 `*-revise` skill；review 失败时 workflow-protocol 把 sub_state 设为 `revising` → 重新 invoke `*-write`（Change Mode）→ 完成后回到 `in-review` → invoke `*-review`，review_iteration +1
- **`*-review` skill 输出术语**：用 `review-passed` 表示 AI review 通过；用 `issues-found` 表示需要 revise；**绝不用 `approved`**（`approved` 仅用于人 gate 后的最终态）
- 不要重复 doc 校验逻辑——doc-guardian 是唯一入口
- skill 命名用 verb-noun，避开 noun-only 反模式
- 单个 SKILL.md 控制在合理篇幅

---

## 4. workflow-protocol Skill Design (Task 2)

### 4.1 责任清单（精简后 5 项）

| # | 责任 | 备注 |
|---|------|------|
| 1 | 状态机定义 | Hybrid: YAML schema + 转移表 + prose 解释 |
| 2 | 转换规则 | state X → state Y 的合法性 |
| 3 | Hook 闭环 / "MUST call X" 硬约束 | 各阶段强制调用清单 |
| 4 | progress.md / progress-history.md 管理 | 含 `skills/workflow-protocol/scripts/progress.py` |
| 5 | 评审循环计数 + 超 7 升级 | 在 progress.md 记录 review_iteration |

剥离责任：Bootstrap → AGENTS.md；Scenario 路由 → scenario-dispatcher；Bug 流程路由 → bug-triage。

### 4.2 progress.md Schema（v0.3 修正示例）

路径：项目根 `progress.md`
格式：YAML frontmatter + markdown body + Recent Activity（自动从 history 派生）
写入：唯一通过 `skills/workflow-protocol/scripts/progress.py update`，禁止直接编辑

```yaml
---
project_name: my-product
workflow_version: v0.3
release: "0.3"                     # 当前 active release（v0.3 修正：示例内部一致）
release_state: active              # active / closed
previous_releases:                 # 已 close 的 release 列表（只读，新 release 必须 > all previous）
  - "0.1"
  - "0.2"
scenario: S2
scenario_subtype: S2-1             # S2 时必填 S2-1/S2-2/S2-3/S2-4；其他场景 null
current_stage: srs-specification

# 通用 sub-state（development 之外的 stage）
sub_state: in-review               # write / in-review / revising / review-passed / approved
review_iteration: 2                # 评审循环计数（cap=7）

# Stage 4 development 专用（仅 current_stage=development 时存在）
development_state:
  total_tasks: 5
  task_states:
    T1: verified
    T2: test-writing
    T3: code-review
    T4: test-done
    T5: planning-done

# 文档产物路径（不含代码）
artifacts:
  prd: docs/prd/prd.md                                # 项目级
  architecture: docs/architecture/architecture.md     # 项目级
  srs: docs/release0.3/srs/srs.md                     # release 级
  acceptance_plan: docs/release0.3/srs/acceptance_plan.md
  integration_plan: docs/release0.3/srs/integration_plan.md
  architecture_delta: docs/release0.3/architecture_delta.md

# Bug 流程
bug_flow:
  active: false
  bug_report_path: null
  root_cause: null               # SRS / Architecture / Development

# Post-close 待处理 bug（v0.3 F2 新加）
unresolved_bugs:                 # release close 后新发现的 bug，等下次 S2 启动时由 srs-write 扫描合并
  - docs/bug/BUG-005.md
  - docs/bug/BUG-006.md

created: 2026-05-04T08:00:00Z
updated: 2026-05-05T10:00:00Z
---

# Current Stage Summary

**Stage**: SRS Specification
**Sub-state**: in-review (iteration 2 of 7)
**Document**: docs/release0.3/srs/srs.md
**Last action**: review found 1 issue
**Next action**: srs-write Change Mode (revise)

# Recent Activity (auto-derived from progress-history.md)

## 2026-05-05T10:00:00Z — srs-review iteration 2 — 1 issue found
## 2026-05-05T08:30:00Z — srs-review iteration 1 — 3 issues found
## 2026-05-05T08:00:00Z — srs-write completed
```

### 4.3 progress-history.md Schema

路径：项目根 `progress-history.md`
格式：append-only，时间顺序（旧顶新底）
每条 entry 严格模板（脚本生成）：

```markdown
## {ISO8601 UTC timestamp} — {action_type} — {one_line_result}
- agent: {agent_id}
- task: {task_id, 仅 Stage 4 时存在}
- result: {结构化结果}
- next: {next_action}
```

### 4.4 scripts/progress.py 接口（v0.3 加 release-start）

物理路径：`skills/workflow-protocol/scripts/progress.py`

| Subcommand | 用途 |
|-----------|------|
| `init` | 新项目首次初始化 progress.md（创建首个 release）|
| `update` | 应用一次状态转换（原子更新两文件 + 回退）|
| `query` | 读取当前 state（只读，可并发）|
| `recover` | 从 progress-history.md 重建 progress.md |
| `release-close` | 当前 release Stage 7 完成时，标记 release_state=closed，准备启动下个 release |
| **`release-start --version <x.y>`** (v0.3 新加) | 启动新 active release；前置条件：当前 release 已 close 且 `<x.y>` 严格大于所有 `previous_releases`；自动初始化 release-scoped artifact 路径并重置 stage state |

`update` 原子流程（不变）：

1. 计算 new_progress + new_history_entry
2. flock on `.progress.lock`
3. 备份两个文件
4. 校验状态机转换合法性
5. 写入：append progress-history.md → overwrite progress.md
6. 一致性校验
7. 任一步失败 → rollback；成功 → 删备份 + 解锁

`release-start` 校验：

- 必须有 closed release（首个 release 用 `init` 不用 `release-start`）
- 新 version 必须严格大于 previous_releases 中所有版本
- progress.md `release_state` 必须是 closed
- 同时只允许 1 个 active release（拒绝重复启动）

### 4.5 Scenario Routing

#### 4.5.1 S2 子场景路由表

scenario-dispatcher 在判定 S2 后，必须进一步判定 sub-type：

| 子场景 | 适用条件 | 入口 Stage | progress 字段 |
|--------|---------|-----------|---------------|
| **S2-1** | PRD 变更引入新功能（不影响原有核心功能/边界）| PRD Inception (Change Mode) | `scenario: S2, scenario_subtype: S2-1` |
| **S2-2** | PRD 不变，仅新增 Software Requirement / 接口 / 行为 | SRS Specification (Full Mode for new sections) | `scenario: S2, scenario_subtype: S2-2` |
| **S2-3** | PRD 不变，仅修改 SRS 细节 / 验收 / 接口 | SRS Specification (Change Mode) | `scenario: S2, scenario_subtype: S2-3` |
| **S2-4** | PRD 变更影响原有核心功能，需要 reconstruction | 终止当前 evolution → 转 S3（新 project）| 不进入 S2 流程 |

**S2 → release 关系**：S2-1/2/3 全部映射为"新 release"；S2-4 转 S3 是新 project（不是 release）。

#### 4.5.2 详细路由（v0.3 修正 S4 部分）

scenario-dispatcher 决策树：

```
项目根有 progress.md？
  否 → S1 (新项目) 或 S3 (重构)，由用户/scenario-dispatcher 选择
  是 → progress.md release_state == active？
        是 → 当前 release 进行中
              ├ 想加新需求 → 拒绝（active release 不接受新需求；需先完成当前 release）
              ├ Stage 5 测试发现 bug → S4 Bug Flow（在当前 active release 内修）
              └ 继续当前 stage → 按 current_stage 路由到对应 skill
        否（closed）→ 当前 release 已 close
              ├ S2 启动新 release（含合并 unresolved_bugs）→ progress.py release-start
              ├ S3 转新项目（如果整体重构）
              └ S4 不可用 ✗（v0.3 F2）
```

**S4 严格在 active release 内**（v0.3 F2）：post-close 发现的 bug 报告写入 `docs/bug/BUG-NNN.md`，frontmatter `target_release: null`，等用户启动下一个 S2 时 srs-write skill 扫描并合并到新 SRS。

### 4.6 并发模型

- **统一接口**：任何 agent（无论主协调还是 sub-agent）都通过 `progress.py update`
- **锁内部处理并发**：多 agent 并发请求由锁序列化
- **Stage 4 子 agent 接口（Option B）**：调一律是 `update`，脚本 diff old vs new task state；没变只 append history、变了原子更新两文件

### 4.7 两层粒度

| 文件 | 粒度 | 装什么 |
|------|------|--------|
| progress.md | 任务级（T1, T2, ...）| task 状态、stage 状态 |
| progress-history.md | 子任务级 + 任务级 | 所有有意义事件 |

子任务（"T2 完成第 5 个测试"）只在 history 里，progress.md 不出现。

### 4.8 P6 Stage 完成判定矩阵（v0.3 术语规范）

通用 4 维 + 部分 stage 第 5 维：

| 维度 | 检查方式 | 失败动作 |
|------|---------|---------|
| A. 必需 artifacts 存在 | 文件路径在 `artifacts:` 中且文件存在；**S3 场景 Stage 1/2 强制额外检查源系统分析 artifacts** | block |
| B. doc-guardian 校验通过 | `validate.py` 跑所有 artifacts exit 0 | block |
| C. Review 通过 | 对应 `*-review` skill 最后一轮返回 `review-passed` (no blocking findings)；**v0.3 注：用 `review-passed`，不用 `approved`** | 触发新一轮 revise（计数+1，超 7 升级人介入）|
| D. 人确认（仅 PRD/SRS/Architecture/CR）| progress-history.md 有 "human-confirmed" 条目；该 doc frontmatter `status: approved` | block |
| E. 内部验证（Stage 4/5/6）| verification artifact frontmatter 含 `verification_status: pass` | 视情况：fail → Bug Flow / 重试 |

### 4.9 7 个 Stage 的判定矩阵

| Stage | A. 必需 Artifacts | B. doc-guardian | C. Review | D. Human | E. Verification |
|-------|-------------------|-----------------|-----------|----------|----------------|
| 1 PRD | PRD（S3 时含源系统 PRD 分析 + Feature Matrix）| ✓ | review-passed | ✓ approved | — |
| 2 SRS | SRS + Acceptance Plan + Integration Plan（多模块）（S3 时含源系统 SRS / Module 分析等）| ✓ | review-passed | ✓ approved | — |
| 3 Architecture | Architecture Document（+ delta if applicable）| ✓ | review-passed | ✓ approved | — |
| **4 Development** | 见 4.10 特殊判定 | | | | |
| 5 Testing | Test Preparation + Procedure + Report | ✓ | review-passed | — | Test Report `verification_status: pass`（fail → Bug Flow）|
| 6 Delivery | Deployment + Operation Manual + Installation Result | ✓ | review-passed | — | Installation 执行成功 |
| 7 Retrospective | Issue Report + Improvement Proposals | ✓ | review-passed | — | — |

### 4.10 Stage 4 特殊判定（v0.3 术语规范）

```
Stage 4 done ⇔ all task_states[Tn] == "verified"
```

每 task 完整子状态序列：

| 子状态 | 满足条件 |
|--------|---------|
| `planning-done` | Detailed Design (Tn) 通过 doc-guardian + review-passed |
| `test-writing` → `test-review` → `test-revising` → `test-done` | Unit/Integration Tests 通过 doc-guardian + review-passed |
| `code-writing` → `code-review` → `code-revising` → `code-review-passed` | Source Code 通过 development-code-review，要求 code-review-report 满足 `review_status: pass` 且 `blocking_findings_count: 0` |
| `verifying` → `verified` | unit + integration test 全部 pass（development-code-write 跑测试，写 Local Verification Result `verification_status: pass`）|

### 4.11 Bug Flow 触发

Stage 5 E 失败（Test Report `verification_status: fail`）→ 不推进 Stage 6，进入 Bug Flow：

1. workflow-protocol 设 `bug_flow.active = true`，记录 `bug_report_path` 和 `root_cause`（由 bug-triage skill 输出）
2. `current_stage` 切到 root_cause 对应的 stage（Change Mode）
3. 该 stage Change Mode 的 done 条件 = "影响范围内的 artifacts 重新通过 A/B/C/D/E"
4. 完成后自动回到 Stage 5 重测
5. Pass 后 `bug_flow.active = false`，正常推进 Stage 6

### 4.12 Release Lifecycle Rule（v0.3 含 S4 policy）

**核心原则**：Release 严格串行，不可并发。

| 规则 | 内容 |
|------|------|
| 同时只 1 个 active release | progress.md `release_state` 字段约束 |
| Release 创建 | 当前 release 走完 Stage 7 close 后，由 `progress.py release-start` 启动下个 |
| Release 编号 | 用户在 `release-start` 时手动指定；必须严格大于 `previous_releases` 中所有版本 |
| Release close 条件 | Stage 7 retrospective 完成且 review-passed（不是 Delivery 完成）|
| 历史 release 只读 | release close 后，对应 `docs/release0.x/` 目录变只读 |
| **S4 policy（v0.3 F2 选 B）** | **S4 仅在 active release 期间触发**（即 release_state=active 且 current_stage=testing 发现 bug）|
| **Post-close bug 处理** | release close 后新发现的 bug 写入 `docs/bug/BUG-NNN.md`，`target_release: null`，加入 progress.md `unresolved_bugs` 列表；待下次 S2 release-start 时，srs-write skill 扫描并合并到新 SRS |
| S2 → release 映射 | S2-1/2/3 全部触发新 release；S2-4 转 S3 是新 project |

### 4.13 Revise Action Ownership

**Revise 由 `*-write` skill 在 Change Mode 下完成**——无独立 `*-revise` skill。

review 失败时的状态转换：

```
sub_state: in-review (review skill 输出 "issues-found")
  ↓ workflow-protocol 转换
sub_state: revising  +  review_iteration += 1
  ↓ workflow-protocol invoke *-write skill in Change Mode
sub_state: in-review (write skill 完成 revise)
  ↓ workflow-protocol invoke *-review skill
sub_state: revising 或 review-passed (按 review 结果)
```

每个 `*-write` skill 的 SKILL.md 必须明示如何区分 Full Mode 和 Change Mode。

### 4.14 关键约定

- **Verification artifact** 必含 `verification_status: pass | fail | partial`
- **Code review report** 必含 `review_status: pass | fail` + `blocking_findings_count: int` + `max_severity: low|medium|high|critical`（v0.3 F7）
- **Required vs Optional artifacts** 由 doc-guardian 集中声明（`skills/doc-guardian/references/required-artifacts.md`，scenario-aware）
- **Stage advance** 显式：stage skill 调 `progress.py update --advance`，workflow-protocol 校验 done 条件后推进，可拒绝
- **Review skill 输出术语**：`review-passed` / `issues-found`；不用 `approved`

---

## 5. doc-guardian Skill Design (Task 4)

### 5.1 F1: 完整目录结构（v0.3 含 source-system-analysis 类型）

```
my-project/
├── AGENTS.md
├── CLAUDE.md
├── progress.md
├── progress-history.md
│
├── docs/
│   ├── prd/                              # 项目级
│   │   ├── prd.md
│   │   └── supporting/
│   │       ├── competitor_research.md
│   │       ├── competitor_architecture.md
│   │       ├── market_research.md
│   │       ├── feature_matrix.md                       # S3 必备 (analysis_kind: feature-matrix)
│   │       └── source_product_prd_analysis.md          # S3 必备 (analysis_kind: prd-level)
│   │
│   ├── architecture/                     # 项目级
│   │   └── architecture.md
│   │
│   ├── release0.1/
│   │   ├── srs/
│   │   │   ├── srs.md
│   │   │   ├── acceptance_plan.md
│   │   │   ├── integration_plan.md
│   │   │   ├── source_product_srs_analysis.md          # S3 必备 (analysis_kind: srs-level)
│   │   │   ├── source_module_analysis.md               # S3 必备 (analysis_kind: module-level)
│   │   │   ├── reuse_replace_capability.md             # S3 必备 (analysis_kind: reuse-replace)
│   │   │   └── technical_debt_analysis.md              # S3 推荐 (analysis_kind: technical-debt)
│   │   ├── architecture_delta.md
│   │   ├── development/
│   │   │   ├── plan.md
│   │   │   ├── breakdown.md
│   │   │   └── tasks/
│   │   │       └── T1/
│   │   │           ├── detailed_design.md
│   │   │           ├── code_review_report.md
│   │   │           └── verification_result.md
│   │   ├── testing/
│   │   │   ├── preparation.md
│   │   │   ├── procedure.md
│   │   │   └── report.md
│   │   └── delivery/
│   │       ├── deployment.md
│   │       ├── operation_manual.md
│   │       └── installation_result.md
│   │
│   ├── release0.2/  ...
│   │
│   ├── retrospective/
│   │   └── retrospective.md
│   │
│   ├── cr/
│   │   ├── CR-001.md
│   │   └── CR-002.md
│   │
│   └── bug/
│       ├── BUG-001.md
│       └── BUG-002.md
│
├── src/
└── tests/
```

### 5.2 F2: 命名 Convention

- **Doc 文件**：lowercase + underscore + `.md`
- **CR / Bug Reports**：ID 大写 `CR-001.md`、`BUG-005.md`
- **不带 `_claude` 后缀**
- **Task 子目录**：`T1/`、`T2/` 大写 + 数字
- **Release 目录**：`release0.1/`、`release0.2/`

### 5.3 F3: Frontmatter Schema（v0.3 含 source-system-analysis、code-review-report 增强）

#### Universal（所有 doc 必含）

```yaml
---
title: <human readable>
type: <doc-type-id>
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/<skill_name>
---
```

#### Status 状态机（v0.3 强调术语区分）

| 状态 | 含义 | 适用 |
|------|------|------|
| `draft` | 写作中 | 全部 doc |
| `in-review` | review skill 评审中 | 全部 doc |
| `revising` | 收到 review 反馈在修订（write skill Change Mode 中）| 全部 doc |
| `review-passed` | AI review 通过（**最终态：非 gated 文档**）| 全部 doc |
| `approved` | 人确认通过（**最终态**）| **PRD / SRS / Architecture / CR** |

**v0.3 术语强调**：`*-review` skill 的输出（review 报告）用 `review-passed` / `issues-found`；与 doc 自身 frontmatter `status` 字段语义不同：

- doc frontmatter `status: review-passed` = doc 整体进入 AI 已通过状态
- review skill 输出 `review-passed` = 当轮 review 没有 blocking issue（驱动 doc status 转移）

#### Per-Type Extensions

| Type | 路径 | 扩展字段 |
|------|------|---------|
| `prd` | `docs/prd/prd.md` | 无 |
| `architecture` | `docs/architecture/architecture.md` | 无 |
| `retrospective` | `docs/retrospective/retrospective.md` | 无 |
| `srs` | `docs/release0.x/srs/srs.md` | `release` |
| `acceptance-plan` | `docs/release0.x/srs/acceptance_plan.md` | `release`, `related_srs` |
| `integration-plan` | `docs/release0.x/srs/integration_plan.md` | `release` |
| `architecture-delta` | `docs/release0.x/architecture_delta.md` | `release`, `parent_architecture` |
| `development-plan` | `docs/release0.x/development/plan.md` | `release` |
| `task-breakdown` | `docs/release0.x/development/breakdown.md` | `release`, `total_tasks` |
| `detailed-design` | `docs/release0.x/development/tasks/Tn/detailed_design.md` | `release`, `task_id` |
| **`code-review-report`** (v0.3 增强) | `docs/release0.x/development/tasks/Tn/code_review_report.md` | `release`, `task_id`, `findings_count`, `severity_distribution`, **`review_status: pass\|fail`**, **`blocking_findings_count: int`**, **`max_severity: low\|medium\|high\|critical`** |
| `verification-result` | `docs/release0.x/development/tasks/Tn/verification_result.md` | `release`, `task_id`, `verification_status` |
| `test-preparation` | `docs/release0.x/testing/preparation.md` | `release` |
| `test-procedure` | `docs/release0.x/testing/procedure.md` | `release` |
| `test-report` | `docs/release0.x/testing/report.md` | `release`, `verification_status`, `total_test_cases`, `passed`, `failed` |
| `deployment-doc` | `docs/release0.x/delivery/deployment.md` | `release` |
| `operation-manual` | `docs/release0.x/delivery/operation_manual.md` | `release` |
| `installation-result` | `docs/release0.x/delivery/installation_result.md` | `release`, `verification_status` |
| `cr` | `docs/cr/CR-NNN.md` | `cr_id`, `target_release`, `affected_doc` |
| `bug-report` | `docs/bug/BUG-NNN.md` | `bug_id`, `found_in_release`, `target_release` (可空), `root_cause` |
| **`source-system-analysis`** (v0.3 新加) | 见下表 | `release` (可空，PRD-level 时 null), `analysis_kind`, `source_system_name` |

#### `source-system-analysis` 详细 schema（v0.3 F3）

| `analysis_kind` 值 | 路径 | 适用 release | 说明 |
|---------------------|------|-------------|------|
| `prd-level` | `docs/prd/supporting/source_product_prd_analysis.md` | null（项目级）| 源系统 PRD 层面分析 |
| `feature-matrix` | `docs/prd/supporting/feature_matrix.md` | null（项目级）| 功能保留/裁剪/增强矩阵 |
| `srs-level` | `docs/release0.x/srs/source_product_srs_analysis.md` | `<release>` | 源系统 SRS 层面分析 |
| `module-level` | `docs/release0.x/srs/source_module_analysis.md` | `<release>` | 源系统 Module / Interface 分析 |
| `reuse-replace` | `docs/release0.x/srs/reuse_replace_capability.md` | `<release>` | 能力复用 vs 替换分析 |
| `technical-debt` | `docs/release0.x/srs/technical_debt_analysis.md` | `<release>` | 源系统技术债与风险分析（推荐，非必备）|

S3 场景下：

- Stage 1 必备：`prd-level`、`feature-matrix`
- Stage 2 必备：`srs-level`、`module-level`、`reuse-replace`（可选 `technical-debt`）

`required-artifacts.md` 在 doc-guardian 中按 scenario × stage 维度声明这些必备项。

### 5.4 F4: 必需章节 — Skipped

每个 doc 类型的 body 章节由对应的 write/review skill pair 协调（共享 sections 列表）。doc-guardian 不强制 body 章节结构。

### 5.5 F5: validate.py 8 类校验

| # | 类别 | 检查内容 |
|---|------|---------|
| 1 | Path | doc 文件路径符合 type 的目录规则；source-system-analysis 按 analysis_kind 分路径 |
| 2 | Naming | 文件名符合 convention |
| 3 | Frontmatter Schema | universal 5 字段全在 + per-type 扩展字段全在 + status/type 是合法 enum |
| 4 | Frontmatter Format | timestamp ISO8601 UTC、release `"x.y"`、owner `agent/skill`、ID `CR-\d+` / `BUG-\d+`；code-review-report 的 `review_status` 必为 `pass` 或 `fail` |
| 5 | Cross-Reference | 路径字段指向真实文件 |
| 6 | Change Log Discipline | `## Pending Changes` 为空 + `## Change Log` 格式合法 |
| 7 | ID Uniqueness | CR-NNN / BUG-NNN 唯一 |
| 8 | Consistency with progress.md | doc `status` 和 progress.md `current_stage`/`sub_state` 兼容 |

#### 子命令

```bash
skills/doc-guardian/scripts/validate.py file <doc-path>
skills/doc-guardian/scripts/validate.py all
skills/doc-guardian/scripts/validate.py consistency
skills/doc-guardian/scripts/validate.py ids
```

### 5.6 F6: doc-guardian 物理结构

```
skills/doc-guardian/
├── SKILL.md                       主协议
├── references/
│   ├── directory-layout.md        F1 + source-system-analysis 路径表
│   ├── frontmatter-schema.md      F3 全文，含 source-system-analysis、code-review-report 增强
│   ├── change-log-format.md       Pending Changes / Change Log 严格格式
│   └── required-artifacts.md      P6 配套：scenario-aware 必备清单
└── scripts/
    ├── validate.py                F5 主校验
    └── changelog.py               promote / validate Pending Changes
```

### 5.7 Change Log 自动化机制（不变）

doc 内两个章节：`## Pending Changes`（AI 写）+ `## Change Log`（脚本管理）。

`scripts/changelog.py promote` 把 Pending Changes 移到 Change Log（按日期分组）。

`validate.py` 强制 `## Pending Changes` 为空。

`*-write` skill 标准流程：

```
1. 生成/修改 doc 主体
2. 在 ## Pending Changes 加 entry
3. 运行 changelog.py promote
4. 自评（调 validate.py）
5. 自修复
6. 提交给 *-review skill
```

---

## 6. AGENTS.md Template (Task 3)

### 6.1 完整 Draft（v0.3，全 skill 路径 + 术语规范）

```markdown
# AGENTS.md

<!-- 任何使用 dev-workflow-skills2 工作流的项目里，agent 第一步必读本文件 -->

## 1. Authority Hierarchy

规则冲突时按以下优先级（数字越小权威越高）：

1. `skills/workflow-protocol/SKILL.md` — 操作协议（状态机、must-call 规则）
2. `AGENTS.md` — 本文件（治理、约定）
3. `skills/doc-guardian/SKILL.md` — 文档合规
4. 当前 stage skill 的 `SKILL.md` — 任务级指令
5. 用户在当前对话中的指令 —— 在以上规则范围内有效，**不能突破硬约束**

## 2. Bootstrap Protocol

任何新会话/新任务起手按顺序：

1. （如果 `AGENTS.md` 通过 `@` 已自动加载，本步已完成）
2. 读 `skills/workflow-protocol/SKILL.md`
3. 跑 `skills/workflow-protocol/scripts/progress.py query` 读取当前 state
4. 从 state 判定：scenario (S1/S2/S3/S4)、`scenario_subtype` (S2-1/2/3/4)、`current_stage`、`sub_state`、`release`、`release_state`、`bug_flow.active`
5. 如果 `scenario` 未设 → invoke `scenario-dispatcher`；如果 `bug_flow.active=true` → invoke `bug-triage`
6. 找到当前 state 对应的 skill，读它的 `SKILL.md`
7. 开始干活

## 3. Skill Catalog (23 physical skills, 4 layers)

### Layer 1: Vertical Stage Skills (18 个)

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + supporting artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 architecture_delta）|
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests（测试代码）|
| `development-code-write` / `development-code-review` | 4 | Source Code + Code Review Report |
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective（项目级，每 release 增量加节）|

### Layer 2: Cross-cutting (2 个)

- `workflow-protocol` — 状态机、转换、progress 管理（`scripts/progress.py`，含 `release-start` / `release-close`）、评审循环计数、must-call 规则
- `doc-guardian` — 目录结构、命名、frontmatter、change log 规范、binary 校验（`scripts/validate.py`、`scripts/changelog.py`）

### Layer 3: Orchestration (2 个)

- `scenario-dispatcher` — 项目入口判定 S1/S2/S3/S4 + S2 子场景 (S2-1/2/3/4)；S4 仅 active release 期间允许
- `bug-triage` — bug 根因分类（SRS / Architecture / Development / PRD-异常），路由到对应 stage 的 Change Mode

### Layer 4: Meta (1 个)

- `workflow-evolution` — 消化 Stage 7 retrospective + PRD 根因异常输入

## 4. Project Conventions

- **语言**：英文用于 skill 名 / 文件路径 / frontmatter / 技术术语；中文用于描述和说明
- **Doc filenames**：lowercase + underscore + `.md`；CR/Bug 用 ID 大写
- **Timestamps**：一律 ISO8601 UTC
- **Release versions**：YAML 中必须加引号字符串 `release: "0.1"`
- **Release 串行**：同时只 1 个 active release
- **S4 policy**：仅在 active release 期间触发；post-close bug 留待下次 S2
- **Directory structure**：见 `skills/doc-guardian/references/directory-layout.md`
- **Frontmatter schema**：见 `skills/doc-guardian/references/frontmatter-schema.md`
- **Change Log**：通过 `skills/doc-guardian/scripts/changelog.py promote` 管理
- **Review iteration cap**：7 次；超过 → 升级人介入
- **Revise**：由 `*-write` skill 在 Change Mode 下完成（无独立 `*-revise` skill）
- **术语**：`review-passed` 是 AI review 输出；`approved` 仅用于人 gate 后的 doc status

## 5. State Files

项目根下脚本管理的文件（**禁止手工编辑**）：

- `progress.md`
- `progress-history.md`
- `.progress.lock`

配置文件：

- `AGENTS.md`
- `CLAUDE.md`（仅含 `@AGENTS.md`）

## 6. Forbidden Actions

- 手工编辑 `progress.md` —— 必须用 `skills/workflow-protocol/scripts/progress.py update`
- 直接编辑 Change Log 章节 —— 必须用 `skills/doc-guardian/scripts/changelog.py promote`
- doc 完成前不跑 `skills/doc-guardian/scripts/validate.py` —— 必须 exit 0 才能 declare done
- stage 推进不调 `skills/workflow-protocol/scripts/progress.py update --advance`
- 在 workflow-protocol 内部跑 unit/integration tests —— workflow-protocol 只读 `verification_status` 字段
- 在 `skills/doc-guardian/references/directory-layout.md` 定义之外的目录创建 doc 文件
- 从 doc 类 skill 修改 `src/` 或 `tests/`
- 启动新 release 不通过 `skills/workflow-protocol/scripts/progress.py release-start`
- 多 release 并发 —— 严格串行
- closed release 期间使用 S4 —— 必须先用 `release-start` 启动新 release（v0.3 F2）
- review skill 输出用 `approved` —— 必须用 `review-passed` / `issues-found`（v0.3 F4）

## 7. Recursion Notice

`dev-workflow-skills2` skill 集禁止作用于 `dev-workflow-skills2` 自身。

## 8. Workflow Specification Reference

本 skill 集实现 `docs/workflow/workflow_specification_claude.md`（skill 仓库）中定义的工作流。每个项目的 `progress.md` 的 `workflow_version` 字段记录其遵循的版本；当前版本是 `v0.3`（2026-05-05）。

## 9. Where to Find Things

| 我想知道... | 去哪里看 |
|------------|---------|
| 项目当前 state | `progress.md` 或 `skills/workflow-protocol/scripts/progress.py query` |
| 历史所有动作 | `progress-history.md` |
| Workflow spec 定义 | `docs/workflow/workflow_specification_claude.md` |
| Doc 目录布局 | `skills/doc-guardian/references/directory-layout.md` |
| 各 skill 干什么 | 上面 Section 3 + 各 skill 的 `SKILL.md` |
| 允许 / 禁止做什么 | 上面 Section 6 + 各 skill 的 "Forbidden" 章节 |
| v1 当年踩过什么坑 | `docs/research/dev_workflow_skills_v1_design_claude.md` |
| Release 当前状态 | `progress.md` `release` + `release_state` 字段 |
| Pending bugs (post-close) | `progress.md` `unresolved_bugs` 字段 |

## 10. Scenarios Quick Reference

| Code | Name | 含义 | 子场景 |
|------|------|------|--------|
| S1 | New Product | 从 0 打造一个新项目 | — |
| S2 | Feature Evolution | 在已规范化的项目上新增需求（每次新需求触发新 release）| S2-1/2/3/4 |
| S3 | Product Reconstruction | 把已存在的外部项目按本规范重建为新项目 | — |
| S4 | Bug Fix | 修复已规范化项目中的 bug；**仅 active release 期间** | — |

S2 子场景：
- S2-1: PRD 变更引入新功能 → PRD Inception 入口
- S2-2: PRD 不变，仅新增 SRS → SRS Specification 入口
- S2-3: PRD 不变，仅修改 SRS → SRS Specification (Change Mode) 入口
- S2-4: PRD 重构级变更 → 转 S3
```

---

## 7. Pending Work

### 7.1 Task 5: 23 个 Skill 的 SKILL.md 骨架

按 3 批展开：

**批 1（关键基础设施，2 个）**：
- `workflow-protocol` 完整 SKILL.md
- `doc-guardian` 完整 SKILL.md

**批 2（Orchestration + Meta，3 个）**：
- `scenario-dispatcher` — 4 场景判定 + S2 子场景路由 + S4 active-release 校验
- `bug-triage` — 4 类根因分类
- `workflow-evolution`

**批 3（Vertical 18 个）**：
- 7 logical Stage 的 write/review pair（Stage 4 拆 6 个）

### 7.2 Task 6: Implementation

```
dev-workflow-skills2/
├── AGENTS.md.template
├── CLAUDE.md.template
├── skills/
│   ├── workflow-protocol/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/progress.py        # 含 init/update/query/recover/release-close/release-start
│   ├── doc-guardian/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/{validate.py, changelog.py}
│   ├── prd-write/SKILL.md
│   ├── prd-review/SKILL.md
│   ├── ...
│   ├── development-code-write/SKILL.md
│   ├── development-code-review/SKILL.md
│   └── ...（23 个 skill 全部）
├── .claude/
│   └── skills/ → ../skills/
├── .agents/
│   └── skills/ → ../skills/
└── docs/
    ├── workflow/
    ├── research/
    ├── design/
    └── review/
```

---

## 8. Decision Log

### 2026-05-05 (v0.1)

[v0.1 决策清单 — 见 v0.1 doc Decision Log]

### 2026-05-05 (v0.2 - reviewer feedback v0.1 采纳)

- ✅ F1 skill count 修正（实际 23）
- ✅ F2 required-artifacts.md scenario-aware
- ✅ F3 (B) 命令统一全 skill 路径
- ✅ F4 `approved` 适用扩到 CR
- ✅ F5 S2 子场景路由表
- ✅ F6 (a) 加 development-code-review skill（推翻原决策）
- ✅ F7 revise = `*-write` Change Mode
- ✅ F8 Release Lifecycle Rule（严格串行）
- ✅ F9 删 Claude-local memory path

### 2026-05-05 (v0.3 - reviewer feedback v0.2 采纳)

- ✅ **F1**：workflow spec v0.3 加 reconciliation：logical vs physical Stage Skill
- ✅ **F2 (B)**：S4 仅 active release 期间允许；post-close bug 留待下次 S2
- ✅ **F3**：加 `source-system-analysis` doc type + `analysis_kind` enum（6 种）
- ✅ **F4**：术语规范，review skill 输出绝不用 `approved`
- ✅ **F5**：progress.md 示例修正（release `0.3`、previous `["0.1","0.2"]`、sub_state `in-review`）
- ✅ **F6**：加 `release-start` 命令 + serial 校验
- ✅ **F7**：`code-review-report` 加 `review_status` / `blocking_findings_count` / `max_severity`
- ✅ **F8**：全文 script 路径 normalize

---

**End of Proposal v0.3**
