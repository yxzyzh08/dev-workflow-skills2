---
name: architecture-write
description: dev-workflow-skills2 Stage 3 Architecture 写作 vertical skill。在 progress.md current_stage==architecture-design AND sub_state ∈ {write, revising} 时被 invoke。S1 / S3 在 SRS 完成后由 AGENTS.md Bootstrap 路由；S2-1/S2-2/S2-3 仅当本 release 引入架构变化时由路由进入；Bug Flow root_cause==architecture 时切回 Change Mode。Doc 输出：项目级单文件 architecture.md（全部场景）+ per-release architecture_delta.md（仅本 release 引入架构变化时必备）。S2 / Bug Flow 时本 skill 决定改 architecture.md 还是仅写 architecture_delta；新建 delta 时 frontmatter parent_architecture 指向项目级 architecture.md。本 skill 不评审自身、不直接 mutation progress.md、不写 SRS / Development / Test。
authority: 4
references:
  - references/architecture-template.md
  - references/delta-policy.md
---

# architecture-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（5 项）**：

1. 产出 / 维护项目级 Architecture 主文档（`docs/architecture/architecture.md`）
2. 决定本 release 是否需要 architecture_delta；必要时产出 `docs/release<x.y>/architecture_delta.md`
3. 在 Architecture 主文档与 architecture_delta 之间维护一致性（delta 的 `parent_architecture` 指回主 doc；**长期事实必须在同一轮 write 中同时改主 doc 与 delta**——v0.6 round 1 H3 决议：workflow-protocol release-close 仅改 release_state / release_close_reason / previous_releases，**不**做 delta → 主 doc 自动合并）
4. 完成后跑 doc-guardian validate.py 自检（每改动 doc 一次）→ 调 progress.py update --event write-complete
5. Bug Flow root_cause==architecture 时按 bug 性质决定改 architecture.md 还是 delta（详见 §7.1 Bug 性质 → 改哪份 doc）

**不属于本 skill**：

- 评审 Architecture（→ `architecture-review`）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py`）
- 推进到 Stage 4（必经 `progress.py update --advance`）
- 写 PRD / SRS / Development plan / Test / BUG report / INCIDENT report
- 实施代码（→ `development-*`）
- 决定哪些 bug 是 architecture 类（→ `bug-triage`）

## 2. When to Invoke

**触发条件**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `workflow_incident_active` | `false` |
| `current_stage` | `architecture-design` |
| `sub_state` | `write` 或 `revising` |
| `bug_flow.active` | `false` 或 (`true` AND `bug_flow.root_cause==architecture`) |

**典型 invocation 路径**：

| 时机 | 上游 | Mode |
|------|------|------|
| S1 SRS 完成后首入 Architecture | SRS `--advance` 后 workflow-protocol 切 `current_stage=architecture-design, sub_state=write` | Full Mode：从 0 写 architecture.md |
| S3 SRS 完成后首入 Architecture | 同上 | Full Mode：写 architecture.md（吸收源系统 reuse-replace 决策）|
| S2-1/S2-2/S2-3 + 本 release 改架构 | scenario-dispatcher / workflow-protocol 路由（Stage 3 是否进入由 SRS 影响范围决定）| Change Mode：改 architecture.md 或新建 architecture_delta；详见 §3 |
| S2-1/S2-2/S2-3 + 本 release **不改**架构 | workflow-protocol 在 Stage 2 advance 时直接跳过 Stage 3 进 Stage 4（具体由状态机配置；详见 workflow-protocol §6）| 本 skill 不被 invoke |
| Bug Flow re-entry: root_cause==architecture | `bug-triage` 调 `progress.py bug-start --root-cause architecture` 后切 `current_stage=architecture-design, sub_state=write, bug_flow.active=true` | Change Mode：按 §7.1 Bug 性质表决定改 architecture.md 还是 delta |
| Revise | `architecture-review` issues-found 触发 `--event review-issues`，状态机自动转 `revising` | Change Mode |

**不被 invoke 的时机**：

- `current_stage != architecture-design`
- `sub_state ∈ {in-review, review-passed, approved}` → 非 write owner 期
- `bug_flow.active==true AND bug_flow.root_cause != architecture` → 其他 root_cause 切到对应 stage write skill
- `workflow_incident_active==true`
- `project_state ∈ {aborted, reconstructing}`

## 3. Full Mode vs Change Mode + Delta 决策

| Scenario | Mode | architecture.md 改？ | architecture_delta 新建？ |
|---------|------|---------------------|--------------------------|
| S1 | Full | 是（从 0 写）| 否（首 release 由 architecture.md 全权承担）|
| S3 | Full | 是（从 0 写，吸收源系统 reuse-replace）| 否（首 release）|
| S2-x + 本 release 引入架构变化 | Change | **决定 1**：改主 doc 还是建 delta？见下方决策树 | 视决策 1 |
| S2-x + 本 release 仅文档级修订（无运行时架构变化）| Change | 仅改主 doc（typo / 描述清晰化）| 否 |
| Bug Flow root_cause==architecture | Change | 视 bug 性质（见 §7.1）| 视 bug 性质 |

### 3.1 architecture.md vs architecture_delta 决策树（v0.6 round 1 H3 收敛为 2 分支）

```
本次改动是否引入运行时架构差异？（如新组件 / 接口变更 / 数据流改变 / 部署拓扑改变）
├ 否 → 仅改 architecture.md（视为文档级修订；走 §6 4-step）
└ 是 → 进一步判断
        ├ 改动是本 release 局部（不影响 release close 后下一 release 的"长期架构事实"）
        │   → 仅写 architecture_delta；不动 architecture.md
        │     （主 doc 保持 release-N-1 状态；下次 release 仍以未变的主 doc 为起点；
        │      本 release 的局部改动作为历史记录留在 release<x.y>/ 目录下）
        └ 改动是长期事实（下个 release 起点应包含本变化）
            → **同一轮 write 中同时改 architecture_delta + architecture.md**：
              delta 描述本 release 增量 / 时间线说明；
              architecture.md 反映新长期事实（接口签名 / 组件清单 / 部署假设 等已更新）
              （v0.6 round 1 H3 决议：workflow-protocol 没有 release-close delta-merge hook；
               长期事实必须 architecture-write 自己一次性同步两份 doc；
               不能依赖任何"延迟合并到 release-close 阶段"的路径）
