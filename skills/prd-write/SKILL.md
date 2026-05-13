---
name: prd-write
description: dev-workflow-skills2 Stage 1 PRD 写作 vertical skill。在 progress.md current_stage==prd-inception AND sub_state ∈ {write, revising} 时被 invoke。S1 / S3 init 后由 AGENTS.md Bootstrap 路由；S2-1 启动 release 后由 scenario-dispatcher 路由。Full Mode 写新 PRD（S1/S3）；Change Mode 修订既有 PRD（S2-1）。S3 时额外产出 source-system-analysis 类 supporting artifacts（prd-level + feature-matrix）。完成 doc 后必经 doc-guardian validate.py 校验 + 调 progress.py update 进入 in-review 由 prd-review 接管。本 skill 不评审自身产出、不直接 mutation progress.md、不写 SRS / Architecture / Bug Report；prd-exception 不会触发本 skill Change Mode（由 workflow-evolution 处理）。
authority: 4
references:
  - references/prd-template.md
---

# prd-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（与其他 vertical stage skill / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（5 项）**：

1. 产出 PRD 主文档（`docs/prd/prd.md`）的 doc body + 合规 frontmatter
2. 维护 PRD 的 Change Log（Pending Changes → `changelog.py promote` → Change Log）
3. **S3 场景**额外产出 supporting artifacts：`source-system-analysis`（`analysis_kind: prd-level` + `feature-matrix`）
4. 完成后跑 doc-guardian `validate.py file <path>` 自检 → exit 0 才能提交 review
5. 调 `progress.py update --event write-complete` 进入 `sub_state: in-review`，把控制权交给 `prd-review`

**不属于本 skill**：

- 评审 PRD（→ `prd-review`）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `skills/workflow-protocol/scripts/progress.py`）
- 推进到 Stage 2（必经 `progress.py update --advance`，且需满足本 stage A/B/C/D 4 维度）
- 写 SRS / Architecture / Bug Report / INCIDENT report（→ 对应 stage skill / orchestration skill）
- 创建 supporting artifacts 之外的 doc（如 `competitor_research.md` 由用户/调研活动产出，非本 skill 强制产物）
- 处理 PRD 异常（`bug_flow.root_cause==prd-exception` → 不切本 skill Change Mode；由 `bug-triage` 调 `incident-start`，`workflow-evolution` 接管）

## 2. When to Invoke

