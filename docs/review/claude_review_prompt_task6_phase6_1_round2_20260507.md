# Claude Review Prompt — Task 6 Phase 6.1 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_1_bug_flow_entry_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 6.2 (`bug-rework`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.1 Round 2 fixes** 做一次回归 review。Round 1 评审给出 **(B) fix before Phase 6.2** 结论，列出 0 High / 1 Medium / 1 Low；本轮请确认两个 finding 全部已修。

本轮范围：

- Round 1 review report：`docs/review/task6_phase6_1_bug_flow_entry_review_20260507.md`
- Round 2 fixes 的 diff（仅触动 `progress_artifacts.py` / `progress_state.py` / `progress.py` / `tests/test_progress_artifacts.py` / `tests/test_apply_bug_start.py` / `tests/test_progress_bug_flow.py`）

**不要**要求 Phase 6.2 已实现。

## Round 1 baseline

- Phase 6.1 Round 1 review report: `docs/review/task6_phase6_1_bug_flow_entry_review_20260507.md`
- Recommendation: **(B) fix before Phase 6.2 (`bug-rework`)**
- Findings: 0 High / **1 Medium (M1)** / **1 Low (L1)**
  - **M1** — `load_bug_report` 对 BUG frontmatter 必填字段 / bug_id 正则 / bug_id 与 path stem 一致 / nullable 字段必含 / root_cause enum 等约束校验不足
  - **L1** — `apply_bug_start` 在 dev root cause + 空 rollback 时，未在 history_result/next 持久化 "需 development-planning-write 重新路由" 的提示

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 575 tests in 4.577s
# OK
#  - baseline before round 1:  553 (Phase 1-5 + Phase 6.1 round 1)
#  - round 2 net change:        +22
#    * test_progress_artifacts.py  +10  (M1 严格 BUG schema)
#    * test_apply_bug_start.py     +4   (L1 PlanningRouteNoteTests)
#    * test_progress_bug_flow.py   +8   (L1 PlanningRoutePersistenceTests + M1 BugStartMalformedFrontmatterTests)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

## Round 2 修复摘要

### M1 — `load_bug_report` 严格 BUG schema 校验

- 修改：`skills/_shared/dev_workflow/progress_artifacts.py:load_bug_report`
  - 新增 `_BUG_ID_RE = re.compile(r"^BUG-\d{3}$")` + `_BUG_ROOT_CAUSE_VALUES = frozenset({"srs", "architecture", "development", "prd-exception"})`
  - bug_id：require key present + regex match + 等于 `Path(bug_path).stem`
  - found_in_release：require key present + 非空 string
  - target_release / consumed_in_release：require key present（"value 可为 null 但 key 必须存在"）+ 值仅接受 None 或 string
  - root_cause：require key present + 仅接受 enum 或 None
  - 各错误消息含 "missing required" / "must match" / "path stem" 等可识别 token
- 新增 / 修改 regression tests（`tests/test_progress_artifacts.py:LoadBugReportTests`）：
  - +10 测试：missing bug_id / invalid bug_id regex / bug_id stem mismatch / missing target_release / missing consumed_in_release / non-string non-None value / missing root_cause / unknown root_cause enum / null root_cause accepted (without expect) / empty found_in_release reject
- 新增 CLI 集成 reject tests（`test_progress_bug_flow.py:BugStartMalformedFrontmatterTests`）：bug_id regex / stem 不一致 / 缺 target_release / 缺 consumed_in_release，全部退 1 + 文件字节级未改

### L1 — Dev root cause + empty rollback 持久化 planning-route 提示

- 修改：`skills/_shared/dev_workflow/progress_state.py:apply_bug_start`
  - 当 root_cause=development 且 applied_rollbacks 空时：
    - history_result = `current_stage=development; route=development-planning-write (no auto-rollback applied)`
    - history_next = `development-planning-write replan/route`
  - 其他 root cause / 有 rollback 时保持原有 next/result 文案
  - 触发条件纯粹基于 "dev + 空 rollback"，**forward 与 replay 都会进入这一分支**（replay 接收同样的 rollback_decisions=()，得到同样 history fields）
- 修改：`skills/workflow-protocol/scripts/progress.py:cmd_bug_start`
  - 把原本仅对 unable_to_localize 的 stderr 警告扩展为对 `unable_to_localize / ambiguous / "no eligible task state" / 其他 empty rollback` 四种情况都触发，消息里说明具体原因
  - 加入 stderr 警告里都建议 "invoke development-planning-write to replan/route"
- 新增 / 修改 regression tests：
  - `test_apply_bug_start.py:PlanningRouteNoteTests` ×4：dev empty rollback → planning route token；dev with rollback → 不加 token；srs / architecture root cause → standard write skill
  - `test_progress_bug_flow.py:PlanningRoutePersistenceTests` ×4：unable_to_localize 持久化 + stderr / ambiguous 持久化 + stderr / 有 affected task 但 task_states 不匹配 (skipped) 持久化 + stderr / recover roundtrip 后 history token 仍存在

## 重点 review 项

请按以下维度逐条核对：

### A. M1 fix 是否到位