```

**保守原则**：决策不清时倾向归类"长期事实"路径，主 doc + delta 同步改；让 architecture-review 评审是否过度。本 batch 移除 v0.6 round 1 之前的"延迟合并"分支——它依赖 workflow-protocol release-close hook，但该 hook 在 command-reference §5 中并不存在。

### 3.2 architecture_delta 的 frontmatter

```yaml
---
title: Release <x.y> Architecture Delta
type: architecture-delta
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/architecture-write
release: "<x.y>"
parent_architecture: docs/architecture/architecture.md
---
```

**`parent_architecture` 必填**：明确 delta 基于的主 doc 路径。doc-guardian validate.py 类 5（Cross-Reference）会校验该路径文件存在。

## 4. Doc Output Contract

### 4.1 主输出（按场景必备）

| Doc Type | 路径 | Frontmatter `type` | 必备性 |
|---------|------|-------------------|--------|
| Architecture | `docs/architecture/architecture.md` | `architecture` | 全部场景必备；项目级单文件 |
| Architecture Delta | `docs/release<x.y>/architecture_delta.md` | `architecture-delta` | **本 release 引入架构变化时必备**（具体由 doc-guardian/required-artifacts.md DSL 决定）|

### 4.2 主 doc Frontmatter

```yaml
---
title: <project> Architecture
type: architecture
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/architecture-write
---
```

不携带 `release` 字段（项目级 doc）。

## 5. 4-Step Standard Procedure（每 doc 走一遍）

```
Step 1. 写/修 doc body
        - 主 doc 改：从 0 写（Full Mode）或 diff（Change Mode）
        - delta 新建：从 0 写 architecture_delta（含 parent_architecture 字段）
        - 同时改主 doc + delta（§3.1 决策长期事实路径）：先改 delta 再回写主 doc 关键决策

Step 2. 加 Pending Changes 段
        - 主 doc / delta 各自的 ## Pending Changes
        - Bug Flow 时关联 BUG-NNN

Step 3. 跑 changelog.py promote
        - 对每个改动的 doc 单独跑

Step 4. 跑 validate.py file 自检
        - 对每个改动的 doc 单独跑
        - delta 时：guardian 校验 parent_architecture 指向主 doc 存在 + frontmatter release 与当前 release 一致

Step 5. 提交 review
        - skills/workflow-protocol/scripts/progress.py update --event write-complete
        - 主 doc + delta 一并提交（不允许部分 submit）
