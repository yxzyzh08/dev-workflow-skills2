# Product Lifecycle Workflow Draft

## 1. Scope

本文档定义 `S1: New Product Creation` 和 `S3: Product Rebuild From Existing System` 的 high-level 研发流程草案。

适用场景：

- `S1: New Product Creation`：从 0 打造一个新产品或新项目。
- `S3: Product Rebuild From Existing System`：基于已存在的产品或项目，按照本工作流新建一个符合规范的新项目；可复制、增强或裁剪原系统能力。

本文档暂不展开每个阶段的内部详细步骤，也暂不定义具体 `skill`。后续应在主流程确认后，再拆分阶段 `skill`、cross-cutting guardian `skill` 和模板制品。

## 2. Core Principles

- `Scenario-first`：先判断属于哪个研发场景，再进入对应 workflow。
- `Artifact-driven`：每个阶段必须有明确输入、输出和下游用途。
- `Human authority on baseline`：`PRD`、`SRS`、`Architecture` 的新增或变更必须由人类确认。
- `AI responsibility on execution`：`Development`、`Testing`、`Delivery`、`Retrospective` 由 AI 自行判断是否完成。
- `Backflow allowed`：阶段允许回流；发现上游问题时，应回到对应阶段的 `Change Mode`。
- `One phase skill, two modes`：主流程阶段 `skill` 应同时支持 `Full Mode` 和 `Change Mode`，不为 bug 修复单独复制一套阶段体系。
- `PRD stability`：`PRD` 是 high-level product baseline，原则上不应成为 bug root cause；如果成为 root cause，应停止普通开发流程并进入 workflow exception review。
- `S3 reference input`：`S3` 不新增独立的 source-system analysis phase；原系统分析作为 `PRD Phase` 和 `SRS Phase` 的参考输入。

## 3. Lifecycle Overview

```text
PRD Phase
  -> SRS Phase
  -> Architecture Phase
  -> Development Phase
  -> Testing Phase
  -> Delivery Phase
  -> Retrospective Phase
```

带回流的 high-level flow：

```text
PRD(full, human approval)
  -> SRS(full, human approval)
  -> Architecture(full, human approval)
  -> Development(full, AI self-check)
  -> Testing(full, AI self-check)
      -> Bug Report
          -> SRS(change, CR, human approval) -> Architecture(change if needed) -> Development(change) -> Testing(change)
          -> Architecture(change, human approval) -> Development(change) -> Testing(change)
          -> Development(change) -> Testing(change)
          -> PRD root cause -> stop normal development -> Workflow Exception Review
  -> Delivery(full, AI self-check)
  -> Retrospective(full, AI self-check)
```

## 4. Phase List

### 4.1 PRD Phase

英文名称：`PRD Phase` / `Product Initiation Phase`

参与者：

- Human
- AI

目标：

- 明确产品或项目为什么存在、为谁服务、解决什么问题、high-level 功能边界是什么。
- 为 `SRS Phase` 提供输入。

核心输出：

- `PRD` 文档。
- `PRD supporting artifacts`，例如：
  - `Competitor Research`
  - `Competitor Architecture Comparison`
  - `Market Research`，如需要
  - `User Scenario Analysis`，如需要
  - `Product Boundary`
  - `Non-goals`
  - `Initial Risk Analysis`

`S1` 输入：

- 人类的新产品想法。
- 市场、竞品、用户场景等调研材料，如需要。

`S3` 输入：

- 人类对新项目的目标。
- 原系统 `PRD`、产品说明、功能说明、用户流程、已知问题等参考材料。
- 原系统竞品或同类系统分析，如需要。

确认规则：

- `PRD` 新增必须人类确认。
- `PRD` 变更必须人类确认。

特殊规则：

- `PRD` 是 high-level product baseline，正常情况下不作为普通 bug root cause。
- 如果后续流程发现 `PRD` 本身存在根本矛盾，应停止普通开发流程，进入 `Workflow Exception Review`，讨论为什么 `PRD Phase` 评审没有发现该问题。

