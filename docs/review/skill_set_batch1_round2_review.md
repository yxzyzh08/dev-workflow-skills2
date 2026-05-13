# Skill Set Batch 1 Round 2 Review

**Review Target**: `skills/workflow-protocol/SKILL.md`, `skills/workflow-protocol/references/command-reference.md`, `skills/doc-guardian/SKILL.md`, `skills/doc-guardian/references/frontmatter-schema.md`, `skills/doc-guardian/references/directory-layout.md`, `skills/doc-guardian/references/required-artifacts.md`, `skills/doc-guardian/references/change-log-format.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review**: `docs/review/skill_set_batch1_review.md`  
**Round 1 Response**: `docs/review/reviewer_feedback_response_v0.5_batch1.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: 16 项 round 1 findings: 6 resolved, 10 partially resolved, 0 not resolved; 9 new/remaining findings (4 High + 4 Medium + 1 Low); recommendation: fix and re-review before batch 2

## Previous Findings Verification

| Finding | Severity | Round 1 Status | Round 2 Status | Notes |
|---------|----------|----------------|----------------|-------|
| F1 | High | 3 ref missing | ✅ Resolved | `directory-layout.md`、`required-artifacts.md`、`change-log-format.md` 均已创建并被 `doc-guardian` frontmatter 引用。新 reference 内仍有若干一致性问题，见 New Findings。 |
| F2 | High | PRD exception 不可达 | 🟡 Partially Resolved | `command-reference.md` 已改为 `incident-start --bug <bug-path> --report <incident-path>` 自闭路径；但 `workflow-protocol/SKILL.md` 仍在命令清单中写旧签名和旧前置，见 High finding 2。 |
| F3 | High | `incident-resolve --action continue` mutation 不确定 | 🟡 Partially Resolved | 新增 `--bug-flow keep|clear` 是正确方向；但 `keep` mutation 仍含 `<preserved or set to "in-review">`，且写入 `continue-keep` / BUG 新字段与 frontmatter schema 冲突，见 High finding 3。 |
| F4 | High | `--advance` artifact 来源不明 | 🟡 Partially Resolved | 已采用 `required-artifacts.md` 作为 map；但 condition DSL 依赖未定义的 `srs.is_multi_module` / `srs.architecture_change`，Stage 4 per-task 匹配语义也不清，见 High finding 1 和 Medium finding 6。 |
| F5 | High | S3 必备清单 4 vs 3+1 冲突 | 🟡 Partially Resolved | 7 份目标文件基本统一为 3 必备 + technical-debt 推荐；但 workflow spec v0.6 正文仍写 Technical Debt 必备，见 High finding 4。 |
| F6 | High | frontmatter 必含表与详细 schema 自相矛盾 | ✅ Resolved | `bug-report`、`workflow-incident`、`source-system-analysis` 的 cheat sheet 已补齐 v0.6 字段；`triggered_by_bug` 的 ID/path 残留归入 F12。 |
| F7 | High | Stage 4 tests 缺 per-task doc type | 🟡 Partially Resolved | 已新增 `test-review-report`、路径和 frontmatter；但 skeleton/产出 owner 与 review 标准仍不够确定，且 Stage 4 artifact map 存在 under-validation 风险，见 Medium findings 5/6。 |
| F8 | High | `update --field` 过宽允许 bypass | ✅ Resolved | 泛型 `--field` 已替换为 `--event` 白名单，受保护字段必须经 dedicated subcommand；状态表可覆盖普通 review loop，Stage 4 走 `--task`。 |
| F9 | Medium | Integration Plan 条件矛盾 | 🟡 Partially Resolved | 文案已改为多模块条件必备；但 `required-artifacts.md` 指向的 `srs.is_multi_module` 未在 `srs` frontmatter schema 定义，见 High finding 1。 |
| F10 | Medium | release-start consume bugs 语义不明 | ✅ Resolved | `release-start` 已规定同时写 `target_release` 与 `consumed_in_release`，`bug-intake` 也补了 duplicate guard。后续可补 unique-consumption 的具体 validate 类别，但不阻塞 batch 1。 |
| F11 | Medium | terminal state 脏字段 | 🟡 Partially Resolved | abort/reconstruct mutation 已清理 bug_flow/sub_state；但 `progress.md` schema 仍不允许 `sub_state: null`，且 terminal 下 `recover` 被称为只读但实际覆盖 progress.md，见 Medium finding 5。 |
| F12 | Medium | `triggered_by_bug` ID vs path 不明 | 🟡 Partially Resolved | 主 schema 已澄清 `triggered_by_bug` 是 BUG ID；但 Path References 小节和 validate 伪码仍没有 ID lookup，directory-layout 的 ID path 模板也与 ID regex 不一致，见 Medium finding 7。 |
| F13 | Medium | shorthand 残留 | 🟡 Partially Resolved | `command-reference.md` 加了 display-only note，但 `SKILL.md` 主文档和 doc-guardian 主文档仍大量使用 `progress.py` / `validate.py` / `changelog.py` shorthand，见 Low finding 8。 |
| F14 | Low | `update` 默认 validates changed-doc 但缺 `--doc` | ✅ Resolved | `command-reference.md` 明确 `update --event` 不自动跑 validate，`--advance` 才执行 artifact 级 validate。 |
| F15 | Low | universal “5 字段”笔误 | ✅ Resolved | 已改为 universal 6 字段。 |
| F16 | Low | doc-guardian SKILL.md changelog 内联过多 | 🟡 Partially Resolved | 新增 `change-log-format.md`，但 `doc-guardian/SKILL.md` 仍完整内联算法和格式；这是简洁度问题，不阻塞。 |

