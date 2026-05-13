---
title: Product/Project Workflow Specification Draft
type: workflow-spec
status: draft
owner: cgs
created: 2026-05-05
updated: 2026-05-05
---

# Product/Project Workflow Specification Draft

## Purpose

本文档用于记录个人定制化 Product/Project R&D Workflow 的 high-level 规范草案。

当前阶段只定义整体流程框架、Scenario 入口、Lifecycle Stage、Gate Rule、Rollback Rule 和 Artifact 方向，不展开每个 Stage 内部的详细步骤，也不定义具体 Skill 实现。

## Design Scope

本规范覆盖 4 个核心 Scenario：

| Scenario | Name | Description |
| --- | --- | --- |
| S1 | New Product | 从 0 打造一个新的 Product/Project。 |
| S2 | Feature Evolution | 基于已经符合 Workflow 规范的 Product/Project 进行新增需求演进。 |
| S3 | Product Reconstruction | 基于已存在的 Product/Project，通过复制、增强、裁剪或重构，打造一个符合本 Workflow 规范的新 Project。 |
| S4 | Bugfix | 修复符合本 Workflow 规范的 Product/Project 中的 Bug。 |

## Core Principles

### Product/Project Lifecycle First

Workflow 必须先围绕完整 Product/Project Lifecycle 设计，再拆分每个 Stage 需要的 Skill 和 Cross-cutting Skill。

这样可以避免一开始陷入局部细节，导致整体流程变形。

### Two-layer Workflow

Workflow 采用 Two-layer Structure：

1. Unified Product/Project Lifecycle：定义所有 Scenario 共享的主流程。
2. Scenario-specific Subflow：定义 S1、S2、S3、S4 在主流程中的入口、裁剪和回流规则。

所有 Scenario 必须回写到统一的 Project Memory、Document Structure、Task State 和 Verification Record。

### Full Mode and Incremental/Change Mode

每个主流程 Stage Skill 必须同时支持两种模式：

| Mode | Description |
| --- | --- |
| Full Mode | 用于 S1 New Product 或 S3 Product Reconstruction，从完整 Stage 输入创建完整 Stage Artifact。 |
| Incremental/Change Mode | 用于 S2 Feature Evolution、S4 Bugfix、Bug Rollback、Architecture Change、Development Fix 等增量场景。 |

Bugfix 不应该维护一套与主流程割裂的独立修复流程，而应该复用对应 Stage Skill 的 Incremental/Change Mode。

### Human Confirmation Gate

以下 Stage 或 Artifact 的新增与变更必须经过 Human Confirmation：

| Artifact / Stage | Confirmation Rule |
| --- | --- |
| PRD | 新增或变更必须 Human Confirmation。 |
| SRS | 新增或变更必须 Human Confirmation。 |
| Architecture Document | 新增或变更必须 Human Confirmation。 |

以下 Stage 默认由 AI 自确认完成：

| Stage | Confirmation Rule |
| --- | --- |
| Development | AI Self-check。 |
| Testing | AI Self-check。 |
| Delivery | AI Self-check。 |
| Project Retrospective | AI Self-check。 |

### Stage Rollback Allowed

Workflow 允许 Stage Rollback。

当 Testing Stage 或 Bugfix Flow 发现问题时，必须先生成 Bug Report，并进行 Root Cause Classification，然后回流到对应 Stage 的 Incremental/Change Mode。

### PRD is Not a Normal Bug Root Cause

PRD 原则上不应该成为 Bug Root Cause。

PRD 是 high-level Product Function 和 Product Goal 描述，应该在 PRD Stage 被严格评审，不应该存在自相矛盾、范围冲突或核心目标不清的问题。

如果 Bug Root Cause 指向 PRD，则必须终止当前 Project Development，不继续普通 Bugfix Flow，而是进入 Workflow Incident Analysis。

输出要求：

1. Workflow Incident Report。
2. PRD Review Failure Analysis。
3. Workflow Improvement Proposal。
4. 是否需要重启 Project 或进入 S3 Product Reconstruction 的建议。

## Main Lifecycle

Unified Product/Project Lifecycle 包含 7 个 high-level Stage：

