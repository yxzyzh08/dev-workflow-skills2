# Claude Review Prompt — Task 6 Phase 6.2 `bug-rework` + Gap-4/5 Reuse

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_2_bug_rework_review_20260507.md`。Phase 6.2 通过后才能进入 Phase 6.3 (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.2 implementation** 做一次代码 review。本批是 Phase 6 的第二段：实现 active Bug Flow 的 retest fail/partial 重路由命令 `bug-rework`（Gap-5），并把 Phase 6.1 的 Gap-4 dev auto-rollback helper（`_compute_bug_start_rollback`）提升到 `skills/_shared/dev_workflow/progress_state.py` 共享层（更名 `compute_dev_bug_rollback`），让 `cmd_bug_start` 与新增的 `cmd_bug_rework` 共用一份 Gap-4 实现。

本轮是代码 review。**写集**仅限：

- 扩展 `skills/_shared/dev_workflow/progress_state.py`（追加 `compute_dev_bug_rollback` 共享 helper + `BugReworkOutcome` dataclass + `apply_bug_rework`；既有 `apply_bug_start` / `apply_bug_close` 行为完全不动）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`（注册 `_apply_bug_rework_handler`；module docstring + unsupported-event 错误消息更新到 6.2；`_HANDLERS` 现 12 项；`apply_bug_rework` 加入 import）
- 扩展 `skills/workflow-protocol/scripts/progress.py`（删除 CLI 端 `_compute_bug_start_rollback`，改 import 共享 `compute_dev_bug_rollback`；`cmd_bug_start` 调用点从 helper 名+签名变化；新增 `cmd_bug_rework`；argparse 加 `bug-rework` 子命令；dispatcher 加分支；`apply_bug_rework` / `compute_dev_bug_rollback` 加入 import；`bug-close` stderr 提示文案小幅调整 "Phase 6.2" 字样去掉）
- 新建 tests `tests/test_apply_bug_rework.py`（36 testcases）
- 新建 tests `tests/test_progress_bug_rework.py`（21 testcases）
- 扩展 tests `tests/test_progress_replay.py`（新 `ReplayBugReworkTests`，5 testcases；`supported_events_in_phase_6_1` 改名 `supported_events_in_phase_6_2` 并加 `bug-rework`；既有 `test_unknown_event_rejected` / `test_timestamp_check_fires_before_handler_dispatch` 的"未支持事件"样本从 `bug-rework` 改为 Phase 6.3 的 `incident-start`）
- 调整 tests `tests/test_progress_recover.py`（"未支持事件"样本同步换 `incident-start` + 注释从 "Phase 5.4" 改 "Phase 6.2"）

Phase 6.2 **不**实现：

- Phase 6.3: `incident-start` / `incident-resolve`（含 `TERMINAL_EVENTS` 首次落地）
- Phase 6.4: `update --advance`（P6 矩阵 + required-artifacts + breakdown count 一致性）
- Phase 6.4: `validate.py consistency`（doc-guardian 端 Class 8 cross-progress 校验）

这些不能因为它们在 6.2 里"还没写"而被当 finding。

## 当前工作背景

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5（4 子 phase）/ Phase 6.1（含 round 2 fixes）全部 (A) closed 或等待 reviewer 给 (A)：

- Phase 6.1 round 2 fixes 落地完毕（575 tests + compileall 干净），评审报告 `task6_phase6_1_bug_flow_entry_round2_review_20260507.md` 写出后预期 (A)。Phase 6.2 在 round 2 fixes 基础上启动；不重做 round 1 已闭环议题。

Phase 6 sub-phase 切分（user agreed 4-split）：

- Phase 6.1 ✅: bug-start + bug-close + Gap-3 update --task
- **Phase 6.2**（本批）: bug-rework + Gap-4/5 共享 helper
- Phase 6.3: incident-start + incident-resolve（含 TERMINAL_EVENTS 落地）
- Phase 6.4: update --advance + validate.py consistency

