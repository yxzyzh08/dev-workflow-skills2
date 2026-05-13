# Skill Set Batch 3a Round 3 Review

**Review Target**: `skills/prd-write/SKILL.md`, `skills/prd-review/SKILL.md`, `skills/srs-write/SKILL.md`, `skills/srs-review/SKILL.md`, `skills/architecture-write/SKILL.md`, `skills/architecture-review/SKILL.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review**: `docs/review/skill_set_batch3a_review.md`  
**Round 2 Review**: `docs/review/skill_set_batch3a_round2_review.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: regression: 0 remain; new findings: 0 High / 0 Medium / 2 Low; recommendation: (A) 进 batch 3b

## Round 2 Findings 回归状态

| Round 2 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| M1 srs-review S2-1 触发 | ✅ 已修 | `srs-review` 维度 7、§5 Step 3、§7 差异表已统一为本 release 首次进入 SRS review 时覆盖 S2-1/S2-2/S2-3，事实源仍是 BUG-*.md scan。未发现“仅 S2-2/S2-3”残留。 |
| M2 arch Bug Flow 保守方向 | ✅ 已修 | `architecture-write` §3.1 保守原则、§7.1 Bug Flow 表/保守路径、§9 Recovery 已统一为“不确定按长期事实候选处理，同轮改 delta + 主 doc，review 后如属本 release 局部再 revise 移除主 doc 改动”。未发现“仅改 delta”残留。`运行时架构有 bug` 行保留“通常是”主 doc 语气，但结合 §7.1 保守路径与 §3.1 本 release 局部分支，可接受为避免过度同步的微调，不构成 round 2 残留。 |
| M3 Gap-2 4 event 调用序列 | ✅ 已修 | 6 份 SKILL.md 的 Gap-2 行完全一致，统一使用 `doc-guardian status-transition helper`，并明确 `progress.py update --event <name>` 成功后由 caller 调 helper，覆盖 `write-complete` / `review-issues` / `review-passed` / `human-confirmed` 四类 event。`srs-write` / `architecture-write` 的 approved Forbidden 已与 `prd-write` 对齐。 |
| M4 prd-exception 脏数据 recovery | ✅ 已修 | `srs-write` §5 Step B 与 §10 Recovery 均明确：`progress.py recover` 只重建 progress.md，不修 BUG report frontmatter；修复路径为从 git 历史恢复 BUG-NNN.md 或人工修正 frontmatter，再重跑 `validate.py file` 并重新触发扫描。 |
| L1 srs-write 4 artifacts 措辞 | ✅ 已修 | `srs-write` 职责第 4 项已改为 3 必备 + 1 recommended optional；description、§2、§3、§4.2、Stage Done 与 `srs-review` Forbidden 均保持 technical-debt 推荐非必备。§6 doc 分类中的 “4 个 analysis_kind 全部”是 snapshot 分类口径，不再表达“4 个必备 artifacts”。 |
| Advisory typo 维度 7.1 → 维度 5 | ✅ 已修 | `srs-write` §4.3 写入时机已指向 `srs-review` 维度 5；未发现类似“维度 X.Y”笔误残留。 |

## New Findings (Round 3)

### Low: architecture-write 顶层 Bug Flow 交叉引用仍指向旧 §8

- **Location**: `skills/architecture-write/SKILL.md:22`, `skills/architecture-write/SKILL.md:73`, `skills/architecture-write/SKILL.md:197`, `skills/architecture-write/SKILL.md:209`
- **Issue**: `architecture-write` 职责第 5 项和 §3 表格仍写 Bug Flow 改 doc 决策“详见 §8 / 见 §8”，但当前 §8 是 Forbidden Actions，实际 Bug Flow policy 在 §7 / §7.1。
- **Impact**: 不影响主流程，因为 §7.1 内容本身已修正；但读者按交叉引用跳转时会落到 Forbidden Actions，降低可导航性，也可能漏读 round 2 M2 的保守路径。
- **Recommendation**: 将两处改为“详见 §7 / §7.1”或“见 §7.1 Bug 性质 → 改哪份 doc”。

### Low: srs-review / architecture-review 职责行把 `issues-found` 写成 progress.py event

