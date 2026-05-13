# Claude Review Prompt — Task 6 Phase 6.1 Bug Flow entry/exit + Gap-3

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_1_bug_flow_entry_review_20260507.md`。Phase 6.1 通过后才能进入 Phase 6.2 (`bug-rework`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.1 implementation** 做一次代码 review。本批是 Phase 6 的第一段：实现 active Bug Flow 的入口/出口（`bug-start` + `bug-close`），以及 `update --task` 路径上的 Gap-3 protected transition (`verifying → code-revising`)。Phase 6.1 同时落地了 Gap-4 dev auto-rollback 完整逻辑（解析 BUG body `## Triage Analysis` + 关键字分类 + per-task 状态回退），让 Phase 6.2 `bug-rework` 可以直接复用同一 helper。

本轮是代码 review。**写集**仅限：

- 扩展 `skills/_shared/dev_workflow/progress_artifacts.py`（追加 `_BUG_PATH_RE` + `test-report` 路径模板 + `_TEST_FIX_KEYWORDS` / `_SOURCE_FIX_KEYWORDS` + `_AFFECTED_TASKS_RE` + `TestReportInfo` / `BugReportInfo` / `TriageAnalysis` dataclass + `load_test_report` / `load_bug_report` / `parse_bug_triage_analysis`）
- 扩展 `skills/_shared/dev_workflow/progress_state.py`（追加 `_ROOT_CAUSE_TO_STAGE` + `ROOT_CAUSES_FOR_BUG_START` 常量 + `BugStartOutcome` / `BugCloseOutcome` dataclass + `apply_bug_start` / `apply_bug_close` + `_check_gap_3_verification_fail` helper；扩展 `apply_update_task` 接受 Gap-3）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`（注册 `_apply_bug_start_handler` / `_apply_bug_close_handler` + `_parse_rollback_token` helper；docstring + unsupported-event 错误消息更新到 6.1；`_HANDLERS` 现 11 项）
- 扩展 `skills/workflow-protocol/scripts/progress.py`（`cmd_bug_start` / `cmd_bug_close` + `_compute_bug_start_rollback` helper；2 个新子命令 + dispatcher）
- 新建 tests `tests/test_apply_bug_start.py` / `test_apply_bug_close.py` / `test_apply_update_task_gap3.py`
- 新建 tests `tests/test_progress_bug_flow.py`
- 扩展 tests `tests/test_progress_artifacts.py`（test-report + bug-report + triage parser 的覆盖）
- 扩展 tests `tests/test_progress_replay.py`（`ReplayBugFlowTests`；`supported_events` 从 9 项升 11 项；既有 `test_unknown_event_rejected` / `ReplayMonotonicityTests` 的"未支持事件"样本从 `bug-start` 改为 Phase 6.2 的 `bug-rework`）
- 调整 `tests/test_apply_update_task.py`（移除 `test_verifying_to_code_revising_rejected_in_phase_5_3`；该测试在 Phase 6.1 的 `test_apply_update_task_gap3.py` 中以"verification fail/partial 才接受"形式重生）
- 调整 `tests/test_progress_recover.py`（"未支持事件"样本同步换 `bug-rework`）

Phase 6.1 **不**实现：

- Phase 6.2: `bug-rework`（含 Gap-4 retest fail/partial 重路由 — 复用 6.1 的 Gap-4 helper）
- Phase 6.3: `incident-start` / `incident-resolve`（含 `TERMINAL_EVENTS` 首次落地）
- Phase 6.4: `update --advance`（P6 矩阵 + required-artifacts + breakdown count 一致性）
- Phase 6.4: `validate.py consistency`（doc-guardian 端 Class 8 cross-progress 校验）

这些不能因为它们在 6.1 里"还没写"而被当 finding。

## 当前工作背景

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5（4 子 phase 全部）全部 (A) closed：

- Phase 5.4 round 2: `docs/review/task6_phase5_4_release_lifecycle_round2_review_20260507.md`（A: BUG path shape + containment / canonical version= token）

Phase 6 sub-phase 切分（user agreed 4-split）：

- **Phase 6.1**（本批）：bug-start + bug-close + Gap-3 update --task
- Phase 6.2：bug-rework（含 Gap-4/5）
- Phase 6.3：incident-start + incident-resolve（含 TERMINAL_EVENTS 落地）
- Phase 6.4：update --advance + validate.py consistency

Phase 6.1 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 553 tests in 4.375s
# OK
#  - baseline (Phase 1-4 + Phase 5.1/5.2/5.3/5.4 round 2):  467  (Phase 5.3 移除 1 个废测)
#  - new in Phase 6.1:                                       86
#    * test_progress_artifacts.py +new                : +20
#    * test_apply_bug_start.py                        : +21
#    * test_apply_bug_close.py                        : +12
#    * test_apply_update_task_gap3.py                 :  +7
#    * test_progress_bug_flow.py                      : +20
#    * test_progress_replay.py +new ReplayBugFlow     :  +6

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 9 子命令: init / query / recover / update / release-close / release-start / bug-intake / bug-start / bug-close
```

