# Skill Set Batch 3b Review (Development planning/test/code write+review × 3)

**Review Target**:
- `skills/development-planning-write/SKILL.md` (234 行)
- `skills/development-planning-review/SKILL.md` (190 行)
- `skills/development-test-write/SKILL.md` (199 行)
- `skills/development-test-review/SKILL.md` (204 行)
- `skills/development-code-write/SKILL.md` (235 行)
- `skills/development-code-review/SKILL.md` (209 行)

**Workflow Baseline**: `docs/workflow/workflow_specification_claude.md` (v0.6)
**Design Reference**: `docs/design/skill_set_design_proposal_v0.5.md`
**Batch 1 Reference**: `skills/workflow-protocol/SKILL.md` + `skills/doc-guardian/SKILL.md` (round 5 闭环)
**Batch 2 Reference**: `skills/scenario-dispatcher/SKILL.md` + `skills/bug-triage/SKILL.md` + `skills/workflow-evolution/SKILL.md` (round 3 闭环)
**Batch 3a Reference**: `skills/prd-*` / `skills/srs-*` / `skills/architecture-*` (round 3 闭环)
**Review Date**: 2026-05-06
**Reviewer**: Claude
**Status**: blocking issues: 2 High（H1 新 Gap-4 + H2 已声明 Gap-3 复核确认）/ 6 Medium / 9 Low；recommendation: **(B) 修后再评** ——在 3 个 dev SKILL.md 增声明 Gap-4 + 修 M1/M2/M4/M5/M6 后即可进 batch 3c

---

## Findings

### High 1: Bug Flow Direct Route 未提供 verified task 回退 transition（新 Gap-4）

- **Location**: `skills/development-planning-write/SKILL.md:80-81`（§3 Bug Flow Direct Route 行），`skills/development-test-write/SKILL.md:36-58`（§2 When to Invoke），`skills/development-code-write/SKILL.md:35-55`（§2）
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:564-580`（Stage 4 task state 转换表只列前向 transition）；`skills/workflow-protocol/SKILL.md:182-195`（§5.2 task 子状态序列）
- **Dimension**: 8 Bug Flow development re-entry 完整性 + 1 spec 一致性 + 11 recovery
- **Issue**:
  - planning-write §3 "Bug Flow Direct Route" 表写"BUG 已标清 Affected Task(s) 且无需改 design...不修改 task state，或仅让 downstream skill 使用既有 task state 进入 revise"。
  - 但 command-reference Stage 4 task state 转换表**只有前向 transition**：`planning-done → test-writing → ... → code-review-passed → verifying → verified`，**没有**`verified → test-revising`、`verified → code-revising`、或任何从 verified / code-review-passed 回退的 transition。
  - test-write §2 入口仅允许 `planning-done / test-writing / test-revising`；code-write §2 入口仅允许 `test-done / code-writing / code-revising / code-review-passed / verifying`。**两者都拒绝 `verified` 作为入口**。
  - `progress.py bug-start --root-cause development`（command-reference §8）只切 `current_stage` + `sub_state=write`，**不修改 task_states**。
  - 结果：当 BUG 涉及一个已 `verified` 的 task 时，进入 development Change Mode 后 task state 仍是 `verified`，下游 test-write / code-write 都无法从 `verified` 启动。Bug Flow Direct Route 路径**实际不可达**。
- **Impact**:
  - 任何 root_cause==development BUG 修复，如果 affected task 已 verified（这是 Bug Flow 最常见场景：Stage 5 测出 bug 时，被影响 task 在 Stage 4 已通过验证），workflow 直接卡死。
  - 违反 workflow-protocol §6 Bug Flow 完整闭环原则；Task 6 实现 progress.py 时若严格按当前转换表，整条 development root cause Bug Flow 不可执行。
- **Recommendation**:
  - 与 Gap-3 同等处理：在 `development-planning-write` / `development-test-write` / `development-code-write` 三份 SKILL.md 显式声明 **Gap-4**：command-reference Stage 4 task transition 表需补 `verified → test-revising` 与 `verified → code-revising`（或等价 `bug-flow-rollback` event），由 `progress.py bug-start --root-cause development` 在切 stage 时按 BUG body `Affected Task(s)` 一并显式回退 affected verified task；Task 6 实现 workflow-protocol 时必须先补这两条 transition。
  - 二选一明确补的方式：(选项 a) 在 task 转换表加两条手动 transition，由 downstream skill 显式调用 `progress.py update --task Tn --status code-revising`；(选项 b) 把 task rollback 内嵌在 `bug-start` 流程，从 BUG body 解析 affected task list + 决定回退到 `test-revising` 或 `code-revising`（按是否需测试改动）。**优先 (b)**：避免 downstream skill 误把不可达 task 误推进；与 H2 Gap-3 同时实现可减少 workflow-protocol 改动次数。
  - 在补齐前，禁止手工编辑 progress.md 把 verified task 改回。
  - 同时 planning-write §3 Bug Flow 表加注：Direct Route 仅适用 affected task **当前不在 verified** 时；verified 时按 Gap-4 路径处理。

### High 2: Verification Fail 回退 transition 缺失（已声明 Gap-3，复核确认是 Task 6 blocker）

- **Location**: `skills/development-code-write/SKILL.md:235`（§10 Gap-3 行）, `skills/development-code-review/SKILL.md:209`（§10 Gap-3 awareness）
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:579-580`（Stage 4 task table 仅列 `verifying → verified`）
- **Dimension**: 7 code pair, 1 spec 一致性, 11 recovery
- **Issue**:
  - 两个 skill 已声明 Gap-3：`verifying → code-revising`（或等价 `verification-failed` event）transition 缺失。
  - 复核确认这是真 blocker：
    - code-write §3 表"Verification Retry"行说"按 verification failure 修 code 后重新 review/verify | 需要 workflow-protocol 补回退 transition（见 Gap-3）"。
    - code-write §5.2 Step V4 fail 分支："不得标 verified；按 Gap-3 需要 workflow-protocol fail transition 回 code-revising"。
    - code-write §9 Recovery："verification tests fail | 写 verification_result.md verification_status: fail/partial；不得标 verified；按 Gap-3 回 code-revising + review"。
  - 当前转换表无法执行"回 code-revising"，task 卡在 `verifying`。
- **Impact**:
  - Task 6 实现前必须解决；否则 code-write Verification Retry mode 与 Recovery 都不可执行。
  - 若 verification fail 后无法回退，唯一可达路径是绕过 task state machine 手工改 progress.md，但 SKILL.md 与 Gap-3 都明令禁止。
