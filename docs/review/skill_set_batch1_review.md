# Skill Set Batch 1 Review (workflow-protocol + doc-guardian)

**Review Target**: `skills/workflow-protocol/SKILL.md`, `skills/workflow-protocol/references/command-reference.md`, `skills/doc-guardian/SKILL.md`, `skills/doc-guardian/references/frontmatter-schema.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.5)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: blocking issues: 8; needs fix before Task 5 batch 2

## Findings

### High: doc-guardian SKILL references 3 个不存在的关键 reference，Task 6 无法取得目录、Change Log 和 required artifacts 契约

- **Dimensions**: 完整性, 可实现性, 跨 skill 引用一致性
- **Location**: `skills/doc-guardian/SKILL.md:6`, `skills/doc-guardian/SKILL.md:7`, `skills/doc-guardian/SKILL.md:8`, `skills/doc-guardian/SKILL.md:9`, `skills/doc-guardian/SKILL.md:20`, `skills/doc-guardian/SKILL.md:23`, `skills/doc-guardian/SKILL.md:26`, `skills/doc-guardian/SKILL.md:27`, `skills/doc-guardian/SKILL.md:351`, `skills/doc-guardian/SKILL.md:353`, `skills/doc-guardian/SKILL.md:354`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:730`, `docs/design/skill_set_design_proposal_v0.5.md:736`, `docs/design/skill_set_design_proposal_v0.5.md:738`, `docs/design/skill_set_design_proposal_v0.5.md:739`
- **Issue**: `directory-layout.md`、`change-log-format.md`、`required-artifacts.md` 被 frontmatter 和正文声明为完整契约来源，但当前仓库只存在 `frontmatter-schema.md`。尤其 `required-artifacts.md` 是 `progress.py update --advance` 与 `validate.py` 场景感知校验的依赖源，缺失后只能靠 SKILL.md 内的“高频示例”推断。
- **Impact**: Task 6 实现者不能按图施工实现 Path/Naming、Change Log Discipline、Required Artifacts 三类核心校验；skill loader 或人工读者也会打开断链 reference。
- **Recommendation**: 补齐 3 个 reference，且内容至少覆盖设计 §5.1、§5.2、§5.7 与 P6 required artifacts；如果 batch 1 有意只交付 4 份文件，则从 `SKILL.md` frontmatter 和正文删除这些断链，并把必须实现的契约完整内联到现有目标文件中。

### High: PRD root-cause exception 的 incident-start 状态不可达，且 Workflow Incident Report 的创建者矛盾

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:193`, `skills/workflow-protocol/SKILL.md:200`, `skills/workflow-protocol/SKILL.md:207`, `skills/workflow-protocol/SKILL.md:208`, `skills/workflow-protocol/references/command-reference.md:267`, `skills/workflow-protocol/references/command-reference.md:277`, `skills/workflow-protocol/references/command-reference.md:337`, `skills/workflow-protocol/references/command-reference.md:343`, `skills/workflow-protocol/references/command-reference.md:344`, `skills/workflow-protocol/references/command-reference.md:345`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:401`, `docs/workflow/workflow_specification_claude.md:407`, `docs/workflow/workflow_specification_claude.md:409`, `docs/workflow/workflow_specification_claude.md:417`, `docs/design/skill_set_design_proposal_v0.5.md:331`, `docs/design/skill_set_design_proposal_v0.5.md:335`, `docs/design/skill_set_design_proposal_v0.5.md:353`, `docs/design/skill_set_design_proposal_v0.5.md:356`, `docs/design/skill_set_design_proposal_v0.5.md:507`, `docs/design/skill_set_design_proposal_v0.5.md:508`
- **Issue**: `bug-start` 明确只接受 `{srs, architecture, development}`，并注释 `prd-exception` 走 `incident-start`；但 `incident-start` 前置又要求 `bug_flow.active == true` 且 `bug_flow.root_cause == prd-exception`。当前 11 个子命令中没有任何命令能先设置这两个字段为 prd-exception 状态，因此该分支不可达。同时 SKILL.md 说 workflow-evolution “产出 Workflow Incident Report”，command reference 却要求 `<incident-report-path>` 已由 bug-triage 创建。
- **Impact**: Task 6 无法实现一个可通过自身前置条件的 PRD exception 路径；实现者要么放宽 `incident-start`，要么让 `bug-start` 接受 prd-exception，二者会产生不兼容实现。
- **Recommendation**: 选定一种状态模型并写成确定性 mutation。选项 A：允许 `bug-start --root-cause prd-exception` 设置 `bug_flow.active/root_cause` 后立即要求 `incident-start`。选项 B：让 `incident-start --bug <BUG> --report <INCIDENT>` 自身从 `current_stage=testing`、BUG frontmatter `root_cause: prd-exception` 创建 incident state，并移除 `bug_flow.active==true` 前置。另需明确 incident report 是 bug-triage 创建 skeleton 后 workflow-evolution 填充，还是 workflow-evolution 在 incident-start 后创建；命令前置要与此一致。

