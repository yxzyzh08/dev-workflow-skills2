---
name: architecture-review
description: dev-workflow-skills2 Stage 3 Architecture 评审 vertical skill。在 progress.md current_stage==architecture-design AND sub_state==in-review 时被 invoke。读 architecture.md（项目级单文件）+ 本 release architecture_delta.md（若存在）按 rubric 逐 doc 评审 + 跨 doc 一致性 + 与上游 SRS 一致性 + 主 doc / delta 决策合理性 + Bug Flow re-entry 时验证 BUG-NNN 实质覆盖。输出 review-passed / issues-found 两态结论（绝不用 approved），finding 列表回到对话由 architecture-write Change Mode 消化；不写独立 review-report doc。本 skill 不修改 doc body、不直接 mutation progress.md（必经 progress.py）、不签发 approved。
authority: 4
references:
  - references/review-rubric.md
---

# architecture-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（6 项）**：

1. 读 Stage 3 改动 doc：`docs/architecture/architecture.md` + 本 release `docs/release<x.y>/architecture_delta.md`（若存在）
2. 跑 `validate.py file <path>` 自检（每 doc 一次；防评审已损坏 doc）
3. 按 Architecture 评审 rubric（§3）逐维度评审，含跨 doc 一致性（架构主 doc ↔ delta ↔ 上游 SRS）
4. 评审 §3 维度 6（主 doc vs delta 决策合理性）：本 release 改动是否合理地分配到主 doc 或 delta
5. Bug Flow re-entry 时额外评审：BUG-NNN 涉及的架构层是否被实质修改
6. 输出 `review-passed` / `issues-found`（业务术语），分别调 `progress.py update --event review-passed` 或 `--event review-issues`（事实源 command-reference §2 白名单）触发 sub_state 转换（v0.6 round 3 L2 修正：旧版"--event review-passed | issues-found"误把业务术语当 event 名）

**不属于本 skill**：

