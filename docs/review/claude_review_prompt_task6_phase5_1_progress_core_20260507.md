# Claude Review Prompt — Task 6 Phase 5.1 progress.py Core (init / query / recover)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_1_progress_core_review_20260507.md`。Phase 5.1 通过后才能进入 Phase 5.2（`update --event`）。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.1 implementation** 做一次代码 review。本批是 progress.py 第一阶段：建立 lock / history / replay 三块基础设施 + 实现 `init` / `query` / `recover` 三条命令。Phase 5.2/5.3/5.4 / Phase 6 会在这套基础上增量加 `update --event` / `update --task` / `release-*` / `bug-*` / `incident-*` / `update --advance`。

本轮是代码 review。**写集**仅限：

- 新建 shared module `skills/_shared/dev_workflow/progress_lock.py`
- 新建 shared module `skills/_shared/dev_workflow/progress_history.py`
- 新建 shared module `skills/_shared/dev_workflow/progress_replay.py`
- 扩展现有 `skills/_shared/dev_workflow/progress_state.py`（追加 `build_initial_state` / `render_progress_text` / 校验常量；不动现有 dataclass / NORMAL/PROTECTED transitions）
- 新建 CLI `skills/workflow-protocol/scripts/progress.py`
- 新建 tests `tests/test_progress_lock.py` / `tests/test_progress_history.py` / `tests/test_progress_replay.py` / `tests/test_progress_init.py` / `tests/test_progress_query.py` / `tests/test_progress_recover.py`

Phase 5.1 **不**实现：

- `update --event` / `update --task` / `update --advance`（Phase 5.2 / 5.3 / Phase 6）
- `release-close` / `release-start` / `bug-intake`（Phase 5.4）
- `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`（Phase 6）
- 完整 state machine（per-event handler 增量加，5.1 仅 `init`）
- Gap-3/4/5 protected rollback（Phase 6）
- `validate.py consistency`（Phase 6+）

这些不能因为它们在 5.1 里"还没写"而被当 finding。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 全部 (A) closed：

- Phase 1 review: `docs/review/task6_phase1_docs_alignment_review_20260507.md`
- Phase 2 round 2: `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md`
- Phase 3 round 2: `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md`
- Phase 4 round 2: `docs/review/task6_phase4_status_transition_round2_review_20260507.md`

Phase 5 在 plan §13 与现 session 协商后被拆为 4 个子 phase：

- **Phase 5.1**（本批）：foundation（lock/history/replay）+ init + query + recover
- Phase 5.2：`update --event`
- Phase 5.3：`update --task`（normal transitions only）
- Phase 5.4：`release-close` + `release-start` + `bug-intake`

