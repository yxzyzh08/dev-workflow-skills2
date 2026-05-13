---
name: srs-review
description: dev-workflow-skills2 Stage 2 SRS 评审 vertical skill。在 progress.md current_stage==srs-specification AND sub_state==in-review 时被 invoke。读 SRS + Acceptance Plan +（多模块时）Integration Plan + S3 时 source-system-analysis（3 必备 + 1 optional），按 rubric 逐 doc 评审 + 跨 doc 一致性 + consumed_unresolved_bugs 合并完整性（v0.6 round 1 H2：扫描 BUG-*.md `consumed_in_release` 为事实源）+ Bug Flow re-entry 时验证 BUG-NNN 已被 SRS 改动覆盖。输出 review-passed / issues-found 两态结论（绝不用 approved），finding 列表回到对话由 srs-write Change Mode 消化；不写独立 review-report doc。本 skill 不修改 doc body、不直接 mutation progress.md（必经 progress.py）、不签发 approved。
authority: 4
references:
  - references/review-rubric.md
---

# srs-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（6 项）**：

1. 读 Stage 2 SRS 阶段全部改动 doc：SRS / Acceptance Plan / Integration Plan（多模块时）/ S3 时 source-system-analysis（3 必备：srs-level/module-level/reuse-replace；technical-debt 推荐 optional）
2. 跑 `validate.py file <path>` 自检（每 doc 一次；防评审已损坏 doc）
3. 按 SRS 评审 rubric（§3）逐维度评审，含跨 doc 一致性（SRS↔Acceptance Plan↔Integration Plan↔source-system-analysis）
4. 评审 `unresolved_bugs` 合并完整性：本 release 消费的每条 BUG-NNN 已在 SRS Change Log 中体现 + body 有对应改动
5. Bug Flow re-entry 模式：额外评审 BUG-NNN 涉及的 SRS 章节是否被实质修改（不是单加 Change Log entry 不动 body）
6. 输出 `review-passed` 或 `issues-found`（业务术语），分别调 `progress.py update --event review-passed` 或 `--event review-issues`（事实源 command-reference §2 白名单）触发 sub_state 转换；event 同时携带 issue count summary（v0.6 round 3 L2 修正：旧版"--event review-passed | issues-found"误把业务术语当 event 名）

**不属于本 skill**：

