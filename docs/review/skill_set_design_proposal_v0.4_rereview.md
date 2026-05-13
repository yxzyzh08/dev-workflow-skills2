# Skill Set Design Proposal v0.4 Re-review

**Review Target**: `docs/design/skill_set_design_proposal_v0.4.md`  
**Previous Review**: `docs/review/skill_set_design_proposal_v0.3_rereview.md`  
**Feedback Response**: `docs/review/reviewer_feedback_response_v0.3.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.4)  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: v0.3 的 High findings 已基本修复；v0.4 剩余问题集中在 Bug/Incident 状态退出语义与少量文档一致性

## Findings

### Medium: Active Bug Flow 缺少确定性的 route / close state mutation，`bug_flow.active` 可能无法退出

- **Location**: `docs/design/skill_set_design_proposal_v0.4.md:244`, `docs/design/skill_set_design_proposal_v0.4.md:472`, `docs/design/skill_set_design_proposal_v0.4.md:477`, `docs/design/skill_set_design_proposal_v0.4.md:480`, `docs/design/skill_set_design_proposal_v0.4.md:490`, `docs/design/skill_set_design_proposal_v0.4.md:781`
- **Issue**: v0.4 定义了 `bug_flow.active/root_cause/bug_report_path`，也说明 Stage 5 失败后设置 `bug_flow.active=true` 并由 bug-triage 路由到 SRS / Architecture / Development Change Mode，但没有定义正常 bug 修复完成后的精确 mutation。尤其是没有说明何时将 `bug_flow.active` 置回 `false`、清空或保留 `bug_report_path/root_cause`、更新 BUG report status、把 `current_stage/sub_state` 切回 Testing retest 或 Stage 6。
- **Impact**: AGENTS bootstrap 明确规定 `bug_flow.active=true` 时优先 invoke `bug-triage`。如果 bug 已修完但 `bug_flow.active` 没有被清理，后续 agent 会反复进入 bug-triage，流程可能卡在 Bug Flow，或依赖人工手改 `progress.md`。
- **Recommendation**: 在 workflow-protocol 增加一组 Bug Flow mutation 表，至少包括 `bug-start`、`bug-route --root-cause <srs|architecture|development|prd-exception>`、`bug-close --result <fixed|duplicate|won't-fix>`。`bug-close` 应明确：更新 BUG report frontmatter/status，append history，`bug_flow.active: true -> false`，`bug_flow.root_cause` 与 `bug_report_path` 的保留/清空策略，以及 `current_stage` 回到 `testing` retest 或推进条件。

### Medium: `incident-resolve` 只列出命令，没有精确 mutation；`abort/reconstruct` 也缺少 project/release 终态字段

- **Location**: `docs/design/skill_set_design_proposal_v0.4.md:303`, `docs/design/skill_set_design_proposal_v0.4.md:363`, `docs/design/skill_set_design_proposal_v0.4.md:481`, `docs/design/skill_set_design_proposal_v0.4.md:485`, `docs/design/skill_set_design_proposal_v0.4.md:487`, `docs/design/skill_set_design_proposal_v0.4.md:488`, `docs/design/skill_set_design_proposal_v0.4.md:689`
- **Issue**: v0.4 增加了 `incident-start` 精确 mutation，但 `incident-resolve --action <continue|abort|reconstruct>` 只有 prose 描述，没有对应前置条件和字段变更表。当前 `progress.md` schema 只有 `release_state: active|closed`，没有 `project_state`、`release_close_reason`、`incident_resolution_action` 这类字段来区分 normal close、incident abort、转 S3 reconstruct。
- **Impact**: PRD 根因异常虽然可以进入 `workflow-incident-analysis`，但无法确定性退出。`abort` 如果只是把 release 设为 closed，会与正常完成的 release close 无法区分，后续 `release-start` 可能误把已终止项目继续演进；`reconstruct` 也缺少“当前项目终止/冻结 + 新 S3 project link”的表达。
- **Recommendation**: 增加 `incident-resolve` 精确 mutation 小节。建议字段包括 `project_state: active|terminated|reconstructing`、`release_close_reason: normal|incident-abort|incident-reconstruct`、`incident_resolution_action`，并规定三种 action：`continue` 清理 incident state 并回到指定 stage；`abort` 终止 project 且禁止后续 `release-start`；`reconstruct` 冻结当前 project 并记录 S3 新 project 入口或 handoff path。同时更新 `workflow-incident` doc 的 `resolution_action` 与 history。

### Low: v0.4 声称全文 script path normalize，但仍有 shorthand 会泄漏到 SKILL.md / AGENTS.md