- 修改 architecture.md / architecture_delta doc body（→ `architecture-write` Change Mode）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py update --event`）
- 签发 `approved`（人 gate 专属）
- 创建 / 编辑 review-report 类 doc（Architecture review 不产 review-report；frontmatter-schema 未注册 `architecture-review-report` type）
- 修改 BUG-NNN.md / SRS / Development plan
- 评审 PRD / SRS / Bug Report / INCIDENT report（→ 对应 review skill）

## 2. When to Invoke

**触发条件**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `workflow_incident_active` | `false` |
| `current_stage` | `architecture-design` |
| `sub_state` | `in-review` |
| `review_iteration` | 0-7 |
| `bug_flow.active` | `false` 或 (`true` AND `bug_flow.root_cause==architecture`) |

**典型 invocation 路径**：

| 时机 | 上游 |
|------|------|
| architecture-write 完成 §5 4-step 后 write-complete | `architecture-write` 调 `progress.py update --event write-complete` 转 `sub_state: in-review` |
| revise 后 architecture-write 重 submit | 同上（review_iteration += 1）|
| Bug Flow re-entry 后 architecture-write Change Mode submit | 同上但 `bug_flow.active==true` |

**不被 invoke 的时机**：

- `sub_state ∈ {write, revising, review-passed, approved}` → 非 review owner 期
- `current_stage != architecture-design`
- `bug_flow.active==true AND bug_flow.root_cause != architecture` → 由对应 review skill 接管
- `workflow_incident_active==true`
- `review_iteration > 7` → progress.py 拒绝；需升级人介入

## 3. Review Rubric Overview

Architecture 评审涵盖 7 个维度。完整 rubric 与 severity 标准将在本 skill 后续 references 中拆出（batch 3a 评审通过后规划 `references/review-rubric.md`）。

| # | 维度 | 关键问题 | Severity 影响 |
|---|------|---------|---------------|
| 1 | **完整性 (per-doc)** | architecture.md：组件 / 接口 / 数据流 / 部署 / 关键决策 章节齐全；architecture_delta：本 release 增量描述完整（哪个组件 / 接口 / 数据流变了，为什么变）| 缺核心章节 → blocking |
| 2 | **跨 doc 一致性（主 doc ↔ delta）** | delta 中的"基础架构"假设与主 doc 一致；delta 不破坏主 doc 长期事实（除非 §3.1 决策长期事实路径已说明并同步更新主 doc）| 主-delta 失配 → blocking |
| 3 | **与上游 SRS 一致性** | SRS 的功能性 / 非功能性需求 → 架构组件 / 接口 / 数据流的映射完整；多模块时 SRS 的 module list 与架构组件切分对应；S3 时 reuse-replace 决策在架构中体现 | 上游需求未映射 → blocking |
| 4 | **可决策性** | 架构描述是否够具体让 Stage 4 Development 下展开（接口签名 / 数据 schema / 关键算法 / 部署假设 可决策）？非功能需求量化 → 架构层兑现路径明确？| 含糊 → blocking |
| 5 | **Change Log 与 frontmatter 业务合理** | Pending Changes 已 promote；Change Log 与 doc body 改动一致；delta `parent_architecture` 指向主 doc；frontmatter `release` / `updated` 合理 | 改动语义与 Change Log 不一致 → blocking |
| 6 | **主 doc vs delta 决策合理性（仅 S2 / Bug Flow + delta 存在时）** | architecture-write §3.1 决策树是否被合理应用？长期事实是否回写主 doc？仅本 release 局部变化是否仅写 delta？| 决策错误（如长期事实仅写 delta）→ blocking |
| 7 | **Bug Flow 实质覆盖（仅 root_cause==architecture）** | BUG-NNN 涉及的架构层（组件 / 接口 / 数据流）是否被实质修改（不是单加 Change Log entry 不动 body）；§7.1 改 doc 决策（主 vs delta）是否符合 architecture-write §7.1 表 | 漏改实质 → blocking |

**关于 doc-guardian 与 architecture-review 的边界**：

- `validate.py` 校验机器层格式（路径 / frontmatter schema / Change Log 章节存在 / Cross-Reference 有效 / delta `parent_architecture` 指向 等）
- `architecture-review` 校验业务层语义（架构合理性、与 SRS 一致、决策路径合理）
- 二者互补；architecture-review 仅在 `validate.py file` 全 exit 0 之后才开始业务评审

## 4. Output Contract

### 4.1 输出形式（两类）

**类 A：review-passed**

- 全部维度无 blocking finding
- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`
- progress-history.md 追加：`...— architecture-review iteration N — review-passed (X non-blocking suggestions, covered architecture<? + delta>)`
- 每个 doc frontmatter `status: in-review → review-passed` 由 **`skills/doc-guardian/scripts/status_transition.py`** 在 `progress.py update --event review-passed` 之后同步（owner = doc-guardian；调用 `skills/doc-guardian/scripts/status_transition.py apply --event review-passed --doc <path> ...`；**Gap-2** 见 §10）；本 skill 不直接改 doc
- 控制权移交：等待人 gate

**类 B：issues-found**

- 至少 1 条 blocking finding
- 调 `progress.py update --event review-issues`（v0.6 round 1 Implementability：finding count / max severity 通过 history entry result prose 携带；不强制结构化 CLI 参数；具体接口待 progress.py 升级）
- progress.md sub_state 转换由 progress.py command-reference 定义
- progress-history.md 追加：`...— architecture-review iteration N — issues-found (B blocking, M medium, L low)`
- finding 列表通过对话回给 caller；不写独立 review-report doc

### 4.2 Finding 描述模板

```markdown
## architecture-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low
**Coverage**: architecture.md<? + delta release-x.y>

### Finding 1 [blocking, 维度 6: 主 doc vs delta 决策]
- **Where**: architecture_delta.md §2.1 新增组件 / architecture.md 主 doc 未同步
- **Issue**: 新增组件 X 是长期事实（下个 release 起点应包含），但仅写在 delta；主 doc 未同步
- **Recommendation**: 把组件 X 的接口与职责回写到 architecture.md §3.2；保留 delta 的 release 时间线说明

### Finding 2 [blocking, 维度 7: Bug Flow 覆盖]
- **Where**: BUG-007 描述 API 限流策略缺陷 / architecture_delta.md 仅加 Change Log entry 未改限流章节
- **Issue**: 限流策略仍按旧描述；本次 Change 实质未覆盖 bug
- **Recommendation**: 在 architecture_delta §4.3 改写限流策略；如属长期事实同步主 doc §6.2
...
```

