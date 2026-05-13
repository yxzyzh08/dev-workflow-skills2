# Session Handoff — dev-workflow-skills2 (v2)

**Handoff Date**: 2026-05-06
**Handoff By**: Claude (Opus 4.7, 1M context)
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Status**: Batch 2 SKILL.md 设计**正式闭环**（评审循环 3 轮：High 3 → 0 → 0；Round 3 全部 ✅，0 New High，3 Low cleanup 已修）；Batch 3 (17 个 Vertical Skill) 待启动

**Predecessor Handoff**: `docs/handoff/session_handoff_20260506.md`（v1，batch 1 闭环时点）

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
| 5.1 | Batch 1 SKILL.md（workflow-protocol + doc-guardian）| ✅ **闭环**（5 轮评审）| 6 份文件，最后 round 5 finding=2 (0H/1M/1L) |
| 5.2 | Batch 2 SKILL.md（scenario-dispatcher + bug-triage + workflow-evolution）| ✅ **闭环**（3 轮评审）| 7 份文件，最后 round 3 finding=3 (0H/0M/3L 已修)|
| 5.3 | Batch 3 SKILL.md（17 个 vertical skill）| ⏳ **Pending — 下一个新 session 的起点** | 见 §7 |
| 6 | 实现：写实际 skill 文件、scripts、AGENTS.md、CLAUDE.md | ⏳ Pending | 待 Task 5 全部完成后启动 |

### 2.2 Batch 2 评审历程

| 轮次 | Finding 总数 | High | Medium | Low | 处置 |
|------|------------|------|--------|-----|------|
| Round 1 | 5 | 3 | 2 | 0 | 全部采纳，写 v0.9 feedback response |
| Round 2 | 7 | 0 | 6 | 1 | 全部采纳，写 v0.10 feedback response |
| Round 3 | 3 | 0 | 0 | 3 | 全部采纳，写 v0.11 feedback response（batch 2 闭环）|

**Batch 2 比 Batch 1 收敛快**：3 轮 vs 5 轮；High 在 round 2 就清零；累计 finding 15 vs batch 1 的 37。

---

## 3. 完整评审循环统计

| 版本 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|---------------|
| design v0.1 | 9 | 5 | 4 | 0 | fix |
| design v0.2 | 8 | 5 | 3 | 0 | fix |
| design v0.3 | 6 | 3 | 2 | 1 | fix |
| design v0.4 | 4 | 0 | 2 | 2 | fix → v0.5 闭环 |
| batch 1 round 1 | 16 | 8 | 5 | 3 | fix |
| batch 1 round 2 | 9 | 4 | 4 | 1 | fix |
| batch 1 round 3 | 5 | 2 | 2 | 1 | fix |
| batch 1 round 4 | 5 | 1 | 3 | 1 | fix |
| batch 1 round 5 | 2 | 0 | 1 | 1 | (A) 闭环 |
| batch 2 round 1 | 5 | 3 | 2 | 0 | fix |
| batch 2 round 2 | 7 | 0 | 6 | 1 | fix |
| batch 2 round 3 | 3 | 0 | 0 | 3 | **(A) 闭环** |
| **总计 12 轮** | **79** | **31** | **34** | **14** | — |

**经验**：
- High → Medium → Low 收敛趋势在每个 batch 都可靠
- 单 batch 评审循环通常收敛于 3-5 轮
- spec-level 推演收益在 round 4-5 急速递减

---

## 4. 关键架构决策（已闭环 — 不可再质疑结构合理性）

### 4.1 Skill 架构

| Layer | Skill 数 | 内容 |
|-------|---------|------|
| 1 Vertical | 18 | 7 logical Stage Skill 的 write/review pair（Stage 4 拆 6 个：planning/test/code 各 write+review）|
| 2 Cross-cutting | 2 | workflow-protocol / doc-guardian |
| 3 Orchestration | 2 | scenario-dispatcher / bug-triage |
| 4 Meta | 1 | workflow-evolution |
| **总计** | **23** | |