### High: `incident-resolve --action continue` 的 `bug_flow` mutation 仍是 prose，不能确定性实现

- **Dimensions**: Spec/Design 一致性, 完整性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/references/command-reference.md:376`, `skills/workflow-protocol/references/command-reference.md:383`, `skills/workflow-protocol/references/command-reference.md:386`, `skills/doc-guardian/references/frontmatter-schema.md:249`, `skills/doc-guardian/references/frontmatter-schema.md:256`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:365`, `docs/design/skill_set_design_proposal_v0.5.md:369`, `docs/design/skill_set_design_proposal_v0.5.md:371`, `docs/design/skill_set_design_proposal_v0.5.md:372`, `docs/review/reviewer_feedback_response_v0.4.md:65`, `docs/review/reviewer_feedback_response_v0.4.md:73`
- **Issue**: `continue` 分支只写“bug_flow 视用户决策保留或清空”，但命令只有 `--action continue`，workflow-incident frontmatter 也只有 `resolution_action`，没有可机读字段告诉 `progress.py` 是 keep 还是 clear、清空时 BUG report 如何标记、保留时下一步回到 testing retest 还是继续修原 bug。
- **Impact**: v0.4 已要求补精确 mutation，当前仍留下实现者必须自行决策的核心状态字段；不同实现会在 incident 继续后产生不同 `bug_flow.active` 与 next action。
- **Recommendation**: 增加显式参数或 report 字段，例如 `incident-resolve --action continue --bug-flow keep|clear`，并分别定义 `bug_flow.active/root_cause/bug_report_path`、BUG report status、`current_stage/sub_state`、history next 的精确 mutation；或禁止 clear，统一保留 bug_flow 并回到 Stage 5 retest。

