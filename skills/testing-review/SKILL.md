---
name: testing-review
description: dev-workflow-skills2 Stage 5 Testing 评审 vertical skill。在 progress.md current_stage==testing AND sub_state==in-review 时被 invoke。评审 testing/preparation.md、procedure.md、report.md，以及初次 fail/partial 时的 BUG-NNN.md skeleton 是否足以进入 bug-triage。输出两态 review-passed / issues-found；不产 review-report doc。testing-review 的 review-passed 只表示 Testing artifacts 合格；Stage 5 advance 仍要求 test-report.verification_status: pass；初次 fail/partial 触发 bug-triage active mode，active Bug Flow retest fail/partial 不重新 triage，后续由 testing-write/Bootstrap 调 bug-rework。本 skill 不修改 docs/tests/source，不判 root_cause，不调 bug-start/bug-rework/bug-close。
authority: 4
references: []
---

# testing-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**职责（6 项）**：

1. 读取 `docs/release<x.y>/testing/preparation.md` / `procedure.md` / `report.md`
2. 对三份 Testing docs 跑 `validate.py file`
3. 若初次 report fail/partial，验证 BUG skeleton 存在、root_cause 仍为 null、可交给 bug-triage；若 active retest fail/partial，验证 report 正确引用 active BUG
4. 按 Testing rubric 评审测试覆盖、执行记录、与 Acceptance Plan / SRS / Development outputs 的一致性
5. 输出 `review-passed` 或 `issues-found`（finding markdown 回对话，不写 review-report doc）
6. 调 `progress.py update --event review-passed` 或 `progress.py update --event review-issues`

**不属于本 skill**：

- 修改 Testing docs / BUG report / source code
- 判定 BUG `root_cause` 或调用 bug-triage/progress.py `bug-start`
- 调 `bug-close`（testing-write post-review submode owner）
- 判断 Stage 6 delivery 是否可启动（workflow-protocol advance owner）
- 直接编辑 `progress.md` / `progress-history.md`
- 输出 `approved`

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `testing` |
| `sub_state` | `in-review` |
| `workflow_incident_active` | `false` |
| `review_iteration` | 0-7 |

**典型路径**：

- `testing-write` write/revise/retest 完成后调 `update --event write-complete`
- Review fail 后由 `testing-write` 修订再重提
- Bug Flow retest 后仍走同一 review 流程

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | Artifact schema | preparation/procedure/report 是否路径、frontmatter、required fields 合规？ | validate fail |
| 2 | Acceptance traceability | procedure 是否覆盖 Acceptance Plan / Integration Plan 的验收点？ | 核心验收点未测试 |
| 3 | Environment fidelity | preparation 是否描述可复现的环境、数据、依赖、版本？ | 环境不可复现 |
| 4 | Execution evidence | report 是否列出执行命令、case 结果、失败证据？ | 结果不可审计 |
| 5 | Result honesty | verification_status 是否与 passed/failed counts 和 body 证据一致？ | pass/fail 与证据矛盾 |
| 6 | BUG readiness / linkage | 初次 fail/partial 时 BUG skeleton 是否存在、root_cause:null、target_release=found release、可 validate？active retest fail/partial 时是否引用当前 active BUG？ | 测试失败但无有效 BUG 或 active BUG 关联丢失 |
| 7 | No invented criteria | 是否临时发明 Acceptance Plan 外的新标准？ | 用未批准标准阻塞 release |

## 4. Output Contract

### 4.1 review-passed

允许三种 review-passed：

- **Testing pass**：report `verification_status: pass`；Stage 5 C/E 都满足，可由 caller `update --advance`（若无 active Bug Flow）或先 `bug-close`（若 active Bug Flow）
- **Initial testing fail but triage-ready**：`bug_flow.active==false` 且 report `fail|partial`，但 Testing docs 与 BUG skeleton 合格；C 满足，E 不满足，caller 必须 invoke bug-triage active mode，不得 advance
- **Active retest fail accurately recorded**：`bug_flow.active==true` 且 report `fail|partial`；C 可满足，E 不满足；caller 不得 re-triage 同一 active BUG，后续由 testing-write/Bootstrap 调 `progress.py bug-rework` 回 root_cause stage

动作：

- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`，`review_iteration → 0`
- doc status 由 `skills/doc-guardian/scripts/status_transition.py` 同步（Gap-2）

### 4.2 issues-found

- 至少一个 blocking finding
- 调 `progress.py update --event review-issues`
- progress.md：`sub_state: in-review → revising`，`review_iteration += 1`
- 控制权回 `testing-write`

## 5. Review Procedure（5 步）

```
Step 1. validate artifacts
        - validate.py file preparation.md / procedure.md / report.md
        - 若 report fail|partial，validate.py file BUG-NNN.md（testing-write 提供路径）

