# Codex Review Prompt — Task 5 Batch 3a Round 2

> 用法：把本文件分隔线之间的内容（"## Prompt Body" 一节的全部内容）整段发给 codex。

---

## Prompt Body

请对 dev-workflow-skills2 项目 Task 5 批 3a 第 2 轮评审。本轮目标是**回归 round 1 的 9 项修复**（4 High + 3 Medium + 1 Low + 1 Implementability，**全部采纳**为 codex 推荐的 Option A 修法，未触及 spec / batch 1+2 闭环决策），并扫描修复引入的新一致性风险。

### Round 1 Review 与采纳记录（必读）

- `docs/review/skill_set_batch3a_review.md`（round 1 review，4H/3M/1L 全部 Adopted）
- `docs/review/codex_review_prompt_batch3a.md`（round 1 prompt；含 Gap-1 等已识别 design gap）

**采纳总览**（修法已逐条按 baseline 对照后 Adopt）：

| Round 1 Finding | 修法（已采纳） | 主要影响文件 |
|----------------|---------------|-------------|
| H1 SRS frontmatter 缺 2 bool | srs-write §4.3 加 `is_multi_module: bool` + `architecture_change: bool` 写入责任段；§4.2 source-system-analysis 表 4 行补 `source_system_name`；srs-write §9 加 3 条 Forbidden；srs-review §3 维度 5 加 bool 一致性校验 | srs-write, srs-review |
| H2 unresolved_bugs 合并 3 处不对齐 | srs-write §5 完全重写：数据源改 BUG-*.md scan (`consumed_in_release == 当前 release`)；触发覆盖 S2-1（PRD advance 后首次进 SRS）；接受 `root_cause: null` 合法性（不强制分类）；srs-review §3 维度 7 + §5 Step 2 + Finding 模板同步重写；srs-write §2/§3 表加 S2-1 行；§9 Forbidden / §10 Recovery 同步修订 | srs-write, srs-review |
| H3 architecture release-close merge hook 不存在 | architecture-write §3.1 决策树从 3 分支收敛为 2 分支（删除"延迟合并"路径）；§1 职责 + §9 Forbidden + §10 References 改成"长期事实必须同轮同时改主 doc + delta；spec 没有该 hook"；architecture-review §9 Recovery 同步修 | architecture-write, architecture-review |
| H4 doc status mutation owner 未定义 | 7 处 "由 hook 写入" 替换为 "由 **doc-guardian status-transition helper** 同步（owner 已声明，接口签名 TBD by doc-guardian batch update）"；6 SKILL.md 末尾统一加 **Design Gaps** 章节标 Gap-1（`review-passed → revising` 缺事件）+ **Gap-2**（doc status mutation owner 接口待 doc-guardian 升级）| 6 SKILL.md 全部 |
| M1 source-system-analysis 不应进 Change Log | prd-write §5 + srs-write §6 4-step 改成 "增量类 vs snapshot 类" 区分：snapshot doc 跳过 Pending Changes / promote，仅走 validate.py | prd-write, srs-write |
| M2 technical-debt optional 表述不一致 | srs-write description / §2 / §3 + srs-review description / §1 / Forbidden 全文统一 "3 必备 + 1 optional/推荐" 措辞 | srs-write, srs-review |
| M3 prd-review iteration reset 时点错误 | prd-review §4.1 类 A 改成 "review_iteration → 0（由 `progress.py update --event review-passed` 事件本身执行；事实源 command-reference §2 + §2.1）" | prd-review |
| L1 prd-supporting type 未注册 | prd-write §4.3 删除伞 type `prd-supporting`；改为列出 `competitor-research` / `competitor-architecture` / `market-research` / `user-scenario-analysis` / `non-goals` / `risk-analysis` 6 个具体已注册 optional type | prd-write |
| Implementability `--finding-count` / `--max-severity` 无 spec | 3 review SKILL.md §4.1 类 B + §5 Step 5 改为 prose："finding count summary 通过 history entry result 字段携带；不强制结构化 CLI 参数；具体接口待 progress.py 升级" | prd-review, srs-review, architecture-review |

### 评审目标文件（同 round 1，6 份）

