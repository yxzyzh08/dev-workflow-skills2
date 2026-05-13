# Skill Set Batch 1 Round 4 Review

**Review Target**: `skills/workflow-protocol/SKILL.md`, `skills/workflow-protocol/references/command-reference.md`, `skills/doc-guardian/SKILL.md`, `skills/doc-guardian/references/frontmatter-schema.md`, `skills/doc-guardian/references/directory-layout.md`, `skills/doc-guardian/references/required-artifacts.md`, `skills/doc-guardian/references/change-log-format.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1-3 History**: `docs/review/skill_set_batch1_review.md` / `docs/review/skill_set_batch1_round2_review.md` / `docs/review/skill_set_batch1_round3_review.md`  
**Round 1-3 Responses**: `docs/review/reviewer_feedback_response_v0.5_batch1.md` / `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md` / `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: 5 项 round 3 findings: 2 resolved, 2 resolved-but-introduced-new-issue, 1 partially resolved; 5 new/remaining findings (1 High + 3 Medium + 1 Low); recommendation: fix and run round 5 before batch 2

## Previous Findings Verification

| Finding | Severity | Round 3 Status | Round 4 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | DSL Hint + `substate_matches` 残留 | ⚠ Resolved but introduced new issue | 旧 operational `substate_matches()` / `task_substate_required` 算法已从实现 Hint 删除，Stage 4 per-task 无条件校验已落地；但新 DSL grammar 对括号与 enum literal tokenization 的定义仍不完整，见 finding M2。 |
| H2 | High | skeleton 默认 `pass` 可绕过 review | ⚠ Resolved but introduced new issue | skeleton 默认 `pending`、Stage 4 转移要求 `review_status: pass` 已落地；但 `pending + blocking_findings_count: 0` 与 “`pass` iff blocking=0” 不变量冲突，且 SKILL quick field row 仍写 `pass | fail`，见 finding H1。 |
| M3 | Medium | command-reference v0.6 init/recover 未同步 | 🟡 Partially Resolved | `init` 已改 `workflow_version: v0.6`，recover 已声明 terminal repair mutation；但 history 在 terminal event 之后出现非法/手工 entry 时的 replay 规则仍未定义，见 finding M3。 |
| M4 | Medium | SRS bool 字段未同步 cheat sheet | ✅ Resolved | `doc-guardian/SKILL.md` 和 `frontmatter-schema.md` per-type cheat sheet 均已列 `is_multi_module` / `architecture_change`；只剩示例 frontmatter 未更新，见 finding L5。 |
| L5 | Low | ID 3 位文案 + >999 模糊 | ✅ Resolved | 主文档、directory-layout、frontmatter ID regex 均收敛为 3 位 zero-padded；`BUG-1000` 当前 reject 的规则已写清。 |

## New Findings (round 4 引入)

### High: `pending` review report 与 “pass iff blocking=0” 不变量冲突，导致 skeleton 合法性无法实现