- **Recommendation**:
  - 评审目标 §3 Q (a)(b)(c)：
    - **(a) 是否真实且阻塞 Task 6？** 真实，是 blocker。
    - **(b) batch 3b SKILL.md 声明是否足够？** 声明位置与措辞合格（不绕过、明确指向 workflow-protocol upgrade owner），但建议统一回退状态名。当前两个 SKILL.md 都用"回 code-revising"，无歧义；可接受。
    - **(c) 推荐补哪种 transition？** 推荐 `verifying → code-revising`，前置 `verification_result.md` 存在且 `verification_status: fail|partial`。理由：(i) `code-revising` 后续走 `code-review` 强制重过 code review（防止开发者绕过 review 直接修），与 H1 推荐 (b) 同时实现可统一 backwards transition 路径；(ii) 不引入新 task state（如 `verification-failed`）减少状态机膨胀。
  - command-reference Stage 4 转换表补：`verifying → code-revising | verification_result.md verification_status: fail|partial`。同时 progress.py update --task 校验 verification_result 存在 + status 合法。

### Medium 1: planning review pass 后 partial task registration 的 recovery 不充分

- **Location**: `skills/development-planning-review/SKILL.md:79-83`（§4.1 pass 流程）, `skills/development-planning-review/SKILL.md:127-129`（§5 Step 5）, `skills/development-planning-review/SKILL.md:168-174`（§9 recovery）
- **Baseline Reference**: `skills/workflow-protocol/references/command-reference.md:108-119`（§2.1 sub_state 转换；review-passed 单独事件）+ `skills/workflow-protocol/references/command-reference.md:564-568`（task 转换表"任意 → planning-done"）
- **Dimension**: 2 sub_state vs task_state 边界 + 11 recovery
- **Issue**:
  - planning-review §5 Step 5 顺序：先 `update --event review-passed`（改 sub_state），**再**逐 task `update --task Tn --status planning-done`。
  - 假设 5 个 task：第 1、2 个成功，第 3 个失败（如磁盘锁竞争 / 校验失败）。结果：sub_state==review-passed 但只有 2 个 task 注册。
  - §9 Recovery：「某个 update --task Tn --status planning-done 失败 | 停止后续 task update；报告具体 Tn；不要手工补 progress.md」**没有说明**：
    - (i) 重 invoke planning-review 时如何区分"已注册的 task 跳过"与"全部回滚重做"；
    - (ii) 是否需 retry 失败 task 而不重走 review；
    - (iii) sub_state 已经 review-passed，重 invoke 触发的"§2 入口要求 sub_state=in-review"已不满足，怎么续？
- **Impact**:
  - Task 6 实现 planning-review 调用层时，对此中断场景没有清晰 idempotent 策略，容易写出非幂等 recovery；agent 中断后摸不清如何继续。
  - 实际可能导致：人工编辑 progress.md（已被 Forbidden 禁止），或 reviewer 误重发 `review-passed` event（已是 review-passed，state machine reject）。
- **Recommendation**:
  - 选 **(a)**：planning-review §5 Step 5 与 §9 recovery 增加幂等性说明：「重 invoke 触发时若 progress.md sub_state 已 == review-passed 但部分 task 未注册（query development_state.task_states），跳过 review 步骤，直接按 breakdown.md task 列表 retry 未注册 task 的 `update --task Tn --status planning-done`；progress.py update --task 自身已是幂等（已 planning-done 重设无副作用）」。
  - 同时 §2 When to Invoke 加一条 reentry 入口：「`sub_state == review-passed` 但 development_state.task_states 不完整时，本 skill 可被重 invoke 仅做 task registration retry」。
  - 备选 **(b)**：要求 progress.py 提供 batch task registration / atomic multi-task update 命令一次性原子注册。**不推荐**：跨 batch 改动大，且 Stage 4 task 数量和 timing 不固定，原子化负担大。

### Medium 2: validate.py file 与 task registration 的"chicken-and-egg"被错误暗示存在

- **Location**: `skills/development-planning-write/SKILL.md:159-160`（§5 关键约束第 2 条）, `skills/development-planning-write/SKILL.md:233-234`（§10 Task registration note）, `skills/development-planning-review/SKILL.md:189-191`（§10 Task registration note）
- **Baseline Reference**: `skills/doc-guardian/SKILL.md:175-187`（§5.1 8 类校验，class 8 仅 cross-file）, `skills/workflow-protocol/references/command-reference.md:146`（v0.6 F14：update --event 不自动 validate；class 8 只在 advance 跑）, `skills/doc-guardian/references/frontmatter-schema.md:549`（不变量"per-task doc 的 task_id 必须在 progress.md task_states 中存在"）
- **Dimension**: 4 doc-guardian 一致性 + 5 planning pair 可实现性
- **Issue**:
  - planning-write §5 Step 4 跑 `validate.py file detailed_design.md`。此时 task_id 尚未在 progress.md task_states 注册（planning-done 是首次注册入口）。
  - planning-write §5 line 159-160 措辞："如果 validate.py 因 task registration 尚未实现而拒绝'task_id 不在 progress.md task_states'，不得手工改 progress.md；应升级实现层修 progress.py update --task planning-done 的原子注册/校验逻辑"——**这暗示 validate 会拒绝**。
  - 但 doc-guardian SKILL.md §5.1 已明确 class 8 (Consistency with progress.md) 仅 `validate.py consistency` 跑（cross-file 重），`validate.py file` 只跑 class 1-7（path / naming / frontmatter schema / format / cross-reference / change log / id uniqueness）。
  - 所以 `validate.py file detailed_design.md` 本身不会因"task_id 不在 progress.md"而失败。frontmatter-schema.md §8 的不变量是**整个系统**的不变量，由 advance 时 `validate.py consistency` 兜底。
  - 当前措辞会让 implementer 误以为 validate.py file 需校验 task_id 存在性，引入不必要的 cross-file 依赖。
- **Impact**:
  - Task 6 实现 doc-guardian validate.py 时可能误把 class 8 加进 file 模式（违反 round 4 M4 边界）；或 implementer 增加额外 task pre-registration 步骤导致 chicken-and-egg。
  - Reviewer 易把假 chicken-and-egg 当真问题，错误升级。
- **Recommendation**:
  - planning-write §5 line 159 改写为："`validate.py file` 只跑 class 1-7（事实源 doc-guardian SKILL.md §5.1），不校验 task_id 是否在 progress.md task_states 中；class 8 由 `validate.py consistency` 在 advance 时执行，那时 task 已注册。Task 6 实现 progress.py update --task Tn --status planning-done 时必须保证 detailed_design.md 已存在 + task_id 与 breakdown.md task table / 路径 tasks/Tn/ 一致；该原子校验是 progress.py 的责任，不在 validate.py file。"
  - planning-write §10 与 planning-review §10 的"Task registration note"同步修订，删除"validate 因 task registration 拒绝"的暗示。

