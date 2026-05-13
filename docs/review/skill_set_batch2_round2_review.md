# Skill Set Batch 2 Round 2 Review (post-fix regression)

**Review Target**: `skills/scenario-dispatcher/SKILL.md`, `skills/scenario-dispatcher/references/scenario-decision-tree.md`, `skills/bug-triage/SKILL.md`, `skills/bug-triage/references/root-cause-rubric.md`, `skills/bug-triage/references/triage-decision-tree.md`, `skills/workflow-evolution/SKILL.md`, `skills/workflow-evolution/references/incident-analysis-template.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review**: `docs/review/skill_set_batch2_review.md`  
**Round 1 Response**: `docs/review/reviewer_feedback_response_v0.9_batch2.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: regression: 0 New High; 6 Medium + 1 Low remain; recommendation: (B) small sync patch + re-review before batch 3

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| F1 PRD-exception INCIDENT changelog | ⚠️ 部分残留 | 主流程和 triage-decision-tree skeleton 已修为 `promote → validate → incident-start`；但 root-cause-rubric 的 prd-exception example 仍直接从创建 INCIDENT 跳到 `incident-start`，且 §4.3 validate checklist 没完整列出 file check 1-7 类。 |
| F2 active 非 testing reject | ⚠️ 部分残留 | scenario-dispatcher 主体已统一 reject；bug-triage 主体前置也已强化。但 bug-triage frontmatter description 仍写“active release 其他 stage 主动报 bug 时调用”，triage-decision-tree 顶层 active 分支也缺少 testing/review-passed early gate。 |
| F3 4 类强制 | ✅ 已修 | root-cause-rubric §4.4a 与 Example D 已删除第五状态承载，明确 4 类强制、三类反模式、用户手动删除 BUG report 的撤销路径。 |
| F4 advisory vs patch | ⚠️ 部分残留 | Incident mode 的 advisory/patch 边界已明显改善；但 retrospective consumption output 模板仍只写“提交去向”，没有按每条建议标注 Action Item，examples 也没有按新模板示范。 |
| F5 finalization 序列 | ⚠️ 部分残留 | Step 6.a-g 主序列已修；但 idempotency/recovery 仍允许在只检测到 `status=review-passed` 时“直接重试 incident-resolve”，没有重新确认 Pending 清空、promote/validate 已完成。另有 progress.py 是否内置二次 validate 的 cross-reference 不一致。 |

## New Findings (Round 2)

### Medium: bug-triage active mode 的入口描述和 reference 伪代码仍留下非 testing 入口残影

