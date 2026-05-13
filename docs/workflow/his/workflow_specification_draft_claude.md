# Workflow Specification Draft (流程规范草案)

**Status**: Draft v0.1
**Date**: 2026-05-05
**Authors**: Human + AI 协同设计

---

## 1. Purpose & Scope (目的与范围)

dev-workflow-skills2 是一套面向个人使用的 R&D workflow skill 集合，定义围绕单个产品/项目展开的研发流程。本规范确定主流程、Bug 流程、4 个使用场景的映射，以及阶段间的协作规则。所有后续 skill 的设计均以本规范为根据。

本草案为 high-level 框架定义，不涉及单个 skill 的内部子步骤细节（这些将在后续讨论中补全）。

---

## 2. Scenarios (使用场景)

| Code | Name | 描述 |
|------|------|------|
| S1 | Greenfield | 从 0 打造一个新产品/项目 |
| S2 | Evolution | 在已规范化的项目上新增需求；新需求一律视为大需求 |
| S3 | Refactoring | 已存在的项目按本工作流重建为新项目，可复制/增强/裁剪原功能 |
| S4 | Bug Fix | 修复已规范化项目中的缺陷 |

S1、S3 是项目"诞生"场景（二选一）。S2、S4 是项目运行期反复发生的场景。

---

## 3. Main Workflow (主流程)

主流程包含 7 个阶段，适用于 S1、S2、S3。S4 走独立的 Bug Flow（见 §4）。

| # | Stage | Lead | Human Gate | Outputs |
|---|-------|------|------------|---------|
| 1 | PRD Inception (PRD 立项) | Human + AI | ✓ | PRD + Supporting Artifacts（如 Competitor Research、Competitor Architecture Comparison 等）|
| 2 | SRS Specification (SRS 调研) | Human + AI | ✓ | SRS + Acceptance Plan + Integration Plan（多模块时） |
| 3 | Architecture Design (架构设计) | AI | ✓ | Technical Architecture + Business Architecture |
| 4 | Development (开发) | AI | × | Development Plan + Task Breakdown + Detailed Design + Unit Tests + Integration Tests + Source Code |
| 5 | Testing (测试) | AI | × | Test Report + Test Preparation + Test Procedure +（Bug Report，如有） |
| 6 | Delivery (交付) | AI | × | Deployment Doc + Operation Manual + Installation/Deployment Artifacts |
| 7 | Project Retrospective (项目复盘) | AI | × | Issue Report（按 AI Capability / Workflow / Token Waste 分类）+ Improvement Proposals |

### 3.1 Human Gates (人确认边界)

- **Gate-required stages**: PRD Inception、SRS Specification、Architecture Design（共 3 个阶段）
- **AI-autonomous stages**: Development、Testing、Delivery、Retrospective（共 4 个阶段）

### 3.2 Stage Transitions (阶段流转)

主流程默认线性推进：1 → 2 → 3 → 4 → 5 → 6 → 7。回流（backflow）仅通过 Bug Flow 触发（即 Stage 5 测试发现 bug 时）。

---

## 4. Bug Flow (Bug 流程)

由 Stage 5 Testing 触发，或在 S4 场景下由交付后的缺陷报告触发。流程：先生成 Bug Report，根据根因分类后路由到对应阶段以变更模式重新执行。

| Root Cause | Routing Path |
|------------|--------------|
| SRS | CR Document → SRS Update → Architecture Update? → Development Plan → Detailed Design? → Development → Testing |
| Architecture | Architecture Update（仅存变更历史）→ Development Plan → Detailed Design? → Development → Testing |
| Development | Development Plan → Detailed Design? → Development → Testing |
| PRD (Exception) | 项目暂停 → 触发工作流反思（escape valve） |

**说明**：
- 路径中 `?` 表示按需生成（如开发任务复杂时才需详细设计）
- PRD 根因属异常逃生阀，几乎不应触发——若触发则意味工作流自身有问题，需在工作流层面反思而非在项目层面修复

---

## 5. Scenario-to-Flow Mapping (场景到流程的映射)

| Scenario | Flow | Input Parameters |
|----------|------|------------------|
| S1 Greenfield | Main Workflow 1 → 7 | 无 |
| S2 Evolution | Main Workflow 1 → 7（incremental mode） | 当前项目的 PRD / SRS / Architecture |
| S3 Refactoring | Main Workflow 1 → 7 | 源系统 PRD + 源系统 SRS（在 Stage 1、2 中作为参考输入） |
| S4 Bug Fix | Bug Flow | Bug Report |

---

## 6. Key Rules (关键规则)

### 6.1 Change Records (变更记录)

| Stage | Change Record Required |
|-------|------------------------|
| PRD Inception | 一般不应出现 PRD 变更；若出现则需触发工作流反思 |
| SRS Specification | 必须生成 CR (Change Request) Document，作为对外契约的正式变更记录 |
| Architecture Design | 仅保存变更历史（version history），不需 CR |
| Development / Testing / Delivery / Retrospective | 无特殊变更记录要求 |

### 6.2 Skill Reuse Strategy (Skill 复用策略)

主流程 7 阶段对应 7 个 skill。每个 skill 内部同时支持两种模式：

- **Full Mode (全量模式)**: 从零产出该阶段的完整文档
- **Delta Mode (增量/变更模式)**: 在既有产物基础上做增量或变更

一套 skill 通过模式切换，统一覆盖 4 个场景：S1（首次产出）、S2（在主流程内增量）、S3（基于源系统输入产出）、S4（Bug 流程下的局部变更）。

### 6.3 Meta-Evolution Loop (元演进闭环)

两条路径汇入工作流自身的演进：

- **Project Retrospective (Stage 7)**: 项目正常结束后产出工作流改进建议
- **PRD Root Cause (Bug Flow Exception)**: 异常触发时暴露出工作流问题

后续可能需要一个独立的 cross-cutting "workflow evolution" skill 消化这两类输入。

---

## 7. Open Items (待定项)

以下内容尚未在本草案中固化，将在后续讨论中补全：

- Cross-cutting skills 的具体清单与定义（包括 Document Guardian、CR Guardian 等）
- 每个主流程 skill 的内部子步骤、产出格式细节
- Acceptance Plan 的标准结构与 Acceptance Test 的执行约定
- Integration Plan 的适用条件与格式定义
- Bug Report 的标准结构与根因分类规则
- 工作流自身演进机制（如何把复盘产出落地为流程改进）
- Document directory structure 与 file naming convention（由 Document Guardian 定义）

---

## 8. Document Conventions (本文档约定)

- 文件命名：英文 + `_claude.md` 后缀
- 目录：英文
- 专业术语：英文（首次出现时附中文注释）
- 描述性文本：中文
