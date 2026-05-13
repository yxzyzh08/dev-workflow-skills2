# Claude Review Prompt — Task 6 Phase 5.3 progress.py update --task

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_3_update_task_review_20260507.md`。Phase 5.3 通过后才能进入 Phase 5.4 (`release-close` / `release-start` / `bug-intake`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.3 implementation** 做一次代码 review。本批是 progress.py 第三阶段：在 Phase 5.1 lock/history/replay 与 Phase 5.2 update --event 基础上加 `update --task` 子命令，覆盖 Stage 4 任务状态机的 14 条 normal transitions + 各状态的 artifact frontmatter precondition + idempotent planning-done。Phase 5.4 / Phase 6 会继续在这套基础上加 `release-*` / `bug-*` / `incident-*` / `update --advance` 与 Gap-3/4/5 protected rollback。

本轮是代码 review。**写集**仅限：

- 新建 shared module `skills/_shared/dev_workflow/progress_artifacts.py`
- 扩展 `skills/_shared/dev_workflow/progress_state.py`（追加 `TaskOutcome` dataclass + `apply_update_task` + 几个 per-status precondition helper + `_TASK_ID_RE`；不动既有 `apply_update_event` / `build_initial_state`）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`（注册 `update-task` handler；handler signature 加 `root` 参数；既有 init / update --event handler 忽略 root；`replay_history` 加 `root=None` keyword）
- 扩展 `skills/workflow-protocol/scripts/progress.py`（mutex group 加 `--task` + `--status`；`cmd_update` 拆为 `_do_update_event` / `_do_update_task` 通过共享 `_run_update_pipeline`；`cmd_recover` 给 `replay_history` 传 root）
- 新建 tests `tests/test_progress_artifacts.py`
- 新建 tests `tests/test_apply_update_task.py`
- 新建 tests `tests/test_progress_update_task.py`
- 扩展 tests `tests/test_progress_replay.py`（`supported_events` 集合 + 新 `ReplayUpdateTaskTests` class）

Phase 5.3 **不**实现：

- `update --advance`（Phase 6）
- `release-close` / `release-start` / `bug-intake`（Phase 5.4）
- `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`（Phase 6）
- Gap-3/4/5 protected rollback transitions（Phase 6；`apply_update_task` 显式 reject 这些 transition 并提示走 bug-start/bug-rework）
- `validate.py consistency`（Phase 6+）
- breakdown.md `total_tasks` 与 declared task 数量一致性校验（Phase 6 update --advance）
- 全 doc-guardian Class 1-7 校验（progress_artifacts 仅做 type/release/task_id 三项 thin check）

这些不能因为它们在 5.3 里"还没写"而被当 finding。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5.1 / Phase 5.2 全部 (A) closed：

- Phase 5.2 round 2: `docs/review/task6_phase5_2_update_event_round2_review_20260507.md`（A: M1 history parse + replay consistency；M2 review_iteration > 7 entry check）

Phase 5 sub-phase 切分：

- Phase 5.1（已闭环）：foundation（lock/history/replay）+ init + query + recover
- Phase 5.2（已闭环）：`update --event`
- **Phase 5.3**（本批）：`update --task`（Stage 4 normal transitions only）
- Phase 5.4：`release-close` + `release-start` + `bug-intake`

