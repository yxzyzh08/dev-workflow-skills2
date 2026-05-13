# Claude Review Prompt — Task 5 Batch 3b

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude。Claude 应在同一个 repo 中完成审查，并把评审报告保存到 `docs/review/skill_set_batch3b_review.md`。

---

## Prompt Body

请评审 dev-workflow-skills2 项目的 Task 5 批 3b 产出（Stage 4 Development 的 3 组 logical skill：planning / test / code，各 write+review，共 6 份 SKILL.md 骨架），按之前 batch 1 / batch 2 / batch 3a review 的格式输出评审报告。

本批是**骨架轮**——仅产出 6 份 SKILL.md，**不含任何 references**（references 拆分待 batch 3 全部收敛后统一规划）。所以本轮**不要**评审 "应该新增哪些 references 文件"；只评审 SKILL.md 自身是否能让 Task 6 实现者按图施工，以及它们与 workflow-protocol / doc-guardian / bug-triage / batch 3a vertical skills 的一致性。

### 评审目标文件（6 份）

主要审查（Stage 4 Development physical skill × 6）：

- `skills/development-planning-write/SKILL.md` (234 行)
- `skills/development-planning-review/SKILL.md` (190 行)
- `skills/development-test-write/SKILL.md` (199 行)
- `skills/development-test-review/SKILL.md` (204 行)
- `skills/development-code-write/SKILL.md` (235 行)
- `skills/development-code-review/SKILL.md` (209 行)

总计 1271 行。

### 必读参考材料

判断"是否符合 spec / design / batch 1 / batch 2 / batch 3a"时必读：