```text
Product/Project Initiation
→ SRS Research
→ Business Architecture and Technical Architecture Design
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

## Stage 1: Product/Project Initiation

### Objective

Human 和 AI 一起完成 Product/Project 立项，明确 Product Goal、User Value、Business Scope、Feature Boundary 和 high-level Function Definition。

### Main Output

| Artifact | Description |
| --- | --- |
| PRD | Product Requirements Document，描述 Product 目标、用户价值、功能范围和业务边界。 |
| PRD Supporting Artifacts | PRD 附属制品，用于支撑 PRD 判断和后续 SRS 输入。 |

### Possible Supporting Artifacts

| Artifact | Description |
| --- | --- |
| Competitive Research | 竞品调研，用于理解市场、功能参考和差异化方向。 |
| Competitive Architecture Comparison | 竞品架构比较，用于辅助判断产品形态和架构方向。 |
| Source Product PRD Analysis | S3 Product Reconstruction 场景下，对原 Product/Project 的 PRD 层面分析。 |
| Feature Keep/Cut/Enhance Matrix | S3 Product Reconstruction 场景下，记录原功能保留、裁剪、增强关系。 |

### Gate Rule

PRD 新增或变更必须 Human Confirmation。

未确认的 PRD 不允许进入 SRS Research。

## Stage 2: SRS Research

### Objective

Human 和 AI 一起基于 PRD 输出 Software Requirements Specification，明确 Software Requirement、System Behavior、Integration Requirement、Acceptance Criteria 和 Test Basis。

### Main Output

| Artifact | Description |
| --- | --- |
| SRS | Software Requirements Specification，作为 Architecture、Development、Testing 的核心事实源。 |
| Integration Plan | 如果存在多个 Module 或外部 System，需要输出集成方案。 |
| Acceptance Plan | 用于指导 Testing Stage 的验收方案。 |

### Possible Supporting Artifacts

| Artifact | Description |
| --- | --- |
| Source Product SRS Analysis | S3 Product Reconstruction 场景下，对原 Product/Project 的 SRS 层面分析。 |
| Source Module Analysis | S3 场景下，对原 Module、Interface、Data Model、Business Rule 的分析。 |
| Reuse/Replace Capability Analysis | S3 场景下，说明哪些能力可复用，哪些能力必须替换。 |
| Technical Debt and Risk Analysis | S3 场景下，说明原系统技术债、风险和不继承内容。 |

### Gate Rule

SRS 新增或变更必须 Human Confirmation。

未确认的 SRS 不允许进入 Architecture Design。

## Stage 3: Business Architecture and Technical Architecture Design

### Objective

AI 基于 PRD 和 SRS 输出 Business Architecture 与 Technical Architecture，Human 进行确认。

### Main Output

| Artifact | Description |
| --- | --- |
| Architecture Document | 描述 Business Architecture、Technical Architecture、Module Boundary、Data Flow、Integration Boundary、Risk 和 Trade-off。 |

### Gate Rule

Architecture Document 新增或变更必须 Human Confirmation。

未确认的 Architecture Document 不允许进入 Development。

## Stage 4: Development

### Objective

AI 基于已确认的 SRS 和 Architecture Document，完成 Development Plan、Task Breakdown、Task Detailed Design、Test Case 和 Source Code。

### Main Output

| Artifact | Description |
| --- | --- |
| Development Plan | 开发计划，描述开发阶段的任务组织和执行顺序。 |
| Work Breakdown | 开发任务分解。 |
| Task Detailed Design | 复杂开发任务需要输出任务详细设计。 |
| Unit Test Cases | 单元测试用例。 |
| Integration Test Cases | 集成测试用例。 |
| Source Code | 源代码。 |

### Gate Rule

Development Stage 默认由 AI Self-check 完成。

AI 必须确认 Development Output 与 SRS、Architecture Document 和 Development Plan 一致后，才能进入 Testing。

## Stage 5: Testing

### Objective

AI 基于 SRS Research Stage 输出的 Acceptance Plan 执行 Testing，验证 Product/Project 是否满足 SRS 和验收标准。

### Main Output

| Artifact | Description |
| --- | --- |
| Test Preparation | 测试准备记录，包括环境、数据、依赖、工具等。 |
| Test Steps | 测试详细步骤。 |
| Test Report | 测试报告。 |
| Bug Report | 如果发现 Bug，必须输出 Bug Report。 |

### Gate Rule

Testing Stage 默认由 AI Self-check 完成。

测试通过后才能进入 Delivery。

如果发现 Bug，必须进入 Bug Rollback Flow。

## Stage 6: Delivery

### Objective

AI 基于 Testing Stage 的通过结果，完成安装部署、部署说明和使用说明。

### Main Output

| Artifact | Description |
| --- | --- |
| Deployment Guide | 部署文档。 |
| Operation Manual | 操作手册。 |
| Installation/Deployment Result | 安装部署结果记录。 |

### Gate Rule

Delivery Stage 默认由 AI Self-check 完成。

Delivery 完成后进入 Project Retrospective。

## Stage 7: Project Retrospective

### Objective

AI 基于整个 Product/Project Lifecycle 的记录，分析项目过程中的问题、AI 能力限制、Workflow 问题和 Token Waste，并输出优化方案。

### Main Output

| Artifact | Description |
| --- | --- |
| Project Problem Report | 项目生命周期问题报告。 |
| AI Capability Limitation Analysis | 分析哪些问题来自 AI 能力限制。 |
| Workflow Problem Analysis | 分析哪些问题来自 Workflow 设计缺陷。 |
| Token Waste Analysis | 分析哪些环节浪费了 Token，是否可以通过流程或 Skill 优化。 |
| Workflow Improvement Proposal | 输出对应的流程改进方案。 |

### Gate Rule

Project Retrospective 默认由 AI Self-check 完成。

Project Retrospective 完成后，当前 Product/Project Lifecycle 结束。

## Main Gate Flow

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

## Bug Rollback Flow

### General Flow

```text
Bug detected
→ Bug Reproduction and Evidence Collection
→ Bug Report
→ Root Cause Classification
→ Rollback to corresponding Stage Incremental/Change Mode
→ Development Fix
→ Regression Testing
→ Test Report updated
→ Delivery Artifact updated if needed
→ Bug closed
```

S4 Bugfix 不单独执行 Bug Retrospective。

Bug 相关记录由 Project Retrospective Stage 统一分析。

### Root Cause: SRS Issue

```text
SRS Issue
→ Rollback to SRS Research Incremental/Change Mode
→ Create CR Document
→ Incrementally update SRS
→ Update Architecture Document if needed
→ Add or change Development Plan / Task
→ Add Task Detailed Design if the development task is complex
→ Development
→ Testing
```

SRS/CR 变更必须 Human Confirmation。

如果 Architecture Document 受影响，Architecture Document 变更也必须 Human Confirmation。

### Root Cause: Architecture Issue

```text
Architecture Issue
→ Rollback to Architecture Design Incremental/Change Mode
→ Update Architecture Document
→ Add or change Development Plan / Task
→ Add Task Detailed Design if the development task is complex
→ Development
→ Testing
```

Architecture Document 变更必须 Human Confirmation。

### Root Cause: Development Issue

```text
Development Issue
→ Rollback to Development Incremental/Change Mode
→ Add or change Development Plan / Task
→ Add Task Detailed Design if the development task is complex
→ Development
→ Testing
```

Development Fix 默认由 AI Self-check 完成。

### Root Cause: PRD Issue

```text
PRD Issue
→ Stop Project Development
→ Enter Workflow Incident Analysis
→ Output Workflow Incident Report
→ Discuss whether the Workflow has a design problem
→ Decide whether to restart Project or enter S3 Product Reconstruction
```

PRD Issue 不走普通 Bug Rollback Flow。

## S1: New Product Flow

S1 用于从 0 打造一个新的 Product/Project。

```text
Product/Project Initiation
→ SRS Research
→ Business Architecture and Technical Architecture Design
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