### 4.3 严禁的输出术语

| 严禁 | 原因 |
|------|------|
| `approved` | 人 gate 专属 |
| `pending` / `pass` / `fail` | 三态术语仅 Stage 4 dev-test/dev-code review 用 |
| `accept` / `reject` / `LGTM` | 非术语化 |

## 5. Review Procedure（5 步）

```
Step 1. 跑 validate.py file 自检（主 doc + delta 各一次）
        - skills/doc-guardian/scripts/validate.py file docs/architecture/architecture.md
        - delta 存在时：skills/doc-guardian/scripts/validate.py file docs/release<x.y>/architecture_delta.md
        - 任一 exit 1 → 不进业务评审；直接 issues-found（finding 1 类：guardian failure）；caller architecture-write 修后重 submit
        - 全部 exit 0 → 进 Step 2

Step 2. 读所有改动 doc + 上游 SRS 关键章节 + 上轮 review iteration
        - architecture.md / architecture_delta.md
        - 上游 SRS：本 release 的 docs/release<x.y>/srs/srs.md（重点功能性 / 非功能性需求）
        - 跨 release 一致性：previous release 的 architecture_delta（如有）
        - 读 progress-history.md 最近 architecture-review entry（参考上轮 finding 是否消化）
        - Bug Flow re-entry 时读 docs/bug/BUG-NNN.md

Step 3. 按 §3 7 维度逐项评审
        - 维度 1-5: 全场景适用
        - 维度 6: 仅 S2-x / Bug Flow + delta 存在时
        - 维度 7: 仅 bug_flow.active==true AND bug_flow.root_cause==architecture

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
| A. 必需 artifacts 存在 | 无（由 architecture-write + guardian validate） |
| B. doc-guardian 校验通过 | 间接（§5 Step 1 + advance 时 double-safety）|
| **C. Review 通过** | **直接** |
| D. 人确认 | 无（人 gate 专属）|
| E. 内部验证 | 不适用（Architecture 是设计 doc；运行时验证在 Stage 5/6）|

## 7. Bug Flow Re-entry

`root_cause==architecture` 时 architecture-write Change Mode 完成后本 skill 接管：

```
1. bug_flow.active==true，bug_flow.root_cause==architecture，sub_state==in-review
2. 本 skill 评审 architecture-write Change Mode 改动
   - §3 维度 1-5 全部走（与 unconditional review 相同）
   - §3 维度 6 特化：本次改动是否合理分配到主 doc / delta
   - §3 维度 7 启用：BUG-NNN 涉及架构层是否被实质修改；§7.1 表（架构-write SKILL.md）是否被合理应用