## New Findings (round 2 引入)

### High: required-artifacts condition DSL 使用的 SRS 字段未在 frontmatter schema 定义

- **Dimensions**: 完整性, 可实现性, 内部一致性
- **Location**: `skills/doc-guardian/references/required-artifacts.md:7`, `skills/doc-guardian/references/required-artifacts.md:71`, `skills/doc-guardian/references/required-artifacts.md:105`, `skills/doc-guardian/references/required-artifacts.md:277`, `skills/doc-guardian/references/required-artifacts.md:278`, `skills/doc-guardian/references/frontmatter-schema.md:77`, `skills/doc-guardian/references/frontmatter-schema.md:83`, `skills/workflow-protocol/references/command-reference.md:130`
- **Baseline Reference**: `docs/workflow/workflow_specification_claude.md:73`, `docs/workflow/workflow_specification_claude.md:134`, `docs/design/skill_set_design_proposal_v0.5.md:672`, `docs/design/skill_set_design_proposal_v0.5.md:674`
- **Issue**: `required-artifacts.md` 用 `srs.is_multi_module == true` 决定 Integration Plan，且用 `srs.architecture_change == true` 决定 Architecture Delta；但 `srs` frontmatter schema 只有 `release`，没有 `is_multi_module` 或 `architecture_change`。实现 Hint 还建议 `eval_condition` 解析这些字段，但没有说明从哪个文档字段、progress 字段或 body section 读取。
- **Impact**: `progress.py update --advance` 和 `validate.py consistency` 无法确定条件 artifact 是否必备；Task 6 实现者必须自创字段或解析正文，导致实现分叉。
- **Recommendation**: 在 `srs` frontmatter schema 中增加必含布尔字段 `is_multi_module: true|false` 与 `architecture_change: true|false`（或改为 progress.md 字段），并在 required-artifacts DSL 章节明确定义可引用变量、类型、默认值和解析规则；避免裸 `eval`，用白名单 parser。

### High: workflow-protocol 主文档仍暴露旧 incident command 签名和旧前置，和 command-reference 冲突

- **Dimensions**: 内部一致性, 跨 skill 引用一致性, 边界状态处理
- **Location**: `skills/workflow-protocol/SKILL.md:44`, `skills/workflow-protocol/SKILL.md:45`, `skills/workflow-protocol/SKILL.md:126`, `skills/workflow-protocol/SKILL.md:128`, `skills/workflow-protocol/SKILL.md:129`, `skills/workflow-protocol/SKILL.md:216`, `skills/workflow-protocol/SKILL.md:217`, `skills/workflow-protocol/references/command-reference.md:372`, `skills/workflow-protocol/references/command-reference.md:378`, `skills/workflow-protocol/references/command-reference.md:384`, `skills/workflow-protocol/references/command-reference.md:420`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.5_batch1.md:50`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:61`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:64`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:80`
- **Issue**: 主 SKILL 的 invocation table 仍写 `progress.py incident-start --report <path>`，命令清单仍写适用 state 为 `bug_flow.root_cause==prd-exception`，`incident-resolve` 也未展示必填 `--bug-flow keep|clear`。正文流程 later 才写了 `--bug ... --report ...`，command-reference 也已采用新签名，导致同一 skill 内入口说明互相矛盾。
- **Impact**: Agent 很可能按 SKILL.md 快查表复制旧命令，重现 round 1 的 PRD exception 不可达问题；Task 6 CLI 参数定义也会在主文档和 reference 间摇摆。
- **Recommendation**: 将 `SKILL.md` 所有命令表统一为 `skills/workflow-protocol/scripts/progress.py incident-start --bug <bug-path> --report <incident-path>`，并将适用 state 改为 `current_stage==testing AND bug_flow.active==false AND BUG.root_cause==prd-exception`；`incident-resolve` 表中显式写 `--action continue --bug-flow <keep|clear>`。