### 4.2 工作流框架

- **7 阶段主流程**：PRD Inception → SRS Specification → Architecture Design → Development → Testing → Delivery → Project Retrospective
- **4 场景**：S1 New Product / S2 Feature Evolution（4 子场景）/ S3 Product Reconstruction / S4 Bug Fix
- **Bug Flow 4 类根因路由**：SRS / Architecture / Development / PRD（异常逃生阀）
- **Release 严格串行**：MAJOR.MINOR 整数对，按 (major, minor) 数字对比较
- **S4 仅 active release 期间允许**；post-close bug 走 bug-intake 暂存

### 4.3 重要设计决策汇总

| 决策点 | 选定 |
|--------|------|
| 评审结构 | Foreman 模式（write/review 分开 physical skill）|
| 评审上限 | 7 次（progress.md 记录）|
| Stage 4 拆分 | Option I：规划设计 / 测试 / 代码 三组（含 code review）|
| D1 校验机制 | Foreman binary：doc-guardian/scripts/validate.py，exit 0/1 |
| D2 CLAUDE.md 形态 | foreman 模式：CLAUDE.md = `@AGENTS.md` |
| D3 SessionStart Hook | 不要 |
| D4 vendor-neutral skill 结构 | 要：双 symlink |
| D5 Risk-based review | 不要 v1 |
| Q1 评审超 7 次 | 升级人介入 |
| Q2 cr-guardian | 合并进 doc-guardian |
| Q3 project-memory-manager | 不独立（用 progress.md + history）|
| 脚本路径 | 全 skill 路径 `skills/<name>/scripts/<x>.py` |
| Release 并发 | 严格串行 |
| S4 policy | active-release-only |
| Logical vs Physical Skill | "One Stage Skill" 是 logical，可对应多个 physical |
| Version grammar | MAJOR.MINOR 整数对（无 patch、无 pre-release）|
| Bug intake | bug-triage post-close mode + `progress.py bug-intake` |
| PRD exception | `bug_flow.root_cause: prd-exception` + `workflow_incident_active: true` |
| Bug Flow 闭环 | `progress.py bug-start` 进入 + `bug-close` 退出 |
| Incident 终态字段 | `project_state: aborted | reconstructing` + `release_close_reason` |
| Code review | `development-code-review` skill（非测试代码评审）|
| Test code review | `development-test-review` skill 产出 `test-review-report` |
| Review report 三态 | `pending | pass | fail`：skeleton 默认 pending；transition 严格要求 pass |
| ID 格式 | 强制 3 位 zero-padded（`^(CR\|BUG\|INCIDENT)-\d{3}$`）|
| Update 接口 | `update --event <name>` 命名事件白名单（4 个）+ `--advance` + `--task` |
| Required artifacts | doc-guardian/references/required-artifacts.md（scenario-aware DSL map）|
| DSL parser | 白名单 6 变量 + 5 运算符 + 3 类 literal；禁用 eval/exec |
| Recover 终态语义 | terminal 后 mutating entry → exit 1 fatal；禁止 silent truncate |

### 4.4 Batch 2 新增决策（全部 3 轮闭环）

