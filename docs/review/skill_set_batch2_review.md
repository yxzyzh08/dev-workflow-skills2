# Skill Set Batch 2 Review (scenario-dispatcher + bug-triage + workflow-evolution)

**Review Target**: `skills/scenario-dispatcher/SKILL.md`, `skills/scenario-dispatcher/references/scenario-decision-tree.md`, `skills/bug-triage/SKILL.md`, `skills/bug-triage/references/root-cause-rubric.md`, `skills/bug-triage/references/triage-decision-tree.md`, `skills/workflow-evolution/SKILL.md`, `skills/workflow-evolution/references/incident-analysis-template.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Batch 1 Reference**: `skills/workflow-protocol/SKILL.md` + `skills/doc-guardian/SKILL.md` (round 5 闭环)  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: blocking issues: 3 High; 2 Medium; recommendation: (B) fix and re-review before batch 3

## Findings

### High: PRD-exception incident skeleton 会因 Pending Changes 未 promote 而无法通过 doc-guardian

- **Dimensions**: Spec / Design 一致性, 跨 skill 协作一致性, Output Contract 严格性, 可实现性
- **Location**: `skills/bug-triage/SKILL.md:93`, `skills/bug-triage/SKILL.md:241`, `skills/bug-triage/SKILL.md:254`, `skills/bug-triage/references/triage-decision-tree.md:440`, `skills/bug-triage/references/triage-decision-tree.md:471`, `skills/bug-triage/references/triage-decision-tree.md:478`
- **Baseline Reference**: `skills/doc-guardian/references/change-log-format.md:18`, `skills/doc-guardian/references/change-log-format.md:191`, `skills/doc-guardian/references/change-log-format.md:193`, `skills/workflow-protocol/references/command-reference.md:422`, `skills/workflow-protocol/references/command-reference.md:424`
- **Issue**: `workflow-incident` 是增量类 doc，`validate.py` 类 6 要求 `## Pending Changes` 为空；但 bug-triage 的 INCIDENT skeleton 模板保留未 promote 的 Pending entry，且 PRD-exception 流程只写“创建 skeleton → validate.py file → incident-start”，没有对 INCIDENT skeleton 调 `changelog.py promote`。更糟的是 triage reference 一边在模板里保留 Pending entry，一边在 skeleton validate 说明里要求“首条已 promote”。
- **Impact**: Task 6 若按此实现，`validate.py file <incident-path>` 会拒绝 skeleton，`progress.py incident-start` 前置也无法通过，整个 `prd-exception → workflow-evolution` 路径不可达。
- **Recommendation**: 在 bug-triage PRD-exception 分支中明确：创建 INCIDENT skeleton 后必须先运行 `skills/doc-guardian/scripts/changelog.py promote <incident-path>`，让 Pending entry 移入 Change Log，再运行 `validate.py file`。同时修正 skeleton 模板，展示 promote 后的空 `## Pending Changes` + `## Change Log` 中的创建 entry；或如果 skeleton 被定义为一次性 doc，则必须先修改 doc-guardian change-log policy，但不建议为此开例外。

### High: active release 非 testing 阶段报 bug 的路由与 `bug-start` 前置冲突，且“known-issue”记录无状态契约

