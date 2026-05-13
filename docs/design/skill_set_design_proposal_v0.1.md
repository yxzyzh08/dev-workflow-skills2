# Skill Set Design Proposal (Skill 集合设计方案)

**Version**: v0.1
**Date**: 2026-05-05
**Status**: Draft — 架构层与详细设计层闭环；待 Task 5 (skill SKILL.md drafts) 与 Task 6 (implementation)
**Workflow Reference**: `docs/workflow/workflow_specification_claude.md` (v0.2)
**Memory Reference**: `~/.claude/projects/-home-cgs-github-projects-dev-workflow-skills2/memory/`

---

## 1. Executive Summary

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合。本方案汇总 Task 1-4 的所有架构层与详细设计层决策，作为 Task 5（23 个 skill 骨架设计）和 Task 6（实现）的依据。

### 1.1 架构概览

- **22 个 skill**，分 4 层（Vertical / Cross-cutting / Orchestration / Meta）
- **7 阶段主流程** + Bug Flow + 4 场景（S1-S4）
- **Release 版本化**：PRD / Architecture / Retrospective 项目级；SRS / Development / Testing / Delivery release 级
- **Foreman binary 校验模式**：doc-guardian 配 `scripts/validate.py`，exit code 决定 block/pass
- **评审循环**：write → review → revise，cap = 7 次，超限升级人介入
- **vendor-neutral**：`CLAUDE.md = @AGENTS.md`，AGENTS.md 治理层 + workflow-protocol 操作层

### 1.2 项目设计哲学

- 用户偏好：先框架后细节；记忆有限所以阶段名要少要清晰；避免文档漂移所以小需求也强制走全流程
- 工作流自身演进：Stage 7 复盘 + PRD 根因异常 两条路径汇入元改进
- 递归悖论意识：本 skill 集**不应作用于 dev-workflow-skills2 自身**，仅用于其他项目

### 1.3 当前进度

| Task | 状态 | 输出 |
|------|------|------|
| Task 1: 架构层决策 | ✅ Done | D1-D5 / Q1-Q3 全闭环 |
| Task 2: workflow-protocol 设计 | ✅ Done | 5 项责任、progress 格式、scripts、并发模型、P6 矩阵 |
| Task 3: AGENTS.md template | 🟡 Draft | 10-section template，待最终确认 |
| Task 4: doc-guardian 设计 | ✅ Done | F1-F6 (F4 跳过)，含 Change Log 自动化 |
| Task 5: 23 个 skill 骨架 | ⏳ Pending | 按 3 批展开 |
| Task 6: 实现 | ⏳ Pending | 写实际 SKILL.md / scripts / AGENTS.md / CLAUDE.md |

---

## 2. Workflow Reference

完整 workflow spec 在 `docs/workflow/workflow_specification_claude.md` (v0.2)。

### 2.1 主流程 7 阶段

| # | Stage | Lead | Human Gate | 主要产出 |
|---|-------|------|------------|---------|
| 1 | PRD Inception | Human + AI | ✓ | PRD + Supporting Artifacts |
| 2 | SRS Specification | Human + AI | ✓ | SRS + Acceptance Plan + Integration Plan（多模块时） |
| 3 | Architecture Design | AI | ✓ | Architecture + (per-release) architecture_delta |
| 4 | Development | AI | × | Plan + Breakdown + Detailed Design + Tests + Source Code |
| 5 | Testing | AI | × | Test Preparation + Procedure + Report |
| 6 | Delivery | AI | × | Deployment Doc + Operation Manual + Installation Result |
| 7 | Project Retrospective | AI | × | Issue Report + Improvement Proposals（项目级，每 release 增量加节）|

### 2.2 4 场景

| Code | Name | 流程 | Input |
|------|------|------|-------|
| S1 | New Product | 主流程全程 | 无 |
| S2 | Feature Evolution | 主流程全程（incremental mode）| 当前项目的 PRD/SRS/Architecture |
| S3 | Product Reconstruction | 主流程全程 | 源系统 PRD + 源系统 SRS |
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
| 1 Vertical | 主流程 7 stage 的 write/review skill 配对 | 17 |
| 2 Cross-cutting | workflow-protocol / doc-guardian | 2 |
| 3 Orchestration | scenario-dispatcher / bug-triage | 2 |
| 4 Meta | workflow-evolution | 1 |
| **总计** | | **22** |

