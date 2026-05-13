# Skill Set Batch 1 Round 5 Review (Final)

**Review Target**: `skills/workflow-protocol/SKILL.md`, `skills/workflow-protocol/references/command-reference.md`, `skills/doc-guardian/SKILL.md`, `skills/doc-guardian/references/frontmatter-schema.md`, `skills/doc-guardian/references/directory-layout.md`, `skills/doc-guardian/references/required-artifacts.md`, `skills/doc-guardian/references/change-log-format.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Review History**: `docs/review/skill_set_batch1_review.md` / `docs/review/skill_set_batch1_round2_review.md` / `docs/review/skill_set_batch1_round3_review.md` / `docs/review/skill_set_batch1_round4_review.md`  
**Round 4 Response**: `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: 5 项 round 4 findings: 4 resolved, 1 partially resolved; 2 new/remaining findings (0 High + 1 Medium + 1 Low); recommendation: (A) proceed to batch 2

## Previous Findings Verification

| Finding | Severity | Round 4 Status | Round 5 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | pending invariant 冲突 | ✅ Resolved | `review_status` 三态已同步到 SKILL quick row、frontmatter detailed schema、关键不变量；`pending + counts=0 + blocking=0 + max_severity=low` skeleton 现在明确合法，Stage 4 转移仍只接受 `pass`。 |
| M2 | Medium | DSL grammar 不完整 | 🟡 Partially Resolved | §Condition DSL 顶部已补完整 grammar、16 个 enum literal、hyphen RHS 规则和 6 个 test cases；但 §12 实现 Hint 内部 docstring 仍保留旧 grammar，见 finding M1。 |
| M3 | Medium | recover post-terminal 模糊 | ✅ Resolved | `command-reference.md` §4 已定义 replay validator：terminal event 后 mutating entry fatal，禁止 silent truncate / replay；terminal event 明确为 `incident-resolve --action abort/reconstruct`。 |
| M4 | Medium | doc-guardian §7 不一致 | ✅ Resolved | `doc-guardian/SKILL.md` §7.1 已改成对齐表：Stage 4 每 task 无条件 4 个 artifacts；Stage 7 是 `retrospective.md` 单文件，Issue Analysis / Improvement Proposals 是内部章节。 |
| L5 | Low | SRS 示例缺字段 | ✅ Resolved | SRS 示例已补 `is_multi_module` 与 `architecture_change` 两个必含 bool，并说明由 `srs-write` 决定、供 required-artifacts DSL 使用。 |

## New Findings (round 5 引入)

### Medium: required-artifacts §12 实现 Hint 仍保留旧 DSL grammar，与顶部完整 grammar 冲突

- **Dimensions**: 内部一致性, 可实现性, 边界状态处理
- **Location**: `skills/doc-guardian/references/required-artifacts.md:30`, `skills/doc-guardian/references/required-artifacts.md:36`, `skills/doc-guardian/references/required-artifacts.md:46`, `skills/doc-guardian/references/required-artifacts.md:54`, `skills/doc-guardian/references/required-artifacts.md:71`, `skills/doc-guardian/references/required-artifacts.md:348`, `skills/doc-guardian/references/required-artifacts.md:352`, `skills/doc-guardian/references/required-artifacts.md:353`, `skills/doc-guardian/references/required-artifacts.md:356`, `skills/doc-guardian/references/required-artifacts.md:366`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md:16`, `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md:41`, `docs/review/reviewer_feedback_response_v0.8_batch1_round4.md:54`, `docs/review/skill_set_batch1_round4_review.md:33`
- **Issue**: 文件顶部的 DSL 规范已经支持 precedence、括号、enum literal 白名单和 hyphenated RHS；但 §12 `eval_condition_whitelist()` docstring 仍写旧版 `<expr> = <comparison> ( ('&&' | '||') <comparison> )*`，没有 `<or-expr>` / `<and-expr>` / `<primary>`，也没有 enum whitelist / hyphenated RHS 规则。该 docstring 还写 `parse(tokens)  # recursive descent，按上面 grammar`，会让实现者误以为应按旧 grammar 实现。
- **Impact**: 顶部规范足够让实现者 workaround，但若 Task 6 直接复制 §12 Hint，parser 可能不支持 round 4 新增的括号/优先级规则，或者继续把 enum literal 与 identifier 混在一起处理，导致单元测试和后续条件扩展不一致。
- **Recommendation**: 将 §12 docstring 替换为与 §Condition DSL 完全相同的 grammar，或删除重复 grammar，仅写“按本文件 §Condition DSL 规范实现”。同时把 `tokenize` 注释补成：识别 identifier、enum-literal whitelist、bool、quoted-string、operators；hyphenated token 仅允许在 comparison RHS。

### Low: frontmatter-schema 的 `task_id` 格式行落在 ID 表外，Markdown 结构易误读

