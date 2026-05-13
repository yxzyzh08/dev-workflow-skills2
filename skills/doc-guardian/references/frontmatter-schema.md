# Frontmatter Schema (Full)

本 reference 提供 doc-guardian 管辖的所有 doc 类型的 frontmatter schema。`validate.py` 的类 3-4 校验严格按本表。

---

## 1. Universal Fields (所有 doc 必含 6 字段)

```yaml
---
title: <string>                        # 人读标题
type: <doc-type-id>                    # enum，见 §3
status: draft | in-review | revising | review-passed | approved
created: <ISO8601 UTC>                 # 如 2026-05-15T10:00:00Z
updated: <ISO8601 UTC>
owner: <agent_id>/<skill_name>         # 如 claude-opus-4-7/srs-write
---
```

**字段约束**：

- `title`：任意 string，非空
- `type`：必为 §3 列出的 enum 之一
- `status`：必为 enum 之一
- `created` / `updated`：ISO8601 UTC，必精确到秒，必带 `Z` 后缀（不接受 `+00:00`）
- `owner`：必含 `/`，前后段非空

## 2. Status 状态机

```
draft → in-review → review-passed (非 gated 终态)
                  → approved (仅 gated; 经人 confirm)
        ↓
        revising → in-review (write Change Mode 完成后回评审)
```

| 状态 | 适用 doc 类型 |
|------|---------------|
| `draft` / `in-review` / `revising` | 全部 doc |
| `review-passed` | 全部 doc（非 gated 此为最终态）|
| `approved` | **仅** PRD / SRS / Architecture / CR（4 种 human-gated）|

非 gated doc（如 dev plan、test report 等）永远不会到 `approved`。

## 3. Doc Type Enum 与 Per-Type Extensions

按粒度分类。

### 3.1 项目级（不绑定 release）

#### `prd`

```yaml
type: prd
# 路径：docs/prd/prd.md
# 无额外 universal 之外的字段
```

#### `architecture`

```yaml
type: architecture
# 路径：docs/architecture/architecture.md
# 无额外字段
```

#### `retrospective`

```yaml
type: retrospective
# 路径：docs/retrospective/retrospective.md
# 无额外字段
```

### 3.2 Release 级（绑定 release）

#### `srs`

```yaml
type: srs
release: "<MAJOR.MINOR>"
is_multi_module: true | false              # 必含（v0.6 round 2 H1 新加）；决定 Integration Plan 是否必备
architecture_change: true | false          # 必含（v0.6 round 2 H1 新加）；决定 architecture-delta 是否必备
# 路径：docs/release<x.y>/srs/srs.md
# 由 srs-write skill 在 SRS specification 阶段写入两个 bool 字段
# required-artifacts.md condition DSL 通过这两个字段决定 Integration Plan / Architecture Delta 必备性
```

#### `acceptance-plan`

```yaml
type: acceptance-plan
release: "<x.y>"
related_srs: <path>                   # 必含；指向同 release 的 srs.md
# 路径：docs/release<x.y>/srs/acceptance_plan.md
```

#### `integration-plan`

```yaml
type: integration-plan
release: "<x.y>"
# 路径：docs/release<x.y>/srs/integration_plan.md
# 仅多模块项目需要
```

#### `architecture-delta`

```yaml
type: architecture-delta
release: "<x.y>"
parent_architecture: docs/architecture/architecture.md   # 固定指向项目级架构
# 路径：docs/release<x.y>/architecture_delta.md
# 仅本 release 引入架构变更时存在
```

#### `development-plan`

```yaml
type: development-plan
release: "<x.y>"
# 路径：docs/release<x.y>/development/plan.md
```

#### `task-breakdown`

