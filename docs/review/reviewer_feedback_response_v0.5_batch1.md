# Reviewer Feedback Response — Batch 1 SKILL.md Review

**Source Review**: `docs/review/skill_set_batch1_review.md`
**Adopted In**: `skills/workflow-protocol/*` + `skills/doc-guardian/*` (修订到位)
**Date**: 2026-05-06
**Reviewed By**: User + Claude
**Review Cycle**: Task 5 Batch 1 第一轮

---

## Findings 处置一览（16 项）

### High（8 项）

| # | Finding | 处置 | 关键设计决策 |
|---|---------|------|--------------|
| F1 | 3 reference 文件缺失（directory-layout / change-log-format / required-artifacts） | **创建** | 全部补齐，required-artifacts.md 同时承担 F4 的 "artifact 来源 map" 职责 |
| F2 | PRD exception 路径不可达 | **改 incident-start 前置** | 移除 `bug_flow.active==true` 要求；改为 `incident-start --bug <BUG-id> --report <INCIDENT-path>` 自身设置 `bug_flow.root_cause: prd-exception` 后再走 incident state；bug-triage 创建 INCIDENT skeleton，workflow-evolution 填充内容 |
| F3 | `incident-resolve --action continue` mutation 不确定 | **加 `--bug-flow keep\|clear` 参数** | 默认 `clear`（最简）；`keep` 显式要求继续修原 bug |
| F4 | `--advance` artifact 来源不明 | **方案 B：required-artifacts.md 作 map** | progress.md `artifacts:` 仅存可变 stage 1-3 路径；其他 stage artifacts 由 doc-guardian 的 required-artifacts.md 按 release/stage/task 推导标准路径 |
| F5 | S3 必备清单 4 vs 3+1 冲突 | **统一为 3 必备 + technical-debt 推荐** | 与 design v0.5 §5.3 一致；同步改 workflow spec §4.9 Stage 2 row、design §4.9、SKILL.md 全部 |
| F6 | 必含表与详细 schema 自相矛盾 | **改 cheat sheet 对齐详细 schema** | bug-report 必含 `bug_id, found_in_release, target_release, root_cause, consumed_in_release`；workflow-incident 必含全部 4 字段；source-system-analysis `release` 字段必须存在（值可为 null） |
| F7 | Stage 4 tests 缺 per-task doc type | **新增 `test-review-report`** | 与 code-review-report 对称；路径 `docs/release<x.y>/development/tasks/Tn/test_review_report.md`；frontmatter 含 `review_status: pass\|fail` + `blocking_findings_count` + `max_severity` |
| F8 | `update --field` 过宽允许 bypass | **替换为命名事件 `--event`** | 白名单 `write-complete\|review-issues\|review-passed\|human-confirmed\|task-status` 等；受保护字段（release_state/current_stage/bug_flow/workflow_incident_active/project_state）必须经 dedicated subcommand；Forbidden 加防 bypass 条目 |

### Medium（5 项）

| # | Finding | 处置 | 关键决策 |
|---|---------|------|---------|
| F9 | Integration Plan 条件矛盾 | P6 row 改 "(when multi-module)" | 由 srs-write skill 在 SRS frontmatter 写 `is_multi_module: true\|false` 决定；required-artifacts.md 据此条件化 |
| F10 | release-start consume bugs 语义不明 | 同时设 `target_release` 和 `consumed_in_release` | 都设为新 release 版本；`bug-intake` 前置加 "未在 unresolved_bugs 中、`consumed_in_release == null`" |
| F11 | terminal state 脏字段 | 允许 `sub_state: null` 并清空 bug_flow | abort/reconstruct mutation 加：`sub_state: null`、`review_iteration: 0`、`bug_flow.{active,bug_report_path,root_cause}: false/null/null` |
| F12 | `triggered_by_bug` ID vs path 不明 | 保持 ID 格式 + 加 ID reference lookup | validate.py 类 5 增加规则：`triggered_by_bug` 是 ID 字段，映射到 `docs/bug/<value>.md` 并校验文件存在 |
| F13 | shorthand 残留 | normalize 全文 | 全部 invocation 改 `skills/<name>/scripts/<x>.py` 全路径 |

### Low（3 项）

| # | Finding | 处置 |
|---|---------|------|
| F14 | `update` 默认 validates changed-doc 但缺 `--doc` | 删除"默认"说法；`update` 只做状态机校验；`--advance` 才执行 artifact 级 validate |
| F15 | universal "5 字段" 笔误 | 改为 "6 字段"（含 owner）|
| F16 | doc-guardian SKILL.md changelog 内联过多 | 现暂保留；待 `change-log-format.md` 创建并稳定后再考虑精简（不阻塞）|

## 关键决策详解

### F2 PRD exception 路径修复

**问题**：v0.5 流程 `bug-start` 拒绝 prd-exception，`incident-start` 又要求 prd-exception 已设。无命令能引发该状态。

**修复后流程**：

```
1. testing-write 发现 bug → 创建 BUG-NNN.md
2. invoke bug-triage active mode
3. bug-triage 判断 root_cause:
   ├ ∈ {srs, architecture, development} → 调 progress.py bug-start
   └ == prd-exception:
       a. bug-triage 在 BUG-NNN.md frontmatter 写 root_cause: prd-exception
       b. bug-triage 创建 INCIDENT-NNN.md skeleton（仅 frontmatter，待 workflow-evolution 填内容）
       c. bug-triage 调 progress.py incident-start --bug BUG-NNN --report docs/incident/INCIDENT-NNN.md
       d. progress.py 校验 BUG-NNN.md frontmatter root_cause==prd-exception，校验通过则进入 incident state
```

