---
name: development-code-review
description: dev-workflow-skills2 Stage 4 Development code 评审 vertical skill。Task-bounded：仅在 progress.md current_stage==development 且目标 task_state==code-review 时被 invoke。评审本 task 的 src/source changes 与 detailed_design、tests、SRS/Architecture 的一致性，填写 code_review_report.md 三态结果：review_status pass 或 fail。pass 时 blocking_findings_count 必须为 0，并调 progress.py update --task Tn --status code-review-passed；fail 时调 progress.py update --task Tn --status code-revising。本 skill 不修改源码/测试、不运行最终 verification、不调用全局 review-passed/review-issues event、不签发 approved。
authority: 4
references: []
---

# development-code-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（6 项）**：

1. 评审本 task 的 source code diff / touched files
2. 对照 `detailed_design.md`、tests、SRS/Architecture 检查实现一致性
3. 检查代码质量、安全性、错误处理、边界条件、并发/资源管理、可维护性
4. 填写 `code_review_report.md` findings 与 `review_status: pass|fail`
5. pass 时调 `progress.py update --task Tn --status code-review-passed`
6. fail 时调 `progress.py update --task Tn --status code-revising`

**不属于本 skill**：

- 修改 `src/`、`tests/`、detailed_design 或 planning docs
- 创建 pending skeleton（→ `development-code-write`）
- 写 `verification_result.md` 或判定 `verified`（→ `development-code-write` verification submode）
- 调全局 `progress.py update --event review-passed/review-issues`
- 关闭 Bug Flow

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `development_state.task_states[Tn]` | `code-review` |
| `code_review_report.md` | 存在且 `review_status: pending`（正常入口） |

**拒绝入口**：

- task_state 不是 `code-review`
- code_review_report 缺失或不是 pending
- tests for this task 尚未 `test-done`
- BUG Flow 中 BUG 的 affected task 不含本 task（除非 planning-write 已更新 routing）

**task-level review_iteration 说明**：本 skill 不使用 global `review_iteration`（task-level 三态 report 循环不计入 workflow-protocol §8 Review Loop cap 7）；如果同一 task 反复 fail，需要 break loop 时按 §9 Recovery 升级人介入。

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | Requirements Fit | source 是否满足 detailed_design / SRS acceptance criteria？ | 核心需求未实现或行为错误 |
| 2 | Test Alignment | source 是否让本 task tests 有合理通过路径；是否遗漏测试暴露的行为？ | 已有测试目标无法被实现满足 |
| 3 | Architecture Fit | 是否遵守 architecture contracts、module boundaries、dependency direction？ | 破坏架构边界或公共契约 |
| 4 | Error Handling | 边界/异常/权限/空值处理是否完整？ | 关键错误路径未处理 |
| 5 | Security / Safety | 输入校验、敏感数据、注入、权限等风险？ | 高风险安全缺陷 |
| 6 | Concurrency / State | race、transaction、cache consistency、resource cleanup？ | 可能导致数据损坏/泄露 |
| 7 | Maintainability | 复杂度、重复、命名、可读性、局部性？ | 难以维护到影响正确性时 blocking |
| 8 | Bug Flow Coverage | root_cause=development 时 source fix 是否覆盖 BUG？（详见 `development-code-write` §7）| BUG 复现路径未被修复 |

## 4. Output Contract（三态 report）

### 4.1 pass

`code_review_report.md` 必须更新为：

```yaml
review_status: pass
blocking_findings_count: 0
findings_count: <medium+low count allowed>
severity_distribution:
  critical: 0
  high: 0
  medium: <int>
  low: <int>
max_severity: low | medium
```

然后：

- `validate.py file code_review_report.md`
- `progress.py update --task Tn --status code-review-passed`
- 对话输出 `development-code-review T<n> — pass`

### 4.2 fail

`code_review_report.md` 必须更新为：

```yaml
review_status: fail
findings_count: <int>
severity_distribution:
  critical: <int>
  high: <int>
  medium: <int>
  low: <int>
blocking_findings_count: <critical+high count>
max_severity: low | medium | high | critical
```

然后：

- `validate.py file code_review_report.md`
- `progress.py update --task Tn --status code-revising`
- 对话输出 findings markdown 给 `development-code-write`

### 4.3 Finding 模板

```markdown
## development-code-review T<n> — fail

**Summary**: <critical> critical / <high> high / <medium> medium / <low> low

### Finding 1 [high, 维度 4: Error Handling]
- **Where**: src/<file>:<line>
- **Issue**: <问题>
- **Recommendation**: <具体修改建议>
```

## 5. Review Procedure（5 步）

