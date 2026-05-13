# Task 6 Phase 1 Docs Alignment Review

**Review Target**: Task 6 implementation plan + workflow-protocol / doc-guardian references + related SKILL.md alignment
**Review Date**: 2026-05-07
**Reviewer**: Claude (claude-opus-4-7[1m])
**Baseline**: Task 5 accepted state (`docs/review/skill_set_batch3c_round2_review.md` 等 19 轮 review 闭环) + Task 6 prerequisites (`docs/handoff/task6_progress_py_prerequisites_20260506.md`)
**Recommendation**: **(A) accept and proceed to Phase 2 shared foundation implementation**
**Status**: findings: 0 High / 0 Medium / 3 Low; blockers: no

---

## Executive Summary

- Phase 1 docs alignment 已经把 Codex 在 prerequisites 文档中预留的 Gap-3 / Gap-4 / Gap-5 + `bug-rework` + `status_transition.py` 全部固化到 `command-reference.md` / `workflow-protocol/SKILL.md` / `doc-guardian/SKILL.md` / `change-log-format.md` / `testing-write/-review` / `scenario-dispatcher` 中；12 个子命令 / 4 个 event 白名单 / Stage 4 完整 task 转移表 / Bug Flow 4 类根因路由全部互相一致。
- Task 6 implementation plan (`docs/implementation/task6_plan_20260507.md`) 完整覆盖 4 大实现目标（progress.py / validate.py / changelog.py / status_transition.py）+ 文件写集 + 测试策略 + 7 阶段实现顺序，并显式声明 Out of Scope（AGENTS/CLAUDE/plugin metadata、Gap-1 reopen event、cryptographic hash-chain、自然语言语义评审）。Phase 1 → Phase 7 顺序与 prompt 要求逐项匹配。
- 16 个 stage SKILL.md 的 Gap-2 helper 文案已经全部统一为 `skills/doc-guardian/scripts/status_transition.py`，没有残留 "接口 TBD / batch upgrade / helper 接口待后续定义" 字样；event whitelist 里没有任何处用 `--event issues-found` 误调；Stage 6 / Stage 7 没有被本轮改动开口给 active Bug Flow 或 release-close 自动化。
- 仅发现 3 条 Low：均为 cross-doc cleanliness 问题（design proposal v0.5 仍说 11 个子命令；prerequisites §6 一句历史性 staging 文本在 Phase 1 后语境不一致；plan §6.2 Gap-4 step 3 措辞混淆 bug-start 与 bug-rework 的 mutation 责任）。3 条都不阻塞 Phase 2，可在 Phase 2 起骨架时顺手清理或在 Phase 7 docs polish 收敛。
- **结论：可以进入 Phase 2 shared foundation 实现**，无需再开 Phase 1 round 2。

---

## Findings

### Low: design proposal v0.5 与 spec 仍说 progress.py "11 个子命令"，与 12 命令 references 形成 cross-doc 不一致

- **Location**: `docs/design/skill_set_design_proposal_v0.5.md:277` / `:805` / `:909`
- **Issue**:
  - line 277: `### 4.4 scripts/progress.py 接口（v0.5 总 11 个子命令）`
  - line 805: `workflow-protocol — ... 11 个子命令：init / update / query / recover / release-close / release-start / bug-intake / bug-start / bug-close / incident-start / incident-resolve` — 明确列出 11 个名字，缺 `bug-rework`
  - line 909: `workflow-protocol（11 个子命令完整规范）`
  - 同时 `docs/workflow/workflow_specification_claude.md` 没有命令计数，但其 release-start `--scenario` 列举与新的 12 命令 references 在 cross-reference 上仍隐含 v0.5 baseline。
- **Impact**: 不阻塞 Phase 2 — Task 6 plan §1 Source References 和 SKILL.md Authority Hierarchy 都把 `command-reference.md` 与各 stage SKILL.md 列为事实源，implementer 不会读 design proposal 取命令清单。但当读者按 plan §1 第 10 项之外的"vertical SKILL"或自行打开 design proposal 时，会遇到 11 vs 12 的字面冲突，制造误读窗口（特别是 line 805 列了 11 个名字、缺 bug-rework，看起来像是 bug-rework 不存在的"权威否认"）。
- **Recommendation**:
  - 选项 A（最小）：在 design proposal v0.5 §4.4 / §11 / §15.1 三处加一条 v0.6 patch note：`v0.6 patch (2026-05-07): progress.py 子命令数 11 → 12，新增 bug-rework，详见 skills/workflow-protocol/references/command-reference.md §9 与 docs/handoff/task6_progress_py_prerequisites_20260506.md §6 Gap-5。`
  - 选项 B：把 `docs/implementation/task6_plan_20260507.md` §3.4 Reference Updates 表加一条 design proposal v0.5 三处 patch，作为 Phase 7 Documentation Polish 的明确 todo。
  - 任一即可，选项 A 信息密度更高、改动更小。