### 3.2 Vertical Skill 完整清单（17 个）

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + Supporting Artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 release 引发的 architecture_delta） |
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests（测试代码）|
| `development-code-write` | 4 | Source Code（**无 review 配对**，靠测试验证质量）|
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective（项目级，每 release 增量加节）|

### 3.3 架构层决策（已闭环）

| ID | 决策点 | 选定 |
|----|--------|------|
| 评审结构 | Skill 拆分模式 | Foreman 模式（write/review 分开 skill）|
| 评审上限 | 评审循环最多次数 | 7 次（在 progress.md 记录）|
| Stage 4 拆分 | Development 内部分组 | Option I：规划设计 / 测试 / 代码 三组 |
| D1 | doc 校验机制 | Foreman binary：doc-guardian 配 `scripts/validate.py`，exit 0/1 |
| D2 | CLAUDE.md 形态 | foreman 模式：`CLAUDE.md` = `@AGENTS.md` + AGENTS.md 治理层 + workflow-protocol skill 操作层 |
| D3 | SessionStart Hook | 不要（AGENTS.md 自动加载已够）|
| D4 | vendor-neutral skill 结构 | 要：双 symlink `.claude/skills/` + `.agents/skills/` → `skills/` |
| D5 | Risk-based review（差异化评审）| 不要 v1（先全量评审）|
| Q1 | 评审超 7 次怎么办 | 升级人介入 |
| Q2 | cr-guardian 是否独立 | 合并进 doc-guardian（CR 是一种 doc 类型）|
| Q3 | project-memory-manager 是否独立 | 不要，使用 progress.md + progress-history.md |

### 3.4 关键设计原则（设计任何 skill 时遵守）

- 检查它属于哪一层
- vertical skill 必须支持 Full Mode + Change Mode
- 任何 doc 类产物完成前必须调 `doc-guardian/scripts/validate.py`（exit code 决定 block/pass）
- 任何阶段转换必须由 workflow-protocol 驱动，stage skill 不可自行决定下一步
- 评审是流程控制（write → review → revise → loop），不是 stage 内部 sub-process
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
| 4 | progress.md / progress-history.md 管理 | 含 `scripts/progress.py` |
| 5 | 评审循环计数 + 超 7 升级 | 在 progress.md 记录 review_iteration |

剥离责任：Bootstrap → AGENTS.md；Scenario 路由 → scenario-dispatcher；Bug 流程路由 → bug-triage。

### 4.2 progress.md Schema

路径：项目根 `progress.md`
格式：YAML frontmatter + markdown body + Recent Activity（自动从 history 派生）
写入：唯一通过 `scripts/progress.py update`，禁止直接编辑

```yaml
---
project_name: my-product
workflow_version: v0.2
release: "0.1"                     # 当前 release 版本
scenario: S1                       # S1/S2/S3/S4
current_stage: srs-specification

# 通用 sub-state（development 之外的 stage）
sub_state: review                  # write / review / revising / review-passed / approved
review_iteration: 2                # 评审循环计数（cap=7）

# Stage 4 development 专用（仅 current_stage=development 时存在）
development_state:
  total_tasks: 5
  task_states:
    T1: verified
    T2: test-writing
    T3: code-writing
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

created: 2026-05-04T08:00:00Z
updated: 2026-05-05T10:00:00Z
---

# Current Stage Summary

**Stage**: SRS Specification
**Sub-state**: review (iteration 2 of 7)
**Document**: docs/release0.1/srs/srs.md
**Last action**: review found 1 issue
**Next action**: srs-revise iteration 2

# Recent Activity (auto-derived from progress-history.md)

## 2026-05-05T10:00:00Z — srs-review iteration 2 — 1 issue found
## 2026-05-05T08:30:00Z — srs-review iteration 1 — 3 issues found
## 2026-05-05T08:00:00Z — srs-write completed
```

**Stage 4 body 用每任务格式化模板**：

