---
name: development-code-write
description: dev-workflow-skills2 Stage 4 Development code 写作 vertical skill。Task-bounded：在 progress.md current_stage==development 且目标 task_state ∈ {test-done, code-writing, code-revising, code-review-passed, verifying} 时被 invoke。负责本 task 的 src/ source code 编写/修订、创建或重置 code_review_report.md pending skeleton；review 通过后还负责 verifying→verified：运行 unit+integration tests，写 verification_result.md。verification fail 是 Stage 4 内部 retry，不进入 Bug Flow；但当前 workflow-protocol 需补明确 verification-failed 回退 transition。本 skill 不评审自身代码、不写 tests/、不填写 code review pass/fail、不直接 mutation progress.md。
authority: 4
references: []
---

# development-code-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（两组 7 项）**：

**Code Write Submode（4 项）**：

1. 在单个 task scope 内修改 `src/` / production code / necessary config
2. 对照 `detailed_design.md`、tests、SRS/Architecture 实现行为
3. 创建或重置 `code_review_report.md` pending skeleton，防止绕过 code review
4. 修复 `development-code-review` findings 后重新提交 code review

**Verification Submode（3 项）**：

5. 在 `code-review-passed` 后进入 verification submode，运行 unit + integration tests
6. 写 `verification_result.md`，frontmatter `verification_status: pass|fail|partial`
7. verification pass 时调 `progress.py update --task Tn --status verified`

**不属于本 skill**：

- 评审代码（→ `development-code-review`）
- 编写/评审测试代码（→ `development-test-write/review`；本 skill只运行 tests）
- 填写 `code_review_report.md` 的 pass/fail findings（review skill 专属）
- 在 verification fail 后进入 Bug Flow（Stage 4 自验证 fail 是内部 retry；Stage 5 Testing fail 才进 bug-triage）
- 直接编辑 `progress.md`

## 2. When to Invoke

| task state | 本 skill submode |
|------------|------------------|
| `test-done` | 首次 code write；先调 `progress.py update --task Tn --status code-writing`（claim task = 用 progress.py 把 task state 推到 in-progress 子状态，不是文件锁）|
| `code-writing` | 继续/恢复 code write |
| `code-revising` | 按 code-review findings 修 source |
| `code-review-passed` | verification submode：先调 `progress.py update --task Tn --status verifying` |
| `verifying` | 恢复 verification / 写 verification_result / 处理 verification fail |

**全局条件**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `workflow_incident_active` | `false` |

**Bug Flow 入口**：`bug_flow.active==true`、`root_cause==development`，且 BUG body `Affected Task(s)` 包含本 task；若 BUG 指向测试遗漏，应先由 `development-test-write` 处理。

若 affected task 当前已 `verified` 或 `code-review-passed`，必须由 `progress.py bug-start --bug <BUG path> --root-cause development` 自动 rollback（Task 6 Phase 6.1 实装的 `compute_dev_bug_rollback` 解析 BUG body `## Triage Analysis` `**Affected Task(s)**` + classification keyword 决定 `verified → test-revising` / `verified → code-revising` / `code-review-passed → code-revising`）；本 skill 在 rollback 完成后才接管。不得手工改 progress.md。

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

## 3. Full Mode vs Change Mode vs Verification Mode

| Mode | 入口 | 动作 | 输出 |
|------|------|------|------|
| Normal Code Write | `test-done` → `code-writing` | 实现本 task source code | pending `code_review_report.md` |
| Code Revise | `code-revising` | 修 review findings | 重置 pending `code_review_report.md` |
| Bug Fix | root_cause=development | 修 BUG 涉及 task source；可添加 notes linking BUG id | 重置 pending report；后续仍要 code review |
| Verification | `code-review-passed` → `verifying` | 运行 unit+integration tests | `verification_result.md` |
| Verification Retry | `verifying` with fail/partial result | 按 verification failure 修 code 后重新 review/verify | 走 `progress.py update --task Tn --status code-revising`（PROTECTED_TASK_TRANSITIONS `verifying → code-revising`，由 verification_result.md `verification_status ∈ {fail, partial}` 间接 enable；Task 6 Phase 6.1 实装） |

**verification 边界（已由用户确认）**：

