---
name: prd-review
description: dev-workflow-skills2 Stage 1 PRD 评审 vertical skill。在 progress.md current_stage==prd-inception AND sub_state==in-review 时被 invoke。读 PRD 主文档（S3 时含 supporting artifacts: prd-level + feature-matrix）按 rubric 评审，输出 review-passed / issues-found 两态结论（绝不用 approved；approved 是 D 维度人 gate 后的 frontmatter 字段，非 review 输出）。finding 列表回到对话由 prd-write Change Mode 消化；progress-history.md 仅记 event + issue summary，不产独立 review-report doc（三态 review-report 仅 Stage 4 dev-test/dev-code review 用）。本 skill 不修改 doc body、不直接 mutation progress.md（必经 progress.py）、不签发 approved（人 gate 专属）。
authority: 4
references:
  - references/review-rubric.md
---

# prd-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`）。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 4（与其他 vertical stage skill / orchestration skill 同级）。

**职责（5 项）**：

1. 读 `docs/prd/prd.md`（+ S3 时 supporting artifacts: `source_product_prd_analysis.md` / `feature_matrix.md`）
2. 跑 `validate.py file <doc-path>` 自检（防评审已损坏的 doc；exit 0 才进入 rubric 评审）
3. 按 PRD 评审 rubric（§3）逐维度评审，输出 finding 列表（severity / 维度 / 改动建议）
4. 输出 `review-passed`（无 finding 或 finding 全部为非 blocking 类）或 `issues-found`（含 blocking finding）
5. 调 `progress.py update --event review-passed` 或 `--event review-issues` 触发 sub_state 转换；event 同时携带 issue count summary

**不属于本 skill**：

- 修改 PRD doc body（→ `prd-write` Change Mode 消化 finding）
- 直接 mutation `progress.md` / `progress-history.md`（必经 `progress.py update --event`）
- 签发 `approved`（人 gate 专属；本 skill 输出最高态是 `review-passed`）
- 创建 / 编辑 review-report 类 doc（PRD review **不产** review-report；三态 review-report 仅 Stage 4 dev-test/dev-code review 用）
- 评审 SRS / Architecture / Bug Report / INCIDENT report（→ 对应 review skill）
- 评审 PRD 之外的 supporting artifacts（如 `competitor_research.md`，optional 类不强制 review）

## 2. When to Invoke

**触发条件（本 skill 是 owner 当且仅当 progress.md 满足）**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `bug_flow.active` | `false` |
| `workflow_incident_active` | `false` |
| `current_stage` | `prd-inception` |
| `sub_state` | `in-review` |
| `review_iteration` | 0-7（≤7；若 = 7 且本轮再 issues-found，progress.py update 会拒绝写入 → 升级人介入）|

**典型 invocation 路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| prd-write 完成 §5 4-step → write-complete | `prd-write` 调 `progress.py update --event write-complete` 转 `sub_state: in-review` | 接管，启动评审 |
| revise 后再次提交 review | `prd-write` Change Mode revise 完成后再次 `write-complete`（review_iteration += 1 由上一轮 issues-found 时已计）| 重新评审 |

**不被 invoke 的时机**：

- `sub_state ∈ {write, revising, review-passed, approved}` → 非 review owner 期
- `current_stage != prd-inception` → 由对应 stage 的 review skill 接管
- `bug_flow.active==true` 或 `workflow_incident_active==true` → 异常路径，让 bug-triage / workflow-evolution 接管
- `review_iteration > 7` → progress.py 已拒绝；不应被 invoke

## 3. Review Rubric Overview

PRD 评审涵盖以下 6 个维度。完整 rubric（含逐维度具体 checklist + severity 标准）将在本 skill 后续 references 中拆出（batch 3a 评审通过后规划 `references/review-rubric.md`）。本节仅给概要。

| # | 维度 | 关键问题 | Severity 影响 |
|---|------|---------|---------------|
| 1 | **完整性** | 产品定位 / 用户故事 / 关键功能集 / 非功能需求 / 边界假设 等核心章节是否齐全？ | 缺失核心章节 → blocking |
| 2 | **业务一致性** | 内部章节是否互相支撑（如功能列表与用户故事互相印证；非功能需求与功能可行性不冲突）？ | 内部矛盾 → blocking |
| 3 | **可决策性** | 描述是否足够具体让 SRS 阶段能下展开（关键功能可拆 module / 非功能需求可量化）？ | 含糊到无法 SRS → blocking |
| 4 | **业务术语清晰** | 关键术语在文中首现处定义；不混用同义词；专有名词稳定 | 术语漂移 → non-blocking（提建议）|
| 5 | **Change Log 与 frontmatter 业务合理** | Pending Changes 已 promote；Change Log 各 entry 描述与 doc body 改动一致；frontmatter `title`/`status`/`updated` 合理 | 改动语义与 Change Log 不一致 → blocking |
| 6 | **S3 源系统分析深度（仅 S3）** | `source_product_prd_analysis.md`：源系统功能 / 痛点 / 重构动因明确；`feature_matrix.md`：源 vs 新 功能映射完整且可决策 | S3 缺关键源系统对照 → blocking |

