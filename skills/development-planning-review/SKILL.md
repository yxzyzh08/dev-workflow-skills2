---
name: development-planning-review
description: dev-workflow-skills2 Stage 4 Development planning 评审 vertical skill。在 progress.md current_stage==development AND sub_state==in-review 时被 invoke，评审 development plan / task breakdown / per-task detailed_design.md。输出两态 review-passed / issues-found；不产独立 review-report doc（三态 review report 仅 development-test-review / development-code-review 使用）。review-passed 后调 progress.py update --event review-passed，并对每个 task 调 progress.py update --task Tn --status planning-done；issues-found 时调 progress.py update --event review-issues 回到 development-planning-write Change Mode。本 skill 不修改 doc body、不写 tests/src、不直接 mutation progress.md。
authority: 4
references: []
---

# development-planning-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py`）。

## 1. Authority & Scope

**权威优先级**：第 4（与其他 vertical stage skill / orchestration skill 同级）。

**职责（6 项）**：

1. 读取 `development/plan.md`、`development/breakdown.md` 与每个 `tasks/T<n>/detailed_design.md`
2. 先跑 `validate.py file <doc-path>` 自检，确保评审对象格式合法
3. 按 planning rubric 评审 task 切分、依赖 DAG、与 SRS/Architecture 的一致性、test/code ownership 可执行性
4. 输出 `review-passed` 或 `issues-found`（finding markdown 回对话，不写 review-report doc）
5. `review-passed` 时调 `progress.py update --event review-passed`，再逐 task 调 `progress.py update --task Tn --status planning-done`
6. `issues-found` 时调 `progress.py update --event review-issues`，让 `development-planning-write` Change Mode 修订

**不属于本 skill**：

- 修改 planning docs body 或 frontmatter（finding 交给 write skill）
- 评审测试代码 / 源代码（→ `development-test-review` / `development-code-review`）
- 创建 `test_review_report.md` / `code_review_report.md`
- 运行 verification 或写 `verification_result.md`
- 签发 `approved`（Stage 4 无人 gate）

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `sub_state` | `in-review`（normal review）或 `review-passed`（retry 入口；见下方 Reentry 入口） |
| `development_state.task_states` | Full planning review 时为空 / 全部未设值；Bug Flow replan 时仅相关 task 可被重新声明 |
| `review_iteration` | 0-7 |
| `workflow_incident_active` | `false` |

**典型路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| planning-write 首次完成 | `development-planning-write` 调 `progress.py update --event write-complete` | 评审全部 planning artifacts |
| planning-write revise 后重提 | `development-planning-write` 再次 write-complete | 回归评审上一轮 findings |
| Bug Flow Replan 后 | `development-planning-write` 修改 task/DAG/detailed_design | 评审 BUG 是否被 planning change 覆盖 |
| task registration retry | 已成功 `review-passed` 但部分 task 未成功置 `planning-done` | 仅重试未注册 task 的 `progress.py update --task Tn --status planning-done`，不重发 review-passed |

**Reentry 入口（partial task registration retry）**：当 `sub_state==review-passed` 但 `development_state.task_states` 与 `breakdown.md` task table 不完整时，本 skill 可被重 invoke；此时只 retry 未注册 task 的 `progress.py update --task Tn --status planning-done`，不重新业务评审、不重发 `review-passed` event。

**不被 invoke 的时机**：

