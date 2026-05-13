---
name: srs-write
description: dev-workflow-skills2 Stage 2 SRS 写作 vertical skill。在 progress.md current_stage==srs-specification AND sub_state ∈ {write, revising} 时被 invoke。S1 / S3 在 PRD 完成后由 AGENTS.md Bootstrap 路由；S2-1（PRD 完成后进 SRS）/ S2-2（新增 SRS Full Mode）/ S2-3（修改 SRS Change Mode）由 scenario-dispatcher / workflow-protocol 路由；Bug Flow root_cause==srs 时由 workflow-protocol 切回 Change Mode。Doc 输出 SRS + Acceptance Plan + Integration Plan（多模块时必备，由 SRS frontmatter `is_multi_module` bool 决定）+ S3 时 source-system-analysis 3 必备（srs-level/module-level/reuse-replace）+ technical-debt 推荐。本 release 首次进 SRS 时按 BUG-*.md `consumed_in_release == 当前 release` 扫描合并 consumed unresolved bugs（root_cause==null 是 post-close intake 合法默认；不要求先分类）。SRS frontmatter 必含 `is_multi_module: bool` + `architecture_change: bool` 两字段（required-artifacts DSL 关键依赖）。本 skill 不评审自身、不直接 mutation progress.md、不写 PRD / Architecture / Bug Report。
authority: 4
references:
  - references/srs-template.md
  - references/bug-merge-policy.md
---

# srs-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（7 项）**：

1. 产出 SRS 主文档（`docs/release<x.y>/srs/srs.md`）的 doc body + 合规 frontmatter
2. 产出 Acceptance Plan（`docs/release<x.y>/srs/acceptance_plan.md`）— 必备
3. 产出 Integration Plan（`docs/release<x.y>/srs/integration_plan.md`）— **多模块时必备**；单模块可省略（具体由 doc-guardian/references/required-artifacts.md DSL 决定）
4. **S3 场景**额外产出 source-system-analysis：3 必备（srs-level / module-level / reuse-replace）+ 1 recommended optional（technical-debt）（详见 §4.2；v0.6 round 2 L1 措辞清理）
5. **本 release 首次进 SRS 时合并 consumed_unresolved_bugs**：扫描 `docs/bug/BUG-*.md` 中 `consumed_in_release == 当前 release` 的 bug 列表，按 root_cause 分类合并到 SRS body / Pending Changes（详见 §5；覆盖 S2-1/S2-2/S2-3）
6. 写入 SRS frontmatter 两个 required-artifacts DSL 关键 bool：`is_multi_module: true|false`（决定 Integration Plan 必备性）+ `architecture_change: true|false`（决定 architecture-delta 必备性；事实源 `skills/doc-guardian/references/frontmatter-schema.md` §3.2）
7. 完成后跑 doc-guardian validate.py 自检（每 doc 一次）→ 调 progress.py update --event write-complete

**不属于本 skill**：