### Low: `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 line 100 仍说 "Before bug-rework exists"，与 Phase 1 后 references 已定义 bug-rework 的事实不一致

- **Location**: `docs/handoff/task6_progress_py_prerequisites_20260506.md:100`
- **Issue**: 当前文本：
  > Before `bug-rework` exists, active Bug Flow retest fail/partial must stop and escalate to user/Bootstrap. Do not create a second BUG for the same active issue, do not call `bug-start` again, do not call `bug-close`, and do not hand-edit `progress.md`.

  Phase 1 docs alignment 完成后，`bug-rework` 已经在 `command-reference.md` §9 完整定义、在 `workflow-protocol/SKILL.md` §2 / §4 / §6 / §11 多处出现、在 `testing-write/-review` §10 staging 引用。此句字面意思是"`bug-rework` 不存在"，与 references 实际状态不再吻合，会让新 implementer 误以为命令尚未定义。命令的脚本实现确实仍在 Phase 5/6，但语义上 prerequisites 文档 §5 Non-Bypass Rule 已经包含 bug-rework 边界（`docs/handoff/task6_progress_py_prerequisites_20260506.md:66`），§6 line 100 这条转述属于历史 staging 的残留。
- **Impact**: 不阻塞 Phase 2。`testing-write/SKILL.md:155` "若脚本尚未实现或前置不满足，停止并升级用户/Bootstrap" 已经把"脚本未实现"作为 caller-side defensive guard，行为路径正确。但 prerequisites 是 Task 6 plan §1 第 2 项 source reference，这条 stale text 会消耗读者注意力。
- **Recommendation**: 把该段改写为：
  > Until the `bug-rework` script lands in Phase 5/6, active Bug Flow retest fail/partial must stop and escalate to user/Bootstrap. The command is now fully specified in `skills/workflow-protocol/references/command-reference.md` §9; testing-write/-review must escalate when the command is unavailable or rejects, but must not create a second BUG, call `bug-start` again, call `bug-close`, or hand-edit `progress.md`.

  保留全部 5 条禁止行为，仅把"command 不存在"改为"script 未实现"，与 Task 6 implementation phasing 对齐。

### Low: `docs/implementation/task6_plan_20260507.md` §6.2 Gap-4 step 3 "set current stage to development/write" 措辞混淆 bug-start 与 bug-rework 的 mutation 责任

- **Location**: `docs/implementation/task6_plan_20260507.md:208`
- **Issue**: §6.2 Gap-4 Classification strategy step 3：
  > If missing or ambiguous, leave affected task unchanged, set current stage to `development/write`, and history must say that `development-planning-write` must replan/route. Do not guess.

  Gap-4 的两个触发命令是 `bug-start --root-cause development` 和 `bug-rework`（root_cause==development）。两者的标准 mutation 已经把 `current_stage` 设到 `development`、`sub_state` 设到 `write`（command-reference §8 line 358-368 / §9 line 408-419）。这意味着 step 3 的 "set current stage to development/write" 实际上就是命令 mutation 的副作用，不是 implementer 在 affected-task rollback 之外要单独执行的步骤。措辞读起来像是"额外动作"，可能让 implementer 在 bug-rework 触发时重复设置 current_stage / sub_state，或在 bug-start 触发时把"development/write"理解成新的 sub_state 命名。
- **Impact**: 不阻塞 Phase 2。command-reference §8 / §9 的精确 mutation 表是事实源，implementer 按 reference 即可正确实现；plan §6.2 的歧义只发生在 affected-task 分类不明确这一支路，且明确禁止猜测。但 Phase 6 实现 `bug-start` / `bug-rework` 时仍可能浪费 review 时间。
- **Recommendation**: 把 step 3 改写为：
  > 3. If `Affected Task(s)` is present but classification is ambiguous (no test-only/source-code language match), leave each affected task state unchanged. The standard `bug-start` / `bug-rework` mutation still routes `current_stage` to `development` and `sub_state` to `write`; no extra stage edit is required. Append a history entry stating that `development-planning-write` must replan/route. Do not guess.

  也可顺带把 step 4 中 "If `Affected Task(s)` is absent and no replan path is selected, reject" 与 step 3 的"leave unchanged + history says replan"拼接起来，明确两条 fallback 是 missing vs ambiguous。

---

## Checklist Results