3. review-passed → progress.py update --event review-passed
4. 后续由 workflow-protocol 决定 advance 路径（可能进 Stage 4 或直接回 Stage 5 重测）
```

**与 S2-x Change Mode review 的差异**：

| 维度 | S2-x Change Mode review | Bug Flow root_cause==architecture review |
|------|-----------------------|------------------------------------------|
| 触发 | `release-start --scenario S2-x` 后 architecture-write 完成 submit | `bug-start --root-cause architecture` 后 architecture-write 完成 submit |
| `bug_flow.active` | false | true |
| 维度 6 | 评审常规 release 增量决策 | 评审 bug 引发的决策（typically 长期事实路径，因为运行时缺陷）|
| 维度 7 | 不启用 | 启用（实质覆盖检查）|

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 修改 architecture.md / architecture_delta doc body（即使发现明显 typo；以 finding 形式回给 architecture-write）
- ❌ 修改任何 doc frontmatter（`status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`；本 skill 不直接改 —— **Gap-2**）
- ❌ 输出 `approved` / `pending` / `pass` / `fail` / `accept` / `reject` / `LGTM`（仅 `review-passed` / `issues-found`）
- ❌ 创建独立 review-report 类 doc（Architecture review 不产 review-report）
- ❌ 修改 BUG-NNN.md / SRS / Development plan（→ 对应 skill）
- ❌ 跳过 §5 Step 1 `validate.py file` 自检
- ❌ 部分 doc review 即输出 review-passed（主 doc + delta 同时改时必须全部覆盖）
- ❌ 在 `sub_state != in-review` 时操作
- ❌ 在 `current_stage != architecture-design` 时操作
- ❌ 在 `bug_flow.active==true AND bug_flow.root_cause != architecture` 时操作
- ❌ 在 `workflow_incident_active==true` 时操作
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时操作
- ❌ `review_iteration > 7` 时 issues-found 仍尝试 update
- ❌ 自行决定推进 stage（→ workflow-protocol advance）
- ❌ 漏掉维度 6 / 7 就输出 review-passed（特化场景必须评审）
- ❌ 直接判断主 doc vs delta 决策应该是哪种（仅评审 architecture-write 已做的决策；不替 architecture-write 决策）

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| §5 Step 1 主 doc / delta validate 失败 | 直接 issues-found（finding 1 类：guardian failure on <doc-path>）；caller 修后重 submit |
| §5 Step 5 update --event 失败 | 读 stderr；review_iteration 超 7 → 升级人介入；先 query 查当前 state |
| 评审时发现 architecture 与 SRS 矛盾 | issues-found；维度 3 blocking；recommendation 指向具体 SRS 章节；同时标注 **design gap**：当前 spec 无 SRS `review-passed → revising` 事件，SRS 端修订须升级人介入；architecture-review 自身仍按本 stage 处理 |
| 评审时发现主 doc / delta 决策路径错误（如长期事实仅写 delta）| issues-found；维度 6 blocking；明确指出应在主 doc 同步哪些决策 |
| Bug Flow 时 BUG 涉及章节未实质改 | issues-found；维度 7 blocking；要求 architecture-write 在 Change Mode 实质改 doc body |
| 跨 release 一致性问题（previous release delta 与本 release delta 矛盾）| issues-found；维度 2 blocking；recommendation 指向 architecture-write 上一 release 是否漏把"长期事实"同步到 architecture.md（v0.6 round 1 H3：spec 无 release-close 自动合并 hook，必须 architecture-write 同步两份 doc）；**不**自行修历史 release |
| review_iteration 已 7 次仍 issues-found | progress.py 第 8 次拒绝；caller 升级人介入 |
| 用户对 review finding 反对 | in-review 期间可通过对话指示 caller 重 review；review-passed 后无 in-spec 回 revising 路径（design gap）；不允许本 skill 撤销已发出的 review-issues event（progress-history.md append-only）|
| Doc 物理损坏 / 误删 | 不要恢复；让用户从 git / 人介入 |

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机、bug-start mutation、release-close mutation（**不含** delta → 主 doc 合并 hook；v0.6 round 1 H3 决议；维度 2 评审基于此）
- `skills/workflow-protocol/references/command-reference.md` — `update --event review-passed` / `review-issues` 完整签名 + §2.1 sub_state 转移表
- `skills/doc-guardian/SKILL.md` — `validate.py file` 入口；delta `parent_architecture` 校验
- `skills/doc-guardian/references/frontmatter-schema.md` — architecture / architecture-delta frontmatter 与 status 状态机
- `skills/doc-guardian/references/required-artifacts.md` — 何时 architecture_delta 必备
- `skills/architecture-write/SKILL.md` — write 接管点；§3.1 决策树 + §7.1 Bug Flow 表
- `skills/srs-write/SKILL.md` — 上游 SRS 来源（评审 §3 维度 3 时参考）
- `skills/bug-triage/SKILL.md` — root_cause==architecture 来源

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/review-rubric.md` — 7 维度逐项 checklist + severity 决断 + 典型 finding 例子 + 维度 6 与 architecture-write `delta-policy.md` 配套的主 doc vs delta 决策校验 + 维度 7 Bug Flow 实质覆盖检查 + anti-patterns + 升级阈值（Phase 7 Task 7-B 拆出）


**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
