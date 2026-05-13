# Skill Set Design Proposal (Skill 集合设计方案)

**Version**: v0.5
**Date**: 2026-05-06
**Status**: Draft — 架构层与详细设计层闭环；待 Task 5 (skill SKILL.md drafts) 与 Task 6 (implementation)
**Workflow Reference**: `docs/workflow/workflow_specification_claude.md` (v0.5)
**Predecessors**: `v0.1` / `v0.2` / `v0.3` / `v0.4`
**Review Responses**: `docs/review/reviewer_feedback_response_v0.{1,2,3,4}.md`

---

## 0. v0.4 → v0.5 主要变化

| 变化点 | 原因 | 影响范围 |
|--------|------|---------|
| 加 `bug-start` / `bug-close` 子命令 + 精确 mutation | F1 | Section 4.4 |
| `incident-resolve` 3 个 action 精确 mutation | F2 | Section 4.4 |
| progress.md 加 `project_state` + `release_close_reason` 字段 | F2 | Section 4.2 |
| 全文 script path shorthand 清理 | F3 | 全文 |
| workflow spec 残留 v0.3 引用 + workflow-evolution 待定标记 | F4 | workflow spec v0.5 |

---

## 1. Executive Summary

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合。本方案汇总 Task 1-4 的所有架构层与详细设计层决策，作为 Task 5（23 个 skill 骨架设计）和 Task 6（实现）的依据。

### 1.1 架构概览

- **23 个 physical skill**（对应 7 个 logical Stage Skill + 5 个 Cross-cutting/Orchestration/Meta），分 4 层
- **7 阶段主流程** + Bug Flow + 4 场景（S1-S4，含 S2 4 个子场景）
- **Release 严格串行**：同时只 1 个 active release，按 `MAJOR.MINOR` 整数对递增
- **S4 仅在 active release 期间允许**；post-close bug 由 bug-triage post-close mode 收集，等下次 S2
- **Bug Flow 完整闭环**（v0.5 F1）：`bug-start` 进入 → 对应 stage Change Mode 修复 → `bug-close` 退出
- **PRD 根因异常**走 workflow-incident-analysis 特殊 stage，由 workflow-evolution skill 消化；`incident-resolve` 支持 continue/abort/reconstruct 3 终态（v0.5 F2）
- **Foreman binary 校验**：doc-guardian 配 `skills/doc-guardian/scripts/validate.py`，exit code 决定 block/pass
- **评审循环**：write → review → revise，cap = 7 次，超限升级人介入；revise 由 `*-write` 在 Change Mode 下完成
- **vendor-neutral**：`CLAUDE.md = @AGENTS.md`，AGENTS.md 治理层 + workflow-protocol 操作层；命令统一 `skills/<name>/scripts/<x>.py` 全路径

### 1.2 项目设计哲学

- 用户偏好：先框架后细节；记忆有限所以阶段名要少要清晰；避免文档漂移所以小需求也强制走全流程
- 工作流自身演进：Stage 7 复盘 + PRD 根因异常 两条路径汇入元改进
- 递归悖论意识：本 skill 集**不应作用于 dev-workflow-skills2 自身**，仅用于其他项目
- 代码质量双轨：代码同时由 review skill 评审 + 测试验证

### 1.3 Logical vs Physical Skill

Workflow spec 的 "One Stage Skill" 是 **logical concept**：每个 Stage 对应一个 logical Stage Skill。

具体物理实现使用 **Foreman 拆分**：每个 logical Stage Skill 由一个或多个 physical skill 组成（如 `*-write` / `*-review` 配对）。

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
| Task 1: 架构层决策 | ✅ Done | D1-D5 / Q1-Q3 / Logical vs Physical |
| Task 2: workflow-protocol 设计 | ✅ Done（v0.5 加 bug-start/close、incident-resolve mutation）| 5 项责任、progress 格式、scripts、并发模型、P6 矩阵、release lifecycle、Bug Flow 闭环 |
| Task 3: AGENTS.md template | 🟡 Draft v0.5 | 10-section template |
| Task 4: doc-guardian 设计 | ✅ Done | F1-F6（F4 跳过）|
| Task 5: 23 个 skill 骨架 | ⏳ Pending | 按 3 批展开 |
| Task 6: 实现 | ⏳ Pending | 写实际 SKILL.md / scripts / AGENTS.md / CLAUDE.md |

---

## 2. Workflow Reference

完整 workflow spec 在 `docs/workflow/workflow_specification_claude.md` (v0.5)。

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
| S2 | Feature Evolution | 主流程全程（含 4 子场景路由）| 当前项目 PRD/SRS/Architecture + `unresolved_bugs` 列表 |
| S3 | Product Reconstruction | 主流程全程 | 源系统 PRD + 源系统 SRS（Stage 1/2 强制要求源系统分析）|
| S4 | Bug Fix | Bug Flow | Bug Report；仅 active release 期间允许 |

### 2.3 Bug Flow 4 类根因路由

| 根因 | 路径 |
|------|------|
| `srs` | CR Document → SRS Update → Architecture Update? → Development → Testing → bug-close |
| `architecture` | Architecture Update（仅版本历史）→ Development → Testing → bug-close |
| `development` | Development Update → Testing → bug-close |
| `prd-exception` | 项目暂停，`workflow_incident_active=true` → workflow-evolution skill → 用户决策（continue / abort / reconstruct）|

