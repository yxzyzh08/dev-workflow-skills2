---
name: doc-guardian
description: dev-workflow-skills2 文档基础设施守卫者。负责文档目录结构、命名 convention、frontmatter schema、change log 格式、binary 校验（exit 0/1）。任何 stage skill 在产出 doc 后**必须 invoke** 本 skill 的 validate.py 校验通过才能 declare done；validate fail 即 block 推进。CR/Bug/Incident/source-system-analysis/code-review-report 等所有 doc 类型由本 skill 统一管辖（无独立 cr-guardian）。
authority: 3
references:
  - references/directory-layout.md
  - references/frontmatter-schema.md
  - references/change-log-format.md
  - references/required-artifacts.md
---

# doc-guardian

> **Path Convention Note**（v0.6 round 2 L9）：本 skill 文档为可读性使用 `validate.py` / `changelog.py` / `status_transition.py` 简写指代脚本；**实际 invocation 必须用完整路径** `skills/doc-guardian/scripts/validate.py`、`skills/doc-guardian/scripts/changelog.py` 与 `skills/doc-guardian/scripts/status_transition.py`。`progress.py` 简写指 `skills/workflow-protocol/scripts/progress.py`。简写仅用于行内 prose / 表格密集处；正式 cross-skill prose 与 Forbidden Actions 一律完整路径。

## 1. Authority & Scope

**权威优先级**：第 3（位于 `workflow-protocol` 和 `AGENTS.md` 之后）。

**职责**：

1. 定义文档目录结构（`references/directory-layout.md`）
2. 定义命名 convention
3. 定义 frontmatter schema（universal + per-type，含 `references/frontmatter-schema.md`）
4. 定义 change log 格式与自动化（`references/change-log-format.md`）
5. 提供 binary 校验：`scripts/validate.py`（8 类 check，exit 0/1）
6. 提供 change log 自动化：`scripts/changelog.py`（promote / validate）
7. 提供 frontmatter `status` 自动化：`scripts/status_transition.py`（Task 6 Gap-2）
8. 集中声明 scenario-aware required artifacts（`references/required-artifacts.md`）

**不属于本 skill**：

- 文档 body 章节内容 → 由各 `*-write` / `*-review` skill pair 协调
- doc 内容质量评审 → 各 `*-review` skill
- 进度 / 状态管理 → `workflow-protocol`

## 2. When to Invoke

| 时机 | 调用 |
|------|------|
| `*-write` skill 完成 doc draft | `validate.py file <doc-path>` |
| `*-write` skill 编辑 incremental doc 完毕 | `changelog.py promote <doc-path>` |
| `progress.py update --event <name>` 成功后 | `status_transition.py apply --event <name> --doc <path> ...` |
| `workflow-protocol update --advance` 推进 stage 时 | `validate.py file <each artifact>` |
| Stage 推进前的 cross-file 一致性 check | `validate.py consistency` |
| 全量 doc 健康检查 | `validate.py all` |
| 检查 ID 唯一性（CR/Bug/Incident）| `validate.py ids` |

**任何 doc 类产物 declare done 前必须经 `validate.py file` exit 0**。validate fail 即 block 推进。

## 3. Doc Type Catalog (核心简表)

完整 schema 见 `references/frontmatter-schema.md`。本节仅列 type → 路径的快查表。

### 项目级（不绑定 release）

| Type | 路径 |
|------|------|
| `prd` | `docs/prd/prd.md` |
| `architecture` | `docs/architecture/architecture.md` |
| `retrospective` | `docs/retrospective/retrospective.md` |

### Release 级（绑定 release）

