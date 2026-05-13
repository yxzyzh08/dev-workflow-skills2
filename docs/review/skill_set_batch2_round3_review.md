# Skill Set Batch 2 Round 3 Review

**Review Target**: `skills/scenario-dispatcher/SKILL.md`, `skills/scenario-dispatcher/references/scenario-decision-tree.md`, `skills/bug-triage/SKILL.md`, `skills/bug-triage/references/root-cause-rubric.md`, `skills/bug-triage/references/triage-decision-tree.md`, `skills/workflow-evolution/SKILL.md`, `skills/workflow-evolution/references/incident-analysis-template.md`, `skills/workflow-protocol/references/command-reference.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review/Response**: `docs/review/skill_set_batch2_review.md` / `docs/review/reviewer_feedback_response_v0.9_batch2.md`  
**Round 2 Review/Response**: `docs/review/skill_set_batch2_round2_review.md` / `docs/review/reviewer_feedback_response_v0.10_batch2_round2.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: regression: 0 blocking remain; 0 New High; 3 Low cleanup notes; recommendation: (A) proceed to batch 3

> Note: `docs/review/reviewer_feedback_response_v0.9_batch3.md` was not present in the repo. This review follows the available Round 3 prompt `docs/review/codex_review_prompt_batch2_round3.md` plus `docs/review/reviewer_feedback_response_v0.10_batch2_round2.md`.

## Round 2 Findings 回归状态

| Round 2 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| M1 三层 gate | ✅ 已修 | bug-triage description 已删除“其他 stage 主动报”入口；triage-decision-tree §1 active 分支拆成 non-testing reject early 与 testing/review-passed active mode；§2.1 Step 0 在读 BUG / 写 frontmatter 前执行，与 dispatcher 和 `bug-start` 前置一致。 |
| M2 Example E + §4.3 | ✅ 已修 | root-cause-rubric Example E 已补 `promote BUG → validate BUG → create INCIDENT → promote INCIDENT → validate INCIDENT → incident-start`；triage-decision-tree §4.3 已列 class 1-7 并说明 class 8 不在 `validate.py file` 时点。仅剩一处 Low 文案清理见 New Findings。 |
| M3 post-close 模板 | ✅ 已修 | post-close BUG 模板的 `## Pending Changes` 已改为 HTML comment `<!-- empty after changelog.py promote -->`，符合 change-log-format §2.3；未发现 `- (空，已 promote)` 模板残留。 |
| M4 retrospective Action Item | ✅ 已修 | workflow-evolution SKILL §4.3 与 incident-analysis-template §5 均加 Advisory Notice 与 Action Item 列；incident examples A/B/C 的 §4 均加 per-item Action Item 和 no patch/diff 提示。仅剩 non-blocking 输出空结果说明可补。 |
| M5 reentrant idempotency | ✅ 已修 | workflow-evolution §7.1 增加 6 条可判定规则；§7.2 拆 finalization-complete 与 finalization-unknown；§10 recovery 与 incident-analysis-template §1.6.1 均要求重跑 validate / Pending 检查，不再 silent skip 到 incident-resolve。 |
| M6 progress.py validate 前置 | ✅ 已修 | command-reference §10/§11 已显式加入 `validate.py file <incident-path> exit 0` double-safety；§11 还要求 `status==review-passed` 与 `resolution_action` 合法且匹配命令参数。未发现与 mutation 描述冲突。 |
| L1 examples finalization | ✅ 已修 | incident-analysis-template Example A/B/C 都在 §7 Resolution 与 incident-resolve 结果之间加入 6.b-g finalization sequence，并明确“仅在 6.g pass 后”调用 progress.py。 |

## New Findings (Round 3)

### Low: triage-decision-tree §4.3 的命令注释仍写 “validate 确认全部 8 类”

- **Location**: `skills/bug-triage/references/triage-decision-tree.md:526`, `skills/bug-triage/references/triage-decision-tree.md:536`, `skills/bug-triage/references/triage-decision-tree.md:548`, `skills/doc-guardian/SKILL.md:190`, `skills/doc-guardian/SKILL.md:191`
- **Issue**: §4.3 bash block 注释写 `validate：确认全部 8 类校验通过`，但 `validate.py file` 的事实源是 class 1-7 single-file checks；同节后文也正确说明 class 8 由 `validate.py consistency` 单独跑，不在 skeleton 创建时点检查。
- **Impact**: 不影响主流程实现，因为实际命令是 `validate.py file`，且后文表格正确；但注释与 class 8 说明相互抵触，容易让实现者误以为 `validate.py file` 会覆盖 progress.md consistency。
- **Recommendation**: 将该注释改为 `# 2. validate：确认 class 1-7 single-file checks 通过`，并保留后文 class 8 说明。