S1 默认使用 Full Mode。

## S2: Feature Evolution Flow

S2 用于基于已经符合 Workflow 规范的 Product/Project 进行新增需求演进。

S2 包含 4 种入口。

### S2-1: PRD Change for New Product Function

适用条件：PRD 发生变更，但变更目标是新增 Product Function，不影响原有核心功能、产品边界、业务模型或基础架构。

```text
PRD Change
→ New SRS
→ Architecture Change Judgment
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

PRD Change、New SRS 和必要的 Architecture Change 必须 Human Confirmation。

### S2-2: New SRS without PRD Change

适用条件：PRD 无变更，但需要新增 Software Requirement、Interface Capability、System Behavior、Integration Capability 或 Acceptance Criteria。

```text
New SRS
→ Architecture Change Judgment
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

New SRS 和必要的 Architecture Change 必须 Human Confirmation。

### S2-3: SRS Change without PRD Change

适用条件：PRD high-level Product Goal 不变，但已有 SRS 的细节、约束、验收条件、接口或业务规则需要调整。

```text
SRS Change
→ Architecture Change Judgment
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

SRS Change 和必要的 Architecture Change 必须 Human Confirmation。

### S2-4: PRD Change Requiring Reconstruction

适用条件：PRD 变更影响原有功能，需要 Function Reconstruction 或 Architecture Reconstruction。

```text
PRD Change
→ Impact existing function
→ Require Function Reconstruction or Architecture Reconstruction
→ Stop current Project Evolution
→ Start a new Project
→ Enter S3 Product Reconstruction
```

S2 只处理可以安全 Incremental Evolution 的需求。

不可安全 Incremental Evolution 的 PRD Change 必须转入 S3。

### Architecture Change Judgment

Architecture Change Judgment 是 SRS 之后的 decision point，不是独立 Stage。

```text
No Architecture Change needed
→ Development

