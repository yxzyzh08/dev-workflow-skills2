# Claude Review Prompt — Task 6 Phase 4 status_transition.py

> 用法：把本文件 "## Prompt Body" 一节的全部内容整段发给 Claude（或 Codex）。Reviewer 应在同一个 repo 中完成代码审查，并把评审报告**完整保存**到 `docs/review/task6_phase4_status_transition_review_20260507.md`。评审通过后才能进入 Phase 5/6（`progress.py` 工作流状态机、Bug Flow、`update --advance`、`validate.py consistency`）。

---

## Prompt Body

请对 `dev-workflow-skills2` 项目的 **Task 6 Phase 4 implementation** 做一次代码 review。目标是在继续 Phase 5/6（`progress.py` + 完整 Bug Flow + `validate.py consistency`）之前，先确认刚新增的 doc-guardian frontmatter status 转移脚本（`status_transition.py`）是否正确、可维护、符合 references 与 Task 6 plan、并正确复用 Phase 3 的 changelog/validate API。

本轮是代码 review。**写集**仅限：

- 新增 CLI `skills/doc-guardian/scripts/status_transition.py`
- 新增 tests `tests/test_status_transition.py`

Phase 4 **不**实现：`progress.py` / `validate.py consistency` / `update --advance` / `bug-rework` / Gap-3/4/5 / event 白名单以外的事件。这些是 Phase 5/6 的范围；不要因为它们尚未存在而把它们当 finding。

## 当前工作背景

项目根：`/home/cgs/github_projects/dev-workflow-skills2/`

Task 6 Phase 1（docs alignment）/ Phase 2（shared foundation）/ Phase 3（`changelog.py` + `validate.py file/ids`）均已通过 review 闭环：

- Phase 1 review: `docs/review/task6_phase1_docs_alignment_review_20260507.md`（accept）
- Phase 2 round 1: `docs/review/task6_phase2_shared_foundation_review_20260507.md`（accept Phase 3，预留 Phase 4/5/6 fix points）
- Phase 2 round 2: `docs/review/task6_phase2_shared_foundation_round2_review_20260507.md`（accept）
- Phase 3 round 1: `docs/review/task6_phase3_changelog_validate_review_20260507.md`（B：Phase 4 前必修 H1 + M1/M2/M3）
- Phase 3 round 2: `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md`（A：accept and proceed to Phase 4，0H/0M/1L 残留 + sweep 已并入）

Phase 4 实现的当前运行结果：

```bash
python3 -m unittest discover -s tests
# Ran 153 tests in 0.352s
# OK
#  - baseline 117 (Phase 1-3 + shared foundation)
#  - new      36  (test_status_transition.py)

python3 -m compileall -q skills/_shared skills/doc-guardian/scripts tests
# OK

python3 skills/doc-guardian/scripts/status_transition.py --help
python3 skills/doc-guardian/scripts/status_transition.py plan --help
python3 skills/doc-guardian/scripts/status_transition.py apply --help
# 三个 help 均正常
```

## 阅读顺序（请严格按序读，不要跳读）

