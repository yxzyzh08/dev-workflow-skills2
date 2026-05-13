# Claude Review Prompt — Task 6 Phase 5.2 progress.py update --event

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_2_update_event_review_20260507.md`。Phase 5.2 通过后才能进入 Phase 5.3 (`update --task`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.2 implementation** 做一次代码 review。本批是 progress.py 第二阶段：在 Phase 5.1 lock / history / replay 基础上加 `update --event` 子命令，覆盖 4 个 event 的状态机。Phase 5.3 / 5.4 / Phase 6 会在这套基础上增量加 `update --task` / `release-*` / `bug-*` / `incident-*` / `update --advance`。

本轮是代码 review。**写集**仅限：

- 扩展现有 `skills/_shared/dev_workflow/progress_state.py`（追加 `EventOutcome` dataclass、`apply_update_event`、`REVIEW_ITERATION_LIMIT` 常量与三个内部校验 helper；不动既有 `build_initial_state` / NORMAL/PROTECTED transitions）
- 扩展现有 `skills/_shared/dev_workflow/progress_replay.py`（用 `_apply_update_event_factory` 注册 4 个新 handler；`_HANDLERS` dict 现含 5 项）
- 扩展现有 `skills/workflow-protocol/scripts/progress.py`（加 `update` 子命令 + `cmd_update`；mutex group 为 5.3/6 留 `--task` / `--advance` 接口）
- 新建 tests `tests/test_apply_update_event.py`
- 新建 tests `tests/test_progress_update_event.py`
- 扩展 tests `tests/test_progress_replay.py`（加 `ReplayUpdateEventTests` class + 更新 `supported_events` 测试）

Phase 5.2 **不**实现：

- `update --task`（Phase 5.3）
- `update --advance`（Phase 6）
- `release-close` / `release-start` / `bug-intake`（Phase 5.4）
- `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`（Phase 6）
- Gap-3/4/5 protected rollback（Phase 6）
- `validate.py consistency`（Phase 6+）
- 任何 progress.md `current_stage` 推进（这是 `--advance` 的事；Phase 5.2 内 current_stage 不变）

这些不能因为它们在 5.2 里"还没写"而被当 finding。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5.1 (含 round 2) 全部 (A) closed：

- Phase 5.1 round 2: `docs/review/task6_phase5_1_progress_core_round2_review_20260507.md`（A: M1 timestamp 文档序、M2 scenario exit code 闭环）

Phase 5 在 plan §13 + 现 session 协商后被拆为 4 个子 phase：

- Phase 5.1（已闭环）：foundation（lock/history/replay）+ init + query + recover
- **Phase 5.2**（本批）：`update --event`（4 events）
- Phase 5.3：`update --task`（Stage 4 normal transitions only）
- Phase 5.4：`release-close` + `release-start` + `bug-intake`

Phase 5.2 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 279 tests in 2.273s
# OK
#  - baseline (Phase 1-4 + Phase 5.1 round 2):  230
#  - new in Phase 5.2:                           49
#    * test_apply_update_event.py     : 28
#    * test_progress_replay.py +new   :  6  (ReplayUpdateEventTests)
#    * test_progress_update_event.py  : 15

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py update --help
# all OK
```

End-to-end smoke 验证（手工跑过）：init → write-complete → review-issues (iter=1) → write-complete (revising→in-review, iter 保留) → review-passed (iter=0) → human-confirmed (approved) → 删 progress.md → recover --confirm → query 恢复一致状态。

## 阅读顺序（请严格按序读，不要跳读）