### 2.4 关键规则

- 变更记录：仅 SRS 变更需 CR Document
- Skill 复用：同一 logical Skill 通过 Full Mode / Change Mode 应对 4 个场景
- 元演进：Stage 7 + PRD 根因异常 都汇入 workflow-evolution

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

### 3.2 Vertical Skill 完整清单（18 个）

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + Supporting Artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan；release-start 时合并 unresolved_bugs |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 architecture_delta）|
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests |
| `development-code-write` / `development-code-review` | 4 | Source Code |
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report；retest pass 后调 `bug-close` |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective |

### 3.3 架构层决策（已闭环）

| ID | 决策点 | 选定 |
|----|--------|------|
| 评审结构 | Skill 拆分模式 | Foreman 模式 |
| 评审上限 | 评审循环最多次数 | 7 次 |
| Stage 4 拆分 | Development 内部分组 | Option I：规划设计 / 测试 / 代码 三组 |
| 代码评审 | Source Code 是否走 review | 是 |
| D1 | doc 校验机制 | Foreman binary：exit 0/1 |
| D2 | CLAUDE.md 形态 | foreman 模式 |
| D3 | SessionStart Hook | 不要 |
| D4 | vendor-neutral skill 结构 | 要 |
| D5 | Risk-based review | 不要 v1 |
| Q1 | 评审超 7 次 | 升级人介入 |
| Q2 | cr-guardian | 合并进 doc-guardian |
| Q3 | project-memory-manager | 不独立 |
| 脚本路径 | 命令路径 | 全 skill 路径 |
| Release 并发 | 是否可并发 | 严格串行 |
| S4 policy | closed release 时 S4 如何 | active-release-only；post-close 走 bug-intake |
| Logical vs Physical | "One Stage Skill" 与 23 skill 关系 | "One" 是 logical，可对应多个 physical |
| Version grammar | release 字符串格式 | MAJOR.MINOR 整数对 |
| Bug intake owner | post-close bug 谁创建 | bug-triage post-close mode + `progress.py bug-intake` |
| PRD exception state | PRD 根因异常如何记 | `bug_flow.root_cause: prd-exception` + `workflow_incident_active: true` |
| **Bug Flow 闭环** (v0.5 F1) | active Bug Flow 怎么进/退 | `progress.py bug-start` 进入 + `bug-close` 退出 |
| **Incident 终态字段** (v0.5 F2) | incident-resolve abort/reconstruct 后状态 | progress.md 加 `project_state` + `release_close_reason` 字段；3 个 action 各有精确 mutation |

### 3.4 关键设计原则

- 检查它属于哪一层
- vertical skill 必须支持 Full Mode + Change Mode
- 任何 doc 类产物完成前必须调 `skills/doc-guardian/scripts/validate.py`
- 任何阶段转换必须由 workflow-protocol 驱动
- 评审是流程控制（write → review → revise → loop），不是 stage 内部 sub-process
- Revise 由 `*-write` skill 在 Change Mode 下完成
- `*-review` skill 输出术语：`review-passed` / `issues-found`；绝不用 `approved`
- 不要重复 doc 校验逻辑
- skill 命名用 verb-noun
- 单个 SKILL.md 控制在合理篇幅

---

## 4. workflow-protocol Skill Design (Task 2)

### 4.1 责任清单（5 项）

| # | 责任 |
|---|------|
| 1 | 状态机定义（Hybrid: YAML schema + 转移表 + prose）|
| 2 | 转换规则（state X → Y 合法性）|
| 3 | Hook 闭环 / "MUST call X" 硬约束 |
| 4 | progress.md / progress-history.md 管理（含 `skills/workflow-protocol/scripts/progress.py`）|
| 5 | 评审循环计数 + 超 7 升级 |

剥离责任：Bootstrap → AGENTS.md；Scenario 路由 → scenario-dispatcher；Bug 流程路由 → bug-triage。

### 4.2 progress.md Schema（v0.5 加 project_state / release_close_reason）

```yaml
---
project_name: my-product
workflow_version: v0.5
project_state: active              # active / aborted / reconstructing（v0.5 F2 新加）
release: "0.3"
release_state: active              # active / closed
release_close_reason: null         # null / "stage-7-completed" / "incident-abort" / "incident-reconstruct"（v0.5 F2 新加）
previous_releases:
  - "0.1"
  - "0.2"
scenario: S2
scenario_subtype: S2-1
current_stage: srs-specification

sub_state: in-review
review_iteration: 2

development_state:
  total_tasks: 5
  task_states:
    T1: verified
    T2: test-writing
    T3: code-review
    T4: test-done
    T5: planning-done

artifacts:
  prd: docs/prd/prd.md
  architecture: docs/architecture/architecture.md
  srs: docs/release0.3/srs/srs.md
  acceptance_plan: docs/release0.3/srs/acceptance_plan.md
  integration_plan: docs/release0.3/srs/integration_plan.md
  architecture_delta: docs/release0.3/architecture_delta.md

bug_flow:
  active: false
  bug_report_path: null
  root_cause: null               # null / srs / architecture / development / prd-exception

workflow_incident_active: false
incident_report_path: null

unresolved_bugs:
  - docs/bug/BUG-005.md
  - docs/bug/BUG-006.md

created: 2026-05-04T08:00:00Z
updated: 2026-05-06T10:00:00Z
---

# Current Stage Summary

[当前 stage / sub_state / 关键 doc 路径 / next action]

# Recent Activity (auto-derived from progress-history.md)

## 2026-05-06T10:00:00Z — srs-review iteration 2 — 1 issue found
## 2026-05-06T08:30:00Z — srs-review iteration 1 — 3 issues found
## 2026-05-06T08:00:00Z — srs-write completed
```

