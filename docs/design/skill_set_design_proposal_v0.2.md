# Skill Set Design Proposal (Skill 集合设计方案)

**Version**: v0.2
**Date**: 2026-05-05
**Status**: Draft — 架构层与详细设计层闭环；待 Task 5 (skill SKILL.md drafts) 与 Task 6 (implementation)
**Workflow Reference**: `docs/workflow/workflow_specification_claude.md` (v0.2)
**Predecessor**: `docs/design/skill_set_design_proposal_v0.1.md`
**Review Response**: `docs/review/reviewer_feedback_response_v0.1.md`

---

## 0. v0.1 → v0.2 主要变化

| 变化点 | 原因 | 影响范围 |
|--------|------|---------|
| Skill 总数 22 → **23** | F6 采纳：新增 `development-code-review` | Section 1, 3, 7, AGENTS.md skill catalog |
| Stage 4 task state 加 code review 循环 | F6 连带 | Section 4 P6 矩阵 |
| `approved` status 适用扩到 CR | F4 | Section 5.3 |
| `required-artifacts.md` 改为 scenario-aware | F2 | Section 5 doc-guardian |
| 命令全文改 `skills/.../scripts/...` 全路径 | F3 (B) | Section 6 AGENTS.md template |
| 新增 Release Lifecycle Rule 节 | F8 | Section 4.12（新增）|
| 新增 S2 Sub-routing 表 | F5 | Section 4.5.1（新增）|
| 明示 revise = `*-write` Change Mode | F7 | Section 3.4 / 4.13 |
| 删 Claude-local memory path | F9 | Section 1 metadata |

---

## 1. Executive Summary

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合。本方案汇总 Task 1-4 的所有架构层与详细设计层决策，作为 Task 5（23 个 skill 骨架设计）和 Task 6（实现）的依据。

### 1.1 架构概览

- **23 个 skill**，分 4 层（Vertical 18 / Cross-cutting 2 / Orchestration 2 / Meta 1）
- **7 阶段主流程** + Bug Flow + 4 场景（S1-S4，含 S2 4 个子场景）
- **Release 严格串行**：同时只 1 个 active release，0.1 → 0.2 → 0.3 顺序推进
- **Foreman binary 校验**：doc-guardian 配 `scripts/validate.py`，exit code 决定 block/pass
- **评审循环**：write → review → revise，cap = 7 次，超限升级人介入；**revise 由 `*-write` 在 Change Mode 下完成**
- **vendor-neutral**：`CLAUDE.md = @AGENTS.md`，AGENTS.md 治理层 + workflow-protocol 操作层；命令统一 `skills/.../scripts/...` 全路径

### 1.2 项目设计哲学

- 用户偏好：先框架后细节；记忆有限所以阶段名要少要清晰；避免文档漂移所以小需求也强制走全流程
- 工作流自身演进：Stage 7 复盘 + PRD 根因异常 两条路径汇入元改进
- 递归悖论意识：本 skill 集**不应作用于 dev-workflow-skills2 自身**，仅用于其他项目
- 代码质量双轨：v0.2 起代码同时由 review skill 评审 + 测试验证（推翻 v0.1 早期"代码不评审"决策）

### 1.3 当前进度

| Task | 状态 | 输出 |
|------|------|------|
| Task 1: 架构层决策 | ✅ Done（v0.2 加 1 项：代码评审）| D1-D5 / Q1-Q3 |
| Task 2: workflow-protocol 设计 | ✅ Done | 5 项责任、progress 格式、scripts、并发模型、P6 矩阵、release lifecycle |
| Task 3: AGENTS.md template | 🟡 Draft v0.2（路径调整）| 10-section template |
| Task 4: doc-guardian 设计 | ✅ Done（v0.2 加 scenario-aware required-artifacts）| F1-F6 (F4 跳过) |
| Task 5: 23 个 skill 骨架 | ⏳ Pending | 按 3 批展开 |
| Task 6: 实现 | ⏳ Pending | 写实际 SKILL.md / scripts / AGENTS.md / CLAUDE.md |

---

## 2. Workflow Reference

完整 workflow spec 在 `docs/workflow/workflow_specification_claude.md` (v0.2)。

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
| S4 | Bug Fix | Bug Flow | Bug Report |

### 2.3 Bug Flow 4 类根因路由

| 根因 | 路径 |
|------|------|
| SRS | CR Document → SRS Update → Architecture Update? → Development → Testing |
| Architecture | Architecture Update（仅版本历史）→ Development → Testing |
| Development | Development Update → Testing |
| PRD（异常逃生阀）| 项目暂停 → Workflow Incident Analysis |

### 2.4 关键规则