| Type | 路径 |
|------|------|
| `srs` | `docs/release<x.y>/srs/srs.md` |
| `acceptance-plan` | `docs/release<x.y>/srs/acceptance_plan.md` |
| `integration-plan` | `docs/release<x.y>/srs/integration_plan.md` |
| `architecture-delta` | `docs/release<x.y>/architecture_delta.md` |
| `development-plan` | `docs/release<x.y>/development/plan.md` |
| `task-breakdown` | `docs/release<x.y>/development/breakdown.md` |
| `test-preparation` | `docs/release<x.y>/testing/preparation.md` |
| `test-procedure` | `docs/release<x.y>/testing/procedure.md` |
| `test-report` | `docs/release<x.y>/testing/report.md` |
| `deployment-doc` | `docs/release<x.y>/delivery/deployment.md` |
| `operation-manual` | `docs/release<x.y>/delivery/operation_manual.md` |
| `installation-result` | `docs/release<x.y>/delivery/installation_result.md` |

### Per-Task（绑定 release + task）

| Type | 路径 |
|------|------|
| `detailed-design` | `docs/release<x.y>/development/tasks/Tn/detailed_design.md` |
| `test-review-report` | `docs/release<x.y>/development/tasks/Tn/test_review_report.md`（v0.6 F7 新增；与 code-review-report 对称）|
| `code-review-report` | `docs/release<x.y>/development/tasks/Tn/code_review_report.md` |
| `verification-result` | `docs/release<x.y>/development/tasks/Tn/verification_result.md` |

### 跨 Release（带 ID）

| Type | 路径 |
|------|------|
| `cr` | `docs/cr/CR-NNN.md` |
| `bug-report` | `docs/bug/BUG-NNN.md` |
| `workflow-incident` | `docs/incident/INCIDENT-NNN.md` |

### 附属 / 分析

| Type | 路径 | 备注 |
|------|------|------|
| `source-system-analysis`（含 6 种 `analysis_kind`）| 见 `references/directory-layout.md` | S3 必备/推荐 |
| 其他 PRD 附属（`competitor-research` 等）| `docs/prd/supporting/` | 按需 |

## 4. Frontmatter Schema (核心简表)

完整 per-type schema 见 `references/frontmatter-schema.md`。

### 4.1 Universal（所有 doc 必含）

```yaml
---
title: <human readable>
type: <doc-type-id>
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/<skill_name>
---
```

### 4.2 Status 状态机

| 状态 | 含义 | 适用 |
|------|------|------|
| `draft` | 写作中 | 全部 doc |
| `in-review` | review skill 评审中 | 全部 doc |
| `revising` | 修订中（write skill Change Mode）| 全部 doc |
| `review-passed` | AI review 通过（**最终态：非 gated 文档**）| 全部 doc |
| `approved` | 人确认通过（**最终态：仅人 gate 后**）| **PRD / SRS / Architecture / CR** |

**术语强调**：

- doc frontmatter `status: review-passed` = 该 doc 整体进入 AI 已通过状态
- review skill **输出**（report 文档）用 `review-passed` / `issues-found`，**绝不用 `approved`**
- `approved` 仅用于人 gate 通过后的 doc status

### 4.3 关键字段格式约定

| 字段 | 规则 |
|------|------|
| `title` | 任意 string |
| `type` | enum（见 §3） |
| `status` | enum |
| `created` / `updated` | ISO8601 UTC（如 `2026-05-15T10:00:00Z`），脚本可解析、可比较 |
| `owner` | `<agent_id>/<skill_name>` 形如 `claude-opus-4-7/srs-write`；`/` 分隔 |
| `release` | 字符串 `"<MAJOR>.<MINOR>"`（YAML 中必须加引号；regex `^(\d+)\.(\d+)$`）|
| `cr_id` / `bug_id` / `incident_id` | `CR-\d{3}` / `BUG-\d{3}` / `INCIDENT-\d{3}`（v0.6 round 3 L5：强制 3 位 zero-padded；大写连字符）|
| `task_id` | `T\d+`（如 `T1`、`T15`）|
| `verification_status` | `pass | fail | partial`（仅 verification artifacts）|
| `review_status`（code-review-report 与 test-review-report）| `pending | pass | fail`（v0.6 round 4 H1：skeleton=pending；transition 需 pass；详见 frontmatter-schema 三态不变量）|
| `analysis_kind`（仅 source-system-analysis）| `prd-level | feature-matrix | srs-level | module-level | reuse-replace | technical-debt` |