1. `docs/handoff/session_handoff_task6_phase4_20260507.md` — Phase 4 起点 & 约束（read order、scope、key constraints、acceptance target）
2. `docs/implementation/task6_plan_20260507.md` §9（status_transition.py plan）+ §11.3（atomicity）+ §12（test strategy）
3. `docs/review/task6_phase3_changelog_validate_round2_review_20260507.md` — Phase 3 closure & invariants
4. `docs/review/task6_phase3_changelog_validate_review_20260507.md` — Phase 3 round 1（解释当前严格度由来）
5. `skills/doc-guardian/SKILL.md` §6.7 — status_transition.py 接口、event 映射、调用顺序、Change Log 原子性、幂等
6. `skills/doc-guardian/references/change-log-format.md` §7.1 — `[frontmatter]` Pending entry 格式（与 §2.2 entry regex 一致）
7. `skills/doc-guardian/references/frontmatter-schema.md` §1-§2 — universal fields、status 状态机、gated 类型集合
8. `skills/_shared/dev_workflow/changelog.py` — Phase 4 复用 `promote_text` / `validate_text` / `Entry`
9. `skills/_shared/dev_workflow/atomic.py` — Phase 4 复用 `transaction()` 上下文管理器
10. `skills/_shared/dev_workflow/frontmatter.py` — `parse_frontmatter` / `render_markdown`
11. `skills/_shared/dev_workflow/markdown.py` — `find_section` / `replace_section_body`
12. `skills/_shared/dev_workflow/schema.py` — `INCREMENTAL_DOC_TYPES` / `GATED_APPROVED_TYPES` / `STATUSES`
13. `skills/doc-guardian/scripts/validate.py` — Phase 4 通过 `validate.validate_file` 做 post-write self-validate
14. `skills/doc-guardian/scripts/changelog.py` — CLI 风格参照（`--root`、bootstrap、exit code）
15. **新文件** `skills/doc-guardian/scripts/status_transition.py`
16. **新文件** `tests/test_status_transition.py`

可选背景：

- `docs/handoff/session_handoff_task6_phase3_20260507.md`
- `docs/handoff/task6_progress_py_prerequisites_20260506.md`
- `docs/design/skill_set_design_proposal_v0.5.md` §15.2

## Phase 4 关键约束（请逐条核对）

1. 本 repo 不是被 workflow 管理的项目；Phase 4 不得创建/编辑 repo-root `progress.md` / `progress-history.md`。
2. 工作树大量 untracked 是项目内容（`docs/` / `skills/` / `tests/` / 启动脚本），不得 delete/clean/reset/revert。
3. Tests 必须用 temp dirs / fixtures，不得 mutate 真实 `docs/` / `skills/` 当 managed project。
4. **写集**仅限：
   - `skills/doc-guardian/scripts/status_transition.py`
   - `tests/test_status_transition.py`

   未引入新的 shared module；status_transition.py 全部依赖已存在的 `_shared/dev_workflow/*` 与 `validate.validate_file`。
5. **Event 白名单严格 = `{write-complete, review-issues, review-passed, human-confirmed}`**；`issues-found` 是业务措辞、不是 event；`bug-rework` 是 Phase 6 territory，不能在 Phase 4 出现。
6. `human-confirmed` 仅对 `prd` / `srs` / `architecture` / `cr`（`schema.GATED_APPROVED_TYPES`）合法；其它 doc type 必须 reject。
7. 幂等重试：doc 已在目标 status 时 exit 0、**不写**文件、**不**追加 `[frontmatter]` Pending entry、**不**改 `updated`。
8. 多 doc：先全 dry-run 校验；reject 即不写；mutate 子集进 `atomic.transaction()`；任一写或 self-validate 失败 → 全部 rollback。
9. 增量类 doc：在同一 transaction 内追加 `[frontmatter]` Pending entry → `changelog.promote_text` 内存 promote → 写回；snapshot doc 仅改 frontmatter `status` + `updated`，不触碰 Change Log。
10. Post-write self-validate **必须**调 `validate.validate_file(abs_path, root)`（in-process，不 subprocess），保证与 Phase 3 单一事实源一致。
11. Phase 4 **不得**触发 `progress.py update --event` —— SKILL.md §6.7 明确"先 progress.py update，再 status_transition.py apply"，progress 端是 Phase 5/6。Phase 4 自己是该序列里的 step 5。

## 重点 review 项

请按以下维度逐条核对，不要跳过：

### A. `compute_plan(event, docs, root)` 纯逻辑