- 修改 SRS / Acceptance Plan / Integration Plan / source-system-analysis doc body（→ `srs-write` Change Mode）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py update --event`）
- 签发 `approved`（人 gate 专属）
- 创建 / 编辑 review-report 类 doc（SRS review 不产 review-report；frontmatter-schema 未注册 `srs-review-report` type）
- 改 BUG-NNN.md（→ bug-triage / testing-write）
- 评审 PRD / Architecture / Bug Report / INCIDENT report（→ 对应 review skill）

## 2. When to Invoke

**触发条件**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `workflow_incident_active` | `false` |
| `current_stage` | `srs-specification` |
| `sub_state` | `in-review` |
| `review_iteration` | 0-7 |
| `bug_flow.active` | `false` 或 (`true` AND `bug_flow.root_cause==srs`) |

**典型 invocation 路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| srs-write 完成 §6 4-step 后 write-complete | `srs-write` 调 `progress.py update --event write-complete` 转 `sub_state: in-review` | 接管，启动评审 |
| revise 后再次 submit | `srs-write` Change Mode revise 完成后再次 write-complete | 重新评审（review_iteration += 1 已由 issues-found 累计）|
| Bug Flow re-entry 后 srs-write 完成 Change Mode submit | 同上，但 bug_flow.active==true | 评审包含 §3 维度 7（Bug 覆盖完整性）|

**不被 invoke 的时机**：

- `sub_state ∈ {write, revising, review-passed, approved}` → 非 review owner 期
- `current_stage != srs-specification` → 由对应 review skill 接管
- `workflow_incident_active==true` → workflow-evolution 接管
- `review_iteration > 7` → progress.py 拒绝 update；需升级人介入

## 3. Review Rubric Overview

SRS 评审涵盖 7 个维度。完整 rubric 与 severity 标准将在本 skill 后续 references 中拆出（batch 3a 评审通过后规划 `references/review-rubric.md`）。

| # | 维度 | 关键问题 | Severity 影响 |
|---|------|---------|---------------|
| 1 | **完整性 (per-doc)** | SRS：功能性 / 非功能性 / 边界 / 约束 章节齐全？Acceptance Plan：每个功能有 acceptance criteria？多模块时 Integration Plan 描述模块边界 / 接口 / 集成顺序？| 缺核心章节 → blocking |
| 2 | **跨 doc 一致性** | SRS 中每个功能在 Acceptance Plan 有覆盖；多模块时 SRS 的模块切分与 Integration Plan 的 module list 一致；source-system-analysis 的源系统功能能映射到 SRS 重构对应章节 | 跨 doc 失配 → blocking |
| 3 | **可决策性** | SRS 描述是否够具体让 Architecture 阶段下展开（接口 / 模块边界 / 数据流可决策）？non-functional req 是否可量化？| 含糊 → blocking |
| 4 | **业务术语稳定** | 术语在文中首现处定义；与 PRD 术语一致；不混用同义词 | 术语漂移 → non-blocking（提建议）|
| 5 | **Change Log 与 frontmatter 业务合理（含 SRS 2 bool 一致性，v0.6 round 1 H1）** | Pending Changes 已 promote；每条 Change Log entry 与 doc body 改动一致；多 doc frontmatter `release` / `updated` 一致；`title` 合理；**SRS frontmatter `is_multi_module: bool` 必含且与 body 模块切分一致**（true ⇔ 多模块 SRS body + Integration Plan 存在；false ⇔ 单模块 SRS body + Integration Plan 不存在）；**SRS frontmatter `architecture_change: bool` 必含且与 SRS body 架构影响描述一致**（true ⇔ SRS 蕴含组件/接口/数据流/部署拓扑改变 + Stage 3 进入；false ⇔ 仅业务规则 / acceptance / NFR 修订）；source-system-analysis 必含 `source_system_name` 字段 | 改动语义与 Change Log 不一致 → blocking；2 bool 缺失或与 body 不一致 → blocking；source_system_name 缺失 → medium |
| 6 | **S3 源系统分析深度（仅 S3）** | `srs-level`：源系统 SRS 章节级别分析（不能是 prd-level 拷贝）；`module-level`：源系统模块切分清晰；`reuse-replace`：每个模块的复用 / 替换 / 新建决策有依据；`technical-debt`（推荐）：识别可弃 / 可重写部分 | S3 缺关键源系统对照 → blocking |
| 7 | **consumed_unresolved_bugs 合并完整性（v0.6 round 1 H2 重写；本 release 首次进 SRS 时 + Bug Flow re-entry，覆盖 S2-1/S2-2/S2-3）** | **事实源 = 扫描 `docs/bug/BUG-*.md` 中 `consumed_in_release == <progress.md.release>` 的 bug**（不读 progress-history.md release-start entry list；该 entry 仅记 count）。校验：每条 consumed bug 中 root_cause ∈ {null, srs} 的，SRS body 有对应修复需求/acceptance criteria + Change Log 有 `Merged BUG-NNN` 条目；root_cause ∈ {architecture, development} 的可有 SRS body 责任注记（非强制）；root_cause==null 是 post-close intake 合法值，srs-write 不要求先分类 | 漏 bug（root_cause ∈ {null, srs} 但 SRS 无改动）→ blocking；脏数据（root_cause==prd-exception 出现 in consumed list）→ blocking；多余合并（root_cause ∈ {architecture, development} 强行写入 SRS body）→ medium |

**关于 doc-guardian 与 srs-review 的边界**：

- `validate.py` 校验机器层格式（路径 / frontmatter schema / Change Log 章节存在 / Cross-Reference 有效 / 类 5 BUG-NNN.md `consumed_in_release` 字段 等）
- `srs-review` 校验业务层语义（章节内容是否合理、跨 doc 一致、bug 合并是否实质）
- 二者互补；srs-review 仅在 `validate.py file` 全 exit 0 之后才开始业务评审

## 4. Output Contract

### 4.1 输出形式（两类）

**类 A：review-passed**

- 全部维度无 blocking finding
- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`
- progress-history.md 追加：`...— srs-review iteration N — review-passed (X non-blocking suggestions, covered SRS + Acceptance + Integration<? + S3-supporting<?>)`
- 每个 doc frontmatter `status: in-review → review-passed` 由 **`skills/doc-guardian/scripts/status_transition.py`** 在 `progress.py update --event review-passed` 之后同步（owner = doc-guardian；调用 `skills/doc-guardian/scripts/status_transition.py apply --event review-passed --doc <path> ...`；**Gap-2** 见 §10）；本 skill 不直接改 doc
- 控制权移交：等待人 gate

