# Codex Review Prompt — Task 5 Batch 3a

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请评审 dev-workflow-skills2 项目的 Task 5 批 3a 产出（PRD / SRS / Architecture 三对 vertical skill 的 SKILL.md 骨架，共 6 份），按之前 batch 1 / batch 2 review 的格式输出评审报告。

本批是**骨架轮**——仅产出 6 份 SKILL.md，**不含任何 references**（references 拆分待 batch 3a 评审风格收敛后做）。所以本轮**不要**评审 "应该有哪些 references"——只评审 SKILL.md 自身是否能让 Task 6 实现者按图施工，以及它们与 batch 1 / batch 2 / spec / design 的一致性。

### 评审目标文件（6 份）

主要审查（vertical skill write/review pair × 3）：

- `skills/prd-write/SKILL.md` (240 行)
- `skills/prd-review/SKILL.md` (242 行)
- `skills/srs-write/SKILL.md` (307 行；最长，因 unresolved_bugs 合并 + 多 doc 输出 + 4 场景 entry)
- `skills/srs-review/SKILL.md` (249 行)
- `skills/architecture-write/SKILL.md` (265 行；含 §3.1 主 doc vs delta 决策树 + §7.1 Bug Flow 改 doc 决策表)
- `skills/architecture-review/SKILL.md` (253 行)

总计 1556 行。

### 必读参考材料

判断"是否符合 spec / design / batch 1 / batch 2"时必读：

- `docs/workflow/workflow_specification_claude.md`（v0.6）
- `docs/design/skill_set_design_proposal_v0.5.md`（当前权威设计，含 §3.2 vertical skill 18 个清单）
- `skills/workflow-protocol/SKILL.md`（已闭环 batch 1 round 5，含 §5 Stage Done 矩阵 + §6 Bug Flow + §8 Review Loop + §9 Project Terminal State）
- `skills/workflow-protocol/references/command-reference.md`（**最重要**——§2 `update --event` 4 白名单 + §2.1 sub_state 转移表 + §2.2 `--advance` 4 维度判定流程；本批 SKILL.md 中所有 progress.py 调用必须与此完全一致）
- `skills/doc-guardian/SKILL.md`（已闭环 batch 1 round 5）
- `skills/doc-guardian/references/frontmatter-schema.md`（**最重要**——本批 SKILL.md 引用的 doc type：`prd` / `srs` / `acceptance-plan` / `integration-plan` / `architecture` / `architecture-delta` / `source-system-analysis`）
- `skills/doc-guardian/references/required-artifacts.md`（**重要**——scenario-aware 必备清单 DSL；本批 SKILL.md 引用的 S3 必备 + 多模块 Integration Plan 触发条件来源）
- `skills/doc-guardian/references/change-log-format.md`（4-step procedure 中 Pending Changes / changelog.py promote 的格式来源）
- `skills/doc-guardian/references/directory-layout.md`（doc 路径布局）
- `skills/bug-triage/SKILL.md`（已闭环 batch 2 round 3；Bug Flow re-entry 的上游：root_cause 分类 → bug-start mutation 来源）
- `skills/workflow-evolution/SKILL.md`（已闭环 batch 2 round 3；prd-exception 的接管点，与 prd-write 不在 PRD Change Mode 处理 prd-exception 的边界相关）
- `skills/scenario-dispatcher/SKILL.md`（已闭环 batch 2 round 3；S1/S2-1/S2-2/S2-3/S3 入口路由）
- `docs/handoff/session_handoff_20260506_v2.md`（项目状态快照，含 batch 3a 的设计决策与已捕获的 design gap）

可选参考（理解评审风格）：

- `docs/review/skill_set_batch2_round3_review.md`（batch 2 round 3 闭环 review，作为评审风格基线）
- `docs/review/skill_set_batch1_round5_review.md`（batch 1 round 5 闭环 review）

### 已知 design gap（请评估）

骨架自检时发现以下 design gap，本批 SKILL.md 已**显式标记 "design gap"** 留 codex 评审决策。请在评审报告中明确处置方向：

**Gap-1：`review-passed → revising` 转移缺失**

