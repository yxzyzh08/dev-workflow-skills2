# Claude Review Prompt — Task 5 Batch 3c

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成审查，并把评审报告保存到 `docs/review/skill_set_batch3c_review.md`。

---

## Prompt Body

请评审 dev-workflow-skills2 项目的 Task 5 Batch 3c 产出（Stage 5 Testing / Stage 6 Delivery / Stage 7 Project Retrospective，各 write+review，共 6 份 SKILL.md 骨架），按之前 batch review 的格式输出评审报告。

本批是**骨架轮**：只产出 6 份 `SKILL.md`，**不含任何 references**，不要求实现 scripts。不要因为 `skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` / `skills/doc-guardian/scripts/changelog.py` 尚未存在而报 finding；只评审 SKILL.md 对这些脚本行为的描述是否与现有 references 一致、是否足以让 Task 6 实现者按图施工。

### 评审目标文件（6 份）

- `skills/testing-write/SKILL.md` (213 行)
- `skills/testing-review/SKILL.md` (162 行)
- `skills/delivery-write/SKILL.md` (164 行)
- `skills/delivery-review/SKILL.md` (143 行)
- `skills/retrospective-write/SKILL.md` (169 行)
- `skills/retrospective-review/SKILL.md` (148 行)

总计 999 行。

### 必读参考材料

判断是否符合 spec / design / batch 1 / batch 2 / batch 3a / batch 3b 时必读：