### High: P6 `--advance` 的 artifact 来源不完整，progress.md 只列 Stage 1-3 部分路径却要求校验 Stage 4-7 产物

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 可实现性
- **Location**: `skills/workflow-protocol/SKILL.md:76`, `skills/workflow-protocol/SKILL.md:77`, `skills/workflow-protocol/SKILL.md:78`, `skills/workflow-protocol/SKILL.md:79`, `skills/workflow-protocol/SKILL.md:80`, `skills/workflow-protocol/SKILL.md:81`, `skills/workflow-protocol/SKILL.md:82`, `skills/workflow-protocol/SKILL.md:156`, `skills/workflow-protocol/SKILL.md:171`, `skills/workflow-protocol/SKILL.md:172`, `skills/workflow-protocol/SKILL.md:173`, `skills/workflow-protocol/SKILL.md:174`, `skills/workflow-protocol/references/command-reference.md:111`, `skills/workflow-protocol/references/command-reference.md:112`, `skills/doc-guardian/SKILL.md:289`, `skills/doc-guardian/SKILL.md:291`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:191`, `docs/workflow/workflow_specification_claude.md:201`, `docs/workflow/workflow_specification_claude.md:218`, `docs/workflow/workflow_specification_claude.md:227`, `docs/workflow/workflow_specification_claude.md:244`, `docs/workflow/workflow_specification_claude.md:252`, `docs/workflow/workflow_specification_claude.md:265`, `docs/workflow/workflow_specification_claude.md:274`, `docs/design/skill_set_design_proposal_v0.5.md:458`, `docs/design/skill_set_design_proposal_v0.5.md:472`, `docs/design/skill_set_design_proposal_v0.5.md:478`
- **Issue**: `progress.md artifacts:` 只包含 PRD、Architecture、SRS、Acceptance Plan、Integration Plan、Architecture Delta；但 P6 矩阵要求 Stage 4 Development、Stage 5 Testing、Stage 6 Delivery、Stage 7 Retrospective 的产物也要 `validate.py file <each artifact>`。当前没有说明这些 artifact 是从 progress.md 读取、从 doc-guardian path map 派生，还是由缺失的 `required-artifacts.md` 提供。
- **Impact**: `progress.py update --advance` 无法确定 “each artifact” 的枚举来源，Stage 5/6/7 的 B/E 维度实现会分叉；某些实现可能只校验 `artifacts:` 中已有字段，导致后半流程漏校验。
- **Recommendation**: 二选一。方案 A：扩展 `progress.md artifacts:`，纳入 development_plan、task_breakdown、test_preparation、test_procedure、test_report、deployment_doc、operation_manual、installation_result、retrospective/issue/proposal 等路径，并定义 optional/null 规则。方案 B：明确 `artifacts:` 只存可变路径，`update --advance` 必须调用 doc-guardian 的 required-artifacts map 按 release/stage/task 推导标准路径；同时补齐 `required-artifacts.md`。

### High: S3 Stage 2 source-system-analysis 必备清单在 4 份文件与 baseline 间不一致

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 可实现性
- **Location**: `skills/workflow-protocol/SKILL.md:168`, `skills/workflow-protocol/SKILL.md:169`, `skills/doc-guardian/SKILL.md:313`, `skills/doc-guardian/SKILL.md:317`, `skills/doc-guardian/SKILL.md:318`, `skills/doc-guardian/SKILL.md:319`, `skills/doc-guardian/SKILL.md:320`, `skills/doc-guardian/references/frontmatter-schema.md:274`, `skills/doc-guardian/references/frontmatter-schema.md:278`, `skills/doc-guardian/references/frontmatter-schema.md:279`, `skills/doc-guardian/references/frontmatter-schema.md:280`, `skills/doc-guardian/references/frontmatter-schema.md:281`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:141`, `docs/workflow/workflow_specification_claude.md:142`, `docs/workflow/workflow_specification_claude.md:143`, `docs/workflow/workflow_specification_claude.md:144`, `docs/design/skill_set_design_proposal_v0.5.md:472`, `docs/design/skill_set_design_proposal_v0.5.md:473`, `docs/design/skill_set_design_proposal_v0.5.md:695`, `docs/design/skill_set_design_proposal_v0.5.md:700`, `docs/design/skill_set_design_proposal_v0.5.md:702`
- **Issue**: workflow-protocol P6 Stage 2 写 “S3 4 类源系统分析”；workflow spec v0.5 也把 Technical Debt and Risk Analysis 标为 S3 必备。但 doc-guardian SKILL 与 frontmatter-schema 把 `technical-debt` 标为推荐。设计 v0.5 自身也存在 §4.9 的 “S3 4 类” 与 §5.3 的 “Stage 2 必备 3 类”冲突，目标文件没有消解该冲突。
- **Impact**: `validate.py` 和 `progress.py update --advance` 对 S3 Stage 2 是否必须存在 `technical_debt_analysis.md` 会实现不一致；S3 项目可能在一个脚本 pass、另一个脚本 fail。
- **Recommendation**: 在 Task 5 目标文件中明确采用一个权威口径。若以 workflow spec 和 P6 矩阵为准，则将 `technical-debt` 改为 Stage 2 必备，并同步 doc-guardian §7.3、frontmatter table、required-artifacts map。若坚持“推荐”，则需先修订 workflow spec 与 P6 矩阵，把 “4 类” 改为 “3 必备 + 1 推荐”。