- **Dimensions**: Spec / Design 一致性, 跨 skill 协作一致性, 决策树完整性, 边界状态处理, 可实现性
- **Location**: `skills/scenario-dispatcher/SKILL.md:75`, `skills/scenario-dispatcher/SKILL.md:115`, `skills/scenario-dispatcher/SKILL.md:143`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:241`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:285`, `skills/bug-triage/SKILL.md:42`, `skills/bug-triage/SKILL.md:48`, `skills/bug-triage/SKILL.md:88`, `skills/bug-triage/references/triage-decision-tree.md:574`, `skills/bug-triage/references/triage-decision-tree.md:594`, `skills/bug-triage/references/triage-decision-tree.md:601`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:347`, `skills/workflow-protocol/references/command-reference.md:351`, `skills/workflow-protocol/references/command-reference.md:353`, `docs/design/skill_set_design_proposal_v0.5.md:329`, `docs/design/skill_set_design_proposal_v0.5.md:332`
- **Issue**: scenario-dispatcher 和 bug-triage 主文档允许“active release 其他 stage 用户主动报 bug”进入 bug-triage active mode；但 batch 1 的 `bug-start` 明确要求 `current_stage == testing` 且 `sub_state == review-passed`。triage-decision-tree Example B 认识到 `bug-start` 会拒绝，于是改成创建 `target_release="0.4", root_cause=null` 的 known-issue BUG 并“不调 progress.py”。这个 known-issue 不进 `unresolved_bugs`、不进 `bug_flow`、不被 required-artifacts 引用，也没有 schema 字段表示“testing scope reminder”。
- **Impact**: 三份文档给实现者三种不兼容选择：直接 triage 并调用会失败的 `bug-start`；创建无 progress 状态承载的 orphan BUG；或拒绝到 testing 再处理。下游 stage/Bootstrap 无法知道这个 known-issue 何时重新触发 triage，可能丢 bug 或重复建 BUG。
- **Recommendation**: 收敛为一个确定路径。建议 Option A：active mode **只允许** `current_stage==testing AND sub_state==review-passed`，scenario-dispatcher 在其他 active stage 一律拒绝，并提示“等 testing 阶段由 testing-write 创建 BUG report”。Option B：正式新增 known-issue queue/字段/required handoff（需要 progress.md schema 或 BUG schema 扩展），但这触及 batch 1 设计，不建议本轮引入。

### High: root-cause-rubric 引入“非真 bug / out of SRS scope”第五路径，但 schema 和 progress.py 没有承载方式

- **Dimensions**: Spec / Design 一致性, Output Contract 严格性, 决策树完整性, 可实现性, 边界状态处理
- **Location**: `skills/bug-triage/SKILL.md:83`, `skills/bug-triage/SKILL.md:89`, `skills/bug-triage/SKILL.md:130`, `skills/bug-triage/references/root-cause-rubric.md:418`, `skills/bug-triage/references/root-cause-rubric.md:436`, `skills/bug-triage/references/root-cause-rubric.md:437`, `skills/bug-triage/references/root-cause-rubric.md:440`, `skills/bug-triage/references/root-cause-rubric.md:442`
- **Baseline Reference**: `skills/doc-guardian/references/frontmatter-schema.md:299`, `skills/workflow-protocol/references/command-reference.md:353`, `skills/workflow-protocol/references/command-reference.md:423`, `docs/design/skill_set_design_proposal_v0.5.md:500`, `docs/design/skill_set_design_proposal_v0.5.md:501`
- **Issue**: bug-triage 的主契约是 active mode 判定 4 类 root cause，并写入 `root_cause ∈ {srs, architecture, development, prd-exception}` 后调用 `bug-start` 或 `incident-start`。但 root-cause-rubric Example D 说某些用户反馈“不应进 Bug Flow”，应“关闭 BUG report / documented limitation”，且不调 progress.py。batch 1 的 `bug-report` schema 没有 `closed/rejected/out_of_scope/final_status` 字段，`progress.py` 也没有关闭未进入 bug_flow 的 BUG 的子命令。
- **Impact**: 实现者无法判断 active BUG report 发现 out-of-scope 时应该写什么 frontmatter、是否允许 `root_cause` 保持 null、是否需要 progress-history entry、后续是否会被 Bootstrap 当作未完成 triage 重试。该路径会制造长期悬挂的 BUG 文档或诱导实现者私自扩展 schema。
- **Recommendation**: 二选一：A) 删除 Example D 的“关闭 BUG”路径，把它改成 triage 前输入过滤：如果不是 SRS 范围内的真实 bug，不创建 BUG report；若 BUG 已由 testing-write 创建，则必须仍映射到四类之一或升级用户决策。B) 正式扩展 `bug-report` schema 与 progress.py，加入 `triage_status: rejected/out-of-scope` 等字段和关闭命令；这属于 design-level 扩展，不建议在 batch 2 临时加入。

### Medium: workflow-evolution 的递归约束与 incident 模板/自评清单互相矛盾

- **Dimensions**: 递归悖论严格性, 内部一致性, Output Contract 严格性, 可实现性
- **Location**: `skills/workflow-evolution/SKILL.md:30`, `skills/workflow-evolution/SKILL.md:102`, `skills/workflow-evolution/SKILL.md:139`, `skills/workflow-evolution/SKILL.md:368`, `skills/workflow-evolution/SKILL.md:370`, `skills/workflow-evolution/SKILL.md:374`, `skills/workflow-evolution/references/incident-analysis-template.md:75`, `skills/workflow-evolution/references/incident-analysis-template.md:82`, `skills/workflow-evolution/references/incident-analysis-template.md:91`, `skills/workflow-evolution/references/incident-analysis-template.md:117`, `skills/workflow-evolution/references/incident-analysis-template.md:354`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:42`, `docs/design/skill_set_design_proposal_v0.5.md:44`, `docs/design/skill_set_design_proposal_v0.5.md:815`
- **Issue**: workflow-evolution 必须填写 §4 Workflow Improvement Suggestions，模板明确让它针对 `docs/workflow/workflow_specification_claude.md` 和 `skills/<name>/SKILL.md` 给出改进建议，并注明走 dev-workflow-skills2 design proposal cycle；但 SKILL §8.2 又说“不应写‘修改 skills/<name>/SKILL.md 章节 X’类建议”，自评清单也把“本 INCIDENT 是否提议修改 dev-workflow-skills2 自身文件”通过标准写成“否”。这会让任何具体的 workflow/skill 改进建议都可能被自评判失败。
- **Impact**: 实现者会在两个方向分叉：要么输出空泛建议以通过递归检查，破坏 §4 的价值；要么输出具体建议但无法通过自评，阻塞 incident-resolve。递归悖论应禁止“直接 patch 自身”，不应禁止“以 design proposal 形式提出改进建议”。
- **Recommendation**: 统一措辞：允许 workflow-evolution 在 §4 提出**advisory** 改进建议，但必须标注“提交到 dev-workflow-skills2 独立 design proposal review cycle”，且禁止输出 patch/diff 或直接编辑文件。将 §8.2 和 checklist #13 改为“是否直接修改 / 输出可直接应用的 patch 到 dev-workflow-skills2 文件：否”。

