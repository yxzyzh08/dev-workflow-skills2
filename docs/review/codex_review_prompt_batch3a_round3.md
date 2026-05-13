# Codex Review Prompt — Task 5 Batch 3a Round 3

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请对 dev-workflow-skills2 项目 Task 5 批 3a 第 3 轮评审。本轮目标是**回归 round 2 的 5 项修复 + 1 项笔误清理**（0 High + 4 Medium + 1 Low + 1 advisory typo），并扫描修复引入的新一致性风险。本轮如全部 ✅ 已修 + 0 New High 即可进 batch 3b（6 个 development-* skill 起骨架）。

### Round 1/2 Review 与采纳记录（必读）

- `docs/review/skill_set_batch3a_review.md`（round 1 review，4H/3M/1L 全部 Adopted）
- `docs/review/codex_review_prompt_batch3a.md`（round 1 prompt）
- `docs/review/skill_set_batch3a_round2_review.md`（round 2 review，0H/4M/1L + 1 advisory typo 全部 Adopted）
- `docs/review/codex_review_prompt_batch3a_round2.md`（round 2 prompt）

**Round 2 采纳总览**（修法已逐条按 baseline 对照后 Adopt）：

| Round 2 Finding | 修法（已采纳） | 主要影响位置 |
|----------------|---------------|-------------|
| M1 srs-review Step 3 仍排除 S2-1 | §5 Step 3 维度 7 触发条件改成"覆盖 S2-1/S2-2/S2-3"；§7 差异表标题从"S2-3 Change Mode review"泛化为"S2-x release-start review" | srs-review:149, 188 |
| M2 arch Bug Flow / Recovery 仍写"不确定时仅改 delta" | §7.1 表 3 行（运行时 / 集成 / 性能）从"视情况"改成"是+是"（双 doc 同改）；末段"保守路径"重写为"按长期事实候选处理（同轮改两份；review 后认定本 release 局部再 revise 移除主 doc 改动）"；§9 Recovery 决策不确定行同步重写 | architecture-write:197-208, 237 |
| M3 Gap-2 owner 已声明但调用链未覆盖 4 event | 6 SKILL.md Design Gaps 段 Gap-2 统一 append 最小调用序列：每次 `progress.py update --event <name>` 成功后 caller 必须调 doc-guardian status-transition helper 同步 frontmatter status，覆盖 4 类 event：(1) `write-complete` → `draft\|revising → in-review`；(2) `review-issues` → `in-review → revising`；(3) `review-passed` → `in-review → review-passed`；(4) `human-confirmed`（仅 gated stage）→ `review-passed → approved`。同时 srs-write / architecture-write 的 approved Forbidden 与 prd-write 一致引用 helper | 6 SKILL.md 全部 Gap-2 段；srs-write:309；architecture-write:216 |
| M4 prd-exception 脏数据 recovery 误指 progress.py recover | srs-write §5 Step B + §10 Recovery prd-exception 行明确"`progress.py recover` 仅从 history 重建 progress.md，**不修 BUG report frontmatter**；脏数据修复路径 = 从 git 历史恢复 BUG-NNN.md 或人工修正 frontmatter → 重跑 validate.py file → 重新触发 srs-write 扫描" | srs-write:191, 334 |
| L1 srs-write 职责第 4 项 "4 个 artifacts" | 改为"3 必备（srs-level/module-level/reuse-replace）+ 1 recommended optional（technical-debt）"措辞 | srs-write:21 |
| 附加 advisory typo（round 2 review H1 评注） | srs-write §4.3 写入时机说明 "srs-review 维度 7.1" → "srs-review 维度 5" | srs-write:133 |

### 评审目标文件（同 round 1/2，6 份）

- `skills/prd-write/SKILL.md`（248 行）
- `skills/prd-review/SKILL.md`（247 行）
- `skills/srs-write/SKILL.md`（374 行；H1+H2 + M3+M4 + L1 重头）
- `skills/srs-review/SKILL.md`（256 行；M1 round 2 修订）
- `skills/architecture-write/SKILL.md`（275 行；M2 round 2 修订）
- `skills/architecture-review/SKILL.md`（259 行）