Phase 5.1 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 227 tests in 1.673s
# OK
#  - baseline (Phase 1-4):  160
#  - new in Phase 5.1:       67
#    * test_progress_lock.py     :  5
#    * test_progress_history.py  : 18
#    * test_progress_replay.py   : 12
#    * test_progress_init.py     : 11
#    * test_progress_query.py    : 11
#    * test_progress_recover.py  : 10

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
python3 skills/workflow-protocol/scripts/progress.py init --help
python3 skills/workflow-protocol/scripts/progress.py query --help
python3 skills/workflow-protocol/scripts/progress.py recover --help
# 4 个 help 均正常
```

End-to-end smoke 验证（手工跑过）：`init` → `query` 全字段/单字段/JSON → 故意写坏 `progress.md` → `recover --confirm` → 重新 `query` 确认重建。

## 阅读顺序（请严格按序读，不要跳读）

1. `docs/handoff/session_handoff_task6_phase4_20260507.md` —— Phase 4 结束态、Phase 5 起点的总体边界
2. `docs/implementation/task6_plan_20260507.md` §5 / §11.1 / §13 / §15 —— progress.py 命令矩阵、原子化策略、Phase 划分、acceptance
3. `docs/review/task6_phase4_status_transition_round2_review_20260507.md` —— Phase 4 closure context（5.1 复用 atomic.transaction / frontmatter / schema）
4. `skills/workflow-protocol/SKILL.md`（命令矩阵 + bug-rework 行）
5. `skills/workflow-protocol/references/command-reference.md` §1（init）/ §3（query）/ §4（recover、terminal-state replay 算法）
6. `skills/_shared/dev_workflow/atomic.py`（已 review 过的 `transaction()`；5.1 复用）
7. `skills/_shared/dev_workflow/frontmatter.py`（5.1 复用 `read_markdown` / `render_markdown`）
8. **新文件** `skills/_shared/dev_workflow/progress_lock.py`
9. **新文件** `skills/_shared/dev_workflow/progress_history.py`
10. **新文件** `skills/_shared/dev_workflow/progress_replay.py`
11. **改动** `skills/_shared/dev_workflow/progress_state.py`（新增 `build_initial_state` / `render_progress_text` / 校验常量；现有 task transitions 行未改）
12. **新文件** `skills/workflow-protocol/scripts/progress.py`
13. **新文件** `tests/test_progress_lock.py`
14. **新文件** `tests/test_progress_history.py`
15. **新文件** `tests/test_progress_replay.py`
16. **新文件** `tests/test_progress_init.py`
17. **新文件** `tests/test_progress_query.py`
18. **新文件** `tests/test_progress_recover.py`

## Phase 5.1 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 5.1 不得创建/编辑 repo-root `progress.md` / `progress-history.md`（这俩在本 repo 不存在，应保持不存在）。
2. 工作树大量 untracked 是项目内容，不得 delete/clean/reset/revert。
3. Tests 必须用 temp dirs / fixtures，不得 mutate 真实 `docs/` / `skills/`。
4. **Phase 5.1 写集严格**（见前文写集列表）；未引入新外部依赖，仍用 `pyyaml` 与 stdlib。
5. **Lock**：`init` / `recover` 必须经 `progress_lock(root, timeout=...)`；`query` 不锁。Lock 文件 `<root>/.progress.lock`，POSIX `fcntl.flock`，跨进程互斥。
6. **History**：strict parser，header `^## (ts) — (event) — (summary)$`，body 仅允许 `- agent: ...` / `- result: ...` / `- next: ...`，未知字段 / 重复 key / 无 entry 内的 field / 无效 header → `HistoryError`。
7. **Replay**：5.1 仅注册 `init` event handler；其他 event → `ReplayError("event ... not supported in current replay validator")`。terminal-state 框架（`TERMINAL_EVENTS` 集合 + `seen_terminal` 状态）已搭好，5.1 集合是空的，等 Phase 6 incident-resolve 加入。
8. **多文件原子写**：`init` 同时写 `progress.md` + `progress-history.md` 必须用 `atomic.transaction()`（任一失败回滚两者）；`recover` 用 `atomic.transaction()` 写 `progress.md`（不动 history）。
9. **State 字段完整性**：`build_initial_state` 必须包含 command-reference.md §1 列出的全部字段（project_name / workflow_version / project_state / release / release_state / release_close_reason / previous_releases / scenario / scenario_subtype / current_stage / sub_state / review_iteration / artifacts / bug_flow / workflow_incident_active / incident_report_path / unresolved_bugs / created / updated）；缺字段就是 finding。
10. **Recover idempotency**：`recover` 必须每次产出与 history 等价的 state；`updated` 字段允许 bump 到 recover 时刻，`created` 必须保留 history 反映的初始时刻。
11. **CLI 风格**：`--root` 默认 cwd（与 Phase 3 / 4 一致）；exit code 0 / 1 / 2 契约；bootstrap path `parents[3]`（脚本被 symlink 调用时仍能定位 repo root）。

## 重点 review 项

请按以下维度逐条核对：

### A. `progress_lock.py`