```markdown
# Tasks

## T1 — [verified] User authentication module
- Planning: done 2026-05-04
- Tests: 12 unit + 3 integration, all passing
- Code: src/auth/ (450 LoC)
- Verification: full suite passing

## T2 — [test-writing] Profile API
- Planning: done 2026-05-04
- Tests: 5/8 done
- Code: not started
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

| Subcommand | 用途 |
|-----------|------|
| `init` | 新项目初始化 progress.md（template） |
| `update` | 应用一次状态转换（原子更新两文件 + 回退） |
| `query` | 读取当前 state（只读，可并发） |
| `recover` | 从 progress-history.md 重建 progress.md（异常恢复） |

`update` 原子流程：

1. 计算 new_progress + new_history_entry
2. 申请 file lock（flock on `.progress.lock`）
3. 备份两个文件
4. 校验状态机转换合法性（不合法 → fail，不动文件）
5. 写入：append progress-history.md → overwrite progress.md
6. 一致性校验（从 history 重建 progress.md == 实际写入）
7. 任一步失败 → rollback 两文件 + report error；成功 → 删备份 + 解锁

任何 update 失败要求 AI 修复触发原因后重新调用，禁止绕过脚本直接写。

### 4.5 并发模型

- **统一接口**：任何 agent（无论主协调还是 sub-agent）都通过 `progress.py update`
- **锁内部处理并发**：多 agent 并发请求由锁序列化
- **Stage 4 子 agent 接口（Option B）**：调一律是 `update`，脚本 diff old vs new task state；没变只 append history、变了原子更新两文件

### 4.6 两层粒度

| 文件 | 粒度 | 装什么 |
|------|------|--------|
| progress.md | 任务级（T1, T2, ...）| task 状态、stage 状态 |
| progress-history.md | 子任务级 + 任务级 | 所有有意义事件 |

子任务（"T2 完成第 5 个测试"）只在 history 里，progress.md 不出现。

### 4.7 P6 Stage 完成判定矩阵

通用 4 维 + 部分 stage 第 5 维：

| 维度 | 检查方式 | 失败动作 |
|------|---------|---------|
| A. 必需 artifacts 存在 | 文件路径在 `artifacts:` 中且文件存在 | block，stage skill 补产 |
| B. doc-guardian 校验通过 | `validate.py` 跑所有 artifacts exit 0 | block，按校验报错修复 |
| C. Review 通过 | 对应 `*-review` skill 最后一轮返回 "approved" | 触发新一轮 revise（计数+1，超 7 升级人介入）|
| D. 人确认（仅 PRD/SRS/Arch）| progress-history.md 有 "human-confirmed" 条目 | block，等人 confirm |
| E. 内部验证（Stage 4/5/6）| verification artifact frontmatter 含 `verification_status: pass` | 视情况：fail → Bug Flow / 重试 |

### 4.8 7 个 Stage 的判定矩阵

| Stage | A. 必需 Artifacts | B. doc-guardian | C. Review | D. Human | E. Verification |
|-------|-------------------|-----------------|-----------|----------|----------------|
| 1 PRD | PRD（Supporting 可选）| ✓ | ✓ | ✓ | — |
| 2 SRS | SRS + Acceptance Plan + Integration Plan（多模块）| ✓ | ✓ | ✓ | — |
| 3 Architecture | Architecture Document（+ delta if applicable） | ✓ | ✓ | ✓ | — |
| **4 Development** | 见 4.9 特殊判定 | | | | |
| 5 Testing | Test Preparation + Procedure + Report | ✓ | ✓ | — | Test Report `status: pass`（fail → Bug Flow）|
| 6 Delivery | Deployment + Operation Manual + Installation Result | ✓ | ✓ | — | Installation 执行成功 |
| 7 Retrospective | Issue Report + Improvement Proposals | ✓ | ✓ | — | — |

### 4.9 Stage 4 特殊判定（按 task 维度）

```
Stage 4 done ⇔ all task_states[Tn] == "verified"
```

每 task 子状态：

| 子状态 | 满足条件 |
|--------|---------|
| `planning-done` | Detailed Design (Tn) 通过 doc-guardian + review approved |
| `test-done` | Unit Tests + Integration Tests (Tn) 通过 doc-guardian + review approved |
| `code-done` | Source Code (Tn) 文件存在（**无 review 配对**） |
| `verified` | Tn 的 unit + integration test 全部 pass（`development-code-write` 跑测试，写 Local Verification Result）|

**注**：workflow-protocol 不直接跑测试，只读 verification artifact 的 status 字段。

### 4.10 Bug Flow 触发

Stage 5 E 失败（Test Report `status: fail`）→ 不推进 Stage 6，进入 Bug Flow：

1. workflow-protocol 设 `bug_flow.active = true`，记录 `bug_report_path` 和 `root_cause`（由 bug-triage skill 输出）
2. `current_stage` 切到 root_cause 对应的 stage（Change Mode）
3. 该 stage Change Mode 的 done 条件 = "影响范围内的 artifacts 重新通过 A/B/C/D/E"
4. 完成后自动回到 Stage 5 重测（不是正常推进）
5. Pass 后 `bug_flow.active = false`，正常推进 Stage 6

### 4.11 关键约定

- **Verification artifact** 必含 `verification_status: pass | fail | partial`
- **Required vs Optional artifacts** 由 doc-guardian 集中声明（`doc-guardian/references/required-artifacts.md`）
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
│   │       └── feature_matrix.md         # S3 必备
│   │
│   ├── architecture/                     # 项目级
│   │   └── architecture.md               # 主架构（含 Pending + Change Log）
│   │
│   ├── release0.1/                       # 第 1 个 release
│   │   ├── srs/
│   │   │   ├── srs.md                    # 唯一 SRS（含 Pending + Change Log）
│   │   │   ├── acceptance_plan.md
│   │   │   └── integration_plan.md       # 多模块时
│   │   ├── architecture_delta.md         # 本 release 引发的架构变更（如有）
│   │   ├── development/
│   │   │   ├── plan.md
│   │   │   ├── breakdown.md
│   │   │   └── tasks/
│   │   │       ├── T1/
│   │   │       │   ├── detailed_design.md
│   │   │       │   └── verification_result.md
│   │   │       └── T2/
│   │   │           └── ...
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

- **Doc 文件**：lowercase + underscore + `.md`（如 `prd.md`、`acceptance_plan.md`）
- **CR / Bug Reports**：ID 大写格式 `CR-001.md`、`BUG-005.md`
- **不带 `_claude` 后缀**（早期约定已废弃）
- **Task 子目录**：`T1/`、`T2/` 大写 + 数字
- **Release 目录**：`release0.1/`、`release0.2/`（lowercase + 版本号）

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
| `draft` | 写作中（write skill 输出但未评审）| 全部 doc |
| `in-review` | review skill 正在评审 | 全部 doc |
| `revising` | 收到 review 反馈在修订中 | 全部 doc |
| `review-passed` | AI review 通过（**最终态：非 gated 文档**）| 全部 doc |
| `approved` | 人确认通过（**最终态：仅 PRD/SRS/Architecture**）| 仅 gated 文档 |

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
| `verification-result` | `docs/release0.x/development/tasks/Tn/verification_result.md` | `release`, `task_id`, **`verification_status`** |
| `test-preparation` | `docs/release0.x/testing/preparation.md` | `release` |
| `test-procedure` | `docs/release0.x/testing/procedure.md` | `release` |
| `test-report` | `docs/release0.x/testing/report.md` | `release`, **`verification_status`**, `total_test_cases`, `passed`, `failed` |
| `deployment-doc` | `docs/release0.x/delivery/deployment.md` | `release` |
| `operation-manual` | `docs/release0.x/delivery/operation_manual.md` | `release` |
| `installation-result` | `docs/release0.x/delivery/installation_result.md` | `release`, **`verification_status`** |
| `cr` | `docs/cr/CR-NNN.md` | `cr_id`, `target_release`, `affected_doc` |
| `bug-report` | `docs/bug/BUG-NNN.md` | `bug_id`, `found_in_release`, `target_release`, `root_cause` |

#### 5 个示例 Frontmatter

**PRD**（最简）：

```yaml
---
title: MyApp Product Requirements
type: prd
status: approved
created: 2026-05-04T08:00:00Z
updated: 2026-05-15T10:00:00Z
owner: claude-opus-4-7/prd-write
---
```

**SRS**：

```yaml
---
title: MyApp v0.1 SRS
type: srs
status: in-review
created: 2026-05-05T09:00:00Z
updated: 2026-05-06T14:30:00Z
owner: claude-opus-4-7/srs-write
release: "0.1"
---
```

**Verification Result**（带 `verification_status`）：

```yaml
---
title: T2 Verification Result
type: verification-result
status: review-passed
created: 2026-05-08T12:00:00Z
updated: 2026-05-08T12:00:00Z
owner: claude-opus-4-7/development-code-write
release: "0.1"
task_id: T2
verification_status: pass
---
```

**CR**：

```yaml
---
title: CR-001 Add user 2FA
type: cr
status: approved
created: 2026-05-12T10:00:00Z
updated: 2026-05-12T15:00:00Z
owner: claude-opus-4-7/srs-write
cr_id: CR-001
target_release: "0.2"
affected_doc: docs/release0.2/srs/srs.md
---
```

**Bug Report**：

```yaml
---
title: BUG-005 Login token expires too quickly
type: bug-report
status: in-review
created: 2026-05-10T08:00:00Z
updated: 2026-05-10T11:00:00Z
owner: claude-opus-4-7/testing-write
bug_id: BUG-005
found_in_release: "0.1"
target_release: "0.1"
root_cause: development
---
```

#### 格式约定

- **Timestamps**：ISO8601 UTC（`2026-05-15T10:00:00Z`）
- **Release**：YAML 加引号字符串 `"0.1"` `"0.2"` `"1.0"`
- **ID**：CR 用 `CR-NNN`、Bug 用 `BUG-NNN`、task 用 `Tn`，全文件名一致
- **可空字段**：用 `null`，不省略字段
- **路径引用**：相对项目根 forward slash 路径

### 5.4 F4: 必需章节 — Skipped

每个 doc 类型的 body 章节由对应的 write/review skill pair 协调（共享 sections 列表）。doc-guardian 不强制 body 章节结构，只校验 doc infrastructure（路径、命名、frontmatter、change log）。

### 5.5 F5: validate.py 8 类校验

| # | 类别 | 检查内容 | 失败示例 |
|---|------|---------|---------|
| 1 | **Path** | doc 文件路径符合该 type 的目录规则 | `type: srs` 但文件在 `docs/prd/`：fail |
| 2 | **Naming** | 文件名符合 convention | `Acceptance_Plan.md` 含大写：fail |
| 3 | **Frontmatter Schema** | universal 5 字段全在 + per-type 扩展字段全在 + status/type 是合法 enum | 缺 `created` 字段：fail |
| 4 | **Frontmatter Format** | timestamp 是 ISO8601 UTC、release 是 `"x.y"` 字符串、owner 是 `agent/skill` 格式、ID 是 `CR-\d+` / `BUG-\d+` | `release: 0.1`（不带引号）：fail |
| 5 | **Cross-Reference** | frontmatter 里的路径字段指向真实存在的文件 | `affected_doc` 指向不存在文件：fail |
| 6 | **Change Log Discipline** | `## Pending Changes` 章节为空 + `## Change Log` 章节 entry 符合格式 | Pending Changes 还有未 promote 的 entry：fail |
| 7 | **ID Uniqueness** | `docs/cr/` 下 CR-NNN 不重复，`docs/bug/` 下 BUG-NNN 不重复 | 两个 `CR-005.md`：fail |
| 8 | **Consistency with progress.md** | doc 的 `status` 字段和 progress.md 当前 stage/sub_state 兼容 | 状态不兼容：fail |