```yaml
type: task-breakdown
release: "<x.y>"
total_tasks: <int>                    # 必含
# 路径：docs/release<x.y>/development/breakdown.md
# Body 必含：以 whole-word `Tn` token 列出每个 task 的标识（如
# `## Tasks\n- T1: ...\n- T2: ...`）。`progress.py update --task Tn` 会
# 用 `\bTn\b` 正则在 body 中查找 task；缺失时 reject "breakdown.md does
# not declare Tn"（progress_artifacts.load_breakdown_with_tasks）。
# 注意：`total_tasks` 与 body 中的 `Tn` 数量是否一致，当前由
# `validate.py consistency` Class 8 / Phase 7+ hardening 留作 deferred；
# Stage 4 task 转换只检查 task ID 在 body 中存在。
```

#### `test-preparation`

```yaml
type: test-preparation
release: "<x.y>"
# 路径：docs/release<x.y>/testing/preparation.md
```

#### `test-procedure`

```yaml
type: test-procedure
release: "<x.y>"
# 路径：docs/release<x.y>/testing/procedure.md
```

#### `test-report`

```yaml
type: test-report
release: "<x.y>"
verification_status: pass | fail | partial    # 必含
total_test_cases: <int>                       # 必含
passed: <int>                                 # 必含
failed: <int>                                 # 必含
# 路径：docs/release<x.y>/testing/report.md
# 约束：total_test_cases == passed + failed + skipped (若有)
```

#### `deployment-doc`

```yaml
type: deployment-doc
release: "<x.y>"
# 路径：docs/release<x.y>/delivery/deployment.md
```

#### `operation-manual`

```yaml
type: operation-manual
release: "<x.y>"
# 路径：docs/release<x.y>/delivery/operation_manual.md
```

#### `installation-result`

```yaml
type: installation-result
release: "<x.y>"
verification_status: pass | fail | partial    # 必含
# 路径：docs/release<x.y>/delivery/installation_result.md
```

### 3.3 Per-Task（绑定 release + task）

#### `detailed-design`

```yaml
type: detailed-design
release: "<x.y>"
task_id: T<n>                         # 大写 T + 数字（如 T1, T15）
# 路径：docs/release<x.y>/development/tasks/T<n>/detailed_design.md
```

#### `code-review-report`

```yaml
type: code-review-report
release: "<x.y>"
task_id: T<n>
findings_count: <int>                            # 必含；总 finding 数
severity_distribution:                           # 必含；含 4 个键（即使为 0）
  critical: <int>
  high: <int>
  medium: <int>
  low: <int>
review_status: pending | pass | fail             # 必含（v0.6 round 3 H2：加 pending；skeleton 用 pending 防 bypass）
blocking_findings_count: <int>                   # 必含；critical + high 数量
max_severity: low | medium | high | critical     # 必含
# 路径：docs/release<x.y>/development/tasks/T<n>/code_review_report.md
# 三态约束（v0.6 round 4 H1 重写）：
#   - skeleton（development-code-write 创建）：
#       review_status: pending；counts 全 0；blocking_findings_count: 0；max_severity: low
#       doc 自身 status: draft
#   - 完成 pass（development-code-review 填）：
#       review_status: pass；blocking_findings_count: 0（强制）；max_severity 与 severity_distribution 一致
#       doc 自身 status: review-passed
#   - 完成 fail（development-code-review 填）：
#       review_status: fail；blocking_findings_count: ≥ 0（可有非 blocking findings）
#       doc 自身 status: in-review 或 revising
# **三态不变量**（v0.6 round 4 H1 替换原 "pass iff blocking=0" 全局规则）：
#   - 仅当 review_status ∈ {pass, fail} 时校验 blocking_findings_count 与 review_status 关系：
#       review_status == pass ⇒ blocking_findings_count == 0
#       review_status == fail ⇒ blocking_findings_count 可任意
#   - review_status == pending 时**豁免** blocking 关系校验（skeleton 阶段允许 0）
# Stage 4 task `code-review-passed` 转移严格要求 review_status: pass（pending/fail 都 reject）
```

#### `test-review-report`（v0.6 F7 新增；与 code-review-report 完全对称）

```yaml
type: test-review-report
release: "<x.y>"
task_id: T<n>
findings_count: <int>
severity_distribution:
  critical: <int>
  high: <int>
  medium: <int>
  low: <int>