### 4.4 Per-Type 必含扩展字段（v0.6 F6 与详细 schema 对齐）

| Type | 必含扩展 |
|------|---------|
| `srs`（v0.6 round 3 M4 加 2 bool）| `release`, **`is_multi_module: bool`**, **`architecture_change: bool`**（required-artifacts.md DSL 关键依赖；validate.py 类 3 必须校验存在且 YAML bool 合法）|
| 其他 release-level docs | `release` |
| `detailed-design` | `release`, `task_id` |
| `test-review-report`（v0.6 F7 新增）| `release`, `task_id`, `findings_count`, `severity_distribution`, `review_status`, `blocking_findings_count`, `max_severity` |
| `code-review-report` | `release`, `task_id`, `findings_count`, `severity_distribution`, `review_status`, `blocking_findings_count`, `max_severity` |
| `verification-result` | `release`, `task_id`, `verification_status` |
| `test-report` | `release`, `verification_status`, `total_test_cases`, `passed`, `failed` |
| `cr` | `cr_id`, `target_release`, `affected_doc` |
| `bug-report` | `bug_id`, `found_in_release`, `target_release`（可空，post-close 后由 release-start 自动填）, `root_cause`（可空，bug-triage 前 null）, `consumed_in_release`（可空）|
| `workflow-incident` | `incident_id`, `triggered_by_bug`, `triggered_in_release`, `resolution_action`（初始 null，由 incident-resolve 写入）|
| `source-system-analysis` | `release`（**字段必含**，值可为 null 仅当 analysis_kind=prd-level/feature-matrix）, `analysis_kind`, `source_system_name` |

完整列表见 `references/frontmatter-schema.md`。

## 5. validate.py 8 类校验

物理路径：`skills/doc-guardian/scripts/validate.py`

### 5.1 校验类别

| # | 类别 | 检查内容 |
|---|------|---------|
| 1 | **Path** | doc 文件路径符合 `type` 的目录规则；source-system-analysis 按 `analysis_kind` 分路径；workflow-incident 必须在 `docs/incident/` |
| 2 | **Naming** | 文件名符合 convention（lowercase + underscore + `.md`；ID 大写格式 `CR-NNN.md` / `BUG-NNN.md` / `INCIDENT-NNN.md`）|
| 3 | **Frontmatter Schema** | universal 6 字段全在 + per-type 扩展字段全在 + status/type/analysis_kind 等 enum 合法 |
| 4 | **Frontmatter Format** | timestamp ISO8601 UTC、release `"<x.y>"` MAJOR.MINOR 整数对、owner `agent/skill`、ID `CR-\d{3}`/`BUG-\d{3}`/`INCIDENT-\d{3}`（v0.6 round 3 L5：3 位 zero-padded）、code/test-review-report `review_status` ∈ {**pending**, pass, fail}（v0.6 round 3 H2 加 pending） |
| 5 | **Cross-Reference** | 路径字段（`affected_doc`、`parent_architecture` 等）指向真实存在的文件；**ID reference 字段**（`triggered_by_bug` 是 BUG-NNN ID，不是路径）按 `docs/bug/<value>.md` lookup 文件存在（v0.6 F12）|
| 6 | **Change Log Discipline** | `## Pending Changes` 章节为空（已 promote）+ `## Change Log` 章节 entry 符合格式 |
| 7 | **ID Uniqueness** | `docs/cr/` 下 CR-NNN 不重复；`docs/bug/` 下 BUG-NNN 不重复；`docs/incident/` 下 INCIDENT-NNN 不重复 |
| 8 | **Consistency with progress.md** | doc 的 `status` 字段和 progress.md 当前 `current_stage`/`sub_state` 兼容（如 progress.md current_stage=development 但 SRS 是 draft：异常）|

