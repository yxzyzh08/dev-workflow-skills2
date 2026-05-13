# Claude Review Prompt — Task 6 Phase 6.3 `incident-start` / `incident-resolve` + `TERMINAL_EVENTS`

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_3_incident_review_20260507.md`。Phase 6.3 通过后才能进入 Phase 6.4 (`update --advance` + `validate.py consistency`)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.3 implementation** 做一次代码 review。本批是 Phase 6 的第三段：实现 PRD-exception incident 生命周期的两个命令（`incident-start` / `incident-resolve`）+ `TERMINAL_EVENTS` 首次落地（采用 Option B：action-aware terminal gate，使 `--action continue` 非终态而 `--action abort` / `reconstruct` 终态）。Phase 6.3 同时引入 progress.py 第一次跨 skill 调用 doc-guardian 的 `validate.py file`（直接 import 而非 subprocess，作为 round 2 M6 double-safety 落地点）。

本轮是代码 review。**写集**仅限：

- 扩展 `skills/_shared/dev_workflow/progress_state.py`
  - 重构 `_validate_bug_path_shape`：与新增的 `_validate_incident_path_shape` 共享 `_validate_doc_path_shape(...)` 私有 helper（行为完全不变；前者 575+ 测试全过证明透明）
  - 新增 `_INCIDENT_PATH_RE` + `_validate_incident_path_shape`
  - 新增 `_INCIDENT_RESOLVE_ACTIONS` / `_INCIDENT_TERMINAL_ACTIONS` 模块常量
  - 新增 `IncidentStartOutcome` + `apply_incident_start`
  - 新增 `IncidentResolveOutcome`（含 `is_terminal: bool` 字段）+ `apply_incident_resolve`（3 action 分支：continue / abort / reconstruct）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`
  - 新增 `_apply_incident_start_handler` + `_apply_incident_resolve_handler`
  - `_HANDLERS` 现 14 项；`supported_events()` 测试同步
  - **`TERMINAL_EVENTS` 首次落地**为 `{"incident-resolve"}` + 新增 `TERMINAL_INCIDENT_ACTIONS = frozenset({"abort", "reconstruct"})`
  - `replay_history` dispatch loop 新增 action-aware terminal gate（解析 `action=` token，仅当 action ∈ TERMINAL_INCIDENT_ACTIONS 时翻转 seen_terminal）
  - module docstring + unsupported-event 错误消息更新到 6.3
- 扩展 `skills/workflow-protocol/scripts/progress.py`
  - 新增 `_DOC_GUARDIAN_SCRIPTS` sys.path 注入 + `validate_doc(path, root) -> list[str]` helper（直接 import `validate` 模块，不走 subprocess；tests 通过 `patch.object(progress, "validate_doc", ...)` 单点 mock）
  - 新增 `cmd_incident_start`：双 path resolve + containment / 双 `validate_doc` M6 double-safety / `load_bug_report(expect_root_cause="prd-exception")` / 读 INCIDENT frontmatter 校验 `triggered_by_bug == BUG bug_id` / `_run_update_pipeline(event_name="incident-start")`
  - 新增 `cmd_incident_resolve`：从 progress.md 读 `incident_report_path` / `validate_doc` 二次 / 读 INCIDENT frontmatter 校验 `resolution_action == --action` 且 `status == review-passed` / `_run_update_pipeline(event_name="incident-resolve")`
  - argparse 加 `incident-start` / `incident-resolve` 两个子命令；dispatcher 加分支
  - `apply_incident_start` / `apply_incident_resolve` / `_validate_incident_path_shape` 加入 import