### Medium 3: Stage 4 advance 的 C 维度复合判定未在 6 SKILL.md 中明确

- **Location**: `skills/development-planning-review/SKILL.md:131-141`（§6 Stage Done 表），`skills/development-test-review/SKILL.md:153-161`（§6），`skills/development-code-review/SKILL.md:155-162`（§6）
- **Baseline Reference**: `skills/workflow-protocol/SKILL.md:170-178`（§5.1 Stage 4 行 C=review-passed），`skills/workflow-protocol/SKILL.md:180-195`（§5.2 task 子状态序列）, `skills/doc-guardian/references/frontmatter-schema.md:215-264`（三态 review report 不变量）
- **Dimension**: 1 spec 一致性 + 4 doc-guardian
- **Issue**:
  - workflow-protocol §5.1 Stage 4 行 C 列写"review-passed"。
  - 但 Stage 4 实际 C 维度是**复合**：(i) `development-planning-review` global event review-passed；(ii) 每 task `test_review_report.md review_status: pass`；(iii) 每 task `code_review_report.md review_status: pass`。
  - 6 个 SKILL.md 各自只声明本 skill 贡献片段：planning-review §6 "C 直接 (planning review-passed)"；test-review §6 "test-done 转移要求 review_status: pass"；code-review §6 "code-review-passed 要求 review_status: pass"。
  - **没有**任一处说明"Stage 4 advance 的 C 维度由 planning + test + code 三层 review pass 共同构成"，也没 cross-link 到 workflow-protocol §5.2 表。
- **Impact**:
  - Task 6 实现 progress.py update --advance 时，可能误读 §5.1 表 C 列为"只看 planning review-passed"（最近一轮）。实际行为会被 task state machine 强制（advance 也要求 task 全部 verified），最终结果正确，但路径绕远。
  - 维护者更难理解 batch 3b 设计意图；后续 batch 3c testing-review 也需对应处理。
- **Recommendation**:
  - planning-review §6 增加一行说明："Stage 4 C 维度复合判定 = (本 skill 输出 review-passed) + (each task test_review_report `review_status: pass`) + (each task code_review_report `review_status: pass`)，详见 workflow-protocol §5.2 task 子状态序列。本 skill 仅贡献 planning 子层。"
  - test-review §6 加一行："Stage 4 C 维度的 test 子层由本 skill 贡献（每 task test_review_report `review_status: pass`），与 planning review 和 code review 共同构成 workflow-protocol §5.1 Stage 4 C 维度。"
  - code-review §6 类似。

### Medium 4: test-review / code-review 没显式声明 review_iteration 不适用 task-level review

- **Location**: `skills/development-test-review/SKILL.md:34-42`（§2 When to Invoke）, `skills/development-code-review/SKILL.md:32-50`（§2）
- **Baseline Reference**: `skills/workflow-protocol/SKILL.md:253-261`（§8 Review Loop，cap 7 仅 global review_iteration），`skills/workflow-protocol/references/command-reference.md:111-119`（§2.1 review_iteration += 1 仅在 review-issues event）
- **Dimension**: 12 simplicity / 术语 + 2 sub_state vs task_state
- **Issue**:
  - planning-review §2 显式列 `review_iteration: 0-7`，§8 Forbidden 第 7 条"在 review_iteration > 7 时继续 issues-found update"。
  - test-review / code-review 是 per-task three-state report 循环，**不**走 global review_iteration（review_iteration += 1 由 `--event review-issues` 触发，但 test/code review 用 `update --task Tn --status test-revising / code-revising`，不发 global event）。
  - 但 test-review §2 / code-review §2 没有明确声明这一点。
- **Impact**:
  - implementer 可能误以为 test/code review 与 planning review 共享 global review_iteration counter，给 7 次循环加保护，错误 reject test-revising / code-revising 循环。
  - 也可能误把同一计数应用于多个 task review，逻辑混乱。
- **Recommendation**:
  - test-review §2 和 code-review §2 各加一行 note："本 skill 不使用 global review_iteration（task-level three-state report 循环不计入 §8 Review Loop cap 7）；若 test/code review 在同一 task 上反复 fail，需要 break loop 时按 Recovery on Failure 升级人介入。"
  - 同时 planning-review §9 recovery 行加注："review_iteration cap 7 仅适用 planning global review；test/code review 由 task-level state machine 控制循环。"

### Medium 5: 三态 report / verification-result 不需 Pending Changes 章节的边界没明确

- **Location**: `skills/development-test-write/SKILL.md:88-110`（§4 skeleton frontmatter）, `skills/development-test-write/SKILL.md:131-134`（§5 Step 3）, `skills/development-code-write/SKILL.md:81-123`（§4.2 / §4.3）, `skills/development-test-review/SKILL.md:67-110`（§4.1 / §4.2）, `skills/development-code-review/SKILL.md:67-110`（§4.1 / §4.2）
- **Baseline Reference**: `skills/doc-guardian/references/change-log-format.md:9-26`（§1 适用 doc 类型表：test-review-report / code-review-report / verification-result 全部"一次性产出，不需 change log"）
- **Dimension**: 4 doc-guardian 一致性
- **Issue**:
  - change-log-format.md §1 表明三态 review report 与 verification-result **不需** Pending Changes / Change Log 章节（一次性 doc）。
  - 但 6 SKILL.md 没明确陈述"创建 skeleton 时不要加 Pending Changes / Change Log 章节"。test-write §4 列 skeleton frontmatter 但不说 body 是否需 Pending Changes；code-write §4.2 / §4.3 类似；test-review §4.1 / §4.2 列 frontmatter 修改字段但没说不写 Change Log。
  - implementer 可能：
    - (i) 误把 detailed_design.md 增量类 doc 的 4 步流程套用到 review report skeleton（加 Pending → promote → validate）；
    - (ii) 不加，但 reviewer 不确定是否有遗漏。
- **Impact**:
  - 若误加，validate.py 类 6 通过（章节存在不报错），但增加无意义维护负担。
  - 若 implementer 多次踩坑会导致 batch 3c 实现拖延。
- **Recommendation**:
  - test-write §4 创建 skeleton 段落加注："`test_review_report.md` 是一次性 doc（事实源 doc-guardian/references/change-log-format.md §1），**不需** Pending Changes / Change Log 章节；body 直接放 review 维度待填字段即可。"
  - code-write §4.2 / §4.3 同步加注（code_review_report 与 verification_result 都是一次性 doc）。
  - test-review / code-review 在 §5 Procedure 也提一行"本 skill 不操作 Pending Changes / Change Log 章节"避免与 planning review 混淆。

### Medium 6: Code-write 职责拆 7 项混合 code write 与 verification submode 表述不清