- `sub_state` 不在 `{in-review, review-passed}`，或 `sub_state==review-passed` 但不满足 Reentry 入口条件
- task 已进入 `test-writing` 之后的 test/code review；不回头评审 planning，除非 Bug Flow 或 explicit planning issues
- `bug_flow.active==true` 且 `root_cause != development`

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | 上游一致性 | 每个 task 是否可追溯到 SRS acceptance criteria 和 Architecture decision？ | task 实现目标与 SRS/Architecture 冲突 |
| 2 | task 粒度 | task 是否足够小、边界清楚、可独立测试/评审？ | task 过大到无法 task-bounded review |
| 3 | 依赖 DAG | `breakdown.md` 是否列出跨 task 依赖和并发限制？ | 有依赖但未声明，可能导致并发 agent 冲突 |
| 4 | detailed design 可执行性 | 每个 task 是否包含 files/modules、test strategy、acceptance criteria？ | 缺核心执行信息，test/code skill 无法接手 |
| 5 | test/code ownership | 每个 task 是否声明 tests/ 与 src/ 预期范围？ | 无法判断 test/code write 的 bounded scope |
| 6 | Change Log discipline | 增量类 docs 是否 Pending 已 promote，Change Log 与改动一致？ | Change Log 缺失或与 body 改动不一致 |
| 7 | Bug Flow 覆盖 | root_cause=development 时 BUG 的 Affected Task(s) 是否被 planning change 覆盖？ | BUG 未定位/未被任何 task 覆盖 |

**Severity 规则**：任一 blocking finding → `issues-found`；仅 medium/low 建议可 `review-passed`，但建议仍在对话输出。

## 4. Output Contract

### 4.1 review-passed

- 对话输出：`development-planning-review iteration <N> — review-passed`
- 可列 non-blocking suggestions，但不得阻塞
- 调用：`skills/workflow-protocol/scripts/progress.py update --event review-passed`
- 成功后由 `skills/doc-guardian/scripts/status_transition.py`（Gap-2）同步 planning docs frontmatter `status: review-passed`
- 随后对 `breakdown.md` 中每个 task 调：`skills/workflow-protocol/scripts/progress.py update --task Tn --status planning-done`
- 如果重 invoke 时发现 global `sub_state==review-passed` 且只有部分 task 已 `planning-done`，跳过业务评审和 `review-passed` event，仅按 `breakdown.md` task table retry 未注册 task；已是 `planning-done` 的 task 视为幂等成功
- 每个 task 成功置为 `planning-done` 后，Bootstrap / downstream 可调 `development-test-write` 把 task 推到 `test-writing`

### 4.2 issues-found

- 对话输出 markdown findings；不写 review-report doc
- 调用：`skills/workflow-protocol/scripts/progress.py update --event review-issues`
- progress.md：`sub_state: in-review → revising`，`review_iteration += 1`
- 控制权回 `development-planning-write` Change Mode

### 4.3 Finding 模板

```markdown
## development-planning-review iteration <N> — issues-found

**Summary**: <B> blocking / <M> medium / <L> low

### Finding 1 [blocking, 维度 3: 依赖 DAG]
- **Where**: docs/release<x.y>/development/breakdown.md §<section>
- **Issue**: <问题>
- **Recommendation**: <具体修改建议>
```

## 5. Review Procedure（5 步）

```
Step 1. 发现 artifact 清单
        - 读 docs/release<x.y>/development/breakdown.md 的 task table
        - 枚举每个 T<n>/detailed_design.md
        - 若 breakdown 与目录不一致 → issues-found

Step 2. validate.py file 自检
        - plan.md / breakdown.md / each detailed_design.md 全部跑 validate.py
        - 任一 fail → 直接 issues-found（guardian failure）

Step 3. 读上游与 Bug Flow context
        - 读 PRD / SRS / Architecture / architecture_delta
        - 若 bug_flow.active==true，读 BUG-NNN.md Triage Analysis

Step 4. 按 §3 逐维度评审
        - 每个 finding 标 severity / 维度 / where / recommendation
        - 对 previous iteration findings 做回归确认

Step 5. 发状态机事件
        - pass: progress.py update --event review-passed；然后逐 task update --task Tn --status planning-done
        - retry: 若 sub_state 已 review-passed 且 task 注册不完整，仅 retry 未 planning-done task，不重发 review-passed
        - fail: progress.py update --event review-issues
```

**顺序约束**：必须先 `review-passed` 记录 planning review 通过，再置 task `planning-done`。不要先置 task，再发现全局 plan 仍有 blocking finding。

## 6. Stage Done Conditions（planning review 贡献）

