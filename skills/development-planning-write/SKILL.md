---
name: development-planning-write
description: dev-workflow-skills2 Stage 4 Development planning 写作 vertical skill。在 progress.md current_stage==development 且 sub_state ∈ {write, revising} 时被 invoke；Bug Flow root_cause==development 时也可由 workflow-protocol 切回 Development Change Mode 后接管。负责 release 级 development plan / task breakdown，以及每个 task 的 detailed_design.md。Full Mode 一次性规划全部 task；Change Mode 仅修 planning-review findings 或 development bug 需要调整的 task/DAG。完成后必须对增量类 doc 执行 Pending Changes → changelog.py promote → validate.py，并调 progress.py update --event write-complete 交给 development-planning-review。本 skill 不写 tests/、不写 src/、不创建 test/code review report、不直接 mutation progress.md。
authority: 4
references: []
---

# development-planning-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；**实际 invocation 必须用完整路径**（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py`）。简写仅用于行内 prose / 表格密集处。

## 1. Authority & Scope

**权威优先级**：第 4（与其他 vertical stage skill / orchestration skill 同级；位于 `workflow-protocol` / `AGENTS.md` / `doc-guardian` 之后）。

**职责（6 项）**：

1. 产出 `docs/release<x.y>/development/plan.md`（release 级 development-plan）
2. 产出 `docs/release<x.y>/development/breakdown.md`（task-breakdown，声明 `T<n>`、依赖 DAG、执行顺序、并发边界）
3. 为每个 task 产出 `docs/release<x.y>/development/tasks/T<n>/detailed_design.md`
4. 在 Change Mode 中按 finding / BUG 只修相关 task、dependency、plan 条目，保留无关 task 历史
5. 对增量类 doc 维护 Pending Changes → `changelog.py promote` → Change Log，并跑 `validate.py file`
6. 调 `progress.py update --event write-complete` 进入 planning review；review pass 后由 `development-planning-review` 负责把 task 置为 `planning-done`

**不属于本 skill**：

- 评审 planning artifacts（→ `development-planning-review`）
- 写 `tests/` 或 `src/`（→ `development-test-write` / `development-code-write`）
- 创建或填写 `test_review_report.md` / `code_review_report.md` / `verification_result.md`
- 直接编辑 `progress.md` / `progress-history.md`（所有 mutation 必经 `skills/workflow-protocol/scripts/progress.py`）
- 自行把 task 推到 `test-writing`、`test-done`、`code-writing`、`verified` 等后续状态
- 推进 Stage 4 到 Stage 5（必须等 all task_states[Tn] == `verified` 后由 workflow-protocol `--advance` 判定）

## 2. When to Invoke

**触发条件（Full / planning revise）**：

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `development` |
| `sub_state` | `write` 或 `revising` |
| `development_state.task_states` | Full Mode 时为空 / 全部未设值；planning revise 时只允许影响尚未进入后续实现的 task，除非 Bug Flow 明确要求 |
| `bug_flow.active` | `false` |
| `workflow_incident_active` | `false` |

**触发条件（Bug Flow Development Change Mode）**：

| 字段 | 值 |
|------|-----|
| `bug_flow.active` | `true` |
| `bug_flow.root_cause` | `development` |
| `current_stage` | `development` |
| `sub_state` | `write`（由 `progress.py bug-start` 从 testing/review-passed 切回） |

**典型 invocation 路径**：

| 时机 | 上游 | 动作 |
|------|------|------|
| Stage 3 Architecture advance 后 | `progress.py update --advance` 设置 `current_stage=development, sub_state=write` | Full Mode 规划全部 development tasks |
| planning review issues-found | `development-planning-review` 调 `progress.py update --event review-issues`，转 `sub_state=revising` | Change Mode 修 plan / breakdown / detailed design |
| Stage 5 testing 判定 `root_cause=development` | `bug-triage` 调 `progress.py bug-start --root-cause development` | 读 BUG body 的 `Affected Task(s)`；决定是否需重规划，或直接路由到 test/code write |

**不被 invoke 的时机**：

- `current_stage != development`
- `sub_state ∈ {in-review, review-passed}` 且不是 planning-write owner 期
- task 已进入 `test-writing` 之后的普通实现流：后续由 task-bounded test/code skill 接管
- `bug_flow.active==true` 但 `root_cause != development`