| 决策点 | Round | 选定 |
|--------|-------|------|
| dispatcher Output Contract 三类 | round 1 | (A) 调命令 / (B) 路由 skill / (C) 拒绝 + 提示 |
| S2 子场景判定 | round 1 | 严格 3 题序列（PRD 改？→ 架构骨架变？→ SRS 改？）；模糊不猜 |
| S2-4 二次确认 | round 1 | 转 S3 起新 project 回滚成本极高，必须二次确认 |
| Active mode 入口前置 | **round 2 batch2-F2** | 严格 = `progress.py bug-start` 前置（current_stage==testing AND sub_state==review-passed）；非 testing 一律 dispatcher reject |
| **三层 gate 一致** | **round 3 M1** | dispatcher / bug-triage / progress.py 前置全文一致；triage-decision-tree §1 顶层决策树 + §2.1 Step 0 early gate；frontmatter description 收紧 |
| Active mode 强制 4 类输出 | **round 2 batch2-F3** | 删除 out-of-scope 第五路径；用户决策 BUG 撤销 → 用户**手动删除**文件，bug-triage 不调 progress.py |
| INCIDENT skeleton changelog 流程 | **round 2 batch2-F1** | bug-triage 创建 skeleton → `changelog.py promote` → `validate.py file` → `incident-start`（缺一不可） |
| advisory vs patch 严格区分 | **round 2 batch2-F4** | workflow-evolution **允许**自然语言 advisory + Action Item 标注；**禁止** patch/diff/直接编辑本 skill 集文件；retrospective + incident mode 一致 |
| INCIDENT finalization 序列 | **round 2 batch2-F5** | Step 6.a-g 严格序列：body → frontmatter (resolution_action + status + updated) → Pending → promote → validate → incident-resolve；validate 后禁改 doc |
| reentrant 幂等性二次确认 | **round 3 M5** | 拆 finalization-complete vs body-only 已写两态；后者必须重 promote/validate；reentrant_finalization_check 伪代码 |
| progress.py 二次 validate 契约 | **round 3 M6** | command-reference §10 incident-start + §11 incident-resolve 加前置 `validate.py file <incident-path> exit 0`（double-safety；caller 一次 + progress.py 二次）|
| no-suggestion legitimacy | **round 3 L2** | retrospective 模板某类无 actionable 建议 → 填 `None — no actionable suggestion found`；不为凑表格编造 |

---

## 5. 文件清单（精确路径）

### 5.1 Skill 文件（已完成 batch 1 + batch 2，共 5 个 skill 物理目录）

```
skills/
├── workflow-protocol/                    # batch 1
│   ├── SKILL.md                          (329 行)
│   └── references/
│       └── command-reference.md          (593 行；round 3 M6 加 §10/§11 validate 前置)
│
├── doc-guardian/                         # batch 1
│   ├── SKILL.md                          (365 行)
│   └── references/
│       ├── directory-layout.md           (236 行)
│       ├── frontmatter-schema.md         (541 行)
│       ├── change-log-format.md          (267 行)
│       └── required-artifacts.md         (391 行)
│
├── scenario-dispatcher/                  # batch 2
│   ├── SKILL.md                          (235 行)
│   └── references/
│       └── scenario-decision-tree.md     (651 行)
│
├── bug-triage/                           # batch 2
│   ├── SKILL.md                          (468 行)
│   └── references/
│       ├── root-cause-rubric.md          (525 行)
│       └── triage-decision-tree.md       (827 行；round 3 L1 注释修复)
│
└── workflow-evolution/                   # batch 2
    ├── SKILL.md                          (489 行；round 3 L2 加 No-Suggestion Legitimacy)
    └── references/
        └── incident-analysis-template.md (762 行；round 3 L2 + L3 修)
```

**总计**：5 个 skill / 12 份 .md 文件 / **约 6378 行**。

### 5.2 Workflow Spec & Design Proposal

```
docs/workflow/
├── workflow_specification_claude.md          v0.6 主 spec（不变）
├── workflow_specification_draft_claude.md    v0.1 历史
├── product_lifecycle_workflow_hermes.md      第三方草稿（合并源）
└── product-project-workflow-spec-draft_code.md 第三方草稿（合并源）

docs/design/
├── skill_set_design_proposal_v0.1.md  历史
├── skill_set_design_proposal_v0.2.md  历史
├── skill_set_design_proposal_v0.3.md  历史
├── skill_set_design_proposal_v0.4.md  历史
└── skill_set_design_proposal_v0.5.md  **当前权威设计** + AGENTS.md template（含 batch 2 后未升 v0.6 design，因 batch 2 修改主要在 SKILL.md 与 references 层）
```