- 现象：`workflow-protocol/references/command-reference.md` §2.1 转移表无 `review-passed → revising` 事件；`update --event` 白名单仅 4 个（`write-complete` / `review-issues` / `review-passed` / `human-confirmed`）。
- 影响场景：用户在 PRD/SRS/Architecture review-passed 后、人 gate（D 维度）前临时发现 doc 错（典型：用户在准备 advance 到下一 stage 时回看时发现）目前**无 in-spec 修复路径**。
- 当前处置：6 份 SKILL.md（prd-write §7 / §9，prd-review §7 / §9，srs-write §10，srs-review §9，architecture-write §9，architecture-review §9）已显式标 "**design gap**" + 写明"升级人介入 / 由 design proposal 增加新事件"作为权宜。
- 请评审：(a) 增加新 event（如 `reopen-from-review-passed`）到白名单是否合理（影响 audit log 形态、review_iteration 处置规则）？(b) 维持现状强制走 release-close + S2-1 release-start 重启 release 是否可接受（成本极高）？(c) 接受 design gap 把它视为人介入路径是否可？请给出建议方向。

### 已自检并修复的 issue（请二次验证）

设计阶段曾错用 5 个非白名单 event 名。已在交付前修了 21 处，请 codex 二次验证修法正确性 + 是否漏修：

**Fix-1：event 名对齐 4 白名单**

| 错误名 | 修正后 | 修法 |
|-------|-------|------|
| `submit-for-review` | `write-complete` | replace_all 全文（含 prose）|
| `--event review-pass` | `--event review-passed` | sed 精确替换 |
| `--event issues-found` | `--event review-issues` | sed 精确替换（保留 review skill 输出术语 issues-found 业务概念）|
| `--event start-revise` | 改写为 "review-issues 触发 in-review→revising 自动转移（见 §2.1 转移表）" | 6 处单条 Edit |
| `--event reopen-from-review-passed` | 改写为 "design gap" 提示 | 10 处单条 Edit（即 Gap-1）|

**已确保**：所有 `--event <name>` 出现处全部在 4 白名单内。`issues-found` / `review-passed` 作为业务术语 / sub_state 状态保留。

请 codex 验证：(a) 6 SKILL.md 中 `--event` 后跟的字符串是否全部 ∈ {write-complete, review-issues, review-passed, human-confirmed}？(b) 修改后 prose 描述（特别是 prd-write §3 表 / srs-write §3 表 / architecture-write §3 表中的 "Revise 触发" 行；prd-write §8 / srs-write §9 / architecture-write §8 中的 in-review→revising Forbidden 行）是否仍符合 §2.1 转移表语义（review-issues 是因；in-review→revising 是果）？

### 评审维度（10 个）

请覆盖以下维度，每条 finding 必须明确归属于其中一个或多个：

1. **Spec / Design / batch 1+2 一致性**
   - SKILL.md 描述与 workflow spec v0.6 + design proposal v0.5 §3.2 vertical skill 清单是否一致？
   - 引用的 progress.py 命令签名是否与 batch 1 `command-reference.md` 完全一致？特别是 `update --event` 4 白名单 + `--advance` + `--task <Tn> --status <new>`
   - 引用的 frontmatter schema 字段是否与 batch 1 `frontmatter-schema.md` 完全一致？特别是 `prd` / `srs` / `acceptance-plan` / `integration-plan` / `architecture` / `architecture-delta` / `source-system-analysis` 7 个 type 的 per-type 扩展字段
   - 引用的 required-artifacts DSL 触发条件描述是否与 batch 1 `required-artifacts.md` 一致？特别是 S3 PRD 必备 (prd-level + feature-matrix) / S3 SRS 必备 (srs-level + module-level + reuse-replace) / 多模块 Integration Plan 触发 / 本 release 改架构时 architecture_delta 必备
   - 6 个 vertical skill 的 authority 全部标 4 是否一致？（与 batch 1 workflow-protocol=1 / batch 2 scenario-dispatcher=4 / bug-triage=4 / workflow-evolution=2 一致）
   - Stage Done 4 维度（A/B/C/D，无 E）描述是否与 workflow-protocol §5 完全一致？
   - Stage 1/2/3 全部是 gated stage（D 维度人 gate）；本批 SKILL.md 是否一致表述？

