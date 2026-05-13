# Session Handoff — dev-workflow-skills2 (v3)

**Handoff Date**: 2026-05-06
**Handoff By**: Claude (Opus 4.7, 1M context)
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Status**: Batch 3a SKILL.md 设计**正式闭环**（评审循环 3 轮：4H/3M/1L → 0H/4M/1L → 0H/0M/2L；Round 3 ✅ recommendation (A)；2 Low cleanup 已修）；**Batch 3b（development-* 6 个 skill）待启动**

**Predecessor Handoffs**: `docs/handoff/session_handoff_20260506.md`（v1 batch 1 闭环时点）/ `docs/handoff/session_handoff_20260506_v2.md`（v2 batch 2 闭环时点）

---

## 1. 项目一句话总结

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合：**23 个 physical skill** 分 4 层（Vertical 18 / Cross-cutting 2 / Orchestration 2 / Meta 1）实现**7 阶段主流程 + Bug Flow + 4 场景（S1-S4）**，强 Foreman binary 校验 + Release 严格串行 + vendor-neutral 架构。

**重要**：本 skill 集**禁止应用于自己**（递归悖论），仅用于其他项目。

---

## 2. 当前进度（精确）

### 2.1 Task 状态总览

| # | Task | 状态 | 输出 |
|---|------|------|------|
| 1 | 收尾架构层决策（D3-Q3）| ✅ Done | 全部 D-decisions / Q-decisions 闭环 |
| 2 | 设计 workflow-protocol skill | ✅ Done | 5 项责任、progress 格式、scripts、并发模型、P6 矩阵、release lifecycle |
| 3 | 起草 AGENTS.md 治理文档 | ✅ Done | 10-section template（含 design v0.5 §6）|
| 4 | 设计 doc-guardian skill | ✅ Done | F1-F6（F4 跳过），含 binary 校验、scenario-aware required-artifacts |
| 5.1 | Batch 1 SKILL.md（workflow-protocol + doc-guardian）| ✅ **闭环**（5 轮评审）| 6 份文件 |
| 5.2 | Batch 2 SKILL.md（scenario-dispatcher + bug-triage + workflow-evolution）| ✅ **闭环**（3 轮评审）| 7 份文件 |
| **5.3a** | **Batch 3a SKILL.md（PRD + SRS + Architecture write/review × 3）** | ✅ **闭环**（3 轮评审）| **6 份文件 1659 行** |
| 5.3b | Batch 3b SKILL.md（development-planning + test + code write/review × 3）| ⏳ **Pending — 下一个新 session 的起点** | 见 §7 / §8 |
| 5.3c | Batch 3c SKILL.md（testing + delivery + retrospective write/review × 3）| ⏳ Pending | 在 batch 3b 后 |
| 6 | 实现：写实际 skill 文件、scripts、AGENTS.md、CLAUDE.md | ⏳ Pending | 待 Task 5 全部完成后启动 |

### 2.2 Batch 3a 评审历程（3 轮）

| 轮次 | Finding 总数 | High | Medium | Low | 处置 |
|------|------------|------|--------|-----|------|
| Round 1 | 8 | 4 | 3 | 1 | 全部采纳；写修复（含 2 个 Design Gaps 标识）|
| Round 2 | 5 | 0 | 4 | 1 | 全部采纳 + 1 advisory typo 顺手修 |
| Round 3 | 2 | **0** | **0** | 2 | 全部采纳；**(A) 进 batch 3b** |

**Batch 3a 收敛趋势**：与 batch 1 / batch 2 一致——High 在 round 2 清零；Medium 在 round 3 清零；最终仅余 2 个 Low（交叉引用 + 顶层摘要清理），codex 明确接受为可发布状态。

---

## 3. 完整评审循环统计（含 batch 3a）

| 版本 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|---------------|
| design v0.1 | 9 | 5 | 4 | 0 | fix |
| design v0.2 | 8 | 5 | 3 | 0 | fix |
| design v0.3 | 6 | 3 | 2 | 1 | fix |
| design v0.4 | 4 | 0 | 2 | 2 | fix → v0.5 闭环 |
| batch 1 round 1-5 | 37 | 15 | 15 | 7 | (A) 闭环 |
| batch 2 round 1-3 | 15 | 3 | 8 | 4 | (A) 闭环 |
| **batch 3a round 1** | **8** | **4** | **3** | **1** | **fix** |
| **batch 3a round 2** | **5** | **0** | **4** | **1** | **fix** |
| **batch 3a round 3** | **2** | **0** | **0** | **2** | **(A) 闭环** |
| **总计 15 轮** | **94** | **35** | **41** | **18** | — |

**经验**（3 个 batch 一致）：

- High → Medium → Low 收敛趋势可靠
- 单 batch 评审循环通常收敛于 3-5 轮；batch 2 / batch 3a 都在 3 轮闭环
- spec-level 推演收益在 round 3-5 急速递减
- batch 越往后，每轮 finding 数量递减（37 → 15 → 8 → 5 → 2）

---

## 4. 关键架构决策（已闭环 — 不可再质疑结构合理性）

### 4.1 Skill 架构（不变）