- `skills/prd-write/SKILL.md`（240 → 248 行）
- `skills/prd-review/SKILL.md`（242 → 247 行）
- `skills/srs-write/SKILL.md`（307 → 374 行；H1+H2 重写最大）
- `skills/srs-review/SKILL.md`（249 → 256 行）
- `skills/architecture-write/SKILL.md`（265 → 275 行）
- `skills/architecture-review/SKILL.md`（253 → 259 行）

总计 1556 → **1659 行**（+103 行）。

### 必读参考材料

- `docs/workflow/workflow_specification_claude.md` (v0.6)
- `docs/design/skill_set_design_proposal_v0.5.md`
- `skills/workflow-protocol/SKILL.md` + `skills/workflow-protocol/references/command-reference.md`（§2 update 4 白名单 + §2.1 转移表 + §5 release-close mutation + §6 release-start mutation + §7 bug-intake mutation + §8 bug-start）
- `skills/doc-guardian/SKILL.md` + `skills/doc-guardian/references/frontmatter-schema.md`（§3.2 SRS 必含 2 bool + §3.5 source-system-analysis 4 子类 + 各 optional type 注册）+ `skills/doc-guardian/references/change-log-format.md`（snapshot 类 vs 增量类区分）+ `skills/doc-guardian/references/required-artifacts.md`（DSL 关键依赖 SRS 2 bool）
- `skills/scenario-dispatcher/SKILL.md` + `skills/bug-triage/SKILL.md` + `skills/workflow-evolution/SKILL.md`（已闭环 batch 2 round 3）
- `docs/handoff/session_handoff_20260506_v2.md`

### 本轮评审重点（针对 9 项修复的回归点）

#### 回归 1：H1 SRS frontmatter 2 bool 写入责任

**修复定位**：

- `skills/srs-write/SKILL.md`：description / §1 职责（5 → 7 项）/ §4.3 SRS frontmatter 示例 + 判定与写入责任段 / §4.2 source-system-analysis 表 4 行 / §9 Forbidden 新增 3 条
- `skills/srs-review/SKILL.md`：description / §3 维度 5（含 bool 一致性校验）

**回归审查**：

- srs-write §4.3 frontmatter 示例是否同时包含 `is_multi_module` + `architecture_change` 两个字段且类型 `true | false`？
- "判定与写入责任" 段是否清晰解释两 bool 的判定标准、写入时机、与下游 required-artifacts DSL 的因果（`is_multi_module` 决定 Integration Plan 必备性 / `architecture_change` 决定 architecture-delta 必备性）？
- §4.2 source-system-analysis 表 4 行（prd-level / srs-level / module-level / reuse-replace / technical-debt）是否每行 frontmatter 都列出 `source_system_name`？
- srs-review §3 维度 5 校验描述是否覆盖：(a) 字段存在 (b) 类型为 YAML bool (c) 与 SRS body 模块切分 / 架构影响一致；severity 是否合理标 blocking（缺 bool / 不一致）+ medium（source_system_name 缺失）？
- Forbidden 新增 3 条是否覆盖：(a) SRS frontmatter 缺 bool；(b) bool 与 body 不一致；(c) 自行修 BUG-NNN.md root_cause？
- frontmatter-schema.md §3.2 写"由 srs-write skill 在 SRS specification 阶段写入两个 bool 字段" → srs-write SKILL.md 是否承接该责任？

#### 回归 2：H2 consumed_unresolved_bugs 合并完全重写

**修复定位**：

- `skills/srs-write/SKILL.md`：description / §1 职责 / §2 When to Invoke 表（加 S2-1 行）/ §3 Mode 表（加 S2-1 行）/ §5 完全重写（事实源 = BUG-*.md scan；触发覆盖 S2-1/S2-2/S2-3；root_cause: null 合法）/ §8 Bug Flow re-entry 差异表 / §9 Forbidden 修 1 条 + 新增 2 条 / §10 Recovery 改 3 行
- `skills/srs-review/SKILL.md`：description / §3 维度 7 重写 / §5 Step 2 数据源 / §4.2 Finding 模板

**回归审查**：

