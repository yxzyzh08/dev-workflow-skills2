# Reviewer Feedback Response — Proposal v0.4

**Source Review**: `docs/review/skill_set_design_proposal_v0.4_rereview.md`
**Adopted In**: `docs/design/skill_set_design_proposal_v0.5.md`
**Workflow Spec Update**: `docs/workflow/workflow_specification_claude.md` (v0.4 → v0.5)
**Date**: 2026-05-06
**Reviewed By**: User + Claude

---

## Findings 处置一览

| # | Severity | Finding 摘要 | 处置 |
|---|----------|---------------|------|
| F1 | Medium | Active Bug Flow 缺 bug-start / bug-close mutation | **采纳**：加 `progress.py bug-start` / `bug-close` 子命令 + 精确 mutation |
| F2 | Medium | incident-resolve 缺精确 mutation；abort/reconstruct 缺终态字段 | **采纳**：详细 3 个 action 的 mutation；progress.md 加 `project_state` + `release_close_reason` 字段 |
| F3 | Low | 仍有 script path shorthand 残留 | **采纳**：grep + 全文清理 |
| F4 | Low | workflow spec 残留 v0.3 引用 + workflow-evolution 待定 | **采纳**：spec 改 2 处，bump v0.5 |

4 项全采纳，无反驳，无 High blocker。

## 关键设计选择

### F1：Active Bug Flow 子命令设计

新增两个 progress.py 子命令：

**`bug-start --bug <path> --root-cause <enum>`**：

- **前置**：`bug_flow.active == false`、`current_stage == testing`、testing 阶段刚发现 bug
- **触发方**：bug-triage active mode 在判定根因后调用
- **mutation**：
  ```yaml
  bug_flow.active: false → true
  bug_flow.bug_report_path: null → <path>
  bug_flow.root_cause: null → <srs|architecture|development>  # prd-exception 走 incident-start
  current_stage: testing → <root_cause stage>  # 进入对应 stage Change Mode
  sub_state: review-passed → write   # Change Mode 下重新走 write 循环
  review_iteration: <N> → 0
  ```

**`bug-close`**：

- **前置**：`bug_flow.active == true` AND testing 重测通过（Test Report `verification_status: pass`）
- **触发方**：testing-write 在 retest pass 后调用
- **mutation**：
  ```yaml
  bug_flow.active: true → false
  bug_flow.bug_report_path: <path> → null
  bug_flow.root_cause: <enum> → null
  current_stage: testing → testing  # 保持，进入正常 Stage 5 done 判定
  ```

bug-close 后 workflow-protocol 评估 Stage 5 done 条件，pass 则推进 Stage 6（正常路径）。

### F2：incident-resolve 精确 mutation（3 个 action）

progress.md 新增字段：

```yaml
project_state: active | aborted | reconstructing  # v0.5 新加，默认 active
release_close_reason: null | "stage-7-completed" | "incident-abort" | "incident-reconstruct"  # v0.5 新加
```

**`incident-resolve --action continue`**：

- **前置**：`workflow_incident_active == true` AND 用户决定 workflow 改进后继续
- **mutation**：
  ```yaml
  workflow_incident_active: true → false
  incident_report_path: <path> → null  # incident report 文件保留在 docs/incident/，但 progress 不再引用
  current_stage: workflow-incident-analysis → testing  # 回到 Stage 5 retest（incident 起点）
  bug_flow: 视用户决策保留或清理
  ```

**`incident-resolve --action abort`**：

- **前置**：`workflow_incident_active == true` AND 用户判定 project 不可继续
- **mutation**：
  ```yaml
  workflow_incident_active: true → false
  project_state: active → aborted
  release_state: active → closed
  release_close_reason: null → "incident-abort"
  current_stage: workflow-incident-analysis → null  # 终态
  ```
- abort 后该 progress.md 进入终态，禁止任何后续 update（除 query / recover）。用户若要继续，需要新开 project。

**`incident-resolve --action reconstruct`**：

- **前置**：`workflow_incident_active == true` AND 用户判定需要从外部源系统重构（即转 S3）
- **mutation**：
  ```yaml
  workflow_incident_active: true → false
  project_state: active → reconstructing
  release_state: active → closed
  release_close_reason: null → "incident-reconstruct"
  current_stage: workflow-incident-analysis → null  # 终态
  ```
- reconstruct 后该 project 进入终态。用户启动新 S3 project（独立目录、独立 progress.md），可在新 PRD 中引用本 project 作为 source system。

### F3：Script Path Shorthand 清理

v0.5 全文 grep `scripts/(progress|validate|changelog)\.py` 替换为 `skills/<name>/scripts/<x>.py` 全路径，仅在表格"display-only" 上下文（如示例输出表）保留 shorthand 并明示。

### F4：Workflow Spec 残留同步

- §5 Stage Mode Rule：移除"v0.3 design"硬引用，改为"latest design proposal"软引用
- §11 Meta-Evolution Loop：`workflow-evolution` skill 不再标"待定"，改为"详见 design proposal Section 6"
- frontmatter `status: Draft v0.4 → Draft v0.5`
- Change Log 加 v0.5 entry

## v0.4 → v0.5 主要修改清单

| 文件 | 变化 |
|------|------|
| `docs/workflow/workflow_specification_claude.md` | v0.4 → v0.5：§5/§11 残留同步 + Change Log entry |
| `docs/design/skill_set_design_proposal_v0.5.md` | 新文件：加 bug-start/bug-close + 完整 incident-resolve mutation + 新字段 + 路径清理 |
| `docs/design/skill_set_design_proposal_v0.4.md` | 保留作为历史 |

## 没有采纳的项

无。4 项全部采纳。

## 评审循环统计

- v0.1 评审：9 项 finding（5 High + 4 Medium）
- v0.2 评审：8 项 finding（5 High + 3 Medium + 1 Low）
- v0.3 评审：6 项 finding（3 High + 2 Medium + 1 Low）
- v0.4 评审：4 项 finding（**0 High** + 2 Medium + 2 Low）

Finding 数量逐轮收敛，且 High 已清零。v0.5 后建议进入 Task 5（实现），实际实现中遇到的细节问题再做 v0.6+ 迭代会更高效（避免纯 spec-level 推演）。