End-to-end smoke 已通过 `test_progress_bug_flow.BugStartHappyTests`：3 个 root_cause 各自路由到正确 stage；dev root cause + test-only / source / ambiguous 三种分类各自正确处理；`unable to localize` 触发 stderr 警告 + 不做 rollback；BugCloseHappyTests 验证 latest test-report=pass 后清空 bug_flow + 保留 testing stage；Gap3UpdateTaskTests 完整覆盖 verification fail/partial/pass 三种状态 → update --task 接受/拒绝。

## 阅读顺序

1. `docs/review/task6_phase5_4_release_lifecycle_round2_review_20260507.md` —— Phase 5 closure
2. `docs/implementation/task6_plan_20260507.md` §5.5 / §6.1 / §6.2 —— Bug Flow 命令矩阵 + Gap-3/4 详细
3. `skills/workflow-protocol/references/command-reference.md` §8 / §10 / 状态机表 Stage 4 protected rows
4. `docs/handoff/task6_progress_py_prerequisites_20260506.md` §1-§5 —— Gap-3/4 prerequisites
5. `skills/doc-guardian/references/frontmatter-schema.md` §3.4 / §4.5 —— bug-report 字段 + path reference
6. `skills/_shared/dev_workflow/progress_artifacts.py`（+ test-report / bug-report / triage helpers）
7. `skills/_shared/dev_workflow/progress_state.py`（+ apply_bug_start / apply_bug_close / Gap-3 在 apply_update_task）
8. `skills/_shared/dev_workflow/progress_replay.py`（+ bug-start / bug-close handlers）
9. `skills/workflow-protocol/scripts/progress.py`（+ cmd_bug_start / cmd_bug_close + _compute_bug_start_rollback）
10. `tests/test_apply_bug_start.py` / `test_apply_bug_close.py` / `test_apply_update_task_gap3.py`
11. `tests/test_progress_bug_flow.py`
12. `tests/test_progress_artifacts.py` / `tests/test_progress_replay.py`