Step 2. read context
        - Acceptance Plan / SRS / Integration Plan
        - Development verified artifacts and verification_result.md
        - active BUG report if bug_flow.active

Step 3. apply rubric
        - 检查 traceability、evidence、counts、verification_status、BUG readiness / active retest linkage

Step 4. decide output
        - blocking finding → issues-found
        - no blocking → review-passed（即使 report fail，只要初次 fail triage-ready 或 active retest linkage-ready）

Step 5. progress event
        - pass: progress.py update --event review-passed
        - fail: progress.py update --event review-issues
```

## 6. Stage Done Conditions

| 维度 | 本 skill 贡献 |
|------|---------------|
| A | 间接确认 Testing artifacts 存在 |
| B | review 前 validate |
| C | 直接贡献 `review-passed` |
| D | 不适用 |
| E | 不贡献；由 `test-report.verification_status: pass` 决定 |

**关键规则**：review-passed 不等于 Stage 5 done。若 report fail/partial，workflow-protocol advance 必须拒绝；只有初次 fail/partial 才由 testing-write/Bootstrap invoke bug-triage。

更精确地说：初次 fail/partial（`bug_flow.active==false`）进入 bug-triage；active Bug Flow retest fail/partial（`bug_flow.active==true`）不重新 triage，由 testing-write/Bootstrap 调 `progress.py bug-rework`。

## 7. Bug Flow Re-entry

- fail/partial 初次测试：本 skill review-passed 只表示 BUG skeleton triage-ready；root_cause 由 bug-triage 判定。
- retest pass：本 skill review-passed 后，testing-write 调 `bug-close`，再由 caller advance。
- retest fail：若同一 active BUG 仍未修好，report fail/partial；本 skill 可 review-passed（报告诚实且证据充分）但不重新 triage active bug；由 testing-write/Bootstrap 调 `progress.py bug-rework`。

## 8. Forbidden Actions

- ❌ 修改 Testing docs / BUG report body / frontmatter
- ❌ 输出 `approved`
- ❌ 创建 review-report doc
- ❌ 因 report fail 自动 issues-found（初次 fail 且 BUG skeleton 完整时可 review-passed 进入 bug-triage；active retest fail 且 linkage 完整时可 review-passed 后调 bug-rework）
- ❌ 因 report pass 跳过 `validate.py file`
- ❌ 判定 root_cause 或调用 `bug-start` / `bug-rework` / `bug-close`
- ❌ 直接编辑 progress.md / progress-history.md 或撤销 progress-history
- ❌ 在 review_iteration > 7 时继续 issues-found update

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| validate fail | issues-found，finding 指向具体 doc/path/stderr |
| report fail/partial 但 BUG 缺失 | issues-found；初次 fail 由 testing-write 创建 BUG skeleton 后重提，active retest fail 则恢复/定位 active BUG |
| BUG root_cause 已非 null 且 bug_flow.active false | 可能是上次 bug-triage 中断；finding 指向 bug-triage idempotent retry |
| verification_status 与 counts/body 矛盾 | issues-found，testing-write 修 report |
| review_iteration 达 7 | progress.py 拒绝；升级人介入 |

## 10. References

- `skills/testing-write/SKILL.md`
- `skills/bug-triage/SKILL.md`
- `skills/workflow-protocol/SKILL.md` — Stage 5 P6 / Bug Flow
- `skills/workflow-protocol/references/command-reference.md` — update / bug-start / bug-rework / bug-close
- `skills/doc-guardian/references/frontmatter-schema.md` — test-report / bug-report schema
- `skills/doc-guardian/references/required-artifacts.md` — Stage 5 required artifacts

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 Testing review-passed 后发现 review 误判或 docs 仍需修订，不能撤销 history 或手工改 progress.md；需升级用户/Bootstrap 或等待 workflow-protocol 增加合法事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
- **Gap-5（已 closed by Task 6 Phase 6.2）**：active Bug Flow retest fail/partial 的合法回退命令 `progress.py bug-rework --bug <BUG-NNN.md>` 已实装；前置同 `testing-write` §10 Gap-5；apply_bug_rework 保持 active bug_flow 并把 `current_stage` 从 testing 切回 `bug_flow.root_cause` 对应 stage Change Mode（root_cause=development 时复用 `compute_dev_bug_rollback` 触发 affected-task rollback）。本 skill 可以确认 report 诚实并 review-passed，但不负责状态回退；后续由 testing-write/Bootstrap 调 bug-rework。本 skill 不重 triage、不调用 bug-start/bug-rework/bug-close；事实源 `skills/_shared/dev_workflow/progress_state.py`。
