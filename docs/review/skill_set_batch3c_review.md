# Skill Set Batch 3c Review (Testing / Delivery / Retrospective write+review × 3)

**Review Target**:
- `skills/testing-write/SKILL.md` (213 行)
- `skills/testing-review/SKILL.md` (162 行)
- `skills/delivery-write/SKILL.md` (164 行)
- `skills/delivery-review/SKILL.md` (143 行)
- `skills/retrospective-write/SKILL.md` (169 行)
- `skills/retrospective-review/SKILL.md` (148 行)
- 总计 999 行

**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`
**Batch 1 Reference**: `skills/workflow-protocol/SKILL.md` + `skills/doc-guardian/SKILL.md`（round 5 闭环）
**Batch 2 Reference**: `skills/scenario-dispatcher/SKILL.md` + `skills/bug-triage/SKILL.md` + `skills/workflow-evolution/SKILL.md`（round 3 闭环）
**Batch 3a Reference**: prd / srs / architecture write+review（round 3 闭环）
**Batch 3b Reference**: development planning/test/code write+review（round 2 闭环）
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: blocking issues: 0；finding 计 0 High / 1 Medium / 5 Low；recommendation: **(B) accept with Task 6 prerequisite**——6 SKILL.md 设计闭环；M1 要求把 Gap-5 候选 transition 命名补到 SKILL.md 与 task6_progress_py_prerequisites 文档；L1-L5 是 trivial cleanup，可在 batch 3c round 2 / Task 6 起骨架时顺手处理

---

## Findings

### Medium 1: Gap-5 推荐 transition 缺具体 command name 候选 + mutation 描述

- **Location**: `skills/testing-write/SKILL.md:213`（§10 Gap-5 段）, `skills/testing-review/SKILL.md:162`（§10 Gap-5 段）
- **Baseline Reference**: `docs/handoff/task6_progress_py_prerequisites_20260506.md`（Gap-3/Gap-4 已用 transition 表 + mutation 描述）；batch 3b round 2 review 对 Gap-3 / Gap-4 staging 的格式
- **Dimension**: 4 Gap-5 active retest fail implementability + 7 Command / state-machine correctness
- **Issue**: Gap-5 在两个 testing skill §10 中都用文字描述："推荐 Task 6 评估新增 dedicated transition（例如从 `current_stage=testing, bug_flow.active=true, sub_state=review-passed, test-report fail|partial` 回到 `bug_flow.root_cause` 对应 stage Change Mode）"。对比 Gap-3 / Gap-4 已用的格式（具体 transition 名 `verifying → code-revising` + 前置 + mutation + owner trigger），Gap-5 缺：
  1. 具体 command name 候选（是新 dedicated subcommand 如 `bug-rework`，还是放宽现有 `bug-start` 前置允许 `bug_flow.active==true` 时 re-trigger？）
  2. mutation 描述（`bug_flow.active` 是否保持 true？`bug_flow.root_cause` 复用还是清空？`current_stage` 切到哪？`sub_state` / `review_iteration` 处理）
  3. precondition 是否包括"BUG.root_cause != null"以区别于 initial bug-start
- **Impact**:
  - Task 6 实现 progress.py 时 Gap-5 是空白决策窗口；implementer 必须先反过来设计语义，可能延迟 Task 6 进度。
  - 当前 `docs/handoff/task6_progress_py_prerequisites_20260506.md` 不含 Gap-5（该文件创建于 batch 3b 后），如不补，Task 6 prerequisites 列表会漏 Gap-5，进 progress.py 实现期才发现。
  - 风险层级低（不会引入误用，因为 testing-write §5.2 Case C / §10 已禁止手工 patch / 错误 bug-start / bug-close），但 batch 3c 评审的设计责任是把 gap stage 清楚。
- **Recommendation**:
  - 在 testing-write §10 Gap-5 段补具体推荐（参考 Gap-3/Gap-4 风格）：

    ```
    Gap-5 推荐方案 (Task 6 评估)：
    - Option A：放宽 `bug-start` 前置——允许 `bug_flow.active==true && BUG.root_cause != null`
      作为重入条件；mutation 与原 bug-start 相同（current_stage→root_cause stage,
      sub_state→write, review_iteration→0；保持 bug_flow.active=true、bug_report_path
      / root_cause 不变）。优点：复用同一命令，schema 不扩；缺点：bug-start 语义偏移。
    - Option B：新增 dedicated `bug-rework --bug <path>`，前置同上 + test-report
      verification_status: fail|partial；mutation 同 Option A。优点：语义清晰；
      缺点：增加一个子命令。
    优先 Option B（语义清晰；与 Gap-3/4 改 transition 表风格一致）。
    ```
  - 同步 `docs/handoff/task6_progress_py_prerequisites_20260506.md` 加 §6 "Gap-5 — Active Bug Flow Retest Re-routing"，列出推荐 Option + transition 表 + mutation。
  - 这两个改动加起来 ~25 行 patch，可在 batch 3c round 2 一并做。

### Low 1: testing-write §2 sub_state 字段值用 narrative 而非 enum（与 batch 3b round 2 L1 同模式）

- **Location**: `skills/testing-write/SKILL.md:42`
- **Baseline Reference**: `skills/workflow-protocol/SKILL.md:73`（`sub_state` enum 定义）；`docs/review/skill_set_batch3b_round2_review.md`（Low 1 同模式）
- **Dimension**: 10 简洁度 / 术语
- **Issue**: §2 When to Invoke 表 `sub_state` 行写 "`write` / `revising`（写或修 Testing docs）；`review-passed`（仅 bug routing / bug-close submode）"。是 narrative 不是 enum。implementer 阅读 When to Invoke 表时可能误以为 `sub_state` 字段允许复合值。
- **Impact**: trivial；run-time 行为由 §3 Mode 表 + §5.2 routing case 多次澄清，不出错。
- **Recommendation**: 改为 enum + 表外 reentry note，同 batch 3b round 2 L1 推荐：
  ```
  | `sub_state` | `write` / `revising`（normal）；`review-passed`（仅 reentry 入口，见下）|

  **Reentry 入口**：当 `sub_state==review-passed` 且符合下表 §5.2 Case A/B/C 任一条件……
  ```

### Low 2: delivery-write §7 "回 testing 阶段重测" 暗示存在不存在的 transition

- **Location**: `skills/delivery-write/SKILL.md:127`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md`（state machine 转移表无 delivery → testing transition）；`skills/workflow-protocol/references/command-reference.md:313`（`bug-intake` 仅在 `release_state==closed` 期间）
- **Dimension**: 7 Command / state-machine correctness + 5 Stage 6 Delivery correctness
- **Issue**: §7 Bug Flow Re-entry 第 3 行 "若必须记录 bug，按项目策略回 testing 阶段重测/创建 BUG，或 release close 后走 post-close bug-intake；本 skill不自创 bypass"。但当前 spec 没有从 delivery → testing 的 transition；implementer 可能误以为存在该路径。`bug-intake` 只在 `release_state==closed` 期间合法，与"按项目策略回 testing 阶段"的暗示不一致。
- **Impact**: 可能导致 Task 6 实现者期望 progress.py 提供 delivery → testing rollback 命令；或 caller 试图触发不存在的回退。但 §8 Forbidden 已禁止 "调 bug-triage / bug-start / bug-close"，最终行为不会出错。
- **Recommendation**: 改写为：
  ```
  若必须记录产品 bug，目前 spec 不提供 delivery → testing 的合法 rollback transition；
  可走的合法路径：
    (a) 升级用户/Bootstrap 决策：保留当前 release，由 user 决定 release-close 后
        post-close mode 走 bug-intake（前置 release_state==closed）；
    (b) 升级用户/Bootstrap 决策：若 product bug 严重到必须当前 release 修，
        由 user/Bootstrap 评估是否需要新 design proposal 加 dedicated rollback
        transition（与 Gap-5 类似的 staging）。
  本 skill 不自创 bypass、不调 bug-triage / bug-start / bug-close。
  ```

