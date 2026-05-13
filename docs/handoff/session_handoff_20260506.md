# Session Handoff — dev-workflow-skills2

**Handoff Date**: 2026-05-06
**Handoff By**: Claude (Opus 4.7, 1M context)
**Project**: `/home/cgs/github_projects/dev-workflow-skills2/`
**Status**: Batch 1 SKILL.md 设计完成（评审循环 5 轮闭环）；Batch 2 Orchestration + Meta skills 待启动

---

## 1. 项目一句话总结

`dev-workflow-skills2` 是一套面向个人使用的 R&D workflow skill 集合：**23 个 physical skill** 分 4 层（Vertical 18 / Cross-cutting 2 / Orchestration 2 / Meta 1）实现**7 阶段主流程 + Bug Flow + 4 场景（S1-S4）**，强 Foreman binary 校验 + Release 严格串行 + vendor-neutral 架构。

**重要**：本 skill 集**禁止应用于自己**（递归悖论），仅用于其他项目。

---

## 2. 当前进度（详细）

### 2.1 Task 状态

| # | Task | 状态 | 输出 |
|---|------|------|------|
| 1 | 收尾架构层决策（D3-Q3）| ✅ Done | 全部 D-decisions / Q-decisions 闭环 |
| 2 | 设计 workflow-protocol skill | ✅ Done | 5 项责任、progress 格式、scripts、并发模型、P6 矩阵、release lifecycle |
| 3 | 起草 AGENTS.md 治理文档 | ✅ Done | 10-section template（含在 design proposal v0.5 §6）|
| 4 | 设计 doc-guardian skill | ✅ Done | F1-F6（F4 跳过），含 binary 校验、scenario-aware required-artifacts |
| 5 | 设计 23 个 skill 的 SKILL.md 骨架 | 🟡 **in_progress（batch 1 done，batch 2/3 pending）** | Batch 1：workflow-protocol + doc-guardian 完整 SKILL.md + 4 references（评审 5 轮闭环）|
| 6 | 实现：写实际 skill 文件、scripts、AGENTS.md、CLAUDE.md | ⏳ Pending | 待 Task 5 全部完成后启动 |

### 2.2 Task 5 三批分解

**Batch 1（已完成）**：
- ✅ `skills/workflow-protocol/SKILL.md`（329 行）+ `references/command-reference.md`（552 行）
- ✅ `skills/doc-guardian/SKILL.md`（363 行）+ 4 个 references（共 1612 行）

**Batch 2（待启动 — 下一个新 session 的起点）**：
- ⏳ `skills/scenario-dispatcher/SKILL.md` — 4 场景判定 + S2 子场景路由 + S4 active-release 校验
- ⏳ `skills/bug-triage/SKILL.md` — active mode + post-close mode + PRD 异常分支
- ⏳ `skills/workflow-evolution/SKILL.md` — 消化 Stage 7 retrospective + PRD 异常 incident

**Batch 3（待 batch 2 完成后启动）**：
- ⏳ 17 个 vertical skill（PRD/SRS/Architecture/Development × 5/Testing/Delivery/Retrospective 各自 write/review pair）

---

## 3. 评审循环统计（已完成 9 轮）

### Design Proposal 评审（4 轮）

| 版本 | Finding 总数 | High | Medium | Low |
|------|-------------|------|--------|-----|
| v0.1 | 9 | 5 | 4 | 0 |
| v0.2 | 8 | 5 | 3 | 0 |
| v0.3 | 6 | 3 | 2 | 1 |
| v0.4 | 4 | 0 | 2 | 2 |

最终 design proposal 是 **v0.5**（design 在 v0.4 评审后升级到 v0.5；workflow spec 升级到 v0.6 含同步 + S3 Technical Debt 修正）。

### Batch 1 SKILL.md 评审（5 轮）

| 轮次 | Finding 总数 | High | Medium | Low | Recommendation |
|------|-------------|------|--------|-----|----------------|
| Round 1 | 16 | 8 | 5 | 3 | fix |
| Round 2 | 9 | 4 | 4 | 1 | fix |
| Round 3 | 5 | 2 | 2 | 1 | fix |
| Round 4 | 5 | 1 | 3 | 1 | fix |
| **Round 5** | **2** | **0** | **1** | **1** | **(A) 进 batch 2** |

**Batch 1 已正式闭环**。Round 5 codex 明确判定可实现：Python 实现者可基于 7 份文件直接实现 progress.py / validate.py / changelog.py。

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
- **Release 严格串行**：MAJOR.MINOR 整数对（`MAJOR.MINOR`），`(major, minor)` 数字对比较；同时只 1 个 active release
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

