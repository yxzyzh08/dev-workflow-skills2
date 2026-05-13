# Skill Set Batch 1 Round 3 Review

**Review Target**: `skills/workflow-protocol/SKILL.md`, `skills/workflow-protocol/references/command-reference.md`, `skills/doc-guardian/SKILL.md`, `skills/doc-guardian/references/frontmatter-schema.md`, `skills/doc-guardian/references/directory-layout.md`, `skills/doc-guardian/references/required-artifacts.md`, `skills/doc-guardian/references/change-log-format.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review**: `docs/review/skill_set_batch1_review.md`  
**Round 1 Response**: `docs/review/reviewer_feedback_response_v0.5_batch1.md`  
**Round 2 Review**: `docs/review/skill_set_batch1_round2_review.md`  
**Round 2 Response**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: 9 项 round 2 findings: 5 resolved, 4 partially resolved, 0 not resolved; 5 new/remaining findings (2 High + 2 Medium + 1 Low); recommendation: fix and re-review before batch 2

## Previous Findings Verification

| Finding | Severity | Round 2 Status | Round 3 Status | Notes |
|---------|----------|----------------|----------------|-------|
| H1 | High | DSL 字段未定义 | 🟡 Partially Resolved | `srs.is_multi_module` / `srs.architecture_change` 已加入详细 SRS schema，DSL 白名单覆盖现有 condition；但 `required-artifacts.md` 实现 Hint 仍建议 `eval`，且 summary/cheat sheet 未同步 SRS 新字段。见 findings H1/M4。 |
| H2 | High | 旧 incident 签名残留 | ✅ Resolved | `SKILL.md`、`command-reference.md`、Forbidden Actions 均使用 `incident-start --bug <bug-path> --report <incident-path>`；旧单参数签名只作为 Forbidden Action 出现。 |
| H3 | High | `--bug-flow` 引入未定义字段 | ✅ Resolved | `--bug-flow keep|clear` 已删除；continue 单一路径清空 bug_flow；未发现 `continue-keep` / `continue-clear` 或新增 BUG 状态字段要求。 |
| H4 | High | spec body Technical Debt | ✅ Resolved | workflow spec Stage 2 表已改为 `S3 推荐（v0.6 修正：非必备）`，与 7 份目标文件的 3 必备 + technical-debt 推荐一致。 |
| M5 | Medium | terminal state 不一致 | 🟡 Partially Resolved | `SKILL.md` schema 已允许 `sub_state: null` 且 `workflow_version: v0.6`；但 `command-reference.md` 的 `init` mutation 仍写 `workflow_version: v0.5`，recover 终态语义也未同步到 command reference。见 finding M3。 |
| M6 | Medium | substate_matches 模糊 | 🟡 Partially Resolved | 主 map 已删 `task_substate_required` 并改为 Stage 4 无条件校验 4 个 per-task artifacts；但实现 Hint 仍引用 `substate_matches(task_state, entry["task_substate_required"])`。见 finding H1。 |
| M7 | Medium | test-review owner 模糊 | 🟡 Partially Resolved | lifecycle owner 表已加入；但 skeleton 默认 `review_status: pass` + blocking=0 会让 update 状态机可绕过 review skill。见 finding H2。 |
| M8 | Medium | ID/path 不一致 | 🟡 Partially Resolved | directory-layout 路径模板已改 `{cr_id}` / `{bug_id}` / `{incident_id}`，ID References 小节已补；但 doc-guardian SKILL summary 仍写 `CR-\d+`，frontmatter ID 表对 >999 的 4 位扩展语义不清。见 finding L5。 |
| L9 | Low | shorthand 残留 | ✅ Resolved | 两个 SKILL.md 均加入 Path Convention Note，允许 prose/table 中使用 display-only 简写；不再作为阻塞问题。 |

## New Findings (round 3 引入)

### High: required-artifacts 的实现 Hint 仍是旧算法，和 DSL 安全约束及 Stage 4 无条件校验冲突

- **Dimensions**: 可实现性, 内部一致性, 边界状态处理
- **Location**: `skills/doc-guardian/references/required-artifacts.md:15`, `skills/doc-guardian/references/required-artifacts.md:134`, `skills/doc-guardian/references/required-artifacts.md:150`, `skills/doc-guardian/references/required-artifacts.md:265`, `skills/doc-guardian/references/required-artifacts.md:279`, `skills/doc-guardian/references/required-artifacts.md:281`, `skills/doc-guardian/references/required-artifacts.md:284`, `skills/doc-guardian/references/required-artifacts.md:288`, `skills/doc-guardian/references/required-artifacts.md:298`, `skills/doc-guardian/references/required-artifacts.md:300`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:45`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:58`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:60`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:72`
- **Issue**: 本文件正文要求 condition DSL 用白名单 parser、禁止裸 `eval`，Stage 4 advance 无条件校验每个 task 的 4 个 per-task artifacts；但实现 Hint 仍保留旧 `substate_matches(task_state, entry["task_substate_required"])`，而 map 已删除 `task_substate_required`。同一 Hint 还写“simple parser 或 eval（受限上下文）”，与前文“禁止裸 eval”冲突。
- **Impact**: Task 6 实现者若复制该伪码，会在 Stage 4 直接 KeyError 或继续实现已废弃的按子状态匹配逻辑；也可能使用 `eval` 解析 condition，违反安全/确定性决策。
- **Recommendation**: 重写 §12 实现 Hint：Stage 4 分支应无条件 append `development_per_task.required` 的全部 entries；`eval_condition` 注释应改为“must use whitelist parser; eval/exec forbidden”。建议补一个最小 grammar 或 tokenization 伪码，覆盖 6 个变量、5 个运算符和 3 类 literal。

### High: review-report skeleton 默认 `review_status: pass` 可绕过 test/code review

- **Dimensions**: 可实现性, Forbidden Actions 完整性, 边界状态处理
- **Location**: `skills/doc-guardian/references/frontmatter-schema.md:238`, `skills/doc-guardian/references/frontmatter-schema.md:242`, `skills/doc-guardian/references/frontmatter-schema.md:247`, `skills/workflow-protocol/references/command-reference.md:522`, `skills/workflow-protocol/references/command-reference.md:524`, `skills/workflow-protocol/references/command-reference.md:527`, `skills/workflow-protocol/references/command-reference.md:529`, `skills/workflow-protocol/SKILL.md:191`, `skills/workflow-protocol/SKILL.md:192`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:21`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:22`
- **Issue**: `development-test-write` 创建 `test-review-report` skeleton 时被要求写 `review_status: pass`、`blocking_findings_count: 0`，且 code-review-report owner 模式相同。状态机从 `test-review` → `test-done` / `code-review` → `code-review-passed` 的条件仅检查 report `review_status: pass` 与 blocking=0。因此 skeleton 一创建就满足通过条件，agent 可不调用 `development-test-review` / `development-code-review` 而直接推进。
- **Impact**: Stage 4 的强制 review gate 可被合法字段值绕过，Task 6 按此实现会把未评审的测试/代码标为 done；这是实质性流程正确性 blocker。
- **Recommendation**: 不要让 skeleton 默认 pass。方案 A：把 `review_status` enum 扩为 `pending | pass | fail`，skeleton 用 `pending`，转 done 只接受 `pass` 且 doc `status: review-passed`。方案 B：保持 enum `pass|fail`，skeleton 用 `review_status: fail`，并要求 transition 同时检查 progress-history 中存在对应 review skill 的 `review-passed` event。code-review-report 采用同一规则。

### Medium: progress.py 的 v0.6 schema 未同步到 command-reference init / recover 小节

- **Dimensions**: 内部一致性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:64`, `skills/workflow-protocol/SKILL.md:73`, `skills/workflow-protocol/SKILL.md:269`, `skills/workflow-protocol/references/command-reference.md:20`, `skills/workflow-protocol/references/command-reference.md:25`, `skills/workflow-protocol/references/command-reference.md:166`, `skills/workflow-protocol/references/command-reference.md:183`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:20`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:74`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:82`
- **Issue**: `SKILL.md` progress schema 已改 `workflow_version: v0.6` 且 `sub_state` 允许 null；但 `command-reference.md` 的 `init` mutation 仍创建 `workflow_version: v0.5`。`recover` 小节仍只说重建 progress.md，没有同步 terminal state 下“唯一 repair mutation、不得改变 project_state 终态语义”的约束。
- **Impact**: Task 6 若按 command-reference 实现 init，会创建与 v0.6 baseline 不一致的 progress.md；recover 可能被实现成可“复活” aborted/reconstructing project，或被 terminal guard 错误拒绝。
- **Recommendation**: 将 init mutation 改为 `workflow_version: v0.6`。在 recover 小节补：terminal state 下允许 recover 作为 repair mutation；replay 后若 history 最终状态为 aborted/reconstructing 必须保持终态，禁止用 recover 变更为 active。

### Medium: SRS 新增 bool 字段未同步到 doc-guardian 主文档和 cheat sheet

- **Dimensions**: 内部一致性, 完整性
- **Location**: `skills/doc-guardian/SKILL.md:151`, `skills/doc-guardian/SKILL.md:155`, `skills/doc-guardian/references/frontmatter-schema.md:77`, `skills/doc-guardian/references/frontmatter-schema.md:83`, `skills/doc-guardian/references/frontmatter-schema.md:375`, `skills/doc-guardian/references/frontmatter-schema.md:382`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:16`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:45`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:52`
- **Issue**: `srs` 详细 schema 已加入 `is_multi_module` 与 `architecture_change`，但 doc-guardian 主文档的 per-type summary 仍把 `srs / 多数 release-level docs` 写成只必含 `release`；frontmatter-schema 的“Per-Type 字段必含表”也把 `srs` 归入只需 `release` 的泛化 row。该表自称必须与详细 schema 一致。
- **Impact**: 实现者若按 SKILL.md summary 或 cheat sheet 写 `require_per_type_fields`，会漏校验两个 condition DSL 的关键字段；条件 artifact 判断又会用默认 false，导致 Integration Plan / Architecture Delta 被误判为非必备。
- **Recommendation**: 在 `doc-guardian/SKILL.md` 和 `frontmatter-schema.md` cheat sheet 中单独列 `srs` row：`release`, `is_multi_module`, `architecture_change`。同时说明 validate.py 类 3 必须校验这两个字段存在且 YAML bool 类型合法。