### Low 3: testing-write §3 Bug Close mode 前置比 spec 严

- **Location**: `skills/testing-write/SKILL.md:70`
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:386-389`（bug-close 前置：`bug_flow.active == true` + `current_stage == testing` + 最新 test-report `verification_status: pass`）
- **Dimension**: 7 Command / state-machine correctness
- **Issue**: §3 表 Bug Close mode 入口写 "`bug_flow.active==true`, report pass, sub_state review-passed | 调 progress.py bug-close"。SKILL.md 加了 `sub_state review-passed` 限制（实际是 testing-review 已 review-passed 后才 close 的 safety net），但 command-reference §9 没列该前置。
- **Impact**: trivial，是 over-cautious 而非 wrong。但 Task 6 实现 progress.py bug-close 时若严格按 command-reference 前置（少了 sub_state 检查），与 SKILL.md 描述前置不一致；测试 / 文档对照可能出现轻微偏差。
- **Recommendation**: 二选一：
  - (a) 接受 SKILL 比 spec 更严，加 footnote："本 skill 在 sub_state==review-passed 后才调用 bug-close 是 caller-side safety net；progress.py bug-close 自身仅检查 bug_flow.active + current_stage==testing + test-report pass。"
  - (b) 调整 SKILL.md 仅要求 bug_flow.active + report pass，sub_state review-passed 作为 caller best-practice 而非 hard precondition。

  **优先 (a)**：保险更安全，且当前 testing-write §5.2 Case B 已建立 review-passed → bug-close 流水线，移除限制反而引入风险。

### Low 4: retrospective-write 没明确说 retrospective.md 首次创建 owner

- **Location**: `skills/retrospective-write/SKILL.md:60-63`（§3 Full Mode 行）
- **Baseline Reference**: `skills/doc-guardian/references/directory-layout.md`（retrospective.md 项目级单文件）；`skills/doc-guardian/references/required-artifacts.md` Stage 7（"项目级单文件，每 release 增量加节"）
- **Dimension**: 1 Spec consistency / 6 Stage 7 Retrospective correctness
- **Issue**: §3 Full Mode 行 "在项目级 retrospective.md 追加当前 release section"。"追加"暗示文件已存在；但项目第一次 release 进入 Stage 7 时文件尚不存在。SKILL.md 没明确说 first-release Stage 7 由本 skill 创建文件（含 universal frontmatter + 第一个 release section + Pending/Change Log skeleton）。implementer 可推断但不显式。
- **Impact**: trivial；任何 implementer 看到目录无 retrospective.md 自然会创建。
- **Recommendation**: §3 Full Mode 行加注："首个 release 进入 Stage 7 时本 skill 创建 retrospective.md（universal frontmatter + 第一个 release section + 空 Pending Changes + 空 Change Log skeleton）；后续 release 在同一文件追加新 release section。"

### Low 5: testing-write description 行长度

- **Location**: `skills/testing-write/SKILL.md:3`
- **Dimension**: 10 简洁度
- **Issue**: description 行 ~600 字符（本批最长），描述 7 项职责精华。其他 batch 3c skill description ~300 字符。
- **Impact**: trivial；description 用于 skill discovery，长一点不影响 invoke。
- **Recommendation**: 不强制改；如未来精简可拆"writes Testing docs"主线 + "manages BUG skeleton, invokes bug-triage, calls bug-close"副线分两段。

---

## Cross-Skill Consistency Check

按 caller → callee 列表（任一不含 H/M 的视为 ✓）：

| Caller | Callee | 一致性 | 评论 |
|--------|--------|--------|------|
| `testing-write` | `testing-review` | ✓ | write-complete / review-issues / review-passed event 三角全闭环；testing-review §4.1 三种 review-passed 与 testing-write §3 Bug Routing / Retest / Bug Close / Retest Fail Escalation modes 一一对应 |
| `testing-review` | `testing-write` | ✓ | issues-found 后 sub_state revising，testing-write §3 Review Revise mode 接管 |
| `testing-write` | `bug-triage` (active mode) | ✓ | testing-write §5.2 Case A 在 sub_state==review-passed + bug_flow.active==false + report fail/partial 时 invoke bug-triage；与 bug-triage SKILL §2.1 active mode gate 严格一致 |
| `testing-write` | `progress.py bug-close` | ✓ | testing-write §5.2 Case B (sub_state==review-passed + bug_flow.active==true + report pass) 调 bug-close；与 command-reference §9 前置基本一致（sub_state==review-passed 是 caller-side safety net；详见 L3） |
| `testing-write` | `progress.py bug-start` (NOT) | ✓ | §1 / §8 Forbidden 严格禁止 testing-write 调 bug-start / incident-start；交给 bug-triage |
| `testing-write` (Retest Fail) | `progress.py` (Gap-5 path) | ⚠ M1 | Case C 行为正确（不 close、不 re-triage、升级用户），但 Gap-5 命令 stage 不充分（详见 M1） |
| `delivery-write` | `delivery-review` | ✓ | write-complete / review-issues / review-passed 三角闭环 |
| `delivery-review` | `delivery-write` | ✓ | fail/partial → issues-found → delivery-write Change Mode（不创建 active BUG） |
| `delivery-write/-review` | `bug-triage` (NOT) | ✓ | 6 个 SKILL.md 在 §1/§8 Forbidden / §7 Bug Flow Re-entry 都明确 Stage 6 不启动 active Bug Flow，与 bug-triage SKILL §2.1 active mode gate（current_stage==testing）严格对齐 |
| `delivery-write` | "回 testing rollback" 暗示 | ⚠ L2 | §7 line 127 有歧义；详见 L2 |
| `delivery-write/-review` | `release-close` (NOT) | ✓ | 6 个 SKILL.md 都不调 release-close；retrospective-* 也不调；交 Bootstrap |
| `retrospective-write` | `retrospective-review` | ✓ | 三角闭环；Pending → promote → validate → write-complete 流水线一致 |
| `retrospective-review` | `retrospective-write` | ✓ | issues-found 后 revising；维度 6 Recursion compliance + 维度 7 Upstream boundary 检查 retrospective-write §8 Forbidden 内容 |
| `retrospective-write/-review` | `workflow-evolution` (NOT auto) | ✓ | 都明确 retrospective consumption 是用户主动 advisory；不调 workflow-evolution；与 workflow-evolution SKILL §2.2 retrospective consumption mode 描述（用户主动）一致 |
| `retrospective-write/-review` | `release-close` (NOT) | ✓ | 都说不调 release-close，由 caller/Bootstrap 在 review-passed 后调用；与 command-reference §5 release-close 前置（sub_state==review-passed）一致 |
| 6 dev skills | `workflow-protocol` event whitelist | ✓ | 全部使用 4 白名单事件 (`write-complete` / `review-issues` / `review-passed` / `human-confirmed`)；`issues-found` 仅作业务术语，不当 event |
| 6 dev skills | `doc-guardian`/Change Log 分类 | ✓ | Testing docs / Delivery docs 一次性 doc 不要 Pending/Change Log；BUG report / Retrospective 增量类 doc Pending → promote → validate；与 change-log-format.md §1 严格对齐 |
| 6 dev skills | Gap-1 / Gap-2 staging | ✓ | 6 个 SKILL.md §10 Design Gaps 都声明 Gap-1 / Gap-2，与 batch 3a round 3 / batch 3b round 2 闭环格式一致 |

**横向无打架**。Stage 5/6/7 各自的 Bug Flow 边界严格分离，符合"Stage 5 是唯一 active Bug Flow 入口/出口"设计边界（v0.6 round 2 batch2-F2）。

---

## Stage 5 Bug Flow Assessment

按 prompt 列出的 5 个评估点：

### 1. Initial fail/partial → BUG skeleton + triage-ready

- testing-write §5.1 Step 3：fail/partial 创建 BUG-NNN.md skeleton；ID 3 位 zero-padded（`BUG-NNN`）；frontmatter `root_cause: null`、`target_release == found_in_release`、`consumed_in_release: null`、`type: bug-report`、`status: draft` ✓
- 与 bug-triage SKILL §3.3 active mode BUG frontmatter 期望严格一致
- BUG report 是增量类 doc，Pending Changes → `changelog.py promote` → `validate.py file` 在 invoke bug-triage 前 ✓
- testing-review §3 维度 6 BUG readiness：root_cause==null、target_release=found release、可 validate ✓

### 2. testing-review 三态 review-passed 条件

- §4.1 列了 3 种 review-passed：
  - Testing pass：report verification_status==pass + 无 blocking finding
  - Initial testing fail but triage-ready：bug_flow.active==false + report fail|partial + Testing docs/BUG skeleton 合规
  - Active retest fail accurately recorded：bug_flow.active==true + report fail|partial + linkage 完整
- 第二种 review-passed 满足 bug-triage active mode gate（current_stage==testing AND sub_state==review-passed）✓
- 第三种 review-passed 让 caller 进 Gap-5 升级 path，不 advance 不 close ✓
- E 维度（report.verification_status==pass）严格作为 advance 前置，不与 review-passed 混淆 ✓（§6 line 117-118 明确）

### 3. Stage 5 advance E 严格性

- testing-write §6 line 161-163：E 维度 = test-report verification_status: pass；fail/partial 不 done
- testing-review §6 line 117-118：review-passed 不等于 Stage 5 done；workflow-protocol advance 必须拒绝 fail/partial
- §8 Forbidden testing-write line 180："`test-report verification_status: fail|partial` 时调 `update --advance`"
- 与 workflow-protocol §5.1 Stage 5 行 E 维度严格一致 ✓

### 4. bug-close 前置 + owner

- bug-close owner = testing-write（§5.2 Case B）
- testing-review §1 不属于本 skill：调 bug-close ✓
- 前置：bug_flow.active==true + report pass + sub_state==review-passed（详见 L3 over-cautious 但安全）
- 与 command-reference §9 一致（除 sub_state 略严）✓

### 5. Active retest fail/partial Gap-5 处理

- testing-write §3 Retest Fail Escalation mode 表行 ✓
- testing-write §5.2 Case C：不 close、不重新 triage、不创建新 BUG、升级 Gap-5 ✓
- testing-write §9 Recovery："不重开 triage、不手工回 root_cause stage；升级用户/Bootstrap" ✓
- testing-review §4.1 第三种 review-passed + §7 retest fail 段对齐 ✓
- §10 Gap-5 声明 ✓（命名 candidate 不充分；详见 M1）

**结论**：Stage 5 Bug Flow 完整性 5 个评估点 4 个 ✓ 1 个 ⚠（Gap-5 staging 缺命名候选；可在 minor patch 修）。Initial fail / triage / retest pass / retest fail 四个分支语义清晰，无误导 implementer 重 triage active BUG / 创建新 BUG / 手工 patch 风险。

---

## Stage 6 Delivery Assessment

### 1. installation_result pass gate

- delivery-write §6 E 维度：installation-result.verification_status: pass ✓
- delivery-review §3 维度 6 / §4.1 / §4.2：fail/partial 一律 blocking，必须 issues-found；pass 才 review-passed ✓
- delivery-write §8 Forbidden line 132："installation_result fail/partial 时调 `update --advance`" ✓

### 2. fail/partial 不进 Bug Flow

- delivery-write §1 line 27："不属于本 skill：创建 BUG report 或调用 bug-triage（Bug Flow 入口仅 Stage 5 testing）" ✓
- delivery-write §7："若安装验证暴露产品 bug → 停止并升级用户/Bootstrap；不要直接创建 active BUG（bug-triage active mode gate 要求 current_stage==testing）" ✓
- delivery-review §1 / §8 Forbidden 同样禁止调 bug-triage / bug-start / bug-close ✓
- 与 bug-triage SKILL §2.1 active mode gate（current_stage==testing）严格对齐 ✓

### 3. Upstream mismatch escalation

- delivery-write §3 Upstream mismatch escalation mode：停止并升级人介入；不在 Stage 6 自行改上游 ✓
- delivery-write §9 Recovery："installation fail due product bug | 停止并升级用户/Bootstrap；不要在 delivery 内创建 active BUG" ✓
- delivery-review §3 维度 7 Upstream mismatch：是否暴露 SRS/Architecture/Development/Testing 上游问题？ ✓

**结论**：Stage 6 设计严格保守，无 Bug Flow 入侵，无擅改上游。L2（"回 testing rollback" 暗示）是术语清晰度问题，不阻塞。

---

## Stage 7 Retrospective Assessment

### 1. 项目级单文件 + 增量加节

- retrospective-write §1 line 16："维护 docs/retrospective/retrospective.md 项目级单文件" ✓
- §4 Doc Output Contract："项目级单文件，每 release 增量加节。Issue Analysis Report / Workflow Improvement Proposal / Skill Improvement Proposal / Template Improvement Proposal / Token Optimization Proposal 都是该单文件内部章节，不是独立 doc" ✓
- 与 doc-guardian directory-layout.md / required-artifacts.md Stage 7 一致 ✓
- L4：首次创建 owner 没明确，但可推断 ✓

### 2. Pending → promote → validate

- retrospective-write §5 Step 3-5 顺序 ✓
- retrospective 是增量类 doc（与 change-log-format.md §1 一致）✓
- §1 / §8 Forbidden：跳过 Pending Changes / changelog promote ✓

### 3. release section 最低内容

- §4 列 7 章节：Release Summary / Stage Timeline / Bug-Incident Summary / Review Loop Summary / Issue Analysis by Dimension / Improvement Proposals / Action Items
- Issue Analysis by Dimension 拆 6 维度（AI Capability / Workflow Defect / Skill Gap / Documentation Gap / Token Waste / No-action Finding）
- 覆盖完整 ✓

### 4. release-close 边界

- retrospective-write §1 line 26："不属于本 skill：调 release-close" ✓
- retrospective-review §1 line 25："不属于本 skill：调 release-close" ✓
- 6 §8 Forbidden 都禁止 release-close
- review-passed 后由 caller/Bootstrap 调 release-close（command-reference §5 前置 sub_state==review-passed 严格一致）✓

### 5. workflow-evolution advisory boundary

- retrospective-write §1 line 27："不属于本 skill：调 workflow-evolution（retrospective consumption mode 是用户主动可选）" ✓
- retrospective-write §7 Workflow Evolution Boundary：advisory 持久化必须在 Stage 7 合法 write/revising 入口；review-passed 后想持久化必须先升级（Gap-1）✓
- retrospective-review §1 / §7 / §8 Forbidden：调 workflow-evolution ✓
- 与 workflow-evolution SKILL §2.2 retrospective consumption mode 描述（用户主动 advisory）严格一致 ✓

### 6. Recursion compliance

- retrospective-write §1 line 28："修改 dev-workflow-skills2 自身 skill 文件（递归悖论；只能提出 advisory）" ✓
- §8 Forbidden line 137："修改 dev-workflow-skills2 自身 skill/reference/script 文件" + line 138："输出 patch / diff / unified diff 作为 workflow 改进落地" ✓
- retrospective-review §3 维度 6 Recursion compliance：是否试图直接 patch dev-workflow-skills2 或修改自身 workflow ✓
- §8 Forbidden line 121："输出 patch / diff / unified diff" ✓
- 与 workflow-evolution §8.1-§8.3 递归约束严格一致 ✓

### 7. Gap-1 限制

- retrospective-write §10 Gap-1 段："review-passed 后想把 advisory 持久化到同一 release section，当前没有合法 reentry event；需升级用户/Bootstrap、延后到下一 release" ✓
- retrospective-review §10 Gap-1 段同样 ✓
- 与 batch 3a round 3 / batch 3b round 2 Gap-1 staging 一致 ✓

**结论**：Stage 7 设计严密。递归悖论 / advisory boundary / Gap-1 处置 / release-close 边界 / 项目级单文件增量 全部合规。L4（首次创建 owner）trivial。

---

## Design Gap Resolution

| Gap | 来源 | Batch 3c 处置 | Task 6 前置 |
|-----|------|---------------|-------------|
| **Gap-1**（`review-passed → revising` 全局 transition）| batch 3a round 3 沿用 | 6 SKILL.md §10 都声明 Gap-1；testing-write / delivery-write / retrospective-write / retrospective-review / testing-review / delivery-review 各自描述 review-passed 后窗口期处理；无任何处误调不存在的全局 event；无回归 | 不阻塞骨架；workflow-protocol 升级周期处理 |
| **Gap-2**（doc frontmatter status mutation helper）| batch 3a round 3 沿用 | 6 SKILL.md §10 都声明 Gap-2；testing-review §4.1 / delivery-review §4.1 / retrospective-review §4.1 等明确 doc status 由 helper 同步；无要求 write/review skill 直接修改不属于自己的 frontmatter status | 不阻塞骨架；doc-guardian batch upgrade 时一并补 |
| **Gap-3**（`verifying → code-revising`）| batch 3b round 2 推荐 transition | 本批不涉及 Stage 4 内部 transition；6 SKILL.md 无任何处暗示 caller 可绕过 Gap-3；与 task6_progress_py_prerequisites 列出的前置一致 | 已 stage 在 task6_progress_py_prerequisites_20260506.md §1 |
| **Gap-4**（Bug Flow verified task rollback）| batch 3b round 2 声明 + 推荐 | 本批不涉及 Stage 4 task rollback；6 SKILL.md 无任何处暗示 testing-write 直接处理 Stage 4 task rollback（只调 bug-triage active mode）；不绕过 Gap-4 | 已 stage 在 task6_progress_py_prerequisites_20260506.md §2 |
| **Gap-5**（active Bug Flow retest fail re-routing）| **本批新识别** | testing-write §10 + testing-review §10 已声明 Gap-5；testing-write §5.2 Case C / §9 / §10 严格保守（不重 triage / 不创建新 BUG / 不手工 patch）；推荐方向已表述（"从 testing+bug_flow.active+review-passed+test-report fail/partial 回到 root_cause stage Change Mode"）；**但 transition / command name 候选 + 完整 mutation 描述未列**（详见 M1） | **应 stage 到 task6_progress_py_prerequisites_20260506.md（§6 新增章节）**；M1 修复后 Task 6 implementer 可直接按 transition 表实现 |

**Gap-5 真实性 + Task 6 prerequisite 评估（回答 prompt §"新识别 design gap"3 个问题）**：

1. **Gap-5 是否真实存在？是否应成为 Task 6 prerequisite？**
   - 真实存在。当前 command-reference 没有 active Bug Flow retest fail/partial 时回到 root_cause stage Change Mode 的合法路径。如不补，active BUG retest fail 后状态机卡死（caller 不能 close、不能重 triage、不能 advance）。
   - **应成为 Task 6 prerequisite**（与 Gap-3/4 同级别）。
2. **当前 2 个 testing skill 对 Gap-5 的声明是否足够保守？**
   - 保守度足够：testing-write §5.2 Case C 不 close、不 re-triage、不创建新 BUG、不手工 patch；testing-review §4.1 第三种 review-passed 让 caller 进 Gap-5 升级 path 而不试图绕过。
   - 改成"retest fail 一律 issues-found"的替代方案**不推荐**：那样会让 caller 不停 issues-found loop（因为 BUG 是 root cause stage 的问题，testing-write 修不了），review_iteration 会撞 cap 7 然后升级人介入——结果一样卡死，但占了 iteration 计数。当前"review-passed 后升级 Gap-5"更准确。
   - 改成"新增明确 command 名"是 M1 推荐的下一步。
3. **是否存在误导实现者的风险？**
   - 不存在。SKILL.md 多处禁止重 triage active BUG（§1 / §3 / §5.2 Case C / §8 / §9 / §10）；不创建新 BUG；不手工修改 progress.md；不错误调 bug-start / bug-close。implementer 按图施工只会停在升级用户/Bootstrap 这一步，等待 Task 6 补 Gap-5 transition。

---

## Implementability Assessment

按 6 个 skill 列出 implementer 能否直接实现：

| Skill | 可实现性 | 关键模糊点 / 阻塞 |
|-------|---------|-------------------|
| `testing-write` | ⚠ 基本可实现 | (i) M1 Gap-5 命名候选缺失；(ii) L1 sub_state narrative；(iii) L3 bug-close 前置略严；(iv) L5 description 长 |
| `testing-review` | ✓ 可实现 | (i) M1 Gap-5 配套；其余无阻塞 |
| `delivery-write` | ⚠ 基本可实现 | (i) L2 "回 testing rollback" 措辞清晰度 |
| `delivery-review` | ✓ 可实现 | 无阻塞 |
| `retrospective-write` | ✓ 可实现 | (i) L4 首次创建 owner 表述 |
| `retrospective-review` | ✓ 可实现 | 无阻塞 |

**总体**：6/6 skill 可在 minor patch 后实现；M1（Gap-5 staging）是文档级补充，不属于 SKILL.md 设计错误。

**需要 progress.py / validate.py / changelog.py 支持的点**（不是本批责任）：

- progress.py：Gap-5 transition / command（M1 推荐 Option B 新增 `bug-rework` 子命令）
- progress.py：Gap-3 / Gap-4 transitions（已 stage 在 prerequisites）
- progress.py：bug-close 前置 sub_state == review-passed 是否加（与 L3 相关；建议 caller-side check 不强制 progress.py 验证）
- doc-guardian validate.py：Stage 5/6/7 doc schema 已在 frontmatter-schema.md 闭环；validate.py file 行为按现有 references 即可
- doc-guardian changelog.py：Testing docs / Delivery docs 一次性 doc 跳过 promote；BUG report / Retrospective 走完整 promote 流程；与 change-log-format.md §1 一致

---

## Positive Notes

1. **Stage 5 三态 review-passed 设计严密**：testing-review §4.1 把 "Testing pass" / "Initial fail triage-ready" / "Active retest fail linkage-ready" 三种合法 review-passed 区分清楚，避免常见误导（"fail = issues-found"）。
2. **Bug Flow 入口/出口集中在 Stage 5**：6 个 SKILL.md（含 delivery / retrospective）一致禁止 Stage 6/7 启动 active Bug Flow，与 v0.6 round 2 batch2-F2 收敛（active mode 严格 testing+review-passed 入口）完美对齐。
3. **递归悖论防御严格**：retrospective-write §1 / §7 / §8、retrospective-review §1 / §3 维度 6 / §7 / §8、与 workflow-evolution §8 一致禁止 patch dev-workflow-skills2，advisory vs patch 边界清晰。
4. **Gap-5 保守处理范本好**：testing-write §5.2 Case C 不 close / 不 re-triage / 不创建新 BUG / 不手工 patch / 升级用户/Bootstrap 五条互锁，确保 implementer 不会在 Task 6 实现前误用状态机。
5. **Stage 6 vs Stage 5 fail 行为差异化设计合理**：Stage 5 fail/partial 可以 review-passed（进 bug-triage path）；Stage 6 fail/partial 一律 issues-found（不进 Bug Flow）。这一差异在 testing-review §4.1 与 delivery-review §3 维度 6 / §4.1 都明确，避免 implementer 误把 Stage 6 fail 当 Bug Flow。
6. **简洁度优秀**：6 个 SKILL.md 平均 166.5 行（vs batch 3b 平均 ~212 行），章节结构清晰，没有冗余。
7. **doc 分类与 Change Log 全程一致**：Testing docs / Delivery docs 一次性 doc 不需 Pending/Change Log；BUG report / Retrospective 增量类。各 SKILL.md 在 §4 Doc Output Contract 表的"Change Log"列与 §5 Procedure 都明确 promote 步骤，没有遗漏或矛盾。
8. **release-close 边界清晰**：retrospective-write/-review 都不调 release-close；命名 owner = caller/Bootstrap；与 command-reference §5 前置一致；避免 retrospective skill 误关 release。

---

## Suggested Next Revision Order

按优先级排序（M first → L last）：

1. **M1 Gap-5 命名 + 追加 prerequisites**（patch ~25 行，2 文件）：
   - testing-write §10 Gap-5 段补具体 command name 候选（推荐 Option B `bug-rework`）+ 前置 + mutation 表
   - testing-review §10 Gap-5 段同步
   - 在 `docs/handoff/task6_progress_py_prerequisites_20260506.md` 加 §6 "Gap-5 — Active Bug Flow Retest Re-routing"
2. **L2 delivery-write §7 措辞**（patch ~6 行，1 文件）：删除"回 testing 阶段重测"暗示，改成 (a)/(b) 升级用户/Bootstrap 决策。
3. **L1 testing-write §2 sub_state narrative**（patch ~4 行，1 文件）：改 enum + reentry note。
4. **L3 testing-write §3 bug-close 前置注**（patch ~2 行，1 文件）：加 footnote 解释 sub_state==review-passed 是 caller-side safety net。
5. **L4 retrospective-write §3 首次创建 owner**（patch ~2 行，1 文件）：加注首次创建。
6. **L5 testing-write description 长度**（patch ~2 行，1 文件）：可选；不强制。

**预计 patch 总量**：~40 行 / 6 文件。M1 是主要内容（Gap-5 staging）；L1-L5 都是 trivial cleanup。可在 1 轮内完成。

**进 Task 6 前置（独立于 SKILL.md patch）**：
- M1 推荐的 prerequisites 文件 §6 新增章节
- Task 6 实现 progress.py 时按 prerequisites §1-§6 顺序补 transition + command

---

## Recommendation

- **(B): accept with Task 6 prerequisite**

**理由**：
- 6 SKILL.md 设计本身闭环且与 batch 1/2/3a/3b 一致；0 High，1 Medium 是 Gap-5 staging 升级（属于 prerequisites 文档管辖，非 SKILL.md 设计错误）；5 Low 都是 trivial cleanup。
- 横向一致性强：testing/delivery/retrospective Bug Flow 边界严格分离；递归悖论防御完整；Gap-1 / Gap-2 staging 与 batch 3a round 3 / batch 3b round 2 一致；event whitelist / task transition / no manual progress.md / no auto release-close / no patch dev-workflow-skills2 全程合规。
- M1 + L1-L5 patch 总量 ~40 行，可在 batch 3c round 2 一次收敛或随 Task 6 起骨架时顺手处理；不阻塞 Task 6。
- 6 SKILL.md 与 design proposal v0.5 §3 23 physical skills 完全对应（testing-write / testing-review / delivery-write / delivery-review / retrospective-write / retrospective-review）；与 frontmatter-schema.md / required-artifacts.md / change-log-format.md / directory-layout.md 全程对齐，无 schema 偏差。

**不推荐 (A) 进 round 2/fix 的判据**：当前 finding 含 0 High / 1 Medium / 5 Low；Medium 主要是文档 staging 改进（Gap-5 命名）+ prerequisites 文件追加，不是 SKILL.md 自身设计错误；按 batch 3a round 3 / batch 3b round 2 处理风格，"已声明 Task 6 prerequisite gap" 不阻塞骨架，可走 (B)。如果项目要求与 batch 3b round 2 同样标准化（"Medium ≥ 3"才 (A)），那本批 1 Medium + 5 Low 自然落在 (B)。

**不推荐 (C) 重设计的判据**：本批 finding 全部不触及已闭环的架构层决策；Gap-5 是 transition 表 + command 命名层面的 staging，不需要 design level 重做；6 SKILL.md 与 23 physical skill 架构一致；Stage 5/6/7 Bug Flow 边界 / 递归悖论 / release-close 边界等关键设计决策均合规。

**Task 6 进入 checklist**：
- [x] Gap-1 / Gap-2 staging（batch 3a round 3 闭环）
- [x] Gap-3 / Gap-4 staging（batch 3b round 2 + task6_progress_py_prerequisites_20260506.md §1-§5）
- [ ] Gap-5 staging（batch 3c M1 修后追加 task6_progress_py_prerequisites_20260506.md §6）
- [x] 6 个 dev-* SKILL.md（batch 3b round 2 闭环）
- [x] 6 个 stage 5/6/7 SKILL.md（batch 3c round 1 接受）
- [ ] Optional：M1 + L1-L5 minor patch（不阻塞 Task 6 起骨架）