总计仍为 **1659 行**（round 2 修法是局部精确替换 + 6 文件 Gap-2 段同步扩展，无显著行数变化）。

### 必读参考材料

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`
- `skills/workflow-protocol/SKILL.md` + `skills/workflow-protocol/references/command-reference.md`（§2 update 4 白名单 + §2.1 转移表 + §5 release-close mutation + §6 release-start mutation + §7 bug-intake mutation + §8 bug-start + §3 query / §4 recover）
- `skills/doc-guardian/SKILL.md` + `skills/doc-guardian/references/frontmatter-schema.md`（§3.2 SRS 必含 2 bool）+ `skills/doc-guardian/references/change-log-format.md`（snapshot 类 vs 增量类）+ `skills/doc-guardian/references/required-artifacts.md`
- `skills/scenario-dispatcher/SKILL.md` + `skills/bug-triage/SKILL.md` + `skills/workflow-evolution/SKILL.md`（已闭环 batch 2 round 3）
- `docs/handoff/session_handoff_20260506_v2.md`

### 本轮评审重点（针对 6 项修复的回归点）

#### 回归 M1 round 2：srs-review S2-1 触发条件对齐

**修复定位**：

- `skills/srs-review/SKILL.md:149`：Step 3 维度 7 触发条件 "本 release 首次进入 SRS review 时启用（覆盖 S2-1/S2-2/S2-3；事实源为 BUG-*.md scan）或 Bug Flow re-entry 时（v0.6 round 2 M1：与 srs-write §5 触发范围对齐，含 S2-1）"
- `skills/srs-review/SKILL.md:188`：§7 差异表标题 "**与 S2-x release-start review 的差异**（v0.6 round 2 M1：S2-x 包含 S2-1/S2-2/S2-3）"+ 列名从 "S2-3 Change Mode review" 改为 "S2-x release-start review（首次进 SRS）"

**回归审查**：

- §5 Step 3 维度 7 触发条件是否与 srs-write §5 触发时机完全对齐（覆盖 S2-1/S2-2/S2-3，含 S2-1 PRD advance 后首次进 SRS）？
- §7 差异表标题 / 列名 / 行内容是否一致（避免读者看到"S2-x"标题但内容仍仅讲 S2-3）？
- 维度 7 描述（§3 表行 75）+ Step 3（行 149）+ §7 差异表（行 188）三处对 S2-1 的支持是否完全一致？是否还有任何残留 "仅 S2-2/S2-3" 措辞？

#### 回归 M2 round 2：architecture-write Bug Flow / Recovery 对齐 H3 保守方向

**修复定位**：

- `skills/architecture-write/SKILL.md` §7.1 表（行 197-205）：3 行（运行时 bug / 集成 bug / 性能假设）从"视情况 / 通常是"改成"是 + 是"（同时改主 doc + delta）
- `skills/architecture-write/SKILL.md` §7.1 末段（行 207）：保守路径重写为"按长期事实候选处理；同轮改两份；review 后认定本 release 局部再 revise 移除主 doc 改动"
- `skills/architecture-write/SKILL.md` §9 Recovery（行 237）：决策不确定行同步重写

**回归审查**：

- §7.1 表 3 行的"是 + 是"是否与 §3.1 §3.2 主决策树（H3 round 1 修法）的"长期事实路径同轮改两份"完全一致？
- §7.1 末段保守路径与 §3.1 末段保守原则的措辞是否一致（都倾向长期事实候选 + 同轮改两份）？是否避免了 round 1 修复后再次出现"仅改 delta"语义残留？
- §9 Recovery "决策不确定" 行是否清楚指向 §3.1 / §7.1 H3 决议的同轮改两份路径，并明确否定"仅改 delta"？
- 是否还有任何残留 "保守：仅改 delta" / "不确定时仅改 delta" 措辞？（round 2 grep 已确认 0 残留，请 codex 二次抽查）
- 反向风险：新保守路径"按长期事实候选处理"是否会让实现者**过度同步**主 doc（即所有 Bug Flow 修都改主 doc）？是否需要在 §7.1 加"明显本 release 局部"的反例？

#### 回归 M3 round 2：Gap-2 调用链覆盖 4 event + approved Forbidden 统一

**修复定位**：

- 6 SKILL.md Design Gaps 段 Gap-2 行（共 6 处）追加最小调用序列说明
- `skills/srs-write/SKILL.md:309`：approved Forbidden 与 prd-write 一致引用 helper
- `skills/architecture-write/SKILL.md:216`：同上

**回归审查**：

- 6 文件 Gap-2 调用序列描述是否完全一致（4 类 event + 转换语义 + 接口签名 TBD）？是否使用同一字符串（不要引入同义异名 "doc-guardian status helper" / "doc-guardian frontmatter mutator" 等变体）？
- 4 类 event 是否完整覆盖 command-reference §2 白名单（write-complete / review-issues / review-passed / human-confirmed）？转换语义（draft|revising → in-review / in-review → revising / in-review → review-passed / review-passed → approved）是否与 §2.1 转移表一致？
- prd-write / srs-write / architecture-write 三处 approved Forbidden 措辞是否完全一致（mutation owner = doc-guardian status-transition helper + 触发于 progress.py update --event human-confirmed 之后 + Gap-2 标注）？
- 实现者读 6 SKILL.md 是否清楚知道：caller（write skill / review skill / AGENTS.md Bootstrap）必须在 progress.py update --event 成功后**显式调用** helper？还是可由 progress.py 内部调用？这个 staging 路径在 6 文件中是否一致？
- 调用序列是否清楚标明 "本 batch 仅声明 owner + 触发点；接口签名 TBD by doc-guardian batch upgrade"？这个边界是否避免了实现者误以为 batch 3a 必须 implement helper？
- 4 event 序列是否会产生新约束："write-complete event 后 doc 必须从 draft 转 in-review" → 但 helper 接口尚未实现 → Task 6 实现时这个 chain 怎么 staging？是否需要 Design Gap 章节加 "Gap-2 staging note"？

#### 回归 M4 round 2：prd-exception 脏数据 recovery 改正

**修复定位**：

- `skills/srs-write/SKILL.md:191`：§5 Step B prd-exception 处置末段重写
- `skills/srs-write/SKILL.md:334`：§10 Recovery prd-exception 行重写

**回归审查**：

- §5 Step B + §10 Recovery 两处对 prd-exception 脏数据的处置是否一致？
- 是否清楚标明 "**`progress.py recover` 不能修该脏数据**——recover 仅从 progress-history.md 重建 progress.md，**不动 BUG report frontmatter**"？
- 脏数据修复路径 (a) git 恢复 BUG-NNN.md / (b) 人工修正 frontmatter / (c) 重跑 validate.py file 是否完整？
- "仅当 progress.md 与 history 自身不一致时才考虑用 recover" 措辞是否避免了用户误用 recover 修 BUG frontmatter 的歧义？
- command-reference §4 recover mutation 描述（"从 history 重建 progress.md"）与本 skill 改写后的 prose 是否一致？是否需要在 srs-write 加 cross-link 到 command-reference §4？

#### 回归 L1 round 2：srs-write 职责 4 项 4 artifacts 措辞清理

**修复定位**：

- `skills/srs-write/SKILL.md:21`：职责第 4 项 "S3 场景额外产出 source-system-analysis 4 个 artifacts" → "3 必备（srs-level / module-level / reuse-replace）+ 1 recommended optional（technical-debt）"

**回归审查**：

- 职责行措辞是否与 description / §2 表 / §3 Mode 表 / §4.2 表 / §4.3 / §6 doc 分类 6 处的 "3 必备 + 1 optional/推荐" 完全一致？
- 是否还有任何残留 "4 个 artifacts" / "4 个 source-system-analysis" 措辞？（round 2 grep 已确认 0 残留，请 codex 二次抽查）

#### 回归 advisory typo：维度 7.1 → 维度 5

**修复定位**：

- `skills/srs-write/SKILL.md:133`：§4.3 SRS frontmatter 写入时机 "srs-review 维度 7.1" → "srs-review 维度 5"

**回归审查**：

- 笔误修后是否与 srs-review §3 维度 5（含 SRS 2 bool 一致性校验）描述完全对应？
- 6 SKILL.md 中是否还有其他类似的"维度 X.Y"风格笔误？

### 横向一致性检查（跨 finding）

1. **S2-1 路由完整覆盖**（M1 round 2）：scenario-dispatcher（batch 2 已闭环）→ release-start --scenario S2-1 → prd-inception → PRD advance → srs-specification 链条是否在 6 文件中一致？srs-write description / §1 职责 / §2 表 / §3 Mode 表 / §5 触发；srs-review description / §3 维度 7 / §5 Step 3 / §7 差异表共 8 处对 S2-1 的描述是否完全一致？
2. **architecture 保守路径一致**（M2 round 2）：architecture-write §3.1 决策树 / §3.1 末段保守原则 / §7.1 表 3 行 / §7.1 末段保守路径 / §9 Recovery 决策不确定行 共 5 处保守方向是否完全统一为 H3 决议（同轮改两份；不确定 → 长期事实候选）？是否产生任何方向相反的残留？
3. **Gap-2 描述一致**（M3 round 2）：6 文件 Design Gaps 段 + 3 个 write skill approved Forbidden + 3 个 review skill modify-frontmatter Forbidden + 3 个 review skill 类 A 输出（review-passed 时 doc status 同步）共 12+ 处 helper 引用是否使用完全相同的命名 + 接口签名 TBD 措辞？
4. **prd-exception 处置一致**（M4 round 2）：srs-write §5 Step B + §10 Recovery 2 处对脏数据的处置是否完全一致？是否清楚区分 progress.py recover 与 BUG frontmatter 修复的责任边界？
5. **technical-debt optional 一致**（L1 round 2）：srs-write description / §1 职责（含 4 项）/ §2 表 / §3 Mode 表 / §4.2 表 + srs-review description / §1 / §3 维度 6 / §8 Forbidden 共 9+ 处是否完全统一为"3 必备 + 1 recommended optional"？
6. **doc 分类一致**（M1 round 1 + M3 round 2）：prd-write §5 + srs-write §6 增量类 vs snapshot 类区分仍然清晰吗？snapshot 类的 helper 调用（write-complete event 后 status: draft → in-review）是否与增量类一致？
7. **review_iteration reset 一致**（M3 round 1）：prd-review §4.1 类 A "review_iteration → 0 (event review-passed 执行)" 与 srs-review / architecture-review 类 A 的描述是否一致？

### 重点排查"修复引入的新风险"

- **M2 round 2 过度同步主 doc**：架构-write §7.1 + §3.1 末段都倾向"长期事实候选"路径 → Bug Flow 时实现者可能过度同步主 doc（即所有 architecture root_cause bug 都同改主 doc + delta），架构主 doc 演化过快可能让 release N+1 起点不稳。是否需要 §7.1 / §3.1 加"明显本 release 局部"的反例（如本 release 临时部署变化、本 release 限定的接口废弃 等）？
- **M3 round 2 helper 缺失但 status 转换链已规范**：Task 6 实现者按 SKILL.md 序列：(a) write skill 调 progress.py update --event write-complete；(b) progress.py 改 progress.md sub_state；(c) **caller 调 doc-guardian helper 改 doc status**；(d) review skill 接管。但当前 doc-guardian 没有 helper 实现 → Task 6 阶段如何 staging？是否需要在 Design Gaps Gap-2 加显式 staging note："batch 3a 实现时 helper 暂不可用；可临时由 caller 直接修 doc frontmatter status，但必须打 TODO 注释 + Gap-2 引用，待 doc-guardian batch 升级后切到 helper"？
- **M3 round 2 4 event 完整性**：调用序列覆盖了 4 类 event，但 progress.py update 还可能因状态机校验失败 reject（如 write 期间被错误调成 review-passed）。helper 调用应在 progress.py update **exit 0** 后才发生 → 这个隐含约束是否需要在 Gap-2 描述中显式声明？
- **M4 round 2 git 恢复路径**：脏数据"从 git 恢复 BUG-NNN.md" 假设 BUG report 已 commit；如果尚未 commit（典型：刚 bug-intake 后未及时 commit），git 恢复不可用 → 实现者只能人工修 frontmatter。这个路径是否需要在 §10 Recovery 表细化？
- **M4 round 2 dirty data 检测时点**：srs-write §5 Step B 在合并扫描时检测 prd-exception 脏数据。如果脏数据在 srs-write 启动前已存在（如用户 run progress.py release-start 时进 active 但 BUG-NNN.md 已被人工编辑成 prd-exception），用户感知会在 srs-write 阶段才出现 → review 是否需要 srs-review 维度 7 也对应处理"启动前已脏"场景？
- **6 SKILL.md 总行数 1659 没增长**：round 2 修法都是局部替换，是否引入冗长措辞（同义反复）？是否有可合并的章节（如 6 文件的 Design Gaps 段？）？

### 评审格式

保存到：`docs/review/skill_set_batch3a_round3_review.md`

格式（沿用 batch 2 round 3 风格）：

```markdown
# Skill Set Batch 3a Round 3 Review

