# Claude Review Prompt — Task 6 Phase 5.1 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_1_progress_core_round2_review_20260507.md`。Round 2 通过后才能进入 Phase 5.2 (`update --event`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.1 Round 2 fixes** 做一次回归 review。Round 1 评审（Codex 出具）给出 **(B) fix before Phase 5.2** 结论，列出 0 High / 2 Medium / 0 Low；本轮请确认两个 Medium 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：

- Round 1 review report：`docs/review/task6_phase5_1_progress_core_review_20260507.md`
- Round 1 实施代码：`skills/_shared/dev_workflow/progress_lock.py` / `progress_history.py` / `progress_replay.py` / `progress_state.py`、`skills/workflow-protocol/scripts/progress.py`、`tests/test_progress_*.py`
- Round 2 fixes 的 diff（仅触动 `progress_replay.py`、`progress.py`、`tests/test_progress_replay.py`、`tests/test_progress_init.py`；未新增脚本，未改 lock / history / state / 其它 4 个测试文件）

**不要**要求 Phase 5.2/5.3/5.4/Phase 6 已实现；这些仍是后续 phase 范围。

## Round 1 baseline

- Phase 5.1 Round 1 review report: `docs/review/task6_phase5_1_progress_core_review_20260507.md`
- Recommendation: **(B) fix before Phase 5.2**
- Findings: 0 High / **2 Medium (M1, M2)** / 0 Low
  - **M1** — `replay_history()` 先 `iter_entries_chronological(history)` 排序，再做 timestamp 倒序校验；排序后 `entry.timestamp < prev_ts` 路径不可达，导致一段被外部破坏 / 时钟错乱 / 篡改顺序的 history 会被静默重排再 replay
  - **M2** — `init --scenario` 用 argparse `choices=` 兜底；非法 scenario 走 exit 2（CLI usage error）而非 prompt 约定的 exit 1（workflow 校验失败）；与 `--release` / `--project` 校验路径不一致

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 230 tests in 1.657s
# OK
#  - baseline before round 1:  227 (Phase 1-4 160 + Phase 5.1 round 1 67)
#  - round 2 net change:        +3
#    * test_progress_replay.py: +2 (replay_uses_document_order, check_fires_before_handler_dispatch); 1 renamed (specific_message)
#    * test_progress_init.py:   +1 (scenario_subtype_also_returns_1); 1 renamed (returns_1)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
python3 skills/workflow-protocol/scripts/progress.py init --help
python3 skills/workflow-protocol/scripts/progress.py query --help
python3 skills/workflow-protocol/scripts/progress.py recover --help
# 4 个 help 均正常；init --help 在 --scenario 描述里仍展示合法值（虽然不再用 argparse choices）
```

## Round 2 修复摘要（请逐条核对是否到位）

### M1 — Replay 改为按文档序遍历，monotonicity 在 handler dispatch 之前 raise

- 修改：`skills/_shared/dev_workflow/progress_replay.py`
  - 删除 `from .progress_history import ... iter_entries_chronological`
  - `replay_history(history)` 不再调用 `iter_entries_chronological(history)` 排序；改为直接 `for entry in history:` 遍历调用方传入的文档序
  - timestamp 倒序检查紧跟 loop 入口、在 `seen_terminal` 与 handler dispatch 之前；触发时 raise `ReplayError("history at <ts>: timestamp goes backwards (previous <prev_ts>)")`
  - docstring 重写说明文档序契约 + monotonicity 在 dispatch 之前
- 调用方契约：`progress.py recover` 一直把 `parse_history_text(...)` 的结果直接传入；`parse_history_text` 已经按文档序返回，所以本次修复不需要改任何调用点
- 新增 / 修改 regression tests（`tests/test_progress_replay.py`，`ReplayMonotonicityTests`）：
  - **renamed** `test_timestamp_going_backwards_rejected` → `test_timestamp_going_backwards_rejected_with_specific_message`：断言异常消息含 `"timestamp goes backwards"` 与前一条 timestamp，避免 round 1 那个被 "init must be first" 假阳掩盖的弱断言
  - **new** `test_timestamp_check_fires_before_handler_dispatch`：第二条 entry 同时 (a) timestamp 倒序、(b) event 是 5.1 不支持的 `release-close`；验证 backwards 错误优先于 "not supported"，证明 check ordering
  - **new** `test_replay_uses_document_order_not_sorted_order`：输入按文档序 [later, earlier]；如果 replay 仍 pre-sort，重排后倒序条件就不复成立；专门防止本 finding 的回归

### M2 — `init --scenario` 走 exit 1 校验路径

- 修改：`skills/workflow-protocol/scripts/progress.py`
  - `argparse` 中 `--scenario` 不再用 `choices=sorted(SCENARIOS_INIT)`；help 文本里仍展示合法值与未来 release-start 走向（避免 UX 退化）
  - 非法 scenario 现在走与 release / project_name 相同的路径：`build_initial_state` 内部 `_validate_scenario_init` raise `ProgressStateError` → `cmd_init` `except ProgressStateError` 打印到 stderr → exit 1，不创建 progress.md / progress-history.md
- 新增 / 修改 regression tests（`tests/test_progress_init.py`，`InitRejectionTests`）：
  - **renamed** `test_init_invalid_scenario_returns_2` → `test_init_invalid_scenario_returns_1`：断言 exit 1、消息含 `scenario`、且 progress.md / progress-history.md 字节级未创建
  - **new** `test_init_invalid_scenario_subtype_also_returns_1`：传 `--scenario S2-1`（属于 release-start 而非 init），同样走 exit 1 路径，确认 `_validate_scenario_init` 的 reject 集合覆盖 S2-* 子类型

## 重点 review 项

请按以下维度逐条核对，不要跳过：

### A. M1 fix 是否到位

- `replay_history` 是否真的去掉了 `iter_entries_chronological` 排序？loop 输入是否就是 caller 给的 `history` iterable，不再有重排？
- timestamp 倒序检查是否在 loop 入口、在 `seen_terminal` 与 handler dispatch 之前执行？
- 错误消息 `"timestamp goes backwards"` 是否含可识别的字符串 + 前一条 timestamp，便于排查？
- `iter_entries_chronological` helper 是否仍保留在 `progress_history.py`（其他 caller 可能用到）但不再被 replay 调用？
- 是否破坏了 round 1 既有的 init/missing-fields/invalid-scenario/invalid-release/duplicate-init 等测试？
- 新增 3 个 monotonicity 测试是否覆盖：(a) 文档序倒序专项、(b) check ordering（timestamp 优先于 unsupported event）、(c) "如果还在 sort 就会过" 的反向 detective test？

### B. M2 fix 是否到位

- argparse 是否真的去掉了 `--scenario` 的 `choices=` 参数？
- help 文本是否仍可读地说明合法值（即使不再做 enforcement，UX 不退化）？
- 非法 scenario 是否走 `cmd_init` 的 `except ProgressStateError → return 1` 路径？
- 测试是否同时校验 exit code、stderr 含 "scenario"、`progress.md` / `progress-history.md` 字节级未创建（防止回归到"半 init 状态"）？
- `--scenario S2-1` / `S2-2` / `S2-3` / `S2-4` 这类 release-start 才合法的值，在 init 路径是否都走 code 1 而非 code 2？

### C. 既有 invariant 是否保持

- Phase 5.1 round 1 的 67 个测试 + 之前 Phase 1-4 的 160 个测试是否仍全部通过？
- `progress_lock.py` / `progress_history.py` / `progress_state.py` 是否未被本次 fix 触动？
- `progress.py init` / `query` / `recover` 三子命令的整体行为（lock、atomic transaction、--root、`--lock-timeout`、exit code 0/1/2）是否仍一致？
- `query` 仍然不锁、并能在 `init` / `recover` 持锁期间读？
- `recover` 仍然 `--confirm` 必填、history empty/missing/parse-fail/unsupported-event 仍走 exit 1 不写 progress.md？

### D. 测试质量

- M1 三个测试（specific_message / check_fires_before_handler_dispatch / uses_document_order_not_sorted_order）：
  - 是否都用 `assertIn("timestamp goes backwards", str(cm.exception))` 这种**具体**字符串断言（而非弱 `assertRaises(ReplayError)`，那是 round 1 的 bug 滋生地）？
  - 是否覆盖：document order 直接逆序、ordering check 在 handler dispatch 之前、若仍 pre-sort 即过的反向场景？
- M2 两个测试（returns_1 / scenario_subtype_also_returns_1）：
  - 是否都校验 (a) exit code 1、(b) stderr 含关键词、(c) 文件字节级未创建？
  - 是否覆盖 init 不允许的 scenario 集合（S2-* 子类型至少举一个）？
- 是否所有 round 2 新测都用 `tempfile.TemporaryDirectory` 隔离？
- Round 1 已有测试是否未被 round 2 修复误伤？

### E. Cross-doc 一致性

- `command-reference.md §1` (init) 字段表与 init mutation 是否仍 100% 对齐？
- `command-reference.md §4` (recover) 描述的"replay validator 必须按状态机校验每条 entry 合法性"在 round 2 后是否更接近 spec（按 append 序而非排序后）？
- `task6_plan §11.1` 的 progress.py atomicity 与 `--root` / `--lock-timeout` 行为是否仍符合？
- `doc-guardian/SKILL.md` / `workflow-protocol/SKILL.md` 命令矩阵是否未受影响？

### F. 设计 / 可维护性

- `replay_history` 的契约现在更明确（"输入必须是 append/document order"）；docstring 是否清楚？
- `progress.py` argparse `--scenario` help 文本提示语是否能保持后续 phase 加 release-start 时的扩展空间（"S2-1/-2/-3 enter via release-start once Phase 5.4 lands"）？
- 是否引入了不必要的依赖或新 shared helper（不应有）？
- 错误消息是否对 caller 友好（含具体字段、值、上一条 timestamp）？

### G. 已知 Phase 5.2+ 后续工作（不在本 review 评判范围）

- Phase 5.2 `update --event`：扩展 `_HANDLERS` 注册 4 个 event handler；replay 会承担更复杂的多 event 历史校验（M1 fix 是这一步的前置）
- Phase 5.3 `update --task`：注册 task handler；可能需要 `progress_history.py` 解锁 `task` 字段（round 1 review §5 Open Questions 提到）
- Phase 5.4 `release-close` / `release-start` / `bug-intake`：跨多文件原子（progress + 多 BUG frontmatter）；`release-start` 在 transaction 内修 BUG `target_release` / `consumed_in_release`
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + `update --advance`；`TERMINAL_EVENTS` 在 incident-resolve abort/reconstruct 时落地

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_1_progress_core_round2_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 3 / 4 round 2 review 结构）：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.2
2. **Round 1 Findings 回归状态** — M1 / M2 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed，附简短理由
3. **New Findings (Round 2)** — Round 2 修复或测试若引入了新的 H/M/L finding，列出 location + issue + impact + recommendation；没有则注明 "No new findings"
4. **Cross-Finding Consistency Check** — 各 reference / plan / SKILL.md 与新代码行为一致性
5. **Round 2 Implementation Quality Spot-checks** — `replay_history` 文档序遍历、`--scenario` 走 ProgressStateError、新增 3+2 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 5.2 (`update --event`)**（5.2 之前可选清理 list）
   - **(B) fix before Phase 5.2**（必修 list；为何 Phase 5.2 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5.2 前修
- 哪些可以推迟到 Phase 5.3/5.4/Phase 6/Phase 7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写 `progress_replay.py` / `progress.py` / `tests/test_progress_replay.py` / `tests/test_progress_init.py` / 其它脚本 / references / SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5.2/5.3/5.4/Phase 6 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