1. `docs/review/task6_phase5_1_progress_core_round2_review_20260507.md` —— Phase 5.1 closure context；Phase 5.2 在这套 lock/history/replay 上扩展
2. `docs/implementation/task6_plan_20260507.md` §5.3 / §11.1 / §13 —— update --event 命令矩阵 + atomicity + Phase 划分
3. `skills/workflow-protocol/references/command-reference.md` §2 / §2.1（update --event whitelist + sub_state 转移表 + iteration ≤7）
4. `skills/workflow-protocol/SKILL.md`（命令矩阵）
5. `skills/_shared/dev_workflow/progress_state.py`（含本批新增 `apply_update_event` / `EventOutcome`）
6. `skills/_shared/dev_workflow/progress_replay.py`（含本批新增 4 handler）
7. `skills/workflow-protocol/scripts/progress.py`（含本批新增 `cmd_update` / `update` 子命令）
8. `tests/test_apply_update_event.py`（新文件）
9. `tests/test_progress_replay.py`（含本批新增 `ReplayUpdateEventTests`）
10. `tests/test_progress_update_event.py`（新文件）

可选背景：

- `docs/review/task6_phase5_1_progress_core_review_20260507.md` —— Phase 5.1 round 1 + 两个 Medium 的来源
- `skills/_shared/dev_workflow/progress_history.py`（Phase 5.2 没动；history entry schema 仍为 `agent` / `result` / `next` 白名单）

## Phase 5.2 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 5.2 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. 工作树大量 untracked 是项目内容，不得 delete/clean/reset/revert。
3. Tests 必须用 temp dirs / fixtures，不得 mutate 真实 `docs/` / `skills/`。
4. **写集严格**（见前文写集列表）；未引入新外部依赖；未新增任何独立 module。
5. **Event 白名单严格 = `{write-complete, review-issues, review-passed, human-confirmed}`**；`issues-found` 是业务措辞，不是 event；`bug-rework` / `bug-start` / `incident-*` 是 Phase 6 territory，本批不能出现。
6. **State 机器规则严格按 command-reference.md §2.1**：
   - `write-complete`：from `{write, revising}` → `in-review`；iteration 不变
   - `review-issues`：from `in-review` → `revising`；iteration +1；新值 > 7 reject
   - `review-passed`：from `in-review` → `review-passed`；iteration 归零
   - `human-confirmed`：from `review-passed` → `approved`；**仅** `current_stage ∈ {prd-inception, srs-specification, architecture-design}`
7. **Pre-condition**：`project_state == active`（aborted/reconstructing 拒绝所有 mutating event）。
8. **Atomicity**：`update --event` 必须经 `progress_lock(root)` + `atomic.transaction()` 双写 progress.md + progress-history.md；任何一边失败 rollback 两者。
9. **History entry**：单条 entry 用 progress_history canonical 形式追加；`event` 字段使用 4 event 名字面（`write-complete` 等）；`agent` / `result` / `next` 三字段白名单不变。
10. **`apply_update_event` 是单一事实源**：`progress.py update --event` 的 forward path 与 `progress_replay.py` 的 replay handler 都通过它，不允许两条独立分支重复实现状态机（防止 forward / replay 漂移）。
11. **`updated` 字段**：`apply_update_event` 在 forward path 写入 `now`；replay handler 写入 entry timestamp。最终 recover 还会再 bump 到 recovery 时刻；这是 round 1 已确立的契约，本批不动。
12. **CLI 风格**：`update` 子命令 `--event` 在 mutually-exclusive group 内（`required=True` 在 group 上），为 5.3/6 加 `--task` / `--advance` 留位；`--event` 自身**不**用 argparse `choices=`（沿用 5.1 round 2 M2 的契约：workflow 校验失败 = exit 1，不是 CLI usage = exit 2）。

## 重点 review 项

请按以下维度逐条核对：

### A. `apply_update_event` 状态机（progress_state.py）

- 4 个 event 分支是否严格匹配 spec：
  - `write-complete`：`sub_state in {write, revising} → in-review`，iteration 不变？
  - `review-issues`：`sub_state == in-review → revising`，iteration `+1` 且新值 ≤ 7 时 OK，> 7 reject 且消息含 "escalate"？（注意是新值 > 7 时 reject，所以 iteration=7 仍允许、iteration=8 不允许）
  - `review-passed`：`sub_state == in-review → review-passed`，iteration 归零；`history_next` 在 gated stage 是 `human-confirmed`、非 gated 是 `advance`？
  - `human-confirmed`：`sub_state == review-passed → approved`；reject 非 gated stage（错误消息含 "gated stages" 与具体 current_stage）？