- `docs/handoff/session_handoff_20260506_v3.md`（当前项目状态；batch 3b 起手指南 §7 / §8 最重要）
- `docs/workflow/workflow_specification_claude.md`（v0.6）
- `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计，含 Stage 4 physical skill 清单）
- `docs/review/skill_set_batch3a_round3_review.md`（最近一次闭环 review；含 Gap-1 / Gap-2 状态 + batch 3b 起步建议）
- `skills/workflow-protocol/SKILL.md`（尤其 §5.2 Stage 4 task-level 判定 + §10 Concurrency Model）
- `skills/workflow-protocol/references/command-reference.md`（**最重要**：§2 `update --event` 4 白名单；§2.1 global sub_state 转移；§2.2 `--advance`；§8 `bug-start`；§Stage 4 task state 转换表）
- `skills/doc-guardian/SKILL.md`（Stage 4 required artifacts 概要 + validate / changelog 边界）
- `skills/doc-guardian/references/frontmatter-schema.md`（**最重要**：`development-plan` / `task-breakdown` / `detailed-design` / `test-review-report` / `code-review-report` / `verification-result` schema；三态 review report 不变量）
- `skills/doc-guardian/references/required-artifacts.md`（Stage 4 per-task artifacts：advance 时对每 task 无条件校验 4 个 artifact；stage-level plan + breakdown）
- `skills/doc-guardian/references/change-log-format.md`（哪些 doc 是增量类：development-plan / task-breakdown / detailed-design 必须 Pending/Change Log；test/code review report 与 verification-result 是一次性 doc）
- `skills/doc-guardian/references/directory-layout.md`（Stage 4 per-task 路径 + `src/` / `tests/` convention）
- `skills/bug-triage/SKILL.md`（development root cause 的 task 标注：BUG body `Affected Task(s)`；active mode 入口 gate）
- `skills/bug-triage/references/root-cause-rubric.md`（development / development-test root cause 判定；Stage 4 自验证 bug 不进 bug-triage）
- `skills/bug-triage/references/triage-decision-tree.md`（non-testing 阶段 bug reject；active mode 与 `bug-start` 前置一致）

可选参考（理解 vertical skill 骨架风格）：

- `skills/prd-write/SKILL.md`
- `skills/prd-review/SKILL.md`
- `skills/srs-write/SKILL.md`
- `skills/srs-review/SKILL.md`
- `skills/architecture-write/SKILL.md`
- `skills/architecture-review/SKILL.md`
- `docs/review/skill_set_batch3a_review.md`
- `docs/review/skill_set_batch3a_round2_review.md`
- `docs/review/skill_set_batch3a_round3_review.md`

### 本批已确认的设计边界（请验证，不要重新争论架构层合理性）

1. **范围**：batch 3b 只做 6 个 SKILL.md 骨架；不做 references。
2. **Stage 4 task 状态机**：事实源为 `workflow-protocol` / `command-reference`：
   - `planning-done`
   - `test-writing -> test-review -> test-revising -> test-done`
   - `code-writing -> code-review -> code-revising -> code-review-passed`
   - `verifying -> verified`
3. **Stage 4 done**：`all development_state.task_states[Tn] == "verified"`；advance 时每 task 无条件校验 4 个 per-task artifacts。
4. **三态 review report**：仅 Stage 4 test/code review 用；`pending` skeleton 由 write skill 创建；review skill 填 `pass|fail`；`pending/fail` 都不能推进 `test-done` / `code-review-passed`。
5. **per-task artifact 路径**：
   - `docs/release{x.y}/development/tasks/{task_id}/detailed_design.md`
   - `docs/release{x.y}/development/tasks/{task_id}/test_review_report.md`
   - `docs/release{x.y}/development/tasks/{task_id}/code_review_report.md`
   - `docs/release{x.y}/development/tasks/{task_id}/verification_result.md`
6. **Stage-level artifact 路径**：
   - `docs/release{x.y}/development/plan.md`
   - `docs/release{x.y}/development/breakdown.md`
7. **Verification owner**（本批起步前已人工确认）：`development-code-write` 负责 `verifying -> verified`，运行 unit + integration tests 并写 `verification_result.md`。
8. **Verification fail 语义**（本批起步前已人工确认）：Stage 4 自验证 fail 是内部 retry，**不进入 Bug Flow**；Stage 5 Testing fail 才进入 bug-triage / Bug Flow。
9. **Bug Flow development re-entry**：`root_cause==development` 时，BUG body 的 `Affected Task(s)` 是当前事实源；若不能定位 task，先由 `development-planning-write` 重新 breakdown。
10. **Stage 4 无人 gate**：无 D 维度；`approved` 不应作为 Stage 4 review 输出或 doc final status。
11. **Stage 4 后续执行以 task state 为主**：planning review-passed 后 global `sub_state` 可能为 `review-passed`，但 test/code/verification flow 由 `development_state.task_states[Tn]` 驱动；不得因此自动 advance。

### 已知 / 新识别 design gap（请评估）

#### Gap-1（来自 batch 3a，沿用）：`review-passed -> revising` 转移缺失

- 事实：`command-reference.md` §2.1 没有 `review-passed -> revising` event。
- batch 3b 只需确认本批没有错误使用不存在的 global event；不要强行在本批解决。

#### Gap-2（来自 batch 3a，沿用）：doc frontmatter status mutation helper 未实现

- owner：`doc-guardian status-transition helper` / task-aware variant。
- batch 3b 只声明 owner 和边界，不实现 helper。
- 请检查 6 个 SKILL.md 是否错误要求 write/review skill 直接修改不属于自己的 frontmatter `status`，或是否留下绕过 helper 的路径。

#### Gap-3（batch 3b 新识别）：verification fail 回退 transition 缺失

- 用户已确认：verification fail 是 Stage 4 内部 retry，非 Bug Flow。
- 但当前 `command-reference.md` Stage 4 task state 转换表只有 `verifying -> verified`，没有 `verifying -> code-revising`（或等价 `verification-failed`）回退 transition。
- `development-code-write` / `development-code-review` 已标记 Gap-3：Task 6 实现前 workflow-protocol 需补齐；补齐前禁止手工编辑 progress.md 绕过。
- 请评审：(a) 这个 gap 是否真实且阻塞 Task 6？(b) 在 batch 3b SKILL.md 中以 design gap 声明是否足够？(c) 推荐补哪种 transition（例如 `verifying -> code-revising`，是否需要验证 report `verification_status: fail|partial` 作为前置）？

### 评审维度（12 个）

每条 finding 必须明确归属于一个或多个维度。

1. **Spec / Design / batch 1+2+3a 一致性**
   - 6 个 development skill 是否与 design proposal Stage 4 physical skill 清单一致？
   - `authority: 4` 是否一致？
   - Stage 4 task 状态机是否与 `workflow-protocol` §5.2 / `command-reference` Stage 4 转换表一致？
   - `update --event` 是否只用于 planning global review loop，且 event 名全部属于 4 白名单：`write-complete` / `review-issues` / `review-passed` / `human-confirmed`？
   - test/code task 状态推进是否全部使用 `progress.py update --task Tn --status <new>`，没有误用 global review events？
   - Stage Done A/B/C/E（无 D）描述是否与 workflow-protocol P6 一致？

2. **Stage 4 global sub_state vs task_state 边界**（重点）
   - planning-write/review 使用 global `sub_state` 是否合理？
   - planning review-passed 后，test/code skill 是否正确改用 task state owner 判定，而不是要求 global `sub_state==write`？
   - 是否存在 planning review-passed 后立即 `--advance` 的误导？
   - `development-planning-review` 是否在 review-passed 后先记录 global event，再逐 task 置 `planning-done`，顺序是否合理？
   - 若某个 task `planning-done` update 失败，部分 task 已注册时的 recovery 是否足够？

3. **三态 review report 防 bypass**（重点）
   - `development-test-write` 是否创建 `test_review_report.md` pending skeleton，而不是 pass？
   - `development-code-write` 是否创建 `code_review_report.md` pending skeleton，而不是 pass？
   - revise 后是否明确重置 stale `pass|fail` 为 pending，防止绕过 review？
   - `development-test-review` / `development-code-review` 是否是唯一可写 `review_status: pass|fail` 的 owner？
   - pass 时 `blocking_findings_count == 0` 是否强制？
   - pending/fail 是否都被禁止推进 `test-done` / `code-review-passed`？
   - review report 路径是否 per-task，非 per-stage？

4. **Per-task artifact / doc-guardian 一致性**
   - 6 个 skill 引用的 doc type、frontmatter 字段、路径是否与 `frontmatter-schema.md` / `directory-layout.md` 一致？
   - `development-plan` / `task-breakdown` / `detailed-design` 是否按增量类 doc 走 Pending Changes + `changelog.py promote`？
   - `test-review-report` / `code-review-report` / `verification-result` 是否按一次性 doc 处理，不强制 Change Log？
   - Stage 4 advance 时每 task 无条件校验 4 个 per-task artifacts 的表述是否一致？
   - tests/ 与 src/ 不在 doc-guardian 管辖的边界是否清楚？

5. **planning pair 职责边界与可实现性**
   - `development-planning-write` 是否清楚产出 plan / breakdown / each detailed_design？
   - breakdown 是否声明 task DAG、parallelizable groups、test/code ownership map？
   - `total_tasks` / `T<n>` / path / frontmatter `task_id` 一致性是否足够明确？
   - `development-planning-review` 的 rubric 是否足以阻止过大 task、依赖缺失、跨 task 冲突？
   - planning review 不产三态 report 是否明确？
   - planning review pass 后 task registration 的事实源与 progress.py 实现边界是否清楚？

6. **test pair 职责边界与可实现性**
   - `development-test-write` 是否只写 tests，不写 src？
   - runtime pass 是否不作为 test-review 必须条件（因 source 未实现）？这个边界是否清楚，是否会误导实现者？
   - `development-test-review` 是否评审测试质量而非最终 runtime verification？
   - coverage / boundary / mock / fixture / assertion / integration contract rubric 是否足够实现？
   - Bug Flow 中测试遗漏是否路由到 test-write，且仍需 test-review pass？

7. **code pair 职责边界与可实现性**
   - `development-code-write` 是否只写 source，不写 tests？
   - `development-code-review` 是否只评审 code，不运行最终 verification / 不写 verification_result？
   - code-review 是否检查 test_review_report pass 前置？
   - code-write verification submode 是否清楚写 `verification_result.md` 并验证 `verification_status: pass`？
   - verification fail retry 是否被正确标为 Gap-3，而不是偷偷绕过 task state machine？

8. **Bug Flow development re-entry 完整性**（重点）
   - `root_cause==development` 入口是否与 bug-triage SKILL / root-cause-rubric 一致？
   - BUG body `Affected Task(s)` 作为当前 task 定位事实源是否表述一致？
   - 无法定位 task 时是否先由 planning-write 重新 breakdown？
   - 测试遗漏 vs source bug vs detailed_design 缺口 的路由是否清楚？
   - development Change Mode 是否不关闭 Bug Flow；必须回 Stage 5 retest 后 `bug-close`？
   - Stage 4 自验证 fail 是否明确不走 bug-triage？

9. **并发 / task-bounded safety**
   - test/code skill 是否强调 task-bounded read/write，仅操作本 task 相关 tests/src/report？
   - 多 task 并发时是否避免直接改 progress.md、避免 revert 其他 agent changes？
   - cross-task integration / shared source 修改是否要求 breakdown DAG 或 cross-task impact 说明？
   - `progress.py update --task` 的 flock/atomic 边界是否被正确依赖，而非自创锁？

10. **Forbidden Actions 完整性**
    - 每份 SKILL.md 是否覆盖明显 bypass：直接改 progress.md、跳过 validate、跳过 changelog、write skill 自评审、review skill 改 source/tests/doc body、绕过 pending skeleton、未 pass 就推进、Stage 4 输出 approved、Stage 4 verification fail 进 bug-triage 等？
    - 是否存在缺失的 forbidden，例如 code-write 修改 tests、test-review 写 source、planning-write 创建 code/test report？

11. **Recovery on Failure 实用性**
    - `validate.py` 失败、`progress.py update --task` 失败、stale report、review fail、verification fail、BUG task 缺失、多 task BUG、partial task registration 等是否有清晰修复路径？
    - Gap-3 之前 verification fail 的 recovery 是否足够保守（不手工改 progress.md）？
    - review_iteration cap 是否只用于 planning global review loop，而不是误套到 task-level test/code review？

12. **简洁度 + 术语一致性**
    - 6 个文件平均 212 行左右是否合理？是否有过度冗余或缺失关键内容？
    - `review-passed` / `issues-found` 是否只用于 planning global review；`pass|fail|pending` 是否只用于 test/code 三态 report？
    - `test_review_report.md` / `code_review_report.md` / `verification_result.md` 文件名是否全程 underscore 一致？
    - doc type `test-review-report` / `code-review-report` / `verification-result` 是否全程 hyphen 一致？
    - Stage naming `development`、task states 字符串是否与 command-reference 完全一致？

### 重点排查"新风险"

- **Planning review global event 与 task state 注册的耦合**：`development-planning-review` 先 `review-passed` 再逐 task `planning-done`，如果中途失败，progress 处于 planning review-passed 但 task 部分注册；当前 recovery 是否足够？是否应要求 progress.py 支持 batch task registration / atomic multi-task update？
- **Task registration 与 validate order**：`detailed_design.md` schema 要求 task_id 在 progress.md task_states 中存在，但 `planning-done` 又要求 detailed_design 通过 validate；是否存在 bootstrap chicken-and-egg？SKILL.md 里的 Task registration note 是否足够，还是应在 workflow-protocol / doc-guardian 设计中明确豁免/顺序？
- **Global `review_iteration` 与 task-level review**：test/code review 是 per-task 三态 report，不走 global `review_iteration`；SKILL.md 是否避免误称 test/code review_iteration？
- **Verification fail gap**：Gap-3 是否会影响当前 batch 3b 进入 review-passed / batch 3c？是否必须先修 workflow-protocol？
- **Bug Flow direct route**：planning-write 可决定 direct route 到 test/code write，但当前 progress.py `bug-start` 只把 global sub_state 设 write，没有 task state rollback 细节；是否需要 progress.py bug-start 明确把 affected task 置 `test-revising` / `code-revising`？还是由 downstream skill 判断？
- **Multiple affected tasks**：BUG body 可标多个 task；6 个 skill 是否清楚每 task 独立处理，且不因一个 task 改动破坏其他 verified task？
- **tests/source physical scope**：tests/ 与 src/ 不由 doc-guardian 管辖；review 输入如何确定 diff 范围？SKILL.md 是否给实现者足够约定？
- **Stage 4 advance C 维度**：workflow-protocol P6 表写 Stage 4 C=review-passed，但 test/code review 用三态 report；SKILL.md 是否需要解释 Stage 4 C 由 planning review-passed + test/code report pass 共同构成？

### 输出要求

保存到：`docs/review/skill_set_batch3b_review.md`

格式（参考 batch 3a review 历史）：

```markdown
# Skill Set Batch 3b Review (Development planning/test/code write+review × 3)