### High: frontmatter per-type 必含表遗漏 bug-report / workflow-incident 的 v0.5 字段，且与同文件上文自相矛盾

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 可实现性
- **Location**: `skills/doc-guardian/SKILL.md:157`, `skills/doc-guardian/SKILL.md:158`, `skills/doc-guardian/SKILL.md:159`, `skills/doc-guardian/references/frontmatter-schema.md:237`, `skills/doc-guardian/references/frontmatter-schema.md:243`, `skills/doc-guardian/references/frontmatter-schema.md:244`, `skills/doc-guardian/references/frontmatter-schema.md:245`, `skills/doc-guardian/references/frontmatter-schema.md:249`, `skills/doc-guardian/references/frontmatter-schema.md:256`, `skills/doc-guardian/references/frontmatter-schema.md:329`, `skills/doc-guardian/references/frontmatter-schema.md:344`, `skills/doc-guardian/references/frontmatter-schema.md:345`, `skills/doc-guardian/references/frontmatter-schema.md:346`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:687`, `docs/design/skill_set_design_proposal_v0.5.md:688`, `docs/design/skill_set_design_proposal_v0.5.md:689`
- **Issue**: 详细 schema 正文要求 `bug-report` 具备 `target_release/root_cause/consumed_in_release`，`workflow-incident` 具备 `resolution_action`；doc-guardian SKILL 简表也列了这些字段。但 `frontmatter-schema.md` 的“Per-Type 字段必含表”只把 `bug-report` 写成 `bug_id, found_in_release`，把 `workflow-incident` 写成 `incident_id, triggered_by_bug, triggered_in_release`，还把 `source-system-analysis` 的 `release` 从必含扩展中弱化为“按 analysis_kind 决定”。
- **Impact**: Task 6 若按 cheat sheet 实现 `validate.py`，会接受缺少 v0.5 关键字段的 BUG/INCIDENT 文档；若按详细 schema 实现，则与“验收 cheat sheet”冲突。
- **Recommendation**: 将 §5 必含表改为与设计 §5.3 和本文件详细 schema 完全一致：`bug-report` 必含 `bug_id`, `found_in_release`, `target_release`, `root_cause`, `consumed_in_release`；`workflow-incident` 必含 `incident_id`, `triggered_by_bug`, `triggered_in_release`, `resolution_action`；`source-system-analysis` 必含 `release`, `analysis_kind`, `source_system_name`，其中 `release` 值可为 null 但字段必须存在。

### High: Stage 4 task state machine 依赖 “Tests doc-guardian + review-passed”，但 doc-guardian 没有任何 per-task tests doc type/path/schema

- **Dimensions**: Spec/Design 一致性, 内部一致性, 完整性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:184`, `skills/workflow-protocol/SKILL.md:186`, `skills/workflow-protocol/SKILL.md:187`, `skills/workflow-protocol/SKILL.md:260`, `skills/workflow-protocol/SKILL.md:264`, `skills/workflow-protocol/references/command-reference.md:65`, `skills/workflow-protocol/references/command-reference.md:447`, `skills/doc-guardian/SKILL.md:76`, `skills/doc-guardian/SKILL.md:80`, `skills/doc-guardian/SKILL.md:81`, `skills/doc-guardian/SKILL.md:82`, `skills/doc-guardian/references/frontmatter-schema.md:184`, `skills/doc-guardian/references/frontmatter-schema.md:223`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:197`, `docs/workflow/workflow_specification_claude.md:198`, `docs/workflow/workflow_specification_claude.md:199`, `docs/workflow/workflow_specification_claude.md:201`, `docs/design/skill_set_design_proposal_v0.5.md:480`, `docs/design/skill_set_design_proposal_v0.5.md:490`, `docs/design/skill_set_design_proposal_v0.5.md:491`, `docs/design/skill_set_design_proposal_v0.5.md:492`, `docs/design/skill_set_design_proposal_v0.5.md:493`
- **Issue**: workflow-protocol 要求 task 从 `test-writing` 到 `test-done` 经过 Tests doc-guardian + review-passed，但 doc-guardian 只定义了 per-task `detailed-design`、`code-review-report`、`verification-result`。没有 test cases / test plan / test review report 的 doc type、路径、frontmatter 或 review_status 字段。
- **Impact**: `progress.py update --task <Tn> --status test-done` 无法知道应校验哪个文件、哪个 frontmatter status、哪个 review report；并发子 agent 更新 task 状态时也缺少完整的单调状态转移表和 expected-from guard，可能出现过期 agent 把任务状态回退或跳跃的实现分歧。
- **Recommendation**: 增加 per-task tests artifact 契约，例如 `test-cases` / `test-review-report` 的路径、frontmatter、review-passed 判定；或改写 Stage 4 task 矩阵，说明 “Tests” 是代码仓库测试文件而非 doc-guardian 文档，并定义由哪个 verification artifact 表达 review 通过。另建议 `update --task` 支持 `--from <expected>` 或明确拒绝非单调/跳跃转换。

### High: `update --field` 过宽，能绕过 dedicated subcommands 与 Forbidden Actions 修改受保护状态

- **Dimensions**: 完整性, 可实现性, Forbidden Actions 完整性
- **Location**: `skills/workflow-protocol/references/command-reference.md:62`, `skills/workflow-protocol/references/command-reference.md:63`, `skills/workflow-protocol/references/command-reference.md:68`, `skills/workflow-protocol/references/command-reference.md:72`, `skills/workflow-protocol/SKILL.md:266`, `skills/workflow-protocol/SKILL.md:268`, `skills/workflow-protocol/SKILL.md:270`, `skills/workflow-protocol/SKILL.md:274`, `skills/workflow-protocol/SKILL.md:275`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:277`, `docs/design/skill_set_design_proposal_v0.5.md:281`, `docs/design/skill_set_design_proposal_v0.5.md:293`, `docs/design/skill_set_design_proposal_v0.5.md:848`, `docs/design/skill_set_design_proposal_v0.5.md:859`, `docs/design/skill_set_design_proposal_v0.5.md:860`
- **Issue**: command reference 暴露 `progress.py update --field <name> --value <new_value>`，但没有字段白名单/黑名单。理论上 caller 可以用该入口直接改 `release_state`、`current_stage`、`bug_flow.active`、`unresolved_bugs`、`workflow_incident_active` 或 `project_state`，绕过 `release-close`、`release-start`、`bug-start`、`incident-start`、`incident-resolve` 的前置条件和 history 模板。
- **Impact**: Forbidden Actions 虽禁止手工编辑文件，但没有禁止“通过泛型 update 修改受保护字段”的 bypass；Task 6 实现若照表提供通用 `--field`，会破坏 11 个子命令 mutation 的唯一性。
- **Recommendation**: 删除泛型 `--field`，改为命名事件参数，例如 `--event write-complete|review-issues|review-passed|human-confirmed`；或保留但显式白名单只允许安全字段/状态事件，并列出受保护字段必须经 dedicated subcommand 或 `--advance`/`--task` 修改。Forbidden Actions 中同步加入“不得用 `update --field` 修改 release/bug/incident/project/artifacts 受保护字段”。