- `development-code-write` 是 `verifying → verified` owner
- verification fail 不进入 Bug Flow；Bug Flow 只由 Stage 5 Testing fail 触发
- verification fail 不能绕过 code review 直接修完再标 verified；必须回到 code review 循环（PROTECTED_TASK_TRANSITIONS `verifying → code-revising` 已 Task 6 Phase 6.1 实装，由 verification_result.md `verification_status ∈ {fail, partial}` 间接 enable，事实源 progress_state.py）

## 4. Output Contract

### 4.1 Source output

- `src/**` 或项目既有 source tree
- 必须 task-bounded：优先只触碰 `detailed_design.md` / `breakdown.md` 声明范围
- 若必须改共享模块，需在对话和 code review report body 中说明 cross-task impact；不得 revert 其他 task/agent 改动
- `src/` 不在 doc-guardian 管辖（事实源 `skills/doc-guardian/references/directory-layout.md`）；source quality gate 由 `code_review_report.md` 与 `development-code-review` 承担，verification execution 由本 skill verification submode 承担

### 4.2 code_review_report.md pending skeleton

路径：`docs/release<x.y>/development/tasks/T<n>/code_review_report.md`

`code_review_report.md` 是一次性 doc（事实源 `skills/doc-guardian/references/change-log-format.md` §1），不需要 `## Pending Changes` / `## Change Log` 章节。

```yaml
---
title: Code Review Report for T<n>
type: code-review-report
status: draft
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/development-code-write
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

注：`status: draft` 是 doc 自身生命周期状态；`review_status: pending` 是三态 review 结果。两字段独立：doc status 由 `skills/doc-guardian/scripts/status_transition.py`（Gap-2）维护，`review_status` 由 `development-code-review` 写入 `pass|fail`。

### 4.3 verification_result.md

路径：`docs/release<x.y>/development/tasks/T<n>/verification_result.md`

`verification_result.md` 是一次性 doc（事实源 `skills/doc-guardian/references/change-log-format.md` §1），不需要 `## Pending Changes` / `## Change Log` 章节。

```yaml
---
title: Verification Result for T<n>
type: verification-result
status: draft | review-passed
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/development-code-write
release: "<x.y>"
task_id: T<n>
verification_status: pass | fail | partial
---
```

Body 必须包含：commands run、unit test result、integration test result、failures（如有）、environment notes、links to relevant test files。

## 5. Standard Procedure

### 5.1 Code Write / Revise Procedure

```
Step 1. Claim / verify task state
        - test-done: progress.py update --task Tn --status code-writing
        - code-writing/code-revising: continue current code loop
        - 其他 state: stop and re-route

Step 2. Implement source changes
        - 读 detailed_design.md + tests + SRS/Architecture
        - 修改 src/ bounded scope
        - 不修改 tests/；若发现 test fixture / assertion 需要改，交 development-test-write

Step 3. 创建或重置 code_review_report.md pending skeleton
        - 首次创建 pending
        - revise 后清空 stale findings，review_status 回 pending
        - 不添加 Pending Changes / Change Log（code-review-report 是一次性 doc）

Step 4. validate report skeleton
        - validate.py file code_review_report.md

Step 5. Submit code review
        - progress.py update --task Tn --status code-review
        - 控制权交 development-code-review
```

### 5.2 Verification Procedure

```
Step V1. Start verification
        - progress.py update --task Tn --status verifying（from code-review-passed）

Step V2. Run tests
        - unit tests for this task
        - integration tests impacted by this task / DAG dependencies
        - record exact commands and outcomes

Step V3. Write verification_result.md
        - pass: verification_status: pass
        - fail/partial: verification_status: fail 或 partial；body 列 failures
        - validate.py file verification_result.md
        - 不添加 Pending Changes / Change Log（verification-result 是一次性 doc）

Step V4. Finish or retry
        - pass: progress.py update --task Tn --status verified
        - fail/partial: do not call verified；caller 调 `progress.py update --task Tn --status code-revising`（PROTECTED_TASK_TRANSITIONS `verifying → code-revising`，由 verification_result.md `verification_status ∈ {fail, partial}` 间接 enable），再走 code review
```

## 6. Stage Done Conditions（per-task code + verification）

