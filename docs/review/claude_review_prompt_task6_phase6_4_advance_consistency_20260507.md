# Claude Review Prompt — Task 6 Phase 6.4 `update --advance` + `validate.py consistency`

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_4_advance_consistency_review_20260507.md`。Phase 6.4 是 **Phase 6 最后一段**；本批通过 (A) 后整个 Task 6 实现闭环。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.4 implementation** 做一次代码 review。本批是 Phase 6 的第四段也是 Task 6 整体实现的收尾：实现 `progress.py update --advance`（P6 矩阵 forward path）+ `skills/doc-guardian/scripts/validate.py consistency`（Class 8 cross-progress 校验），把 Phase 2 已落地的 `conditions.py` / `artifacts.py` 共享层接入 P6 advance + consistency 工作流。

本轮是代码 review。**写集**仅限：

- 扩展 `skills/_shared/dev_workflow/progress_state.py`：新增 `AdvanceOutcome` dataclass + `apply_update_advance`（state-machine legality only：M2 + active project + workflow_incident_active=false + next_stage 存在 + gated/non-gated/development 三类 sub_state 前置 + Stage 4 surrogate "all task_states verified" + testing 期间禁 active bug flow）
- 扩展 `skills/_shared/dev_workflow/progress_replay.py`：新增 `_apply_update_advance_handler`，必含 `from=` / `to=` token；handler 在 apply 之后做 state-diff guard（M1 之外的额外 defense-in-depth：若 `outcome.new_state.current_stage != to=` 则 reject "history may be corrupt"）；module docstring + unsupported-event 错误消息更新到 6.4 closes Phase 6
- 扩展 `skills/doc-guardian/scripts/validate.py`：替换 `consistency` 子命令的 deferred stub 为实现：读 `progress.md`，调 `get_required_artifacts(progress, root)` 派生当前 stage 的必备 artifact list，对每个 spec 校验 (a) 文件存在 (b) `validate_file(spec.path, root)` 返回空；workflow-incident-analysis 直接返回 [] 跳过 P6（按 spec §9）；`all` 子命令现明确 deferred to Phase 7
- 扩展 `skills/workflow-protocol/scripts/progress.py`：
  - import `apply_update_advance` + `NEXT_STAGE` + `GATED_STAGES`
  - `cmd_update` 加 `--advance` 分支
  - 新 `_do_update_advance` 实现 P6 forward path（A 收集 ALL missing path 后再 reject；B 对每个 present path 跑 `validate_doc` 收集所有 issue；E 调 stage-specific helper `_check_p6_dim_e`；最后走 `_run_update_pipeline(event_name="update-advance")`）
  - 新 `_check_p6_dim_e` 内部 import `progress_artifacts.load_test_report` / `load_artifact_frontmatter`；testing 校验 test-report.verification_status=pass；delivery 校验 installation-result.verification_status=pass；development 不读 per-task verification_result（surrogate 在 apply 已 enforce）；其它 stage 跳过 E
  - argparse `update` mutex group 加 `--advance` (action="store_true")
- 新建 `tests/test_apply_update_advance.py`（22 testcases：3 gated + 4 dev surrogate + 4 non-gated + 1 retro reject + 5 general reject + 2 history token + 2 contract）
- 新建 `tests/test_validate_consistency.py`（12 testcases：2 happy + 6 reject + 4 CLI integration）
- 新建 `tests/test_progress_update_advance.py`（16 testcases：3 argparse mutex + 3 happy + 2 A reject + 1 B reject + 2 E reject + 3 state-machine reject + 1 recover + 1 lock）
- 扩展 `tests/test_progress_replay.py`：新 `ReplayUpdateAdvanceTests`（4 testcases：happy / missing token / to= mismatch / no artifact reads）；`test_supported_events_in_phase_6_3` 重命名 `_in_phase_6_4` 含 15 events；`test_unknown_event_rejected` / `test_timestamp_check_fires_before_handler_dispatch` 样本从 `update-advance` 改为 `synthetic-test-event`（明确 not-on-roadmap 占位）
- 扩展 `tests/test_progress_recover.py`：unsupported event 样本同步切到 `synthetic-test-event`

Phase 6.4 **不**实现（Phase 7 territory）：

- `validate.py all`（仍 returns 2 with explicit Phase 7 message）
- 端到端 managed-project happy path smoke（Phase 7）
- progress.md `artifacts:` dict 在 advance 时按 stage 重初始化（user 决定保留 spec 模糊性，不在 6.4 scope）
- Stage 4 → Stage 5 advance 时再读每个 task 的 `verification_result.md`（apply surrogate 已 enforce all task_states verified；CLI E dim 不重复校验）

这些不能因为它们在 6.4 里"还没写"而被当 finding。

## 当前工作背景

Task 6 Phase 1 / Phase 2 / Phase 3 / Phase 4 / Phase 5（4 sub-phases）/ Phase 6.1 / Phase 6.2 / Phase 6.3（含 round 2 + 1 non-blocking Low）全部 (A) closed。本批是 Phase 6 收尾。

Phase 6 sub-phase 切分（user agreed 4-split）：

- Phase 6.1 ✅: bug-start + bug-close + Gap-3 update --task
- Phase 6.2 ✅: bug-rework + Gap-4/5 reuse
- Phase 6.3 ✅: incident-start + incident-resolve + TERMINAL_EVENTS + Option B action-aware terminal gate
- **Phase 6.4**（本批）: update --advance (P6 matrix) + validate.py consistency

Phase 6.4 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 773 tests in 6.9s — OK
#  - baseline (Phase 1-4 + 5.* + 6.1 + 6.2 + 6.3 round 2 + 6.3 round-2 L1): 719
#  - new in Phase 6.4:                                                       54
#    * test_apply_update_advance.py                          : +22
#    * test_validate_consistency.py                          : +12
#    * test_progress_update_advance.py                       : +16
#    * test_progress_replay.py +new ReplayUpdateAdvanceTests :  +4
#    * test_progress_replay.py +supported_events            :   0 net (rename)
#    * test_progress_replay.py / test_progress_recover.py   :   0 net (sample swap)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py update --help | grep -- '--advance'
# --advance        Phase 6.4: explicit stage advance after the current stage's P6 matrix passes...

python3 skills/doc-guardian/scripts/validate.py consistency --help
# usage: validate.py consistency [-h]
```

