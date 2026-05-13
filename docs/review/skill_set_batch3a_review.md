# Skill Set Batch 3a Review (PRD / SRS / Architecture write+review × 3)

**Review Target**: `skills/prd-write/SKILL.md`, `skills/prd-review/SKILL.md`, `skills/srs-write/SKILL.md`, `skills/srs-review/SKILL.md`, `skills/architecture-write/SKILL.md`, `skills/architecture-review/SKILL.md`  
**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)  
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`  
**Batch 1 Reference**: `skills/workflow-protocol/SKILL.md` + `skills/doc-guardian/SKILL.md` (round 5 闭环)  
**Batch 2 Reference**: `skills/scenario-dispatcher/SKILL.md` + `skills/bug-triage/SKILL.md` + `skills/workflow-evolution/SKILL.md` (round 3 闭环)  
**Review Date**: 2026-05-06  
**Reviewer**: Codex  
**Status**: blocking issues: 4 High + 3 Medium + 1 Low; recommendation: (B) 修后再评（其中 H3/H4 需要同步 command-reference/design 决策，但不需要推翻 skill architecture）

## Findings

### High: SRS frontmatter contract omits the two DSL-driving bools that decide Integration Plan and Architecture Delta

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 4. Doc Output Contract 严格性; 9. 可实现性
- **Location**: `skills/srs-write/SKILL.md:104`, `skills/srs-write/SKILL.md:109`, `skills/srs-write/SKILL.md:118`, `skills/srs-write/SKILL.md:120`, `skills/architecture-write/SKILL.md:115`, `skills/architecture-write/SKILL.md:116`
- **Baseline Reference**: `skills/doc-guardian/references/frontmatter-schema.md:80`, `skills/doc-guardian/references/frontmatter-schema.md:83`, `skills/doc-guardian/references/frontmatter-schema.md:405`, `skills/doc-guardian/references/required-artifacts.md:25`, `skills/doc-guardian/references/required-artifacts.md:26`, `skills/doc-guardian/references/required-artifacts.md:136`, `skills/doc-guardian/references/required-artifacts.md:138`, `skills/doc-guardian/references/required-artifacts.md:170`, `skills/doc-guardian/references/required-artifacts.md:172`
- **Issue**: `srs-write` 的 frontmatter 示例只列 `release`，未列 SRS per-type 必含字段 `is_multi_module: bool` 与 `architecture_change: bool`。但 required-artifacts DSL 依赖 `srs.is_multi_module` 决定 `integration-plan` 必备性，依赖 `srs.architecture_change` 决定 `architecture-delta` 必备性。`architecture-write` 又把 architecture_delta 触发条件交给 required-artifacts DSL，因此 Stage 3 是否进入 / 是否校验 delta 的事实源缺了写入责任。
- **Impact**: Task 6 实现者若照 SKILL.md 生成 SRS，会被 `validate.py` 类 3 拒绝；若实现者按 required-artifacts 的默认 false 处理缺字段，则多模块 Integration Plan 或 architecture_delta 会被错误跳过，Stage Done A/B 维度出现漏校验。架构阶段也无法可靠知道“本 release 改架构”是否成立。
- **Recommendation**: 在 `srs-write` §4.3 SRS frontmatter 示例中显式加入 `is_multi_module: true|false` 与 `architecture_change: true|false`，并新增一小段“判定与写入责任”：`srs-write` 必须基于本 release SRS 内容设置两字段；`integration-plan` 的创建与 `architecture-write` 的 delta 触发均以这两个字段为准。同步让 `srs-review` 增加校验维度：字段存在、类型为 YAML bool，且与 SRS 模块数 / 架构影响描述一致。`source-system-analysis` 表格中也应每行完整列出 `source_system_name`，避免实现者从表格复制时漏字段。

### High: unresolved_bugs merge path contradicts release-start and post-close bug-intake semantics

- **Dimensions**: 2. 跨 skill 协作一致性; 6. Bug Flow Re-entry 路径完整性; 8. Recovery on Failure 实用性; 9. 可实现性
- **Location**: `skills/srs-write/SKILL.md:126`, `skills/srs-write/SKILL.md:128`, `skills/srs-write/SKILL.md:131`, `skills/srs-write/SKILL.md:149`, `skills/srs-write/SKILL.md:151`, `skills/srs-write/SKILL.md:154`, `skills/srs-write/SKILL.md:271`, `skills/srs-write/SKILL.md:278`, `skills/srs-review/SKILL.md:75`, `skills/srs-review/SKILL.md:142`, `skills/srs-review/SKILL.md:148`, `skills/srs-review/SKILL.md:221`, `skills/srs-review/SKILL.md:222`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:270`, `skills/workflow-protocol/references/command-reference.md:295`, `skills/workflow-protocol/references/command-reference.md:298`, `skills/workflow-protocol/references/command-reference.md:309`, `skills/bug-triage/SKILL.md:197`, `skills/bug-triage/SKILL.md:203`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:423`, `skills/scenario-dispatcher/references/scenario-decision-tree.md:429`, `skills/workflow-protocol/SKILL.md:249`, `skills/workflow-protocol/SKILL.md:250`
- **Issue**: 当前 merge 机制同时有三处不对齐：第一，`srs-write` 说从 progress-history 最近 release-start entry 读取 `result.consumed_unresolved_bugs[]`，但 command-reference 的 history entry 只记录 consumed count，权威下游处理是扫描 `docs/bug/BUG-*.md` 中 `consumed_in_release == <current release>`。第二，`srs-write` 对每个 consumed BUG 读取 `root_cause` 并按 `srs/architecture/development/prd-exception` 分支，但 post-close bug-intake 明确保持 `root_cause: null`，下次 release-start 只设置 `target_release` / `consumed_in_release`，不做 active triage。第三，触发时机列了 S2-2/S2-3/S3，遗漏 S2-1：S2-1 也通过 `release-start` 消费 unresolved_bugs，只是先进入 PRD，稍后才首次进入 SRS。
- **Impact**: 任何带 post-close pending bug 的新 release 都可能卡死或漏合并：`root_cause` 为空会被 recovery 视为缺字段而拒绝；S2-1 release 的 consumed bugs 可能完全不进 SRS；review skill 又会按不存在的 `consumed_unresolved_bugs[]` 校验，导致实现者无法按图施工。
- **Recommendation**: 重写 §5 / srs-review 维度 7：canonical bug list = 扫描 `docs/bug/BUG-*.md` 且 `consumed_in_release == progress.release`。触发时机 = 本 release 首次进入 `srs-write`，覆盖 S2-1/S2-2/S2-3（S1/S3 初始项目通常为空）。post-close consumed bug 的 `root_cause: null` 是合法状态；SRS 应把每条 intake bug 转为修复需求 / acceptance criteria / Pending Changes，不能要求先分类。只有 active Bug Flow re-entry (`bug_flow.active==true`) 才使用 `root_cause==srs` 语义。

### High: architecture_delta policy relies on a release-close merge hook that is absent from workflow-protocol

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 2. 跨 skill 协作一致性; 4. Doc Output Contract 严格性; 9. 可实现性
- **Location**: `skills/architecture-write/SKILL.md:20`, `skills/architecture-write/SKILL.md:75`, `skills/architecture-write/SKILL.md:87`, `skills/architecture-write/SKILL.md:221`, `skills/architecture-write/SKILL.md:243`, `skills/architecture-review/SKILL.md:228`, `skills/architecture-review/SKILL.md:237`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:228`, `skills/workflow-protocol/references/command-reference.md:245`, `skills/workflow-protocol/SKILL.md:240`, `skills/workflow-protocol/SKILL.md:249`, `skills/doc-guardian/references/required-artifacts.md:164`, `skills/doc-guardian/references/required-artifacts.md:172`
- **Issue**: `architecture-write` §3.1 提供“仅 delta，release close hook 把 delta 关键决策合并回主 doc”的路径，并在 Forbidden/References 中反复依赖该 hook；`architecture-review` recovery 也让实现者检查 release-close hook 是否漏合并。但 command-reference 的 `release-close` mutation 只改 `release_state`、`release_close_reason`、`previous_releases`，并明确其他字段保留不变；workflow-protocol lifecycle 也没有任何 delta→主 doc 合并 hook。
- **Impact**: 实现者会在两个错误方向之间二选一：要么在 Task 6 给 `release-close` 私自加未授权 doc merge side effect，破坏 batch 1 command-reference 的闭环契约；要么照 command-reference 实现，导致 `architecture-write` 所谓“下一 release 起点正确”的长期事实永远不会回写主 doc。
- **Recommendation**: 二选一并写清事实源。推荐短期修法：删除“release-close hook 合并”路径；凡是长期架构事实，`architecture-write` 必须在同一轮同时修改 `architecture.md` + `architecture_delta.md`，review 维度 6 校验该同步。若确实需要 hook，必须先修改 `skills/workflow-protocol/references/command-reference.md` 的 `release-close` mutation、history entry、失败恢复和 doc-guardian validate 责任，再让 batch 3a SKILL.md 引用。