```
Step 1. validate code_review_report skeleton
        - validate.py file code_review_report.md
        - 要求 review_status == pending

Step 2. 读上下文与 diff
        - detailed_design.md
        - test_review_report.md（必须 pass）
        - tests for this task
        - source diff/touched files
        - file scope 以 detailed_design.md `Files / Modules to Touch` + breakdown.md task ownership map 为基准，可结合 git diff 取证 actual delta；跨 scope 改动列为 finding
        - BUG report（若 bug_flow.active）

Step 3. 按 §3 rubric 评审代码
        - 可运行 lint/targeted tests 作 evidence，但不写 verification_result.md
        - 不修改任何 source/test 文件

Step 4. 填写 code_review_report.md
        - blocking findings → fail
        - 无 blocking → pass
        - counts 与 severity_distribution 必须一致
        - 不操作 Pending Changes / Change Log（code-review-report 是一次性 doc）

Step 5. validate + task transition
        - validate.py file code_review_report.md
        - pass: progress.py update --task Tn --status code-review-passed
        - fail: progress.py update --task Tn --status code-revising
```

## 6. Stage Done Conditions（per-task code review）

`code-review-passed` 转移硬条件：

- `code_review_report.md` 存在
- `review_status == "pass"`
- `blocking_findings_count == 0`
- `validate.py file` exit 0

`code-review-passed` 后仍未 `verified`：必须由 `development-code-write` verification submode 跑 unit + integration tests 并写 `verification_result.md verification_status: pass`。

**Stage 4 C 维度复合判定**：本 skill 贡献 code 子层（each task `code_review_report.md review_status: pass`）；它必须与 planning review-passed、test review pass 共同构成 workflow-protocol §5.1 Stage 4 C 维度。

## 7. Bug Flow Re-entry

当 root_cause=development 且 BUG 指向 source bug：

- 本 skill检查 code fix 是否覆盖 BUG 复现路径
- 检查 regression tests 是否存在且 test-review 已 pass；若缺测试，fail 并要求先回 `development-test-write`
- 如发现修复需要 detailed_design/SRS/Architecture 改动，fail 并路由对应上游，不允许在 code 层硬编码补丁
- pass 后不关闭 Bug Flow；仍需 verification + Stage 5 retest + bug-close

## 8. Forbidden Actions

- ❌ 修改 source/test/doc body（除 owned `code_review_report.md` fields）
- ❌ 让 `review_status` 保持 pending 后调 `code-review-passed`
- ❌ `review_status: pass` 且 `blocking_findings_count > 0`
- ❌ 调全局 `progress.py update --event review-passed` / `review-issues`
- ❌ 写 `verification_result.md` 或调 `verified`
- ❌ 输出 `approved`
- ❌ 忽略 `test_review_report.md` 未 pass 直接 code-review pass
- ❌ 因本 task review revert 其他 task/agent changes

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| skeleton 缺失 | 停止；要求 development-code-write 创建 pending skeleton |
| skeleton 已 pass/fail 但 task 仍 code-review | 判 stale/corrupt；要求 write skill 重置 pending 或 query 并发状态 |
| validate report fail | 修 owned report fields 后重跑 |
| `update --task code-review-passed` 被拒 | 检查 review_status/pass/blocking count/test-done 前置 |
| `update --task code-revising` 被拒 | 检查 task state 是否仍 code-review；并发推进时停止 |
| 发现 tests 不足 | fail，finding 指向 test-write；不要自行加 test |
| 发现 architecture mismatch | fail，要求 planning/upstream route；不要自行改 architecture |

## 10. References

- `skills/development-code-write/SKILL.md` — code write / verification owner
- `skills/development-test-review/SKILL.md` — test review pass 前置
- `skills/workflow-protocol/SKILL.md` — Stage 4 task matrix
- `skills/workflow-protocol/references/command-reference.md` — `code-review -> code-review-passed/code-revising`
- `skills/doc-guardian/references/frontmatter-schema.md` — code-review-report 三态 schema
- `skills/doc-guardian/references/required-artifacts.md` — Stage 4 per-task artifacts
- `skills/bug-triage/references/root-cause-rubric.md` — development root cause examples

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：code_review_report frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
- **Gap-3（已 closed by Task 6 Phase 6.1）**：verification fail 的 `verifying → code-revising` rollback 已实装为 PROTECTED_TASK_TRANSITIONS 的一部分；由 `progress.py update --task Tn --status code-revising` 触发，apply_update_task 间接通过 `verification_result.md verification_status ∈ {fail, partial}` enable。本 skill pass 后只到 `code-review-passed`，fail retry 由 `development-code-write` 接手；事实源 `skills/_shared/dev_workflow/progress_state.py`。
