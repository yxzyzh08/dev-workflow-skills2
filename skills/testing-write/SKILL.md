---
name: testing-write
description: dev-workflow-skills2 Stage 5 Testing 写作 vertical skill。在 progress.md current_stage==testing 且 sub_state ∈ {write, revising} 时写 testing preparation/procedure/report 并执行测试；在 review-passed reentry 中处理初次 fail/partial 的 BUG skeleton → bug-triage、Bug Flow retest pass 的 bug-close、retest fail/partial 的 bug-rework。本 skill 不判 root_cause、不调 bug-start/incident-start、不直接 mutation progress.md。
authority: 4
references: []
---

# testing-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；实际 invocation 必须用完整路径（`skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py`）。

## 1. Authority & Scope

**权威优先级**：第 4（vertical stage skill；位于 `workflow-protocol` / `doc-guardian` 之后）。

**职责（7 项）**：

1. 写 `docs/release<x.y>/testing/preparation.md`（test-preparation）
2. 写 `docs/release<x.y>/testing/procedure.md`（test-procedure）
3. 执行测试并写 `docs/release<x.y>/testing/report.md`（test-report，含 `verification_status`）
4. 初次测试 fail/partial 时创建 `docs/bug/BUG-NNN.md` skeleton（frontmatter `root_cause: null`）；active retest fail/partial 时只更新 report 并引用 active BUG
5. 对 Testing docs 跑 `validate.py file`；对 BUG report 跑 Pending Changes → `changelog.py promote` → `validate.py file`
6. 调 `progress.py update --event write-complete` 进入 `testing-review`
7. review-passed 后按 test-report + bug_flow 结果：初次 fail/partial → invoke `bug-triage` active mode；Bug Flow retest pass → 调 `progress.py bug-close`；Bug Flow retest fail/partial → 调 `progress.py bug-rework`

**不属于本 skill**：

- 评审 Testing docs（→ `testing-review`）
- 判定 BUG root cause 或调用 `bug-start` / `incident-start`（→ `bug-triage`）
- 修 SRS / Architecture / Development / Delivery artifact
- 直接编辑 `progress.md` / `progress-history.md`
- 在 non-testing 阶段创建 active BUG report
- 输出 `approved`（Stage 5 无人 gate）

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `testing` |
| `sub_state` | `write` / `revising` / `review-passed` |
| `workflow_incident_active` | `false` |

**Reentry 入口**：`sub_state==review-passed` 只允许 §5.2 Case A/B/C 三种 post-review routing；否则本 skill 不应被 invoke。

**典型路径**：

| 时机 | 上游 | 本 skill 行为 |
|------|------|--------------|
| Stage 4 advance 后 | `progress.py update --advance` 设置 `current_stage=testing, sub_state=write` | Full Mode 写 testing docs + 执行测试 |
| testing-review issues-found | `testing-review` 调 `update --event review-issues` | Change Mode 修 testing docs / report |
| 初次测试 fail/partial 且 review-passed | Bootstrap 重新 invoke testing-write bug routing submode | 确认 BUG skeleton 存在并 invoke `bug-triage` active mode |
| Bug Flow 修复后返回 testing | upstream stage advance 回 testing | Retest Mode 重测并更新 report |
| Bug Flow retest pass 且 review-passed | Bootstrap 重新 invoke testing-write bug-close submode | 调 `progress.py bug-close`；caller 随后可 `update --advance` 到 delivery |

**不被 invoke 的时机**：

- `current_stage != testing`
- `sub_state==in-review`（由 `testing-review` 接管）
- `sub_state==review-passed` 但既没有初次 fail/partial routing、active Bug Flow retest pass close、active Bug Flow retest fail/partial bug-rework 动作
- `workflow_incident_active==true`（由 `workflow-evolution` 接管）

## 3. Full Mode / Change Mode / Bug Flow Retest

| Mode | 入口 | 主要工作 | progress 影响 |
|------|------|----------|---------------|
| Full Mode | Stage 5 首次 `sub_state=write` | 写测试准备、步骤、执行测试、写 report | `write-complete` → review |
| Review Revise | `sub_state=revising` | 按 testing-review findings 修 docs/report；必要时重跑测试 | `write-complete` → review |
| Bug Routing | `sub_state=review-passed`, `bug_flow.active=false`, report fail/partial | 确认 BUG skeleton，invoke `bug-triage` active mode | bug-triage 调 `bug-start` / `incident-start` |
| Retest | `bug_flow.active==true`, current_stage 回 testing | 重跑 BUG regression / relevant acceptance tests，更新 report | `write-complete` → review |
| Bug Close | `bug_flow.active==true`, report pass, sub_state review-passed | 调 `progress.py bug-close` | bug_flow 清空；caller 可 advance |
| Retest Rework | `bug_flow.active==true`, report fail/partial, sub_state review-passed | 不 close、不重新 triage；报告 active BUG 仍失败 | `progress.py bug-rework --bug <active BUG>` |