- 评审 SRS（→ `srs-review`）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py`）
- 推进到 Stage 3（必经 `progress.py update --advance`）
- 写 PRD / Architecture / BUG report / INCIDENT report
- 创建 architecture_delta（→ `architecture-write`；本 skill 仅在 SRS 中描述需求，不触碰架构 doc）
- 决定 consumed_unresolved_bugs 哪些可保留（→ 用户在 release-start 之前决定；本 skill 一概合并 root_cause ∈ {null, srs} 的 bug）
- 修改 BUG-NNN.md frontmatter `root_cause`（→ bug-triage active triage 才能改；本 skill 仅读取）

## 2. When to Invoke

**触发条件（本 skill 是 owner 当且仅当 progress.md 满足）**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `workflow_incident_active` | `false` |
| `current_stage` | `srs-specification` |
| `sub_state` | `write` 或 `revising` |
| `bug_flow.active` | `false` 或 (`true` AND `bug_flow.root_cause==srs`) |

**典型 invocation 路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| S1 PRD 完成后首入 SRS | PRD `--advance` 后 workflow-protocol 切 `current_stage=srs-specification, sub_state=write` | Full Mode 写新 SRS + Acceptance Plan（多模块时含 Integration Plan）|
| S3 PRD 完成后首入 SRS | 同上 | Full Mode 写 SRS + source-system-analysis（3 必备：srs-level/module-level/reuse-replace；technical-debt 推荐 optional）|
| S2-1 PRD 完成后首入 SRS | `release-start --scenario S2-1` 后先进 PRD，PRD `--advance` 后 workflow-protocol 切到 srs-specification | Change Mode 改既有 SRS + 合并本 release `consumed_unresolved_bugs` |
| S2-2 启新 release 新增模块 | `progress.py release-start --scenario S2-2` 后直接路由 | Full Mode 写 SRS（仅本 release 新增模块部分）+ 关联 Acceptance/Integration Plan + 合并 consumed_unresolved_bugs |
| S2-3 启新 release 修既有 SRS | `progress.py release-start --scenario S2-3` 后直接路由 | Change Mode 改既有 SRS + 合并 consumed_unresolved_bugs |
| Bug Flow re-entry: root_cause==srs | `bug-triage` 调 `progress.py bug-start --root-cause srs` 后 workflow-protocol 切 `current_stage=srs-specification, sub_state=write, bug_flow.active=true` | Change Mode 修 SRS 应对 bug |
| Revise 触发 | `srs-review` 调 `progress.py update --event review-issues`（业务上即 issues-found）后状态机自动转 `sub_state: revising`（见 workflow-protocol command-reference.md §2.1 转移表）| Change Mode 应对 review findings |

**不被 invoke 的时机**：

- `current_stage != srs-specification` → caller 路由错误
- `sub_state ∈ {in-review, review-passed, approved}` → 非 write owner 期
- `scenario==S2-1` 且 `current_stage==prd-inception` → 仍在 PRD 阶段；本 skill 不介入（PRD advance 后才进入本 skill；那时仍属 S2-1 srs-specification 入口）
- `workflow_incident_active==true` → workflow-evolution 接管
- `project_state ∈ {aborted, reconstructing}` → 终态

## 3. Full Mode vs Change Mode

| Scenario | Mode | 入口条件 | 主要工作 |
|---------|------|---------|---------|
| S1 | **Full** | PRD `--advance` 后第一次进 srs-specification | 从 0 写 SRS + Acceptance Plan +（多模块时）Integration Plan |
| S3 | **Full** | PRD `--advance` 后 + 已有源系统 PRD/SRS 输入 | 从 0 写 SRS + Acceptance/Integration Plan + 3 必备 source-system-analysis（technical-debt 推荐）|
| S2-1 | **Change** | PRD `--advance` 后首次进 srs-specification（PRD 已在本 release Change Mode 修过）| 在既有 SRS 上 diff（PRD 改动可能影响 SRS）+ 合并本 release `consumed_unresolved_bugs` |
| S2-2 | **Full** for new sections | `release-start --scenario S2-2` 后；本 release 新增模块的 SRS sections 是新写的 | 在既有 SRS 文件上加新章节 + 在 Acceptance/Integration Plan 加对应章节；旧章节不动 + 合并 consumed_unresolved_bugs |
| S2-3 | **Change** | `release-start --scenario S2-3` 后；改既有模块 SRS | 在既有 SRS 上 diff 改既有章节；Pending Changes 记每条改动 + 合并 consumed_unresolved_bugs |
| Bug Flow re-entry (root_cause==srs) | **Change** | `bug-start --root-cause srs` 后切回 srs-specification | 仅修 bug 涉及的具体 SRS 章节；Pending Changes 关联 BUG-NNN.md |
| Revise（任意 mode）| **Change** | review issues-found 触发 `--event review-issues`，状态机自动转 `revising` | 按 srs-review finding 修 |

**Mode 区分要点**：

- **Full Mode**：主 doc 从 0 写；多 doc 同时新建
- **Change Mode**：主 doc 已有；本次仅做 diff；Pending Changes 必须能映射回具体改动
- 4-step 标准流程（§6）一致；每个 doc 单独走一遍 §6

## 4. Doc Output Contract

### 4.1 主输出（按场景必备）

| Doc Type | 路径 | Frontmatter `type` | 必备场景 |
|---------|------|-------------------|---------|
| SRS | `docs/release<x.y>/srs/srs.md` | `srs` | 全部场景必备 |
| Acceptance Plan | `docs/release<x.y>/srs/acceptance_plan.md` | `acceptance-plan` | 全部场景必备 |
| Integration Plan | `docs/release<x.y>/srs/integration_plan.md` | `integration-plan` | **多模块时必备**（具体 DSL 由 required-artifacts.md 决定；触发条件 typically `module_count > 1`）|

### 4.2 S3 场景必备 source-system-analysis（3+1）

| Doc Type | 路径 | Frontmatter | 必备性 |
|---------|------|-------------|--------|
| source-system-analysis | `docs/release<x.y>/srs/source_product_srs_analysis.md` | `type: source-system-analysis`, `analysis_kind: srs-level`, `release: <x.y>`, `source_system_name: <name>` | **必备** |
| source-system-analysis | `docs/release<x.y>/srs/source_module_analysis.md` | `analysis_kind: module-level`, `release: <x.y>`, `source_system_name: <name>` | **必备** |
| source-system-analysis | `docs/release<x.y>/srs/reuse_replace_capability.md` | `analysis_kind: reuse-replace`, `release: <x.y>`, `source_system_name: <name>` | **必备** |
| source-system-analysis | `docs/release<x.y>/srs/technical_debt_analysis.md` | `analysis_kind: technical-debt`, `release: <x.y>`, `source_system_name: <name>` | 推荐（非必备）|

**事实源**：完整 scenario-aware 必备清单见 `skills/doc-guardian/references/required-artifacts.md`。本表反映当前权威设计（design proposal v0.5 §5.3）；以 required-artifacts.md DSL 实际推导为准。

### 4.3 Frontmatter 必备字段（v0.6 round 1 H1：SRS 必含 2 个 bool）

#### SRS 主文档

```yaml
---
title: <human readable>
type: srs
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/srs-write
release: "<MAJOR.MINOR>"
is_multi_module: true | false        # **必含（v0.6 round 2 H1）**：决定 Integration Plan 必备性
architecture_change: true | false    # **必含（v0.6 round 2 H1）**：决定 architecture-delta 必备性
---
```

**判定与写入责任**（v0.6 round 1 H1）：

- `is_multi_module: true` ⇔ 本 release SRS 在多个模块上下文（典型：SRS body 列出 ≥2 个独立模块、需要明确模块间集成边界）→ Integration Plan 必备
- `is_multi_module: false` ⇔ 单模块 / 单服务 / 不需要跨模块集成描述 → Integration Plan 跳过
- `architecture_change: true` ⇔ 本 release SRS 蕴含组件 / 接口 / 数据流 / 部署拓扑 改变 → 进入 Stage 3 Architecture 时 architecture_delta 必备
- `architecture_change: false` ⇔ 本 release 仅业务规则 / acceptance criteria / non-functional req 修订；不影响运行时架构 → Stage 3 跳过 delta（甚至跳过 architecture-design 阶段，由 workflow-protocol 状态机决定）

**写入时机**：srs-write Step 1 写 doc body 时同步设这两字段；review 反馈或 Bug Flow re-entry 时如果 SRS 模块数 / 架构影响发生变化，必须**同步更新**这两字段（否则 srs-review 维度 5 拒绝）。

**事实源**：`skills/doc-guardian/references/frontmatter-schema.md` §3.2 SRS。required-artifacts.md DSL 通过这两字段决定下游必备性。

#### 其他 doc frontmatter

| Doc Type | 必含扩展字段 |
|---------|-------------|
| `acceptance-plan` | `release`, `related_srs: docs/release<x.y>/srs/srs.md` |
| `integration-plan` | `release` |
| `source-system-analysis` | `release`（项目级 prd-level/feature-matrix 时为 null）, `analysis_kind`, `source_system_name: <name>`（每行均必含；从源系统 PRD/SRS 输入获取）|

完整 schema 与 per-type 扩展见 `skills/doc-guardian/references/frontmatter-schema.md`。

## 5. consumed_unresolved_bugs Merge Procedure（v0.6 round 1 H2 重写）

**触发时机（唯一）**：**本 release 首次进入 `srs-specification` AND `sub_state==write`**。覆盖：

- **S2-1**：release-start 后先进 PRD（`current_stage=prd-inception`），PRD 阶段 advance 后首次进入 SRS write —— 也属本触发点
- **S2-2 / S2-3**：release-start 后直接进 SRS write
- **S1 / S3**：首次 release，BUG scan 列表通常为空，但仍跑本流程（保持一致性）
- **同一 release 内本 skill 二次进入**（如 advance 失败回退、Bug Flow re-entry 后再 advance 回 SRS）：扫描结果应已无新增"未被 SRS 引用的 consumed bug"；幂等地跳过 §5 主体

**不在以下场景触发**：

- Bug Flow re-entry（`bug_flow.active==true AND bug_flow.root_cause==srs`）：这是 active bug 修复，独立路径（见 §8），与 release-start 消费语义无关
- revise 循环：不是新 release 起点

**事实源（canonical bug list）**：

- 扫描 `docs/bug/BUG-*.md` 文件 frontmatter（**不**依赖 progress-history.md release-start entry 的 result 字段；命令的 history 仅记 count，不记 list）
- 筛选条件：`consumed_in_release == <progress.md 当前 release>`
- 筛选结果即本 release 消费的 bug 列表

**前置约束（由 progress.py release-start 已处理；事实源 command-reference §6）**：

- release-start 已为每条原 `unresolved_bugs` 中的 BUG-NNN.md frontmatter 原子设置：`target_release: "<x.y>"` + `consumed_in_release: "<x.y>"`
- progress.md `unresolved_bugs` 字段已清空（本 skill 不读它）
- 同一 BUG 不能被多个 release 消费（doc-guardian validate.py 类 5 unique consumption 校验）

**实施步骤**：

```
Step A. 扫描 consumed bug 列表
        - 对 docs/bug/ 下所有 BUG-*.md 读 frontmatter
        - 筛选 consumed_in_release == <progress.md.release> 的 bug
        - 列表为空（S1 首次 / 无 post-close intake）→ 跳过 §5 全程