End-to-end 验证：

- `tests/test_progress_update_advance.py` 跑通了 prd→srs / dev→testing / testing→delivery 三个代表性 happy path（用 mocked `validate_doc` 隔离 doc-guardian compliance），加上 A reject（缺 artifact，列出全部 missing path）/ B reject（mocked validate_doc 返回 issues）/ E reject（fail / partial test-report）/ state-machine reject（active bug flow / retrospective / gated stage 用 review-passed）/ recover roundtrip / lock blocking
- `tests/test_validate_consistency.py` 端到端 cover 真实 doc-guardian validate（happy with PRD on disk + workflow-incident-analysis 跳过 P6）+ 6 种 reject path + 4 项 CLI integration（exit 0 / exit 1 / `all` 仍 deferred）

## 阅读顺序

1. `docs/review/task6_phase6_3_incident_round2_review_20260507.md` —— Phase 6.3 round 2 closure (A) + 1 non-blocking Low（已修复）
2. `docs/handoff/session_handoff_task6_phase6_4_20260507.md` §0-§9 —— Phase 6.4 scope + work order + watch points
3. `docs/implementation/task6_plan_20260507.md` §10（Condition DSL + required-artifacts resolver；Phase 2 已实现）+ §7（validate.py Class 8 = consistency）+ §13 phase boundaries
4. `skills/workflow-protocol/references/command-reference.md` §2.2（`--advance` 子选项 — primary spec 源）+ 状态机表 line ~615
5. `skills/doc-guardian/references/required-artifacts.md` §1-§12（P6 fact source + condition DSL + consistency algorithm sketch）
6. `skills/_shared/dev_workflow/conditions.py`（Phase 2 — whitelist DSL parser，无 eval）/ `artifacts.py`（Phase 2 — `get_required_artifacts(progress, root)` + `progress_from_mapping` + `condition_variables`）
7. `skills/_shared/dev_workflow/progress_state.py` 新 `apply_update_advance` + `AdvanceOutcome`（在 `apply_incident_resolve` 之后）
8. `skills/_shared/dev_workflow/progress_replay.py` 新 `_apply_update_advance_handler`（含 to= state-diff guard）；`_HANDLERS` 现 15 项；module docstring + unsupported-event 文案改到 6.4 closes Phase 6
9. `skills/doc-guardian/scripts/validate.py` 新 `check_consistency` + `consistency` CLI 分支；`all` 现 deferred to Phase 7
10. `skills/workflow-protocol/scripts/progress.py` 新 `_do_update_advance` + `_check_p6_dim_e`；`cmd_update` dispatcher + argparse `--advance`
11. `tests/test_apply_update_advance.py` / `tests/test_validate_consistency.py` / `tests/test_progress_update_advance.py`
12. `tests/test_progress_replay.py` 新 `ReplayUpdateAdvanceTests` + supported_events / unsupported event 样本切换；`tests/test_progress_recover.py` 同步