**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。

## 3. Full Mode vs Change Mode

| Mode | 入口 | 主要工作 | task_state 影响 |
|------|------|----------|-----------------|
| Full Mode | Stage 4 首次 `sub_state=write` | 根据 PRD / SRS / Architecture 拆全部 task，生成 plan / breakdown / each detailed_design | 本 skill 不直接设 task state；review pass 后由 planning-review 调 `update --task Tn --status planning-done` |
| Planning Revise | planning-review 输出 issues-found 后 `sub_state=revising` | 按 findings 修 plan / breakdown / detailed_design | 不新增后续状态；review pass 后重新置相关 task `planning-done` |
| Bug Flow Replan | `bug_flow.root_cause==development` 且 BUG 无法精确定位 task，或修复需要新增/拆分 task | 更新 breakdown DAG、增加修复 task 或调整 existing task 的 detailed_design | 仅影响 BUG 涉及 task；不得回退无关 verified task |
| Bug Flow Direct Route | BUG 已标清 `Affected Task(s)` 且无需改 design | 在 plan / BUG note 中记录 routing decision，然后退出并让 Bootstrap 调 test/code write | 若 affected task 已在 `verified` / `code-review-passed`，由 `progress.py bug-start --bug <BUG path> --root-cause development` 自动 rollback（PROTECTED_TASK_TRANSITIONS + compute_dev_bug_rollback；Task 6 Phase 6.1 已实装），rollback 完成后再 Direct Route 到 test/code write |

**Bug Flow Replan 与 Direct Route 是平行二选一**：判别依据是 BUG body `Affected Task(s)` 是否完整、是否需要修 `detailed_design.md` / task split / DAG。需要改 design 或无法定位 task → Replan；不需改 design 且 affected task 已可被合法路由 → Direct Route。

**task ID 规则**：

- task id 统一为 `T<n>`（大写 T + 数字），在 `breakdown.md` 中首次声明
- `breakdown.md total_tasks` 必须等于 task 列表数量
- 每个 `detailed_design.md` frontmatter `task_id` 必须与路径 `tasks/T<n>/` 和 breakdown 条目一致
- 首次把 task 注册到 progress 的合法入口是 `progress.py update --task Tn --status planning-done`（由 planning-review 在 review-passed 后调用；事实源 command-reference Stage 4 task 转换表的“任意（首次设值）→ planning-done”）

## 4. Doc Output Contract

| Doc Type | 路径 | Frontmatter extra | Change Log |
|----------|------|-------------------|------------|
| `development-plan` | `docs/release<x.y>/development/plan.md` | `release: "<x.y>"` | 必须 |
| `task-breakdown` | `docs/release<x.y>/development/breakdown.md` | `release: "<x.y>"`, `total_tasks: <int>` | 必须 |
| `detailed-design` | `docs/release<x.y>/development/tasks/T<n>/detailed_design.md` | `release: "<x.y>"`, `task_id: T<n>` | 必须 |

**development-plan 最低章节**：

- Scope from SRS / Architecture
- Implementation Strategy
- Task Execution Policy（串行/并发边界）
- Cross-task Dependencies
- Risk / Rollback Notes
- Known Issues from BUG Flow（仅 Bug Flow Change Mode 时）
- Pending Changes / Change Log

**task-breakdown 最低章节**：

- Task Table（`T<n>`、title、owner skill group、status expectation）
- Task DAG（dependencies / blockers / parallelizable groups）
- Cross-task Interface Contracts
- Test Ownership Map（每个 task 对应 unit/integration test area）
- Code Ownership Map（预期 src/files/modules；允许后续 code-write 调整但须回写说明）
- Pending Changes / Change Log

**detailed_design.md 最低章节**：

- Task Goal / Non-goal
- Inputs from SRS / Architecture
- Design Decisions
- Files / Modules to Touch
- Test Strategy for This Task
- Acceptance Criteria
- Risks / Edge Cases
- Pending Changes / Change Log

## 5. 5-Step Standard Procedure