| Area | Status | Notes |
|------|--------|-------|
| Task 6 implementation plan | ✅ | §1-§15 完整覆盖；4 大目标、文件写集（含 _shared 共享模块）、测试策略（unit + integration 含 Gap-3/4/5 + incident + release-start consume bugs）、Phase 1→7 顺序与 prompt 要求逐项匹配；§2.2 Out of Scope + §14 Open Decisions 显式标 Gap-1 deferred、AGENTS/CLAUDE/plugin metadata 延后、cryptographic hash-chain 延后；唯一一处措辞 Low 见 Findings LOW3 |
| progress.py command-reference alignment | ✅ | command-reference.md / workflow-protocol/SKILL.md / scenario-dispatcher/SKILL.md 全局 12；Bug Flow / terminal state / `--advance` artifact 来源 / event 白名单 / Stage 4 task 转移表 / 受保护字段 / Forbidden Actions 全部已加 `bug-rework`；只在 design proposal v0.5 baseline 残留 11 命令引用，见 LOW1 |
| bug-rework / Gap-5 | ✅ | command-reference §9 完整列 8 条前置 + 7 步 mutation + Rejected alternatives；workflow-protocol/SKILL.md §2 invocation matrix / §4 子命令清单 / §6 Bug Flow 闭环 / §11 Forbidden Action 第 8 条全部覆盖；testing-write §3 Mode 表 + §5.2 Case C + §10 Gap-5、testing-review §10 Gap-5 一致引用；与 prerequisites §6 内容相同（仅 line 100 staging wording 见 LOW2） |
| Gap-3 verification rollback | ✅ | command-reference 状态机表 line 645：`verifying → code-revising` 前置 `verification_status ∈ {fail, partial}`；明确"verification retry，不走 bug-triage"；plan §6.1 / §12.3 Test 3 都覆盖；与 development-code-write/-review §10 Gap-3 staging 一致 |
| Gap-4 development task rollback | ✅ | command-reference 状态机表 line 646-648 三条 transition；`bug-start` §8 / `bug-rework` §9 都明确 owner/trigger 与 BUG body `Affected Task(s)` 事实源；明确 `unable to localize` / 字段缺失 / 分类不明确时不得猜测，必须要求 `development-planning-write` replan/route；plan §6.2 测试覆盖 4 项 classification strategy（仅 step 3 措辞 Low 见 LOW3） |
| status_transition.py helper | ✅ | doc-guardian/SKILL.md §1 第 7 项责任 + §2 invocation 表 + §6.7 完整 plan/apply 接口 + 4 event mapping + 多 doc all-or-nothing rollback + 幂等重试；change-log-format.md §7.1 增量类 doc `[frontmatter]` Pending Changes → Change Log 同 transaction promote；16 个 stage SKILL.md Gap-2 helper 文案已统一指向 `skills/doc-guardian/scripts/status_transition.py`；plan §9.1-§9.4 完整给出 CLI / event mapping / 原子性 / 调用顺序 |
| Stage 5 testing flow | ✅ | testing-write §3 五种 mode（Full/Review Revise/Bug Routing/Retest/Bug Close/Retest Rework）+ §5.2 Case A/B/C + §6 E 维度 + §7 Bug Flow Re-entry + §10 Gap-5；testing-review §4.1 三种 review-passed（pass / initial fail triage-ready / active retest fail accurately recorded）+ §6 review-passed ≠ Stage 5 done + §7 Bug Flow Re-entry + §10 Gap-5；初次 fail/partial → bug-triage active mode；retest fail/partial → bug-rework；testing-review 不调 bug-start/bug-rework/bug-close（§1 + §8 Forbidden）；与 prerequisites §6 一致（仅 line 100 stale wording 见 LOW2） |
| stale text / regression scan | ⚠️ | 没有发现 `--event issues-found` 误用 / `helper 接口待后续定义` 残留 / Stage 6 delivery → testing rollback 暗示 / Stage 7 自动 release-close。但有 3 条 cross-doc 残留：design proposal v0.5 三处 11 命令（LOW1）+ prerequisites §6 line 100 "Before bug-rework exists" wording（LOW2）+ plan §6.2 step 3 措辞（LOW3）。均不阻塞，但建议 Phase 2/7 顺手清理 |

---

## Open Questions / Assumptions