review_status: pending | pass | fail             # v0.6 round 3 H2：加 pending；skeleton 用 pending
blocking_findings_count: <int>
max_severity: low | medium | high | critical
# 路径：docs/release<x.y>/development/tasks/T<n>/test_review_report.md
# 约束同 code-review-report；Stage 4 task `test-done` 转移要求 review_status: pass
```

**生命周期 owner（v0.6 round 3 H2 修正：skeleton 用 pending 防 bypass）**：

| 阶段 | 责任 skill | 写入字段 |
|------|-----------|---------|
| skeleton 创建 | `development-test-write` | universal 字段（`status: draft`、`title`、`type`、`task_id`、`release`、`owner`）+ counts 全 0 + **`review_status: pending`**（**不是 pass**——避免 review skill 被绕过）+ `max_severity: low` + `blocking_findings_count: 0` |
| findings 填充 | `development-test-review` | 重写 `findings_count` / `severity_distribution` / `blocking_findings_count` / `max_severity` / `review_status: pass\|fail`；改 doc `status: review-passed`（review_status=pass 时）或维持 `in-review` 触发循环 |

**关键约束**：Stage 4 task `test-done` 转移由 `progress.py update --task` 严格校验：
- `test-review-report` 必存在
- `review_status == "pass"`（pending 和 fail 都 reject）
- `blocking_findings_count == 0`

skeleton 的 `pending` 状态确保了：在 `development-test-review` skill 真正写入 review 结果前，task 不可能转 `test-done`。code-review-report 同理。

测试代码 quality 评审最低维度（待 `development-test-review/SKILL.md` 在 batch 3 完整定义；本文件仅声明）：覆盖率 / 边界条件 / mock 合理性 / fixture 隔离 / 重复或脆弱断言。

`code-review-report` 的 owner 模式相同（`development-code-write` 创 skeleton，`development-code-review` 填）；下方不再重述。

#### `verification-result`

```yaml
type: verification-result
release: "<x.y>"
task_id: T<n>
verification_status: pass | fail | partial       # 必含
# 路径：docs/release<x.y>/development/tasks/T<n>/verification_result.md
```

### 3.4 跨 Release（带 ID）

#### `cr`

```yaml
type: cr
cr_id: CR-<NNN>                                  # 必含；规律 CR-001/CR-042/...
target_release: "<x.y>"                          # 必含
affected_doc: <path>                             # 必含；一般指向 SRS
# 路径：docs/cr/CR-<NNN>.md
```

#### `bug-report`

```yaml
type: bug-report
bug_id: BUG-<NNN>                                # 必含
found_in_release: "<x.y>"                        # 必含
target_release: "<x.y>" | null                   # 可空（post-close intake 时 null，下次 release-start 后填值）
root_cause: srs | architecture | development | prd-exception | null   # 可空（bug-triage 前 null）
consumed_in_release: "<x.y>" | null              # 可空（仅 post-close intake 后由 release-start 自动填）
# 路径：docs/bug/BUG-<NNN>.md
```

#### `workflow-incident`

```yaml
type: workflow-incident
incident_id: INCIDENT-<NNN>                                          # 必含
triggered_by_bug: BUG-<NNN>                                          # 必含；**ID 字段（不是路径）**，validate.py 按 docs/bug/<value>.md 模式 lookup
triggered_in_release: "<x.y>"                                        # 必含
resolution_action: continue | abort | reconstruct | null             # 字段必含，值初始 null（v0.6 F6 强调）
# 路径：docs/incident/INCIDENT-<NNN>.md
# v0.6 F12 澄清：triggered_by_bug 是 BUG ID（如 "BUG-007"），不是 path（如 "docs/bug/BUG-007.md"）
# validate.py 类 5 ID reference lookup：用 ID 渲染路径 docs/bug/<value>.md 后校验文件存在
```

### 3.5 附属 / 分析

#### `source-system-analysis`

```yaml
type: source-system-analysis
release: "<x.y>" | null                                              # null 仅 PRD-level
analysis_kind: prd-level | feature-matrix | srs-level | module-level | reuse-replace | technical-debt
source_system_name: <string>                                         # 必含
# 路径见 §3.5.1 表
```

##### 3.5.1 `analysis_kind` 与路径

| `analysis_kind` | 路径 | release 字段 | S3 必备 |
|-----------------|------|-------------|---------|
| `prd-level` | `docs/prd/supporting/source_product_prd_analysis.md` | null | Stage 1 必备 |
| `feature-matrix` | `docs/prd/supporting/feature_matrix.md` | null | Stage 1 必备 |
| `srs-level` | `docs/release<x.y>/srs/source_product_srs_analysis.md` | `"<x.y>"` | Stage 2 必备 |
| `module-level` | `docs/release<x.y>/srs/source_module_analysis.md` | `"<x.y>"` | Stage 2 必备 |
| `reuse-replace` | `docs/release<x.y>/srs/reuse_replace_capability.md` | `"<x.y>"` | Stage 2 必备 |
| `technical-debt` | `docs/release<x.y>/srs/technical_debt_analysis.md` | `"<x.y>"` | **Stage 2 推荐（v0.6 F5：非必备）** |

#### PRD Supporting Artifacts（非 source-system-analysis）

```yaml
type: competitor-research | competitor-architecture | market-research | user-scenario-analysis | non-goals | risk-analysis
# 路径：docs/prd/supporting/<descriptive_name>.md
# 全部为 PRD 附属文档，按需创建
```

## 4. 字段格式约束（validate.py 类 4 校验）

### 4.1 Timestamp

- 格式：`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`
- 例：`2026-05-15T10:00:00Z`
- 不接受 `+00:00` 后缀（必须用 `Z`）
- 不接受省略秒数

### 4.2 Release

- 格式：YAML string，必须加引号 `release: "0.1"`（不带引号 YAML 会解析为 float `0.1`，validate.py reject）
- 内容 regex：`^(\d+)\.(\d+)$`
- 不允许：patch 版本（`0.1.1`）、pre-release（`0.1-alpha`）、build metadata（`0.1+abc`）

### 4.3 Owner

- 格式：`<agent_id>/<skill_name>`
- 必含一个 `/`
- 前后段非空
- 例：`claude-opus-4-7/srs-write`

### 4.4 ID（v0.6 round 2 M8：强制 3 位 zero-padded）

| Field | 格式 |
|-------|------|
| `cr_id` | `^CR-\d{3}$`（如 `CR-001`、`CR-042`、`CR-100`；**强制 3 位 zero-padded**）|
| `bug_id` | `^BUG-\d{3}$` |
| `incident_id` | `^INCIDENT-\d{3}$` |
| `task_id` | `^T\d+$`（如 `T1`、`T15`；不强制 zero-pad，因 task 数量可控）|

**v0.6 round 3 L5 澄清**：当前 validate.py **只接受 3 位**。若未来 ID 数量超过 999，必须先经 review cycle 升级 regex（改为 `\d{3,}`）和 directory-layout policy；在那之前 `BUG-1000` 等 4 位 ID 一律 reject。不允许以"未来扩展"为由当前接受 4 位 ID。

### 4.5 Path References（v0.6 round 2 M8：移除 triggered_by_bug）

字段类型为路径的（`affected_doc`、`parent_architecture`、`related_srs`），必须满足：

- 相对项目根的 forward slash 路径
- 文件实际存在（validate.py 类 5 校验）

### 4.6 ID References（v0.6 round 2 M8 新增；区别于 Path References）

字段类型为 ID 的（`triggered_by_bug` 是 BUG ID，不是 path），validate.py 类 5 用 ID lookup 模式校验：

| ID Field | 渲染规则 | 校验文件存在 |
|----------|---------|--------------|
| `triggered_by_bug` | `docs/bug/{value}.md`（如 value=`BUG-007`，渲染为 `docs/bug/BUG-007.md`） | ✓ |

**v0.6 round 2 强调**：`triggered_by_bug` 不是 path 字段；不要写 `docs/bug/BUG-007.md` 作为字段值。

## 5. Per-Type 字段必含表（v0.6 F6 与详细 schema 完全对齐）

**注**：本表是 cheat sheet，必含字段与 §3 详细 schema **必须一致**。`validate.py` 类 3 严格按详细 schema 校验，本表仅为快速查阅。

| Type | universal | 必含扩展字段 |
|------|-----------|--------------|
| `prd` / `architecture` / `retrospective` | ✓ | — |
| `srs`（v0.6 round 2/3 加 2 bool）| ✓ | `release`, **`is_multi_module: bool`**, **`architecture_change: bool`**（条件 DSL 关键依赖；必须存在且 YAML bool 类型合法）|
| 其他 release-level docs（acceptance-plan / dev plan 等）| ✓ | `release` |
| `acceptance-plan` | ✓ | `release`, `related_srs` |
| `architecture-delta` | ✓ | `release`, `parent_architecture` |
| `task-breakdown` | ✓ | `release`, `total_tasks` |
| `detailed-design` | ✓ | `release`, `task_id` |
| `test-review-report`（v0.6 F7）| ✓ | `release`, `task_id`, `findings_count`, `severity_distribution`, `review_status`, `blocking_findings_count`, `max_severity` |
| `code-review-report` | ✓ | `release`, `task_id`, `findings_count`, `severity_distribution`, `review_status`, `blocking_findings_count`, `max_severity` |
| `verification-result` | ✓ | `release`, `task_id`, `verification_status` |
| `test-report` | ✓ | `release`, `verification_status`, `total_test_cases`, `passed`, `failed` |
| `installation-result` | ✓ | `release`, `verification_status` |
| `cr` | ✓ | `cr_id`, `target_release`, `affected_doc` |
| `bug-report`（v0.6 F6 修正：必含全部 5 字段）| ✓ | `bug_id`, `found_in_release`, `target_release`（值可为 null）, `root_cause`（值可为 null）, `consumed_in_release`（值可为 null）|
| `workflow-incident`（v0.6 F6 修正：必含 `resolution_action`）| ✓ | `incident_id`, `triggered_by_bug`, `triggered_in_release`, `resolution_action`（初始 null）|
| `source-system-analysis`（v0.6 F6 修正：`release` 字段必含）| ✓ | `release`（**字段必须存在**，值按 analysis_kind 可为 null 或 `<x.y>`）, `analysis_kind`, `source_system_name` |

**关键澄清**：
- "值可为 null" ≠ "字段可省略"。`validate.py` 类 3 要求**字段必须存在于 frontmatter 中**；只是允许其值为 YAML `null`。这样 schema 演化时不会因字段缺失而误通过。
- `bug-report.target_release`：post-close intake 时为 null，`release-start` 自动设为新 release（同时设 `consumed_in_release` 一致值）。
- `bug-report.consumed_in_release`：仅在 BUG 经历过 post-close intake 才有值；active release 内修复的 bug 此字段保持 null。

## 6. 示例 Frontmatter（5 个典型）

### 6.1 PRD（最简）

```yaml
---
title: MyApp Product Requirements
type: prd
status: approved
created: 2026-05-04T08:00:00Z
updated: 2026-05-15T10:00:00Z
owner: claude-opus-4-7/prd-write
---
```

### 6.2 SRS（v0.6 round 4 L5：示例补 2 bool 字段）

```yaml
---
title: MyApp v0.1 SRS
type: srs
status: in-review
created: 2026-05-05T09:00:00Z
updated: 2026-05-06T14:30:00Z
owner: claude-opus-4-7/srs-write
release: "0.1"
is_multi_module: false                       # 必含；srs-write 决定；required-artifacts.md DSL 用此字段判定 Integration Plan 必备性
architecture_change: false                   # 必含；srs-write 决定；DSL 用此判定 Architecture Delta 必备性
---
```

### 6.3 Code Review Report

```yaml
---
title: T2 Code Review Report
type: code-review-report
status: review-passed
created: 2026-05-08T11:00:00Z
updated: 2026-05-08T11:00:00Z
owner: claude-opus-4-7/development-code-review
release: "0.1"
task_id: T2
findings_count: 3
severity_distribution:
  critical: 0
  high: 0
  medium: 2
  low: 1
