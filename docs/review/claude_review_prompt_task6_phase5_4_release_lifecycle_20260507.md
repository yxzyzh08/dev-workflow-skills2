# Claude Review Prompt — Task 6 Phase 5.4 progress.py release lifecycle + bug-intake

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_4_release_lifecycle_review_20260507.md`。Phase 5.4 通过后 Phase 5 子拆分整体闭环，可进入 **Phase 6**（`bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + `update --advance` + Gap-3/4/5）。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.4 implementation** 做一次代码 review。本批是 progress.py Phase 5 子拆分的最后一段：在 Phase 5.1 / 5.2 / 5.3 基础上加 `release-close` / `release-start` / `bug-intake` 三个子命令。这是 Phase 5 中最复杂的一批，因为 `release-start` 需要在同一个 atomic.transaction 里同时改 progress.md + progress-history.md + N 个 BUG-NNN.md（fan-out 跨文件原子写）。

本轮是代码 review。**写集**仅限：

- 扩展 `skills/_shared/dev_workflow/progress_state.py`（追加 3 个 outcome dataclass + 3 个 apply 函数 + `RELEASE_START_SUBTYPES` 常量 + `_RELEASE_VERSION_RE` / `_RELEASE_START_STAGE_MAP`）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`（注册 3 个 handler + `_kv_tokens` helper；docstring 更新到 5.4 现状；`supported_events()` 现 9 项）
- 扩展 `skills/workflow-protocol/scripts/progress.py`（`_run_update_pipeline` 加 `extra_writes_factory` 钩子；3 个新 cmd_*；BUG fan-out 在 `_release_start_extra_writes` 内构造）
- 新建 tests `tests/test_apply_release_close.py` / `test_apply_release_start.py` / `test_apply_bug_intake.py`
- 新建 tests `tests/test_progress_release_lifecycle.py` / `test_progress_bug_intake.py`
- 扩展 tests `tests/test_progress_replay.py`（`ReplayReleaseLifecycleTests` + `supported_events` 集合）
- 调整 tests `tests/test_progress_recover.py` / `tests/test_progress_replay.py`（之前用 `release-close` 当"未支持事件"样本，现已被支持，换成 Phase 6 的 `bug-start`）

Phase 5.4 **不**实现：

- Phase 6: `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` / `update --advance` / Gap-3/4/5 protected rollback
- `validate.py consistency`（Phase 6+）
- BUG 文件的 doc-guardian Class 1-7 完整校验（Phase 6 `validate.py consistency` / Phase 6 advance 的 P6 矩阵承担）；Phase 5.4 仅做 thin frontmatter 检查（type / target_release / consumed_in_release）
- breakdown.md `total_tasks == len(declared_tasks)` 一致性（Phase 6 advance）

这些不能因为它们在 5.4 里"还没写"而被当 finding。

## 当前工作背景

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5.1 / Phase 5.2 / Phase 5.3 全部 (A) closed：

- Phase 5.3 round 2: `docs/review/task6_phase5_3_update_task_round2_review_20260507.md`（A: M1 task 路径 iter guard / M2 total_tasks 严格校验 / L1 docstring 刷新 / L2 revision-loop 测试）

Phase 5 sub-phase 切分（user agreed 4-split）：

- Phase 5.1（已闭环）：foundation（lock/history/replay）+ init + query + recover
- Phase 5.2（已闭环）：`update --event`
- Phase 5.3（已闭环）：`update --task`
- **Phase 5.4**（本批）：`release-close` + `release-start` + `bug-intake`（Phase 5 收官）

Phase 5.4 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 454 tests in 3.878s
# OK
#  - baseline (Phase 1-4 + Phase 5.1/5.2/5.3 round 2):  383
#  - new in Phase 5.4:                                   71
#    * test_apply_release_close.py        : 13
#    * test_apply_release_start.py        : 19
#    * test_apply_bug_intake.py           : 12
#    * test_progress_release_lifecycle.py : 11
#    * test_progress_bug_intake.py        : 10
#    * test_progress_replay.py +new       :  6  (ReplayReleaseLifecycleTests)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 7 个子命令：init / query / recover / update / release-close / release-start / bug-intake
```

End-to-end smoke 已通过 `test_release_start_with_unresolved_bugs_fans_out_to_BUG_files`：seed→bug-intake×2→release-start，验证 BUG-001 / BUG-002 frontmatter 的 target_release / consumed_in_release 被同步设置为 0.2，progress.md unresolved_bugs 清空。`test_release_start_recover_roundtrip_preserves_state` 验证 recover 重建后状态完全一致（含 BUG 文件状态）。