- 是否使用 `fcntl.flock` 而非 stale lock-file 检查（避免 stale .lock 残留误锁）？
- 超时通过非阻塞 + poll 实现，超时即 raise `ProgressLockError`？
- context manager 出口处释放锁（即使 `yield` 内部 raise）？
- 关闭文件描述符在 `finally` 块（避免 fd 泄漏）？
- root 目录不存在时是否 `mkdir(parents=True)`（init 在空目录里可用）？
- 测试覆盖：acquire+release、root 不存在自动创建、跨进程互斥（fork）、超时 raise、串行重入。

### B. `progress_history.py`

- header regex 是否严格匹配 spec：`^## (ts) — (event) — (summary)$`，timestamp ISO8601 UTC，event 是 `[A-Za-z][A-Za-z0-9_-]*`，summary 非空？
- body field 仅 `agent` / `result` / `next` 三项白名单？unknown key / 重复 key / 无 entry 内的 field / 无 header 的 field 是否 raise `HistoryError`？
- `render_history_entry` 是否按 spec 顺序输出，optional field 缺省时不渲染（结尾不留空 `- result:`）？
- `append_history_text` 是否保留首部 `# Project History` 标题（如有）+ 与上一条 entry 之间空一行？
- `iter_entries_chronological` 是 stable sort（同 timestamp 保持输入顺序，便于后续 monotonicity 报错）？
- 测试覆盖：empty / single / multi / round-trip render→parse / header 错 / field 错 / 重复 key / unknown top-level line 拒绝。

### C. `progress_replay.py`

- 5.1 仅 `init` handler 注册；其他 event 是否在 `replay_history` 中 raise `ReplayError("event ... not supported")`？错误消息是否清晰提示这是 Phase 5.1 边界？
- `_apply_init` 是否：
  - 拒绝非首条出现（state 已非空时）？
  - 从 summary / result 字段抽 `project=`、`scenario=`、`release=`，缺任一 → `ReplayError`？
  - 调 `build_initial_state` 校验值合法性（scenario ∈ {S1, S3}、release `^\d+\.\d+$`、project name 合规）？
- timestamp 倒序（second `<` first）→ `ReplayError`？
- `seen_terminal` 框架在 5.1 是不动手的（`TERMINAL_EVENTS` 与 `READ_ONLY_EVENTS` 都是空集），代码框架是否已经为 Phase 6 留好挂接点？
- `supported_events()` 是否对外暴露当前 handler 集合（5.1 唯一 init），便于 Phase 5.2 / 5.3 / 5.4 / Phase 6 在加 handler 时同步把 event 加入这个集合？
- 测试覆盖：empty history / init only / init can read fields from result / init missing fields / init invalid scenario/release / init must be first / unknown event reject / supported_events 集合 / timestamp backwards / parse→replay round trip。

### D. `progress_state.py` 扩展

- `build_initial_state` 字段是否与 command-reference.md §1 的 init mutation 表 100% 一致（包括 nested `artifacts` 与 `bug_flow` 形状、`workflow_incident_active=False` 等）？
- 校验函数（`_validate_project_name` / `_validate_release` / `_validate_scenario_init` / `_validate_timestamp`）是否覆盖 spec 要求？project_name 用 `^[A-Za-z][A-Za-z0-9_.-]{0,63}$`、release 用 `^\d+\.\d+$`、scenario init 仅 `{S1, S3}`（S2-1/-2/-3 是 `release-start` 走的，不在 init）。
- 是否未引入 Phase 5.2/5.3 的状态机校验（保持本期 scope 干净）？
- `render_progress_text` 默认 body template 是否合理（init 后 readable summary + Recent Activity 引用 history）？
- `PROGRESS_BODY_TEMPLATE` 是模块级常量，便于 recover / 未来 update 路径复用。

### E. `progress.py` CLI

- 三子命令布局：`init` / `query` / `recover`，各自参数与 spec 一致？
- `--root` 全局；`--lock-timeout` 全局并能被子命令使用？
- bootstrap：`parents[3]` 加到 sys.path；symlink 兼容性是否经过手工核查？
- `init`：
  - 已存在 `progress.md` 或 `progress-history.md` 任一 → reject + exit 1？
  - 锁失败 → exit 1 + 清晰提示（不创建任何文件）？
  - 字段校验失败（scenario / release / project_name）→ exit 1，不创建文件？
  - 成功后 stdout 含 `created progress.md and progress-history.md`，exit 0。
