---
title: Product/Project R&D Workflow Specification
type: workflow-spec
status: Draft v0.6
owner: cgs
created: 2026-05-05
updated: 2026-05-05
sources:
  - workflow_specification_draft_claude.md (v0.1)
  - product_lifecycle_workflow_hermes.md
  - product-project-workflow-spec-draft_code.md
---

# Product/Project R&D Workflow Specification (产品/项目研发工作流规范)

## 1. Purpose & Scope (目的与范围)

dev-workflow-skills2 是一套面向个人使用的 R&D workflow skill 集合。本规范定义围绕单个 Product/Project 展开的研发流程，涵盖 4 个使用场景（Scenario）、统一的 7 阶段主流程（Main Lifecycle）、Stage Mode 规则、Bug Rollback Flow、Human Confirmation Gate、CR 规则与 Meta-Evolution Loop。

本规范为 high-level 框架定义，不展开每个 Stage 的内部子步骤、产物模板与具体 Skill 实现，这些将在主流程确认后逐项设计（见 §13 Open Items）。

---

## 2. Scenarios (使用场景)

| Code | Name | 描述 |
|------|------|------|
| S1 | New Product | 从 0 打造一个新的 Product/Project |
| S2 | Feature Evolution | 在已规范化的 Product/Project 上新增或变更需求 |
| S3 | Product Reconstruction | 已存在的 Product/Project 按本规范重建为新 Project，可复制/增强/裁剪原系统能力 |
| S4 | Bug Fix | 修复已规范化 Product/Project 中的 Bug；**仅在 active release 期间触发**（v0.4）。release close 后新发现的 bug 仅作为 intake record，等下次 S2 release 启动时合并。 |

**结构关系**：S1、S3 是项目"诞生"场景（任何项目从 S1 或 S3 开始）。S2、S4 是项目"运行期"反复发生的场景。

---

## 3. Core Principles (核心原则)

- **Lifecycle First**：先围绕完整 Product/Project Lifecycle 设计主流程，再拆分各 Stage Skill 与 Cross-cutting Skill，避免被局部细节牵走整体形态
- **Scenario-first Entry**：先判断属于哪个 Scenario，再决定走哪条流程入口
- **Artifact-driven**：每个 Stage 必须有明确的输入、输出与下游用途
- **Human Authority on Baseline**：PRD、SRS、Architecture 的新增或变更必须 Human Confirmation
- **AI Responsibility on Execution**：Development、Testing、Delivery、Retrospective 由 AI 自行确认完成
- **Backflow Allowed**：阶段允许回流；发现上游问题时回到对应 Stage 的 Change Mode，而非另起一套修复流程
- **One Logical Stage Skill, Two Modes**（v0.3 reconciled）：每个主流程 Stage 对应一个 **logical Stage Skill**，可被实现为**一个或多个 physical skills**（如 `*-write` / `*-review` 配对）；所有 physical skills 共享同一 Stage 和 Mode 契约。Skill 内部同时支持 Full Mode 与 Change Mode；Bug 修复不另建独立 Skill 体系
- **PRD Stability**：PRD 是 high-level product baseline，正常不应成为 bug root cause；若成为 root cause，触发 Workflow Incident Analysis 而非普通 bug 修复
- **S3 Reference Input**：S3 不新增独立的 Source System Analysis Stage；源系统分析作为 PRD Phase 与 SRS Phase 的参考输入
- **CR Scope**：CR Document 仅用于 SRS 契约级变更；Architecture 变更只保存 version history，不需 CR

---

## 4. Main Lifecycle (主流程)

主流程由 7 个 high-level Stage 组成，适用 S1、S2、S3。S4 走 Bug Rollback Flow（见 §6）。

### 4.1 Lifecycle Overview

```text
PRD Inception
  → SRS Specification
    → Architecture Design
      → Development
        → Testing
          → Delivery
            → Project Retrospective
```

### 4.2 Stage Summary