## Phase 6.4 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 6.4 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。Tests 必须用 `tempfile.TemporaryDirectory` 隔离。
2. **`apply_update_advance` 状态机严格按 command-reference.md §2.2**：
   - 必备前置：M2 (review_iteration ≤ 7) + project_state=active + workflow_incident_active=false + current_stage ∈ NEXT_STAGE keys
   - gated stages (PRD/SRS/Architecture)：sub_state==`approved`
   - development：所有 task_states 值 == `verified`，且至少有一个 task
   - 其它 non-gated（testing/delivery）：sub_state==`review-passed`
   - testing 额外：bug_flow.active==false（active flow must close via bug-close 先）
   - retrospective：reject 并提示 `release-close`
3. **mutation 仅触动 current_stage / sub_state / review_iteration / updated**：`artifacts:` dict 故意**不重初始化**（user 决定保留模糊性，stage write skill 自管 entry；Phase 7 视情况调整）。
4. **canonical history token**：`from=<old> to=<new> Stage advance`（_kv_tokens 反解）；history_result 是 `current_stage=<new> sub_state=write iteration=0`；history_next 是 `<new>-write`（与 §11/§12 风格一致）。
5. **replay handler 防 history corruption**：除 M1（forward outcome vs replay diff）+ token presence check 外，再加一层 state-diff guard：`outcome.new_state.current_stage != to=` 则 reject "history may be corrupt"。
6. **CLI P6 forward 顺序 A → B → E → apply**：A 收集所有 missing path 后再 reject；B 对每个 present path 跑 `validate_doc` 收集所有 per-file issue；E 用 stage-specific helper `_check_p6_dim_e`；任一 dim 失败 progress.md 字节级未改。
7. **CLI E dim 实现**：testing 调 `load_test_report(root, release)` 校 `verification_status==pass`；delivery 调 `load_artifact_frontmatter("installation-result", release)` 校 `verification_status==pass`；development 不重读 per-task verification_result（apply surrogate 已 enforce）；其它 stage 跳过 E。
8. **`validate.py consistency` 算法**：读 progress.md → 派生 required artifact list → 对每个 path 校 (a) 存在 (b) `validate_file(path, root)` 返回空；workflow-incident-analysis 跳过；malformed progress.md frontmatter / 缺 current_stage / unknown current_stage 各自精确报错；exit 0 OK / exit 1 inconsistent / exit 2 仅 usage error。
9. **import 路径与现有惯例一致**：`progress_state.py` 不 import `validate.py`（避免环依）；`validate.py` lazy import `skills._shared.dev_workflow.artifacts`（避免 startup 时强制依赖）；`_do_update_advance` lazy import `artifacts` + `progress_artifacts`（与既有 cmd_bug_* 风格一致）。
10. **既有 invariant 全部继承**：`_run_update_pipeline` 的 M1 + lock + atomic write 在 advance 路径上保持；apply_update_advance 调 `_validate_active_project` + `_validate_review_iteration_value` 保持 M2；canonical token 契约保持。
11. **15 events / 12 CLI 子命令 final state**：`update --advance` 不增加 CLI 子命令计数（join 既有 update mutex group）；replay 总数 14 → 15；TERMINAL_EVENTS 仍 `{"incident-resolve"}` 不动。
12. **unsupported event 样本永久占位**：从 `update-advance` 切到 `synthetic-test-event`，明确不是 future-phase 占位、是故意永远不会被支持的合成名，让测试在 Phase 7+ 也保持 meaningful。

