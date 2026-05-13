---
name: development-test-write
description: dev-workflow-skills2 Stage 4 Development test 写作 vertical skill。Task-bounded：仅在 progress.md current_stage==development 且目标 task_state ∈ {planning-done, test-writing, test-revising} 时被 invoke。负责为本 task 编写/修订 tests/ 下 unit/integration 测试代码，并创建或重置 docs/release<x.y>/development/tasks/T<n>/test_review_report.md pending skeleton。完成后跑 validate.py 校验 report skeleton，并调 progress.py update --task Tn --status test-review。Bug Flow root_cause==development 且修复为测试遗漏时进入 Change Mode。本 skill 不写 src/、不填写 review_status pass/fail、不推进 test-done、不写 code_review_report/verification_result。
authority: 4
references: []
---

# development-test-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（6 项）**：

1. 在单个 task scope 内编写或修订 `tests/unit/`、`tests/integration/` 中的测试代码
2. 依据 `detailed_design.md` 和 SRS acceptance criteria 设计 test cases
3. 创建本 task 的 `test_review_report.md` skeleton，frontmatter `review_status: pending`
4. 在 revise 后重置 stale report（`pass`/`fail` → `pending`，counts 清零），防止绕过 review
5. 跑 `validate.py file test_review_report.md`，确保 skeleton schema 合规
6. 调 `progress.py update --task Tn --status test-review`，把控制权交给 `development-test-review`

**不属于本 skill**：

- 评审测试代码（→ `development-test-review`）
- 填写 `review_status: pass|fail` 或 findings counts
- 修改源代码 `src/`（→ `development-code-write`）
- 写 `code_review_report.md` / `verification_result.md`
- 让 task 进入 `test-done`（只有 test-review pass 后可转）
- 直接 mutation `progress.md`

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `development_state.task_states[Tn]` | `planning-done` / `test-writing` / `test-revising` |
| `workflow_incident_active` | `false` |

**入口解释**：

| task state | 本 skill 行为 |
|------------|---------------|
| `planning-done` | 首次开始测试编写；先调 `progress.py update --task Tn --status test-writing`（claim task = 用 progress.py 把 task state 推到 in-progress 子状态，不是文件锁）|
| `test-writing` | 已 claim 后继续/恢复测试编写 |
| `test-revising` | 按 test-review findings 修测试；完成前重置 report 为 pending skeleton |

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

**Bug Flow 入口**：

- `bug_flow.active==true` 且 `root_cause==development`
- BUG body `Affected Task(s)` 包含 `Tn`
- triage / planning-write 判定问题属于测试遗漏或测试错误（不需改 SRS/Architecture）
- 若 affected task 当前已 `verified`，由 `progress.py bug-start --bug <BUG path> --root-cause development` 按 BUG body `**Affected Task(s)**` + `test-only` / `regression-test` 类 classification keyword 自动 rollback 到 `test-revising`（PROTECTED_TASK_TRANSITIONS + compute_dev_bug_rollback；Task 6 Phase 6.1 实装），rollback 完成后本 skill 才接管

## 3. Full Mode vs Change Mode

| Mode | 入口 | 测试动作 | report skeleton |
|------|------|----------|-----------------|
| Normal Write | `planning-done` → `test-writing` | 新增本 task tests | 创建 pending skeleton |
| Resume Write | `test-writing` | 继续未完成 tests | 确保 skeleton 不存在或仍 pending；不得已有 pass |
| Review Revise | `test-revising` | 按 findings 修 tests | 重置为 pending，清空 counts |
| Bug Flow Test Fix | root_cause=development 且测试遗漏 | 增补 regression test / 修错误断言 | 重置为 pending，记录 BUG id in body |

**测试代码边界**：

- 优先写本 task 相关 tests；跨 task integration test 必须在 `breakdown.md` DAG 中有依赖说明
- tests 目录不在 doc-guardian 管辖；quality gate 由 `test_review_report.md` 和 `development-test-review` 承担
- 由于源代码可能尚未实现，本阶段不要求所有 tests runtime pass；runtime pass 在 code verification 阶段判定

## 4. Output Contract

**测试代码输出**：

| 输出 | 路径 |
|------|------|
| Unit tests | `tests/unit/**`（具体结构由项目技术栈决定）|
| Integration tests | `tests/integration/**`（跨 task 需遵守 DAG）|

**doc artifact 输出**：

`docs/release<x.y>/development/tasks/T<n>/test_review_report.md`

`test_review_report.md` 是一次性 doc（事实源 `skills/doc-guardian/references/change-log-format.md` §1），不需要 `## Pending Changes` / `## Change Log` 章节；body 直接保留 review context / 待填 findings 区即可。

```yaml
---
title: Test Review Report for T<n>
type: test-review-report
status: draft
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/development-test-write
release: "<x.y>"
task_id: T<n>
findings_count: 0
severity_distribution:
  critical: 0
  high: 0
  medium: 0
  low: 0
review_status: pending
blocking_findings_count: 0
max_severity: low
---
```

注：`status: draft` 是 doc 自身生命周期状态；`review_status: pending` 是三态 review 结果。两字段独立：doc status 由 `skills/doc-guardian/scripts/status_transition.py`（Gap-2）维护，`review_status` 由 `development-test-review` 写入 `pass|fail`。