| # | Stage | Lead | Human Gate | Main Outputs |
|---|-------|------|------------|--------------|
| 1 | PRD Inception (PRD 立项) | Human + AI | ✓ | PRD + Supporting Artifacts |
| 2 | SRS Specification (SRS 调研) | Human + AI | ✓ | SRS + Acceptance Plan + Integration Plan（多模块时）|
| 3 | Architecture Design (架构设计) | AI | ✓ | Technical Architecture + Business Architecture |
| 4 | Development (开发) | AI | × | Development Plan + Task Breakdown + Detailed Design + Unit Tests + Integration Tests + Source Code |
| 5 | Testing (测试) | AI | × | Test Preparation + Test Procedure + Test Report + Bug Report（如有）|
| 6 | Delivery (交付) | AI | × | Deployment Doc + Operation Manual + Installation/Deployment Artifacts |
| 7 | Project Retrospective (项目复盘) | AI | × | Issue Report（按 AI Capability / Workflow / Token Waste 分类）+ Improvement Proposals |

### 4.3 Stage 1: PRD Inception (PRD 立项)

**Lead**: Human + AI

**Objective**：明确产品/项目为什么存在、为谁服务、解决什么问题、high-level 功能边界。为 SRS Specification 提供输入。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| PRD | Product Requirements Document，描述产品目标、用户价值、功能范围、业务边界 |
| PRD Supporting Artifacts | PRD 附属制品集合，用于支撑 PRD 判断与 SRS 输入 |

**Possible Supporting Artifacts**

| Artifact | 描述 | 适用 |
|----------|------|------|
| Competitor Research | 竞品调研 | 全场景 |
| Competitor Architecture Comparison | 竞品架构对比 | 全场景 |
| Market Research | 市场调研 | 按需 |
| User Scenario Analysis | 用户场景分析 | 按需 |
| Product Boundary / Non-goals | 产品边界 / 非目标声明 | 推荐 |
| Initial Risk Analysis | 初始风险分析 | 推荐 |
| Source Product PRD Analysis | 源产品 PRD 层面分析 | S3 必备 |
| Feature Keep/Cut/Enhance Matrix | 功能保留/裁剪/增强矩阵 | S3 必备 |

**Inputs**

- S1: Human idea + 市场/竞品/用户场景调研材料
- S3: Human target for 新项目 + 源系统 PRD / 产品说明 / 功能说明 / 用户流程 / 已知问题

**Gate Rule**

- PRD 新增必须 Human Confirmation
- PRD 变更必须 Human Confirmation
- 未确认的 PRD 不得进入 SRS Specification

**Special Rules**

- PRD 是 high-level product baseline，正常不应成为 bug root cause
- 若后续流程发现 PRD 存在根本矛盾，触发 Workflow Incident Analysis（见 §6.4），不进入普通 bug 修复

### 4.4 Stage 2: SRS Specification (SRS 调研)

**Lead**: Human + AI

**Objective**：将 PRD 转化为可设计、可开发、可测试的软件需求规格，明确系统功能、非功能要求、接口、集成关系与验收依据。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| SRS | Software Requirements Specification，作为 Architecture / Development / Testing 的核心事实源 |
| Acceptance Plan | 验收方案，作为 Testing Stage 的主要验收依据 |
| Integration Plan | 集成方案，存在多个 Module 或外部系统集成时必需 |

**Possible Supporting Artifacts**

| Artifact | 描述 | 适用 |
|----------|------|------|
| Requirement Traceability | 需求追溯关系 | 推荐 |
| Source Product SRS Analysis | 源产品 SRS 层面分析 | S3 必备 |
| Source Module Analysis | 源 Module / Interface / Data Model / Business Rule 分析 | S3 必备 |
| Reuse / Replace Capability Analysis | 能力复用 vs 替换分析 | S3 必备 |
| Technical Debt and Risk Analysis | 源系统技术债与不继承内容 | S3 推荐（v0.6 修正：非必备）|

**Inputs**

- S1: 已确认的 PRD + PRD Supporting Artifacts
- S3: 已确认的新项目 PRD + 源系统 SRS / 功能列表 / 接口文档 / 集成说明 / 代码行为分析 / 测试材料

**Gate Rule**

- SRS 新增必须 Human Confirmation
- SRS 变更必须 Human Confirmation（同时生成 CR Document，见 §7）
- 未确认的 SRS 不得进入 Architecture Design

**Special Rules**

- Testing Stage 必须以本阶段输出的 Acceptance Plan 为主要验收依据
- 如果 Testing 中发现 Acceptance Plan 不完整或 SRS 存在功能/业务矛盾，回到 SRS Change Mode，通过 CR 增量更新

### 4.5 Stage 3: Architecture Design (架构设计)

**Lead**: AI 输出，Human 确认