---

## 5. 文件清单（关键路径）

### 5.1 Skill 文件（已完成 batch 1）

```
skills/
├── workflow-protocol/
│   ├── SKILL.md                         主协议（329 行）
│   └── references/
│       └── command-reference.md         11 子命令完整 mutation（552 行）
└── doc-guardian/
    ├── SKILL.md                         主协议（363 行）
    └── references/
        ├── directory-layout.md          目录结构 + 命名 convention（236 行）
        ├── frontmatter-schema.md        全部 doc type 详细 schema（541 行）
        ├── change-log-format.md         Pending/Change Log 格式 + changelog.py（267 行）
        └── required-artifacts.md        scenario-aware required map + DSL parser 规范（391 行）
```

### 5.2 Workflow Spec & Design Proposal

```
docs/workflow/
├── workflow_specification_claude.md     v0.6 主 spec（含 5 轮 Change Log）
├── workflow_specification_draft_claude.md  v0.1 历史
├── product_lifecycle_workflow_hermes.md  第三方草稿（合并源）
└── product-project-workflow-spec-draft_code.md  第三方草稿（合并源）

docs/design/
├── skill_set_design_proposal_v0.1.md    历史
├── skill_set_design_proposal_v0.2.md    历史
├── skill_set_design_proposal_v0.3.md    历史
├── skill_set_design_proposal_v0.4.md    历史
└── skill_set_design_proposal_v0.5.md    **当前权威设计** + AGENTS.md template
```

### 5.3 Research 调研

```
docs/research/
├── superpowers_design_claude.md
├── dev_workflow_skills_v1_design_claude.md
├── forge_design_claude.md
├── foreman_design_claude.md
└── skill_design_comparison_claude.md
```

### 5.4 Review Cycle 历史

```
docs/review/
├── codex_review_prompt_batch1.md          round 1 prompt
├── codex_review_prompt_batch1_round2.md   round 2 prompt
├── codex_review_prompt_batch1_round3.md   round 3 prompt
├── codex_review_prompt_batch1_round4.md   round 4 prompt
├── codex_review_prompt_batch1_round5.md   round 5 prompt
├── skill_set_design_proposal_v0.1_review.md
├── skill_set_design_proposal_v0.2_rereview.md
├── skill_set_design_proposal_v0.3_rereview.md
├── skill_set_design_proposal_v0.4_rereview.md
├── skill_set_batch1_review.md
├── skill_set_batch1_round2_review.md
├── skill_set_batch1_round3_review.md
├── skill_set_batch1_round4_review.md
├── skill_set_batch1_round5_review.md      **本轮终轮，A 通过**
├── reviewer_feedback_response_v0.1.md
├── reviewer_feedback_response_v0.2.md
├── reviewer_feedback_response_v0.3.md
├── reviewer_feedback_response_v0.4.md
├── reviewer_feedback_response_v0.5_batch1.md
├── reviewer_feedback_response_v0.6_batch1_round2.md
├── reviewer_feedback_response_v0.7_batch1_round3.md
└── reviewer_feedback_response_v0.8_batch1_round4.md
```

---

## 6. Memory 文件（持久化决策）

位置：`~/.claude/projects/-home-cgs-github-projects-dev-workflow-skills2/memory/`

| 文件 | 内容 |
|------|------|
| `MEMORY.md` | 索引 |
| `feedback_design_style.md` | 用户偏好：先框架后细节 |
| `project_framework.md` | 7 阶段主流程 + Bug 流程 + 4 场景映射 |
| `project_skill_architecture.md` | 22 个 skill 4 层架构（**实际 23**，待 update）+ 全部 D/Q-decisions |
| `project_workflow_protocol_design.md` | workflow-protocol 详细设计 + 11 子命令 + S4 / PRD 异常处理 |

**Memory 同步注意**：`project_skill_architecture.md` 仍写"22 个 skill"；实际 v0.6 起含 development-code-review 后是 **23 个**。新 session 启动时建议 update（或在新 session 内查看 design proposal v0.5 为准）。

---

## 7. 新 Session 起手指南

**第一步（必做）**：读以下 3 份文件了解全貌：

