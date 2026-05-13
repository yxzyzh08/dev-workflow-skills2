# Claude Review Prompt — Task 6 Phase 5.4 Round 2 (post-fix regression review)

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase5_4_release_lifecycle_round2_review_20260507.md`。Round 2 通过后 Phase 5 子拆分整体闭环，可进入 **Phase 6**（`bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + `update --advance` + Gap-3/4/5）。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 5.4 Round 2 fixes** 做一次回归 review。Round 1 评审给出 **(B) fix before Phase 6** 结论，列出 0 High / 1 Medium / 1 Low；本轮请确认 2 个 finding 全部已修，并扫一眼新引入的代码 / 测试是否埋下新问题。

本轮是回归 review。范围：

- Round 1 review report：`docs/review/task6_phase5_4_release_lifecycle_review_20260507.md`
- Round 1 实施代码：`skills/_shared/dev_workflow/progress_state.py` / `progress_replay.py`、`skills/workflow-protocol/scripts/progress.py`、6 个新测试文件
- Round 2 fixes 的 diff（仅触动 progress_state.py / progress.py / 4 个测试文件）

**不要**要求 Phase 6 已实现。

## Round 1 baseline

- Phase 5.4 Round 1 review report: `docs/review/task6_phase5_4_release_lifecycle_review_20260507.md`
- Recommendation: **(B) fix before Phase 6**
- Findings: 0 High / **1 Medium (M1)** / **1 Low (L1)**
  - **M1** — `release-start` 的 BUG fan-out 信任 `unresolved_bugs` 路径；如果 progress.md / progress-history.md 被 corrupt 成绝对路径或含 `..`，replay 与 forward 都未拦截，可能写入 --root 之外的文件
  - **L1** — `release-start` 的 history summary 缺 canonical `version=` token；`version=` 仅在 result 字段，summary-only 消费者会漏掉

当前 Round 2 后测试 / compile：

```bash
python3 -m unittest discover -s tests
# Ran 468 tests in 3.941s
# OK
#  - baseline before round 1:  454 (Phase 1-4 + Phase 5.1/5.2/5.3 round 2 + Phase 5.4 round 1)
#  - round 2 net change:        +14
#    * test_apply_bug_intake.py        : +10 (BugPathShapeTests)
#    * test_progress_replay.py         : +2  (replay rejects absolute / traversal bug= token)
#    * test_progress_release_lifecycle.py : +2 (release-start refuses outside-root / absolute unresolved BUG)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts skills/workflow-protocol/scripts tests
# OK
```

## Round 2 修复摘要

### M1 — BUG 路径 shape + containment 双层防御

- 修改：`skills/_shared/dev_workflow/progress_state.py`
  - 新增 `_BUG_PATH_RE = re.compile(r"^docs/bug/BUG-\d{3}\.md$")`
  - 新增 `_validate_bug_path_shape(bug_path)` —— 一处定义：
    - 拒空 / 非 string
    - 拒 backslash（`docs\bug\BUG-001.md`）
    - 拒 POSIX 绝对路径（`/etc/passwd`）+ Windows drive (`C:/...`)
    - 拒 `.` / `..` / 空 segment
    - 拒不匹配 `docs/bug/BUG-NNN.md` (3 位 zero-pad，与 frontmatter-schema §4.4 round 3 L5 一致)
  - 在 `apply_bug_intake` 入口调一次 → forward path (CLI bug-intake) **与** replay path (`_apply_bug_intake_handler`) **共享** shape 校验
- 修改：`skills/workflow-protocol/scripts/progress.py`
  - import `_validate_bug_path_shape`
  - `_read_bug_for_release_start` 先调 `_validate_bug_path_shape`（捕 ProgressStateError 转 ProgressArtifactError），再 `(root / bug_rel).resolve()` + `relative_to(root.resolve())` 双重 containment（防 symlink/race）
  - 错误消息含 rel path + `outside --root` + 拒绝 fan-out 提示