### Medium: workflow-evolution 设置 `status: review-passed` 的顺序会让最终 INCIDENT 逃过 changelog/validate

- **Dimensions**: 内部一致性, Output Contract 严格性, 可实现性, Forbidden Actions 完整性
- **Location**: `skills/workflow-evolution/SKILL.md:87`, `skills/workflow-evolution/SKILL.md:89`, `skills/workflow-evolution/SKILL.md:90`, `skills/workflow-evolution/SKILL.md:91`, `skills/workflow-evolution/SKILL.md:121`, `skills/workflow-evolution/SKILL.md:123`, `skills/workflow-evolution/SKILL.md:150`, `skills/workflow-evolution/SKILL.md:152`, `skills/workflow-evolution/SKILL.md:155`, `skills/workflow-evolution/SKILL.md:310`, `skills/workflow-evolution/SKILL.md:312`
- **Baseline Reference**: `skills/doc-guardian/SKILL.md:271`, `skills/doc-guardian/SKILL.md:278`, `skills/doc-guardian/references/change-log-format.md:18`, `skills/doc-guardian/references/change-log-format.md:191`, `skills/workflow-protocol/references/command-reference.md:456`, `skills/workflow-protocol/references/command-reference.md:459`
- **Issue**: Incident flow Step 6 写 `resolution_action` 后先 `changelog.py promote → validate.py file → 全 pass`，再“设 INCIDENT frontmatter status: review-passed”。这意味着最后一次 status frontmatter mutation 发生在 validate 之后，且没有明确添加 Pending Changes / promote / 再 validate。Output Contract 又要求 workflow-evolution 改 `status: draft → review-passed` 和 `resolution_action`，但没有给出原子顺序。
- **Impact**: Task 6 若照此实现，`incident-resolve` 前最终 INCIDENT 文件可能含未记录的 frontmatter 改动，或最终状态未经过 `validate.py file`。这会绕开 doc-guardian 的 change-log discipline，与 batch 1 的“编辑完 doc → promote → validate → workflow-protocol 才允许推进”不一致。
- **Recommendation**: 明确单一顺序：完成 §3-§7、设置 `resolution_action`、设置 `status: review-passed`、为所有 frontmatter/body 变更写 Pending Changes，然后运行 `changelog.py promote <incident>`，最后运行 `validate.py file <incident>`，仅在 validate pass 后调 `progress.py incident-resolve --action <enum>`。

## Cross-Skill Consistency Check

- **scenario-dispatcher → bug-triage**: closed-release bug 路径与 `bug-intake` 对齐；active testing bug 路径与 `bug-start` 对齐；active non-testing bug 路径未对齐，是当前最大跨 skill 路由问题。
- **bug-triage → workflow-protocol**: `bug-start --bug --root-cause`、`incident-start --bug --report` 的签名与 batch 1 command-reference 对齐；但 bug-start 的 `current_stage==testing` 前置没有在主 active-mode contract 中被严格执行。
- **bug-triage → doc-guardian**: `bug-report` 五个字段和 `workflow-incident.triggered_by_bug` ID 字符串基本对齐；但 INCIDENT skeleton 未 promote 就 validate，与 doc-guardian change-log discipline 冲突。
- **bug-triage → workflow-evolution**: INCIDENT body 责任分工总体清楚（bug-triage §1-§2/skeleton，workflow-evolution §3-§7）；但 skeleton 的 Pending/Change Log 状态不一致，会阻断 handoff。
- **workflow-evolution → workflow-protocol**: `incident-resolve --action continue|abort|reconstruct` 签名与 mutation 概要对齐；没有 `--bug-flow keep|clear` 残留。
- **workflow-evolution → dev-workflow-skills2**: 递归悖论方向正确（不直接 patch 自身），但“允许 advisory suggestion”与“禁止提议修改自身文件”的边界需要重写。