### High: review skills assert a progress.py frontmatter-status hook that command-reference does not define

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 2. 跨 skill 协作一致性; 5. 4-Step Standard Procedure 严格性; 9. 可实现性
- **Location**: `skills/prd-review/SKILL.md:90`, `skills/prd-review/SKILL.md:179`, `skills/srs-review/SKILL.md:93`, `skills/architecture-review/SKILL.md:94`, `skills/prd-write/SKILL.md:199`, `skills/srs-write/SKILL.md:253`, `skills/architecture-write/SKILL.md:212`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:58`, `skills/workflow-protocol/references/command-reference.md:77`, `skills/workflow-protocol/references/command-reference.md:95`, `skills/workflow-protocol/references/command-reference.md:106`, `skills/doc-guardian/SKILL.md:119`, `skills/doc-guardian/SKILL.md:184`, `skills/doc-guardian/references/frontmatter-schema.md:28`, `skills/doc-guardian/references/frontmatter-schema.md:41`
- **Issue**: 三个 review skill 都写“每个 doc frontmatter `status` 由 hook 写入”，write skill 又禁止自己设置 `approved`，但 command-reference 对 `update --event` 的定义只描述 progress.md 的 `sub_state` / `review_iteration` 等事件字段 mutation，没有定义任何 doc frontmatter status hook，也没有说明该 hook 如何满足 Change Log Discipline。
- **Impact**: 这是 Task 6 的真实阻塞点：`write-complete` 后若 doc 仍是 `draft`，review skill Step 1 调 `validate.py file` 会因 class 8（doc status 与 progress.md 兼容）失败；`review-passed` / `human-confirmed` 后若 doc status 未同步，advance 的 C/D 维度也会失败。反过来，若实现者擅自在 progress.py 里改 doc frontmatter，又会超出 command-reference，且必须处理 Pending Changes / Change Log 的原子性。
- **Recommendation**: 在 batch 3a 修订前先明确“doc status mutation owner”。可选方案：A) 正式扩展 command-reference：`update --event write-complete/review-issues/review-passed/human-confirmed` 同步更新当前 stage required artifacts 的 frontmatter status，并通过 doc-guardian/changelog 机制原子写 Change Log；B) 新增 doc-guardian `status-transition` helper，由 write/review/human gate caller 在 progress.py event 前后按固定顺序调用。无论选哪种，6 份 SKILL.md 必须统一替换“hook 写入”的模糊表述。

### Medium: source-system-analysis snapshots are being pulled into the Change Log procedure even though they are non-incremental docs

- **Dimensions**: 4. Doc Output Contract 严格性; 5. 4-Step Standard Procedure 严格性; 10. 简洁度 + 术语一致性
- **Location**: `skills/prd-write/SKILL.md:119`, `skills/prd-write/SKILL.md:139`, `skills/srs-write/SKILL.md:166`, `skills/srs-write/SKILL.md:184`
- **Baseline Reference**: `skills/doc-guardian/references/change-log-format.md:11`, `skills/doc-guardian/references/change-log-format.md:25`, `skills/doc-guardian/references/frontmatter-schema.md:319`, `skills/doc-guardian/references/frontmatter-schema.md:338`
- **Issue**: `srs-write` 标题写“每个 doc 走一遍”，Step 1 包含 S3 supporting artifacts，Step 2/3 又要求每个 doc 加 Pending Changes 并跑 `changelog.py promote`。`prd-write` 的 4-step prose 也容易被读成 S3 supporting artifacts 同样走 Pending/promote。但 `change-log-format.md` 明确 `source-system-analysis` 系列是一次性 snapshot，不需要 Change Log / Pending Changes。
- **Impact**: S3 实现会出现两种不一致：有的实现者给 source-system-analysis 人为加 Change Log，有的实现者跳过；若 `changelog.py promote` 对缺少章节的 snapshot 返回失败，S3 PRD/SRS 写作流程会被无意义阻塞。
- **Recommendation**: 把 4-step 改成“增量类 doc 走 Step 2-3；snapshot doc 只写 body/frontmatter + validate”。在 `prd-write` / `srs-write` 的 Step 1 后加一行：`source-system-analysis 不含 Pending Changes / Change Log，不跑 changelog.py promote`。多 doc 统一 submit 仍保留。

### Medium: S3 Stage 2 technical-debt artifact is optional but several places describe “4 docs” as if it were required

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 4. Doc Output Contract 严格性; 10. 简洁度 + 术语一致性
- **Location**: `skills/srs-write/SKILL.md:21`, `skills/srs-write/SKILL.md:52`, `skills/srs-write/SKILL.md:93`, `skills/srs-write/SKILL.md:100`, `skills/srs-review/SKILL.md:3`, `skills/srs-review/SKILL.md:18`, `skills/srs-review/SKILL.md:74`, `skills/srs-review/SKILL.md:205`
- **Baseline Reference**: `skills/doc-guardian/references/required-artifacts.md:139`, `skills/doc-guardian/references/required-artifacts.md:158`, `skills/workflow-protocol/SKILL.md:173`, `docs/workflow/workflow_specification_claude.md:711`
- **Issue**: 表格本身把 `technical-debt` 标为推荐，但 description / 职责 / review coverage 多次写“S3 时 4 个 source-system-analysis”，容易把推荐项升级成必备项。workflow v0.6 与 required-artifacts 已收敛为 Stage 2 S3 三个必备（srs-level / module-level / reuse-replace）+ technical-debt 推荐。
- **Impact**: `srs-review` 可能在缺 technical_debt_analysis.md 时错误输出 issues-found，或 `srs-write` 可能把 optional artifact 当成 Stage Done A 维度必备，造成 S3 多余阻塞。
- **Recommendation**: 全文统一写“3 required + 1 optional/recommended”。`srs-review` 的 Step 1 / Forbidden 改为“必须覆盖 SRS + Acceptance + 条件 Integration + S3 三个必备 source-system-analysis；technical-debt 若存在则评审，不存在不阻断 review-passed”。

### Medium: prd-review gives the wrong review_iteration reset semantics for review-passed

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 2. 跨 skill 协作一致性; 10. 简洁度 + 术语一致性
- **Location**: `skills/prd-review/SKILL.md:88`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:74`, `skills/workflow-protocol/references/command-reference.md:77`, `skills/workflow-protocol/references/command-reference.md:112`, `skills/workflow-protocol/references/command-reference.md:119`, `skills/workflow-protocol/references/command-reference.md:556`, `skills/workflow-protocol/references/command-reference.md:562`
- **Issue**: `prd-review` 写 `review_iteration` 在 `review-passed` 后“保留，不归零，归零由 advance 时执行”。但 command-reference 的 event 白名单表、§2.1 转换表和状态机合法性表均写 `review-passed` 事件使 `review_iteration` 归零。
- **Impact**: 如果 Task 6 实现者以 `prd-review` prose 为准，PRD review-passed 后 progress.md 中的 iteration 会与 workflow-protocol 事实源不一致。虽然实际 `progress.py` 应以 command-reference 为准，但这个错误会误导 caller 对 cap / history iteration 的解释。
- **Recommendation**: 将该行改为：`progress.md: sub_state in-review → review-passed；review_iteration → 0（由 progress.py update --event review-passed 执行）`。同时检查 SRS/Architecture review 中不要引入“advance 才归零”的说法。