- **变更记录**：仅 SRS 变更需 CR Document；Architecture 仅版本历史；其他无需
- **Skill 复用**：同一 skill 通过 Full Mode / Change Mode 应对 4 个场景
- **元演进**：Stage 7 + PRD 根因异常 都汇入 workflow-evolution

---

## 3. Skill Architecture (Task 1)

### 3.1 4 层架构

| Layer | 职责 | Skill 数 |
|-------|------|---------|
| 1 Vertical | 主流程 7 stage 的 write/review skill 配对 | **18** |
| 2 Cross-cutting | workflow-protocol / doc-guardian | 2 |
| 3 Orchestration | scenario-dispatcher / bug-triage | 2 |
| 4 Meta | workflow-evolution | 1 |
| **总计** | | **23** |

### 3.2 Vertical Skill 完整清单（18 个）

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + Supporting Artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 release 引发的 architecture_delta）|
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests（测试代码）|
| **`development-code-write` / `development-code-review`** | 4 | **Source Code（v0.2 起加 review；评审关注架构一致性 / 安全 / 可维护性 / 边界覆盖）** |
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective（项目级，每 release 增量加节）|

### 3.3 架构层决策（已闭环）

| ID | 决策点 | 选定 |
|----|--------|------|
| 评审结构 | Skill 拆分模式 | Foreman 模式（write/review 分开 skill）|
| 评审上限 | 评审循环最多次数 | 7 次（在 progress.md 记录）|
| Stage 4 拆分 | Development 内部分组 | Option I：规划设计 / 测试 / 代码 三组（**v0.2 起代码也有 review**）|
| **代码评审** (v0.2 新加) | Source Code 是否走 review 流程 | **是**（development-code-review skill）|
| D1 | doc 校验机制 | Foreman binary：doc-guardian 配 `scripts/validate.py`，exit 0/1 |
| D2 | CLAUDE.md 形态 | foreman 模式：`CLAUDE.md` = `@AGENTS.md` + AGENTS.md 治理层 + workflow-protocol skill 操作层 |
| D3 | SessionStart Hook | 不要（AGENTS.md 自动加载已够）|
| D4 | vendor-neutral skill 结构 | 要：双 symlink `.claude/skills/` + `.agents/skills/` → `skills/` |
| D5 | Risk-based review（差异化评审）| 不要 v1（先全量评审）|
| Q1 | 评审超 7 次怎么办 | 升级人介入 |
| Q2 | cr-guardian 是否独立 | 合并进 doc-guardian（CR 是一种 doc 类型）|
| Q3 | project-memory-manager 是否独立 | 不要，使用 progress.md + progress-history.md |
| 脚本路径 (v0.2 F3) | 命令路径形式 | 全 skill 路径 `skills/<name>/scripts/...`（不在项目根做 wrapper）|
| Release 并发 (v0.2 F8) | 多 release 是否可并发 | **否，严格串行** |

### 3.4 关键设计原则

设计任何 skill 时遵守：

- 检查它属于哪一层
- vertical skill 必须支持 Full Mode + Change Mode
- 任何 doc 类产物完成前必须调 `skills/doc-guardian/scripts/validate.py`（exit code 决定 block/pass）
- 任何阶段转换必须由 workflow-protocol 驱动，stage skill 不可自行决定下一步
- 评审是流程控制（write → review → revise → loop），不是 stage 内部 sub-process
- **Revise 由 `*-write` skill 在 Change Mode 下完成**——无独立 `*-revise` skill；review 失败时 workflow-protocol 把 sub_state 设为 `revising` → 重新 invoke `*-write`（Change Mode）→ 完成后回到 `in-review` → invoke `*-review`，review_iteration +1
- 不要重复 doc 校验逻辑——doc-guardian 是唯一入口
- skill 命名用 verb-noun（如 `prd-write`），避开 noun-only 反模式
- 单个 SKILL.md 控制在合理篇幅（避开 foreman 690 行 SKILL.md 反例）

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

### 4.2 progress.md Schema

路径：项目根 `progress.md`
格式：YAML frontmatter + markdown body + Recent Activity（自动从 history 派生）
写入：唯一通过 `skills/workflow-protocol/scripts/progress.py update`，禁止直接编辑