- event 不在白名单时是否 raise `StatusTransitionError`（不写 / 不进入 plan）？
- 文件不存在 / 读失败 / frontmatter parse 失败 → `op="reject"` + `errors=(...)`，不抛？
- doc_type / current_status 缺失或非法 → `op="reject"` 并保留可读 errors？
- gated_only=True 且 doc_type ∉ `GATED_APPROVED_TYPES` → reject。**先于** current==target 的 no-op 检查执行（避免非 gated doc 偶然处于 approved 时被错误 no-op）？
- current_status == target → `op="no-op"`，不进入 mutate 分支、**不**改文件？
- current_status ∉ `allowed_old` → reject 并指出 `allowed_old` 集合？
- `is_incremental` 是否仅以 `INCREMENTAL_DOC_TYPES` 集合为准？snapshot 类不会被强制要求 Pending Changes / Change Log 章节？
- `compute_plan` 是否完全 read-only（无 file write、无 atomic_write、无 transaction）？

### B. `apply_plan(plan, root, *, now=None)` 写流程

- plan 含任一 reject 时是否在**未写**之前 raise `StatusTransitionError`，并把所有 reject 的 errors 拼到 message？
- mutating 子集为空（全部 no-op）时是否直接返回 `ApplyResult(mutated=(), no_ops=...)`、不进入 transaction？
- `_build_new_content`：
  - 是否先 `parse_frontmatter` → 改 dict → `render_markdown`？
  - 是否对 incremental doc 找 `## Pending Changes` 章节后追加严格符合 §7.1 的 entry 行：`- {now} [frontmatter]: 更新 status 至 {target}`？
  - 是否在追加后直接调 `changelog.promote_text(new_content)` 在内存中合并 → Pending 清空 → Change Log 严格 layout？**没有**先写一次 Pending、再 promote、再覆盖（这种顺序会暴露 crash 中间态）？
  - 对 snapshot doc 是否仅 `render_markdown`、不动 Pending/Change Log 章节？
  - 内存阶段任何 `FrontmatterError` / `ChangelogError` / `MarkdownSectionError` 是否封装为 `StatusTransitionError` 并抛出（不写文件）？
- `transaction()` 上下文里：先把所有 mutate doc `tx.write_text` 完，再循环调 `validate_module.validate_file(abs_path, root)`；任一 issue 非空 → raise → context manager 触发 `tx.rollback()`，所有已写 doc 字节级恢复（per Phase 2 round 2 atomic 契约）？
- `now` 默认 `_utc_now_iso()` 即 `datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")`；测试可以注入固定 `now` 保证确定性？

### C. CLI（`plan` / `apply` 子命令 + `--root`）

- `--root` 默认 cwd；relative `--doc` 相对 `--root` 解析；absolute `--doc` 直接使用 — 行为是否与 Phase 3 changelog.py / validate.py 一致？
- `--event` 用 argparse `choices=` 校验，非法值由 argparse 输出 usage error → exit 2？
- `--doc` `action="append"` 支持重复，至少 1 个；缺失时 argparse exit 2？
- `plan` 子命令：
  - 任一 reject → exit 1 + stderr 列每条；
  - 全部 mutate / no-op → exit 0 + stdout 列每条；
  - 不写任何文件（dry-run）。
- `apply` 子命令：
  - reject → exit 1 + stderr 列 plan 全部条目（含未 reject 的 mutate / no-op）+ "refusing to mutate" 字样；
  - mutating 失败（apply_plan 抛 StatusTransitionError 或 OSError/AtomicWriteError）→ exit 1 + stderr 描述；
  - 全部 mutate / no-op → exit 0；no-op 在 stderr 单行提示，mutate 在 stdout 列出。
- 无子命令 → 打印 help → exit 2？
- `_REPO_ROOT = parents[3]` 与 `_SCRIPTS_DIR = parent`：在脚本被 `.claude/skills/` / `.agents/skills/` symlink 调用时是否仍能定位到原仓库（`__file__.resolve()` 走真实路径）？
- import bootstrap 是否同时把 repo root 与 scripts dir 加入 sys.path？`import validate as validate_module` 是否在 cross-script 场景下稳定？是否破坏 Phase 3 已有的 `tests/test_validate_file.py` import？

### D. 与 Phase 3 invariants 的一致性

请核对 Phase 4 没有违反 Phase 3 round 2 closure 留下的强契约：