2. **跨 skill 协作一致性**（**重点**）
   - prd-write / srs-write / architecture-write **不**直接 mutation progress.md（必经 progress.py）的边界，是否在每份 SKILL.md "不属于本 skill" / Forbidden 中清晰约束？
   - prd-review / srs-review / architecture-review 的"调 progress.py update --event review-passed/review-issues 触发转换"路径，是否与 workflow-protocol §2.1 转移表完全一致？特别是 review_iteration 计数规则（review-issues +1，review-passed 归零由 advance 时执行）
   - 三个 review skill 都明确"不产 review-report doc"（仅 Stage 4 dev-test/dev-code review 才产三态 review-report）；该约束是否一致？
   - prd-write **不**通过 Bug Flow re-entry（仅 S2-1 / 首次写入 / revise 三条入口）；该边界是否与 bug-triage `root_cause` 4 类（含 prd-exception 走 incident path 不切 prd Change Mode）一致？bug-triage SKILL.md / triage-decision-tree.md 中的描述是否一致？
   - srs-write 的 `unresolved_bugs` 合并机制（§5）是否与 workflow-protocol command-reference.md `release-start` mutation（清空 unresolved_bugs + 写 BUG-NNN.md `consumed_in_release`）一致？合并时机（仅 release-start 后首次 invoke）是否与 progress-history.md `release-start` entry 上的 `consumed_unresolved_bugs[]` 字段对齐？
   - architecture-write §3.1 决策树（主 doc vs delta）是否与 workflow-protocol §6 / command-reference.md `release-close` 中关于 delta 合并到主 doc 的 hook 描述一致（如有）？
   - architecture-write §7 Bug Flow re-entry 表（root_cause==architecture 时的 mutation）是否与 workflow-protocol command-reference.md §8 `bug-start` 完全一致？
   - srs-write §8 Bug Flow re-entry 表是否与 workflow-protocol command-reference.md §8 一致？

3. **Full Mode vs Change Mode 区分严格性**
   - 每份 *-write SKILL.md 的 §3 (Full vs Change) 是否明确每个场景对应 Mode + 入口条件？
   - prd-write §3：S1/S3=Full，S2-1=Change，Revise=Change；不接 S2-2/S2-3/S4 —— 是否清晰？
   - srs-write §3：S1/S3=Full，S2-2=Full for new sections（部分），S2-3=Change，Bug Flow re-entry=Change，Revise=Change —— S2-2 "Full for new" 与 "Change for existing" 共存是否产生歧义？
   - architecture-write §3：S1/S3=Full，S2-x + 改架构=Change，Bug Flow re-entry=Change，本 release 不改架构=不被 invoke —— 是否清晰？
   - Mode 影响行为（Full=from-scratch；Change=diff + Pending Changes 关联）的描述是否一致？

4. **Doc Output Contract 严格性**（**重点**）
   - 每份 *-write SKILL.md 的 §4 (Doc Output Contract) 是否清晰列出主输出 + 条件输出？
   - prd-write §4：主 PRD（全场景）+ S3 必备 supporting (prd-level + feature-matrix) + optional supporting —— 边界是否清晰？
   - srs-write §4：SRS + Acceptance Plan（全场景）+ Integration Plan（多模块时）+ S3 必备 3+1 source-system-analysis —— 多模块判定来源（required-artifacts.md DSL）是否引用清晰？
   - architecture-write §4：architecture.md（项目级单文件全场景）+ architecture_delta（本 release 改架构时）—— 触发条件是否清晰？
   - 主 doc 单文件 vs per-release 文件区分（PRD / Architecture 是项目级单文件复用；SRS / Acceptance / Integration / delta 是 per-release）是否在每份 SKILL.md 中清晰描述？
   - 多 doc 时**统一一次 submit**（§5 / §6 Step 5）的约束是否覆盖：srs-write SKILL.md §6 Step 5 / Forbidden 已有；architecture-write §5 Step 5 / Forbidden 已有；prd-write 因仅单 doc + supporting 不需该约束—— 是否一致？

5. **4-Step Standard Procedure 严格性**
   - 三份 *-write SKILL.md 的 4-step 流程（write → Pending → changelog promote → validate self-check → submit）是否一致？
   - Step 间依赖与失败处理（如 validate exit 1 时禁止 submit）描述是否一致？
   - Pending Changes / Change Log 章节格式与 doc-guardian/references/change-log-format.md 是否一致？
   - 多 doc 时（srs-write / architecture-write）每个 doc 单独走一遍 §6 step 1-4 + 统一 step 5 提交的描述是否清晰？

6. **Bug Flow Re-entry 路径完整性**（**重点**）
   - prd-write §7 明确"不会通过 Bug Flow re-entry"（仅 S2-1 / 首次 / revise 入口）—— 是否漏掉某条潜在路径？
   - srs-write §8 / srs-review §7 描述 root_cause==srs 路径 —— mutation（current_stage / sub_state / review_iteration / bug_flow.*）是否与 workflow-protocol command-reference.md §8 完全一致？
   - architecture-write §7 描述 root_cause==architecture 路径 + §7.1 表（bug 性质 → 改主 doc / delta）—— mutation 是否一致？
   - architecture-review §7 与 architecture-write §7 互相引用是否对齐？
   - Bug Flow Change Mode 与一般 S2-x Change Mode 的差异表（srs-write §8 表 / architecture-write 隐含 + architecture-review §7）是否清晰？
   - retest pass 后 `bug-close` 的触发主体（testing-write）描述是否一致（Stage 5 testing skill 是后续 batch 3c 才设计；现在仅引用名是否合适）？