Step B. 对每条 consumed bug 决定合并方式
        - 读 BUG-NNN.md frontmatter root_cause + body
        - root_cause 5 种合法状态（含 post-close intake 默认 null）：
          - root_cause == null（post-close intake 默认）→ 视为"未分类修复需求"合并到 SRS：
            * post-close bug-intake 不做 active triage（command-reference §7）；root_cause: null 是合法状态
            * srs-write 把 bug 描述的故障/缺陷转为 SRS 中的修复需求 / acceptance criteria 草案
            * 不要求 srs-write 自行分类 root_cause（active triage 仅在 testing 阶段发现 bug 时由 bug-triage 做）
          - root_cause == srs → 合并到 SRS（与 null 同等处理；frontmatter 已显式标）
          - root_cause == architecture → 不进 SRS body；可在 SRS 加跨 stage 责任注记（非强制；srs-review 不阻断）；该 bug 由 architecture-write 在 Stage 3 看 BUG-NNN 自行判定
          - root_cause == development → 同 architecture：不进 SRS body；可加注记；由 development-* 在 Stage 4 处理
          - root_cause == prd-exception → 不应出现在 consumed 列表（prd-exception 在原 release testing 阶段已通过 incident-resolve 处理）。若出现 → 视为脏数据；srs-write 不静默跳过，**拒绝合并 + 输出 issue 让用户人工 audit**：从 git 历史恢复 BUG-NNN.md 正确 frontmatter（或人工修正 `root_cause` / `consumed_in_release` 字段）后重跑 `validate.py file <BUG-NNN.md>`。**不要**期待 `progress.py recover` 修该脏数据——`recover` 仅从 progress-history.md 重建 progress.md，**不**修 BUG report frontmatter（v0.6 round 2 M4 修正）