## Phase 6.1 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 6.1 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. Tests 必须用 `tempfile.TemporaryDirectory` 隔离。
3. **bug-start 状态机严格按 command-reference.md §8**：bug_flow.active=false + release_state=active + current_stage=testing + sub_state=review-passed + canonical BUG path + root_cause ∈ {srs, architecture, development}。Mutation: bug_flow 三字段 + current_stage 按 `_ROOT_CAUSE_TO_STAGE` map + sub_state=write + iter=0。dev root cause + caller 提供 rollback_decisions → 应用 Gap-4 protected transitions 到 development_state.task_states。
4. **bug-close 状态机严格按 command-reference.md §10**：bug_flow.active=true + current_stage=testing + 最新 test-report verification_status=pass（CLI 端校验）。Mutation: bug_flow 清零 + current_stage=testing 保持 + sub_state 不动（待 Phase 6.4 advance 处理）。
5. **Gap-3 严格按 prerequisites.md §1**：(verifying, code-revising) protected transition 在 `apply_update_task` 中接受，前提 verification_result.md `verification_status ∈ {fail, partial}`。**无需** active Bug Flow（区别于 Gap-4）。
6. **Gap-4 仍 deferred 在 update --task 路径**：(verified, test-revising) / (verified, code-revising) / (code-review-passed, code-revising) 在 `apply_update_task` 中仍 reject 并提示 "use Phase 6 bug-start / bug-rework"。这些 transition 只能通过 `apply_bug_start` 的 `rollback_decisions` 参数应用。
7. **Replay 不读 BUG / test-report**（与 update-task / release-start 一致）：所有 mutation 信息走 history summary canonical token。bug-start summary：`bug=<path> root_cause=<srs|architecture|development> Bug Flow entered [rollback=Tn:old->new;...]`；bug-close summary 简洁，状态恢复纯粹通过 state machine。
8. **BUG body 关键字分类（Phase 6.1 MVP）**：`_TEST_FIX_KEYWORDS` 五个 + `_SOURCE_FIX_KEYWORDS` 五个；test-only AND source 同时出现 → ambiguous；test-only AND not source → "test"；source AND not test-only → "source"；其它 → "ambiguous"。
9. **`unable to localize` 处理**：affected_tasks 空 + classification 仍可分类（用于 history note），但 caller 应当不做 auto-rollback；CLI 端 print stderr 警告；history 仍记录 bug-start 但 rollback 列表为空。
10. **canonical history token contract**：Phase 6.1 的 11 个 supported event 中，所有需要 token 的（init / update-task / release-start / bug-intake / bug-start）都满足 "summary 单独可被 _kv_tokens 反解"约束。bug-close 无 token（mutation 纯由 state machine 决定）。
11. **M1 + M2 + L1 (canonical token) invariants 全继承**：bug-start / bug-close / Gap-3 update-task 都共享 `_run_update_pipeline`（含 history parse + composed-history replay + state diff）+ `_validate_review_iteration_value` + canonical summary token。

## 重点 review 项

请按以下维度逐条核对：

### A. `progress_artifacts.py` 扩展

- `_BUG_PATH_RE` 与 progress_state.py 中的 `_BUG_PATH_RE` 是否一致（两个内部共享 `^docs/bug/BUG-\d{3}\.md$`）？是否考虑去重（一处定义）？
- `_PATH_TEMPLATES` 加 `test-report` 项是否复用 `load_artifact_frontmatter` 的现有路径解析？
- `load_test_report`：missing / 错 type / 错 release / `verification_status` 不在 enum 时全 reject？
- `load_bug_report`：canonical path shape 校验 / type=bug-report / `expect_root_cause` 比对 / 缺失 bug_id / found_in_release 类型校验？返回 body 给 caller 用？
- `parse_bug_triage_analysis`：缺 `## Triage Analysis` section 拒；缺 `**Affected Task(s)**:` 行拒；`unable to localize` 返回空 tuple + classification 仍按 body 关键字算；任务 token 不匹配 `^T\d+$` 拒；token dedup 后保序；分类 `test` / `source` / `ambiguous` 三档？
- `_classify_bug_body` 关键字逻辑：test∧source → ambiguous；test∧¬source → test；source∧¬test → source；其它 ambiguous？
- 39 测试覆盖（baseline 19 + Phase 6.1 新 20）：所有 happy + 所有 reject + 边界（dedup / 双关键字 / unable to localize）？

### B. `apply_bug_start` 状态机

- 6 条前置全 enforce：active project + iter ≤ 7 + bug_path canonical shape + release=active + current_stage=testing + sub_state=review-passed + bug_flow.active=false + root_cause ∈ {srs, architecture, development}？
- mutation 仅触动 bug_flow / current_stage / sub_state / review_iteration / updated；其它字段（含 unresolved_bugs / 项目级 artifacts）原样保留？
- root_cause 按 `_ROOT_CAUSE_TO_STAGE` 三向 map（srs/arch/dev → spec/design/development）？
- `rollback_decisions` 处理：
  - 仅 root_cause=development 允许（其它 reject）
  - 每条 (task_id, old, new, reason) 都校验 `(old, new) ∈ PROTECTED_TASK_TRANSITIONS`
  - 每条都校验 `task_states.get(task_id) == old`（出 stale → reject "out-of-band"）
  - 全部应用到 task_states，写回 development_state？
- history summary 含 canonical token：`bug=` + `root_cause=` + 可选 `rollback=Tn:old->new;Tn2:old->new`？
- 21 单测覆盖：3 root_cause × happy / 3 种 Gap-4 rollback 场景 / 5 种 rollback reject / 8 种前置 reject + outcome frozen + 常量契约？