| 维度 | 本 skill 贡献 | 说明 |
|------|---------------|------|
| A | 间接 | 确认 planning artifacts 存在 |
| B | 间接 | review 前跑 validate |
| C | 直接 | 记录 development-planning-review `review-passed`；并把 task 置 `planning-done` |
| D | 不适用 | Stage 4 无人 gate |
| E | 不适用 | verification 由 code-write 后置完成 |

Stage 4 不能因 planning review-passed 就 advance；必须等 test/code/verification 全部完成。

**Stage 4 C 维度复合判定**：Stage 4 的 Review 通过 = 本 skill 输出 global `review-passed` + each task `test_review_report.md review_status: pass` + each task `code_review_report.md review_status: pass`。本 skill 仅贡献 planning 子层；完整条件见 workflow-protocol §5.2。

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

## 7. Bug Flow Re-entry

当 `bug_flow.root_cause==development`：

- 如果 planning-write 决定需重规划，本 skill 必须检查 BUG 的现象是否被新的 task / detailed design 覆盖
- 如果 BUG 涉及多个 task，本 skill 检查 DAG 与 cross-task interface 是否明确
- 如果 BUG 实际暴露 SRS/Architecture 问题，本 skill输出 blocking finding，要求升级到对应 stage；不得在 development 层偷偷改上游事实
- review-passed 后仍不关闭 Bug Flow；关闭只能在 Stage 5 retest pass 后由 `progress.py bug-close` 完成

## 8. Forbidden Actions

- ❌ 修改 planning docs body / frontmatter
- ❌ 创建任何 review-report doc（planning review 不产三态 report）
- ❌ 输出 `approved` / `pass` / `fail` 作为 planning review 术语（仅 `review-passed` / `issues-found`）
- ❌ 跳过 `validate.py file` 直接业务评审
- ❌ 先置 task `planning-done` 后再记录 review-passed
- ❌ 把未在 breakdown.md 声明的 task 置为 `planning-done`
- ❌ 在 `review_iteration > 7` 时继续 issues-found update
- ❌ 因 BUG 修复回退无关 verified task

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| validate 失败 | 输出 guardian failure finding；由 planning-write 修 |
| `progress.py update --event review-passed` 失败 | 查 state；若已非 in-review，停止并让 Bootstrap 重路由 |
| 某个 `update --task Tn --status planning-done` 失败 | 停止后续 task update；报告具体 Tn；不要手工补 progress.md。重 invoke 时若 sub_state 已 `review-passed`，按 §5 Step 5 retry 未注册 task，跳过已 `planning-done` task |
| breakdown 与 task dirs 不一致 | issues-found；要求 planning-write 修 breakdown / 目录 |
| review_iteration 达 7 | 升级人介入；该 cap 仅适用 planning global review loop，test/code task-level review 不使用 global review_iteration |
| BUG 标注的 task 不存在 | issues-found；planning-write 必须新增 task 或修 BUG routing note |

## 10. References

- `skills/development-planning-write/SKILL.md` — planning artifact owner
- `skills/workflow-protocol/SKILL.md` — Stage 4 task-level 判定
- `skills/workflow-protocol/references/command-reference.md` — `update --event` / `update --task` 合法转换
- `skills/doc-guardian/references/frontmatter-schema.md` — planning doc schema
- `skills/doc-guardian/references/required-artifacts.md` — Stage 4 required artifacts
- `skills/doc-guardian/references/change-log-format.md` — planning docs 属于增量类
- `skills/bug-triage/SKILL.md` — development root cause task body 标注
- `docs/design/skill_set_design_proposal_v0.5.md`

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：planning docs frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`；caller 在 `progress.py update --event <name>` 成功后调用 `skills/doc-guardian/scripts/status_transition.py apply --event <name> --doc <path> ...`。Task-aware 场景通过显式传入 per-task doc path 实现。
- **Task registration note（v0.6 batch 3b M2）**：`update --task Tn --status planning-done` 是 task 首次设值入口；`validate.py file` 不负责校验 task 是否已在 progress.md 注册。实现必须在 progress.py task transition 内保证 breakdown / detailed_design / path / progress task key 原子一致。