Step C. 在 SRS 中合并改动 + 加 Pending Changes 条目
        - root_cause ∈ {null, srs} 的 bug：
          * SRS body 加修复需求 / acceptance criteria（Full Mode 时融入新章节；Change Mode 时改既有章节）
          * ## Pending Changes 加 entry「Merged BUG-NNN: <bug title> — root_cause=<value or 'null/awaiting-classification'>，见 docs/bug/BUG-NNN.md」
        - root_cause ∈ {architecture, development} 的 bug：
          * 可加 SRS body 跨 stage 责任注记（非强制）
          * 不加 Pending Changes / Change Log（避免在 SRS 中虚假记录"改动"）

Step D. 完成 §6 标准 4-step 时一并 promote
        - changelog.py promote 把 §C Pending Changes 移到 Change Log
        - validate.py file 校验 SRS 整体合规（含 Cross-Reference 校验 BUG-NNN.md 存在）
```

**关键约束**：

- BUG-*.md frontmatter `consumed_in_release` 是合并完整性的事实源；srs-review §3 维度 7 必须以 BUG-*.md scan 为准（不查 progress-history）
- `root_cause: null` 是合法值（post-close intake 默认）；srs-write 不要求其他 skill 先做 active triage；nukeing root_cause 才是错的
- 同一 release 不复消费同一 bug（release-start 已通过 frontmatter unique consumption 校验）
- 本 skill 不创建 / 删除 BUG-NNN.md，不改 BUG-NNN.md frontmatter；仅读取 + 在 SRS 引用
- 本 skill 不修改 progress.md `unresolved_bugs` 字段（release-start 已处理）

## 6. 4-Step Standard Procedure（每个 doc 走一遍 Step 1-4，统一 Step 5 submit）

**Doc 分类（v0.6 round 1 M1）**：

- **增量类 doc**（走 Pending Changes / Change Log 完整流程）：SRS / Acceptance Plan / Integration Plan
- **Snapshot 类 doc**（不含 Pending Changes / Change Log；事实源 doc-guardian/references/change-log-format.md）：source-system-analysis（4 个 analysis_kind 全部）

```
Step 1. 写/修 doc body
        - SRS 主文档 / Acceptance Plan / Integration Plan / S3 supporting artifacts
        - Full Mode: 从 0 写
        - Change Mode: diff
        - 多 doc 时按依赖顺序：SRS → Acceptance Plan → Integration Plan → S3 supporting