### 4.3 progress-history.md Schema

append-only，时间顺序（旧顶新底），每条 entry：

```markdown
## {ISO8601 UTC timestamp} — {action_type} — {one_line_result}
- agent: {agent_id}
- task: {task_id, 仅 Stage 4}
- result: {结构化结果}
- next: {next_action}
```

### 4.4 scripts/progress.py 接口（v0.5 原始接口；v0.6 patch 后 12 个子命令）

> **v0.6 patch (2026-05-07)**：Task 6 Phase 1 将 `progress.py` 子命令数从 11 扩展为 12，新增 `bug-rework --bug <BUG-NNN.md>`，用于 active Bug Flow retest fail/partial 后回到同一 root-cause stage。精确前置与 mutation 以 `skills/workflow-protocol/references/command-reference.md` §9 和 `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 为准。

物理路径：`skills/workflow-protocol/scripts/progress.py`

| Subcommand | 用途 |
|-----------|------|
| `init` | 新项目首次初始化 progress.md |
| `update` | 应用一次状态转换（原子 + 回退）|
| `query` | 读取当前 state（只读）|
| `recover` | 从 progress-history.md 重建 progress.md |
| `release-close` | Stage 7 完成时 close 当前 release |
| `release-start --version <x.y> --scenario <S2-1\|S2-2\|S2-3>` | 启动新 active release |
| `bug-intake --bug <path>` | post-close 期间记录 bug |
| **`bug-start --bug <path> --root-cause <enum>`** (v0.5 F1) | active Bug Flow 入口 |
| `bug-rework --bug <BUG-NNN.md>` (v0.6 patch) | active Bug Flow retest fail/partial 后回同一 root-cause stage |
| **`bug-close`** (v0.5 F1) | active Bug Flow 出口（retest pass 后）|
| `incident-start --report <path>` | bug-triage 判 prd-exception 后调用 |
| `incident-resolve --action <continue\|abort\|reconstruct>` | 退出 incident state |

#### 4.4.1 `release-close` mutation

```yaml
# 前置：release_state==active && current_stage==project-retrospective && sub_state==review-passed
release_state: active → closed
release_close_reason: null → "stage-7-completed"
previous_releases: [...] → [..., <current release>]
```

#### 4.4.2 `release-start` mutation

```yaml
# 前置：release_state==closed; <x.y> 解析合法且严格大于所有 previous_releases; scenario in {S2-1,S2-2,S2-3}
release: <previous> → <x.y>
release_state: closed → active
release_close_reason: <previous_reason> → null
scenario: → S2
scenario_subtype: → <S2-1|S2-2|S2-3>
current_stage: → 按 scenario（S2-1=prd-inception；S2-2/S2-3=srs-specification）
sub_state: → write
review_iteration: → 0
artifacts.{srs,acceptance_plan,integration_plan,architecture_delta}: → 新 release 路径
artifacts.prd / artifacts.architecture: 不变
unresolved_bugs: [...] → []  # 全部消费
# 同时为每个原 unresolved_bug 在对应 BUG-NNN.md frontmatter 加 consumed_in_release: <x.y>
```

#### 4.4.3 `bug-intake` mutation

```yaml
# 前置：release_state==closed; <bug-report-path> 文件存在 + frontmatter target_release==null
unresolved_bugs: [...] → [..., <bug-report-path>]
```

#### 4.4.4 `bug-start` mutation（v0.5 F1）

```yaml
# 前置：bug_flow.active==false; current_stage==testing; testing 阶段刚发现 bug
bug_flow.active: false → true
bug_flow.bug_report_path: null → <path>
bug_flow.root_cause: null → <srs|architecture|development>  # prd-exception 走 incident-start
current_stage: testing → <root_cause stage>  # 进对应 stage Change Mode
sub_state: review-passed → write    # Change Mode 重走 write 循环
review_iteration: <N> → 0
```

#### 4.4.5 `bug-close` mutation（v0.5 F1）

```yaml
# 前置：bug_flow.active==true; testing 重测通过（test-report verification_status==pass）
bug_flow.active: true → false
bug_flow.bug_report_path: <path> → null
bug_flow.root_cause: <enum> → null
current_stage: testing → testing  # 保持，进入正常 Stage 5 done 判定
```

bug-close 后 workflow-protocol 评估 Stage 5 done 条件，pass 则推进 Stage 6（正常路径）。

#### 4.4.6 `incident-start` mutation

```yaml
# 前置：bug_flow.active==true && bug_flow.root_cause==prd-exception
workflow_incident_active: false → true
incident_report_path: null → <path>
current_stage: <previous> → workflow-incident-analysis
# bug_flow.active 保留（incident 期间）
```

#### 4.4.7 `incident-resolve` mutation（v0.5 F2，3 个 action）

**`--action continue`**：

```yaml
# 前置：workflow_incident_active==true; 用户决定 workflow 改进后继续
workflow_incident_active: true → false
incident_report_path: <path> → null
current_stage: workflow-incident-analysis → testing  # 回到 incident 起点 Stage 5 retest
# bug_flow 视用户决策保留或清空（继续修就保留，转走就清空）
```

**`--action abort`**：

```yaml
# 前置：workflow_incident_active==true; 用户判定 project 不可继续
workflow_incident_active: true → false
project_state: active → aborted
release_state: active → closed
release_close_reason: null → "incident-abort"
current_stage: workflow-incident-analysis → null  # 终态
incident_report_path: <path> → null
```

abort 后 progress.md 进入终态，禁止任何后续 update（除 query / recover）。

**`--action reconstruct`**：

```yaml
# 前置：workflow_incident_active==true; 用户判定需要从外部源系统重构（即转 S3）
workflow_incident_active: true → false
project_state: active → reconstructing
release_state: active → closed
release_close_reason: null → "incident-reconstruct"
current_stage: workflow-incident-analysis → null  # 终态
incident_report_path: <path> → null
```

reconstruct 后该 project 进入终态。用户启动新 S3 project（独立目录、独立 progress.md），可在新 PRD 中引用本 project 作为 source system。

#### 4.4.8 `update` 原子流程（不变）

1. 计算 new_progress + new_history_entry
2. flock on `.progress.lock`
3. 备份两个文件
4. 校验状态机转换合法性
5. 写入：append progress-history.md → overwrite progress.md
6. 一致性校验
7. 失败 → rollback；成功 → 删备份 + 解锁

### 4.5 Scenario Routing

#### 4.5.1 S2 子场景路由表

| 子场景 | 适用条件 | 入口 Stage | progress 字段 |
|--------|---------|-----------|---------------|
| S2-1 | PRD 变更引入新功能 | PRD Inception (Change Mode) | `scenario_subtype: S2-1` |
| S2-2 | PRD 不变，仅新增 SRS | SRS Specification (Full Mode for new) | `scenario_subtype: S2-2` |
| S2-3 | PRD 不变，仅修改 SRS | SRS Specification (Change Mode) | `scenario_subtype: S2-3` |
| S2-4 | PRD 重构级变更 | 转 S3（新 project）| 不进入 S2 流程 |

#### 4.5.2 详细路由

```
项目根有 progress.md？
  否 → S1 (新项目) 或 S3 (重构)，由用户/scenario-dispatcher 选择
  是 → progress.md project_state == active？
        否（aborted/reconstructing）→ project 已终态，禁止操作（query/recover 除外）
        是 → release_state == active？
              是 → 当前 release 进行中
                    ├ Stage 5 测试发现 bug → bug-triage active mode → progress.py bug-start
                    ├ Bug Flow 修复完成 + retest pass → progress.py bug-close
                    ├ 用户报新 bug（非 testing 触发）→ bug-triage active mode
                    ├ workflow_incident_active==true → workflow-evolution skill
                    └ 继续当前 stage → 按 current_stage 路由
              否（closed）→ 当前 release 已 close
                    ├ S2 启动新 release → progress.py release-start
                    ├ S3 转新项目（如果整体重构）
                    ├ 用户报 bug → bug-triage post-close mode → progress.py bug-intake
                    └ S4 不可用 ✗