1. `docs/handoff/session_handoff_20260506.md`（**本文件**）
2. `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计）
3. `docs/review/skill_set_batch1_round5_review.md`（最近评审 + recommendation）

**第二步**：检查 memory 加载情况（`MEMORY.md` 应自动加载）。

**第三步**：决定 batch 2 起点（推荐顺序）：

1. **scenario-dispatcher**（先）—— 决定 S1/S2/S3/S4 + S2 子场景（最复杂的入口路由）
2. **bug-triage**（次）—— 双模式（active + post-close）+ PRD 异常分支
3. **workflow-evolution**（最后）—— 消化 retrospective 与 incident report

每个 skill 设计参考 batch 1 `workflow-protocol` / `doc-guardian` 的结构模板（SKILL.md + references/）。

---

## 8. Watch List for Task 6 实现

Round 5 评审给的实现关注点：

1. **DSL parser**：以 `required-artifacts.md` 顶部 §Condition DSL 完整 grammar 为准（不要照抄 §12 docstring，已修正但仍简略）
2. **recover**：按 `command-reference.md` §4 的 replay validator 算法实现；terminal event 后 mutating entry **必须 fatal**（exit 1），禁止 silent truncate
3. **review report 三态**：`pending` skeleton 合法但不能推进 task；只有 `pass` 才允许 Stage 4 `test-done` / `code-review-passed`
4. **Stage 4 unconditional validation**：advance 时对每个 task 无条件校验全部 4 个 per-task artifacts（不按 substate 匹配）
5. **S3 必备 artifacts**：Stage 1 `prd-level` + `feature-matrix`；Stage 2 `srs-level` + `module-level` + `reuse-replace`（technical-debt 推荐非必备）
6. **ID 格式**：强制 3 位 zero-padded；`BUG-1000` 等 4 位 reject

Task 6 单元测试必须覆盖：

- 三态 review report（pending → pass / pending → fail / 直接 pass / 直接 fail）
- terminal recover corruption（terminal 后伪造 mutating entry → fatal）
- Stage 4 unconditional per-task validation（任一 artifact 缺失 → fail）
- S3 3+1 source-system-analysis 清单（Stage 2 缺 reuse-replace → fail；缺 technical-debt → pass）
- DSL parser 6 个 test cases（见 `required-artifacts.md` §Condition DSL）

---

## 9. 关键约束（不可破坏）

任何后续工作必须遵守：

- ❌ **不修改架构层决策**（除非有强理由 + 用户同意）—— 评审循环已 5 轮验证
- ❌ **不应用本 skill 集到 dev-workflow-skills2 自身**（递归悖论）
- ❌ **不绕过 progress.py 直接编辑 progress.md / progress-history.md**
- ❌ **不绕过 changelog.py 直接编辑 Change Log 章节**
- ❌ **不绕过 validate.py 推进 stage**
- ❌ **review skill 输出绝不用 `approved`**（用 `review-passed` / `issues-found`）
- ❌ **新 doc type 必须先走 design proposal review cycle**

---

## 10. 上下文压缩 / Memory Note

**用户偏好**：
- 先框架后细节（记忆有限）
- 中文描述、英文术语
- 倾向 explicit 决策（不喜欢"待定"）
- 重视 reviewer feedback（codex 评审）

**典型对话节奏**：
- 用户给方向 → claude 提方案 + 选项 → 用户选定 → claude 落地
- claude 主动提示风险 + 推荐选项 + 备选选项

**已建立的工作模式**：

1. 重大设计 → 写 design proposal → 送 codex 评审 → 采纳 → 升版
2. SKILL.md 设计 → 4 文件包（SKILL.md + key references）→ 送 codex 评审 → 5 轮迭代到 0 High

---

## 11. 评审循环结论

**收益递减拐点**：design v0.4（0 High）和 batch 1 round 5（0 High）。
**总评审时间投入**：9 轮（4 design + 5 batch 1）。
**最终 finding 收敛**：High 8 → 0；总数 16 → 2。

**经验**：

- High → Medium → Low 收敛趋势可靠
- 同一份文档评审 3+ 轮后基本收敛
- Reviewer 反馈高质量（具体 file:line + 可执行 recommendation）
- spec-level 推演收益在 round 4-5 急速递减；建议 batch 2/3 评审循环可放宽到 2-3 轮

---

## 12. 下一个 Session 推荐第一句话

> "请读 `docs/handoff/session_handoff_20260506.md` 了解项目状态，然后我们开始 Task 5 batch 2：设计 scenario-dispatcher、bug-triage、workflow-evolution 三个 SKILL.md。"

claude 应：

1. 读 handoff doc + memory + 关键设计文件（v0.5 design proposal、batch 1 SKILL.md）
2. 简短确认理解状态（不要长篇复述）
3. 推荐从 scenario-dispatcher 起步（最复杂的路由 skill）
4. 用 batch 1 的结构模板（SKILL.md + references/）作骨架

---

**End of Handoff**