Step 2. 加 Pending Changes 段（仅增量类 doc）
        - SRS / Acceptance Plan / Integration Plan 末尾 ## Pending Changes 段加本次改动条目
        - consumed_unresolved_bugs 合并条目按 §5 Step C 写入 SRS Pending Changes
        - **source-system-analysis 跳过**（v0.6 round 1 M1）：snapshot doc 不含 Pending Changes / Change Log；只写 body + frontmatter

Step 3. 跑 changelog.py promote（仅增量类 doc）
        - 对 SRS / Acceptance Plan / Integration Plan 单独跑 changelog.py promote <doc-path>
        - **不对 source-system-analysis 跑 promote**（v0.6 round 1 M1）

Step 4. 跑 validate.py file 自检（每个改动 doc 都跑，含 snapshot 类）
        - 对每个改动的 doc 单独跑 validate.py file <doc-path>
        - 全部 exit 0 才进 Step 5

Step 5. 提交 review（统一一次，覆盖所有改动 doc）
        - skills/workflow-protocol/scripts/progress.py update --event write-complete
        - 转 sub_state: write/revising → in-review
        - 控制权移交给 srs-review
```

**关键约束**：

- 多 doc 不分别 write-complete；统一一次 submit；srs-review 一次性评审本 stage 所有 doc
- 多 doc 时任一 doc validate 失败 → 必须修后再统一提交（不允许部分 submit）
- snapshot 类 doc（source-system-analysis）跳过 Pending Changes / promote 步骤；validate.py 仍要跑（v0.6 round 1 M1）

## 7. Stage Done Conditions

Stage 2 SRS 推进到 Stage 3 Architecture 由 `progress.py update --advance` 触发。本 skill 满足 4 维度：

| 维度 | 检查 | 责任方 |
|------|------|--------|
| **A. 必需 artifacts 存在** | SRS + Acceptance Plan + (多模块时) Integration Plan + (S3 时) 3 必备 source-system-analysis 全部存在 | srs-write 在 §6 Step 1 写、Step 4 自检 |
| **B. doc-guardian 校验通过** | `validate.py file <each artifact>` 全部 exit 0 | srs-write Step 4 自检；advance 时 workflow-protocol 再跑一次 double-safety |
| **C. Review 通过** | `srs-review` 最近一轮输出 `review-passed`（覆盖所有改动 doc）| `srs-review` |
| **D. 人确认** | `apply_update_advance` 校验 `progress.md.sub_state == approved`（即 `progress.py update --event human-confirmed` 已 fire；progress-history.md 自动有对应条目）；每 doc frontmatter `status: approved` 由 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path>`（多 doc 重复 `--doc`）同步（B 维度 validate.py file 复检）。advance 不在 D 维度独立重读 doc.status；事实源 command-reference §2.2 + Phase 7 P4 polish。 | 人 gate |