**Bug Close safety note**：`sub_state==review-passed` 是本 skill 的 caller-side safety net。`progress.py bug-close` 自身的事实源前置仍以 command-reference 为准：`bug_flow.active==true`、`current_stage==testing`、最新 test-report pass。

**Stage 5 特例**：testing-review 可以在 `test-report.verification_status: fail|partial` 时输出 `review-passed`，前提是 report 准确记录失败且 BUG skeleton / active BUG linkage 合规。初次 fail/partial 时，这样满足 bug-triage active mode 的 gate（`current_stage==testing AND sub_state==review-passed`）；active Bug Flow retest fail/partial 时则调用 `progress.py bug-rework` 回 root-cause stage。这两种情况都不表示 Stage 5 done；E 维度仍因 report fail/partial 阻止 advance。

## 4. Doc Output Contract

| Doc Type | 路径 | Frontmatter extra | Change Log |
|----------|------|-------------------|------------|
| `test-preparation` | `docs/release<x.y>/testing/preparation.md` | `release: "<x.y>"` | 不需要 |
| `test-procedure` | `docs/release<x.y>/testing/procedure.md` | `release: "<x.y>"` | 不需要 |
| `test-report` | `docs/release<x.y>/testing/report.md` | `release`, `verification_status`, `total_test_cases`, `passed`, `failed` | 不需要 |
| `bug-report`（初次 fail/partial 时）| `docs/bug/BUG-NNN.md` | `bug_id`, `found_in_release`, `target_release`, `root_cause`, `consumed_in_release` | 必须 |

Testing 三份 doc 是一次性 doc（事实源 `change-log-format.md` §1），不需要 `## Pending Changes` / `## Change Log`。BUG report 是增量类 doc，必须有 Pending Changes / Change Log，并在 invoke bug-triage 前 promote + validate。

**BUG skeleton frontmatter（active mode）**：

```yaml
---
title: BUG-<NNN> <short title>
type: bug-report
status: draft
created: <ISO8601 UTC>
updated: <ISO8601 UTC>
owner: <agent_id>/testing-write
bug_id: BUG-<NNN>
found_in_release: "<x.y>"
target_release: "<x.y>"
root_cause: null
consumed_in_release: null
---
```

## 5. Standard Procedure

### 5.1 Write / Revise / Retest Procedure

```
Step 1. 读上游事实源
        - SRS + Acceptance Plan + Integration Plan（如有）
        - Architecture / architecture_delta
        - Development plan/breakdown + each verified task artifacts
        - Bug Flow retest 时读 active BUG report + fix artifacts

Step 2. 写/修 Testing docs 并执行测试
        - preparation.md：环境、数据、依赖、工具、版本
        - procedure.md：test cases / steps / expected results，必须追溯 Acceptance Plan
        - report.md：执行结果 + verification_status: pass|fail|partial

Step 3. 处理 fail/partial
        - 初次 fail/partial：创建 BUG skeleton，新 BUG ID 必须 3 位 zero-padded
        - 初次 BUG root_cause 保持 null（bug-triage owner）
        - 初次 BUG 添加 Pending Changes entry，changelog.py promote，validate.py file
        - active BUG retest fail/partial：不要创建新 BUG，更新 report 并引用 active BUG

Step 4. validate Testing docs
        - validate.py file preparation.md / procedure.md / report.md
        - Testing docs 不跑 changelog.py promote（一次性 doc）

Step 5. submit review
        - progress.py update --event write-complete
        - 控制权交 testing-review
```

### 5.2 Post-review Routing Procedure

```
Case A. sub_state==review-passed, bug_flow.active==false, test-report fail|partial
        - 确认 BUG-NNN.md 存在且 validate.py file exit 0
        - invoke bug-triage active mode（bug-triage 负责 root_cause + bug-start/incident-start）
        - 本 skill 不调用 bug-start

Case B. sub_state==review-passed, bug_flow.active==true, test-report pass
        - progress.py bug-close
        - caller/Bootstrap 随后调 progress.py update --advance 到 delivery

Case C. sub_state==review-passed, bug_flow.active==true, test-report fail|partial
        - 不调用 bug-close
        - 不创建新 BUG、不 invoke bug-triage（active BUG 已有 root_cause）
        - 调 progress.py bug-rework --bug <progress.md bug_flow.bug_report_path>
        - 若脚本尚未实现或前置不满足，停止并升级用户/Bootstrap；不得手工回 root_cause stage
```

## 6. Stage Done Conditions

| 维度 | 判定 | 本 skill 贡献 |
|------|------|---------------|
| A | preparation.md + procedure.md + report.md 存在 | 直接写 |
| B | 三份 Testing docs `validate.py file` pass | 直接自检；advance double-safety |
| C | testing-review 输出 `review-passed` | 间接，交 review skill |
| D | 不适用 | Stage 5 非 gated |
| E | `test-report.verification_status: pass` | 直接执行测试并写 report |