```
Step 1. 写/修 planning artifacts
        - 读 PRD / SRS / Architecture / architecture_delta（如有）
        - 写 plan.md + breakdown.md + each detailed_design.md
        - Change Mode 仅修改相关 task；不要重写无关 verified task

Step 2. 为增量类 doc 添加 Pending Changes
        - development-plan / task-breakdown / detailed-design 全部是增量类 doc
        - 每个实质修改必须有一条 Pending Changes
        - 新文件也写 Initial draft / Initial detailed design entry

Step 3. 跑 changelog.py promote
        - skills/doc-guardian/scripts/changelog.py promote <doc-path>
        - 对 plan.md / breakdown.md / each detailed_design.md 分别执行
        - promote 后 Pending Changes 必须为空

Step 4. 跑 validate.py file 自检
        - skills/doc-guardian/scripts/validate.py file <doc-path>
        - 对所有 planning artifacts 分别执行
        - detailed_design 的 frontmatter / path / Change Log 格式必须通过；task_id 与 breakdown/progress 的跨文件一致性由后续 progress.py/consistency 校验承担

Step 5. 提交 planning review
        - skills/workflow-protocol/scripts/progress.py update --event write-complete
        - current_stage 保持 development；sub_state: write/revising → in-review
        - 控制权移交 development-planning-review
```

**关键约束**：

- `progress.py update --event write-complete` 不自动 validate；本 skill 必须先显式跑 Step 4
- `validate.py file` 只跑 doc-guardian file-level 校验（class 1-7），不校验 `task_id` 是否已在 `progress.md development_state.task_states` 中；class 8 consistency 由 `validate.py consistency` / `progress.py update --advance` 在 task 注册后兜底
- `progress.py update --task Tn --status planning-done` 的实现必须原子校验 `detailed_design.md` 已存在，且 `task_id` 与路径 `tasks/Tn/`、`breakdown.md` task table 一致；不要为通过 file-level validate 手工预填 progress.md
- planning review-passed 只代表 plan/breakdown/detailed design 被评审通过；**不代表 Stage 4 可 advance**

## 6. Stage Done Conditions（Stage 4 中的 planning 部分）

本 skill 贡献 Stage 4 的 A/B/C 起点，但不贡献 E：

| 维度 | 本 skill 贡献 | 完整判定 |
|------|---------------|----------|
| A. 必需 artifacts | 写 `plan.md` / `breakdown.md` / each `detailed_design.md` | Stage 4 advance 时还要求 each task 的 test/code review report + verification_result |
| B. doc-guardian | 对 planning artifacts 跑 `validate.py file` | workflow-protocol advance 时再对全部 Stage 4 artifacts double-safety |
| C. Review 通过 | 由 `development-planning-review` 输出 review-passed | test/code review 也必须通过；test/code 使用三态 report |
| D. 人确认 | 不适用 | Stage 4 非 gated |
| E. 内部验证 | 不适用 | 由 `development-code-write` 在 verification submode 写 `verification_result.md` |

Stage 4 done 的唯一最终条件：`all development_state.task_states[Tn] == "verified"`。

## 7. Bug Flow Re-entry

当 `bug_flow.root_cause==development` 时，本 skill 是 Development Change Mode 的第一判断点：

1. 读 `bug_flow.bug_report_path` 指向的 `docs/bug/BUG-NNN.md`
2. 确认 BUG frontmatter `root_cause: development`（若不一致，停止并让 bug-triage/progress.py 恢复）
3. 读 BUG body `## Triage Analysis` 中的 `Affected Task(s)`（当前 schema 不注册 `task_id` frontmatter；若未来新增，frontmatter 与 body 必须一致）
4. 决策：
   - **只需改测试** → 路由 `development-test-write` Change Mode（task 回到 / 保持 `test-revising`）
   - **只需改代码** → 路由 `development-code-write` Change Mode（task 回到 / 保持 `code-revising`）
   - **需改 detailed_design / task split / dependency DAG** → 本 skill 先改 planning artifacts，再交 planning-review
   - **无法定位 task** → 本 skill 更新 breakdown，新增或重划分修复 task
5. 不关闭 Bug Flow；修复后必须回 Stage 5 retest，由 `progress.py bug-close` 退出