- srs-write §5 事实源是否明确"扫描 docs/bug/BUG-*.md frontmatter 筛 `consumed_in_release == <progress.md.release>`"？是否在脚注/旁注解释**不读** progress-history.md release-start entry result list（command-reference §6 仅记 count）？
- 触发时机是否覆盖：S2-1（PRD advance 后首次进 SRS）/ S2-2 / S2-3 / S1-S3 首次（列表为空也跑流程保持一致）？是否明确**不**在 Bug Flow re-entry / revise 循环触发？
- §5 Step B 5 种 root_cause 处置（null / srs / architecture / development / prd-exception）是否清晰？特别是：
  - root_cause==null（post-close intake 默认）合法性是否清楚指向 command-reference §7 bug-intake？
  - root_cause==prd-exception 视为脏数据 → "输出 issue 让用户人工 audit / 走 progress.py recover" 是否完整覆盖（不静默跳过）？
- §5 Step C 是否清楚：root_cause ∈ {null, srs} 的 bug 进 SRS body + Pending Changes；root_cause ∈ {architecture, development} 的可加跨 stage 责任注记（非强制；不进 Pending Changes 避免虚假 Change Log）？
- §5 Step D promote / validate 顺序是否与 §6 4-step 一致？
- srs-review §3 维度 7 数据源声明是否与 srs-write §5 完全一致（**事实源 = 扫描 BUG-*.md**）？severity 是否合理标 blocking（漏 bug / prd-exception 出现 in list）+ medium（多余合并）？
- §4.2 Finding 模板示例是否使用新事实源（`BUG-*.md scan: BUG-005 (consumed_in_release=0.3, root_cause=null) ...`）而非旧 history list？
- srs-write §10 Recovery 是否覆盖：(a) BUG 文件缺失 reject；(b) root_cause==null 合法不报错；(c) prd-exception 脏数据 reject + 不静默？
- §2 / §3 表新增的 S2-1 路由（PRD advance 后 → 进 SRS Change Mode + 合并 consumed bug）是否清晰区分于 S2-2（直接进 SRS Full for new sections）/ S2-3（直接进 SRS Change Mode）？

#### 回归 3：H3 architecture release-close hook 删除

**修复定位**：

- `skills/architecture-write/SKILL.md`：§1 职责（第 3 项重写）/ §3.1 决策树（3 → 2 分支）/ §9 Forbidden（改 1 条）/ §10 References（标注 hook 不存在）
- `skills/architecture-review/SKILL.md`：§9 Recovery（cross release 一致性行重写）/ §10 References

**回归审查**：

- §3.1 决策树是否完全删除"延迟合并到 release-close hook"路径？保留的 2 分支（"本 release 局部" 仅写 delta；"长期事实" 必须同轮改主 doc + delta）是否清晰？
- "保守原则" 是否清楚说明：决策不清时倾向归类"长期事实"路径而非"局部"路径（这个方向比 round 1 之前更保守，避免长期事实漏写主 doc）？
- §9 Forbidden 是否清楚禁止"把长期事实改动仅写在 delta 而期待 release-close 阶段被自动合并"？
- §10 References + §1 职责 + 决策树是否所有提及 release-close 的位置都明确"不含 delta 合并 hook" / "command-reference §5 release-close mutation 仅改 release_state / release_close_reason / previous_releases"？
- architecture-review §9 Recovery "跨 release 一致性问题" 行是否明确归因为"上一 release 漏把长期事实同步到 architecture.md"（不是缺 release-close hook）？
- 维度 6（主 doc vs delta 决策合理性）是否仍能正确捕捉"长期事实仅写 delta"反模式？

#### 回归 4：H4 doc status mutation owner = doc-guardian helper TBD

**修复定位**：

- 7 处行内描述：prd-write §8 Forbidden / prd-review §4.1 类 A + §8 Forbidden / srs-review §4.1 类 A + §8 Forbidden / architecture-review §4.1 类 A + §8 Forbidden
- 6 SKILL.md 末尾统一加 **Design Gaps** 章节（Gap-1 + Gap-2）

**回归审查**：