### 4.2 SRS Phase

英文名称：`SRS Phase` / `Software Requirements Specification Phase`

参与者：

- Human
- AI

目标：

- 将 `PRD` 转化为可设计、可开发、可测试的软件需求规格。
- 明确系统必须具备的功能、非功能要求、接口、集成关系和验收依据。

核心输出：

- `SRS` 文档。
- `Integration Plan`，如果存在多个模块、子系统或外部系统集成。
- `Acceptance Plan`。
- `Requirement Traceability` 基础信息，如需要。

`S1` 输入：

- 已确认的 `PRD`。
- `PRD supporting artifacts`。

`S3` 输入：

- 已确认的新项目 `PRD`。
- 原系统 `SRS`、功能列表、接口文档、集成说明、代码行为分析、测试材料等参考输入。

确认规则：

- `SRS` 新增必须人类确认。
- `SRS` 变更必须人类确认。

特殊规则：

- `Testing Phase` 必须以 `SRS Phase` 输出的 `Acceptance Plan` 为主要验收依据。
- 如果测试中发现 `Acceptance Plan` 不完整或 `SRS` 存在功能/业务矛盾，应回到 `SRS Phase` 的 `Change Mode`，通过 `CR` 增量更新。

### 4.3 Architecture Phase

英文名称：`Architecture Phase` / `Technical and Business Architecture Design Phase`

参与者：

- AI 输出。
- Human 确认。

目标：

- 基于已确认的 `PRD` 和 `SRS`，设计技术架构和业务架构。
- 明确模块边界、业务流程、数据流、接口边界、技术选型、集成方式和关键风险。

核心输出：

- `Technical Architecture Document`。
- `Business Architecture Document`。
- `Module Boundary`。
- `Business Flow`。
- `Data Flow`。
- `Interface Boundary`。
- `Technology Selection`。
- `Architecture Risk and Tradeoff`。
- `Human Approval Record`。

确认规则：

- `Architecture` 新增必须人类确认。
- `Architecture` 变更必须人类确认。
- 未获得人类确认前，不应进入对应的 `Development Phase`。

### 4.4 Development Phase

英文名称：`Development Phase`

参与者：

- AI 主导。
- Human 仅在出现 `PRD`、`SRS` 或 `Architecture` 变更时介入确认。

目标：

- 基于已确认的 `SRS` 和 `Architecture`，输出可验证的实现。

核心输出：

- `Development Plan`。
- `Development Task Breakdown`。
- `Detailed Design`，当开发任务复杂时必须输出。
- `Unit Test Cases`。
- `Integration Test Cases`。
- `Source Code`。
- `Local Verification Result`。

确认规则：

- `Development Phase` 完成由 AI 自行确认。
- 如果开发过程中发现必须修改 `SRS` 或 `Architecture`，应回到对应阶段，并等待人类确认。

### 4.5 Testing Phase

英文名称：`Testing Phase`

参与者：

- AI 主导。
- Human 仅在缺陷涉及 `PRD`、`SRS` 或 `Architecture` 变更时介入确认。

目标：

- 基于 `SRS Phase` 的 `Acceptance Plan` 对系统进行测试和验收验证。
- 发现问题时输出 `Bug Report`，并根据 root cause 回流到对应阶段。

核心输出：

- `Test Preparation`。
- `Test Environment Description`。
- `Detailed Test Steps`。
- `Test Execution Record`。
- `Test Report`。
- `Bug Report`，如果发现问题。

确认规则：

- `Testing Phase` 完成由 AI 自行确认。
- 测试不得临时发明新的验收标准；如果验收标准不足，应回到 `SRS Phase` 的 `Change Mode`。

### 4.6 Delivery Phase

英文名称：`Delivery Phase`

参与者：

- AI 主导。
- Human 按需确认最终可交付状态。

目标：

- 基于 `Testing Phase` 的输出物完成项目交付准备。

