# Skill Set Batch 3b Round 2 Review (post-fix regression)

**Review Target**:
- `skills/development-planning-write/SKILL.md` (240 行，+6)
- `skills/development-planning-review/SKILL.md` (195 行，+5)
- `skills/development-test-write/SKILL.md` (206 行，+7)
- `skills/development-test-review/SKILL.md` (210 行，+6)
- `skills/development-code-write/SKILL.md` (252 行，+17)
- `skills/development-code-review/SKILL.md` (215 行，+6)
- 总计 1318 行（+47 vs Round 1）

**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`
**Round 1 Review**: `docs/review/skill_set_batch3b_review.md`
**Round 1 Prompt**: `docs/review/claude_review_prompt_batch3b.md`
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: regression: 0 remaining；new findings: 0 High / 0 Medium / 1 Low；recommendation: **(A) 进 batch 3c**

---

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|----------|------|
| **H1 Gap-4 verified task rollback** | ✅ 已修 | planning-write §3 line 81（Direct Route 行）+ §7 line 194 + §10 末段、test-write §2 line 59 + §10 末段、code-write §2 line 60 + §10 末段三处共 6 个声明位均显式声明 Gap-4，含三条缺失 transition（`verified -> test-revising` / `verified -> code-revising` / `code-review-passed -> code-revising`）+ 推荐 `progress.py bug-start --root-cause development` 解析 BUG body `Affected Task(s)` 自动回退；明确禁止手工改 progress.md。与 bug-triage `Affected Task(s)` 事实源一致。 |
| **H2 Gap-3 verification fail rollback** | ✅ 已修 | code-write §10 Gap-3 段已增推荐 transition `verifying -> code-revising` + 前置 `verification_result.md verification_status: fail|partial`；code-review §10 Gap-3 awareness 同步更新；§5.2 Step V4 仍要求 pass 才 verified、fail/partial 不得标 verified；§8 Forbidden 第 6 条仍禁止 verification fail 后绕过 code review。 |
| **M1 partial task registration recovery** | ✅ 已修 | planning-review §2 line 40 / 52 / 56 增加 review-passed + partial registration 入口；§4.1 line 83 + §5 Step 5 retry 行 + §9 recovery 行三处一致地声明：跳过业务评审 / 不重发 review-passed event / 已 planning-done task 视为幂等成功 / 不手工补 progress.md / 顺序 review-passed 先于 task planning-done 仍保持。 |
| **M2 validate.py file/task registration boundary** | ✅ 已修 | planning-write §5 Step 4 line 151 改写："task_id 与 breakdown/progress 的跨文件一致性由后续 progress.py/consistency 校验承担"；§5 关键约束第 2-3 条明确 `validate.py file` 仅 class 1-7、class 8 由 `validate.py consistency` / `progress.py update --advance` 兜底，原子一致性责任在 `progress.py update --task ... planning-done` 实现内。planning-write §10 与 planning-review §10 Task registration note (v0.6 batch 3b M2) 同步修。 |
| **M3 Stage 4 C composite** | ✅ 已修 | planning-review §6 line 146、test-review §6 line 167、code-review §6 line 168 各增"Stage 4 C 维度复合判定"段，明确 = planning review-passed + each task test_review_report.md `review_status: pass` + each task code_review_report.md `review_status: pass`；3 处都 cross-link workflow-protocol §5.1 / §5.2，措辞表达"本 skill 仅贡献 X 子层"。 |
| **M4 review_iteration not task-level** | ✅ 已修 | test-review §2 line 45、code-review §2 line 50 各增"task-level review_iteration 说明"段，明确不使用 global review_iteration、不计入 §8 cap 7、需 break loop 升级人介入；planning-review §9 recovery 行加注 "该 cap 仅适用 planning global review loop，test/code task-level review 不使用 global review_iteration"。 |
| **M5 one-shot doc no Change Log** | ✅ 已修 | test-write §4 line 89 + §5 Step 3 line 140；code-write §4.2 line 93 + §4.3 line 123 + §5.1 Step 3 line 159 + §5.2 Step V3 line 184；test-review §5 Step 4 line 148；code-review §5 Step 4 line 149——8 处一致声明 test-review-report / code-review-report / verification-result 是一次性 doc，不需 Pending Changes / Change Log；write skill 创建时不加，review skill 填写时不操作；与 change-log-format.md §1 分类一致。 |
| **M6 code-write submodes** | ✅ 已修 | code-write §1 line 16 改"职责（两组 7 项）" + Code Write Submode 4 项 + Verification Submode 3 项；§3 mode table 5 mode 与 submode 划分对齐；§5 procedure 拆 §5.1 Code Write/Revise + §5.2 Verification；verification owner 明确仍是 development-code-write。 |
| **L1 step number title** | ✅ 已修 | planning-write §5 改"5-Step Standard Procedure"；test-write §5 同；code-write §5 改"Standard Procedure"（已拆 5.1/5.2 子节，无单数步数更合理）；planning-review / test-review / code-review §5 维持"Review Procedure（5 步）"准确。 |
| **L2 partial registration cross-link** | ✅ 已修 | planning-review §9 该行末显式回指 §5 Step 5："按 §5 Step 5 retry 未注册 task，跳过已 planning-done task"。 |
| **L3 status:draft vs review_status:pending** | ✅ 已修 | test-write §4 line 113 + code-write §4.2 line 117 各增独立段，明确 doc.status 由 doc-guardian helper（Gap-2）维护，review_status 由对应 review skill 写入 pass\|fail。 |
| **L4 src/ not in doc-guardian** | ✅ 已修 | code-write §4.1 line 87 增"src/ 不在 doc-guardian 管辖（事实源 directory-layout.md）；source quality gate 由 code_review_report.md + development-code-review 承担；verification execution 由本 skill verification submode 承担"。与 test-write §3 line 73 描述对称。 |
| **L5 claim task definition** | ✅ 已修 | test-write §2 line 48 + code-write §2 line 43 首次出现处加括注："（claim task = 用 progress.py 把 task state 推到 in-progress 子状态，不是文件锁）"。 |
| **L6 cross-link Bug Flow regression** | ✅ 已修 | test-review §3 维度 7 末加 "（详见 development-test-write §7）"；code-review §3 维度 8 末加 "（详见 development-code-write §7）"。 |
| **L7 diff/file scope convention** | ✅ 已修 | test-review §5 Step 2 line 137 + code-review §5 Step 2 line 138 增同一句："file scope 以 detailed_design.md `Files / Modules to Touch` + breakdown.md task ownership map 为基准，可结合 git diff 取证 actual delta；跨 scope 改动列为 finding"。 |
| **L8 Bug Flow Replan vs Direct Route parallel** | ✅ 已修 | planning-write §3 line 83 表格下方加段："Bug Flow Replan 与 Direct Route 是平行二选一：判别依据是 BUG body Affected Task(s) 是否完整、是否需要修 detailed_design.md / task split / DAG。需要改 design 或无法定位 task → Replan；不需改 design 且 affected task 已可被合法路由 → Direct Route"。 |
| **L9 Stage 4 特例 statement uniformity** | ✅ 已修 | 6 个 SKILL（planning-write §2 line 72、planning-review §6 line 148、test-write §2 line 52、test-review §2 line 47、code-write §2 line 62、code-review §2 line 52）全部使用 identical 语句："Stage 4 特例：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。" |

**回归结论**：17/17 项全部 ✅ 已修。0 项 ⚠️ 部分残留，0 项 ❌ 未修。

---

## New Findings (Round 2)

### Low: planning-review §2 中 `sub_state` 字段允许值表达为 narrative 而非 enum

- **Location**: `skills/development-planning-review/SKILL.md:40`
- **Baseline Reference**: `skills/workflow-protocol/SKILL.md:73`（`sub_state` enum 定义）
- **Dimension**: 12 simplicity / 术语一致性
- **Issue**: §2 When to Invoke 表 `sub_state` 行的值写为"`in-review`；或 `review-passed` 且仅做 partial task registration retry"。这是一段 narrative 描述（含中文标点 + 限定条件），不是 progress.md schema 中 `sub_state` 字段的 enum 值。implementer 阅读 When to Invoke 表时可能误以为 `sub_state` 字段允许复合值。
- **Impact**: 实际语义在 §2 line 56（"不被 invoke 的时机"段）与 §4.1 line 83 / §5 Step 5 retry 行已多次澄清，run-time 行为不会出错。trivial。
- **Recommendation**: 把 `sub_state` 行简化为 enum `in-review | review-passed`，并把 `review-passed` 限定条件下沉到表外的 narrative bullet（或 §2 末尾增"Reentry 入口"小段一次性说清楚）。如：
  ```
  | `sub_state` | `in-review`（normal review）；`review-passed`（仅限 retry 入口，见下） |

  **Reentry 入口**：当 `sub_state==review-passed` 但 `development_state.task_states` 不完整……
  ```
  既保持 enum 直观，又保留 retry 语义。

---

## Cross-Finding Consistency Check

横向一致性 7 大点全部满足：

| 检查点 | 状态 | 评论 |
|--------|------|------|
| 1. **Event whitelist** ∈ {`write-complete`, `review-issues`, `review-passed`, `human-confirmed`} | ✓ | planning-write 仅用 `write-complete`；planning-review 仅用 `review-passed` / `review-issues`；test/code 系列**全部** `update --task`，无误用 global event 推 task 状态 |
| 2. **Task transition calls** 用 `update --task Tn --status` | ✓ | 全部 task transition 严格使用 progress.py task 命令 |
| 3. **Gap-3 / Gap-4 staging** | ✓ | 推荐 transition + 前置都明确；3 个 dev write skill + 2 个 dev code 系列 review skill 共 5 个声明位措辞高度一致；Round 1 H1/H2 不重复成新 High |
| 4. **No manual progress.md** | ✓ | 6 个 SKILL 的 Forbidden / Recovery / Gap-3 / Gap-4 段均显式禁止；planning-review §9 / planning-write §10 / test-write §10 / code-write §10 / code-review §10 都重申 |
| 5. **Three-state report** 不变量 | ✓ | pending skeleton owner = write skill；pass/fail owner = review skill；blocking_findings_count == 0 强制；一次性 doc 不加 Pending/Change Log；per-task 路径全程一致 |
| 6. **Global sub_state vs task_state** | ✓ | planning 用 global review loop；test/code/verification owner 看 `development_state.task_states[Tn]`；6 个 SKILL"Stage 4 特例"段语句完全一致（L9） |
| 7. **Bug Flow development re-entry** | ✓ | BUG body `Affected Task(s)` 是事实源；无法定位 task → planning rebreakdown；测试遗漏 → test-write；source bug → code-write；verification fail 不走 bug-triage（code-write §1 line 36 + §8 第 7 条 + description） |

**Gap-3 vs Gap-4 staging 互相不打架**：
- Gap-3 仅影响 `verifying → code-revising` 路径（Stage 4 内部 retry）；Gap-4 仅影响 Bug Flow re-entry 时 `verified` / `code-review-passed` task 回退路径。两者命中不同场景。
- code-write §10 同时声明 Gap-3 + Gap-4 措辞清楚，无歧义。
- 推荐 transition 的命名（`verifying -> code-revising`、`verified -> code-revising`、`verified -> test-revising`、`code-review-passed -> code-revising`）共 4 条，可一次性补在 command-reference Stage 4 task transition 表内，不互相耦合。

**Gap-2 沿用一致性**：6 个 SKILL.md `Gap-2 沿用` 行命名都用 `doc-guardian status-transition helper`（与 batch 3a round 3 闭环一致），未出现别名。

---

## Task State Machine Verification

按 `skills/workflow-protocol/references/command-reference.md` 当前 Stage 4 task state 转换表（line 564-580）逐条核对：

| 当前事实源 transition | batch 3b round 2 SKILL.md 覆盖 | 状态 |
|-----------------------|-------------------------------|------|
| `任意 → planning-done` | planning-review §4.1 / §5 Step 5；planning-write §3 task ID 规则 | ✓ |
| `planning-done → test-writing` | test-write §2 入口 + §5 Step 1（含 claim task 释义） | ✓ |
| `test-writing → test-review` | test-write §5 Step 5 | ✓ |
| `test-review → test-revising` | test-review §4.2 / §5 Step 5 fail | ✓ |
| `test-review → test-done` | test-review §4.1 / §5 Step 5 pass；§6 硬条件 | ✓ |
| `test-revising → test-review` | test-write §3 / §5 Step 5 重提 | ✓ |
| `test-done → code-writing` | code-write §2 + §5.1 Step 1（含 claim task 释义） | ✓ |
| `code-writing → code-review` | code-write §5.1 Step 5 | ✓ |
| `code-review → code-revising` | code-review §4.2 / §5 Step 5 fail | ✓ |
| `code-review → code-review-passed` | code-review §4.1 / §5 Step 5 pass；§6 硬条件 | ✓ |
| `code-revising → code-review` | code-write §3 / §5.1 重提 | ✓ |
| `code-review-passed → verifying` | code-write §5.2 Step V1 | ✓ |
| `verifying → verified` | code-write §5.2 Step V4 pass | ✓ |

**当前缺失（已声明 Gap-3 / Gap-4，本批不修，Task 6 前置）**：

| 缺失 transition | 声明位置 | 状态 |
|-----------------|---------|------|
| `verifying → code-revising`（Gap-3）| code-write §10 末段 + code-review §10 末段 | ✅ 声明充分 |
| `verified → test-revising`（Gap-4）| planning-write §10 末段 + test-write §10 末段 + code-write §10 末段 | ✅ 声明充分 |
| `verified → code-revising`（Gap-4）| 同上 3 处 | ✅ 声明充分 |
| `code-review-passed → code-revising`（Gap-4 衍生）| 同上 3 处 | ✅ 声明充分 |

**没有发现的误用**：
- 6 SKILL.md **没有**任何处暗示用 global event 推 task 状态。
- 6 SKILL.md **没有**任何处声明 caller 可以手工 patch progress.md 绕过缺失 transition。
- 6 SKILL.md **没有**直接调 `update --advance` 推 Stage 4 → Stage 5（Stage 4 done 一律 all task verified）。
- 6 SKILL.md **没有**新增非法 transition call。

---

## Three-State Review Report Verification

按 `skills/doc-guardian/references/frontmatter-schema.md` §3.3 三态不变量 + `change-log-format.md` §1（一次性 doc）逐条核对：

| 不变量 / 步骤 | test_review_report.md | code_review_report.md | 状态 |
|---------------|------------------------|------------------------|------|
| skeleton 由 write skill 创建 | test-write §4 + §5 Step 3 | code-write §4.2 + §5.1 Step 3 | ✓ |
| skeleton `review_status: pending`（**不是 pass**） | test-write §4 line 107 | code-write §4.2 line 111 | ✓ |
| skeleton counts 全 0 / blocking_findings_count: 0 / max_severity: low | test-write §4 yaml | code-write §4.2 yaml | ✓ |
| skeleton doc.status: draft 与 review_status: pending 字段独立性已说明 | test-write §4 line 113（**Round 2 新增 L3 修复**）| code-write §4.2 line 117 | ✓ |
| revise 前重置 stale → pending | test-write §3 / §5 Step 3 / §8 Forbidden 第 4 条 | code-write §3 / §5.1 Step 3 | ✓ |
| 仅 review skill 可写 review_status: pass\|fail | test-review §4.1 / §4.2 + §8 Forbidden | code-review §4.1 / §4.2 + §8 Forbidden | ✓ |
| pass 强制 blocking_findings_count == 0 | test-review §4.1 + §6 + §8 Forbidden 第 3 条 | code-review §4.1 + §6 + §8 Forbidden 第 3 条 | ✓ |
| pending/fail 都不能推进 test-done / code-review-passed | test-review §6 + state machine 强制 | code-review §6 + state machine 强制 | ✓ |
| review report 路径 per-task | test-write §4 / test-review §4 / code-write §4.2 / code-review §4 全程 `docs/release{x.y}/development/tasks/T<n>/...md` | 同 | ✓ |
| **一次性 doc，不需 Pending/Change Log（M5 修复）** | test-write §4 line 89 + §5 Step 3 line 140；test-review §5 Step 4 line 148 | code-write §4.2 line 93 + §5.1 Step 3 line 159；code-review §5 Step 4 line 149 | ✓ |
| Stage 4 task `test-done` / `code-review-passed` 转移强制校验 review_status: pass | progress.py 状态机 + test-review §6 / code-review §6 互锁 | 同 | ✓ |
| Bug Flow 重置 stale 后必经 review pass，不可 bypass | test-write §3 + §7；code-write §3 + §7 | ✓ | ✓ |
| **verification-result 一次性 doc（M5 修复）** | code-write §4.3 line 123 + §5.2 Step V3 line 184 | — | ✓ |

**结论**：三态 report 防 bypass 设计全部满足，M5 一次性 doc 边界明确化已落地，新增的 status vs review_status 字段独立性说明（L3 修复）进一步降低了 implementer 误读风险。

---

## Bug Flow Development Re-entry Assessment

按 Round 1 Bug Flow re-entry 评估清单 + Gap-4 声明完整性核对：

| 子项 | 状态 | 位置 |
|------|------|------|
| `root_cause==development` 入口与 bug-triage / root-cause-rubric 一致 | ✓ | planning-write §2 + §7；test-write §2；code-write §2；与 bug-triage SKILL §3.2 + §3.4 一致 |
| BUG body `Affected Task(s)` 作为事实源 | ✓ | planning-write §7 line 186；test-write §2 line 57；code-write §2 line 58；与 bug-triage SKILL §3.4 + triage-decision-tree §2.2 一致 |
| 无法定位 task 时由 planning-write 重 breakdown | ✓ | planning-write §7 第 4 决策项；与 root-cause-rubric.md §4.8 一致 |
| 测试遗漏 vs source bug vs design 缺口 路由 | ✓ | planning-write §7 决策树；test-write §3 / §7；code-write §3 / §7 |
| development Change Mode 不关闭 Bug Flow；必须 Stage 5 retest | ✓ | planning-write §7 第 5 项；test-write §7；code-write §7 |
| Stage 4 自验证 fail 不走 bug-triage | ✓ | code-write description + §1 line 36 + §3 verification 边界 + §8 Forbidden 第 7 条 |
| 多个 affected task 处理 | ✓ | test-write §9；code-write §9 |
| **Bug Flow Direct Route（已标清 task 无需改 design）** | ✓ | planning-write §3 line 81 表格行已限制 affected task 不在 verified / code-review-passed；line 83 增"平行二选一"段（L8 修复）；§7 line 194 增"已 verified / code-review-passed"段指向 Gap-4 升级路径；与 H1 修复一致 |
| **Bug Flow Replan（需重新 breakdown）**| ✓ | planning-write §3 Replan 行 + §7 第 3 决策项；line 83 平行二选一段已澄清判别依据 |
| **verified task rollback（H1 / Gap-4 修复）** | ✓ | 3 个 dev write skill §10 末段都声明 Gap-4，含 3 条 transition + 推荐 progress.py bug-start auto-rollback；明确禁止手工改 progress.md |
| **verification fail（Gap-3 修复）** | ✓ | code-write §10 + code-review §10 都增推荐 transition + 前置 |

**结论**：H1 修复后 Bug Flow development re-entry 闭环度从 Round 1 的 ❌（不可达）变为 ✓（已声明 Task 6 前置 + 修复推荐路径，骨架轮可接受）。implementer 不会被误导手工回退 task：3 个 dev write skill 都明确写 "补齐前不得手工改 progress.md"。

**潜在小注（不构成 finding）**：code-write §2 line 60 "若 affected task 当前已 verified 或 code-review-passed，必须先由 workflow-protocol/progress.py 按 Gap-4 回退到 code-revising（**或测试遗漏时回退到 test-revising**）" 中后半句"测试遗漏时"语义稍紧——实际测试遗漏 BUG 应不进 code-write，但作为前置条件描述提示存在该回退分支；该措辞与 H1 修复中"BUG body Affected Task(s) + planning-write 决策"的事实源一致，可接受。

---

## Design Gap Status Update

| Gap | 来源 | Round 2 状态 | Task 6 前置 |
|-----|------|---------------|-------------|
| **Gap-1**（`review-passed → revising` 全局 transition）| batch 3a round 3 沿用 | open；6 SKILL.md 无任何处误调不存在的全局 event | 不阻塞骨架；可在 design proposal 升级周期处理 |
| **Gap-2**（doc frontmatter status mutation helper）| batch 3a round 3 沿用 | open；6 SKILL.md `Gap-2 沿用` 行命名一致；test-review §5 Step 4 / code-review §5 Step 4 / test-write §4 line 113 / code-write §4.2 line 117 / planning-write §10 / planning-review §10 边界清晰，未要求 write/review skill 直接修改不属于自己的 frontmatter status | 不阻塞骨架；Task 6 实现 doc-guardian status-transition helper 时一并补 |
| **Gap-3**（`verifying → code-revising`）| Round 1 声明 → Round 2 推荐 transition 落地 | open；code-write §10 + code-review §10 已推荐 transition + 前置 + 禁止 bypass | **必须**先扩 command-reference Stage 4 task 转换表（推荐与 Gap-4 同 patch） |
| **Gap-4**（Bug Flow verified task rollback）| Round 1 识别 → Round 2 在 3 个 dev write skill 声明 | open；planning-write §10 + test-write §10 + code-write §10 已声明 3 条 transition + 推荐 `progress.py bug-start` auto-rollback 行为 + 禁止手工 patch | **必须**先扩 command-reference Stage 4 task 转换表 + progress.py bug-start affected task auto-rollback 行为 |

**Gap-3 + Gap-4 联合 Task 6 前置 patch 范围**：

1. command-reference Stage 4 task transition 表新增 4 条 transition（`verifying → code-revising`、`verified → test-revising`、`verified → code-revising`、`code-review-passed → code-revising`），各自前置见 SKILL.md 声明。
2. `progress.py bug-start --root-cause development` 行为扩展：解析 `<bug-path>` BUG body `## Triage Analysis` 的 `Affected Task(s)`，对每个 affected task 按其当前 task_state + BUG 性质（测试遗漏 / source bug）显式回退到 `test-revising` 或 `code-revising`。
3. progress.py 文档需增 idempotent retry 语义（M1 已声明，但 Task 6 实现时仍需确认 `update --task` 自身幂等）。

