# Skill Set Design Proposal v0.1 Review

**Review Target**: `docs/design/skill_set_design_proposal_v0.1.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md`  
**Review Date**: 2026-05-05  
**Reviewer**: Codex  
**Status**: Findings require revision before Task 5 / Task 6 implementation

## Findings

### High: Skill count and batch scope are inconsistent

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:13`, `docs/design/skill_set_design_proposal_v0.1.md:17`, `docs/design/skill_set_design_proposal_v0.1.md:38`, `docs/design/skill_set_design_proposal_v0.1.md:95`, `docs/design/skill_set_design_proposal_v0.1.md:792`, `docs/design/skill_set_design_proposal_v0.1.md:800`, `docs/design/skill_set_design_proposal_v0.1.md:829`
- **Issue**: 文档同时声明 `22 个 skill` 和 `23 个 skill`。Layer 汇总是 17 + 2 + 2 + 1 = 22，但 Task 5 多处写 23；同时 `批 2（Orchestration + Meta，5 个）` 实际只列出 3 个 skill。
- **Impact**: Task 5 生成 SKILL.md 骨架时会出现范围不确定：到底实现 22 个还是 23 个、批 2 是否缺 2 个 skill、是否有未命名的 hidden skill。
- **Recommendation**: 统一为一个数字。如果总数是 22，修正 Task 5 和批 2 文案；如果是 23，补齐缺失 skill 的名称、Layer、职责、触发条件和实现路径。

### High: S3 mandatory source-system artifacts can be skipped by the gate

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:299`, `docs/design/skill_set_design_proposal_v0.1.md:300`, `docs/design/skill_set_design_proposal_v0.1.md:337`, `docs/design/skill_set_design_proposal_v0.1.md:360`
- **Baseline**: `docs/workflow/workflow_specification_claude.md:103`, `docs/workflow/workflow_specification_claude.md:104`, `docs/workflow/workflow_specification_claude.md:141`, `docs/workflow/workflow_specification_claude.md:144`, `docs/workflow/workflow_specification_claude.md:569`
- **Issue**: Workflow baseline 要求 S3 在 Stage 1 / Stage 2 强制引入 Source System Reference Artifact，但 P6 判定矩阵把 Stage 1 的 Supporting Artifacts 设为可选，Stage 2 只要求 SRS / Acceptance Plan / Integration Plan，没有把 `Source Product PRD Analysis`、`Feature Keep/Cut/Enhance Matrix`、`Source Product SRS Analysis`、`Source Module Analysis` 等 S3 必备物纳入 gate。
- **Impact**: S3 Product Reconstruction 可以在没有原系统分析的情况下通过 Stage Gate，导致 S3 退化为普通 S1，违背“旧系统仅作为参考输入，但必须被分析”的核心规则。
- **Recommendation**: 将 `required-artifacts.md` 设计为 scenario-aware / mode-aware。例如：`scenario=S3,current_stage=prd-inception` 时强制检查源系统 PRD 分析与功能矩阵；`scenario=S3,current_stage=srs-specification` 时强制检查源系统 SRS / module / interface / technical debt 分析。