- **Location**: `skills/development-code-write/SKILL.md:16-25`（§1 职责 7 项）
- **Baseline Reference**: 本 skill 自身
- **Dimension**: 12 简洁度 + 7 code pair 可实现性
- **Issue**:
  - §1 职责 7 项：(1)-(4) 描述 code write submode；(5)-(7) 描述 verification submode。两类职责混在一个列表中，没有 sub-section 标记。
  - description 行确实提及"两类职责"，但 §1 表没把(1)-(4)（code-write）与 (5)-(7)（verification）分开。
  - §3 表分了 5 个 mode（Normal / Revise / Bug Fix / Verification / Verification Retry），但 §1 未对齐。
- **Impact**:
  - implementer 起骨架时易误读为单 mode 7 项任务，导致 code-write 与 verification 边界模糊（如把 verification fail 的 retry 当作 code-write Step 6）。
  - 后续 batch 3c testing-write 若类似分两 submode（例如 prep + procedure），缺一致命名 pattern。
- **Recommendation**:
  - §1 职责表分两组：「Code Write Submode (4 项)」+「Verification Submode (3 项)」。
  - 也可在每条尾部标 [code]/[verification]。

### Low 1: planning-write §5 标题"4-Step Standard Procedure"实际 5 步

- **Location**: `skills/development-planning-write/SKILL.md:128`
- **Dimension**: 12 simplicity
- **Issue**: §5 标题"4-Step Standard Procedure"，但实际步骤是 Step 1 / 2 / 3 / 4 / 5（写、Pending、promote、validate、submit review）。
- **Impact**: 文档可读性。
- **Recommendation**: 标题改"5-Step Standard Procedure"或简化为"Standard Procedure"。

### Low 2: planning-review §4.1 / §5 Step 5 顺序约束与 §9 recovery 没显式 cross-link

- **Location**: `skills/development-planning-review/SKILL.md:79-83`, `skills/development-planning-review/SKILL.md:128-129`, `skills/development-planning-review/SKILL.md:168-174`
- **Dimension**: 12 cross-reference + 11 recovery
- **Issue**: §5 Step 5 强调"必须先 review-passed 记录 planning review 通过，再置 task planning-done"，§4.1 也按此顺序，但 §9 recovery 表对"某个 update --task ... planning-done 失败"的修复没回指 §5 顺序约束。
- **Impact**: trivial。
- **Recommendation**: §9 该行末加"（参 §5 Step 5 顺序约束）"。

### Low 3: test-write §4 / code-write §4.2 skeleton frontmatter 未列 doc 自身 status: draft（实际有但隐藏在示例 yaml 第 3 行）

- **Location**: `skills/development-test-write/SKILL.md:88-108`, `skills/development-code-write/SKILL.md:84-105`
- **Baseline Reference**: `skills/doc-guardian/references/frontmatter-schema.md:217-219`（skeleton 阶段 doc 自身 status: draft）
- **Dimension**: 4 doc-guardian 一致性
- **Issue**: skeleton frontmatter 示例中包含 `status: draft`，但 SKILL.md 没在散文中强调 doc 自身 status 是 draft、与 review_status: pending 是两个独立字段（不变量见 frontmatter-schema.md §3.3 三态 report skeleton）。implementer 可能混淆 doc.status 与 review_status。
- **Impact**: trivial。
- **Recommendation**: §4 skeleton 段加一行注："注：`status: draft` 是 doc 自身生命周期状态；`review_status: pending` 是 review 三态结果。两字段独立由不同 owner 写：doc.status 由 doc-guardian status-transition helper（Gap-2）维护；review_status 由对应 review skill 写。"

### Low 4: test-write §3 已声明"src/不在 doc-guardian 管辖"；code-write 缺类似声明

- **Location**: `skills/development-code-write/SKILL.md:74-80`（§4.1 source output 段）
- **Baseline Reference**: `skills/doc-guardian/references/directory-layout.md:184-191`（§4 不在 doc-guardian 管辖的目录）
- **Dimension**: 4 doc-guardian 一致性
- **Issue**: test-write §3 line 73 明确声明"tests 目录不在 doc-guardian 管辖；quality gate 由 test_review_report.md 和 development-test-review 承担"。code-write §4.1 没同等声明 src/ 不在 doc-guardian 管辖、quality gate 由 code review 承担。
- **Impact**: trivial。
- **Recommendation**: code-write §4.1 加一行："`src/` 不在 doc-guardian 管辖（事实源 doc-guardian/references/directory-layout.md §4）；source quality gate 由 `code_review_report.md` 与 development-code-review 承担；verification execution 由本 skill verification submode 承担。"

### Low 5: 术语 "claim task" 首次出现未定义

- **Location**: `skills/development-test-write/SKILL.md:48`（§2 入口表注），`skills/development-code-write/SKILL.md:38`
- **Dimension**: 12 terminology
- **Issue**: 两处用 "claim task" 描述把 task state 推进到 in-progress 子状态（test-writing / code-writing），首次出现没定义。可能让 implementer 误以为是某种锁机制。
- **Impact**: trivial；上下文可推断。
- **Recommendation**: 首次使用时加括注："（claim task = 把 task state 从 `planning-done` 推到 `test-writing`/从 `test-done` 推到 `code-writing`，用 progress.py update --task；不是文件锁）"。

### Low 6: test-review §3 维度 7 与 test-write §7 Bug Flow re-entry 缺 cross-link

- **Location**: `skills/development-test-review/SKILL.md:64`（维度 7 Bug Flow Regression）, `skills/development-test-write/SKILL.md:158-163`（§7 Bug Flow Test Fix mode）
- **Dimension**: 8 Bug Flow re-entry + 12 cross-reference
- **Issue**: test-review §3 维度 7 提及"BUG 未被测试覆盖"作为 blocking condition，但没回指 test-write §7 / §3 Bug Flow Test Fix mode；implementer 跨 skill 阅读时需自己推导。
- **Impact**: trivial。
- **Recommendation**: test-review §3 维度 7 行加 cross-ref："（详见 development-test-write §7 Bug Flow Re-entry）"。code-review §3 维度 8 同样可加 cross-ref 到 code-write §7。

### Low 7: tests/src diff 范围 convention 缺失

- **Location**: `skills/development-test-review/SKILL.md:130-138`（§5 Step 2）, `skills/development-code-review/SKILL.md:131-138`（§5 Step 2）
- **Dimension**: 9 task-bounded safety
- **Issue**: review skill 需读 "tests diff/files for this task" / "source diff/touched files"，但 SKILL.md 没说明 implementer 如何确定 diff 范围（git diff vs detailed_design.md "Files / Modules to Touch" vs breakdown.md task ownership map）。
- **Impact**: trivial；可 implementer-defined。但 batch 3b 设计目标是"按图施工不歧义"，建议给 convention。
- **Recommendation**: 两个 review skill §5 Step 2 加一行："review 的 file scope 以 `detailed_design.md` Files / Modules to Touch 章节 + `breakdown.md` task ownership map 为基准，可结合 git diff 取证 actual delta；跨 scope 改动须按维度 9 task-bounded 列为 finding。"

