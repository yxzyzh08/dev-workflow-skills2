---
name: delivery-write
description: dev-workflow-skills2 Stage 6 Delivery 写作 vertical skill。在 progress.md current_stage==delivery AND sub_state ∈ {write, revising} 时被 invoke。负责写 delivery/deployment.md、operation_manual.md、installation_result.md，并执行安装/部署验证，installation-result.verification_status 必须记录 pass/fail/partial。完成后 validate 三份 one-shot docs 并调 progress.py update --event write-complete 交给 delivery-review。本 skill 不进入 Bug Flow、不修上游 baseline、不直接 mutation progress.md。
authority: 4
references: []
---

# delivery-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**职责（6 项）**：

1. 写 `docs/release<x.y>/delivery/deployment.md`（deployment-doc）
2. 写 `docs/release<x.y>/delivery/operation_manual.md`（operation-manual）
3. 执行安装/部署验证并写 `docs/release<x.y>/delivery/installation_result.md`（installation-result）
4. 对三份 Delivery docs 跑 `validate.py file`
5. 调 `progress.py update --event write-complete` 进入 `delivery-review`
6. review issues-found 后按 findings 修 Delivery docs / installation result

**不属于本 skill**：

- 评审 Delivery docs（→ `delivery-review`）
- 修改 source code、tests、SRS、Architecture、Testing docs
- 创建 BUG report 或调用 bug-triage（Bug Flow 入口仅 Stage 5 testing）
- 关闭 release（Stage 7 retrospective 后 `release-close`）
- 直接编辑 progress.md / progress-history.md
- 输出 `approved`

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `delivery` |
| `sub_state` | `write` 或 `revising` |
| `bug_flow.active` | `false` |
| `workflow_incident_active` | `false` |

**典型路径**：

- Stage 5 Testing `update --advance` 后进入 delivery/write
- delivery-review issues-found 后进入 delivery/revising

**不被 invoke 的时机**：

- `current_stage != delivery`
- `sub_state==in-review`（delivery-review owner）
- `sub_state==review-passed`（caller应 advance 到 retrospective）
- `bug_flow.active==true`（必须先回 testing retest + bug-close）

## 3. Full Mode vs Change Mode

| Mode | 入口 | 主要工作 |
|------|------|----------|
| Full Mode | Stage 6 首次 `sub_state=write` | 写部署/运维/安装结果，执行验证 |
| Review Revise | `sub_state=revising` | 按 delivery-review findings 修 docs 或重跑安装验证 |
| Upstream mismatch escalation | 发现问题源于 SRS/Architecture/Development/Testing | 停止并升级人介入；不在 Stage 6 自行改上游 |

**重要边界**：Stage 6 安装失败通常由本 skill 修部署文档、环境步骤或安装流程后重测。若发现产品实现或验收标准本身错误，当前 spec 没有 Stage 6 专属 Bug Flow 或 rollback command；必须升级用户/Bootstrap 决策（如 release close 后 post-close bug-intake，或先经 design cycle 增加 dedicated rollback），不要在 delivery-write 里绕过状态机。

## 4. Doc Output Contract

| Doc Type | 路径 | Frontmatter extra | Change Log |
|----------|------|-------------------|------------|
| `deployment-doc` | `docs/release<x.y>/delivery/deployment.md` | `release: "<x.y>"` | 不需要 |
| `operation-manual` | `docs/release<x.y>/delivery/operation_manual.md` | `release: "<x.y>"` | 不需要 |
| `installation-result` | `docs/release<x.y>/delivery/installation_result.md` | `release`, `verification_status: pass|fail|partial` | 不需要 |

Delivery docs 是一次性 doc（事实源 `change-log-format.md` §1），不需要 Pending Changes / Change Log。

**installation_result.md body 最低内容**：

- Environment / host / runtime versions
- Commands run
- Deployment artifact versions
- Installation result summary
- Smoke checks / health checks
- Failures and rollback notes（如 verification_status fail/partial）