#### 子命令

```bash
validate.py file <doc-path>      # 单文件 check（1-7）
validate.py all                   # 整个 docs/ 目录
validate.py consistency           # 类 8 cross-file（按需，stage advance 前调）
validate.py ids                   # 仅 ID 唯一性
```

`progress.py update` 内部默认调 `validate.py file <changed-doc>`；类 8 一致性 check 仅 stage advance 前跑一次。

### 5.6 F6: doc-guardian 物理结构

```
skills/doc-guardian/
├── SKILL.md                       主协议（~200-300 行）
├── references/
│   ├── directory-layout.md        F1 全文：目录树 + 各 type 路径规则
│   ├── frontmatter-schema.md      F3 全文：universal + 各 type 字段表 + 模板
│   ├── change-log-format.md       Pending Changes 和 Change Log 严格格式 + 示例
│   └── required-artifacts.md      P6 配套：每 stage required vs optional artifact 清单
└── scripts/
    ├── validate.py                F5 主校验（8 类 check, 4 个子命令）
    └── changelog.py               promote / validate Pending Changes
```

无 `templates/` 子目录——模板内嵌在 `references/frontmatter-schema.md`。Body section 模板由各 skill 自管。

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
<!-- AI 写新变更进这里，格式严格 -->
- 2026-05-15T10:00:00Z [Section 3.2]: 新增用户认证需求
- 2026-05-15T10:30:00Z [Section 1.3]: 精简产品边界描述