- 7 处 owner 描述是否一致：`doc frontmatter status mutation owner = doc-guardian status-transition helper（接口签名 TBD by doc-guardian batch update）`？术语是否统一？
- "Gap-2" 标记是否在所有 7 处都引用且指向 §10 Design Gaps 集中段？
- 6 SKILL.md 末尾 Design Gaps 段（Gap-1 + Gap-2）是否一致措辞？是否清晰传达"本 batch 仅声明 owner，不实现接口"？
- write skill 的 Forbidden（"自行设置 frontmatter `status: approved`"）+ review skill 的 Forbidden（"修改任何 doc frontmatter"）是否一致地指向 doc-guardian helper 作为 mutation owner？
- 是否还有任何残留 "progress.py update 内的 hook 写入" / "由 hook 写入" 措辞？（本次 grep 已确认 0 处，请 codex 二次抽查）
- Gap-2 处置是否合理（owner 声明 + 接口 TBD），还是应该升级为强制要求 doc-guardian 在 batch 3a 内同步上线 helper 接口？
- 实现者读 6 SKILL.md 能否清楚知道：当 progress.py update --event 触发时，doc-guardian helper 是同步链中下一个被调用方？或者 helper 由 caller 显式调用？这个流程在 6 SKILL.md 中是否需要更精细化？

#### 回归 5：M1 source-system-analysis snapshot 跳过 Change Log

**修复定位**：

- `skills/prd-write/SKILL.md` §5 4-step（Step 2-3 区分增量类 vs snapshot 类）
- `skills/srs-write/SKILL.md` §6 4-step + 顶部 doc 分类表

**回归审查**：

- prd-write §5 / srs-write §6 是否清晰列出"增量类 doc"清单（PRD / SRS / Acceptance Plan / Integration Plan）+ "snapshot 类 doc"清单（source-system-analysis 4 子类）？
- snapshot 类是否明确"跳过 Pending Changes 段 + 跳过 changelog.py promote"，但 validate.py 仍要跑？
- 事实源引用 `doc-guardian/references/change-log-format.md` 是否准确？
- 多 doc 时 snapshot + 增量混合走流程的细节是否清楚（如 S3 时 SRS 走 Pending/promote，3+1 source-system-analysis 跳过 Pending/promote，但都走 Step 4 validate + Step 5 统一 submit）？
- "Step 5 统一一次 submit" 约束是否仍正确（含 snapshot 与增量 doc 一并）？
- 是否需要 srs-review / prd-review 也对应加"snapshot 类不评审 Change Log 章节"提醒？（当前 review skill 仅评审 SRS / PRD 主 doc Change Log；source-system-analysis 因为没 Change Log 自然不评审，但是否应该显式声明？）

#### 回归 6：M2 technical-debt optional 表述统一

**修复定位**：

- srs-write description / §2 表 / §3 表 / Mode 表
- srs-review description / §1 职责 / §8 Forbidden 行

**回归审查**：

- 全文是否统一为 "3 必备（srs-level / module-level / reuse-replace）+ 1 optional/推荐（technical-debt）" 措辞？
- 旧错误措辞 "S3 时 4 个 source-system-analysis" 是否完全清除（不应再有）？
- srs-review §8 Forbidden 是否清楚 "technical-debt 若存在则评审，不存在不阻断 review-passed"？
- §3 维度 6 描述（"technical-debt（推荐）：识别可弃 / 可重写部分"）是否仍隐含 optional 性质？

#### 回归 7：M3 prd-review iteration reset 时点

**修复定位**：

- `skills/prd-review/SKILL.md` §4.1 类 A 第 3 行

**回归审查**：

- 当前描述 "review_iteration → 0（v0.6 round 1 M3 修正：归零由 `progress.py update --event review-passed` 事件本身执行；事实源 command-reference §2 + §2.1）" 是否完全对齐 command-reference §2 白名单表 + §2.1 转移表？
- srs-review / architecture-review 是否也应加类似精确说明（即使原本没 round 1 错误，加上更对齐）？或者保持现状（不动）？
- prd-review § Stage Done Conditions 是否仍用旧"归零由 advance 时执行"措辞？（应同步更新）

#### 回归 8：L1 prd-supporting type 删除

**修复定位**：

- `skills/prd-write/SKILL.md` §4.3 Optional supporting artifacts 段

**回归审查**：

- 是否完全删除伞 type `prd-supporting`？
- 是否列出 6 个已注册具体 optional type：`competitor-research` / `competitor-architecture` / `market-research` / `user-scenario-analysis` / `non-goals` / `risk-analysis`？
- 是否与 doc-guardian frontmatter-schema 已注册 type 完全一致（命名 / hyphen 与 underscore 使用）？
- "禁止使用未注册的伞 type 名" 措辞是否清晰防止实现者再次回退？