### Low: retrospective consumption 模板未明示 “无建议也合法”，可能诱导填充空泛建议

- **Location**: `skills/workflow-evolution/SKILL.md:205`, `skills/workflow-evolution/SKILL.md:217`, `skills/workflow-evolution/SKILL.md:239`, `skills/workflow-evolution/references/incident-analysis-template.md:667`, `skills/workflow-evolution/references/incident-analysis-template.md:696`, `skills/workflow-evolution/references/incident-analysis-template.md:721`
- **Issue**: retrospective consumption mode 已要求每条 advisory 含 Action Item，但模板没有说明如果某类没有发现，应填写 `None` / `No actionable suggestion found`。当前所有 suggestion sections 都带示例行和 `...`，可能被误读为必须产出建议。
- **Impact**: 这不会影响 state mutation，因为 retrospective consumption 是只读 conversation 输出；但可能导致 AI 为了填满表格而生成低价值或假阳性的 workflow 建议。
- **Recommendation**: 在 SKILL §4.3 与 incident-analysis-template §5 的 Advisory Notice 或每张表后加一句：`If no actionable suggestion exists for a category, write "None — no actionable suggestion found" and do not fabricate items.`

### Low: incident-analysis-template 新增 §1.6.1 后缺少 “## 2. Three Action Decision Matrix” 标题

- **Location**: `skills/workflow-evolution/references/incident-analysis-template.md:291`, `skills/workflow-evolution/references/incident-analysis-template.md:330`, `skills/workflow-evolution/references/incident-analysis-template.md:332`
- **Issue**: §1.6.1 结束后直接出现“详细判定矩阵...”和 `### 2.1 关键评估维度`，但缺少原本的二级标题 `## 2. Three Action Decision Matrix`。
- **Impact**: 纯结构清理问题，不影响 Step 6 / reentrant 实现；但 Markdown 层级不完整会降低 reference 可导航性，并让 §2.1 看起来挂在 §1 下。
- **Recommendation**: 在 line 330 前补回 `## 2. Three Action Decision Matrix` 标题。

## Cross-Finding Consistency Check

- **三层 gate 一致**: dispatcher、bug-triage SKILL、triage-decision-tree Step 0、workflow-protocol `bug-start` 前置均统一为 `release_state==active` + `current_stage==testing` + `sub_state==review-passed`；Forbidden Actions 与 early gate 是兜底关系，没有冲突。
- **promote / validate 顺序**: BUG active triage、post-close BUG intake、PRD-exception INCIDENT skeleton、workflow-evolution finalization 的主流程和 examples 均为 `Pending entry → changelog.py promote → validate.py file → progress.py`；唯一残留是 §4.3 注释把 file check 误写成 8 类。
- **空 Pending Changes**: 未发现 `- (空，已 promote)` 模板残留；post-close BUG 使用 HTML comment，INCIDENT promote 后示例使用纯空章节，均符合 change-log-format。
- **Action Item / advisory boundary**: Incident mode、retrospective mode、examples 都已覆盖 Action Item 与 no patch/diff 边界；建议补 “无建议也合法” 以避免假阳性建议，但不阻塞 batch 3。
- **reentrant idempotency**: SKILL §7.1 / §7.2 / §10 与 incident-analysis-template §1.6.1 对齐；重 invoke 必须再次 validate + 检查 Pending，不再只凭 `status=review-passed` 直接 incident-resolve。
- **double-safety validate**: bug-triage / workflow-evolution caller 先 validate，`progress.py incident-start` / `incident-resolve` 再 validate；workflow-protocol 调 doc-guardian 与既有 `update --advance` 校验方向一致，没有发现新的循环依赖风险。

## Recommendation

- **(A)**: 进 batch 3。Round 2 的 7 项修复已实质闭环，0 New High，且未发现需要阻塞的 Medium；3 个 Low 都是文档清理 / 输出质量提示，可在 batch 3 起骨架期间顺手修，不需要再开 batch 2 round 4。
