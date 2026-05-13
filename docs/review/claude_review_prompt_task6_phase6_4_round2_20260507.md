# Claude Review Prompt — Task 6 Phase 6.4 Round 2 Fixes

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_4_advance_consistency_round2_review_20260507.md`。round 1 给的是 (B) fix-before-Task-6-closure；本轮是确认 round 2 修复是否足以升 (A) 并关闭 Task 6。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.4 round 2 修复** 做一次代码 review。round 1 评审（`docs/review/task6_phase6_4_advance_consistency_review_20260507.md`）给 (B) fix-before-Task-6-closure，列出 1 H + 2 M + 2 L：

- **H1**（must fix）：delivery E-dim 调 `load_artifact_frontmatter("installation-result")` 但 `_PATH_TEMPLATES` 没注册 → delivery → project-retrospective 实际无法 advance。
- **M1**（must fix）：`_do_update_advance` 在 `_run_update_pipeline` 之前 unlocked 跑 P6 A/B/E + 不读 locked state → 并发 race 可让 advance 跳过新 stage 的 P6 校验。
- **M2**（strongly recommended）：结构残缺但可解析的 progress.md（缺 scenario / release 字段）抛 KeyError 而非 exit 1。
- **L1**（defer-able）：`validate.py` module docstring + argparse help 里 `consistency` / `all` 仍说 "deferred to Phase 5/6"。
- **L2**（defer-able）：`workflow-protocol/SKILL.md` P6 matrix Dimension A 行还指 `progress.md.artifacts:` 而非 required-artifacts.md resolver。

User 选择**全部修**（与 Phase 6.2 round 2 / Phase 6.3 round 2 一致），不留 polish 给 Phase 7 backlog。本 round 2 修复已落地。

本轮是代码 review。**写集**仅限：

- `skills/_shared/dev_workflow/progress_artifacts.py` `_PATH_TEMPLATES` 加 `"installation-result": "docs/release{release}/delivery/installation_result.md"`（**H1**）
- `skills/workflow-protocol/scripts/progress.py`：
  - `_do_update_advance` 重构为 thin wrapper，把 P6 A/B/E 的整段逻辑搬到 `_run_p6_advance_preflight(state, current_stage, root)` helper（**M1**）
  - 新 `_advance_compute_outcome(state, now, root)` lambda：在 locked compute_outcome 内做 current_stage 类型校验 → 若 ∈ NEXT_STAGE 则跑 `_run_p6_advance_preflight` → 调 `apply_update_advance`；任何 P6 失败抛 `ProgressStateError(multi-line message)`，pipeline 捕获后打印 `progress.py update: <msg>` 并不动 progress.md（**M1**）
  - `_run_p6_advance_preflight` 在 `get_required_artifacts(...)` 调用点用 try/except 捕 `KeyError`/`TypeError`/`AttributeError`，转 ProgressStateError "progress.md is structurally incomplete"（**M2**）
- `skills/doc-guardian/scripts/validate.py`：
  - 顶部 module docstring 重写 4 个 subcommand 描述（含 `consistency` 是 Class 8、`all` 是 deferred to Phase 7）+ Class index 加 Class 8（**L1**）
  - argparse `consistency` help 改为 "Class 8 cross-progress consistency check — required-artifact existence + per-file validity for the current stage"（**L1**）
  - argparse `all` help 改为 "Validate every doc in docs/ (deferred to Phase 7)"（**L1**）
  - `check_consistency` 在 `get_required_artifacts(...)` 调用点同样加 KeyError/TypeError/AttributeError 捕获 → 单 issue "progress.md is structurally incomplete: ..."（**M2**）
- `skills/workflow-protocol/SKILL.md` §5 P6 matrix 5 行重写：
  - **A** 现明确事实源是 required-artifacts.md + `get_required_artifacts(progress, root)`，**不是** progress.md `artifacts:` dict（**L2**）
  - **B** 描述精确化（A 推导出的每个路径都跑 `validate.py file`）
  - **C** / **D** 补 "由 apply_update_advance 间接 enforce" 说明
  - **E** 拆 Stage 4 / 5 / 6 三个分支精确化（Stage 4 苛 task surrogate / Stage 5 testing test-report / Stage 6 delivery installation-result）
- `tests/test_progress_update_advance.py`：
  - 新 `test_advance_delivery_to_retrospective_with_passing_installation_result` happy（**H1 regression**）
  - 新 `test_delivery_advance_rejects_with_failing_installation_result` reject（**H1 regression**）
  - 新 `AdvanceLockedStatePreflightTests`（**M1 regression**）：
    - `test_p6_dim_a_runs_against_locked_state`：development with all tasks verified 但 NO dev artifacts 在盘 → 若 P6 不跑 advance 会(错误地)成功；M1 fix 让 P6 在 lock 内跑 → reject "dimension A"
    - `test_p6_uses_locked_progress_md_not_stale_snapshot`：用 `patch.object(progress, "progress_lock", _spy_lock)` 包装 lock，acquire 后 mutate progress.md 到 state Y（development without artifacts）→ 验证 P6 看到 state Y 并 reject
  - 新 `AdvanceMalformedProgressTests` `test_missing_scenario_field_returns_exit_1_with_clean_message`（**M2 regression**）
- `tests/test_validate_consistency.py`：
  - 新 `StructurallyIncompleteProgressTests` × 3（**M2 regression**）：missing scenario / missing release / CLI exit 1

Round 2 不修改：
- `progress_state.py` 的 `apply_update_advance` 状态机（round 1 已 ✓）
- `progress_replay.py` 的 `_apply_update_advance_handler` / TERMINAL_EVENTS / `_HANDLERS` registry（round 1 已 ✓）
- 既有 `cmd_update` dispatcher / argparse mutex group（round 1 已 ✓）
- 既有 18 advance CLI tests + 22 apply tests + 12 consistency tests + 4 replay tests + recover/replay 重构（round 1 已 ✓）

## 当前工作背景

Task 6 Phase 1-3 / Phase 4 / Phase 5（4 sub-phases）/ Phase 6.1 / Phase 6.2 / Phase 6.3（含 round 2 + 1 non-blocking Low）全部 (A) closed。Phase 6.4 round 1 给 (B)；本 round 2 把 (B) 中 5 项全部修复。Round 2 (A) 后 Task 6 整体闭环。

Round 2 实施后基线：

```bash
python3 -m unittest discover -s tests
# Ran 781 tests in 7.0s — OK
#  - baseline (round 1 close): 773
#  - new in round 2:           +8
#    * test_progress_update_advance new tests   : +5
#      (delivery happy + delivery E reject + 2 M1 locked-state + 1 M2 malformed)
#    * test_validate_consistency new tests       : +3
#      (M2 missing scenario / missing release / CLI exit 1)
#  - 既有 19 advance CLI tests + 22 apply + 12 consistency 全过

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/doc-guardian/scripts/validate.py --help
# 4 subcommands: file / ids / all (deferred to Phase 7) / consistency (Class 8)