```yaml
---
project_name: my-product
workflow_version: v0.2
release: "0.1"                     # 当前 active release 版本（严格串行）
scenario: S1                       # S1/S2/S3/S4
scenario_subtype: null             # S2 时填 S2-1/S2-2/S2-3/S2-4；其他场景 null
current_stage: srs-specification

# 通用 sub-state（development 之外的 stage）
sub_state: review                  # write / in-review / revising / review-passed / approved
review_iteration: 2                # 评审循环计数（cap=7）

# Stage 4 development 专用（仅 current_stage=development 时存在）
development_state:
  total_tasks: 5
  task_states:
    T1: verified
    T2: test-writing
    T3: code-review                # v0.2 加：代码 review 中
    T4: test-done
    T5: planning-done

# 文档产物路径（不含代码）
artifacts:
  prd: docs/prd/prd.md                                # 项目级
  architecture: docs/architecture/architecture.md     # 项目级
  srs: docs/release0.1/srs/srs.md                     # release 级
  acceptance_plan: docs/release0.1/srs/acceptance_plan.md
  integration_plan: docs/release0.1/srs/integration_plan.md      # 多模块时
  architecture_delta: docs/release0.1/architecture_delta.md      # 本 release 改架构时

# Bug 流程
bug_flow:
  active: false
  bug_report_path: null
  root_cause: null               # SRS / Architecture / Development

# Release 状态（v0.2 新加）
release_state: active              # active / closed
previous_releases:                 # 已 close 的 release 列表（只读）
  - "0.1"
  - "0.2"

created: 2026-05-04T08:00:00Z
updated: 2026-05-05T10:00:00Z
---

# Current Stage Summary

**Stage**: SRS Specification
**Sub-state**: review (iteration 2 of 7)
**Document**: docs/release0.1/srs/srs.md
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

### 4.4 scripts/progress.py 接口

物理路径：`skills/workflow-protocol/scripts/progress.py`

| Subcommand | 用途 |
|-----------|------|
| `init` | 新项目初始化 progress.md |
| `update` | 应用一次状态转换（原子更新两文件 + 回退）|
| `query` | 读取当前 state（只读，可并发）|
| `recover` | 从 progress-history.md 重建 progress.md |
| **`release-close`** (v0.2 新加) | Stage 7 完成时 close 当前 release，准备启动下个 release |

`update` 原子流程：

1. 计算 new_progress + new_history_entry
2. 申请 file lock（flock on `.progress.lock`）
3. 备份两个文件
4. 校验状态机转换合法性（不合法 → fail，不动文件）
5. 写入：append progress-history.md → overwrite progress.md
6. 一致性校验（从 history 重建 progress.md == 实际写入）
7. 任一步失败 → rollback 两文件 + report error；成功 → 删备份 + 解锁

任何 update 失败要求 AI 修复触发原因后重新调用，禁止绕过脚本直接写。

### 4.5 Scenario Routing

#### 4.5.1 S2 子场景路由表（v0.2 新加）

scenario-dispatcher 在判定 S2 后，必须进一步判定 sub-type：

| 子场景 | 适用条件 | 入口 Stage | progress 字段 |
|--------|---------|-----------|---------------|
| **S2-1** | PRD 变更引入新功能（不影响原有核心功能/边界）| PRD Inception (Change Mode) | `scenario: S2, scenario_subtype: S2-1` |
| **S2-2** | PRD 不变，仅新增 Software Requirement / 接口 / 行为 | SRS Specification (Full Mode for new sections) | `scenario: S2, scenario_subtype: S2-2` |
| **S2-3** | PRD 不变，仅修改 SRS 细节 / 验收 / 接口 | SRS Specification (Change Mode) | `scenario: S2, scenario_subtype: S2-3` |
| **S2-4** | PRD 变更影响原有核心功能，需要 reconstruction | 终止当前 evolution → 转 S3（新 project）| 不进入 S2 流程 |

**S2 → release 关系**：S2-1/2/3 全部映射为"新 release"（每个 S2 子场景启动一个新 release）。S2-4 不是 release，是新 project（走 S3）。

#### 4.5.2 详细路由由 scenario-dispatcher skill 实现

scenario-dispatcher 在新会话时检查项目状态，按以下决策树路由：

```
项目根有 progress.md？
  否 → S1 (新项目) 或 S3 (重构)，由用户/scenario-dispatcher 选择
  是 → 当前 release 已 close（release_state == closed）?
        是 → S2 (新 release) 或 S4 (bug fix)，由用户选择
        否 → 继续当前 release（current_stage 决定 invoke 哪个 skill）