### Low: prd-write references an unregistered `prd-supporting` doc type for optional artifacts

- **Dimensions**: 1. Spec / Design / batch 1+2 一致性; 10. 简洁度 + 术语一致性
- **Location**: `skills/prd-write/SKILL.md:96`
- **Baseline Reference**: `skills/doc-guardian/references/frontmatter-schema.md:340`, `skills/doc-guardian/references/frontmatter-schema.md:344`, `skills/doc-guardian/references/directory-layout.md:100`, `skills/doc-guardian/references/directory-layout.md:109`
- **Issue**: Optional PRD supporting artifacts 的 prose 写 `type: prd-supporting` 或具体已注册 type；但 frontmatter schema 没有 `prd-supporting`，只注册了 `competitor-research` / `competitor-architecture` / `market-research` / `user-scenario-analysis` / `non-goals` / `risk-analysis` 等具体 type。
- **Impact**: 低风险，因为本批不要求 prd-write 创建 optional artifacts；但用户或后续调研活动若照这个 type 写文件，会被 doc-guardian path/type 校验拒绝。
- **Recommendation**: 删除 `prd-supporting`，改成“必须使用 frontmatter-schema 已注册的具体 optional type”。

## Cross-Skill Consistency Check

- `scenario-dispatcher → prd-write`: S1/S3 init 后进 PRD Full Mode、S2-1 release-start 后进 PRD Change Mode 的表述对齐；S2-2/S2-3/S4 不进入 prd-write 的边界清晰。
- `prd-write → prd-review`: write-complete event 名对齐，review-issues 作为 cause、in-review→revising 作为 effect 的 prose 对齐；但 frontmatter status hook owner 未对齐 command-reference（见 H4）。
- `prd-review → workflow-protocol`: 不产 review-report、只输出 `review-passed` / `issues-found`、不签发 `approved` 的边界对齐；`review_iteration` reset 语义有一处错误（M3）。
- `bug-triage/workflow-evolution → prd-write/prd-review`: PRD 不走 Bug Flow re-entry，`prd-exception` 走 incident-start + workflow-evolution 的边界对齐 batch 2。
- `scenario-dispatcher/release-start → srs-write`: S2-2/S2-3 Mode 对齐；但 unresolved_bugs 在 S2-1 release 里被消费后也应由 srs-write 合并，当前遗漏（H2）。
- `workflow-protocol release-start → srs-write/srs-review`: command-reference 规定扫描 `consumed_in_release == <current release>`；当前 srs-write/srs-review 改读不存在的 history list 且错误依赖 `root_cause`（H2）。
- `srs-write → doc-guardian`: SRS / Acceptance / Integration / S3 required artifacts 的路径基本对齐；缺 `is_multi_module` / `architecture_change` 两个 required-artifacts DSL 字段（H1），并把 source-system-analysis 拉进 changelog 流程（M1）。
- `srs-write → architecture-write`: architecture_delta 条件应由 SRS frontmatter `architecture_change` 驱动；当前 srs-write 未明确写入责任，architecture-write 只能主观判断（H1）。
- `bug-triage → srs-write/srs-review`: active Bug Flow root_cause==srs 的 mutation 表与 `bug-start` 对齐，D 人 gate 仍要求的描述对齐。
- `srs-review → architecture-review`: SRS review 不产 review-report、不改 doc body 的边界对齐；但 unresolved_bugs 合并完整性检查的数据源需改成 BUG frontmatter scan（H2）。
- `architecture-write → architecture-review`: 主 doc + delta 一次 submit、review 覆盖主 doc/delta、Bug Flow root_cause==architecture 的路径基本对齐；但 release-close merge hook 是未定义跨 skill 依赖（H3）。
- `architecture-write/review → workflow-protocol`: `bug-start` mutation 表（testing→architecture-design, sub_state write, review_iteration 0）对齐；`release-close` hook 不对齐（H3）。