**E 维度不适用**：SRS 是规格 doc，无内部 verification。

**unresolved_bugs 一致性额外检查**：advance 时 workflow-protocol 校验 SRS Change Log 中每条 `Merged BUG-NNN` 条目对应的 BUG-NNN.md frontmatter `consumed_in_release` 字段已设置（释义：bug 已被消费）。该校验由 doc-guardian validate.py 类 5（Cross-Reference）实现。

## 8. Bug Flow Re-entry

`bug-triage` 判定 `root_cause==srs` 时切回本 stage：

```
1. bug-triage 判 root_cause=srs；写 BUG-NNN.md frontmatter
2. bug-triage 调 skills/workflow-protocol/scripts/progress.py bug-start --bug docs/bug/BUG-NNN.md --root-cause srs
3. workflow-protocol mutation:
   - bug_flow.active = true
   - bug_flow.bug_report_path = docs/bug/BUG-NNN.md
   - bug_flow.root_cause = srs
   - current_stage: testing → srs-specification
   - sub_state: review-passed → write
   - review_iteration: 0
4. 本 skill 被路由 invoke：Change Mode 应对 bug
   - 读 docs/bug/BUG-NNN.md body 决定具体 SRS 章节修法
   - 走 §6 标准 4-step（仅修 bug 涉及的章节）
   - Pending Changes 关联 BUG-NNN
5. write-complete → srs-review → review-passed
6. workflow-protocol 检测人 gate（D 维度仍要求；Bug Flow 不绕过）
7. 推 advance（仅 Stage 2 done；下游 Stage 3 / 4 视 root_cause 影响而定，由 workflow-protocol 决定）
8. 回到 testing 重测 → testing-write 调 progress.py bug-close → bug_flow.active=false
```

**Bug Flow Change Mode 与 S2-3 Change Mode 的差异**：