```

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

### 4.8 P6 Stage 完成判定矩阵

通用 4 维 + 部分 stage 第 5 维：

| 维度 | 检查方式 | 失败动作 |
|------|---------|---------|
| A. 必需 artifacts 存在 | 文件路径在 `artifacts:` 中且文件存在；**S3 场景 Stage 1/2 强制额外检查源系统分析 artifacts** | block，stage skill 补产 |
| B. doc-guardian 校验通过 | `validate.py` 跑所有 artifacts exit 0 | block，按校验报错修复 |
| C. Review 通过 | 对应 `*-review` skill 最后一轮返回 "approved" | 触发新一轮 revise（计数+1，超 7 升级人介入）|
| D. 人确认（仅 PRD/SRS/Architecture/CR）| progress-history.md 有 "human-confirmed" 条目 | block，等人 confirm |
| E. 内部验证（Stage 4/5/6）| verification artifact frontmatter 含 `verification_status: pass` | 视情况：fail → Bug Flow / 重试 |

### 4.9 7 个 Stage 的判定矩阵

| Stage | A. 必需 Artifacts | B. doc-guardian | C. Review | D. Human | E. Verification |
|-------|-------------------|-----------------|-----------|----------|----------------|
| 1 PRD | PRD（S3 时含源系统 PRD 分析 + Feature Matrix）| ✓ | ✓ | ✓ | — |
| 2 SRS | SRS + Acceptance Plan + Integration Plan（多模块）（S3 时含源系统 SRS / Module 分析等）| ✓ | ✓ | ✓ | — |
| 3 Architecture | Architecture Document（+ delta if applicable）| ✓ | ✓ | ✓ | — |
| **4 Development** | 见 4.10 特殊判定（**v0.2 加 code review**）| | | | |
| 5 Testing | Test Preparation + Procedure + Report | ✓ | ✓ | — | Test Report `status: pass`（fail → Bug Flow）|
| 6 Delivery | Deployment + Operation Manual + Installation Result | ✓ | ✓ | — | Installation 执行成功 |
| 7 Retrospective | Issue Report + Improvement Proposals | ✓ | ✓ | — | — |

### 4.10 Stage 4 特殊判定（v0.2 含 code review）

```
Stage 4 done ⇔ all task_states[Tn] == "verified"
```

每 task 完整子状态序列（v0.2）：

| 子状态 | 满足条件 |
|--------|---------|
| `planning-done` | Detailed Design (Tn) 通过 doc-guardian + review approved |
| `test-writing` → `test-review` → `test-revising` → `test-done` | Unit/Integration Tests 通过 doc-guardian + review approved |
| `code-writing` → `code-review` → `code-revising` → `code-review-passed` | Source Code 通过 development-code-review |
| `verifying` → `verified` | unit + integration test 全部 pass（development-code-write 跑测试，写 Local Verification Result）|

注意 v0.2 加了 code-review 阶段：代码先经 review skill 评审通过，再跑测试验证，**双 gate 并存**。

### 4.11 Bug Flow 触发

Stage 5 E 失败（Test Report `status: fail`）→ 不推进 Stage 6，进入 Bug Flow：

1. workflow-protocol 设 `bug_flow.active = true`，记录 `bug_report_path` 和 `root_cause`（由 bug-triage skill 输出）
2. `current_stage` 切到 root_cause 对应的 stage（Change Mode）
3. 该 stage Change Mode 的 done 条件 = "影响范围内的 artifacts 重新通过 A/B/C/D/E"
4. 完成后自动回到 Stage 5 重测（不是正常推进）
5. Pass 后 `bug_flow.active = false`，正常推进 Stage 6

### 4.12 Release Lifecycle Rule（v0.2 新加）

**核心原则**：Release 严格串行，不可并发。

| 规则 | 内容 |
|------|------|
| **同时只 1 个 active release** | progress.md `release_state` 字段约束。只有当前 active release 接受写入。|
| **Release 创建** | 当前 release 走完 Stage 7 后，scenario-dispatcher 启动新 release（S2 子场景或 S3 入口）|
| **Release 编号** | 用户在 init 新 release 时手动指定（如 `0.2`、`1.0`），不强制递增规则；建议遵循 SemVer 风格 |
| **Bug fix target** | 必须 target **当前 active release**；旧 release close 后不接受补丁 |
| **Release close 条件** | Stage 7 retrospective 完成且 review-passed（**不是 Delivery 完成**）|
| **历史 release 只读** | release close 后，对应 `docs/release0.x/` 目录变只读；ID artifact (CR/Bug) 仍可创建但 target_release 必须是当前 active |
| **S2 → release 映射** | S2-1/S2-2/S2-3 全部触发新 release；S2-4 转 S3 是新 project（不是 release）|
| **Release 编号约束** | progress.md 的 `previous_releases` 列表追踪历史；新 release 编号必须大于所有 previous（弱约束，由用户保证）|

### 4.13 Revise Action Ownership（v0.2 新加澄清）

**问题（F7）**：状态机有 `revising` 状态，但 Skill Catalog 没 `*-revise` skill。

**规则**：

- **Revise 由 `*-write` skill 在 Change Mode 下完成**——无独立 `*-revise` skill
- review 失败时的状态转换由 workflow-protocol 驱动：

```
sub_state: in-review (review skill 输出 "issues found")
  ↓ workflow-protocol 转换