## Design Gap Resolution

Gap-1（`review-passed → revising` 转移缺失）是真实 design gap；6 份 SKILL.md 对该 gap 的临时处理（升级人介入、不手工改 progress.md）是安全的，但不适合作为 Task 6 长期实现策略。

- **建议选择 (a)**：新增白名单事件，例如 `reopen-from-review-passed` 或更短的 `reopen-for-revision`。约束应非常窄：仅 gated stages（PRD/SRS/Architecture/CR）、当前 `sub_state==review-passed`、本 stage 尚未 `human-confirmed`、project/release active、无 active bug_flow / incident。Mutation：`sub_state: review-passed → revising`，`review_iteration` 建议保持 0 或显式设 0；history 追加 reopen 原因；doc status 同步走 H4 中确定的 status mutation owner。
- **不建议 (b)**：强制 release-close + S2-1 重启 release 成本过高，而且在 PRD/SRS/Architecture review-passed 但尚未 approved / advance 时，当前 release 尚未走到 Stage 7，物理上也不满足 release-close 前置。
- **可短期接受 (c)**：在 batch 3a 骨架里标为 design gap 并升级人介入是安全兜底；但如果 Task 6 要实现完整工具链，应先在 command-reference 中补该 event 或明确“人工修复流程”的唯一合法操作序列。