### C. `apply_bug_close` 状态机

- 4 条前置全 enforce：active project + iter ≤ 7 + bug_flow.active=true + current_stage=testing？
- mutation: bug_flow 三字段清零 + updated；current_stage / sub_state 保留？
- caller 责任明确（test-report.verification_status=pass 在 CLI 校验，不在 apply 内）？
- history summary 简洁 "Bug Flow exited (retest passed)"；history result 含 closed bug path + root_cause（便于诊断）？
- 12 单测覆盖：5 happy + 5 reject + outcome frozen + sub_state 不动验证？

### D. `apply_update_task` Gap-3 扩展

- (verifying, code-revising) 现在被识别为 Gap-3，allow_protected 隐式接受？
- 其它 PROTECTED transitions（Gap-4）仍 reject 并明确提示 "use Phase 6 bug-start / bug-rework"？
- `validate_artifacts=True` 时调 `_check_gap_3_verification_fail` 校验 verification_result fail/partial？
- `validate_artifacts=False`（replay 路径）时跳过 artifact 校验，与 Phase 5.3 design 一致？
- 7 单测覆盖：fail/partial happy / pass reject / missing artifact reject / Gap-4 transitions 仍 reject / replay bypass？
- 旧 5.3 测试 `test_verifying_to_code_revising_rejected_in_phase_5_3` 是否被合理移除（Phase 6.1 不再 reject Gap-3，rejection 路径已迁移到 test_apply_update_task_gap3.py 的 Gap3RejectionTests）？

### E. `progress_replay.py` 扩展

- `_parse_rollback_token` 解析 `Tn:old->new;Tn2:old->new` → 4-tuple list；malformed 抛 ValueError？
- `_apply_bug_start_handler` 必含 root_cause + bug 两个 token（缺任一 raise ReplayError "missing"）；rollback token 可选；root 参数 `del` 明确忽略？
- `_apply_bug_close_handler` 不需要 token（state machine 单纯回滚）；root `del` 忽略？
- `_HANDLERS` 现 11 项；`supported_events()` 测试断言精确？
- module docstring 与 unsupported-event 错误消息描述 6.1 现状（init + 4 update events + update-task + 3 release lifecycle + bug-start + bug-close = 11）？

### F. `progress.py` CLI

- `cmd_bug_start` 流程：argparse → resolve abs_bug → `relative_to(root)` 防 outside-root → `load_bug_report(expect_root_cause=arg)` → 若 dev root cause 则 `parse_bug_triage_analysis` → 读当前 task_states → `_compute_bug_start_rollback` → `_run_update_pipeline(compute_outcome=apply_bug_start(...rollback_decisions))`？
- `_compute_bug_start_rollback` 分类逻辑：test → only verified→test-revising；source → verified→code-revising 或 code-review-passed→code-revising；ambiguous / unable_to_localize → 返回 ()（不做自动 rollback）？task_states 不含的 affected task 跳过？
- `cmd_bug_close` 流程：先读 progress.md 拿 release → `load_test_report(release)` → 校验 verification_status=pass → 进入 pipeline 调 `apply_bug_close`？
- argparse: bug-start 含 --bug + --root-cause + --agent；bug-close 仅 --agent；缺关键参数 → exit 2（CLI usage error）；非法 root_cause / 错 BUG 类型 / 不匹配 root_cause / verification 失败 → exit 1（workflow validation）？
- main dispatcher 两个新分支齐全？

### G. tests 设计

- 单测全部 pure（不走 CLI），CLI 集成 `_install_test_stage_advance_handler` + `_FakeClock` patch 风格与 Phase 5.3 / 5.4 一致？
- `_seed_testing_review_passed` / `_seed_testing_review_passed_with_dev_tasks` / `_seed_development_with_task` 三个 helper 把 progress.md 与 history 同步 forge，保证 M1 一致性 check 不误伤？
- bug-start CLI 测试覆盖 3 root_cause × happy + dev × test/source/ambiguous/unable_to_localize 四种分类 + 5 种 reject（active release 错 / root_cause 不匹配 / missing BUG / invalid path / argparse 缺）？
- bug-close CLI 测试覆盖 happy + 3 种 reject（no active flow / failing test / missing test report）？
- Gap-3 CLI 测试覆盖 fail/partial happy + pass reject + 文件字节级未改？
- 既有 5.x 测试 supported_events 集合从 9 升 11 + "未支持事件"样本从 `release-close` (5.4) → `bug-start` (6.1) → `bug-rework` (Phase 6.2) 同步更新？