### Low 8: planning-write §3 Bug Flow Replan vs Direct Route 关系不清

- **Location**: `skills/development-planning-write/SKILL.md:74-83`
- **Dimension**: 8 Bug Flow re-entry
- **Issue**: §3 表列 Bug Flow Replan 与 Bug Flow Direct Route 是平行还是顺序（先 try direct 不通 → replan）？看上下文是平行（按 BUG 是否能精确定位 task + 是否需 design 改动），但表格没显式说"二选一"。
- **Impact**: trivial。
- **Recommendation**: §3 表上方加注："Bug Flow Replan 与 Bug Flow Direct Route 是**平行二选一**：判别 = (BUG body Affected Task(s) 是否完整 + 是否需修 detailed_design / DAG)；都需 → Replan；都不需 → Direct Route。"

### Low 9: Bootstrap "auto advance" 风险术语 6 SKILL.md 措辞不统一

- **Location**: `skills/development-planning-write/SKILL.md:72`（"Stage 4 特例"）, `skills/development-planning-review/SKILL.md:143`（同），`skills/development-test-write/SKILL.md:52`（同），`skills/development-test-review/SKILL.md:45-46`, `skills/development-code-write/SKILL.md:55`, `skills/development-code-review/SKILL.md:50-51`
- **Dimension**: 12 terminology / 一致性
- **Issue**: 6 个 SKILL 都有"Stage 4 特例"段落警告 planning review-passed 后不要因 sub_state==review-passed 自动 advance。但措辞各自不同（部分说"不要因此自动 advance"、部分说"Bootstrap 不得在 planning review-passed 后立即调用 progress.py update --advance"、部分说"不得因此调用全局 advance"）。
- **Impact**: trivial；语义一致。
- **Recommendation**: 统一为同一句："**Stage 4 特例**：planning review-passed 后 global `sub_state` 可能停在 `review-passed`，但 Stage 4 后续执行由 `development_state.task_states[Tn]` 驱动；Bootstrap / caller 不得因 `sub_state==review-passed` 调用 `progress.py update --advance`，advance 仅在 all task verified 后允许。" 或在 batch 3b reference 拆分时统一抽公共 note。

---

## Cross-Skill Consistency Check

按 caller → callee 列表（任一节点不含 H 级 finding 的视为 ✓）：

| Caller | Callee | 一致性 | 评论 |
|--------|--------|--------|------|
| `development-planning-write` | `development-planning-review` | ✓ | write-complete / review-issues / review-passed event 全程互锁；revise after issues-found 路径清晰 |
| `development-planning-review` | `development-test-write` | ⚠ M1 | review-passed 后 task registration 时序 + partial recovery 不充分（M1）；test-write §2 入口"planning-done"是 review-passed 后才到，contract 一致 |
| `development-planning-write` | `development-test-write` (Bug Flow Direct Route) | ❌ H1 | 当 affected task verified 时无回退路径，Direct Route 不可达 |
| `development-planning-write` | `development-code-write` (Bug Flow Direct Route) | ❌ H1 | 同上，verified task 路径不可达 |
| `development-test-write` | `development-test-review` | ✓ | pending skeleton + revise 重置 + transition `test-writing → test-review` 全闭环 |
| `development-test-review` | `development-test-write` | ✓ | fail → test-revising → test-write Change Mode → 重置 pending → 重提 |
| `development-test-review` (pass) | `development-code-write` | ✓ | test-done 是 code-write 的 `test-done` 入口；code-review §2 line 47 检查 test-done 前置 |
| `development-code-write` | `development-code-review` | ✓ | pending skeleton + revise 重置 + transition `code-writing → code-review` 全闭环；code-review §5 Step 2 检查 test_review_report 必须 pass |
| `development-code-review` (pass) | `development-code-write` (verification submode) | ⚠ H2 | code-review-passed → verifying transition 存在；但 verifying → code-revising 回退缺失（Gap-3） |
| `development-code-write` (verification fail) | `development-code-write` (Verification Retry) | ❌ H2 | Gap-3 未补，retry 不可达 |
| 6 dev skills | `workflow-protocol`/progress.py | ⚠ M2 | task registration validate 时序的措辞误导（M2） |
| 6 dev skills | `doc-guardian`/validate.py / changelog.py | ⚠ M5 | 三态 report / verification-result 不需 Pending/Change Log 边界没明确 |
| 6 dev skills | `bug-triage` | ⚠ H1 | BUG body Affected Task(s) 作为事实源 OK；但 verified task rollback 缺路径 |
| `bug-triage`（root_cause==development）| `development-planning-write` | ✓ | bug-triage SKILL §3.4 + planning-write §7 一致：BUG body Affected Task(s) 是事实源；多 task / unable to localize 处理一致 |
| 6 dev skills | batch 3a (`prd-write`/`srs-write`/`architecture-write`) | ✓ | upstream artifacts 路径与 frontmatter-schema 一致；本批没误改上游 doc owner；§9 recovery 涉及"上游 mismatch"时 reject + 升级 stage 的措辞与 batch 3a 一致 |

**一致性热点**：

1. **Stage 4 sub_state == review-passed 警告**：6 SKILL.md 都有"Stage 4 特例"段，措辞不统一（L9）；语义一致。
2. **task ID 格式**：6 SKILL.md 都用 `T<n>` / `Tn`，与 frontmatter-schema.md §4.4 `T\d+` 一致 ✓。
3. **review_status 三态术语**：6 SKILL.md 全程 hyphen `pending|pass|fail`；与 frontmatter-schema.md / change-log-format.md 一致 ✓。
4. **`update --event` 4 白名单使用**：planning-write `write-complete`（§5 Step 5）、planning-review `review-passed` / `review-issues`（§4 / §5 Step 5）；6 个 dev skill **没有**误用 `human-confirmed`（Stage 4 无人 gate） ✓。
5. **task-level 转换**：test/code 系列全部 `update --task Tn --status <new>`，**没有**误用全局 event；与 batch 3a round 3 review L1 (advisory `issues-found` event) 教训对齐——planning-review §5 Step 5 用 `--event review-issues` 而非 `issues-found` ✓。
6. **Forbidden Actions "approved"**：6 SKILL.md 都禁止输出 approved（Stage 4 无 D 维度） ✓。
7. **Stage 4 verification fail 不进 bug-triage**：code-write §1 line 31 + §8 第 7 条 ✓；bug-triage SKILL.md §2.3 不会被 invoke 时机已含此约束。