## Event Whitelist Verification

验证脚本扫描了 6 份目标文件中所有 `--event <name>`：

| File | `--event` occurrences | 非白名单 |
|------|-----------------------|----------|
| `skills/prd-write/SKILL.md` | 8 | 0 |
| `skills/prd-review/SKILL.md` | 14 | 0 |
| `skills/srs-write/SKILL.md` | 5 | 0 |
| `skills/srs-review/SKILL.md` | 8 | 0 |
| `skills/architecture-write/SKILL.md` | 4 | 0 |
| `skills/architecture-review/SKILL.md` | 8 | 0 |

- 所有 `--event` 后跟字符串均属于 `{write-complete, review-issues, review-passed, human-confirmed}`。
- 未发现 `--event submit-for-review`、`--event review-pass`、`--event issues-found`、`--event start-revise`、`--event reopen-from-review-passed` 残留。
- `issues-found` / `review-passed` 作为业务输出术语保留是正确的；review skill 调用 `review-issues` event 触发 `in-review → revising` 的 cause/effect 表述在 6 份文件中整体对齐。
- 语义残留问题：`prd-review` 将 `review-passed` 的 `review_iteration` 归零时点写成 advance，而 command-reference 规定 `review-passed` event 即归零（见 M3）。

## Implementability Assessment