### Low: ID 3 位规则仍有少量文案不一致，>999 扩展语义不够明确

- **Dimensions**: 内部一致性, 边界状态处理
- **Location**: `skills/doc-guardian/SKILL.md:145`, `skills/doc-guardian/SKILL.md:177`, `skills/doc-guardian/SKILL.md:179`, `skills/doc-guardian/references/frontmatter-schema.md:353`, `skills/doc-guardian/references/directory-layout.md:156`, `skills/doc-guardian/references/directory-layout.md:166`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:23`, `docs/review/reviewer_feedback_response_v0.6_batch1_round2.md:85`
- **Issue**: directory-layout 已强制 `^(CR|BUG|INCIDENT)-\d{3}$`，但 doc-guardian SKILL summary 仍写 `CR-\d+` / `BUG-\d+` / `INCIDENT-\d+`。frontmatter-schema 的 ID row 一方面写 `^CR-\d{3}$`，另一方面说超过 999 时 4 位“仍合法但当前规模内不允许”，这会让 validate.py 当前应 reject 还是 accept `BUG-1000` 不够直观。
- **Impact**: 低风险；当前规模内 3 位规则可执行，但边界 case 和主文档快查表可能误导实现。
- **Recommendation**: 主文档 summary 改为 `CR-\d{3}` / `BUG-\d{3}` / `INCIDENT-\d{3}`。frontmatter-schema 明确当前 validate.py 只接受 3 位；超过 999 必须先经 review cycle 升级 regex 和 directory policy，不应写“仍合法”。

## Cross-File Consistency Check

- **DSL 字段**: 详细 SRS schema 已定义 `is_multi_module` / `architecture_change`，required-artifacts conditions 使用的变量均在白名单内；但 SKILL summary 和 cheat sheet 未列这两个字段，且实现 Hint 仍保留 `eval` / `substate_matches` 旧逻辑。
- **Incident 签名**: `incident-start --bug <bug-path> --report <incident-path>` 已在 SKILL.md、command-reference、Forbidden Actions 对齐；旧 `--report <path>` 单参数仅作为 forbidden 出现。
- **Incident continue**: `--bug-flow keep|clear` 已删除；`resolution_action: continue` 仍是 schema enum 合法值；未发现 `continue-keep` / `continue-clear` 残留。
- **Technical Debt**: workflow spec v0.6、workflow-protocol、doc-guardian、required-artifacts 均已统一为 Stage 2 推荐、非必备。
- **Terminal state**: SKILL.md schema 与 terminal cleanup 对齐；command-reference init/recover 小节仍未完全同步 v0.6。
- **Stage 4 validation**: map 正文已无条件全校验；实现 Hint 仍旧，是当前最大 cross-file inconsistency。
- **ID format**: directory-layout 与 detailed ID regex 基本对齐；doc-guardian SKILL 快查表和 >999 prose 仍需清理。

## Implementability Assessment (Round 3 更新)

整体已比 round 2 明显收敛，7 份文件的主体契约基本可读，incident 路径、technical-debt 口径、ID lookup、Path Convention Note 都有实质改善。但当前仍不建议直接进入 Task 6，因为两个问题会导致实现错误：

- `required-artifacts.md` 的实现伪码仍是旧算法，Task 6 实现者照抄会破坏 Stage 4 advance 或使用被禁止的 `eval`。
- review-report skeleton 默认 pass 会绕过 development-test-review / development-code-review，破坏 Stage 4 的核心 review gate。

其余 Medium/Low 可快速修复，主要是 schema/cheat sheet 同步与边界文案清理。

## Recommendation

(B) 修复 2 项 High 后再 round 4。虽然 finding 总数已降到 5，但 High 仍为 2；按本轮门槛（High ≥ 2）不建议直接进 batch 2。

## Suggested Next Revision Order

1. 先修 `required-artifacts.md` §12 实现 Hint：删除 `task_substate_required` / `substate_matches` / eval 选项，改成无条件 per-task 全校验 + 白名单 parser。
2. 修 review-report skeleton：新增 `pending` 或默认 `fail`，并让 `test-done` / `code-review-passed` 同时要求真实 review event 或 doc `status: review-passed`。
3. 同步 `command-reference.md` init/recover 的 v0.6 schema 与 terminal repair semantics。
4. 同步 SRS 新 bool 字段到 doc-guardian SKILL summary 和 frontmatter cheat sheet。
5. 清理 ID 3 位文案与 >999 扩展说明。

## Positive Notes

- Round 2 的 4 个 High 中，incident 签名、incident continue 简化、Technical Debt 口径已基本闭环。
- `sub_state: null` 和 terminal cleanup 已在主 SKILL.md 中清晰表达。
- `test-review-report` lifecycle owner 表比 round 2 明确很多，只剩 skeleton 默认值导致的 bypass 风险。
- ID lookup 的方向已正确：`triggered_by_bug` 明确是 ID，而不是 path。
- Path Convention Note 已覆盖两个 SKILL.md，shorthand 不再是实质阻塞。