- `_validate_active_project`：terminal `project_state ∈ {aborted, reconstructing}` 是否 reject？
- `_validate_sub_state_value` / `_validate_review_iteration_value`：bool 是否被识别为非 int（Python int 子类问题）？字符串非合法 sub_state 是否 reject？
- 返回 `EventOutcome` 是否 frozen？`new_state` 是否仅触动 sub_state / review_iteration / updated 三字段，其它字段（含 nested `bug_flow` / `unresolved_bugs` / `artifacts`）是否原样复制？
- `now` 是否用同一 `_validate_timestamp` helper 校验（与 `build_initial_state` 一致）？
- `EVENTS` set 是否仍为 `{write-complete, review-issues, review-passed, human-confirmed}`？是否未引入新 event？

### B. `progress_replay.py` 扩展

- `_apply_update_event_factory(event_name)` 是否正确把 `apply_update_event` 包装成 `ApplyFn`？
- 4 个 handler 是否经 dict comprehension 注册到 `_HANDLERS` 中？
- handler 内 `apply_update_event(state, event_name, now=entry.timestamp)`：用 entry timestamp 作为 `now` 是否符合 round 1 设计（`updated` 字段反映最后一次事件时间，最终被 recover 覆盖）？
- ProgressStateError → ReplayError 包装是否带 entry timestamp，便于诊断？
- `supported_events()` 现在是否返回 5 项？
- 5.1 round 2 的 timestamp 文档序检查（M1 fix）有没有被本批意外触动？replay 仍按文档序，monotonicity check 在 handler dispatch 之前。

### C. `progress.py update` CLI

- `cmd_update` 的执行顺序：lock → 检查 progress.md/history.md 存在 → 读 + 解析 → `apply_update_event` 校验 → 拼装 history entry → atomic.transaction 双写 → 释放锁。任何一步失败必须 exit 1 + stderr 提示 + 文件字节级未改？
- `argparse` mutually-exclusive group：`--event` 是当前唯一选项；group `required=True`；缺失时 argparse exit 2（与 5.1 init `--scenario` 走 exit 1 的设计**有意区分**：Phase 5.2 唯一选项缺失是 CLI usage error，5.3 加 `--task` 后 group 仍 required-one-of 且缺失走 exit 2；event/task 名本身的合法性走 exit 1）？
- `--event` 描述文本是否说明了：白名单值 + 走 `apply_update_event` 校验路径（与 `--scenario` 同一契约：unknown 不走 argparse choices）？
- 是否复用 `_utc_now_iso` / `progress_lock` / `atomic.transaction`，不另起逻辑？
- 错误消息：illegal sub_state、unknown event、aborted project 是否都通过 `apply_update_event` 抛 `ProgressStateError` → `cmd_update` 捕获 → exit 1？
- 成功输出：stdout 一行带 event 名 + summary；stderr 仅 lock 等错误时使用？

### D. Tests

- `test_apply_update_event.py`（28 测试）：
  - 4 events × 各自 happy from-state（write/revising/in-review/review-passed）+ 各自 illegal from-state？
  - iteration 边界：6→7 OK、7→8 reject？
  - human-confirmed × 各 gated stage（PRD/SRS/Architecture）通过；× 4 个非 gated stage（development/testing/delivery/project-retrospective）reject？
  - terminal `project_state` 拒绝？
  - unknown event / invalid now / invalid sub_state value / negative iteration 全部 reject？
  - field preservation（unresolved_bugs / bug_flow / release / created）？