- **Dimensions**: 内部一致性, 可实现性, 边界状态处理, Forbidden Actions 完整性
- **Location**: `skills/doc-guardian/references/frontmatter-schema.md:216`, `skills/doc-guardian/references/frontmatter-schema.md:218`, `skills/doc-guardian/references/frontmatter-schema.md:235`, `skills/doc-guardian/references/frontmatter-schema.md:246`, `skills/doc-guardian/references/frontmatter-schema.md:538`, `skills/doc-guardian/SKILL.md:148`, `skills/doc-guardian/SKILL.md:180`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:16`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:25`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:33`, `docs/review/skill_set_batch1_round3_review.md:39`
- **Issue**: Round 3 选择了 `pending | pass | fail`，且 skeleton 要写 `review_status: pending`、counts 全 0；但 `frontmatter-schema.md` 仍保留 `review_status == "pass" iff blocking_findings_count == 0`，关键不变量又说“任何时候”成立。这样 skeleton 的 `pending + blocking_findings_count: 0` 同时被 lifecycle 要求和 invariant 禁止。主 `doc-guardian/SKILL.md` 的字段快查还仍写 `review_status` 仅用于 code-review-report 且只允许 `pass | fail`，与类 4 row 的 `{pending, pass, fail}` 冲突。
- **Impact**: Task 6 实现者无法确定 `validate.py` 应如何处理 skeleton：若严格实现 iff，`development-test-write` / `development-code-write` 创建的 skeleton 会 validate fail，Stage 4 卡死；若忽略 iff，又会和 schema invariant 冲突，且不同实现者会对 `pending` 选择不同特判。
- **Recommendation**: 把 review report 不变量改成三态规则，并同步主 SKILL 快查表。建议：`pending` 只允许 skeleton 状态（counts 全 0、`blocking_findings_count: 0`、`max_severity: low`、doc `status: draft` 或明确改为 `in-review`）；`pass` 要求 `blocking_findings_count == 0` 且 doc `status: review-passed`；`fail` 的 blocking / non-blocking 判定需明确。删除全局 “pass iff blocking=0” 或改成 “completed report 中 pass iff blocking=0；pending 例外”。

### Medium: Condition DSL grammar 声称支持括号和 enum literal，但 parser 规范不足以确定实现

- **Dimensions**: 可实现性, 内部一致性, Spec/Design 一致性
- **Location**: `skills/doc-guardian/references/required-artifacts.md:28`, `skills/doc-guardian/references/required-artifacts.md:31`, `skills/doc-guardian/references/required-artifacts.md:33`, `skills/doc-guardian/references/required-artifacts.md:303`, `skills/doc-guardian/references/required-artifacts.md:308`, `skills/doc-guardian/references/required-artifacts.md:311`, `skills/doc-guardian/references/required-artifacts.md:326`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:42`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:45`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:46`
- **Issue**: DSL 正文把 `()` 列为允许运算符，但 grammar 只有 `<expr> = <comparison> (&&/|| <comparison>)*`，没有 parenthesized expression 产生式。literal 又允许裸 enum（示例含 `S3`、`srs-specification`），但 tokenizer 只笼统说识别 identifier/bool/enum，没有定义 enum literal 白名单，也没有说明如何处理带 hyphen 的 stage literal。
- **Impact**: 当前 map 的 conditions 都较简单，短期可 workaround；但 Python 实现者写 parser/unit tests 时会在这些选择上分叉：有人会不支持括号，有人会把 RHS `S3` 当 identifier，有人会无法 token 化 `srs-specification`。后续一旦新增 `current_stage == srs-specification` 或带括号条件，会出现不兼容实现。
- **Recommendation**: 补完整 grammar，例如 `<primary> = <comparison> | '(' <expr> ')'`，并明确 token 规则：RHS enum literal 来自固定集合（scenario、scenario_subtype、current_stage 的所有合法值）且可含 hyphen；或要求所有 hyphenated enum/string literal 必须加引号，并同步修改示例。建议附 4-6 个 parser test case（`scenario == S3`、`srs.is_multi_module == true`、带括号、非法变量、非法函数调用、hyphen literal）。

### Medium: terminal `recover` 未定义 terminal event 之后的非法 history entry 如何处理