核心输出：

- `Deployment Document`。
- `Installation Guide`。
- `Operations Manual`。
- `Release Notes`，如需要。
- `Delivery Summary`。

确认规则：

- `Delivery Phase` 完成由 AI 自行确认。
- 如果交付准备中发现需求、架构或验收标准问题，应回流到对应阶段。

### 4.7 Retrospective Phase

英文名称：`Retrospective Phase` / `Project Retrospective Phase`

参与者：

- AI 主导。
- Human 按需确认流程优化方向。

目标：

- 回顾整个项目生命周期，识别 AI 能力限制、workflow 问题、阶段设计问题和 token / process waste。
- 输出问题报告和改进方案。

核心输出：

- `Retrospective Report`。
- `Issue Analysis Report`。
- `Workflow Improvement Proposal`。
- `Skill Improvement Proposal`，如需要。
- `Template Improvement Proposal`，如需要。
- `Token Optimization Proposal`，如需要。

分析维度：

- `AI Capability Limitation`：哪些问题来自 AI 能力限制，是否可通过流程或模板规避。
- `Workflow Defect`：哪些问题来自 workflow 设计不合理、阶段缺失、确认点错误或输入输出断裂。
- `Skill Gap`：哪些地方说明现有 skill 不足，是否需要新增或修改 skill。
- `Documentation Gap`：哪些地方说明文档结构或模板不足。
- `Token Waste`：哪些环节消耗了 token 但没有产生足够价值，是否可优化。
- `No-action Finding`：如果没有明显问题，也应记录哪些流程有效、哪些检查可以保持。

确认规则：

- `Retrospective Phase` 完成由 AI 自行确认。
- 如果复盘建议修改 `PRD`、`SRS` 或 `Architecture` 基线，不能在复盘中直接修改，应生成后续变更建议并进入对应阶段的人类确认流程。

## 5. Phase Mode Rule

每个主流程阶段 `skill` 必须支持两种模式。

### 5.1 Full Mode

用途：

- 首次创建该阶段完整产物。
- 用于从 0 建设阶段 baseline。

输入：

- 上一阶段已确认产物。
- 当前阶段所需参考材料。

输出：

- 当前阶段完整 baseline artifact。
- 当前阶段输出给下游的标准输入。

### 5.2 Change Mode

用途：

- bug 回流。
- `CR` 变更。
- review 发现问题。
- 测试失败。
- 上游 baseline 变化。

输入：

- `Bug Report`、`CR`、review finding 或上游变更说明。
- 当前阶段已有 baseline artifact。
- 下游影响范围。

输出：

- 增量变更文档。
- 更新后的阶段产物。
- `Impact Analysis`。
- 下游阶段更新建议。

确认规则：

- 如果当前阶段是 `PRD`、`SRS` 或 `Architecture`，`Change Mode` 输出必须等待人类确认。
- 如果当前阶段是 `Development`、`Testing`、`Delivery` 或 `Retrospective`，通常由 AI 自行确认；但如果引发 baseline 变更，必须回到对应人类确认阶段。

## 6. Backflow Rule

阶段允许回流。回流不是重新执行整个项目，而是进入对应阶段的 `Change Mode`。

### 6.1 SRS Root Cause

触发条件：

- 功能需求矛盾。
- 业务规则不清或冲突。
- `Acceptance Plan` 不完整。
- 测试发现 SRS 无法支持真实业务或验收需求。

流程：

```text
Bug Report
  -> SRS(change)
  -> CR Document
  -> Incremental SRS Update
  -> Human Approval
  -> Architecture(change if needed, human approval)
  -> Development(change)
  -> Testing(change)
```

### 6.2 Architecture Root Cause

触发条件：

- 架构无法满足 `SRS`。
- 模块边界错误。
- 数据流、业务流或接口设计错误。
- 集成方案不可行。
- 非功能需求无法被当前架构满足。

流程：