- **Location**: `skills/bug-triage/SKILL.md:3`, `skills/bug-triage/SKILL.md:45`, `skills/bug-triage/SKILL.md:48`, `skills/bug-triage/references/triage-decision-tree.md:23`, `skills/bug-triage/references/triage-decision-tree.md:24`, `skills/bug-triage/references/triage-decision-tree.md:41`, `skills/bug-triage/references/triage-decision-tree.md:42`, `skills/bug-triage/references/triage-decision-tree.md:143`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:347`, `skills/workflow-protocol/references/command-reference.md:351`, `skills/workflow-protocol/references/command-reference.md:353`
- **Issue**: SKILL frontmatter description 仍说用户在 “active release 其他 stage” 主动报 bug 时由 scenario-dispatcher 调用 bug-triage active mode；triage-decision-tree 顶层伪代码也写成 `release_state == active → Active Mode`，`active_mode_triage()` 开头只校验 BUG 文件，不先校验 `current_stage==testing AND sub_state==review-passed`。这与同文件正文前置条件和 dispatcher reject 路径不一致。
- **Impact**: Task 6 若按 reference 伪代码实现，可能在非 testing active release 被错误 invoke 后先写 BUG.frontmatter / Pending Changes，再等 `progress.py bug-start` 拒绝，制造 `root_cause` 已设但 bug_flow 未进入的半成品重试状态。
- **Recommendation**: 同步三处 gate：1) 修改 frontmatter description，只允许 “Stage 5 testing 自动发现”或“active testing review-passed 主动报 bug”；2) 在 triage-decision-tree 顶层 active 分支和 `active_mode_triage()` 第一行加入 `if not (current_stage == testing and sub_state == review-passed): reject before reading/writing BUG`；3) 保留 Forbidden Actions 作为兜底，但不要让伪代码依赖后置拒绝。

### Medium: PRD-exception 示例和 validate checklist 未完全回归到 promote-first 契约

- **Location**: `skills/bug-triage/references/root-cause-rubric.md:372`, `skills/bug-triage/references/root-cause-rubric.md:374`, `skills/bug-triage/references/root-cause-rubric.md:494`, `skills/bug-triage/references/root-cause-rubric.md:495`, `skills/bug-triage/references/triage-decision-tree.md:500`, `skills/bug-triage/references/triage-decision-tree.md:510`, `skills/bug-triage/references/triage-decision-tree.md:518`
- **Baseline Reference**: `skills/bug-triage/SKILL.md:95`, `skills/bug-triage/SKILL.md:97`, `skills/bug-triage/SKILL.md:99`, `skills/bug-triage/SKILL.md:101`, `skills/doc-guardian/SKILL.md:175`, `skills/doc-guardian/SKILL.md:183`
- **Issue**: root-cause-rubric Example E 仍展示 “创建 INCIDENT skeleton → 调 progress.py incident-start”，没有插入 `changelog.py promote <incident>` 与 `validate.py file <incident>`。另外 triage-decision-tree §4.3 声称覆盖 single-file check 1-7，但实际只列 frontmatter/ID/cross-ref/change-log 相关项，缺 Path、Naming、universal fields、timestamp/owner、ID uniqueness 等类别。
- **Impact**: 主流程已正确，但实现者读 root-cause-rubric 的端到端 example 或复制 §4.3 checklist 时，会得到比主契约弱的流程，回归到 Round 1 F1 的“incident-start 前未 promote/validate”风险，或误以为 validate check 范围小于 doc-guardian 实际范围。
- **Recommendation**: 把 root-cause-rubric Example E 改为：创建 INCIDENT skeleton → `changelog.py promote` → `validate.py file` → `progress.py incident-start`。triage-decision-tree §4.3 改成完整 1-7 类清单，或直接引用 `skills/doc-guardian/SKILL.md` §5.1 并只补 workflow-incident 特有字段，避免维护一份不完整 checklist。

### Medium: post-close BUG 完整模板的 Pending Changes 仍是 validate.py 会拒绝的非空内容

- **Location**: `skills/bug-triage/references/triage-decision-tree.md:304`, `skills/bug-triage/references/triage-decision-tree.md:305`, `skills/bug-triage/references/triage-decision-tree.md:307`, `skills/bug-triage/references/triage-decision-tree.md:310`
- **Baseline Reference**: `skills/doc-guardian/references/change-log-format.md:91`, `skills/doc-guardian/references/change-log-format.md:95`, `skills/doc-guardian/references/change-log-format.md:191`, `skills/doc-guardian/references/change-log-format.md:194`
- **Issue**: Post-close BUG template 在 `## Pending Changes` 下写了 `- (空，已 promote)`。doc-guardian 明确要求 Pending body 为空或仅注释；任何非注释、非空白行都会被类 6 视为未 promote entry。
- **Impact**: 若 Task 6 实现者把该“完整模板”作为 promote 后文件内容复制，`validate.py file` 会失败；若实现者特殊处理这行，又会与 change-log-format 的空章节定义不一致。
- **Recommendation**: 将模板改成真正空章节：`## Pending Changes` 后直接空行接 `## Change Log`；如需要人读提示，只能用 HTML comment，例如 `<!-- empty after changelog.py promote -->`，并确认 change-log-format 允许注释。

### Medium: retrospective consumption 模板没有按 F4 决策为每条 advisory 标注 Action Item