#### 回归 9：Optional `--finding-count` / `--max-severity` 简化

**修复定位**：

- 3 review SKILL.md §4.1 类 B + §5 Step 5（共 6 处）

**回归审查**：

- 6 处是否一致改成 "history entry result 字段携带 finding count summary；不强制结构化 CLI 参数；具体接口待 progress.py 升级"？
- 是否避免了实现者错误地把 `--finding-count` / `--max-severity` 当成 progress.py 必需参数？
- review skill 仍能在 history entry result prose 中携带 `B/M/L counts + max_severity` 摘要的能力是否清楚？
- §4.2 Finding 模板是否仍能为 caller / 用户提供足够 finding 详情（B/M/L 分布在 review skill 对话输出层显示）？

### 横向一致性检查（跨 finding）

1. **doc-guardian helper 引用**（H4）：6 SKILL.md 中 7 处行内引用 + 6 处 Design Gaps 章节引用 helper 的措辞是否一致？是否避免引入"doc-guardian status helper" / "doc-guardian frontmatter mutator" 等同义异名？
2. **BUG-*.md scan 一致性**（H2）：srs-write §5 + srs-review §3 维度 7 + §5 Step 2 + §4.2 Finding 模板 4 处描述事实源是否完全一致？是否还有任何残留 "progress-history.md release-start consumed_unresolved_bugs[]" 错误数据源？
3. **release-close 描述一致性**（H3）：architecture-write §1 / §3.1 / §9 / §10 + architecture-review §9 / §10 共 6 处对 release-close mutation 范围（仅 release_state / release_close_reason / previous_releases）描述是否一致？
4. **Design Gaps 章节一致性**（H4）：6 SKILL.md 末尾 Design Gaps 段措辞是否完全一致（同 Gap-1 + Gap-2 描述）？
5. **doc 分类一致性**（M1）：prd-write §5 + srs-write §6 对"增量类 vs snapshot 类"的措辞与分类是否一致？是否需要也在 doc-guardian/references/change-log-format.md 同步加 cross-link？（注：本 batch 不改 doc-guardian 文件，但可建议）
6. **technical-debt optional 一致性**（M2）：srs-write description + §2 + §3 + srs-review description + §1 + §8 Forbidden 6 处措辞是否一致？
7. **S2-1 路由一致性**（H2）：scenario-dispatcher（batch 2 已闭环）路由 S2-1 → prd-inception 后 PRD advance → srs-specification 的 cross-skill 路径，与 srs-write 新加 S2-1 行的 entry 描述是否对齐？
8. **review_iteration reset 一致性**（M3）：prd-review / srs-review / architecture-review 三个 review skill 对 review-passed event 时归零的措辞是否一致（哪怕只有 prd-review 显式提到 M3 修正）？

### 重点排查"修复引入的新风险"

- **H1 引入的 review burden**：srs-review 维度 5 现在需要校验 SRS body 模块切分与 `is_multi_module` bool 一致性 + body 架构影响描述与 `architecture_change` bool 一致性 → review skill 实施时是否过于主观？是否需要在 review-rubric.md（待 batch 3a 后续 references）中给出量化判定标准？
- **H2 root_cause:null 合法化**：srs-write §5 接受 `root_cause: null` 合法性是否会导致 testing-write（batch 3c）在 active triage 时找不到这条 BUG report 然后再次 triage？是否需要警告 testing-write 不要 reclassify 已 consumed bug？
- **H2 prd-exception 脏数据**：srs-write §5 / Recovery 要求"输出 issue 让用户人工 audit / 走 progress.py recover"——`progress.py recover` 是否真能修这种类型的脏数据？还是需要其他机制（如 doc-guardian validate.py 类 7 ID Uniqueness 增强）？
- **H3 决策树收敛风险**：architecture-write 删除"延迟合并"分支后，"本 release 局部" 与 "长期事实" 二选一是否过于二元？是否存在中间情况（部分长期事实 + 部分仅 release 局部）让实现者无所适从？
- **H4 doc-guardian helper 调用时机**：实现者要不要在 batch 3a 内为 progress.py update --event 后注入 doc-guardian helper 调用？还是等 doc-guardian batch 升级时才接通？这个 staging 路径在 6 SKILL.md 中是否清楚？
- **M1 snapshot 类校验**：source-system-analysis 跳过 Pending Changes 后，validate.py 类 6（Change Log Discipline）是否会对 snapshot 类豁免？这个豁免是否需要在 doc-guardian/references/change-log-format.md 显式声明？（注：本 batch 不改 doc-guardian；但 SKILL.md 是否应建议）
- **9 项修复合计**：6 SKILL.md 行数 +103，是否在某处引入冗余表述（同义反复）？是否有可合并的章节？