```

### 4.6 并发模型

- 任何 agent 通过 `skills/workflow-protocol/scripts/progress.py update`
- 锁内部处理并发
- Stage 4 子 agent 接口（Option B）：调一律是 `update`

### 4.7 两层粒度

| 文件 | 粒度 |
|------|------|
| progress.md | 任务级 |
| progress-history.md | 子任务级 + 任务级 |

### 4.8 P6 Stage 完成判定矩阵

| 维度 | 检查方式 |
|------|---------|
| A. 必需 artifacts 存在 | 文件存在；S3 场景 Stage 1/2 强制源系统分析 |
| B. doc-guardian 校验通过 | `validate.py` exit 0 |
| C. Review 通过 | `*-review` skill 返回 `review-passed` |
| D. 人确认（仅 PRD/SRS/Architecture/CR）| history 有 "human-confirmed" 条目；frontmatter `status: approved` |
| E. 内部验证（Stage 4/5/6）| `verification_status: pass` |

### 4.9 7 个 Stage 的判定矩阵

| Stage | A. Required | B. Guardian | C. Review | D. Human | E. Verification |
|-------|------|----|----|----|----|
| 1 PRD | PRD（S3 含源系统 PRD/Feature Matrix）| ✓ | review-passed | approved | — |
| 2 SRS | SRS + Acceptance Plan + Integration Plan + S3 4 类源系统分析 | ✓ | review-passed | approved | — |
| 3 Architecture | Architecture Document + delta? | ✓ | review-passed | approved | — |
| 4 Development | 见 4.10 | | | | |
| 5 Testing | Test Prep + Procedure + Report | ✓ | review-passed | — | Test Report `verification_status: pass`（fail → bug-start）|
| 6 Delivery | Deployment + Manual + Installation Result | ✓ | review-passed | — | Installation 执行成功 |
| 7 Retrospective | Issue Report + Improvement Proposals | ✓ | review-passed | — | — |

### 4.10 Stage 4 特殊判定

```
Stage 4 done ⇔ all task_states[Tn] == "verified"
```

每 task 子状态：

| 子状态 | 满足条件 |
|--------|---------|
| `planning-done` | Detailed Design (Tn) doc-guardian + review-passed |
| `test-writing` → `test-review` → `test-revising` → `test-done` | Tests doc-guardian + review-passed |
| `code-writing` → `code-review` → `code-revising` → `code-review-passed` | code-review-report `review_status: pass` 且 `blocking_findings_count: 0` |
| `verifying` → `verified` | Local Verification Result `verification_status: pass` |

### 4.11 Bug Flow 完整闭环（v0.5 F1）

Stage 5 E 失败 → 进入 Bug Flow：

1. testing-write 写 Bug Report
2. invoke bug-triage active mode → 输出 `root_cause`
3. **若 root_cause ∈ {srs, architecture, development}**：
   - 调 `progress.py bug-start --bug <path> --root-cause <enum>`
   - workflow-protocol 切 `current_stage` 到对应 stage（Change Mode）
   - 该 stage 重新过 A/B/C/D/E
   - 完成后回到 Stage 5 重测
   - retest pass → 调 `progress.py bug-close` → 推进 Stage 6
4. **若 root_cause == prd-exception**：
   - 调 `progress.py incident-start --report <path>`
   - workflow-evolution skill 接管
   - 用户决策后调 `progress.py incident-resolve --action <continue|abort|reconstruct>`

### 4.12 Release Lifecycle Rule

| 规则 | 内容 |
|------|------|
| 同时只 1 个 active release | progress.md `release_state` 字段约束 |
| Release 创建 | `progress.py release-start` |
| Release 编号 | MAJOR.MINOR 整数对 |
| Release close 条件 | Stage 7 retrospective 完成且 review-passed；mutation 见 4.4.1 |
| 历史 release 只读 | release close 后，对应 `docs/release<x.y>/` 目录变只读 |
| S4 policy | 仅 active release 期间触发 |
| Post-close bug 处理 | bug-triage post-close mode + `progress.py bug-intake` |
| S2 → release 映射 | S2-1/2/3 全部触发新 release；S2-4 转 S3 |

### 4.13 Revise Action Ownership

Revise 由 `*-write` skill 在 Change Mode 下完成。状态转换：

```
sub_state: in-review (review skill 输出 "issues-found")
  ↓ workflow-protocol