| 子状态 | 条件 |
|--------|------|
| `code-review` | source change 完成，`code_review_report.md review_status: pending` |
| `code-review-passed` | `development-code-review` 已写 `review_status: pass` 且 blocking=0 |
| `verifying` | code review pass 后正在运行 unit/integration tests |
| `verified` | `verification_result.md verification_status: pass` 且 validate exit 0 |

Stage 4 done 需要所有 task 都 `verified`，且 advance 时无条件校验 each task 4 个 artifacts。

## 7. Bug Flow Re-entry

当 `root_cause==development` 且 BUG 指向 source bug：

1. 读 BUG body `Affected Task(s)` 和 likely affected files
2. 确认 SRS / Architecture / detailed_design 不需要变；若需要，停止并路由上游 skill
3. 若 tests 未覆盖 BUG，先让 `development-test-write` 添加 regression test
4. 修改 source code，重置 code_review_report pending
5. 通过 code review 后由本 skill跑 verification
6. 返回 Stage 5 retest；只有 retest pass 后才能 `bug-close`

## 8. Forbidden Actions

- ❌ 修改 `progress.md` / `progress-history.md`
- ❌ 创建 `code_review_report.md` 时使用 `review_status: pass`
- ❌ 自己填写 code review `pass` / `fail` findings（review skill 专属）
- ❌ 修改 `tests/`（测试代码 owner 是 `development-test-write`）
- ❌ code review 未 pass 就运行 verification 并标 verified
- ❌ verification fail 后直接改代码并再次标 verified，绕过 code review
- ❌ Stage 4 verification fail 时调用 bug-triage / bug-start
- ❌ 因本 task 修改 revert 其他 task/agent 的 source changes
- ❌ 跳过 `validate.py file` 校验 review/verification artifacts

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| `update --task code-writing` 失败 | 查 task state；若 test 未 done，返回 test flow |
| code skeleton validate 失败 | 修 report frontmatter/counts/type 后重跑 |
| `update --task code-review` 失败 | 确认 report pending 且 task in code-writing/code-revising |
| code-review fail | 等 `development-code-review` 转 `code-revising`；修 code，重置 pending，再 submit |
| verification tests fail | 写 `verification_result.md verification_status: fail/partial`；不得标 verified；caller 调 `progress.py update --task Tn --status code-revising`（PROTECTED_TASK_TRANSITIONS verifying → code-revising，已 Task 6 实装）回到 code review 循环 |
| verification_result validate 失败 | 修 report schema/body 后重跑 validate |
| BUG 指向多个 task | 逐 task 修复；共享代码改动必须在 breakdown/DAG 中说明 |

## 10. References

- `skills/development-code-review/SKILL.md` — code review owner
- `skills/development-test-write/SKILL.md` — tests source owner
- `skills/development-planning-write/SKILL.md` — detailed design source
- `skills/workflow-protocol/SKILL.md` — Stage 4 task matrix
- `skills/workflow-protocol/references/command-reference.md` — task transitions
- `skills/doc-guardian/references/frontmatter-schema.md` — code-review-report / verification-result schema
- `skills/doc-guardian/references/required-artifacts.md` — Stage 4 per-task unconditional validation
- `skills/bug-triage/references/root-cause-rubric.md` — development source bug examples

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：task doc frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
- **Gap-3（已 closed by Task 6 Phase 6.1）**：verification fail 的 `verifying → code-revising` rollback 已实装为 PROTECTED_TASK_TRANSITIONS 的一部分，由 `progress.py update --task Tn --status code-revising` 触发；apply_update_task 间接通过 `verification_result.md verification_status ∈ {fail, partial}` enable。事实源 `skills/_shared/dev_workflow/progress_state.py` `PROTECTED_TASK_TRANSITIONS`。
- **Gap-4（已 closed by Task 6 Phase 6.1）**：Bug Flow `root_cause==development` 切回 Stage 4 时，`progress.py bug-start --bug <BUG path> --root-cause development` 会自动解析 BUG body `## Triage Analysis` `**Affected Task(s)**` + classification keyword（`test-only` / `source-code` / 等）决定 `verified → test-revising` / `verified → code-revising` / `code-review-passed → code-revising`，原子化写入 progress.md；compute_dev_bug_rollback + apply_bug_start 共同 enforce。事实源 `skills/_shared/dev_workflow/progress_state.py` 的 `compute_dev_bug_rollback`。
