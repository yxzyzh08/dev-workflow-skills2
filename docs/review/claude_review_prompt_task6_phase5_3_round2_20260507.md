# Claude Review Prompt — Task 6 Phase 5.3 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_3_update_task_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 5.4 (`release-close` / `release-start` / `bug-intake`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.3 Round 2 fixes** 做一次回归 review。Round 1 评审（Codex 出具）给出 **(B) fix before Phase 5.4** 结论，列出 0 High / 2 Medium / 2 Low；本轮请确认 4 个 finding 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：

- Round 1 review report：`docs/review/task6_phase5_3_update_task_review_20260507.md`
- Round 1 实施代码：`skills/_shared/dev_workflow/progress_artifacts.py` / `progress_state.py` / `progress_replay.py`、`skills/workflow-protocol/scripts/progress.py`、`tests/test_progress_artifacts.py` / `test_apply_update_task.py` / `test_progress_update_task.py` / `test_progress_replay.py`
- Round 2 fixes 的 diff（仅触动 `progress_artifacts.py` / `progress_state.py` / `progress_replay.py` / `progress.py` 的 docstring；tests 加了若干 class）

**不要**要求 Phase 5.4 / Phase 6 已实现。

## Round 1 baseline

- Phase 5.3 Round 1 review report: `docs/review/task6_phase5_3_update_task_review_20260507.md`
- Recommendation: **(B) fix before Phase 5.4 (`release-*` + `bug-intake`)**
- Findings: 0 High / **2 Medium (M1, M2)** / **2 Low (L1, L2)**
  - **M1** — `apply_update_task` 未继承 Phase 5.2 round 2 M2 的 `review_iteration > 7` 入口校验
  - **M2** — `load_breakdown_with_tasks` 接受 `total_tasks` 非 int / 缺失（spec 要求必含 int）
  - **L1** — `_apply_update_task` docstring 与 `_run_update_pipeline` 注释仍说 replay 重读 artifact，与 `validate_artifacts=False` 设计相反
  - **L2** — 测试缺 revision-loop 转移（`test-review→test-revising`、`code-review→code-revising`、`code-revising→code-review`）

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 383 tests in 3.314s
# OK
#  - baseline before round 1:  367 (Phase 1-4 + Phase 5.1/5.2 round 2 + Phase 5.3 round 1)
#  - round 2 net change:        +16
#    * test_progress_artifacts.py     : +4 (M2 reject paths + zero allowed; renamed 1)
#    * test_apply_update_task.py      : +9 (M1 ×4 + L2 ×5)
#    * test_progress_update_task.py   : +3 (M1 ×1 + L2 ×2)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

## Round 2 修复摘要（请逐条核对是否到位）

### M1 — `apply_update_task` 入口校验加 `review_iteration > 7` guard

- 修改：`skills/_shared/dev_workflow/progress_state.py:apply_update_task`
  - 在 current_stage 校验之后、release 校验之前调 `_validate_review_iteration_value(state.get('review_iteration', 0))`
  - 复用 Phase 5.2 round 2 既有的 helper（无新代码）
  - 注释说明 update --task 不直接动 review_iteration，但读到并保留越界值会让后续命令继承 corruption
- 新增 / 修改 regression tests：
  - **new** `tests/test_apply_update_task.py:IterationOverLimitTaskTests`（4 测试）：planning-done / test-writing / verified × iter=8 全 reject；iter=7 入口仍允许
  - **new** `tests/test_progress_update_task.py:UpdateTaskIterationOverLimitTests`（1 测试）：CLI 层面 forge progress.md `review_iteration=8` 后 update --task 退 1，文件字节不动

### M2 — `load_breakdown_with_tasks` 严格校验 `total_tasks`

- 修改：`skills/_shared/dev_workflow/progress_artifacts.py`
  - `load_breakdown_with_tasks`：missing / 非 int / bool / 负值 → `ProgressArtifactError`，消息含 rel_path、字段名、type、value
  - `BreakdownInfo.total_tasks` 类型从 `int | None` 收紧为 `int`
  - count-vs-declared 一致性仍 deferred 到 Phase 6 advance（设计契约不变）
- 新增 / 修改 regression tests（`tests/test_progress_artifacts.py`）：
  - **renamed** `test_breakdown_total_tasks_optional` → `test_breakdown_total_tasks_string_rejected`（断言 reject 而非 fallback to None）
  - **new** `test_breakdown_total_tasks_missing_rejected`、`test_breakdown_total_tasks_bool_rejected`、`test_breakdown_total_tasks_negative_rejected`、`test_breakdown_total_tasks_zero_allowed`

### L1 — replay artifact 注释统一刷新

- 修改：`progress_replay.py:_apply_update_task` docstring + `progress.py:_run_update_pipeline` 内注释
  - 旧文案"replay re-evaluates artifact preconditions ... raises if artifacts diverged"
  - 新文案明确"replay validates state-machine legality ONLY; review report files mutate from skeleton to pass/fail across transitions, so re-reading current artifacts during replay would falsely fail historical transitions. Forward path is the gatekeeper for artifact state at write time."
  - root 在 update-task replay handler 中改述为"required defensively for forward compatibility (Phase 5.4+ may extend artifact-aware replay)"
- 无新测试（注释/文档纯刷新）

### L2 — revision-loop 转移测试补齐

- 新增 / 修改 regression tests：
  - **new** `tests/test_apply_update_task.py:RevisionLoopTransitionsTests`（5 测试）：
    - test-review → test-revising
    - test-revising 回 test-review（要 pending skeleton）
    - code-review → code-revising
    - code-revising 回 code-review（要 pending skeleton）
    - code-revising 回 code-review 当 report 已是 pass → reject
  - **new** `tests/test_progress_update_task.py:UpdateTaskRevisionLoopTests`（2 测试）：
    - CLI test-review/test-revising 完整 loop（先 pass→revising→pending skeleton→test-review）
    - CLI code-review/code-revising 完整 loop（同上 code path）