sub_state: revising  +  review_iteration += 1
  ↓ invoke *-write skill in Change Mode
sub_state: in-review (write skill 完成 revise)
  ↓ invoke *-review skill
sub_state: revising 或 review-passed
```

### 4.14 Release Version Grammar

`<MAJOR>.<MINOR>` 两个非负整数（regex `^(\d+)\.(\d+)$`）。

按数字对比较：`"0.10" > "0.2"` 因为 `(0, 10) > (0, 2)`。

`progress.py release-start` 校验新 version 严格大于 `previous_releases` 中所有版本。

### 4.15 关键约定

- **Verification artifact** 必含 `verification_status: pass | fail | partial`
- **Code review report** 必含 `review_status: pass | fail` + `blocking_findings_count: int` + `max_severity: low|medium|high|critical`
- **Required vs Optional artifacts** 由 doc-guardian 集中声明（scenario-aware）
- **Stage advance** 显式：stage skill 调 `skills/workflow-protocol/scripts/progress.py update --advance`
- **Review skill 输出术语**：`review-passed` / `issues-found`
- **Release version**：MAJOR.MINOR 整数对
- **Bug Flow 闭环**（v0.5）：`bug-start` → 修复 → `bug-close`
- **Project terminal state**（v0.5）：`project_state: aborted | reconstructing` 后禁止 update

---

## 5. doc-guardian Skill Design (Task 4)

### 5.1 F1: 完整目录结构

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
│   │       ├── feature_matrix.md
│   │       └── source_product_prd_analysis.md
│   │
│   ├── architecture/
│   │   └── architecture.md
│   │
│   ├── release0.1/
│   │   ├── srs/
│   │   │   ├── srs.md
│   │   │   ├── acceptance_plan.md
│   │   │   ├── integration_plan.md
│   │   │   ├── source_product_srs_analysis.md
│   │   │   ├── source_module_analysis.md
│   │   │   ├── reuse_replace_capability.md
│   │   │   └── technical_debt_analysis.md
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
│   ├── bug/
│   │   ├── BUG-001.md
│   │   └── BUG-002.md
│   │
│   └── incident/                         # PRD 异常 incident report
│       └── INCIDENT-001.md
│
├── src/
└── tests/
```

### 5.2 F2: 命名 Convention

- Doc 文件：lowercase + underscore + `.md`
- CR / Bug / Incident：ID 大写 `CR-001.md` / `BUG-005.md` / `INCIDENT-001.md`
- 不带 `_claude` 后缀
- Task 子目录：`T1/`、`T2/`
- Release 目录：`release<x.y>/`

### 5.3 F3: Frontmatter Schema

#### Universal

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

#### Status 状态机

| 状态 | 含义 | 适用 |
|------|------|------|
| `draft` | 写作中 | 全部 doc |
| `in-review` | review skill 评审中 | 全部 doc |
| `revising` | 修订中（write Change Mode）| 全部 doc |
| `review-passed` | AI review 通过（最终态：非 gated）| 全部 doc |
| `approved` | 人确认通过（最终态）| PRD / SRS / Architecture / CR |