| Layer | Skill 数 | 内容 |
|-------|---------|------|
| 1 Vertical | 18 | 7 logical Stage Skill 的 write/review pair（Stage 4 拆 6 个：planning/test/code 各 write+review）|
| 2 Cross-cutting | 2 | workflow-protocol / doc-guardian |
| 3 Orchestration | 2 | scenario-dispatcher / bug-triage |
| 4 Meta | 1 | workflow-evolution |
| **总计** | **23** | |

### 4.2 工作流框架（不变）

- **7 阶段主流程**：PRD Inception → SRS Specification → Architecture Design → Development → Testing → Delivery → Project Retrospective
- **4 场景**：S1 New Product / S2 Feature Evolution（4 子场景）/ S3 Product Reconstruction / S4 Bug Fix
- **Bug Flow 4 类根因路由**：SRS / Architecture / Development / PRD（异常逃生阀）
- **Release 严格串行**：MAJOR.MINOR 整数对，按 (major, minor) 数字对比较
- **S4 仅 active release 期间允许**；post-close bug 走 bug-intake 暂存

### 4.3 已闭环的设计决策（汇总）

batch 1+2 全部决策（评审结构 / 评审上限 7 / Stage 4 Option I / Foreman binary / 双 symlink / 严格串行 / S4 active-release-only / Logical vs Physical / MAJOR.MINOR 整数对 / bug-intake / PRD exception path / Bug Flow 闭环 / Incident 终态字段 / Code review skill / Test code review / 三态 review report / ID 3 位 zero-padded / Update 接口白名单 / Required artifacts DSL 6 var + 5 op / Recover 终态语义 / dispatcher 三类输出 / S2-4 二次确认 / 三层 active mode gate / advisory vs patch / INCIDENT skeleton flow / reentrant 幂等性 / double-safety validate / no-suggestion legitimacy 等）—— 详见 v2 handoff §4。

### 4.4 Batch 3a 新增决策（全部 3 轮闭环）

| 决策点 | Round | 选定 |
|--------|-------|------|
| 6 vertical SKILL.md 9 章节框架 | round 1 | Authority + When to Invoke + Mode + Output Contract + Procedure + Stage Done + Bug Flow Re-entry + Forbidden + Recovery + References |
| review skill **不**产 review-report doc | round 1 | 三态 review-report 仅 Stage 4 dev-test/dev-code review；PRD/SRS/Architecture review 输出仅 review-passed/issues-found event + finding markdown 回对话 |
| **PRD 不走 Bug Flow re-entry** | round 1 | bug-triage 4 类不含 prd；prd-exception 走 incident path 由 workflow-evolution 处理，不切 PRD Change Mode |
| **architecture-write 决策树**（H3）| round 1+2 | 2 分支：(a) 本 release 局部 → 仅 delta；(b) 长期事实 → 同轮改主 doc + delta；**无 release-close 自动合并 hook**；不确定时按长期事实候选处理 |
| **SRS frontmatter 必含 2 bool**（H1）| round 1 | `is_multi_module: bool` + `architecture_change: bool`；srs-write 写入责任；required-artifacts DSL 关键依赖；srs-review 维度 5 校验一致性 |
| **consumed_unresolved_bugs 事实源**（H2）| round 1+2 | 扫描 `docs/bug/BUG-*.md` 中 `consumed_in_release == <progress.md.release>`（**不**读 progress-history.md release-start entry）；触发覆盖 S2-1/S2-2/S2-3；`root_cause: null` 是 post-close intake 合法默认 |
| **doc 分类**（M1 round 1）| round 1 | 增量类 doc（PRD/SRS/Acceptance/Integration）走 Pending Changes / changelog promote；snapshot 类 doc（source-system-analysis）跳过 promote 但仍跑 validate.py |
| **review_iteration 归零时点**（M3 round 1）| round 1 | `review-passed` event 本身归零（事实源 command-reference §2 + §2.1）；**不**是 advance 时归零 |
| **finding count summary 携带方式**（Implementability round 1）| round 1 | 通过 history entry result prose 携带 `B/M/L counts + max_severity`；**不**强制结构化 CLI 参数（progress.py implementation 决定） |
| **prd-exception 脏数据修复**（M4 round 2）| round 2 | `progress.py recover` 仅重建 progress.md，**不**修 BUG report frontmatter；脏数据修复路径 = 从 git 恢复或人工修 + 重跑 validate.py |
| **technical-debt 表述**（M2 round 1+2 + L1 round 2）| round 2 | 全文统一 "3 必备（srs-level/module-level/reuse-replace）+ 1 recommended optional（technical-debt）" |

### 4.5 Design Gaps（batch 3a 已识别，**留下游 batch / spec 升级解决**）