## Change Log
<!-- 脚本自动从 Pending Changes 移过来 -->

### 2026-05-10
- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建
```

#### Pending Changes 严格格式

```
- {ISO8601 UTC timestamp} [{section_ref}]: {one_line_summary}
```

非此格式的 entry 脚本拒绝处理 → block。

#### scripts/changelog.py promote 行为

1. 读取目标 doc，找 `## Pending Changes` 章节
2. 校验每条 entry 符合严格格式
3. 按日期分组（同一天合并到 `### YYYY-MM-DD` 块）
4. 插入 `## Change Log` 章节顶部（最新日期在最上）
5. 清空 `## Pending Changes`（保留章节标题，body 为空）
6. 写回文件（atomic：备份 + 写入 + 校验）

#### 强制纪律

`validate.py` 检查 `## Pending Changes` 章节必须为空，否则 exit 1。
意味着 AI 编辑完 doc → 必须运行 `changelog.py promote` 移走 pending → 然后 validate 才会通过 → workflow-protocol 才允许 stage 推进。

#### *-write skill 标准 4 步流程

```
1. 生成/修改 doc 主体内容
2. 在 ## Pending Changes 章节加新 entry（按严格格式）
3. 运行 changelog.py promote（移走 pending）
4. 自评（调 doc-guardian validate.py）
5. 自修复
6. 提交给 *-review skill
```