#### Per-Type Extensions

| Type | 路径 | 扩展字段 |
|------|------|---------|
| `prd` | `docs/prd/prd.md` | 无 |
| `architecture` | `docs/architecture/architecture.md` | 无 |
| `retrospective` | `docs/retrospective/retrospective.md` | 无 |
| `srs` | `docs/release<x.y>/srs/srs.md` | `release` |
| `acceptance-plan` | `docs/release<x.y>/srs/acceptance_plan.md` | `release`, `related_srs` |
| `integration-plan` | `docs/release<x.y>/srs/integration_plan.md` | `release` |
| `architecture-delta` | `docs/release<x.y>/architecture_delta.md` | `release`, `parent_architecture` |
| `development-plan` | `docs/release<x.y>/development/plan.md` | `release` |
| `task-breakdown` | `docs/release<x.y>/development/breakdown.md` | `release`, `total_tasks` |
| `detailed-design` | `docs/release<x.y>/development/tasks/Tn/detailed_design.md` | `release`, `task_id` |
| `code-review-report` | `docs/release<x.y>/development/tasks/Tn/code_review_report.md` | `release`, `task_id`, `findings_count`, `severity_distribution`, `review_status: pass\|fail`, `blocking_findings_count: int`, `max_severity: low\|medium\|high\|critical` |
| `verification-result` | `docs/release<x.y>/development/tasks/Tn/verification_result.md` | `release`, `task_id`, `verification_status` |
| `test-preparation` | `docs/release<x.y>/testing/preparation.md` | `release` |
| `test-procedure` | `docs/release<x.y>/testing/procedure.md` | `release` |
| `test-report` | `docs/release<x.y>/testing/report.md` | `release`, `verification_status`, `total_test_cases`, `passed`, `failed` |
| `deployment-doc` | `docs/release<x.y>/delivery/deployment.md` | `release` |
| `operation-manual` | `docs/release<x.y>/delivery/operation_manual.md` | `release` |
| `installation-result` | `docs/release<x.y>/delivery/installation_result.md` | `release`, `verification_status` |
| `cr` | `docs/cr/CR-NNN.md` | `cr_id`, `target_release`, `affected_doc` |
| `bug-report` | `docs/bug/BUG-NNN.md` | `bug_id`, `found_in_release`, `target_release` (可空), `root_cause` (可空), `consumed_in_release` (可空) |
| `workflow-incident` | `docs/incident/INCIDENT-NNN.md` | `incident_id`, `triggered_by_bug`, `triggered_in_release`, `resolution_action` (continue / abort / reconstruct，初始 null) |
| `source-system-analysis` | 见专表 | `release` (可空), `analysis_kind`, `source_system_name` |

#### `source-system-analysis` 详细 schema

| `analysis_kind` 值 | 路径 | 适用 release | 说明 |
|---------------------|------|-------------|------|
| `prd-level` | `docs/prd/supporting/source_product_prd_analysis.md` | null | 源系统 PRD 分析 |
| `feature-matrix` | `docs/prd/supporting/feature_matrix.md` | null | 功能矩阵 |
| `srs-level` | `docs/release<x.y>/srs/source_product_srs_analysis.md` | `<release>` | 源系统 SRS 分析 |
| `module-level` | `docs/release<x.y>/srs/source_module_analysis.md` | `<release>` | 源 Module 分析 |
| `reuse-replace` | `docs/release<x.y>/srs/reuse_replace_capability.md` | `<release>` | 复用 vs 替换 |
| `technical-debt` | `docs/release<x.y>/srs/technical_debt_analysis.md` | `<release>` | 技术债（推荐）|

S3 场景：Stage 1 必备 prd-level + feature-matrix；Stage 2 必备 srs-level + module-level + reuse-replace。

### 5.4 F4: 必需章节 — Skipped

doc body 章节由各 skill pair 协调。doc-guardian 不强制 body 章节。

### 5.5 F5: validate.py 8 类校验

| # | 类别 | 检查内容 |
|---|------|---------|
| 1 | Path | doc 文件路径符合 type 规则；source-system-analysis 按 analysis_kind；workflow-incident 在 `docs/incident/` |
| 2 | Naming | 文件名符合 convention |
| 3 | Frontmatter Schema | universal 5 字段 + per-type 扩展字段 + status/type 合法 enum |
| 4 | Frontmatter Format | timestamp ISO8601 UTC；release MAJOR.MINOR；owner `agent/skill`；ID 格式；code-review-report `review_status` ∈ {pass, fail} |
| 5 | Cross-Reference | 路径字段指向真实文件 |
| 6 | Change Log Discipline | `## Pending Changes` 为空 + `## Change Log` 格式合法 |
| 7 | ID Uniqueness | CR-NNN / BUG-NNN / INCIDENT-NNN 各自唯一 |
| 8 | Consistency with progress.md | doc `status` 和 progress.md `current_stage`/`sub_state` 兼容 |

子命令：

```bash
skills/doc-guardian/scripts/validate.py file <doc-path>
skills/doc-guardian/scripts/validate.py all
skills/doc-guardian/scripts/validate.py consistency
skills/doc-guardian/scripts/validate.py ids
```

### 5.6 F6: doc-guardian 物理结构