| Gap | 描述 | 当前处置（batch 3a 已声明） | 待解决方 |
|-----|------|---------------------------|--------|
| **Gap-1** | `review-passed → revising` 转移缺失（用户在 review-passed 后人 gate 前发现 doc 错时无 in-spec 修复路径）| 6 SKILL.md 标 design gap；要求"升级人介入 / 不要手工编辑 progress.md"；不经 Bug Flow | workflow-protocol 升级（增加新 event）|
| **Gap-2** | doc frontmatter `status` mutation owner 未实现 | owner = `doc-guardian status-transition helper`；调用序列已声明（每次 `progress.py update --event <name>` 成功后 caller 调 helper 同步当前 stage 改动 artifacts 的 frontmatter status；覆盖 4 类 event：write-complete / review-issues / review-passed / human-confirmed）；接口签名 TBD | doc-guardian batch upgrade |

**Codex round 3 确认**：两个 Gap 当前状态足以支撑 batch 3b 起骨架；不必在 batch 3a 内 close。

---

## 5. 文件清单（精确路径）

### 5.1 Skill 文件（已完成 batch 1 + 2 + 3a，共 11 个 skill 物理目录）

```
skills/
├── workflow-protocol/                    # batch 1 (闭环 round 5)
│   ├── SKILL.md                          (329 行)
│   └── references/
│       └── command-reference.md          (593 行；§2 update 4 白名单 + §2.1 转移表 + §10/§11 含 batch 2 round 3 M6 修订)
│
├── doc-guardian/                         # batch 1 (闭环 round 5)
│   ├── SKILL.md                          (365 行)
│   └── references/
│       ├── directory-layout.md           (236 行)
│       ├── frontmatter-schema.md         (541 行；§3.2 SRS 必含 is_multi_module + architecture_change)
│       ├── change-log-format.md          (267 行；snapshot 类 vs 增量类区分基础)
│       └── required-artifacts.md         (391 行；DSL 关键依赖 SRS 2 bool)
│
├── scenario-dispatcher/                  # batch 2 (闭环 round 3)
│   ├── SKILL.md                          (235 行)
│   └── references/
│       └── scenario-decision-tree.md     (651 行)
│
├── bug-triage/                           # batch 2 (闭环 round 3)
│   ├── SKILL.md                          (468 行)
│   └── references/
│       ├── root-cause-rubric.md          (525 行)
│       └── triage-decision-tree.md       (827 行)
│
├── workflow-evolution/                   # batch 2 (闭环 round 3)
│   ├── SKILL.md                          (489 行)
│   └── references/
│       └── incident-analysis-template.md (762 行)
│
├── prd-write/                            # batch 3a (闭环 round 3) ★
│   └── SKILL.md                          (248 行)
├── prd-review/                           # batch 3a (闭环 round 3) ★
│   └── SKILL.md                          (247 行)
├── srs-write/                            # batch 3a (闭环 round 3) ★
│   └── SKILL.md                          (374 行；最长，因 H1+H2 + M3+M4+L1 重头)
├── srs-review/                           # batch 3a (闭环 round 3) ★
│   └── SKILL.md                          (256 行)
├── architecture-write/                   # batch 3a (闭环 round 3) ★
│   └── SKILL.md                          (275 行)
└── architecture-review/                  # batch 3a (闭环 round 3) ★
    └── SKILL.md                          (259 行)
```

**总计**：11 个 skill / 18 份 .md 文件 / **约 8037 行**（batch 3a 加 1659 行）。

**Batch 3a 6 份文件骨架特征**（同 round 1 决议）：仅 SKILL.md，**不含** references；references 拆分留 batch 3 全部完成后规划。

### 5.2 Workflow Spec & Design Proposal（不变）

```
docs/workflow/
├── workflow_specification_claude.md          v0.6 主 spec (含所有改动)
├── workflow_specification_draft_claude.md    v0.1 历史
├── product_lifecycle_workflow_hermes.md      第三方草稿（合并源）
└── product-project-workflow-spec-draft_code.md 第三方草稿（合并源）

docs/design/
├── skill_set_design_proposal_v0.1.md  历史
├── skill_set_design_proposal_v0.2.md  历史
├── skill_set_design_proposal_v0.3.md  历史
├── skill_set_design_proposal_v0.4.md  历史
└── skill_set_design_proposal_v0.5.md  **当前权威设计** + AGENTS.md template
```

**注意**：design proposal 仍是 v0.5；batch 2/3a 决议未升 design 版本（修改主要在 SKILL.md 与 references 层）。可在 batch 3 全部完成后升 v0.6 收尾。

### 5.3 Review Cycle 历史（完整 15 轮）

```
docs/review/
├── codex_review_prompt_batch1.md
├── codex_review_prompt_batch1_round{2,3,4,5}.md
├── codex_review_prompt_batch2.md
├── codex_review_prompt_batch2_round{2,3}.md
├── codex_review_prompt_batch3a.md                 # batch 3a round 1
├── codex_review_prompt_batch3a_round2.md          # batch 3a round 2
├── codex_review_prompt_batch3a_round3.md          # batch 3a round 3
│
├── skill_set_design_proposal_v0.1_review.md
├── skill_set_design_proposal_v0.{2,3,4}_rereview.md
│
├── skill_set_batch1_review.md                       # round 1
├── skill_set_batch1_round{2,3,4,5}_review.md
│
├── skill_set_batch2_review.md                       # round 1
├── skill_set_batch2_round{2,3}_review.md
│
├── skill_set_batch3a_review.md                       # batch 3a round 1
├── skill_set_batch3a_round2_review.md                # batch 3a round 2
├── skill_set_batch3a_round3_review.md                # batch 3a round 3 ★
│
├── reviewer_feedback_response_v0.{1,2,3,4}.md       # design 阶段
├── reviewer_feedback_response_v0.5_batch1.md        # batch 1 round 1
├── reviewer_feedback_response_v0.{6,7,8}_batch1_round{2,3,4}.md
├── reviewer_feedback_response_v0.9_batch2.md        # batch 2 round 1
├── reviewer_feedback_response_v0.10_batch2_round2.md
└── reviewer_feedback_response_v0.11_batch2_round3.md  # batch 2 闭环
```