### Medium: Integration Plan 是否 Stage 2 必备存在条件性冲突，可能误阻塞单模块项目

- **Dimensions**: Spec/Design 一致性, 内部一致性, 可实现性
- **Location**: `skills/workflow-protocol/SKILL.md:169`, `skills/workflow-protocol/SKILL.md:172`, `skills/doc-guardian/SKILL.md:63`, `skills/doc-guardian/SKILL.md:65`, `skills/doc-guardian/SKILL.md:303`, `skills/doc-guardian/SKILL.md:305`, `skills/workflow-protocol/references/command-reference.md:217`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:73`, `docs/workflow/workflow_specification_claude.md:134`, `docs/design/skill_set_design_proposal_v0.5.md:473`, `docs/design/skill_set_design_proposal_v0.5.md:672`, `docs/design/skill_set_design_proposal_v0.5.md:673`
- **Issue**: workflow spec 明确 Integration Plan 是多模块或外部集成时必需；doc-guardian §7.2 也写“多模块项目”。但 workflow-protocol P6 Stage 2 row 写成无条件 `SRS + Acceptance Plan + Integration Plan`，command-reference `release-start` 又把 `artifacts.integration_plan` 初始化为 null。
- **Impact**: `progress.py update --advance` 如果按 P6 row 无条件检查，会拒绝合法的单模块 release；如果按 doc-guardian 条件检查，又与 workflow-protocol 主矩阵文字不一致。
- **Recommendation**: 把 P6 row 改成 `Integration Plan (required when multi-module or external integration)`，并定义判定来源（如 SRS frontmatter/body、task-breakdown、progress.md flag 或 required-artifacts map）。`artifacts.integration_plan: null` 应被明确定义为“不适用”而不是“缺失”。

### Medium: release-start 消费 post-close bugs 只写 `consumed_in_release`，但 BUG schema 注释要求同时填 `target_release`

- **Dimensions**: 内部一致性, 完整性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:231`, `skills/workflow-protocol/references/command-reference.md:221`, `skills/workflow-protocol/references/command-reference.md:223`, `skills/workflow-protocol/references/command-reference.md:224`, `skills/workflow-protocol/references/command-reference.md:240`, `skills/workflow-protocol/references/command-reference.md:248`, `skills/doc-guardian/references/frontmatter-schema.md:240`, `skills/doc-guardian/references/frontmatter-schema.md:243`, `skills/doc-guardian/references/frontmatter-schema.md:245`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:31`, `docs/workflow/workflow_specification_claude.md:336`, `docs/workflow/workflow_specification_claude.md:592`, `docs/design/skill_set_design_proposal_v0.5.md:318`, `docs/design/skill_set_design_proposal_v0.5.md:319`, `docs/design/skill_set_design_proposal_v0.5.md:522`
- **Issue**: command-reference 规定 `release-start` 清空 `unresolved_bugs` 并给每个 BUG 增加 `consumed_in_release`，但 frontmatter-schema 对 `target_release` 的注释写“post-close intake 时 null，下次 release-start 后填值”。没有说明 `target_release` 是否同步设为当前 release，也没有 duplicate intake / already consumed 的拒绝规则。
- **Impact**: srs-write 后续扫描应依据 `consumed_in_release` 还是 `target_release` 不明确；同一 BUG 可能被重复 intake 或重复消费。
- **Recommendation**: 规定 `release-start` 对每个 unresolved BUG 原子设置 `target_release: "<x.y>"` 与 `consumed_in_release: "<x.y>"`，或修改 schema 注释明确 target_release 保持 null、唯一消费依据是 consumed 字段。`bug-intake` 前置应增加“不在 unresolved_bugs 中、`consumed_in_release == null`、未被当前/历史 release 消费”。

### Medium: terminal project state 的 `current_stage: null` 与 `sub_state` schema 不兼容，abort/reconstruct 后可能保留脏状态

- **Dimensions**: 内部一致性, 完整性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:63`, `skills/workflow-protocol/SKILL.md:70`, `skills/workflow-protocol/SKILL.md:71`, `skills/workflow-protocol/SKILL.md:245`, `skills/workflow-protocol/SKILL.md:249`, `skills/workflow-protocol/references/command-reference.md:393`, `skills/workflow-protocol/references/command-reference.md:401`, `skills/workflow-protocol/references/command-reference.md:410`, `skills/workflow-protocol/references/command-reference.md:418`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:377`, `docs/design/skill_set_design_proposal_v0.5.md:383`, `docs/design/skill_set_design_proposal_v0.5.md:389`, `docs/design/skill_set_design_proposal_v0.5.md:397`, `docs/design/skill_set_design_proposal_v0.5.md:556`
- **Issue**: schema 允许 `current_stage: null`，但 `sub_state` enum 不允许 null。`incident-resolve --action abort/reconstruct` 只设置 `current_stage: null`，没有设置 `sub_state`，也没有说明是否清空 `bug_flow`。终态 progress.md 可能出现 `current_stage: null` + `sub_state: review-passed/write` + `bug_flow.active: true` 的残留组合。
- **Impact**: schema validator / recover replay / query caller 会看到不一致终态；某些 guard 只看 `bug_flow.active` 时可能仍路由到 bug-triage，违背终态只允许 query/recover。
- **Recommendation**: 在 schema 中允许 `sub_state: null`，并在 abort/reconstruct mutation 中设置 `sub_state: null`、`review_iteration: 0`、`bug_flow.active: false`、`bug_flow.bug_report_path: null`、`bug_flow.root_cause: null`；或明确终态仍保留 incident stage/sub_state，但不得写 `current_stage: null`。

### Medium: workflow-incident 的 `triggered_by_bug` 在 schema 中是 BUG ID，但 validate.py Cross-Reference 把它当路径字段

- **Dimensions**: 内部一致性, 可实现性, 跨 skill 引用一致性
- **Location**: `skills/doc-guardian/SKILL.md:175`, `skills/doc-guardian/references/frontmatter-schema.md:253`, `skills/doc-guardian/references/frontmatter-schema.md:254`, `skills/doc-guardian/references/frontmatter-schema.md:322`, `skills/doc-guardian/references/frontmatter-schema.md:324`, `skills/doc-guardian/references/frontmatter-schema.md:327`, `skills/doc-guardian/references/frontmatter-schema.md:450`, `skills/doc-guardian/references/frontmatter-schema.md:451`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:688`, `docs/design/skill_set_design_proposal_v0.5.md:716`
- **Issue**: `workflow-incident` schema 写 `triggered_by_bug: BUG-<NNN>`，但 doc-guardian 的 Cross-Reference check 示例把 `triggered_by_bug` 与 `affected_doc/parent_architecture` 一起列为路径字段并要求真实文件存在。
- **Impact**: validate.py 实现者不知道 `triggered_by_bug` 应接受 `BUG-001`、`docs/bug/BUG-001.md`，还是两者都接受；ID uniqueness 与 cross-reference lookup 的错误类别也会混淆。
- **Recommendation**: 统一字段类型。建议保留 `triggered_by_bug: BUG-NNN` 作为 ID 字段，并在 Class 5 中定义“ID reference lookup”：映射到 `docs/bug/BUG-NNN.md` 并校验文件存在；或者改 schema 为 `triggered_by_bug: docs/bug/BUG-NNN.md` 并同步所有模板和 examples。