任一类失败 → exit 1 + stderr 列出具体失败项。

### 5.2 子命令

```bash
skills/doc-guardian/scripts/validate.py file <doc-path>      # 单文件 check（类 1-7）
skills/doc-guardian/scripts/validate.py all                   # 整个 docs/ 目录跑全部 check
skills/doc-guardian/scripts/validate.py consistency           # 仅 cross-file 类 8（重，按需调）
skills/doc-guardian/scripts/validate.py ids                   # 仅 ID 唯一性
```

`skills/workflow-protocol/scripts/progress.py update --advance` 内部对 stage 必备 artifacts 调 `skills/doc-guardian/scripts/validate.py file <each artifact>`（v0.6 F14 修正：之前误说 update 默认 validate 单个 changed-doc，实际是 advance 才执行 artifact 级 validate）。`*-write` skill 在自评步骤显式调 `validate.py file <doc>`。
`progress.py update --advance` 内部调 `validate.py file <each artifact>` 全部 + 可选 `validate.py consistency`。

### 5.3 失败处理

任何 validate 失败：

1. exit 非 0（exit code 1）
2. stderr 输出 `Category <N>: <description>` 格式的错误
3. caller AI 必须 (a) 读懂错误 (b) 修复触发原因 (c) 重新 invoke validate.py
4. **不允许绕过 validate.py 直接 declare doc done**

## 6. changelog.py — Change Log 自动化

物理路径：`skills/doc-guardian/scripts/changelog.py`

### 6.1 文档内的两个章节

任何"增量类"doc（PRD / Architecture / Retrospective / SRS / CR / Bug Report / dev plan 等）必含两个章节：

```markdown
---
[frontmatter]
---

# Document Title

## 1. ... (主体内容)
## 2. ...

## Pending Changes
- 2026-05-15T10:00:00Z [Section 3.2]: 新增用户认证需求
- 2026-05-15T10:30:00Z [Section 1.3]: 精简产品边界描述

## Change Log

### 2026-05-10
- 2026-05-10T08:00:00Z [Section 4.1]: 初始版本创建
```

### 6.2 Pending Changes 严格格式

每条 entry 必须符合：

```
- {ISO8601 UTC timestamp} [{section_ref}]: {one_line_summary}
```

- `timestamp`：ISO8601 UTC，精确到秒
- `section_ref`：受影响章节（"Section 3.2" 或 "全文" 或 "frontmatter"）
- `summary`：一句话变更描述

非此格式的 entry → `changelog.py promote` 拒绝（exit 1）。

### 6.3 子命令

```bash
skills/doc-guardian/scripts/changelog.py promote <doc-path>    # Pending → Change Log
skills/doc-guardian/scripts/changelog.py validate <doc-path>   # 仅校验 Pending 格式（不 mutation）
```

### 6.4 promote 行为

```
1. 读取目标 doc，找 ## Pending Changes 章节
2. 校验每条 entry 符合严格格式（不符合 → exit 1）
3. 按日期分组（同一天合并到 ### YYYY-MM-DD 块）
4. 插入 ## Change Log 章节顶部（最新日期在最上）
5. 清空 ## Pending Changes（保留章节标题，body 为空）
6. 写回文件（atomic：备份 + 写入 + 校验）
```

### 6.5 强制纪律

`validate.py` 类 6 (Change Log Discipline) 检查：

- `## Pending Changes` 章节必须为空（即 entries 全部已 promote）
- `## Change Log` 章节符合 `### YYYY-MM-DD` 分组 + entry 格式

不通过 → exit 1。

意味着 AI 编辑完 doc → 必须运行 `changelog.py promote` 移走 pending → 然后 `validate.py` 才会通过 → workflow-protocol 才允许 stage 推进。

### 6.6 `*-write` skill 标准 4 步流程

每个 `*-write` skill 处理增量类 doc 时遵循：