## 阅读顺序

1. `docs/review/task6_phase5_3_update_task_round2_review_20260507.md` —— Phase 5.3 closure
2. `docs/implementation/task6_plan_20260507.md` §5.2 / §5.5 / §11.1 / §11.2 —— release lifecycle 命令矩阵 + atomicity + multi-file BUG 原子事务
3. `skills/workflow-protocol/references/command-reference.md` §5（release-close）/ §6（release-start）/ §7（bug-intake）
4. `skills/doc-guardian/references/frontmatter-schema.md` §3.4（bug-report 的 target_release / consumed_in_release nullable + 必含语义）
5. `skills/_shared/dev_workflow/progress_state.py`（含本批新增 3 个 apply 函数 + outcome dataclass）
6. `skills/_shared/dev_workflow/progress_replay.py`（含 3 个新 handler + `_kv_tokens` helper）
7. `skills/workflow-protocol/scripts/progress.py`（含 `_run_update_pipeline` 的 `extra_writes_factory` 钩子 + 3 个 cmd_*）
8. `tests/test_apply_release_close.py`、`tests/test_apply_release_start.py`、`tests/test_apply_bug_intake.py`
9. `tests/test_progress_release_lifecycle.py`、`tests/test_progress_bug_intake.py`
10. `tests/test_progress_replay.py`（含 `ReplayReleaseLifecycleTests`）

## Phase 5.4 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 5.4 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. Tests 必须用 `tempfile.TemporaryDirectory` 隔离。
3. **State 机器规则严格按 command-reference.md §5/§6/§7**：
   - `release-close`：active + project-retrospective + review-passed → release_state=closed + release_close_reason="stage-7-completed" + previous_releases.append
   - `release-start --version --scenario`：closed + 版本严格大于所有 prior + scenario ∈ {S2-1, S2-2, S2-3}（**S2-4 forbidden**，必须转 S3 新 project）→ 重置 release / scenario / scenario_subtype / current_stage / sub_state / artifacts / 清 unresolved_bugs / 清 development_state
   - `bug-intake --bug`：active + closed + BUG file 存在 + frontmatter (type=bug-report + target_release=null + consumed_in_release=null) + 不重复 → unresolved_bugs.append
4. **跨文件原子 fan-out（release-start）**：在同一 atomic.transaction 内：progress.md + progress-history.md + N 个 BUG-NNN.md 的 frontmatter (target_release / consumed_in_release / updated)。任一失败回滚全部。
5. **Replay 不触碰 BUG 文件**（与 update-task 设计一致）：release-start replay 只应用 progress 状态机，BUG 文件的 mutation 由 forward 在写时一次性确定。这是 Phase 5.3 round 1 已确立的"replay validates state-machine legality only"设计选择的延展。
6. **M1 + M2 + L1 invariants 全继承**：3 条新命令路径都共享 `_run_update_pipeline`（含 history parse + composed-history replay + state diff），且 3 个 apply 函数都调 `_validate_review_iteration_value`。
7. **`progress_history.py` 字段白名单仍 `agent / result / next` 不变**；version / scenario / bug 信息全部走 summary canonical token (`version=` / `scenario=` / `bug=`)，replay 用 `_kv_tokens` 反解。
8. **Phase 5 子拆分整体闭环**：Phase 5.4 通过后，progress.py 现已实现 init / query / recover / update --event / update --task / release-close / release-start / bug-intake 共 8 个生效子命令；Phase 6 在此基础上加 bug-start / bug-close / bug-rework / incident-start / incident-resolve / update --advance + Gap-3/4/5 + TERMINAL_EVENTS 落地。

## 重点 review 项

请按以下维度逐条核对：

### A. `apply_release_close` 状态机

- 前置校验完整：active project / iter ≤ 7 / release_state=active / current_stage=project-retrospective / sub_state=review-passed / release 格式 / release 不在 previous_releases（防 out-of-band 篡改）？
- mutation 仅触动 release_state / release_close_reason / previous_releases / updated；其它字段（含 development_state / unresolved_bugs / bug_flow）原样保留？
- ReleaseCloseOutcome frozen + history 三字段（summary / result / next）齐全？
- 错误消息含具体期望值与实际值（便于 caller 排错）？
- 13 单测覆盖：happy + 各前置 reject + 字段保留 + history 字段填充 + outcome frozen？

### B. `apply_release_start` 状态机