- `changelog.promote_text(content)` 是 pure in-memory；Phase 4 调用之前**没有**先写 Pending 再 promote（否则 crash 中间态可绕过单调性 / 严格 layout）？
- `changelog.validate_text` 是讨论 Phase 3 已经设的 discipline gate；Phase 4 自己**不**重新解析或绕过它？
- Phase 4 生成的 Pending entry 是单行 canonical，**不**带 inline `<!-- -->` / 多行 close 等 trailing 内容（这些在 Phase 3 round 2 sweep 已被 `_classify_comment_line` 严格 reject）？
- `atomic.transaction()` 的 per-target rollback 与 parent dir fsync 行为已经过 Phase 2 round 2 review；Phase 4 没有自己另起原子化逻辑？
- `validate.validate_file(doc_path, root)` 作为 in-process 调用：Phase 4 是否避免 subprocess 让 self-validate 路径与 Phase 3 单一事实源同步演化？

### E. Tests

请逐类核对：

- `EventMappingTests`：
  - 4 events × incremental(srs) + snapshot(test-report)；
  - draft → in-review、revising → in-review、in-review → revising、in-review → review-passed、review-passed → approved（gated SRS）；
  - snapshot doc 只改 frontmatter，不出现 `## Pending Changes` / `## Change Log` / `[frontmatter]:` 字样。
- `GatedRejectionTests`：
  - PRD / SRS / Architecture / CR 各一条 review-passed → approved 通过；
  - development-plan / test-report 在 review-passed 调 human-confirmed 必 reject 且文件字节级不变。
- `IdempotencyTests`：
  - incremental + snapshot + 已 approved 的 gated doc 三种 already-at-target 场景，全部 byte-for-byte unchanged；
  - no-op 与 mutate 共存时只动 mutating 子集。
- `MultiDocTransactionTests`：
  - SRS + acceptance-plan happy path 全部 mutate；
  - 一 doc 状态非法 → 整批不写；
  - **post-write validate failure 通过 `unittest.mock.patch.object` mock `validate_module.validate_file` 强制返回 `["forced post-write failure"]`**，验证 transaction rollback 后双 doc 字节级恢复；
  - 未知 event → `compute_plan` raise；
  - 文件不存在 → reject + apply 抛错。
- `PendingEntryFormatTests`：
  - 验证 Pending entry 字面量 `- {now} [frontmatter]: 更新 status 至 {new}` 出现在最终 doc；
  - `validate_text` 与 `validate_file` 在 apply 后均返回 `[]`；
  - new (2026-05-20) 在 existing (2026-05-15) 上方（date desc）；
  - 已存在 HTML comment 在 Pending Changes 时 apply 仍能 promote 并通过 validate_text。
- `CliIntegrationTests`：
  - `--help`、no-subcommand → 2；
  - invalid event → 2；
  - plan 不写、列 MUTATE / `draft -> in-review`；
  - apply 写 + stdout 含 "mutated"；
  - 幂等 no-op CLI exit 0 + stderr 含 "no-op"；
  - reject 时 plan exit 1（含 REJECT），apply exit 1（含 "refusing to mutate"）+ 文件不变；
  - multi-doc CLI all-or-nothing happy path。
- 是否全部用 `tempfile.TemporaryDirectory()` 隔离？是否触碰真实 repo 的 `docs/` / `skills/`（不应触碰）？

### F. Cross-doc 一致性

- `change-log-format.md §7.1` 描述的 helper 调用模式（更新 frontmatter → 追加 Pending entry → 同 transaction promote → 写回前 validate Change Log → 多 doc rollback → 幂等 no-op）与 `status_transition.py` 实现严格一致？
- `change-log-format.md §2.2` entry regex（timestamp / `[section_ref]` / summary）与生成的 Pending entry 字面量一致？
- `frontmatter-schema.md §1-§2` 的 status 状态机（draft → in-review → review-passed / approved；revising 反向）与 EVENTS 表格一致？`approved` 仅 PRD/SRS/Architecture/CR 与 `gated_only=True` 配置一致？
- `doc-guardian/SKILL.md §6.7` 描述的 4 events 映射、调用顺序（caller 先 progress.py update --event 成功后再调 helper）、Change Log 原子性段落与实现一致？
- `task6_plan_20260507.md §9 / §11.3 / §12` 的 status_transition.py CLI 形态、多 doc atomicity、test 策略与实现一致？