- **Location**: `skills/srs-review/SKILL.md:23`, `skills/srs-review/SKILL.md:157`, `skills/architecture-review/SKILL.md:23`, `skills/architecture-review/SKILL.md:160`, `skills/workflow-protocol/references/command-reference.md:70`
- **Issue**: 两个 review skill 的职责第 6 项写“调 `progress.py update --event review-passed | issues-found`”，但 command-reference 的 event 白名单是 `review-issues`；`issues-found` 是 review 输出类，不是 progress.py event。两份文件的 Step 5 已正确写 `--event review-issues`，所以这是顶层摘要与 procedure 的低级不一致。
- **Impact**: 详细执行步骤不会出错；但 Task 6 起骨架时若只复制职责摘要，可能生成无效的 `--event issues-found` 调用。
- **Recommendation**: 改成“输出 `review-passed` / `issues-found`；调 `progress.py update --event review-passed` / `--event review-issues`”。可同步检查后续 development-* review skill，避免复制该摘要错误。

## Cross-Finding Consistency Check

- **S2-1 路由完整覆盖**: `scenario-dispatcher` → `release-start --scenario S2-1` → PRD Change Mode → PRD advance → SRS Change Mode 的链路在 `prd-write`、`srs-write`、`srs-review` 中一致；SRS consumed bug merge/review 触发均覆盖 S2-1/S2-2/S2-3。
- **architecture 保守路径一致**: §3.1 决策树、§3.1 保守原则、§7.1 表、§7.1 保守路径、§9 Recovery 均统一为“不确定 → 长期事实候选 → 同轮改两份”；未发现方向相反的“只改 delta”残留。
- **architecture 过度同步风险**: §3.1 仍保留“明显本 release 局部 → 仅写 delta”分支，§7.1/§9 要求在 delta 标注需 review 确认是否过度同步，`architecture-review` 维度 6 会检查“仅本 release 局部是否仅写 delta”；因此无需阻塞 batch 3b。可在后续 reference 拆分时补本 release 局部反例。
- **Gap-2 描述一致**: 6 文件 Design Gaps 的 Gap-2 行是同一字符串；3 个 write skill 的 approved Forbidden、3 个 review skill 的 modify-frontmatter Forbidden、3 个 review skill 的 review-passed 输出均使用 `doc-guardian status-transition helper` 命名，无同义异名。
- **prd-exception 处置一致**: `srs-write` §5 Step B 与 §10 Recovery 都清楚区分 BUG frontmatter 脏数据修复和 `progress.py recover` 的 progress.md 重建职责；`srs-review` 维度 7 也把 consumed list 中的 `prd-exception` 判为 blocking 脏数据。
- **technical-debt optional 一致**: `srs-write` 与 `srs-review` 的 description、职责、输出表、Stage Done / Forbidden 均统一为 Stage 2 S3 只有 3 个必备 source-system-analysis，`technical-debt` 推荐且存在则评审、不存在不阻断。
- **doc 分类与 status-transition 一致**: `prd-write` / `srs-write` 仍清楚区分增量类 doc 与 snapshot 类 doc；snapshot 类跳过 Pending/Change Log，但仍跑 `validate.py file`，并通过 Gap-2 helper 在 `write-complete` 后同步 frontmatter status。
- **review_iteration reset 一致**: `prd-review` 明确 `review-passed` event 本身将 `review_iteration → 0`；`srs-review` / `architecture-review` 没有相反描述。后续可选清理是把同一句显式说明复制到 SRS/Architecture review，但不阻塞。

## Design Gap Status Update

- **Gap-1 (`review-passed → revising`)**: 仍按设计保持 open。6 份 SKILL.md 都标为 design gap，并要求用户在人 gate 前发现问题时升级人介入 / 新 proposal 增加事件，禁止手工编辑 progress.md；batch 3a 可接受。
- **Gap-2 (doc status mutation owner)**: round 2 的 owner + 触发点修复已闭环。当前文本明确“每次 `progress.py update --event <name>` 成功后”才由 caller 调 helper，覆盖 4 个 event，并把接口签名/参数/回退留给 doc-guardian batch upgrade。由于本批只声明 owner + staging，不实现 helper，当前状态足以支撑 batch 3b 起骨架；若 batch 3b 实现时 helper 尚不可用，应在 Task 6 的实现策略中显式记录临时路径与 Gap-2 TODO，而不是回改 batch 3a 规则。

## Recommendation

- **(A)**: 进 batch 3b（development-* 6 个 skill 起骨架）。Round 2 的 5 项修复 + 1 项 advisory typo 均已实质闭环，0 New High / 0 New Medium；2 个 Low 都是交叉引用 / 顶层摘要清理，可在 batch 3b 起骨架期间顺手修，不需要再开 batch 3a round 4。