- `docs/handoff/session_handoff_20260506_v3.md`（当前项目状态；Gap-1 / Gap-2 背景）
- `docs/handoff/task6_progress_py_prerequisites_20260506.md`（Batch 3b 留给 Task 6 的 Gap-3 / Gap-4 前置）
- `docs/workflow/workflow_specification_claude.md`（v0.6；Stage 5/6/7 + Bug Flow + retrospective）
- `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计，含 23 physical skill 清单）
- `docs/review/skill_set_batch3a_round3_review.md`（Gap-1 / Gap-2 闭环状态）
- `docs/review/skill_set_batch3b_round2_review.md`（Stage 4 development-* 闭环状态 + Task 6 prerequisites）
- `skills/workflow-protocol/SKILL.md`（P6 判定、Bug Flow、release lifecycle）
- `skills/workflow-protocol/references/command-reference.md`（最重要：`update --event` 白名单、global sub_state 转换、`--advance`、`release-close`、`bug-start`、`bug-close`、`incident-start/resolve`）
- `skills/doc-guardian/SKILL.md`
- `skills/doc-guardian/references/frontmatter-schema.md`（test-report / installation-result / retrospective / bug-report schema）
- `skills/doc-guardian/references/required-artifacts.md`（Stage 5/6/7 required artifacts；Bug Flow active artifacts）
- `skills/doc-guardian/references/change-log-format.md`（testing/delivery one-shot vs retrospective/bug-report incremental）
- `skills/doc-guardian/references/directory-layout.md`（路径约定）
- `skills/bug-triage/SKILL.md`（active mode gate：`release_state==active AND current_stage==testing AND sub_state==review-passed`；root_cause owner；post-close mode）
- `skills/bug-triage/references/root-cause-rubric.md`
- `skills/bug-triage/references/triage-decision-tree.md`
- `skills/workflow-evolution/SKILL.md`（retrospective consumption mode advisory-only；递归悖论边界）
- Batch 3a/3b vertical style references（可选）：`skills/prd-*`, `skills/srs-*`, `skills/architecture-*`, `skills/development-*`

### 本批已确认的设计边界（请验证，不要重新争论架构层合理性）

1. **范围**：batch 3c 只做 6 个 `SKILL.md` 骨架；不做 references，不改 workflow-protocol/doc-guardian references。
2. **Stage 5 Testing required docs**：
   - `docs/release<x.y>/testing/preparation.md` type `test-preparation`
   - `docs/release<x.y>/testing/procedure.md` type `test-procedure`
   - `docs/release<x.y>/testing/report.md` type `test-report`
   - `test-report` frontmatter 必含 `release`, `verification_status`, `total_test_cases`, `passed`, `failed`
   - E 维度：`test-report.verification_status: pass`
3. **Stage 5 initial fail/partial semantics**：初次 `test-report.verification_status: fail|partial` 不代表 Testing docs 一定不合格。若 report 诚实、证据充分且 BUG skeleton 合规，`testing-review` 可以输出 `review-passed`，让 `current_stage==testing AND sub_state==review-passed` 满足 `bug-triage` active mode gate；但 Stage 5 advance 仍必须因 E 不满足而拒绝。
4. **Stage 5 BUG skeleton**：初次 fail/partial 时由 `testing-write` 创建 `docs/bug/BUG-NNN.md` skeleton，frontmatter 包含 `type: bug-report`, `bug_id`, `found_in_release`, `target_release`, `root_cause: null`, `consumed_in_release: null`；BUG report 是增量类 doc，必须 Pending Changes → `changelog.py promote` → `validate.py file`。
5. **Bug Flow owner boundary**：`testing-write` / `testing-review` 不判 `root_cause`，不调 `bug-start` / `incident-start`；`bug-triage` active mode 判 root cause 并调用对应 command。Bug Flow retest pass 后由 `testing-write` 调 `progress.py bug-close`，然后 caller/Bootstrap 才能 `update --advance` 到 delivery。
6. **Stage 6 Delivery required docs**：
   - `docs/release<x.y>/delivery/deployment.md` type `deployment-doc`
   - `docs/release<x.y>/delivery/operation_manual.md` type `operation-manual`
   - `docs/release<x.y>/delivery/installation_result.md` type `installation-result`
   - E 维度：`installation-result.verification_status: pass`
7. **Stage 6 fail/partial semantics**：Delivery `installation_result.verification_status: fail|partial` 必须 `issues-found` 回 `delivery-write` 修部署/环境/文档或升级用户/Bootstrap；Stage 6 不启动 Bug Flow，不创建 active BUG，不调 bug-triage。
8. **Stage 7 Retrospective required doc**：`docs/retrospective/retrospective.md` type `retrospective`，项目级单文件，每 release 增量加节；必须 Pending Changes → `changelog.py promote` → `validate.py file`。Stage 7 无 D/E。
9. **Release close boundary**：`retrospective-write` 和 `retrospective-review` 都不调用 `release-close`。`retrospective-review` 只输出 `review-passed`；review-passed 后由 workflow-protocol / Bootstrap 调 `progress.py release-close`。
10. **Workflow evolution boundary**：`workflow-evolution` retrospective consumption mode 是用户主动、只读、conversation advisory。Retrospective skills 可以记录自然语言 Action Item / advisory，但不得直接 patch/diff dev-workflow-skills2 自身，也不得自动调用 workflow-evolution。
11. **No human gate / no approved**：Stage 5/6/7 都是非 gated stage；6 个 skill 的业务输出只能是 `write-complete`/`review-passed`/`issues-found` 语义，不得签发 `approved`。
12. **Event whitelist**：所有 `progress.py update --event <name>` 必须属于 `{write-complete, review-issues, review-passed, human-confirmed}`。注意 `issues-found` 是业务术语，不是 event 名；实际 event 是 `review-issues`。
13. **Gap-1 沿用**：global `review-passed → revising` 转移缺失。本批只需正确声明，不在 batch 3c 修 workflow-protocol。
14. **Gap-2 沿用**：doc frontmatter `status` mutation owner = `doc-guardian status-transition helper`；本批只声明 owner，不实现 helper。
15. **Gap-3 / Gap-4 已由 Batch 3b 记录为 Task 6 prerequisites**：本批不要重复要求修改 Stage 4 SKILL.md，但需要确保 Stage 5/6/7 没有绕过这些 prerequisites。

### 新识别 design gap（请重点评估）

#### Gap-5（Batch 3c candidate）：active Bug Flow retest fail/partial 缺合法回退命令

当前 command-reference 已定义：

- `bug-start`：`current_stage==testing AND sub_state==review-passed AND bug_flow.active==false` → 切到 root_cause stage。
- `bug-close`：`bug_flow.active==true AND current_stage==testing AND latest test-report pass` → 清空 bug_flow。

但未定义：active Bug Flow 修复后回到 testing，若 retest 仍 `fail|partial`，如何合法回到 `bug_flow.root_cause` 对应 stage 继续修。

Batch 3c SKILL.md 当前处理：

- `testing-review` 可确认 report 诚实并 `review-passed`，但不重新 triage 同一 active BUG。
- `testing-write` 在 `bug_flow.active==true AND report fail|partial AND sub_state==review-passed` 时不 `bug-close`、不新建 BUG、不 invoke bug-triage，只升级用户/Bootstrap。
- Design Gaps / Notes 中把它标为 Gap-5 candidate，建议 Task 6 评估 dedicated transition（例如从 `current_stage=testing, bug_flow.active=true, sub_state=review-passed, test-report fail|partial` 回到 `bug_flow.root_cause` stage Change Mode）。

请评审：

1. Gap-5 是否真实存在？是否应成为 Task 6 progress.py prerequisite？
2. 当前 2 个 testing skill 对 Gap-5 的声明是否足够保守，还是应该改成别的行为（例如 retest fail 一律 `issues-found`、或新增明确 command 名）？
3. 是否存在误导实现者重 triage active BUG、创建新 BUG、手工修改 progress.md、或错误调用 `bug-start`/`bug-close` 的风险？

### 评审维度（10 个）

每条 finding 必须明确归属于一个或多个维度。

1. **Spec / Design / prior batches 一致性**
   - 6 个 skill 是否与 23 physical skill 架构和 Stage 5/6/7 清单一致？
   - `authority: 4`、frontmatter、section structure 是否与 batch 3a/3b 风格一致？
   - 是否错误重开已闭环的架构决策？

2. **Stage 5 Testing correctness（重点）**
   - required docs、路径、doc type、frontmatter fields 是否与 doc-guardian references 一致？
   - `test-report.verification_status` pass/fail/partial 的语义是否正确？
   - `testing-review` fail/partial review-passed 的条件是否只在 triage-ready/linkage-ready 时允许？
   - Stage 5 advance 是否仍严格要求 E pass？
   - `bug-close` 是否只在 active Bug Flow retest pass 后调用？

3. **BUG report / bug-triage boundary（重点）**
   - BUG skeleton schema、3 位 zero-padded ID、active `target_release == found_in_release`、`root_cause:null`、`consumed_in_release:null` 是否正确？
   - BUG report 是否按增量类 doc 处理，Testing docs 是否按一次性 doc 处理？
   - `testing-write` / `testing-review` 是否不判 root_cause、不调 bug-start/incident-start？
   - active mode gate 是否严格是 testing + review-passed + bug_flow inactive？
   - retest fail 是否不重新 triage active BUG？

4. **Gap-5 active retest fail implementability（重点）**
   - 当前 SKILL.md 是否足以避免状态机绕过？
   - 是否应在 Task 6 增加 dedicated command / transition？推荐前置与 mutation 是什么？
   - 如果不增加 command，是否存在不可恢复 stuck state？
   - 是否需要把 Gap-5 追加到 `docs/handoff/task6_progress_py_prerequisites_20260506.md`，还是等 review 后再决定？

5. **Stage 6 Delivery correctness**
   - delivery docs 路径/doc type/schema 是否正确？
   - Delivery docs 是否 one-shot，不需要 Change Log？
   - `installation_result.verification_status: pass` 是否作为 review-passed / advance 的硬条件？
   - fail/partial 是否 `issues-found` 而不是 Bug Flow？
   - Stage 6 upstream mismatch 是否保守升级，不手工回上游 stage？

6. **Stage 7 Retrospective correctness**
   - `docs/retrospective/retrospective.md` 是否项目级单文件、每 release 增量加节？
   - Pending Changes / Change Log / `changelog.py promote` / `validate.py` 顺序是否正确？
   - 当前 release section 最低内容是否覆盖 release summary、timeline、BUG/INCIDENT、review loops、issue classification、improvement proposals、action items？
   - write/review 是否都不调 release-close？
   - workflow-evolution advisory 持久化是否受 Gap-1 限制，不手工回 revising？

7. **Command / state-machine correctness**
   - `update --event` 是否只使用 4 个白名单事件？
   - 是否错误把 `issues-found` 当 command event？
   - non-gated stages 是否不输出 `approved`？
   - `review_iteration` cap 7 是否只在 global review loop 使用，且没有绕过？
   - `release-close`、`bug-start`、`bug-close` protected command owner 是否正确？

8. **doc-guardian consistency**
   - doc type、frontmatter required fields、Change Log 分类是否全程一致？
   - Gap-2 status-transition helper owner 是否声明充分？
   - 是否错误要求 write/review skill 直接改不属于自己的 status，或在 validate 后再变更 frontmatter？

9. **Forbidden Actions / Recovery on Failure**
   - 是否覆盖直接改 progress.md、跳过 validate/changelog、review skill 改 doc/source、write skill 自评审、非法 advance、非法 Bug Flow、非法 release-close、patch dev-workflow-skills2 等 bypass？
   - validate fail、progress update reject、review_iteration 达 7、BUG ID 冲突、delivery upstream mismatch、retrospective advisory persistence 等 recovery 是否可操作？

10. **简洁度 + 术语一致性**
   - 6 个文件总计 999 行是否仍足够简洁？
   - `review-passed` / `issues-found` / `review-issues` / `verification_status` / `installation_result` / `retrospective` 等术语是否统一？
   - 路径 `docs/release<x.y>/...` 与 doc type hyphen 命名是否一致？

### 输出要求

保存到：`docs/review/skill_set_batch3c_review.md`

格式（参考 batch 3a / batch 3b review 历史）：

```markdown
# Skill Set Batch 3c Review (Testing / Delivery / Retrospective write+review × 3)