**Review Target**: 6 份 SKILL.md 文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Batch 1 Reference**: skills/workflow-protocol/SKILL.md + skills/doc-guardian/SKILL.md (round 5 闭环)
**Batch 2 Reference**: skills/scenario-dispatcher/SKILL.md + skills/bug-triage/SKILL.md + skills/workflow-evolution/SKILL.md (round 3 闭环)
**Batch 3a Reference**: skills/prd-* / skills/srs-* / skills/architecture-* (round 3 闭环)
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: <一句话总结，例如 "blocking issues: <count>; recommendation: (A) 进 batch 3c / (B) fix / (C) revisit design">

## Findings

### High/Medium/Low: <一句话标题>

- **Location**: `<file>:<line>`（如 multi-line `<line-start>-<line-end>`）
- **Baseline Reference**: <相关 spec/design/batch1+2+3a file:line>（如有）
- **Dimension**: <对应评审维度编号/名称>
- **Issue**: <具体描述>
- **Impact**: <实现 / 协作时会导致什么问题>
- **Recommendation**: <具体修复建议；2 选项时列出取舍>

[每条 finding 一节，按 High → Medium → Low 排]

## Cross-Skill Consistency Check

[专门列举 6 个 development skill 之间 + 与 workflow-protocol/doc-guardian/bug-triage/batch3a 的 cross-reference 是否对齐；按 caller → callee 列表。]