## 5. Standard Procedure

```
Step 1. 读前置事实源
        - Testing report must be pass
        - Deployment target assumptions / release artifacts / operation requirements

Step 2. 写 Delivery docs
        - deployment.md: 部署步骤、配置、rollback plan
        - operation_manual.md: 日常运维、监控、告警、常见故障
        - installation_result.md: 实际执行结果 + verification_status

Step 3. 执行安装/部署验证
        - verification_status: pass only when installation + smoke checks pass
        - fail/partial: 记录失败证据；不要 advance

Step 4. validate docs
        - validate.py file deployment.md / operation_manual.md / installation_result.md
        - 不跑 changelog.py promote（一次性 doc）

Step 5. submit review
        - progress.py update --event write-complete
        - 控制权交 delivery-review
```

## 6. Stage Done Conditions

| 维度 | 判定 | 本 skill 贡献 |
|------|------|---------------|
| A | deployment.md + operation_manual.md + installation_result.md 存在 | 直接写 |
| B | 三份 docs validate pass | 直接自检；advance double-safety |
| C | delivery-review 输出 review-passed | 间接 |
| D | 不适用 | Stage 6 非 gated |
| E | `installation-result.verification_status: pass` | 直接执行验证并写 result |

`verification_status: fail|partial` 时，delivery-review 应输出 issues-found（不同于 testing fail 可 review-passed 进入 bug-triage），让本 skill修复 Delivery docs/安装流程或升级人介入。

## 7. Bug Flow Re-entry

Stage 6 不启动 active Bug Flow：

- 若安装验证失败是部署/环境/运维文档问题 → 本 skill revise。
- 若安装验证暴露产品 bug → 停止并升级用户/Bootstrap；不要直接创建 active BUG（bug-triage active mode gate 要求 current_stage==testing）。
- 若必须记录产品 bug，当前 spec 不提供 delivery → testing 的合法 rollback transition；可升级用户/Bootstrap 决策：release close 后走 post-close `bug-intake`，或先经 design cycle 增加 dedicated rollback。本 skill 不自创 bypass。

## 8. Forbidden Actions

- ❌ 调 bug-triage / bug-start / bug-close
- ❌ installation_result fail/partial 时调 `update --advance`
- ❌ 跳过 validate 直接 write-complete
- ❌ 对 one-shot Delivery docs 添加/维护 Change Log（不需要）
- ❌ 修改 SRS / Architecture / Development / Testing artifacts
- ❌ 直接编辑 progress.md / progress-history.md
- ❌ 输出 `approved`
- ❌ 关闭 release

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| validate fail | 修 doc/frontmatter/path 后重跑 |
| installation fail due environment/doc | 修 deployment/operation docs，重跑验证，重提 review |
| installation fail due product bug | 停止并升级用户/Bootstrap；不要在 delivery 内创建 active BUG |
| delivery-review issues-found | sub_state revising；按 findings 修后重提 |
| progress.py write-complete 拒绝 | query 当前 state；若不在 delivery write/revising，重新路由 |
| review_iteration 达 7 | 升级人介入 |

## 10. References

- `skills/delivery-review/SKILL.md`
- `skills/workflow-protocol/SKILL.md` — Stage 6 P6
- `skills/workflow-protocol/references/command-reference.md` — update / advance
- `skills/doc-guardian/references/frontmatter-schema.md` — delivery doc schemas
- `skills/doc-guardian/references/required-artifacts.md` — Stage 6 required artifacts
- `skills/doc-guardian/references/change-log-format.md` — one-shot Delivery docs

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 Delivery docs 在 review-passed 后、advance 到 retrospective 前被发现需要修订，不能手工编辑 progress.md；需升级用户/Bootstrap 或等待 workflow-protocol 增加合法事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
- **Stage 6 upstream rollback note**：当前 command-reference 没有 Stage 6 → upstream rollback command；若 delivery 暴露产品 bug，必须升级用户/Bootstrap 走合法 workflow，不得手工改 progress.md。