### High: `incident-resolve --bug-flow keep|clear` 引入了 schema 不允许或未定义的状态字段

- **Dimensions**: 内部一致性, 可实现性, 边界状态处理
- **Location**: `skills/workflow-protocol/references/command-reference.md:424`, `skills/workflow-protocol/references/command-reference.md:435`, `skills/workflow-protocol/references/command-reference.md:436`, `skills/workflow-protocol/references/command-reference.md:437`, `skills/workflow-protocol/references/command-reference.md:438`, `skills/workflow-protocol/references/command-reference.md:447`, `skills/workflow-protocol/references/command-reference.md:451`, `skills/workflow-protocol/references/command-reference.md:452`, `skills/workflow-protocol/references/command-reference.md:453`, `skills/doc-guardian/references/frontmatter-schema.md:257`, `skills/doc-guardian/references/frontmatter-schema.md:276`, `skills/doc-guardian/references/frontmatter-schema.md:370`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:365`, `docs/design/skill_set_design_proposal_v0.5.md:372`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:18`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:19`
- **Issue**: `--bug-flow keep` 的 mutation 写 `sub_state: <preserved or set to "in-review">`，不是单一确定值；它还保留 `bug_flow.root_cause=prd-exception`，同时用 prose 说“不再触发 incident”，这需要额外 hidden state。command-reference 要 workflow-evolution 写 `resolution_action: continue-keep`，但 workflow-incident schema 只允许 `continue | abort | reconstruct | null`。`--bug-flow clear` 又要求在 BUG frontmatter 写 `resolved_by_workflow_change` 与 `final_status`，这两个字段不在 bug-report schema 中。
- **Impact**: 实现者无法写出可验证的 deterministic mutation；validate.py 会拒绝 command-reference 要求写入的 incident/bug frontmatter，或实现者会私自扩展 schema。
- **Recommendation**: 二选一：A) 扩展 schema，增加 `workflow-incident.resolution_detail: keep|clear`，BUG 增加 `resolved_by_workflow_change` / `final_status`，并给 `keep` 明确 `sub_state` 和 root_cause 重置规则；B) 简化 `continue`，只允许一个确定路径（例如清空 bug_flow、`resolution_action: continue`、不新增 BUG 字段），后续重新分类由新的 Bug Report 触发。

### High: S3 Technical Debt 必备性在 v0.6 workflow spec 正文与目标文件之间仍冲突

- **Dimensions**: Spec/Design 一致性, 内部一致性
- **Location**: `docs/workflow/workflow_specification_claude.md:141`, `docs/workflow/workflow_specification_claude.md:142`, `docs/workflow/workflow_specification_claude.md:143`, `docs/workflow/workflow_specification_claude.md:144`, `docs/workflow/workflow_specification_claude.md:711`, `skills/workflow-protocol/SKILL.md:171`, `skills/doc-guardian/SKILL.md:319`, `skills/doc-guardian/SKILL.md:323`, `skills/doc-guardian/references/required-artifacts.md:84`, `skills/doc-guardian/references/required-artifacts.md:91`, `skills/doc-guardian/references/frontmatter-schema.md:303`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:695`, `docs/design/skill_set_design_proposal_v0.5.md:700`, `docs/design/skill_set_design_proposal_v0.5.md:702`
- **Issue**: v0.6 Change Log 声称 Technical Debt 已改为推荐，但 workflow spec 正文 Stage 2 Possible Supporting Artifacts 仍标 `Technical Debt and Risk Analysis` 为 `S3 必备`。7 份目标文件则均按 “3 必备 + technical-debt 推荐” 实现。
- **Impact**: spec baseline 与 SKILL/reference 不一致；后续 stage skill 或 validate.py 以 workflow spec 为准时会要求 technical_debt_analysis.md，以 required-artifacts 为准时不会要求。
- **Recommendation**: 修正 workflow spec 正文 `docs/workflow/workflow_specification_claude.md:144` 为 `S3 推荐`，或撤回目标文件中的 3+1 决议并把 `technical-debt` 放回 required。必须让 spec 正文、Change Log、workflow-protocol、doc-guardian 四处一致。

