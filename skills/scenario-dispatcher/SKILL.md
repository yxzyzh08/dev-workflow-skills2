---
name: scenario-dispatcher
description: dev-workflow-skills2 场景路由 orchestration skill。在 progress.md scenario 字段未设（首次新建项目 / release_state==closed 后用户提新需求）时由 AGENTS.md Bootstrap 调用，判定 S1 (New Product) / S2 (Feature Evolution，含 S2-1/2/3/4 子场景) / S3 (Reconstruction) / S4 (Bug Fix)，并调对应 progress.py 子命令（init / release-start）或路由到 bug-triage / workflow-evolution。S4 仅 active release 期间允许；post-close bug 必须走 bug-triage post-close mode。本 skill 不直接 mutation progress.md，不分 bug 根因，不写任何 doc body。
authority: 4
references:
  - references/scenario-decision-tree.md
---

# scenario-dispatcher

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` 简写指代脚本；**实际 invocation 必须用完整路径** `skills/workflow-protocol/scripts/progress.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（与 stage skill / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（5 项）**：

1. 检测项目入口 state（项目根有无 progress.md / `project_state` / `release_state` / `bug_flow.active` / `workflow_incident_active`）
2. 判定主场景：S1 / S2 / S3 / S4
3. 判定 S2 子场景：S2-1 / S2-2 / S2-3 / S2-4（含 S2-4 转 S3 的特殊路径）
4. 校验 S4 active-release 约束（仅 `release_state==active` 期间允许）
5. 路由：调 `progress.py init` / `release-start` 或 invoke `bug-triage` / `workflow-evolution`

**不属于本 skill**：

- 直接 mutation `progress.md` / `progress-history.md` → 全部走 `workflow-protocol` 的 `progress.py`
- 分类 bug 根因（srs / architecture / development / prd-exception）→ `bug-triage`
- 写任何 doc body（PRD / SRS / Architecture / BUG report / INCIDENT report）→ 对应 stage skill 或 orchestration skill
- 评审任何产物 → 对应 `*-review` skill
- workflow incident 分析与 resolution → `workflow-evolution`

## 2. When to Invoke

| 时机 | 由谁调用 | 期望输出 |
|------|---------|---------|
| 首次会话且项目根**无** `progress.md` | AGENTS.md Bootstrap 第 5 步检测到 | 决定 S1 / S3 → 调 `progress.py init --project <name> --scenario <S1\|S3> --release <x.y>` |
| `progress.md` 存在但 `scenario` 字段缺失或 schema 损坏 | AGENTS.md Bootstrap 第 5 步 | **拒绝 dispatch**；提示用户调 `progress.py recover --confirm` 修复 |
| `release_state==closed` 期间用户提**新需求** | AGENTS.md Bootstrap 第 5 步 + 用户对话 | 判定 S2 子场景 / S3 / 路由 bug-triage post-close mode |
| `release_state==active` 期间用户提**整体重构 / 改产品方向** | AGENTS.md Bootstrap 检测到与 active scenario 矛盾 | **拒绝**；提示用户：(a) 完成当前 release 再起新；(b) 走 incident path（`incident-start` / `incident-resolve abort\|reconstruct`） |

**不会被 invoke 的时机（必须直接由其他 skill 接管）**：

- `release_state==active` 期间正常推进 stage：scenario 已锁定，dispatcher 不参与；调用方应直接路由到 `current_stage` 对应的 stage skill
- `release_state==active` 且 `bug_flow.active==true`：已在 Bug Flow 内 → `bug-triage` active mode 或对应 stage skill
- `workflow_incident_active==true`：→ `workflow-evolution`
- `project_state ∈ {aborted, reconstructing}`：终态，禁止任何 dispatch

## 3. Decision Flow Overview

完整决策树（含 heuristic 问句、example、edge cases）见 `references/scenario-decision-tree.md`。本节为高层概要。