7. **Forbidden Actions 完整性**
   - 每份 SKILL.md 都有 Forbidden Actions 清单。是否有明显的 bypass 路径未被列入？例如：
     - *-write 自行评审本 skill 产出（输出 review-passed/issues-found）
     - *-review 修改 doc body / frontmatter / BUG-NNN.md
     - *-write 自行设置 frontmatter `status: approved`（人 gate 越权）
     - *-write 跳过 doc-guardian validate.py 直接 `update --event write-complete`
     - *-write 跳过 changelog.py promote 直接编辑 Change Log 章节
     - *-review 跳过 §5 Step 1 validate 自检直接进入业务评审
     - *-review 创建独立 review-report doc（PRD/SRS/Architecture review 不产 review-report）
     - prd-write 在 prd-exception 时切 PRD Change Mode（应让 workflow-evolution 接管）
     - srs-write 改 BUG-NNN.md / 自清空 progress.md `unresolved_bugs`（progress.py 统一）
     - architecture-write 自行决定 release-close 时 delta → 主 doc 合并（应让 workflow-protocol release-close hook 处理）
     - 跨 release 改 SRS（已 close release 目录只读）
     - `review_iteration > 7` 仍尝试 `--event review-issues` / 升级人介入提示是否清晰
   - prd-write 没有"严禁产生 architecture_delta"是否合理（architecture-write 才是 owner）？
   - srs-write Forbidden 列表（19 条）是否过密 / 过松？
   - 三个 review skill 严禁的输出术语（approved / pending / pass / fail / accept / reject / LGTM）列表是否完整？

8. **Recovery on Failure 实用性**
   - 各 SKILL.md §9 / §10 (Recovery) 列表是否覆盖 Task 6 实际会遇到的失败模式？
   - validate.py exit 1 / progress.py update 失败 / review_iteration > 7 / doc 物理损坏 / Bug Flow 状态不一致 / 多 doc 部分失败 等场景是否有清晰修复路径？
   - 跨 stage 影响（如 srs-write Bug Flow 修了 SRS 但其他 active stage 已基于旧 SRS 完成工作）的处置是否清晰？
   - design gap（review-passed → revising）的 recovery 提示是否一致（升级人介入 / 不要手工编辑 progress.md）？

9. **可实现性**
   - Python / TypeScript 实现者读这 6 份 SKILL.md 能否直接动手实现 vertical skill 的 write / review 行为？
   - 哪些地方语义模糊导致实现者会做不一致选择？特别关注：
     - srs-write §5 unresolved_bugs 合并步骤的"取消费快照"（从 progress-history.md 读 `consumed_unresolved_bugs[]`）是否过于依赖 progress-history.md 实现细节？
     - architecture-write §3.1 决策树的"长期事实"判定是否过于主观？
     - architecture-write §7.1 表（bug 性质 → 改主 doc / delta）是否可程序化判定（哪怕需要 architecture-review 反馈）？
     - srs-review §3 维度 7（unresolved_bugs 合并完整性）的检查方式（progress-history derive vs 直接 grep BUG-NNN）是否清晰？
     - architecture-review §3 维度 6（主 doc vs delta 决策合理性）的判定标准是否清晰？
   - review skill 的 finding markdown 块（§4.2）是否给实现者足够清晰的 caller agent 解析约定？

10. **简洁度 + 术语一致性**
    - 6 份文件平均 259 行（最长 srs-write 307 / 最短 prd-write 240）是否合理？与 batch 1 (workflow-protocol 329 / doc-guardian 365) / batch 2 (scenario-dispatcher 235 / bug-triage 468 / workflow-evolution 489) 比较是否合理？
    - 哪些章节冗余、可合并？哪些应拆 reference（留给 batch 3a 评审收敛后做）？
    - `review-passed` / `issues-found` 作为业务术语保持一致（评审输出）；`approved` 仅人 gate 后的 doc status —— 是否在 6 份 SKILL.md 中一致？
    - `Full Mode` / `Change Mode` / `Bug Flow re-entry` / `Stage Done` / `4-Step Standard Procedure` / `Doc Output Contract` 等术语在 6 份 SKILL.md 中是否一致？
    - **Stage Naming**：`prd-inception` / `srs-specification` / `architecture-design` 在 SKILL.md 与 workflow-protocol §3 schema / command-reference.md 中是否完全一致？
    - **doc type**：`prd` / `srs` / `acceptance-plan` / `integration-plan` / `architecture` / `architecture-delta` / `source-system-analysis` / `bug-report` / `workflow-incident` 在 6 份 SKILL.md 中拼写是否与 frontmatter-schema.md 一致（特别是 hyphen 与 underscore 的使用）？