**Review Target**: 6 份 SKILL.md 文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Batch 1 Reference**: workflow-protocol + doc-guardian (round 5 闭环)
**Batch 2 Reference**: scenario-dispatcher + bug-triage + workflow-evolution (round 3 闭环)
**Batch 3a Reference**: prd/srs/architecture write+review (round 3 闭环)
**Batch 3b Reference**: development planning/test/code write+review (round 2 闭环)
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: <一句话总结；例如 "blocking issues: <count>; recommendation: (A) 进 round 2/fix / (B) accept with Task 6 prerequisite / (C) revisit design">

## Findings

### High/Medium/Low: <一句话标题>

- **Location**: `<file>:<line>`
- **Baseline Reference**: `<file>:<line>`（如有）
- **Dimension**: <对应评审维度编号/名称>
- **Issue**: <具体描述>
- **Impact**: <实现 / 协作时会导致什么问题>
- **Recommendation**: <具体修复建议；如有两种方案请列取舍>

[每条 finding 一节，按 High → Medium → Low 排]

## Cross-Skill Consistency Check

[列 testing-write ↔ testing-review ↔ bug-triage ↔ workflow-protocol；delivery-write ↔ delivery-review；retrospective-write ↔ retrospective-review ↔ workflow-evolution/release-close 的一致性。]

## Stage 5 Bug Flow Assessment

[专门评估 initial fail/partial、BUG skeleton、triage-ready review-passed、active retest pass bug-close、active retest fail Gap-5。]

## Stage 6 Delivery Assessment

[专门评估 installation_result pass gate、fail/partial no Bug Flow、upstream mismatch escalation。]

## Stage 7 Retrospective Assessment

[专门评估 project-level single file、incremental Change Log、release-close boundary、workflow-evolution advisory boundary、recursion compliance。]

## Design Gap Resolution

[分别评估 Gap-1 / Gap-2 / Gap-3 / Gap-4 / Gap-5。对 Gap-5 给出明确建议：是否 Task 6 prerequisite、推荐 command/transition、当前 SKILL.md 是否足够。]

## Implementability Assessment

[按 6 个 skill 列出实现者能否直接实现；列出需要 progress.py / validate.py / changelog.py 支持的点。]

## Positive Notes

[列做得好的设计决策；不强制。]

## Suggested Next Revision Order

[如果有 findings，给最小修复顺序；如果没有 High/Medium，明确建议是否进入后续 batch / Task 6。]
```