- 新建 tests `tests/test_apply_incident_start.py`（16 testcases）
- 新建 tests `tests/test_apply_incident_resolve.py`（24 testcases）
- 新建 tests `tests/test_progress_incident.py`（26 testcases；含 6 argparse / 1 happy start / 4 reject start / 3 happy resolve / 4 reject resolve / 4 terminal-state semantics / 2 recover roundtrip / 1 lock）
- 扩展 tests `tests/test_progress_replay.py`：
  - `ReplayUnsupportedEventTests` 样本从 `incident-start`（Phase 6.2 placeholder）改为 `update-advance`（Phase 6.4 placeholder）
  - `test_supported_events_in_phase_6_2` 重命名 `_phase_6_3` 并加 2 个 incident events（共 14 项）
  - `ReplayTerminalSemanticsTests`：从断言 empty `TERMINAL_EVENTS` 改为断言 `{"incident-resolve"}` + 新增 `TERMINAL_INCIDENT_ACTIONS` 断言
  - 新增 `ReplayIncidentTests`（10 testcases：happy start / missing token reject / continue 非终态 / abort 终态 / abort 后 mutating reject / reconstruct 后 mutating reject / missing action reject / unknown action reject / does not read artifacts）
- 调整 tests `tests/test_progress_recover.py`："未支持事件"样本同步换 `update-advance` + 注释从 "Phase 6.2" 改 "Phase 6.3"

Phase 6.3 **不**实现：

- Phase 6.4: `update --advance`（P6 矩阵 + required-artifacts + breakdown count 一致性）
- Phase 6.4: `validate.py consistency`（doc-guardian 端 Class 8 cross-progress 校验）
- INCIDENT body content / `Pending Changes` 内容验证（owner 是 workflow-evolution skill；validate.py 端的 frontmatter 类校验是 6.3 唯一 doc-side gate）
- abort/reconstruct 之后用户工作流路由（user/workflow-evolution territory）

这些不能因为它们在 6.3 里"还没写"而被当 finding。

## 当前工作背景

Task 6 全部前序 phase 已闭合：

- Phase 1-4 / 5 (4 sub-phases) / 6.1 / 6.2 全部 (A) closed。Phase 6.2 + 3 Low polish 全部落地（`task6_phase6_2_bug_rework_review_20260507.md` 给 (A)）。

Phase 6 sub-phase 切分（user agreed 4-split）：

- Phase 6.1 ✅: bug-start + bug-close + Gap-3 update --task
- Phase 6.2 ✅: bug-rework + Gap-4/5 reuse
- **Phase 6.3**（本批）: incident-start + incident-resolve + TERMINAL_EVENTS 首次激活
- Phase 6.4: update --advance + validate.py consistency