**body 最低内容**：

- Task Context（link to detailed_design）
- Test Files Under Review
- Intended Coverage
- Known Runtime Limitations before Code Implementation
- Review Findings（由 review skill 填或改写）

## 5. 5-Step Standard Procedure

```
Step 1. Claim / verify task state
        - 若 task_state == planning-done: progress.py update --task Tn --status test-writing
        - 若 task_state == test-revising: 继续 revise，不调其他全局 event
        - 若 task_state 不在允许集合：停止并让 Bootstrap 重路由

Step 2. 写/修 tests
        - 读 detailed_design.md / SRS acceptance / Architecture contracts
        - 写 unit tests + integration tests
        - 不改 src/；如发现 source design 不可测，记录 finding 给 planning/code，不自行改

Step 3. 创建或重置 test_review_report.md pending skeleton
        - 首次：新建 skeleton，review_status: pending
        - revise：清空上一轮 findings counts，review_status: pending
        - 不写 pass/fail；不提前设置 review-passed
        - 不添加 Pending Changes / Change Log（test-review-report 是一次性 doc）

Step 4. validate report skeleton
        - skills/doc-guardian/scripts/validate.py file docs/release<x.y>/development/tasks/T<n>/test_review_report.md
        - exit 0 后才可进入 Step 5

Step 5. Submit to test review
        - skills/workflow-protocol/scripts/progress.py update --task Tn --status test-review
        - 控制权交给 development-test-review
```

## 6. Stage Done Conditions（per-task test 部分）

| 子状态 | 需要满足 |
|--------|----------|
| `test-writing` | 本 skill 正在写 tests；report 可不存在或 pending |
| `test-review` | tests 已写完；`test_review_report.md` 必须存在且 `review_status: pending` |
| `test-revising` | test-review fail 后修 tests；完成时必须重置 pending |
| `test-done` | 仅 `development-test-review` 可在 `review_status: pass` 且 `blocking_findings_count: 0` 后设置 |

Stage 4 advance 时仍会无条件校验每 task 4 个 per-task artifacts；test code 本身不由 doc-guardian 校验。

## 7. Bug Flow Re-entry

当 Stage 5 testing 发现 bug 且 root_cause=development：

- 若 BUG 显示测试遗漏（例如原 Stage 4 tests 未覆盖边界），本 skill进入 Change Mode 添加 regression test
- 若 BUG 是 source code 错误，本 skill不应被直接调用；应路由 `development-code-write`
- 若 BUG 暴露 detailed_design 缺失，本 skill停止并要求 `development-planning-write` 先修设计
- 修测试后仍须 `development-test-review` pass，再进入 code 修复 / verification / Stage 5 retest

## 8. Forbidden Actions

- ❌ 修改 `src/` 或 production config
- ❌ 在 `test_review_report.md` 中写 `review_status: pass` 或 `fail`（review skill 专属）
- ❌ 创建 skeleton 时用 `review_status: pass`（会绕过 review；必须 pending）
- ❌ 不重置 stale fail/pass report 就提交 `test-review`
- ❌ 调 `progress.py update --task Tn --status test-done`
- ❌ 跳过 `validate.py file` 提交 review
- ❌ 直接编辑 `progress.md`
- ❌ 跨 task 修改 tests 却不更新/引用 breakdown DAG

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| `update --task test-writing` 失败 | 查 task state；若不是 planning-done/test-writing/test-revising，停止 |
| tests 编写发现 detailed_design 不可执行 | 停止并记录 planning issue；不要自行改 detailed_design |
| skeleton validate 失败 | 修 frontmatter / counts / type / task_id 后重跑 |
| `update --task test-review` 失败 | 检查 report 是否存在 pending；检查 task state 是否 test-writing/test-revising |
| review fail 后重新提交但 report 仍 fail | 重置为 pending skeleton 后再 submit |
| Bug Flow 指向多个 task | 逐 task 处理；每个 task 都要独立 pending report + review |

## 10. References

- `skills/development-test-review/SKILL.md` — test review owner
- `skills/development-planning-write/SKILL.md` — task detailed design source
- `skills/workflow-protocol/SKILL.md` — Stage 4 task state matrix
- `skills/workflow-protocol/references/command-reference.md` — task transitions
- `skills/doc-guardian/references/frontmatter-schema.md` — test-review-report 三态 schema
- `skills/doc-guardian/references/directory-layout.md` — per-task paths
- `skills/bug-triage/references/root-cause-rubric.md` — development-test 层 bug 判断

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：task doc frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`；本 skill只创建/重置 owned skeleton，caller 在 progress event 成功后显式传入 per-task doc path 调用 helper。
- **Gap-4（已 closed by Task 6 Phase 6.1）**：Bug Flow `root_cause==development` 若要修已 `verified` task 的测试，`progress.py bug-start --bug <BUG path> --root-cause development` 已实装按 BUG body `## Triage Analysis` `**Affected Task(s)**` + classification keyword 自动执行 `verified → test-revising` rollback（PROTECTED_TASK_TRANSITIONS + compute_dev_bug_rollback）。本 skill 在 rollback 后接管 task `test-revising` 入口；事实源 `skills/_shared/dev_workflow/progress_state.py`。
