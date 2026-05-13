# Claude Review Prompt — Task 6 Phase 6.3 Round 2 Fixes

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase6_3_incident_round2_review_20260507.md`。round 1 给的是 (B) fix-before-Phase-6.4；本轮是确认 round 2 修复是否足以升 (A)。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 6.3 round 2 修复** 做一次代码 review。round 1 评审（`docs/review/task6_phase6_3_incident_review_20260507.md`）给 (B) fix-before-Phase-6.4，列出 1 Medium + 3 Low + 1 cosmetic：

- **M1**（must fix）：`cmd_incident_resolve` 在 `_validate_incident_path_shape` + 容器化检查之前就读 `progress.md.incident_report_path` 并调用 `validate_doc` / `read_markdown`；hand-edited progress.md 可让 absolute path 或 traversal 路径在 reject 前已被读盘。
- **L1**（must fix）：`cmd_incident_resolve` 收到非法 `--action retry` 返回 exit 2，应该是 exit 1（workflow validation，与 `release-start --scenario` / `init --scenario` 一致）。
- **L2**（defer-able）：`command-reference.md §11/§12` Append history 模板未展示 canonical replay tokens（缺 `bug=`/`incident=` for start，`incident=` for resolve）。
- **L3**（defer-able）：`workflow-protocol/SKILL.md` command matrix + reference 受保护字段表说 incident-start 是 `current_stage==testing` 触发，但 implementation/tests 允许任意 stage 触发。
- **cosmetic**：`load_bug_report(expect_root_cause=...)` 错误消息提到 bug-start / bug-rework 两个 caller，但未提到 incident-start。

User 选择 **全部修**（与 Phase 6.2 round 2 保持一致），不留 polish 给 Phase 7 backlog。本 round 2 修复已落地。

本轮是代码 review。**写集**仅限：

- `skills/workflow-protocol/scripts/progress.py`
  - `cmd_incident_resolve`：从 `progress.md` 读 `incident_report_path` 之后 + `validate_doc` 之前，加 `_validate_incident_path_shape` + `(root / path).resolve().relative_to(root.resolve())` 容器化校验，任一失败直接 exit 1（**M1**）
  - `cmd_incident_start`：在 `_resolve_under_root` 之后、`validate_doc` 之前对 `rel_bug` / `rel_incident` 各跑一次 `_validate_bug_path_shape` / `_validate_incident_path_shape`（**M1 一致性加固**：`_resolve_under_root` 已防越界，但 in-tree-but-non-canonical 路径之前会先到 validate_doc 才被拒；现改为 shape 先于 validate_doc）
  - `cmd_incident_resolve`：非法 `--action <bad>` 分支 `return 2 → return 1`（**L1**）+ 注释解释 exit code 契约（与 5.1 round 2 M2 一致）
- `skills/_shared/dev_workflow/progress_artifacts.py` `load_bug_report` `expect_root_cause` mismatch 错误消息追加 incident-start caller 说明（**cosmetic**）
- `skills/workflow-protocol/references/command-reference.md`：
  - §11 Append history 模板重写为 canonical-token 形式（含 `bug=`/`incident=`/`root_cause=prd-exception`），加说明清单（**L2**）
  - §12 Append history 模板重写（含 `action=`/`incident=`），加 3 action result/next prose 对照（**L2**）
  - 受保护字段转换表 `incident-start` 行：移除 `current_stage=testing` 描述，改为 `project_state=active + bug_flow.active=false + workflow_incident_active=false + BUG.root_cause=prd-exception`，注明 Phase 6.3 起 `current_stage` 不再 gate（**L3**）
- `skills/workflow-protocol/SKILL.md` command matrix `incident-start` 行：state 列从 `current_stage==testing AND ...` 改为 `project_state==active AND bug_flow.active==false AND workflow_incident_active==false AND BUG.root_cause==prd-exception`，并备注 PRD-exception escalation 可在 Stage 5 / 6 / 7 任一 stage 触发（**L3**）
- `tests/test_progress_incident.py`：
  - `test_incident_resolve_invalid_action_returns_2` 重命名 `_returns_1` 并断言 exit 1 + 注释解释 round 2 L1 修复缘由（**L1 test pin**）
  - 新增 `IncidentResolveCorruptIncidentPathTests`（4 testcases：absolute / traversal / non-canonical 目录 / 4-digit ID 各 1）+ `IncidentStartCorruptPathPreflightTests`（2 testcases：BUG / INCIDENT 在 in-tree 但非 canonical 路径）（**M1 regression**）
  - 6 个新 test 都通过 `patch.object(progress, "validate_doc", ...)` 加 spy，断言 `validate_doc` 调用次数为 0（即 path-shape guard 真的在 validate_doc 之前 reject）

Round 2 不修改：
- `progress_state.py` 的 incident state-machine 逻辑（round 1 已闭合）
- `progress_replay.py` 的 incident handler / TERMINAL_EVENTS / TERMINAL_INCIDENT_ACTIONS / dispatch loop
- `apply_incident_start` / `apply_incident_resolve` 函数体
- 既有 26 个 incident CLI tests（仅 1 个 rename）

## 当前工作背景

Task 6 Phase 6.1 / 6.2 已 (A) closed（含 6.2 + 3 Low polish）。Phase 6.3 round 1 给 (B)；本 round 2 把 (B) 中 5 项全部修复。

Round 2 实施后基线：

```bash
python3 -m unittest discover -s tests
# Ran 719 tests in 6.5s — OK
#  - baseline (round 1 close): 713
#  - new in round 2:           +6
#    * IncidentResolveCorruptIncidentPathTests : +4
#    * IncidentStartCorruptPathPreflightTests  : +2
#  - 既有 _returns_2 重命名为 _returns_1：净 0 项

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK

python3 skills/workflow-protocol/scripts/progress.py incident-resolve --action retry
# stderr 含 "continue / abort / reconstruct"，exit 1（round 1 是 exit 2）
```

End-to-end 加固验证：

- 6 个 spy 测试都让 `validate_doc` 不被调用（path-shape guard 优先 reject）
- IncidentStartCorruptPathPreflightTests 两个用例分别用 in-tree 非法 BUG / INCIDENT 路径，shape guard 在 validate_doc 之前 reject + progress.md 字节级未改（spy_validate 未被触达）

## 阅读顺序

1. `docs/review/task6_phase6_3_incident_review_20260507.md` round 1 评审报告（5 项 finding 一览 + recommendation）
2. `skills/workflow-protocol/scripts/progress.py` `cmd_incident_resolve` 与 `cmd_incident_start` 的 round 2 改动（shape+containment preflight；invalid --action exit 1）
3. `skills/_shared/dev_workflow/progress_artifacts.py` `load_bug_report` 错误消息（cosmetic 段）
4. `skills/workflow-protocol/references/command-reference.md` §11/§12 Append history + 受保护字段表 incident-start 行（L2 + L3 doc 修复）
5. `skills/workflow-protocol/SKILL.md` command matrix incident-start 行（L3）
6. `tests/test_progress_incident.py` 新 `IncidentResolveCorruptIncidentPathTests` + `IncidentStartCorruptPathPreflightTests` + 重命名的 invalid_action 测试

## Round 2 关键约束（请逐条核对）

1. **M1 fix order**：incident-resolve 顺序变为 (a) parse progress.md (b) workflow_incident_active 检查 (c) 取 incident_report_path 字段 (d) `_validate_incident_path_shape` (e) containment via `relative_to` (f) `validate_doc` (g) `read_markdown` (h) cross-check resolution_action/status (i) `_run_update_pipeline`。step (d)(e) 在 (f)(g) 之前，且任一失败 exit 1 + progress.md 字节级未改。
2. **M1 incident-start 一致性加固**：cmd_incident_start 顺序变为 (a) argparse (b) `_resolve_under_root` 双 path (c) `_validate_bug_path_shape` + `_validate_incident_path_shape` (d) progress.md 存在 (e) `validate_doc` BUG (f) `validate_doc` INCIDENT (g) load_bug_report (h) read_markdown INCIDENT + triggered_by_bug 校验 (i) `_run_update_pipeline`。shape guard 在 step (c) 触发，spy 证明 validate_doc 不会先于 shape guard。
3. **L1 exit code 契约**：missing required → exit 2（CLI usage error，argparse-style）；supplied-but-invalid → exit 1（workflow validation error，与 release-start --scenario / init --scenario 同型）。L1 fix 注释明确这两类的边界。
4. **L2 canonical token 文档**：§11 incident-start summary template 现含 `bug=<path> incident=<path> root_cause=prd-exception PRD exception triggered`；§12 incident-resolve template 现含 `action=<v> incident=<path> Incident resolved`；说明清单覆盖 result/next 在 3 action 下的具体 prose（与实现 `apply_incident_start` / `apply_incident_resolve` 的 history_result / history_next 完全一致）。
5. **L3 stage applicability 对齐**：SKILL.md command matrix `incident-start` 行 state 列改为 `project_state==active AND bug_flow.active==false AND workflow_incident_active==false AND BUG.root_cause==prd-exception`，无 current_stage 限制；command-reference.md 受保护字段表 incident-start 行同步更新；并明确"Phase 6.3 起：不 gate `current_stage`——PRD 异常 escalation 可在 Stage 5、6、7 任一 stage 触发；前序 phase 描述的 testing-only 已废止"。
6. **Cosmetic load_bug_report 错误消息**：现含 3 个 caller 提示（bug-start / bug-rework / incident-start），覆盖所有 `expect_root_cause` 调用点。
7. **既有 invariant 全部保持**：M1 (round 2) shape preflight 与 round 1 的 M6 double-safety / cross-check 串接合法；既有 32 个 incident CLI tests（去掉 1 个 rename）+ 16 incident-start unit + 24 incident-resolve unit + 10 ReplayIncidentTests + ReplayTerminalSemanticsTests 全过；Phase 6.1/6.2 + earlier phase 测试全过。

## 重点 review 项

请按以下维度逐条核对：

### A. M1 fix 完整性

- `cmd_incident_resolve` shape+containment preflight 是否在所有 disk read 之前？grep `validate_doc` / `read_markdown` 在 cmd_incident_resolve 内的位置都晚于新加的 `_validate_incident_path_shape` + `relative_to` 块？
- 4 个 corrupt-path regression test 真的覆盖：absolute / traversal / 非 canonical 目录 / 4-digit ID？每个都 patch validate_doc 为 spy 并断言 `validate_calls == []`？
- progress.md 字节级未改 assertion 用比较 `_open_incident_then_corrupt` 返回的 corrupted text vs `(root / "progress.md").read_text()` 后的 text；两者相等说明 path-shape guard 拒绝后不再写 progress.md？
- `cmd_incident_start` 的 shape 加固对 `rel_bug` 和 `rel_incident` 两路径都做？2 个 IncidentStartCorruptPathPreflightTests 用 in-tree 非 canonical 路径（如 `docs/foo/BUG-700.md` / `docs/notes/INCIDENT-007.md`），spy 证明 `validate_doc` 未被调用？
- 同时确认 round 1 既有 happy / reject path 全过（spy 不影响 validate_doc 真实调用的合法路径）？

### B. L1 exit code

- invalid `--action retry` 现在 exit 1？missing `--action` 仍 exit 2？
- 注释明确两类区别（CLI usage error vs workflow validation error），并引用 5.1 round 2 M2 contract？
- 重命名后的 `test_incident_resolve_invalid_action_returns_1` 断言 exit 1 + stderr 含 `continue / abort / reconstruct`？
- 与既有 `bug-rework --root-cause development`（reject）/ `release-start --scenario` reject 的 exit code 一致（均 exit 1，因为是 workflow-meaning 错误）？

### C. L2 doc 修复

- §11 Append history block summary 现含 3 个必备 token（`bug=` / `incident=` / `root_cause=prd-exception`）+ 字面词 `PRD exception triggered`；result 含 `current_stage=workflow-incident-analysis; bug_flow.active=true root_cause=prd-exception`；next 默认 `workflow-evolution fills INCIDENT body`？
- §11 说明清单覆盖：必备 token / 字面词 grep 用途 / replay 不重读 BUG/INCIDENT 文件 / forward CLI double-safety 校验 doc 文件？
- §12 Append history block summary 现含 2 个必备 token（`action=` / `incident=`）+ 字面词 `Incident resolved`？
- §12 说明清单覆盖：3 个 action 的 result/next 对应 prose（continue / abort / reconstruct 各自一段）；replay dispatch 用 `action=` token 决定是否标 terminal；replay 不重读 INCIDENT 文件？
- 模板与 `apply_incident_start` / `apply_incident_resolve` 实现 history_summary / history_result / history_next 字面级别一致（grep "current_stage=workflow-incident-analysis" / "Bug Flow exited" / "Incident resolved" 几个关键串都对得上）？

### D. L3 SKILL.md / 受保护字段表对齐

- `workflow-protocol/SKILL.md` 第 132 行 `incident-start` 行的 state 列现写 `project_state==active AND bug_flow.active==false AND workflow_incident_active==false AND BUG.root_cause==prd-exception`，并附 Phase 6.3 起 `current_stage` 不再 gate 的说明？
- `command-reference.md` 受保护字段转换表 `incident-start` 行同步更新，"Phase 6.3 起：不 gate `current_stage`" 字样存在？
- 与 `apply_incident_start` 实际前置条件（`_validate_active_project` + `_validate_bug_flow_inactive` + `_validate_incident_active` 检查 + path 校验）字面对齐？
- `test_apply_incident_start.test_can_trigger_from_any_stage_and_substate` 与文档现声明形成 documentation-implementation 闭环？

### E. Cosmetic

- `load_bug_report` `expect_root_cause` mismatch 错误现按 3 caller 列出："bug-start passes the --root-cause argument; bug-rework passes bug_flow.root_cause from progress.md; incident-start passes the literal 'prd-exception'"？
- 既有 BUG-related 测试（grep `expect_root_cause`）未引用旧错误消息字面（避免 regression）？

### F. 既有 invariant 保持

- 719 测试全过；compileall 干净；no repo-root progress.md leak？
- M1 round 2 shape preflight 与 round 1 既有 M6 double-safety 串接：先 path-shape (round 2) → containment (round 2) → validate.py file (round 1 M6) → load_bug_report / read_markdown frontmatter cross-check (round 1)？
- 既有 32 incident CLI tests 中 1 重命名 + 6 新 = 38 项全过？
- Phase 6.1 / 6.2 / 6.2 polish + earlier phase 测试全过？

### G. Round 2 范围控制

- Round 2 不动 incident apply 状态机 / replay handler / TERMINAL_EVENTS / dispatch terminal gate（这些 round 1 已 (A)）？
- Round 2 不引入新 phase 6.4 设计讨论？
- Round 2 不动 unrelated SKILL.md / reference 文档（仅 incident-start 行修复）？

### H. Open issue 状态

- Round 1 的 4 个 Open Question（§5）：
  - "Phase 6.3 prompt's broader incident-start state-machine behavior" → round 2 已通过 SKILL/table 修复完整 alignment ✓
  - "replay require `root_cause=prd-exception` validation" → 仍 open（round 2 未动 replay；reviewer 可决定是否 must-fix Phase 6.4）
  - "_INCIDENT_RESOLVE_ACTIONS public" → 仍 open（无变更）
  - "validate_doc catch ImportError" → 仍 open（无变更）
- 这些 open question 在 round 2 review 中可视为 nice-to-have 而非 (B) 阻塞？

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase6_3_incident_round2_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — round 2 修复总体判断、剩余 findings 数量分布、是否升 (A)
2. **Findings**（如仍有；按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Round 1 Findings 状态对照表**：M1 / L1 / L2 / L3 / cosmetic 各自标 ✓ fixed / ⚠ partial / ❌ unfixed，并简要 grade
4. **Cross-Doc Consistency Check** — command-reference.md §11/§12 + SKILL.md command matrix + 受保护字段表 与脚本行为一致性
5. **Checklist Results** — 按本 prompt §A-§G 各维度逐项 ✓ / ⚠️ / ❌
6. **Open Questions / Assumptions**（仅承接 round 1，不引入新；§H 列了 4 项可继承）
7. **Recommendation** — 三选一：
   - **(A) round 2 fixes complete; accept and proceed to Phase 6.4 (`update --advance` + `validate.py consistency`)**
   - **(B) further fix needed before Phase 6.4**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：
- 哪些 finding 必须在进 Phase 6.4 前修
- 哪些可推迟到 Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6.4 设计讨论；如发现后续 phase 隐患，记 Open Questions / Assumptions 即可。
- 不要重新评判 round 1 已 (A) 部分（incident apply 状态机 / replay / TERMINAL_EVENTS / 既有测试设计）；本 round 仅评 5 项 fix 是否到位 + 既有 invariant 是否保持。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