- 前置校验：active project / iter ≤ 7 / release_state=closed / scenario_subtype ∈ {S2-1,-2,-3}（**S2-4 / S1 / S3 / S2 / S2-7 全部 reject**）/ version 格式 `^\d+\.\d+$` / version 严格大于所有 prior（current + previous_releases 中的最大值）？
- mutation 完整：release / release_state=active / release_close_reason=null / scenario=S2 / scenario_subtype / current_stage 按 stage_map / sub_state=write / iter=0 / artifacts 重置（srs / acceptance_plan 用新版本路径，integration_plan / architecture_delta=null，prd / architecture 项目级保留）/ unresolved_bugs=[] / development_state 删除？
- 返回 `consumed_bugs` tuple 给 CLI 做 BUG 文件 fan-out？
- `RELEASE_START_SUBTYPES` 常量 frozenset({S2-1, S2-2, S2-3}) 暴露给 CLI argparse help？
- history summary 含 `version=` 与 `scenario=`/`scenario_subtype=` token（replay 必须能反解）？
- 19 单测覆盖：3 scenario × happy / artifacts 重置 / development_state 清 / consumed_bugs / 各种 reject（version 不递增 / version 等于 / version 格式 / scenario 非法 / aborted / iter > 7 / invalid now）？

### C. `apply_bug_intake` 状态机

- 前置：active project / iter ≤ 7 / release_state=closed / bug_path 非空 string / 不在 unresolved_bugs（duplicate guard）？
- mutation 仅 unresolved_bugs.append + updated；其它字段保留？
- history summary 含 `bug=<path>` token（replay 反解）？
- 12 单测覆盖：first/multi intake / 字段保留 / history 字段 / 各 reject（active / aborted / duplicate / 空 path / non-string / iter > 7 / invalid now）？

### D. `progress_replay.py` 扩展

- `_kv_tokens(entry)` 提取 summary + result 中的 `key=value` token？兼容 `,` 与空格分隔？
- 3 个 handler 都 `del root` 明确忽略 root 参数？（release lifecycle 不读 BUG/artifact files during replay）
- `_apply_release_start_handler` 缺 version / scenario_subtype token 时 raise ReplayError，错误消息提示 `expected version=<x.y> scenario=<S2-x>`？
- `_apply_bug_intake_handler` 缺 `bug=` token 时 raise ReplayError？
- `_HANDLERS` 字典含 9 项（init + 4 update events + update-task + release-close + release-start + bug-intake）？
- `supported_events()` 测试现在断言 9 项？
- module docstring 更新到 5.4 现状？unsupported-event 错误消息提到 5.4 实际范围？

### E. `progress.py` CLI

- `_run_update_pipeline` 的 `extra_writes_factory` 钩子位置正确：在 `replayed_state == outcome.new_state` 一致性比对**之后**、`with transaction()` **之前**调用？factory 失败（ProgressStateError / ProgressArtifactError / FrontmatterError / OSError）走 exit 1 不写文件？
- `cmd_release_close`：仅调 `_run_update_pipeline` 即可（无 extra writes）；event_name="release-close"？
- `cmd_bug_intake`：先做 thin BUG frontmatter 校验（`_validate_bug_for_intake`，覆盖 missing / parse 失败 / 非 bug-report / target_release 非 null / consumed_in_release 非 null / duplicate 在 unresolved_bugs）；通过后调 `_run_update_pipeline`，bug_path 用相对 root 的 forward-slash 形式？
- `cmd_release_start`：argparse `--version` / `--scenario` 缺失走 exit 2（CLI usage error）；其它前置失败走 exit 1（ProgressStateError）；`_release_start_extra_writes` 工厂为每个 consumed BUG 读 + 改 frontmatter（target_release + consumed_in_release + updated）+ render，返回 `(abs_path, new_text)` 列表？
- `_read_bug_for_release_start`：raise ProgressArtifactError 当 BUG 文件 missing / FrontmatterError / type 错 / target_release 已 set / consumed_in_release 已 set？
- argparse 子命令 layout：`release-close` 仅 --agent；`release-start` 含 --version / --scenario / --agent；`bug-intake` 含 --bug (required) + --agent？
- main dispatcher 三个分支齐全？

### F. tests/test_apply_release_close.py + test_apply_release_start.py + test_apply_bug_intake.py

- 单测全部 pure（无 file I/O 除非生成 fixture）？
- HappyPathTests / RejectionTests / ContractTests 风格一致？
- 所有 reject 路径都断言 ProgressStateError + 关键消息 token？
- field preservation 测试（release-close 保留 development_state / unresolved_bugs；release-start 重置 development_state / artifacts；bug-intake 仅触动 unresolved_bugs + updated）？