**关于 doc-guardian 与 prd-review 的边界**：

- `validate.py` 校验**机器层格式**（路径 / frontmatter schema / Change Log 章节存在 / Cross-Reference 有效 等）
- `prd-review` 校验**业务层语义**（章节内容是否合理、可决策、互相一致）
- 二者互补；prd-review 仅在 `validate.py file` exit 0 之后才开始业务评审（防评审已损坏的 doc）

## 4. Output Contract

### 4.1 输出形式（两类）

**类 A：review-passed**

- 全部维度无 blocking finding（可有 non-blocking 建议）
- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`；`review_iteration → 0`（v0.6 round 1 M3 修正：归零由 `progress.py update --event review-passed` 事件本身执行；事实源 command-reference §2 白名单表 + §2.1 转移表，**不**是 advance 时才归零）
- progress-history.md 追加一条 entry：`...— prd-review iteration N — review-passed (X non-blocking suggestions)`
- doc frontmatter `status: in-review → review-passed` 由 **`skills/doc-guardian/scripts/status_transition.py`** 在 `progress.py update --event review-passed` 之后同步（owner = doc-guardian；调用 `skills/doc-guardian/scripts/status_transition.py apply --event review-passed --doc <path> ...`；**Gap-2** 见 §10）；本 skill 不直接改 doc
- 控制权移交回主流程：等待人 gate（D 维度）

**类 B：issues-found**

- 至少 1 条 blocking finding
- 调 `progress.py update --event review-issues`（v0.6 round 1 Implementability：command-reference §2 update 仅定义 4 白名单 event 名 + `[--params ...]` 通配；finding 数 / max severity 携带方式由 progress.py implementation 决定，本 SKILL.md 不强制结构化 CLI 参数。当前推荐 caller 在 history entry result 字段中以 prose 形式记 `B/M/L counts + max_severity` 摘要；具体接口待 progress.py 升级）
- progress.md：`sub_state: in-review → revising` 由 `--event review-issues` 状态机自动转换（见 workflow-protocol command-reference.md §2.1 转移表；同事件触发 `review_iteration += 1`，prd-write 不需也不可调单独的 start 类事件）
- progress-history.md 追加一条 entry：`...— prd-review iteration N — issues-found (B blocking, M medium, L low)`
- finding 列表通过对话回给 caller（typically `prd-write` 在 revise 时直接读对话上下文）；不写独立 review-report doc

### 4.2 Finding 描述模板

review skill 在对话输出 markdown 块（caller agent / 用户可读）：

```markdown
## prd-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low

### Finding 1 [blocking, 维度 1: 完整性]
- **Where**: §<section ref> / line <range or N/A>
- **Issue**: <一句话问题描述>
- **Recommendation**: <可执行修改建议>

### Finding 2 [medium, 维度 4: 业务术语清晰]
...
```

**Severity 定义**：

| Severity | 含义 | 处置 |
|---------|------|------|
| `blocking` | 阻断 review-passed | issues-found；必修 |
| `medium` | 建议修但不阻断 | 视情况修；不阻断 review-passed（同轮可一并出，但单独 medium/low → 仍可 review-passed）|
| `low` | 提示 / 风格类 | 不修也行 |

review-passed 的判定：**全部 finding 中无 blocking**。即使有 medium / low 建议也可 review-passed（issues 在 progress-history 摘要里照样列出，但不阻 advance）。

### 4.3 严禁的输出术语

| 严禁 | 原因 |
|------|------|
| `approved` | 人 gate 专属（D 维度）；review skill 输出 `approved` 等于越权人 gate |
| `pending` / `pass` / `fail` | 三态术语仅 Stage 4 dev-test/dev-code review 用；PRD review 是两态 |
| `accept` / `reject` / `OK` / `LGTM` | 非术语化输出；caller / 用户解析困难 |

## 5. Review Procedure（5 步）

```
Step 1. 跑 validate.py file <doc-path> 自检
        - skills/doc-guardian/scripts/validate.py file docs/prd/prd.md
        - exit 0 → 进 Step 2
        - exit 1 → 不进入业务评审；直接 issues-found（finding 1 类：guardian 失败）；caller 须由 prd-write 修 doc
        - S3 时对每个 supporting artifact 单独跑