### Medium: terminal state schema、cleanup mutation 与 recover 行为仍不一致

- **Dimensions**: 内部一致性, 边界状态处理, 可实现性
- **Location**: `skills/workflow-protocol/SKILL.md:62`, `skills/workflow-protocol/SKILL.md:71`, `skills/workflow-protocol/SKILL.md:265`, `skills/workflow-protocol/SKILL.md:271`, `skills/workflow-protocol/SKILL.md:319`, `skills/workflow-protocol/references/command-reference.md:25`, `skills/workflow-protocol/references/command-reference.md:175`, `skills/workflow-protocol/references/command-reference.md:179`, `skills/workflow-protocol/references/command-reference.md:469`, `skills/workflow-protocol/references/command-reference.md:491`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.5_batch1.md:30`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:32`, `docs/design/skill_set_design_proposal_v0.5.md:377`, `docs/design/skill_set_design_proposal_v0.5.md:397`
- **Issue**: terminal cleanup 要写 `sub_state: null`，但 progress.md schema 仍只允许 `write | in-review | revising | review-passed | approved`。同一 schema 还仍写 `workflow_version: v0.5`，而本轮 baseline 是 v0.6。终态规则称只允许 `query/recover` “只读操作”，但 recover 的 mutation 明确会覆盖 progress.md。
- **Impact**: abort/reconstruct 后生成的 progress.md 不符合本 SKILL 自己的 schema；recover 在 terminal state 下到底是允许 mutation 还是只读不明确。
- **Recommendation**: 将 schema 改为 `workflow_version: v0.6`、`sub_state: write | in-review | revising | review-passed | approved | null`，并把 recover 描述改成“terminal state 下唯一允许的 repair mutation”，同时明确 recover 不得改变 project_state 的终态语义。

### Medium: Stage 4 per-task required-artifacts map 可能只校验最终子状态对应 artifact，漏校验前置 artifact

