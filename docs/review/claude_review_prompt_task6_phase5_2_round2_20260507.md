# Claude Review Prompt — Task 6 Phase 5.2 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_2_update_event_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 5.3 (`update --task`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.2 Round 2 fixes** 做一次回归 review。Round 1 评审（Codex 出具）给出 **(B) fix before Phase 5.3 (`update --task`)** 结论，列出 0 High / 2 Medium / 0 Low；本轮请确认两个 Medium 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：

- Round 1 review report：`docs/review/task6_phase5_2_update_event_review_20260507.md`
- Round 1 实施代码：`skills/_shared/dev_workflow/progress_state.py` + `progress_replay.py`、`skills/workflow-protocol/scripts/progress.py`、`tests/test_apply_update_event.py` / `tests/test_progress_replay.py` / `tests/test_progress_update_event.py`
- Round 2 fixes 的 diff（仅触动 `progress_state.py` / `progress_replay.py` / `progress.py` / `tests/test_apply_update_event.py` / `tests/test_progress_update_event.py`；未改 lock / history / 既有 init/query/recover 测试）

**不要**要求 Phase 5.3/5.4/Phase 6 已实现。

## Round 1 baseline

- Phase 5.2 Round 1 review report: `docs/review/task6_phase5_2_update_event_review_20260507.md`
- Recommendation: **(B) fix before Phase 5.3 (`update --task`)**
- Findings: 0 High / **2 Medium (M1, M2)** / 0 Low
  - **M1** — `cmd_update` 读 `progress-history.md` 后未 `parse_history_text`、未 replay 校验；既能往 malformed history 末尾追加 entry，又无法捕到 progress.md 被 out-of-band 篡改的情形（forward 与 replay 漂移）
  - **M2** — `_validate_review_iteration_value` 仅拒绝 non-int / bool / negative，没拒 `value > REVIEW_ITERATION_LIMIT`；导致已有 `review_iteration=8` 在 `write-complete` / `review-passed` / `human-confirmed` 路径下被静默保留或归零，绕过 spec 的 0-7 上限与人工 escalate 不变量

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 293 tests in 2.423s
# OK
#  - baseline before round 1:  279 (Phase 1-4 + Phase 5.1 round 2 + Phase 5.2 round 1)
#  - round 2 net change:        +14
#    * test_apply_update_event.py +6 (IterationOverLimitTests):
#         write-complete iter=8 / review-issues iter=8 / review-passed iter=8 /
#         human-confirmed iter=8 / iter=7 仍允许 / iter=42 远超也拒
#    * test_progress_update_event.py +8:
#         History parse guard ×2: bad header / unknown field
#         Replay consistency ×3: tampered release / tampered project_name / clean cycle 不误判
#         Iteration over-limit CLI ×3: write-complete / review-passed / human-confirmed
#    * test_progress_update_event.py 既有测试 1 处更新（gated reject 测试改用单步 forge，不再依赖会被 M1 catch 的多步驱动）

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py update --help
# OK
```

## Round 2 修复摘要（请逐条核对是否到位）

### M1 — `cmd_update` 加 history parse + replay 一致性

- 修改：`skills/workflow-protocol/scripts/progress.py:cmd_update`
  - 锁内、读完 history_text 之后立刻 `parse_history_text(history_text)`；`HistoryError` 即 `print(... "existing progress-history.md is malformed: ...") + return 1`
  - 调 `apply_update_event` 拿到 outcome 后、composing 完 `new_history_text` 后：
    - `parse_history_text(new_history_text)` → 失败 `print("composed history is malformed: ...") + return 1`
    - `replay_history(replayed_entries)` → 失败 `print("composed history fails replay: ...") + return 1`
    - 比较 `replayed_state == outcome.new_state`，不一致计算 `diff_keys`、`print("replay consistency check failed; ... fields {diff_keys}; ... run 'progress.py recover --confirm' ...") + return 1`
  - 上述三个 reject 路径都在 `with progress_lock:` 之内、`with transaction()` 之外；不写 progress.md / progress-history.md 任何字节
- 既有 round 1 行为保留：lock + atomic.transaction + apply_update_event 单一事实源
- 新增 / 修改 regression tests（`tests/test_progress_update_event.py`）：
  - **new** `UpdateEventHistoryParseGuardTests`（2 测试）：bad header 与 unknown field 两种 corruption；`progress.md` / `progress-history.md` byte-for-byte unchanged
  - **new** `UpdateEventReplayConsistencyTests`（3 测试）：
    - 篡改 `release` 字段：forward outcome.new_state.release='0.2'，replay 得 '0.1'，diff 报 release，不写
    - 篡改 `project_name` 字段：同上
    - 干净状态跑完整 5-event 循环：consistency 检查不误判
  - **modified** `UpdateEventRejectionTests.test_human_confirmed_on_non_gated_stage_returns_1`：原测试用多步 `_rewrite_progress` + `_update("review-passed")` 驱动会被 M1 一致性 catch（属于"功能正确"），改为单步 forge 终态（review-passed + development），让 forward 的 gated_only 在 M1 之前先 reject，专注测 forward gated-stage 反例本身

### M2 — `_validate_review_iteration_value` 入口拒 `> REVIEW_ITERATION_LIMIT`

- 修改：`skills/_shared/dev_workflow/progress_state.py:_validate_review_iteration_value`
  - 新增 `if value > REVIEW_ITERATION_LIMIT: raise ProgressStateError(... "exceeding the limit of 7 ... escalate to a human and reset history")`
  - 既有的 `< 0` / 非 int / bool 拒绝逻辑保留
  - `review-issues` 的 post-increment 检查（`new_iter > REVIEW_ITERATION_LIMIT`）保持不变；6→7 仍允许，7→8 仍拒（同样的 "escalate" 消息文案）
- 新增 / 修改 regression tests：
  - **new** `tests/test_apply_update_event.py:IterationOverLimitTests`（6 测试）：write-complete/review-issues/review-passed/human-confirmed × iter=8 全 reject + iter=7 入口仍允许 + iter=42 远超也拒
  - **new** `tests/test_progress_update_event.py:UpdateEventIterationOverLimitTests`（3 测试）：CLI 层面 `_rewrite_progress` 设 iter=8 后 update --event 返回 1，progress.md 字节级未改

### 杂项 polish

- `progress_replay.py` 模块 docstring 与 unsupported-event 错误消息从 "phase 5.1 only registers init" 更新为反映 5.2 现状："phase 5.2 implements 'init' plus the four update --event handlers"；后续 phase 描述也写明（5.3 task / 5.4 release / Phase 6 bug+incident+terminal）

## 重点 review 项

请按以下维度逐条核对，不要跳过：

### A. M1 fix 是否到位

- `cmd_update` 是否在锁内、apply_update_event 之前就先 parse 现有 history_text？
- 拼好 new_history_text 后是否做了 parse + replay + 状态等值比对三步？
- 三个 reject 路径都返回 1 + 写到 stderr + 文件字节级不动？
- diff_keys 输出是否能定位 caller 篡改的字段？
- 错误消息是否提示 `recover --confirm` 作为修复路径？
- `with progress_lock:` 仍包住所有读 / parse / apply / compose / verify / write 步骤；`with transaction():` 仅包写入？

### B. M2 fix 是否到位

- `_validate_review_iteration_value` 是否真的把 `> REVIEW_ITERATION_LIMIT` 加到了 reject 条件？
- `review-issues` post-increment 检查的相对位置（在 `apply_update_event` 内的 `new_iter > REVIEW_ITERATION_LIMIT`）是否仍保留？
- iter=7 入口仍允许（spec 上限 inclusive）？
- iter=42 与 iter=8 的错误消息都明确 escalate？
- 是否未误伤 round 1 已通过的 `test_review_issues_iteration_seven_to_eight_rejected` / `test_review_issues_iteration_six_to_seven_allowed`？

### C. 既有 invariant 是否保持

- Phase 5.1 round 2 + Phase 5.2 round 1 的 279 个测试是否仍全通过？
- `progress_lock.py` / `progress_history.py` / `init` / `query` / `recover` 行为未受 round 2 触动？
- `apply_update_event` 仍是 forward + replay 单一事实源；replay handler 不复制状态机逻辑？
- `EventOutcome` 形状未改？
- argparse mutex group 仍然 `required=True`，为 5.3/6 留出 `--task` / `--advance` 接口？

### D. 测试质量

- M1 的 5 个新测试：
  - 是否都 byte-for-byte 验证 progress.md 与 progress-history.md 未被改写？
  - 是否覆盖：(a) bad header (b) unknown field (c) 篡改非 state-machine 字段 (release) (d) 篡改 project_name (e) 干净 cycle 不误判？
  - 错误消息是否有具体 assertion（"malformed" / "replay consistency check failed" / 字段名 / "recover --confirm"）？
- M2 的 6 个 unit 测试 + 3 个 CLI 测试：
  - 是否覆盖 4 个 event × iter=8、iter=7 仍允许、iter=42 也拒？
  - CLI 层是否同样 byte-for-byte 验证文件未改？
  - 错误消息含具体 value / limit / escalate？
- 修改后的 `test_human_confirmed_on_non_gated_stage_returns_1`：注释是否清楚说明为何改用单步 forge（M1 一致性会 catch 多步驱动），让阅读者理解这是测 forward gated_only 反例而不是 M1 一致性反例？
- 所有 round 2 新测都用 `tempfile.TemporaryDirectory` 隔离？
- Round 1 既有 30+ 个测试（apply_update_event 28 + replay 6 + CLI 15 = 49 减去 1 修改）是否仍全通过？

### E. Cross-doc 一致性

- `command-reference.md §2` "通用 update 流程" 中的 7 步是否在本次 round 2 后被完整覆盖（含"一致性校验"）？
- `command-reference.md §2.1` 中 `review_iteration > 7 → reject + 报错升级人` 是否在 round 2 后所有 mutating event 路径都生效（不仅 review-issues）？
- `frontmatter-schema.md` / progress.md schema 中描述 review_iteration `0-7` 的范围是否被 entry 校验严格执行？
- `task6_plan §11.1` "失败 → rollback；成功 → 解锁退出" 是否仍由 `atomic.transaction()` + `progress_lock` 兜底？
- `progress_replay.py` docstring 与错误消息是否准确反映 5.2 现状（init + 4 update events）？

### F. 设计 / 可维护性

- M1 的 parse + replay 一致性是否成本可控（每次 update 都 parse 全 history + 全量 replay）？对 long-running project 是否有性能担忧？答：current implementation 是 O(N) per update；project 进入数千 entries 后才会有可观察 cost，到 Phase 6 / Phase 7 时若需要可改增量校验
- diff_keys 输出的字段顺序是否 deterministic（用 sorted）？
- 错误消息建议运行 `recover --confirm` 是否对 caller 友好？
- M2 的入口校验位置（在 `_validate_review_iteration_value` 而非 `apply_update_event` 主体）是否便于未来 review-issues 之外的 event 共享同一 guard？

### G. 已知 Phase 5.3+ 后续工作（不在本 review 评判范围）

- Phase 5.3 `update --task`：扩展 mutex group 加 `--task <Tn> --status <new>`；注册若干 task handler；可能解锁 `progress_history.py` 的 `task` 字段白名单
- Phase 5.4 `release-close` / `release-start` / `bug-intake`：跨多文件原子（progress + N 个 BUG frontmatter）；`release-start` 在 transaction 内修 BUG `target_release` / `consumed_in_release`
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + `update --advance`；`TERMINAL_EVENTS` 在 incident-resolve abort/reconstruct 时落地

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_2_update_event_round2_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 3 / 4 / 5.1 round 2 review 结构）：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.3
2. **Round 1 Findings 回归状态** — M1 / M2 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed，附简短理由
3. **New Findings (Round 2)** — Round 2 修复或测试若引入了新的 H/M/L finding，列出 location + issue + impact + recommendation；没有则注明 "No new findings"
4. **Cross-Finding Consistency Check** — 各 reference / plan / SKILL.md 与新代码行为一致性
5. **Round 2 Implementation Quality Spot-checks** — `cmd_update` 的 parse + replay 三步、`_validate_review_iteration_value` 加严、`progress_replay.py` docstring polish、新增 14 个 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 5.3 (`update --task`)**（5.3 之前可选清理 list）
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
