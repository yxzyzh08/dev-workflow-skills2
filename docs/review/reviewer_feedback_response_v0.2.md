# Reviewer Feedback Response — Proposal v0.2

**Source Review**: `docs/review/skill_set_design_proposal_v0.2_rereview.md`
**Adopted In**: `docs/design/skill_set_design_proposal_v0.3.md`
**Workflow Spec Update**: `docs/workflow/workflow_specification_claude.md` (v0.2 → v0.3)
**Date**: 2026-05-05
**Reviewed By**: User + Claude

---

## Findings 处置一览

| # | Severity | Finding 摘要 | 处置 | 备注 |
|---|----------|---------------|------|------|
| F1 | High | 23-skill 与 spec "One Stage Skill" 冲突 | **采纳** | workflow spec v0.3 加 reconciliation：logical vs physical skill |
| F2 | High | S4 vs closed-release 矛盾 | **采纳 (B)** | 用户裁决：S4 仅 active release 期间允许；post-close bug 等下次 S2 |
| F3 | High | S3 必备 artifact 没正式 type | **采纳** | 加 `source-system-analysis` type + `analysis_kind` enum |
| F4 | Medium | review-passed vs approved 术语混用 | **采纳** | 全文规范化；review skill 输出绝不用 "approved" |
| F5 | Medium | progress.md 示例自相矛盾 | **采纳** | 修示例：`release: "0.3"`、`previous_releases: ["0.1","0.2"]`、`sub_state: in-review` |
| F6 | Medium | 缺 `release-start` 命令 | **采纳** | 加 `progress.py release-start --version <x.y>` 子命令 |
| F7 | Medium | code-review-report 缺 pass/fail contract | **采纳** | 加 `review_status: pass\|fail`、`blocking_findings_count`、`max_severity` |
| F8 | Low | script 路径 shorthand 残留 | **采纳** | normalize 全文 |

8 项全部采纳，无反驳。

## 用户裁决（F2）

S4 严格只在 active release 期间触发。Release close 后，新发现的 bug 报告会留在 `docs/bug/` 目录，frontmatter `target_release: null`，等下次 S2 release 启动时由 srs-write skill 扫描合并到新 SRS。

理由：

- 与"Release 严格串行"哲学一致
- 模型最简：1 时 1 个 active release，所有变更进 active
- 无版本号特例（不引入 `0.1.1` 之类）
- 接受代价：紧急 bug 没快速通道

## v0.2 → v0.3 主要修改

| 文件 | 变化 |
|------|------|
| `docs/workflow/workflow_specification_claude.md` | 状态 v0.2 → v0.3；Section 3 "One Stage Skill" 改 "One Logical Stage Skill"；Section 5 加物理实现说明；Change Log 加 v0.3 entry |
| `docs/design/skill_set_design_proposal_v0.3.md` | 新文件，应用全部 8 项 fix |
| `docs/design/skill_set_design_proposal_v0.2.md` | 保留作为历史 |

## v0.3 关键变化点

1. **F1 reconciliation**：design 提案 Section 3 加 "Logical vs Physical Skills" 注；workflow spec 同步更新
2. **F2 S4 policy (B)**：4.5.2 决策树修正为"closed release + 需修 bug → 必须先 S2 启动新 release"；4.12 加 "S4 active-release-only" 规则；progress schema 加 `unresolved_bugs` 字段
3. **F3 source-system-analysis type**：5.3 frontmatter schema 加新 type，含 `analysis_kind: prd-level|srs-level|module-level|reuse-replace|technical-debt|feature-matrix` enum；目录布局相应调整
4. **F4 terminology cleanup**：所有 review skill 输出从 "approved" 改 "review-passed"；P6 矩阵 C 维描述更新；Stage 4 task state 描述更新
5. **F5 sample fix**：progress.md 示例改为内部一致（active release `0.3`、previous `["0.1","0.2"]`、sub_state `in-review`）
6. **F6 release-start command**：scripts/progress.py 加子命令；含 serial 校验（拒绝同时启动多个 active）
7. **F7 code review contract**：`code-review-report` frontmatter 加 `review_status`、`blocking_findings_count`、`max_severity`；Stage 4 `code-review-passed` 判定要求 `review_status: pass + blocking_findings_count: 0`
8. **F8 path normalization**：全文 grep 替换 `scripts/<x>.py` → `skills/<skill>/scripts/<x>.py`

## 没有采纳的项

无。8 项全部采纳。