**Objective**：基于已确认的 PRD 和 SRS，设计 Business Architecture 与 Technical Architecture，明确模块边界、业务流程、数据流、接口、技术选型、集成方式与关键风险。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| Architecture Document | 含 Business Architecture + Technical Architecture + Module Boundary + Business Flow + Data Flow + Interface Boundary + Technology Selection + Architecture Risk and Tradeoff |
| Human Approval Record | 人确认记录 |

**Gate Rule**

- Architecture Document 新增必须 Human Confirmation
- Architecture Document 变更必须 Human Confirmation
- 未确认的 Architecture Document 不得进入 Development

**Change Record Rule**

- Architecture 变更**只需保存 version history**，**不需 CR Document**（与 SRS 区别：SRS 是对外契约；Architecture 是内部实现选择）

### 4.6 Stage 4: Development (开发)

**Lead**: AI

**Objective**：基于已确认的 SRS 和 Architecture Document，输出可验证的实现。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| Development Plan | 开发计划，描述任务组织与执行顺序 |
| Task Breakdown | 任务拆解 |
| Task Detailed Design | 任务详细设计，复杂任务必须输出 |
| Unit Test Cases | 单元测试用例 |
| Integration Test Cases | 集成测试用例 |
| Source Code | 源代码 |
| Local Verification Result | 本地验证结果 |

**Gate Rule**

- Development Stage 完成由 AI Self-check
- AI 必须确认 Development Output 与 SRS、Architecture Document、Development Plan 一致后才能进入 Testing

**Special Rules**

- 开发过程中若发现必须修改 SRS 或 Architecture，回流到对应 Stage 并等待 Human Confirmation

### 4.7 Stage 5: Testing (测试)

**Lead**: AI

**Objective**：基于 SRS Stage 输出的 Acceptance Plan 执行测试与验收验证；发现问题输出 Bug Report 并按根因路由回流。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| Test Preparation | 测试准备记录（环境、数据、依赖、工具） |
| Test Environment Description | 测试环境描述 |
| Detailed Test Steps | 测试详细步骤 |
| Test Execution Record | 测试执行记录 |
| Test Report | 测试报告 |
| Bug Report | Bug 报告，发现问题时必输 |

**Gate Rule**

- Testing Stage 完成由 AI Self-check
- 测试不得临时发明新的验收标准；若验收标准不足，回到 SRS Change Mode

**Special Rules**

- 测试发现 Bug 时进入 Bug Rollback Flow（见 §6）

### 4.8 Stage 6: Delivery (交付)

**Lead**: AI（Human 按需确认最终可交付状态）

**Objective**：基于 Testing Stage 的通过结果完成交付准备。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| Deployment Document | 部署文档 |
| Installation Guide | 安装指南 |
| Operation Manual | 操作手册 |
| Release Notes | 发布说明，按需 |
| Delivery Summary | 交付总结 |

**Gate Rule**

- Delivery Stage 完成由 AI Self-check
- 交付准备中若发现需求/架构/验收标准问题，回流到对应阶段

### 4.9 Stage 7: Project Retrospective (项目复盘)

**Lead**: AI（Human 按需确认流程改进方向）

**Objective**：回顾整个项目生命周期，识别问题与浪费，输出改进方案。

**Main Outputs**

| Artifact | 描述 |
|----------|------|
| Retrospective Report | 复盘报告 |
| Issue Analysis Report | 问题分析报告 |
| Workflow Improvement Proposal | 工作流改进建议 |
| Skill Improvement Proposal | Skill 改进建议（按需）|
| Template Improvement Proposal | 模板改进建议（按需）|
| Token Optimization Proposal | Token 优化建议（按需）|

**Analysis Dimensions (分析维度)**

| 维度 | 说明 |
|------|------|
| AI Capability Limitation | 哪些问题源自 AI 能力限制；是否可通过流程或模板规避 |
| Workflow Defect | 哪些问题源自 workflow 设计缺陷、阶段缺失、确认点错误或输入输出断裂 |
| Skill Gap | 哪些地方说明现有 skill 不足，是否需新增/修改 |
| Documentation Gap | 哪些地方说明文档结构或模板不足 |
| Token Waste | 哪些环节消耗 token 但没产生足够价值，是否可优化 |
| No-action Finding | 没有明显问题但值得记录的有效流程或检查点 |

**Gate Rule**