### 输出要求

保存到：`docs/review/skill_set_batch3a_review.md`

格式（参考 batch 1 / batch 2 review 历史）：

```markdown
# Skill Set Batch 3a Review (PRD / SRS / Architecture write+review × 3)

**Review Target**: 6 份 SKILL.md 文件路径
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Batch 1 Reference**: skills/workflow-protocol/SKILL.md + skills/doc-guardian/SKILL.md (round 5 闭环)
**Batch 2 Reference**: skills/scenario-dispatcher/SKILL.md + skills/bug-triage/SKILL.md + skills/workflow-evolution/SKILL.md (round 3 闭环)
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "blocking issues: <count>; recommendation: (A) 进 batch 3b / (B) fix / (C) revisit design">

## Findings

### High/Medium/Low: <一句话标题>

- **Location**: `<file>:<line>` (如 multi-line `<line-start>-<line-end>`)
- **Baseline Reference**: <相关 spec/design/batch1+2 file:line>（如有）
- **Issue**: <具体描述>
- **Impact**: <实现 / 协作时会导致什么问题>
- **Recommendation**: <具体修复建议；2 选项时列出取舍>

[每条 finding 一节，按 High → Medium → Low 排]

## Cross-Skill Consistency Check

[专门一节列举 batch 3a 6 个 skill 之间 + 与 batch 1 workflow-protocol/doc-guardian + batch 2 scenario-dispatcher/bug-triage/workflow-evolution 的 cross-reference 是否对齐；按 (caller skill → callee skill) 列表]

## Design Gap Resolution

[针对本 prompt §"已知 design gap" Gap-1（review-passed → revising 转移缺失）给出明确处置方向 (a)/(b)/(c)]

## Event Whitelist Verification

[针对本 prompt §"已自检并修复的 issue" Fix-1，验证 6 SKILL.md 中所有 `--event <name>` 是否全部 ∈ 4 白名单 + 修法是否漏改 / 是否产生新歧义]

## Implementability Assessment

[评估实现者能否直接基于此规范实现 prd-write / prd-review / srs-write / srs-review / architecture-write / architecture-review 各自的 4-step 流程 / Bug Flow re-entry / 主 doc vs delta 决策；列出每个 skill 的"语义模糊点"清单]

## Positive Notes

[列出做得好的设计决策；不强制]

## Suggested Next Revision Order

[按优先级排序的 fix 顺序：High first, Medium second, Low last，给出每条估计的 patch 体量]

## Recommendation

- **(A)**: 进 batch 3b（development-* 6 个 skill 起骨架）—— 当前批 finding 全部 Medium/Low 且数量 ≤ 3
- **(B)**: 修后再评（再评 1 轮）—— 有 High finding 或 Medium ≥ 5
- **(C)**: 重设计（design level 问题）—— 触及架构层决策
```

### 评审风格约束

- **High** = blocker，会导致 Task 6 实现错误、跨 skill 协作崩盘、event 调用错乱、Bug Flow 路径漏洞、Stage Done 4 维度不一致；不修不能进 batch 3b
- **Medium** = 设计问题但有 workaround；可在 batch 3b 设计期间补；或 design gap 需后续 design proposal 决策
- **Low** = 文档清理 / 风格问题；不阻塞
- Finding 数量不限，但每条必须有具体 location 和可执行 recommendation
- 不评审"内容是否专业 / 写得好不好"，只评审"是否能让 Task 6 实现者按图施工不歧义 / 是否能让其他 skill 调用本 skill 不出错 / event 调用是否对齐 4 白名单"
- 已经在 v0.5 design / batch 1 round 5 / batch 2 round 3 闭环过的决策（如 11 个 progress.py 子命令的存在、双 symlink、Foreman 拆分、4 event 白名单本身、INCIDENT type 字段、3 位 zero-padded ID、bug-triage 4 类强制、workflow-evolution advisory only 等）不需要 revisit
- handoff §11 提示：建议 batch 2/3 评审循环放宽到 2-3 轮；本轮发现**质量比数量**重要——优先抓跨 skill 协作错位、event 名残留 / 误用、Bug Flow re-entry 漏路径、Forbidden Actions 缺口、design gap 处置这类"会真正破事"的问题
- 评审完毕后给出明确的 (A) / (B) / (C) recommendation

请直接产出报告，不需要先和我对齐范围。