**重要**：以上 patch 不在 batch 3b 范围内；batch 3b 骨架轮收敛到此处即可。Task 6 实现 progress.py 之前必须补这两个 transition + bug-start 行为；batch 3c（testing/delivery/retrospective write+review × 3）无须等待，因为这些 stage 的设计本就不依赖 Stage 4 task transition 表。

---

## Recommendation

- **(A): 进 batch 3c（testing + delivery + retrospective write/review × 3）**

**理由**：
- Round 1 全部 2 High / 6 Medium / 9 Low 共 17 项 finding ✅ 全部已修。
- 横向一致性 7 大点全部满足；6 SKILL.md "Stage 4 特例" 段语句完全一致（L9 完美修）；event whitelist / task transition / no manual progress.md / three-state report 不变量 / global sub_state vs task_state / Bug Flow development re-entry 全程无新引入风险。
- New Round 2 finding 仅 1 条 Low（planning-review §2 sub_state 字段值 narrative 表达），不阻塞骨架，可在 batch 3c 起骨架时顺手清理或留到后续 reference 拆分时收敛。
- Gap-3 / Gap-4 已正确声明为 Task 6 前置（不属于 batch 3b 范围；不重复作为 Round 2 High）；声明位置 + 措辞 + 推荐 transition + 禁止 bypass 均充分。
- 6 SKILL.md 总行数 1271 → 1318（+47），patch 体量与 Round 1 推荐顺序中 H+M 部分预估 ~80 行接近，且每条 fix 都带 cross-link 与事实源引用，文档自洽性增强。

**不推荐 (B) 的判据**：当前 finding 含 0 High / 0 Medium，仅 1 Low；远低于 (B) 阈值（"仍有 High 或 Medium ≥ 3"）。

**不推荐 (C) 的判据**：本批 patch 都是局部澄清和 Gap 声明完善，未触及已闭环的架构层决策（authority hierarchy / Stage 4 task 状态机框架 / 三态 report 不变量 / Bug Flow 4 类根因路由）；Gap-3 / Gap-4 是 transition 表补完整型 patch，不需要 design level 重做。

**进 batch 3c 的最小前提**（建议同步处理但不阻塞）：

1. 在 `docs/handoff/` 增 Task 6 progress.py 实现前置 checklist：4 条 transition + bug-start affected task auto-rollback 行为 + idempotent task registration retry。可选。
2. Round 2 Low 1（planning-review §2 sub_state narrative）在 batch 3c 起骨架时顺手清理。可选。