sub_state: revising  +  review_iteration += 1
  ↓ workflow-protocol invoke *-write skill in Change Mode
sub_state: in-review (write skill 完成 revise，重新进入 review)
  ↓ workflow-protocol invoke *-review skill
sub_state: revising 或 review-passed (按 review 结果)
```

- 每个 `*-write` skill 的 SKILL.md 必须明示如何区分 Full Mode 和 Change Mode：
  - **Full Mode**：from scratch，输入是上游 stage 产物
  - **Change Mode**：增量改，输入是 review issues 列表 + 当前 doc 内容

### 4.14 关键约定

- **Verification artifact** 必含 `verification_status: pass | fail | partial`
- **Required vs Optional artifacts** 由 doc-guardian 集中声明（`skills/doc-guardian/references/required-artifacts.md`，**scenario-aware**）
- **Stage advance** 显式：stage skill 调 `progress.py update --advance`，workflow-protocol 校验 done 条件后推进，可拒绝

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
│   │   ├── prd.md                        # 主 PRD（含 Pending Changes + Change Log 章节）
│   │   └── supporting/                   # 附属文档
│   │       ├── competitor_research.md
│   │       ├── competitor_architecture.md
│   │       ├── market_research.md
│   │       ├── feature_matrix.md         # S3 必备
│   │       └── source_product_prd_analysis.md  # S3 必备（v0.2 强调）
│   │
│   ├── architecture/                     # 项目级
│   │   └── architecture.md               # 主架构（含 Pending + Change Log）
│   │
│   ├── release0.1/                       # 第 1 个 release
│   │   ├── srs/
│   │   │   ├── srs.md                    # 唯一 SRS（含 Pending + Change Log）
│   │   │   ├── acceptance_plan.md
│   │   │   ├── integration_plan.md       # 多模块时
│   │   │   ├── source_product_srs_analysis.md  # S3 必备
│   │   │   ├── source_module_analysis.md       # S3 必备
│   │   │   └── reuse_replace_capability.md     # S3 必备
│   │   ├── architecture_delta.md         # 本 release 引发的架构变更（如有）
│   │   ├── development/
│   │   │   ├── plan.md
│   │   │   ├── breakdown.md
│   │   │   └── tasks/
│   │   │       ├── T1/
│   │   │       │   ├── detailed_design.md
│   │   │       │   ├── code_review_report.md  # v0.2 加：代码评审报告
│   │   │       │   └── verification_result.md
│   │   │       └── T2/...
│   │   ├── testing/
│   │   │   ├── preparation.md
│   │   │   ├── procedure.md
│   │   │   └── report.md
│   │   └── delivery/
│   │       ├── deployment.md
│   │       ├── operation_manual.md
│   │       └── installation_result.md
│   │
│   ├── release0.2/                       # 第 2 个 release（结构同 0.1）
│   │   └── ...
│   │
│   ├── retrospective/                    # 项目级，每 release 增量加节
│   │   └── retrospective.md              # 含 Pending + Change Log
│   │
│   ├── cr/                               # 横跨 release
│   │   ├── CR-001.md
│   │   └── CR-002.md
│   │
│   └── bug/                              # 横跨 release
│       ├── BUG-001.md
│       └── BUG-002.md
│
├── src/                                  # 源代码（doc-guardian 不管辖）
└── tests/                                # 测试代码（doc-guardian 不管辖）
    ├── unit/
    └── integration/
```

### 5.2 F2: 命名 Convention

- **Doc 文件**：lowercase + underscore + `.md`
- **CR / Bug Reports**：ID 大写 `CR-001.md`、`BUG-005.md`
- **不带 `_claude` 后缀**
- **Task 子目录**：`T1/`、`T2/` 大写 + 数字
- **Release 目录**：`release0.1/`、`release0.2/`

### 5.3 F3: Frontmatter Schema

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

#### Status 状态机