- `_BUG_ID_RE` 模式 `^BUG-\d{3}$` 与 frontmatter-schema.md §4.4 一致？
- `_BUG_ROOT_CAUSE_VALUES` 集合 `{srs, architecture, development, prd-exception}` 与 frontmatter-schema.md §3.4 一致？
- 缺 key vs key 存在但值非法 vs key 存在但值 None — 三种状态错误消息是否区分清楚？
- `bug_id` 与 path stem 比对（`Path(bug_path).stem`）的实现是否在 BUG-NNN.md 与 docs/bug/BUG-NNN.md 之间正确比较？
- target_release / consumed_in_release / root_cause 这三个 nullable 字段的 "key 必含" 语义是否严格执行？
- 既有 round 1 的 LoadBugReportTests 6 个测试是否仍全过？
- 新增 10 个 reject tests 是否覆盖：missing key 三处 / invalid regex / stem mismatch / non-string nullable / unknown enum / null accepted (without expect) / empty found_in_release？

### B. L1 fix 是否到位

- `apply_bug_start` 的分支顺序：(applied_rollbacks 非空) → 保持原有 → (root_cause=dev + 空) → 加 planning-route → (其他) → 标准 write skill。逻辑是否正确？
- forward 与 replay 都通过同一分支判断（rollback_decisions=() + root_cause=development），所以 replay 重建后 history fields 一致？
- CLI 端 4 个分支：unable_to_localize / ambiguous / 有 affected task 但 task_states 不匹配 / 其他空 rollback。错误消息文案是否清晰？
- 测试 `test_recover_replay_preserves_planning_route_token` 是否真的验证 recover 后状态等价（current_stage / bug_flow / development_state.task_states）？history token 由于不在状态里，无法跨 recover 直接验证；但 recover 后再 query 应该看到 dev 阶段 + active bug flow，这就够了？
- ambiguous classification 在 round 1 之前没 stderr 警告；round 2 加了警告 + 持久化是否到位？

### C. 既有 invariant 是否保持

- Phase 1-5 + Phase 6.1 round 1 的 553 个测试是否仍全过？特别是 `test_development_unable_to_localize_warns`（round 1 既有，round 2 后行为兼容）？
- `progress_lock.py` / `progress_history.py` / `progress_replay.py` 未被本批触动？
- `apply_bug_close` / Gap-3 update --task / `_run_update_pipeline` / `extra_writes_factory` 行为完全保留？
- `_validate_bug_path_shape` (来自 5.4 round 2) 仍生效？
- M1 history parse + replay 一致性 + M2 review_iteration 都继承到 round 2 的修改？

### D. 测试质量

- M1 测试是否 byte-for-byte 验证文件未改 + 错误消息含可识别 token？
- L1 测试是否同时检查 (a) stderr 含具体原因 + (b) 持久化进 history.result/next + (c) recover 后状态一致？
- 既有 fixtures `_bug_fm()` 已加返回 dict 后让 caller mutate（避免 multiple values 错误）？
- 所有 round 2 新测都用 `tempfile.TemporaryDirectory` 隔离？

### E. Cross-doc 一致性

- `frontmatter-schema.md §3.4` bug-report 必含字段（5 个）现在被 `load_bug_report` 一处 enforce；schema 演化时只需要在这一处加？
- `frontmatter-schema.md §4.4` bug_id 3 位 zero-pad 与 `_BUG_ID_RE` 完全一致？
- `command-reference.md §8` 关于 ambiguous / unable_to_localize 必须 "记录 development-planning-write 重新路由" 的要求被 L1 fix 兑现？
- `task6_progress_py_prerequisites_20260506.md §2 Bug-Start Development Auto-Rollback` 第 4 步 "Append a progress-history entry that lists affected tasks and rollback targets" 在有 rollback 时 + 第 5 步 "Reject or require human escalation if BUG body lacks Affected Task(s) and no planning rebreakdown path is selected" 在空 rollback 时 — 现在都满足？

### F. 设计 / 可维护性

- L1 的"dev root + empty rollback → planning-route"判断是 forward / replay 共享的纯函数行为，避免 caller 必须传 hint 标志：是好设计，还是过于隐式？
- M1 把 BUG schema 校验集中到 `load_bug_report`，让 cmd_bug_start 不需要自己额外 checks；后续 Phase 6.2 bug-rework 复用同一 helper 即可：是否合理？
- planning-route 的 history token (`route=development-planning-write`) 是否便于后续 grep / log 分析？
- `_BUG_ID_RE` 与 `_BUG_PATH_RE` 一处定义在 progress_artifacts.py，progress_state.py 也有自己的 `_BUG_PATH_RE`：是否考虑后续整合？(round 1 review 已提到这是 optional cleanup)

### G. 已知 Phase 6.2+ 后续工作（不在本 review 评判范围）

- Phase 6.2 `bug-rework`：复用 6.1 的 `_compute_bug_start_rollback`（CLI helper）— 可能时机将其移到 progress_state.py / progress_artifacts.py 共享层；Gap-5 retest fail/partial 重路由
- Phase 6.3 `incident-start` / `incident-resolve`：含 TERMINAL_EVENTS 落地
- Phase 6.4 `update --advance` + `validate.py consistency`

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_1_bug_flow_entry_round2_review_20260507.md
```

报告需要包含：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6.2
2. **Round 1 Findings 回归状态** — M1 / L1 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed
3. **New Findings (Round 2)** — 没有则注明 "No new findings"
4. **Cross-Finding Consistency Check**
5. **Round 2 Implementation Quality Spot-checks** — `load_bug_report` 的严格校验、`apply_bug_start` 的 dev empty-rollback 分支、CLI ambiguous warning、新增 22 个 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 6.2 (`bug-rework`)**
   - **(B) fix before Phase 6.2**
   - **(C) revisit design**

如果 (B)，请明确：必修 / 可推迟 / 修复路径估计。

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6.2/6.3/6.4 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