Phase 5.3 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 367 tests in 3.104s
# OK
#  - baseline (Phase 1-4 + Phase 5.1/5.2 round 2):  293
#  - new in Phase 5.3:                                74
#    * test_progress_artifacts.py     : 15  (artifact loaders)
#    * test_apply_update_task.py      : 37  (state machine + per-status preconditions + protected reject + field preservation)
#    * test_progress_update_task.py   : 16  (CLI + M1 inheritance + recover roundtrip + lock + happy cycle via test stage-advance handler)
#    * test_progress_replay.py +new   :  6  (ReplayUpdateTaskTests)
#    * test_progress_replay.py rename :  ±0 (supported_events_in_phase_5_2 → supported_events_in_phase_5_3)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py update --help
# 输出 mutex group with (--event | --task) + --status + --agent
```

End-to-end smoke 已通过 `test_full_stage_4_cycle_for_T1` 验证：T1 走完 planning-done → test-writing → test-review → test-done → code-writing → code-review → code-review-passed → verifying → verified；删 progress.md 后 `recover --confirm` 重建出一致的 development_state.task_states。

## 阅读顺序（请严格按序读）

1. `docs/review/task6_phase5_2_update_event_round2_review_20260507.md` —— Phase 5.2 closure，5.3 复用 lock + M1 + atomic.transaction
2. `docs/implementation/task6_plan_20260507.md` §5.4 / §11.1 / §13 —— update --task 命令矩阵 + atomicity + Phase 划分
3. `skills/workflow-protocol/references/command-reference.md` §2.1 Stage 4 task transition 表
4. `docs/handoff/task6_progress_py_prerequisites_20260506.md` —— Gap-3/4/5 / planning-done idempotent / atomic 一致性的来源
5. `skills/doc-guardian/references/frontmatter-schema.md` §3.3（per-task doc 类型：detailed-design / test-review-report / code-review-report / verification-result）+ §3.2 task-breakdown
6. `skills/_shared/dev_workflow/progress_state.py`（含本批新增 `apply_update_task` / `TaskOutcome` / per-status preconditions）
7. `skills/_shared/dev_workflow/progress_artifacts.py`（**新文件**）
8. `skills/_shared/dev_workflow/progress_replay.py`（含本批新增 `_apply_update_task` + handler signature `root`）
9. `skills/workflow-protocol/scripts/progress.py`（含本批新增 `_do_update_task` / `_run_update_pipeline` 重构）
10. `tests/test_progress_artifacts.py`（**新文件**）
11. `tests/test_apply_update_task.py`（**新文件**）
12. `tests/test_progress_update_task.py`（**新文件**）—— 注意 `_install_test_stage_advance_handler` 与 `_FakeClock` 的测试侧 patch 设计
13. `tests/test_progress_replay.py`（含本批新增 `ReplayUpdateTaskTests`）

## Phase 5.3 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 5.3 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. 工作树大量 untracked 是项目内容，不得 delete/clean/reset/revert。
3. Tests 必须用 temp dirs / fixtures，不得 mutate 真实 `docs/` / `skills/`。
4. **写集严格**（见前文写集列表）；progress_artifacts.py 是新 shared module，但只暴露 `load_artifact_frontmatter` + `load_breakdown_with_tasks` + `ArtifactFrontmatter` / `BreakdownInfo` / `ProgressArtifactError`。
5. **State 机器规则严格按 command-reference.md §2.1 Stage 4 表**：14 条 normal transitions + idempotent planning-done。protected transitions（4 条）显式 reject 并提示 Phase 6 路径。
6. **per-status artifact precondition** 严格按 frontmatter-schema.md §3.3 的 lifecycle：
   - `planning-done`: breakdown.md 含 `\bT<n>\b` token + detailed_design.md 存在 + frontmatter.task_id 一致
   - `test-review`: test_review_report.md `review_status==pending`（skeleton）
   - `test-done`: review_status==pass + blocking_findings_count==0
   - `code-review`: code_review_report.md `review_status==pending`
   - `code-review-passed`: review_status==pass + blocking_findings_count==0
   - `verified`: verification_result.md `verification_status==pass`
   - 其它（test-writing / test-revising / code-writing / code-revising / verifying）transitional，无 artifact precondition
7. **共同前置**：`project_state==active` + `current_stage=='development'` + `task_id` 匹配 `^T\d+$` + `(old, new) ∈ NORMAL_TASK_TRANSITIONS`。
8. **Atomicity**：`update --task` 必须经 `progress_lock` + `atomic.transaction` 双写 progress.md + progress-history.md；任一失败 rollback 两者；任一 ProgressStateError / ProgressArtifactError → exit 1 文件不动。
9. **Phase 5.2 round 2 invariants 全继承**：M1 existing-history parse + composed-history replay + state diff；M2 review_iteration > 7 entry check（虽然 update --task 不直接动 review_iteration，但状态机经过 `_validate_review_iteration_value` 仍会触发）。
10. **History entry**：`event="update-task"` 字面；summary canonical `task=Tn status=<new>`，idempotent retry 加 `(idempotent retry)` 后缀；`progress_history.py` 字段白名单仍 `agent / result / next` 不变（task 信息进 summary，不进新字段）。
11. **`apply_update_task` 单一事实源**：CLI forward path 与 replay 都通过它，但 replay 用 `validate_artifacts=False`（设计选择，见下）。
12. **replay artifact 校验 = False**（关键设计选择）：Stage 4 review 报告文件 lifecycle 是 skeleton(pending) → pass，同一文件在不同 transition 时是不同状态。replay 重读"当前"artifact 会让一个早期 transition（要求 pending）在文件已经被改成 pass 后误 fail。M1 仍通过 progress.md state 比对捕到 out-of-band 篡改。
13. **replay_history(history, *, root=None)** 新签名向后兼容：既有 init / update --event handler 忽略 root；只有 `_apply_update_task` 用到。无 root 时 `_apply_update_task` 显式 raise（防 caller 误用）。
14. **CLI 风格**：`update` mutex group `(--event | --task)` 必填一个；`--task` 必须配 `--status`；非法 task_id / status / 不支持的转移 → exit 1（与 5.2 round 2 M2 契约一致：workflow validation 失败走 1，CLI usage 失败走 2）。

## 重点 review 项

请按以下维度逐条核对：

### A. `progress_artifacts.py`

- `_PATH_TEMPLATES` 路径与 frontmatter-schema.md / directory-layout.md / TYPE_PATHS 是否一致？
- `load_artifact_frontmatter`：missing file / FrontmatterError / type 不匹配 / release 不匹配 / task_id 不匹配 / unknown doc_type / 缺 task_id when required → 全部 raise `ProgressArtifactError` 且消息含可定位字段？
- `load_breakdown_with_tasks`：调用 `load_artifact_frontmatter` 校验 frontmatter；body extract 用 `\bT\d+\b` word-boundary，正确识别 T10 但不识别 TenThousand？
- 是否有意识地不复制 doc-guardian 的全套 Class 1-7（仅做 thin check）？文档清晰说明 boundary？

### B. `apply_update_task` 状态机

- `_TASK_ID_RE` 与 frontmatter-schema.md §4.4 task_id 格式（`^T\d+$`）一致？
- 14 条 normal transitions 全在 `NORMAL_TASK_TRANSITIONS`（progress_state.py 既有常量）；idempotent planning-done × planning-done 在常量内；protected transitions 显式 reject 并提示 Phase 6？
- per-status precondition routing 表（`_check_artifact_preconditions`）是否覆盖：planning-done / test-review / test-done / code-review / code-review-passed / verified？transitional 状态无 precondition？
- `_check_planning_done_artifacts`：先 load_breakdown_with_tasks → 检查 task_id 在 declared_tasks → 再 load detailed_design 查 task_id 一致？
- `_require_review_skeleton` / `_require_review_pass`：检查 review_status / blocking_findings_count（pass 时 blocking==0 强制）？错误消息含具体值？
- `_require_verification_pass`：仅接受 verification_status=pass？
- TaskOutcome：仅触动 `development_state.task_states[Tn]` + `updated`，其它字段（含 sub_state / current_stage / unresolved_bugs / bug_flow）原样保留？
- summary 文案：normal `task=Tn status=<new>`；idempotent 加 `(idempotent retry)`；result 文案区分"registered"vs"from <old>"？
- `_next_skill_for_status` 11 条映射是否合理（用于 history.next 字段）？
- `validate_artifacts=True` 默认；`validate_artifacts=False` 用于 replay 的 design rationale 是否在 docstring 写清楚？

### C. `progress_replay.py` 扩展

- `replay_history(history, *, root=None)` 签名向后兼容（init / update --event 测试无 root 仍能跑）？
- `ApplyFn` 类型签名加 root，既有 handler 加 `del root`（明确忽略，避免 lint 警告）？
- `_apply_update_task`：root 缺失立即 raise；summary regex `^task=(?P<task>T\d+) status=(?P<status>[a-z][a-z0-9-]*)\b`（注意 `\b` 让 idempotent suffix 不影响解析）；调 `apply_update_task(..., validate_artifacts=False)` 以避开历史 artifact 时变；ProgressStateError / ProgressArtifactError 都包成 ReplayError？
- `_HANDLERS` 字典更新：含 init + 4 update events + update-task = 6 项？
- `supported_events()` 现 6 项？
- `cmd_recover` 是否传 root 给 replay_history（否则 update-task 历史会因为缺 root 失败）？

### D. `progress.py` CLI 重构

- `cmd_update` 拆为 dispatcher + `_do_update_event` + `_do_update_task` + `_run_update_pipeline`；后者闭包接受 `compute_outcome` callable，避免代码重复？
- argparse mutex group `add_mutually_exclusive_group(required=True)` 含 `--event` 与 `--task`；`--status` 是 group 外 sibling argument（仅 `--task` 模式需要，由 `_do_update_task` 显式校验缺失）？
- `--status` 缺失走 exit 2 还是 exit 1？设计是：`--task` without `--status` → exit 2（CLI usage error，因为 --status 是必备 sibling）；非法 status 值（不在 TASK_STATES）→ exit 1（workflow validation）；与 5.2 `--scenario` exit 1 契约对齐。
- `_run_update_pipeline` 共享：lock + 文件存在 + frontmatter 解析 + history parse (M1 入口) + apply (compute_outcome 闭包) + history append + composed-history replay (M1 出口) + atomic.transaction → 任何一步失败 exit 1 文件不动？
- `replay_history` 调用是否传 root（M1 更新后 update-task replay 需要）？
- 错误消息：ProgressArtifactError 在 cmd 路径上是否独立 catch（与 ProgressStateError 同级处理为 exit 1）？

### E. tests/test_progress_artifacts.py

- 15 测试覆盖：happy path（2 类型）+ missing / 损坏 frontmatter / wrong type / wrong release / wrong task_id / unknown doc_type / invalid task_id format / requires task_id（共 8 reject 路径）+ breakdown extract 3 测试（正常 / wrong type / total_tasks 非 int / word-boundary）？

### F. tests/test_apply_update_task.py

- 37 测试覆盖：
  - PlanningDoneTests ×5：first-time / idempotent / breakdown missing / breakdown does not declare / detailed_design missing / detailed_design task_id mismatch
  - TransitionalStatesTests ×4：planning-done→test-writing / test-revising→test-review (要 skeleton) / test-done→code-writing / code-review-passed→verifying
  - TestReviewSkeletonTests ×2：pending OK / non-pending reject
  - TestDoneTests ×4：pass+0 OK / pending reject / fail reject / blocking>0 reject
  - CodeReviewTests ×3：pending OK / pass+0 OK / pass+nonzero reject
  - VerifiedTests ×3：pass OK / fail reject / partial reject
  - ProtectedTransitionsRejectedTests ×4：4 protected transitions 都 reject 并提示 Phase 6
  - GenericPreconditionTests ×8：invalid task_id / invalid status / non-development stage / aborted project / invalid now / illegal normal transition / first-time test-writing reject / sibling tasks preserved
  - FieldPreservationTests ×2：other top-level fields preserved / outcome frozen
  - TaskStatesContractTests ×1：TASK_STATES 集合恰好 11 项

### G. tests/test_progress_update_task.py

- 16 测试覆盖：
  - argparse: help / mutex 不允许 --event 与 --task 同传 / --task 无 --status 退 2 / 非法 task_id 退 1
  - non-development: prd-inception 上 update --task 退 1
  - M1 inheritance: forge progress.md 到 development 但不 forge history → replay diff 退 1 / malformed history 退 1
  - happy cycle: planning-done roundtrip / 完整 9-state stage 4 cycle / idempotent planning-done / 双 task 并行
  - history 字段：summary 含 `task=T1 status=...` canonical 格式
  - recover roundtrip: 跑半 stage 4 后删 progress.md，recover 重建一致
  - artifact reject: planning-done 缺 breakdown / verified 拿 partial 验证 → 退 1 文件不动
  - lock 阻塞: lock 持有时 update --task 退 1 文件不动
- 测试侧 `_install_test_stage_advance_handler` 与 `_FakeClock` patch 设计是否清楚？是否仅 patch contextual scope（不污染其他测试）？
- `_seed_development` 文档说明 advance_ts 必须用 patched clock 取，确保 monotonicity？
- 是否所有 CLI 测试用 `tempfile.TemporaryDirectory()` 隔离？真实 repo `progress.md` / `progress-history.md` 不被触动？

### H. tests/test_progress_replay.py 扩展

- `ReplayUpdateTaskTests` 6 测试覆盖：supported_events 含 update-task / 无 root 立即 raise / 不可解析 summary reject / 不重读 artifact (validate_artifacts=False) / 仍验状态机 / idempotent suffix 解析？
- `supported_events_in_phase_5_3` 集合恰好 6 项？

### I. 与既有 invariant 的一致性

- Phase 5.1 + 5.2 的所有测试是否仍全过（包括 timestamp 文档序、scenario exit 1、M1 history parse + replay consistency、M2 review_iteration > 7 entry check）？
- `progress_lock.py` / `progress_history.py` 是否未被本批触动？
- `init` / `query` / `recover` 既有行为保留？特别是 recover 现在能 replay update-task 历史？
- `cmd_update --event` 路径是否未被重构破坏（已被 367 测试中的 5.2 round 1/2 测试 cover）？
- `EventOutcome` / `TaskOutcome` 字段一致（new_state / history_summary / history_result / history_next）便于 `_run_update_pipeline` 鸭子类型？

### J. 设计 / 可维护性

- `apply_update_task` 单一事实源 + `validate_artifacts` 旗帜的设计是否清晰？docstring 是否充分解释 forward (True) 与 replay (False) 的不同动机？
- replay 不重读 artifact 的设计选择带来的语义影响（"replay validates state-machine legality, not artifact compliance"）是否在 module docstring 与 review prompt 中明确？
- artifact 路径模板集中在 `_PATH_TEMPLATES`（progress_artifacts.py）便于 5.4/Phase 6 添加新 artifact 类型？
- 错误消息：ProgressArtifactError 都含 rel_path + 关键 field name + 期望/实际值？
- `_run_update_pipeline` 闭包参数 `compute_outcome` 是否便于 Phase 6 加 `--advance` 时再扩展？

### K. 已知 Phase 5.4+ 后续工作（不在本 review 评判范围）

- Phase 5.4 `release-close`：Stage 7 review-passed 后 `release_state: active → closed`
- Phase 5.4 `release-start --version --scenario`：跨多文件原子（progress + N 个 BUG frontmatter）；BUG `target_release` / `consumed_in_release` 同步
- Phase 5.4 `bug-intake`：post-close 期间记录 BUG，加 unresolved_bugs
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`：含 Gap-3/4 protected rollback；`TERMINAL_EVENTS` 在 incident-resolve abort/reconstruct 落地
- Phase 6 `update --advance`：P6 矩阵（A/B/C/D/E）+ required-artifacts 解析

这些不应作为 Phase 5.3 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_3_update_task_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 5.3 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.4
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §2.1、frontmatter-schema.md §3.3、task6_progress_py_prerequisites_20260506.md、task6_plan §5.4/§13、SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§J 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 `validate_artifacts=False` 设计选择的看法）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 5.4 (`release-*` + `bug-intake`)**
   - **(B) fix before Phase 5.4**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5.4 前修
- 哪些可以推迟到 Phase 6 / Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5.4/Phase 6 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