**触发条件（本 skill 是 owner 当且仅当 progress.md 满足）**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active`（aborted / reconstructing 时拒绝） |
| `release_state` | `active` |
| `bug_flow.active` | `false`（Bug Flow 期间不入本 skill；prd-exception 走 workflow-evolution） |
| `workflow_incident_active` | `false` |
| `current_stage` | `prd-inception` |
| `sub_state` | `write` 或 `revising` |

**典型 invocation 路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| S1 新项目首入 PRD | `scenario-dispatcher` 调 `progress.py init --scenario S1` 后，AGENTS.md Bootstrap §6 路由到 `prd-write` | Full Mode 写新 PRD |
| S3 重构项目首入 PRD | `scenario-dispatcher` 调 `progress.py init --scenario S3` 后路由 | Full Mode 写新 PRD + S3 必备 supporting artifacts |
| S2-1 启新 release 修 PRD | `scenario-dispatcher` 调 `progress.py release-start --scenario S2-1` 后路由 | Change Mode 改既有 PRD |
| 评审反馈触发 revise | `prd-review` 调 `progress.py update --event review-issues`（业务上即 issues-found）后状态机自动转 `sub_state: revising`（见 workflow-protocol command-reference.md §2.1 转移表）| Change Mode 修订并应对 review findings |

**不被 invoke 的时机**：

- `current_stage != prd-inception`（即使 `sub_state==write`）→ scenario-dispatcher / AGENTS.md Bootstrap 不应路由到本 skill
- `sub_state ∈ {in-review, review-passed, approved}` → 不属于 write owner 期；in-review 由 `prd-review` 接管
- `scenario ∈ {S2-2, S2-3, S4}` → 这些场景不改 PRD（S2-2/S2-3 改 SRS；S4 不改 PRD）
- `bug_flow.active==true` 或 `workflow_incident_active==true` → 异常路径，由 bug-triage / workflow-evolution 接管

## 3. Full Mode vs Change Mode

| Scenario | Mode | 入口条件 | 主要工作 |
|---------|------|---------|---------|
| S1 | **Full** | `progress.py init --scenario S1` 后 `current_stage=prd-inception, sub_state=write` | 从 0 写 PRD 主体 + Change Log §Pending 加 "Initial PRD draft" |
| S3 | **Full** | `progress.py init --scenario S3` 后 `current_stage=prd-inception, sub_state=write` | 从 0 写 PRD 主体 + 写 supporting artifacts（prd-level + feature-matrix）+ Change Log §Pending 加 "Initial PRD with source system analysis" |
| S2-1 | **Change** | `progress.py release-start --scenario S2-1` 后 `current_stage=prd-inception, sub_state=write`，artifact `prd` 路径不变指向既有 `docs/prd/prd.md` | 编辑既有 PRD 章节 + Change Log §Pending 记录每条 diff（增/改/删 哪一节）+ 不动 `created` 字段、更新 `updated` |
| Revise（任意 mode）| **Change** | review-passed 之前任意 review 输出 issues-found 后 → `sub_state=revising` | 按 `prd-review` 输出的 finding 列表修；每条 finding 对应 1 条 Pending Changes |

**Mode 区分的实质**：

- **Full Mode**：PRD 全文是新写的；S3 时还要写 supporting artifacts
- **Change Mode**：PRD 已有内容；本次仅做 diff；Change Log 每个 Pending Changes 必须能映射回具体改动
- 两 mode 的 4-step 标准流程（§5）一致；区别仅在 doc body 是 from-scratch 还是 incremental

## 4. Doc Output Contract

### 4.1 主输出（所有场景必备）

| Doc Type | 路径 | Frontmatter `type` | 备注 |
|---------|------|-------------------|------|
| PRD | `docs/prd/prd.md` | `prd` | 项目级单文件；S2-1 Change Mode 在原文件上修；不创新文件 |

### 4.2 S3 场景必备 supporting artifacts

| Doc Type | 路径 | Frontmatter | 备注 |
|---------|------|-------------|------|
| source-system-analysis | `docs/prd/supporting/source_product_prd_analysis.md` | `type: source-system-analysis`, `analysis_kind: prd-level`, `release: null`, `source_system_name: <name>` | 源系统 PRD 分析 |
| source-system-analysis | `docs/prd/supporting/feature_matrix.md` | `type: source-system-analysis`, `analysis_kind: feature-matrix`, `release: null`, `source_system_name: <name>` | 功能矩阵（必备）|

**事实源**：完整的 scenario-aware 必备清单见 `skills/doc-guardian/references/required-artifacts.md`；本表仅列本 skill 直接产出的部分。

### 4.3 Optional supporting artifacts（不强制）

`docs/prd/supporting/` 下用户可选放：`competitor_research.md` / `competitor_architecture.md` / `market_research.md` / `user_scenario_analysis.md` / `non_goals.md` / `risk_analysis.md` 等。这些**非必备**，本 skill 不主动创建；validate.py 不要求其存在。但若用户/调研活动已产出，frontmatter `type` 必须使用 `skills/doc-guardian/references/frontmatter-schema.md` 已注册的具体 optional type（如 `competitor-research` / `competitor-architecture` / `market-research` / `user-scenario-analysis` / `non-goals` / `risk-analysis`）；**禁止使用未注册的伞 type 名 `prd-supporting`**（v0.6 round 1 L1 修正）。

### 4.4 Frontmatter 必备字段（Universal + Per-type）

```yaml
---
title: <human readable>
type: prd
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/prd-write
---
```

`status` 状态机：`draft` → `in-review` → (`revising` ↔ `in-review`) → `review-passed` → `approved`（人 gate 后）。

完整 schema 与 per-type 扩展见 `skills/doc-guardian/references/frontmatter-schema.md`。

## 5. 4-Step Standard Procedure

每次 write/revise 循环（无论 Full / Change Mode）严格按本流程：

```
Step 1. 写/修 doc body
        - Full Mode: 从 0 写 PRD 章节 + frontmatter
        - Change Mode: 在既有文件上做 diff；不动 created；更新 updated
        - S3: 同步写 supporting artifacts（prd-level + feature-matrix）

Step 2. 加 Pending Changes 段（仅增量类 doc：PRD 主文档）
        - 在 PRD doc 末尾 ## Pending Changes 节加新条目
        - 每条 Pending Changes 描述本次改动的语义（不是 git diff 行级）
        - Change Mode 时一条改动对应一条 Pending Changes
        - **source-system-analysis snapshot 类不走本步**（v0.6 round 1 M1）：snapshot doc 表示一次性源系统分析快照，不含 Pending Changes / Change Log（事实源 doc-guardian/references/change-log-format.md）；只写 body + frontmatter