- **Location**: `docs/design/skill_set_design_proposal_v0.4.md:414`, `docs/design/skill_set_design_proposal_v0.4.md:416`, `docs/design/skill_set_design_proposal_v0.4.md:422`, `docs/design/skill_set_design_proposal_v0.4.md:440`, `docs/design/skill_set_design_proposal_v0.4.md:481`, `docs/design/skill_set_design_proposal_v0.4.md:485`, `docs/design/skill_set_design_proposal_v0.4.md:497`, `docs/design/skill_set_design_proposal_v0.4.md:502`, `docs/design/skill_set_design_proposal_v0.4.md:805`, `docs/design/skill_set_design_proposal_v0.4.md:806`, `docs/design/skill_set_design_proposal_v0.4.md:811`, `docs/design/skill_set_design_proposal_v0.4.md:946`
- **Issue**: 文档中仍有 `progress.py ...`、`validate.py`、`scripts/progress.py`、`scripts/validate.py`、`调 progress.py bug-intake` 等 shorthand。v0.4 Decision Log 同时声称“全文 script 路径 normalize”。
- **Impact**: 低风险，但 Task 5 要把这些内容展开成实际 `SKILL.md`，shorthand 可能被复制进去，削弱“命令统一 `skills/<name>/scripts/...` 全路径”的规则。
- **Recommendation**: 对命令型/规范型语句统一替换为 `skills/workflow-protocol/scripts/progress.py ...` 或 `skills/doc-guardian/scripts/validate.py ...`。如果是目录树或 display-only 名称，显式标注“display-only shorthand”。

### Low: workflow spec v0.4 仍有 v0.3 / TBD 残留引用，容易误导后续实现

- **Location**: `docs/workflow/workflow_specification_claude.md:309`, `docs/workflow/workflow_specification_claude.md:647`, `docs/workflow/workflow_specification_claude.md:678`
- **Issue**: workflow spec 已标为 v0.4，但 Stage Mode Rule 仍引用 `docs/design/skill_set_design_proposal_v0.3.md`；Meta-Evolution 仍说后续“可能需要” Workflow Evolution skill；Open Items 仍把 Cross-cutting Skill 列表与定义作为候选项。设计文档 v0.4 已明确 23 个 physical skills，且 `workflow-evolution` 是实际 Meta skill。
- **Impact**: 低到中等风险。workflow spec 是 declared baseline，后续 agent 如果优先读 spec，可能误以为 skill 列表仍未确定，或查阅旧 v0.3 design。
- **Recommendation**: 将 spec 中实现引用更新到 `docs/design/skill_set_design_proposal_v0.4.md`，并把已由 v0.4 design 决定的 Open Items 改成“由 design proposal 定义，不在 workflow spec 展开”。

## Previous Findings Verification

| Previous Finding | v0.4 Status | Notes |
|---|---|---|
| F1 workflow spec S4 与 active-only policy 不一致 | Resolved | §2 / §6 / §9.4 已同步 active-release-only，post-close bug 改为 intake record。 |
| F2 post-close bug intake 无 owner / transition | Mostly Resolved | bug-triage post-close mode + `bug-intake` 已补齐；仍建议补 duplicate 防护与 BUG status 细节，但不阻塞架构。 |
| F3 PRD root-cause exception 无 state 表达 | Mostly Resolved | `prd-exception`、`workflow_incident_active`、`incident_report_path`、`workflow-incident-analysis` 已补齐；退出语义见本次 Finding 2。 |
| F4 release-close/start mutation 不完整 | Resolved | `release-close`、`release-start`、`bug-intake`、`incident-start` 均有 mutation 表；缺的是新增的 `incident-resolve`。 |
| F5 release version ordering 不明确 | Resolved | MAJOR.MINOR integer pair + numeric tuple comparison 已清晰。 |
| F6 script path shorthand 残留 | Partially Resolved | 可执行示例多数已全路径，但规范文本和 AGENTS.md snippet 仍有 shorthand；见本次 Finding 3。 |

## Positive Notes

- S4 active-release-only 与 post-close intake 的边界已经清晰，比 v0.3 更一致。
- Release lifecycle 的串行模型、version grammar、`release-close/release-start` mutation 已足够支撑实现。
- PRD root cause exception 已从“无法表达”提升为“可进入 incident state”，这是 v0.4 最大改进。
- `workflow-incident` doc type、`consumed_in_release`、`unresolved_bugs` 的组合基本能支撑 post-close bug 合并到下次 S2。

## Suggested Next Revision Order

1. 先补 Bug Flow state mutation：`bug-start` / `bug-route` / `bug-close`，避免 `bug_flow.active` 卡死。
2. 再补 `incident-resolve` mutation 与 `project_state` / `release_close_reason`，避免 PRD incident 无法确定性退出。
3. 清理 script path shorthand，尤其是 AGENTS.md template 与 Decision Log 中会被复制到实现的文本。
4. 同步 workflow spec 中 v0.3 / TBD 残留引用，让 spec 与 v0.4 design 保持一致。
