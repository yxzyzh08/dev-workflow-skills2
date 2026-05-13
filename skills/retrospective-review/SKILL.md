---
name: retrospective-review
description: dev-workflow-skills2 Stage 7 Project Retrospective 评审 vertical skill。在 progress.md current_stage==project-retrospective AND sub_state==in-review 时被 invoke。评审 docs/retrospective/retrospective.md 当前 release section 的完整性、证据追溯、issue classification、improvement proposals 与递归悖论合规。输出 review-passed / issues-found；不产 review-report doc，不调 release-close，不修改 retrospective body。
authority: 4
references: []
---

# retrospective-review

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**职责（5 项）**：

1. 读取 `docs/retrospective/retrospective.md`
2. 跑 `validate.py file` 自检
3. 评审当前 release section 的完整性、证据、分类、actionability
4. 输出 `review-passed` 或 `issues-found`
5. 调 `progress.py update --event review-passed` 或 `review-issues`

**不属于本 skill**：

- 修改 retrospective body/frontmatter
- 调 `release-close`
- 调 workflow-evolution retrospective consumption
- 修改 dev-workflow-skills2 自身文件
- 直接编辑 `progress.md` / `progress-history.md`
- 输出 `approved` 或 patch/diff

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `project-retrospective` |
| `sub_state` | `in-review` |
| `bug_flow.active` | `false` |
| `workflow_incident_active` | `false` |
| `review_iteration` | 0-7 |

## 3. Review Rubric Overview

| # | 维度 | 关键问题 | Blocking 条件 |
|---|------|----------|---------------|
| 1 | Schema / Change Log | retrospective.md validate pass？Pending Changes 已 promote？ | validate fail / pending 未清 |
| 2 | Release coverage | 当前 release stages、decisions、outcomes 是否覆盖？ | 漏关键 stage / release outcome |
| 3 | Evidence traceability | BUG/INCIDENT/progress-history/review loops 是否可追溯？ | 关键结论无证据 |
| 4 | Issue classification | AI capability / workflow / skill / docs / token waste / no-action 分类是否合理？ | 分类混乱导致 action 不可执行 |
| 5 | Improvement actionability | proposal 是否有 owner/target/next action？ | 建议空泛不可执行 |
| 6 | Recursion compliance | 是否试图直接 patch dev-workflow-skills2 或修改自身 workflow？ | 输出 patch/diff 或直接改 skill 集 |
| 7 | Upstream boundary | 是否试图在 retrospective 中修改 PRD/SRS/Architecture baseline？ | 越权修改上游 baseline |

## 4. Output Contract

### 4.1 review-passed

- 无 blocking finding
- 调 `progress.py update --event review-passed`
- progress.md：`sub_state: in-review → review-passed`，`review_iteration → 0`
- caller/Bootstrap 可调 `progress.py release-close`

### 4.2 issues-found

- 任一 blocking finding
- 调 `progress.py update --event review-issues`
- progress.md：`sub_state: in-review → revising`，`review_iteration += 1`
- findings 交给 retrospective-write 修

## 5. Review Procedure（5 步）

```
Step 1. validate retrospective.md
        - validate.py file docs/retrospective/retrospective.md

Step 2. read release context
        - progress-history.md
        - BUG/INCIDENT reports
        - Testing/Delivery outcomes
        - review history if available

Step 3. apply rubric
        - 特别检查 evidence traceability + recursion compliance

Step 4. decide output
        - blocking → issues-found
        - no blocking → review-passed

Step 5. progress event
        - pass: progress.py update --event review-passed
        - fail: progress.py update --event review-issues
```

## 6. Stage Done Conditions

| 维度 | 本 skill 贡献 |
|------|---------------|
| A | 间接确认 retrospective.md 存在 |
| B | review 前 validate |
| C | 直接贡献 review-passed |
| D | 不适用 |
| E | 不适用 |

Stage 7 review-passed 后 release-close 前置满足；本 skill 不自行 close release。

## 7. Workflow Evolution Boundary

- Review 可要求 retrospective-write 补充 workflow improvement proposals。
- Review 不调用 workflow-evolution；workflow-evolution retrospective consumption 是用户主动 advisory mode。
- 如果 retrospective 中建议改 dev-workflow-skills2，必须是自然语言 advisory + Action Item，不得是 patch/diff。
- 若 review-passed 后用户想把 workflow-evolution advisory 持久化回同一 retrospective section，当前缺 `review-passed → revising` 事件；本 skill 不撤销 review-passed，需升级用户/Bootstrap 或延后到下一 release。

## 8. Forbidden Actions

- ❌ 修改 retrospective.md
- ❌ 调 `progress.py release-close`
- ❌ 调 workflow-evolution
- ❌ 直接编辑 progress.md / progress-history.md
- ❌ 输出 `approved`
- ❌ 输出 patch / diff / unified diff
- ❌ 创建 review-report doc
- ❌ 在 review_iteration > 7 时继续 issues-found update
- ❌ 因 retrospective finding 直接修改 PRD/SRS/Architecture/Development/Testing/Delivery artifacts

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| validate fail | issues-found，finding 指向 validate stderr |
| release section 缺关键 evidence | issues-found，retrospective-write 补 BUG/progress references |
| improvement proposal 空泛 | issues-found，要求 owner/target/action item |
| 发现 patch/diff | issues-found，要求改为 advisory 自然语言建议 |
| progress update 拒绝 | query state；若已 review-passed，不重发 event |
| review_iteration 达 7 | 升级人介入 |

## 10. References

- `skills/retrospective-write/SKILL.md`
- `skills/workflow-evolution/SKILL.md` — advisory retrospective consumption mode
- `skills/workflow-protocol/references/command-reference.md` — release-close preconditions
- `skills/doc-guardian/references/frontmatter-schema.md` — retrospective schema
- `skills/doc-guardian/references/change-log-format.md` — retrospective Change Log

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 Retrospective review-passed 后发现 review 误判或需要补写 advisory，不能撤销 history 或手工改 progress.md；需升级用户/Bootstrap 或等待 workflow-protocol 增加合法事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