```
invoke scenario-dispatcher
  ↓
读 progress.py query
  ↓
分支 1：progress.md 不存在
        ↓
        与用户对话：「从 0 打造新产品」 vs 「重构外部系统」？
          ├ 新产品 → S1 → invoke project-init（传 --scenario S1）
          │           → project-init 跑 templates cp + placeholder 替换 + progress.py init
          └ 重构 → S3 → 要求用户提供源系统 PRD/SRS → invoke project-init（传 --scenario S3）
                 → 提示后续 Stage 1/2 必备 source-system-analysis artifacts
                 （事实源 skills/project-init/SKILL.md §3；本 dispatcher 不直接调 progress.py init）

分支 2：progress.md 存在
        ↓
        2a. project_state ∈ {aborted, reconstructing}
            → 拒绝；提示起新 project（独立目录）
        2b. workflow_incident_active==true
            → invoke workflow-evolution（结束本 dispatch）
        2c. bug_flow.active==true
            → invoke bug-triage active mode（结束本 dispatch）
        2d. release_state==active
            ├ 用户提：继续当前 stage → 路由当前 stage skill（dispatcher 不介入）
            ├ 用户提：报新 bug（非 testing 触发）
            │     ├ current_stage==testing AND sub_state==review-passed
            │     │   → 提示用户先创建 BUG report → invoke bug-triage active mode
            │     └ 其他 stage / sub_state（v0.6 round 2 batch2-F2）
            │       → 拒绝；解释 bug-start 前置（current_stage==testing AND sub_state==review-passed）
            │         提示路径：(a) 等本 release 推进到 testing 阶段由 testing-write 自动发现；
            │                  (b) 当前现象作为 known-issue 在用户笔记 / 当前 stage doc 注记
            └ 用户提：整体重构 / 改产品方向
                → 拒绝；提示走 release-close（正常）或 incident-resolve abort/reconstruct（异常）
        2e. release_state==closed
            ├ 用户提：新需求（功能/SRS 修改）→ S2 子场景判定（§4）
            │    → progress.py release-start --version <x.y> --scenario <S2-1|S2-2|S2-3>
            ├ 用户提：PRD 重构级变更 → S2-4 → 拒绝在本 project 继续，提示起新 S3 project
            └ 用户提：报 bug → invoke bug-triage post-close mode
```

## 4. S2 Sub-scenario Routing

仅适用于 `release_state==closed` 且用户提"非 bug 类"新需求。

| 子场景 | 适用条件 | 入口 Stage | 命令 |
|--------|---------|-----------|------|
| S2-1 | PRD 变更引入新功能（产品边界微调，但产品形态/技术栈不变）| `prd-inception`（Change Mode）| `progress.py release-start --version <x.y> --scenario S2-1` |
| S2-2 | PRD 不变，**新增**模块/功能的 SRS | `srs-specification`（Full Mode for new SRS sections）| `progress.py release-start --version <x.y> --scenario S2-2` |
| S2-3 | PRD 不变，**修改**现有 SRS | `srs-specification`（Change Mode）| `progress.py release-start --version <x.y> --scenario S2-3` |
| S2-4 | PRD **重构级**变更（产品形态 / 技术栈 大改）| 不进入 S2 流程 | **拒绝 release-start**；提示起新 S3 project |

**判定 heuristic**（详见 `references/scenario-decision-tree.md` §S2 Decision Tree）：

| # | 关键问句 | Yes → | No → |
|---|---------|------|------|
| Q1 | PRD 是否需要改写**产品定位 / 用户故事 / 关键功能集**？ | 进 Q2 | 进 Q3 |
| Q2 | 是否影响现有架构骨架（**技术栈替换 / 重大架构重写**）？ | **S2-4**（转 S3 新 project）| **S2-1** |
| Q3 | 现有 SRS 是否需要**修改**？ | **S2-3** | **S2-2** |

**模糊情况处理原则**：dispatcher 无把握时**不要猜**，列出 2-3 个候选场景 + 对应路径让用户选。

## 5. S4 Active-Release Constraint

S4 (Bug Fix) 仅在 `release_state==active` 期间触发。两种入口路径区分：

### 5.1 active-release 期间报 bug（S4 合法）

不一定经 dispatcher。三种情况：

- **Stage 5 testing 自动发现**：testing-write 创建 BUG report → 直接 invoke `bug-triage` active mode（dispatcher 不介入）
- **用户在 testing 阶段主动报**（current_stage==testing AND sub_state==review-passed）：dispatcher 检测到用户输入是 bug 描述 → 提示用户先创建 BUG report skeleton → invoke `bug-triage` active mode
- **用户在非 testing 阶段主动报**（v0.6 round 2 batch2-F2 收敛）：**dispatcher 拒绝**进入 bug-triage active mode；理由：`progress.py bug-start` 前置要求 `current_stage==testing AND sub_state==review-passed`，dispatcher 不绕过该约束。提示用户：(a) 等本 release 推进到 testing 阶段由 testing-write 自动发现并 triage；(b) 把当前现象写到当前 stage 的相关 doc（如 detailed_design 的 known-issue 段）作笔记；**不**创建 orphan BUG report、不调任何 progress.py 子命令

### 5.2 closed-release 期间报 bug（post-close path）

- dispatcher 判定为 post-close bug → invoke `bug-triage` **post-close mode**
- bug-triage post-close mode 创建 `docs/bug/BUG-NNN.md`（`target_release: null`）+ 调 `progress.py bug-intake --bug <path>`
- **不**触发 release-start；bug 进 `unresolved_bugs` 队列等下次 release-start 时由 srs-write 合并到新 SRS