**类 B：issues-found**

- 至少 1 条 blocking finding
- 调 `progress.py update --event review-issues`（v0.6 round 1 Implementability：finding count / max severity 通过 history entry result prose 携带；不强制结构化 CLI 参数；具体接口待 progress.py 升级）
- progress.md：sub_state 转换由 progress.py command-reference 定义（统一 in-review → revising 的 path 由 workflow-protocol 决定）
- progress-history.md 追加：`...— srs-review iteration N — issues-found (B blocking, M medium, L low)`
- finding 列表通过对话回给 caller；不写独立 review-report doc

### 4.2 Finding 描述模板

```markdown
## srs-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low
**Coverage**: SRS + Acceptance Plan + (Integration Plan?) + (S3 supporting?)

### Finding 1 [blocking, 维度 2: 跨 doc 一致性]
- **Where**: SRS §3.2 Function F1 / Acceptance Plan: 缺 F1 acceptance criteria
- **Issue**: 功能 F1 在 SRS 已定义但 Acceptance Plan 无对应 acceptance criteria
- **Recommendation**: 在 Acceptance Plan §4 加 F1 acceptance criteria；至少包含 happy path + 2 个 edge cases

### Finding 2 [blocking, 维度 7: bug 合并]
- **Where**: BUG-*.md scan: BUG-005 (consumed_in_release=0.3, root_cause=null) + BUG-007 (consumed_in_release=0.3, root_cause=srs) / SRS Change Log 仅有 BUG-005
- **Issue**: BUG-007（root_cause=srs）已 consumed 但 SRS body 无对应修复改动
- **Recommendation**: 在 SRS body 加 BUG-007 修复需求/acceptance criteria + Pending Changes 加 Merged BUG-007 entry → promote → 重 submit
...
```

### 4.3 严禁的输出术语

| 严禁 | 原因 |
|------|------|
| `approved` | 人 gate 专属 |
| `pending` / `pass` / `fail` | 三态术语仅 Stage 4 dev-test/dev-code review 用 |
| `accept` / `reject` / `LGTM` | 非术语化输出 |

## 5. Review Procedure（5 步 + bug 合并校验）

