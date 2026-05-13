---
name: development-test-review
description: dev-workflow-skills2 Stage 4 Development test 评审 vertical skill。Task-bounded：仅在 progress.md current_stage==development 且目标 task_state==test-review 时被 invoke。评审本 task 的 tests/unit、tests/integration 与 detailed_design/SRS 的一致性，填写 docs/release<x.y>/development/tasks/T<n>/test_review_report.md 三态结果：review_status pass 或 fail。pass 时 findings_count/severity/blocking counts 必须一致且 blocking_findings_count==0，并调 progress.py update --task Tn --status test-done；fail 时调 progress.py update --task Tn --status test-revising。本 skill 不修改测试代码、不写 src、不调用全局 review-passed/review-issues event、不签发 approved。
authority: 4
references: []
---

# development-test-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**权威优先级**：第 4。

**职责（6 项）**：

1. 评审本 task 的测试代码质量与覆盖意图
2. 对照 `detailed_design.md`、SRS acceptance criteria、Architecture contracts 检查测试充分性
3. 填写 `test_review_report.md` 的 findings counts、severity_distribution、blocking_findings_count、max_severity
4. 设置 `review_status: pass` 或 `review_status: fail`（不保留 pending 作为终态）
5. pass 时调 `progress.py update --task Tn --status test-done`
6. fail 时调 `progress.py update --task Tn --status test-revising`，让 `development-test-write` 修订

**不属于本 skill**：

- 修改 `tests/`、`src/` 或 detailed_design（只能输出 findings）
- 创建 skeleton（→ `development-test-write`）
- 调全局 `progress.py update --event review-passed/review-issues`
- 写 `code_review_report.md` / `verification_result.md`
- 判定 Stage 4 done

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `development_state.task_states[Tn]` | `test-review` |
| `test_review_report.md` | 存在且 `review_status: pending`（正常入口） |

**允许的重试**：如果上次 review 失败后 write skill 已把 report 重置为 pending，并把 task 重新置 `test-review`，本 skill重新评审。

**task-level review_iteration 说明**：本 skill 不使用 global `review_iteration`（task-level 三态 report 循环不计入 workflow-protocol §8 Review Loop cap 7）；如果同一 task 反复 fail，需要 break loop 时按 §9 Recovery 升级人介入。

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

**拒绝入口**：

- report 缺失
- report 已是 `pass` 但 task 仍是 `test-review`（stale/corrupt；不要直接 test-done）
- task_state 不是 `test-review`

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | Coverage | 是否覆盖 detailed_design acceptance criteria 与 SRS edge cases？ | 核心 acceptance criteria 无测试 |
| 2 | Boundary / Error Cases | 是否覆盖空值、边界、错误路径、权限/状态异常？ | 关键 bug-prone path 未覆盖 |
| 3 | Fixture Isolation | fixture 是否隔离、可重复、不会依赖执行顺序？ | 测试间共享脏状态导致不稳定 |
| 4 | Mock 合理性 | mock 是否只隔离外部依赖，不掩盖被测逻辑？ | mock 掉核心逻辑，测试失真 |
| 5 | Assertion Quality | 断言是否验证行为而非实现细节；是否避免脆弱 snapshot？ | 断言不能捕捉实际 regression |
| 6 | Integration Contract | integration tests 是否覆盖跨模块/跨 task contract？ | 声明有 cross-task dependency 但无集成测试 |
| 7 | Bug Flow Regression | root_cause=development 时是否新增能复现 BUG 的 regression test？（详见 `development-test-write` §7）| BUG 未被测试覆盖 |

## 4. Output Contract（三态 report）

### 4.1 pass

`test_review_report.md` 必须更新为：

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

- 跑 `validate.py file test_review_report.md`
- 调 `skills/workflow-protocol/scripts/progress.py update --task Tn --status test-done`
- 对话输出 `development-test-review T<n> — pass`，可附 non-blocking suggestions

### 4.2 fail

`test_review_report.md` 必须更新为：

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

- 跑 `validate.py file test_review_report.md`
- 调 `skills/workflow-protocol/scripts/progress.py update --task Tn --status test-revising`
- 对话输出 findings markdown；`development-test-write` 消化后必须重置 report 为 pending

### 4.3 Finding 模板

```markdown
## development-test-review T<n> — fail

**Summary**: <critical> critical / <high> high / <medium> medium / <low> low

### Finding 1 [high, 维度 1: Coverage]
- **Where**: tests/unit/<file>
- **Issue**: <问题>
- **Recommendation**: <具体测试补充/修改建议>
```