### 评审格式

保存到：`docs/review/skill_set_batch3a_round2_review.md`

格式（沿用 batch 2 round 2 风格）：

```markdown
# Skill Set Batch 3a Round 2 Review (post-fix regression)

**Review Target**: 6 份 SKILL.md 文件路径（prd / srs / architecture × write+review）
**Workflow Baseline**: docs/workflow/workflow_specification_claude.md (v0.6)
**Design Reference**: docs/design/skill_set_design_proposal_v0.5.md
**Round 1 Review**: docs/review/skill_set_batch3a_review.md
**Round 1 Prompt**: docs/review/codex_review_prompt_batch3a.md
**Review Date**: <date>
**Reviewer**: Codex
**Status**: <一句话总结，例如 "regression: <count> remaining; new findings: <H/M/L>; recommendation: (A)/(B)/(C)">

## Round 1 Findings 回归状态

| Round 1 Finding | 处置状态 | 评论 |
|----------------|---------|------|
| H1 SRS frontmatter 2 bool | ✅ 已修 / ⚠️ 部分残留 / ❌ 未修 | <具体描述> |
| H2 unresolved_bugs 合并 | ... | ... |
| H3 architecture release-close hook | ... | ... |
| H4 doc status mutation owner | ... | ... |
| M1 source-system-analysis snapshot | ... | ... |
| M2 technical-debt optional | ... | ... |
| M3 prd-review iteration reset | ... | ... |
| L1 prd-supporting type | ... | ... |
| Optional --finding-count / --max-severity | ... | ... |

## New Findings (Round 2)

### High/Medium/Low: <一句话标题>

- **Location**: `<file>:<line>`
- **Baseline Reference**: <相关 spec/design/batch1+2 file:line>（如有）
- **Issue**: <具体描述>
- **Impact**: <实现 / 协作时会导致什么问题>
- **Recommendation**: <具体修复建议>

[每条 finding 一节，按 High → Medium → Low 排]

## Cross-Finding Consistency Check

[9 项修复之间是否引入新的协作不一致；横向一致性 8 项检查结果]

## Design Gap Status Update

[Gap-1（review-passed → revising 缺事件）+ Gap-2（doc status mutation owner 接口待 doc-guardian 升级）的处置进展评估]

## Recommendation

- **(A)**: 进 batch 3b（development-* 6 个 skill 起骨架）—— 0 New High，且 Round 1 Findings 全部 ✅ 已修
- **(B)**: 修后再评（再评 1 轮）—— 有 New High 或 Round 1 残留
- **(C)**: 重设计（design level 问题）—— 触及架构层决策
```

### 评审风格约束

- 优先做**回归测试**：9 项修复是否完整落地到所有相关文件 + 措辞一致性
- 重点抓"修复引入的新一致性风险"，不重复 Round 1 已闭环的 10 个评审维度（如 spec/design 一致性、authority 标注、event 白名单等）
- 已经在 Round 1 闭环的决策（如 4 event 白名单、batch 3a 仅做骨架不做 references、三态 review-report 仅 Stage 4、PRD 不走 Bug Flow re-entry 等）不需要重新质疑结构合理性
- handoff §11 提示批 3a 评审循环放宽到 2-3 轮；本轮如 Round 1 全部 ✅ 已修 + 0 High new finding，建议 (A) 进 batch 3b
- 期望本轮 finding 数量 ≤ 5（Round 1 已抓主要骨头）；如出现 ≥ 3 New High 则可能 round 1 修法存在系统性问题，需 round 3
- Design Gaps（Gap-1 + Gap-2）是 design-level 议题；本批仅当 owner 声明清晰即可视为可接受；无需在 batch 3a 内 close（属下游 batch / spec 升级范畴）

请直接产出报告，不需要先和我对齐范围。