```

## 6. Stage Done Conditions

Stage 3 Architecture 推进到 Stage 4 Development 由 `progress.py update --advance` 触发：

| 维度 | 检查 | 责任方 |
|------|------|--------|
| **A. 必需 artifacts 存在** | `artifacts.architecture` 存在；本 release 改架构时 `artifacts.architecture_delta` 也存在 | architecture-write Step 1 + Step 4 |
| **B. doc-guardian 校验通过** | `validate.py file <each artifact>` exit 0；delta 类 5 cross-ref 通过 | architecture-write Step 4；advance 时 double-safety |
| **C. Review 通过** | `architecture-review` 最近一轮输出 `review-passed`（覆盖主 doc + delta，若有改动）| architecture-review |
| **D. 人确认** | `apply_update_advance` 校验 `progress.md.sub_state == approved`（即 `progress.py update --event human-confirmed` 已 fire；progress-history.md 自动有对应条目）；每改动 doc frontmatter `status: approved` 由 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path>`（多 doc 重复 `--doc`）同步（B 维度 validate.py file 复检）。advance 不在 D 维度独立重读 doc.status；事实源 command-reference §2.2 + Phase 7 P4 polish。 | 人 gate |

**E 维度不适用**：Architecture 是设计 doc，Stage 3 阶段无内部 verification（运行时验证在 Stage 5/6）。

## 7. Bug Flow Re-entry

`bug-triage` 判定 `root_cause==architecture` 时切回本 stage：

```
1. bug-triage 判 root_cause=architecture；写 BUG-NNN.md frontmatter
2. bug-triage 调 skills/workflow-protocol/scripts/progress.py bug-start --bug docs/bug/BUG-NNN.md --root-cause architecture
3. workflow-protocol mutation:
   - bug_flow.active = true
   - bug_flow.bug_report_path = docs/bug/BUG-NNN.md
   - bug_flow.root_cause = architecture
   - current_stage: testing → architecture-design
   - sub_state: review-passed → write
   - review_iteration: 0
4. 本 skill 被路由 invoke：Change Mode 应对 bug
   - 读 docs/bug/BUG-NNN.md body 决定 bug 性质（见下表）
   - 走 §5 标准 4-step（仅修 bug 涉及部分）
   - Pending Changes 关联 BUG-NNN
5. write-complete → architecture-review → review-passed
6. 人 gate（D 维度仍要求；Bug Flow 不绕过）
7. 推 advance（路径由 workflow-protocol 决定：可能进 Stage 4 或直接回 Stage 5）
```

### 7.1 Bug 性质 → 改哪份 doc（v0.6 round 2 M2 对齐 H3 保守方向）

| Bug 性质 | 改 architecture.md | 改 architecture_delta | 备注 |
|---------|---------------------|----------------------|------|
| 主 doc 描述错误（与运行时实现不符）| 是 | 否 | 运行时实现是事实；改主 doc 让其反映 |
| delta 描述错误（与本 release 实现不符）| 否 | 是 | 仅本 release 范围 |
| 运行时架构有 bug（实现层缺陷反推到设计）| 通常是 | 是 | 长期事实候选：bug 暴露的架构问题大概率影响下个 release 起点 |
| 集成 / 接口 bug 暴露架构假设错误 | 是 | 是 | 长期事实层；下个 release 应基于修订后主 doc |
| 性能 / 容量假设需修订 | 是 | 是 | 同上 |

