# Session Handoff — dev-workflow-skills2 (v4)

**Handoff Date**: 2026-05-06  
**Handoff By**: Codex (GPT-5)  
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`  
**Status**: **Task 5 全部闭环**（Batch 1 / 2 / 3a / 3b / 3c 均已通过 review）；下一新 session 起点是 **Task 6 implementation planning / progress.py + doc-guardian scripts 实现准备**。  
**Predecessor Handoffs**: `docs/handoff/session_handoff_20260506.md` / `docs/handoff/session_handoff_20260506_v2.md` / `docs/handoff/session_handoff_20260506_v3.md`

---

## 0. 新 Session 先读顺序

新 session 建议按以下顺序恢复上下文：

1. `docs/handoff/session_handoff_20260506_v4.md`（本文）
2. `docs/handoff/task6_progress_py_prerequisites_20260506.md`（Task 6 必须先补的 Gap-3 / Gap-4 / Gap-5）
3. `docs/review/skill_set_batch3c_round2_review.md`（最新 review 结论：A accept）
4. `skills/workflow-protocol/references/command-reference.md`（Task 6 progress.py 实现事实源）
5. `skills/workflow-protocol/SKILL.md`
6. `skills/doc-guardian/SKILL.md`
7. `skills/doc-guardian/references/frontmatter-schema.md`
8. `skills/doc-guardian/references/required-artifacts.md`
9. `skills/doc-guardian/references/change-log-format.md`
10. 需要实现具体 stage 时再读对应 vertical skill（尤其 `development-*`、`testing-*`）

**重要**：本 skill 集禁止应用于自身项目作为被管理项目（递归悖论）。当前工作是在设计/实现这套 skill，而不是用它来驱动本 repo 自己的 release workflow。

---

## 1. 项目一句话总结

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合：**23 个 physical skill** 分 4 层（Vertical 18 / Cross-cutting 2 / Orchestration 2 / Meta 1）实现 **7 阶段主流程 + Bug Flow + 4 场景（S1-S4）**，强 Foreman binary 校验 + Release 严格串行 + vendor-neutral 架构。

核心工作流：

1. PRD Inception
2. SRS Specification
3. Architecture Design
4. Development（拆 planning / test / code 三组 physical skill）
5. Testing
6. Delivery
7. Project Retrospective

---

## 2. 当前总进度

| # | Task | 状态 | 当前结论 / 输出 |
|---|------|------|----------------|
| 1 | 收尾架构层决策（D3-Q3）| ✅ Done | D-decisions / Q-decisions 闭环 |
| 2 | 设计 workflow-protocol skill | ✅ Done | workflow 状态机、progress 格式、命令、并发模型、P6、release lifecycle |
| 3 | 起草 AGENTS.md 治理文档 | ✅ Design Done | design proposal v0.5 含 template；实际文件待 Task 6 |
| 4 | 设计 doc-guardian skill | ✅ Done | frontmatter schema、required artifacts、directory layout、change-log discipline |
| 5.1 | Batch 1 SKILL.md（workflow-protocol + doc-guardian）| ✅ 闭环 | Round 5 recommendation (A) |
| 5.2 | Batch 2 SKILL.md（scenario-dispatcher + bug-triage + workflow-evolution）| ✅ 闭环 | Round 3 recommendation (A) |
| 5.3a | Batch 3a SKILL.md（PRD / SRS / Architecture write+review）| ✅ 闭环 | Round 3 recommendation (A) |
| 5.3b | Batch 3b SKILL.md（Development planning/test/code write+review）| ✅ 闭环 | Round 2 recommendation (A) 进 batch 3c；1 Low 已修 |
| 5.3c | Batch 3c SKILL.md（Testing / Delivery / Retrospective write+review）| ✅ 闭环 | Round 2 recommendation **(A) accept** |
| 6 | 实现 scripts、AGENTS.md、CLAUDE.md、插件/skill 发布结构 | ⏳ Next | 从 implementation planning 开始，不建议直接编码 |

**当前状态一句话**：Task 5 的 23 个 physical skill 骨架和核心 references 已全部 review 闭环；Task 6 可以启动。

---

## 3. 最新 Review 结论

### 3.1 Batch 3b 最终状态

- Review 文件：`docs/review/skill_set_batch3b_round2_review.md`
- 状态：`regression: 0 remaining; new findings: 0 High / 0 Medium / 1 Low`
- Recommendation：**(A) 进 batch 3c**
- 后续已处理：Round 2 的唯一 Low（`development-planning-review` §2 `sub_state` narrative）已修。
- 重要输出：`docs/handoff/task6_progress_py_prerequisites_20260506.md` 初版，记录 Gap-3 / Gap-4 / task registration prerequisites。

### 3.2 Batch 3c 最终状态

- Round 1 review：`docs/review/skill_set_batch3c_review.md`
  - 0 High / 1 Medium / 5 Low
  - 主要 finding：Gap-5 需要具体 command name + mutation + prerequisites staging
- Round 2 review：`docs/review/skill_set_batch3c_round2_review.md`
  - `regression: 0 remaining`
  - `new findings: 0 High / 0 Medium / 0 Low`
  - Recommendation：**(A) accept**
  - 明确结论：可进入 Task 6 progress.py implementation planning
- Round 2 后顺手修复：报告里的 non-finding cleanup 已处理——`task6_progress_py_prerequisites_20260506.md` §1 Gap-4 owner/trigger 已补 `or bug-rework auto-rollback`。

### 3.3 Review 循环总统计

截至 v4：**19 轮 review**，累计 finding **118**：

| 范围 | Findings | High | Medium | Low | 最终状态 |
|------|----------|------|--------|-----|----------|
| design v0.1-v0.4 | 27 | 13 | 11 | 3 | v0.5 闭环 |
| batch 1 round 1-5 | 37 | 15 | 15 | 7 | (A) proceed batch 2 |
| batch 2 round 1-3 | 15 | 3 | 8 | 4 | (A) proceed batch 3 |
| batch 3a round 1-3 | 15 | 4 | 7 | 4 | (A) proceed batch 3b |
| batch 3b round 1-2 | 18 | 2 | 6 | 10 | (A) proceed batch 3c；Low 已修 |
| batch 3c round 1-2 | 6 | 0 | 1 | 5 | (A) accept |
| **Total** | **118** | **37** | **48** | **33** | Task 5 closed |

---

## 4. 文件状态总览

### 4.1 Skill 总量

当前 `skills/` 下共有 **23 个 SKILL.md**，总计 **5866 行**；连同 references 总计 **10701 行**。

| Layer | Skill 数 | 文件 |
|-------|----------|------|
| Vertical | 18 | PRD/SRS/Architecture/Development/Testing/Delivery/Retrospective write+review（Development 拆 planning/test/code × write/review） |
| Cross-cutting | 2 | `workflow-protocol`, `doc-guardian` |
| Orchestration | 2 | `scenario-dispatcher`, `bug-triage` |
| Meta | 1 | `workflow-evolution` |
| **Total** | **23** | |

### 4.2 当前 Skill 文件清单（精确行数）

```text
skills/architecture-review/SKILL.md                 259
skills/architecture-write/SKILL.md                  275
skills/bug-triage/SKILL.md                          468
skills/delivery-review/SKILL.md                     143
skills/delivery-write/SKILL.md                      164
skills/development-code-review/SKILL.md             215
skills/development-code-write/SKILL.md              252
skills/development-planning-review/SKILL.md         197
skills/development-planning-write/SKILL.md          240
skills/development-test-review/SKILL.md             210
skills/development-test-write/SKILL.md              206
skills/doc-guardian/SKILL.md                        365
skills/prd-review/SKILL.md                          247
skills/prd-write/SKILL.md                           248
skills/retrospective-review/SKILL.md                148
skills/retrospective-write/SKILL.md                 171
skills/scenario-dispatcher/SKILL.md                 235
skills/srs-review/SKILL.md                          256
skills/srs-write/SKILL.md                           374
skills/testing-review/SKILL.md                      162
skills/testing-write/SKILL.md                       217
skills/workflow-evolution/SKILL.md                  485
skills/workflow-protocol/SKILL.md                   329
```

### 4.3 References 文件清单（精确行数）

```text
skills/bug-triage/references/root-cause-rubric.md        525
skills/bug-triage/references/triage-decision-tree.md     826
skills/doc-guardian/references/change-log-format.md      267
skills/doc-guardian/references/directory-layout.md       236
skills/doc-guardian/references/frontmatter-schema.md     556
skills/doc-guardian/references/required-artifacts.md     415
skills/scenario-dispatcher/references/scenario-decision-tree.md 651
skills/workflow-evolution/references/incident-analysis-template.md 766
skills/workflow-protocol/references/command-reference.md 593
```

### 4.4 Docs 关键文件

```text
docs/design/skill_set_design_proposal_v0.5.md          # 当前权威设计 proposal
docs/workflow/workflow_specification_claude.md         # 当前 workflow spec v0.6
docs/handoff/task6_progress_py_prerequisites_20260506.md # Task 6 必读 prerequisites
docs/review/skill_set_batch3b_round2_review.md         # Batch 3b 最终 review
docs/review/skill_set_batch3c_round2_review.md         # Batch 3c 最终 review
docs/review/claude_review_prompt_batch3c_round2.md     # 最新复评 prompt（仅历史用）
```

---

## 5. 已闭环的关键设计决策

### 5.1 全局架构

- 23 physical skills 分 4 层：Vertical 18 / Cross-cutting 2 / Orchestration 2 / Meta 1。
- 7 阶段主流程固定：PRD → SRS → Architecture → Development → Testing → Delivery → Retrospective。
- 4 场景固定：S1 New Product / S2 Feature Evolution / S3 Product Reconstruction / S4 Bug Fix。
- S4 active bug 只允许在 active release 的 Stage 5 testing + review-passed gate 进入 active Bug Flow。
- Release 严格串行；版本号为 `MAJOR.MINOR` 两个整数，不支持 patch/pre-release/build metadata。
- Foreman binary 是状态事实源守门人；agent 不得直接 mutation `progress.md` / `progress-history.md`。

### 5.2 Event / command 边界

`progress.py update --event` 白名单只有 4 个：

- `write-complete`
- `review-issues`
- `review-passed`
- `human-confirmed`

业务术语 `issues-found` 不是 event 名；review skill 输出 issues-found 时实际调用 `--event review-issues`。

Protected commands 包括：

- `release-start`
- `release-close`
- `bug-start`
- `bug-close`
- `bug-intake`
- `incident-start`
- `incident-resolve`
- Task 6 新增推荐：`bug-rework`

### 5.3 Review report 决策

- PRD/SRS/Architecture/Testing/Delivery/Retrospective review skill 不产独立 review-report doc；findings 只回对话 + progress-history prose summary。
- 只有 Stage 4 `development-test-review` / `development-code-review` 使用三态 per-task review report：`pending | pass | fail`。
- `pending` skeleton 由 write skill 创建；`pass|fail` 只能由 review skill 写。
- `pending/fail` 不得推进 `test-done` / `code-review-passed`。

### 5.4 Change Log 分类

增量类 doc 必须 Pending Changes → `changelog.py promote` → `validate.py file`：

- PRD / SRS / Architecture / Retrospective
- SRS supporting：acceptance-plan / integration-plan / architecture-delta
- Development planning docs：development-plan / task-breakdown / detailed-design
- CR / BUG / workflow-incident

一次性 doc 不需要 Change Log：

- test-preparation / test-procedure / test-report
- deployment-doc / operation-manual / installation-result
- test-review-report / code-review-report / verification-result
- source-system-analysis 系列

### 5.5 Stage 5 / 6 / 7 最新决策

- Stage 5 Testing 初次 `test-report.verification_status: fail|partial` 可以 review-passed，只要 Testing docs 诚实且 BUG skeleton 合规；这样进入 bug-triage active mode。Stage 5 advance 仍必须因 E 不满足而拒绝。
- Stage 5 active Bug Flow retest pass 后由 `testing-write` 调 `bug-close`。
- Stage 5 active Bug Flow retest fail/partial 不重 triage、不新建 BUG、不 bug-close；Task 6 通过 `bug-rework` 回 root-cause stage。
- Stage 6 Delivery fail/partial 一律 issues-found；Stage 6 不启动 active Bug Flow，不创建 active BUG，不提供 delivery → testing rollback。
- Stage 7 Retrospective 是 `docs/retrospective/retrospective.md` 项目级单文件，每 release 增量加节；write/review 都不调 `release-close`。
- workflow-evolution retrospective consumption 是用户主动 advisory-only；不得自动 patch dev-workflow-skills2 自身。

---

## 6. 当前 Open Gaps / Task 6 Prerequisites

完整事实源：`docs/handoff/task6_progress_py_prerequisites_20260506.md`。

### Gap-1：`review-passed → revising` 全局 transition 缺失

- 来源：Batch 3a。
- 当前处理：所有 vertical SKILL.md 都声明不要手工编辑 `progress.md`；需要升级用户/Bootstrap 或等待 workflow-protocol 新事件。
- 是否阻塞 Task 6：不阻塞基础实现，但实现时应决定是否新增 event，例如 `review-reopen` / `reopen-review`。

### Gap-2：doc frontmatter `status` mutation helper 未实现

- 来源：Batch 3a。
- Owner：`doc-guardian status-transition helper`（Task-aware variant for Stage 4）。
- 当前处理：SKILL.md 只声明 owner，不实现接口。
- Task 6 需要：定义 helper 接口、status transition 顺序、Change Log 原子性、失败回滚策略。

### Gap-3：Stage 4 verification fail 回退 transition

- 需要新增 task transition：`verifying → code-revising`。
- 前置：`verification_result.md verification_status` is fail/partial。
- Owner/trigger：`development-code-write` verification retry。
- 禁止：verification fail 后手工改 progress 或标 `verified`。

### Gap-4：Development Bug Flow verified task rollback

需要在 `bug-start --root-cause development` 或 `bug-rework` 中自动 rollback affected tasks：

| From | To | 条件 |
|------|----|------|
| `verified` | `test-revising` | BUG body `Affected Task(s)` includes Tn，fix 需要 test change |
| `verified` | `code-revising` | BUG body `Affected Task(s)` includes Tn，fix 需要 source change |
| `code-review-passed` | `code-revising` | source fix needed before verification |

- BUG body `Affected Task(s)` 是当前 task 定位事实源；schema 目前不把 task IDs 放 frontmatter。
- 无法分类时不要猜；交 `development-planning-write` replan/route。

### Gap-5：Active Bug Flow retest fail re-routing

新增推荐 command：

```bash
progress.py bug-rework --bug <BUG-NNN.md>
```

前置：

- `bug_flow.active == true`
- `current_stage == testing`
- `sub_state == review-passed`
- latest `test-report.verification_status` is fail/partial
- `<BUG>` equals `bug_flow.bug_report_path`
- BUG frontmatter `root_cause == bug_flow.root_cause ∈ {srs, architecture, development}`

Mutation：

1. 保持 `bug_flow.active` true。
2. 保持 `bug_flow.bug_report_path` / `bug_flow.root_cause` 不变。
3. `current_stage: testing -> <root_cause stage>`。
4. `sub_state: review-passed -> write`。
5. `review_iteration -> 0`。
6. append `bug-rework` history。
7. 若 `root_cause==development`，复用 Gap-4 affected-task rollback。

禁止：不要 overload initial `bug-start`；不要为同一 active issue 创建第二个 BUG；不要 retest fail 时 `bug-close`。

### Task registration prerequisites

- `progress.py update --task Tn --status planning-done` 必须幂等。
- 重复注册已经 `planning-done` 的 task 应 no-op 或 append idempotent history。
- `planning-done` transition 内部必须原子校验：breakdown / detailed_design / path / progress task key 一致。
- `validate.py file` 不负责校验 task 是否已在 progress.md 注册；cross-file/progress consistency 由 `progress.py update --task` 和 `validate.py consistency` 兜底。

---

## 7. Task 6 建议范围

Task 6 不建议直接一口气实现所有文件。建议先做 implementation plan，然后分批 patch。

### 7.1 Task 6 第一阶段：implementation plan

建议新 session 第一件事：写 `docs/handoff/task6_implementation_plan_20260506.md` 或 `docs/implementation/task6_plan_20260506.md`，内容包含：

1. 文件写集
2. progress.py command matrix
3. validate.py checker classes
4. changelog.py promote/validate behavior
5. status-transition helper API
6. test fixtures / golden files
7. Gap-3/4/5 实现顺序
8. 不做范围（AGENTS/CLAUDE 是否延后等）

### 7.2 Task 6 第二阶段：progress.py MVP

优先实现 `skills/workflow-protocol/scripts/progress.py`：

1. `query`
2. `init`
3. `recover`
4. `release-start`
5. `update --event`
6. `update --advance`
7. `update --task Tn --status <state>`
8. `bug-start`
9. `bug-close`
10. `bug-intake`
11. `incident-start`
12. `incident-resolve`
13. **新增** `bug-rework`

实现前必须把 `command-reference.md` 与 `task6_progress_py_prerequisites_20260506.md` 合并成明确 code-level state transition table。

### 7.3 Task 6 第三阶段：doc-guardian scripts

实现：

- `skills/doc-guardian/scripts/validate.py`
- `skills/doc-guardian/scripts/changelog.py`
- `doc-guardian status-transition helper`（可合并进 validate/changelog 或单独脚本，需先设计接口）

关键 checker：

- frontmatter schema class 1-4
- path/type consistency
- ID uniqueness / reference lookup
- Change Log discipline
- Required artifacts P6
- consistency / cross-file checks

### 7.4 Task 6 第四阶段：entry docs

实现或更新：

- root `AGENTS.md`
- root `CLAUDE.md`
- 可能的 `.codex-plugin/plugin.json` 或 plugin marketplace metadata（若项目目标仍是 Codex plugin）
- 运行 smoke tests / demo fixtures

---

## 8. 新 Session 推荐第一条用户指令

可以直接让新 session 从这里开始：

> 请读取 `docs/handoff/session_handoff_20260506_v4.md` 和 `docs/handoff/task6_progress_py_prerequisites_20260506.md`，然后开始 Task 6 implementation planning：先不要写代码，先给出 progress.py / validate.py / changelog.py / status-transition helper 的实现计划、文件写集、测试策略和分阶段顺序。

如果要更激进：

> 请读取 handoff，然后直接实现 Task 6 第一阶段：创建 implementation plan 文档，并列出 progress.py command matrix 和 Gap-3/4/5 transition table。

---

## 9. 注意事项 / 不要踩坑

- 不要手工编辑任何 future managed project 的 `progress.md`；本 repo 当前还没有 runtime progress files。
- 不要把 `issues-found` 当成 progress.py event；event 是 `review-issues`。
- 不要把 Stage 4 test/code review 的三态 report 逻辑套到 Stage 1/2/3/5/6/7 review。
- 不要让 Stage 6 Delivery 进入 active Bug Flow；active Bug Flow gate 是 Stage 5 Testing review-passed。
- 不要让 `bug-start` 处理 active retest fail；用 Task 6 新增 `bug-rework`。
- 不要让 retrospective skill 自动 patch dev-workflow-skills2；只能 advisory。
- 不要实现 references 时重新打开已闭环架构决策，除非 review 发现不可实现。
- 当前 repo `git status --short` 显示大量 untracked（`docs/`, `skills/`, scripts 等）；不要运行 destructive git clean/reset。

---

## 10. 当前工作树状态

当前命令输出：

```text
?? docs/
?? skills/
?? startclaude.sh
?? startcode.sh
?? temp.md
```

这说明当前 repository 中这些文件/目录尚未被 git track（或 repo 初始化状态特殊）。新 session 不要把它当作可删除垃圾；这些就是当前全部设计产物。

---

## 11. 最终结论

Task 5 已完成：

- 23 个 physical skill 已全部有 SKILL.md。
- Batch 1/2/3a/3b/3c 全部 review 闭环。
- Task 6 prerequisites 已集中在 `docs/handoff/task6_progress_py_prerequisites_20260506.md`。
- 最新 review `docs/review/skill_set_batch3c_round2_review.md` 给出 **(A) accept**。

**下一步唯一推荐**：开启新 session，进入 **Task 6 implementation planning**，先写计划，再分批实现 `progress.py` / `validate.py` / `changelog.py` / status-transition helper / root governance docs。