python3 skills/workflow-protocol/scripts/progress.py --help
# 12 subcommands; update has --event / --task / --advance modes
```

End-to-end 验证：

- `test_advance_delivery_to_retrospective_with_passing_installation_result` 端到端验证 H1 fix：installation-result 现可 load → delivery → project-retrospective 真的能 advance
- `AdvanceLockedStatePreflightTests` 两个 testcase 用 `patch.object(progress, "progress_lock", _spy_lock)` wrapper 在 lock acquire 后 mutate progress.md，验证 P6 看到 locked-state 而非 pre-lock snapshot
- `StructurallyIncompleteProgressTests` × 3 端到端验证 M2：缺 scenario / 缺 release / CLI exit 1 都拿到 clean diagnostic 而不是 traceback

## 阅读顺序

1. `docs/review/task6_phase6_4_advance_consistency_review_20260507.md` round 1 评审报告（5 项 finding 一览 + recommendation）
2. `skills/_shared/dev_workflow/progress_artifacts.py` `_PATH_TEMPLATES` 现含 installation-result（H1）
3. `skills/workflow-protocol/scripts/progress.py`：
   - `_do_update_advance` thin wrapper（M1）
   - `_advance_compute_outcome` 与 `_run_p6_advance_preflight`（M1 + M2 一并修，try/except KeyError/TypeError/AttributeError）
4. `skills/doc-guardian/scripts/validate.py`：
   - 顶部 module docstring 重写（L1）
   - argparse help 重写（L1）
   - `check_consistency` 加 KeyError/TypeError/AttributeError 捕获（M2）
5. `skills/workflow-protocol/SKILL.md` §5 P6 matrix 5 行重写（L2）
6. `tests/test_progress_update_advance.py` 新 5 个 testcase（H1 + M1 × 2 + M2）
7. `tests/test_validate_consistency.py` 新 `StructurallyIncompleteProgressTests`（M2 × 3）

## Round 2 关键约束（请逐条核对）

1. **H1**：`load_artifact_frontmatter("installation-result", release=...)` 现在能正确 resolve 到 `docs/release{release}/delivery/installation_result.md`；delivery → project-retrospective happy + reject 各有 CLI test。
2. **M1 lock contract**：`_do_update_advance` 现是 thin wrapper（仅调 `_run_update_pipeline`）；P6 A/B/E 整段移到 `_advance_compute_outcome` lambda → 再调 `_run_p6_advance_preflight(state, current_stage, root)` helper；compute_outcome 由 pipeline 在 locked critical section 内调用，state 是 freshly-locked frontmatter；任一 P6 dim 失败抛 ProgressStateError + multi-line msg → pipeline 印 `progress.py update: P6 dimension X failed; ...`（不动 progress.md）。
3. **M1 regression test**：`AdvanceLockedStatePreflightTests` 两个用例：
   - case 1: development with all tasks verified 但无 dev artifacts → 若 P6 不跑 apply 会成功；M1 fix 让 P6 跑 → reject "dimension A"；列出全部 6 个 missing path（2 stage-level + 4 per-task for T1）
   - case 2: spy lock 在 acquire 后 mutate progress.md 到 state Y（development without artifacts）→ 即使 setup 时 state X (prd-inception with PRD) 是 P6-passing，advance 仍 reject 因为 P6 看到 locked state Y
4. **M2 防御**：`get_required_artifacts(...)` 内部 `progress_from_mapping(state)` 直接 index `scenario` / `release` / `current_stage` 几个 required key，结构不全时抛 KeyError；现在 `_run_p6_advance_preflight`（progress.py 端）和 `check_consistency`（validate.py 端）都各自捕 `KeyError`/`TypeError`/`AttributeError` 转 ProgressStateError / issue string "progress.md is structurally incomplete"。
5. **M2 双端覆盖**：CLI 端（progress.py update --advance）和 doc-guardian 端（validate.py consistency）都修；3 + 1 = 4 个 regression test 验证 exit 1 + 干净 diagnostic（无 traceback）。
6. **L1 docstring + help**：validate.py 顶部 docstring 4 subcommand 描述精确（file / ids / consistency / all）；Class index 加 Class 8；argparse help 文本与实现一致（`consistency` 是 Class 8、`all` 是 Phase 7）。
7. **L2 SKILL P6 matrix**：A 行明确事实源是 required-artifacts.md + resolver；新增 "**不是** progress.md `artifacts:` dict" 强调；E 行拆 3 stage 分支与实现完全对齐。
8. **既有 invariant 保持**：M1 + M2 + L1 (canonical token) + replay-skips-artifacts 在 advance 路径上保持继承；既有 18 advance CLI tests + 22 apply + 12 consistency + 4 replay 全过；Phase 1-3 + 4 + 5.* + 6.1-6.3 测试全过。
9. **stderr 输出格式**：M1 refactor 后 P6 dim X 失败的 stderr prefix 从 `progress.py update --advance: P6 dimension X failed; ...` 变为 `progress.py update: P6 dimension X failed; ...`（pipeline 统一 prefix）；既有测试 substring assertion（`"dimension A"` / `"verification_status"` 等）继续通过。
10. **happy path tests 不受影响**：mocked `validate_doc` 模式继续工作；mock 在 lambda 内被消费而非 lambda 外；既有的 prd→srs / dev→testing / testing→delivery 三个 happy advance 仍全过。

## 重点 review 项

请按以下维度逐条核对：

### A. H1 fix 完整性

- `_PATH_TEMPLATES` 含 `"installation-result": "docs/release{release}/delivery/installation_result.md"`，与 directory-layout.md / artifacts.py REQUIRED_ARTIFACTS["delivery"] installation-result spec 一致？
- `_check_p6_dim_e(current_stage="delivery", ...)` 现成功调 `load_artifact_frontmatter("installation-result", release=release)` 不抛 "unknown doc_type"？
- `test_advance_delivery_to_retrospective_with_passing_installation_result`：写完整 delivery 三件套（deployment.md / operation_manual.md / installation_result.md with verification_status=pass）→ advance 成功 → current_stage=project-retrospective？
- `test_delivery_advance_rejects_with_failing_installation_result`：相同 setup 但 installation_result.verification_status=fail → reject "dimension E" + "verification_status" + progress.md 字节级未改？
- 既有 18 advance CLI tests 是否都没 break？

### B. M1 fix lock contract

- `_do_update_advance` 现是 5 行 thin wrapper：argparse → `_run_update_pipeline(args, root, event_name="update-advance", compute_outcome=lambda state, now: _advance_compute_outcome(state, now, root), success_label=...)`？
- `_advance_compute_outcome(state, now, root)` 流程：(1) `current_stage` isinstance str 校验 → ProgressStateError if not (2) `if current_stage in NEXT_STAGE:` 跑 `_run_p6_advance_preflight(state, current_stage, root)` (3) 调 `apply_update_advance(state, now=now)` 返回 outcome？
- `_run_p6_advance_preflight(state, current_stage, root)`：try `get_required_artifacts(state, root=root)` → except ArtifactError → ProgressStateError；except (KeyError, TypeError, AttributeError) → ProgressStateError "structurally incomplete"；A/B/E 失败 raise ProgressStateError(multi-line)？
- A 收集所有 missing → multi-line msg "P6 dimension A failed; required artifacts missing:\n- <path>\n- <path>"？
- B 收集所有 per-file issue → "P6 dimension B failed; doc-guardian rejected required artifacts:\n- <path>: <issue>\n- <path>: <issue>"？
- E 调 `_check_p6_dim_e(current_stage, state, root)` 返回 issue string → "P6 dimension E failed; <message>"？
- compute_outcome 抛 ProgressStateError 后 pipeline 行为：catch → 印 `progress.py update: <multi-line>` → exit 1 → progress.md 字节级未改（atomic write 未执行）？
- M1 regression test case 1（development without artifacts）：apply 单跑会成功（surrogate 满足）；M1 fix 后 P6 在 locked state 跑 → reject "dimension A" + 列出 6 个 missing dev artifact？
- M1 regression test case 2（spy lock mutate to state Y）：`patch.object(progress, "progress_lock", _spy_lock)` 用 contextmanager 在 acquire 后 mutate progress.md → P6 看到 locked state Y → reject + "dimension A" + "plan.md"？

### C. M2 防御性处理

- progress.py 端：`_run_p6_advance_preflight` 在 `get_required_artifacts` 调用周围加 `except (KeyError, TypeError, AttributeError) as exc:` → raise ProgressStateError "progress.md is structurally incomplete; required-artifact resolver inputs are missing or wrong type: <repr>"？
- validate.py 端：`check_consistency` 在 `get_required_artifacts` 调用周围加同样的 except → return [issue] (issues list)？
- 双端 4 个 regression test：3 progress.py（缺 scenario / 缺 release 各 1 + CLI exit 1 验证）+ 1 progress.py 端（advance with missing scenario）？
- structurally-incomplete diagnostic 单行消息能让 operator 一眼看出哪个字段错？

### D. L1 doc/help 准确性

- validate.py 顶部 docstring 4 subcommand 现描述准确：file (1-7) / ids / consistency (Class 8) / all (Phase 7 deferred)？
- Class index 加第 8 项 "Consistency"，与 task6_plan §7 + Phase 6.4 implementation 对齐？
- argparse `consistency` help 现是 "Class 8 cross-progress consistency check — required-artifact existence + per-file validity for the current stage"？
- argparse `all` help 现是 "Validate every doc in docs/ (deferred to Phase 7)"（不是 5/6）？
- `python3 skills/doc-guardian/scripts/validate.py --help` 输出完全一致？

### E. L2 SKILL.md P6 matrix 对齐

- A 行现明确：required-artifacts.md + `get_required_artifacts(progress, root)` 是事实源；progress.md `artifacts:` dict **不是** P6 A 推导依据（旧描述废止）？
- B 行精确化：对 A 推导出的每个路径都跑 `validate.py file`？
- C / D 行加 "由 apply_update_advance 间接 enforce" 说明（与实现的 sub_state 前置一致）？
- E 行拆 Stage 4 / 5 / 6 三个分支：Stage 4 用 task surrogate（per-task verification 已在 transition 时校验）；Stage 5 读 test-report；Stage 6 读 installation-result？
- 与 `command-reference.md §2.2` 描述一致？与 `_run_p6_advance_preflight` + `_check_p6_dim_e` 实现对应一致？

### F. Round 1 既有 (A) 部分保持

- `apply_update_advance` 状态机未动？22 unit tests 全过？
- `_apply_update_advance_handler` replay handler 未动？4 ReplayUpdateAdvanceTests 全过？
- `cmd_update` dispatcher / argparse mutex group 未动？三模式 event/task/advance 分支齐全？
- TERMINAL_EVENTS = `{"incident-resolve"}` + 14 → 15 events count 不变？supported_events_in_phase_6_4 测试断言准确？
- 既有 18 advance CLI tests + 22 apply tests + 12 consistency tests + 4 replay tests 全部仍 pass？
- Phase 1-3 / 4 / 5.* / 6.1-6.3 + Phase 6.3 round 2 + 6.3 round 2 L1 polish 全部测试仍 pass？

### G. Round 2 范围控制

- Round 2 不引入 Phase 7 设计讨论（如 `validate.py all` / 端到端 smoke / managed-project happy path）？
- Round 2 不动 incident apply / replay / TERMINAL_EVENTS（这些 6.3 round 2 已 (A)）？
- Round 2 不动 既有 advance state machine 和 replay handler（round 1 已 (A)）？
- Round 2 不动 Phase 6.1-6.3 已闭合的部分？

### H. 回归覆盖完整性

- Round 1 H1 修复 ✓ fixed（2 tests）
- Round 1 M1 修复 ✓ fixed（2 tests）
- Round 1 M2 修复 ✓ fixed（4 tests：3 validate.py + 1 progress.py）
- Round 1 L1 修复 ✓ fixed（doc + argparse help）
- Round 1 L2 修复 ✓ fixed（SKILL.md P6 matrix）

每项 finding 是否都有 evidence（具体 file:line + 测试或观察方式）？

### I. Open Question 状态

承接 round 1：

- "from= token validation 是否应严格比较 pre-advance state？" 仍 open（无变更，hardening 选项）
- "Class 8 consistency 是否应扩展含 doc status compatibility / task-count check？" 仍 open（无变更，Phase 7 territory）
- 这些 open question 在 round 2 review 中可视为 nice-to-have 而非 (B) 阻塞。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_4_advance_consistency_round2_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — round 2 修复总体判断、剩余 findings 数量分布、是否升 (A) + 是否阻塞 Task 6 closure
2. **Findings**（如仍有；按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Round 1 Findings 状态对照表**：H1 / M1 / M2 / L1 / L2 各自标 ✓ fixed / ⚠ partial / ❌ unfixed，并简要 grade
4. **Cross-Doc Consistency Check** — command-reference.md §2.2 + SKILL.md P6 matrix + validate.py docstring/help 与脚本行为一致性
5. **Checklist Results** — 按本 prompt §A-§H 各维度逐项 ✓ / ⚠️ / ❌
6. **Open Questions / Assumptions**（仅承接 round 1，不引入新；§I 列了 2 项可继承）
7. **Recommendation** — 三选一：
   - **(A) round 2 fixes complete; Task 6 implementation closes; ready for Phase 7 / next-task scope**
   - **(B) further fix needed before Task 6 closure**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：
- 哪些 finding 必须在 Task 6 closure 前修
- 哪些可推迟到 Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 7 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 不要重新评判 round 1 已 (A) 部分（apply state machine / replay handler / argparse mutex / TERMINAL_EVENTS / 既有测试）；本 round 仅评 5 项 fix 是否到位 + 既有 invariant 是否保持。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
