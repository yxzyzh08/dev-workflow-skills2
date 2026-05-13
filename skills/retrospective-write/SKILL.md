---
name: retrospective-write
description: dev-workflow-skills2 Stage 7 Project Retrospective 写作 vertical skill。在 progress.md current_stage==project-retrospective AND sub_state ∈ {write, revising} 时被 invoke。负责维护项目级单文件 docs/retrospective/retrospective.md，每个 release 增量加节，分析本 release 的 bug、incident、workflow gap、skill/template gap、token waste 与 no-action findings。Retrospective 是增量类 doc，必须 Pending Changes → changelog.py promote → validate.py。完成后调 progress.py update --event write-complete 交给 retrospective-review。本 skill 不调用 release-close、不直接修改 dev-workflow-skills2 自身、不输出 patch/diff。
authority: 4
references: []
---

# retrospective-write

> **Path Convention Note**：本 skill 文档为可读性使用 `progress.py` / `validate.py` / `changelog.py` 简写指代脚本；实际 invocation 必须用完整路径。

## 1. Authority & Scope

**职责（6 项）**：

1. 维护 `docs/retrospective/retrospective.md` 项目级单文件（frontmatter `type: retrospective`）
2. 为当前 release 增量追加/修订 retrospective section
3. 汇总 PRD/SRS/Architecture/Development/Testing/Delivery 的主要事件、BUG、INCIDENT、review loops、token waste
4. 输出 workflow / skill / template improvement proposals（自然语言建议，不是 patch）
5. 维护 Pending Changes → `changelog.py promote` → Change Log
6. validate 后调 `progress.py update --event write-complete` 交给 retrospective-review

**不属于本 skill**：

- 评审 retrospective（→ `retrospective-review`）
- 调 `release-close`（workflow-protocol / Bootstrap 在 review-passed 后执行）
- 修改 PRD / SRS / Architecture / Development / Testing / Delivery artifacts
- 修改 dev-workflow-skills2 自身 skill 文件（递归悖论；只能提出 advisory）
- 调 workflow-evolution（retrospective consumption mode 是用户主动可选）
- 直接编辑 progress.md / progress-history.md
- 输出 `approved`

## 2. When to Invoke

| 字段 | 值 |
|------|-----|
| `project_state` | `active` |
| `release_state` | `active` |
| `current_stage` | `project-retrospective` |
| `sub_state` | `write` 或 `revising` |
| `bug_flow.active` | `false` |
| `workflow_incident_active` | `false` |

**典型路径**：

- Stage 6 Delivery advance 后进入 project-retrospective/write
- retrospective-review issues-found 后进入 revising

**不被 invoke 的时机**：

- `current_stage != project-retrospective`
- `sub_state==in-review`（retrospective-review owner）
- `sub_state==review-passed`（caller可 release-close）
- `release_state==closed`（历史 release 只读；新建议走后续 release）

## 3. Full Mode vs Change Mode

| Mode | 入口 | 主要工作 |
|------|------|----------|
| Full Mode for release section | Stage 7 首次 `sub_state=write` | 首个 release 创建 retrospective.md；后续 release 追加当前 release section |
| Review Revise | `sub_state=revising` | 按 review findings 修当前 release section |
| Advisory persistence | 用户想持久化 workflow-evolution advisory | 仅在 Stage 7 合法 `write/revising` 入口中把自然语言建议纳入 retrospective section；不 patch skill 集 |

## 4. Doc Output Contract

| Doc Type | 路径 | Frontmatter extra | Change Log |
|----------|------|-------------------|------------|
| `retrospective` | `docs/retrospective/retrospective.md` | universal fields only | 必须 |

Retrospective 是项目级单文件，每 release 增量加节。Issue Analysis Report / Workflow Improvement Proposal / Skill Improvement Proposal / Template Improvement Proposal / Token Optimization Proposal 都是该单文件内部章节，不是独立 doc。

首个 release 进入 Stage 7 时，本 skill 创建 `retrospective.md`（universal frontmatter + 第一个 release section + `## Pending Changes` + `## Change Log` skeleton）；后续 release 只在同一文件追加/修订当前 release section。

**当前 release section 最低内容**：

- Release Summary（scenario / scope / major decisions）
- Stage Timeline（key progress-history events）
- Bug / Incident Summary（BUG IDs, root causes, outcome）
- Review Loop Summary（iterations and recurring finding patterns）
- Issue Analysis by Dimension
  - AI Capability Limitation
  - Workflow Defect
  - Skill Gap
  - Documentation Gap
  - Token Waste
  - No-action Finding