review_status: pass
blocking_findings_count: 0
max_severity: medium
---
```

### 6.4 CR

```yaml
---
title: CR-001 Add user 2FA
type: cr
status: approved
created: 2026-05-12T10:00:00Z
updated: 2026-05-12T15:00:00Z
owner: claude-opus-4-7/srs-write
cr_id: CR-001
target_release: "0.2"
affected_doc: docs/release0.2/srs/srs.md
---
```

### 6.5 Source System Analysis (S3 必备)

```yaml
---
title: Source Product PRD Analysis (LegacyApp)
type: source-system-analysis
status: review-passed
created: 2026-05-04T10:00:00Z
updated: 2026-05-04T16:00:00Z
owner: claude-opus-4-7/prd-write
release: null
analysis_kind: prd-level
source_system_name: LegacyApp
---
```

## 7. validate.py 校验逻辑（伪码）

```python
def validate_frontmatter(doc_path: str) -> ValidateResult:
    fm = parse_yaml_frontmatter(doc_path)

    # Class 3: Schema
    require_universal_fields(fm)        # title/type/status/created/updated/owner
    require_per_type_fields(fm)         # 按 type 查表
    require_enum_legal(fm)              # status/type/analysis_kind/...

    # Class 4: Format
    validate_timestamp(fm['created'], fm['updated'])
    validate_release_format(fm.get('release'))
    validate_owner_format(fm['owner'])
    validate_id_format(fm)              # CR-NNN/BUG-NNN/INCIDENT-NNN/Tn

    # Class 5: Cross-reference
    validate_path_references(fm)        # affected_doc/parent_architecture/...

    # Class 1: Path
    validate_path_matches_type(doc_path, fm['type'], fm.get('release'),
                                fm.get('task_id'), fm.get('analysis_kind'))

    # Class 2: Naming
    validate_filename_convention(doc_path)

    return ok_or_fail
```

## 8. 关键不变量

任何时候，以下不变量必须成立：

- 任何 doc 的 `type` 字段决定其 path（不能 type=srs 但放 docs/prd/）
- 任何 release-level doc 的 `release` 字段必须等于 progress.md 当前 `release` 字段
- 任何 per-task doc 的 `task_id` 必须在 progress.md `development_state.task_states` 中存在
- `code-review-report` / `test-review-report` 的三态规则（v0.6 round 4 H1 重写）：
  - `review_status == pending` → blocking_findings_count 可为 0（skeleton 状态豁免）
  - `review_status == pass` → blocking_findings_count **必须为 0**
  - `review_status == fail` → blocking_findings_count 可任意（≥ 0）
- `test-report` 的 `total_test_cases == passed + failed + skipped`（skipped 字段可选）
- ID 类 doc（CR/Bug/Incident）的 ID 在其类目录下唯一
- gated doc（PRD/SRS/Architecture/CR）的 `status: approved` ↔ progress-history.md 有对应 `human-confirmed` 条目
