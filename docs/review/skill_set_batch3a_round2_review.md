# Skill Set Batch 3a Round 2 Review (post-fix regression)

**Review Target**: `skills/prd-write/SKILL.md`, `skills/prd-review/SKILL.md`, `skills/srs-write/SKILL.md`, `skills/srs-review/SKILL.md`, `skills/architecture-write/SKILL.md`, `skills/architecture-review/SKILL.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Round 1 Review**: `docs/review/skill_set_batch3a_review.md`  
**Round 1 Prompt**: `docs/review/codex_review_prompt_batch3a.md`  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: regression: 3 partial residuals; new findings: 0 High / 4 Medium / 1 Low; recommendation: (B) 修后再评（1 轮即可）

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| H1 SRS frontmatter 2 bool | ✅ 已修 | `srs-write` frontmatter 示例已含 `is_multi_module` / `architecture_change`，并说明写入责任与 required-artifacts DSL 因果；`source_system_name` 已补到 SRS source-system-analysis 表；`srs-review` 维度 5 覆盖 bool 存在/一致性。仅有一处小笔误：`srs-write` 写“srs-review 维度 7.1”，实际应是维度 5，不影响实现。 |
| H2 unresolved_bugs 合并 | ⚠️ 部分残留 | 主体修复正确：事实源改为扫描 `docs/bug/BUG-*.md` 的 `consumed_in_release == <progress.md.release>`，S2-1/S2-2/S2-3 已进 `srs-write` 入口，`root_cause: null` 合法化也对齐 post-close intake。但 `srs-review` Step 3 仍只写 S2-2/S2-3，遗漏 S2-1；`srs-write` recovery 仍建议用 `progress.py recover` 处理 BUG frontmatter 脏数据，和 recover 事实源不完全一致。见 M1 / M4。 |
| H3 architecture release-close hook | ⚠️ 部分残留 | `architecture-write` §3.1 主决策树已删除 release-close merge hook，长期事实同轮改主 doc + delta 的主路径正确；references / architecture-review recovery 也已声明无 hook。但 `architecture-write` Bug Flow §7.1 与 Recovery §9 仍保留“不确定时仅改 delta”的旧保守路径，和 H3 新决策相冲突。见 M2。 |
| H4 doc status mutation owner | ⚠️ 部分残留 | 术语已统一为 `doc-guardian status-transition helper`，旧“progress.py hook 写入”未发现残留；6 份文件都有 Gap-2。残留是调用时机仍偏 review-passed/human-confirmed，未覆盖 write-complete / review-issues 等 status 转换链，且 `srs-write` / `architecture-write` 的 approved Forbidden 未指向 helper。见 M3。 |
| M1 source-system-analysis snapshot | ✅ 已修 | `prd-write` / `srs-write` 已区分增量类 doc 与 snapshot 类 doc；source-system-analysis 跳过 Pending Changes 与 `changelog.py promote`，仍跑 `validate.py file`；与 `change-log-format.md` 对齐。 |
| M2 technical-debt optional | ⚠️ 小残留 | 大部分位置已统一为“3 必备 + technical-debt optional/推荐”，`srs-review` Forbidden 也明确 technical-debt 不存在不阻断。残留：`srs-write` 职责第 4 项仍写“S3 场景额外产出 source-system-analysis 4 个 artifacts”，容易被误读为 4 个必备。见 L1。 |
| M3 prd-review iteration reset | ✅ 已修 | `prd-review` §4.1 已明确 `review_iteration → 0` 由 `progress.py update --event review-passed` 事件本身执行；Stage Done 未发现“advance 才归零”残留。 |
| L1 prd-supporting type | ✅ 已修 | `prd-write` §4.3 已列 6 个已注册 optional type，并明确禁止未注册伞 type `prd-supporting`；保留该字符串作为“禁止项”是可接受的，不再作为可用 type 出现。 |
| Optional --finding-count / --max-severity | ✅ 已修 | 3 个 review skill 已删除结构化 CLI 参数要求，改为 history entry result prose 携带 `B/M/L counts + max_severity`；未发现 `--finding-count` / `--max-severity` 残留。 |

## New Findings (Round 2)

### Medium: srs-review Step 3 still excludes S2-1 from consumed bug merge review

- **Location**: `skills/srs-review/SKILL.md:75`, `skills/srs-review/SKILL.md:140`, `skills/srs-review/SKILL.md:149`, `skills/srs-write/SKILL.md:149`, `skills/srs-write/SKILL.md:153`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:270`, `skills/workflow-protocol/references/command-reference.md:298`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:168`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:170`
- **Issue**: `srs-review` 维度 7 描述已经写“覆盖 S2-1/S2-2/S2-3”，Step 2 数据源也已改为 BUG scan；但 Step 3 仍写“维度 7: 仅 S2-2/S2-3 release-start 后首次 review 或 Bug Flow re-entry”。这和 `srs-write` §5 的触发范围不一致。
- **Impact**: S2-1 release-start 会先走 PRD，随后 PRD advance 进入 SRS 时也需要合并已 consumed bugs。如果 review procedure 被实现者按 Step 3 执行，S2-1 下可能跳过 consumed bug 合并完整性检查，重新打开 round 1 H2 的漏检风险。
- **Recommendation**: 将 `srs-review` Step 3 改为：`维度 7: 本 release 首次进入 SRS review 时（覆盖 S2-1/S2-2/S2-3；事实源为 BUG-*.md scan）或 Bug Flow re-entry 时启用`。同时在 §7 差异表把标题从 “S2-3 Change Mode review” 泛化为 “S2-x release-start review”。