## 5. Review Procedure（5 步）

```
Step 1. validate report skeleton
        - validate.py file test_review_report.md
        - 要求 review_status == pending；否则判 stale/corrupt

Step 2. 读上下文
        - detailed_design.md
        - SRS acceptance / Architecture contracts
        - tests diff/files for this task
        - file scope 以 detailed_design.md `Files / Modules to Touch` + breakdown.md task ownership map 为基准，可结合 git diff 取证 actual delta；跨 scope 改动列为 finding
        - BUG report（若 bug_flow.active）

Step 3. 按 §3 rubric 评审 tests
        - 可运行轻量测试/静态检查作为证据，但 runtime pass 不作为本阶段必须条件
        - 不修改文件，只记录 findings

Step 4. 填写 test_review_report.md
        - blocking findings → fail
        - 无 blocking → pass（medium/low 可作为建议）
        - status frontmatter 由 `skills/doc-guardian/scripts/status_transition.py` 最终同步；本 skill只写 owned report 内容字段
        - 不操作 Pending Changes / Change Log（test-review-report 是一次性 doc）

Step 5. validate + task transition
        - validate.py file test_review_report.md
        - pass: progress.py update --task Tn --status test-done
        - fail: progress.py update --task Tn --status test-revising
```

## 6. Stage Done Conditions（per-task test review）

`test-done` 转移的硬条件：

- `test_review_report.md` 存在
- `review_status == "pass"`
- `blocking_findings_count == 0`
- `validate.py file` exit 0

`pending` 和 `fail` 都不能转 `test-done`。这条规则防止 test-write 绕过 review skill。

**Stage 4 C 维度复合判定**：本 skill 贡献 test 子层（each task `test_review_report.md review_status: pass`）；它必须与 planning review-passed、code review pass 共同构成 workflow-protocol §5.1 Stage 4 C 维度。

## 7. Bug Flow Re-entry

当 BUG 是 development 根因且测试遗漏：

- 本 skill 必须检查 regression test 是否能描述/覆盖 BUG 复现步骤
- 如果测试只证明当前 happy path，而未覆盖 BUG path，输出 fail
- 如果 BUG 实际需要 code 修复，test review pass 后仍要进入 `development-code-write` Change Mode
- 如果 BUG 暴露 detailed_design 缺口，输出 fail 并要求 planning rewrite；不要把 design 问题压成 test issue

## 8. Forbidden Actions

- ❌ 修改测试代码或源代码
- ❌ 让 `review_status` 保持 pending 后调 `test-done`
- ❌ `review_status: pass` 但 `blocking_findings_count > 0`
- ❌ 调全局 `progress.py update --event review-passed` / `review-issues`
- ❌ 创建新的 review report 文件名或 per-stage report（必须 per-task）
- ❌ 输出 `approved`（Stage 4 无人 gate）
- ❌ 因 tests runtime fail 自动判 fail（代码尚未实现时 runtime fail 可能正常；本 skill评审测试质量）

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| skeleton 缺失 | 不创建；停止并要求 development-test-write 重建 pending skeleton |
| skeleton 不是 pending | 判 stale/corrupt；若 task 仍 test-review，要求 write skill 重置 pending |
| validate report fail | 修 owned report fields 后重跑；若 schema 不清，升级人介入 |
| `update --task test-done` 被拒 | 检查 review_status/pass/blocking count；不要手工改 progress |
| `update --task test-revising` 被拒 | 检查 task state 是否仍 test-review；若并发 agent 已推进，停止并 query |
| findings 争议 | 可在 test-review 状态内重评；一旦发出 task transition，history append-only，不撤销 |

## 10. References

- `skills/development-test-write/SKILL.md` — test write / skeleton owner
- `skills/workflow-protocol/SKILL.md` — Stage 4 task matrix
- `skills/workflow-protocol/references/command-reference.md` — `test-review -> test-done/test-revising`
- `skills/doc-guardian/references/frontmatter-schema.md` — test-review-report 三态不变量
- `skills/doc-guardian/references/required-artifacts.md` — Stage 4 per-task unconditional validation
- `skills/bug-triage/references/root-cause-rubric.md` — test omission 属 development 层

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：review report doc frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`；本 skill负责三态 review fields，helper 负责最终 status 同步策略；caller 显式传入 per-task report path。