---

## Task State Machine Verification

逐条对照 `skills/workflow-protocol/references/command-reference.md` Stage 4 task state 转换表（line 564-580）：

| 事实源 transition | batch 3b SKILL.md 覆盖位置 | 状态 |
|-------------------|----------------------------|------|
| `任意 → planning-done` | planning-review §4.1 / §5 Step 5；planning-write §3 task ID 规则 | ✓ |
| `planning-done → test-writing` | test-write §2 入口表 + §5 Step 1 | ✓ |
| `test-writing → test-review` | test-write §5 Step 5 | ✓ |
| `test-review → test-revising` | test-review §4.2 / §5 Step 5 fail 分支 | ✓ |
| `test-review → test-done` | test-review §4.1 / §5 Step 5 pass 分支；§6 硬条件 | ✓ |
| `test-revising → test-review` | test-write §3 Resume Write / Review Revise；§5 Step 5 重提 | ✓ |
| `test-done → code-writing` | code-write §2 入口表 + §5.1 Step 1 | ✓ |
| `code-writing → code-review` | code-write §5.1 Step 5 | ✓ |
| `code-review → code-revising` | code-review §4.2 / §5 Step 5 fail | ✓ |
| `code-review → code-review-passed` | code-review §4.1 / §5 Step 5 pass；§6 硬条件 | ✓ |
| `code-revising → code-review` | code-write §3 Code Revise；§5.1 Step 5 重提 | ✓ |
| `code-review-passed → verifying` | code-write §5.2 Step V1 | ✓ |
| `verifying → verified` | code-write §5.2 Step V4 pass 分支 | ✓ |
| **`verifying → code-revising`（缺）** | **未覆盖** | ❌ Gap-3（H2） |
| **`verified → test-revising`（Bug Flow rollback，缺）** | **未覆盖** | ❌ Gap-4（H1） |
| **`verified → code-revising`（Bug Flow rollback，缺）** | **未覆盖** | ❌ Gap-4（H1） |
| **`code-review-passed → code-revising`（Bug Flow rollback，缺）** | **未覆盖** | ⚠ Gap-4 衍生 |

**结论**：batch 3b 6 SKILL.md 对**当前转换表**覆盖完整、无误用；**真实 gap** 是转换表本身缺 Gap-3 和 Gap-4 两族 transition。Task 6 实现 progress.py 前必须先扩。

**没有发现的误用**：
- 6 SKILL.md **没有**任何处用全局 review event（`review-passed` / `review-issues`）推进 task 状态。
- 6 SKILL.md **没有**直接调 `update --advance`。
- 6 SKILL.md **没有**手工编辑 progress.md 的暗示。

---

## Three-State Review Report Verification

按 frontmatter-schema.md §3.3 三态不变量（line 219-264）+ change-log-format.md §1（一次性 doc）逐条核对：

| 不变量 / 步骤 | test_review_report.md | code_review_report.md | 状态 |
|---------------|------------------------|------------------------|------|
| skeleton 由 write skill 创建 | test-write §4 / §5 Step 3 | code-write §4.2 / §5.1 Step 3 | ✓ |
| skeleton `review_status: pending`（**不是 pass**）| test-write §4 line 104 | code-write §4.2 line 101 | ✓ |
| skeleton counts 全 0 / blocking_findings_count: 0 / max_severity: low | test-write §4 yaml | code-write §4.2 yaml | ✓ |
| skeleton doc.status: draft | test-write §4 yaml line 92 | code-write §4.2 yaml line 89 | ✓ |
| revise 前重置 stale fail/pass → pending | test-write §3 Review Revise / Bug Flow + §5 Step 3 + §8 Forbidden 第 4 条 | code-write §3 Code Revise + §5.1 Step 3 + §8 暗含 | ✓ |
| 仅 review skill 可写 review_status: pass\|fail | test-review §4.1 / §4.2 + §8 Forbidden | code-review §4.1 / §4.2 + §8 Forbidden | ✓ |
| pass 强制 blocking_findings_count == 0 | test-review §4.1 + §6 硬条件 + §8 Forbidden 第 3 条 | code-review §4.1 + §6 + §8 Forbidden 第 3 条 | ✓ |
| pending/fail 都不能推进 test-done / code-review-passed | test-review §6 + state machine 强制 | code-review §6 + state machine 强制 | ✓ |
| review report 路径 per-task | test-write §4 / test-review §4 / code-write §4.2 / code-review §4 全部 `docs/release{x.y}/development/tasks/T<n>/...md` | 同 | ✓ |
| 一次性 doc，**不需** Pending/Change Log | **未明确陈述**（M5） | **未明确陈述**（M5） | ⚠ M5 |
| Stage 4 task `test-done` / `code-review-passed` 转移强制校验 review_status: pass | progress.py 状态机 + test-review §6 / code-review §6 互锁 | 同 | ✓ |
| Bug Flow 重置 stale 后必经 review pass 不可 bypass | test-write §7 Bug Flow Test Fix → 重置 pending → 仍 review；code-write §7 → 重置 pending | ✓ | ✓ |

**结论**：三态 report 防 bypass 设计在 6 SKILL.md 中**完整且健壮**，唯一改进点是 M5（一次性 doc 边界明确化，不阻塞）。

---

## Bug Flow Development Re-entry Assessment

按评审目标 §10 维度 8 + 重点排查"Bug Flow direct route" / "Multiple affected tasks" 综合评估：

| 子项 | 状态 | 位置 |
|------|------|------|
| `root_cause==development` 入口与 bug-triage / root-cause-rubric 一致 | ✓ | planning-write §2 + §7；test-write §2 Bug Flow 入口；code-write §2 Bug Flow 入口；与 bug-triage SKILL.md §3.2 + §3.4 + root-cause-rubric.md §2.4 一致 |
| BUG body `Affected Task(s)` 作为事实源 | ✓ | planning-write §7 line 183；test-write §2 Bug Flow 入口；code-write §2 Bug Flow 入口；与 bug-triage SKILL.md §3.4 + triage-decision-tree §2.2 一致 |
| 无法定位 task 时由 planning-write 重 breakdown | ✓ | planning-write §7 第 4 决策项；与 root-cause-rubric.md §4.8 一致 |
| 测试遗漏 vs source bug vs design 缺口 路由 | ✓ | planning-write §7 决策树（4 选项）；test-write §3 Bug Flow Test Fix；code-write §3 Bug Fix；test-write §7 / code-write §7 |
| development Change Mode 不关闭 Bug Flow；必须 Stage 5 retest | ✓ | planning-write §7 第 5 项；test-write §7；code-write §7 |
| Stage 4 自验证 fail 不走 bug-triage | ✓ | code-write description 行 + §1 line 31 + §3 verification 边界 + §8 Forbidden 第 7 条 |
| 多个 affected task 处理 | ✓ | test-write §9 "Bug Flow 指向多个 task | 逐 task 处理"；code-write §9 同 |
| Bug Flow Direct Route（已标清 task 无需改 design） | ❌ H1 | planning-write §3 Direct Route mode 没处理 verified task rollback；transition gap |
| Bug Flow Replan（需重新 breakdown）| ✓ | planning-write §3 Replan mode + §7 第 3 决策项 |
| 跨 release 回归测试 | N/A | 不在本批 6 个 skill 责任范围（属 testing-write） |