第 3 步仅对增量类 doc 适用（PRD / Architecture / Retrospective / SRS / CR / Bug Report 等）。

---

## 6. AGENTS.md Template (Task 3)

部署说明：本 template 由 `scenario-dispatcher` 在新项目初始化时拷贝到项目根，并做项目特定的轻微定制（如 `Section 8` 的项目名）。skill 仓库内 template 物理位置等 Task 6 实现时确定。

### 6.1 完整 Draft

```markdown
# AGENTS.md

<!-- 任何使用 dev-workflow-skills2 工作流的项目里，agent 第一步必读本文件 -->

## 1. Authority Hierarchy

规则冲突时按以下优先级（数字越小权威越高）：

1. `skills/workflow-protocol/SKILL.md` — 操作协议（状态机、must-call 规则）
2. `AGENTS.md` — 本文件（治理、约定）
3. `skills/doc-guardian/SKILL.md` — 文档合规（路径、命名、frontmatter、change log）
4. 当前 stage skill 的 `SKILL.md` — 任务级指令
5. 用户在当前对话中的指令 —— 在以上规则范围内有效，**不能突破硬约束**

## 2. Bootstrap Protocol

任何新会话/新任务起手按顺序：

1. （如果 `AGENTS.md` 通过 `@` 已自动加载，本步已完成）
2. 读 `skills/workflow-protocol/SKILL.md`
3. 跑 `scripts/progress.py query` 读取当前 state
4. 从 state 判定：scenario (S1/S2/S3/S4)、`current_stage`、`sub_state`、`release`、`bug_flow.active`
5. 如果 `scenario` 未设 → invoke `scenario-dispatcher`；如果 `bug_flow.active=true` → invoke `bug-triage`
6. 找到当前 state 对应的 skill，读它的 `SKILL.md`
7. 开始干活

## 3. Skill Catalog (22 skills, 4 layers)

### Layer 1: Vertical Stage Skills (17 个)

| Skill | Stage | 角色 |
|-------|-------|------|
| `prd-write` / `prd-review` | 1 | PRD + supporting artifacts |
| `srs-write` / `srs-review` | 2 | SRS + Acceptance Plan + Integration Plan |
| `architecture-write` / `architecture-review` | 3 | Architecture（含 release 引发的 architecture_delta） |
| `development-planning-write` / `development-planning-review` | 4 | Plan + Breakdown + Detailed Design |
| `development-test-write` / `development-test-review` | 4 | Unit Tests + Integration Tests（测试代码） |
| `development-code-write` | 4 | Source Code（**无 review 配对**，靠测试验证质量） |
| `testing-write` / `testing-review` | 5 | Test Preparation + Procedure + Report |
| `delivery-write` / `delivery-review` | 6 | Deployment Doc + Operation Manual + Installation Result |
| `retrospective-write` / `retrospective-review` | 7 | Project Retrospective（项目级，每 release 增量加节） |

### Layer 2: Cross-cutting (2 个)

- `workflow-protocol` — 状态机、转换、progress 管理（`scripts/progress.py`）、评审循环计数、must-call 规则
- `doc-guardian` — 目录结构、命名、frontmatter、change log 规范、binary 校验（`scripts/validate.py`、`scripts/changelog.py`）

### Layer 3: Orchestration (2 个)

- `scenario-dispatcher` — 项目入口判定 S1/S2/S3/S4，路由到对应工作流入口
- `bug-triage` — bug 根因分类（SRS / Architecture / Development / PRD-异常），路由到对应 stage 的 Change Mode

### Layer 4: Meta (1 个)

- `workflow-evolution` — 消化 Stage 7 retrospective + PRD 根因异常输入，提出 workflow / skill / template 改进建议

## 4. Project Conventions

- **语言**：英文用于 skill 名 / 文件路径 / frontmatter / 技术术语；中文用于描述和说明
- **Doc filenames**：lowercase + underscore + `.md`（如 `prd.md`、`acceptance_plan.md`）；CR/Bug 用 ID 大写格式 `CR-001.md`、`BUG-005.md`
- **Timestamps**：一律 ISO8601 UTC（`2026-05-15T10:00:00Z`）
- **Release versions**：YAML 中必须加引号字符串 `release: "0.1"`
- **Directory structure**：见 `skills/doc-guardian/references/directory-layout.md`
- **Frontmatter schema**：见 `skills/doc-guardian/references/frontmatter-schema.md`
- **Change Log**：通过 `skills/doc-guardian/scripts/changelog.py promote` 管理；不要直接编辑 Change Log 章节
- **Review iteration cap**：7 次；超过 → 升级人介入（详见 workflow-protocol）

## 5. State Files

项目根下脚本管理的文件（**禁止手工编辑**）：

- `progress.md` — 当前 workflow state（YAML frontmatter + body + Recent Activity）
- `progress-history.md` — append-only 全量日志
- `.progress.lock` — 原子更新用文件锁

配置文件：

- `AGENTS.md` — 本文件
- `CLAUDE.md` — 仅含 `@AGENTS.md` 一行 import

## 6. Forbidden Actions

- 手工编辑 `progress.md` —— 必须用 `scripts/progress.py update`
- 直接编辑 Change Log 章节 —— 必须用 `scripts/changelog.py promote`
- doc 完成前不跑 `validate.py` —— 必须 exit 0 才能 declare done
- stage 推进不调 `scripts/progress.py update --advance` —— workflow-protocol 会校验 done 条件
- 在 workflow-protocol 内部跑 unit/integration tests —— workflow-protocol 只读 `verification_status` 字段；测试由 `development-code-write` 执行
- 在 `doc-guardian/references/directory-layout.md` 定义之外的目录创建 doc 文件
- 从 doc 类 skill 修改 `src/` 或 `tests/` —— 那是 doc-guardian 范围之外

## 7. Recursion Notice

`dev-workflow-skills2` skill 集**禁止**作用于 `dev-workflow-skills2` 自身。本 skill 集应用于**其他项目**。自我应用会产生递归语义悖论（用本 skill 集设计本 skill 集），参考 v1 D-003 / D-006 经验。

## 8. Workflow Specification Reference

本 skill 集实现 `docs/workflow/workflow_specification_claude.md`（skill 仓库）中定义的工作流。每个项目的 `progress.md` 的 `workflow_version` 字段记录其遵循的版本；当前版本是 `v0.2`（2026-05-05）。

## 9. Where to Find Things

| 我想知道... | 去哪里看 |
|------------|---------|
| 项目当前 state | `progress.md` 或 `scripts/progress.py query` |
| 历史所有动作 | `progress-history.md` |
| Workflow spec 定义 | `docs/workflow/workflow_specification_claude.md`（skill 仓库）|
| Doc 目录布局 | `skills/doc-guardian/references/directory-layout.md` |
| 各 skill 干什么 | 上面 Section 3 + 各 skill 的 `SKILL.md` |
| 允许 / 禁止做什么 | 上面 Section 6 + 各 skill 的 "Forbidden" 章节 |
| v1 当年踩过什么坑 | `docs/research/dev_workflow_skills_v1_design_claude.md` |

## 10. Scenarios Quick Reference

| Code | Name | 含义 |
|------|------|------|
| S1 | New Product | 从 0 打造一个新项目 |
| S2 | Feature Evolution | 在已规范化的项目上新增需求（每次新需求就是新 release） |
| S3 | Product Reconstruction | 把已存在的外部项目按本规范重建为新项目 |
| S4 | Bug Fix | 修复已规范化项目中的 bug |
```