1. **bug-triage SKILL.md 是否需要显式提及 Gap-5/bug-rework 边界？** 目前 bug-triage active mode entry gate (`bug_flow.active==false`) 与 bug-rework precondition (`bug_flow.active==true`) 已经互斥，bug-triage §10 Forbidden 没有显式禁止 "active retest fail/partial 期间被 invoke"。语义上不构成 bypass（gate 互斥），且 bug-triage 不在本轮 Phase 1 docs alignment 必修 list 里。但 cross-skill 引用层面，bug-triage §1 / §10 加 1 行 "active Bug Flow retest fail/partial 由 testing-write/Bootstrap 调 `progress.py bug-rework`，本 skill 不重 triage" 可进一步降低读者误读概率。**判断：本轮可接受不动；建议留到 Phase 2 起骨架时顺手；不作为 finding。**

2. **scenario-dispatcher / workflow-evolution 是否需要列出 bug-rework？** 二者均不直接 invoke bug-rework；scenario-dispatcher §6.2 Type B 仅列 active mode / post-close mode 路由；workflow-evolution 只 owner incident state。本轮 references 状态足以让 implementer 正确路由。**判断：不作为 finding；不阻塞 Phase 2。**

3. **task6 plan §10.1 Resolver Inputs 关于 SRS bool 字段默认 false 的描述 narrower than required-artifacts.md：** plan 说 "default false only when SRS is unavailable for condition evaluation"，required-artifacts.md §Condition DSL 默认值表说 "false（若 SRS 不存在或字段缺失）"。frontmatter-schema 已经把 `is_multi_module` / `architecture_change` 列为 srs 必含字段，validate.py file 会先 reject 字段缺失的 SRS，因此 condition evaluation 实际只在 SRS missing 时落到 default false。**判断：意图一致，措辞 narrower 但行为闭环；不作为 finding。**

4. **plan §3.2 引入新的 `skills/_shared/dev_workflow/` 共享模块树，与 `directory-layout.md` 的覆盖范围。** directory-layout.md §1 完整目录树聚焦于 managed-project 的 `docs/`、`src/`、`tests/`，没有约束 `skills/` 内部如何组织共享 Python lib。`_shared/dev_workflow/` 在 skills 工程范围内，不属于 doc-guardian 管辖（doc-guardian §4 仅校验 `docs/` 下 doc 文件路径合规）。**判断：不构成 cross-skill 冲突；不作为 finding。**

---

## Recommendation

**(A) accept — Proceed to Phase 2 shared foundation implementation.**

进入 Phase 2 之前**可选**清理（不阻塞）：

1. （LOW1）在 `docs/design/skill_set_design_proposal_v0.5.md` §4.4 / §11 / §15.1 三处加 v0.6 patch note，注明 progress.py 子命令数 11 → 12 + 新增 `bug-rework`；或在 task6 plan §3.4 Reference Updates 加一条 Phase 7 todo。
2. （LOW2）改写 `docs/handoff/task6_progress_py_prerequisites_20260506.md:100` "Before bug-rework exists ..." 为 "Until the `bug-rework` script lands in Phase 5/6 ..."。
3. （LOW3）改写 `docs/implementation/task6_plan_20260507.md:208` Gap-4 step 3，去除"set current stage to development/write"的歧义动作描述，改为说明命令 mutation 已经处理 stage/sub_state 推进。

按 task6 plan §13 Implementation Phases，Phase 2 应实现：

- `skills/_shared/dev_workflow/frontmatter.py` / `markdown.py` / `atomic.py` / `conditions.py` / `artifacts.py` / `progress_state.py` / `schema.py` 共 7 个共享模块
- 对应 unit tests：`tests/test_required_artifacts.py`（含 6 个 condition DSL parser test cases）+ frontmatter / markdown / atomic 基础 case
- Acceptance：focused unit tests pass for shared modules

Phase 2 完成后再进入 Phase 3 (changelog.py + validate.py file) → Phase 4 (status_transition.py) → Phase 5 (progress.py core) → Phase 6 (Bug Flow / Incident / advance) → Phase 7 (full smoke + docs polish)。

**不推荐 (B) fix docs before Phase 2 的判据**：当前 finding 0 High / 0 Medium / 3 Low；3 条 Low 都是 cross-doc cleanliness 而非 spec violation 或 broken state machine；Phase 2 的实现不依赖这 3 条 Low 的修复（implementer 按 command-reference / SKILL.md 即可）。

**不推荐 (C) revisit design 的判据**：本轮 Codex 的 Phase 1 docs alignment 没有触及任何已闭环架构层决策（authority hierarchy / 7 阶段主流程 / Bug Flow 4 类根因路由 / 三态 review report 不变量 / 递归悖论防御 / event 白名单 / terminal state cleanup / Change Log 分类）。Gap-3 / Gap-4 / Gap-5 + bug-rework + status_transition.py 都是 prerequisites 已经识别的 Task 6 范围内 transition / command / helper staging，不需要 design level 重做。