### Medium: architecture-write Bug Flow and recovery still recommend the old “only delta when uncertain” path

- **Location**: `skills/architecture-write/SKILL.md:94`, `skills/architecture-write/SKILL.md:197`, `skills/architecture-write/SKILL.md:207`, `skills/architecture-write/SKILL.md:230`, `skills/architecture-write/SKILL.md:237`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:228`, `skills/workflow-protocol/references/command-reference.md:245`, `skills/architecture-write/SKILL.md:75`, `skills/architecture-write/SKILL.md:91`, `skills/architecture-write/SKILL.md:225`
- **Issue**: 主决策树 §3.1 已改为“不确定时倾向长期事实，主 doc + delta 同步改”；Forbidden 也禁止期待 release-close 自动合并。但 Bug Flow §7.1 仍写“不确定时仅改 delta”，Recovery §9 也写“保守：仅改 delta；待评审决定是否回写主 doc”。这与 H3 修复后的保守方向相反。
- **Impact**: Bug Flow root_cause==architecture 时最容易出现“运行时 bug 暴露长期架构事实错误”。若实现者按 §7.1 / §9 处理不确定情况，会继续把长期事实只写入 delta，造成下一 release 主架构起点不正确。
- **Recommendation**: 统一改成 H3 新规则：不确定时按“长期事实候选”处理，同轮改 `architecture_delta.md` + `docs/architecture/architecture.md`，并在 delta body 标注“需 architecture-review 确认是否过度同步”。若最终 review 认为只是本 release 局部，再由 architecture-write revise 移除主 doc 改动。

### Medium: Gap-2 owner is named, but the status-transition call chain is still underspecified for write-complete and review-issues

- **Location**: `skills/prd-write/SKILL.md:141`, `skills/prd-write/SKILL.md:201`, `skills/srs-write/SKILL.md:241`, `skills/srs-write/SKILL.md:309`, `skills/architecture-write/SKILL.md:156`, `skills/architecture-write/SKILL.md:216`, `skills/prd-review/SKILL.md:90`, `skills/srs-review/SKILL.md:93`, `skills/architecture-review/SKILL.md:94`
- **Baseline Reference**: `skills/doc-guardian/SKILL.md:119`, `skills/doc-guardian/SKILL.md:184`, `skills/workflow-protocol/references/command-reference.md:74`, `skills/workflow-protocol/references/command-reference.md:77`, `skills/workflow-protocol/references/command-reference.md:95`, `skills/workflow-protocol/references/command-reference.md:106`
- **Issue**: H4 的“owner 名称”已收敛为 `doc-guardian status-transition helper`，但 6 份 SKILL.md 只明确 review-passed 后同步 `in-review → review-passed`，以及 prd-write 的 human-confirmed 后同步 `approved`。`write-complete` 后 `draft/revising → in-review`、`review-issues` 后 `in-review → revising` 仍没有明确 helper 调用点；`srs-write` / `architecture-write` 的“自行设置 approved”Forbidden 也没有像 prd-write 一样指向 helper。
- **Impact**: Task 6 实现者仍无法判断完整顺序是 `progress.py update --event` 之后 caller 显式调用 helper，还是 progress.py 内部调用 helper。尤其 write-complete 后若 doc frontmatter 仍是 `draft`，review skill Step 1 的 `validate.py file` 可能因 progress/doc status 不兼容失败。
- **Recommendation**: 不要求 batch 3a 实现 helper，但应在 6 份 SKILL.md 的 Design Gaps 中补一个最小序列说明：`每个 update --event 成功后，caller/AGENTS Bootstrap 必须调用 doc-guardian status-transition helper 同步当前 stage artifacts frontmatter status；覆盖 write-complete、review-issues、review-passed、human-confirmed 四类 event；接口签名 TBD`。同时把 `srs-write` / `architecture-write` 的 approved Forbidden 改成和 `prd-write` 一致。

### Medium: prd-exception dirty-data recovery points to progress.py recover, which does not repair BUG frontmatter

- **Location**: `skills/srs-write/SKILL.md:191`, `skills/srs-write/SKILL.md:327`, `skills/srs-write/SKILL.md:334`, `skills/workflow-protocol/references/command-reference.md:166`, `skills/workflow-protocol/references/command-reference.md:224`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:181`, `skills/workflow-protocol/references/command-reference.md:188`, `skills/bug-triage/SKILL.md:197`, `skills/bug-triage/SKILL.md:203`, `skills/bug-triage/SKILL.md:218`, `skills/bug-triage/SKILL.md:324`
- **Issue**: `srs-write` 将 consumed bug 中 `root_cause==prd-exception` 视为脏数据是正确的，但 recovery 写“人工 audit / 走 progress.py recover”。command-reference 的 `recover` 只从 `progress-history.md` 重放重建 `progress.md`，不会修复 `docs/bug/BUG-NNN.md` frontmatter 的 `root_cause` / `consumed_in_release` 脏值。
- **Impact**: 实现者或用户可能误以为 recover 能自动清理 BUG report frontmatter，结果 recover 后再次扫描仍命中同一脏数据，形成不可恢复循环。
- **Recommendation**: 改成“拒绝合并 + 人工 audit；若 progress.md 与 history 不一致才使用 `progress.py recover`；若 BUG frontmatter 本身错误，需人工修正/从 git 恢复 BUG report，并重新跑 `validate.py file <BUG-NNN.md>`”。不要把 recover 描述成修复 BUG frontmatter 的主路径。