```
1. 生成/修改 doc 主体内容
2. 在 ## Pending Changes 章节加新 entry（按严格格式）
3. 运行 skills/doc-guardian/scripts/changelog.py promote <doc>
4. 自评（调 skills/doc-guardian/scripts/validate.py file <doc>）
5. 自修复
6. 提交给 *-review skill
```

第 3 步仅对增量类 doc 适用（一次性 doc 如 verification_result / test_report 不需要）。

### 6.7 status_transition.py — frontmatter status 自动化（Task 6 Gap-2）

物理路径：`skills/doc-guardian/scripts/status_transition.py`

**用途**：统一修改 doc frontmatter `status` 与 `updated`，并在增量类 doc 中通过 Pending Changes → Change Log 记录 frontmatter 状态变化。各 stage skill 不直接手工改 `status` 来绕过此 helper。

**MVP 子命令**：

```bash
skills/doc-guardian/scripts/status_transition.py plan \
  --event <write-complete|review-issues|review-passed|human-confirmed> \
  --doc <path> [--doc <path> ...]

skills/doc-guardian/scripts/status_transition.py apply \
  --event <write-complete|review-issues|review-passed|human-confirmed> \
  --doc <path> [--doc <path> ...]
```

`plan` 为 dry-run，不 mutation；`apply` 执行多 doc all-or-nothing mutation。Task-aware 调用通过显式传入 per-task doc 路径完成；未来可加 `--stage-current` / `--task Tn` 路径推导 shortcut，但 MVP 不依赖 shortcut。

**Event → status 映射**：

| Event | Allowed old status | New status | 适用 |
|-------|--------------------|------------|------|
| `write-complete` | `draft` / `revising` | `in-review` | 全部 doc |
| `review-issues` | `in-review` | `revising` | 全部 doc |
| `review-passed` | `in-review` | `review-passed` | 全部 doc |
| `human-confirmed` | `review-passed` | `approved` | 仅 `prd` / `srs` / `architecture` / `cr` |

**调用顺序**：

1. caller 写/修 doc，并按需运行 `skills/doc-guardian/scripts/changelog.py promote <doc>`。
2. caller 运行 `skills/doc-guardian/scripts/validate.py file <doc>`。
3. caller 运行 `skills/workflow-protocol/scripts/progress.py update --event <event>`。
4. progress event 成功后，caller 立即运行 `skills/doc-guardian/scripts/status_transition.py apply --event <event> --doc <doc> ...`。
5. caller rerun `validate.py file` 或 `validate.py consistency` 后再推进 stage。

**Change Log 原子性**：

- 增量类 doc：helper 更新 frontmatter `status` / `updated` 后，追加 `- <now> [frontmatter]: 更新 status 至 <new-status>` 到 `## Pending Changes`，随后在同一 transaction 内 promote 到 `## Change Log`。
- 一次性 doc：helper 只更新 frontmatter；不强制 Pending Changes / Change Log。
- 多 doc：先全部 dry-run 校验，再写入；任一失败必须 restore 所有已写 doc。
- 幂等重试：doc 已在目标 status 时 exit 0，不重复写 Change Log entry。

## 7. Required Artifacts (Scenario-Aware)

完整清单见 `references/required-artifacts.md`。本节仅列高频示例。

### 7.1 全场景必备（v0.6 round 4 M4 与 required-artifacts.md 对齐）

| Stage | 必备 artifacts |
|-------|---------------|
| Stage 1 | PRD（项目级单文件 `docs/prd/prd.md`）|
| Stage 2 | SRS + Acceptance Plan |
| Stage 3 | Architecture Document（项目级单文件）|
| Stage 4 stage 级 | Development Plan + Task Breakdown |
| Stage 4 **每个 task 无条件 4 个 per-task artifacts**（v0.6 round 4 M4 修正：删原 "复杂任务必有 Detailed Design" 的条件描述）| `detailed_design.md` + `test_review_report.md` + `code_review_report.md` + `verification_result.md` |
| Stage 5 | Test Preparation + Test Procedure + Test Report |
| Stage 6 | Deployment Doc + Operation Manual + Installation Result |
| Stage 7 | **Project Retrospective**（项目级单文件 `docs/retrospective/retrospective.md`）—— Issue Analysis + Improvement Proposals 等是该单文件**内部章节**（每 release 增量加节），**不是独立 doc**（v0.6 round 4 M4 澄清）|