**注意**：batch 3a 没有显式写 reviewer_feedback_response_vX 文件——修复直接在 SKILL.md 上做（in-place edit），review report 中的 "Round X Findings 回归状态" 表已记录全部修法。后续 batch 3b/3c 可参考 batch 3a 这种 in-place 修法（不必额外 write feedback response）。

### 5.4 Handoff 文档

```
docs/handoff/
├── session_handoff_20260506.md      # v1（batch 1 闭环时点；batch 2 起步前）
├── session_handoff_20260506_v2.md   # v2（batch 2 闭环时点；batch 3 起步前）
└── session_handoff_20260506_v3.md   # v3（**本文件**；batch 3a 闭环时点；batch 3b 起步前）
```

### 5.5 Research 调研（不变）

```
docs/research/
├── superpowers_design_claude.md
├── dev_workflow_skills_v1_design_claude.md
├── forge_design_claude.md
├── foreman_design_claude.md
└── skill_design_comparison_claude.md
```

---

## 6. Memory 文件（持久化决策）

位置：`~/.claude/projects/-home-cgs-github-projects-dev-workflow-skills2/memory/`

| 文件 | 内容 | 同步状态 |
|------|------|---------|
| `MEMORY.md` | 索引 | OK |
| `feedback_design_style.md` | 用户偏好：先框架后细节 | OK |
| `project_framework.md` | 7 阶段主流程 + Bug 流程 + 4 场景映射 | OK |
| `project_skill_architecture.md` | 4 层架构 + 全部 D/Q-decisions + batch 1+2 闭环决策 | ⚠️ **建议 update**：加 batch 3a 闭环 decision 摘要（Gap-1, Gap-2, SRS 2 bool, consumed_unresolved_bugs 事实源, doc 分类, review_iteration 归零时点 等）|
| `project_workflow_protocol_design.md` | workflow-protocol 详细设计 | OK |

**新 Session 起手时建议**：检查并 update `project_skill_architecture.md` 加入 batch 3a 决策摘要。本 handoff §4.4 + §4.5 是该 update 的内容来源。

---

## 7. 新 Session 起手指南：Batch 3b（Development-* 6 个 Skill 骨架）

### 7.1 第一步（必做）：读以下 4 份文件了解全貌

1. `docs/handoff/session_handoff_20260506_v3.md`（**本文件**）
2. `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计）
3. `docs/review/skill_set_batch3a_round3_review.md`（最近评审 + recommendation A）
4. **`skills/workflow-protocol/SKILL.md` §5.2 Stage 4 task-level 判定**（含 task 5+ 子状态：planning-done / test-writing/review/revising/done / code-writing/review/revising/passed / verifying / verified）+ **`skills/doc-guardian/references/frontmatter-schema.md`** §3.x 的 `code-review-report` + `test-review-report` 三态 schema（pending/pass/fail）

### 7.2 第二步：检查 memory 加载情况

`MEMORY.md` 应自动加载。建议 update `project_skill_architecture.md` 加入 batch 3a 决策摘要（见 §6）；不阻塞 batch 3b 起手。

### 7.3 第三步：确认 batch 3a 闭环状态

- 全部 6 个 batch 3a 文件 round 3 已 ✅
- 2 个 Design Gaps（Gap-1 + Gap-2）已声明 owner + staging；不阻塞 batch 3b
- 进 batch 3b 前**不需要**再做 batch 3a review

### 7.4 第四步：Batch 3b 范围（6 个 skill，1 sub-batch）

按 batch 3a 的 sub-batch 方式（一次 6 个 SKILL.md 骨架），batch 3b 做 Stage 4 Development 的全部 3 个 logical group × 2 = 6 个 physical skill：

| Group | Skills（physical）| 每个 skill 主要 doc 输出 |
|-------|-----------------|----------------------|
| 4-Planning | `development-planning-write` / `development-planning-review` | Plan + Breakdown + per-task Detailed Design |
| 4-Test | `development-test-write` / `development-test-review` | Tests source（`tests/`）+ per-task **test-review-report**（三态 pending/pass/fail）|
| 4-Code | `development-code-write` / `development-code-review` | Source code（`src/`）+ per-task **code-review-report**（三态 pending/pass/fail）|

**预期产出量参考**（batch 3a 平均 259 行/skill；batch 3b 因 task 状态机 + 三态 report + per-task 而更复杂，预计每个 skill 280-380 行；总计 1700-2300 行）。

### 7.5 第五步：Batch 3b 比 Batch 3a 多出的设计点（**重点**）

batch 3a 是规格类 doc（PRD / SRS / Architecture）；batch 3b 是实现类 task，设计复杂度高。**关键 5 点**：

#### (1) Task 状态机（每 task 子状态序列；事实源：workflow-protocol §5.2）

```
T<n> 子状态序列：
  planning-done                # development-planning-write/review 输出
    ↓
  test-writing → test-review → test-revising → test-done
                 (development-test-write/review pair；含三态 review report)
    ↓
  code-writing → code-review → code-revising → code-review-passed
                 (development-code-write/review pair；含三态 review report)
    ↓
  verifying → verified
              (单元 + 集成 测试执行 + verification_result.md)