- Project Retrospective 完成由 AI Self-check
- 复盘建议若涉及修改 PRD / SRS / Architecture baseline，**不能在复盘中直接修改**，应生成后续变更建议并进入对应阶段的 Human Confirmation 流程

### 4.10 Main Gate Flow

```text
PRD confirmed by Human
  → SRS confirmed by Human
    → Architecture Document confirmed by Human
      → Development self-checked by AI
        → Testing self-checked by AI
          → Delivery self-checked by AI
            → Project Retrospective self-checked by AI
              → Lifecycle completed
```

---

## 5. Stage Mode Rule (阶段模式规则)

每个主流程 logical Stage Skill 必须支持两种模式。具体物理实现（如 `*-write` / `*-review` 拆分）见 latest design proposal（当前 `docs/design/skill_set_design_proposal_v0.5.md`），所有 physical skills 共享 Stage 与 Mode 契约。一套 Skill 通过模式切换，统一覆盖 4 个 Scenario。

### 5.1 Full Mode (全量模式)

**用途**：首次创建该阶段完整产物（用于 S1 New Product 或 S3 Product Reconstruction 的从 0 建设阶段 baseline）

**Inputs**：上一阶段已确认产物 + 当前阶段所需参考材料

**Outputs**：当前阶段完整 baseline artifact + 给下游的标准输入

### 5.2 Change Mode (增量/变更模式)

**用途**：bug 回流 / CR 变更 / review 发现问题 / 测试失败 / 上游 baseline 变化（用于 S2 Feature Evolution、S4 Bugfix 等增量场景）

**Inputs**：Bug Report / CR / review finding / 上游变更说明 + 当前阶段已有 baseline artifact + 下游影响范围

**Outputs**：增量变更文档 + 更新后的阶段产物 + Impact Analysis + 下游阶段更新建议

### 5.3 Mode Confirmation Rules

- 当前阶段是 PRD / SRS / Architecture 时，Change Mode 输出必须等待 Human Confirmation
- 当前阶段是 Development / Testing / Delivery / Retrospective 时，由 AI Self-check；但若引发 baseline 变更，必须回到对应 Human Confirmation 阶段

---

## 6. Bug Rollback Flow (Bug 回流流程)

由 Stage 5 Testing 触发（active release 内的 S4），或由 active release 期间收到的缺陷输入触发。**v0.4 注**：release close 后才发现的 bug 不进入 Bug Rollback Flow，仅作为 intake record（`docs/bug/BUG-NNN.md` + `target_release: null`）等下一个 S2 release 启动时被 srs-write skill 合并。

### 6.1 General Flow

```text
Bug detected
  → Bug Reproduction and Evidence Collection
  → Bug Report
  → Root Cause Classification
  → Rollback to corresponding Stage Change Mode
  → Development Fix
  → Regression Testing
  → Test Report updated
  → Delivery Artifact updated if needed
  → Bug closed
```

S4 Bugfix 不单独执行 Bug Retrospective；Bug 相关记录由 Project Retrospective 统一分析。

### 6.2 Root Cause: SRS Issue

**触发条件**：功能需求矛盾 / 业务规则不清或冲突 / Acceptance Plan 不完整 / 测试发现 SRS 无法支撑真实业务或验收需求

```text
Bug Report
  → Rollback to SRS Specification Change Mode
  → Create CR Document
  → Incrementally update SRS
  → Human Confirmation
  → Architecture Update if needed (Human Confirmation)
  → Development Plan update / new task
  → Task Detailed Design if complex
  → Development
  → Testing
```

### 6.3 Root Cause: Architecture Issue

**触发条件**：架构无法满足 SRS / 模块边界错误 / 数据流-业务流-接口设计错误 / 集成方案不可行 / 非功能需求无法被当前架构满足

```text
Bug Report
  → Rollback to Architecture Design Change Mode
  → Update Architecture Document (version history only, no CR)
  → Human Confirmation
  → Development Plan update / new task
  → Task Detailed Design if complex
  → Development
  → Testing
```

### 6.4 Root Cause: Development Issue

**触发条件**：源代码不符合 SRS / Architecture / Detailed Design / 单元测试遗漏 / 集成测试遗漏 / 边界条件错误 / 实现质量问题

```text
Bug Report
  → Rollback to Development Change Mode
  → Development Plan update / task change
  → Task Detailed Design update if complex
  → Unit / Integration Test update
  → Source Code update
  → Testing
```