### Low: srs-write still has one “4 artifacts” phrase that can blur technical-debt optionality

- **Location**: `skills/srs-write/SKILL.md:21`, `skills/srs-write/SKILL.md:97`, `skills/srs-write/SKILL.md:104`, `skills/srs-review/SKILL.md:18`, `skills/srs-review/SKILL.md:206`
- **Baseline Reference**: `skills/doc-guardian/references/required-artifacts.md:139`, `skills/doc-guardian/references/required-artifacts.md:158`, `skills/doc-guardian/references/frontmatter-schema.md:331`, `skills/doc-guardian/references/frontmatter-schema.md:338`
- **Issue**: Most M2 fixes are correct, but `srs-write` responsibilities still say “S3 场景额外产出 source-system-analysis 4 个 artifacts”。The nearby table marks `technical-debt` as recommended, so this is not a blocking contradiction, but it is the last old-style phrase in a high-level responsibility list.
- **Impact**: A skeleton implementer may treat `technical_debt_analysis.md` as mandatory because responsibilities are often read before the output contract table.
- **Recommendation**: Replace line 21 with “S3 场景额外产出 source-system-analysis：3 必备 + 1 recommended optional（详见 §4.2）”。The `source-system-analysis（4 个 analysis_kind 全部）` phrase in §6 doc classification can remain if clarified as “all source-system-analysis docs, when present, are snapshot docs”.

## Cross-Finding Consistency Check

- **doc-guardian helper 引用**: Term spelling is consistent as `doc-guardian status-transition helper`; old “progress.py hook 写入” phrasing was not found. Remaining risk is sequencing/coverage, not naming (M3).
- **BUG-*.md scan 一致性**: `srs-write` §5, `srs-review` 维度 7, Step 2, and finding template all use BUG frontmatter scan as canonical source. Only `srs-review` Step 3 trigger condition still omits S2-1 (M1).
- **release-close 描述一致性**: Main `architecture-write` §3.1 and references correctly state release-close has no delta merge hook. Bug Flow §7.1 / Recovery §9 still contradict the new conservative direction (M2).
- **Design Gaps 章节一致性**: All 6 files include Gap-1 + Gap-2 with the same core wording. Some local pointers are coarse/stale, but not blocking; the substantive issue is Gap-2 call-chain specificity (M3).
- **doc 分类一致性**: `prd-write` and `srs-write` now align with `change-log-format.md`: incremental docs use Pending/Change Log; source-system-analysis snapshots skip promote and still validate.
- **technical-debt optional 一致性**: `srs-review` is clear; `srs-write` is clear in description / mode / output table / Stage Done, with one high-level residual “4 artifacts” phrase (L1).
- **S2-1 路由一致性**: `srs-write` now correctly models S2-1 as PRD advance → SRS Change Mode + consumed bug merge. `srs-review` procedure still needs the same S2-1 trigger wording (M1).
- **review_iteration reset 一致性**: `prd-review` now explicitly matches command-reference (`review-passed` event resets to 0). `srs-review` / `architecture-review` do not contradict it; adding the same explicit line would be optional cleanup.

## Design Gap Status Update

- **Gap-1 (`review-passed → revising`)**: Still open by design. All 6 files mark it as a design gap and use safe “upgrade human / do not edit progress.md manually” guidance. This is acceptable for batch 3a and should be handled by a workflow-protocol event addition later.
- **Gap-2 (doc status mutation owner)**: Owner naming is now acceptable and consistent (`doc-guardian status-transition helper`), but the invocation sequence remains underspecified. This does not require implementing the helper in batch 3a, but the SKILL.md skeleton should state that the helper must cover all four stage-level status events (`write-complete`, `review-issues`, `review-passed`, `human-confirmed`) and when it runs relative to `progress.py update --event`.

## Recommendation

- **(B)**: 修后再评（再评 1 轮）。There are no new High findings, and most round 1 fixes landed. However H2/H3/H4 still have partial residuals in high-risk prose/procedure paths, so this should not proceed to batch 3b until the 4 Medium items and the 1 Low cleanup are patched.