若 BUG 的 affected task 当前已是 `verified`（Stage 5 testing 发现 development bug 的常见情形）或 `code-review-passed`（少量中断/重试场景），由 `progress.py bug-start --bug <BUG path> --root-cause development` 在原子 transaction 内自动 rollback 到 `test-revising` 或 `code-revising`（PROTECTED_TASK_TRANSITIONS + compute_dev_bug_rollback；Task 6 Phase 6.1 实装；事实源 `skills/_shared/dev_workflow/progress_state.py`）。本 skill 不必也不应手工改 progress.md；rollback 完成后再做 Replan 或 Direct Route。

## 8. Forbidden Actions

- ❌ 直接编辑 `progress.md` / `progress-history.md`
- ❌ 跳过 `validate.py file` 或 `changelog.py promote` 调 `progress.py update --event write-complete`
- ❌ 写 `tests/` / `src/` 或创建 review report skeleton
- ❌ 在 `sub_state==in-review` 时继续修改 planning artifacts（必须等 review-issues 转 revising）
- ❌ 把未评审的 task 设为 `planning-done`（只有 planning-review pass 后可调 `update --task Tn --status planning-done`）
- ❌ 因单个 BUG 回退/重写无关 verified task
- ❌ 自行推进到 Stage 5（Stage 4 done 由 all task verified 判定）
- ❌ 输出 `approved`（Stage 4 无人 gate）

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| `changelog.py promote` 失败 | 修 Pending Changes / Change Log 章节格式后重跑 |
| `validate.py file` 失败 | 按 stderr 修 frontmatter / path / cross-reference；3 次仍失败升级人介入 |
| `progress.py update --event write-complete` 拒绝 | 查 progress state；若不在 development write/revising，停止并让 Bootstrap 重路由 |
| planning-review 连续 issues-found 达 7 次 | progress.py 第 8 次会拒绝；升级人介入 |
| BUG `Affected Task(s)` 缺失或多 task 冲突 | 由本 skill 先补 breakdown/DAG decision；不要猜测直接改代码 |
| Change Mode 发现 SRS/Architecture 已不支持当前 plan | 停止并输出 upstream mismatch；需要用户决定是否触发 srs/architecture Change Mode，不能在 Stage 4 擅改上游 doc |

## 10. References

**Cross-skill 强依赖**：

- `skills/workflow-protocol/SKILL.md` — §5.2 Stage 4 task-level 判定、§10 并发模型
- `skills/workflow-protocol/references/command-reference.md` — `update --event` / `update --task` 转换表
- `skills/doc-guardian/SKILL.md` — validate / changelog 入口
- `skills/doc-guardian/references/frontmatter-schema.md` — development-plan / task-breakdown / detailed-design schema
- `skills/doc-guardian/references/directory-layout.md` — Stage 4 per-task 路径
- `skills/doc-guardian/references/change-log-format.md` — 增量类 doc 清单
- `skills/development-planning-review/SKILL.md` — planning review 接管点
- `skills/bug-triage/SKILL.md` — development root cause 的 task body 标注

**项目级 references**：

- `docs/workflow/workflow_specification_claude.md`
- `docs/design/skill_set_design_proposal_v0.5.md`

**Design Gaps / Implementation Notes**：

- **Gap-2 沿用**：doc frontmatter `status` mutation owner = `skills/doc-guardian/scripts/status_transition.py`；Stage 4 task 内部 doc 也必须在 progress event 成功后显式传入 per-task doc path 调用 helper 同步 status。
- **Task registration note（v0.6 batch 3b M2）**：`planning-done` 是 task 首次注册入口。`validate.py file` 不负责校验 task 是否已在 progress.md 注册；Task 6 实现 `progress.py update --task Tn --status planning-done` 时必须原子校验 `breakdown.md` / `detailed_design.md` / path 中的 task_id 一致，避免手工预填 progress.md。
- **Gap-4（已 closed by Task 6 Phase 6.1）**：Bug Flow `root_cause==development` 切回 Stage 4 时，`progress.py bug-start --bug <BUG path> --root-cause development` 已实装解析 BUG body `## Triage Analysis` `**Affected Task(s)**` + classification keyword（`test-only` / `source-code` / 等）的能力，按 PROTECTED_TASK_TRANSITIONS 自动执行 `verified → test-revising` / `verified → code-revising` / `code-review-passed → code-revising` rollback。事实源 `skills/_shared/dev_workflow/progress_state.py` 的 `PROTECTED_TASK_TRANSITIONS` + `compute_dev_bug_rollback`。