**禁止**：closed-release 期间使用 S4 / 调 `progress.py bug-start`。dispatcher 必须 reject 并解释正确路径（post-close mode）。

## 6. Output Contract

scenario-dispatcher **不直接 mutation** `progress.md` / `progress-history.md`。本 skill 的"输出"是以下三类之一：

### 6.1 Type A: 调 progress.py 子命令 / project-init skill

| 决策结果 | 入口 |
|---------|------|
| S1 首次新建 | invoke `skills/project-init/SKILL.md`（传 `--scenario S1`；project-init 内部完成 templates cp + placeholder 替换 + 调 `progress.py init`）|
| S3 首次新建 | invoke `skills/project-init/SKILL.md`（传 `--scenario S3`）；调 project-init 之前 dispatcher 与 user 确认源系统 PRD/SRS 路径或内容 |
| S2-1 / S2-2 / S2-3 启新 release | `skills/workflow-protocol/scripts/progress.py release-start --version <x.y> --scenario <S2-1\|S2-2\|S2-3>` |

**为什么 S1 / S3 走 project-init 而非直接 progress.py init**（v0.7 / Phase 7 Task 7-C 决议）：`progress.py init` 仅创建 `progress.md` / `progress-history.md`；新 project 还需要 `AGENTS.md` / `CLAUDE.md` / `README.md` / `docs/` 骨架（事实源 `skills/doc-guardian/references/directory-layout.md §1`）。`project-init` 是新 orchestration skill，把 templates 拷贝 + placeholder 替换 + `progress.py init` 串成原子 bootstrap 流程；dispatcher 只负责场景判定，不重复 bootstrap 逻辑。S2-x 的 `release-start` 不创建新 project root，沿用既有 dir，所以仍直接调 progress.py 子命令。

### 6.2 Type B: 路由到其他 skill

| 决策结果 | 路由到 |
|---------|-------|
| `bug_flow.active==true` 已存在（dispatcher 检测到，无需重新 dispatch）| `bug-triage` active mode |
| `workflow_incident_active==true` | `workflow-evolution` |
| active-release 期间用户在 **testing** 阶段（`current_stage==testing AND sub_state==review-passed`）主动报 bug | `bug-triage` active mode（先与用户确认 bug 描述并提示创建 BUG report skeleton）|
| closed-release 期间用户报 bug | `bug-triage` post-close mode |

### 6.3 Type C: 拒绝并提示用户走正确路径

| 触发条件 | 提示内容 |
|---------|---------|
| `project_state ∈ {aborted, reconstructing}` | 当前 project 已终态；起新 project（独立目录、独立 progress.md） |
| `release_state==active` 期间用户提整体重构 | 先完成当前 release（走 Stage 7 → `release-close`），或走 `incident-start` → `incident-resolve abort\|reconstruct` |
| **`release_state==active` 但 `current_stage != testing`（或 `sub_state != review-passed`）期间用户主动报 bug**（v0.6 round 2 batch2-F2）| 拒绝；解释 `progress.py bug-start` 前置；提示路径：(a) 等本 release 推进到 testing 阶段由 testing-write 自动发现并 triage；(b) 把现象写到当前 stage doc 的 known-issue 段作笔记；**不**创建 orphan BUG report |
| `release_state==closed` 期间用户提 S4 / `bug-start` | 改用 bug-triage post-close mode（`bug-intake`） |
| S2-4（PRD 重构级变更）| 不能在本 project 内继续；起新 S3 project |
| `progress.md` 损坏（schema 不合法 / 关键字段缺失）| 调 `progress.py recover --confirm` |

## 7. S3 Special Handling

S3 (Product Reconstruction) 在 init 之前有两个特殊要求：

### 7.1 用户必须提供源系统资料

dispatcher 在调 `progress.py init --scenario S3` 前与用户确认：

- 源系统 PRD（路径或内容）
- 源系统 SRS（路径或内容）

缺失时**不允许 init**；提示用户先准备这两份 doc 再回来。

### 7.2 提示后续 Stage 1/2 必备源系统分析 artifacts

dispatcher init 完成后告知用户后续 Stage 1/2 强制要求（事实源 `skills/doc-guardian/references/required-artifacts.md`）：

- **Stage 1（2 必备）**：
  - `source-system-analysis`（`analysis_kind: prd-level`）→ `docs/prd/supporting/source_product_prd_analysis.md`
  - `source-system-analysis`（`analysis_kind: feature-matrix`）→ `docs/prd/supporting/feature_matrix.md`
- **Stage 2（3 必备 + 1 推荐）**：
  - `source-system-analysis`（`analysis_kind: srs-level`）→ 必备
  - `source-system-analysis`（`analysis_kind: module-level`）→ 必备
  - `source-system-analysis`（`analysis_kind: reuse-replace`）→ 必备
  - `source-system-analysis`（`analysis_kind: technical-debt`）→ 推荐非必备

