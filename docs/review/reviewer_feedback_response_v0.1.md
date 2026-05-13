# Reviewer Feedback Response — Proposal v0.1

**Source Review**: `docs/review/skill_set_design_proposal_v0.1_review.md`
**Adopted In**: `docs/design/skill_set_design_proposal_v0.2.md`
**Date**: 2026-05-05
**Reviewed By**: User + Claude

---

## Findings 处置一览

| # | Severity | Finding 摘要 | 处置 | 备注 |
|---|----------|---------------|------|------|
| F1 | High | skill count 22 vs 23 不一致 | **修正** | F6 采纳后，最终 count = 23（不是 22）|
| F2 | High | S3 必备源系统 artifact 可被跳过 | **采纳** | required-artifacts.md 改为 scenario-aware |
| F3 | High | scripts 路径冲突 | **采纳 (B)** | 全文改用 skill 全路径 `skills/.../scripts/...` |
| F4 | High | CR `status: approved` 与 status enum 矛盾 | **采纳** | `approved` 适用范围扩到 PRD/SRS/Architecture/CR |
| F5 | High | S2 路由简化漏 4 子场景 | **采纳** | 补 S2 子场景路由表，progress schema 加 `scenario_subtype` |
| F6 | Medium | development-code-write 无 review | **采纳 (a)** | 新增 `development-code-review` skill；推翻 v0.1 早期"代码不评审"决策 |
| F7 | Medium | revise 动作 owner 模糊 | **采纳** | 明示 revise = `*-write` 在 Change Mode 下完成 |
| F8 | Medium | release lifecycle 未规则化 | **采纳（带用户裁决）** | 加 Release Lifecycle Rule 节；用户定串行规则 |
| F9 | Low | Memory Reference 引用 Claude-local 路径 | **采纳** | 删除 |

## 用户裁决要点

- **F3 (B)**：脚本属于 skill，命令统一 `skills/<skill-name>/scripts/...` 全路径，不在目标项目根做 wrapper
- **F6 (a)**：增加代码评审 skill，推翻前期"代码不评审"决策（用户原话：之前的意见可能不靠谱）
- **F8**：Release 严格串行，不可并发；0.1 → 0.2 → 0.3 顺序

## 由 F6 引发的连带修改

- Stage 4 skill 数从 5 → **6**（development-code-review 加入）
- Layer 1 Vertical 从 17 → **18**
- 总 skill 数从 22 → **23**
- Stage 4 task state 加一段 code-review 循环：`code-writing → code-review → code-revising → code-review-passed → verifying → verified`

## 由 F8 引发的连带规则

- 同时只 1 个 active release（强制串行）
- 新 release 由当前 release Stage 7 完成后启动
- Bug fix 一律 target 当前 active release（旧 release close 后只读，不接受补丁）
- S2 子场景全部映射到"新 release"（S2-1/S2-2/S2-3）；S2-4 转 S3 是"新项目"
- Release close = Stage 7 retrospective 完成（不是 Delivery 完成）

## v0.1 → v0.2 增删差异概览

| 章节 | v0.2 修改 |
|------|----------|
| 1 Executive Summary | 22 → 23、加 development-code-review、加串行 release 提要 |
| 3 Skill Architecture | Layer 1 表加 development-code-review 行；架构决策表加"代码评审"项（推翻原决策）|
| 4 workflow-protocol | Stage 4 task state 矩阵更新；progress schema 加 scenario_subtype 字段 |
| 5 doc-guardian | F2/F3/F4 落地：scenario-aware required-artifacts、全 skill 路径、approved 适用扩展 |
| 6 AGENTS.md Template | 全文 script 路径改为 `skills/.../scripts/...` |
| 7 Pending Work | Task 5 批 1/批 2/批 3 数量更新（22 → 23）|
| **新增章节** | Section 4.12 Release Lifecycle Rule、Section 4.5.1 S2 Sub-routing、Section 4.13 Revise Action Ownership |

## 没有采纳/弱采纳的项

无。9 项 finding 全部采纳；F6 由用户主动推翻自己原决策。