```
skills/doc-guardian/
├── SKILL.md
├── references/
│   ├── directory-layout.md
│   ├── frontmatter-schema.md
│   ├── change-log-format.md
│   └── required-artifacts.md      # scenario-aware
└── scripts/
    ├── validate.py
    └── changelog.py
```

### 5.7 Change Log 自动化机制

doc 内两章节（`## Pending Changes` + `## Change Log`）+ `skills/doc-guardian/scripts/changelog.py promote`：把 Pending 移到 Change Log（按日期分组）。`skills/doc-guardian/scripts/validate.py` 强制 `## Pending Changes` 为空。

`*-write` skill 4 步：1) 修改 doc → 2) 加 Pending Changes → 3) 跑 `skills/doc-guardian/scripts/changelog.py promote` → 4) 跑 `skills/doc-guardian/scripts/validate.py` → 5) 自修 → 6) 提交 review。

---

## 6. AGENTS.md Template (Task 3)

### 6.1 完整 Draft（v0.5）

```markdown
# AGENTS.md

<!-- 任何使用 dev-workflow-skills2 工作流的项目里，agent 第一步必读本文件 -->

## 1. Authority Hierarchy

规则冲突时按以下优先级（数字越小权威越高）：

1. `skills/workflow-protocol/SKILL.md` — 操作协议
2. `AGENTS.md` — 本文件（治理、约定）
3. `skills/doc-guardian/SKILL.md` — 文档合规
4. 当前 stage skill 的 `SKILL.md`
5. 用户在当前对话中的指令 —— 在以上规则范围内有效

## 2. Bootstrap Protocol

任何新会话/新任务起手按顺序：

1. （如果 `AGENTS.md` 通过 `@` 已自动加载，本步已完成）
2. 读 `skills/workflow-protocol/SKILL.md`
3. 跑 `skills/workflow-protocol/scripts/progress.py query` 读取当前 state
4. 从 state 判定：`project_state` / `release_state` / scenario / scenario_subtype / current_stage / sub_state / release / bug_flow / workflow_incident_active
5. 若 `project_state ∈ {aborted, reconstructing}` → 拒绝操作（query/recover 除外）
   否则若 `workflow_incident_active=true` → invoke `workflow-evolution`
   否则若 `bug_flow.active=true` → invoke `bug-triage`
   否则若 `scenario` 未设 → invoke `scenario-dispatcher`
6. 找到当前 state 对应的 skill，读它的 `SKILL.md`
7. 开始干活

## 3. Skill Catalog (23 physical skills, 4 layers)

### Layer 1: Vertical Stage Skills (18 个)

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + supporting artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture |
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests |
| `development-code-write` / `development-code-review` | 4 | Source Code |
| `testing-write` / `testing-review` | 5 | Test Prep + Procedure + Report；retest pass 后调 `bug-close` |
| `delivery-write` / `delivery-review` | 6 | Deployment + Manual + Installation |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective |

### Layer 2: Cross-cutting (2 个)

- `workflow-protocol` — 状态机、转换、progress 管理（v0.6 patch 后 12 个子命令：init / update / query / recover / release-close / release-start / bug-intake / bug-start / bug-rework / bug-close / incident-start / incident-resolve）
- `doc-guardian` — 目录、命名、frontmatter、change log、binary 校验

### Layer 3: Orchestration (2 个)

- `scenario-dispatcher` — S1/S2/S3/S4 + S2 子场景；S4 仅 active release 期间允许
- `bug-triage` — active mode（分类根因，含 prd-exception）+ post-close mode（创建 BUG + bug-intake）

### Layer 4: Meta (1 个)

- `workflow-evolution` — 消化 Stage 7 retrospective + PRD 异常（incident），产出 workflow / skill / template 改进建议

## 4. Project Conventions

- 语言：英文用于技术术语；中文用于描述
- Doc filenames：lowercase + underscore + `.md`；CR/Bug/Incident 用 ID 大写
- Timestamps：ISO8601 UTC
- Release versions：MAJOR.MINOR 整数对，加引号 `release: "0.1"`
- Release 串行：1 时 1 个 active
- S4 policy：仅 active release 期间触发
- PRD 异常：incident-start → workflow-evolution → incident-resolve（continue/abort/reconstruct）
- Project terminal state：`project_state ∈ {aborted, reconstructing}` 进入终态
- Directory structure：`skills/doc-guardian/references/directory-layout.md`
- Frontmatter schema：`skills/doc-guardian/references/frontmatter-schema.md`
- Change Log：`skills/doc-guardian/scripts/changelog.py promote`
- Review iteration cap：7
- Revise：`*-write` Change Mode
- 术语：`review-passed` / `issues-found`；`approved` 仅人 gate

## 5. State Files

项目根（**禁止手工编辑**）：

- `progress.md` / `progress-history.md` / `.progress.lock`

配置：

- `AGENTS.md` / `CLAUDE.md`（仅 `@AGENTS.md`）

## 6. Forbidden Actions

- 手工编辑 `progress.md`
- 直接编辑 Change Log 章节
- doc 完成前不跑 `skills/doc-guardian/scripts/validate.py`
- stage 推进不调 `skills/workflow-protocol/scripts/progress.py update --advance`
- 在 workflow-protocol 内部跑 unit/integration tests
- 在 directory-layout 定义之外创建 doc 文件
- 从 doc 类 skill 修改 `src/` 或 `tests/`
- 启动新 release 不通过 `skills/workflow-protocol/scripts/progress.py release-start`
- 多 release 并发
- closed release 期间使用 S4
- post-close bug 不通过 `skills/workflow-protocol/scripts/progress.py bug-intake`
- review skill 输出用 `approved`
- bug-triage 判定 `prd-exception` 后切 PRD Change Mode
- Bug Flow 不通过 `skills/workflow-protocol/scripts/progress.py bug-start` 进入 / `bug-close` 退出（v0.5）
- 在 `project_state ∈ {aborted, reconstructing}` 时 update 任何 state（v0.5）

## 7. Recursion Notice

`dev-workflow-skills2` skill 集禁止作用于自身。

## 8. Workflow Specification Reference

实现 `docs/workflow/workflow_specification_claude.md` 中定义的工作流。当前版本 `v0.5`（2026-05-06）。

## 9. Where to Find Things

| 我想知道... | 去哪里看 |
|------------|---------|
| 项目当前 state | `progress.md` 或 `skills/workflow-protocol/scripts/progress.py query` |
| 历史所有动作 | `progress-history.md` |
| Workflow spec | `docs/workflow/workflow_specification_claude.md` |
| Doc 目录布局 | `skills/doc-guardian/references/directory-layout.md` |
| 各 skill 干什么 | 上面 Section 3 |
| 允许 / 禁止 | 上面 Section 6 |
| v1 经验教训 | `docs/research/dev_workflow_skills_v1_design_claude.md` |
| Release 状态 | `progress.md` `release` + `release_state` + `release_close_reason` |
| Pending bugs (post-close) | `progress.md` `unresolved_bugs` |
| Workflow incident | `progress.md` `workflow_incident_active` + `incident_report_path` |
| Project 终态 | `progress.md` `project_state` |

## 10. Scenarios Quick Reference

| Code | Name | 含义 | 子场景 |
|------|------|------|--------|
| S1 | New Product | 从 0 打造 | — |
| S2 | Feature Evolution | 新增需求 | S2-1/2/3/4 |
| S3 | Product Reconstruction | 重建外部项目 | — |
| S4 | Bug Fix | 修 bug；仅 active release | — |

S2 子场景：
- S2-1: PRD 变更引入新功能 → PRD Inception 入口
- S2-2: PRD 不变，仅新增 SRS → SRS Specification (Full Mode for new)
- S2-3: PRD 不变，仅修改 SRS → SRS Specification (Change Mode)
- S2-4: PRD 重构级变更 → 转 S3
```