## Task State Machine Verification

[逐条验证 command-reference Stage 4 task transitions 是否在 6 SKILL.md 中正确覆盖；指出缺失/多余/错用。]

## Three-State Review Report Verification

[验证 pending skeleton / pass / fail 生命周期、owner、blocking count、progress.py transition 前置是否完整。]

## Bug Flow Development Re-entry Assessment

[评估 root_cause==development 从 bug-triage 到 planning/test/code 的路径；覆盖 task_id/Affected Task(s)、多 task、testing vs Stage 4 verification fail 边界。]

## Design Gap Resolution

[分别评估 Gap-1 / Gap-2 / Gap-3。对 Gap-3 给出明确建议：是否 blocker、推荐 transition、Task 6 前置要求。]

## Implementability Assessment

[按 6 个 skill 列出实现者能否直接实现；列出语义模糊点、需要 script 支持的点、是否应在 workflow-protocol/doc-guardian 后续升级中补。]

## Positive Notes

[列出做得好的设计决策；不强制。]

## Suggested Next Revision Order

[按优先级排序的 fix 顺序：High first, Medium second, Low last，给出每条估计 patch 体量。]

## Recommendation

- **(A)**: 进 batch 3c（testing + delivery + retrospective write/review × 3）—— 当前批 finding 全部 Medium/Low 且数量 ≤ 3，或只有已声明 design gap 不阻塞骨架继续
- **(B)**: 修后再评（再评 1 轮）—— 有 High finding 或 Medium ≥ 5
- **(C)**: 重设计（design level 问题）—— 触及已闭环架构层决策或 Stage 4 状态机需要大改
```

### 评审风格约束

- **High** = blocker，会导致 Task 6 实现错误、状态机不可达、三态 report 被绕过、Bug Flow development re-entry 崩盘；不修不能进 batch 3c。
- **Medium** = 设计/可实现性问题但有 workaround；可在 batch 3b 修后再评，或明确留 Task 6 script upgrade。
- **Low** = 文档清理 / 术语 / cross-reference / 可读性问题；不阻塞。
- Finding 数量不限，但每条必须有具体 location 和可执行 recommendation。
- 不评审"内容是否专业 / 写得好不好"；只评审"是否能让 Task 6 实现者按图施工不歧义 / 是否能让其他 skill 调用本 skill 不出错"。
- 已经在 v0.5 design / batch 1 / batch 2 / batch 3a 闭环过的架构层决策不要重开；只指出 batch 3b 对这些决策是否引用错位。
- 本批没有 scripts 实现；不要因 `skills/workflow-protocol/scripts/progress.py` / `skills/doc-guardian/scripts/validate.py` 尚不存在而报 finding，除非 SKILL.md 对脚本行为的描述与 reference 矛盾。
- 评审完毕后给出明确 (A) / (B) / (C) recommendation。

请直接产出报告，不需要先和我对齐范围。