- **Location**: `skills/workflow-evolution/SKILL.md:203`, `skills/workflow-evolution/SKILL.md:231`, `skills/workflow-evolution/SKILL.md:385`, `skills/workflow-evolution/SKILL.md:402`, `skills/workflow-evolution/references/incident-analysis-template.md:81`, `skills/workflow-evolution/references/incident-analysis-template.md:82`, `skills/workflow-evolution/references/incident-analysis-template.md:417`, `skills/workflow-evolution/references/incident-analysis-template.md:421`, `skills/workflow-evolution/references/incident-analysis-template.md:473`, `skills/workflow-evolution/references/incident-analysis-template.md:477`, `skills/workflow-evolution/references/incident-analysis-template.md:539`, `skills/workflow-evolution/references/incident-analysis-template.md:542`, `skills/workflow-evolution/references/incident-analysis-template.md:617`, `skills/workflow-evolution/references/incident-analysis-template.md:647`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.9_batch2.md:25`, `docs/review/reviewer_feedback_response_v0.9_batch2.md:95`, `docs/review/reviewer_feedback_response_v0.9_batch2.md:98`
- **Issue**: workflow-evolution §8.2 要求 retrospective consumption 输出 advisory 时明确标注提交到 design proposal cycle；incident template §1.2 还要求每条建议尾部标注 Action Item。但 SKILL §4.3 和 incident-analysis-template §5 的 retrospective 输出模板只在分组标题下写“提交去向”，且部分标题仅写“dev-workflow-skills2 仓库”，没有逐条 `Action Item` 字段，也没有在 retrospective 模板开头重申 “禁止 patch/diff”；incident examples §4.1-§4.3 里的 §4 Workflow Improvement Suggestions 也仍只列建议和优先级，没有示范每条 Action Item。
- **Impact**: Incident mode 与 retrospective mode 会产出两种不同格式：前者要求 per-item Action Item，后者可能只给全局 caveat。实现者在 retrospective mode 下容易输出没有落地路径的泛化建议，或被用户要求时滑向 patch 模式。
- **Recommendation**: 在 SKILL §4.3 与 incident-analysis-template §5 的所有 suggestion tables 增加 `Action Item` 列，值固定为 `提交 dev-workflow-skills2 design proposal review cycle`；将 “提交去向：dev-workflow-skills2 仓库” 统一改为 “dev-workflow-skills2 design proposal review cycle”；在 retrospective 输出模板顶部加入与 §1.2 同等强度的 “advisory only; no patch/diff/unified diff; no direct file edits” notice；同步更新 incident examples 的 §4 建议表，避免示例继续教旧格式。

### Medium: workflow-evolution 重 invoke 幂等路径会绕过 Step 6.e-g 的完成性确认

- **Location**: `skills/workflow-evolution/SKILL.md:87`, `skills/workflow-evolution/SKILL.md:95`, `skills/workflow-evolution/SKILL.md:99`, `skills/workflow-evolution/SKILL.md:347`, `skills/workflow-evolution/SKILL.md:355`, `skills/workflow-evolution/SKILL.md:440`, `skills/workflow-evolution/references/incident-analysis-template.md:262`, `skills/workflow-evolution/references/incident-analysis-template.md:283`
- **Baseline Reference**: `skills/doc-guardian/references/change-log-format.md:224`, `skills/doc-guardian/references/change-log-format.md:233`
- **Issue**: 主流程 Step 6.a-g 已正确规定 “body/frontmatter mutation → Pending entry → promote → validate → incident-resolve”。但 idempotency/recovery 写成：只要检测到 body §3-§7 已填、`resolution_action` 已设、`status=review-passed`，就“直接重试 incident-resolve”。它没有确认 `## Pending Changes` 是否为空、Change Log 是否已有最终 entry、以及上次是否已成功跑过 `validate.py file`。
- **Impact**: 如果会话在 Step 6.b-d 之后、Step 6.f/g 之前中断，重 invoke 会直接尝试 `incident-resolve`。最乐观情况是 progress.py 拒绝后再手工排查；最坏情况是如果 progress.py 未内置完整 validate（见下一条 finding），未 promote 的最终 frontmatter/body 改动会逃过 change-log discipline。
- **Recommendation**: 把 §7.1/§7.2/§10 的“直接重试”改为“先运行 `validate.py file <incident>` 并检查 Pending 已空；若 fail 或 Pending 非空，重走 Step 6.e-g（必要时补 Pending entry）后再 incident-resolve”。Idempotency 表建议拆成两行：`finalization complete` 才 direct retry；`body/frontmatter complete but finalization unknown` 必须 re-promote/re-validate。

### Medium: batch2 文档声称 progress.py 会二次 validate INCIDENT，但 command-reference 未定义该前置