### Medium: 跨 skill 命令引用仍大量使用 shorthand，且有一个 validate.py 路径缺 `skills/` 前缀

- **Dimensions**: 内部一致性, 跨 skill 引用一致性, 完整性
- **Location**: `skills/workflow-protocol/SKILL.md:20`, `skills/workflow-protocol/SKILL.md:36`, `skills/workflow-protocol/SKILL.md:45`, `skills/workflow-protocol/references/command-reference.md:63`, `skills/workflow-protocol/references/command-reference.md:65`, `skills/workflow-protocol/references/command-reference.md:111`, `skills/doc-guardian/SKILL.md:38`, `skills/doc-guardian/SKILL.md:43`, `skills/doc-guardian/SKILL.md:191`, `skills/doc-guardian/SKILL.md:192`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.4.md:102`, `docs/review/reviewer_feedback_response_v0.4.md:104`, `docs/design/skill_set_design_proposal_v0.5.md:724`, `docs/design/skill_set_design_proposal_v0.5.md:727`, `docs/design/skill_set_design_proposal_v0.5.md:805`
- **Issue**: v0.4 采纳记录要求命令型/规范型语句使用 `skills/<name>/scripts/<x>.py` 全路径，除 display-only shorthand 外需明示。目标文件多数 invocation table 使用 `progress.py`、`validate.py`、`changelog.py` shorthand，command-reference 还写了 `doc-guardian/scripts/validate.py`，缺少 `skills/` 前缀。
- **Impact**: Agent 直接复制命令时可能找不到脚本；跨 skill 调用路径在 workflow-protocol 和 doc-guardian 中不完全一致。
- **Recommendation**: invocation table、Forbidden Actions、Recovery、cross-skill prose 全部改为全路径命令；如果未来会安装 shell alias，则在 SKILL.md 开头显式声明 shorthand alias 的前置条件，否则不要使用 shorthand。

### Medium: doc-guardian 声称 `progress.py update` 默认校验 `<changed-doc>`，但 update 命令没有 doc path 参数

- **Dimensions**: 内部一致性, 可实现性, 跨 skill 引用一致性
- **Location**: `skills/doc-guardian/SKILL.md:191`, `skills/doc-guardian/SKILL.md:192`, `skills/workflow-protocol/references/command-reference.md:62`, `skills/workflow-protocol/references/command-reference.md:63`, `skills/workflow-protocol/references/command-reference.md:64`, `skills/workflow-protocol/references/command-reference.md:65`, `skills/workflow-protocol/references/command-reference.md:100`, `skills/workflow-protocol/references/command-reference.md:118`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:403`, `docs/design/skill_set_design_proposal_v0.5.md:411`, `docs/design/skill_set_design_proposal_v0.5.md:724`, `docs/design/skill_set_design_proposal_v0.5.md:727`
- **Issue**: doc-guardian 写 `progress.py update` 内部默认调 `validate.py file <changed-doc>`，但 workflow-protocol 的 update modes 只有 `--field/--advance/--task`，没有 `--doc` 或 changed-doc 推导规则。只有 `--advance` 有 `<each artifact>` 语义。
- **Impact**: Task 6 实现者无法知道普通 review loop 状态转换时应验证哪个 doc；也可能重复执行 stage skill 已经做过的 validate，或者漏掉状态变更前的校验。
- **Recommendation**: 给 `update` 增加明确的 doc 参数（如 `--doc <path>`）并定义哪些 transition 必须携带；或删除“默认调 changed-doc”的说法，改为普通 `update` 只做状态机校验，`--advance` 才执行 artifact 级 validate。