### 6.5 Root Cause: PRD Issue (Exception, Escape Valve)

**触发条件**：bug root cause 被判断为 PRD high-level product baseline 存在根本矛盾

```text
Bug Report
  → Stop Project Development
  → Enter Workflow Incident Analysis
  → Output Workflow Incident Report
  → Analyze why PRD review failed
  → Decide whether to revise workflow / review gate / PRD template / project direction
  → Decide whether to restart Project or enter S3 Product Reconstruction
```

**特殊规则**：

- PRD Root Cause 不作为普通 bug 修复处理
- 不应直接进入 PRD Change Mode 并继续开发
- 必须先讨论 workflow 是否存在问题，输出归入 Meta-Evolution Loop（见 §11）

---

## 7. Change Request Rule (CR 规则)

CR Document 是 SRS Change Mode 的标准入口制品。

### 7.1 When CR is Required

- SRS 变更（由 bug、review finding、测试结果或新需求引发）：**必须**生成 CR Document
- Architecture 变更：**不需** CR，仅保存 version history
- Development / Testing / Delivery / Retrospective 变更：**不需** CR，可直接更新对应产物

### 7.2 CR Document Required Fields

CR Document 至少应描述以下字段：

| Field | 描述 |
|-------|------|
| Change Background | 变更背景 |
| Trigger Source | 触发源（bug / review / 新需求等）|
| Affected Requirement | 受影响的需求 |
| Current Behavior or Current Spec | 当前行为或现有规格 |
| Expected Behavior or Updated Spec | 期望行为或更新后规格 |
| Impact Analysis | 影响分析 |
| Acceptance Plan Change | 验收方案变更 |
| Downstream Impact | 下游影响（Architecture / Development / Testing）|
| Human Approval Status | 人确认状态 |

### 7.3 Future Extension

第一版 CR 仅用于 SRS 变更。Architecture 和 Development 变更可引用 Bug Report、CR Document 或上游变更说明作为输入。后续如需要，可扩展 Architecture Change Request 或 Development Change Task。

---

## 8. Human Approval Rule (人确认规则)

### 8.1 必须 Human Confirmation 的 Baseline

- PRD
- SRS
- Architecture Document

### 8.2 必须 Human Confirmation 的动作

| Action | Required |
|--------|----------|
| 新增 PRD | ✓ |
| 变更 PRD | ✓ |
| 新增 SRS | ✓ |
| 变更 SRS | ✓（同时生成 CR Document）|
| 新增 Architecture | ✓ |
| 变更 Architecture | ✓（同时保存 version history）|

### 8.3 AI 可自行确认的 Stage 完成

- Development
- Testing
- Delivery
- Project Retrospective

### 8.4 Exception

如果 AI 自确认阶段发现需要修改 PRD / SRS / Architecture，必须回流到对应阶段并等待 Human Confirmation。

---

## 9. Scenario-Specific Flows (场景特定流程)

### 9.1 S1: New Product Flow

S1 用于从 0 打造一个新的 Product/Project。

```text
Product/Project Initiation (Human Idea)
  → PRD Inception (Full Mode)
  → SRS Specification (Full Mode)
  → Architecture Design (Full Mode)
  → Development (Full Mode)
  → Testing (Full Mode)
  → Delivery (Full Mode)
  → Project Retrospective
```

S1 默认全程使用 Full Mode。

### 9.2 S2: Feature Evolution Flow

S2 用于已规范化的 Product/Project 上新增或变更需求。包含 4 个子场景，**入口 Stage 不全相同**：2 个从 PRD 起步，2 个直接从 SRS 起步。

#### 9.2.1 S2-1: PRD Change for New Function (PRD 变更引入新功能)

**适用条件**：PRD 发生变更，目标是新增 Product Function，不影响原有核心功能、产品边界、业务模型或基础架构。

```text
PRD Change Mode (Human Confirmation)
  → New SRS or SRS Change Mode (Human Confirmation, CR Document)
  → Architecture Change Judgment (见 §10)
  → Development (Full or Change Mode)
  → Testing
  → Delivery
  → Project Retrospective
```

#### 9.2.2 S2-2: New SRS without PRD Change (新增 SRS，PRD 不变)

**适用条件**：PRD 无变更，但需新增 Software Requirement / Interface Capability / System Behavior / Integration Capability / Acceptance Criteria。