- **Dimensions**: 完整性, 可实现性, 边界状态处理
- **Location**: `skills/doc-guardian/references/required-artifacts.md:112`, `skills/doc-guardian/references/required-artifacts.md:128`, `skills/doc-guardian/references/required-artifacts.md:263`, `skills/doc-guardian/references/required-artifacts.md:268`, `skills/workflow-protocol/references/command-reference.md:527`, `skills/workflow-protocol/references/command-reference.md:543`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:480`, `docs/design/skill_set_design_proposal_v0.5.md:490`, `docs/design/skill_set_design_proposal_v0.5.md:493`
- **Issue**: Stage 4 的 map 为每个 artifact 标 `task_substate_required`，实现 Hint 用 `substate_matches(task_state, entry["task_substate_required"])`，但未定义 `substate_matches` 是精确匹配还是“当前状态已达到/超过要求”。当 task state 为最终 `verified` 时，朴素实现会只匹配 `verification-result`，漏掉 `detailed-design`、`test-review-report`、`code-review-report`。
- **Impact**: `update --advance` 可能在 Stage 4 只校验 verification_result，未重新确认设计/测试评审/代码评审 artifacts；实现者需要猜测状态序关系。
- **Recommendation**: 定义 Stage 4 task state 的严格有序 rank，并规定 `substate_matches(current, required) := rank(current) >= rank(required)`；或更简单：Stage 4 advance 对每个 task 无条件校验 4 个 per-task artifacts，task 状态转换时再校验子状态要求。

### Medium: `test-review-report` 的创建/产出 owner 与评审标准仍不够清晰

- **Dimensions**: 内部一致性, 完整性, 可实现性
- **Location**: `skills/workflow-protocol/SKILL.md:189`, `skills/workflow-protocol/SKILL.md:193`, `skills/workflow-protocol/references/command-reference.md:533`, `skills/doc-guardian/references/frontmatter-schema.md:215`, `skills/doc-guardian/references/frontmatter-schema.md:231`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.5_batch1.md:121`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:146`, `docs/design/skill_set_design_proposal_v0.5.md:140`, `docs/design/skill_set_design_proposal_v0.5.md:491`
- **Issue**: command-reference 写 `development-test-write 完成 + 写 test_review_report skeleton`，frontmatter-schema 又写 `test-review-report` 由 `development-test-review` skill 产出。两者可以共存，但当前没有明确 skeleton 必含哪些字段、review skill 是否覆盖更新、以及测试代码质量评审标准（覆盖率、边界条件、mock 合理性、fixture 隔离等）由哪个 reference 定义。
- **Impact**: Stage 4 task 从 `test-review` 到 `test-done` 的判定依赖该 report，但 write/review 两个 skill 可能对 owner 和字段填充职责理解不同。
- **Recommendation**: 明确生命周期：`development-test-write` 只创建 skeleton（status=draft、counts=0?），`development-test-review` 负责填充 findings 与 `review_status`；或改为 review skill 独占创建。另在 future stage skill reference 中至少列出 test review 的最低检查维度，并在本文件引用该来源。

### Medium: ID 命名、frontmatter regex 与 directory-layout 路径模板仍不完全一致

- **Dimensions**: 内部一致性, 可实现性
- **Location**: `skills/doc-guardian/references/directory-layout.md:152`, `skills/doc-guardian/references/directory-layout.md:153`, `skills/doc-guardian/references/directory-layout.md:154`, `skills/doc-guardian/references/directory-layout.md:164`, `skills/doc-guardian/references/directory-layout.md:201`, `skills/doc-guardian/references/directory-layout.md:208`, `skills/doc-guardian/references/frontmatter-schema.md:339`, `skills/doc-guardian/references/frontmatter-schema.md:340`, `skills/doc-guardian/references/frontmatter-schema.md:341`, `skills/doc-guardian/references/frontmatter-schema.md:346`, `skills/doc-guardian/references/frontmatter-schema.md:349`
- **Baseline Reference**: `docs/design/skill_set_design_proposal_v0.5.md:634`, `docs/design/skill_set_design_proposal_v0.5.md:686`, `docs/design/skill_set_design_proposal_v0.5.md:688`
- **Issue**: directory-layout 要三位 zero-padded ID 文件名，并写路径模板 `docs/cr/CR-{NNN}.md`；frontmatter-schema 的 ID regex 允许 `CR-42`，只“建议”三位。directory-layout 的算法却用 `cr_id/bug_id/incident_id` 渲染，但 §2.6 模板不是 `{cr_id}`。此外 frontmatter-schema Path References 小节仍把 `triggered_by_bug` 列为路径字段，尽管上文已改为 ID lookup。
- **Impact**: validate.py path/naming 实现会不确定：`CR-42.md` 是否合法？路径模板应从 `cr_id` 直接渲染还是从 NNN 渲染？`triggered_by_bug` 是 Class 4 ID format 还是 Class 5 path reference？
- **Recommendation**: 统一为一种规则。建议 ID 字段和文件名均强制 `^CR-\d{3}$` / `^BUG-\d{3}$` / `^INCIDENT-\d{3}$`，directory-layout 路径模板改为 `docs/cr/{cr_id}.md`、`docs/bug/{bug_id}.md`、`docs/incident/{incident_id}.md`；Path References 小节删除 `triggered_by_bug`，另列 ID Reference lookup。

### Low: 主 SKILL.md 仍大量使用 shorthand command，与 F13 的 full-path 决议不符

- **Dimensions**: 跨 skill 引用一致性, 简洁度
- **Location**: `skills/workflow-protocol/SKILL.md:20`, `skills/workflow-protocol/SKILL.md:36`, `skills/workflow-protocol/SKILL.md:45`, `skills/workflow-protocol/SKILL.md:204`, `skills/workflow-protocol/SKILL.md:221`, `skills/doc-guardian/SKILL.md:38`, `skills/doc-guardian/SKILL.md:43`, `skills/doc-guardian/SKILL.md:194`, `skills/doc-guardian/SKILL.md:195`, `skills/doc-guardian/SKILL.md:329`, `skills/doc-guardian/SKILL.md:330`
- **Baseline Reference**: `docs/review/reviewer_feedback_response_v0.4.md:102`, `docs/review/reviewer_feedback_response_v0.4.md:104`, `docs/review/reviewer_feedback_response_v0.5_batch1.md:34`
- **Issue**: `command-reference.md` 加了 display-only shorthand note，但主 SKILL.md 并没有同等 note，且仍大量出现 `progress.py`、`validate.py`、`changelog.py` shorthand。F13 声称“全部 invocation 改全路径”未完全落地。
- **Impact**: 低风险；熟悉项目的人能推断路径，但 agent 复制快查表命令时仍可能执行失败。
- **Recommendation**: 命令型语句统一改为 `skills/workflow-protocol/scripts/progress.py`、`skills/doc-guardian/scripts/validate.py`、`skills/doc-guardian/scripts/changelog.py`；如果保留 shorthand，则在两个 SKILL.md 开头声明 alias 由 AGENTS.md/bootstrap 提供。

## Cross-File Consistency Check (新增)

- 3 个新 reference 文件已存在，F1 的断链问题解除；`change-log-format.md` 与 `doc-guardian/SKILL.md` 的核心格式基本一致。
- `workflow-protocol/SKILL.md` 与 `command-reference.md` 在 incident command 签名、适用 state、`--bug-flow` 必填参数上仍不一致。
- `required-artifacts.md` 与 `frontmatter-schema.md` 在 condition 字段上不一致：`srs.is_multi_module` / `srs.architecture_change` 没有 schema 来源。
- `required-artifacts.md` 与 workflow-protocol P6 已选择 “Technical Debt 推荐”，但 workflow spec v0.6 正文仍写 “S3 必备”。
- `frontmatter-schema.md` 与 `directory-layout.md` 在 ID zero-padding、ID path template、`triggered_by_bug` ID lookup 上仍存在可实现性分歧。
- `test-review-report` 已在 doc catalog、frontmatter、directory layout、required-artifacts 中出现，路径对齐；剩余问题集中在产出 owner 和 quality criteria。
- `progress.md` schema 与 terminal cleanup 不一致：schema 未允许 `sub_state: null`，但 terminal mutation 必写 null。

## Implementability Assessment (Round 2 更新)

当前比 round 1 明显更接近可实现：11 个子命令主体、3 个新增 reference、artifact map、`test-review-report` 和 BUG consume 语义都有实质推进。但仍不建议直接进入 Task 6 实现，因为以下点会让 Python 实现者必须自行裁决：

- `progress.py`: incident 快查表与详细 reference 冲突；`incident-resolve --bug-flow keep|clear` 不是 deterministic schema-compatible mutation；terminal `sub_state:null` schema 不合法；recover 在 terminal 下是 repair mutation 还是只读不清。
- `validate.py`: condition DSL 依赖未定义字段；ID path / zero-padding / `triggered_by_bug` lookup 规则不统一；Stage 4 per-task artifact 匹配语义未定义。
- `required-artifacts`: Stage 2/3 条件 artifact 能否求值取决于缺失的 SRS metadata；Stage 4 final advance 可能漏校验前置 artifacts。
- Cross-file baseline: workflow spec v0.6 正文与目标 reference 对 S3 technical-debt 必备性不一致。

如果先修复上述 High findings，剩余 Medium/Low 可以在 batch 2 stage skill 设计中继续细化。

## Recommendation

(B) 修复 4 项 High 后再 round 3。当前不建议直接进 batch 2；主要原因不是总体设计方向错误，而是 round 2 修复后仍有几处“脚本实现必须猜”的契约空洞。

## Suggested Next Revision Order

1. 先修 `required-artifacts.md` condition DSL：补 SRS frontmatter 字段或改条件来源，并定义 parser/默认值。
2. 统一 incident command surface：主 SKILL.md、command-reference、workflow-incident/bug-report schema 同步 `incident-start` 与 `incident-resolve --bug-flow` 的确定 mutation。
3. 修 workflow spec v0.6 正文的 technical-debt 必备性，确保 spec / SKILL / required-artifacts 一致。
4. 修 progress.md schema：`workflow_version: v0.6`、`sub_state` 允许 null，并明确 terminal recover 行为。
5. 定义 Stage 4 `substate_matches` 或改为 advance 时无条件校验所有 per-task artifacts。
6. 对齐 ID regex/path template/zero-padding 与 `triggered_by_bug` ID lookup。
7. 最后清理 command shorthand 与 doc-guardian SKILL.md 中可迁移到 `change-log-format.md` 的重复细节。

## Positive Notes

- F1 的 3 个 reference 补齐后，doc-guardian 的物理结构终于完整，读者不再遇到断链。
- `required-artifacts.md` 作为 P6 artifact map 的方向正确，能避免把后半流程所有路径塞进 progress.md。
- `update --field` 已收敛为事件白名单，明显降低了绕过 dedicated subcommand 的风险。
- BUG post-close consume 现在同时设置 `target_release` 和 `consumed_in_release`，比 round 1 更可验证。
- `test-review-report` 已贯穿目录、schema、Stage 4 状态表，Stage 4 测试评审闭环比 round 1 完整很多。