- **`prd-write`**: 主流程、Full/Change Mode、S3 PRD supporting 清单和 PRD 不走 Bug Flow re-entry 都可实现；需修 optional type `prd-supporting`，并明确 source-system-analysis 是否跳过 changelog。
- **`prd-review`**: 两态 review 输出、finding markdown、无 review-report 的 contract 清晰；需修 `review_iteration` reset prose，并等待 H4 解决 frontmatter status owner。
- **`srs-write`**: 当前不能直接实现，原因是 H1/H2。必须先补 SRS `is_multi_module` / `architecture_change` 写入责任，并重写 unresolved_bugs merge policy。
- **`srs-review`**: 基础 review procedure 可实现；unresolved_bugs 合并完整性的数据源、S2-1 覆盖、post-close `root_cause:null` 处理必须先修。S3 technical-debt 要改成 optional-only review。
- **`architecture-write`**: Full/Change Mode 主体可实现；但主 doc vs delta 决策树中“release-close hook 合并”不可实现，必须改成同轮同步主 doc或先扩展 workflow-protocol。
- **`architecture-review`**: 7 维 rubric 足够做骨架实现；主 doc vs delta 决策仍较主观，后续 reference 可拆细。但 H3 修复前，review 的“检查 release-close hook” recovery 不可实现。
- **通用实现风险**: 三个 review skill 都使用 `--finding-count <N> --max-severity <enum>`，command-reference 只写 `[--params ...]`，没有定义参数名、合法 enum 或 history 格式。若这些参数要被 Task 6 CLI 解析，应在 command-reference 中补一个 mini schema；否则 SKILL.md 应写“summary in history prose，不要求 progress.py 结构化参数”。

## Positive Notes

- 6 份文件的 `authority: 4`、stage naming、write/review ownership、禁止直接 mutation progress.md 的边界总体一致。
- Event 白名单修复已实质完成；所有 `--event` 调用均为 4 个合法事件名。
- 三个 review skill 都明确不产 PRD/SRS/Architecture review-report，避免与 Stage 4 三态 review report 混淆。
- PRD 不走 Bug Flow re-entry、`prd-exception` 交给 bug-triage + workflow-evolution 的边界与 batch 2 对齐。
- 多 doc 统一一次 submit 的原则已在 SRS / Architecture write 中写清，能避免 stage 局部提交。

## Suggested Next Revision Order

1. **H2 unresolved_bugs policy**（预计 1-2h）：先修数据源、S2-1 覆盖、`root_cause:null` 合法性；这是 release lifecycle 的最高风险。
2. **H1 SRS bool frontmatter**（预计 0.5-1h）：补 `is_multi_module` / `architecture_change` 和 srs-review 校验；否则 required-artifacts DSL 无法可靠工作。
3. **H4 frontmatter status owner**（预计 1-2h + 设计决策）：在 command-reference 或 doc-guardian helper 中确定 status transition，随后统一 6 份 SKILL.md prose。
4. **H3 architecture delta hook**（预计 1h；若改 command-reference 则更久）：移除未定义 hook或正式设计 hook。
5. **M1/M2 S3 source-system-analysis cleanup**（预计 0.5h）：source-system-analysis 跳过 changelog；technical-debt 全文改 optional。
6. **M3/L1 文案清理**（预计 0.25-0.5h）：修 PRD review iteration reset；删除 `prd-supporting`。
7. **Optional implementability hardening**（预计 0.5h）：为 review-issues 的 `--finding-count` / `--max-severity` 参数补 command-reference 小节，或从 SKILL.md 移除结构化参数要求。

## Recommendation

- **(B)**: 修后再评（再评 1 轮）。当前存在 4 个 High，且 H2 会直接破坏 post-close bug → next release 的主路径，H1 会破坏 required-artifacts DSL，H3/H4 会误导 Task 6 实现 command-reference 以外的 side effect。修复后建议再跑一轮 batch 3a review；不建议在这些 High 未清零时进入 batch 3b。