Stage 4 done ⇔ all task_states[Tn] == "verified"
```

**对每个 development-* skill 含义**：
- `development-planning-write/review` 决定 task list（写 task-breakdown.md + 每 task detailed_design.md）；invoke 时 progress.md `current_stage==development AND sub_state==write/in-review`，task_states 全部 `null`
- `development-test-*` 仅当 task 进入 `test-writing` 子状态时被 invoke
- `development-code-*` 仅当 task 进入 `code-writing` 子状态时被 invoke
- `verifying → verified` 由谁负责？设计中可能有 **verification skill**（隐含 dev-code 或独立 testing 子）；需 batch 3b 早期与用户确认

#### (2) 三态 review report（首次出现，仅 Stage 4）

事实源：`doc-guardian/references/frontmatter-schema.md` §3.x `code-review-report` + `test-review-report`：

```yaml
type: code-review-report  # 或 test-review-report
review_status: pending | pass | fail
findings_count: int
severity_distribution: {...}
blocking_findings_count: int
max_severity: low | medium | high | critical
```

**三态语义**（已闭环 batch 1 round 3 H2）：
- `pending` = skeleton 状态；development-test-write/development-code-write 创建时默认；防 review skill 被 bypass
- `pass` = 真正 review 通过；blocking_findings_count == 0；review skill 才能填
- `fail` = review 拒绝；blocking_findings_count ≥ 0

**Stage 4 task `test-done` / `code-review-passed` 转移严格要求 `review_status: pass`**（pending / fail 都 reject）。

**Skeleton 创建责任**（已闭环 batch 1 round 3 H2）：
- `development-test-write` 创建 `test-review-report.md` skeleton（pending）
- `development-test-review` 填 review_status: pass / fail
- `development-code-write` / `development-code-review` 同理

#### (3) Per-task artifact 路径（事实源 doc-guardian directory-layout）

```
docs/release<x.y>/development/
├── plan.md                                  # planning skill 产
├── breakdown.md                             # planning skill 产
└── tasks/
    └── T<n>/
        ├── detailed_design.md               # planning skill 产
        ├── test_review_report.md            # test-write skeleton + test-review 填
        ├── code_review_report.md            # code-write skeleton + code-review 填
        └── verification_result.md           # verifying 时产；含 verification_status: pass | fail