**关键发现**：除 H1 外，Bug Flow re-entry **设计完整且与 batch 2 bug-triage 闭环对齐**。BUG body `Affected Task(s)` 这一事实源约定在 6 个 SKILL.md 与 bug-triage / root-cause-rubric 之间无歧义。

**缺口**：H1 暴露一个完整闭环漏洞——已 verified task 的 BUG 修复路径不可达。这是 Stage 5 testing 测出 bug 时**最常见**场景（Stage 4 既然走完，task 必然 verified），所以这是 development root cause Bug Flow 的核心阻塞，必须在 Task 6 前修。

---

## Design Gap Resolution

### Gap-1（沿用）：`review-passed → revising` 全局 transition 缺失

- **状态**：仍 open（已在 batch 3a round 3 闭环时声明，本批继承）。
- **batch 3b 检查**：6 SKILL.md **没有**任何处误调不存在的全局 event。planning-review 仅用 `review-passed` / `review-issues`；test/code 系列使用 task-level transition。**无回归**。
- **结论**：本批不解决，沿用旧 status。

### Gap-2（沿用）：doc frontmatter status mutation helper 未实现

- **状态**：仍 open（owner = `doc-guardian status-transition helper` / task-aware variant）。
- **batch 3b 检查**：
  - planning-write §10 / planning-review §10 / test-write §10 / test-review §10 / code-write §10 / code-review §10 都明确 owner = doc-guardian status-transition helper / task-aware helper，与 batch 3a 闭环一致。
  - test-review §5 Step 4 注："status frontmatter 由 doc-guardian helper 最终同步；本 skill 只写 owned report 内容字段"——边界清晰。
  - code-review 同。
  - **没有**误要求 write/review skill 直接修改不属于自己的 frontmatter status，**没有**绕过 helper 的路径。
- **结论**：本批合规，无新动作。

### Gap-3（已声明）：verification fail 回退 transition 缺失

- **状态**：本批新声明（H2）。
- **评估 (a)(b)(c)**：见 H2 finding。
- **是否阻塞 Task 6**：是。
- **batch 3b SKILL.md 声明是否足够**：合格（明确 owner、明确禁止绕过、明确推荐 transition 候选）；与 Gap-2 同样级别。
- **推荐补的 transition**：`verifying → code-revising`，前置 `verification_result.md` 存在 + `verification_status: fail|partial`。

### Gap-4（本批新识别）：Bug Flow 中 verified task 回退 transition 缺失

- **状态**：本批新识别（H1）。Batch 3b SKILL.md 当前**未声明**此 gap，需补声明。
- **是否阻塞 Task 6**：是。这是 Bug Flow development root cause 最常见路径（Stage 5 测出 verified task bug）的核心阻塞。
- **推荐补的 transition**：
  - `verified → test-revising`（前置：BUG body Affected Task(s) 包含本 task；BUG.root_cause==development；BUG fix 涉及测试遗漏）
  - `verified → code-revising`（前置：同上；BUG fix 涉及 source bug）
  - `code-review-passed → code-revising`（衍生：极少数情况 BUG 在 verified 前介入 + code review 已 pass）
- **集成方式建议**：与 Gap-3 一并修——由 `progress.py bug-start --root-cause development` 在切 stage 时按 BUG body `Affected Task(s)` 自动回退 affected task。具体语义建议：
  - 解析 BUG body Affected Task(s)（list of `T<n>`）；
  - 对每个 affected task，按 BUG.body 中 `Affected Doc/Module` 是否包含 tests 决定回退到 `test-revising` 还是 `code-revising`；
  - planning-write 在 Bug Flow Replan 模式只新增/调整 task，不直接修改 task state（保持职责边界）。

**Gap 总结表**：

| Gap | 来源 | Batch 3b 处置 | Task 6 前置 |
|-----|------|---------------|-------------|
| Gap-1 | batch 3a round 3 沿用 | 沿用 open | 不阻塞骨架，可在 design proposal 升级周期处理 |
| Gap-2 | batch 3a round 3 沿用 | 沿用 open，本批已用 helper owner | 不阻塞骨架；Task 6 实现 doc-guardian status-transition helper 时一并补 |
| Gap-3 | 本批声明（H2 复核） | 声明 + 推荐 transition | **必须**先扩 command-reference Stage 4 转换表 |
| Gap-4 | 本批新识别（H1） | **需补声明** | **必须**先扩 command-reference Stage 4 转换表 + progress.py bug-start 行为 |

---

## Implementability Assessment

按 6 个 skill 列出 implementer 能否直接实现：

| Skill | 可实现性 | 关键模糊点 / 阻塞 |
|-------|---------|-------------------|
| `development-planning-write` | ⚠ 部分可实现 | (i) Bug Flow Direct Route verified rollback（H1）阻塞；(ii) M2 task validation 措辞误导；(iii) M1 partial registration recovery 不充分；(iv) L1 步骤数；(v) L8 mode 关系不清 |
| `development-planning-review` | ⚠ 部分可实现 | (i) M1 partial task registration recovery；(ii) M3 Stage 4 C 维度复合；(iii) M2 task registration note 误导 |
| `development-test-write` | ⚠ 基本可实现 | (i) M5 一次性 doc 边界；(ii) L5 claim task 术语；(iii) Bug Flow re-entry 在 H1 修后才能完整 |
| `development-test-review` | ✓ 基本可实现 | (i) M4 review_iteration 适用范围；(ii) L7 diff 范围 convention；(iii) L6 cross-link |
| `development-code-write` | ❌ 部分阻塞 | (i) H2 Gap-3 verification fail 回退；(ii) M6 职责拆分；(iii) M5 一次性 doc；(iv) Bug Flow re-entry 在 H1 修后才能完整 |
| `development-code-review` | ✓ 基本可实现 | (i) H2 awareness 已声明；(ii) M4 review_iteration；(iii) L4 src/边界；(iv) L7 diff 范围 |