### G. tests/test_progress_release_lifecycle.py + test_progress_bug_intake.py

- 复用 Phase 5.3 风格的 `_install_test_stage_advance_handler` + `_FakeClock` patch？合成 `test-stage-advance` event 仅在 patched scope 内有效？
- `_seed_stage_7` / `_seed_post_close` helpers 把 progress.md 与 history 同步 forge（progress.md 的 frontmatter 改 + history 加合成 advance entry），保证 M1 一致性 check 不误伤？
- BUG fan-out 测试覆盖：双 BUG happy path + 1 个 stale BUG（target_release 已 set）整批 reject + recover roundtrip 后 BUG 状态保留？
- bug-intake CLI 测试覆盖：happy / 多次 / recover roundtrip / 各 reject（active release / missing BUG / 错 type / target_release 已 set / consumed_in_release 已 set / duplicate）+ 文件字节级不动？
- 所有 CLI 测试用 `_FakeClock` 保证 timestamp 单调，避免 forge 的 advance entry 与系统时钟冲突？

### H. tests/test_progress_replay.py 扩展

- `ReplayReleaseLifecycleTests` 6 测试：release-close happy / release-start happy + token 反解 / release-start missing tokens reject / bug-intake happy / bug-intake missing bug token reject / release-start replay does not touch BUG files（用空 tempdir 验证）？
- `supported_events_in_phase_5_4` 集合恰好 9 项？
- 既有 `test_unknown_event_rejected` 改用 Phase 6 的 `bug-start` 作为 sample？同步 `test_progress_recover.test_recover_rejects_history_with_unsupported_event`？

### I. 既有 invariant 是否保持

- Phase 5.1 + 5.2 + 5.3 round 2 的 383 个测试是否仍全过？
- `progress_lock.py` / `progress_history.py` / `progress_artifacts.py` / `init` / `query` / `recover` / `update --event` / `update --task` 行为完全保留？
- M1 (history parse + composed-history replay + state diff) + M2 (review_iteration > 7 entry guard) 在 3 条新命令路径上都生效？
- argparse 主层级现 7 个子命令，没遗漏 dispatcher？
- replay `validate_artifacts=False` 设计在 release-start BUG fan-out 上一致执行（replay 不读 BUG 文件，因为 BUG 文件 lifecycle 是"intake null → release-start set → 永不 reset"，replay 时刻读到的是终态）？

### J. 设计 / 可维护性

- 3 个 outcome dataclass 形状是否便于 `_run_update_pipeline` 鸭子类型？（`new_state` / `history_summary` / `history_result` / `history_next`，其中 ReleaseStartOutcome 多一个 `consumed_bugs` 由 factory 用而 pipeline 忽略）
- `extra_writes_factory` 闭包设计是否便于 Phase 6 `update --advance` 复用？
- BUG fan-out 错误消息：哪个 BUG / 哪个字段 / 期望值 / 实际值 都齐全？
- `_validate_bug_for_intake` 与 `_read_bug_for_release_start` 两个 helper 的职责区别清晰（前者用于 bug-intake 的 thin pre-flight，后者用于 release-start 的 fan-out 准备阶段）？
- import 顺序与 `noqa: E402` 仍合理？

### K. 已知 Phase 6 后续工作（不在本 review 评判范围）

- Phase 6 `bug-start` / `bug-close` / `bug-rework`：active Bug Flow 入口/出口/重路由，含 Gap-3/4/5 protected task transitions
- Phase 6 `incident-start` / `incident-resolve`：workflow-incident-analysis stage + `TERMINAL_EVENTS` 在 abort/reconstruct 时落地
- Phase 6 `update --advance`：P6 矩阵（A/B/C/D/E）+ required-artifacts 解析 + breakdown count 一致性 + cross-progress doc validation
- Phase 6 `validate.py consistency`：跨 progress.md + 全部 doc 的 cross-cutting 校验（Class 8）

这些不应作为 Phase 5.4 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_4_release_lifecycle_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 5.4 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §5/§6/§7、frontmatter-schema.md §3.4、task6_plan §5.2/§5.5/§11.1/§11.2、SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§J 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 BUG fan-out 在 atomic transaction 中的多文件原子保证、与 replay-skips-BUG-files 设计的看法）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 6 (`bug-*` + `incident-*` + `update --advance`)**
   - **(B) fix before Phase 6**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 6 前修
- 哪些可以推迟到 Phase 7 polish
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6 设计讨论；如发现 Phase 6 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