### Low: validate.py “universal 5 fields” 是明显笔误，和 6 个 universal 字段不一致

- **Dimensions**: 内部一致性, 可实现性
- **Location**: `skills/doc-guardian/SKILL.md:103`, `skills/doc-guardian/SKILL.md:112`, `skills/doc-guardian/SKILL.md:173`, `skills/doc-guardian/references/frontmatter-schema.md:7`, `skills/doc-guardian/references/frontmatter-schema.md:16`, `skills/doc-guardian/references/frontmatter-schema.md:439`, `skills/doc-guardian/references/frontmatter-schema.md:440`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:641`, `docs/design/skill_set_design_proposal_v0.5.md:650`, `docs/design/skill_set_design_proposal_v0.5.md:714`
- **Issue**: universal schema 实际有 `title/type/status/created/updated/owner` 6 个字段，但 validate.py 类 3 文案写“universal 5 字段”。设计 v0.5 也有同样笔误，但目标 reference 的伪码已列 6 个字段。
- **Impact**: 低风险；实现者大概率按枚举字段实现，但“5 字段”会制造不必要疑问。
- **Recommendation**: 将 “universal 5 字段” 改为 “universal 6 字段”，并在设计后续补丁中同步修正。

### Low: SKILL.md 篇幅尚未触发 foreman 反模式，但 doc-guardian 主文档已经承载过多 changelog 细节

- **Dimensions**: 简洁度
- **Location**: `skills/doc-guardian/SKILL.md:203`, `skills/doc-guardian/SKILL.md:288`, `skills/doc-guardian/SKILL.md:349`, `skills/doc-guardian/SKILL.md:353`, `skills/workflow-protocol/SKILL.md:113`, `skills/workflow-protocol/SKILL.md:115`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:180`, `docs/design/skill_set_design_proposal_v0.5.md:183`, `docs/design/skill_set_design_proposal_v0.5.md:745`, `docs/design/skill_set_design_proposal_v0.5.md:749`
- **Issue**: 两个 SKILL.md 分别为 294 行和 356 行，低于 foreman 690 行反模式；workflow-protocol 已把 command 详表拆到 reference，做法合理。但 doc-guardian SKILL.md 把 changelog.py 的格式、示例、promote 行为、标准流程大段内联，同时又引用缺失的 `change-log-format.md`。
- **Impact**: 不阻塞实现，但主文档扫描成本偏高，且缺失 reference 会让读者不知道以内联还是外链为准。
- **Recommendation**: 补齐 `change-log-format.md` 后，将 `SKILL.md` §6 缩成 invocation、强制纪律和失败处理摘要；严格格式、示例、promote 算法放入 reference。