- `query`：
  - 不锁、可与 `init` / `recover` 持锁同时运行？
  - 不存在 progress.md → exit 1；frontmatter 不可解析 → exit 1。
  - `--field <name>`：scalar / null / dict 各种类型输出格式合理（null 输出 `null`，bool 输出 `true/false`，dict 输出 yaml）？`--json` flag 切换为 JSON。
  - 未知 field → exit 1。
- `recover`：
  - 必须 `--confirm`，否则 reject + exit 1？
  - 锁失败 → exit 1。
  - history 不存在 / empty / parse 失败 / replay 失败 → exit 1，不写 progress.md（不创建占位）？
  - 成功后 progress.md 重建、history 不变；`updated` 重写为当前 ISO，`created` 保留 history 时刻。
- exit code 0 / 1 / 2 契约一致；无子命令 → 2。

### F. Tests

- 6 个测试文件覆盖：lock primitive、history schema、replay framework、init CLI/API、query CLI/API、recover CLI/API。
- `_run` helper 隔离 stdout / stderr 并能捕获 SystemExit？
- 所有 CLI 测试用 `tempfile.TemporaryDirectory()`？真实 repo 的 `progress.md` / `progress-history.md` 完全不被触碰（应该不存在）？
- `_seed` helper 在 query / recover 测试里把 init 输出静音（避免 unittest 输出噪声）？
- 测试中关键 assert：byte-equality（recover 不动 history、init 失败时不留半成品文件）、特定字段值（project_name / current_stage / sub_state / created==updated）、错误消息片段（`refusing to overwrite` / `held by another process` / `not supported` 等）。
- 是否覆盖 lock 阻断的 init / recover 路径？
- 是否覆盖 history 含未实现 event（5.1 边界）的 recover 拒绝？

### G. 与既有 invariant 的一致性

- `atomic.transaction()` 仍是多文件原子写的唯一入口（`init` / `recover` 路径）？
- `frontmatter.read_markdown` / `render_markdown` 用于 progress.md 的解析与渲染？
- Phase 4 `status_transition.py` / `validate.py` / `changelog.py` 行为未被 Phase 5.1 触动？
- 全套 227 测试 pass、compileall 干净（包括 `skills/workflow-protocol/scripts`）？

### H. 已知 Phase 5.2+ 后续工作（不在本 review 评判范围）

- Phase 5.2 `update --event`：扩展 replay handler 集合 + `_HANDLERS["update-event-..."]` + sub_state 状态机 + review_iteration ≤7 + gated/non-gated；caller 调 `progress.py update --event` 走 lock + atomic transaction。
- Phase 5.3 `update --task`：注册 `_HANDLERS["update-task-..."]`，复用 `progress_state.NORMAL_TASK_TRANSITIONS`，加 planning-done 原子四件套校验。
- Phase 5.4 `release-close` / `release-start` / `bug-intake`：跨多文件原子（progress + 多 BUG frontmatter）；`release-start` 在 transaction 内修 BUG `target_release` / `consumed_in_release`。
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve`：`TERMINAL_EVENTS` 添加 `incident-resolve --action abort/reconstruct`。
- Phase 6 `update --advance` + Gap-3/4/5 protected rollback。

这些不应作为 Phase 5.1 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_1_progress_core_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 5.1 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5.2
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §1/§3/§4、task6_plan §5/§11.1/§13、SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§G 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 5.2 (`update --event`)**（5.2 之前可选清理 list）
   - **(B) fix before Phase 5.2**（必修 list；为何 Phase 5.2 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5.2 前修
- 哪些可以推迟到 Phase 5.3/5.4/Phase 6/Phase 7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5.2/5.3/5.4/Phase 6 设计讨论；如发现 Phase 5.2+ 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