```text
SRS Specification (Full Mode for new SRS section, Human Confirmation)
  → Architecture Change Judgment
  → Development (Full or Change Mode)
  → Testing
  → Delivery
  → Project Retrospective
```

#### 9.2.3 S2-3: SRS Change without PRD Change (SRS 变更，PRD 不变)

**适用条件**：PRD 不变，但已有 SRS 的细节、约束、验收条件、接口或业务规则需要调整。

```text
SRS Change Mode (Human Confirmation, CR Document)
  → Architecture Change Judgment
  → Development (Change Mode)
  → Testing
  → Delivery
  → Project Retrospective
```

#### 9.2.4 S2-4: PRD Change Requiring Reconstruction (PRD 变更需要重构)

**适用条件**：PRD 变更影响原有功能，需要 Function Reconstruction 或 Architecture Reconstruction。

```text
PRD Change
  → Impact existing function
  → Require Function Reconstruction or Architecture Reconstruction
  → Stop current Project Evolution
  → Start a new Project
  → Enter S3 Product Reconstruction
```

**S2 范围规则**：S2 只处理可以安全 incremental evolution 的需求。不可安全演进的 PRD Change 必须转入 S3。

### 9.3 S3: Product Reconstruction Flow

S3 用于基于已存在的 Product/Project，通过复制/增强/裁剪/重构，打造一个符合本规范的新 Project。

**核心原则**：S3 不新增独立的 Source System Analysis Stage；复用 S1 主流程，但在 Stage 1 和 Stage 2 强制引入 Source System Reference Artifact。

```text
PRD Inception (Full Mode + Source Product PRD Analysis)
  → SRS Specification (Full Mode + Source Product SRS Analysis)
  → Architecture Design (Full Mode)
  → Development (Full Mode)
  → Testing (Full Mode)
  → Delivery (Full Mode)
  → Project Retrospective
```

**S3 关键规则**：

1. Source Product/Project 是新 Project 的输入参考，**不是直接搬迁对象**
2. New PRD 必须基于新目标重新定义，不是简单复制旧系统
3. New SRS 必须基于新 Project 的需求重新定义
4. Source System Analysis 只作为 Stage 1、Stage 2 的参数与参考制品，不改变主流程结构

### 9.4 S4: Bugfix Flow

S4 用于修复符合本规范的 Product/Project 中的 Bug。前提是 Project 已具备 Workflow Scaffold、Document Structure 与 Skills，且**当前 release 处于 active 状态**（v0.4）。

**v0.4 限制**：当所有 release 都已 close 时，S4 不可用；新发现的 bug 仅作为 intake record（写入 `docs/bug/BUG-NNN.md`，frontmatter `target_release: null`），等下一个 S2 release 启动时由 srs-write skill 扫描合并到新 SRS。

```text
Bug Input (来自 active release 内的测试或交付期间)
  → Bug Reproduction and Evidence Collection
  → Bug Report
  → Root Cause Classification (见 §6.2-6.5)
  → Corresponding Stage Change Mode
  → Development Fix
  → Regression Testing
  → Test Report updated
  → Delivery Artifact updated if needed
  → Bug Closed
```

S4 不单独执行 Bug Retrospective；Bug Report、Root Cause、Fix Record 与 Regression Testing Record 由 Project Retrospective Stage 统一分析。

---

## 10. Architecture Change Judgment (架构变更判断)

Architecture Change Judgment 是 SRS 之后的 **decision point**，**不是独立 Stage**。用于判断 SRS 变更或新增是否触发架构变更。

```text
After SRS Confirmation
  → Architecture Change Judgment
      → No Architecture Change needed
          → Development
      → Architecture Change needed
          → Architecture Design Change Mode
          → Human Confirmation of Architecture Document
          → Development
```

**判断依据**（详细规则待定，见 §13）：模块边界变化 / 数据流变化 / 接口变化 / 技术选型变化 / 集成方式变化 / 非功能需求变化。

---

## 11. Meta-Evolution Loop (元演进闭环)

工作流自身的演进有两条路径汇入：

| 路径 | 触发 | 输出 |
|------|------|------|
| Project Retrospective (Stage 7) | 项目正常结束 | Workflow Improvement Proposal、Skill / Template / Token Optimization Proposal |
| PRD Root Cause Exception (§6.5) | Bug 流程异常分支 | Workflow Incident Report、PRD Review Failure Analysis、Workflow Improvement Proposal |