- `test_progress_replay.py` 新增 `ReplayUpdateEventTests`（6 测试）：
  - full review cycle（init→write-complete→review-passed→human-confirmed → approved）
  - review-issues 累积 iteration（write-complete + review-issues × 2 = iteration 2）
  - review-passed 重置 iteration
  - 非法 transition reject（init 后直接 review-passed → ReplayError 含 "review-passed" 和 "in-review"）
  - human-confirmed 在 sub_state ≠ review-passed 时 reject
  - replay handler 用 entry timestamp 写入 `updated`
- `test_progress_update_event.py`（15 测试）：
  - 完整 review cycle（5 个 event 串联）+ frontmatter / history 一致性
  - 各种 reject（unknown event / illegal transition / non-gated human-confirmed / iteration limit / aborted project）byte-for-byte 不动
  - argparse：缺 --event 退 2、`update --help` OK
  - file guard：缺 progress.md / 缺 history / 损坏 frontmatter 全 exit 1
  - lock 阻塞：lock 持有时 update 退 1 + 文件不动
  - recover roundtrip：跑完 5 event，删 progress.md，recover --confirm 后 sub_state / review_iteration / current_stage / created / project_name 与 cycle 末尾一致
- 是否所有 CLI 测试用 `tempfile.TemporaryDirectory()` 隔离？
- 是否 `_seed` helper 已 silent 抑制 init 的 stdout/stderr（避免 noise）？
- 是否有用 `_rewrite_progress` 测 hook 把 current_stage 强写到 development（用于测 non-gated human-confirmed reject）？这种 test-only frontmatter rewrite 是否清晰标注、不污染产线代码？

### E. 与既有 invariant 的一致性

- Phase 5.1 round 2 的 60+ 个测试是否仍全部通过？特别是 `test_progress_replay.py` 的 timestamp 文档序 / handler dispatch ordering 测试？
- `progress_lock.py` / `progress_history.py` 是否未被本批触动？
- `init` / `query` / `recover` 三子命令的整体行为是否与 5.1 round 2 一致？特别是 recover 在 5.2 后能 replay 完整 update --event 历史？
- `atomic.transaction()` 仍是 progress + history 多文件写入的唯一原子化入口？
- progress-history.md 头部 `# Project History` 行仍保留？append 时入口分隔符仍是恰好 1 个空行？

### F. 设计 / 可维护性

- `apply_update_event` 单一事实源设计是否清晰（forward + replay 共用一份状态机）？避免了状态机被复制两份的漂移风险？
- 错误消息是否对 caller 友好（含字段名、具体值、上一条 timestamp、合法集合）？
- `EventOutcome` dataclass 字段（new_state / history_summary / history_result / history_next）是否合理、可被 caller 直接 surface 给 history entry 与日志？
- mutex group 设计是否为 5.3 (`--task`) 与 Phase 6 (`--advance`) 留出足够扩展空间？
- import 顺序与 `noqa: E402` 是否仍合理？

### G. 已知 Phase 5.3+ 后续工作（不在本 review 评判范围）

- Phase 5.3 `update --task`：扩展 mutex group 加 `--task <Tn> --status <new>`；注册若干 task handler；可能解锁 `progress_history.py` 的 `task` 字段白名单
- Phase 5.4 `release-close` / `release-start` / `bug-intake`：跨多文件原子（progress + N 个 BUG frontmatter）；`release-start` 在 transaction 内修 BUG `target_release` / `consumed_in_release`
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + `update --advance`；`TERMINAL_EVENTS` 在 incident-resolve abort/reconstruct 时落地

这些不应作为 Phase 5.2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_2_update_event_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 5.2 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.3
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §2/§2.1、task6_plan §5.3/§11.1、SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 5.3 (`update --task`)**（5.3 之前可选清理 list）
   - **(B) fix before Phase 5.3**（必修 list；为何 Phase 5.3 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5.3 前修
- 哪些可以推迟到 Phase 5.4/Phase 6/Phase 7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5.3/5.4/Phase 6 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