| 维度 | S2-3 Change Mode | Bug Flow root_cause==srs Change Mode |
|------|-----------------|--------------------------------------|
| 触发 | `release-start --scenario S2-3` | `bug-start --root-cause srs` |
| 改动范围 | 用户提的新需求 | bug 涉及的章节 |
| Pending Changes 关联 | 一般业务变更 | 关联具体 BUG-NNN |
| 是否触发新 release | 是（release-start 已建）| 否（仍在原 release；retest pass 后回 Stage 5）|
| `consumed_unresolved_bugs` 合并（§5）| 触发（本 release 首次进 SRS write，扫描 BUG-*.md `consumed_in_release` 列表）| 不触发（不在新 release 起点；§5 仅首次进入处理）|

## 9. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 跳过 `skills/doc-guardian/scripts/validate.py file` 直接 write-complete
- ❌ 跳过 `skills/doc-guardian/scripts/changelog.py promote` 直接编辑 `## Change Log` 章节
- ❌ 自行评审本 skill 产出（→ `srs-review`）
- ❌ 在 `sub_state==in-review` 时继续修改 doc body（in-review→revising 由 `srs-review` 调 `progress.py update --event review-issues` 触发；本 skill 在 in-review 期间不可动 doc）
- ❌ 自行设置 frontmatter `status: approved`（人 gate；mutation owner = `skills/doc-guardian/scripts/status_transition.py`，在 `skills/workflow-protocol/scripts/progress.py update --event human-confirmed` 成功后调用 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc <path> ...` 同步；**Gap-2**）
- ❌ S2-2 时新建 `docs/release<x.y>/srs/srs_v2.md` 等附加文件（同 release 内 SRS 是单文件；新 release 在新 release<x.y>/ 目录下另建）
- ❌ 跨 release 改 SRS（如本 release 改另一 release 目录下的 srs.md）— release close 后那目录变只读
- ❌ 在 Bug Flow Change Mode 改 bug 涉及之外的章节（除非该改动也由 BUG-NNN 蕴含）
- ❌ 把 `root_cause ∈ {architecture, development}` 的 consumed bug 强行写入 SRS body 修复需求（仅可加跨 stage 责任注记；架构/开发类修复由对应 stage 负责）
- ❌ 把 `root_cause==null`（post-close intake 默认）的 consumed bug 视为脏数据跳过（v0.6 round 1 H2 决议：null 是合法值；srs-write 不要求先分类）
- ❌ SRS frontmatter 缺 `is_multi_module: bool` 或 `architecture_change: bool` 任一字段（v0.6 round 1 H1：required-artifacts DSL 关键依赖；缺失 → validate.py 类 3 拒绝 + srs-review 维度 5 blocking）
- ❌ 写 `is_multi_module: true` 但 SRS body 仅描述单模块（或反之）；写 `architecture_change: false` 但 SRS body 蕴含运行时架构变化（或反之）：必须保持 frontmatter 与 body 一致；review 维度 5 校验
- ❌ 自行修改 BUG-NNN.md frontmatter `root_cause` 字段（→ bug-triage active triage 才能改 root_cause；srs-write 仅读取）
- ❌ 多 doc 部分 write-complete（必须全 doc 准备好统一 submit）
- ❌ 修改 BUG-NNN.md 文件（→ 由 bug-triage / testing-write 管理；本 skill 仅读取）
- ❌ 自行清空 progress.md `unresolved_bugs` 字段（→ progress.py release-start 已统一处理）
- ❌ 创建 architecture_delta（→ `architecture-write` 在 Stage 3 处理）
- ❌ 创建 BUG-NNN.md 文件（→ testing-write / bug-triage 创建）
- ❌ 自行决定推进 stage（必经 `progress.py update --advance`）
- ❌ 评审循环超 7 次仍尝试 revise（必须升级人介入）
- ❌ 在 `current_stage != srs-specification` 时被 invoke 仍继续操作

## 10. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| 多 doc 中某 doc validate 失败 | 修对应 doc → 重跑该 doc 的 §6 Step 3-4；其他 doc 不必重跑；最终所有 doc validate 0 后再 write-complete |
| `consumed_unresolved_bugs` 合并扫描时 BUG-NNN.md 文件缺失（frontmatter `consumed_in_release` 设了但物理文件不存在）| 拒绝合并；提示用户从 git 恢复 BUG report 或人介入；不静默跳过；validate.py 类 5 cross-ref 也会拒绝 advance |
| `consumed_unresolved_bugs` 合并扫描时 BUG-NNN.md `root_cause==null`（post-close intake 默认）| **合法**：v0.6 round 1 H2 决议；视为"未分类修复需求"按 §5 Step B 合并到 SRS；不要求先分类 |
| `consumed_unresolved_bugs` 合并扫描时 BUG-NNN.md `root_cause==prd-exception`（脏数据）| 拒绝合并；输出 issue 让用户人工 audit。修复路径：从 git 历史恢复 BUG-NNN.md 或人工修正 frontmatter（`root_cause` / `consumed_in_release`）→ 重跑 `validate.py file <BUG-NNN.md>` → 重新触发 srs-write 扫描。**`progress.py recover` 不能修该脏数据**——`recover` 仅从 progress-history.md 重建 progress.md，**不动 BUG report frontmatter**（v0.6 round 2 M4 修正）；仅当 progress.md 与 history 自身不一致时才考虑用 recover |
| Bug Flow re-entry 时 BUG-NNN.md frontmatter `root_cause` 与 progress.md `bug_flow.root_cause` 不一致 | 拒绝操作；让用户先用 `progress.py recover` 或人介入修 |
| S3 supporting artifact 漏写（advance 时 P6 §A 失败）| 回 §6 Step 1 补；走完 §6 全 5 步 |
| Multi-module Integration Plan 漏写但项目实际多模块 | required-artifacts.md DSL 推导该 doc 必备 → validate 拒绝 → 补 Integration Plan 后重跑 |
| 用户在人 gate 前发现 SRS 问题 | **design gap**：当前 spec 无 `review-passed → revising` 事件；不要手工编辑 progress.md；升级人介入或在 design proposal 增加新事件后再修 |
| 用户改主意：取消 consumed bug 中某条 | 不改 progress.md；改 BUG-NNN.md frontmatter `target_release: null` + `consumed_in_release: null`（视为撤回；srs-review 维度 7 扫描不到该 BUG，自然不要求 SRS 合并）；保留 BUG report 文件作 audit 痕迹；推荐用户在 release-start 之前从 progress.md `unresolved_bugs` 列表移除而非事后撤回 |
| Doc 物理损坏 / 误删 | 从 git 恢复；本 skill 不重建 doc body |

## 11. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机、bug-start mutation
- `skills/workflow-protocol/references/command-reference.md` — `release-start` / `bug-start` / `update --event` 完整签名
- `skills/doc-guardian/SKILL.md` — 校验入口
- `skills/doc-guardian/references/frontmatter-schema.md` — SRS / Acceptance Plan / Integration Plan / source-system-analysis frontmatter
- `skills/doc-guardian/references/required-artifacts.md` — 多模块时 Integration Plan 必备性 / S3 必备清单 DSL
- `skills/doc-guardian/references/change-log-format.md` — Pending Changes / Change Log
- `skills/doc-guardian/references/directory-layout.md` — `docs/release<x.y>/srs/` 目录
- `skills/srs-review/SKILL.md` — review 接管点
- `skills/bug-triage/SKILL.md` — root_cause 分类来源
- `skills/architecture-write/SKILL.md` — 架构变更接力点

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/srs-template.md` — SRS 主文档 + Acceptance Plan + Integration Plan（多模块时）章节级模板 + 写作准则 + 关键 frontmatter 字段（`is_multi_module` / `architecture_change`）+ Common Pitfalls（Phase 7 Task 7-B 拆出）
- `references/bug-merge-policy.md` — §5 consumed_unresolved_bugs Merge Procedure 完整细则：触发时机、按 root_cause 分类合并决策表、SRS body 修订 pattern、edge cases、与 srs-review 维度 7 校验对照（Phase 7 Task 7-B 拆出）


**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