```text
Stage 7 Retrospective
  ↘
    Workflow Self-Improvement
  ↗
PRD Root Cause Exception
```

独立的 cross-cutting `workflow-evolution` skill 消化这两类输入并产出 workflow / skill / template 升级建议。详见 design proposal Section 6。

---

## 12. Artifact Relationship (产物关系)

```text
PRD
  → SRS (含 Acceptance Plan, Integration Plan)
    → Architecture Document
      → Development Plan + Task Detailed Design + Test Cases + Source Code
        → Test Report + Bug Report
          → Deployment Document + Operation Manual
            → Project Retrospective Report
```

**关键依赖**：

- SRS 是 Architecture / Development / Testing 的核心事实源
- Acceptance Plan 是 Testing Stage 的关键依据
- Bug Report 是 Bug Rollback 与 Project Retrospective 的关键依据
- Project Retrospective Report 是 Meta-Evolution Loop 的关键输入

---

## 13. Open Items (待定项)

以下内容不在本规范展开，将在主流程确认后逐项设计：

1. 每个 Stage 的内部详细子步骤
2. 每个 Stage Skill 的职责、输入、输出与 Mode 切换逻辑设计
3. Cross-cutting Skill 列表与定义（候选：Document Structure Guardian、Artifact Validator、Project Memory Manager、Token Cost Auditor、Workflow Evolution Skill）
4. Document Directory Policy 与 Filename Policy（由 Document Structure Guardian 定义）
5. 各类模板：PRD Template / SRS Template / Architecture Document Template / CR Document Template / Bug Report Template / Test Report Template / Retrospective Report Template
6. Validation Script 与 Workflow Gate Check 规则
7. Root Cause Classification 的详细判断标准
8. Architecture Change Judgment 的详细判断标准
9. Task Complexity 判断规则（用于决定是否需要 Task Detailed Design）
10. Workflow Evolution 机制（如何把 §11 的输入落地为流程升级）
11. Acceptance Plan 与 Acceptance Test 的标准结构与执行约定
12. Integration Plan 的适用条件与格式定义

---

## 14. Document Conventions (文档自身约定)

- **文件命名**：英文 + `_claude.md` 后缀
- **目录**：英文（本文档位于 `docs/workflow/`）
- **专业术语**：英文（首次出现时附中文注释）
- **描述性文本**：中文
- **元数据**：YAML frontmatter（title / type / status / owner / created / updated / sources）
- **变更**：每次重大修订追加到 Change Log

---

## Change Log

| Date | Version | Change |
|------|---------|--------|
| 2026-05-05 | v0.1 | Initial Workflow Specification Draft (claude) |
| 2026-05-05 | v0.2 | 合并 hermes / code 两份草案：吸收 code 的 4 场景结构与 S2 子场景、Architecture Change Judgment、Artifact Relationship、frontmatter；吸收 hermes 的 per-stage 模板、Mode Rule 详细定义、CR 9 字段；保留 claude 的 Meta-Evolution Loop 显式命名、Architecture-CR 豁免明文、Document Conventions |
| 2026-05-05 | v0.3 | F1 reconciliation：明确 "One Stage Skill" 是 logical concept，可对应多个 physical skill（如 `*-write` / `*-review` 配对，Stage 4 含 `development-code-review`）。详见 `docs/design/skill_set_design_proposal_v0.3.md` |
| 2026-05-05 | v0.4 | F2 sync：S4 严格 active-release-only；release close 后的 bug 仅作 intake record，不进入 Bug Rollback Flow，等下一个 S2 release 合并。详见 `docs/design/skill_set_design_proposal_v0.4.md` |
| 2026-05-06 | v0.5 | 残留同步：移除 v0.3 design 路径引用、workflow-evolution 不再标"待定"。详见 `docs/design/skill_set_design_proposal_v0.5.md` |
| 2026-05-06 | v0.6 | Batch 1 review F5 sync：S3 Stage 2 必备清单与 design v0.5 §5.3 对齐为 **3 必备（srs-level / module-level / reuse-replace）+ technical-debt 推荐**（不再写"4 类"）；其他 batch 1 finding 落地到 SKILL.md 与 references。详见 `docs/review/reviewer_feedback_response_v0.5_batch1.md` |