```
Step 1. 跑 validate.py file 自检（每 doc 一次）
        - skills/doc-guardian/scripts/validate.py file <each artifact>
        - 任一 exit 1 → 不进业务评审；直接 issues-found（finding 1 类：guardian failure）；caller srs-write 修后重 submit
        - 全部 exit 0 → 进 Step 2

Step 2. 读所有改动 doc + 上轮 review iteration（如有）+ consumed bug 列表
        - SRS / Acceptance Plan / Integration Plan / S3 supporting
        - 读 progress-history.md 最近 srs-review entry（取上轮 finding 是否消化）
        - **维度 7 数据源**：扫描 `docs/bug/BUG-*.md` 筛 `consumed_in_release == <progress.md.release>`（v0.6 round 1 H2 重写：不读 release-start entry 的 result list）
        - Bug Flow re-entry 时（`bug_flow.active==true AND bug_flow.root_cause==srs`）读 `bug_flow.bug_report_path` 指向的 BUG-NNN.md

Step 3. 按 §3 7 维度逐项评审
        - 维度 1-5: 全场景适用
        - 维度 6: 仅 scenario==S3 时
        - 维度 7: 本 release 首次进入 SRS review 时启用（覆盖 S2-1/S2-2/S2-3；事实源为 BUG-*.md scan）或 Bug Flow re-entry 时（v0.6 round 2 M1：与 srs-write §5 触发范围对齐，含 S2-1）

Step 4. 合并 finding，决定输出类
        - 任一 blocking → issues-found
        - 全部 ≤ medium → review-passed

Step 5. 调 progress.py update --event 触发转换
        - review-passed: skills/workflow-protocol/scripts/progress.py update --event review-passed
        - issues-found: skills/workflow-protocol/scripts/progress.py update --event review-issues（finding count summary 通过 history entry result prose 携带；不强制结构化 CLI 参数）
        - 同时在对话输出 §4.2 finding markdown 块
```

## 6. Stage Done Conditions

本 skill 仅贡献 P6 §C 维度（Review 通过）。完整 4 维度由 `progress.py update --advance` 校验：

| 维度 | 本 skill 是否贡献 |
|------|------------------|
| A. 必需 artifacts 存在 | 无（由 srs-write + guardian validate） |
| B. doc-guardian 校验通过 | 间接（§5 Step 1 + advance 时 double-safety）|
| **C. Review 通过** | **直接** |
| D. 人确认 | 无（人 gate 专属）|
| E. 内部验证 | 不适用 |

## 7. Bug Flow Re-entry

`root_cause==srs` 时 bug-triage 切回 srs-specification 后，本 skill 在 srs-write 完成 Change Mode + write-complete 后被 invoke：

```
1. bug_flow.active==true，bug_flow.root_cause==srs，sub_state==in-review
2. 本 skill 评审 SRS Change Mode 改动
   - §3 维度 1-5 全部走（与 unconditional review 相同）
   - §3 维度 7 特化：检查 BUG-NNN 涉及的 SRS 章节有实质改动；不允许仅在 Change Log 加 entry 而 body 不动
   - 关注点：具体 BUG 描述提到的接口 / 数据流 / 边界 是否在 SRS 里被改正
3. review-passed → progress.py update --event review-passed
4. 后续由 workflow-protocol 决定是否 advance 到 architecture 或直接回 testing
   （由 root_cause 影响范围决定；具体 routing 表见 workflow-protocol §6 / command-reference.md）
```

**与 S2-x release-start review 的差异**（v0.6 round 2 M1：S2-x 包含 S2-1/S2-2/S2-3）：