### High: Script command paths conflict with the planned physical layout

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:149`, `docs/design/skill_set_design_proposal_v0.1.md:158`, `docs/design/skill_set_design_proposal_v0.1.md:247`, `docs/design/skill_set_design_proposal_v0.1.md:580`, `docs/design/skill_set_design_proposal_v0.1.md:688`, `docs/design/skill_set_design_proposal_v0.1.md:712`, `docs/design/skill_set_design_proposal_v0.1.md:713`, `docs/design/skill_set_design_proposal_v0.1.md:750`, `docs/design/skill_set_design_proposal_v0.1.md:753`, `docs/design/skill_set_design_proposal_v0.1.md:817`, `docs/design/skill_set_design_proposal_v0.1.md:826`
- **Issue**: AGENTS template 和 workflow-protocol 多处要求运行根目录 `scripts/progress.py`、`scripts/changelog.py`、`validate.py`，但目标项目目录树没有 `scripts/` 目录；Task 6 物理结构则把脚本放在 `skills/workflow-protocol/scripts/progress.py` 和 `skills/doc-guardian/scripts/{validate.py,changelog.py}`。
- **Impact**: 新项目 bootstrap 后，agent 按 AGENTS.md 执行会找不到脚本，或者不同 skill 使用不同路径，导致 gate、progress update、change log promote 失效。
- **Recommendation**: 二选一固化：A) 在目标项目根生成 `scripts/` wrapper，统一命令为 `scripts/progress.py` / `scripts/validate.py` / `scripts/changelog.py`；B) 全文改为 skill 内路径，例如 `skills/workflow-protocol/scripts/progress.py` 与 `skills/doc-guardian/scripts/validate.py`。建议 A，因为 AGENTS.md 更短，agent 记忆负担更低。

### High: CR status schema contradicts the CR example and SRS approval flow

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:425`, `docs/design/skill_set_design_proposal_v0.1.md:439`, `docs/design/skill_set_design_proposal_v0.1.md:440`, `docs/design/skill_set_design_proposal_v0.1.md:463`, `docs/design/skill_set_design_proposal_v0.1.md:517`
- **Baseline**: `docs/workflow/workflow_specification_claude.md:425`, `docs/workflow/workflow_specification_claude.md:429`, `docs/workflow/workflow_specification_claude.md:447`
- **Issue**: Status 表声明 `approved` 仅适用于 PRD / SRS / Architecture，但 CR 示例使用 `status: approved`，且 CR 是 SRS Change Mode 的标准入口并包含 `Human Approval Status`。如果 `validate.py` 按 Status 表实现，CR 示例会被判定非法；如果允许 CR approved，则 Status 表错误。
- **Impact**: SRS 变更流程无法稳定落地：CR 到底是独立 human-approved artifact，还是只记录 SRS 的 approval 状态，目前不明确。
- **Recommendation**: 明确定义 CR 的状态规则。建议将 `approved` 适用范围改为 `human-gated artifacts`，包括 PRD / SRS / Architecture / CR；或改为 CR 不使用 `status: approved`，只使用 `human_approval_status` 字段，并让 SRS 自身进入 `approved`。

### High: S2 routing is oversimplified compared with the workflow baseline

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:26`, `docs/design/skill_set_design_proposal_v0.1.md:64`, `docs/design/skill_set_design_proposal_v0.1.md:783`
- **Baseline**: `docs/workflow/workflow_specification_claude.md:506`, `docs/workflow/workflow_specification_claude.md:508`, `docs/workflow/workflow_specification_claude.md:510`, `docs/workflow/workflow_specification_claude.md:563`
- **Issue**: 设计文档把 S2 描述为“主流程全程（incremental mode）”“小需求也强制走全流程”“每次新需求就是新 release”。但 workflow baseline 明确 S2 有 4 个子场景，入口 Stage 不全相同，其中 S2-2 / S2-3 直接从 SRS 起步，S2-4 必须停止当前演进并进入 S3。
- **Impact**: `scenario-dispatcher` 可能把所有 Feature Evolution 都路由成完整主流程，导致额外 token 消耗、错误创建 PRD 变更，甚至把应进入 S3 的重构型 PRD 变更误当作普通 release。
- **Recommendation**: 在设计文档中补充 S2 子场景路由表，并让 progress schema 支持 `scenario_subtype: S2-1 | S2-2 | S2-3 | S2-4` 或等价字段。

### Medium: Development code has no review gate beyond tests

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:106`, `docs/design/skill_set_design_proposal_v0.1.md:122`, `docs/design/skill_set_design_proposal_v0.1.md:319`, `docs/design/skill_set_design_proposal_v0.1.md:705`
- **Issue**: 文档声明 v1 不做 Risk-based review、先全量评审，但 `development-code-write` 没有 review 配对，`code-done` 只要求 Source Code 文件存在，最终靠 unit / integration tests 验证。
- **Impact**: 测试能发现行为错误，但不一定能发现架构偏离、安全问题、可维护性问题、重复代码、边界设计问题或未覆盖路径。尤其这是“研发流程 skill 集”，代码质量缺口会在后续项目中放大。
- **Recommendation**: 至少增加一个轻量 `development-code-review` 或 `code-quality-review` gate；如果坚持不加 skill，也应要求 lint/static analysis/security scan/architecture conformance checklist 写入 `verification_result.md`，不能只看测试 pass。