Step 3. 跑 changelog.py promote（仅增量类 doc）
        - skills/doc-guardian/scripts/changelog.py promote docs/prd/prd.md
        - 把 ## Pending Changes 内容移到 ## Change Log 对应日期分组
        - 移动后 ## Pending Changes 必须为空
        - **不对 source-system-analysis 跑 promote**（v0.6 round 1 M1）

Step 4. 跑 validate.py file 自检（每 doc 都跑）
        - skills/doc-guardian/scripts/validate.py file <doc-path>
        - 期望 exit 0
        - exit 1 → 读 stderr 修复 → 重跑（最多重试 3 次后升级人介入）
        - S3 时对每个 supporting artifact 单独跑一次 validate.py（含 source-system-analysis）

Step 5. 提交 review（统一一次，覆盖所有改动 doc）
        - skills/workflow-protocol/scripts/progress.py update --event write-complete
        - 转 sub_state: write/revising → in-review
        - 控制权移交给 prd-review skill；本 skill 退出
```

**关键约束**：

- Step 3 之前 doc 不应被认为完成（Change Log 未刷）
- Step 4 失败时**禁止**直接调 progress.py update（会被 P6 §B 维度拒绝）
- Step 5 调用前必须确认 Step 4 全部 exit 0（含 supporting artifacts）

## 6. Stage Done Conditions

Stage 1 PRD 推进到 Stage 2 SRS 由 `progress.py update --advance` 触发，本 skill 必须先满足以下 4 维度（事实源：workflow-protocol §5）：

| 维度 | 检查 | 责任方 |
|------|------|--------|
| **A. 必需 artifacts 存在** | `artifacts.prd` 文件存在；S3 时 `docs/prd/supporting/source_product_prd_analysis.md` + `feature_matrix.md` 也存在 | prd-write 在 §5 Step 1 写、Step 4 自检 |
| **B. doc-guardian 校验通过** | `validate.py file <each artifact>` 全部 exit 0 | prd-write Step 4 自检；workflow-protocol 在 advance 时再跑一次 double-safety |
| **C. Review 通过** | `prd-review` 最近一轮输出 `review-passed`（PRD 主文档；S3 时 supporting artifacts 也走 review） | `prd-review` 输出 |
| **D. 人确认** | `apply_update_advance` 校验 `progress.md.sub_state == approved`（即 `progress.py update --event human-confirmed` 已 fire；progress-history.md 自动有对应条目）；PRD frontmatter `status: approved` 由 `status_transition.py apply --event human-confirmed --doc docs/prd/prd.md` 同步（B 维度复检）。advance 不在 D 维度独立重读 doc.status——P4 polish 后的 wording，事实源 command-reference §2.2。 | 人 gate；用户在 review-passed 后手动确认 |

**E 维度不适用**：PRD 是 conceptual / business doc，无内部 verification（无 unit test / integration test / installation 概念）。

**`--advance` 失败时**：本 skill 须根据失败维度回到对应步骤：

- A 失败 → 检查 supporting artifacts 是否漏写（S3 时常见）
- B 失败 → 重跑 §5 Step 3-4
- C 失败 → 等 prd-review 完成 review-passed
- D 失败 → 等用户确认；不要自行改 frontmatter `status: approved`（必须人 gate）

## 7. Bug Flow Re-entry

**关键规则**：本 skill **不会**通过 Bug Flow 被 re-entry。

理由：

- Bug Flow `root_cause` 4 类：`srs` / `architecture` / `development` / `prd-exception`
- `root_cause==prd-exception` 不走 PRD Change Mode，而是由 `bug-triage` 调 `progress.py incident-start` 进 `workflow-incident-analysis` stage，由 `workflow-evolution` skill 接管 + 用户决策（continue / abort / reconstruct）
- 其他 3 类（srs / architecture / development）不影响 PRD

因此本 skill 仅通过以下两条路径被 invoke：

1. **首次写 PRD**：S1 / S3 init 之后
2. **S2-1 Change Mode**：新 release 启动后修 PRD

**不会**因 Stage 5 testing 失败而被切回（该路径仅切到 srs / architecture / development write skill）。

**例外说明（design gap）**：当前 workflow-protocol command-reference.md §2.1 转移表未提供 `review-passed → revising` 的事件转换。若用户在 prd-review review-passed 后、人 gate 之前发现 PRD 错误想改，目前**无 in-spec 路径**回到 `revising`；必须升级人介入，或由新一轮 design proposal 在事件白名单中增加相应 event 后才能修。该路径**不**经 Bug Flow（`prd-exception` 是 testing 阶段触发的 PRD 异常 incident path，与本 case 不同）。

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 跳过 `skills/doc-guardian/scripts/validate.py file` 直接调 `progress.py update --event write-complete`
- ❌ 跳过 `skills/doc-guardian/scripts/changelog.py promote` 直接编辑 `## Change Log` 章节
- ❌ 自行评审本 skill 产出（`prd-review` 才是 review owner；本 skill 输出 `review-passed` / `issues-found` 一律违规）
- ❌ 在 `sub_state==in-review` 时继续修改 doc body（in-review→revising 由 `prd-review` 调 `progress.py update --event review-issues` 触发，不是 prd-write 自己调；本 skill 在 in-review 期间不可动 doc）
- ❌ 自行设置 frontmatter `status: approved`（人 gate；mutation owner = `skills/doc-guardian/scripts/status_transition.py`，在 `skills/workflow-protocol/scripts/progress.py update --event human-confirmed` 成功后调用 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path> ...` 同步；**Gap-2**）
- ❌ 在 `current_stage != prd-inception` 时被 invoke 还继续操作（应让 caller 重新路由）
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时操作（终态；progress.py 会拒绝任何 mutation）
- ❌ 在 `bug_flow.active==true` 或 `workflow_incident_active==true` 时被 invoke 仍继续操作（应让 bug-triage / workflow-evolution 接管）
- ❌ S2-1 Change Mode 时新建 `docs/prd/prd_v2.md` 等附加文件（PRD 是项目级单文件；多 release 复用同一 `docs/prd/prd.md`，靠 Change Log 区分版本）
- ❌ S3 场景跳过 supporting artifacts（`source_product_prd_analysis.md` + `feature_matrix.md` 必备；validate.py P6 §A 维度会拒绝）
- ❌ 自行决定推进 stage（必经 `progress.py update --advance` 经 workflow-protocol 校验 4 维度）
- ❌ 评审循环超 7 次仍尝试 revise（必须升级人介入；progress.py 第 8 次 `--event review-issues` 因 `review_iteration > 7` 会被拒）

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| `validate.py file` 失败（frontmatter 字段缺失 / Path 不合规 / Cross-Reference 失效）| 读 stderr → 修 doc → 重跑；3 次仍失败升级人介入 |
| `changelog.py promote` 失败（`## Pending Changes` 章节不存在 / `## Change Log` 章节格式损坏）| 按 `skills/doc-guardian/references/change-log-format.md` 修复 doc 章节结构后重跑 |
| `progress.py update --event write-complete` 失败（review_iteration > 7 / sub_state 不合法转换）| 读 stderr；超 7 次升级人介入；sub_state 不对则先 query 看当前 state |
| S3 场景 supporting artifact 漏写（advance 时 P6 §A 失败）| 回 §5 Step 1 补写 prd-level / feature-matrix → 走完 §5 5 步 |
| 用户在人 gate 前发现 PRD 错（已 review-passed 但未 approved）| **design gap**：当前 spec 无 `review-passed → revising` 事件；不要手工编辑 progress.md；升级人介入或在 design proposal 增加新事件后再修 |
| 用户在 PRD `status: approved`（已进 Stage 2/3/4...）后想改 PRD | 不走本 skill；应由用户提新需求触发 release-close + S2-1 release-start，进入新 release 的 prd-inception Change Mode |
| Doc 物理损坏 / 误删 | 不要恢复；让用户从 git 恢复或人介入；**禁止**通过 progress.py recover 假装修 doc（recover 只重建 progress.md，不重建 doc body）|

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机 / sub_state 转换 / progress.py 接口
- `skills/workflow-protocol/references/command-reference.md` — `progress.py update --event` 白名单 + 各子命令前置条件
- `skills/doc-guardian/SKILL.md` — 校验入口 + Change Log 自动化机制
- `skills/doc-guardian/references/frontmatter-schema.md` — PRD type 完整 frontmatter schema
- `skills/doc-guardian/references/required-artifacts.md` — S3 PRD 必备清单（prd-level + feature-matrix）
- `skills/doc-guardian/references/change-log-format.md` — Pending Changes / Change Log 格式
- `skills/doc-guardian/references/directory-layout.md` — `docs/prd/` 目录结构
- `skills/prd-review/SKILL.md` — review 接管点

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/prd-template.md` — PRD 主文档 + S3 必备 supporting artifacts (`source_product_prd_analysis.md` + `feature_matrix.md`) + optional supporting 章节级模板 + 写作准则 + common pitfalls（Phase 7 Task 7-B 拆出）


**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