## 重点 review 项

请按以下维度逐条核对：

### A. `apply_update_advance` 状态机

- 6 类前置全 enforce：M2 + active project + workflow_incident_active=false + next_stage 存在 + 三类 sub_state 前置（gated/dev/non-gated）+ testing 不接受 active bug flow？
- mutation 仅触动 current_stage / sub_state=write / review_iteration=0 / updated；其它字段（含 artifacts / bug_flow / development_state / unresolved_bugs / project_state / release_state）原样保留？
- gated stages 的 `sub_state==approved` 来自 apply_update_event(human-confirmed)；non-gated 的 review-passed 来自 apply_update_event(review-passed)；这种"两类前置由不同 event 自然形成"的设计是否清晰？
- development 分支用 task_states.values() == "verified" 全集判断；空 dict reject "at least one"；非全 verified reject 并按字典序列出 non_verified？
- retrospective reject 消息提到 `release-close`（操作者 next step 明确）？
- history summary 含 canonical `from=` / `to=` token + 字面词 `Stage advance`？
- 22 单测覆盖：3 gated（prd/srs/arch）+ 4 dev（happy / 1 task 未 verified / 空 dict / 缺 development_state）+ 3 non-gated（testing / delivery / testing 含 active bug flow）+ 1 retrospective + 5 general reject（aborted / reconstructing / incident active / iter > 7 / 错 now）+ 2 history token + 2 contract（outcome frozen / NEXT_STAGE 完整性）？

### B. `_apply_update_advance_handler` replay handler

- 必含 `from=` 与 `to=` token，缺任一 raise ReplayError "missing"；root 参数 `del` 明确忽略？
- 调 `apply_update_advance(state, now=entry.timestamp)` → 不传 from/to 给 apply（apply 从 state 推导）→ 然后比较 `outcome.new_state.current_stage` 与 `tokens["to"]`；不一致 raise "history may be corrupt"？
- 这层 state-diff guard 与 `_run_update_pipeline` M1 区别：M1 是 forward 路径自检（发现 progress.md 与 history 重放不符则 reject）；handler guard 是 replay 路径自检（发现 history 内 to= 与 state-machine 推导不符则 reject）—— 二者互补？
- 4 个 ReplayUpdateAdvanceTests 是否覆盖：happy / missing token / to= mismatch / no artifact reads？

### C. `validate.py consistency` 实现

- `check_consistency(root)` 函数：读 progress.md → frontmatter parse error → 单 issue 返回；缺 current_stage → 单 issue 返回；unknown current_stage → ArtifactError 转 issue；workflow-incident-analysis 跳过 → 返回 []？
- `get_required_artifacts(fm, root=root)` 返回 list[ArtifactSpec]；遍历去重（`seen` set）；对每个 spec：(a) 文件不存在 → "required artifact missing: <path> (type=<type>)"；(b) 存在 → `validate_file(spec.path, root_path)` 收集 per-file issue 加 `<path>:` 前缀？
- `consistency` CLI exit 0 (issues==[]) / exit 1 (issues != []) / exit 2 仅 usage error；`all` 现明确返回 2 + "deferred to Phase 7" 文案？
- 12 单测覆盖：2 happy（prd-inception with PRD / workflow-incident-analysis 跳过）+ 6 reject（missing progress / malformed progress / missing artifact / artifact invalid / unknown stage / 缺 current_stage 字段）+ 4 CLI integration（happy / missing progress exit 1 / missing artifact exit 1 / `all` deferred exit 2）？
- `validate_file(path, root)` 复用既有 Phase 3 实现，未引入重复逻辑？

### D. `_do_update_advance` CLI