- **Dimensions**: 边界状态处理, 可实现性, 内部一致性
- **Location**: `skills/workflow-protocol/references/command-reference.md:175`, `skills/workflow-protocol/references/command-reference.md:178`, `skills/workflow-protocol/references/command-reference.md:179`, `skills/workflow-protocol/references/command-reference.md:181`, `skills/workflow-protocol/references/command-reference.md:187`, `skills/workflow-protocol/references/command-reference.md:552`, `skills/workflow-protocol/SKILL.md:263`, `skills/workflow-protocol/SKILL.md:269`, `skills/workflow-protocol/SKILL.md:323`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:17`, `docs/review/skill_set_batch1_round3_review.md:48`, `docs/review/skill_set_batch1_round3_review.md:53`
- **Issue**: command-reference 现在要求 recover “按 history 全程”重放，且重建后的 state 与 history 最末状态一致；同时状态表又说 terminal 后 reject all mutation。若 `progress-history.md` 在 `incident-resolve --action abort/reconstruct` 后被手工追加了格式合法但语义非法的 entry，规范没有说明 recover 应停在第一个 terminal event、拒绝 history、还是继续 replay。
- **Impact**: 实现者可能做出三种不一致行为；最危险的是继续 replay 后续非法 entry，可能把 `aborted/reconstructing` project 恢复成 active，违反 terminal 语义。即使不复活，也会掩盖 history corruption，影响故障恢复可靠性。
- **Recommendation**: 明确 recover 算法在 replay 时必须执行同一状态机 validator；一旦遇到第一个 terminal event，后续任何 mutating history entry 都判定为 history corrupt 并 `exit 1`（或只重建到 terminal 并报告 fatal，二选一）。不要 silently truncate，也不要 replay terminal 之后的非法 entry；如需 `--force-truncate`，应单独走 design review。

### Medium: doc-guardian Required Artifacts 快查仍与 required-artifacts 单一事实源不一致

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 跨 skill 引用一致性
- **Location**: `skills/doc-guardian/SKILL.md:295`, `skills/doc-guardian/SKILL.md:307`, `skills/doc-guardian/SKILL.md:313`, `skills/doc-guardian/references/required-artifacts.md:134`, `skills/doc-guardian/references/required-artifacts.md:140`, `skills/doc-guardian/references/required-artifacts.md:205`, `skills/doc-guardian/references/required-artifacts.md:210`, `skills/workflow-protocol/SKILL.md:178`, `skills/workflow-protocol/SKILL.md:190`, `docs/workflow/workflow_specification_claude.md:78`, `docs/workflow/workflow_specification_claude.md:265`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:478`, `docs/design/skill_set_design_proposal_v0.5.md:490`
- **Issue**: `required-artifacts.md` 自称单一事实源，并要求 Stage 4 每个 task 无条件校验 `detailed_design.md` 等 4 个 per-task artifacts；workflow-protocol task 状态表也把 `planning-done` 绑定到 `detailed_design.md`。但 `doc-guardian/SKILL.md` 快查仍写“各 Stage 4 task: 复杂任务必有 Detailed Design”，会让实现者误以为 detailed design 是条件 artifact。另一个同节快查把 Stage 7 写成 “Issue Report, Improvement Proposals”，而 required-artifacts / workflow-protocol 当前实际要求的是单个 `retrospective.md`；workflow spec v0.6 也列出多个 retrospective outputs，但未说明它们是 `retrospective.md` 的章节还是独立 artifacts。
- **Impact**: `progress.py update --advance` 若严格按 required-artifacts 实现可以工作，但 stage skill / validate.py consistency 的实现者读快查表时会对 Stage 4 和 Stage 7 required artifact 集合作出不同选择，导致 batch 2/Task 6 的文档模板和推进条件分叉。
- **Recommendation**: 让 `doc-guardian/SKILL.md` §7 与 `required-artifacts.md` 完全同源：Stage 4 写“每个 task 无条件必含 detailed-design / test-review-report / code-review-report / verification-result”；Stage 7 写“Project Retrospective: `docs/retrospective/retrospective.md`，Issue Analysis / Improvement Proposals 是该文档内必备章节（若这是设计意图）”。若 Issue Report / Improvement Proposals 应为独立 doc，则需补 doc type、路径、frontmatter schema 和 required-artifacts 条目，不应只停留在 prose。

### Low: SRS 示例 frontmatter 仍缺 round 3 新增的两个必含 bool 字段

- **Dimensions**: 内部一致性, 完整性
- **Location**: `skills/doc-guardian/references/frontmatter-schema.md:77`, `skills/doc-guardian/references/frontmatter-schema.md:82`, `skills/doc-guardian/references/frontmatter-schema.md:83`, `skills/doc-guardian/references/frontmatter-schema.md:395`, `skills/doc-guardian/references/frontmatter-schema.md:431`, `skills/doc-guardian/references/frontmatter-schema.md:442`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:18`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:52`, `docs/review/skill_set_batch1_round3_review.md:57`
- **Issue**: 详细 schema 和必含表已要求 `srs.is_multi_module` 与 `srs.architecture_change` 必含，但 §6.2 SRS 示例只包含 `release`，复制该示例会生成 validate.py 类 3 不通过的 SRS。
- **Impact**: 不阻塞实现者按 schema 写代码，但会误导模板/fixture 作者，导致示例驱动测试或 batch 2 stage skill 模板产出无效 frontmatter。
- **Recommendation**: 在 SRS 示例中补 `is_multi_module: false` 与 `architecture_change: false`（或 true 示例），并加一行注释说明这两个字段由 `srs-write` 决定 required-artifacts 条件。