- **Location**: `skills/bug-triage/SKILL.md:104`, `skills/workflow-evolution/SKILL.md:99`, `skills/workflow-evolution/SKILL.md:100`, `skills/workflow-protocol/references/command-reference.md:419`, `skills/workflow-protocol/references/command-reference.md:425`, `skills/workflow-protocol/references/command-reference.md:456`, `skills/workflow-protocol/references/command-reference.md:460`
- **Baseline Reference**: `skills/doc-guardian/SKILL.md:190`, `skills/doc-guardian/SKILL.md:191`, `skills/doc-guardian/references/change-log-format.md:216`, `skills/doc-guardian/references/change-log-format.md:218`
- **Issue**: bug-triage 写 “validate pass 是 incident-start 前置（progress.py 内部 validate INCIDENT 文件）”；workflow-evolution 写 “progress.py incident-resolve 会再次 validate INCIDENT 文件”。但 workflow-protocol command-reference 的 `incident-start` 前置只写 incident file 存在且为合法 skeleton，`incident-resolve` 前置只写 workflow incident active 与 resolution_action 已标注，没有明确调用 `validate.py file <incident>`。
- **Impact**: Task 6 实现 progress.py 时会以 command-reference 为准，可能不会实现二次 validate；而 batch2 skill 作者会以为有双重保险。这个错位会放大 F5 idempotency 风险，也会让错误 INCIDENT 在 caller 漏 validate 时仍进入 progress mutation。
- **Recommendation**: 二选一并同步全部文件：A) 在 command-reference `incident-start` 与 `incident-resolve` 前置中明确调用 `skills/doc-guardian/scripts/validate.py file <incident-path>`，失败则拒绝；B) 删除 batch2 文档中的“progress.py 内部再次 validate”表述，改为“caller 必须先 validate，progress.py 只校验必要 frontmatter fields”。推荐 A，因它与本轮 F1/F5 的 double-safety 设计一致。

### Low: workflow-evolution 端到端 examples 跳过 finalization block，示例层没有展示 Step 6.a-g

- **Location**: `skills/workflow-evolution/references/incident-analysis-template.md:439`, `skills/workflow-evolution/references/incident-analysis-template.md:448`, `skills/workflow-evolution/references/incident-analysis-template.md:503`, `skills/workflow-evolution/references/incident-analysis-template.md:514`, `skills/workflow-evolution/references/incident-analysis-template.md:565`, `skills/workflow-evolution/references/incident-analysis-template.md:576`
- **Baseline Reference**: `skills/workflow-evolution/references/incident-analysis-template.md:262`, `skills/workflow-evolution/references/incident-analysis-template.md:283`, `skills/workflow-evolution/SKILL.md:87`, `skills/workflow-evolution/SKILL.md:100`
- **Issue**: Example A/B/C 都从 §7 Resolution 直接展示 `incident-resolve --action ...` 的效果，没有示范 “frontmatter status/resolution_action/updated → Pending entry → changelog.py promote → validate.py file” 这一最终序列。
- **Impact**: 主模板已足够，故不阻塞；但 examples 是实现者最可能复制的路径，示例跳步会削弱 F5 修复的记忆点。
- **Recommendation**: 在每个 example 的 §7 Resolution 与 `incident-resolve` 结果之间加一行或小段：`Run finalization sequence (§1.6): update frontmatter + Pending entry → changelog.py promote → validate.py file → only then progress.py incident-resolve`。

## Cross-Finding Consistency Check

- **三层前置 gate**: scenario-dispatcher 已在 SKILL、decision flow、Example I 统一 reject 非 testing active bug；bug-triage 主文档前置也正确。但 bug-triage metadata description 与 triage-decision-tree 顶层伪代码仍需同步，否则 dispatcher → bug-triage → progress.py 三层 gate 不是全文一致。
- **changelog promote / validate 顺序**: Active BUG、post-close BUG、INCIDENT skeleton、workflow-evolution finalization 的主流程均采用 “promote → validate → progress.py”。残留问题集中在 examples/templates：root-cause-rubric Example E、post-close BUG template 的 Pending section、workflow-evolution examples。
- **Action Item 标注**: Incident mode §4 的规则已修；retrospective consumption mode 的 output template 仍未按每条 advice 标注 Action Item，也没有与 incident mode 同等的 no patch/diff notice。
- **Forbidden Actions 覆盖**: 三个 SKILL.md 的新增 Forbidden 基本覆盖 round 1 修复点；F2/F5 的问题不是 Forbidden 缺失，而是入口伪代码、description、idempotency/recovery 与 Forbidden/主流程不同步。
- **progress.py 二次 validate**: batch2 skill 文档依赖“progress.py 会再次 validate INCIDENT”的说法，但 batch1 command-reference 未给出同等前置。需要在 batch1 reference 或 batch2 skill 文案中选定一个权威说法。

## Recommendation

- **(B)**: 修后再评（再评 1 轮）。本轮没有发现新的 High blocker，Round 1 的核心设计方向也基本落地；但 F1/F2/F4/F5 仍有多处文档同步残留，尤其是 active-mode early gate、retrospective Action Item、incident finalization idempotency 与 progress.py 二次 validate 契约。建议小 patch 后再做一次 focused regression；不建议直接进 batch 3。