### H. 既有 invariant 是否保持

- Phase 1-4 + Phase 5.x 的 467 测试是否仍全过？
- M1 (history parse + replay 一致性 + state diff) + M2 (review_iteration > 7 entry guard) 在 bug-start / bug-close / Gap-3 update-task 三条路径上保持继承？
- `progress_lock.py` / `progress_history.py` 未被本批触动？
- `init` / `query` / `recover` / `update --event` / `update --task` (normal) / `release-*` / `bug-intake` 行为完全保留？
- `_run_update_pipeline` + `extra_writes_factory` 钩子未被触动？
- `_validate_bug_path_shape`（来自 5.4 round 2）继续在 bug-start 路径上生效？

### I. 设计 / 可维护性

- `_compute_bug_start_rollback` 作为 CLI 端 helper，Phase 6.2 `bug-rework` 复用是否会有不便？是否考虑后续移到 progress_state.py / progress_artifacts.py 共享层？
- BUG body 关键字列表（test/source）是否合理？是否便于 doc-guardian 团队后续扩展？
- `_check_gap_3_verification_fail` 函数命名清晰，与 `_require_verification_pass` 形成对照？
- bug-start summary 的 rollback token 格式 `Tn:old->new` 是否便于后续手工 grep / log 分析？分号分隔多个的可读性？
- import 顺序 / `noqa: E402` 与既有约定一致？

### J. Cross-doc 一致性

- `command-reference.md §8` (bug-start) 字段 mutation 表与 `apply_bug_start` 完整对齐？
- `command-reference.md §10` (bug-close) 字段 mutation 表与 `apply_bug_close` 完整对齐？
- `command-reference.md` 状态机表 Stage 4 task 行：Gap-3 (verifying→code-revising) 的"verification_result `verification_status ∈ {fail, partial}`"约束在 6.1 完整 enforce？
- `docs/handoff/task6_progress_py_prerequisites_20260506.md` Gap-3/4 描述被 6.1 落实（Gap-3 已实现；Gap-4 dev rollback 已实现 via bug-start，6.2 复用）？
- `frontmatter-schema.md §3.4` bug-report 字段（bug_id / found_in_release / target_release / consumed_in_release / root_cause）被 `load_bug_report` thin check 验证？

### K. 已知 Phase 6.2+ 后续工作（不在本 review 评判范围）

- Phase 6.2 `bug-rework`：active Bug Flow retest fail/partial 重路由；前置含最新 test-report fail/partial + bug_path / root_cause 与当前 bug_flow 一致；含 Gap-4 dev rollback 复用 6.1 helper（`_compute_bug_start_rollback` 或重构后的共享版）；Gap-5 是 rework 命令本身的新引入语义
- Phase 6.3 `incident-start` / `incident-resolve`：workflow-incident-analysis 特殊 stage；resolve abort/reconstruct 写 `TERMINAL_EVENTS`，replay 后续 mutating entries fatal
- Phase 6.4 `update --advance`：P6 矩阵 + required-artifacts.md condition DSL 求值（Phase 2 已有 conditions/artifacts.py）+ doc-guardian validate.py file 调用 + breakdown count/declared 一致性
- Phase 6.4 `validate.py consistency`：doc-guardian 端 Class 8 cross-progress 校验

这些不应作为 Phase 6.1 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_1_bug_flow_entry_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 6.1 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6.2
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §8/§10/Stage 4 task 表、prerequisites.md §1-§5、frontmatter-schema.md §3.4、SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§J 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 BUG body 关键字分类的 robustness 看法）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 6.2 (`bug-rework` + Gap-4/5 复用)**
   - **(B) fix before Phase 6.2**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 6.2 前修
- 哪些可以推迟到 Phase 6.3 / 6.4 / Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6.2/6.3/6.4 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