---

## 7. Pending Work

### 7.1 Task 5: 23 个 Skill 的 SKILL.md 骨架

按 3 批展开：

**批 1（关键基础设施）**：
- `workflow-protocol` 完整 SKILL.md（含 references/scripts 详细规范）
- `doc-guardian` 完整 SKILL.md（含 validate.py / changelog.py 行为）

**批 2（Orchestration + Meta，5 个）**：
- `scenario-dispatcher` — 4 场景判定逻辑
- `bug-triage` — 4 类根因分类逻辑
- `workflow-evolution` — Retrospective + PRD-exception 消化逻辑

**批 3（Vertical 17 个）**：
- 7 个 stage 的 write/review skill pair（Stage 4 拆 5 个）
- 模板化程度高，可批量产出

### 7.2 Task 6: Implementation

按物理结构落地实际文件：

```
dev-workflow-skills2/
├── AGENTS.md.template                    # 给目标项目用
├── CLAUDE.md.template                    # @AGENTS.md
├── skills/                               # 真实 skill 源（vendor-neutral）
│   ├── workflow-protocol/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   ├── scripts/progress.py
│   │   └── ...
│   ├── doc-guardian/
│   │   ├── SKILL.md
│   │   ├── references/
│   │   └── scripts/{validate.py, changelog.py}
│   ├── prd-write/SKILL.md
│   ├── prd-review/SKILL.md
│   └── ...（22 个 skill 全部）
├── .claude/
│   └── skills/ → ../skills/             # symlinks 暴露给 Claude Code
├── .agents/
│   └── skills/ → ../skills/             # symlinks 暴露给其他 vendor
└── docs/                                # 已有
    ├── workflow/
    ├── research/
    └── design/                          # 本文档所在
```