若 `verification_status: fail|partial`：Stage 5 不 done；初次 fail/partial 在 review-passed 后进入 bug-triage active mode，active Bug Flow retest fail/partial 调 `progress.py bug-rework`。

## 7. Bug Flow Re-entry

Stage 5 是 Bug Flow 的入口和出口：

- **入口**：初次测试 fail/partial → testing-write 创建 BUG skeleton → testing-review review-passed → testing-write/Bootstrap invoke bug-triage active mode。
- **出口**：root_cause 修复完成后返回 testing → testing-write retest → testing-review review-passed → testing-write 调 `progress.py bug-close`。
- `prd-exception` incident continue 后回到 testing/review-passed；若原问题仍需修复，按 workflow-evolution 规则创建新 BUG，不复用 prd-exception BUG。

## 8. Forbidden Actions

- ❌ 判定或写入 BUG `root_cause`（bug-triage owner）
- ❌ 跳过 BUG report `changelog.py promote` / `validate.py file` 直接 invoke bug-triage
- ❌ 在 `sub_state != review-passed` 时 invoke bug-triage active mode（bug-start gate 会拒绝）
- ❌ 调 `progress.py bug-start` / `incident-start`（bug-triage owner）
- ❌ 在 retest pass 前调 `progress.py bug-close`
- ❌ `test-report verification_status: fail|partial` 时调 `update --advance`
- ❌ 直接编辑 progress.md / progress-history.md
- ❌ 因测试失败直接修改 SRS/Architecture/Development 文档或代码
- ❌ 输出 `approved`

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| Testing doc validate fail | 修 doc/frontmatter/path 后重跑 validate |
| BUG ID 冲突 | 扫描 `docs/bug/BUG-*.md` 取下一个 3 位 ID；重命名并重跑 validate |
| BUG report validate fail | 修 BUG frontmatter / Change Log / body 后重跑；不要 invoke bug-triage |
| testing-review issues-found | sub_state 转 revising；修 docs/report 后重提 |
| bug-triage 拒绝 active mode | 检查 current_stage/testing + sub_state review-passed + BUG root_cause null/set 状态；不要绕过 gate |
| bug-close 拒绝 | 确认 `bug_flow.active==true` 且最新 test-report pass；不手工清 bug_flow |
| active Bug Flow retest 仍 fail/partial | 不重开 triage、不手工回 root_cause stage；调 `progress.py bug-rework --bug <active BUG>`；若命令拒绝则按 stderr 修前置或升级人介入 |
| 测试发现 Acceptance Plan 不完整 | 创建 BUG skeleton；review-passed 后由 bug-triage 判 root_cause=srs，不在 testing-write 自行改 SRS |

## 10. References

- `skills/testing-review/SKILL.md` — review owner
- `skills/bug-triage/SKILL.md` — active bug triage owner
- `skills/workflow-protocol/SKILL.md` — Stage 5 P6 + Bug Flow
- `skills/workflow-protocol/references/command-reference.md` — `update --event`, `bug-start`, `bug-rework`, `bug-close`
- `skills/doc-guardian/references/frontmatter-schema.md` — test / bug report schemas
- `skills/doc-guardian/references/required-artifacts.md` — Stage 5 required artifacts
- `skills/doc-guardian/references/change-log-format.md` — one-shot testing docs vs incremental bug-report
- `docs/design/skill_set_design_proposal_v0.5.md`

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 Testing docs 在 review-passed 后、advance/bug-routing/bug-close 前被发现需要修订，不能手工编辑 progress.md；需升级用户/Bootstrap 或等待 workflow-protocol 增加合法事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`；Testing docs / BUG doc status 由 helper 或 owning orchestration flow 同步；helper 调用使用 `apply --event <event> --doc <path> ...`。
- **Gap-5（已 closed by Task 6 Phase 6.2）**：active Bug Flow retest fail/partial 的合法回退命令 `progress.py bug-rework --bug <BUG-NNN.md>` 已实装。前置：`bug_flow.active==true`、`current_stage==testing`、`sub_state==review-passed`、最新 test-report `verification_status: fail|partial`、`<BUG>` 等于 `bug_flow.bug_report_path`、BUG frontmatter `root_cause == bug_flow.root_cause ∈ {srs, architecture, development}`。mutation：保持 `bug_flow.active/bug_report_path/root_cause` 不变，`current_stage: testing → <root_cause stage>`，`sub_state: review-passed → write`，`review_iteration → 0`，append `bug-rework` history；root_cause=development 时 apply_bug_rework 同步执行 Gap-4 affected-task rollback（与 bug-start 共用 `compute_dev_bug_rollback`）。事实源 `skills/_shared/dev_workflow/progress_state.py` `apply_bug_rework` + `skills/workflow-protocol/scripts/progress.py` `cmd_bug_rework`。命令拒绝时按 stderr 修前置或升级人介入，不手工绕过状态机。