- 新增 / 修改 regression tests：
  - **new** `tests/test_apply_bug_intake.py:BugPathShapeTests` ×10：absolute / Windows drive / `..` traversal / `.` segment / backslash / 错 filename pattern (INCIDENT-001) / 4 位 ID (BUG-1000) / 2 位 ID (BUG-01) / 错 parent dir (docs/incident) / canonical 接受
  - **new** `tests/test_progress_replay.py` ×2：replay 收到 `bug=/etc/passwd` 或 `bug=../etc/BUG-001.md` 都 reject，错误消息含 `absolute` 或 `'.' or '..'`
  - **new** `tests/test_progress_release_lifecycle.py` ×2：forge progress.md `unresolved_bugs` 含 `../etc/BUG-001.md` 或 `/etc/BUG-001.md` → release-start 退 1，progress.md / progress-history.md 字节不动

### L1 — release-start summary 加 canonical `version=` token

- 修改：`skills/_shared/dev_workflow/progress_state.py:apply_release_start`
  - history_summary 从 `"new release 0.2 started, scenario=S2-1, consumed N unresolved bugs"`
  - 改为 `"version=0.2 scenario=S2-1 new release started, consumed N unresolved bugs"`
  - history_result 保留 `version=...` token 作 human-readable echo
- 修改 test：`tests/test_apply_release_start.py:test_history_summary_canonical_for_replay` → `test_history_summary_canonical_tokens_in_summary_only`，断言 `version=0.5` 与 `scenario=S2-2` **直接在 summary** 中，不再 join result

## 重点 review 项

请按以下维度逐条核对：

### A. M1 fix 是否到位

- `_validate_bug_path_shape` 是否覆盖全部反向情形：empty / non-str / backslash / POSIX absolute / Windows drive / `.` / `..` / 空 segment / 错 filename pattern (INCIDENT-/CR-/4 位 ID/ 2 位 ID) / 错 parent dir？
- 错误消息含字段名 / 期望值 / 实际值，便于 caller 排错？
- `apply_bug_intake` 是否调一次 `_validate_bug_path_shape`，从而 forward + replay 共享同一道防线？
- `_read_bug_for_release_start` 是否双层防御：先 shape 校验（结构层），再 `relative_to(root_resolved)` containment（运行时层）？两层错误消息是否各自清晰？
- `_validate_bug_path_shape` 在 `release-start` 路径上的位置（在 `_read_bug_for_release_start` 顶部、`(root / bug_rel).resolve()` 之前）是否能在 progress.md tampered 时第一时间 abort？
- import 链路：`progress.py` from `progress_state` import `_validate_bug_path_shape`（前缀 `_` 表示 internal package shared，跨 module 用是 OK 的）— 命名约定是否合理？是否考虑改为 `validate_bug_path_shape`（无 `_`）？

### B. L1 fix 是否到位

- `apply_release_start` 的 history_summary 现在是否真的把 `version=<x.y>` 与 `scenario=<S2-x>` 都放进 summary 字符串本身？
- 测试 `test_history_summary_canonical_tokens_in_summary_only` 是否仅查 `outcome.history_summary`（不再 join `outcome.history_result`）？
- 既有 round 1 `test_replay_full_review_cycle` / `test_release_start_replay_extracts_version_and_scenario` 等测试是否仍然通过（replay 用 `_kv_tokens` 抽 summary + result，新 wording 不破坏 replay 行为）？

### C. 既有 invariant 是否保持

- Phase 5.1 + 5.2 + 5.3 + 5.4 round 1 的 454 个测试是否仍全过？
- M1 + M2 (review_iteration > 7 entry guard / history parse / replay consistency) 在 3 条 release lifecycle 命令路径上保持继承？
- `progress_lock.py` / `progress_history.py` / `progress_artifacts.py` 未被本批触动？
- `init` / `query` / `recover` / `update --event` / `update --task` 行为完全保留？
- `_run_update_pipeline` + `extra_writes_factory` 钩子未被触动？

### D. 测试质量