**Review Target**: 6 份 SKILL.md 文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch3a_review.md
**Round 2 Review**: docs/review/skill_set_batch3a_round2_review.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "regression: 0 remain; new findings: 0H/M/L; recommendation: (A) 进 batch 3b">

## Round 2 Findings 回归状态

| Round 2 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| M1 srs-review S2-1 触发 | ✅ / ⚠️ / ❌ | <具体描述> |
| M2 arch Bug Flow 保守方向 | ... | ... |
| M3 Gap-2 4 event 调用序列 | ... | ... |
| M4 prd-exception 脏数据 recovery | ... | ... |
| L1 srs-write 4 artifacts 措辞 | ... | ... |
| Advisory typo 维度 7.1 → 维度 5 | ... | ... |

## New Findings (Round 3)

[每条 finding 一节；按 High → Medium → Low 排]

## Cross-Finding Consistency Check

[7 项横向一致性检查结果]

## Design Gap Status Update

[Gap-1（review-passed → revising 缺事件）+ Gap-2（doc status mutation owner 接口 TBD）的处置进展评估；含 round 2 新加的 Gap-2 调用序列 staging 是否清楚]

## Recommendation

- **(A)**: 进 batch 3b（development-* 6 个 skill 起骨架）—— 0 New High，且 Round 2 Findings 全部 ✅ 已修
- **(B)**: 修后再评（再评 1 轮）—— 有 New High 或 Round 2 残留
- **(C)**: 重设计（design level 问题）—— 触及架构层决策
```

### 评审风格约束

- 优先做**回归审查**：5 项修复 + 1 advisory typo 是否完整落地到所有相关位置 + 措辞一致性
- 抓**修复引入的新风险**（特别是 M2 过度同步主 doc / M3 helper 缺失 staging / M4 git 恢复路径假设）
- 已经在 Round 1/2 闭环的决策（如 4 event 白名单、batch 3a 仅做骨架不做 references、三态 review-report 仅 Stage 4、PRD 不走 Bug Flow re-entry、release-close 无 delta merge hook、root_cause==null 合法、source-system-analysis 跳过 changelog 等）不再重新质疑
- handoff §11 提示批 3a 评审循环放宽到 2-3 轮；本轮是第 3 轮，建议 (A) / (B) 二选一，避免再延迟到 round 4
- 本轮如全部 ✅ 已修 + 0 New High，强烈推荐 (A) 进 batch 3b（development-planning / test / code 共 6 个 skill）
- 期望本轮 finding 数量 ≤ 3（Round 1/2 已抓主要骨头）；如出现 ≥ 1 New High 或 ≥ 4 New Medium，则 round 2 修法可能存在系统性遗漏需 round 4
- Design Gaps Gap-1 + Gap-2 是 design-level 议题；本批仅当 owner 声明 + staging 路径清晰即可视为可接受；无需在 batch 3a 内 close（属下游 batch / spec 升级范畴）

请直接产出报告，不需要先和我对齐范围。