### 5.3 Review Cycle 历史（完整 12 轮）

```
docs/review/
├── codex_review_prompt_batch1.md
├── codex_review_prompt_batch1_round{2,3,4,5}.md
├── codex_review_prompt_batch2.md
├── codex_review_prompt_batch2_round{2,3}.md
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
├── reviewer_feedback_response_v0.{1,2,3,4}.md       # design 阶段
├── reviewer_feedback_response_v0.5_batch1.md        # batch 1 round 1
├── reviewer_feedback_response_v0.{6,7,8}_batch1_round{2,3,4}.md
├── reviewer_feedback_response_v0.9_batch2.md        # batch 2 round 1
├── reviewer_feedback_response_v0.10_batch2_round2.md
└── reviewer_feedback_response_v0.11_batch2_round3.md  # batch 2 闭环
```

### 5.4 Handoff 文档

```
docs/handoff/
├── session_handoff_20260506.md      # v1（batch 1 闭环时点；batch 2 起步前）
└── session_handoff_20260506_v2.md   # v2（**本文件**；batch 2 闭环时点；batch 3 起步前）
```

### 5.5 Research 调研

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
| `project_skill_architecture.md` | 4 层架构 + 全部 D/Q-decisions | ⚠️ **需 update**：仍写 22；实际是 **23 个 skill**（含 development-code-review）|
| `project_workflow_protocol_design.md` | workflow-protocol 详细设计 | OK |

**新 Session 起手时建议**：检查并 update `project_skill_architecture.md` 的 skill 总数（22→23）；或在新 session 内以 design proposal v0.5 为准（design 中已写 23）。

---

## 7. 新 Session 起手指南：Batch 3（17 个 Vertical Skill 骨架）

### 7.1 第一步（必做）：读以下 3 份文件了解全貌