| 状态 | 含义 | 适用 |
|------|------|------|
| `draft` | 写作中 | 全部 doc |
| `in-review` | review skill 评审中 | 全部 doc |
| `revising` | 收到 review 反馈在修订（write skill Change Mode 中）| 全部 doc |
| `review-passed` | AI review 通过（**最终态：非 gated 文档**）| 全部 doc |
| `approved` | 人确认通过（**最终态**）| **PRD / SRS / Architecture / CR**（v0.2 扩展含 CR）|

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
| **`code-review-report`** (v0.2) | `docs/release0.x/development/tasks/Tn/code_review_report.md` | `release`, `task_id`, `findings_count`, `severity_distribution` |
| `verification-result` | `docs/release0.x/development/tasks/Tn/verification_result.md` | `release`, `task_id`, **`verification_status`** |
| `test-preparation` | `docs/release0.x/testing/preparation.md` | `release` |
| `test-procedure` | `docs/release0.x/testing/procedure.md` | `release` |
| `test-report` | `docs/release0.x/testing/report.md` | `release`, **`verification_status`**, `total_test_cases`, `passed`, `failed` |
| `deployment-doc` | `docs/release0.x/delivery/deployment.md` | `release` |
| `operation-manual` | `docs/release0.x/delivery/operation_manual.md` | `release` |
| `installation-result` | `docs/release0.x/delivery/installation_result.md` | `release`, **`verification_status`** |
| `cr` | `docs/cr/CR-NNN.md` | `cr_id`, `target_release`, `affected_doc` |
| `bug-report` | `docs/bug/BUG-NNN.md` | `bug_id`, `found_in_release`, `target_release`, `root_cause` |

S3 必备 supporting artifacts（type 复用类似 `competitor-research`，路径在 `docs/prd/supporting/` 或 `docs/release0.x/srs/`，frontmatter 加 `s3_mandatory: true` 标记）。

### 5.4 F4: 必需章节 — Skipped

每个 doc 类型的 body 章节由对应的 write/review skill pair 协调（共享 sections 列表）。doc-guardian 不强制 body 章节结构。

### 5.5 F5: validate.py 8 类校验

| # | 类别 | 检查内容 | 失败示例 |
|---|------|---------|---------|
| 1 | Path | doc 文件路径符合 type 的目录规则 | `type: srs` 但在 `docs/prd/`：fail |
| 2 | Naming | 文件名符合 convention | `Acceptance_Plan.md` 含大写：fail |
| 3 | Frontmatter Schema | universal 5 字段全在 + per-type 扩展字段全在 + status/type 是合法 enum（含 v0.2 CR-approved 扩展）| 缺 `created`：fail |
| 4 | Frontmatter Format | timestamp ISO8601 UTC、release `"x.y"`、owner `agent/skill`、ID `CR-\d+` / `BUG-\d+` | `release: 0.1`：fail |
| 5 | Cross-Reference | 路径字段指向真实文件 | `affected_doc` 指向不存在文件：fail |
| 6 | Change Log Discipline | `## Pending Changes` 为空 + `## Change Log` 格式合法 | Pending 残留：fail |
| 7 | ID Uniqueness | `docs/cr/` 下 CR-NNN 唯一，`docs/bug/` 下 BUG-NNN 唯一 | 两个 `CR-005.md`：fail |
| 8 | Consistency with progress.md | doc 的 `status` 和 progress.md `current_stage`/`sub_state` 兼容 | 状态不兼容：fail |

#### 子命令

```bash
skills/doc-guardian/scripts/validate.py file <doc-path>      # 单文件 check（1-7）
skills/doc-guardian/scripts/validate.py all                   # 整个 docs/ 目录
skills/doc-guardian/scripts/validate.py consistency           # 类 8 cross-file
skills/doc-guardian/scripts/validate.py ids                   # 仅 ID 唯一性
```

`progress.py update` 内部默认调 `validate.py file <changed-doc>`。

### 5.6 F6: doc-guardian 物理结构

```
skills/doc-guardian/
├── SKILL.md                       主协议（~200-300 行）
├── references/
│   ├── directory-layout.md        F1 全文：目录树 + 各 type 路径规则
│   ├── frontmatter-schema.md      F3 全文：universal + 各 type 字段表 + 模板
│   ├── change-log-format.md       Pending Changes 和 Change Log 严格格式
│   └── required-artifacts.md      P6 配套：每 stage required vs optional artifact 清单（**scenario-aware**：S1/S2/S3/S4 各自不同必备清单）
└── scripts/
    ├── validate.py                F5 主校验（8 类 check）
    └── changelog.py               promote / validate Pending Changes
```

### 5.7 Change Log 自动化机制

#### 文档内的两个章节

```markdown
---
[frontmatter]
---

# Document Title

## 1. ... (主体内容)
## 2. ...
...

## Pending Changes
- 2026-05-15T10:00:00Z [Section 3.2]: 新增用户认证需求

## Change Log

### 2026-05-10
- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建
```

#### Pending Changes 严格格式

```
- {ISO8601 UTC timestamp} [{section_ref}]: {one_line_summary}
```

#### scripts/changelog.py promote 行为