```text
Bug Report
  -> Architecture(change)
  -> Architecture Document Update
  -> Human Approval
  -> Development(change)
  -> Testing(change)
```

### 6.3 Development Root Cause

触发条件：

- 源代码实现不符合 `SRS`、`Architecture` 或 `Detailed Design`。
- 单元测试遗漏。
- 集成测试遗漏。
- 边界条件处理错误。
- 实现质量问题。

流程：

```text
Bug Report
  -> Development(change)
  -> Development Plan Update or Task Change
  -> Detailed Design Update if complex
  -> Unit / Integration Test Update
  -> Source Code Update
  -> Testing(change)
```

### 6.4 PRD Root Cause

触发条件：

- bug root cause 被判断为 `PRD` high-level product baseline 存在根本矛盾。

流程：

```text
Bug Report
  -> Stop Normal Development
  -> Workflow Exception Review
  -> Analyze why PRD review failed
  -> Decide whether to revise workflow, review gate, PRD template, or project direction
```

特殊规则：

- `PRD Root Cause` 不作为普通 bug 修复处理。
- 不应直接进入 `PRD(change)` 并继续开发。
- 必须先讨论 workflow 是否存在问题。

## 7. Change Request Rule

`CR` 是 `SRS Change Mode` 的标准入口制品。

当 bug、review finding 或测试结果要求修改 `SRS` 时，必须生成 `CR Document`。

`CR Document` 至少应描述：

- `Change Background`
- `Trigger Source`
- `Affected Requirement`
- `Current Behavior or Current Spec`
- `Expected Behavior or Updated Spec`
- `Impact Analysis`
- `Acceptance Plan Change`
- `Downstream Impact`
- `Human Approval Status`

第一版中，`CR` 主要用于 `SRS` 变更。`Architecture` 和 `Development` 变更可引用 `Bug Report`、`CR Document` 或上游变更说明作为输入。后续如有需要，可扩展 `Architecture Change Request` 或 `Development Change Task`。

## 8. Human Approval Rule

必须人类确认的 baseline：

- `PRD`
- `SRS`
- `Architecture`

必须人类确认的动作：

- 新增 `PRD`
- 变更 `PRD`
- 新增 `SRS`
- 变更 `SRS`
- 新增 `Architecture`
- 变更 `Architecture`

AI 可自行确认的阶段完成：

- `Development Phase`
- `Testing Phase`
- `Delivery Phase`
- `Retrospective Phase`

例外：

- 如果 AI 自确认阶段发现需要修改 `PRD`、`SRS` 或 `Architecture`，必须回流到对应阶段，并等待人类确认。

## 9. S1 and S3 Difference

`S1` 和 `S3` 使用同一条主流程。

区别不在 phase，而在输入材料。

### 9.1 S1 Input Pattern

```text
Human Idea
  -> PRD Phase
  -> SRS Phase
  -> Architecture Phase
  -> Development Phase
  -> Testing Phase
  -> Delivery Phase
  -> Retrospective Phase
```

### 9.2 S3 Input Pattern

```text
Human Target
  + Existing System PRD / Product Analysis
  + Existing System SRS / Feature / Interface / Code Analysis
  -> PRD Phase
  -> SRS Phase
  -> Architecture Phase
  -> Development Phase
  -> Testing Phase
  -> Delivery Phase
  -> Retrospective Phase
```

`S3` 中的 `Existing System Analysis` 只作为 `PRD Phase` 和 `SRS Phase` 的参考输入，不作为独立主阶段。

## 10. Open Items For Later Design

以下内容后续再拆，不在本文档中展开：

- 每个 phase 的内部详细步骤。
- 每个 phase 的输入输出模板。
- `Bug Workflow` 的完整子流程。
- `CR Document` 模板。
- `Retrospective Report` 模板。
- 阶段 `skill` 的命名、触发条件和使用方式。
- cross-cutting guardian `skill`，例如 documentation structure、git workflow、quality gate、memory / skill governance。
- 文档目录结构和文件命名规范。