- 7 步流程：(1) progress.md 存在 + parse (2) current_stage 类型校验 (3) 若 current_stage ∈ NEXT_STAGE → 跑 P6 A/B/E（否则跳过 P6 让 apply 产生 "no next stage" 错误）(4) A: get_required_artifacts → 收集 ALL missing path → reject (5) B: 对每个 present path validate_doc → 收集 ALL per-file issue → reject (6) E: `_check_p6_dim_e(current_stage, fm, root)` (7) `_run_update_pipeline(event_name="update-advance")`
- A reject 列出**所有** missing path（不止第一个）让 operator 一次修完？
- B reject 列出**所有** per-file issue（含 path 前缀）让 operator 知道每个 doc 哪里坏？
- E reject 仅触发于 testing/delivery（development surrogate 已在 apply）；testing 调 `load_test_report` 校 verification_status==pass + 失败时提示 bug-start/bug-rework；delivery 调 `load_artifact_frontmatter("installation-result", release)` 校 verification_status==pass？
- argparse `--advance` 是 action="store_true"（无值），与 `--event` / `--task` 共享 mutex group required=True？
- `cmd_update` dispatcher 三分支顺序合理（event 优先，task 次之，advance 最后）？
- 16 CLI 测试覆盖：3 argparse mutex + 3 happy + 2 A reject（单 path / 多 path 列出）+ 1 B reject（mocked validate_doc）+ 2 E reject（fail / partial test-report）+ 3 state-machine reject（active bug flow / retrospective / gated 用 review-passed）+ 1 recover roundtrip + 1 lock？
- happy path 测试用 `patch.object(progress, "validate_doc", return_value=[])` 短路 doc-guardian compliance；真实 doc-guardian 校验由 `test_validate_consistency.py` cover —— 这种关注点分离合理？

### E. tests 设计

- 单测 pure（不走 CLI）；CLI 集成 `_install_test_stage_advance_handler` + `_FakeClock` 风格与 6.1/6.2/6.3 一致；mock `validate_doc` 通过 `patch.object` 单点 mock？
- ReplayUpdateAdvanceTests 4 个用例覆盖完整：happy / missing token / to= mismatch / 不读 artifact？
- supported_events 测试从 `_in_phase_6_3` 重命名 `_in_phase_6_4` 含 15 events？
- "未支持事件"样本从 `update-advance` 切换到 `synthetic-test-event`，避免 Phase 7+ 引入新 event 时这测试不再 meaningful？test_progress_recover.py 同步更新？
- ReplayTerminalSemanticsTests 仍断言 `TERMINAL_EVENTS == {"incident-resolve"}`（Phase 6.4 不动 terminal）？

### F. 既有 invariant 是否保持

- 719 测试（Phase 6.3 round 2 + 1 doc-wording fix 后基线）是否仍全过？
- M1 + M2 + L1 (canonical token) + replay-skips-artifacts 在 update-advance 路径上保持继承？
- `progress_lock.py` / `progress_history.py` / `progress_artifacts.py` / `changelog.py` / `status_transition.py` 未被本批触动？
- `init` / `query` / `recover` / `update --event` / `update --task` / `release-*` / `bug-intake` / `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` 行为完全保留？尤其是 `cmd_update` 加 advance 分支后既有 event/task 分支没有 regression？
- `_run_update_pipeline` + `extra_writes_factory` 钩子未被触动？
- `validate.py file` / `validate.py ids` 行为不变；只 `consistency` 与 `all` 子命令的实现状态变化？

### G. 设计 / 可维护性