Phase 6.3 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 713 tests in 6.4s — OK
#  - baseline (Phase 1-4 + 5.* + 6.1 + 6.2 含 L1/L2/L3 polish):  637
#  - new in Phase 6.3:                                            76
#    * test_apply_incident_start.py                       : +16
#    * test_apply_incident_resolve.py                     : +24
#    * test_progress_incident.py                          : +26
#    * test_progress_replay.py +new ReplayIncidentTests    : +10
#    * test_progress_replay.py +TERMINAL_INCIDENT_ACTIONS  :  +1
#    *                          rename supported_events    :   0 net
#  - test_progress_replay.py / test_progress_recover.py   :  -1 / 0 net
#    （unsupported event 样本切到 update-advance；从 incident-start 改）

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py --help
# 12 子命令: init / query / recover / update / release-close / release-start / bug-intake / bug-start / bug-close / bug-rework / incident-start / incident-resolve
```

End-to-end smoke 已通过 `tests/test_progress_incident.py`：

- IncidentStartHappyTests / IncidentResolveHappyTests 覆盖 incident-start 1 happy + incident-resolve 3 actions 各自 happy
- IncidentStartRejectionTests 覆盖 active-incident reject / validate.py 双重校验 reject（BUG 端 + INCIDENT 端各 1）/ BUG.root_cause != prd-exception reject / INCIDENT.triggered_by_bug != BUG.bug_id reject
- IncidentResolveRejectionTests 覆盖 no-active-incident / action 与 INCIDENT.resolution_action 不匹配 / INCIDENT.status != review-passed / validate.py reject
- TerminalStateSemanticsTests 覆盖 abort 后 query / recover 仍可 / abort 后 update --event reject / reconstruct 后 bug-intake reject（终态校验全链路）
- IncidentRecoverRoundtripTests 覆盖 continue / abort 各自 recover 还原所有终态字段
- IncidentLockTests 覆盖 incident-start 锁阻塞

## 阅读顺序

1. `docs/review/task6_phase6_2_bug_rework_review_20260507.md` —— Phase 6.2 closure (A) + 3 Low fixes 摘要
2. `docs/handoff/session_handoff_task6_phase6_3_20260507.md` §0-§9 —— Phase 6.3 scope + work order + watch points（包括 §4.7 Option A vs B 决策点）
3. `skills/workflow-protocol/references/command-reference.md` §11（incident-start）+ §12（incident-resolve 三子节）+ 状态机表 11.1 / 12.x mutation 行
4. `skills/doc-guardian/references/frontmatter-schema.md` §3.4 workflow-incident schema + §4.4 / §4.6 incident_id / triggered_by_bug 校验
5. `skills/_shared/dev_workflow/progress_state.py`（重构 `_validate_bug_path_shape` + 新增 `_validate_incident_path_shape` + `apply_incident_start` + `apply_incident_resolve`；新增段在 `apply_bug_close` 之后）
6. `skills/_shared/dev_workflow/progress_replay.py`（+ 2 个 incident handler；`_HANDLERS` / `TERMINAL_EVENTS` / `TERMINAL_INCIDENT_ACTIONS` / dispatch loop action-aware gate）
7. `skills/workflow-protocol/scripts/progress.py`（+ `_DOC_GUARDIAN_SCRIPTS` import / `validate_doc` helper / `cmd_incident_start` / `cmd_incident_resolve` / argparse + dispatcher）
8. `skills/doc-guardian/scripts/validate.py`（仅作 reference：`validate_file(doc_path, root) -> list[str]` 是 progress.py M6 double-safety 唯一 entry point）
9. `tests/test_apply_incident_start.py` / `tests/test_apply_incident_resolve.py` / `tests/test_progress_incident.py`
10. `tests/test_progress_replay.py`（新 `ReplayIncidentTests` + 修改的 `ReplayTerminalSemanticsTests` / `ReplayUnsupportedEventTests` / `ReplayMonotonicityTests`）/ `tests/test_progress_recover.py`（unsupported event 样本同步）

## Phase 6.3 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 6.3 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。Tests 必须用 `tempfile.TemporaryDirectory` 隔离。
2. **incident-start 状态机严格按 command-reference.md §11**：project_state=active + iter ≤ 7 + bug_flow.active=false + workflow_incident_active=false + 双 path shape 合法 + BUG `validate.py file` exit 0 + INCIDENT `validate.py file` exit 0 + BUG.root_cause=prd-exception + INCIDENT.triggered_by_bug==BUG.bug_id。
3. **incident-start Mutation**：bug_flow.{active,bug_report_path,root_cause}=true/path/"prd-exception"；workflow_incident_active=true；incident_report_path=path；current_stage=workflow-incident-analysis；**sub_state / review_iteration 保持不变**。
4. **incident-resolve 状态机严格按 command-reference.md §12**：iter ≤ 7 + workflow_incident_active=true + incident_path 合法 shape + 与 progress.md.incident_report_path 一致 + INCIDENT `validate.py file` exit 0 + INCIDENT.resolution_action==--action + INCIDENT.status="review-passed" + action ∈ {continue/abort/reconstruct}。
5. **incident-resolve 不 gate project_state==active**：abort/reconstruct 合法地从 active 翻转 project_state；只 gate workflow_incident_active=true 才能正确处理终态。
6. **3 个 action 分支 mutation 完全按 §12.1/§12.2/§12.3**：continue 清 incident + bug_flow + 回 testing/review-passed + iter=0；abort 终态 + project_state=aborted + release_close_reason=incident-abort + 全清 sub_state/iter/bug_flow；reconstruct 同 abort 但 project_state=reconstructing + release_close_reason=incident-reconstruct。
7. **Option B action-aware terminal gate**：`TERMINAL_EVENTS = {"incident-resolve"}` 但 dispatch loop 解析 summary 中的 `action=` token，**仅当** action ∈ {abort, reconstruct} 才翻转 seen_terminal。`--action continue` 后续 mutating event 必须**不**被拒（test 覆盖）。
8. **canonical history token**：incident-start 的 summary 含 `bug=<path> incident=<path> root_cause=prd-exception`；incident-resolve 的 summary 含 `action=<continue|abort|reconstruct> incident=<path>`。Replay 通过 `_kv_tokens` 反解；replay 不读 BUG / INCIDENT 文件（一致 Phase 5.3+ 设计契约）。
9. **M6 double-safety**：incident-start 在已被 caller (bug-triage) promote+validate 的基础上，CLI 端再次 `validate.py file` 校验 BUG + INCIDENT 两个 doc；incident-resolve 在已被 caller (workflow-evolution) finalize（Step 6.e-g）的基础上 CLI 端再次校验 INCIDENT。两次都不通过即 reject + 不动 progress.md。
10. **`_validate_bug_path_shape` refactor 完全透明**：所有既有 5.4/6.1/6.2 调用者都依然通过；refactored helper 把 BUG 与 INCIDENT 的"非空 + 无 backslash + 不绝对路径 + 无 ./.. 段 + 匹配 regex"五项合并为一个私有 `_validate_doc_path_shape`，错误消息每条都用 `label` 前缀让操作者一眼看出是 BUG 还是 INCIDENT 出问题。
11. **`prd-exception` 不进 `_ROOT_CAUSE_TO_STAGE`**：bug-rework / bug-start 的 root_cause 三向 map 仍然只有 srs / architecture / development；incident-start 直接写字面 "prd-exception" 到 bug_flow.root_cause；apply_bug_rework 已显式 reject prd-exception（Phase 6.2 留下的，6.3 加 contract test 在 test_apply_incident_start.ContractTests 里反向断言）。
12. **`validate_doc` helper 设计**：直接 in-process import `validate` 模块（不走 subprocess），调 `validate.validate_file(path, root)` 拿到 list[str]，空列表⇔合法。tests 通过 `patch.object(progress, "validate_doc", side_effect=fake)` 单点 mock 校验 reject 路径；happy path tests 写真实合法 doc 让 validate 真跑（避免 mock 漂移）。

## 重点 review 项

请按以下维度逐条核对：

### A. `_validate_doc_path_shape` 重构 + `_validate_incident_path_shape`

- 重构是否完全保持 `_validate_bug_path_shape` 的 5 项规则（非空/无 backslash/不绝对/无 ./.. 段/匹配 regex）+ 错误消息均带 `label` 前缀（BUG / INCIDENT）？
- `_INCIDENT_PATH_RE = ^docs/incident/INCIDENT-\d{3}\.md$` 与 doc-guardian `_INCIDENT_ID_RE = ^INCIDENT-\d{3}$` 的 regex 风格、3 位 zero-padded 约束保持一致？
- 既有 5.4 / 6.1 / 6.2 测试（涉及 BUG path shape 的 21+ testcases）是否全过 → refactor 透明？
- 4 处旧 `_validate_bug_path_shape` 调用点（apply_bug_intake / apply_bug_start / apply_bug_rework / cmd_bug_*）依然通过（运行 baseline 验证）？

### B. `apply_incident_start` 状态机

- 6 条前置全 enforce：project_state=active / iter ≤ 7 / bug_path shape / incident_path shape / bug_flow.active=false / workflow_incident_active=false？
- mutation 仅触动 bug_flow / workflow_incident_active / incident_report_path / current_stage / updated；其它字段（含 sub_state / review_iteration / unresolved_bugs / 项目级 artifacts）原样保留？
- bug_flow.root_cause 直接写字面 "prd-exception"（不进 `_ROOT_CAUSE_TO_STAGE`）？
- history summary 含 canonical token：`bug=<path> incident=<path> root_cause=prd-exception PRD exception triggered`？
- 16 单测覆盖：1 happy（bug_flow + incident state 同时开启）+ 5 sub-state 保持 / iter 保持 / 3 stage 都可触发 / history token / 9 reject（active bug flow / 已在 incident / aborted / reconstructing / iter > 7 / 错 bug path / 错 incident path / 非 canonical incident / 错 now）+ 1 outcome frozen + 1 prd-exception 不进 ROOT_CAUSES_FOR_BUG_START？

### C. `apply_incident_resolve` 状态机

- 4 条通用前置全 enforce：iter ≤ 7 + incident_path shape + workflow_incident_active=true + incident_path == state.incident_report_path + action ∈ {continue/abort/reconstruct}？
- **不 gate** project_state==active（区别于 bug-* 系列）？
- continue mutation 完整：清 incident + bug_flow + current_stage=testing + sub_state=review-passed + iter=0 + project_state 不动？
- abort mutation 完整（v0.6 F11 cleanup）：project_state=aborted / release_state=closed / release_close_reason=incident-abort / current_stage=null / sub_state=null / iter=0 / bug_flow 全清 / incident state 全清？
- reconstruct mutation 完整：与 abort shape 一致但 project_state=reconstructing + release_close_reason=incident-reconstruct + history_next 提到 "new directory"？
- `is_terminal: bool` 标志在 outcome 上正确设置：continue=False / abort=True / reconstruct=True？
- history summary 含 canonical token：`action=<v> incident=<path> Incident resolved`？
- 24 单测覆盖：5 continue / 4 abort / 3 reconstruct + 2 完整 cleanup 字段断言 + 7 reject（no incident active / path 不匹配 / 错 path shape / 错 action / iter > 7 / 错 now / continue 不需 active project）+ 2 contract（outcome frozen / is_terminal 与 action 映射一致）？

### D. `progress_replay` Option B action-aware terminal gate

- `TERMINAL_EVENTS = {"incident-resolve"}` 必要不充分；`TERMINAL_INCIDENT_ACTIONS = frozenset({"abort", "reconstruct"})` 是 frozenset 防止外部 mutate 策略？
- dispatch loop 末尾 gate 改为 `if entry.event in TERMINAL_EVENTS: action = _kv_tokens(entry).get("action"); if action in TERMINAL_INCIDENT_ACTIONS: seen_terminal = True`？
- gate 在 handler 调用**之后**触发（保证 handler 已 raise 任何 ProgressStateError 才考虑 terminal flag），重 parse `_kv_tokens` 是显式安全？
- READ_ONLY_EVENTS 仍空（Phase 6.3 没有新增 read-only event；recover 自身不 append history）？
- `_apply_incident_start_handler` 必含 bug + incident token，缺任一 raise ReplayError "missing"；`_apply_incident_resolve_handler` 必含 action + incident token，缺任一 raise ReplayError "missing"；root 参数 `del`？
- `_HANDLERS` 现 14 项；module docstring + unsupported-event 错误消息 / `supported_events_in_phase_6_3` 测试断言精确？
- replay 不读 BUG / INCIDENT 文件（test 覆盖：`test_incident_replay_does_not_read_artifact_files` 用空 tempdir）？

### E. `cmd_incident_start` / `cmd_incident_resolve` CLI

- `validate_doc(path, root) -> list[str]` 直接 in-process import `validate` 模块（lazy import inside helper），单点 entry point 便于 mock，文档说明清晰？
- argparse: incident-start 含 --bug + --report + --agent；incident-resolve 含 --action + --agent；缺关键参数 → exit 2；非法 action / 错 path shape / validate.py reject / 跨字段不一致 → exit 1？
- incident-start 流程顺序：argparse → 双 path resolve+containment → progress.md 存在 → 双 validate_doc → load_bug_report (expect_root_cause=prd-exception) → 读 INCIDENT frontmatter (triggered_by_bug==bug_id) → `_run_update_pipeline`？任一步失败 progress.md 字节级未改？
- incident-resolve 流程顺序：argparse → action ∈ {3} 校验（exit 1 不是 exit 2）→ progress.md 存在 + parseable → workflow_incident_active=true 检查 → 取 incident_report_path → validate_doc → 读 INCIDENT frontmatter (resolution_action==action AND status==review-passed) → `_run_update_pipeline`？
- main dispatcher 两个新分支齐全？
- `validate_doc` 在 incident-start 双重调用（BUG + INCIDENT）顺序合理：先 BUG 再 INCIDENT 让操作者最早看到错误？

### F. tests 设计

- 单测全部 pure（不走 CLI）；CLI 集成 `_install_test_stage_advance_handler` + `_FakeClock` 风格与 Phase 6.1 / 6.2 一致；M6 double-safety reject path 通过 `patch.object(progress, "validate_doc", side_effect=...)` 单点 mock？
- happy path tests 用真实合法 BUG / INCIDENT 文件（含 Change Log section）让 validate.py 真跑（端到端真实路径），避免 mock 漂移？
- 26 个 CLI 测试覆盖：6 argparse + 1 happy start + 4 reject start + 3 happy resolve（continue / abort / reconstruct）+ 4 reject resolve + 4 terminal-state semantics（query 仍工作 / recover 仍工作 / abort 后 update --event reject / reconstruct 后 bug-intake reject）+ 2 recover roundtrip（continue / abort）+ 1 lock？
- `ReplayIncidentTests` 10 个用例：happy start / missing token start / continue 非终态 / abort 终态 / abort 后 mutating reject / reconstruct 后 mutating reject / missing action token / unknown action / does not read files？
- `ReplayTerminalSemanticsTests` 从 empty 断言改为 `{"incident-resolve"}` + 新增 TERMINAL_INCIDENT_ACTIONS 断言？
- `ReplayUnsupportedEventTests.test_supported_events_in_phase_6_2` 重命名 `_in_phase_6_3` 并加 incident-start / incident-resolve（共 14 events）？unsupported event 样本（`test_unknown_event_rejected` / `test_timestamp_check_fires_before_handler_dispatch` / `test_recover_rejects_history_with_unsupported_event`）从 `incident-start` 改为 `update-advance`？

### G. 既有 invariant 是否保持

- Phase 1-4 + Phase 5.x + Phase 6.1 + Phase 6.2 + L1/L2/L3 polish 的 637 测试是否仍全过？
- M1（history parse + replay 一致性 + state diff）+ M2（review_iteration > 7 entry guard）在 incident-start / incident-resolve 路径上保持继承（两者都走 `_run_update_pipeline`）？
- `progress_lock.py` / `progress_history.py` / `progress_artifacts.py` / `validate.py` / `changelog.py` / `status_transition.py` 未被本批触动？
- `init` / `query` / `recover` / `update --event` / `update --task` / `release-*` / `bug-intake` / `bug-start` / `bug-close` / `bug-rework` 行为完全保留？尤其是 `_validate_bug_path_shape` refactor 后所有 BUG-相关 happy + reject 路径全过？
- `_run_update_pipeline` + `extra_writes_factory` 钩子未被触动？
- `_validate_bug_path_shape` 与 `_validate_incident_path_shape` 共享私有 helper 后，错误消息 label 前缀清晰（BUG / INCIDENT 各自）？

### H. 设计 / 可维护性

- `validate_doc` 直接 import 设计 vs subprocess：选择直接 import 是否合理？trade-offs 是 (1) 不需要管理子进程、不会有 PATH/venv 问题 (2) tests 单点 mock 简单（patch.object on validate_doc 一处）vs (3) 跨 skill 直接 import 让 dependency graph 隐性？是否需要在 SKILL.md / handoff 中显式声明 doc-guardian 是 progress.py 的硬依赖？
- `validate_doc` 用 lazy import（inside function）vs top-of-file import：lazy 让 progress.py 启动时不需要 doc-guardian 加载；但 tests 已经把 doc-guardian/scripts 加入 sys.path（与 progress.py 同步注入），lazy 可以再降一次首次启动开销？
- `apply_incident_start` 与 `apply_bug_start` 都"开启 bug_flow"，但前者多写 workflow_incident_active + incident_report_path 字段；是否考虑后续抽出 `_open_bug_flow(...)` helper？现阶段不抽是否合适（spec/intent 明显不同）？
- 3 个 action 分支在 `apply_incident_resolve` 内部用 if/elif 分支：是否考虑 dict-based dispatch？现阶段 if/elif 是否更可读（每条 mutation 表显式列在源码中，便于与 spec 对照）？
- `_INCIDENT_RESOLVE_ACTIONS` / `_INCIDENT_TERMINAL_ACTIONS` 模块级 frozenset：scope 选择合理？是否考虑暴露为 public（如 `INCIDENT_RESOLVE_ACTIONS`）让 CLI argparse `choices=` 复用？现版 CLI 故意不用 choices=（exit 1 vs exit 2 区分）；这是 Phase 5.1 round 2 M2 contract 的一致做法吗？
- `_validate_doc_path_shape` 命名是否合适（已经"doc"很泛）；是否考虑 `_validate_relative_doc_path_shape`？
- `apply_incident_resolve` 的 `is_terminal` 字段是否需要进 history token？目前不需要（replay 通过 action 重导出）；这种"forward outcome 比 history token 多一字段"的设计与 BugStartOutcome.rollback_decisions 类似，是否 consistent？

### I. Cross-doc 一致性

- `command-reference.md §11` (incident-start) 字段 mutation 表与 `apply_incident_start` 完整对齐（含 sub_state / review_iteration **不动**）？
- `command-reference.md §12.1/§12.2/§12.3` (incident-resolve 三个 action) 字段 mutation 表与 `apply_incident_resolve` 三个分支完整对齐？
- `command-reference.md §11/§12` "前置条件" 列表与 CLI 端 + apply 函数前置校验加起来是否完整覆盖？
- `frontmatter-schema.md §3.4` workflow-incident frontmatter（incident_id / triggered_by_bug / triggered_in_release / resolution_action）是否被 `cmd_incident_start` / `cmd_incident_resolve` 通过 validate_doc + 读 frontmatter cross-check 全部 enforce？
- `directory-layout.md` `docs/incident/INCIDENT-NNN.md` path pattern 与 `_INCIDENT_PATH_RE` 一致？
- `task6_plan_20260507.md` §13 phase 6 边界声明 incident-start/incident-resolve 在 6.3、advance/consistency 在 6.4：6.3 实施严格守此边界？

### J. 已知 Phase 6.4 后续工作（不在本 review 评判范围）

- Phase 6.4 `update --advance`：P6 矩阵 + required-artifacts.md condition DSL 求值（Phase 2 已有 conditions/artifacts.py）+ doc-guardian validate.py file 调用 + breakdown count/declared 一致性
- Phase 6.4 `validate.py consistency`：doc-guardian 端 Class 8 cross-progress 校验

这些不应作为 Phase 6.3 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_3_incident_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 6.3 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6.4
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §11/§12 + frontmatter-schema.md §3.4 + directory-layout.md + task6_plan §13 + SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§I 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 validate_doc 直接 import vs subprocess、apply_incident_resolve action 分支抽象、`_INCIDENT_RESOLVE_ACTIONS` 是否暴露 public 的看法）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 6.4 (`update --advance` + `validate.py consistency`)**
   - **(B) fix before Phase 6.4**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 6.4 前修
- 哪些可以推迟到 Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6.4 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