---

## 7. Pending Work

### 7.1 Task 5: 23 个 Skill 的 SKILL.md 骨架

**批 1（关键基础设施，2 个）**：
- `workflow-protocol`（v0.6 patch 后 12 个子命令完整规范；新增 `bug-rework`）
- `doc-guardian`（8 类 check + changelog.py promote）

**批 2（Orchestration + Meta，3 个）**：
- `scenario-dispatcher`
- `bug-triage`（active + post-close + PRD 异常分支）
- `workflow-evolution`

**批 3（Vertical 18 个）**：
- 7 logical Stage 的 write/review pair（Stage 4 拆 6 个）

### 7.2 Task 6: Implementation

```
dev-workflow-skills2/
├── AGENTS.md.template
├── CLAUDE.md.template
├── skills/
│   ├── workflow-protocol/{SKILL.md, references/, scripts/progress.py}
│   ├── doc-guardian/{SKILL.md, references/, scripts/{validate.py, changelog.py}}
│   ├── prd-write/SKILL.md ... （23 个 physical skill 全部）
├── .claude/skills/ → ../skills/
├── .agents/skills/ → ../skills/
└── docs/{workflow, research, design, review}/
```

---

## 8. Decision Log

### 历史决策（v0.1 / v0.2 / v0.3 / v0.4）

详见各 v0.x doc 的 Decision Log 部分。

### 2026-05-06 (v0.5 - reviewer feedback v0.4 采纳)

- ✅ **F1**：active Bug Flow 闭环—— `progress.py bug-start --bug <path> --root-cause <enum>` 进入；`progress.py bug-close` 退出（retest pass 后）；mutation 精确规定
- ✅ **F2**：`incident-resolve` 3 个 action 精确 mutation；progress.md 加 `project_state: active|aborted|reconstructing` + `release_close_reason` 字段
- ✅ **F3**：全文 script path normalize（清理 v0.4 残留）
- ✅ **F4**：workflow spec §5 移除 v0.3 design 硬引用；§11 workflow-evolution 不再标"待定"；bump v0.5

---

## 9. 评审循环统计

| 版本 | Finding 总数 | High | Medium | Low |
|------|-------------|------|--------|-----|
| v0.1 评审 | 9 | 5 | 4 | 0 |
| v0.2 评审 | 8 | 5 | 3 | 0 |
| v0.3 评审 | 6 | 3 | 2 | 1 |
| v0.4 评审 | 4 | 0 | 2 | 2 |
| v0.5 (current) | — | — | — | — |

**收敛趋势明显**：High 已清零（v0.4 起），Medium 数量稳定低位。

建议 v0.5 后进入 Task 5 实现，实际写 SKILL.md 时遇到的问题再做 v0.6+ 迭代——纯 spec-level 推演已收益递减。

---

**End of Proposal v0.5**