### Medium: Review/revise loop names a revise action without defining who owns it

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:21`, `docs/design/skill_set_design_proposal_v0.1.md:133`, `docs/design/skill_set_design_proposal_v0.1.md:169`, `docs/design/skill_set_design_proposal_v0.1.md:207`, `docs/design/skill_set_design_proposal_v0.1.md:291`
- **Issue**: 状态机和样例中有 `revising` / `srs-revise` / write → review → revise，但 Skill Catalog 只有 `*-write` 与 `*-review`，没有 `*-revise`，也没有明确说明 revise 由 write skill 的 Change Mode 负责。
- **Impact**: workflow-protocol 实现时会出现状态到 skill 的映射缺口：review 失败后应该调用哪个 skill、使用 Full Mode 还是 Change Mode、review_iteration 何时递增，都可能被不同 agent 解释不同。
- **Recommendation**: 明确 revise 的归属。建议统一规则：`*-write` 同时负责 initial write 和 revise；review 失败时进入同一 stage skill 的 `Revise Mode` 或 `Change Mode`，并由 progress.py 记录 `sub_state: revising` 与 `review_iteration`。

### Medium: Release lifecycle is introduced but not fully specified

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:19`, `docs/design/skill_set_design_proposal_v0.1.md:57`, `docs/design/skill_set_design_proposal_v0.1.md:164`, `docs/design/skill_set_design_proposal_v0.1.md:183`, `docs/design/skill_set_design_proposal_v0.1.md:392`, `docs/design/skill_set_design_proposal_v0.1.md:783`
- **Issue**: 设计文档引入 release-level artifact 结构，规定 SRS / Development / Testing / Delivery 按 release 组织，Retrospective 项目级按 release 增量加节。但 workflow baseline 只定义 Product/Project Lifecycle，没有定义 release lifecycle、release 创建条件、关闭条件、版本号递增、并发 release、S2 与 release 的一一关系。
- **Impact**: Task 6 实现 progress.py 和目录校验时会遇到未定义行为：Bugfix 是否创建新 release、S2-2 是否总是新 release、S2-3 是修改当前 release 还是创建下一 release、Delivery 后是否自动 close release。
- **Recommendation**: 在设计文档中增加 `Release Lifecycle Rule` 小节，至少定义 release creation / active release / release close / bugfix target release / retrospective section append 规则。

### Low: Claude-local memory path conflicts with vendor-neutral design

- **Location**: `docs/design/skill_set_design_proposal_v0.1.md:7`, `docs/design/skill_set_design_proposal_v0.1.md:22`, `docs/design/skill_set_design_proposal_v0.1.md:121`
- **Issue**: 文档 front matter 区域引用 `~/.claude/projects/.../memory/`，但设计目标同时强调 vendor-neutral 和 `.claude/skills` + `.agents/skills` 双适配。
- **Impact**: 该路径不可移植，Codex 或其他 agent 无法访问同一 memory 语义；如果后续实现依赖它，会破坏 vendor-neutral 目标。
- **Recommendation**: 移除本地 Claude memory path，或改成 repo-local reference，例如 `docs/memory/`、`docs/research/`、`progress-history.md`。

## Open Questions

1. 总 skill 数最终是 22 还是 23？如果是 23，缺失的 skill 是什么？
2. `development-code-write` 无 review 是临时 v0.1 决策，还是长期原则？是否接受测试之外的代码质量风险？
3. S2 的“每次新需求就是新 release”是否是新决策？如果是，需要同步更新 workflow spec；如果不是，需要从设计文档删除。
4. CR 是否是独立 human-approved document？如果是，frontmatter status 规则需要允许 `type: cr` 使用 `approved`。
5. 目标项目中脚本最终暴露路径是 root `scripts/` 还是 `skills/*/scripts/`？

## Positive Notes

- 4 层 skill 架构整体清晰，`workflow-protocol` / `doc-guardian` 作为基础设施的方向是对的。
- `progress.md` + `progress-history.md` 的双文件设计能解决用户记忆负担，也适合并发 agent。
- `doc-guardian` 的 binary validation 模式非常适合做 workflow gate。
- `Change Log` 自动化机制能显著降低文档漂移风险。
- AGENTS.md template 对新项目 bootstrap 很有价值，只需要修正路径和职责边界即可。

## Suggested Next Revision Order

1. 先统一 skill count、batch scope、script path，这是 Task 5 / Task 6 的 blocker。
2. 补齐 S2 subtype routing 和 S3 scenario-aware required artifacts，避免流程偏离 baseline。
3. 修正 frontmatter status / CR approval 规则，避免 validate.py 设计自相矛盾。
4. 决定是否加入 code review gate 或至少加入 code quality verification checklist。
5. 单独补一节 `Release Lifecycle Rule`，再进入 SKILL.md 骨架设计。