| 维度 | S2-x release-start review（首次进 SRS）| Bug Flow root_cause==srs review |
|------|---------------------------------------|--------------------------------|
| 触发 | `release-start --scenario S2-1\|S2-2\|S2-3` 后本 release 首次进 SRS write → srs-write submit | `bug-start --root-cause srs` 后 srs-write 完成 submit |
| `bug_flow.active` | false | true |
| 维度 7 是否特化 | 一般 release-start consumed_unresolved_bugs 合并完整性检查（事实源 BUG-*.md scan）| BUG-NNN 实质覆盖检查（仅本 active bug）|
| 推 advance 后路径 | 进 Stage 3 Architecture（正常推进）| 由 workflow-protocol 决定（可能跳过 Architecture 直接回 Stage 5）|

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 修改 SRS / Acceptance Plan / Integration Plan / source-system-analysis doc body（即使发现明显 typo；以 finding 形式回给 srs-write）
- ❌ 修改任何 doc frontmatter（`status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`；本 skill 不直接改 —— **Gap-2**）
- ❌ 输出 `approved` / `pending` / `pass` / `fail` / `accept` / `reject` / `LGTM`（仅 `review-passed` / `issues-found`）
- ❌ 创建独立 review-report 类 doc（SRS review 不产 review-report）
- ❌ 修改 BUG-NNN.md（→ bug-triage / testing-write）
- ❌ 跳过 §5 Step 1 `validate.py file` 自检
- ❌ 部分 doc review 即输出 review-passed（必须全部覆盖：SRS + Acceptance + 多模块 Integration + S3 时 3 必备 source-system-analysis；technical-debt 若存在则评审，不存在不阻断 review-passed）
- ❌ 在 `sub_state != in-review` 时操作
- ❌ 在 `current_stage != srs-specification` 时操作
- ❌ 在 `bug_flow.active==true AND bug_flow.root_cause != srs` 时被 invoke 仍继续操作（应让对应 stage review 接管）
- ❌ 在 `workflow_incident_active==true` 时操作
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时操作
- ❌ `review_iteration > 7` 时 issues-found 仍尝试 update
- ❌ 自行决定推进 stage（→ workflow-protocol advance）
- ❌ 漏掉维度 7（unresolved_bugs 合并完整性 / Bug Flow 覆盖检查）就输出 review-passed

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| §5 Step 1 某 doc validate 失败 | 直接 issues-found（finding 1 类：guardian failure on <doc-path>）；caller 修后重 submit |
| §5 Step 5 update --event 失败 | 读 stderr；可能 review_iteration 超 7；先 query 查当前 state |
| 评审时发现 SRS 与 PRD 矛盾（业务级冲突）| 输出 issues-found；finding severity blocking；recommendation 指向 PRD 章节；同时标注 **design gap**：当前 spec 无 PRD `review-passed → revising` 事件，PRD 端修订须升级人介入；srs-review 自身仍按本 stage 处理（不强制 PRD 同步修，给 finding 让 srs-write / 用户选择路径）|
| 评审时发现 unresolved_bugs 列表与 SRS Change Log 不一致 | issues-found；维度 7 blocking finding；列具体哪条 BUG-NNN 漏 / 多 |
| Bug Flow re-entry 时 BUG 涉及章节没改 | issues-found；维度 7 blocking finding；srs-write 须重 Change Mode 实质改 SRS body |
| review_iteration 已 7 次仍 issues-found | progress.py 第 8 次拒绝；caller 须升级人介入；不要尝试绕过 |
| 用户对 review finding 反对（认为误判） | in-review 期间可通过对话指示 caller 重 review；review-passed 后无 in-spec 回 revising 路径（design gap）；不允许本 skill 撤销已发出的 review-issues event（progress-history.md append-only）|
| Doc 物理损坏 / 误删 | 不要恢复；让用户从 git / 人介入 |
| S3 supporting 中 reuse-replace 与 SRS module 切分不匹配 | issues-found；维度 6 blocking；finding 指出具体哪个模块决策与 SRS 不一致 |

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机、bug-start 后 sub_state 转换
- `skills/workflow-protocol/references/command-reference.md` — `update --event review-passed` / `review-issues` 完整签名 + §2.1 sub_state 转移表
- `skills/doc-guardian/SKILL.md` — `validate.py file` 入口；BUG-NNN.md `consumed_in_release` 验证
- `skills/doc-guardian/references/frontmatter-schema.md` — SRS / Acceptance Plan / Integration Plan / source-system-analysis frontmatter / status 状态机
- `skills/doc-guardian/references/required-artifacts.md` — 多模块 Integration Plan 必备性 + S3 必备
- `skills/srs-write/SKILL.md` — write 接管点（issues-found 后 srs-write Change Mode 消化）
- `skills/bug-triage/SKILL.md` — root_cause 来源
- `skills/architecture-review/SKILL.md` — Stage 3 review 接力点

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/review-rubric.md` — 7 维度逐项 checklist + severity 决断 + 典型 finding 例子 + 维度 7 与 `bug-merge-policy.md` 配套的 BUG 合并完整性校验 + anti-patterns + 升级阈值（Phase 7 Task 7-B 拆出）


**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