### 7.2 条件必备

- Stage 2 **Integration Plan**：仅 `srs.is_multi_module == true` 时必备
- Stage 3 **Architecture Delta**：仅 `srs.architecture_change == true` 时必备
- 详细 condition DSL 见 `references/required-artifacts.md` §Condition DSL 规范

### 7.3 S3 强制（v0.6 修正：3 必备 + technical-debt 推荐）

S3 场景在 Stage 1/2 强制要求源系统分析 artifacts。完整 condition 见 `references/required-artifacts.md`。

- **Stage 1（2 必备）**:
  - `source-system-analysis` (analysis_kind=`prd-level`)
  - `source-system-analysis` (analysis_kind=`feature-matrix`)
- **Stage 2（3 必备 + 1 推荐）**:
  - `source-system-analysis` (analysis_kind=`srs-level`) — 必备
  - `source-system-analysis` (analysis_kind=`module-level`) — 必备
  - `source-system-analysis` (analysis_kind=`reuse-replace`) — 必备
  - `source-system-analysis` (analysis_kind=`technical-debt`) — **推荐，非必备**

`validate.py` 在 `update --advance` 时调用 `references/required-artifacts.md` 按当前 progress.md `scenario` 字段决定必备清单。

## 8. Forbidden Actions

- ❌ 跳过 `validate.py` 直接 declare doc done
- ❌ 直接编辑 `## Change Log` 章节（必须用 `changelog.py promote`）
- ❌ 手工改 doc frontmatter `status` 绕过 `skills/doc-guardian/scripts/status_transition.py`（Task 6 Gap-2 owner）
- ❌ 在 directory-layout 定义之外的目录创建 doc 文件
- ❌ 修改 `src/` 或 `tests/` 目录（这些不在 doc-guardian 管辖）
- ❌ frontmatter 字段名拼错（脚本严格匹配，不容忍变体）
- ❌ 在 release 字符串中省略引号（YAML 解析错；如 `release: 0.1` 会变 float 0.1）
- ❌ 在 review skill 输出中用 `approved`（必须用 `review-passed` / `issues-found`）

## 9. Recovery on Failure

`validate.py` fail 的 troubleshooting：

| 失败类别 | 修复路径 |
|---------|---------|
| Path | 把文件移到 `references/directory-layout.md` 规定的位置 |
| Naming | rename 文件符合 convention |
| Frontmatter Schema | 补缺字段 / 改 enum 值；查 `references/frontmatter-schema.md` |
| Frontmatter Format | 改 timestamp / release / owner / ID 格式 |
| Cross-Reference | 创建被引用的文件，或修改引用路径 |
| Change Log Discipline | 跑 `changelog.py promote` |
| ID Uniqueness | 重命名冲突 ID（注意更新跨文件引用）|
| Consistency with progress.md | 检查 doc `status` 是否与 progress.md `current_stage`/`sub_state` 一致 |
| status_transition.py apply 失败 | 先重试（幂等）；仍失败则按 stderr 修 doc status / Change Log，再重新运行 helper 与 validate |

## 10. References

- `references/directory-layout.md` — F1 全文：完整目录树 + 各 type 路径规则
- `references/frontmatter-schema.md` — F3 全文：universal + 各 type 字段表 + 模板
- `references/change-log-format.md` — Pending Changes 和 Change Log 严格格式 + 示例
- `references/required-artifacts.md` — P6 配套：每 stage required vs optional artifact 清单（scenario-aware）
- `docs/workflow/workflow_specification_claude.md`（项目级）— Workflow spec 定义
- `docs/design/skill_set_design_proposal_v0.5.md`（项目级）— 完整设计方案