---

## 8. Decision Log

### 2026-05-05

- ✅ Workflow spec v0.2（merge 三份草案）
- ✅ 4 层 skill 架构 + 22 skill 总数
- ✅ Foreman 模式（write/review 拆分）
- ✅ Stage 4 拆 3 组（planning / test / code）
- ✅ 评审循环 cap = 7
- ✅ D1 Foreman binary 校验
- ✅ D2 CLAUDE.md = `@AGENTS.md` + AGENTS.md + workflow-protocol
- ✅ D3 不要 SessionStart Hook
- ✅ D4 vendor-neutral skill 结构（双 symlink）
- ✅ D5 不做 Risk-based review v1
- ✅ Q1 评审超 7 升级人介入
- ✅ Q2 cr-guardian 合并进 doc-guardian
- ✅ Q3 不独立 project-memory-manager
- ✅ workflow-protocol 责任精简到 5 项
- ✅ progress.md / progress-history.md schema 与格式
- ✅ scripts/progress.py 4 个子命令 + 原子更新流程
- ✅ 并发模型：统一 update 接口（Option B）+ lock
- ✅ 两层粒度：progress.md = task 级，history = 子任务级
- ✅ P6 完成判定矩阵 4-5 维 + Stage 4 特殊处理
- ✅ Release 版本化结构
- ✅ doc 文件不带 `_claude` 后缀
- ✅ PRD 文件名 = `prd.md`（generic）
- ✅ change_log 章节 + 自动化（Pending Changes + scripts/changelog.py promote）
- ✅ Frontmatter 5 universal 字段
- ✅ Status 5 状态：draft / in-review / revising / review-passed / approved
- ✅ owner = `<agent>/<skill>` 格式
- ✅ doc-guardian 不强制 body 章节
- ✅ validate.py 8 类 check + 4 个子命令
- ✅ AGENTS.md 10-section template
- ✅ Recursion notice（不自我应用）

---

**End of Proposal v0.1**