## Implementability Assessment

当前不建议直接进入 Task 6 或 batch 3，因为三个 High 会让实现者在真实流程中卡住或自创状态：

- **scenario-dispatcher**: S1/S2/S3/closed-post bug 基本可实现；active non-testing bug intent 的输出不确定，必须收敛为 reject 或正式 known-issue queue。
- **bug-triage**: Stage 5 testing active mode 的四类 root cause 主路径可实现；PRD-exception handoff 因 INCIDENT changelog 未 promote 会失败；out-of-scope “非真 bug”路径没有 schema/progress 承载。
- **workflow-evolution**: 3 action matrix 和 incident-resolve 调用基本可实现；但递归约束与 §4 模板/自评冲突，且 INCIDENT finalization 的 promote/validate 顺序需要明确。

可实现性上的剩余语义模糊点：

- active release 非 testing 阶段用户报 bug：是否创建 BUG、写哪些字段、何时触发 triage。
- “非 bug / out of SRS scope”是否允许出现在已经创建的 BUG report 中；若允许，状态如何关闭。
- workflow-evolution 的 §4 建议到底是可写的 advisory 产物，还是被递归约束禁止。
- INCIDENT frontmatter 和 body 多次编辑的 changelog/validate 原子顺序。

## Recursion Paradox Compliance

workflow-evolution 有清晰的递归悖论意识：禁止直接修改 `dev-workflow-skills2` 自身文件、禁止输出 patch/diff、要求走独立 design proposal cycle。这是正确方向。

残留 bypass / 矛盾：

- §4 模板要求列出 workflow spec / skill / template / rubric 具体改进，但 §8.2 和 self-eval #13 可能把这些 advisory 建议误判为违规。
- Retrospective conversation 模板同样列 “Skill Suggestions / Template Suggestions”，需要明确它们只能是 design proposal 输入，不能由 workflow-evolution 持久化或 patch。
- 如果用户直接要求“按 §4 建议修改 dev-workflow-skills2”，SKILL §8.3 已给拒绝模板；该点覆盖充分。

结论：递归悖论的防 patch 规则基本完整，但必须修正文案，避免禁止合法的 advisory 改进建议。

## Positive Notes

- 三个 skill 的 authority 均为 4，与 batch 1 authority hierarchy 一致。
- `incident-start --bug --report`、`incident-resolve --action continue|abort|reconstruct`、`bug-intake --bug` 等命令签名总体已同步 batch 1 round 5。
- `triggered_by_bug` 在 bug-triage、workflow-evolution、doc-guardian 中基本一致为 BUG ID 字符串，而不是路径。
- post-close bug intake 的 `target_release: null` / `consumed_in_release: null` 与 release-start consume 语义对齐。
- `workflow-evolution` 明确不支持 `--bug-flow keep|clear`，continue 后创建新 BUG 的决策与 batch 1 一致。

## Suggested Next Revision Order

1. **High / 小 patch**: 修 bug-triage PRD-exception skeleton 流程：创建 INCIDENT 后 `changelog.py promote`，模板展示 promote 后状态，再 validate，再 incident-start。
2. **High / 中 patch**: 统一 active non-testing bug 路径。建议直接改为 reject/延后到 testing；同步 scenario-dispatcher SKILL、scenario-decision-tree、bug-triage SKILL、triage-decision-tree Example B。
3. **High / 中 patch**: 删除或重写 root-cause-rubric “非真 bug close”路径，确保 active BUG report 只有 4 类 root_cause 输出；若要保留关闭语义，需先回 design 扩 schema。
4. **Medium / 小 patch**: 重写 workflow-evolution 递归约束：允许 advisory 建议，禁止 direct patch；同步 §8.2、self-eval #13、incident template §4。
5. **Medium / 小 patch**: 明确 workflow-evolution INCIDENT finalization 顺序：body + resolution_action + status + Pending entry → promote → validate → incident-resolve。

## Recommendation

- **(B)**: 修后再评（再评 1 轮）。当前存在 3 个 High：PRD-exception incident handoff 不可达、active non-testing bug 路由无合法 state、out-of-scope bug 第五路径无 schema/progress 承载；不修不能进 batch 3。