dispatcher 不创建这些 doc（由后续 prd-write / srs-write 负责），只是**提醒用户**这是 S3 后续硬约束。

## 8. Concurrency & Idempotency

- dispatcher 是**只读 + 路由**逻辑，**不持有** `.progress.lock`
- 实际 mutation 由下游 `progress.py init` / `release-start` / `bug-intake` 等子命令内部 flock 串行化
- dispatcher 决策**不持久化**：每次 invoke 重新 `progress.py query`
- 行为 **idempotent**：相同 (progress.md state, 用户输入) → 相同决策

**重复 invoke 防护**：dispatcher 进入时若检测到 `scenario` 字段已设且 `release_state==active`（即已在某 release 中），应**跳过**重新 dispatch（除非用户输入是"整体重构 / 改方向"，按 §6.3 拒绝）。避免在同一 active release 内重复 init / release-start。

## 9. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必须经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 在 `release_state==closed` 期间允许 S4 / 调 `skills/workflow-protocol/scripts/progress.py bug-start`（必须走 `bug-intake`）
- ❌ 在 `release_state==active` 期间重新 dispatch 已锁定的 scenario（同一 release 内 scenario 不变）
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时 dispatch 任何场景（必须起新 project）
- ❌ 在 `bug_flow.active==true` 时 dispatch（已在 Bug Flow 内，应让 `bug-triage` 接管）
- ❌ 在 `workflow_incident_active==true` 时 dispatch（应让 `workflow-evolution` 接管）
- ❌ 自行判定 bug 根因（必须 invoke `bug-triage`）
- ❌ S2 子场景判定不确定时**猜**（必须列候选让用户选）
- ❌ S3 init 前不要求用户提供源系统 PRD/SRS
- ❌ 跳过 schema 损坏检测直接 dispatch（progress.md 异常时必须先 `recover`）
- ❌ 调用 `progress.py init --scenario S2` 或 `--scenario S4`（init 仅接 S1 / S3；S2 走 release-start；S4 不存在 init 入口）
- ❌ S1 / S3 首次新建时直接调 `skills/workflow-protocol/scripts/progress.py init`（必须经 `skills/project-init/SKILL.md`，让其完成 templates cp + placeholder 替换 + init 串行流程）
- ❌ **在 `release_state==active` 但 `current_stage != testing` 或 `sub_state != review-passed` 时把用户主动报的 bug 路由到 `bug-triage` active mode**（v0.6 round 2 batch2-F2）：`progress.py bug-start` 前置必然 reject；不要创建 orphan BUG report、不要绕过状态机；统一拒绝 + 提示用户等 testing 阶段或在当前 stage doc 注记

## 10. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| `progress.py query` 报错（progress.md schema 损坏 / 缺失关键字段）| 调 `progress.py recover --confirm` 从 history 重建；recover 失败则升级人介入 |
| 用户输入意图不明确（如 "加点东西"）| 拒绝 dispatch；列 S2-1 / S2-2 / S2-3 例子 + S4 (bug) 选项让用户选 |
| 用户在 active release 期间提"整体重构" | 解释路径：(a) 完成当前 release 走 `release-close` 再起新 S2/S3；(b) 如果是 PRD 异常，由 testing 触发 → bug-triage → `incident-start` |
| S2-4 误判（用户实际想 S2-1）| 在调 `progress.py init`（新 S3 project）**前**与用户二次确认；S2-4 一旦起新 project，回滚成本高 |
| 重复 invoke（同一 session 多次 dispatch）| 第二次起检测 `scenario` 已设 → 跳过；避免重复 `init` / `release-start` |
| `progress.py release-start` 校验失败（version 不严格大于 previous_releases）| 提示用户选更大 version；不要尝试改 progress.md previous_releases |
| 用户提供的源系统 PRD/SRS 路径不存在（S3）| 拒绝 init；要求用户先创建 / 提供有效路径 |

## 11. References

- `references/scenario-decision-tree.md` — 完整决策树 + S1 vs S3 判定 + S2 4 子场景 heuristic + edge cases
- `skills/project-init/SKILL.md` — S1 / S3 首次 bootstrap orchestration（templates cp + placeholder 替换 + progress.py init 串行）
- `skills/workflow-protocol/SKILL.md` — workflow-protocol 主协议
- `skills/workflow-protocol/references/command-reference.md` — `progress.py` 12 个子命令完整 mutation
- `skills/doc-guardian/references/required-artifacts.md` — S3 必备源系统分析 artifacts
- `docs/workflow/workflow_specification_claude.md`（项目级）— Workflow spec 4 场景定义
- `docs/design/skill_set_design_proposal_v0.5.md`（项目级）— 完整设计方案