**总体**：4/6 skill 可在简单 patch 后实现；**2/6 skill（planning-write、code-write）**因 H1/H2 阻塞，必须先在 workflow-protocol command-reference 补 Gap-3 + Gap-4 transition。

**需要 script 支持的点**：
- progress.py 应在 `update --task Tn --status planning-done` 时原子校验 detailed_design.md 存在 + task_id 与 breakdown.md task table / 路径 tasks/Tn/ 一致（M2 推荐位置）。
- progress.py `bug-start --root-cause development` 应解析 BUG body Affected Task(s) 自动回退 verified task（H1 推荐方案 b）。
- progress.py 应支持幂等 task registration retry（M1 推荐方案 a）：planning-review 重 invoke 时按 query 结果跳过已注册 task。
- doc-guardian validate.py 需明确 class 8 边界：仅 `validate.py consistency` 跑（M2 已在事实源说明，仅 SKILL.md 措辞需修）。

**需要在 workflow-protocol 后续升级补的点**：
- command-reference Stage 4 task state 转换表加 Gap-3 (`verifying → code-revising`) + Gap-4 (`verified → test-revising` / `verified → code-revising` / `code-review-passed → code-revising`) 共 4 条 transition。
- `progress.py bug-start` 增加 affected task auto-rollback 行为；schema 不变。

---

## Positive Notes

1. **三态 review report 设计闭环度极高**：6 SKILL.md 的 pending skeleton + revise 重置 + sole owner of pass/fail + state machine 强制 review_status==pass 互锁，防 bypass 路径完整。
2. **task-bounded 边界清晰**：test-write §3 / §8 / §9 + code-write §4.1 / §8 都强调"不 revert 其他 task/agent changes"；多 task 并发场景设计合理。
3. **Stage 4 sub_state 与 task_state 边界**：6 SKILL.md 都有"Stage 4 特例"段落警告 Bootstrap 不要因 sub_state==review-passed 触发 advance，与 workflow-protocol §5.2 一致。
4. **Bug Flow re-entry 与 batch 2 bug-triage 闭环**：BUG body `Affected Task(s)` 事实源约定 + 多 task 处理 + 测试遗漏/source bug/design 缺口路由 全部对齐 bug-triage SKILL §3.4 + root-cause-rubric §4 series。
5. **Forbidden Actions 覆盖广**：6 SKILL.md 明确禁止的常见 bypass（直接改 progress、绕过 validate/changelog、write skill 自评、review skill 改 source/test、bypass pending、未 pass 推进、Stage 4 输出 approved、verification fail 进 bug-triage）总数 ~50 条，无显著遗漏（除 M5 提到的边界）。
6. **Gap 处理风格延续 batch 3a**：Gap-2 owner 命名、helper 声明位置、声明边界与 batch 3a round 3 闭环格式一致。
7. **planning vs test/code event 边界**：planning 用 global event（`write-complete` / `review-issues` / `review-passed`），test/code 用 task transition（`update --task`），无任何处误用。

---

## Suggested Next Revision Order

按优先级排序（High first）：

1. **H1 Gap-4 声明**（patch ~30 行 / 3 文件）——在 planning-write §10 / test-write §10 / code-write §10 增 Gap-4 声明；planning-write §3 Bug Flow Direct Route 表加 verified rollback 注；与 H2 Gap-3 文风对齐。**必做**。
2. **H2 Gap-3 措辞最终化**（patch ~5 行 / 2 文件）——code-write §10 / code-review §10 已声明，可在文末补一句"推荐 transition: `verifying → code-revising`，前置 verification_result `verification_status: fail|partial`"明确推荐方案。可与 H1 同 patch。
3. **M1 partial task registration recovery**（patch ~15 行 / 1 文件）——planning-review §2 增 reentry 入口 + §5 Step 5 + §9 增幂等性说明。
4. **M2 validate.py file 边界澄清**（patch ~8 行 / 2 文件）——planning-write §5 line 159 + planning-write §10 + planning-review §10 改写"task registration note"。
5. **M3 Stage 4 C 维度复合判定**（patch ~6 行 / 3 文件）——planning-review §6 + test-review §6 + code-review §6 各加一行 cross-link。
6. **M4 review_iteration 不适用 task-level review**（patch ~4 行 / 2 文件）——test-review §2 + code-review §2 + planning-review §9 各加一行注。
7. **M5 一次性 doc 边界明确**（patch ~6 行 / 4 文件）——test-write §4 + code-write §4.2 / §4.3 + test-review §5 + code-review §5 各加一行注。
8. **M6 code-write 职责 7 项分两组**（patch ~10 行 / 1 文件）——code-write §1 加 sub-section 标记。
9. **L1-L9** 文档清理（合计 patch ~25 行 / 6 文件）——可在 batch 3c 起骨架时顺手修；不阻塞。

**预计 patch 总量**：High + Medium 部分 ~80 行 / 6 文件；可在 1 轮内完成；不需要架构层改动（Gap-3 / Gap-4 的 workflow-protocol 升级是 Task 6 前置，不属于 batch 3b 内 patch）。

---

## Recommendation

- **(B): 修后再评（再评 1 轮）**

**理由**：
- 1 个新 High（H1 Gap-4）尚未在 SKILL.md 声明，必须补声明后再进 batch 3c；这是 Bug Flow development re-entry 的核心闭环漏洞。
- H2 Gap-3 已声明，但与 H1 同源（都是 task transition 缺失），建议同 patch 同时收敛措辞。
- 6 个 Medium 中 M1/M2/M3/M4/M5/M6 都是描述/边界澄清，patch 体量小但分布广。
- Lows 总量 9 条，可顺手修。

**进 batch 3c 前置**：
1. 上述 H1 Gap-4 + H2 Gap-3 声明在 SKILL.md 中完成；
2. M1 / M2 / M3 / M4 / M5 / M6 6 个 Medium patch 完成；
3. （非阻塞）在 `docs/handoff/` 下记录 Task 6 实现 progress.py 时必须先补的 transition 列表（Gap-3 + Gap-4 合计 4 条 + 1 条 bug-start affected task auto-rollback 行为）。

**不推荐 (A) 的判据**：当前 finding 含 1 个未声明 New High（H1）+ 6 个 Medium，超出 (A) 阈值（"全部 Medium/Low 且数量 ≤ 3，或只有已声明 design gap 不阻塞骨架继续"）。即使 H2 是已声明 design gap，H1 不是；且 Medium 数量也超过 3。

**不推荐 (C) 的判据**：所有 finding 都不触及已闭环的架构层决策（authority hierarchy / Stage 4 task 状态机框架 / 三态 report 不变量 / Bug Flow 4 类根因路由）；Gap-3 / Gap-4 都是 transition 表补完整型 patch，不需要 design level 重做。