**保守路径（v0.6 round 2 M2 修正）**：不确定时**按"长期事实候选"处理**——同轮 write 中同时改 `architecture_delta.md` + `docs/architecture/architecture.md`，并在 delta body 标注"需 architecture-review 确认是否过度同步主 doc"。若最终 review 认为只是本 release 局部改动，再由 architecture-write 在下一轮 revise 中移除主 doc 改动。这与 H3 决议一致：**不**依赖任何 release-close hook 自动合并，**避免**长期事实漏写主 doc 导致下一 release 起点错误。

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 跳过 `skills/doc-guardian/scripts/validate.py file` 直接 write-complete
- ❌ 跳过 `skills/doc-guardian/scripts/changelog.py promote` 直接编辑 `## Change Log`
- ❌ 自行评审本 skill 产出（→ `architecture-review`）
- ❌ 在 `sub_state==in-review` 时继续修改 doc body
- ❌ 自行设置 frontmatter `status: approved`（人 gate；mutation owner = `skills/doc-guardian/scripts/status_transition.py`，在 `skills/workflow-protocol/scripts/progress.py update --event human-confirmed` 成功后调用 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path> ...` 同步；**Gap-2**）
- ❌ 创建多份 architecture.md（项目级单文件；多 release 共享同一 `docs/architecture/architecture.md`）
- ❌ delta frontmatter `parent_architecture` 指向不存在或非主 doc 的路径
- ❌ 改 release close 后历史 release 目录下的 architecture_delta（只读）
- ❌ 在 `current_stage != architecture-design` 时被 invoke 仍继续操作
- ❌ 在 `bug_flow.active==true AND bug_flow.root_cause != architecture` 时被 invoke
- ❌ 在 `workflow_incident_active==true` 时操作
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时操作
- ❌ 部分 doc write-complete（主 doc + delta 同时改时必须一起 submit）
- ❌ 把"长期事实"改动仅写在 delta 而期待 release-close 阶段被自动合并到主 doc（v0.6 round 1 H3 决议：workflow-protocol 没有该 hook；长期事实必须本 skill 在同一轮 write 中同步改主 doc + delta）
- ❌ 修改 BUG-NNN.md（→ bug-triage / testing-write）
- ❌ 自行决定推进 stage（→ workflow-protocol advance）
- ❌ 评审循环超 7 次仍尝试 revise

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| validate.py 失败（主 doc 或 delta）| 读 stderr 修；3 次仍失败升级人介入 |
| delta `parent_architecture` 路径校验失败（类 5 cross-ref）| 修正 frontmatter 字段；不要静默改 architecture.md 路径 |
| `progress.py update --event write-complete` 失败（review_iteration > 7）| 升级人介入 |
| §3.1 决策不确定（不知改主 doc 还是 delta）| **保守按"长期事实候选"处理（v0.6 round 2 M2）**：同轮改 delta + architecture.md；在 delta body 标注"待 architecture-review 确认是否过度同步主 doc"；若 review 反馈"仅本 release 局部"再 revise 移除主 doc 改动。**不**只改 delta（避免长期事实漏写主 doc；H3 决议无 release-close 合并 hook）|
| Bug Flow 时主 doc 改了，但其他 active stages（dev / testing）已基于旧主 doc 完成工作 | 不要回滚那些 stages 的产物；让 workflow-protocol advance 路径决定后续 stage 是否需重审；本 skill 不直接处理跨 stage 影响 |
| 用户在人 gate 前发现 architecture 问题 | **design gap**：当前 spec 无 `review-passed → revising` 事件；不要手工编辑 progress.md；升级人介入或在 design proposal 增加新事件后再修 |
| Doc 物理损坏 / 误删 | 从 git 恢复；本 skill 不重建 doc body |
| release close 后试图改历史 release 的 architecture_delta | 拒绝；historic release 目录只读；用户须新 release 写新 delta |

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机、bug-start mutation、release-close mutation（**不含** delta → 主 doc 合并 hook；v0.6 round 1 H3 决议）
- `skills/workflow-protocol/references/command-reference.md` — `update --event` / `bug-start` / `release-close` 完整签名（§5 release-close 仅改 release_state / release_close_reason / previous_releases）
- `skills/doc-guardian/SKILL.md` — 校验入口
- `skills/doc-guardian/references/frontmatter-schema.md` — architecture / architecture-delta frontmatter 与 status 状态机
- `skills/doc-guardian/references/required-artifacts.md` — 何时 architecture_delta 必备的 DSL 推导
- `skills/doc-guardian/references/change-log-format.md` — Pending Changes / Change Log
- `skills/doc-guardian/references/directory-layout.md` — `docs/architecture/` + `docs/release<x.y>/` 目录
- `skills/architecture-review/SKILL.md` — review 接管点
- `skills/srs-write/SKILL.md` — Stage 2 接力点（架构需求由 SRS 输入）
- `skills/bug-triage/SKILL.md` — root_cause==architecture 来源

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/architecture-template.md` — architecture.md 主文档（10 章节：Overview / System Context / Component Catalog / Interfaces / Data Flows / Data Model / Deployment / Operational / ADR）+ architecture_delta.md（5 章节，含 Long-Term Fact Sync 表）模板 + 写作准则 + Common Pitfalls（Phase 7 Task 7-B 拆出）
- `references/delta-policy.md` — §3.1 决策树展开：长期事实 vs 本 release 局部判别 heuristic（7 类长期事实信号 + 6 类局部信号 + 5 类模糊场景保守处理）+ Bug Flow 性质表（SKILL.md §7.1 展开）+ 同步两份 doc 的 4-step 操作 + 与 architecture-review 维度 6 校验对照（Phase 7 Task 7-B 拆出）


**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