Step 2. 读 PRD 全文 + 上轮 review iteration（如有）
        - 读 docs/prd/prd.md doc body + frontmatter
        - 读 progress-history.md 最近 prd-review entry（参考上轮 finding 是否被 prd-write Change Mode 消化）
        - S3 时读 supporting artifacts

Step 3. 按 §3 6 维度逐项评审
        - 每维度产出 0+ finding
        - 每 finding 标注 severity / 维度 / where / issue / recommendation
        - 维度 6（S3）：scenario != S3 时跳过

Step 4. 合并 finding，决定输出类
        - 任一 finding severity == blocking → 输出 issues-found
        - 全部 finding ∈ {medium, low} 或无 finding → 输出 review-passed

Step 5. 调 progress.py update --event 触发转换
        - review-passed: skills/workflow-protocol/scripts/progress.py update --event review-passed
        - issues-found: skills/workflow-protocol/scripts/progress.py update --event review-issues
                        （finding count summary 通过 history entry result prose 携带；不强制结构化 CLI 参数）
        - 同时在对话输出 §4.2 finding markdown 块（issues-found 时必须；review-passed 时若有 non-blocking 建议也输出）
```

## 6. Stage Done Conditions

本 skill 仅贡献 P6 §C 维度（Review 通过）。完整 4 维度由 `progress.py update --advance` 统一校验：

| 维度 | 本 skill 是否贡献 | 关系 |
|------|------------------|------|
| A. 必需 artifacts 存在 | 无 | 由 `prd-write` Step 1 写、guardian validate 校验 |
| B. doc-guardian 校验通过 | 间接 | §5 Step 1 跑 validate；最终校验由 advance 时 workflow-protocol 再跑 double-safety |
| **C. Review 通过** | **直接** | review skill 最近一轮输出 `review-passed`（progress-history.md 末条 prd-review entry 是 review-passed）|
| D. 人确认 | 无 | 人 gate；用户在 review-passed 后手动确认；本 skill 不签发 approved |
| E. 内部验证 | 不适用 | PRD 无内部 verification 概念 |

**review-passed 后的行为**：本 skill 退出。后续人 gate 由两步原子 mutation 完成：(1) caller 调 `skills/workflow-protocol/scripts/progress.py update --event human-confirmed` 把 `sub_state: review-passed → approved`（progress-history.md 自动加 `human-confirmed` 条目）；(2) caller 调 `skills/doc-guardian/scripts/status_transition.py apply --event human-confirmed --doc docs/prd/prd.md` 把 PRD frontmatter `status: review-passed → approved`。两步均成功后 caller 调 `progress.py update --advance` 推进 Stage 2 SRS（advance D 维度入口是 `sub_state==approved`，不重读 doc.status；事实源 command-reference §2.2）。

## 7. Bug Flow Re-entry

**关键规则**：本 skill **不会**通过 Bug Flow 被 re-entry。

理由：

- Bug Flow `root_cause` 4 类不含 `prd`；`prd-exception` 走 `incident-start` 进 workflow-evolution，不切 prd-inception
- 其他 3 类（srs / architecture / development）不影响 PRD，因此不触发 prd 阶段重审

本 skill 仅通过以下 1 条路径被 invoke：

- `prd-write` 调 `progress.py update --event write-complete` 后接管评审

**例外说明（design gap）**：当前 workflow-protocol command-reference.md §2.1 转移表未提供 `review-passed → revising` 事件；若用户在 review-passed 后、人 gate 之前发现 PRD 错，目前**无 in-spec 路径**让本 skill 再次被 invoke。须升级人介入或新一轮 design proposal 增加事件。该路径不经 Bug Flow。

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`（mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- ❌ 修改 PRD doc body（即使发现明显 typo；必须以 finding 形式回给 prd-write）
- ❌ 修改 PRD frontmatter（`status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`，由 helper 在 `progress.py update --event` 之后同步；本 skill 不直接改 —— **Gap-2**）
- ❌ 输出 `approved` / `pending` / `pass` / `fail` / `accept` / `reject` / `LGTM` 等非法术语（仅 `review-passed` / `issues-found`）
- ❌ 创建独立 review-report 类 doc（PRD review **不产** review-report；frontmatter-schema 未注册 `prd-review-report` type）
- ❌ 跳过 §5 Step 1 `validate.py file` 自检直接进入业务评审（评审已损坏 doc 是浪费）
- ❌ 在 `sub_state != in-review` 时 invoke 仍继续操作（应让 caller 重新路由）
- ❌ 在 `current_stage != prd-inception` 时操作（由其他 review skill 接管）
- ❌ 在 `bug_flow.active==true` 或 `workflow_incident_active==true` 时操作（让 bug-triage / workflow-evolution 接管）
- ❌ 在 `project_state ∈ {aborted, reconstructing}` 时操作（终态；progress.py 会拒绝 mutation）
- ❌ `review_iteration > 7` 时 issues-found 仍尝试 update（progress.py 会拒绝；caller 须升级人介入）
- ❌ 自行决定推进 stage（→ workflow-protocol 在 advance 时统一判定）
- ❌ S3 场景跳过 supporting artifacts 评审（维度 6）→ S3 review-passed 的判定漏掉源系统分析深度

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|---------|---------|
| §5 Step 1 `validate.py file` 失败 | 不进入业务评审；直接调 `progress.py update --event review-issues`，finding 1 类：guardian validation failed at <stderr summary>；caller `prd-write` 修后重 submit |
| §5 Step 5 `progress.py update --event review-passed` 失败 | 读 stderr：可能是 `review_iteration` 异常 / sub_state 不合法转换；先 `progress.py query` 看当前 state；若 state 异常 caller 手动修 |
| §5 Step 5 `progress.py update --event review-issues` 失败 | 同上；如果 review_iteration 已 7，下次 issues-found 触发 cap 拒绝 → 升级人介入 |
| Review 时发现 PRD 与 workflow spec 矛盾（业务级冲突）| 仍输出 issues-found；finding 标注 severity blocking；recommendation 指向具体 spec 章节；不要尝试调和（让用户决定）|
| 用户对 review finding 反对（认为 prd-review 误判）| in-review 期间可通过对话指示 caller 重 review（不发 review-issues / review-passed）；review-passed 后无 in-spec 回 revising 路径（design gap）；不允许本 skill 自行撤销已发出的 review-issues event（progress-history.md append-only）|
| review_iteration 已达 7 次仍 issues-found | progress.py 第 8 次 update --event review-issues 会拒绝；caller 必须升级人介入；不要尝试绕过（如手工编辑 progress.md `review_iteration`）|
| Doc 物理损坏 / 误删 | 不要恢复；让用户从 git / 人介入恢复；review skill 不写 doc body |

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — 状态机 / sub_state 转换 / review_iteration cap
- `skills/workflow-protocol/references/command-reference.md` — `progress.py update --event review-passed` / `review-issues` 完整签名 + §2.1 sub_state 转移表
- `skills/doc-guardian/SKILL.md` — `validate.py file` 入口
- `skills/doc-guardian/references/frontmatter-schema.md` — PRD type frontmatter / status 状态机；确认无 `prd-review-report` 注册
- `skills/doc-guardian/references/required-artifacts.md` — S3 必备 supporting artifacts
- `skills/prd-write/SKILL.md` — write 接管点（review-passed 后 prd-write 不再修；issues-found 后 prd-write Change Mode 消化）

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md` — Workflow spec
- `docs/design/skill_set_design_proposal_v0.5.md` — 完整设计方案

**本 skill references**：

- `references/review-rubric.md` — 6 维度逐项 checklist + severity 决断 + 典型 finding 例子 + anti-patterns + 升级阈值（Phase 7 Task 7-B 拆出）

**Design Gaps（本 batch 3a 已识别，留 codex / 后续 batch 解决）**：

- **Gap-1**：`review-passed → revising` 转移缺失（见 §7 / §9 描述；待 workflow-protocol 增加新事件）
- **Gap-2**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`。每次 `skills/workflow-protocol/scripts/progress.py update --event <name>` 成功后，caller（write/review skill 或 AGENTS.md Bootstrap）必须调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...` 同步当前 stage 改动 artifacts 的 frontmatter `status`。覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 PRD/SRS/Architecture/CR gated stage）→ `review-passed → approved`。helper 负责增量类 doc 的 `[frontmatter]` Pending Changes → Change Log 原子 promote、失败回滚与幂等重试。