Phase 6.2 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 637 tests in 5.45s
# OK
#  - baseline (Phase 1-4 + Phase 5.1/5.2/5.3/5.4 + Phase 6.1 round 2):  575
#  - new in Phase 6.2:                                                    62
#    * test_apply_bug_rework.py                              : +36
#    * test_progress_bug_rework.py                           : +21
#    * test_progress_replay.py +new ReplayBugReworkTests      :  +5

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 10 子命令: init / query / recover / update / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework
```

End-to-end smoke 已通过 `test_progress_bug_rework.BugReworkHappyTests`：3 个 root_cause 各自重路由到正确 stage；retest fail / partial 两种 verification_status 都接受；dev root cause + test-only / source / ambiguous / unable_to_localize 四种分类各自正确处理（与 6.1 bug-start 行为一致）；BugReworkRecoverRoundtripTests 验证 recover 后状态机还原（含 Gap-4 dev rollback）；BugReworkRejectionTests 7 项前置 reject（无 active flow / bug path 不匹配 / passing test report / missing test report / root_cause 不匹配 / invalid path / non-testing stage）；BugReworkM1Tests 验证 out-of-band edit 触发 pipeline reject；BugReworkLockTests 验证 lock 阻塞。

## 阅读顺序

1. `docs/review/task6_phase6_1_bug_flow_entry_round2_review_20260507.md`（如果已存在）—— Phase 6.1 closure
2. `docs/handoff/session_handoff_task6_phase6_2_20260507.md` §0 / §4 —— Phase 6.2 scope + work order
3. `docs/implementation/task6_plan_20260507.md` §6.3 —— Gap-5 详细 plan
4. `docs/handoff/task6_progress_py_prerequisites_20260506.md` §6 —— Gap-5 contract
5. `skills/workflow-protocol/references/command-reference.md` §9 —— bug-rework 主 spec（含 mutation 表 + history append 模板）
6. `skills/_shared/dev_workflow/progress_state.py`（+ `compute_dev_bug_rollback` 共享 helper + `apply_bug_rework`；新增段在 `apply_bug_close` 之前）
7. `skills/_shared/dev_workflow/progress_replay.py`（+ `_apply_bug_rework_handler`；module docstring + unsupported-event 文案改到 6.2）
8. `skills/workflow-protocol/scripts/progress.py`（- 旧 `_compute_bug_start_rollback`；+ `cmd_bug_rework`；`cmd_bug_start` 调用点改 import 共享 helper）
9. `tests/test_apply_bug_rework.py` / `tests/test_progress_bug_rework.py`
10. `tests/test_progress_replay.py`（新 `ReplayBugReworkTests` + 修改 `ReplayUnsupportedEventTests` / `ReplayMonotonicityTests`）/ `tests/test_progress_recover.py`（unsupported event 样本同步）

## Phase 6.2 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 6.2 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. Tests 必须用 `tempfile.TemporaryDirectory` 隔离。
3. **bug-rework 状态机严格按 command-reference.md §9**：bug_flow.active=true + current_stage=testing + sub_state=review-passed + bug_path == bug_flow.bug_report_path + BUG frontmatter root_cause == bug_flow.root_cause + bug_flow.root_cause ∈ {srs, architecture, development} + 最新 test-report verification_status ∈ {fail, partial}（CLI 端校验）。
4. **bug-rework Mutation**：bug_flow.{active, bug_report_path, root_cause} **保持不变**；current_stage: testing → root_cause stage（按 `_ROOT_CAUSE_TO_STAGE` map）；sub_state: review-passed → write；review_iteration → 0。
5. **Gap-4 dev rollback 复用**：dev root cause + caller 提供 rollback_decisions → 应用 PROTECTED_TASK_TRANSITIONS 到 development_state.task_states，与 bug-start 完全一致（同一份 helper）。bug-rework 不接受 `--root-cause` CLI 参数，root_cause 来自 bug_flow（已写入 progress.md）。
6. **`_compute_bug_start_rollback` → `compute_dev_bug_rollback` refactor**：从 progress.py 提到 progress_state.py 共享层；签名从 `(state, bug_info, triage)` 简化为 `(state, triage)`（bug_info 在原实现里就没被用）；行为完全不变（重 run 的 575 baseline 通过证明）。
7. **CLI 校验顺序**：先 path resolve+containment，再 progress.md parse + bug_flow.active 检查，再 bug_path / root_cause 与 bug_flow 比对，再 release 提取，再 load_test_report（fail/partial），再 load_bug_report（含 expect_root_cause），再 dev triage parse + rollback compute，最后 _run_update_pipeline。任一步失败 exit 1 + progress.md 字节级未改。
8. **Replay 不读 BUG / test-report**（与 update-task / release-start / bug-start 一致）：所有 mutation 信息走 history summary canonical token。bug-rework summary 模板：`bug=<path> root_cause=<srs|architecture|development> Bug Flow rerouted [rollback=Tn:old->new;...]`。注意词序（"rerouted"，区别于 bug-start 的 "entered"）便于 grep。
9. **Planning-route note 复用**：dev root cause 但 rollback 列表为空（unable_to_localize / ambiguous / no eligible task state）→ 在 history_result 写 `route=development-planning-write (no auto-rollback applied)`，history_next 写 `development-planning-write replan/route`；与 bug-start round 2 L1 行为完全对称。
10. **canonical history token contract**：Phase 6.2 的 12 个 supported event 中，所有需要 token 的（init / update-task / release-start / bug-intake / bug-start / bug-rework）都满足 "summary 单独可被 _kv_tokens 反解" 约束。bug-rework token 集合 = bug-start token 集合（bug + root_cause + 可选 rollback）。
11. **M1 + M2 + L1 invariants 全继承**：bug-rework 走 `_run_update_pipeline`（含 history parse + composed-history replay + state diff）+ `_validate_review_iteration_value` + canonical summary token。
12. **bug-close 的 stderr 提示**：从 "use bug-rework for fail/partial — Phase 6.2" 改为 "use bug-rework for fail/partial"（Phase 注脚已不再准确）。

## 重点 review 项

请按以下维度逐条核对：

### A. `compute_dev_bug_rollback` shared helper

- 从 `progress.py._compute_bug_start_rollback` 迁移到 `progress_state.py`，命名是否合理（去除 underscore prefix → public，因为现在跨模块共享）？
- 签名从 `(state, bug_info, triage)` 简化为 `(state, triage)`：原实现里 `bug_info` 完全未使用，删除是否合理？是否破坏既有 caller（grep `_compute_bug_start_rollback` 应只剩 0 处）？
- 用 `getattr(triage, ...)` 而非直接属性访问 → 让 helper 接受任何 duck-typed triage 对象（test 用 `_FakeTriage` 验证），是否合理？是否对 production 代码（接受真实 `TriageAnalysis`）有任何副作用？
- 分类逻辑：test → only verified→test-revising；source → verified→code-revising AND code-review-passed→code-revising；ambiguous / unable_to_localize → 返回 ()；task_states 不含的 affected task 跳过；状态不在 verified/code-review-passed 也跳过 → 与 6.1 行为字节一致？
- 6 个 ComputeDevBugRollbackTests 是否覆盖完整（test/source/ambiguous/unable_to_localize/未注册 task/不可回退状态）？
- bug-start 既有的 8 个 dev-rollback 集成测试（`test_progress_bug_flow.py` BugStartHappyTests dev × 4 + PlanningRoutePersistenceTests × 4）依然全过，证明 refactor 透明？

### B. `apply_bug_rework` 状态机

- 7 条前置全 enforce：active project + iter ≤ 7 + bug_path canonical shape + current_stage=testing + sub_state=review-passed + bug_flow.active=true + bug_path == bug_flow.bug_report_path + root_cause ∈ {srs, architecture, development}？
- bug_flow 三字段全部**不动**（区别于 bug-start 的"从 null 到设值"和 bug-close 的"从设值到 null"）？
- current_stage 按 `_ROOT_CAUSE_TO_STAGE` 三向 map（srs/arch/dev → spec/design/development）；sub_state → write；review_iteration → 0；updated → now？
- `rollback_decisions` 处理：
  - 仅 root_cause=development 允许（其它 reject）—— 与 bug-start 同一逻辑
  - 每条 (task_id, old, new, reason) 都校验 `(old, new) ∈ PROTECTED_TASK_TRANSITIONS`
  - 每条都校验 `task_states.get(task_id) == old`（出 stale → reject "out-of-band"）
  - 全部应用到 task_states，写回 development_state？
- history summary 含 canonical token：`bug=` + `root_cause=` + 可选 `rollback=Tn:old->new;Tn2:old->new`，字面词 "rerouted"（区别于 bug-start "entered"）？
- 36 单测覆盖：3 root_cause × happy / Gap-4 dev rollback × 3 单 + 1 多 / 5 种 rollback reject / 9 种前置 reject + 4 planning-route note + 6 helper test + outcome frozen + 常量契约？

### C. `progress_replay._apply_bug_rework_handler`

- token 集合 = bug-start token 集合（bug + root_cause + 可选 rollback），缺任一 raise ReplayError "missing"；malformed rollback raise ReplayError "rollback ... malformed"；root 参数 `del` 明确忽略？
- handler 调 `apply_bug_rework(state, bug_path, now=entry.timestamp, rollback_decisions=...)` → 不传 root_cause（因为 root_cause 由 state.bug_flow 决定，replay 不需重新指定；token 提供 root_cause 仅用于"summary 必含 root_cause"的可读性 + missing 检测，与 bug-start handler 一致）？
- `_HANDLERS` 现 12 项；`supported_events_in_phase_6_2` 测试断言精确（注意从 `_in_phase_6_1` 重命名）？
- module docstring 改到 6.2（init + 4 update events + update-task + 3 release lifecycle + bug-start + bug-close + bug-rework = 12）；unsupported-event 错误消息文案同步改？

### D. `cmd_bug_rework` CLI

- 流程：argparse → resolve abs_bug → `relative_to(root)` 防 outside-root → 读 progress.md 拿 release / bug_flow → bug_flow.active 检查 → bug_path 与 bug_flow.bug_report_path 比对 → bug_flow.root_cause ∈ {srs/arch/dev} 检查 → load_test_report(release) 校验 verification_status fail/partial → load_bug_report(expect_root_cause=bug_flow.root_cause) → 若 dev root cause 则 parse_bug_triage_analysis + compute_dev_bug_rollback → 若 dev + 空 rollback 则 stderr 警告 → `_run_update_pipeline(compute_outcome=apply_bug_rework(...rollback_decisions))`？
- argparse: bug-rework 含 --bug + --agent；缺 --bug → exit 2（CLI usage error）；非法 root_cause / passing test / 错 BUG 类型 / 不匹配 path / 不匹配 root_cause / verification 失败 → exit 1（workflow validation）？
- bug-rework **不**含 --root-cause 参数（区别于 bug-start）：root_cause 来自 progress.md.bug_flow.root_cause，CLI 端用 load_bug_report 的 expect_root_cause 校验 BUG 文件 frontmatter 一致；如果不一致 reject？
- main dispatcher 新增 bug-rework 分支齐全？
- `bug-close` stderr 文案 "Phase 6.2" 字样去除（避免后续维护时跟不上 phase 实情）？

### E. tests 设计

- 单测全部 pure（不走 CLI），CLI 集成 `_install_test_stage_advance_handler` + `_FakeClock` + `_bring_active_bug_flow_to_retest_failed` helper 串起完整 happy 路径，与 Phase 6.1 风格一致？
- bug-rework CLI 测试覆盖 3 root_cause × happy + dev × 4 分类（test / source / ambiguous / unable_to_localize）+ retest fail / partial 两种 verification_status × happy + 7 种 reject + recover 2 种（含 dev rollback / planning-route）+ M1 (out-of-band edit reject) + lock blocking + argparse？
- 测试样本 BUG ID 选 `BUG-200` 系列（避免与 6.1 测试 BUG-001…BUG-103 同名冲突）？
- replay 5 个新测试覆盖：happy 1 + 含 rollback token 1 + missing token reject 1 + malformed rollback reject 1 + does not read BUG/test-report 1？
- `test_unknown_event_rejected` / `test_timestamp_check_fires_before_handler_dispatch` / `test_supported_events_in_phase_6_*` / `test_recover_rejects_history_with_unsupported_event` 四处的 unsupported event 样本从 `bug-rework` 改为 `incident-start`（Phase 6.3 territory）一致？

### F. 既有 invariant 是否保持

- Phase 1-4 + Phase 5.x + Phase 6.1 round 2 的 575 测试是否仍全过？
- M1 (history parse + replay 一致性 + state diff) + M2 (review_iteration > 7 entry guard) 在 bug-rework 路径上保持继承？
- `progress_lock.py` / `progress_history.py` / `progress_artifacts.py` / `validate.py` / `changelog.py` / `status_transition.py` 未被本批触动？
- `init` / `query` / `recover` / `update --event` / `update --task` / `release-*` / `bug-intake` / `bug-start` / `bug-close` 行为完全保留？尤其是 `cmd_bug_start` 由于改用了共享 helper，是否还能通过既有的 `BugStartHappyTests` 8 个测试 + `PlanningRoutePersistenceTests` 4 个测试？
- `_run_update_pipeline` + `extra_writes_factory` 钩子未被触动？
- `_validate_bug_path_shape` / `compute_dev_bug_rollback` / `_BUG_PATH_RE` 等共享函数是否保持单一来源（无重复定义）？

### G. 设计 / 可维护性

- bug-rework 与 bug-start 共享 token 集合（含 rollback semantics）→ replay 用同一 `_kv_tokens` + `_parse_rollback_token` 无需新 helper；这种镜像设计是否合理？后续 incident-resolve 是否能延续？
- `apply_bug_rework` 与 `apply_bug_start` 行为高度对称：是否有进一步抽象空间（基类 / 公共校验函数）？现阶段暴力复制是否可接受（spec/intent 显然不同，强行抽象会反噬可读性）？
- `apply_bug_rework` 文档说明清晰列出与 bug-start 的核心差异（保持 bug_flow / 不取 root_cause 参数 / requires retest fail/partial 由 CLI 校验）？
- BUG path containment 是否仍依赖 `_validate_bug_path_shape` + `relative_to` 双重检查？
- import 顺序 / `noqa: E402` 与既有约定一致？
- module-level helper（compute_dev_bug_rollback）是 public（无 underscore）还是 private 是否合理选择？

### H. Cross-doc 一致性

- `command-reference.md §9` (bug-rework) 字段 mutation 表与 `apply_bug_rework` 完整对齐？
- `command-reference.md §9` "rejected alternatives" 列表（不得 bug-start 同一 issue / 不得创建第二个 BUG / 不得在 fail/partial 调 bug-close / 不得手编 progress.md）：CLI 端通过哪些 reject 路径间接实现？是否需要在 docstring / 测试中显式记录这条对照？
- `task6_plan_20260507.md §6.3` (Gap-5) 全部 7 步 mutation 是否被 `apply_bug_rework` + `cmd_bug_rework` 实现？
- `task6_progress_py_prerequisites_20260506.md §6` (Gap-5 prerequisite) 全部条款是否落地？
- `command-reference.md §9` 状态机表 Stage 4 task 行：Gap-4 protected transitions 现在被 `bug-start` AND `bug-rework` 两个 owner 共同管理（替换 6.1 描述只 mention bug-start）— 是否需要在 reference 文档中同步更新（不属本批写集，但可作为 Open Question 记录）？

### I. 已知 Phase 6.3+ 后续工作（不在本 review 评判范围）

- Phase 6.3 `incident-start` / `incident-resolve`：workflow-incident-analysis 特殊 stage；resolve abort/reconstruct 写 `TERMINAL_EVENTS`，replay 后续 mutating entries fatal
- Phase 6.4 `update --advance`：P6 矩阵 + required-artifacts.md condition DSL 求值（Phase 2 已有 conditions/artifacts.py）+ doc-guardian validate.py file 调用 + breakdown count/declared 一致性
- Phase 6.4 `validate.py consistency`：doc-guardian 端 Class 8 cross-progress 校验

这些不应作为 Phase 6.2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_2_bug_rework_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 6.2 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6.3
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §9 / task6_plan §6.3 / progress_py_prerequisites §6 / SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§H 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 compute_dev_bug_rollback refactor 命名/可见性、bug-rework 与 bug-start 镜像设计的看法）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 6.3 (`incident-start` / `incident-resolve` + `TERMINAL_EVENTS`)**
   - **(B) fix before Phase 6.3**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 6.3 前修
- 哪些可以推迟到 Phase 6.4 / Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6.3/6.4 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