### G. 设计 / 可维护性

- API 是否便于 Phase 5 `progress.py update --event` 在事件路由里通过 `import status_transition` + `compute_plan` / `apply_plan` 直接复用，**而不是** subprocess 启动 CLI？
- `PlanItem` / `ApplyResult` dataclass 形状是否清晰、frozen？
- `EVENTS` 表格是否单一定义、便于未来扩展（如未来加 review-reopen，需要并发改 SKILL.md / change-log-format.md / progress.py event whitelist）？
- 错误信息是否带 `rel_path` + 关键事实（current_status / allowed_old），便于 caller 直接 surface 给用户？
- import 顺序与 `noqa: E402` 注释是否合理？是否同时 bootstrap repo root 与 scripts 目录？
- 是否引入了不必要的新 shared helper（应避免；Phase 4 优先用现有 `_shared/dev_workflow/*`）？

### H. 已知 Phase 5/6 后续工作（不在本 review 评判范围）

仅供参考、避免误评：

- Phase 5 `progress.py` 工作流状态机（init / query / recover / update --event / update --task / release-close / release-start / bug-intake）
- Phase 5 `validate.py consistency` 跨 progress.md ↔ doc 一致性（Class 8）
- Phase 6 `bug-start` / `bug-close` / `bug-rework` / `incident-start` / `incident-resolve` + Gap-3/4/5 protected rollback
- Phase 6 `progress.py update --advance` P6 矩阵 + required-artifacts 解析
- Phase 7 full smoke + AGENTS/CLAUDE/plugin metadata polish

这些不应作为 Phase 4 阻塞 finding。

## 评审报告输出

请把评审报告**完整保存**到：

```
/home/cgs/github_projects/dev-workflow-skills2/docs/review/task6_phase4_status_transition_review_20260507.md
```

评审报告需要包含以下章节（参考 Phase 1 / 2 / 3 review 结构）：

1. **Executive Summary** — Phase 4 实施总体判断、findings 数量分布（H/M/L）、是否阻塞 Phase 5/6
2. **Findings**（按 H / M / L 排序，每条含 location（file:line）+ issue + impact + recommendation）
3. **Cross-Doc Consistency Check** — change-log-format.md / frontmatter-schema.md / doc-guardian SKILL.md / task6_plan §9/§11.3/§12 与脚本行为一致性
4. **Checklist Results** — 按本 prompt §A-§G 各维度逐项 ✓ / ⚠️ / ❌
5. **Open Questions / Assumptions**（如有）
6. **Recommendation** — 三选一：
   - **(A) accept and proceed to Phase 5/6**（可附 Phase 5 之前可选清理 list）
   - **(B) fix before Phase 5/6**（必修 list；为何 Phase 5 不能在不修这些 finding 下推进）
   - **(C) revisit design**（哪些已闭环架构层决策被本批 implementation 触发了再设计需求）

如果 recommendation 是 (B)，请明确：

- 哪些 finding 必须在进 Phase 5 前修
- 哪些可以推迟到 Phase 5/6/7
- 修复路径估计（行数级粗估）

## Boundaries

- 不要重写 `status_transition.py` / `tests/test_status_transition.py` / 其它脚本 / references / SKILL.md。仅 review。
- 不要主动修改任何文件，**除了**评审报告本身（保存到上方指定路径）。
- 不要让 review 滑入 Phase 5/6 设计讨论；如发现 Phase 5/6 隐患，记 Open Questions / Assumptions 即可。
- 评审完成后，回到主对话告知 review 已写入指定路径 + 一句话结论，不要在主对话粘贴整份报告。
