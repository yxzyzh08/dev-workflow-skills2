---
name: delivery-review
description: dev-workflow-skills2 Stage 6 Delivery 评审 vertical skill。在 progress.md current_stage==delivery AND sub_state==in-review 时被 invoke。评审 deployment.md、operation_manual.md、installation_result.md，要求安装/部署验证结果 pass 才能 review-passed；fail/partial 必须 issues-found 回 delivery-write 修复或升级。输出两态 review-passed / issues-found；不产 review-report doc，不调 bug-triage，不关闭 release。
authority: 4
references: []
---

# delivery-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**职责（5 项）**：

1. 读取 Delivery 三份 docs：deployment、operation_manual、installation_result
2. 跑 `validate.py file` 自检
3. 按 Delivery rubric 评审部署可执行性、运维完整性、安装结果证据
4. 输出 `review-passed` 或 `issues-found`
5. 调 `progress.py update --event review-passed` 或 `review-issues`

**不属于本 skill**：

- 修改 Delivery docs body/frontmatter
- 执行部署命令或重跑安装验证
- 创建 BUG report / 调 bug-triage
- 调 release-close
- 直接编辑 `progress.md` / `progress-history.md`
- 输出 `approved`

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `delivery` |
| `sub_state` | `in-review` |
| `bug_flow.active` | `false` |
| `review_iteration` | 0-7 |

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | Schema / required docs | 3 docs 是否存在且 validate pass？ | 缺 doc / validate fail |
| 2 | Deployment executability | deployment.md 步骤是否可按顺序执行，配置/依赖明确？ | 部署步骤不可执行 |
| 3 | Rollback / recovery | 是否有回滚、失败恢复、版本确认？ | 无回滚路径且风险高 |
| 4 | Operation readiness | operation_manual 是否含监控、告警、常见故障、日常操作？ | 交付后无法运维 |
| 5 | Installation evidence | installation_result 是否列命令、环境、结果、健康检查？ | 结果不可审计 |
| 6 | Verification pass | installation_result `verification_status` 是否为 pass？ | fail/partial 一律 blocking |
| 7 | Upstream mismatch | 是否暴露 SRS/Architecture/Development/Testing 上游问题？ | 上游问题未升级，试图在 delivery 掩盖 |

## 4. Output Contract

### 4.1 review-passed

条件：无 blocking finding，且 `installation_result.verification_status: pass`。

- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`，`review_iteration → 0`
- caller/Bootstrap 可调 `progress.py update --advance` 进入 project-retrospective

### 4.2 issues-found

条件：任一 blocking finding，尤其 installation_result fail/partial。

- 调 `progress.py update --event review-issues`
- progress.md：`sub_state: in-review → revising`，`review_iteration += 1`
- findings 交给 delivery-write 修复

## 5. Review Procedure（5 步）

```
Step 1. validate docs
        - deployment.md / operation_manual.md / installation_result.md

Step 2. read context
        - testing/report.md（必须 pass）
        - deployment targets / release artifacts

Step 3. apply §3 rubric
        - 特别检查 installation_result verification_status == pass

Step 4. decide output
        - fail/partial installation result → issues-found
        - no blocking → review-passed

Step 5. progress event
        - pass: progress.py update --event review-passed
        - fail: progress.py update --event review-issues
```

## 6. Stage Done Conditions

| 维度 | 本 skill 贡献 |
|------|---------------|
| A | 间接确认 docs 存在 |
| B | review 前 validate |
| C | 直接贡献 review-passed |
| D | 不适用 |
| E | 仅当 installation_result pass 时才 review-passed，配合 workflow-protocol E 维度 |

## 7. Bug Flow Re-entry

Delivery review 不启动 Bug Flow。若发现产品 bug 或验收标准问题：

- 输出 issues-found；finding 标注 suspected upstream stage。
- 要求 delivery-write 升级用户/Bootstrap 决策。
- 不创建 BUG report，不调用 bug-triage。

## 8. Forbidden Actions

- ❌ installation_result fail/partial 时 review-passed
- ❌ 修改 docs 或运行部署命令
- ❌ 调 bug-triage / bug-start / bug-close
- ❌ 调 release-close
- ❌ 直接编辑 progress.md / progress-history.md
- ❌ 输出 `approved`
- ❌ 创建 review-report doc
- ❌ review_iteration > 7 时继续 issues-found update

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| validate fail | issues-found，delivery-write 修 |
| installation_result fail/partial | issues-found；delivery-write 修部署/环境或升级 upstream |
| testing report 不是 pass | issues-found；不应进入 delivery，要求 Bootstrap 停止并升级状态异常；不要手工回 testing |
| progress update 拒绝 | query state；若非 delivery/in-review，重新路由 |
| review_iteration 达 7 | 升级人介入 |

## 10. References

- `skills/delivery-write/SKILL.md`
- `skills/workflow-protocol/SKILL.md` — Stage 6 P6
- `skills/doc-guardian/references/frontmatter-schema.md` — delivery schemas
- `skills/doc-guardian/references/required-artifacts.md` — Stage 6 required docs

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 Delivery review-passed 后发现 review 误判或 docs 仍需修订，不能撤销 history 或手工改 progress.md；需升级用户/Bootstrap 或等待 workflow-protocol 增加合法事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