1. 读取目标 doc 的 `## Pending Changes` 章节
2. 校验每条 entry 符合严格格式
3. 按日期分组到 `### YYYY-MM-DD` 块
4. 插入 `## Change Log` 章节顶部
5. 清空 `## Pending Changes`
6. 写回文件（atomic）

#### 强制纪律

`validate.py` 检查 `## Pending Changes` 章节必须为空，否则 exit 1。

#### `*-write` skill 标准流程（v0.2 含自评）

```
1. 生成/修改 doc 主体内容
2. 在 ## Pending Changes 章节加新 entry
3. 运行 changelog.py promote
4. 自评（调 doc-guardian validate.py）
5. 自修复
6. 提交给 *-review skill
```

---

## 6. AGENTS.md Template (Task 3)

### 6.1 完整 Draft（v0.2，命令路径调整）

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
4. 从 state 判定：scenario (S1/S2/S3/S4)、`scenario_subtype` (S2-1/2/3/4)、`current_stage`、`sub_state`、`release`、`bug_flow.active`
5. 如果 `scenario` 未设 → invoke `scenario-dispatcher`；如果 `bug_flow.active=true` → invoke `bug-triage`
6. 找到当前 state 对应的 skill，读它的 `SKILL.md`
7. 开始干活

## 3. Skill Catalog (23 skills, 4 layers)

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

- `workflow-protocol` — 状态机、转换、progress 管理（`scripts/progress.py`）、评审循环计数、must-call 规则
- `doc-guardian` — 目录结构、命名、frontmatter、change log 规范、binary 校验（`scripts/validate.py`、`scripts/changelog.py`）

### Layer 3: Orchestration (2 个)

- `scenario-dispatcher` — 项目入口判定 S1/S2/S3/S4 + S2 子场景 (S2-1/2/3/4)
- `bug-triage` — bug 根因分类（SRS / Architecture / Development / PRD-异常），路由到对应 stage 的 Change Mode

### Layer 4: Meta (1 个)

- `workflow-evolution` — 消化 Stage 7 retrospective + PRD 根因异常输入

## 4. Project Conventions

- **语言**：英文用于 skill 名 / 文件路径 / frontmatter / 技术术语；中文用于描述和说明
- **Doc filenames**：lowercase + underscore + `.md`；CR/Bug 用 ID 大写 `CR-001.md`、`BUG-005.md`
- **Timestamps**：一律 ISO8601 UTC（`2026-05-15T10:00:00Z`）
- **Release versions**：YAML 中必须加引号字符串 `release: "0.1"`
- **Release 串行**：同时只 1 个 active release，0.1 → 0.2 → 0.3 顺序
- **Directory structure**：见 `skills/doc-guardian/references/directory-layout.md`
- **Frontmatter schema**：见 `skills/doc-guardian/references/frontmatter-schema.md`
- **Change Log**：通过 `skills/doc-guardian/scripts/changelog.py promote` 管理
- **Review iteration cap**：7 次；超过 → 升级人介入
- **Revise**：由 `*-write` skill 在 Change Mode 下完成（无独立 `*-revise` skill）

## 5. State Files

项目根下脚本管理的文件（**禁止手工编辑**）：

- `progress.md` — 当前 workflow state
- `progress-history.md` — append-only 全量日志
- `.progress.lock` — 原子更新用文件锁

配置文件：

- `AGENTS.md` — 本文件
- `CLAUDE.md` — 仅含 `@AGENTS.md`

## 6. Forbidden Actions

- 手工编辑 `progress.md` —— 必须用 `skills/workflow-protocol/scripts/progress.py update`
- 直接编辑 Change Log 章节 —— 必须用 `skills/doc-guardian/scripts/changelog.py promote`
- doc 完成前不跑 `validate.py` —— 必须 exit 0 才能 declare done
- stage 推进不调 `skills/workflow-protocol/scripts/progress.py update --advance`
- 在 workflow-protocol 内部跑 unit/integration tests —— workflow-protocol 只读 `verification_status` 字段
- 在 `skills/doc-guardian/references/directory-layout.md` 定义之外的目录创建 doc 文件
- 从 doc 类 skill 修改 `src/` 或 `tests/`
- 启动新 release 不通过 `skills/workflow-protocol/scripts/progress.py release-close`（必须先 close 当前）
- 多 release 并发 —— 严格串行，违反此规则会被 progress.py 拒绝

## 7. Recursion Notice

`dev-workflow-skills2` skill 集**禁止**作用于 `dev-workflow-skills2` 自身。本 skill 集应用于**其他项目**。

## 8. Workflow Specification Reference