**incident-start 新前置**：

- `<bug-path>` 文件存在且 frontmatter `root_cause == prd-exception`
- `<incident-path>` 文件存在（skeleton）且为合法 `workflow-incident` 类型

**incident-start mutation**（更新）：

```yaml
bug_flow.active: false → true   # incident-start 同时启动 bug_flow
bug_flow.bug_report_path: null → <bug-path>
bug_flow.root_cause: null → prd-exception
workflow_incident_active: false → true
incident_report_path: null → <incident-path>
current_stage: <previous, usually testing> → workflow-incident-analysis
```

不再依赖 bug-start，整条 PRD exception 路径自闭。

### F4 artifact 来源决策（方案 B）

`progress.md artifacts:` 仅存"项目级或 release 级 mutable 入口路径"：PRD / Architecture / SRS / Acceptance Plan / Integration Plan? / Architecture Delta?。

`update --advance` 时 workflow-protocol 调 doc-guardian 的 required-artifacts.md（YAML map）按当前 `(scenario, scenario_subtype, current_stage, release, task_id?, is_multi_module?)` 推导该 stage 应有的全部 artifact 路径列表，对每个路径调 validate.py file。

required-artifacts.md 是声明式的：

```yaml
# 例：Stage 5 Testing
testing:
  required:
    - path_template: "docs/release{release}/testing/preparation.md"
      type: test-preparation
    - path_template: "docs/release{release}/testing/procedure.md"
      type: test-procedure
    - path_template: "docs/release{release}/testing/report.md"
      type: test-report
  conditions: []   # 无条件必备
```

scenario-aware（如 S3 Stage 1 含 source-system-analysis）由 `conditions` 表达。

### F8 `--event` 命名事件白名单

替换 `update --field <name> --value <value>` 为 `update --event <event-name> [--params ...]`：

| Event | 触发时机 | 影响字段 |
|-------|---------|---------|
| `write-complete` | `*-write` 完成 draft + self-validate pass | `sub_state: write → in-review` |
| `review-issues` | `*-review` 输出 issues-found | `sub_state: in-review → revising`，`review_iteration += 1` |
| `review-passed` | `*-review` 输出 review-passed | `sub_state: → review-passed`，`review_iteration → 0` |
| `human-confirmed` | 人 gate 通过 | `sub_state: review-passed → approved`（仅 PRD/SRS/Architecture/CR）|
| `task-status` | Stage 4 task 状态变化 | `development_state.task_states[Tn]: → <new>` |

受保护字段（`release_state`、`release`、`current_stage`、`bug_flow.*`、`workflow_incident_active`、`incident_report_path`、`project_state`、`previous_releases`、`unresolved_bugs`）**绝不可通过 `update --event` 修改**，必须经 dedicated subcommand（`release-close` / `release-start` / `bug-start` / `bug-close` / `bug-intake` / `incident-start` / `incident-resolve`）。

`update --advance` 是另一个独立子命令（不属于 event）。

### F7 `test-review-report` 新 doc type

与 `code-review-report` 完全对称：

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
review_status: pass | fail
blocking_findings_count: <int>
max_severity: low | medium | high | critical
# 路径：docs/release<x.y>/development/tasks/T<n>/test_review_report.md
# 约束同 code-review-report
```

Stage 4 task state 转移：

- `test-writing` → `test-review`：development-test-write 完成测试代码 + 写 test-review-report skeleton
- `test-review` → `test-revising`：development-test-review skill 输出 issues
- `test-review` → `test-done`：test-review-report 满足 `review_status: pass` AND `blocking_findings_count: 0`

## 影响的物理文件清单

| 文件 | 类型 | 主要修改 |
|------|------|---------|
| `docs/workflow/workflow_specification_claude.md` | 修改 | F5 (S3 4→3+1)；bump v0.5→v0.6 |
| `skills/workflow-protocol/SKILL.md` | 修改 | F2/F3/F4/F7/F8/F9/F11/F13/F14 多处 |
| `skills/workflow-protocol/references/command-reference.md` | 修改 | F2/F3/F4/F8/F10/F11/F13/F14 多处 |
| `skills/doc-guardian/SKILL.md` | 修改 | F5/F6/F7/F12/F13/F15/F16 多处 |
| `skills/doc-guardian/references/frontmatter-schema.md` | 修改 | F5/F6/F7/F12/F15 多处 |
| `skills/doc-guardian/references/directory-layout.md` | **新增** | F1 |
| `skills/doc-guardian/references/required-artifacts.md` | **新增** | F1 + F4 |
| `skills/doc-guardian/references/change-log-format.md` | **新增** | F1 |

## 没有采纳/弱采纳的项

无强反驳。F16 仅延迟（不阻塞），其他 15 项全部直接采纳。

## 评审循环统计

| 版本 | Finding 总数 | High | Medium | Low |
|------|-------------|------|--------|-----|
| v0.1 评审 | 9 | 5 | 4 | 0 |
| v0.2 评审 | 8 | 5 | 3 | 0 |
| v0.3 评审 | 6 | 3 | 2 | 1 |
| v0.4 评审 | 4 | 0 | 2 | 2 |
| **batch 1 评审** | **16** | **8** | **5** | **3** |

batch 1 评审 finding 反弹是预期内：SKILL.md 是契约层，比 design proposal 多两个数量级的可实现性细节。这一轮修完后契约才真正闭环。