1. `docs/handoff/session_handoff_20260506_v2.md`（**本文件**）
2. `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计）
3. `docs/review/skill_set_batch2_round3_review.md`（最近评审 + recommendation A）

### 7.2 第二步：检查 memory 加载情况

`MEMORY.md` 应自动加载。如发现 `project_skill_architecture.md` 仍写 22，update 为 23（不阻塞）。

### 7.3 第三步：确认 batch 2 闭环状态

- 全部 5 个 batch 2 文件（3 SKILL.md + 4 references）round 3 已 ✅
- batch 1 reference command-reference.md 在 round 3 M6 也同步修了（incident-start / incident-resolve 加 validate 前置）
- 进 batch 3 前**不需要**再做 batch 2 review

### 7.4 第四步：决定 batch 3 拆分（17 个 vertical skill）

**17 个 vertical skill** = 7 logical stage 的 write/review pair（Stage 4 拆 6 个）：

| Stage | Skills（physical）|
|-------|-----------------|
| 1 PRD | `prd-write` / `prd-review` |
| 2 SRS | `srs-write` / `srs-review` |
| 3 Architecture | `architecture-write` / `architecture-review` |
| 4 Development - Planning | `development-planning-write` / `development-planning-review` |
| 4 Development - Test | `development-test-write` / `development-test-review` |
| 4 Development - Code | `development-code-write` / `development-code-review` |
| 5 Testing | `testing-write` / `testing-review` |
| 6 Delivery | `delivery-write` / `delivery-review` |
| 7 Retrospective | `retrospective-write` / `retrospective-review` |

**总计**：17 个 physical vertical skill。design proposal §3.2 列 18 — 那是因为 batch 1 闭环阶段把 development-code-review 单独算入；实际 vertical skill = 18，但已包括 18 个 write/review pair；本 batch 仅起骨架 17 个的 SKILL.md（development-code-review 在 batch 1 已隐含但仍需 SKILL.md）。

**确认 design proposal §3.2 准确**：18 个 vertical = **9 stage role × 2 (write/review)**：
1. prd × 2
2. srs × 2
3. architecture × 2
4. development-planning × 2
5. development-test × 2
6. development-code × 2
7. testing × 2
8. delivery × 2
9. retrospective × 2

= **18 个 vertical skill**。本 batch 起骨架的就是这 18 个。前一个 handoff 因小笔误写"17"，真实数字是 **18**。

### 7.5 第五步：Batch 3 子拆分推荐

由于 18 个 skill 量大，建议进一步拆 **3 sub-batch**：

| Sub-batch | Stages | Skill 数 | 备注 |
|-----------|--------|---------|------|
| **3a 主线 PRD/SRS/Arch** | 1, 2, 3 | 6 | 高 gating 阶段（人 gate）；最复杂的契约层 |
| **3b 主线 Development** | 4 (planning/test/code) | 6 | task 状态机最复杂；含 code review 三态 / per-task artifact |
| **3c 主线 Testing/Delivery/Retro** | 5, 6, 7 | 6 | E 维度内部验证 / Bug Flow 触发 / 跨 release retrospective |

**推荐顺序**：3a → 3b → 3c。3a 完成后送一轮 codex review 校准风格，再开 3b/3c。

### 7.6 第六步：每个 vertical skill SKILL.md 应覆盖的章节

参考 batch 1 / batch 2 的结构模板（Authority + When to Invoke + 5-7 个核心 sections + Forbidden Actions + Recovery + References），具体到 vertical skill 应额外覆盖：

| 章节 | 内容 |
|------|------|
| Authority & Scope | authority 4；本 skill pair 在 stage X 中的角色 |
| When to Invoke | 由 progress.py update 状态机驱动；列出 sub_state 转换条件 |
| Full Mode vs Change Mode | 4 场景（S1/S2/S3/S4）的入口分别走哪种 mode |
| Doc Output Contract | 该 skill 写哪些 doc 类型（type / 路径 / required artifacts）；引用 doc-guardian frontmatter-schema |
| 4 步标准流程（write skill）| 1) 写 doc → 2) Pending Changes → 3) changelog promote → 4) validate self-check → 5) 提交 review |
| Review Rubric（review skill）| 评审维度 + 输出术语 (`review-passed` / `issues-found`) + 三态报告（仅 development-test/code-review）|
| Stage Done Conditions | A/B/C/D/E 5 维度（参 workflow-protocol §5.2）|
| Bug Flow Re-entry | Stage 5 testing 失败时如何切 Change Mode（applicable to PRD/SRS/Arch/Dev write skills）|
| Forbidden Actions | bypass progress.py / bypass validate.py / approval 权限越界 |

### 7.7 第七步：每个 vertical skill 的 references 建议

| Skill 类型 | 推荐 references |
|-----------|----------------|
| `prd-write` / `prd-review` | `references/prd-template.md`（含 supporting artifacts schema）+ `references/review-rubric.md` |
| `srs-write` / `srs-review` | `references/srs-template.md`（多模块 / Acceptance Plan / Integration Plan）+ `references/review-rubric.md`；srs-write 还需 `references/bug-merge-policy.md`（合并 unresolved_bugs 到新 SRS） |
| `architecture-write` / `architecture-review` | `references/architecture-template.md`（含 architecture_delta 增量格式）+ `references/review-rubric.md` |
| `development-planning-*` | `references/breakdown-template.md` + `references/detailed-design-template.md` + `references/review-rubric.md` |
| `development-test-*` | `references/test-naming.md` + `references/test-review-rubric.md`（三态：pending/pass/fail）|
| `development-code-*` | `references/code-style.md`（vendor-neutral）+ `references/code-review-rubric.md`（三态）|
| `testing-*` | `references/test-procedure-template.md` + `references/bug-report-trigger-rules.md`（何时触发 bug-triage）|
| `delivery-*` | `references/deployment-checklist.md` + `references/operation-manual-template.md` |
| `retrospective-*` | `references/retrospective-sections-template.md`（项目级单文件，每 release 加节）|

具体决定哪些 reference 拆分由 batch 3 设计时与 codex 评审周期共同决定，无需现在锁定。

### 7.8 第八步：Batch 3 评审策略

handoff §11 提示 batch 2/3 评审循环放宽到 2-3 轮。Batch 3 量大（18 skill），建议：

- **3a sub-batch** 完成后送 1 轮 codex review；如 0 High 进 3b
- **3b sub-batch** 完成后送 1 轮 codex review
- **3c sub-batch** 完成后送 1 轮 codex review
- 全部 3 sub-batch 完成后**整体送 1 轮**横向一致性 review
- 期望总评审 ≤ 5 轮（含 1 轮整体）

---

## 8. Watch List for Task 6 实现

Round 5 (batch 1) + Round 3 (batch 2) 评审给的实现关注点：

1. **DSL parser**：以 `required-artifacts.md` 顶部 §Condition DSL 完整 grammar 为准
2. **recover**：按 `command-reference.md` §4 的 replay validator 算法实现；terminal event 后 mutating entry **必须 fatal**（exit 1）
3. **review report 三态**：`pending` skeleton 合法但不能推进 task；只有 `pass` 才允许 Stage 4 `test-done` / `code-review-passed`
4. **Stage 4 unconditional validation**：advance 时对每个 task 无条件校验全部 4 个 per-task artifacts
5. **S3 必备 artifacts**：Stage 1 `prd-level` + `feature-matrix`；Stage 2 `srs-level` + `module-level` + `reuse-replace`（technical-debt 推荐非必备）
6. **ID 格式**：强制 3 位 zero-padded；`BUG-1000` 等 4 位 reject
7. **bug-triage active mode 三层 gate**（batch 2 round 3 M1）：dispatcher / bug-triage / progress.py 前置全文一致 = `release_state==active AND current_stage==testing AND sub_state==review-passed`
8. **INCIDENT skeleton 必经 promote**（batch 2 round 2 F1）：bug-triage 创建后必须 `changelog.py promote → validate.py file → incident-start`，缺一不可
9. **incident-start / incident-resolve 二次 validate**（batch 2 round 3 M6）：progress.py 内部必须再跑一次 `validate.py file <incident-path>`，与 caller validate 形成 double-safety
10. **workflow-evolution reentrant 幂等性**（batch 2 round 3 M5）：重 invoke 时不可仅凭 `status=review-passed` 直接重试 incident-resolve，必须再跑 validate.py 确认 Pending 已空
11. **bug-triage 4 类强制**（batch 2 round 2 F3）：active mode 必须输出 4 类之一，无 out-of-scope 第五路径；用户决策 BUG 撤销 → 用户手动删文件
12. **workflow-evolution advisory vs patch**（batch 2 round 2 F4）：禁止输出 patch/diff；自然语言 advisory + Action Item 标注允许并鼓励

Task 6 单元测试必须覆盖：

- 三态 review report（pending → pass / pending → fail / 直接 pass / 直接 fail）
- terminal recover corruption（terminal 后伪造 mutating entry → fatal）
- Stage 4 unconditional per-task validation（任一 artifact 缺失 → fail）
- S3 3+1 source-system-analysis 清单（Stage 2 缺 reuse-replace → fail；缺 technical-debt → pass）
- DSL parser 6 个 test cases
- bug-triage 三层 gate（非 testing 报 bug → dispatcher reject；testing 报 bug → 走 active mode）
- INCIDENT skeleton promote 流程（缺 promote → validate fail）
- incident-resolve double-safety（caller 漏 validate → progress.py 拒绝）
- workflow-evolution reentrant（status=review-passed 但 Pending 非空 → 不允许直接重试）

---

## 9. 关键约束（不可破坏）

任何后续工作必须遵守：

- ❌ **不修改架构层决策**（除非有强理由 + 用户同意）—— 评审循环已 12 轮验证（4 design + 5 batch 1 + 3 batch 2）
- ❌ **不应用本 skill 集到 dev-workflow-skills2 自身**（递归悖论）
- ❌ **不绕过 progress.py 直接编辑 progress.md / progress-history.md**
- ❌ **不绕过 changelog.py 直接编辑 Change Log 章节**
- ❌ **不绕过 validate.py 推进 stage**
- ❌ **review skill 输出绝不用 `approved`**（用 `review-passed` / `issues-found`）
- ❌ **新 doc type 必须先走 design proposal review cycle**
- ❌ **bug-triage active mode 在非 testing 阶段不应被 invoke**（dispatcher 在那一层 reject）
- ❌ **bug-triage 不引入第五种 root_cause 状态**（4 类强制）
- ❌ **workflow-evolution 不输出 patch/diff，不直接修 dev-workflow-skills2 文件**（advisory only + Action Item 标注）
- ❌ **INCIDENT skeleton 创建后不能跳过 changelog.py promote**（validate.py 类 6 会拒绝）
- ❌ **workflow-evolution finalization 序列 6.a-g 不可乱序 / 不可 silent skip**

---

## 10. 上下文压缩 / Memory Note

**用户偏好**（沿用 v1 handoff）：
- 先框架后细节（记忆有限）
- 中文描述、英文术语
- 倾向 explicit 决策（不喜欢"待定"）
- 重视 reviewer feedback（codex 评审）

**典型对话节奏**：
- 用户给方向 → claude 提方案 + 选项 → 用户选定 → claude 落地
- claude 主动提示风险 + 推荐选项 + 备选选项

**已建立的工作模式**：

1. 重大设计 → 写 design proposal → 送 codex 评审 → 采纳 → 升版（design v0.1 → v0.5 闭环）
2. SKILL.md 设计 → 4-7 文件包（SKILL.md + key references）→ 送 codex 评审 → 3-5 轮迭代到 0 High
3. 评审反馈 → 写 reviewer_feedback_response_vN.md → 修文件 → 准备下一轮 prompt → 用户手动跑 codex
4. 本 session 持续 batch 2 round 1-3 + 全部 finding 闭环 + 完整交接

---

## 11. 评审循环结论

**收益递减拐点**：每个 batch 都在 round 3-5 急速收敛到 0 High。
**总评审时间投入**：12 轮（4 design + 5 batch 1 + 3 batch 2）。
**最终 finding 收敛**：每 batch 都 High → 0；总数趋近个位。

**经验**（batch 2 验证 batch 1 经验）：

- High → Medium → Low 收敛趋势可靠
- 同一份文档评审 3+ 轮后基本收敛
- Reviewer 反馈高质量（具体 file:line + 可执行 recommendation）
- batch 2 比 batch 1 收敛快（3 轮 vs 5 轮），印证文档质量随经验提升
- batch 3 应可以更快收敛（每 sub-batch 2-3 轮，总不超过 5 轮）

---

## 12. 下一个 Session 推荐第一句话

> "请读 `docs/handoff/session_handoff_20260506_v2.md` 了解项目状态，然后我们开始 Task 5 batch 3：设计 18 个 vertical skill 的 SKILL.md 骨架。我们先做 batch 3a（PRD/SRS/Architecture，6 个 skill）。"

Claude 应：

1. 读 handoff doc + memory + 关键设计文件（v0.5 design proposal、batch 1 + 2 SKILL.md）
2. 简短确认理解状态（不要长篇复述）
3. 推荐从 batch 3a 起步（参考 §7.5）
4. 与用户确认每个 skill 的 reference 数量预算（参考 §7.7）
5. 用 batch 1 / batch 2 的结构模板（SKILL.md + references/）作骨架

**预期 batch 3 总产出**：18 个 vertical skill SKILL.md + 约 25-35 个 references；总行数估计 8000-12000 行；评审 3-5 轮（每 sub-batch 1-2 轮 + 整体 1 轮）。

---

**End of Handoff v2 (batch 2 闭环 + batch 3 起步前)**