```

**注意**：这是 **per-task** 目录，不是 per-stage。每个 task `T<n>/` 下有自己的 4 份 doc。

#### (4) Task 子 agent 并发模型（事实源 workflow-protocol §10）

- progress.py 子命令：`update --task <Tn> --status <new>`
- task 状态转换原子（flock 保护）
- 多个 task 并发推进（不同 T<n> 子状态可不同）；scripts 内部 diff old vs new task state
- 每个 development-* skill 是 task-bounded：read/write 仅本 task 子目录

#### (5) Stage 4 Done 完整判定（无 D 维度，但 E 维度复杂）

| 维度 | 判定 |
|------|------|
| A. 必需 artifacts | 每 task 4 份 doc 全在 + plan + breakdown |
| B. doc-guardian validate | 每 doc exit 0 |
| C. Review 通过 | development-planning-review / test-review / code-review 三处都 review-passed；含三态 review-report `review_status: pass` |
| **D. 人确认** | **不适用**（Stage 4 非 gated）|
| **E. 内部验证** | 每 task `verification_result.md` `verification_status: pass`（unit + integration 测试全部通过）|

### 7.6 第六步：每个 development-* SKILL.md 应覆盖的章节（参考 batch 3a 9 章节框架）

| 章节 | 内容 |
|------|------|
| 1. Authority & Scope | authority 4；本 skill pair 在 Stage 4 中的角色 |
| 2. When to Invoke | progress.md task_states[Tn] 状态驱动；列出适用子状态 |
| 3. Full Mode vs Change Mode | task 是 once-per-task，不存在 Change Mode 重复执行；Bug Flow re-entry 才是 Change Mode |
| 4. Doc Output Contract | per-task artifact + skeleton 创建责任（test/code review report）|
| 5. 4-Step Standard Procedure | 写 → Pending → promote → validate → progress.py update --task |
| 6. Stage Done Conditions（per-task）| A/B/C/E（无 D）|
| 7. Bug Flow Re-entry | root_cause==development 时切回；具体 task 由 bug-triage 在 BUG-NNN 标 |
| 8. Forbidden Actions | 不直接改 progress.md / 不 bypass three-state report 等 |
| 9. Recovery on Failure | review_iteration 超 7 / skeleton 缺失 / verification fail 等 |
| 10. References | cross-skill + 项目级 + Design Gaps |

### 7.7 第七步：Batch 3b 评审策略

期待 batch 3b 评审循环 **2-3 轮收敛**（参考 batch 2 / batch 3a 经验）：

- Round 1 期待 finding 5-10（含 1-3 High，主要在 task 状态机错位、三态 report bypass、per-task artifact 路径不一致）
- Round 2 期待 0 High，2-5 Medium
- Round 3 期待 0 High / 0 Medium / 1-2 Low → (A) 进 batch 3c

### 7.8 第八步：与用户确认的 Batch 3b 范围决策（**起步前必做**）

参考 batch 3a 起手时的 3 个范围问题（仅做 SKILL.md 骨架 / template 放 *-write references / rubric 放 *-review references）。Batch 3b 同样建议先确认：

1. **范围**：仅 6 个 SKILL.md 骨架，不做 references？（推荐 yes，与 batch 3a 一致）
2. **三态 review report skeleton 创建时机**：是 development-*-write 在调 progress.py update --task <Tn> --status test-writing 时创建？还是有其他触发点？（事实源 doc-guardian frontmatter-schema 已闭环；但 SKILL.md 应明确写时机）
3. **`verifying → verified` 责任主体**：是 development-code-* 自己跑 unit/integration tests 后写 verification_result.md？还是有独立 skill？（影响 dev-code-review 与 testing skill 的边界）

---

## 8. Batch 3b 关键设计预告（Pre-meditated）

以下是 batch 3b 设计时**预期会出现**的设计议题（已在 batch 1/2/3a 决策中埋好种子；batch 3b 设计时可直接参照决议而非重新设计）：

### 8.1 已闭环可直接参照

- task 状态序列（workflow-protocol §5.2）
- 三态 review report 三态语义（doc-guardian frontmatter-schema § code-review-report / test-review-report）
- skeleton 创建责任（batch 1 round 3 H2）
- per-task artifact 4 类清单（directory-layout）
- progress.py update --task 子命令签名（command-reference §2）
- Bug Flow root_cause==development 路径（已在 batch 3a 引用：development-* 在 BUG-NNN.md frontmatter 的 task_id 标注）

### 8.2 Batch 3b 才需要新决议

- **task 子 agent 调度**：是 development-planning-write 一次创建全部 task 让 development-*-write 子 agent 并发跑？还是串行？（design proposal v0.5 §4.6 提到 Option B 子 agent 接口）
- **跨 task 依赖**：T1 是否可作为 T2 的 detailed_design 输入？（如有跨 task 依赖，breakdown.md 必须显式声明 task DAG）
- **task 失败回退路径**：T<n> verifying 时单元测试 fail → 退回 code-writing 还是触发 Bug Flow？（v0.5 §4.10 暗示 fail 触发 verification fail，但不明确是否进 Bug Flow 还是 task 内 retry）
- **测试代码本身的 review**：tests/ 目录下的 unit/integration 测试代码由 development-test-review 评审；test-review-report 是它的输出。但 tests/ 代码物理变更如何 promote？（不走 Change Log，因为 tests/ 不是 doc-guardian 管辖；但 review 输入需要明确）
- **code-review 评审范围**：src/ 全部还是仅本 task 涉及的部分？（Stage 4 是 task-bounded，应仅本 task；但 cross-task 接口 / 公共组件 怎么处理？）

### 8.3 Gap-2 在 batch 3b 中的应用（doc-guardian helper TBD）

batch 3a 的 Gap-2 调用序列已声明覆盖 4 类 event；batch 3b 应**沿用同一序列**：
- task 内部状态转换（如 test-writing → test-review）由 `progress.py update --task <Tn> --status <new>` 触发；不在 4 event 白名单内
- 但 task 内部产生的 doc（如 test_review_report.md / code_review_report.md / detailed_design.md）的 frontmatter status mutation **仍** owner = doc-guardian helper
- batch 3b SKILL.md 同样在 Design Gaps 段引用 Gap-2

### 8.4 Bug Flow root_cause==development 进 dev-code-write Change Mode 路径

事实源：bug-triage SKILL.md + workflow-protocol command-reference.md §8 bug-start。

`bug-start --root-cause development` 后切：
- `current_stage: testing → development`
- task 子状态：原 verified 状态被某 task `code-revising` 替换（具体哪个 task 由 bug-triage 在 BUG-NNN.md frontmatter `task_id` 标注）

batch 3b 的 development-code-write SKILL.md 必须明确 §7 Bug Flow Re-entry 路径含 task_id 解析。

---

## 9. Watch List for Task 6 实现

batch 1+2+3a 评审给的实现关注点（更新到 batch 3a 闭环时点）：

1. **DSL parser**：`required-artifacts.md` 顶部 §Condition DSL 完整 grammar 为准；含 SRS frontmatter 2 bool（`is_multi_module` / `architecture_change`）作 DSL 输入
2. **recover**：按 `command-reference.md` §4 实现；terminal event 后 mutating entry **必须 fatal**；**不修 BUG report frontmatter**（v0.6 round 2 M4 决议）
3. **review report 三态**：仅 Stage 4 dev-test-review / dev-code-review；skeleton 默认 pending；只有 pass 才允许 task `test-done` / `code-review-passed` 转移
4. **Stage 4 unconditional validation**：advance 时对每个 task 无条件校验全部 4 个 per-task artifacts
5. **S3 必备 artifacts**：Stage 1 prd-level + feature-matrix；Stage 2 srs-level + module-level + reuse-replace（technical-debt 推荐非必备）
6. **ID 格式**：强制 3 位 zero-padded（`^(CR|BUG|INCIDENT)-\d{3}$`）
7. **bug-triage active mode 三层 gate**：dispatcher / bug-triage / progress.py 前置全文一致 = `release_state==active AND current_stage==testing AND sub_state==review-passed`
8. **INCIDENT skeleton 必经 promote**：bug-triage 创建后必须 `changelog.py promote → validate.py file → incident-start`，缺一不可
9. **incident-start / incident-resolve 二次 validate**：progress.py 内部必须再跑 `validate.py file <incident-path>`，与 caller validate 形成 double-safety
10. **workflow-evolution reentrant 幂等性**：重 invoke 时不可仅凭 `status=review-passed` 直接重试 incident-resolve，必须再跑 validate.py 确认 Pending 已空
11. **bug-triage 4 类强制**：active mode 必须输出 4 类之一，无 out-of-scope 第五路径
12. **workflow-evolution advisory vs patch**：禁止输出 patch/diff；自然语言 advisory + Action Item 标注允许并鼓励
13. **review_iteration 归零时点（batch 3a M3 round 1）**：`progress.py update --event review-passed` 事件本身归零；**不**是 advance 时
14. **consumed_unresolved_bugs 事实源（batch 3a H2）**：扫描 BUG-*.md `consumed_in_release == 当前 release`；**不**读 progress-history.md release-start entry
15. **architecture_delta 长期事实（batch 3a H3）**：必须同轮改主 doc + delta；**无** release-close 自动合并 hook
16. **doc 分类（batch 3a M1）**：snapshot 类（source-system-analysis）跳过 changelog promote；增量类全部走完整 4-step
17. **SRS 必含 2 bool（batch 3a H1）**：`is_multi_module: bool` + `architecture_change: bool`；srs-write 写入；required-artifacts DSL 关键依赖
18. **finding count 携带（batch 3a Implementability）**：通过 history entry result prose；**不**强制 progress.py 结构化 CLI 参数
19. **Gap-1 处置**：spec 当前无 `review-passed → revising` 事件；用户错过人 gate 前修改窗口须升级人介入或新 design proposal 加 event
20. **Gap-2 处置**：doc frontmatter status mutation owner = doc-guardian status-transition helper；接口待 doc-guardian batch upgrade；当前 batch 3a 仅声明 owner + 4 event 调用序列；Task 6 实现时若 helper 不可用，临时由 caller 直接修 frontmatter（打 TODO + Gap-2 引用）

Task 6 单元测试必须覆盖：

- 三态 review report（pending → pass / pending → fail / 直接 pass / 直接 fail）
- terminal recover corruption（terminal 后伪造 mutating entry → fatal）
- Stage 4 unconditional per-task validation
- S3 3+1 source-system-analysis 清单（缺 reuse-replace → fail；缺 technical-debt → pass）
- DSL parser 6 个 test cases（含 SRS 2 bool driver）
- bug-triage 三层 gate
- INCIDENT skeleton promote 流程
- incident-resolve double-safety
- workflow-evolution reentrant
- **review_iteration 归零（review-passed event 时归零；advance 时不归零）**
- **consumed_unresolved_bugs 扫描 BUG-*.md（不读 history list）**
- **architecture_delta 长期事实路径（同轮改两份）**
- **snapshot 类 doc 跳过 changelog（source-system-analysis 不需 Pending Changes）**
- **SRS 缺 2 bool → validate.py 类 3 fail**

---

## 10. 关键约束（不可破坏）

任何后续工作必须遵守（v2 + batch 3a 新增）：

- ❌ **不修改架构层决策**（除非有强理由 + 用户同意）—— 评审循环已 15 轮验证（4 design + 5 batch 1 + 3 batch 2 + 3 batch 3a）
- ❌ **不应用本 skill 集到 dev-workflow-skills2 自身**（递归悖论）
- ❌ **不绕过 progress.py 直接编辑 progress.md / progress-history.md**
- ❌ **不绕过 changelog.py 直接编辑 Change Log 章节**
- ❌ **不绕过 validate.py 推进 stage**
- ❌ **review skill 输出绝不用 `approved`**（用 `review-passed` / `issues-found`）
- ❌ **新 doc type 必须先走 design proposal review cycle**
- ❌ **bug-triage active mode 在非 testing 阶段不应被 invoke**
- ❌ **bug-triage 不引入第五种 root_cause 状态**（4 类强制）
- ❌ **workflow-evolution 不输出 patch/diff，不直接修 dev-workflow-skills2 文件**（advisory only + Action Item 标注）
- ❌ **INCIDENT skeleton 创建后不能跳过 changelog.py promote**
- ❌ **workflow-evolution finalization 序列 6.a-g 不可乱序 / 不可 silent skip**
- ❌ **PRD 不走 Bug Flow re-entry**（prd-exception 走 incident path 由 workflow-evolution 处理）
- ❌ **architecture_delta 长期事实改动不能仅写 delta**（必须同轮改主 doc）
- ❌ **SRS frontmatter 不能缺 `is_multi_module` / `architecture_change`**
- ❌ **consumed_unresolved_bugs 不能读 progress-history.md release-start entry list**（必须 BUG-*.md scan）
- ❌ **review skill 不能输出 `pending` / `pass` / `fail`**（三态术语仅 Stage 4 dev-test/dev-code review 用）
- ❌ **PRD/SRS/Architecture review 不能创建独立 review-report doc**（仅 Stage 4 三态 review-report）
- ❌ **review_iteration 归零不能等 advance**（progress.py update --event review-passed 事件本身归零）
- ❌ **`progress.py recover` 不修 BUG report frontmatter**（脏数据须人工 audit）
- ❌ **doc frontmatter `status` 不由 SKILL 自己改**（owner = doc-guardian status-transition helper）

---

## 11. 上下文压缩 / Memory Note

**用户偏好**（沿用 v1/v2 handoff）：

- 先框架后细节（记忆有限）
- 中文描述、英文术语
- 倾向 explicit 决策（不喜欢"待定"）
- 重视 reviewer feedback（codex 评审）

**典型对话节奏**：

- 用户给方向 → claude 提方案 + 选项 → 用户选定 → claude 落地
- claude 主动提示风险 + 推荐选项 + 备选选项

**已建立的工作模式**：

1. 重大设计 → 写 design proposal → 送 codex 评审 → 采纳 → 升版（design v0.1 → v0.5 闭环）
2. SKILL.md 设计 → 6 文件包（仅 SKILL.md 骨架，不带 references）→ 送 codex 评审 → 3 轮迭代到 0 High/0 Medium
3. 评审反馈 → 在 SKILL.md 上 in-place 修复（batch 3a 起省略独立 reviewer_feedback_response 文件；review report 表格已含修法记录）→ 准备下一轮 prompt → 用户手动跑 codex
4. 用 grep / sed / Python 脚本批量做精确替换（保持 6 文件一致性）；核心修改用 Edit 单条做以保持 unique 上下文

---

## 12. 评审循环结论

**收益递减拐点**：每个 batch 都在 round 3 急速收敛到 0 High / 0 Medium。

**总评审时间投入**：15 轮（4 design + 5 batch 1 + 3 batch 2 + 3 batch 3a）。

**最终 finding 收敛**：每 batch 都 High → 0；总数趋近个位（batch 3a 最终 round 3 仅 2 个 Low）。

**经验**（3 个 batch 一致）：

- High → Medium → Low 收敛趋势可靠
- 同一份文档评审 3 轮基本收敛
- Reviewer 反馈高质量（具体 file:line + 可执行 recommendation）
- batch 越往后，每轮 finding 数量递减（37 → 15 → 8 → 5 → 2）；batch 3a 收敛速度与 batch 2 相当（3 轮）
- batch 3b 应可类似 3 轮收敛（每轮 finding 不超过 batch 3a 水平）
- 总 batch 3 评审循环（batch 3a + 3b + 3c）期望不超过 9 轮

---

## 13. 下一个 Session 推荐第一句话

> "请读 `docs/handoff/session_handoff_20260506_v3.md` 了解项目状态，然后我们开始 Task 5 batch 3b：设计 development-* 6 个 vertical skill 的 SKILL.md 骨架（development-planning / development-test / development-code 各 write+review）。"

Claude 应：

1. 读 handoff doc + memory + 关键设计文件（v0.5 design proposal、batch 1+2+3a 关键 SKILL.md）
2. 简短确认理解状态（不要长篇复述）
3. 推荐 1 sub-batch 6 个 skill 一起做（参考 batch 3a 模式）
4. 与用户确认 §7.8 三个范围决策：(1) 仅 SKILL.md 骨架不做 references；(2) 三态 review report skeleton 创建时机；(3) verifying → verified 责任主体
5. 用 batch 3a 的 9 章节框架作骨架；额外覆盖 §7.5 列出的 5 个 batch 3b 特化点（task 状态机 / 三态 review report / per-task artifact / 子 agent 并发模型 / Stage 4 Done E 维度）
6. 设计完后送 codex review（参考 batch 3a 3 轮 prompt 模式：round 1 全面 + round 2/3 回归审查）

**预期 batch 3b 总产出**：6 个 development-* SKILL.md 骨架，约 1700-2300 行；评审 3 轮（每轮 finding ≤ 8）；总评审时间投入与 batch 3a 相当。

---

**End of Handoff v3 (batch 3a 闭环 + batch 3b 起步前)**