- Improvement Proposals（workflow / skill / template / token optimization）
- Action Items（owner, target, whether advisory only）

## 5. 5-Step Standard Procedure

```
Step 1. 读全 release context
        - progress-history.md
        - PRD/SRS/Architecture/Development/Testing/Delivery artifacts
        - BUG reports for this release
        - INCIDENT reports if any
        - review reports / review markdown history if available

Step 2. 写/修 retrospective.md 当前 release section
        - 保留历史 release sections，只追加/修当前 release section
        - 不修改其他 stage artifacts

Step 3. 添加 Pending Changes
        - retrospective 是增量类 doc
        - 每个 release section 新增/修订都必须有 Pending Changes entry

Step 4. changelog promote + validate
        - changelog.py promote docs/retrospective/retrospective.md
        - validate.py file docs/retrospective/retrospective.md

Step 5. submit review
        - progress.py update --event write-complete
        - 控制权交 retrospective-review
```

## 6. Stage Done Conditions

| 维度 | 判定 | 本 skill 贡献 |
|------|------|---------------|
| A | `docs/retrospective/retrospective.md` 存在 | 直接写 |
| B | validate pass | 直接自检；advance/release-close double-safety |
| C | retrospective-review 输出 review-passed | 间接 |
| D | 不适用 | Stage 7 非 gated |
| E | 不适用 | Retrospective 无 verification artifact |

Stage 7 review-passed 后 release close 条件成立；本 skill 不直接 close release。

## 7. Workflow Evolution Boundary

- 本 skill 写 retrospective report，本身不执行 workflow-evolution retrospective consumption mode。
- 用户可在 retrospective review-passed 后主动 invoke `workflow-evolution`，获得 advisory 自然语言建议。
- 如果要把 advisory 持久化到 retrospective.md，应由 retrospective-write Change Mode 写入当前 release section，并再次 review；但当前 spec 缺 `review-passed → revising` 事件，review-passed 后同 release 持久化必须先由用户/Bootstrap 升级决策（见 Gap-1），不得手工改 progress.md。
- 任何针对 dev-workflow-skills2 自身的改进只能作为 Action Item / advisory，必须走独立 design proposal review cycle；本 skill不输出 patch/diff。

## 8. Forbidden Actions

- ❌ 调 `progress.py release-close`
- ❌ 修改 dev-workflow-skills2 自身 skill/reference/script 文件
- ❌ 输出 patch / diff / unified diff 作为 workflow 改进落地
- ❌ 把 Issue Analysis / Improvement Proposal 写成独立 doc type
- ❌ 跳过 Pending Changes / changelog.py promote
- ❌ 修改历史 closed release section，除非用户明确要求勘误并记录 Change Log
- ❌ 直接编辑 progress.md / progress-history.md
- ❌ 输出 `approved`

## 9. Recovery on Failure

| 失败模式 | 修复路径 |
|----------|----------|
| changelog promote fail | 修 Pending Changes / Change Log 章节后重跑 |
| validate fail | 修 frontmatter/path/Change Log 后重跑 |
| retrospective-review issues-found | sub_state revising；按 findings 修当前 release section |
| 发现上游 doc 缺信息 | 在 retrospective 记录 documentation gap；不要回改上游 closed artifacts |
| workflow-evolution advisory 需要持久化 | 用户确认后在 retrospective-write Change Mode 纳入 advisory，不直接 patch skill 集 |
| progress update 拒绝 | query state；若 release closed，不改历史 release，转后续 release advisory |

## 10. References

- `skills/retrospective-review/SKILL.md`
- `skills/workflow-evolution/SKILL.md` — optional retrospective consumption mode
- `skills/workflow-protocol/SKILL.md` — Stage 7 / release close
- `skills/workflow-protocol/references/command-reference.md` — release-close preconditions
- `skills/doc-guardian/references/frontmatter-schema.md` — retrospective schema
- `skills/doc-guardian/references/required-artifacts.md` — Stage 7 required artifact
- `skills/doc-guardian/references/change-log-format.md` — retrospective is incremental

**Design Gaps / Notes**：

- **Gap-1 沿用**：`review-passed → revising` 转移缺失。若 retrospective review-passed 后还想把 workflow-evolution advisory 持久化到同一 release section，当前没有合法 reentry event；需升级用户/Bootstrap、延后到下一 release，或等待 workflow-protocol 增加事件。
- **Gap-2 沿用**：frontmatter status mutation owner = `skills/doc-guardian/scripts/status_transition.py`。