Architecture Change needed
→ Architecture Design Incremental/Change Mode
→ Human confirms Architecture Document
→ Development
```

## S3: Product Reconstruction Flow

S3 用于基于已存在的 Product/Project，通过复制、增强、裁剪或重构，打造一个符合本 Workflow 规范的新 Project。

S3 不新增独立的 Source System Analysis Stage。

S3 复用 S1 主流程，但在 Stage 1 和 Stage 2 强制引入 Source System Reference Artifact。

```text
Product/Project Initiation with Source Product PRD Analysis
→ SRS Research with Source Product SRS Analysis
→ Business Architecture and Technical Architecture Design
→ Development
→ Testing
→ Delivery
→ Project Retrospective
```

S3 的核心规则：

1. Source Product/Project 是新 Project 的输入参考，不是直接搬迁对象。
2. New PRD 必须基于新目标重新定义，而不是简单复制旧系统。
3. New SRS 必须基于新 Project 的 Software Requirement 重新定义。
4. Source System Analysis 只作为 Stage 1 和 Stage 2 的参数与参考制品，不改变主流程结构。

## S4: Bugfix Flow

S4 用于修复符合本 Workflow 规范的 Product/Project 中的 Bug。

S4 的前提是 Project 已经具备 Workflow Scaffold、Document Structure 和 Skills。

```text
Bug Input
→ Bug Reproduction and Evidence Collection
→ Bug Report
→ Root Cause Classification
→ Corresponding Stage Incremental/Change Mode
→ Development Fix
→ Regression Testing
→ Test Report updated
→ Delivery Artifact updated if needed
→ Bug Closed
```

S4 不单独执行 Bug Retrospective。

Bug Report、Root Cause、Fix Record 和 Regression Testing Record 会在 Project Retrospective Stage 统一分析。

## Artifact Relationship

```text
PRD
→ SRS
→ Architecture Document
→ Development Plan / Task Detailed Design / Test Cases / Source Code
→ Test Report / Bug Report
→ Deployment Guide / Operation Manual
→ Project Retrospective Report
```

SRS 是 Architecture、Development、Testing 的关键事实源。

Acceptance Plan 是 Testing Stage 的关键依据。

Bug Report 是 Rollback 和 Project Retrospective 的关键依据。

## Deferred Design Topics

以下内容不在本草案中展开，需要在主流程确认后逐项设计：

1. 每个 Stage 内部的详细步骤。
2. 每个 Stage Skill 的职责、输入、输出和 Mode 设计。
3. Cross-cutting Skill 列表，例如 Document Structure Guardian、Artifact Validator、Project Memory Manager、Token Cost Auditor。
4. Document Directory Policy 和 Filename Policy。
5. PRD Template、SRS Template、Architecture Document Template、CR Document Template、Bug Report Template、Test Report Template、Retrospective Report Template。
6. Validation Script 和 Workflow Gate Check 规则。
7. Root Cause Classification 的详细判断标准。
8. Architecture Change Judgment 的详细判断标准。
9. Task Complexity 判断规则，用于决定是否需要 Task Detailed Design。

## Change Log

| Date | Change |
| --- | --- |
| 2026-05-05 | Create initial high-level Workflow Specification Draft based on discussion. |