## Cross-File Consistency Check

- **H1 parser rewrite**: 旧 operational `eval` / `substate_matches` 算法已删除；`task_substate_required` 只在历史说明和 Forbidden 中出现，不再驱动实现。剩余风险集中在 DSL grammar tokenization 和 parentheses。
- **H2 pending enum**: `frontmatter-schema.md` 详细 schema、workflow-protocol Stage 4 转移条件、command-reference 状态表都已改为 skeleton pending + transition only pass；但 doc-guardian 主文档字段快查和 `pass iff blocking=0` invariant 未同步。
- **M3 terminal recover**: `workflow-protocol/SKILL.md` 与 `command-reference.md` 都承认 terminal 下 recover 是唯一 repair mutation；但 command-reference 还缺 terminal 后非法 history entry 的确定处理。
- **M4 SRS bool**: 主 schema和 cheat sheet 已同步；SRS 示例未同步。
- **L5 ID regex**: 7 份目标文件未发现 `CR-\d+` / `BUG-\d+` / `INCIDENT-\d+` 旧正则残留；`>999` 当前 reject 已明确。
- **P6 required artifacts**: `required-artifacts.md` 作为脚本事实源基本可实现；`doc-guardian/SKILL.md` §7 的 Stage 4/7 快查仍需对齐，避免 batch 2 stage skill 复制旧描述。
- **Cross-skill command paths**: workflow-protocol 调 `skills/doc-guardian/scripts/validate.py file <artifact>` 与 doc-guardian 的子命令表一致；doc-guardian 引用 `skills/workflow-protocol/scripts/progress.py update --advance` 的语义一致。

## Implementability Assessment

当前主体契约已接近可实现：11 个 `progress.py` 子命令、S3 required artifacts、incident path、release-start consume、ID policy、Stage 4 per-task artifact map 都比 round 3 前清晰很多。但不建议直接进入 Task 6，因为仍有一个会直接影响 `validate.py` / Stage 4 状态机的 blocker：review report `pending` skeleton 与 `pass iff blocking=0` 不变量冲突。

实现者若现在开工，最可能出现的分叉点：

- `validate.py` 是否允许 `review_status: pending` 且 `blocking_findings_count: 0` 的 skeleton 通过。
- `progress.py recover` 在 terminal history 后出现非法 entry 时是 reject、truncate，还是继续 replay。
- `required-artifacts` DSL 是否支持括号、hyphenated enum literal，以及 enum literal 与 identifier 的区分策略。
- Stage 7 的 `Issue Report / Improvement Proposals` 是 `retrospective.md` 的章节还是独立 artifact。

## Recommendation

(B) 修复 5 项后再 round 5。当前 finding 数 > 3 且存在 1 个 High；按 round 4 判定门槛，暂不建议进入 batch 2。无需回 design proposal 重审整体结构，但需要把 pending review-report invariant、recover edge case、DSL grammar、quick summary 同步清楚后再放行。

## Suggested Next Revision Order

1. 先修 H1：把 review-report 三态不变量写成可执行规则，并同步 `doc-guardian/SKILL.md` 的 `review_status` 快查行。
2. 修 M2：补全 Condition DSL grammar/tokenizer 规则和最小 parser test cases。
3. 修 M3：明确 recover replay 到 terminal 后的非法 history entry 处理策略。
4. 修 M4：同步 `doc-guardian/SKILL.md` §7 的 Stage 4/7 required artifacts 快查。
5. 修 L5：更新 SRS 示例 frontmatter，避免模板/fixture 复制无效示例。

## Positive Notes

- Round 3 的两个 High 都有实质修复：旧 eval/substate algorithm 已撤掉，review skeleton 默认 pass 的 bypass 也已改成 pending。
- `init` 的 `workflow_version: v0.6` 与 terminal recover 语义已同步到 command-reference，明显降低了 round 3 的 schema drift。
- SRS 条件字段已经进入详细 schema 和 per-type cheat sheet，`required-artifacts.md` 的条件来源比 round 2/3 清楚。
- ID 3 位和 `>999` policy 已闭环，当前实现者可直接按 regex reject 4 位 ID。