## 重点 review 项

请按以下维度逐条核对：

### A. M1 fix 是否到位

- `apply_update_task` 是否在所有非 transitional check（task_id 格式 / status 合法 / now / project_state / current_stage）之后、release 校验之前调 `_validate_review_iteration_value`？
- 错误消息复用 Phase 5.2 round 2 的"review_iteration is N, exceeding the limit of 7 ... escalate"文案？
- 与 `apply_update_event` 的 iter guard 行为一致（iter=7 入口允许、iter=8 入口拒）？
- 4 个单测 + 1 个 CLI 测试是否覆盖各种 task transition 路径（planning-done / test-writing / verified / + CLI integration）？
- 既有 round 1 的 37 个 apply_update_task 测试是否仍全过？

### B. M2 fix 是否到位

- `load_breakdown_with_tasks` 是否真的把 missing / non-int / bool / negative 全 reject？
- 错误消息含 rel_path + field name + actual type + actual value？
- `BreakdownInfo.total_tasks` 类型注解从 `int | None` 改为 `int`？
- `_check_planning_done_artifacts` 调用 `load_breakdown_with_tasks` 的路径是否仍正常工作？
- 5 个 artifact 测试是否覆盖：string / missing / bool / negative reject + zero allowed + 既有 word-boundary / wrong-type / happy 不破坏？
- count-vs-declared 仍是 Phase 6 deferred，没有提前实现？

### C. L1 fix 是否到位

- `_apply_update_task` docstring 现在明确说 replay validates state-machine legality only？
- root 描述改为 "required defensively"？
- `_run_update_pipeline` M1 注释说明"forward 是 artifact 守门员，replay 不重读"，避免阅读者认为 replay 还会捕到 artifact 篡改？

### D. L2 fix 是否到位

- 5 个单测 × 2 个 CLI 测试是否覆盖 `test-review→test-revising` / 反向 / `code-review→code-revising` / 反向 / 反向但 report 已 pass reject？
- CLI revision loop 测试是否完整跑通：pass 进入 revising → 重置 skeleton → 回 review？
- 文件字节级状态在 reject 路径是否仍 unchanged？

### E. 既有 invariant 是否保持

- Phase 5.1 + 5.2 + 5.3 round 1 的 367 个测试是否仍全过？
- `progress_lock.py` / `progress_history.py` / `init` / `query` / `recover` 既有行为保留？
- `apply_update_event` 路径未被本批改动（M1 fix 仅触动 `apply_update_task`）？
- argparse mutex group / dispatcher / `_run_update_pipeline` / atomic.transaction 链路未受影响？

### F. 测试质量

- M1 单测：是否同时检查 exception 类型 + 消息含 "review_iteration"、"8"、"escalate" 三个关键 token？
- M1 CLI 测试：是否 byte-for-byte 验证 progress.md 与 progress-history.md 未被改写？
- M2 测试：是否覆盖 missing / string / bool / negative / zero？
- L2 测试：是否检查 development_state.task_states[Tn] 在每步后的具体值（避免 false-pass）？
- 所有 round 2 新测都用 `tempfile.TemporaryDirectory` 隔离？

### G. Cross-doc 一致性

- `command-reference.md §2.1` Stage 4 task 表（normal + protected）与 round 2 后的实现仍一致？
- `frontmatter-schema.md §3.2` 关于 `task-breakdown.total_tasks` 必含 int 的要求现在被严格执行？
- Phase 5.2 round 2 closure 的 M2 invariant（review_iteration > 7 entry check）现在覆盖 update --event 与 update --task 两条路径？
- `progress_replay.py` docstring 现在准确反映 5.3 设计选择（state-machine legality only，不重读 artifact）？

### H. 设计 / 可维护性

- `_validate_review_iteration_value` 作为 cross-command shared helper 的位置 / 命名是否合理？将来 Phase 5.4 release-* 与 Phase 6 bug-* 应继续复用？
- `BreakdownInfo.total_tasks: int` 类型收紧是否影响 Phase 6 advance 的 count consistency 实现路径（应该不会，advance 直接用 `info.total_tasks` 与 `len(info.declared_tasks)` 比较）？
- L1 文档刷新后，是否任何 lookups（grep "re-evaluates artifact"）已无残留？

### I. 已知 Phase 5.4+ 后续工作（不在本 review 评判范围）

- Phase 5.4 `release-close` / `release-start` / `bug-intake`：跨多文件原子（progress + N 个 BUG frontmatter）；release-start 在 transaction 内修 BUG `target_release` / `consumed_in_release`
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`：含 Gap-3/4/5 protected rollback；`TERMINAL_EVENTS` 在 incident-resolve abort/reconstruct 落地
- Phase 6 `update --advance`：P6 矩阵（A/B/C/D/E）+ required-artifacts 解析 + breakdown count 一致性

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_3_update_task_round2_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 4 / 5.1 / 5.2 round 2 review 结构）：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.4
2. **Round 1 Findings 回归状态** — M1 / M2 / L1 / L2 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed
3. **New Findings (Round 2)** — 没有则注明 "No new findings"
4. **Cross-Finding Consistency Check**
5. **Round 2 Implementation Quality Spot-checks** — apply_update_task 加 iter guard、load_breakdown_with_tasks 加 total_tasks 校验、docstring 刷新、新增 16 个 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§H 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 5.4 (`release-*` + `bug-intake`)**
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