- M1 的 14 个新测试覆盖：单测 10（apply_bug_intake 各种 malformed path）+ replay 2（forward 早拒之外的 replay 路径独立验证）+ CLI 2（forge progress.md 后 release-start 拒的端到端路径）。各 reject 都断言 (a) 异常类型/exit 1、(b) 错误消息含可识别 token (`absolute` / `forward slashes` / `'.' or '..'` / `BUG-NNN.md` / `outside`)、(c) 文件字节级未改？
- L1 的测试断言纯粹是 summary-only？
- 所有新测都用 `tempfile.TemporaryDirectory` 隔离？
- 既有 round 1 测试（含 22 + 19 + 12 + 11 + 10 + 6 = 80 个 5.4 测试）是否未被本批误伤？

### E. Cross-doc 一致性

- `frontmatter-schema.md §4.4` 关于 `bug_id: ^BUG-\d{3}$` 的 3 位 zero-pad 要求现在被 `_BUG_PATH_RE` 严格执行？
- `command-reference.md §6 release-start` 的"BUG fan-out 必须仅作用于 managed-project BUG 文件"约束在 round 2 后真正生效？
- `command-reference.md §7 bug-intake` 的"<bug-report-path> 文件存在且通过 doc-guardian validate"在 Phase 5.4 仍是 thin check（type / target_release / consumed_in_release / 路径 shape）；完整 Class 1-7 / 全 doc-guardian 校验仍 deferred Phase 6？
- canonical history token contract（version= / scenario= / bug=）现在 3 条命令都满足"summary 单独可解析"约束？

### F. 设计 / 可维护性

- `_validate_bug_path_shape` 作为 cross-module shared helper 的命名 / 暴露方式是否合理？将来 Phase 6 `bug-start` / `bug-rework` 也会触碰 BUG 路径，能否复用同一 helper？
- 双层防御（shape + containment）的成本 / 收益：shape 是 O(1) string 操作，containment 是一次 `resolve()` + `relative_to()`，加起来微秒级；对 release-start fan-out（per-BUG 一次）成本可忽略？
- 错误消息层级：shape 错由 ProgressStateError 抛、containment 错由 ProgressArtifactError 抛，CLI 层都路由到 exit 1，分类合理？
- import `_validate_bug_path_shape` 跨 module 的 lint warning（`_`-prefixed 名字暴露）：是否值得改为 public 命名？

### G. 已知 Phase 6 后续工作（不在本 review 评判范围）

- Phase 6 `bug-start` / `bug-close` / `bug-rework`：active Bug Flow 入口/出口/重路由，含 Gap-3/4/5 protected task transitions
- Phase 6 `incident-start` / `incident-resolve`：workflow-incident-analysis stage + `TERMINAL_EVENTS` 在 abort/reconstruct 时落地
- Phase 6 `update --advance`：P6 矩阵 + required-artifacts + breakdown count 一致性 + cross-progress doc validation
- Phase 6 `validate.py consistency`：跨 progress.md + 全部 doc 的 cross-cutting 校验

这些不应作为 Round 2 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase5_4_release_lifecycle_round2_review_20260507.md
```

评审报告需要包含以下章节：

1. **Executive Summary** — Round 2 总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 6
2. **Round 1 Findings 回归状态** — M1 / L1 各自 ✅ Fixed / ⚠️ Partially Fixed / ❌ Not Fixed
3. **New Findings (Round 2)** — 没有则注明 "No new findings"
4. **Cross-Finding Consistency Check**
5. **Round 2 Implementation Quality Spot-checks** — `_validate_bug_path_shape`、`_read_bug_for_release_start` 双层防御、`apply_release_start` 新 summary、新增 14 个 regression test 的覆盖度
6. **Checklist Results** — 按本 prompt §A-§F 各维度逐项 ✓ / ⚠️ / ❌
7. **Open Questions / Assumptions**（如有）
8. **Recommendation** — 三选一：
   - **(A) accept regression and proceed to Phase 6**
   - **(B) fix before Phase 6**
   - **(C) revisit design**

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 6 前修
- 哪些可以推迟到 Phase 7
- 修复路径估计

## Boundaries

- 不要重写脚本、tests、references 或 SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 6 设计讨论；如发现 Phase 6 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