- **Dimensions**: 内部一致性, 简洁度, 可实现性
- **Location**: `skills/doc-guardian/references/frontmatter-schema.md:370`, `skills/doc-guardian/references/frontmatter-schema.md:372`, `skills/doc-guardian/references/frontmatter-schema.md:378`, `skills/doc-guardian/references/frontmatter-schema.md:379`, `skills/doc-guardian/SKILL.md:146`, `skills/doc-guardian/references/frontmatter-schema.md:195`
- **Baseline Reference**: `docs/review/skill_set_batch1_round3_review.md:66`, `docs/review/reviewer_feedback_response_v0.7_batch1_round3.md:56`
- **Issue**: `frontmatter-schema.md` §4.4 的 ID 表在 `incident_id` 后结束，随后插入 `>999` 说明；`task_id` 行紧接在说明后，已经不属于 Markdown 表。虽然 `doc-guardian/SKILL.md` 和 detailed per-task schema 仍定义了 `T\d+`，但 full schema 的格式约束表渲染会丢失 `task_id` row。
- **Impact**: 低风险；实现者仍可从其他位置获得 `task_id` 规则，但按 full schema 表生成校验清单或文档模板时可能漏掉 `task_id` format row。
- **Recommendation**: 把 `task_id` row 移回表内（放在 `incident_id` 后、`>999` 段落前），或单独开 “Task ID” 小节。该修复可在 batch 2 或 Task 6 文档清理中完成。

## Cross-File Consistency Check

- **review_status 三态**: `doc-guardian/SKILL.md` §4.3、`frontmatter-schema.md` detailed schema / lifecycle / invariants、`workflow-protocol/SKILL.md` Stage 4 表、`command-reference.md` Stage 4 task 表均已对齐为 `pending | pass | fail`，且转移只接受 `pass`。
- **DSL 字段四处对齐**: `srs.is_multi_module` / `srs.architecture_change` 已在 SRS schema、per-type cheat sheet、doc-guardian summary、required-artifacts conditions 中一致；残留问题仅是 §12 Hint 的重复 grammar 未同步。
- **terminal recover**: `command-reference.md` 给出完整 replay validator；`workflow-protocol/SKILL.md` §9 保持 summary 级描述，没有相反规则。两者不冲突，Task 6 应以 command-reference 的详细算法为准。
- **Stage 4 unconditional validation**: `required-artifacts.md` §5 / §12、`doc-guardian/SKILL.md` §7.1、`workflow-protocol/SKILL.md` §5.2 均表达为每 task 无条件校验 4 个 per-task artifacts；旧“复杂任务才有 Detailed Design”已从主快查中删除。
- **Stage 7 artifact**: doc-guardian、directory-layout、frontmatter-schema、required-artifacts 都已收敛为 `docs/retrospective/retrospective.md` 单文件；workflow spec / design 中的 Issue Report / Improvement Proposals 可按内部章节理解。
- **ID policy**: 主文档、directory-layout 和 frontmatter schema 都维持 3 位 zero-padded；`>999` 当前 reject 的规则仍明确。

## Implementability Assessment (Final)

**明确判断**：可以。Python 实现者可以直接基于 7 份文件实现 `progress.py`、`validate.py`、`changelog.py` 三个脚本。

需关注的实现注意点：

- DSL parser 应以 `required-artifacts.md` 顶部 §Condition DSL 的完整 grammar / enum whitelist / parser test cases 为准，不要照抄 §12 docstring 的旧 grammar。
- `recover` 应按 `command-reference.md` §4 的 replay validator 实现，terminal event 后 mutating entry 必须 fatal，不允许 silent truncate。
- `validate.py` 对 review report 应实现三态分支：`pending` skeleton 合法但不能推进 task；`pass` 才允许 Stage 4 `test-done` / `code-review-passed`。

## Recommendation (Final)

(A) **进 batch 2**。当前 High = 0，finding 数 = 2，且唯一 Medium 有明确 workaround（以顶部 DSL 规范为准）。按 round 5 终轮门槛，继续纯文档 round 的收益已经低于进入 batch 2 / Task 6 获取实现反馈的收益。

## Suggested Next Revision Order

Batch 2 / Task 6 watch list：

1. 开始实现前先清理 `required-artifacts.md` §12 的 stale DSL docstring，或在 Task 6 parser tests 中强制引用顶部 6 个 parser test cases。
2. 顺手修 `frontmatter-schema.md` §4.4 的 `task_id` table formatting，避免自动生成校验清单时漏行。
3. 在 Task 6 单元测试中覆盖三态 review report、terminal recover corruption、Stage 4 unconditional per-task validation、S3 3+1 source-system-analysis 清单。

## Positive Notes

- Round 4 的唯一 High 已实质修复：`pending` skeleton 与三态不变量现在能同时成立，review bypass 风险解除。
- DSL 顶部规范已足够驱动 parser 实现，包含括号、优先级、hyphen enum literal 和错误用例。
- terminal recover 从 prose 约束升级成可实现的 replay algorithm，边界状态处理明显更确定。
- doc-guardian §7 与 required-artifacts 的 Stage 4 / Stage 7 口径已对齐，batch 2 stage skill 不再会从主快查复制旧条件描述。