- `apply_update_advance` 与 `apply_update_event` / `apply_update_task` 的关系：三者都是 update mutex group 下的 mode；前两者已有，apply_update_advance 加在它们之后保持类似 shape（dataclass + 校验 + mutation + history token）？
- `_check_p6_dim_e` 抽出来作为 helper 函数：clarity vs inlining？目前的 4 stage（testing/delivery/development/其它）分支 if-chain 是否清晰？
- `validate.py consistency` 内 lazy import `skills._shared.dev_workflow.artifacts` 的 trade-off：避免 startup 时强制依赖，但 import 失败时给出明确错误（defensive 代码已加）；这种 lazy import 模式在 doc-guardian 端是否合理？
- `_do_update_advance` 内 lazy import `progress_artifacts` 与 `artifacts` 的位置选择：紧贴使用点（P6 dim 检查时）vs 函数顶（启动时）；当前选择跟 cmd_bug_* 风格一致？
- `synthetic-test-event` 作为 unsupported sample 永久占位的命名是否清晰？是否考虑未来 Phase 7 加 event 时这个测试自动 grow（current 测试不会 — 它直接 assert string contains "not supported" + "synthetic-test-event"）？
- `apply_update_advance` 的 history_next 用 `<new_stage>-write`：是否与各 stage 实际 write skill 命名（如 "prd-write" / "srs-write"）一致？
- `_do_update_advance` 当前 stage 不在 NEXT_STAGE 时 skip P6 让 apply 产生 "no next stage" 错误：这种委托设计 vs 在 CLI 端先 reject—— trade-off 是？目前选择避免 P6 派生在终态/未知 stage 上跑（artifacts.get_required_artifacts 会 raise ArtifactError）；CLI 委托给 apply 让错误消息更一致？

### H. Cross-doc 一致性

- `command-reference.md §2.2` `--advance` 流程 6 步与实现完全对齐？
- `command-reference.md §2.2` "Artifact 必备清单事实源" 指向 required-artifacts.md：实现确实通过 `get_required_artifacts(...)` 走该资源，无 hardcode？
- `task6_plan_20260507.md §10` Condition DSL + ALLOWED_VARIABLES 6 项与 conditions.py 完全对齐（Phase 2 已锁定，6.4 仅消费）？
- `task6_plan_20260507.md §7` validate.py Class 8 consistency 算法描述与 `check_consistency` 实现一致？
- `required-artifacts.md §12` consistency 算法 sketch 与实现一致（含 workflow-incident-analysis 跳过）？
- `progress.py` 帮助文本 update --advance 描述清晰 + 与 spec 风格一致？

### I. Phase 6.4 acceptance

按 handoff §6 列出的 13 项验收点逐一确认：

- `progress.py update --advance --help` works ✓
- 6 stage advances 至少有代表性 happy path（prd→srs / dev→testing / testing→delivery 三个，已有）
- A/B/E reject 各有 CLI 测试展示 exit 1 + 具体 stderr + progress.md 字节级未改 ✓
- `validate.py consistency` 在 tempdir-managed projects 上 happy + reject ✓
- replay handler 注册；`supported_events()` 返回 15 ✓
- recover roundtrip 保 advance 后 state ✓
- 既有 719 测试全过；总数 ≈ 770+（实际 773） ✓
- compileall clean ✓

### J. 已知 Phase 7 后续工作（不在本 review 评判范围）

- `validate.py all`：full-project sweep over every doc type
- 端到端 managed-project happy path smoke
- progress.md `artifacts:` dict 在 advance 时按 stage 重初始化（如果用户后续判定有需要）
- Stage 4 → 5 advance 时再读每个 task 的 verification_result.md（额外 defense-in-depth；当前 surrogate 已 enforce）
- doc-guardian 的批量 consistency 报表 / 监控集成

这些不应作为 Phase 6.4 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_4_advance_consistency_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Phase 6.4 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Task 6 closure / Phase 7 启动
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — command-reference.md §2.2 + task6_plan §7/§10 + required-artifacts.md §12 + SKILL.md command matrix 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§I 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有；特别欢迎对 artifacts: dict mutation defer / `_check_p6_dim_e` 抽出粒度 / `synthetic-test-event` 永久占位策略 的看法）
6. **Recommendation** — 三选一：
   - **(A) accept; Task 6 implementation closes; ready for Phase 7 / next-task scope**
   - **(B) fix before Task 6 closure**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在 Task 6 closure 前修
- 哪些可以推迟到 Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 7 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 不要重新评判 Phase 6.1-6.3 已 (A) 部分；本 round 仅评 Phase 6.4 新增 + 与既有 invariant 的兼容性。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
