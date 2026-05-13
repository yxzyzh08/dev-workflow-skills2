# Reviewer Feedback Response — Proposal v0.3

**Source Review**: `docs/review/skill_set_design_proposal_v0.3_rereview.md`
**Adopted In**: `docs/design/skill_set_design_proposal_v0.4.md`
**Workflow Spec Update**: `docs/workflow/workflow_specification_claude.md` (v0.3 → v0.4)
**Date**: 2026-05-05
**Reviewed By**: User + Claude

---

## Findings 处置一览

| # | Severity | Finding 摘要 | 处置 | 备注 |
|---|----------|---------------|------|------|
| F1 | High | workflow spec S4 描述与 v0.3 active-only policy 不一致 | **采纳** | 改 spec 4 处：§2 表、§6 引言、§9.4 段、Change Log 加 v0.4 entry |
| F2 | High | post-close bug intake 无 owner / state transition | **采纳** | bug-triage skill 双模式（active + post-close） + `progress.py bug-intake --bug <path>` |
| F3 | High | PRD 根因异常无法在 state 表达 | **采纳** | 扩 `bug_flow.root_cause` enum 加 `prd-exception`；progress.md 加 `workflow_incident_active`、`incident_report_path` |
| F4 | Medium | release-close/start mutation 不完整 | **采纳** | 详细规定每个 subcommand 的字段变更 |
| F5 | Medium | release version 比较不明确 | **采纳** | 限定 `MAJOR.MINOR` integer pair；progress.py 按整数对解析 |
| F6 | Low | script 路径仍有 shorthand | **采纳** | normalize 残留 |

6 项全采纳，无反驳。

## 关键设计选择（claude 拍板，用户可 override）

### F2 设计选择：bug-triage 双模式 + 新 progress.py 子命令

**Bug 报告产生路径**：

| 场景 | Owner | 流程 |
|------|-------|------|
| Active release + Stage 5 测试发现 bug | testing-write 写 bug 报告 + 触发 bug-triage active mode | bug-triage 分类根因 → workflow-protocol 切 stage Change Mode |
| Active release + 用户手动报告 bug | bug-triage active mode | 同上 |
| Closed release + 用户手动报告 bug | bug-triage post-close mode | 仅创建 BUG-NNN.md（target_release=null）+ 调 `progress.py bug-intake` 追加 unresolved_bugs；不路由 stage |

新命令：`skills/workflow-protocol/scripts/progress.py bug-intake --bug docs/bug/BUG-NNN.md`：

- 校验：当前 release_state 必须是 closed（active release 应走 active mode 流程）
- 校验：bug 文件存在 + frontmatter `target_release: null`
- 动作：原子追加到 `unresolved_bugs` + append 一条 history 条目

下一次 release-start 时，progress.py 把 `unresolved_bugs` 里的每个 bug 标记 `consumed_in_release: <new_version>` 并清空列表（详见 F4）。

### F3 设计选择：root_cause 加 prd-exception + 加 workflow_incident_active

**bug_flow.root_cause** enum 扩为 5 值：`null | srs | architecture | development | prd-exception`

当 bug-triage 判定 `prd-exception`：

- workflow-protocol 不切 current_stage 到 PRD Change Mode
- 改为：设 `workflow_incident_active: true`、`incident_report_path: <path>`、`current_stage: workflow-incident-analysis`（特殊伪 stage）
- workflow-evolution skill 接管，产出 Workflow Incident Report
- 用户决策（继续修订 workflow / 重启 project / 转 S3 重构）后，由用户手动调 progress.py 切回正常路径或终止 project

progress.md 新增字段：

```yaml
workflow_incident_active: false
incident_report_path: null   # 仅在 active=true 时有值
```

### F5 设计选择：MAJOR.MINOR integer pair

**Release version 语法**：

- `<MAJOR>.<MINOR>` 两个非负整数（如 `"0.1"`、`"0.10"`、`"1.0"`、`"2.5"`）
- 不允许 patch 版本（无 `0.1.1` 之类）—— 与"严格串行 + 简单"哲学一致
- 不允许其他 SemVer 元素（无 prerelease、build metadata）

**比较逻辑**：

- 解析两个非负整数 (major, minor)
- 词典序比较（先 major 后 minor），所以 `"0.10" > "0.2"` 因为 minor 10 > 2

`progress.py release-start` 的 version 校验：

1. 解析 `<x>.<y>` 形如 `^(\d+)\.(\d+)$` 的字符串
2. 把 previous_releases 全部解析成 (major, minor)
3. 新 version 必须严格大于所有 previous (按数字比较)

### F4 设计选择：精确 mutation 表

**`release-close`**：

```yaml
# 前置条件
- release_state == active
- current_stage == project-retrospective
- sub_state == review-passed

# 字段变更
release_state: active → closed
previous_releases: [...] → [..., <current release>]
# 其他字段保留不变（current_stage 留在 project-retrospective）
```

**`release-start --version <x.y>`**：

```yaml
# 前置条件
- release_state == closed（首次 init 不用 release-start）
- <x.y> 解析合法 + 严格大于 all previous_releases

# 字段变更
release: <previous> → <x.y>
release_state: closed → active
scenario: 由 caller 提供（S2-1/2/3 之一）
scenario_subtype: 同上
current_stage: 按 scenario 决定（S2-1=prd-inception, S2-2=srs-specification, S2-3=srs-specification）
sub_state: write
review_iteration: 0
artifacts: 重新初始化 release-scoped 路径（srs/development/testing/delivery 都改 docs/release<x.y>/...）
artifacts.prd: 不变（项目级）
artifacts.architecture: 不变（项目级）
unresolved_bugs: [...] → []  # 全部消费
# 同时为每个原 unresolved_bug 在对应 BUG-NNN.md frontmatter 加 consumed_in_release: <x.y>
```

由 srs-write skill 在 SRS write 阶段读取 `consumed_in_release == <current release>` 的 bug 列表，把它们的修复需求合并到新 SRS 中。

## v0.3 → v0.4 主要修改清单

| 文件 | 变化 |
|------|------|
| `docs/workflow/workflow_specification_claude.md` | v0.3 → v0.4：§2 S4 表行加 active-only 注；§6 引言加 v0.4 注；§9.4 段重写引言；Change Log 加 v0.4 |
| `docs/design/skill_set_design_proposal_v0.4.md` | 新文件，应用全部 6 项 fix + 上述设计选择 |
| `docs/design/skill_set_design_proposal_v0.3.md` | 保留作为历史 |

## 没有采纳的项

无。6 项全部采纳。