## Cross-Skill Consistency Check

- `workflow-protocol` → `doc-guardian`: P6 B 维度在 `skills/workflow-protocol/SKILL.md:157` 使用了全路径 `skills/doc-guardian/scripts/validate.py`，但 command reference 在 `skills/workflow-protocol/references/command-reference.md:111` 写成 `doc-guardian/scripts/validate.py`，少 `skills/` 前缀。
- `doc-guardian` → `workflow-protocol`: `skills/doc-guardian/SKILL.md:40`、`skills/doc-guardian/SKILL.md:191`、`skills/doc-guardian/SKILL.md:192` 使用 `workflow-protocol update --advance` / `progress.py update` shorthand，与 workflow-protocol 的物理路径 `skills/workflow-protocol/scripts/progress.py` 没有完全对齐。
- Required artifacts: workflow-protocol 依赖 “each artifact”，doc-guardian 把完整清单外包给缺失的 `required-artifacts.md`，导致 cross-skill gate 缺少共享数据源。
- S3 artifacts: workflow-protocol 的 “S3 4 类源系统分析” 与 doc-guardian 的 “3 必备 + technical-debt 推荐” 不一致。
- Bug/Incident: workflow-protocol command-reference 要求 `bug_flow.root_cause == prd-exception` 才能 incident-start，但没有任何 doc-guardian BUG/incident lifecycle 字段能把该状态与 BUG/INCIDENT 文档确定性绑定。
- Frontmatter references: `triggered_by_bug` 是 ID 还是 path 未对齐，会影响 workflow-protocol incident command 与 doc-guardian cross-reference validation 的接口。

## Implementability Assessment

当前产出还不能让 Task 6 实现者直接、确定性地实现 `progress.py` 和 `validate.py`。11 个子命令名称和大部分 release / bug / terminal 字段已经齐全，但以下语义仍会导致实现分叉：

- `progress.py`: PRD exception incident 路径不可达；`incident-resolve --action continue` 缺少精确 bug_flow mutation；`update --field` 过宽；`--advance` artifact 枚举来源不完整；Stage 4 task tests artifact 缺失。
- `validate.py`: frontmatter per-type cheat sheet 与详细 schema 不一致；S3 technical-debt required/recommended 不一致；`triggered_by_bug` ID/path 类型不明确；缺失 directory-layout / required-artifacts / change-log references。
- `changelog.py`: 主文档描述足以实现基本 promote，但引用的完整格式文件缺失；Forbidden Actions 尚未覆盖“手工清空 Pending Changes + 直接写 Change Log 以模拟 promote”的 bypass。
- Edge cases: recover 在 history 损坏时已说明“无法 recover”，review_iteration 超 7 已有升级路径，project_state 终态有 query/recover guard；但 terminal sub_state/bug_flow 清理、post-close bug duplicate/target_release、Stage 4 stale update guard 仍需补。

## Positive Notes

- 11 个 `progress.py` 子命令在两个 workflow-protocol 文件中均已列全，且 release version grammar、atomic write/rollback、一致性校验路径比较清晰。
- `release-start` 消费 `unresolved_bugs` 并写 `consumed_in_release` 已进入 command reference，比 v0.4 更接近可实现闭环。
- `project_state ∈ {aborted, reconstructing}` 终态和“只允许 query/recover”已在主 SKILL.md 中明确。
- P6 A/B/C/D/E 五维矩阵的总体结构与设计 §4.8 对齐，问题集中在 artifact 枚举与条件细节。
- doc-guardian 把 CR/Bug/Incident/source-system-analysis/code-review-report 统一收口，方向符合“无独立 cr-guardian”的设计决策。

## Suggested Next Revision Order

1. 先补齐或移除断链 references，尤其 `required-artifacts.md`；同时解决 `--advance` artifact 枚举来源。
2. 修正 PRD exception incident 路径：让 `incident-start` 可达，并给 `incident-resolve continue` 增加确定性 mutation。
3. 对齐 S3 source-system-analysis 必备清单，并决定 `technical-debt` 是必备还是推荐。
4. 修正 frontmatter per-type 必含表，尤其 BUG/INCIDENT/source-system-analysis 字段。
5. 收紧 `update --field`，补 Stage 4 per-task tests artifact 和 task 状态单调/CAS 规则。
6. 明确 post-close bug consume 时 `target_release` 与 duplicate guard，并清理 terminal sub_state/bug_flow mutation。
7. 统一跨 skill script 全路径与 `triggered_by_bug` ID/path 语义。
8. 最后做低风险文案清理：universal 6 字段、doc-guardian changelog 细节拆分、shorthand/display-only 标注。