本 skill 集实现 `docs/workflow/workflow_specification_claude.md`（skill 仓库）中定义的工作流。每个项目的 `progress.md` 的 `workflow_version` 字段记录其遵循的版本；当前版本是 `v0.2`（2026-05-05）。

## 9. Where to Find Things

| 我想知道... | 去哪里看 |
|------------|---------|
| 项目当前 state | `progress.md` 或 `skills/workflow-protocol/scripts/progress.py query` |
| 历史所有动作 | `progress-history.md` |
| Workflow spec 定义 | `docs/workflow/workflow_specification_claude.md`（skill 仓库）|
| Doc 目录布局 | `skills/doc-guardian/references/directory-layout.md` |
| 各 skill 干什么 | 上面 Section 3 + 各 skill 的 `SKILL.md` |
| 允许 / 禁止做什么 | 上面 Section 6 + 各 skill 的 "Forbidden" 章节 |
| v1 当年踩过什么坑 | `docs/research/dev_workflow_skills_v1_design_claude.md` |
| Release 当前状态 | `progress.md` `release` + `release_state` 字段 |

## 10. Scenarios Quick Reference

| Code | Name | 含义 | 子场景 |
|------|------|------|--------|
| S1 | New Product | 从 0 打造一个新项目 | — |
| S2 | Feature Evolution | 在已规范化的项目上新增需求（每次新需求触发新 release）| S2-1/2/3/4 |
| S3 | Product Reconstruction | 把已存在的外部项目按本规范重建为新项目 | — |
| S4 | Bug Fix | 修复已规范化项目中的 bug | — |

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
- `workflow-protocol` 完整 SKILL.md（含 references/scripts 详细规范）
- `doc-guardian` 完整 SKILL.md（含 validate.py / changelog.py 行为）

**批 2（Orchestration + Meta，3 个）**：
- `scenario-dispatcher` — 4 场景判定 + S2 子场景路由
- `bug-triage` — 4 类根因分类逻辑
- `workflow-evolution` — Retrospective + PRD-exception 消化

**批 3（Vertical 18 个）**：
- 7 个 stage 的 write/review skill pair（Stage 4 拆 6 个：含新增 development-code-review）
- 模板化程度高，可批量产出

### 7.2 Task 6: Implementation

```
dev-workflow-skills2/
├── AGENTS.md.template
├── CLAUDE.md.template
├── skills/
│   ├── workflow-protocol/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/progress.py
│   ├── doc-guardian/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/{validate.py, changelog.py}
│   ├── prd-write/SKILL.md
│   ├── prd-review/SKILL.md
│   ├── ...
│   ├── development-code-write/SKILL.md
│   ├── development-code-review/SKILL.md      # v0.2 新加
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

- ✅ Workflow spec v0.2（merge 三份草案）
- ✅ 4 层 skill 架构 + 22 skill 总数（v0.2 后改 23）
- ✅ Foreman 模式（write/review 拆分）
- ✅ Stage 4 拆 3 组（planning / test / code）
- ✅ 评审循环 cap = 7
- ✅ D1-D5 / Q1-Q3 全闭环
- ✅ workflow-protocol 责任精简到 5 项
- ✅ progress.md / progress-history.md schema
- ✅ scripts/progress.py 接口
- ✅ 并发模型：统一 update + lock
- ✅ 两层粒度：progress.md = task 级，history = 子任务级
- ✅ P6 完成判定矩阵 4-5 维 + Stage 4 特殊处理
- ✅ Release 版本化结构
- ✅ doc 文件不带 `_claude` 后缀
- ✅ change_log 章节 + 自动化
- ✅ Frontmatter 5 universal 字段
- ✅ Status 5 状态
- ✅ owner = `<agent>/<skill>` 格式
- ✅ doc-guardian 不强制 body 章节
- ✅ validate.py 8 类 check
- ✅ AGENTS.md 10-section template

### 2026-05-05 (v0.2，评审反馈采纳)

- ✅ **F1**：skill count 修正（实际 23）
- ✅ **F2**：required-artifacts.md 改为 scenario-aware（S3 强制源系统分析）
- ✅ **F3 (B)**：命令统一全 skill 路径 `skills/<name>/scripts/...`
- ✅ **F4**：`approved` status 适用扩到 CR
- ✅ **F5**：S2 子场景路由表 + progress 加 scenario_subtype 字段
- ✅ **F6 (a)**：新增 `development-code-review` skill（**推翻"代码不评审"原决策**）
- ✅ **F7**：明示 revise = `*-write` Change Mode（无独立 `*-revise` skill）
- ✅ **F8**：Release Lifecycle Rule（**严格串行**，一时只 1 个 active）
- ✅ **F9**：删除 Memory Reference 中 Claude-local path

---

**End of Proposal v0.2**
